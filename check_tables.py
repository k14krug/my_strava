from strava.models import db
from strava import create_app

app = create_app()
with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("Existing tables:")
    print(inspector.get_table_names())
