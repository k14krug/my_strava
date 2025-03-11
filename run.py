# run.py
import os
from strava import create_app

app = create_app()

if __name__ == "__main__":
    debug_mode = (os.environ.get("FLASK_DEBUG", "false").lower() == "true")
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
