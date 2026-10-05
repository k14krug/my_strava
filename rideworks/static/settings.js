'use strict';
for (const form of document.querySelectorAll('.strava-actions form')) {
  form.addEventListener('submit', () => {
    for (const button of document.querySelectorAll('.strava-actions button')) button.disabled = true;
    const button = form.querySelector('button');
    button.textContent = form.action.endsWith('/sync') ? 'Syncing…' : form.action.endsWith('/connect') ? 'Connecting…' : 'Disconnecting…';
  });
}
