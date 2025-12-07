#!/usr/bin/env python
# coding: utf-8

"""Dash app: Visualizing Missing Migrants Project data (optimized for Dash 3.x and Python 3.12).

Changes from original:
- One-time preprocessing of CSV (dates, totals, dtypes).
- Centralized filtering logic.
- Single dcc.Store to share filtered data across callbacks.
- Modern @callback pattern (no @app.callback).
- Light in-memory caching of filtered results with functools.lru_cache.
"""

import numpy as np
import pandas as pd
import plotly.express as px
from statsmodels.tsa.seasonal import seasonal_decompose

from functools import lru_cache

from dash import Dash, callback, dash_table, dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# ------------------------------------------------------------
# A. Load and preprocess data once at startup
# ------------------------------------------------------------

# Preprocessed CSV from MM_Cleaner must be in the same directory
MM = pd.read_csv("MM_Cleaned_27.csv")

# Ensure date column is parsed
if "Reported_Date" in MM.columns:
    MM["Reported_Date"] = pd.to_datetime(MM["Reported_Date"], errors="coerce")

# Ensure numeric columns are numeric
for col in ["Number_Dead", "Minimum_Missing"]:
    if col in MM.columns:
        MM[col] = pd.to_numeric(MM[col], errors="coerce").fillna(0).astype("int64")

# Compute total dead + missing (overwrite or create)
if {"Number_Dead", "Minimum_Missing"}.issubset(MM.columns):
    MM["Total_Dead_and_Missing"] = (
        MM["Number_Dead"].fillna(0).astype("int64")
        + MM["Minimum_Missing"].fillna(0).astype("int64")
    )

# Cast some high-cardinality text columns to category for faster filtering
for col in ["Region", "Country", "Migration_Route"]:
    if col in MM.columns:
        MM[col] = MM[col].astype("category")

# Reported year as integer (where present)
if "Reported_Year" in MM.columns:
    MM["Reported_Year"] = pd.to_numeric(MM["Reported_Year"], errors="coerce").astype("Int64")

# ------------------------------------------------------------
# B. Dropdown option lists (built once)
# ------------------------------------------------------------
from operator import itemgetter

# Region options
if "Region" in MM.columns:
    col_options_Region = [dict(label=x, value=x) for x in MM["Region"].dropna().unique()]
    col_options_Region = sorted(col_options_Region, key=itemgetter("label"))
else:
    col_options_Region = []
col_options_Region.insert(0, {"label": "All", "value": "All"})

# Year options
if "Reported_Year" in MM.columns:
    years = sorted(MM["Reported_Year"].dropna().unique())
    col_options_Year = [dict(label=int(x), value=int(x)) for x in years]
else:
    col_options_Year = []
col_options_Year.insert(0, {"label": "All", "value": "All"})

# Cause of death options: same slice as original (cols 23:30)
if MM.shape[1] >= 30:
    COD_COLUMNS = list(MM.columns[23:30])
else:
    COD_COLUMNS = []
col_options_COD = [dict(label=x, value=x) for x in sorted(COD_COLUMNS)]
col_options_COD.insert(0, {"label": "All", "value": "All"})

# Country options
if "Country" in MM.columns:
    col_options_Country = [dict(label=x, value=x) for x in MM["Country"].dropna().unique()]
    col_options_Country = sorted(col_options_Country, key=itemgetter("label"))
else:
    col_options_Country = []
col_options_Country.insert(0, {"label": "All", "value": "All"})

# Migration route options
if "Migration_Route" in MM.columns:
    col_options_Route = [dict(label=x, value=x) for x in MM["Migration_Route"].dropna().unique()]
    col_options_Route = sorted(col_options_Route, key=itemgetter("label"))
else:
    col_options_Route = []
col_options_Route.insert(0, {"label": "All", "value": "All"})

# ------------------------------------------------------------
# C. Dash app and layout
# ------------------------------------------------------------

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[{
        "name": "viewport",
        "content": "width-device-width, initial-scale=1.0",
    }],
)
server = app.server

