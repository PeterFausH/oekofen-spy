## -*- coding: utf-8 -*-
# funktioniert nicht mehr ab JSON V4.0 da dort kein lokaler Webserver mehr bereitsteht
# python oekofen_fetch_csv.py
# ermöglicht die csv von einer Pellematic abzuholen und einen Wert dort auszulesen
# der Wert wird aus der letzten (aktuellen) Zeile geholt.
# die csv Dateien haben typischerweise am Ende des Tages 1440 Zeilen
# in meinen Anlagen wird zwischen 0 Uhr und 1 Uhr nichts geschrieben,
# somit fehlen Daten aus dieser Stunde bei mir.
#
# bitte so aufrufen:")
# python oekofen_fetch_csv.py Einschubzeit 25
# die letzte Zahl ist die Spalte beginnend mit 0 zu zählen
# Spalte0 ist das Datum, Spalte1 ist die Uhrzeit und so weiter
# default ist auf Einschubzeit und 25 gesetzt.
# das passt nicht bei allen Datensätzen. Es kommt dabei auf die
# Ausstattung der Anlage mit optionen wie Solar, Zirkulationspumpe etc. an
#
# crontab:
#    */2 * * * *  pi   /usr/bin/python /home/pi/oekofen_fetch_csv.py Einschubzeit 25
#
# erstellt: Peter Fürle, pf@nc-x.com, 30.01.2022
# copyright MINT, freie Nutzung, Änderung unter Namensnennung.


import os
import csv
import sys
import urllib
import urllib.request #python3
from datetime import date, timedelta
from influxdb import InfluxDBClient


#hier die richtige IP-Adresse eintragen
source = "http://192.168.22.189/logfiles/pelletronic/"

# Configure InfluxDB connection variables
host = "127.0.0.1" 
port = 8086 
user = "pellematic"
password = "smart"
# notfalls auch anpassen
dbname = "oekofen" 

# Influx Datenbank verbinden
client = InfluxDBClient(host, port, user, password, dbname)

# den Dateinamen mit aktuellem Datum zusammenbauen
d_heute = date.today()
heute = d_heute.strftime('%Y%m%d')
csvfile = "touch_" + heute + ".csv"
destin = "/home/pi/csv_von_oekofen.csv"

# nur für Tests nutzen
testfile = "/home/peterf/python-scripte/Touch_20220122.csv" #für lokale tests
dummy = source+"touch_20220127.csv"

# das alte csv-file löschen
try:
    os.remove(destin)
except OSError:
    pass

#cache leeren klappt noch nicht
urllib.request.urlcleanup()

# U-Prog um in die INflux-Datenbank eintragen
def eintragen(measurement,name,wert):
    if wert == "":
        wert = " "
    info=[{"measurement": "oekofen","tags": {"bereich": measurement},"fields": {measurement+"_"+name+"n" : wert}}]
    print(info)
    client.write_points(info, time_precision='m')
    return

# U-Prog zum Prüfen ob Wert numerisch sein könnte, sonst String
def num(s):
    try:
        return float(s)
    except ValueError:
        return s

# hoffentlich ist die Heizung erreichbar
print("hole csv: ",source+csvfile)
try:
    response = urllib.request.urlopen(source+csvfile)
    #response = urllib.request.urlopen(dummy)
except urllib.error.HTTPError as ex:
    print('Problem:', ex)

# Bezeichnung und Feldnummer als Parameter übergeben
# wurden 2 Parameter mit angegeben ?
if len(sys.argv) == 3:
    feldbezeichnung=sys.argv[1]
    spaltennummer=int(sys.argv[2])
    print("deine Parameter:",feldbezeichnung, spaltennummer)
else:
    print("bitte so aufrufen:")
    print("  python oekofen_fetch_csv.py Einschubzeit 25")
    print("die letzte Zahl ist die Spalte beginnend mit 0 zu zählen")
    print("Spalte0 ist das Datum, Spalte1 ist die Uhrzeit und so weiter...")
    #default-Einstellung
    feldbezeichnung = "Einschubzeit"
    spaltennummer=25

#alles erstmal einlesen und als String anlegen   
content =response.read().decode('latin-1')
#in einzelne Zeilen splitten
data = content.splitlines(True)
if len(data):
    #die letzte Zeile holen
    last = data[-2]
    #in Einzelwerte aufsplitten 
    x=last.split(";")
    # Komma in Punkt ändern um in Zahl konvertieren zu können
    n = float(x[spaltennummer].replace(',', '.'))
    # Kontrollausgabe Uhrzeit und Einschubzeit
    print('letzter gelesener Wert',x[1],n)
    # in die Influx-Datenbank als float schreiben
    eintragen('csv',feldbezeichnung,num(n))
else:
    print("keine Daten von Pellematic holen können!")
    
