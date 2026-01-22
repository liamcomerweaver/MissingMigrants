# =============================================================================
# MISSING MIGRANTS PROJECT - IMPROVED DASHBOARD
# =============================================================================
# Changes made:
# 1. Removed map legend for more space
# 2. Added more map detail (relief, terrain colors)
# 3. Fixed "No Article Available" issue (was causing reload)
# 4. Changed text to "View Source" / "Click on a point to see the associated source"
# 5. Made points smaller
# 6. BONUS: Integrated dropdowns as floating controls over the map
# =============================================================================

import logging
from functools import lru_cache
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


import dash
from dash import Dash, dcc, html, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import gunicorn
# =============================================================================
# CONFIGURATION
# =============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

COD_COLUMNS = [
    'Other Accidents', 'Drowning', 'Lack of Shelter, Food, or Water',
    'Mixed or unknown', 'Sickness', 'Transportation Accident', 'Violence'
]
COD_DISPLAY_NAMES = {col: col for col in COD_COLUMNS}

CHART_LAYOUT = {"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"}
COLOR_SCHEME = px.colors.sequential.RdBu
HIGHLIGHT_COLOR = '#CC7A29'

# Custom muted color palette for migration routes
ROUTE_COLORS = [
    '#2E5A87',  # Steel blue
    '#8B4513',  # Saddle brown
    '#2F6B4F',  # Forest green
    '#8B3A62',  # Muted magenta
    '#CC7A29',  # Burnt orange
    '#5B4B8A',  # Muted purple
    '#1A7F7F',  # Teal
    '#994D4D',  # Brick red
    '#6B8E23',  # Olive
    '#4A6670',  # Slate
    '#9E6B4A',  # Copper
    '#3D6B99',  # Denim blue
    '#7A5D47',  # Umber
    '#5C8A6B',  # Sage
    '#87455A',  # Dusty rose
    '#B8860B',  # Dark goldenrod
    '#4F7178',  # Cadet blue
    '#8B6B4F',  # Taupe
    '#6A5D7B',  # Dusty violet
    '#5F8575',  # Cambridge blue
]

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data(filepath: str) -> pd.DataFrame:
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath, parse_dates=['Reported_Date'])
    
    for col in ['Region', 'Country', 'Migration_Route']:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    numeric_cols = ['Total_Dead_and_Missing', 'Number_Dead', 'Minimum_Missing',
                    'Females', 'Males', 'Children', 'Unknown_Sex', 'Unknown_Age_Status']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    logger.info(f"Loaded {len(df):,} records ({df.memory_usage(deep=True).sum() / 1e6:.1f} MB)")
    return df


class DataCache:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._precompute_seasonality()
    
    def _precompute_seasonality(self):
        try:
            df_dated = self.df.dropna(subset=['Reported_Date']).set_index('Reported_Date')
            monthly = df_dated.resample('ME')['Total_Dead_and_Missing'].sum()
            if len(monthly) >= 24:
                monthly.index.freq = 'ME'
                result = seasonal_decompose(monthly, model='add', period=12)
                self.seasonality = result.seasonal
            else:
                self.seasonality = None
        except Exception as e:
            logger.warning(f"Could not compute seasonality: {e}")
            self.seasonality = None
    
    def get_filtered_indices(self, year, region, country, cod, route) -> pd.Index:
        mask = pd.Series(True, index=self.df.index)
        if year != "All":
            mask &= (self.df["Reported_Year"] == year)
        if region != "All":
            mask &= (self.df["Region"] == region)
        if country != "All":
            mask &= (self.df["Country"] == country)
        if route != "All":
            mask &= (self.df["Migration_Route"] == route)
        if cod != "All" and cod in self.df.columns:
            mask &= (self.df[cod] == 1)
        return self.df.index[mask]


def build_dropdown_options(series, sort=True, add_all=True):
    unique_vals = series.dropna().unique().tolist()
    if sort:
        unique_vals = sorted(unique_vals)
    options = [{'label': str(x), 'value': x} for x in unique_vals]
    if add_all:
        options.insert(0, {'label': 'All', 'value': 'All'})
    return options


def empty_figure(fig_type='bar'):
    creators = {
        'bar': px.bar, 'pie': px.pie, 'scatter_geo': px.scatter_geo,
        'treemap': px.treemap, 'line': px.line
    }
    return creators.get(fig_type, px.bar)().update_layout(**CHART_LAYOUT)


# =============================================================================
# LOAD DATA
# =============================================================================
MM = load_data("MM_Dummies_CleanRefactored_Jan16.csv")
cache = DataCache(MM)

