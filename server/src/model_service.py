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
    print(os.getcwd())
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                     dtype={"fips": str})
    fig = px.choropleth(df, geojson=counties, locations='fips', color='unemp',
                        color_continuous_scale="Viridis",
                        range_color=(0, 12),
                        scope="usa",
                        labels={'unemp': 'unemployment rate'}
                        )
    # Set the map footer.
    #plt.annotate("Updated on " + get_now(), xy=(-.8, -3.2), size=14, xycoords='axes fraction')
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

def prepare_model():

    # Run all model
    generate_map()

    # Set scheduling
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(func=generate_map,
                      trigger="cron",
                      hour="21",
                      id="map_schedule",
                      name="map_schedule",
                      replace_existing=True)

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
