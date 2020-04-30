from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
from plotly.offline import plot
from flask import render_template
import os
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
    df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                     dtype={"fips": str})
    # counties["features"][0]
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
    plot(fig, filename="server/templates/map_plot.html", auto_open=False)
    log("End generating map")


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
