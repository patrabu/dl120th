#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# dat2db - Insert content of dat file from the Voltcraft DL-120TH into a sqlite DB.
#
# Copyright 2012,2015 Patrick Rabu

import argparse
import sys
import os
import sqlite3

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Insert content of dat file into sqlite DB.',
        prog='dat2db.py', version='0.1')
    parser.add_argument('-f', '--filename', help='Name of the data file.')
    parser.add_argument('-d', '--database', help='Name of the database file.')

    args = parser.parse_args()

    print "Filename=", args.filename
    print "Database=", args.database

    commandOk = True

    if args.filename == None:
        print "Filename is mandatory."
        commandOk = False
    else:
        filename = args.filename

    if args.database == None:
        print "DataBase name is mandatory."
        commandOk = False
    else:
        dbname = args.database

    if not commandOk:
        print "Command line error..."
        sys.exit(2)

    conn = sqlite3.connect(dbname)

    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sensors (logger text, dt text, temp real, hygro real)''')

    with open(filename) as datfile:
        # Read the first line
        line = datfile.readline()
        print line
        words = line.split()
        print words[0], "-", words[1], "-", words[2], "-", words[3], "-", words[4]
        logger_name = words[1]

        for line in datfile:
            words = line.split()
            print words[0], "-", words[3], "-", words[4]
            c.execute('INSERT INTO sensors VALUES (?, ?, ?, ?)', (logger_name, words[0], words[3], words[4]))

    conn.commit()
    conn.close()

sys.exit(0)

