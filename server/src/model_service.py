from pmdarima.arima import auto_arima
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
import numpy as np


def get_now():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(get_now() + " " + msg, file=sys.stdout)


# TODO: Do we still use this??????????????????????????
# def interactive_map():
#     log("Start generating interactive map")
#     df_sample = pd.read_csv(
#         'https://raw.githubusercontent.com/plotly/datasets/master/minoritymajority.csv')
#     df_sample_r = df_sample[df_sample['STNAME'] == 'California']

#     values = df_sample_r['TOT_POP'].tolist()
#     fips = df_sample_r['FIPS'].tolist()

#     colorscale = [
#         'rgb(193, 193, 193)',
#         'rgb(239,239,239)',
#         'rgb(195, 196, 222)',
#         'rgb(144,148,194)',
#         'rgb(101,104,168)',
#         'rgb(65, 53, 132)'
#     ]

#     fig = ff.create_choropleth(
#         fips=fips, values=values, scope=[
#             'CA', 'AZ', 'Nevada', 'Oregon', ' Idaho'],
#         binning_endpoints=[14348, 63983, 134827, 426762, 2081313], colorscale=colorscale,
#         county_outline={'color': 'rgb(255,255,255)', 'width': 0.5}, round_legend_values=True,
#         legend_title='Population by County', title='California and Nearby States'
#     )
#     fig.layout.template = None
#     fig.show()
#     log("End generating interactive map")


def update_mobility():
    log("Start updating mobility")

    # Import mobility from url
    url = 'https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv'
    mobility = pd.read_csv(url)

    filterlist = ['retail_and_recreation_percent_change_from_baseline',
                  'grocery_and_pharmacy_percent_change_from_baseline',
                  'parks_percent_change_from_baseline',
                  'transit_stations_percent_change_from_baseline',
                  'workplaces_percent_change_from_baseline',
                  'residential_percent_change_from_baseline']

    # Get ONLY US mobility
    country = mobility['country_region'].value_counts()
    countrylist = country.index.to_list()
    usmobility = mobility[mobility['country_region'] == 'United States']

    # Change column names
    usmobility = usmobility.rename(
        columns={"sub_region_1": "Province_State", "sub_region_2": "Admin2"})

    # Split "county" text out of county
    countylist = []
    txt = usmobility['Admin2'].to_list()
    for i in txt:
        i = str(i)
        countylist.append(i.replace(' County', ''))
    usmobility['Admin2'] = countylist

    usmobility['Lookup'] = usmobility['Admin2'] + usmobility['Province_State']
    mobilitylist = usmobility['Lookup'].value_counts().index.to_list()

    for i in mobilitylist:
        usmobility[usmobility['Lookup'] ==
                   i] = usmobility[usmobility['Lookup'] == i].fillna(method='ffill')

    usmobility['Lookup'] = usmobility['Lookup'] + usmobility['date']
    lookuplist = usmobility['Lookup'].to_list()
    usmobility = usmobility.transpose()
    usmobility.columns = lookuplist
    usmobility = usmobility.transpose()

    filterlist1 = filterlist.copy()
    filterlist1.append('Lookup')
    usmobility = usmobility.loc[:, filterlist1]

    # Update usmobility csv
    usmobility.to_csv('usmobility.csv', index=False)
    log("End updating mobility")


