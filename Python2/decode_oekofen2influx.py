#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Created by: Peter Fürle, python2.7
# Execute ./decode_oekofen2influx.py 'j2.txt' to use a recorded test file as input
#
# Fetches the current data from the JSON interface of an Oekofen pellet boiler
# See https://github.com/thannaske/oekofen-json-documentation for an inofficial documentation 
# of the API
#
# Best put this script into a Cronjob to run e.g. every 4 minutes (see README.md)
# Attempt with .decode("cp1252")

import io
import sys
import json
import urllib2
import requests
from influxdb import InfluxDBClient

#API URL of the Oekofen Touch Control of the heater
json_quelle = "http://192.168.178.23:4321/97VI/all"

# Configure InfluxDB connection variables
host = "127.0.0.1"
port = 8086
user = "grafana"
password = "pellematic"
dbname = "oekofen"


# Connect Influx Database
client = InfluxDBClient(host, port, user, password, dbname)



# Each part gets its own measurement (hk1,hk2,pu1,se1,..)
def eintragen(measurement,name,wert):
    # Apparently Influx can't handle empty strings, fix here:
    if wert == "":
        wert = " "    
    info=[
        {
            "measurement": measurement,
            "fields":{
                name : wert
                }
            }
        ]
    #print(info)
    client.write_points(info)
    return



# Check if the value is a number, otherwise it's a String
def num(s):
    try:
        return float(s)
    except ValueError:
        return s



# Iterate through all elements of the JSON output, post-process and submit 
# them into the database
def iter_dict(data):
    for key in data:
        if isinstance(data[key], dict):
           #print("Anzahl Paare: "+str(len(d[key])))
            bereich = key
            iter_dict(data[key])
            #print(str(bereich))
            for attribute, value in data[key].items():
                w = num(value)
                if "mode" in str(attribute):
                    w = int(w)
                elif "_prg" in str(attribute):
                    w = int(w)
                elif str(attribute)=="L_state":
                    w = int(w)
                elif "temp_" in str(attribute):
                    w = float(w)/10
                    #print(str(attribute)+"  temp_  "+str(w))
                elif "_temp" in str(attribute):
                    w = float(w)/10
                    #print(str(attribute)+"  _temp  "+str(w))
                elif "ambient" in str(attribute):
                    w = float(w)/10
                elif "L_tp" in str(attribute):
                    w = float(w)/10
                elif "L_day" in str(attribute):
                    w = float(w)/10
                elif "L_yesterday" in str(attribute):
                    w = float(w)/10
                elif "L_sp" in str(attribute):
                    w = float(w)/10
                elif str(attribute)=="L_flow":
                    w = float(w)/100
                elif str(attribute)=="L_pwr":
                    w = float(w)/10
                #if "?" in str(w):
                #    w = str(w).replace("u?e","usse")
                #    w = str(w).replace("?ber","ueber")
                #    w = str(w).replace("t?t","taet")
                eintragen(str(key),str(attribute),w)


#print(len(sys.argv))

if len(sys.argv) == 2:
    # instead of querying the data, read it from a recorded file
    # (e.g. test data for adapting to a new data set or format)
    testfile = io.open(sys.argv[1], encoding='cp1252').read()
    print(sys.argv[1])
    d = json.loads(testfile)
else:
    # Query all data via JSON API
    #url = (urllib2.urlopen(request).geturl() + '?output=json')
    #    request = str(url)
    #    request_read = urlopen(request).read().decode("utf-8")
    response = urllib2.urlopen(json_quelle)
    #mydata = response.read()
    mydata = response.read().decode("cp1252")
    d = json.loads(mydata)
    #print(d)


# Iterate through the results
iter_dict(d)


print("All data queried from Oekofen JSON API and submitted into InfluxDB "+dbname)