options_year = build_dropdown_options(MM["Reported_Year"], sort=False)
options_region = build_dropdown_options(MM["Region"])
options_country = build_dropdown_options(MM["Country"])
options_route = build_dropdown_options(MM["Migration_Route"])
options_cod = [{'label': 'All', 'value': 'All'}] + [
    {'label': col, 'value': col} for col in COD_COLUMNS if col in MM.columns
]

# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.SPACELAB],
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
    suppress_callback_exceptions=True
)
server = app.server

# =============================================================================
# REUSABLE COMPONENTS
# =============================================================================
def make_section_header(title, subtitle=None):
    components = [html.H3(title, className="text-center mb-2")]
    if subtitle:
        components.append(html.P(subtitle, className="text-center text-muted small"))
    return html.Div(components, className="mb-3")


def make_chart_card(graph_id, title, subtitle=None, full_width=False):
    return dbc.Col([
        make_section_header(title, subtitle),
        dcc.Loading(
            type="circle",
            children=[dcc.Graph(id=graph_id, figure={}, config={'responsive': True}, style={'height': '450px'})]
        )
    ], xs=12, lg=12 if full_width else 6, className="mb-4")


# =============================================================================
# LAYOUT - Style A: Floating Filters Over Map
# =============================================================================
app.layout = dbc.Container([
    dcc.Store(id='store-filter-indices', data=[]),
    
    # Header
    html.Div(className="py-3"),
    dbc.Row([
        dbc.Col([
            html.H1("The World's Missing Migrants", className="text-center fw-bold", style={'color': HIGHLIGHT_COLOR}),
            html.P([
                "Data Source: International Organization for Migration's Missing Migrants Project: ",
                html.A("missingmigrants.iom.int", href="https://missingmigrants.iom.int/", target="_blank")
            ], className="text-center text-muted")
        ], width=12)
    ]),
    
    # Map Section with Integrated Floating Filters
    html.Div([
        # The map itself
        dcc.Loading(type="circle", children=[
            dcc.Graph(
                id="map-incidents",
                figure={},
                config={'responsive': True, 'displayModeBar': True, 'displaylogo': False},
                style={'height': '75vh', 'width': '100%'}
            )
        ]),
        
        # Floating filter panel (top-left overlay)
        html.Div([
            html.Div([
                html.Div("FILTERS", style={
                    'fontSize': '0.7rem',
                    'fontWeight': '600',
                    'letterSpacing': '0.1em',
                    'color': '#666',
                    'marginBottom': '0.75rem',
                    'borderBottom': '1px solid #ddd',
                    'paddingBottom': '0.5rem',
                }),
                
                html.Div([
                    html.Label("Year", style={'fontSize': '0.75rem', 'fontWeight': '500', 'color': '#444'}),
                    dcc.Dropdown(
                        id="filter-year", value="All", options=options_year,
                        clearable=False, style={'fontSize': '0.8rem'}
                    ),
                ], style={'marginBottom': '0.5rem'}),
                
                html.Div([
                    html.Label("Region", style={'fontSize': '0.75rem', 'fontWeight': '500', 'color': '#444'}),
                    dcc.Dropdown(
                        id="filter-region", value="All", options=options_region,
                        clearable=False, style={'fontSize': '0.8rem'}
                    ),
                ], style={'marginBottom': '0.5rem'}),
                
                html.Div([
                    html.Label("Route", style={'fontSize': '0.75rem', 'fontWeight': '500', 'color': '#444'}),
                    dcc.Dropdown(
                        id="filter-route", value="All", options=options_route,
                        clearable=False, style={'fontSize': '0.8rem'}
                    ),
                ], style={'marginBottom': '0.5rem'}),
                
                html.Div([
                    html.Label("Cause of Death", style={'fontSize': '0.75rem', 'fontWeight': '500', 'color': '#444'}),
                    dcc.Dropdown(
                        id="filter-cod", value="All", options=options_cod,
                        clearable=False, style={'fontSize': '0.8rem'}
                    ),
                ], style={'marginBottom': '0.5rem'}),
                
                html.Div([
                    html.Label("Country", style={'fontSize': '0.75rem', 'fontWeight': '500', 'color': '#444'}),
                    dcc.Dropdown(
                        id="filter-country", value="All", options=options_country,
                        clearable=False, style={'fontSize': '0.8rem'}
                    ),
                ]),
            ], style={
                'padding': '1rem',
            }),
        ], style={
            'position': 'absolute',
            'top': '10px',
            'left': '10px',
            'width': '220px',
            'backgroundColor': 'rgba(255, 255, 255, 0.95)',
            'borderRadius': '8px',
            'boxShadow': '0 2px 10px rgba(0,0,0,0.15)',
            'zIndex': '1000',
            'maxHeight': '90%',
            'overflowY': 'auto',
        }),
        
        # Summary stats panel (top-right overlay)
        html.Div([
            html.Div(id="summary-stats"),
        ], style={
            'position': 'absolute',
            'top': '10px',
            'right': '10px',
            'backgroundColor': 'rgba(255, 255, 255, 0.95)',
            'borderRadius': '8px',
            'boxShadow': '0 2px 10px rgba(0,0,0,0.15)',
            'padding': '1rem',
            'zIndex': '1000',
        }),
        
        # Source link panel (bottom-center overlay)
        html.Div([
            html.Div(id="incident-details"),
        ], style={
            'position': 'absolute',
            'bottom': '20px',
            'left': '50%',
            'transform': 'translateX(-50%)',
            'backgroundColor': 'rgba(255, 255, 255, 0.95)',
            'borderRadius': '8px',
            'boxShadow': '0 2px 10px rgba(0,0,0,0.15)',
            'padding': '0.75rem 1.5rem',
            'zIndex': '1000',
        }),
        
    ], style={
        'position': 'relative',
        'marginBottom': '2rem',
    }),
    
    # Charts below the map
    dbc.Row([
        make_chart_card("chart-by-year", "Dead and Missing Migrants by Year"),
        make_chart_card("chart-by-month", "Dead and Missing Migrants by Month"),
    ]),
    dbc.Row([
        make_chart_card("chart-by-cod", "Incident Count by Cause of Death",
                       "A single incident can present more than one cause of death."),
        make_chart_card("chart-by-region", "Dead and Missing Migrants by Region"),
    ]),
    dbc.Row([
        make_chart_card("chart-by-sex", "Dead and Missing Migrants by Sex"),
        make_chart_card("chart-by-age", "Dead and Missing Migrants by Age"),
    ]),
    
    # Download
    dbc.Row([
        dbc.Col([
            dbc.Button("Download Selected Data", id="btn-download", color="info", size="lg"),
            dcc.Download(id="download-csv")
        ], width=12, className="text-center mb-4")
    ]),
    
    html.Div(className="py-4"),
], fluid=True)


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(Output('filter-country', 'options'), Input('filter-region', 'value'))
def update_country_options(region):
    if region == "All":
        countries = MM['Country'].dropna().unique()
    else:
        countries = MM.loc[MM['Region'] == region, 'Country'].dropna().unique()
    return [{'label': 'All', 'value': 'All'}] + [{'label': c, 'value': c} for c in sorted(countries)]


