from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
from plotly.offline import plot
from flask import render_template
import os
import plotly.figure_factory as ff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import time
import sys
import datetime


def get_now():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(get_now() + " " + msg, file=sys.stdout)


def generate_map():
    log("Start generating map")
    
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    df = pd.read_csv("./src/thisone.csv",
                     dtype={"fips": str})
    df['FIPS'] = df['FIPS'].astype('int32').astype('str').str.zfill(5)
    df['text'] ='State: '+ df['Admin2']  
    fig = px.choropleth(df, geojson=counties, locations='FIPS', color='Confirmed',  hover_name= 'text',
                        color_continuous_scale="Viridis",
                        range_color=(0, 100),
                        scope="usa",
                        labels={'county': 'Confirmed cases'}
                        )
    # Set the map footer.
    fig.add_annotation(text="Updated on " + get_now(),
                       x=0.1, y=0, showarrow=False)

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Save map to local directory
    plot(fig, filename="templates/map_plot.html", auto_open=False)
    log("End generating map")


def interactive_map():
    log("Start interactive map")
    df_sample = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/minoritymajority.csv')
    df_sample_r = df_sample[df_sample['STNAME'] == 'California']

    values = df_sample_r['TOT_POP'].tolist()
    fips = df_sample_r['FIPS'].tolist()

    colorscale = [
        'rgb(193, 193, 193)',
        'rgb(239,239,239)',
        'rgb(195, 196, 222)',
        'rgb(144,148,194)',
        'rgb(101,104,168)',
        'rgb(65, 53, 132)'
    ]

    fig = ff.create_choropleth(
        fips=fips, values=values, scope=['CA', 'AZ', 'Nevada', 'Oregon', ' Idaho'],
        binning_endpoints=[14348, 63983, 134827, 426762, 2081313], colorscale=colorscale,
        county_outline={'color': 'rgb(255,255,255)', 'width': 0.5}, round_legend_values=True,
        legend_title='Population by County', title='California and Nearby States'
    )
    fig.layout.template = None
    fig.show()

def update_mobility():
    #Import mobility from url
    url = 'https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv'
    mobility = pd.read_csv(url)

    filterlist = ['retail_and_recreation_percent_change_from_baseline',
    'grocery_and_pharmacy_percent_change_from_baseline',
    'parks_percent_change_from_baseline',
    'transit_stations_percent_change_from_baseline',
    'workplaces_percent_change_from_baseline',
    'residential_percent_change_from_baseline']

    #Get ONLY US mobility
    country = mobility['country_region'].value_counts()
    countrylist = country.index.to_list()
    usmobility = mobility[mobility['country_region']=='United States']

    #Change column names
    usmobility = usmobility.rename(columns={"sub_region_1":"Province_State", "sub_region_2": "Admin2"})

    #Split "county" text out of county
    countylist = []
    txt = usmobility['Admin2'].to_list()
    for i in txt:
        i = str(i)
        countylist.append(i.replace(' County', ''))
    usmobility['Admin2'] = countylist

    usmobility['Lookup'] = usmobility['Admin2'] + usmobility['Province_State'] 
    mobilitylist = usmobility['Lookup'].value_counts().index.to_list()

    for i in mobilitylist:
        usmobility[usmobility['Lookup']==i] = usmobility[usmobility['Lookup']==i].fillna(method='ffill')

    usmobility['Lookup'] = usmobility['Lookup'] + usmobility['date']
    lookuplist = usmobility['Lookup'].to_list()
    usmobility = usmobility.transpose()
    usmobility.columns = lookuplist
    usmobility = usmobility.transpose()

    filterlist1 = filterlist.copy()
    filterlist1.append('Lookup')
    usmobility = usmobility.loc[:,filterlist1]

    #Update usmobility csv
    usmobility.to_csv('usmobility.csv',index=False)


def prepare_model():

    ## Update Map #####
    # Run all model
    generate_map()

    # Set scheduling every 9pm
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(func=generate_map,
                      trigger="cron",
                      hour="21",
                      id="map_schedule",
                      name="map_schedule",
                      replace_existing=True)

    ## Update Mobility ####
    #update_mobility()

    # Set scheduling every Saturday
    scheduler.add_job(func=update_mobility,
                      trigger="cron",
                      day_of_week="5",
                      id="update_mobility",
                      name="update_mobility",
                      replace_existing=True)

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


