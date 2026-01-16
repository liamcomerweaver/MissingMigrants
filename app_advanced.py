#!/usr/bin/env python
# coding: utf-8
"""
Missing Migrants Dashboard - Advanced Visualizations
Features: Animated maps, Sankey diagrams, stacked areas, choropleth, sunburst, heatmaps, and more
"""

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# =============================================================================
# CONFIGURATION
# =============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Colors
HIGHLIGHT_COLOR = '#0099C6'
COLOR_SCHEME = px.colors.sequential.Plasma
COLOR_CONTINUOUS = 'YlOrRd'

CHART_LAYOUT = {
    "plot_bgcolor": "rgba(0, 0, 0, 0)",
    "paper_bgcolor": "rgba(0, 0, 0, 0)",
    "font": {"size": 12}
}

# Cause of Death columns (without COD_ prefix based on standardized format)
COD_COLUMNS = [
    'Other Accidents',
    'Drowning',
    'Lack of Shelter, Food, or Water',
    'Mixed or unknown',
    'Sickness',
    'Transportation Accident',
    'Violence'
]

MONTH_ORDER = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data(filepath: str) -> pd.DataFrame:
    """Load and preprocess the dataset."""
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)

    # Parse dates
    if 'Reported_Date' in df.columns:
        df['Reported_Date'] = pd.to_datetime(df['Reported_Date'], errors='coerce')
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Ensure numeric columns
    numeric_cols = ['Total_Dead_and_Missing', 'Number_Dead', 'Minimum_Missing',
                    'Females', 'Males', 'Children', 'Unknown_Sex', 'Unknown_Age_Status',
                    'Latitude', 'Longitude', 'Log_Dead']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Add derived columns
    if 'Date' in df.columns and 'Reported_Year' not in df.columns:
        df['Reported_Year'] = df['Date'].dt.year
        df['Reported_Month'] = df['Date'].dt.month_name()

    # Create a primary COD column for easier filtering
    if all(col in df.columns for col in COD_COLUMNS):
        def get_primary_cod(row):
            for cod in COD_COLUMNS:
                if row[cod] == 1:
                    return cod
            return 'Unknown'
        df['Primary_COD'] = df.apply(get_primary_cod, axis=1)

    logger.info(f"Loaded {len(df):,} records")
    return df

# Load data - using the new standardized file
MM = load_data("MM_Dummies_CleanRefactored_Jan16.csv")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def apply_filters(df: pd.DataFrame, year, region, route) -> pd.DataFrame:
    """Apply filters to the dataframe."""
    filtered = df.copy()

    if year != "All":
        filtered = filtered[filtered["Reported_Year"] == year]
    if region != "All":
        filtered = filtered[filtered["Region"] == region]
    if route != "All":
        filtered = filtered[filtered["Migration_Route"] == route]

    return filtered

def build_dropdown_options(series, sort=True, add_all=True):
    """Build dropdown options from a pandas series."""
    unique_vals = series.dropna().unique().tolist()
    if sort:
        unique_vals = sorted(unique_vals)
    options = [{'label': str(x), 'value': x} for x in unique_vals]
    if add_all:
        options.insert(0, {'label': 'All', 'value': 'All'})
    return options

# Build dropdown options
options_year = build_dropdown_options(MM["Reported_Year"], sort=False)
options_region = build_dropdown_options(MM["Region"])
options_route = build_dropdown_options(MM["Migration_Route"])

# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],  # Dark theme for dramatic effect
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
    suppress_callback_exceptions=True
)
server = app.server

