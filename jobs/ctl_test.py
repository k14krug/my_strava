#!/usr/bin/env python3
# ...existing imports if any...
import os
import sys
import math
from datetime import datetime
# Add project root to path to locate "jobs" package
sys.path.insert(0, "/home/kkrug/projects/strava")
from jobs.jobs_config import create_app
from strava.models import db
from sqlalchemy.sql import text

# Global starting CTL value
STARTING_CTL = 2

# Updated SQL_QUERY using the FTP from ftp_history for TSS calculation.
SQL_QUERY = """
SELECT
    a.id,
    a.name,
    a.start_date,
    a.normalized_power,
    a.intensity_factor,
    a.moving_time,
    (
      (a.moving_time * a.normalized_power * a.intensity_factor)/
      (
        ((SELECT f.ftp
          FROM ftp_history f
          WHERE f.date <= DATE(a.start_date)
          ORDER BY f.date DESC
          LIMIT 1) * 3600)
      )
    ) * 100 as tss,
    (SELECT f.ftp
     FROM ftp_history f
     WHERE f.date <= DATE(a.start_date)
     ORDER BY f.date DESC
     LIMIT 1) AS ftp
FROM activities a
WHERE a.start_date > '2023-09-13'
  and a.start_date < '2024-01-10'
order by a.start_date;
"""

def main():
    app = create_app()
    with app.app_context():
        # Use a connection context to execute the SQL query
        with db.engine.connect() as connection:
            # Use .mappings() so that rows are dict-like objects
            result = connection.execute(text(SQL_QUERY)).mappings()
            ctl = STARTING_CTL  # use global starting CTL value
            for row in result:
                tss = row['tss']
                ctl += (tss - ctl) / 42.0  # update CTL for each row
                # Now display TSS along with CTL
                print(f"Activity {row['id']} on {row['start_date']}: TSS = {tss:.2f}, CTL = {ctl:.2f}, FTP = {row['ftp']}")

def main_with_decay():
    """
    Same as main but applies exponential decay between activities based on days gap.
    """
    app = create_app()
    with app.app_context():
        with db.engine.connect() as connection:
            result = connection.execute(text(SQL_QUERY)).mappings()
            rows = list(result)
            if not rows:
                print("No activities found.")
                return
            ctl = STARTING_CTL  # use global starting CTL value
            last_date = None
            for row in rows:
                # Ensure start_date is a datetime object
                current_date = row['start_date']
                if not isinstance(current_date, datetime):
                    current_date = datetime.strptime(current_date, "%Y-%m-%d")
                if last_date is not None:
                    gap_days = (current_date.date() - last_date.date()).days
                    if gap_days > 1:
                        # Print gap information before applying decay
                        print(f"Gap of {gap_days} days detected between {last_date.date()} and {current_date.date()}")
                        ctl *= math.exp(- (gap_days - 1) / 42.0)
                tss = row['tss']
                ctl += (tss - ctl) / 42.0  # update CTL
                print(f"Activity {row['id']} on {current_date.date()}: TSS = {tss:.2f}, CTL = {ctl:.2f}, FTP = {row['ftp']}")
                last_date = current_date

if __name__ == "__main__":
    #main()
    # To run the decay-aware processing, uncomment the following line:
    main_with_decay()