app.layout = dbc.Container(
    [
        # Store for filtered data
        dcc.Store(id="store-data", data=[]),

        # Title and source
        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "Visualizing Missing Migrants",
                        className="text-primary, mb-4",
                        style={"color": "#0099C6", "text-align": "center"},
                    ),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=12,
                )
            ],
            justify="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        "Dashboard generated using data from the Missing Migrants Project.",
                        style={"text-align": "center"},
                    ),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=12,
                ),
            ],
            justify="center",
        ),
        dbc.Row([dbc.Col(html.Br())]),

        # Summary text
        dbc.Row(
            [
                dbc.Col(
                    html.H5(
                        id="text1",
                        children="Choose filters to view summary statistics.",
                        style={"text-align": "center"},
                    ),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=12,
                )
            ]
        ),
        dbc.Row([dbc.Col(html.Br())]),

        # Dropdown menus
        dbc.Row(
            children=[
                dbc.Col(
                    [
                        html.H4("Year"),
                        dcc.Dropdown(
                            id="Reported_Year",
                            value="All",
                            options=col_options_Year,
                            clearable=False,
                        ),
                    ],
                    xs=4,
                    sm=4,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.H4("Region of Incident"),
                        dcc.Dropdown(
                            id="Region",
                            value="All",
                            options=col_options_Region,
                            clearable=False,
                        ),
                    ],
                    xs=4,
                    sm=4,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.H4("Migration Route"),
                        dcc.Dropdown(
                            id="Migration_Route",
                            value="All",
                            options=col_options_Route,
                            clearable=False,
                        ),
                    ],
                    xs=4,
                    sm=4,
                    md=4,
                    lg=4,
                    xl=4,
                ),
            ],
            justify="around",
        ),
        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row(
            children=[
                dbc.Col(
                    [
                        html.H4("Country of Incident"),
                        dcc.Dropdown(
                            id="Country",
                            value="All",
                            options=col_options_Country,
                            clearable=False,
                        ),
                    ],
                    xs=4,
                    sm=4,
                    md=4,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(
                    [
                        html.H4("Cause of Death"),
                        dcc.Dropdown(
                            id="COD",
                            value="All",
                            options=col_options_COD,
                            clearable=False,
                        ),
                    ],
                    xs=4,
                    sm=4,
                    md=4,
                    lg=4,
                    xl=4,
                ),
            ],
            justify="around",
        ),

        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        "Click on a point for a link to the Missing Migrants Project page.",
                        style={"text-align": "center", "color": "#808080"},
                    ),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=12,
                ),
            ],
            justify="center",
        ),
        dbc.Row([dbc.Col(html.Br())]),

        # Map
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="fig1", figure={}),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=12,
                )
            ],
            justify="center",
        ),

        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row([dbc.Col(html.Br())]),

        # Bar charts with year and month
        dbc.Row(
            children=[
                dbc.Col(
                    [
                        html.H3("Dead and Missing Migrants by Year"),
                        dcc.Graph(id="fig2", figure={}),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=6,
                ),
                dbc.Col(
                    [
                        html.H3("Dead and Missing Migrants by Month"),
                        dcc.Graph(id="fig3", figure={}),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=6,
                ),
            ],
            justify="around",
        ),

        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row([dbc.Col(html.Br())]),

        # Graphs with Cause of Death and region
        dbc.Row(
            children=[
                dbc.Col(
                    [
                        html.H3("Incident Count by Cause of Death"),
                        dcc.Graph(id="fig4", figure={}),
                        html.Div(
                            "A single incident can present more than one cause of death.",
                            style={"text-align": "center", "color": "#808080"},
                        ),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=6,
                ),
                dbc.Col(
                    [
                        html.H3("Share of Deaths and Disappearances by Region"),
                        dcc.Graph(id="fig5", figure={}),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=6,
                ),
            ],
            justify="around",
        ),

        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row([dbc.Col(html.Br())]),

        # Country treemap and sex/age pies
        dbc.Row(
            children=[
                dbc.Col(
                    [
                        html.H3("Share of Deaths and Disappearances by Country"),
                        dcc.Graph(id="fig6", figure={}),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=6,
                ),
                dbc.Col(
                    [
                        html.H3("Sex of Missing Migrants"),
                        dcc.Graph(id="fig7", figure={}),
                        html.H3("Age of Missing Migrants"),
                        dcc.Graph(id="fig8", figure={}),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=6,
                ),
            ],
            justify="around",
        ),

        dbc.Row([dbc.Col(html.Br())]),
        dbc.Row([dbc.Col(html.Br())]),

        # Seasonal decomposition
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3(
                            "Seasonality of Dead and Missing Migrants by Month (Seasonal Component)"
                        ),
                        dcc.Graph(id="fig9", figure={}),
                    ],
                    xs=12,
                    sm=12,
                    md=12,
                    lg=12,
                    xl=12,
                )
            ],
            justify="center",
        ),

        # Download button
        dbc.Row(
            [
                html.Button("Download Selected Data", id="btn"),
                dcc.Download(id="download_csv"),
            ],
            justify="center",
        ),

        dbc.Row([dbc.Col(html.Br())]),
    ],
    fluid=True,
)

# ------------------------------------------------------------
# D. Filtering logic with light caching
# ------------------------------------------------------------

