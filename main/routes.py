from flask import Blueprint, render_template, request
from flask_login import login_required
from models import Activity, TrainingLoad
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import func
from datetime import datetime
from datetime import date, timedelta



main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@login_required
def index():
    activities = Activity.query.order_by(Activity.start_date.desc()).all()
    return render_template("main/index.html", activities=activities)


@main_bp.route("/year_progression", methods=["GET"])
@login_required
def year_progression():
    """Generate the yearly distance progression graph with improved formatting and height."""

    # Get unit preference (default: miles)
    unit = request.args.get("unit", "miles")
    conversion_factor = 1609.34 if unit == "miles" else 1000  # Convert meters to miles or km

    # Query activities from the database
    activities = Activity.query.with_entities(
        func.date(Activity.start_date).label("ride_date"),
        func.year(Activity.start_date).label("year"),
        func.sum(Activity.distance / conversion_factor).label("distance")
    ).group_by("ride_date", "year").order_by("ride_date").all()

    # Convert to DataFrame
    df = pd.DataFrame(activities, columns=["ride_date", "year", "distance"])

    # Ensure `ride_date` is a DateTime object
    df["ride_date"] = pd.to_datetime(df["ride_date"])

    # Convert ride_date to "day of year" (0 = Jan 1, 364 = Dec 31)
    df["day_of_year"] = df["ride_date"].dt.dayofyear

    # Convert day of year to formatted Month-Day (MMM DD)
    df["formatted_date"] = df["ride_date"].dt.strftime("%b %d")

    # Compute cumulative distance for each year
    df["cumulative_distance"] = df.groupby("year")["distance"].cumsum()

    # Get list of available years
    available_years = sorted(df["year"].unique())

    # Create Plotly figure
    fig = go.Figure()

    # Add each year as a separate line, overlaying them
    for year in available_years:
        year_data = df[df["year"] == year]
        fig.add_trace(go.Scatter(
            x=year_data["day_of_year"],  # X-axis: Days of the year
            y=year_data["cumulative_distance"],  # Y-axis: Cumulative distance
            mode="lines",
            name=str(year),
            customdata=list(zip(year_data["year"], year_data["formatted_date"])),  # Attach year and formatted date
            hovertemplate="Year: %{customdata[0]}<br>Date: %{customdata[1]}<br>Distance: %{y:.2f} " + unit + "<extra></extra>"
        ))

    # Style the chart
    fig.update_layout(
        title="Yearly Distance Progression (Overlaid)",
        xaxis_title="Date",
        yaxis_title=f"Total Distance ({'miles' if unit == 'miles' else 'km'})",
        hovermode="x unified",
        template="plotly_white",
        legend_title="Year",
        height=800,  # Make the graph taller
        xaxis=dict(
            tickmode="array",
            tickvals=[0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365],  # Approx month markers
            ticktext=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            showgrid=True
        ),
        yaxis=dict(
            showgrid=True
        )
    )

    graph_html = fig.to_html(full_html=False)

    return render_template("main/year_progression.html", graph_html=graph_html, available_years=available_years, unit=unit)


@main_bp.route("/fitness_fatigue")
@login_required
def fitness_fatigue():
    """Generate a graph of Fitness (CTL) and Fatigue (ATL) over time with filtering."""
    
    # Get selected date range from the form (default: all time)
    date_range = request.args.get("date_range", "all")
    
    # Query training load data with filtering
    today = date.today()
    query = TrainingLoad.query.order_by(TrainingLoad.date)

    if date_range == "3m":
        cutoff_date = today - timedelta(days=90)
    elif date_range == "6m":
        cutoff_date = today - timedelta(days=180)
    elif date_range == "1y":
        cutoff_date = today - timedelta(days=365)
    else:
        cutoff_date = None  # No filter, show all data

    if cutoff_date:
        query = query.filter(TrainingLoad.date >= cutoff_date)

    training_data = query.all()
    print(f"🔍 Found {len(training_data)} training load records for range: {date_range}")

    if not training_data:
        return "<p>No training data found for the selected period.</p>"

    df = pd.DataFrame([(t.date, t.ctl, t.atl, t.tsb) for t in training_data],
                      columns=["date", "ctl", "atl", "tsb"])
    print(df.head())  # Debugging DataFrame

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["ctl"], mode="lines", name="CTL (Fitness)", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df["date"], y=df["atl"], mode="lines", name="ATL (Fatigue)", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df["date"], y=df["tsb"], mode="lines", name="TSB (Form)", line=dict(color="green")))

    fig.update_layout(title="Fitness & Fatigue Over Time",
                      xaxis_title="Date",
                      yaxis_title="CTL / ATL / TSB",
                      hovermode="x unified",
                      height=600,
                      template="plotly_white")

    graph_html = fig.to_html(full_html=False)

    print(f"✅ Graph generated successfully. Graph HTML Length: {len(graph_html)}")  # Debug output

    return render_template("main/fitness_fatigue.html", graph_html=graph_html, date_range=date_range)


@main_bp.route("/graph")
@login_required
def graph():
    activities = Activity.query.all()
    dates = [act.start_date for act in activities]
    distances = [act.distance / 1000 for act in activities]

    fig = px.line(x=dates, y=distances, title="Distance Over Time", labels={"x": "Date", "y": "Distance (km)"})
    graph_html = fig.to_html(full_html=False)

    return render_template("main/graph.html", graph_html=graph_html)
