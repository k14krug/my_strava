from __init__ import create_app
from strava.models import db, User

app = create_app()

with app.app_context():
    user = User(username="kkrug", email="kenkrug@yahoo.com")
    user.set_password("admin14")
    db.session.add(user)
    db.session.commit()

print("Test user created!")
