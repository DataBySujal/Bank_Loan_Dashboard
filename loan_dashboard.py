# loan_dashboard.py
import pandas as pd
import numpy as np
import datetime as dt
import os
import urllib.parse

from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context, no_update
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# ---------- Config ----------
# Default to a CSV file located next to this script (workspace root).
# Change this if your CSV lives elsewhere.
CSV_PATH = os.path.join(os.path.dirname(__file__), "financial_loan.csv")
# ---------- Load & prepare data ----------
if not os.path.exists(CSV_PATH):
    raise SystemExit(f"Missing required data file: {CSV_PATH}\nPlease place financial_loan.csv next to loan_dashboard.py")
try:
    df = pd.read_csv(CSV_PATH)
except Exception as e:
    raise SystemExit(f"Failed to read CSV file {CSV_PATH}: {e}")

# Convert dates
for col in ["issue_date", "last_payment_date", "last_credit_pull_date", "next_payment_date"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# Create a month column for MTD/MOM-like metrics
if "issue_date" in df.columns:
    df["issue_month"] = df["issue_date"].dt.to_period("M").dt.to_timestamp()
else:
    df["issue_month"] = pd.NaT

# Normalize loan_status into 'Good' and 'Bad' categories
# Adjust mapping to your real values if different
good_statuses = {"Fully Paid", "Current", "Issued", "In Grace Period"}  # adjust if needed
def classify(status):
    try:
        if pd.isna(status):
            return "Unknown"
        s = str(status).strip()
        return "Good" if s in good_statuses else "Bad"
    except:
        return "Unknown"

if "loan_status" in df.columns:
    df["loan_quality"] = df["loan_status"].apply(classify)
else:
    # If loan_status missing, create a default Unknown column so downstream code doesn't fail
    df["loan_quality"] = "Unknown"

# Some numeric columns might be strings; coerce
for col in ["loan_amount", "total_payment", "int_rate", "dti", "installment", "annual_income"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ---------- Helper aggregations ----------
def compute_kpis(filtered_df):
    """Return dictionary of KPI values."""
    total_apps = int(filtered_df["id"].nunique()) if "id" in filtered_df.columns else len(filtered_df)
    total_funded = float(filtered_df["loan_amount"].sum()) if "loan_amount" in filtered_df.columns else 0.0
    total_received = float(filtered_df["total_payment"].sum()) if "total_payment" in filtered_df.columns else 0.0
    avg_int_rate = float(filtered_df["int_rate"].mean()) if "int_rate" in filtered_df.columns else np.nan
    avg_dti = float(filtered_df["dti"].mean()) if "dti" in filtered_df.columns else np.nan

    return {
        "total_apps": total_apps,
        "total_funded": total_funded,
        "total_received": total_received,
        "avg_int_rate": avg_int_rate,
        "avg_dti": avg_dti,
    }

# ---------- App layout ----------
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  # dark theme like PowerBI
server = app.server

# Note: Dash will automatically serve static files from an `assets/` folder next to this script.
# If you want to use custom images, create an `assets/` folder and place images there.
# If no local assets are found, we fall back to simple placeholder/clip-art style images
# served from a public placeholder image service so the dashboard looks presentable.

# Determine image sources: prefer local assets if present, otherwise use placeholder URLs.
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
def asset_src(name, fallback_url):
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path):
        return f"/assets/{name}"
    return fallback_url

def svg_data_uri(svg_text: str) -> str:
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg_text)

# Simple inline SVG fallbacks (guaranteed to render without external requests)
HEADER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="80">
    <rect width="100%" height="100%" fill="#0b2239"/>
    <text x="70" y="52" font-family="Arial, Helvetica, sans-serif" font-size="28" fill="#ffcc80">Finance Dashboard</text>
</svg>
"""
LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="70">
    <rect width="100%" height="100%" fill="#14384a"/>
    <text x="10" y="44" font-family="Arial, Helvetica, sans-serif" font-size="20" fill="white">B
    
    ANK</text>
</svg>
"""
BANNER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="60">
    <rect width="100%" height="100%" fill="#07101a"/>
    <text x="130" y="44" font-family="Arial, Helvetica, sans-serif" font-size="18" fill="#9fd3ff">Powered by Loan Analytics</text>
