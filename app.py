#!/usr/bin/env python
# coding: utf-8
"""
Missing Migrants Dashboard - Refactored Version

Key improvements over original:
1. Single filtering function (eliminates ~200 lines of duplicated code)
2. Filter once, use everywhere via dcc.Store (11x fewer filter operations)
3. Proper error handling with logging
4. Responsive charts (no fixed widths)
5. Loading indicators for better UX
6. Chained dropdowns (Country options filter based on Region)
7. Date parsing at load time (not in callbacks)
8. Centralized configuration
9. Cleaner layout with reusable components
"""

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import pandas as pd
import numpy as np
import plotly.express as px
from statsmodels.tsa.seasonal import seasonal_decompose

import dash
from dash import Dash, dcc, html, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# =============================================================================
# CONFIGURATION
# =============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Column configuration (avoid hard-coded indices)
COD_COLUMNS = [
    'COD_Other Accidents',
    'COD_Drowning', 
    'COD_Lack of Shelter, Food, or Water',
    'COD_Mixed or unknown',
    'COD_Sickness',
    'COD_Transportation Accident',
    'COD_Violence'
]

# Display names for COD columns
COD_DISPLAY_NAMES = {col: col.replace('COD_', '') for col in COD_COLUMNS}

# Chart styling
CHART_LAYOUT = {
    "plot_bgcolor": "rgba(0, 0, 0, 0)",
    "paper_bgcolor": "rgba(0, 0, 0, 0)"
}

COLOR_SCHEME = px.colors.sequential.RdBu
HIGHLIGHT_COLOR = '#0099C6'
MUTED_COLOR = '#808080'

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data(filepath: str) -> pd.DataFrame:
    """Load and preprocess the dataset."""
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    
    # Parse dates at load time (not in callbacks)
    if 'Reported_Date' in df.columns:
        df['Reported_Date'] = pd.to_datetime(df['Reported_Date'], errors='coerce')
    
    # Ensure numeric columns are numeric
    numeric_cols = ['Total_Dead_and_Missing', 'Number_Dead', 'Minimum_Missing',
                    'Females', 'Males', 'Children', 'Unknown_Sex', 'Unknown_Age_Status']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    logger.info(f"Loaded {len(df):,} records")
    return df

# Load data
MM = load_data("MM_Cleaned_27.csv")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def apply_filters(df: pd.DataFrame, year, region, country, cod, route) -> pd.DataFrame:
    """
    Apply all filters to the dataframe.
    This single function replaces ~200 lines of duplicated filter code.
    """
    filtered = df.copy()
    
    if year != "All":
        filtered = filtered[filtered["Reported_Year"] == year]
    if region != "All":
        filtered = filtered[filtered["Region"] == region]
    if country != "All":
        filtered = filtered[filtered["Country"] == country]
    if route != "All":
        filtered = filtered[filtered["Migration_Route"] == route]
    if cod != "All" and cod in filtered.columns:
        filtered = filtered[filtered[cod] == 1]
    
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


def empty_figure(fig_type='bar'):
    """Return an empty figure with consistent styling."""
    if fig_type == 'bar':
        fig = px.bar()
    elif fig_type == 'pie':
        fig = px.pie()
    elif fig_type == 'scatter_geo':
        fig = px.scatter_geo()
    elif fig_type == 'treemap':
        fig = px.treemap()
    elif fig_type == 'line':
        fig = px.line()
    else:
        fig = px.bar()
    return fig.update_layout(**CHART_LAYOUT)


# =============================================================================
# BUILD DROPDOWN OPTIONS
# =============================================================================
options_year = build_dropdown_options(MM["Reported_Year"], sort=False)
options_region = build_dropdown_options(MM["Region"])
options_country = build_dropdown_options(MM["Country"])
options_route = build_dropdown_options(MM["Migration_Route"])

# COD options with cleaner labels
options_cod = [{'label': 'All', 'value': 'All'}]
for col in COD_COLUMNS:
    if col in MM.columns:
        options_cod.append({'label': COD_DISPLAY_NAMES[col], 'value': col})

# =============================================================================
# REUSABLE LAYOUT COMPONENTS
# =============================================================================
def make_section_header(title, subtitle=None):
    """Create a consistent section header."""
    components = [
        html.H3(title, className="text-center mb-2")
    ]
    if subtitle:
        components.append(
            html.P(subtitle, className="text-center text-muted small")
        )
    return html.Div(components, className="mb-3")