@app.callback(
    Output('store-filter-indices', 'data'),
    Input('filter-year', 'value'),
    Input('filter-region', 'value'),
    Input('filter-country', 'value'),
    Input('filter-cod', 'value'),
    Input('filter-route', 'value')
)
def filter_and_store_indices(year, region, country, cod, route):
    indices = cache.get_filtered_indices(year, region, country, cod, route)
    logger.info(f"Filtered to {len(indices):,} records")
    return indices.tolist()


@app.callback(Output('summary-stats', 'children'), Input('store-filter-indices', 'data'))
def update_summary(indices):
    if not indices:
        return html.Div("No data matches filters", style={'color': '#888', 'fontSize': '0.9rem'})
    
    df = MM.loc[indices]
    incidents = len(df)
    total = df['Total_Dead_and_Missing'].sum()
    
    return html.Div([
        html.Div([
            html.Span(f"{incidents:,}", style={'fontSize': '1.5rem', 'fontWeight': '700', 'color': HIGHLIGHT_COLOR}),
            html.Span(" incidents", style={'fontSize': '0.85rem', 'color': '#666', 'marginLeft': '0.25rem'}),
        ]),
        html.Div([
            html.Span(f"{total:,.0f}", style={'fontSize': '1.5rem', 'fontWeight': '700', 'color': '#c9553d'}),
            html.Span(" dead/missing", style={'fontSize': '0.85rem', 'color': '#666', 'marginLeft': '0.25rem'}),
        ]),
    ])


