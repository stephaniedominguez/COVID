#!/usr/bin/env python3
#Utility
import urllib
import os
import datetime
import socket

#Data Science
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from hmmlearn import hmm

#Google API
import google.auth
from google.cloud import bigquery
from google.cloud import bigquery_storage_v1beta2


HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)

def retrive_data():
    confirmed_ts = pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv")
    return confirmed_ts