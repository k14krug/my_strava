"""Narrow local Strava Settings boundary; shared OAuth/sync logic lives in strava."""
from datetime import datetime, timezone
from html import escape
import json
import secrets
from threading import Lock
import time
from urllib.parse import parse_qs

from .config import ConfigurationError, strava_credentials
from .store import Store
from .strava import (ApiClient, ApiError, AuthenticationError, OperationBusyError, TokenFile, authorization_url,
                     callback_values, complete_connect, disconnect, sync)
from .strava_api import SyncError

COUNTS = ('new_activities', 'existing_activities_enriched', 'unchanged_observations',
          'ambiguous_new_associations', 'performance_rebuild_recommended')
NOTICES = {
    'connected': 'Strava connected. You can sync now.',
    'disconnected': 'Strava disconnected. Your activity history is retained.',
    'unconfirmed': 'Local Strava connection removed; remote revocation was not confirmed. Check your Strava app settings.',
    'credentials': 'Configure your Strava app credentials in the local .env, then try again.',
    'authorization': 'Authorization needs attention. Reconnect and grant activity:read_all using the original Strava account. If Strava cannot return here, check that its Authorization Callback Domain is 127.0.0.1.',
    'sync_failed': 'Sync could not complete. Check your connection and stored export boundary, then try a later manual sync. Activity history and the successful-sync checkpoint were not advanced.',
    'rate_limited': 'Strava rate limit reached. Sync stopped without retry; try a later manual sync.',
    'busy': 'Another Strava operation is running. Wait for it to finish before trying again.',
}