# =============================================================================
# MAP CALLBACK - Improved with more detail, no legend, smaller points
# =============================================================================
@app.callback(Output('map-incidents', 'figure'), Input('store-filter-indices', 'data'))
def update_map(indices):
    if not indices:
        return empty_figure('scatter_geo')
    
    df = MM.loc[indices].copy()
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    if df.empty:
        return empty_figure('scatter_geo')
    
    # Very small points with log scale variance
    df['marker_size'] = np.log1p(df['Total_Dead_and_Missing'])
    df['marker_size'] = 6 + (df['marker_size'] / df['marker_size'].max()) * 20  
    
    fig = px.scatter_geo(
        df,
        lat='Latitude',
        lon='Longitude',
        size='marker_size',
        color='Migration_Route',
        hover_name='Migration_Route',
        hover_data={
            'Number_Dead': True,
            'Minimum_Missing': True,
            'Reported_Year': True,
            'Country': False,
            'marker_size': False,
            'Latitude': False,
            'Longitude': False,
        },
        custom_data=['URL1'],
        projection='orthographic',
        color_discrete_sequence=ROUTE_COLORS,
        opacity=0.6,
    )
    
    # Detailed, terrain-style base map
    fig.update_geos(
        showland=True,
        landcolor='rgb(228, 223, 215)',           # Warm parchment tone
        showocean=True,
        oceancolor='rgb(185, 206, 220)',          # Muted ocean blue
        showcoastlines=True,
        coastlinecolor='rgb(120, 120, 120)',      # Darker coastlines
        coastlinewidth=1,
        showlakes=True,
        lakecolor='rgb(185, 206, 220)',
        showcountries=True,
        countrycolor='rgb(160, 160, 160)',        # Visible country borders
        countrywidth=0.8,
        showsubunits=True,
        subunitcolor='rgb(200, 200, 200)',
        subunitwidth=0.8,
        showrivers=True,
        rivercolor='rgb(170, 195, 215)',
        riverwidth=1,
        showframe=False,
        bgcolor='rgba(0,0,0,0)',
        resolution=50,                             # Higher resolution (50 or 110)
        lataxis_showgrid=True,
        lataxis_gridcolor='rgba(0,0,0,0.05)',
        lonaxis_showgrid=True,
        lonaxis_gridcolor='rgba(0,0,0,0.05)',
    )
    
    # Make markers smaller and remove legend
    fig.update_traces(
        marker=dict(
            sizemode='area',
            sizeref=1.0,        # Larger sizeref = smaller markers
            sizemin=1,
            line=dict(width=0.3, color='rgba(30,30,30,0.4)'),
        )
    )
    
    fig.update_layout(
        **CHART_LAYOUT,
        height=None,  # Let container control height
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,  # REMOVED LEGEND
    )
    
    return fig


# =============================================================================
# INCIDENT DETAILS - Fixed to not cause reload
# =============================================================================
@app.callback(Output('incident-details', 'children'), Input('map-incidents', 'clickData'))
def display_incident_details(clickData):
    if clickData is None:
        return html.P(
            "Click on a point to see the associated source",
            style={'margin': '0', 'color': '#666', 'fontSize': '0.85rem'}
        )
    
    try:
        # Safely extract the URL
        points = clickData.get('points', [])
        if not points:
            return html.P(
                'No Article Available',
                style={'margin': '0', 'color': '#b8860b', 'fontSize': '0.85rem'}
            )
        
        customdata = points[0].get('customdata', [])
        if not customdata:
            return html.P(
                'No Article Available',
                style={'margin': '0', 'color': '#b8860b', 'fontSize': '0.85rem'}
            )
        
        the_link = customdata[0] if len(customdata) > 0 else None
        
        # Check for None, empty string, NaN, 'nan', etc.
        if the_link is None or the_link == '' or str(the_link).lower() == 'nan' or pd.isna(the_link):
            return html.P(
                'No Article Available',
                style={'margin': '0', 'color': '#b8860b', 'fontSize': '0.85rem'}
            )
        
        # Valid link - return button
        link_url = str(the_link).split(",")[0].strip()
        return html.A(
            "View Source",
            href=link_url,
            target="_blank",
            style={
                'display': 'inline-block',
                'padding': '0.5rem 1.5rem',
                'backgroundColor': HIGHLIGHT_COLOR,
                'color': 'white',
                'borderRadius': '4px',
                'textDecoration': 'none',
                'fontSize': '0.9rem',
                'fontWeight': '500',
            }
        )
    except Exception as e:
        logger.error(f"Error in display_incident_details: {e}")
        return html.P(
            'No Article Available',
            style={'margin': '0', 'color': '#b8860b', 'fontSize': '0.85rem'}
        )


# =============================================================================
# OTHER CHART CALLBACKS
# =============================================================================

