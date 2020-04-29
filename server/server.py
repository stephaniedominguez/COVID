import os
from flask import Flask, render_template
from urllib.request import urlopen
import json
import pandas as pd
import plotly.express as px
import schedule
import time


app = Flask(__name__)

# Import controller
import src.controller as ctr

# Initiate root url
@app.route("/")
def hello( ): 
    return render_template("index.html", template_folder='template'); 

# Bind other url
app.add_url_rule('/decision', view_func=ctr.get_decision)

@app.route("/map/")
def map( ):
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                   dtype={"fips": str})
    #counties["features"][0]
    fig = px.choropleth(df, geojson=counties, locations='fips', color='unemp',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
                           scope="usa",
                           labels={'unemp':'unemployment rate'}
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()

# TODO: Is that good? 
def scheduling():
    schedule.every().day.at("21:30").do(map)
# Run application
app.run(host='0.0.0.0', port=8018)