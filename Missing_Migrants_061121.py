#!/usr/bin/env python
# coding: utf-8

# # Missing Migrants Project

# ## Importing libraries and adjusting other settings

# In[1]:


#If you haven't done it, please install:
#!pip install plotly
#!pip install pandas
#!pip install numpy
#!pip install dash
#!pip install dash-bootstrap-components


# In[2]:


# To manipulate the dataframe
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import math


# In[3]:


# To use dates
import datetime
# Date parser to pass to read_csv
d = lambda x: pd.datetime.strptime(x, '%d-%b-%y')


# In[4]:


# To find countries from coordinates
from geopy.geocoders import Nominatim


# In[5]:


# To create dashboard
import dash
from dash import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc


# In[6]:


import collections
from dash.exceptions import PreventUpdate
import dash_table


# In[7]:


# A. Load the data 

#option A: if you ran the code above in its entirety, just continue.
#option B: store the file MM_dumies in your directory and load with the following command:

MM = pd.read_csv("MM_dummies.csv")


# In[8]:


# B. Determining the different menus 
from operator import itemgetter
col_options_Region = [dict(label=x, value=x) for x in MM["Region"].unique()]
col_options_Region = sorted(col_options_Region, key=itemgetter('label'), reverse=False)
col_options_Region.insert(0,{'label': 'All', 'value': 'All'})


col_options_Year = [dict(label=x, value=x) for x in MM["Reported_Year"].unique()]
col_options_Year.insert(0,{'label': 'All', 'value': 'All'})


col_options_COD = [dict(label=x, value=x) for x in MM.columns[20:-7]]
col_options_COD = sorted(col_options_COD, key=itemgetter('label'), reverse=False)
col_options_COD.insert(0, {'label': 'All', 'value': 'All'})


col_options_Country = [dict(label=x, value=x) for x in MM["Country"].unique()]
col_options_Country = sorted(col_options_Country, key=itemgetter('label'), reverse=False)
col_options_Country.insert(0, {'label': 'All', 'value': 'All'})

col_options_Route = [dict(label=x, value=x) for x in MM["Migration_Route"].unique()]
col_options_Route = sorted(col_options_Route, key=itemgetter('label'), reverse=False)
col_options_Route.insert(0, {'label': 'All', 'value': 'All'})


# In[9]:


# C. Building app Layout 
app = dash.Dash(__name__, external_stylesheets = [dbc.themes.LUX],
                  meta_tags = [{'name' : 'viewport',
                               'content' : 'width-device-width, initial-scale=1.0'}]
                  )