def prepare_data():
    """
    Pulling data from JHU repo and returning processed dataframes, and a FIPS dictionary.
    """
    log("Start preparing data")
    confirmed = pd.read_csv(
        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv")
    # preparing to remove some areas, not in US counties
    confirmed = confirmed.replace('Unassigned', np.nan)
    confirmed = confirmed.dropna()  # removing said areas
    confirmed['FIPS'] = confirmed['FIPS'].astype('int32').astype(
        'str').str.zfill(5)  # Setting FIPS to be strings
    confirmed = confirmed.rename(
        columns={'Province_State': 'State', 'Admin2': 'County'})

    # making a dictionary FIPS to counties and states
    fips_dict = confirmed.iloc[:-51,
                               :].set_index('FIPS')[['State', 'County']].to_dict('index')

    confirmed = confirmed.transpose()  # Transposing df
    confirmed.columns = confirmed.iloc[4]  # Setting column names
    confirmed = confirmed.iloc[11:, :-51]  # Slicing df
    confirmed = confirmed.reset_index()  # Pulling out the dates
    confirmed = confirmed.rename(
        columns={"index": "Date"})  # Renaming date column
    # changing date column to datetime
    confirmed['Date'] = pd.to_datetime(confirmed['Date'], format='%m/%d/%y')
    log("End preparing data")

    return confirmed, fips_dict


def forecast_all(confirmed, dictionary, horizon):
    """
    Running an ARIMA forecast, predicting the horizon into the future.
    """
    log("Start forecasting")
    result = pd.DataFrame()   # Blank DataFrame
    second_df = pd.DataFrame()

    for fips in dictionary:

        temp_df = confirmed.loc[:, [fips]]

        if temp_df.iloc[-1, 0] != 0:
            stepwise_model_confirmed = auto_arima(temp_df, start_p=1, start_q=1,
                                                  max_p=30, max_q=30,
                                                  start_P=0, seasonal=False,
                                                  error_action='ignore',
                                                  suppress_warnings=True,
                                                  stepwise=True,
                                                  max_order=None)

            stepwise_model_confirmed.fit(temp_df)
            forecast_confirmed = stepwise_model_confirmed.predict(
                n_periods=horizon)
            conf_pred = forecast_confirmed[-1]-temp_df.iloc[-1, 0]
        else:
            conf_pred = 0

        result[fips] = [dictionary[fips]['County'],
                        dictionary[fips]['State'], conf_pred]

        second_df[fips] = forecast_confirmed

    result = result.transpose().reset_index()
    result = result.rename(
        columns={'index': 'FIPS', 0: 'County', 1: 'State', 2: 'Prediction'})
    result['Prediction'] = result['Prediction'].astype('int32')
    second_df = second_df.astype('int32')
    log("End forecasting")

    return result, second_df


def get_predictions(horizon=7):
    log("Start prediction")

    confirmed, dictionary = prepare_data()

    results, second = forecast_all(confirmed, dictionary, horizon)

    results.to_csv('predictions.csv', index=False)
    second.to_csv('VerbosePredictions.csv', index=False)
    log("End prediction")


def generate_map():
    log("Start generating map")

    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    df = pd.read_csv("ML_results.csv")
    df['FIPS'] = df['FIPS'].astype('int32').astype('str').str.zfill(5)
    df['ML'] = df['ML'].astype('str')
   
    df['text'] = 'County: ' + df['County'] +'</br>'+'ML: ' + df['ML']
    fig = px.choropleth(df, geojson=counties, locations='FIPS', color='Prediction',  hover_name='text',
                        color_continuous_scale="Viridis",
                        range_color=(0, 100),
                        scope="usa",
                        labels={'County': 'New cases'}
                        )
    # Set the map footer.
    fig.add_annotation(text="Updated on " + get_now(),
                       x=0.1, y=0, showarrow=False)

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Save map to local directory
    plot(fig, filename="templates/map_plot.html", auto_open=False)
    log("End generating map")


def arima_forecast():
    # Load data , train the model, and get prediction
    #get_predictions()

    # Generate the map
    generate_map()


def prepare_mobility(scheduler):
    ## Update Mobility ####
    # update_mobility()

    # Set scheduling every Saturday
    scheduler.add_job(func=update_mobility,
                      trigger="cron",
                      day_of_week="5",
                      id="update_mobility",
                      name="update_mobility",
                      replace_existing=True)


def prepare_forecast(scheduler):
    arima_forecast()

    # Set scheduling every 9pm
    #scheduler.add_job(func=arima_forecast,
    #                  trigger="cron",
    #                  hour="21",
    #                  id="get_predictions",
    #                 name="get_predictions",
    #                  replace_existing=True)


def prepare_model():

    scheduler = BackgroundScheduler()
    scheduler.start()

    #prepare_mobility(scheduler)

    prepare_forecast(scheduler)

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
