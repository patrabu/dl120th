#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# dl-120th - Control data logger Voltcraft DL-120TH
#
# Copyright 2012 Patrick Rabu

import argparse
import sys
import sqlite3
import locale

import datetime
from time import strftime, localtime

from matplotlib import pyplot
from matplotlib import dates as mdates
from matplotlib.dates import epoch2num


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Copy content of dat file into sqlite DB.',
        prog='plotdb.py')
    parser.add_argument(
        '-m', '--month',
        help='Month to plot data.')
    parser.add_argument(
        '-o', '--output',
        help='Name of the output file.')
    parser.add_argument(
        '-d', '--database',
        help='Name of the database file.')

    args = parser.parse_args()

    print("Month=", args.month)
    print("Output=", args.output)
    print("Database=", args.database)

    if args.database is None:
        database = 'sensors.db'
    else:
        database = args.database

    if args.output is None:
        output = args.month + '.png'
    else:
        output = args.output

    ymin = int(args.month[0:4])
    mmin = int(args.month[4:6])
    ymax = ymin
    mmax = mmin + 1
    if mmax > 12:
        ymax += 1
        mmax = 1

    dtmin = datetime.datetime(ymin, mmin, 1)
    print("Date mini=", dtmin)
    dtmax = datetime.datetime(ymax, mmax, 1)
    print("Date maxi=", dtmax)

    locale.setlocale(locale.LC_TIME, '')
    titre = dtmin.strftime("Releves de %B %Y")
    print(titre)

    # first logger
    dates0 = []
    temp0 = []
    hygro0 = []
    # Second logger
    dates1 = []
    temp1 = []
    hygro1 = []

    # stmt = '''
    # SELECT logger, datetime(dt, \'unixepoch\', \'localtime\'), temp, hygro
    stmt = '''SELECT logger, dt, temp, hygro
        from sensors
        where dt >= ? and dt < ?;'''

    conn = sqlite3.connect(database)

    c = conn.cursor()

    for row in c.execute(stmt, (dtmin.strftime("%s"), dtmax.strftime("%s"))):
        if row[0] == 'rdc':
            dates0.append(float(row[1]))
            temp0.append(row[2])
            hygro0.append(row[3])
        else:
            dates1.append(float(row[1]))
            temp1.append(row[2])
            hygro1.append(row[3])
        # print row[0].encode('ascii'), ' ', row[1], ' ', row[2], ' ', row[3]

    # print dates
    # print temp
    # print hygro
    # lineChart('plotdb.png', temp, hygro)

    conn.close()

    # Matplotlib date format
    dfmt = mdates.DateFormatter('%d')

    # Creation of the figure 9 inches x 6 inches
    fig = pyplot.figure(figsize=(9, 6))
    # fig, (ax0, ax1) = pyplot.subplots(nrows=2, sharex=True)

    # ax0 = fig.add_subplot(111)
    ax0 = pyplot.subplot(2, 1, 1)
    # Un trait par jour
    ax0.xaxis.set_major_locator(mdates.DayLocator())
    # Un trait toutes les 6 heures
    ax0.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    ax0.xaxis.set_major_formatter(dfmt)
    ax0.set_xlim(dtmin, dtmax)
    ax0.set_ylim(10, 35)
    ax0.plot_date(epoch2num(dates0), temp0, '-', xdate=True)
    ax0.plot_date(epoch2num(dates1), temp1, '-', xdate=True)
    ax0.grid(True)
    # ax0.set_title(dtmin.strftime("Températures de %B %Y"))
    pyplot.ylabel("Températures")
    pyplot.title(titre)

    ax1 = pyplot.subplot(2, 1, 2)
    # Un trait par jour
    ax1.xaxis.set_major_locator(mdates.DayLocator())
    # Un trait toutes les 6 heures
    ax1.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    ax1.xaxis.set_major_formatter(dfmt)
    ax1.set_xlim(dtmin, dtmax)
    ax1.set_ylim(35, 75)
    ax1.plot_date(epoch2num(dates0), hygro0, '-', xdate=True)
    ax1.plot_date(epoch2num(dates1), hygro1, '-', xdate=True)
    ax1.grid(True)
    pyplot.ylabel("Hygrométrie")
    pyplot.xlabel('Jours')

    #fig.set_title(titre)
    fig.autofmt_xdate()
    pyplot.savefig(output)

sys.exit(0)