app.layout = dbc.Container([
    
#For storing data   
                dcc.Store(id='memory-output'),
    
#Title and source            
                dbc.Row([dbc.Col(html.Br())]),
                dbc.Row([dbc.Col(html.Br())]),
    
                dbc.Row(
                    [
                        dbc.Col(html.H1("Visualizing Missing Migrants",
                                       className = 'text-primary, mb-4',
                                        style ={'color': '#0099C6', "text-align": "center",
                                                "font-weight": "bold"}),
                                
                               #width = {"size": 6, "offset":0},
                                xs = 12, sm = 12, md = 12, lg = 12, xl = 12
                               ),
                    ],
                    no_gutters=True, justify = 'center',
                ),
                
                dbc.Row(
                    [
                        dbc.Col(html.H6("Source: IOM", 
                                        style ={"text-align": "center"}),
                               #width = {"size": 6, "offset": 0},
                               xs = 12, sm = 12, md = 12, lg = 12, xl = 12
                               ),
                    ],
                    no_gutters=True, justify = 'center',
                ),
    
                dbc.Row([dbc.Col(html.Br())]),
    
#Dropdown menus    
                dbc.Row(
                    children = [dbc.Col([html.H4("Year"), 
                                   
                                dcc.Dropdown(id = "Reported_Year", value = "All", 
                                        options = col_options_Year)],
                                        #width = {"size": 5, "offset": 0},
                                        xs = 4, sm = 4, md = 4, lg = 4, xl = 4
                                       ), 
                                
                                dbc.Col([html.H4("Region"), 
                                         
                                dcc.Dropdown(id = "Region", value = "All",  
                                        options = col_options_Region)],
                                        #width = {"size": 5, "offset": 0},
                                        xs = 4, sm = 4, md = 4, lg = 4, xl = 4
                                       ),
                                
                                dbc.Col([html.H4("Route"), 
                                         
                                dcc.Dropdown(id = "Migration_Route", value = "All",  
                                        options = col_options_Route)],
                                        #width = {"size": 5, "offset": 0},
                                        xs = 4, sm = 4, md = 4, lg = 4, xl = 4
                                       ),
                              ],
                                
                    no_gutters=False, justify = 'around',                             
                    
                ),
    
                dbc.Row([dbc.Col(html.Br())]),
    
              
    
                dbc.Row(children = [dbc.Col([html.H4("Cause of Death"), 
                                   
                            dcc.Dropdown(id = "COD", value = "All", 
                                    options = col_options_COD)],
                                    #width = {"size": 5, "offset": 0},
                                    xs = 6, sm = 6, md = 6, lg = 6, xl = 6
                                    ), 
                                
                            dbc.Col([html.H4("Country"), 
                                         
                            dcc.Dropdown(id = "Country", value = "All",  
                                    options = col_options_Country)],
                                    #width = {"size": 5, "offset": 0},
                                    xs = 6, sm = 6, md = 6, lg = 6, xl = 6
                                   ),
                            
                            ],
                        
                    no_gutters=False, justify = 'around',

                   ),
    
                dbc.Row([dbc.Col(html.Br())]),
                dbc.Row([dbc.Col(html.Br())]),

             
                    
                dbc.Row(
                    [
                        dbc.Col(dcc.Markdown(id= "text1",
                                       style ={"text-align": "center",
                                               "color": '#0099C6',
                                               "backgroundColor": "#dcdcdc", "font-weight": "bold"}),
                                     xs = 11, sm = 11, md = 11, lg = 11, xl = 11),
                    ], 
                        no_gutters = True, justify = 'center',
        
                       ),
    
                dbc.Row([dbc.Col(html.Br())]),
                dbc.Row([dbc.Col(html.Br())]),

#Map and button   
                dbc.Row(
                    [
                        dbc.Col(html.H3("Dead and Missing Migrants by Incident",
                                       style ={"text-align": "center"}),
                                    #width = {"size": 5, "offset": 0},
                                     xs = 12, sm = 12, md = 12, lg = 12, xl = 12),
                    ], 
                        no_gutters = True, justify = 'center',
        
                       ),
                dbc.Row(
                                    
                    [
                        dbc.Col(dbc.Button(html.Pre(id = "web_link", children = []), 
                                    color='info'), 
                                    #width = {"size": 5, "offset": 0}),
                                    xs = 12, sm = 12, md = 12, lg = 12, xl = 12),
                
                                   ], 
                        no_gutters = False, justify = 'left',
        
                       ),
                       
                
                dbc.Row(children = [dbc.Col(html.Div(
                                    dcc.Graph(id = "fig1", figure = {})),
                                    width = {"size": 'auto', "offset": 0},),
                                    #xs = 12, sm = 12, md = 12, lg = 12, xl = 12), 
                                   ],
        
                        no_gutters=False, justify = 'around'
                        
                        ),

    
                    dbc.Row(
                    [
                        dbc.Col(html.Div("The boundaries and names shown and the designations used on maps do not imply endorsement or acceptance.",
                                       style ={"text-align": "center", "color": '#808080'}),
                                     xs = 12, sm = 12, md = 12, lg = 12, xl = 12),
                    ], 
                        no_gutters = True, justify = 'center',
                    ),
                                                
               dbc.Row([dbc.Col(html.Br())]), 
               dbc.Row([dbc.Col(html.Br())]), 
                        
#Bar charts with year and month
    
                dbc.Row(children = [dbc.Col([html.H3("Dead and Missing Migrants by Year"),
                                             
                                        html.Div(
                                        dcc.Graph(id = "fig2", figure = {}))
                                            ],
                                             
                                    #width = {"size": 5, "offset": 0}),
                                    xs = 12, sm = 12, md =12, lg = 12, xl = 6),
                                
                                    dbc.Col([html.H3("Dead and Missing Migrants by Month"),
                                             html.Div(dcc.Graph(id = "fig3", figure = {})),
                                            ],
                                            
                                    # width = {"size": 5, "offset": 0})
                                    xs = 12, sm = 12, md = 12, lg = 12, xl = 6)
                                    
                                   ],
                        
                        no_gutters=False, justify = 'around'
                       ),
                                            
               dbc.Row([dbc.Col(html.Br())]), 
               dbc.Row([dbc.Col(html.Br())]), 
    
#Graphs with Cause of Death and region
                                    
               dbc.Row(children = [dbc.Col([html.H3("Incident Count by Cause of Death"),
                                          #width = {"size": 5, "offset": 0},), 
                                          html.Div(dcc.Graph(id = "fig4", figure = {})),
                                            
                                          html.Div("A single incident can present more than one cause of death.",
                                        style ={"text-align": "center", "color": '#808080'}),
                                        
                                           ],
                                           
                                           xs = 12, sm = 12, md = 12, lg = 12, xl = 6),
                                   
                                   
                                   dbc.Col([html.H3("Dead and Missing Migrants by Region"),
                                          #width = {"size": 5, "offset": 0}),
                                           html.Div(dcc.Graph(id = "fig5", figure = {})),
                                           ],
                                           
                                          xs = 12, sm = 12, md = 12, lg = 12, xl = 6), 
                                  ],
                       no_gutters=False, justify = 'around'
                       ),
    
               dbc.Row([dbc.Col(html.Br())]), 
               dbc.Row([dbc.Col(html.Br())]), 
    
    
#Treemap with countries
    
               dbc.Row(
                    [
                        dbc.Col(html.H3("Dead and Missing Migrants by Country",
                                       style ={"text-align": "center"}),
                                     xs = 12, sm = 12, md = 12, lg = 12, xl = 12),
                    ], 
                        no_gutters = True, justify = 'center',
        
                       ),

    
                dbc.Row(children = [dbc.Col(html.Div(
                                    dcc.Graph(id = "fig6", figure = {})),
                                    width = {"size": 'auto', "offset": 0},),
                                    #xs = 12, sm = 12, md = 12, lg = 12, xl = 12), 
                                   ],
        
                        no_gutters=False, justify = 'around'), 
    
                    dbc.Row(
                    [
                        dbc.Col(html.Div("The category Not Found corresponds to incidents that occurred at sea or in territories that could not be identified with a country.",
                                       style ={"text-align": "center", "color": '#808080'}),
                                     xs = 12, sm = 12, md = 12, lg = 12, xl = 12),
                    ], 
                        no_gutters = True, justify = 'center',
                    ),
    
                dbc.Row([dbc.Col(html.Br())]), 
                dbc.Row([dbc.Col(html.Br())]), 
    
#Pie chart with sex and age  
                                    
               dbc.Row(children = [dbc.Col([html.H3("Dead and Missing Migrants by Sex"),
                                          html.Div(dcc.Graph(id = "fig7", figure = {})),
                                        
                                           ],
                                           
                                           xs = 12, sm = 12, md = 12, lg = 12, xl = 6),
                                   
                                   
                                   dbc.Col([html.H3("Dead and Missing Migrants by age"),
                                           html.Div(dcc.Graph(id = "fig8", figure = {})),
                                           ],
                                           
                                          xs = 12, sm = 12, md = 12, lg = 12, xl = 6), 
                                  ],
                       no_gutters=False, justify = 'around'
                       ),
    
                dbc.Row([dbc.Col(html.Br())]), 
                dbc.Row([dbc.Col(html.Br())]), 
    
#Download button
     dbc.Row(
                    
       [html.Button("Download Selected Data", id="btn_dta"), dcc.Download(id="download_csv")],
       no_gutters=False, justify = 'center'),
    
                dbc.Row([dbc.Col(html.Br())]), 
    
     dbc.Row(
                    [
                        dbc.Col(html.Div("Once you have clicked this button, please hit refresh before doing a new search.",
                                       style ={"text-align": "center", "color": '#808080'}),
                                     xs = 4, sm = 4, md = 4, lg = 4, xl = 4),
                    ], 
                        no_gutters = True, justify = 'center',
                    ),
    

                dbc.Row([dbc.Col(html.Br())]), 
                dbc.Row([dbc.Col(html.Br())]),                        
    
], fluid = True)