@lru_cache(maxsize=128)
def _filter_mm_data_cached(reported_year, region, country, cod, migration_route):
    """Return a list-of-dicts of filtered rows (cached)."""
    df = MM

    # Build a boolean mask
    mask = pd.Series(True, index=df.index)

    if reported_year not in (None, "All"):
        mask &= df["Reported_Year"] == int(reported_year)

    if region not in (None, "All"):
        mask &= df["Region"] == region

    if country not in (None, "All"):
        mask &= df["Country"] == country

    if migration_route not in (None, "All"):
        mask &= df["Migration_Route"] == migration_route

    if cod not in (None, "All") and cod in COD_COLUMNS:
        mask &= df[cod] == 1

    filtered = df.loc[mask]

    # Return JSON-serializable structure (and allow caching)
    return tuple(filtered.to_dict("records"))

# ------------------------------------------------------------
# E. Callbacks
# ------------------------------------------------------------

# E.1 Store filtered data
@callback(
    Output("store-data", "data"),
    Input("Reported_Year", "value"),
    Input("Region", "value"),
    Input("Country", "value"),
    Input("COD", "value"),
    Input("Migration_Route", "value"),
)
def update_store(reported_year, region, country, cod, migration_route):
    records = _filter_mm_data_cached(
        reported_year or "All",
        region or "All",
        country or "All",
        cod or "All",
        migration_route or "All",
    )
    # Convert cached tuple back to list for dcc.Store
    return list(records)

# E.2 Summary text
@callback(
    Output("text1", "children"),
    Input("store-data", "data"),
)
def update_summary(data):
    if not data:
        return "No incidents found for the selected filters."

    try:
        df = pd.DataFrame(data)
        incidents = df["Incident_ID"].nunique() if "Incident_ID" in df.columns else len(df)
        dead_and_missing = int(df["Total_Dead_and_Missing"].sum())
        return (
            f"There are {incidents} incidents that correspond to the selected filters. "
            f"In total, {dead_and_missing} migrants were reported as dead or missing."
        )
    except Exception:
        return "No content."

# E.3 Map
@callback(
    Output("fig1", "figure"),
    Input("store-data", "data"),
)
def update_map(data):
    if not data:
        return px.scatter_mapbox().update_layout(
            mapbox_style="open-street-map",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)

    # Require coordinates
    if not {"Latitude", "Longitude"}.issubset(df.columns):
        return px.scatter_mapbox().update_layout(
            mapbox_style="open-street-map",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        hover_data={
            "Total_Dead_and_Missing": True,
            "Number_Dead": True if "Number_Dead" in df.columns else False,
            "Minimum_Missing": True if "Minimum_Missing" in df.columns else False,
            "Reported_Year": True if "Reported_Year" in df.columns else False,
        },
        custom_data=["URL1"] if "URL1" in df.columns else None,
        mapbox_style="open-street-map",
        zoom=3,
        opacity=0.5,
        height=1000,
        width=1750,
        color="Migration_Route" if "Migration_Route" in df.columns else None,
        color_discrete_sequence=[
            "black",
            "brown",
            "red",
            "firebrick",
            "darkslateblue",
            "darkgreen",
            "maroon",
            "navy",
            "thistle",
            "forestgreen",
            "midnightblue",
            "darkorange",
            "orangered",
        ],
    )

    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01, title=""),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig

# E.4 Dead and missing by year
@callback(
    Output("fig2", "figure"),
    Input("store-data", "data"),
)
def update_yearly_chart(data):
    if not data:
        return px.bar().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    if "Reported_Year" not in df.columns:
        return px.bar().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    grouped = (
        df.groupby("Reported_Year", as_index=False)[["Number_Dead", "Minimum_Missing"]]
        .sum()
        .sort_values("Reported_Year")
    )

    fig = px.bar(
        grouped,
        x="Reported_Year",
        y=["Number_Dead", "Minimum_Missing"],
        height=500,
        width=750,
        barmode="group",
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        xaxis_title="Year",
        yaxis_title="Number of Migrants",
        xaxis_tickangle=-90,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, title=""),
    )
    return fig

# E.5 Dead and missing by month
@callback(
    Output("fig3", "figure"),
    Input("store-data", "data"),
)
def update_monthly_chart(data):
    if not data:
        return px.bar().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    if "Reported_Date" not in df.columns:
        return px.bar().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df["Reported_Date"] = pd.to_datetime(df["Reported_Date"], errors="coerce")
    mm_date = df.set_index("Reported_Date").sort_index()
    mm_month = mm_date.resample("M")[["Number_Dead", "Minimum_Missing"]].sum()

    fig = px.bar(
        mm_month,
        y=["Number_Dead", "Minimum_Missing"],
        height=500,
        width=750,
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        xaxis_tickangle=-90,
        xaxis_title="Date",
        yaxis_title="Number of Migrants",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, title=""),
    )
    return fig