def make_chart_card(graph_id, title, subtitle=None, full_width=False):
    """Create a chart with loading indicator and optional subtitle."""
    width = 12 if full_width else 6
    return dbc.Col([
        make_section_header(title, subtitle),
        dcc.Loading(
            type="circle",
            children=[
                dcc.Graph(
                    id=graph_id, 
                    figure={},
                    config={'responsive': True},
                    style={'height': '450px'}
                )
            ]
        )
    ], xs=12, lg=width, className="mb-4")


# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
    suppress_callback_exceptions=True
)
server = app.server

# =============================================================================
# LAYOUT
# =============================================================================
app.layout = dbc.Container([
    # Data store - filtered data computed once, used by all charts
    dcc.Store(id='store-data', data=[]),
    
    # Header
    html.Div(className="py-4"),
    dbc.Row([
        dbc.Col([
            html.H1(
                "Visualizing Missing Migrants",
                className="text-center fw-bold",
                style={'color': HIGHLIGHT_COLOR}
            ),
            html.P(
                ["Data Source: International Organization for Migration's Missing Migrants Project: ",
                 html.A("missingmigrants.iom.int", href="https://missingmigrants.iom.int/", target="_blank")],
                className="text-center text-muted"
            )
        ], width=12)
    ]),
    
    html.Hr(),
    
    # Filters Row 1
    dbc.Row([
        dbc.Col([
            html.Label("Year", className="fw-bold"),
            dcc.Dropdown(id="filter-year", value="All", options=options_year, clearable=False)
        ], xs=12, md=4, className="mb-3"),
        
        dbc.Col([
            html.Label("Region of Incident", className="fw-bold"),
            dcc.Dropdown(id="filter-region", value="All", options=options_region, clearable=False)
        ], xs=12, md=4, className="mb-3"),
        
        dbc.Col([
            html.Label("Migration Route", className="fw-bold"),
            dcc.Dropdown(id="filter-route", value="All", options=options_route, clearable=False)
        ], xs=12, md=4, className="mb-3"),
    ]),
    
    # Filters Row 2
    dbc.Row([
        dbc.Col([
            html.Label("Cause of Death", className="fw-bold"),
            dcc.Dropdown(id="filter-cod", value="All", options=options_cod, clearable=False)
        ], xs=12, md=6, className="mb-3"),
        
        dbc.Col([
            html.Label("Country of Incident", className="fw-bold"),
            dcc.Dropdown(id="filter-country", value="All", options=options_country, clearable=False)
        ], xs=12, md=6, className="mb-3"),
    ]),
    
    # Summary Stats
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="summary-stats", className="text-center py-2")
                ])
            ], color="light")
        ], width=12)
    ], className="mb-4"),
    
    # Map Section
    dbc.Row([
        dbc.Col([
            make_section_header(
                "Dead and Missing Migrants by Incident Location",
                "Click on a point to see incident details. Bubble size indicates number of dead/missing."
            ),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="map-incidents", figure={}, config={'responsive': True}, style={'height': '500px'})
                ]
            ),
            html.Div(id="incident-details", className="text-center mt-2"),
            html.P(
                "The boundaries and names shown and the designations used on maps do not imply endorsement or acceptance.",
                className="text-center text-muted small mt-2"
            )
        ], width=12)
    ], className="mb-4"),
    
    # Year and Month Charts
    dbc.Row([
        make_chart_card("chart-by-year", "Dead and Missing Migrants by Year"),
        make_chart_card("chart-by-month", "Dead and Missing Migrants by Month"),
    ]),
    
    # COD and Region Charts
    dbc.Row([
        make_chart_card(
            "chart-by-cod", 
            "Incident Count by Cause of Death",
            "A single incident can present more than one cause of death."
        ),
        make_chart_card("chart-by-region", "Dead and Missing Migrants by Region"),
    ]),
    
    # Treemap
    dbc.Row([
        dbc.Col([
            make_section_header(
                "Dead and Missing Migrants by Country",
                "The category 'Not Found' corresponds to incidents at sea or in unidentified territories."
            ),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="treemap-country", figure={}, config={'responsive': True}, style={'height': '500px'})
                ]
            )
        ], width=12)
    ], className="mb-4"),
    
    # Demographics Charts
    dbc.Row([
        make_chart_card("chart-by-sex", "Dead and Missing Migrants by Sex"),
        make_chart_card("chart-by-age", "Dead and Missing Migrants by Age"),
    ]),
    
    # Seasonality Section
    dbc.Row([
        dbc.Col([
            html.H2("Data Seasonality", className="text-center fw-bold mt-4", style={'color': HIGHLIGHT_COLOR}),
            html.P("Seasonality drawn from ETS decomposition", className="text-center text-muted"),
            dcc.Loading(
                type="circle",
                children=[
                    dcc.Graph(id="chart-seasonality", figure={}, config={'responsive': True}, style={'height': '400px'})
                ]
            )
        ], width=12)
    ], className="mb-4"),
    
    # Download Button
    dbc.Row([
        dbc.Col([
            dbc.Button("Download Selected Data", id="btn-download", color="info", size="lg", className="me-2"),
            dcc.Download(id="download-csv")
        ], width=12, className="text-center mb-4")
    ]),
    
    html.Div(className="py-4"),
    
], fluid=True)