# =============================================================================
# LAYOUT
# =============================================================================
app.layout = dbc.Container([
    # Data store
    dcc.Store(id='store-data', data=[]),

    # Header
    html.Div(className="py-4"),
    dbc.Row([
        dbc.Col([
            html.H1(
                "📊 Missing Migrants: Advanced Analytics",
                className="text-center fw-bold",
                style={'color': HIGHLIGHT_COLOR, 'textShadow': '2px 2px 4px rgba(0,0,0,0.3)'}
            ),
            html.P(
                ["Enhanced visualizations powered by Plotly & Dash | ",
                 html.A("Data: IOM Missing Migrants", href="https://missingmigrants.iom.int/",
                       target="_blank", style={'color': HIGHLIGHT_COLOR})],
                className="text-center text-muted"
            )
        ], width=12)
    ]),

    html.Hr(style={'borderColor': HIGHLIGHT_COLOR}),

    # Filters
    dbc.Row([
        dbc.Col([
            html.Label("📅 Year", className="fw-bold"),
            dcc.Dropdown(id="filter-year", value="All", options=options_year,
                        clearable=False, style={'color': '#000'})
        ], xs=12, md=4, className="mb-3"),

        dbc.Col([
            html.Label("🌍 Region of Incident", className="fw-bold"),
            dcc.Dropdown(id="filter-region", value="All", options=options_region,
                        clearable=False, style={'color': '#000'})
        ], xs=12, md=4, className="mb-3"),

        dbc.Col([
            html.Label("🛤️ Migration Route", className="fw-bold"),
            dcc.Dropdown(id="filter-route", value="All", options=options_route,
                        clearable=False, style={'color': '#000'})
        ], xs=12, md=4, className="mb-3"),
    ]),

    # Summary Stats
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="summary-stats", className="text-center py-2")
                ])
            ], color="dark", outline=True, style={'borderColor': HIGHLIGHT_COLOR, 'borderWidth': '2px'})
        ], width=12)
    ], className="mb-4"),

    # Section 1: ANIMATED TIME MAP
    dbc.Row([
        dbc.Col([
            html.H3("🗺️ Animated Migration Crisis Map", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Watch how incident locations change over time", className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="animated-map", figure={},
                             config={'responsive': True}, style={'height': '600px'})
                ]
            )
        ], width=12)
    ], className="mb-5"),

    # Section 2: SANKEY DIAGRAM
    dbc.Row([
        dbc.Col([
            html.H3("🔀 Migration Flow: Origin → Incident → Outcome", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Follow the journey from origin region through incident location to cause of death",
                  className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="sankey-flow", figure={},
                             config={'responsive': True}, style={'height': '700px'})
                ]
            )
        ], width=12)
    ], className="mb-5"),

    # Section 3: STACKED AREA + CHOROPLETH
    dbc.Row([
        dbc.Col([
            html.H3("📈 Causes of Death Over Time", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Stacked area chart showing composition of causes", className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="stacked-area", figure={},
                             config={'responsive': True}, style={'height': '450px'})
                ]
            )
        ], xs=12, lg=6),

        dbc.Col([
            html.H3("🌍 Global Death Toll by Country", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Choropleth map colored by total deaths", className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="choropleth-map", figure={},
                             config={'responsive': True}, style={'height': '450px'})
                ]
            )
        ], xs=12, lg=6)
    ], className="mb-5"),

    # Section 4: SUNBURST + HEATMAP
    dbc.Row([
        dbc.Col([
            html.H3("☀️ Hierarchical Drill-Down", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Click to explore: Region → Country → Route", className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="sunburst-chart", figure={},
                             config={'responsive': True}, style={'height': '500px'})
                ]
            )
        ], xs=12, lg=6),

        dbc.Col([
            html.H3("🔥 Seasonality Heatmap", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Calendar view: Month vs Year patterns", className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="heatmap-season", figure={},
                             config={'responsive': True}, style={'height': '500px'})
                ]
            )
        ], xs=12, lg=6)
    ], className="mb-5"),

    # Section 5: BOX PLOT + BUBBLE CHART
    dbc.Row([
        dbc.Col([
            html.H3("📦 Incident Severity Distribution", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Box plots show typical deaths per incident + outliers", className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="box-plot", figure={},
                             config={'responsive': True}, style={'height': '450px'})
                ]
            )
        ], xs=12, lg=6),

        dbc.Col([
            html.H3("🫧 Cause of Death by Region", className="text-center mb-2",
                   style={'color': HIGHLIGHT_COLOR}),
            html.P("Bubble size = deaths | See which causes dominate which regions",
                  className="text-center text-muted small"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="bubble-chart", figure={},
                             config={'responsive': True}, style={'height': '450px'})
                ]
            )
        ], xs=12, lg=6)
    ], className="mb-5"),

    html.Div(className="py-4"),

], fluid=True, style={'backgroundColor': '#1a1a1a'})