# E.6 Incident count by cause of death (bar)
@callback(
    Output("fig4", "figure"),
    Input("store-data", "data"),
)
def update_cod_bar(data):
    if not data:
        return px.bar().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)

    needed_cols = [
        "Other Accidents",
        "Drowning",
        "Lack of Shelter, Food, or Water",
        "Mixed or unknown",
        "Sickness",
        "Transportation Accident",
    ]
    existing_cols = [c for c in needed_cols if c in df.columns]
    if not existing_cols:
        return px.bar().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    COD_df = df[existing_cols].sum().to_frame().reset_index()
    COD_df.columns = ["COD_category", "Incident_Count"]
    COD_df = COD_df.sort_values(by="Incident_Count", ascending=True)

    fig = px.bar(
        COD_df,
        y="COD_category",
        x="Incident_Count",
        height=500,
        width=750,
        orientation="h",
        color="Incident_Count",
        color_continuous_scale="YlOrRd",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    return fig

# E.7 Region shares (pie)
@callback(
    Output("fig5", "figure"),
    Input("store-data", "data"),
)
def update_region_pie(data):
    if not data:
        return px.pie().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    if not {"Region", "Total_Dead_and_Missing"}.issubset(df.columns):
        return px.pie().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    fig = px.pie(
        df,
        values="Total_Dead_and_Missing",
        names="Region",
        height=500,
        width=750,
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    return fig

# E.8 Country treemap
@callback(
    Output("fig6", "figure"),
    Input("store-data", "data"),
)
def update_country_treemap(data):
    if not data:
        return px.treemap().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    if not {"Country", "Total_Dead_and_Missing"}.issubset(df.columns):
        return px.treemap().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    Country_df = (
        df[["Country", "Total_Dead_and_Missing"]]
        .groupby("Country", as_index=False)
        .sum()
    )

    fig = px.treemap(
        Country_df,
        path=["Country"],
        values="Total_Dead_and_Missing",
        height=500,
        width=1500,
        color="Total_Dead_and_Missing",
        color_continuous_scale="YlOrRd",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    return fig

# E.9 Sex pie
@callback(
    Output("fig7", "figure"),
    Input("store-data", "data"),
)
def update_sex_pie(data):
    if not data:
        return px.pie().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    cols = [c for c in ["Females", "Males", "Unknown_Sex"] if c in df.columns]
    if not cols:
        return px.pie().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    Sex_df = df[cols].sum().to_frame().reset_index()
    Sex_df.columns = ["Sex", "Total_Dead_and_Missing"]

    fig = px.pie(
        Sex_df,
        values="Total_Dead_and_Missing",
        names="Sex",
        height=500,
        width=750,
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    return fig

# E.10 Age pie
@callback(
    Output("fig8", "figure"),
    Input("store-data", "data"),
)
def update_age_pie(data):
    if not data:
        return px.pie().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    cols = [c for c in ["Confirmed_Adults", "Children", "Unknown_Age_Status"] if c in df.columns]
    if not cols:
        return px.pie().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    Age_df = df[cols].sum().to_frame().reset_index()
    Age_df.columns = ["Age_Status", "Total_Dead_and_Missing"]

    fig = px.pie(
        Age_df,
        values="Total_Dead_and_Missing",
        names="Age_Status",
        height=500,
        width=750,
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    return fig

# E.11 Seasonal decomposition plot (seasonal component)
@callback(
    Output("fig9", "figure"),
    Input("store-data", "data"),
)
def update_seasonal_decomposition(data):
    if not data:
        return px.line().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df = pd.DataFrame(data)
    if "Reported_Date" not in df.columns or "Total_Dead_and_Missing" not in df.columns:
        return px.line().update_layout(
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

    df["Reported_Date"] = pd.to_datetime(df["Reported_Date"], errors="coerce")
    mm_date = df.set_index("Reported_Date").sort_index()
    mm_month = mm_date.resample("M")["Total_Dead_and_Missing"].sum()
    mm_month.index.freq = "M"

    # statsmodels seasonal decomposition
    result = seasonal_decompose(mm_month, model="add")

    fig = px.line(result.seasonal)
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    return fig

# E.12 Download selected data as CSV
@callback(
    Output("download_csv", "data"),
    Input("btn", "n_clicks"),
    Input("store-data", "data"),
    prevent_initial_call=True,
)
def download_csv(n_clicks, data):
    if n_clicks is None:
        raise PreventUpdate

    # Only respond when the button is the trigger
    if ctx.triggered_id != "btn":
        raise PreventUpdate

    df = pd.DataFrame(data)
    return dict(content=df.to_csv(index=False), filename="Missing_Migrants.csv")

# ------------------------------------------------------------
# F. Run app
# ------------------------------------------------------------

if __name__ == "__main__":
    app.run_server(debug=False)