# =============================================================================
# CALLBACKS
# =============================================================================

# Chained dropdown: Update country options based on region
@app.callback(
    Output('filter-country', 'options'),
    Input('filter-region', 'value')
)
def update_country_options(region):
    """Filter country dropdown based on selected region."""
    if region == "All":
        countries = MM['Country'].dropna().unique()
    else:
        countries = MM.loc[MM['Region'] == region, 'Country'].dropna().unique()
    
    options = [{'label': 'All', 'value': 'All'}]
    options += [{'label': c, 'value': c} for c in sorted(countries)]
    return options


# Main filter callback - filters data ONCE and stores it
@app.callback(
    Output('store-data', 'data'),
    Input('filter-year', 'value'),
    Input('filter-region', 'value'),
    Input('filter-country', 'value'),
    Input('filter-cod', 'value'),
    Input('filter-route', 'value')
)
def filter_and_store(year, region, country, cod, route):
    """Apply filters once and store results for all charts to use."""
    try:
        filtered = apply_filters(MM, year, region, country, cod, route)
        logger.info(f"Filtered to {len(filtered):,} records")
        return filtered.to_dict('records')
    except Exception as e:
        logger.error(f"Error in filter_and_store: {e}")
        return []


# Summary statistics
@app.callback(
    Output('summary-stats', 'children'),
    Input('store-data', 'data')
)
def update_summary(data):
    """Update the summary statistics display."""
    try:
        if not data:
            return "No data matches the selected filters."
        
        df = pd.DataFrame(data)
        incidents = len(df)
        total_dead_missing = df['Total_Dead_and_Missing'].sum()
        
        return html.Div([
            html.Span(f"{incidents:,}", className="fw-bold fs-4", style={'color': HIGHLIGHT_COLOR}),
            html.Span(" incidents with ", className="fs-5"),
            html.Span(f"{total_dead_missing:,.0f}", className="fw-bold fs-4", style={'color': HIGHLIGHT_COLOR}),
            html.Span(" migrants reported dead or missing", className="fs-5"),
        ])
    except Exception as e:
        logger.error(f"Error in update_summary: {e}")
        return "Error loading summary"


