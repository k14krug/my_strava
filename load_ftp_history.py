import csv
from datetime import datetime
from strava import create_app, db
from strava.models import FTPHistory

app = create_app()

def load_ftp_history(csv_filepath):
    with app.app_context():
        with open(csv_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                ftp_value, date_str = row
                date = datetime.strptime(date_str, '%d-%b-%y').date()
                ftp_history = FTPHistory(date=date, ftp=int(ftp_value.split()[0]))
                db.session.add(ftp_history)
            db.session.commit()

if __name__ == "__main__":
    csv_filepath = '/home/kkrug/projects/strava/ftp-history.csv'
    load_ftp_history(csv_filepath)
    print("FTP history loaded successfully.")