# =============================================================================
# CALLBACKS
# =============================================================================

# Filter data
@app.callback(
    Output('store-data', 'data'),
    Input('filter-year', 'value'),
    Input('filter-region', 'value'),
    Input('filter-route', 'value')
)
def filter_and_store(year, region, route):
    """Apply filters and store results."""
    try:
        filtered = apply_filters(MM, year, region, route)
        logger.info(f"Filtered to {len(filtered):,} records")
        return filtered.to_dict('records')
    except Exception as e:
        logger.error(f"Error in filter_and_store: {e}")
        return []

# Summary stats
@app.callback(
    Output('summary-stats', 'children'),
    Input('store-data', 'data')
)
def update_summary(data):
    """Update summary statistics."""
    try:
        if not data:
            return "No data matches the selected filters."

        df = pd.DataFrame(data)
        incidents = len(df)
        total_dead_missing = df['Total_Dead_and_Missing'].sum()

        return html.Div([
            html.Span(f"📊 {incidents:,}", className="fw-bold fs-4 me-3", style={'color': HIGHLIGHT_COLOR}),
            html.Span("incidents | ", className="fs-5"),
            html.Span(f"⚠️ {total_dead_missing:,.0f}", className="fw-bold fs-4 me-3", style={'color': '#ff4444'}),
            html.Span("dead/missing", className="fs-5"),
        ])
    except Exception as e:
        logger.error(f"Error in update_summary: {e}")
        return "Error loading summary"