# Map
@app.callback(
    Output('map-incidents', 'figure'),
    Input('store-data', 'data')
)
def update_map(data):
    """Update the scatter map of incidents."""
    try:
        if not data:
            return empty_figure('scatter_geo')
        
        df = pd.DataFrame(data)
        
        # Filter out invalid coordinates
        df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
        
        if df.empty:
            return empty_figure('scatter_geo')
        
        fig = px.scatter_geo(
            df,
            lat='Latitude',
            lon='Longitude',
            size='Log_Dead',
            color='Total_Dead_and_Missing',
            hover_name='Location_Description',
            hover_data={
                'Total_Dead_and_Missing': True,
                'Reported_Date': True,
                'Migration_Route': True,
                'Log_Dead': False,
                'Latitude': False,
                'Longitude': False
            },
            color_continuous_scale='YlOrRd',
            projection='natural earth'
        )
        
        fig.update_layout(
            **CHART_LAYOUT,
            margin=dict(l=0, r=0, t=0, b=0),
            geo=dict(
                showland=True,
                landcolor='rgb(243, 243, 243)',
                countrycolor='rgb(204, 204, 204)',
                showocean=True,
                oceancolor='rgb(230, 245, 255)'
            )
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_map: {e}")
        return empty_figure('scatter_geo')


# Chart: By Year
@app.callback(
    Output('chart-by-year', 'figure'),
    Input('store-data', 'data')
)
def update_chart_by_year(data):
    """Update the bar chart by year."""
    try:
        if not data:
            return empty_figure('bar')
        
        df = pd.DataFrame(data)
        yearly = df.groupby('Reported_Year')[['Number_Dead', 'Minimum_Missing']].sum().reset_index()
        
        fig = px.bar(
            yearly,
            x='Reported_Year',
            y=['Number_Dead', 'Minimum_Missing'],
            color_discrete_sequence=COLOR_SCHEME,
            labels={'value': 'Number of Migrants', 'Reported_Year': 'Year', 'variable': ''}
        )
        
        fig.update_layout(
            **CHART_LAYOUT,
            xaxis_tickangle=-45,
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_chart_by_year: {e}")
        return empty_figure('bar')


# Chart: By Month
@app.callback(
    Output('chart-by-month', 'figure'),
    Input('store-data', 'data')
)
def update_chart_by_month(data):
    """Update the bar chart by month."""
    try:
        if not data:
            return empty_figure('bar')
        
        df = pd.DataFrame(data)
        df['Reported_Date'] = pd.to_datetime(df['Reported_Date'], errors='coerce')
        df = df.set_index('Reported_Date')
        monthly = df.resample('M')[['Number_Dead', 'Minimum_Missing']].sum()
        
        fig = px.bar(
            monthly,
            y=['Number_Dead', 'Minimum_Missing'],
            color_discrete_sequence=COLOR_SCHEME,
            labels={'value': 'Number of Migrants', 'Reported_Date': 'Date', 'variable': ''}
        )
        
        fig.update_layout(
            **CHART_LAYOUT,
            xaxis_tickangle=-90,
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_chart_by_month: {e}")
        return empty_figure('bar')


# Chart: By Cause of Death
@app.callback(
    Output('chart-by-cod', 'figure'),
    Input('store-data', 'data')
)
def update_chart_by_cod(data):
    """Update the bar chart by cause of death."""
    try:
        if not data:
            return empty_figure('bar')
        
        df = pd.DataFrame(data)
        
        # Get COD columns that exist in the data
        cod_cols = [c for c in COD_COLUMNS if c in df.columns]
        if not cod_cols:
            return empty_figure('bar')
        
        # Sum each COD column
        cod_sums = df[cod_cols].sum()
        cod_df = pd.DataFrame({
            'Cause': [COD_DISPLAY_NAMES.get(c, c) for c in cod_sums.index],
            'Count': cod_sums.values
        }).sort_values('Count', ascending=True)
        
        fig = px.bar(
            cod_df,
            x='Count',
            y='Cause',
            orientation='h',
            color='Count',
            color_continuous_scale='YlOrRd',
            labels={'Count': 'Number of Incidents', 'Cause': ''}
        )
        
        fig.update_layout(**CHART_LAYOUT)
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_chart_by_cod: {e}")
        return empty_figure('bar')


# Chart: By Region
@app.callback(
    Output('chart-by-region', 'figure'),
    Input('store-data', 'data')
)
def update_chart_by_region(data):
    """Update the pie chart by region."""
    try:
        if not data:
            return empty_figure('pie')
        
        df = pd.DataFrame(data)
        
        fig = px.pie(
            df,
            values='Total_Dead_and_Missing',
            names='Region',
            color_discrete_sequence=COLOR_SCHEME,
            hole=0.3
        )
        
        fig.update_layout(**CHART_LAYOUT)
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_chart_by_region: {e}")
        return empty_figure('pie')


# Treemap: By Country
@app.callback(
    Output('treemap-country', 'figure'),
    Input('store-data', 'data')
)
def update_treemap_country(data):
    """Update the treemap by country."""
    try:
        if not data:
            return empty_figure('treemap')
        
        df = pd.DataFrame(data)
        country_totals = df.groupby('Country')['Total_Dead_and_Missing'].sum().reset_index()
        
        if country_totals.empty:
            return empty_figure('treemap')
        
        fig = px.treemap(
            country_totals,
            path=['Country'],
            values='Total_Dead_and_Missing',
            color='Total_Dead_and_Missing',
            color_continuous_scale='YlOrRd'
        )
        
        fig.update_layout(**CHART_LAYOUT)
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_treemap_country: {e}")
        return empty_figure('treemap')


# Chart: By Sex
@app.callback(
    Output('chart-by-sex', 'figure'),
    Input('store-data', 'data')
)
def update_chart_by_sex(data):
    """Update the pie chart by sex."""
    try:
        if not data:
            return empty_figure('pie')
        
        df = pd.DataFrame(data)
        
        sex_cols = ['Females', 'Males', 'Unknown_Sex']
        sex_cols = [c for c in sex_cols if c in df.columns]
        
        sex_totals = df[sex_cols].sum()
        sex_df = pd.DataFrame({
            'Sex': sex_totals.index,
            'Count': sex_totals.values
        })
        
        fig = px.pie(
            sex_df,
            values='Count',
            names='Sex',
            color_discrete_sequence=COLOR_SCHEME,
            hole=0.4
        )
        
        fig.update_layout(**CHART_LAYOUT)
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_chart_by_sex: {e}")
        return empty_figure('pie')


# Chart: By Age
@app.callback(
    Output('chart-by-age', 'figure'),
    Input('store-data', 'data')
)
def update_chart_by_age(data):
    """Update the pie chart by age."""
    try:
        if not data:
            return empty_figure('pie')
        
        df = pd.DataFrame(data)
        
        age_cols = ['Confirmed_Adults', 'Children', 'Unknown_Age_Status']
        age_cols = [c for c in age_cols if c in df.columns]
        
        age_totals = df[age_cols].sum()
        age_df = pd.DataFrame({
            'Age': age_totals.index,
            'Count': age_totals.values
        })
        
        fig = px.pie(
            age_df,
            values='Count',
            names='Age',
            color_discrete_sequence=COLOR_SCHEME,
            hole=0.4
        )
        
        fig.update_layout(**CHART_LAYOUT)
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_chart_by_age: {e}")
        return empty_figure('pie')


# Chart: Seasonality
@app.callback(
    Output('chart-seasonality', 'figure'),
    Input('store-data', 'data')
)
def update_seasonality(data):
    """Update the seasonality chart."""
    try:
        if not data or len(data) < 24:  # Need at least 2 years for seasonal decomposition
            return empty_figure('line')
        
        df = pd.DataFrame(data)
        df['Reported_Date'] = pd.to_datetime(df['Reported_Date'], errors='coerce')
        df = df.dropna(subset=['Reported_Date'])
        
        if df.empty:
            return empty_figure('line')
        
        df = df.set_index('Reported_Date')
        monthly = df.resample('M')['Total_Dead_and_Missing'].sum()
        
        if len(monthly) < 24:
            return empty_figure('line')
        
        monthly.index.freq = 'M'
        result = seasonal_decompose(monthly, model='add', period=12)
        
        fig = px.line(
            x=result.seasonal.index,
            y=result.seasonal.values,
            labels={'x': 'Date', 'y': 'Seasonal Component'}
        )
        
        fig.update_layout(**CHART_LAYOUT)
        
        return fig
    except Exception as e:
        logger.error(f"Error in update_seasonality: {e}")
        return empty_figure('line')


# Download CSV
@app.callback(
    Output('download-csv', 'data'),
    Input('btn-download', 'n_clicks'),
    State('store-data', 'data'),
    prevent_initial_call=True
)
def download_csv(n_clicks, data):
    """Download the filtered data as CSV."""
    if n_clicks is None:
        raise PreventUpdate
    
    try:
        df = pd.DataFrame(data)
        return dict(
            content=df.to_csv(index=False),
            filename="Missing_Migrants_Filtered.csv"
        )
    except Exception as e:
        logger.error(f"Error in download_csv: {e}")
        raise PreventUpdate


# =============================================================================
# RUN SERVER
# =============================================================================
if __name__ == '__main__':
    app.run_server(debug=True)
