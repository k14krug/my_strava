"""Minimal local import, inspection and rebuild commands."""

import argparse
import json
import sqlite3
import sys

from .analysis import analyze_activity, compact_analysis
from .config import startup_config
from .errors import RideWorksError
from .store import Store


def main(argv=None):
    parser = argparse.ArgumentParser(prog="rideworks")
    parser.add_argument("--data-dir", help="Data location (overrides RIDEWORKS_DATA_DIR and ~/.rideworks)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("import-fit", help="Preserve and import one FIT/FIT.GZ").add_argument("path")
    commands.add_parser("inspect", help="Compact source evidence; no raw streams").add_argument("activity_id")
    commands.add_parser("analyze", help="Source summary and best 20-minute result; no raw streams").add_argument("activity_id")
    commands.add_parser("reextract", help="Rebuild from the preserved original").add_argument("source_id")
    serve = commands.add_parser("serve", help="Open the local RideWorks browser application")
    serve.add_argument("--port", type=int, help="Loopback port (overrides FLASK_RUN_PORT; default: 8765)")
    args = parser.parse_args(argv)
    try:
        config = startup_config(args.data_dir, getattr(args, 'port', None))
        if args.command == "serve":
            from .web import serve as serve_web
            serve_web(config.data_dir, config.port, debug=config.debug)
            return 0
        with Store(config.data_dir) as store:
            if args.command == "import-fit":
                result = store.import_fit(args.path)
            elif args.command == "inspect":
                result = store.inspect(args.activity_id)
            elif args.command == "analyze":
                result = compact_analysis(analyze_activity(store, args.activity_id))
            else:
                result = store.reextract(args.source_id)
        print(json.dumps(result, indent=2, ensure_ascii=True))
    except (RideWorksError, OSError, sqlite3.Error) as exc:
        print(f"RideWorks: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