# 1. ANIMATED TIME MAP
@app.callback(
    Output('animated-map', 'figure'),
    Input('store-data', 'data')
)
def update_animated_map(data):
    """Create animated scatter geo map."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)
        df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)].copy()

        if df.empty:
            return go.Figure()

        fig = px.scatter_geo(
            df,
            lat='Latitude',
            lon='Longitude',
            size='Log_Dead',
            color='Total_Dead_and_Missing',
            hover_name='Location Description',
            hover_data={
                'Total_Dead_and_Missing': True,
                'Reported_Date': True,
                'Migration_Route': True,
                'Primary_COD': True,
                'Log_Dead': False,
                'Latitude': False,
                'Longitude': False
            },
            animation_frame='Reported_Year',
            color_continuous_scale=COLOR_CONTINUOUS,
            projection='natural earth',
            size_max=30
        )

        fig.update_layout(
            **CHART_LAYOUT,
            margin=dict(l=0, r=0, t=40, b=0),
            geo=dict(
                showland=True,
                landcolor='rgb(40, 40, 40)',
                countrycolor='rgb(80, 80, 80)',
                showocean=True,
                oceancolor='rgb(20, 20, 40)',
                showcountries=True
            )
        )

        return fig
    except Exception as e:
        logger.error(f"Error in update_animated_map: {e}")
        return go.Figure()

# 2. SANKEY DIAGRAM
@app.callback(
    Output('sankey-flow', 'figure'),
    Input('store-data', 'data')
)
def update_sankey(data):
    """Create Sankey diagram showing migration flows."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)

        # Create flows: Region of Origin -> Region of Incident -> Cause of Death
        flow_data = df.groupby(['Region of Origin', 'Region', 'Primary_COD'])['Total_Dead_and_Missing'].sum().reset_index()
        flow_data = flow_data[flow_data['Total_Dead_and_Missing'] > 0]

        # Create node list
        origins = flow_data['Region of Origin'].unique().tolist()
        regions = flow_data['Region'].unique().tolist()
        cods = flow_data['Primary_COD'].unique().tolist()

        # Remove duplicates and create full node list
        all_nodes = list(dict.fromkeys(origins + regions + cods))
        node_dict = {node: idx for idx, node in enumerate(all_nodes)}

        # Create links
        source = []
        target = []
        value = []

        # Origin -> Region
        for _, row in flow_data.iterrows():
            source.append(node_dict[row['Region of Origin']])
            target.append(node_dict[row['Region']])
            value.append(row['Total_Dead_and_Missing'])

        # Region -> COD (aggregate)
        region_cod = df.groupby(['Region', 'Primary_COD'])['Total_Dead_and_Missing'].sum().reset_index()
        for _, row in region_cod.iterrows():
            if row['Total_Dead_and_Missing'] > 0:
                source.append(node_dict[row['Region']])
                target.append(node_dict[row['Primary_COD']])
                value.append(row['Total_Dead_and_Missing'])

        # Create colors
        node_colors = ['rgba(0, 153, 198, 0.8)' if 'Origin' in node
                      else 'rgba(255, 68, 68, 0.8)' if node in cods
                      else 'rgba(153, 153, 153, 0.8)'
                      for node in all_nodes]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=node_colors
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color='rgba(0, 153, 198, 0.3)'
            )
        )])

        fig.update_layout(
            **CHART_LAYOUT,
            height=700,
            font=dict(size=11, color='white')
        )

        return fig
    except Exception as e:
        logger.error(f"Error in update_sankey: {e}")
        return go.Figure()

# 3. STACKED AREA CHART
@app.callback(
    Output('stacked-area', 'figure'),
    Input('store-data', 'data')
)
def update_stacked_area(data):
    """Create stacked area chart of causes over time."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        if df.empty:
            return go.Figure()

        # Aggregate by month and COD
        df_monthly = df.set_index('Date').resample('M')[COD_COLUMNS].sum()

        fig = go.Figure()

        for cod in COD_COLUMNS:
            if cod in df_monthly.columns:
                fig.add_trace(go.Scatter(
                    x=df_monthly.index,
                    y=df_monthly[cod],
                    name=cod,
                    mode='lines',
                    stackgroup='one',
                    fillcolor=None,
                    hovertemplate='%{y:.0f}<extra></extra>'
                ))

        fig.update_layout(
            **CHART_LAYOUT,
            xaxis_title="Date",
            yaxis_title="Deaths",
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig
    except Exception as e:
        logger.error(f"Error in update_stacked_area: {e}")
        return go.Figure()

# 4. CHOROPLETH MAP
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('store-data', 'data')
)
def update_choropleth(data):
    """Create choropleth map by country."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)

        # Aggregate by country
        country_deaths = df.groupby('Country of Incident')['Total_Dead_and_Missing'].sum().reset_index()
        country_deaths = country_deaths[country_deaths['Total_Dead_and_Missing'] > 0]

        fig = px.choropleth(
            country_deaths,
            locations='Country of Incident',
            locationmode='country names',
            color='Total_Dead_and_Missing',
            hover_name='Country of Incident',
            color_continuous_scale=COLOR_CONTINUOUS,
            labels={'Total_Dead_and_Missing': 'Deaths'}
        )

        fig.update_layout(
            **CHART_LAYOUT,
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth',
                bgcolor='rgba(0,0,0,0)',
                landcolor='rgb(40, 40, 40)',
                oceancolor='rgb(20, 20, 40)'
            )
        )

        return fig
    except Exception as e:
        logger.error(f"Error in update_choropleth: {e}")
        return go.Figure()