@app.callback(Output('chart-by-year', 'figure'), Input('store-filter-indices', 'data'))
def update_chart_by_year(indices):
    if not indices:
        return empty_figure('bar')
    df = MM.loc[indices]
    yearly = df.groupby('Reported_Year')[['Number_Dead', 'Minimum_Missing']].sum().reset_index()
    fig = px.bar(yearly, x='Reported_Year', y=['Number_Dead', 'Minimum_Missing'],
                 color_discrete_sequence=COLOR_SCHEME,
                 labels={'value': 'Number of Migrants', 'Reported_Year': 'Year', 'variable': ''})
    fig.update_layout(**CHART_LAYOUT, xaxis_tickangle=-45,
                      legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
    return fig


@app.callback(Output('chart-by-month', 'figure'), Input('store-filter-indices', 'data'))
def update_chart_by_month(indices):
    if not indices:
        return empty_figure('bar')
    df = MM.loc[indices].copy()
    df = df.dropna(subset=['Reported_Date'])
    df = df.set_index('Reported_Date')
    monthly = df.resample('ME')[['Number_Dead', 'Minimum_Missing']].sum()
    fig = px.bar(monthly, y=['Number_Dead', 'Minimum_Missing'],
                 color_discrete_sequence=COLOR_SCHEME,
                 labels={'value': 'Number of Migrants', 'Reported_Date': 'Date', 'variable': ''})
    fig.update_layout(**CHART_LAYOUT, xaxis_tickangle=-90,
                      legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
    return fig


@app.callback(Output('chart-by-cod', 'figure'), Input('store-filter-indices', 'data'))
def update_chart_by_cod(indices):
    if not indices:
        return empty_figure('bar')
    df = MM.loc[indices]
    cod_cols = [c for c in COD_COLUMNS if c in df.columns]
    if not cod_cols:
        return empty_figure('bar')
    cod_sums = df[cod_cols].sum()
    cod_df = pd.DataFrame({
        'Cause': [COD_DISPLAY_NAMES.get(c, c) for c in cod_sums.index],
        'Count': cod_sums.values
    }).sort_values('Count', ascending=True)
    fig = px.bar(cod_df, x='Count', y='Cause', orientation='h',
                 color='Count', color_continuous_scale='YlOrRd',
                 labels={'Count': 'Number of Incidents', 'Cause': ''})
    fig.update_layout(**CHART_LAYOUT)
    return fig


@app.callback(Output('chart-by-region', 'figure'), Input('store-filter-indices', 'data'))
def update_chart_by_region(indices):
    if not indices:
        return empty_figure('pie')
    df = MM.loc[indices]
    fig = px.pie(df, values='Total_Dead_and_Missing', names='Region',
                 color_discrete_sequence=COLOR_SCHEME, hole=0.3)
    fig.update_layout(**CHART_LAYOUT)
    return fig


@app.callback(Output('chart-by-sex', 'figure'), Input('store-filter-indices', 'data'))
def update_chart_by_sex(indices):
    if not indices:
        return empty_figure('pie')
    df = MM.loc[indices]
    sex_cols = [c for c in ['Females', 'Males', 'Unknown_Sex'] if c in df.columns]
    sex_totals = df[sex_cols].sum()
    sex_df = pd.DataFrame({'Sex': sex_totals.index, 'Count': sex_totals.values})
    fig = px.pie(sex_df, values='Count', names='Sex', color_discrete_sequence=COLOR_SCHEME, hole=0.4)
    fig.update_layout(**CHART_LAYOUT)
    return fig


@app.callback(Output('chart-by-age', 'figure'), Input('store-filter-indices', 'data'))
def update_chart_by_age(indices):
    if not indices:
        return empty_figure('pie')
    df = MM.loc[indices]
    age_cols = [c for c in ['Confirmed_Adults', 'Children', 'Unknown_Age_Status'] if c in df.columns]
    age_totals = df[age_cols].sum()
    age_df = pd.DataFrame({'Age': age_totals.index, 'Count': age_totals.values})
    fig = px.pie(age_df, values='Count', names='Age', color_discrete_sequence=COLOR_SCHEME, hole=0.4)
    fig.update_layout(**CHART_LAYOUT)
    return fig


@app.callback(
    Output('download-csv', 'data'),
    Input('btn-download', 'n_clicks'),
    State('store-filter-indices', 'data'),
    prevent_initial_call=True
)
def download_csv(n_clicks, indices):
    if n_clicks is None or not indices:
        raise PreventUpdate
    df = MM.loc[indices]
    return dict(content=df.to_csv(index=False), filename="Missing_Migrants_Filtered.csv")


# =============================================================================
# RUN SERVER
# =============================================================================
if __name__ == '__main__':
  app.run_server()

