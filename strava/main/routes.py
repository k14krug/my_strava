from flask import Blueprint, render_template, request, abort, current_app, session
from flask_login import login_required
from ..models import Activity, TrainingLoad, FTPHistory
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sqlalchemy import func
from datetime import datetime
from datetime import date, timedelta
from jobs.training_load import TrainingLoadCalculator

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

    # Query activities from the database
    if unit == "miles":
        # If showing miles, use the distance directly (already in miles)
        activities = Activity.query.with_entities(
            func.date(Activity.start_date).label("ride_date"),
            func.year(Activity.start_date).label("year"),
            func.sum(Activity.distance).label("distance")
        ).group_by("ride_date", "year").order_by("ride_date").all()
    else:
        # If showing kilometers, convert miles to km (1 mile = 1.60934 km)
        activities = Activity.query.with_entities(
            func.date(Activity.start_date).label("ride_date"),
            func.year(Activity.start_date).label("year"),
            func.sum(Activity.distance * 1.60934).label("distance")
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
        cutoff_date = date(2018, 2, 1)  # Set to February 1, 2018

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


@main_bp.route("/activity/<int:activity_id>")
@login_required
def activity_detail(activity_id):
    """Display detailed information about a specific activity"""
    activity = Activity.query.get_or_404(activity_id)
    print(f"🔍 Found activity: {activity.strava_id}")
    training_load = TrainingLoad.query.filter_by(activity_id=activity.strava_id).first()
    
    segment_details = []
    for se in activity.segment_efforts:
        # Retrieve all efforts for the same segment
        all_efforts = se.segment.efforts  # using backref defined in models
        sorted_efforts = sorted(all_efforts, key=lambda e: e.average_watts or 0, reverse=True)
        rank = sorted_efforts.index(se) + 1 if se in sorted_efforts else None
        fastest_effort = min(all_efforts, key=lambda e: e.elapsed_time or float('inf'))
        segment_details.append({
            "segment_name": se.segment.name,
            "favorite": se.segment.favorite,                      # New key
            "distance_miles": se.segment.distance * 0.000621371 if se.segment.distance else None,  # New key
            "power": se.average_watts,
            "time": se.elapsed_time,
            "rank": rank,
            "fastest_time": fastest_effort.elapsed_time,
            "fastest_date": fastest_effort.start_date,
            "total_efforts": len(all_efforts)
        })
    
    return render_template("main/activity.html", 
                           activity=activity,
                           training_load=training_load,
                           segment_details=segment_details)

@main_bp.route("/segment_efforts/<int:segment_id>")
@login_required
def segment_efforts(segment_id):
    """
    Display a page showing all local efforts for a specific segment.
    """
    from ..models import Segment, SegmentEffort
    segment = Segment.query.get_or_404(segment_id)
    efforts = segment.efforts  # Initially unsorted

    # Retrieve sorting parameters from query string
    sort_by = request.args.get("sort", "start_date")
    order = request.args.get("order", "asc")
    reverse_flag = (order == "desc")

    # Define key function based on sort criteria
    if sort_by == "start_date":
        key_func = lambda e: e.start_date or datetime.min
    elif sort_by == "elapsed":
        key_func = lambda e: e.elapsed_time or 0
    elif sort_by == "avg_watts":
        key_func = lambda e: e.average_watts or 0
    else:
        key_func = lambda e: e.start_date or datetime.min

    efforts = sorted(efforts, key=key_func, reverse=reverse_flag)

    # Build Plotly chart as before...
    import pandas as pd
    import plotly.express as px
    data = []
    for e in efforts:
        data.append({
            "date": e.start_date.date() if e.start_date else None,
            "distance": e.distance,
            "elapsed_time": e.elapsed_time,
            "average_watts": e.average_watts,
            "average_heartrate": e.average_heartrate
        })
    df = pd.DataFrame(data)
    if not df.empty:
        fig = px.line(df, x="date", y="average_watts",
                      #title=f"Your Recent Efforts on {segment.name}",
                      labels={"date": "Date", "average_watts": "Average Power (W)"})
        graph_html = fig.to_html(full_html=False)
    else:
        graph_html = "<p>No efforts found for this segment.</p>"
        
    return render_template("main/segment_efforts.html",
                           segment=segment,
                           efforts=efforts,
                           graph_html=graph_html,
                           sort=sort_by,
                           order=order)


@main_bp.route("/power_graph", methods=["GET"])
@login_required
def power_graph():
    """Generate a graph of best_*m_power results with filtering, overlaid with FTP history and detected peaks."""
    
    # Get selected date range and power metric from the form
    date_range = request.args.get("date_range", "all")
    power_metric = request.args.get("power_metric", "best_10m_power")
    
    # Query activities with filtering
    today = date.today()
    query = Activity.query.order_by(Activity.start_date)

    if date_range == "1m":
        cutoff_date = today - timedelta(days=30)
    elif date_range == "3m":
        cutoff_date = today - timedelta(days=90)
    elif date_range == "6m":
        cutoff_date = today - timedelta(days=180)
    elif date_range == "1y":
        cutoff_date = today - timedelta(days=365)
    elif date_range == "2y":
        cutoff_date = today - timedelta(days=730)
    else:
        cutoff_date = None  # No filter, show all data

    if cutoff_date:
        query = query.filter(Activity.start_date >= cutoff_date)

    activities = query.all()

    if not activities:
        return "<p>No activities found for the selected period.</p>"

    # Create a DataFrame for the selected power metric
    df = pd.DataFrame(
        [(act.start_date.date(), getattr(act, power_metric)) for act in activities],
        columns=["date", "power"]
    )
    df = df[df["power"] > 0]  # Exclude dates with zero power values
    df = df.sort_values("date")
    
    # Detect local maxima (peaks) in the power data
    power_array = df["power"].values
    # Adjust distance and prominence as needed based on your data characteristics
    peak_indices, properties = find_peaks(power_array, distance=5, prominence=5)
    df_peaks = df.iloc[peak_indices].copy()
    df_peaks["ftp_est_95pct"] = 0.95 * df_peaks["power"]  # 95% of the detected peak power

    # Query FTP history from the FTPHistory table and create a DataFrame
    if cutoff_date:
        ftp_records = FTPHistory.query.filter(FTPHistory.date >= cutoff_date).order_by(FTPHistory.date).all()
    else:
        ftp_records = FTPHistory.query.order_by(FTPHistory.date).all()
    if ftp_records:
        df_ftp = pd.DataFrame(
            [(record.date, record.ftp) for record in ftp_records],
            columns=["date", "ftp"]
        )
        df_ftp = df_ftp.sort_values("date")
    else:
        df_ftp = pd.DataFrame(columns=["date", "ftp"])

    # Create the Plotly figure
    fig = go.Figure()
    
    # Add power metric trace
    fig.add_trace(go.Scatter(
        x=df["date"], 
        y=df["power"], 
        mode="lines",
        name=power_metric
    ))
    
    # Overlay FTP history trace
    if not df_ftp.empty:
        fig.add_trace(go.Scatter(
            x=df_ftp["date"],
            y=df_ftp["ftp"],
            mode="lines",
            name="FTP History",
            line=dict(dash="dash", color="orange")
        ))
    
    # Overlay detected peak points
    fig.add_trace(go.Scatter(
        x=df_peaks["date"],
        y=df_peaks["power"],
        mode="markers",
        name="Detected Peaks",
        marker=dict(color="red", size=8, symbol="cross")
    ))
    
    # Overlay 95% of the peak power values (potential FTP updates)
    fig.add_trace(go.Scatter(
        x=df_peaks["date"],
        y=df_peaks["ftp_est_95pct"],
        mode="markers",
        name="95% of Peak",
        marker=dict(color="purple", size=6, symbol="triangle-up")
    ))
    
    fig.update_layout(
        title=f"{power_metric.replace('_', ' ').title()} Over Time with FTP History and Detected Peaks",
        xaxis_title="Date",
        yaxis_title="Power (Watts)",
        hovermode="x unified",
        height=600,
        template="plotly_white"
    )

    # For debugging, you can print the peaks:
    #print(df_peaks[["date", "power", "ftp_est_95pct"]])
    
    graph_html = fig.to_html(full_html=False)
    return render_template("main/power_graph.html", graph_html=graph_html, date_range=date_range, power_metric=power_metric)

@main_bp.route("/power_over_time", methods=["GET"])
@login_required
def power_over_time():
    """Display power over various time intervals with filtering options."""
    
    # Retrieve filter values from query or session with defaults
    power_metric = request.args.get("power_metric", session.get("power_over_time_power_metric", "best_20m_power"))
    date_range = request.args.get("date_range", session.get("power_over_time_date_range", "1y"))
    sort_by = request.args.get("sort", session.get("power_over_time_sort", "power"))
    sort_order = request.args.get("order", session.get("power_over_time_order", "desc"))
    
    # Save filter preferences to session for persistence
    session["power_over_time_power_metric"] = power_metric
    session["power_over_time_date_range"] = date_range
    session["power_over_time_sort"] = sort_by
    session["power_over_time_order"] = sort_order

    # Query activities with filtering
    today = date.today()
    query = Activity.query.order_by(Activity.start_date)

    if date_range == "6m":
        cutoff_date = today - timedelta(days=180)
    elif date_range == "1y":
        cutoff_date = today - timedelta(days=365)
    elif date_range == "2y":
        cutoff_date = today - timedelta(days=730)
    else:
        cutoff_date = None  # No filter, show all data

    if cutoff_date:
        query = query.filter(Activity.start_date >= cutoff_date)

    activities = query.all()

    if not activities:
        return "<p>No activities found for the selected period.</p>"

    # Create a DataFrame and sort by power value
    df = pd.DataFrame([(act.id, act.strava_id, act.start_date, act.name, act.distance, act.ftp, getattr(act, power_metric), act.normalized_power, act.intensity_factor) for act in activities],
                      columns=["id", "strava_id", "date", "name", "distance", "ftp", "power", "normalized_power", "intensity_factor"])
    df = df[df["power"] > 0]  # Exclude activities with zero power values

    # Sort the DataFrame
    df = df.sort_values(by=sort_by, ascending=(sort_order == "asc")).reset_index(drop=True)
    df["rank"] = df["power"].rank(ascending=False, method='min').astype(int)  # Rank the activities by power

    return render_template("main/power_over_time.html", activities=df.to_dict(orient="records"), power_metric=power_metric, date_range=date_range, sort_by=sort_by, sort_order=sort_order)

@main_bp.route("/dynamic_fitness_fatigue")
@login_required
def dynamic_fitness_fatigue():
    """Dynamically calculate and display Fitness (CTL) and Fatigue (ATL) over time."""
    
    # Process line selection form submission
    if "update_lines" in request.args:
        selected = request.args.getlist("lines")
        session['show_ctl'] = 'ctl' in selected
        session['show_atl'] = 'atl' in selected
        session['show_tsb'] = 'tsb' in selected
        session['show_ftp'] = 'ftp' in selected

    selected_lines = {
        "ctl": session.get('show_ctl', True),
        "atl": session.get('show_atl', True),
        "tsb": session.get('show_tsb', True),
        "ftp": session.get('show_ftp', True)
    }

    # Get selected date range and custom dates (if provided)
    date_range = request.args.get("date_range", "all")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    
    start_date_custom = end_date_custom = None
    if start_date_str and end_date_str:
        try:
            start_date_custom = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date_custom = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    today = date.today()
    query = Activity.query.order_by(Activity.start_date)
    # print how many rows are returned
    print(f"🔍Found {query.count()} activities in the database")
    
    
    if start_date_custom and end_date_custom:
        query = query.filter(Activity.start_date >= start_date_custom,
                             Activity.start_date <= end_date_custom)
        print(f"🔍 filtered to  {query.count()} activities in date range of {start_date_custom} to {end_date_custom}")
    
        cutoff_date = start_date_custom  # Use custom start date as cutoff for FTP records
    else:
        if date_range == "3m":
            cutoff_date = today - timedelta(days=90)
        elif date_range == "6m":
            cutoff_date = today - timedelta(days=180)
        elif date_range == "1y":
            cutoff_date = today - timedelta(days=365)
        elif date_range == "2y":
            cutoff_date = today - timedelta(days=730)
        else:
            cutoff_date = date(2018, 2, 1)
        query = query.filter(Activity.start_date >= cutoff_date)

    activities = query.all()
    if not activities:
        return "<p>No activities found for the selected period.</p>"
    else:
        print(f"🔍 filtereed to {len(activities)} activities for range: {date_range}")

    # Initialize TrainingLoadCalculator
    app = current_app._get_current_object()
    tl_calculator = TrainingLoadCalculator(app)

    # Calculate training loads dynamically
    training_loads = []
    for act in activities:
        ftp = tl_calculator.get_ftp_for_date(act.start_date.date())
        # Use 'norm_power' instead of 'np' to avoid shadowing numpy
        norm_power = act.normalized_power if act.normalized_power else tl_calculator.estimate_np(act.average_speed, act.distance, act.total_elevation_gain)
        intensity_factor = (norm_power / ftp) if norm_power and ftp else 0.75
        tss = round((act.moving_time / 3600 * norm_power * intensity_factor) / ftp * 100, 2) if norm_power and ftp else 0

        training_loads.append({
            "date": act.start_date.date(),
            "tss": tss,
            "ctl": 0,
            "atl": 0,
            "tsb": 0
        })

    # Calculate CTL, ATL, TSB
    
    
    
    
    tl_calculator._calculate_fitness_metrics(training_loads)

    # Convert to DataFrame
    df = pd.DataFrame(training_loads, columns=["date", "ctl", "atl", "tsb"])
    
    # Now that we have build training_loads, print a datafrom of just their date and tss values for debugging
    x = pd.DataFrame(training_loads, columns=["date","tss", "ctl"])
    print(f"🔍 training_loads: {x}")

    # Query FTP history from the FTPHistory table and create a DataFrame
    if start_date_custom and end_date_custom:
        ftp_records = FTPHistory.query.filter(FTPHistory.date >= start_date_custom,
                                              FTPHistory.date <= end_date_custom).order_by(FTPHistory.date).all()
    elif cutoff_date:
        ftp_records = FTPHistory.query.filter(FTPHistory.date >= cutoff_date).order_by(FTPHistory.date).all()
    else:
        ftp_records = FTPHistory.query.order_by(FTPHistory.date).all()
    if ftp_records:
        # Apply custom logarithmic transformation but also store the true FTP value
        scale = 84.68
        offset = -174.8
        df_ftp = pd.DataFrame(
            [(record.date, scale * np.log10(record.ftp) + offset, record.ftp) for record in ftp_records],
            columns=["date", "ftp", "ftp_true"]
        )
        df_ftp = df_ftp.sort_values("date")
    else:
        df_ftp = pd.DataFrame(columns=["date", "ftp", "ftp_true"])

    fig = go.Figure()
    if selected_lines["ctl"]:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ctl"], mode="lines", name="CTL (Fitness)", line=dict(color="blue")))
    if selected_lines["atl"]:
        fig.add_trace(go.Scatter(x=df["date"], y=df["atl"], mode="lines", name="ATL (Fatigue)", line=dict(color="red")))
    if selected_lines["tsb"]:
        fig.add_trace(go.Scatter(x=df["date"], y=df["tsb"], mode="lines", name="TSB (Form)", line=dict(color="green")))
    if selected_lines["ftp"] and not df_ftp.empty:
        fig.add_trace(go.Scatter(
            x=df_ftp["date"],
            y=df_ftp["ftp"],
            mode="lines",
            name="FTP History",
            customdata=df_ftp["ftp_true"],
            hovertemplate="True FTP: %{customdata}<extra></extra>",
            line=dict(dash="dash", color="orange")
        ))

    fig.update_layout(title="Dynamic Fitness & Fatigue Over Time",
                      xaxis_title="Date",
                      yaxis_title="CTL / ATL / TSB",
                      hovermode="x unified",
                      height=600,
                      template="plotly_white")

    graph_html = fig.to_html(full_html=False)

    return render_template("main/fitness_fatigue.html", graph_html=graph_html, date_range=date_range, selected_lines=selected_lines)

@main_bp.route("/toggle_favorite", methods=["POST"])
@login_required
def toggle_favorite():
    from ..models import Segment, db
    seg_id = request.form.get("segment_id")
    new_value = request.form.get("favorite") == "1"  # '1' means set as favorite
    segment = Segment.query.get(seg_id)
    if segment:
        segment.favorite = new_value
        db.session.commit()
    return "", 204

@main_bp.route("/my_segments")
@login_required
def my_segments():
    from ..models import Segment
    # Retrieve filters from request or session
    search = request.args.get("search", session.get("my_segments_search", "")).strip()
    country_filter = request.args.get("country", session.get("my_segments_country", ""))
    only_favorites = request.args.get("only_favorites")
    if only_favorites is None:
        only_favorites = "0"
    sort_by = request.args.get("sort_by", session.get("my_segments_sort_by", ""))
    sort_order = request.args.get("sort_order", session.get("my_segments_sort_order", "asc"))
    
    session["my_segments_search"] = search
    session["my_segments_country"] = country_filter
    session["my_segments_only_favorites"] = only_favorites
    session["my_segments_sort_by"] = sort_by
    session["my_segments_sort_order"] = sort_order

    segments_query = Segment.query
    if only_favorites == "1":
        segments_query = segments_query.filter_by(favorite=True)
    if search:
        segments_query = segments_query.filter(Segment.name.ilike(f"%{search}%"))
    if country_filter:
        if country_filter == "Watopia":
            segments_query = segments_query.filter(Segment.country == "Solomon Islands")
        else:
            segments_query = segments_query.filter(Segment.country == country_filter)
    # Do not sort by "total_efforts" here because it is computed.
    if sort_by == "distance":
        segments_query = segments_query.order_by(getattr(Segment, "distance").asc() 
                                                  if sort_order=="asc" else getattr(Segment, "distance").desc())
    segments = segments_query.all()

    # Generate list of countries for drop-down; filter out None values
    all_countries = { (seg.country if seg.country!="Solomon Islands" else "Watopia") 
                      for seg in Segment.query.with_entities(Segment.country).all() 
                      if seg.country is not None }
    available_countries = sorted(all_countries)

    segment_data = []
    for seg in segments:
        efforts = seg.efforts  # using backref from SegmentEffort
        total_efforts = len(efforts)
        if total_efforts > 0:
            best_effort = max(efforts, key=lambda e: e.average_watts or 0)
            fastest_effort = min(efforts, key=lambda e: e.elapsed_time or float('inf'))
        else:
            best_effort = None
            fastest_effort = None

        country = seg.country if seg.country != "Solomon Islands" else "Watopia"
        distance_miles = seg.distance * 0.000621371 if seg.distance else 0
        fastest_hhmm = ""
        if fastest_effort and fastest_effort.elapsed_time:
            fastest_hhmm = f"{fastest_effort.elapsed_time // 3600}:{(fastest_effort.elapsed_time % 3600) // 60:02d}"

        segment_data.append({
            "id": seg.id,
            "strava_id": seg.strava_id,  # Newly added Strava segment ID
            "country": country,
            "name": seg.name,
            "climb_category": seg.climb_category,
            "distance": distance_miles,
            "average_grade": seg.average_grade,
            "total_efforts": total_efforts,
            "best_power": best_effort.average_watts if best_effort else None,
            "best_power_date": best_effort.start_date if best_effort else None,
            "fastest_hhmm": fastest_hhmm,
            "fastest_effort_power": fastest_effort.average_watts if fastest_effort else None,
            "fastest_effort_date": fastest_effort.start_date if fastest_effort else None,
            "favorite": seg.favorite
        })
    # Manually sort segment_data if needed
    if sort_by in ["distance", "total_efforts"]:
        segment_data = sorted(segment_data,
                              key=lambda s: s.get(sort_by) or 0,
                              reverse=(sort_order=="desc"))
    return render_template("main/my_segments.html", segments=segment_data, search=search,
                           only_favorites=only_favorites, country=country_filter,
                           sort_by=sort_by, sort_order=sort_order, available_countries=available_countries)

@main_bp.route("/heart_rate_graph", methods=["GET"])
@login_required
def heart_rate_graph():
    """Generate a graph of maximum heart rate over time using the highest value in 6-month windows."""
    
    # Get selected date range from the form (default: 1 year)
    date_range = request.args.get("date_range", "1y")
    
    # Import the SegmentEffort model
    from ..models import SegmentEffort
    import json
    import os
    
    # Load exclusion list if file exists
    exclusion_file = os.path.join(current_app.root_path, '..', 'config', 'hr_exclusions.json')
    excluded_activities = []
    
    try:
        if os.path.exists(exclusion_file):
            with open(exclusion_file, 'r') as f:
                exclusion_data = json.load(f)
                excluded_activities = [entry["id"] for entry in exclusion_data.get("excluded_activities", [])]
                print(f"Loaded {len(excluded_activities)} excluded activities")
    except Exception as e:
        print(f"Error loading HR exclusions: {str(e)}")

    # print the activities that are excluded
    print(f"🔍 Excluded activities: {excluded_activities}" )
    
    # Query segment efforts with filtering
    today = date.today()
    query = SegmentEffort.query.filter(SegmentEffort.max_heartrate.isnot(None))
    
    # Apply exclusions if any were loaded - filter by activity_id instead of segment effort id
    print(f"🔍 Found {query.count()} segment efforts in the database")
    if excluded_activities:
        query = query.filter(~SegmentEffort.activity_id.in_(excluded_activities))
    print(f"🔍 After filtering excluded activities, found {query.count()} segment efforts")
    
    query = query.order_by(SegmentEffort.start_date)
    
    if date_range == "6m":
        cutoff_date = today - timedelta(days=180)
    elif date_range == "1y":
        cutoff_date = today - timedelta(days=365)
    elif date_range == "2y":
        cutoff_date = today - timedelta(days=730)
    else:
        cutoff_date = None  # No filter, show all data
    
    if cutoff_date:
        query = query.filter(SegmentEffort.start_date >= cutoff_date)
    
    segment_efforts = query.all()
    
    if not segment_efforts:
        return "<p>No segment efforts found with heart rate data for the selected period.</p>"
    
    # Create a DataFrame for heart rate data
    df = pd.DataFrame(
        [(effort.start_date.date(), effort.max_heartrate, effort.segment.name if effort.segment else "Unknown Segment") 
         for effort in segment_efforts if effort.max_heartrate],
        columns=["date", "max_hr", "segment_name"]
    )
    
    # Sort by date
    df = df.sort_values("date")
    
    # Find the start and end dates for the entire period
    start_date = df["date"].min()
    end_date = df["date"].max()
    
    # Create 6-month windows (approximately 180 days)
    window_size = 180  # days (changed from 30 to 180)
    current_date = start_date
    max_hr_data = []
    
    while current_date <= end_date:
        window_end = current_date + timedelta(days=window_size)
        
        # Get data points in this window
        mask = (df["date"] >= current_date) & (df["date"] < window_end)
        window_data = df[mask]
        
        if not window_data.empty:
            # Find the highest heart rate in this window
            max_hr_index = window_data["max_hr"].idxmax()
            max_hr_date = window_data.loc[max_hr_index, "date"]
            max_hr_value = window_data.loc[max_hr_index, "max_hr"]
            segment_name = window_data.loc[max_hr_index, "segment_name"]
            
            # Format the date as a string for display
            formatted_date = max_hr_date.strftime("%Y-%m-%d")
            
            max_hr_data.append({
                "date": max_hr_date,
                "max_hr": max_hr_value,
                "formatted_date": formatted_date,
                "segment_name": segment_name
            })
        
        # Move to the next window
        current_date = window_end
    
    # Create a new DataFrame with only the maximum values for each window
    df_max = pd.DataFrame(max_hr_data)
    
    if df_max.empty:
        return "<p>No maximum heart rate data could be calculated for the selected period.</p>"
    
    # Calculate the rolling average (optional, but can help show trend)
    # Using a window of 2 since we're now using 6-month windows for the data points
    if len(df_max) >= 2:
        df_max['trend_line'] = df_max['max_hr'].rolling(window=2, min_periods=1).mean()
    else:
        df_max['trend_line'] = df_max['max_hr']
    
    # Create the Plotly figure
    fig = go.Figure()
    
    # Add the maximum heart rate points with custom hover template
    fig.add_trace(go.Scatter(
        x=df_max["date"], 
        y=df_max["max_hr"], 
        mode="markers+lines",
        name="Max Heart Rate (6-month window)",
        text=[f"Date: {row['formatted_date']}<br>Max HR: {row['max_hr']}<br>Segment: {row['segment_name']}" 
              for _, row in df_max.iterrows()],
        hoverinfo="text+name",
        line=dict(color="red", width=1),
        marker=dict(size=8, symbol="circle")
    ))
    
    # Add the trend line
    fig.add_trace(go.Scatter(
        x=df_max["date"],
        y=df_max["trend_line"],
        mode="lines",
        name="Trend",
        line=dict(color="blue", width=2)
    ))
    
    # Add annotations for all points as there will be fewer with 6-month windows
    for i, row in df_max.iterrows():
        fig.add_annotation(
            x=row["date"],
            y=row["max_hr"],
            text=f"{row['max_hr']} bpm<br>{row['formatted_date']}",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        )
    
    fig.update_layout(
        title="Maximum Heart Rate Over Time (Highest in 6-month Windows)",
        xaxis_title="Date",
        yaxis_title="Heart Rate (bpm)",
        hovermode="closest",
        height=600,
        template="plotly_white"
    )
    
    graph_html = fig.to_html(full_html=False)
    return render_template("main/heart_rate_graph.html", graph_html=graph_html, date_range=date_range)

