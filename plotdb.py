#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# dl-120th - Control data logger Voltcraft DL-120TH
#
# Copyright 2012 Patrick Rabu

import argparse
import sys
import os
import sqlite3
import locale

import datetime
from datetime import date
from datetime import time
from datetime import timedelta

from matplotlib import pyplot
from matplotlib import dates as mdates
from matplotlib.dates import date2num, epoch2num

import cairo
import pycha.line

def lineChart(output, data1, data2):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 400)

    dataSet = (
        ('Temp', data1),
        )

    options = {
        'background': {
            'color': '#eeeeff',
            'lineColor': '#444444'
        },
        'colorScheme': {
            'name': 'gradient',
            'args': {
                'initialColor': 'blue',
            },
        },
        'legend': {
            'hide': True,
        },
    }
    chart = pycha.line.LineChart(surface, options)

    chart.addDataset(dataSet)
    chart.render()

    surface.write_to_png(output)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Copy content of dat file into sqlite DB.', 
        prog='plotdb.py', version='0.1')
    parser.add_argument('-m', '--month', help='Month to plot data.')
    parser.add_argument('-o', '--output', help='Name of the output file.')
    parser.add_argument('-d', '--database', help='Name of the database file.')

    args = parser.parse_args()

    print "Month=", args.month
    print "Output=", args.output
    print "Database=", args.database

    conn = sqlite3.connect('sensors.db')

    c = conn.cursor()

    ymin = int(args.month[0:4])
    mmin = int(args.month[4:6])
    ymax = ymin
    mmax = mmin + 1
    if mmin > 12 :
        ymax += 1
        mmin = 1
        
    
    dtmin = datetime.datetime(ymin, mmin, 1)
    print "Date mini=", dtmin
    dtmax = datetime.datetime(ymax, mmax, 1) - timedelta(seconds=1)
    print "Date maxi=", dtmax
    
    locale.setlocale(locale.LC_TIME, 'fr_FR')
    titre = dtmin.strftime("Releves de %B %Y")
    print titre
    
    dates = []
    temp = []
    hygro = []

    #stmt = '''SELECT logger, datetime(dt, \'unixepoch\', \'localtime\'), temp, hygro 
    stmt = '''SELECT logger, dt, temp, hygro 
        from sensors 
        where dt >= ? and dt <= ?;'''
    for row in c.execute(stmt, (dtmin.strftime("%s"), dtmax.strftime("%s"))):
        dates.append(float(row[1]))
        temp.append(row[2])
        hygro.append(row[3])
        #print row[0].encode('ascii'), ' ', row[1], ' ', row[2], ' ', row[3]

    #print dates
    #print temp
    #print hygro
    #lineChart('plotdb.png', temp, hygro)

    conn.close()

    # Matplotlib date format
    dfmt = mdates.DateFormatter('%a %d %H:%M')
    
    # Creation of the figure 8 inches x 5 inches
    fig = pyplot.figure(figsize=(8,5))
    ax = fig.add_subplot(111)
    # Un trait par jour
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    # Un trait toutes les 6 heures
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    ax.xaxis.set_major_formatter(dfmt)
    
    p1 = pyplot.plot_date(epoch2num(dates), temp, '-', xdate=True )
    p2 = pyplot.plot_date(epoch2num(dates), hygro, '-', xdate=True )
    pyplot.title( 'Releves de ' )
    pyplot.xlabel( 'Jours' )
    pyplot.ylabel( 'Temperatures / Hygrometrie' )
    pyplot.grid(True)
    fig.autofmt_xdate()
    pyplot.savefig( 'plotdb.png' )

sys.exit(0)