# 5. SUNBURST CHART
@app.callback(
    Output('sunburst-chart', 'figure'),
    Input('store-data', 'data')
)
def update_sunburst(data):
    """Create sunburst chart for hierarchical drill-down."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)

        # Aggregate
        hierarchy = df.groupby(['Region', 'Country of Incident', 'Migration_Route'])['Total_Dead_and_Missing'].sum().reset_index()
        hierarchy = hierarchy[hierarchy['Total_Dead_and_Missing'] > 0]

        fig = px.sunburst(
            hierarchy,
            path=['Region', 'Country of Incident', 'Migration_Route'],
            values='Total_Dead_and_Missing',
            color='Total_Dead_and_Missing',
            color_continuous_scale=COLOR_CONTINUOUS
        )

        fig.update_layout(**CHART_LAYOUT)

        return fig
    except Exception as e:
        logger.error(f"Error in update_sunburst: {e}")
        return go.Figure()

# 6. HEATMAP
@app.callback(
    Output('heatmap-season', 'figure'),
    Input('store-data', 'data')
)
def update_heatmap(data):
    """Create heatmap of month vs year."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)

        # Pivot table
        pivot = df.pivot_table(
            values='Total_Dead_and_Missing',
            index='Reported_Month',
            columns='Reported_Year',
            aggfunc='sum',
            fill_value=0
        )

        # Reorder months
        pivot = pivot.reindex([m for m in MONTH_ORDER if m in pivot.index])

        fig = px.imshow(
            pivot,
            labels=dict(x="Year", y="Month", color="Deaths"),
            color_continuous_scale=COLOR_CONTINUOUS,
            aspect="auto"
        )

        fig.update_layout(**CHART_LAYOUT)

        return fig
    except Exception as e:
        logger.error(f"Error in update_heatmap: {e}")
        return go.Figure()

# 7. BOX PLOT
@app.callback(
    Output('box-plot', 'figure'),
    Input('store-data', 'data')
)
def update_boxplot(data):
    """Create box plot of incident severity by region."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)
        df = df[df['Total_Dead_and_Missing'] > 0]  # Remove zeros for better visualization

        fig = px.box(
            df,
            x='Region',
            y='Total_Dead_and_Missing',
            color='Region',
            points='outliers',
            color_discrete_sequence=COLOR_SCHEME
        )

        fig.update_layout(
            **CHART_LAYOUT,
            showlegend=False,
            xaxis_tickangle=-45,
            yaxis_title="Deaths per Incident"
        )

        return fig
    except Exception as e:
        logger.error(f"Error in update_boxplot: {e}")
        return go.Figure()

# 8. BUBBLE CHART
@app.callback(
    Output('bubble-chart', 'figure'),
    Input('store-data', 'data')
)
def update_bubble(data):
    """Create bubble chart of COD vs Region."""
    try:
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)

        # Aggregate by Region and Primary COD
        bubble_data = df.groupby(['Region', 'Primary_COD']).agg({
            'Total_Dead_and_Missing': 'sum',
            'Incident_ID': 'count'
        }).reset_index()

        bubble_data = bubble_data[bubble_data['Total_Dead_and_Missing'] > 0]

        fig = px.scatter(
            bubble_data,
            x='Region',
            y='Primary_COD',
            size='Total_Dead_and_Missing',
            color='Total_Dead_and_Missing',
            hover_data={'Incident_ID': True},
            color_continuous_scale=COLOR_CONTINUOUS,
            size_max=60
        )

        fig.update_layout(
            **CHART_LAYOUT,
            xaxis_tickangle=-45,
            xaxis_title="Region",
            yaxis_title="Cause of Death"
        )

        return fig
    except Exception as e:
        logger.error(f"Error in update_bubble: {e}")
        return go.Figure()

# =============================================================================
# RUN SERVER
# =============================================================================
if __name__ == '__main__':
    app.run(debug=True, port=8051, host='0.0.0.0')