</svg>
"""
SUMMARY_BANNER_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="70">
    <rect width="100%" height="100%" fill="#051826"/>
    <text x="70" y="44" font-family="Arial, Helvetica, sans-serif" font-size="20" fill="#ffcc80">SUMMARY</text>
</svg>
"""

HEADER_SRC = asset_src("header.png", svg_data_uri(HEADER_SVG))
LOGO_SRC = asset_src("logo.png", svg_data_uri(LOGO_SVG))
BANNER_SRC = asset_src("banner.png", svg_data_uri(BANNER_SVG))
SUMMARY_BANNER_SRC = asset_src("summary_banner.png", svg_data_uri(SUMMARY_BANNER_SVG))

# Additional inline SVG clip-art style icons (bank, building, loan envelope, good-vs-bad, details)
ICON_BANK_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' width='64' height='64'>
    <rect width='100%' height='100%' fill='none' />
    <polygon points='32 8 4 24 60 24' fill='#0b2239'/>
    <rect x='12' y='26' width='40' height='28' fill='#14384a'/>
    <circle cx='32' cy='40' r='6' fill='#ffcc80'/>
</svg>
"""
ICON_BUILDING_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' width='64' height='64'>
    <rect width='100%' height='100%' fill='none' />
    <rect x='8' y='20' width='48' height='32' fill='#ffd27f'/>
    <polygon points='32 6 6 18 58 18' fill='#f0b350'/>
    <rect x='18' y='28' width='8' height='8' fill='#ffffff'/>
    <rect x='38' y='28' width='8' height='8' fill='#ffffff'/>
</svg>
"""
ICON_LOAN_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 80' width='120' height='80'>
    <rect width='100%' height='100%' fill='none' />
    <rect x='6' y='18' width='108' height='44' rx='6' fill='#e8f3e8'/>
    <text x='20' y='46' font-family='Arial' font-size='18' fill='#2f6f2f'>LOAN</text>
    <text x='72' y='46' font-family='Arial' font-size='16' fill='#2f6f2f'>$</text>
</svg>
"""
ICON_GOODBAD_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 60' width='120' height='60'>
    <rect width='100%' height='100%' fill='none' />
    <rect x='6' y='10' width='48' height='40' fill='#9fd3ff'/>
    <rect x='66' y='10' width='48' height='40' fill='#ffb3a7'/>
    <text x='20' y='36' font-family='Arial' font-size='12' fill='#033a5b'>GOOD</text>
    <text x='80' y='36' font-family='Arial' font-size='12' fill='#6b1a00'>BAD</text>
</svg>
"""
ICON_DETAILS_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' width='64' height='64'>
    <rect width='100%' height='100%' fill='none' />
    <circle cx='28' cy='28' r='10' fill='#cfe6ff'/>
    <rect x='36' y='36' width='16' height='6' fill='#bdbdbd' transform='rotate(20 44 39)' />
    <text x='8' y='56' font-family='Arial' font-size='10' fill='#ffffff'>DETAILS</text>