# In[10]:


#Storing data

@app.callback(Output('memory-output', 'data'),
              Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def filter(Reported_Year, Region, Country, COD, Migration_Route):
    

    if Reported_Year != "All":
        MM_Year = MM.query("Reported_Year == @Reported_Year")
    else:
        MM_Year = MM

    if Region != "All":
        MM_Region = MM_Year.query("Region == @Region")
    else:
        MM_Region = MM_Year
            
    if Country != "All":
        MM_Country = MM_Region.query("Country == @Country")
    else:
        MM_Country = MM_Region
            
    if Migration_Route != "All":
        MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
    else:
        MM_Route = MM_Country

    if COD != "All":
        MM_COD = MM_Route.loc[MM[COD] ==1]
    else:
        MM_COD = MM_Route
    
    return MM_Route.to_dict("records")


# In[11]:


# D. Defining callbacks to update the graphs


# In[12]:


#D.0 Counting the number of incidents corresponding to the filtered data


def callback(n_clicks, data):
    
    MM_download = pd.DataFrame.from_dict(data)
    
    if n_clicks is None:
            
        raise PreventUpdate
    else:
    
        return dict(content = MM_download.iloc[0:, 0:20].to_csv(), filename = "Missing_Migrants.csv")


@app.callback(Output('text1', 'children'), Input("memory-output", 'data'))

def callback(data):
    
    try:
        MM_summary = pd.DataFrame.from_dict(data)
            
        incidents = MM_summary["Web_ID"].count()
        dead_and_missing = MM_summary["Total_Dead_and_Missing"].sum()
            
        return f"""There are {incidents} incidents that correspond to the selected characteristics. In them, {dead_and_missing} migrants were reported as or missing."""
    
    except: 
        
        return """No content"""


# In[13]:


# D.1 Map with all incidents
@app.callback(Output('fig1', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route
            
        return px.scatter_mapbox(
            MM_COD,
            lat="Latitude", 
            lon="Longitude", 
            hover_name="Cause_of_Death", 
            hover_data ={"Log_Dead":False,"Latitude":False,"Longitude":False,"Migration_Route":False,"Number_Dead":True,"Minimum_Missing":True, "Reported_Year":True}, 
            size = "Log_Dead",
            size_max =12,
            custom_data = ["URL1"],
            mapbox_style ="open-street-map",
            zoom=2,
            opacity = .5,
            height=800,
            width =1900,
            color="Migration_Route",
            color_discrete_sequence=px.colors.sequential.RdBu).update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                              "paper_bgcolor": "rgba(0, 0, 0, 0)"},
                                                                            legend=dict(yanchor="bottom", y=0.01,
                                                                                                   xanchor="left", x=0.01,
                                                                                                  title = "Migration Route"))
    except: 
        return px.scatter().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[14]:


#D.2 button that shows link for selected point in scatterplot map
@app.callback(
    Output('web_link', "children"),
    [Input("fig1", 'clickData')])

def display_click_data(clickData):
    if clickData is None:
        return ("Click on a bubble to get the associated news article")
    else:
        print(clickData["points"][0]["customdata"][0])
        the_link = clickData['points'][0]['customdata'][0]
        the_link = the_link.split(",")
        if the_link is None:
            return 'No Article Available'
        else:
            return html.A(the_link, href=the_link[0], target = "_blank")


# In[15]:


# D.3 Bar chart with deaths per year
@app.callback(Output('fig2', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route
            

        return px.bar(MM_COD.groupby(by="Reported_Year").sum(),
                      y = ["Number_Dead", "Minimum_Missing"],
                      height = 500, width = 750, color_discrete_sequence=px.colors.sequential.RdBu).update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                                                                   "paper_bgcolor": "rgba(0, 0, 0, 0)"},
                                                                                                                  xaxis_tickangle=-90, xaxis_title = "Date",
                                                                                                                 yaxis_title= "Number of Migrants",
                                                                                                                 legend=dict(yanchor="top", y=0.99,
                                                                                                                             xanchor="right", x=0.99,
                                                                                                                            title =""))
                                                                                        
    except:
        
        return px.bar().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[16]:


# D.4 Time series with dead and missing per month
@app.callback(Output('fig3', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route

        MM_COD["Reported_Date"] = pd.to_datetime(MM_COD["Reported_Date"])
        MM_date = MM_COD.set_index("Reported_Date")
        MM_month = MM_date.resample("M").sum()


        return px.bar(MM_month, y= ['Number_Dead', "Minimum_Missing"], height = 500, width = 750,
                      color_discrete_sequence=px.colors.sequential.RdBu).update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                                        "paper_bgcolor": "rgba(0, 0, 0, 0)"},
                                                                                       xaxis_tickangle=-90, xaxis_title = "Date",
                                                                                      yaxis_title="Number of Migrants",
                                                                                       legend=dict(yanchor="top", y=0.99,
                                                                                                   xanchor="right", x=0.99,
                                                                                                  title = ""))
        
    except:
        
        return px.bar().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[17]:


# D.4 Bar chart with number of incidents by COD
@app.callback(Output('fig4', 'figure'), Input('Reported_Year', 'value'),
             Input('Region', 'value'), Input('Country', 'value'),
             Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
   
   try:
       if Reported_Year != "All":
           MM_Year = MM.query("Reported_Year == @Reported_Year")
       else:
           MM_Year = MM

       if Region != "All":
           MM_Region = MM_Year.query("Region == @Region")
       else:
           MM_Region = MM_Year
           
       if Country != "All":
           MM_Country = MM_Region.query("Country == @Country")
       else:
           MM_Country = MM_Region
           
       if Migration_Route != "All":
           MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
       else:
           MM_Route = MM_Country

       if COD != "All":
           MM_COD = MM_Route.loc[MM_Route[COD]==1]
       else:
           MM_COD = MM_Route
       
       COD_df = MM_COD[['Drowning', 'Suicide', 'Accident', 'Accident_vehicle', 'Hypothermia',
       'Dehydration', 'Exposure', 'Accident_train', 'Violence', 'Shot',
       'Sickness', 'Accident_border_wall', 'Starvation', 'Burning', 'Asphyxia','Hyperthermia', 'Sexual_violence', 'Hypoglycemia', 'Other']]
       COD_df = COD_df.sum().to_frame().reset_index()
       COD_df.columns = ["COD_category", "Incident_Count"] 
       COD_df = COD_df.sort_values(by ="Incident_Count", ascending=True)    

       return px.bar(COD_df,
                     y="COD_category",
                     x = "Incident_Count",
                     height = 500,
                     width = 750,
                     orientation = "h",
                     color="Incident_Count",
                     color_continuous_scale='RdBu').update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                  "paper_bgcolor": "rgba(0, 0, 0, 0)"},
                                                                  xaxis_tickangle=-90,
                                                                  xaxis_title= "Cause of Death",
                                                                  yaxis_title = "Number of Incidents")
   
   except:
       
       return px.bar().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[18]:


# D.5 Pie Chart: number of deaths per region
@app.callback(Output('fig5', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route
            
        return px.pie(MM_COD, values='Total_Dead_and_Missing', names='Region',
                      height = 500, width = 750,
                      color_discrete_sequence=px.colors.sequential.RdBu).update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                                        "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    
    
    except:
        
        return px.pie().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})
    


# In[19]:


# D.6 Treemap: number of deaths by country

@app.callback(Output('fig6', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route
            
        Country_df = MM_COD[["Country", 'Total_Dead_and_Missing']]
        Country_df= Country_df.groupby(["Country"]).sum().reset_index()
            
        return px.treemap(Country_df,
                 path=['Country'],
                 values='Total_Dead_and_Missing',
                 labels = ['Country', 'Total_Dead_and_Missing'],
                 height=500,
                 width =1900,
                 color = "Total_Dead_and_Missing",
                 color_continuous_scale='RdBu')

    except:
        
        return px.treemap().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[20]:


# D.7 Pie Chart: number of deaths by sex
@app.callback(Output('fig7', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route
            
        Sex_df = MM_COD[['Females', 'Males', 'Unknown_Sex']]
        Sex_df = Sex_df.sum().to_frame().reset_index()
        Sex_df.columns = ["Sex", "Total_Dead_and_Missing"]  

            
        return px.pie(Sex_df, 
                      values='Total_Dead_and_Missing', 
                      names='Sex',
                      height = 500, 
                      width = 750,
                      hole = .4,
                      color_discrete_sequence=px.colors.sequential.RdBu).update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                                        "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    
    
    except:
        
        return px.pie().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[21]:


# D.8 Pie Chart: number of deaths by age
@app.callback(Output('fig8', 'figure'), Input('Reported_Year', 'value'),
              Input('Region', 'value'), Input('Country', 'value'),
              Input('COD', 'value'), Input('Migration_Route', 'value'))

def callback(Reported_Year, Region, Country, COD, Migration_Route):
    
    try:
        if Reported_Year != "All":
            MM_Year = MM.query("Reported_Year == @Reported_Year")
        else:
            MM_Year = MM

        if Region != "All":
            MM_Region = MM_Year.query("Region == @Region")
        else:
            MM_Region = MM_Year
            
        if Country != "All":
            MM_Country = MM_Region.query("Country == @Country")
        else:
            MM_Country = MM_Region
            
        if Migration_Route != "All":
            MM_Route = MM_Country.query("Migration_Route == @Migration_Route")
        else:
            MM_Route = MM_Country

        if COD != "All":
            MM_COD = MM_Route.loc[MM_Route[COD]==1]
        else:
            MM_COD = MM_Route
            
        Age_df = MM_COD[["Children", 'Unknown_age_status']]
        Age_df = Age_df.sum().to_frame().reset_index()
        Age_df.columns = ["Age_Status", "Total_Dead_and_Missing"]  

            
        return px.pie(Age_df, 
                      values='Total_Dead_and_Missing', 
                      names='Age_Status',
                      height = 500, 
                      width = 750,
                      hole = .4,
                      color_discrete_sequence=px.colors.sequential.RdBu).update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)",
                                                                                        "paper_bgcolor": "rgba(0, 0, 0, 0)"})
    
    
    except:
        
        return px.pie().update_layout({"plot_bgcolor":"rgba(0, 0, 0, 0)","paper_bgcolor": "rgba(0, 0, 0, 0)"})


# In[22]:


#D9 Download csv file with selected data

@app.callback(Output("download_csv", 'data'), Input("btn_dta", "n_clicks"),
              Input("memory-output", 'data'), prevent_initial_call=True)

def callback(n_clicks, data):
    
    MM_download = pd.DataFrame.from_dict(data)
    
    if n_clicks is None:
            
        raise PreventUpdate
    else:
    
        return dict(content = MM_download.iloc[0:, 0:20].to_csv(), filename = "Missing_Migrants.csv")



# E. run app in server
if __name__ == '__main__':
    app.run_server(debug=False, port=8053)




