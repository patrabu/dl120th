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

import pygal

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
        output = args.month + '.svg'
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

    dates = []
    # first logger
    temp0 = []
    hygro0 = []
    # Second logger
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
        dates.append(float(row[1]))
        if row[0] == 'rdc':
            temp0.append(row[2])
            hygro0.append(row[3])
        else:
            temp1.append(row[2])
            hygro1.append(row[3])

    conn.close()

    chart = pygal.Line(x_label_rotation=20)
    chart.title = titre
    chart.x_label_format = '%d'
    chart.x_labels = map(str, dates)
    chart.add('Temp RDC', temp0)
    chart.add('Temp étage', temp1)
    chart.add('Hygro RDC', hygro0)
    chart.add('Hygro étage', hygro1)
    chart.render_to_file(output)

sys.exit(0)