class Settings:
    def __init__(self, data_dir, *, credentials=strava_credentials, client_factory=ApiClient):
        self.data_dir = data_dir
        self.credentials = credentials
        self.client_factory = client_factory
        self.nonce = secrets.token_urlsafe(32)
        self.pending = None
        self.operation = Lock()
        # Derived aggregate display state only. No credentials, OAuth codes or IDs.
        self.display = TokenFile(data_dir)
        self.display.path = self.display.root / '.strava-settings.json'
        self.notice = None
        self.port = 8765

    def configured(self):
        try:
            return self.credentials()
        except ConfigurationError:
            return None

    def state(self):
        try:
            value = json.loads(self.display.path.read_text())
            if not isinstance(value, dict):
                return {}
            result = {'attention': value.get('attention') is True}
            if type(value.get('successful_at')) is int and value['successful_at'] > 0:
                result['successful_at'] = value['successful_at']
                if all(type(value.get(k)) is int and value[k] >= 0 for k in COUNTS):
                    result.update({k: value[k] for k in COUNTS})
            return result
        except (OSError, ValueError):
            return {}

    def remember(self, value):
        try:
            self.display.save(value)
        except OSError:
            # Derived display state cannot undo an already committed sync/token change.
            self.notice = 'Display details could not be saved; connection and sync checkpoint remain authoritative.'

    def content(self, local_time):
        credentials = self.configured()
        saved = self.state()
        token_file = TokenFile(self.data_dir)
        try:
            token_file.read()
            connected, attention = True, False
        except AuthenticationError:
            connected = False
            attention = token_file.path.exists() or saved.get('attention', False)
        expired = self.pending is not None and time.monotonic() > self.pending[1]
        attention = attention or expired
        status = 'Connected' if connected else 'Authorization needs attention' if attention else 'Not connected'
        with Store(self.data_dir) as store:
            row = store.connection.execute('SELECT successful_at FROM strava_sync_state WHERE singleton=1').fetchone()
        cutoff = row[0] if row else None
        last_time = local_time(datetime.fromtimestamp(cutoff, timezone.utc).isoformat(), compact=True) if cutoff else 'Never'
        outcome = ''
        if cutoff == saved.get('successful_at') and all(k in saved for k in COUNTS):
            outcome = (f'<p id="strava-outcome">{saved[COUNTS[0]]:,} new · {saved[COUNTS[1]]:,} enriched · '
                       f'{saved[COUNTS[2]]:,} unchanged</p>')
            if saved[COUNTS[3]]:
                outcome += f'<p>{saved[COUNTS[3]]:,} ambiguous local matches created separate Activities.</p>'
            if saved[COUNTS[4]]:
                activities = 'Activity needs' if saved[COUNTS[4]] == 1 else 'Activities need'
                outcome += f'<p>{saved[COUNTS[4]]:,} {activities} an explicit Performance rebuild; changed results remain hidden.</p>'
        def action(name, label, secondary=False):
            button_class = ' class="secondary"' if secondary else ''
            return (f'<form method="post" action="/settings/strava/{name}">'
                    f'<input type="hidden" name="nonce" value="{self.nonce}">'
                    f'<button type="submit"{button_class}>{label}</button></form>')
        actions = ''
        if credentials:
            actions += action('sync', 'Sync now') if connected else action('connect', 'Reconnect Strava' if attention else 'Connect Strava')
        if connected or token_file.path.exists():
            actions += action('disconnect', 'Disconnect', secondary=True)
        setup = '' if credentials else '<p>Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in the ignored local <code>.env</code>, then reload Settings. Use <code>127.0.0.1</code> as the Strava Authorization Callback Domain.</p>'
        message = 'Authorization timed out. Reconnect and check that the Strava Authorization Callback Domain is 127.0.0.1.' if expired else self.notice
        notice = f'<p role="status" id="strava-notice">{escape(message)}</p>' if message else ''
        return f'''<header><h1>Settings</h1></header><section class="panel strava-settings" aria-labelledby="strava-heading">
<h2 id="strava-heading">Strava</h2><dl><div><dt>Connection</dt><dd id="strava-connection">{status}</dd></div>
<div><dt>App credentials</dt><dd id="strava-credentials">{'Configured' if credentials else 'Missing'}</dd></div>
<div><dt>Last successful sync</dt><dd id="strava-last-sync">{last_time}</dd></div></dl>
{setup}{notice}{outcome}<div class="strava-actions">{actions}</div>
<p class="strava-manual-note">Sync runs only when you choose Sync now. It does not run continuously.</p></section>
<script src="/static/settings.js" defer></script>'''

    @staticmethod
    def redirect(location='/settings'):
        return 303, {'Location': location}, b''

    def failure(self, error, *, authorization=False):
        if isinstance(error, OperationBusyError):
            name = 'busy'
        elif isinstance(error, ConfigurationError):
            name = 'credentials'
        elif isinstance(error, AuthenticationError):
            name = 'authorization'
            if authorization or not TokenFile(self.data_dir).path.exists():
                self.remember(self.state() | {'attention': True})
        elif isinstance(error, ApiError) and error.status == 429:
            name = 'rate_limited'
        else:
            name = 'sync_failed'
        self.notice = NOTICES[name]  # Never render exception text or request/response bodies.

    def post(self, path, body, origin):
        origins = {f'http://127.0.0.1:{self.port}', f'http://localhost:{self.port}'}
        try:
            values = parse_qs(body.decode('ascii'), max_num_fields=2, strict_parsing=True)
            supplied = values.get('nonce', [])
            valid = len(supplied) == 1 and secrets.compare_digest(supplied[0].encode(), self.nonce.encode())
        except (ValueError, UnicodeError):
            valid = False
        if origin not in origins or not valid:
            return 403, {}, b'Invalid Settings action. Reload Settings and try again.'
        if path not in ('/settings/strava/connect', '/settings/strava/sync', '/settings/strava/disconnect'):
            return 404, {}, b'Unknown Settings action.'
        if not self.operation.acquire(blocking=False):
            return 409, {}, NOTICES['busy'].encode()
        # A second queued submission cannot reuse this action nonce.
        self.nonce = secrets.token_urlsafe(32)
        self.notice = None
        try:
            with Store(self.data_dir) as store:
                credentials = self.configured()
                if path.endswith('/disconnect'):
                    result = disconnect(store, self.client_factory(credentials) if credentials else None)
                    self.pending = None
                    self.remember(self.state() | {'attention': False})
                    self.notice = NOTICES['disconnected' if result['remote_revocation'] in ('revoked', 'not_connected') else 'unconfirmed']
                else:
                    if not credentials:
                        raise ConfigurationError('Missing Strava app configuration')
                    client = self.client_factory(credentials)
                    if path.endswith('/connect'):
                        with TokenFile(self.data_dir).lock():
                            state = secrets.token_urlsafe(32)
                            self.pending = state, time.monotonic() + 180
                            return self.redirect(authorization_url(client.client_id, f'http://127.0.0.1:{self.port}/strava/callback', state))
                    result = sync(store, client)
                    self.remember({'attention': False, 'successful_at': result['before'], **{k: result[k] for k in COUNTS}})
        except (SyncError, ConfigurationError, OSError) as error:
            self.failure(error)
        finally:
            self.operation.release()
        return self.redirect()

    def callback(self, query):
        if not self.operation.acquire(blocking=False):
            return 409, {}, NOTICES['busy'].encode()
        pending, self.pending = self.pending, None  # One use, including a declined/malformed response.
        try:
            if pending is None or time.monotonic() > pending[1]:
                raise AuthenticationError('Authorization expired; reconnect')
            code, scopes = callback_values(query, pending[0])
            credentials = self.configured()
            if not credentials:
                raise ConfigurationError('Missing Strava app configuration')
            with Store(self.data_dir) as store, TokenFile(self.data_dir).lock():
                complete_connect(store, self.client_factory(credentials), code, scopes)
            self.remember(self.state() | {'attention': False})
            self.notice = NOTICES['connected']
        except (SyncError, ConfigurationError, OSError) as error:
            self.failure(error, authorization=True)
        finally:
            self.operation.release()
        return self.redirect()
