
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# --------------------------------------------------
# 1. Find and load the dataset
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent

possible_files = [
    PROJECT_DIR / "data" / "dataset_part_1.csv",
    PROJECT_DIR / "data" / "spacex_launches_clean.csv",
    PROJECT_DIR / "data" / "spacex_launches_raw.csv",
]

DATA_FILE = next((p for p in possible_files if p.exists()), None)

if DATA_FILE is None:
    raise FileNotFoundError(
        "Dataset not found. Place dataset_part_1.csv in "
        "SpaceX_Capstone/data/ and run the app again."
    )

df = pd.read_csv(DATA_FILE)

# --------------------------------------------------
# 2. Validate and prepare the data
# --------------------------------------------------
required_columns = [
    "LaunchSite", "Outcome", "PayloadMass", "FlightNumber"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}. "
        f"Available columns: {df.columns.tolist()}"
    )

df["PayloadMass"] = pd.to_numeric(
    df["PayloadMass"], errors="coerce"
)

df["FlightNumber"] = pd.to_numeric(
    df["FlightNumber"], errors="coerce"
)

df["Outcome"] = df["Outcome"].fillna("Unknown").astype(str)
df["LaunchSite"] = df["LaunchSite"].fillna("Unknown").astype(str)

# The standard IBM dataset uses labels such as True ASDS
# for successful landing outcomes.
df["LandingSuccess"] = df["Outcome"].str.startswith("True")
df["LandingResult"] = df["LandingSuccess"].map({
    True: "Successful landing",
    False: "Unsuccessful / other outcome"
})

# --------------------------------------------------
# 3. Create the Dash application
# --------------------------------------------------
app = Dash(__name__)
app.title = "SpaceX Launch Analytics"

launch_sites = sorted(df["LaunchSite"].unique())

app.layout = html.Div(
    style={
        "fontFamily": "Arial",
        "margin": "25px",
        "maxWidth": "1200px"
    },
    children=[
        html.H1(
            "SpaceX Falcon 9 Launch Analytics",
            style={"textAlign": "center"}
        ),

        html.P(
            f"Dataset: {DATA_FILE.name} | "
            f"Records: {len(df)}",
            style={"textAlign": "center"}
        ),

        html.Label(
            "Select Launch Site:",
            style={"fontWeight": "bold"}
        ),

        dcc.Dropdown(
            id="site-dropdown",
            options=[
                {"label": "All Launch Sites", "value": "ALL"}
            ] + [
                {"label": site, "value": site}
                for site in launch_sites
            ],
            value="ALL",
            clearable=False
        ),

        html.H2("Landing Outcome Distribution"),
        dcc.Graph(id="success-pie"),

        html.H2("Payload Mass vs Flight Number"),
        dcc.Graph(id="payload-scatter"),

        html.H2("Landing Success by Launch Site"),
        dcc.Graph(id="site-success-chart"),
    ]
)

# --------------------------------------------------
# 4. Update all charts when a site is selected
# --------------------------------------------------
@app.callback(
    Output("success-pie", "figure"),
    Output("payload-scatter", "figure"),
    Output("site-success-chart", "figure"),
    Input("site-dropdown", "value")
)
def update_dashboard(selected_site):
    filtered = df.copy()

    if selected_site != "ALL":
        filtered = filtered[
            filtered["LaunchSite"] == selected_site
        ]

    # Pie chart: landing outcome distribution
    outcome_counts = (
        filtered["LandingResult"]
        .value_counts()
        .rename_axis("LandingResult")
        .reset_index(name="Launches")
    )

    pie_fig = px.pie(
        outcome_counts,
        names="LandingResult",
        values="Launches",
        title="Landing Outcomes",
        hole=0.35
    )

    # Scatter plot: payload mass vs flight number
    scatter_data = filtered.dropna(
        subset=["PayloadMass", "FlightNumber"]
    )

    scatter_fig = px.scatter(
        scatter_data,
        x="PayloadMass",
        y="FlightNumber",
        color="LandingResult",
        hover_data=["LaunchSite", "Outcome"],
        title="Payload Mass vs Flight Number",
        labels={
            "PayloadMass": "Payload Mass (kg)",
            "FlightNumber": "Flight Number",
            "LandingResult": "Landing Result"
        }
    )

    # Bar chart: successful vs other outcomes by site
    site_summary = (
        filtered.groupby(["LaunchSite", "LandingResult"])
        .size()
        .reset_index(name="Launches")
    )

    site_fig = px.bar(
        site_summary,
        x="LaunchSite",
        y="Launches",
        color="LandingResult",
        barmode="group",
        title="Landing Outcomes by Launch Site"
    )

    return pie_fig, scatter_fig, site_fig


# --------------------------------------------------
# 5. Run the local dashboard
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