</svg>
"""

ICON_BANK_SRC = svg_data_uri(ICON_BANK_SVG)
ICON_BUILDING_SRC = svg_data_uri(ICON_BUILDING_SVG)
ICON_LOAN_SRC = svg_data_uri(ICON_LOAN_SVG)
ICON_GOODBAD_SRC = svg_data_uri(ICON_GOODBAD_SVG)
ICON_DETAILS_SRC = svg_data_uri(ICON_DETAILS_SVG)

# Create options for filters
state_options = [{"label": s, "value": s} for s in sorted(df["address_state"].dropna().unique())] if "address_state" in df.columns else []
grade_options = [{"label": g, "value": g} for g in sorted(df["grade"].dropna().unique())] if "grade" in df.columns else []
purpose_options = [{"label": p, "value": p} for p in sorted(df["purpose"].dropna().unique())] if "purpose" in df.columns else []

# Prepare month marks for a RangeSlider (if issue_month exists)
if "issue_month" in df.columns:
    months = sorted(df["issue_month"].dropna().unique())
    month_labels = [pd.to_datetime(m).strftime("%Y-%m") for m in months]
    month_marks = {i: month_labels[i] for i in range(len(month_labels)) if i % max(1, len(month_labels)//8) == 0}
    month_slider_min = 0
    month_slider_max = max(0, len(month_labels)-1)
    month_slider_value = [month_slider_min, month_slider_max]
else:
    months = []
    month_labels = []
    month_marks = {}
    month_slider_min = 0
    month_slider_max = 0
    month_slider_value = [0, 0]

# Layout components
sidebar = dbc.Card(
    [
        html.H4("Menu", className="card-title", style={"color":"white"}),
        dbc.Button("Summary", id="btn-summary", color="secondary", className="mb-2" , style={"width":"100%"}),
        dbc.Button("Overview", id="btn-overview", color="dark", className="mb-2" , style={"width":"100%"}),
        dbc.Button("Details", id="btn-details", color="dark", className="mb-2" , style={"width":"100%"}),

        html.Hr(),
        html.Label("Select Measure", style={"color":"white"}),
        dcc.Dropdown(id="measure-selector", options=[
            {"label":"Total Loan Applications","value":"total_apps"},
            {"label":"Total Funded Amount","value":"total_funded"},
            {"label":"Total Amount Received","value":"total_received"},
            {"label":"Avg Interest Rate","value":"avg_int_rate"},
        ], value="total_apps", clearable=False),

        html.Hr(),
        html.Label("State", style={"color":"white"}),
        dcc.Dropdown(options=state_options, multi=False, id="filter-state", placeholder="All", clearable=True),

        html.Br(),
        html.Label("Grade", style={"color":"white"}),
        dcc.Dropdown(options=grade_options, multi=False, id="filter-grade", placeholder="All", clearable=True),

        html.Br(),
        html.Label("Purpose", style={"color":"white"}),
        dcc.Dropdown(options=purpose_options, multi=False, id="filter-purpose", placeholder="All", clearable=True),

        html.Br(),
        html.Label("Issue Month Range", style={"color":"white"}),
        dcc.RangeSlider(
            id="filter-month-range",
            min=month_slider_min,
            max=month_slider_max,
            value=month_slider_value,
            marks={},  # remove dense date labels under the slider for clarity
            step=1,
            updatemode="mouseup",
            tooltip={"placement":"bottom", "always_visible": False},
        ),

        html.Br(), html.Br(),
        dbc.Button("Reset Filters", id="reset-filters", color="light", style={"width":"100%"}),
    ],
    body=True,
    style={"width":"300px", "backgroundColor":"#0b2239", "padding":"10px"}
)

# Main content: three page divs which we'll show/hide via a small callback
summary_div = html.Div([
    # Small banner for the Summary page
    dbc.Row([
        dbc.Col(html.Img(src=SUMMARY_BANNER_SRC, style={"width":"100%","height":"70px","objectFit":"cover"}), width=12)
    ], style={"marginBottom":"8px"}),
    html.H2(id="page-title", children="BANK LOAN REPORT | SUMMARY", style={"color":"white", "marginTop":"6px"}),
    dbc.Row(id="kpi-row", className="g-2", style={"marginTop":"6px"}),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="good-donut"), style={"padding": "4px", "backgroundColor": "transparent"}),
                style={"backgroundColor": "#ffd27f", "padding": "6px", "borderRadius": "6px"}
            ),
            width=6
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="bad-donut"), style={"padding": "4px", "backgroundColor": "transparent"}),
                style={"backgroundColor": "#ffd27f", "padding": "6px", "borderRadius": "6px"}
            ),
            width=6
        ),
    ], style={"marginTop":"6px"}),
], id="summary-div", style={"display":"block"})

overview_div = html.Div([
    # Top header with an optional banner and logo
    dbc.Row([
        # Single full-width header image (removed small right-side BANK/logo column)
        dbc.Col(html.Img(src=HEADER_SRC, style={"width":"100%", "height":"80px", "objectFit":"cover"}), width=12),
    ], style={"marginBottom":"8px"}),
    html.H2("BANK LOAN REPORT | OVERVIEW", style={"color":"white", "marginTop":"6px"}),
    # Icons row (clip-art style)
    # dbc.Row([
    #     dbc.Col(html.Img(src=ICON_BANK_SRC, style={"height":"60px"}), width=2),
    #     dbc.Col(html.Img(src=ICON_BUILDING_SRC, style={"height":"60px"}), width=2),
    #     dbc.Col(html.Img(src=ICON_LOAN_SRC, style={"height":"60px"}), width=3),
    #     dbc.Col(html.Img(src=ICON_GOODBAD_SRC, style={"height":"60px"}), width=3),
    #     dbc.Col(html.Img(src=ICON_DETAILS_SRC, style={"height":"60px"}), width=2),
    # ], style={"marginTop":"6px","marginBottom":"6px"}),
    dbc.Row([
        # make the overview chart and the map equal width so they appear the same size
        # Wrap the overview graph in a small card with a lake-orange background so
        # the plot sits on an orange rectangle (lake-orange tone used from SVGs)
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    dcc.Graph(id="overview-graph"),
                    style={"padding": "4px", "backgroundColor": "transparent"}
                ),
                style={"backgroundColor": "#ffd27f", "padding": "6px", "borderRadius": "6px"}
            ),
            width=6
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="map-graph"), style={"padding": "4px", "backgroundColor": "transparent"}),
                style={"backgroundColor": "#ffd27f", "padding": "6px", "borderRadius": "6px"}
            ),
            width=6
        ),

    ], style={"marginTop":"6px"}),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="purpose-bar"), style={"padding": "4px", "backgroundColor": "transparent"}),
                style={"backgroundColor": "#ffd27f", "padding": "6px", "borderRadius": "6px"}
            ),
            width=6
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(dcc.Graph(id="grade-pie"), style={"padding": "4px", "backgroundColor": "transparent"}),
                style={"backgroundColor": "#ffd27f", "padding": "6px", "borderRadius": "6px"}
            ),
            width=6
        ),
    ], style={"marginTop":"6px"}),
    # Decorative banner at the bottom of overview
    dbc.Row([
        dbc.Col(html.Img(src=BANNER_SRC, style={"width":"100%", "height":"60px", "objectFit":"cover"}), width=12)
    ], style={"marginTop":"8px"}),
], id="overview-div", style={"display":"none"})

details_div = html.Div([
    html.H2("BANK LOAN REPORT | DETAILS", style={"color":"white", "marginTop":"6px"}),
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id="loan-table",
            page_size=10,
            style_header={'backgroundColor': '#0b2b3b', 'color': 'white'},
            style_cell={'backgroundColor': '#051826', 'color': 'white', 'textAlign': 'left', 'minWidth':'100px'},
            style_table={'overflowX': 'auto'},
        ), width=12)
    ], style={"marginTop":"10px"})
], id="details-div", style={"display":"none"})

app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row([
            dbc.Col(sidebar, width=3),
            dbc.Col([summary_div, overview_div, details_div], width=9)
        ], style={"padding":"10px"})
    ],
    style={"backgroundColor":"#07101a", "height":"100vh"}
)

# ---------- Callbacks ----------
@app.callback(
    Output("kpi-row", "children"),
    Output("good-donut", "figure"),
    Output("bad-donut", "figure"),
    Output("overview-graph", "figure"),
    Output("map-graph", "figure"),
    Output("purpose-bar", "figure"),
    Output("grade-pie", "figure"),
    Output("loan-table", "data"),
    Output("loan-table", "columns"),
    Input("filter-state", "value"),
    Input("filter-grade", "value"),
    Input("filter-purpose", "value"),
    Input("filter-month-range", "value"),
    Input("reset-filters", "n_clicks"),
    Input("measure-selector", "value"),
)
def update_dashboard(state, grade, purpose, month_range, reset_clicks, measure):
    dff = df.copy()
    # Apply filters
    if state:
        dff = dff[dff["address_state"] == state]
    if grade:
        dff = dff[dff["grade"] == grade]
    if purpose:
        dff = dff[dff["purpose"] == purpose]
    # Filter by selected month index range if available
    if month_range and len(months) > 0:
        try:
            start_idx, end_idx = month_range
            start_month = pd.to_datetime(months[int(start_idx)])
            end_month = pd.to_datetime(months[int(end_idx)])
            dff = dff[(dff["issue_month"] >= start_month) & (dff["issue_month"] <= end_month)]
        except Exception:
            pass

    # KPIs
    kpis = compute_kpis(dff)
    # Format values for display
    total_apps = kpis["total_apps"]
    total_funded = kpis["total_funded"]
    total_received = kpis["total_received"]
    avg_int_rate = kpis["avg_int_rate"]
    avg_dti = kpis["avg_dti"]

    kpi_cards = [
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.Small("Total Loan Application", style={"color":"#ffcc80"}),
                html.H4(f"{total_apps:,}", style={"color":"white"}),
            ]),
            style={"backgroundColor":"#1f2f3f"}
        ), width=2),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.Small("Total Funded Amount", style={"color":"#ffcc80"}),
                html.H4(f"${total_funded:,.0f}", style={"color":"white"}),
            ]),
            style={"backgroundColor":"#14384a"}
        ), width=3),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.Small("Total Amount Received", style={"color":"#ffcc80"}),
                html.H4(f"${total_received:,.0f}", style={"color":"white"}),
            ]),
            style={"backgroundColor":"#14384a"}
        ), width=3),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.Small("Avg. Interest Rate", style={"color":"#ffcc80"}),
                html.H4(f"{avg_int_rate:.2f}%" if not np.isnan(avg_int_rate) else "N/A", style={"color":"white"}),
            ]),
            style={"backgroundColor":"#1f2f3f"}
        ), width=2),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.Small("Avg. DTI", style={"color":"#ffcc80"}),
                html.H4(f"{avg_dti:.2f}%" if not np.isnan(avg_dti) else "N/A", style={"color":"white"}),
            ]),
            style={"backgroundColor":"#1f2f3f"}
        ), width=2),
    ]

    # Donut charts
    quality_counts = dff["loan_quality"].value_counts(dropna=False)
    # Good donut
    good_val = int(quality_counts.get("Good", 0))
    bad_val = int(quality_counts.get("Bad", 0))
    donut_good = go.Figure(go.Pie(
        labels=["Good", "Other"],
        values=[good_val, max(0, good_val+bad_val - good_val)],  # fallback if weird
        hole=0.6,
        sort=False,
        textinfo="percent+label"
    ))
    donut_good.update_layout(title_text="GOOD LOAN ISSUED", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="white")
    # Bad donut
    donut_bad = go.Figure(go.Pie(
        labels=["Bad", "Other"],
        values=[bad_val, max(0, good_val+bad_val - bad_val)],
        hole=0.6,
        sort=False,
        textinfo="percent+label"
    ))
    donut_bad.update_layout(title_text="BAD LOAN ISSUED", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="white")

    # Overview chart (monthly sum of funded amount)
    if "issue_month" in dff.columns and "loan_amount" in dff.columns:
        overview_df = dff.dropna(subset=["issue_month"]).groupby("issue_month")["loan_amount"].sum().reset_index()
        try:
            overview_fig = px.line(overview_df, x="issue_month", y="loan_amount", title="Funded Amount by Month")
            # match the map size so both charts display equally
            overview_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=700,
                margin=dict(l=10, r=10, t=60, b=10),
            )
        except Exception:
            overview_fig = go.Figure()
    else:
        overview_fig = go.Figure()

    # Map: choropleth by state (if available)
    if "address_state" in dff.columns and "loan_amount" in dff.columns:
        try:
            # Aggregate by state and create a choropleth (shape) map for the USA.
            # This uses built-in state shapes and doesn't require mapbox tokens.
            state_df = dff.groupby("address_state").agg(total_funded=("loan_amount", "sum")).reset_index()
            map_fig = px.choropleth(
                state_df,
                locations="address_state",
                locationmode="USA-states",
                color="total_funded",
                scope="usa",
                color_continuous_scale="Viridis",
                labels={"total_funded": "Total Funded"},
                title="Funded Amount by State",
            )
            # Improve visuals and make the map large/responsive
            map_fig.update_traces(marker_line_width=0.5, marker_line_color='rgba(0,0,0,0.2)')
            map_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=700,
                margin=dict(l=10, r=10, t=60, b=10),
            )
        except Exception:
            map_fig = go.Figure()
    else:
        map_fig = go.Figure()

    # Purpose bar chart
    if "purpose" in dff.columns and "loan_amount" in dff.columns:
        try:
            purpose_df = dff.groupby("purpose").agg(total_funded=("loan_amount","sum")).reset_index().sort_values("total_funded", ascending=False).head(10)
            purpose_fig = px.bar(purpose_df, x="purpose", y="total_funded", title="Top Purposes by Funded Amount")
            purpose_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        except Exception:
            purpose_fig = go.Figure()
    else:
        purpose_fig = go.Figure()

    # Grade pie chart
    if "grade" in dff.columns:
        try:
            grade_df = dff["grade"].value_counts().reset_index()
            grade_df.columns = ["grade","count"]
            grade_fig = px.pie(grade_df, names="grade", values="count", title="Distribution by Grade")
            grade_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        except Exception:
            grade_fig = go.Figure()
    else:
        grade_fig = go.Figure()

    # Table for DETAILS page: show row-level data (limited to first 200 rows for performance)
    if len(dff) > 200:
        table_df = dff.head(200).copy()
    else:
        table_df = dff.copy()

    # Convert for DataTable (details)
    details_data = table_df.round(2).to_dict("records")
    details_columns = [{"name": c, "id": c} for c in table_df.columns]

    return kpi_cards, donut_good, donut_bad, overview_fig, map_fig, purpose_fig, grade_fig, details_data, details_columns


# ---------- Page navigation callback ----------
@app.callback(
    Output('summary-div', 'style'),
    Output('overview-div', 'style'),
    Output('details-div', 'style'),
    Output('btn-summary', 'color'),
    Output('btn-overview', 'color'),
    Output('btn-details', 'color'),
    Input('btn-summary', 'n_clicks'),
    Input('btn-overview', 'n_clicks'),
    Input('btn-details', 'n_clicks'),
)
def display_page(n_summary, n_overview, n_details):
    """Show one page div and hide the others based on which sidebar button was clicked."""
    ctx = callback_context
    # default: show summary
    summary_style = {"display": "block"}
    overview_style = {"display": "none"}
    details_style = {"display": "none"}

    # default colors
    summary_color = "secondary"
    overview_color = "dark"
    details_color = "dark"

    if not ctx.triggered:
        return summary_style, overview_style, details_style, summary_color, overview_color, details_color

    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn_id == "btn-overview":
        summary_color = "dark"
        overview_color = "secondary"
        details_color = "dark"
        return {"display": "none"}, {"display": "block"}, {"display": "none"}, summary_color, overview_color, details_color
    if btn_id == "btn-details":
        summary_color = "dark"
        overview_color = "dark"
        details_color = "secondary"
        return {"display": "none"}, {"display": "none"}, {"display": "block"}, summary_color, overview_color, details_color

    # fallback to summary
    return summary_style, overview_style, details_style, summary_color, overview_color, details_color



# ---------- Reset filters callback ----------
@app.callback(
    Output("filter-state", "value"),
    Output("filter-grade", "value"),
    Output("filter-purpose", "value"),
    Output("filter-month-range", "value"),
    Output("measure-selector", "value"),
    Input("reset-filters", "n_clicks"),
)
def reset_filters(n_clicks):
    """Reset filter controls to their defaults when Reset Filters is clicked."""
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update

    # reset to defaults: clear dropdowns (None), reset slider to full range, reset measure
    return None, None, None, [month_slider_min, month_slider_max], "total_apps"

# ---------- Run server ----------
if __name__ == "__main__":
    # `app.run_server` is obsolete in recent Dash versions; use `app.run` instead.
    app.run(debug=True, port=8050)
