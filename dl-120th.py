#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# dl-120th - Control data logger Voltcraft DL-120TH
#
# Copyright 2012 Patrick Rabu

import argparse
import sys
import os
import usb

from datetime import datetime, timedelta
from array import array
from struct import *


class DeviceDescriptor:
    def __init__(self, vendor_id, product_id, interface_id) :
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.interface_id = interface_id

    def get_device(self) :
        buses = usb.busses()
        for bus in buses :
            for device in bus.devices :
                if device.idVendor == self.vendor_id :
                    if device.idProduct == self.product_id :
                        return device
        return None


class Dl120th:
    """
    Class to interact with Voltcraft DL-120TH data logger.
    This tool is used to record temperatures and relative humidity.
    """
    VENDOR_ID       = 0x10C4        #: Vendor Id
    PRODUCT_ID      = 0x0003        #: Product Id for the Voltcraft DL-120TH
    INTERFACE_ID    = 0             #: The interface we use to talk to the device
    BULK_IN_EP      = 0x81          #: Endpoint for Bulk reads
    BULK_OUT_EP     = 0x02          #: Endpoint for Bulk writes
    PACKET_LENGTH   = 0x40          #: 64 bytes
    
    THRESHOLD = [0x0000, 0x3F80, 0x4000, 0x4040, 0x4080, 0x40A0, 0x40C0, 0x40E0, 0x4100, 
        0x4110, 0x4120, 0x4130, 0x4140, 0x4150, 0x4160, 0x4170, 0x4180, 0x4188, 0x4190, 
        0x4198, 0x41A0, 0x41A8, 0x41B0, 0x41B8, 0x41C0, 0x41C8, 0x41D0, 0x41D8, 0x41E0, 
        0x41E8, 0x41F0, 0x41F8, 0x4200, 0x4204, 0x4208, 0x420C, 0x4210, 0x4214, 0x4218, 
        0x421C, 0x4220, 0x4224, 0x4228, 0x422C, 0x4230, 0x4234, 0x4238, 0x423C, 0x4240, 
        0x4244, 0x4248, 0x424C, 0x4250, 0x4254, 0x4258, 0x425C, 0x4260, 0x4264, 0x4268, 
        0x426C, 0x4270, 0x4274, 0x4278, 0x427C, 0x4280, 0x4282, 0x4284, 0x4286, 0x4288, 
        0x428A, 0x428C, 0x428E, 0x4290, 0x4292, 0x4294, 0x4296, 0x4298, 0x429A, 0x429C, 
        0x429E, 0x42A0, 0x42A2, 0x42A4, 0x42A6, 0x42A8, 0x42AA, 0x42AC, 0x42AE, 0x42B0, 
        0x42B2, 0x42B4, 0x42B6, 0x42B8, 0x42BA, 0x42BC, 0x42BE, 0x42C0, 0x42C2, 0x42C4, 
        0x42C6, 0x42C8]

    num_data = 0
    temp = []
    rh = []

    device_descriptor = DeviceDescriptor(VENDOR_ID, PRODUCT_ID, INTERFACE_ID)

    def __init__(self,):
        # The actual device (PyUSB object)
        self.device = self.device_descriptor.get_device()
        # Handle that is used to communicate with device. Setup in L{open}
        self.handle = None
        self.status = (0,0,0,0)

    def open(self):
        """ Aquire device interface """
        self.device = self.device_descriptor.get_device()
        if not self.device:
            print >> sys.stderr, "Device isn't plugged in"
            sys.exit(1)
        try:
            self.handle = self.device.open()
            self.handle.claimInterface(self.device_descriptor.interface_id)
        except usb.USBError, err:
            print >> sys.stderr, err
            sys.exit(1)

    def close(self):
        """ Release device interface """
        try:
            self.handle.reset()
            self.handle.releaseInterface()
        except Exception, err:
            print >> sys.stderr, err

        self.handle, self.device = None, None

    def read_config(self):
        """ Read the configuration. """

        msg=[0x00, 0x10, 0x01]

        # Write the request
        sent_bytes = self.handle.bulkWrite(Dl120th.BULK_OUT_EP, msg, 1000)
        print "Read Config request return:", sent_bytes

        #  Read the response (Status)
        if (sent_bytes):
            read_bytes = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)

        print "Read Config response return:", read_bytes

        # Read the configuration
        data = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)
        print "Config data:", data

        # Unpack the configuration data
        self.logger_state,     \
        self.num_data_conf,    \
        self.num_data_rec,     \
        self.interval,         \
        start_year,            \
        padding1,              \
        self.thresh_temp_low,  \
        padding2,              \
        self.thresh_temp_high, \
        start_month,           \
        start_mday,            \
        start_hour,            \
        start_min,             \
        start_sec,             \
        self.temp_fahrenheit,  \
        self.led_conf,         \
        self.logger_name,      \
        self.logger_start,     \
        padding3,              \
        self.thresh_rh_low,    \
        padding4,              \
        self.thresh_rh_high,   \
        self.logger_end = unpack("IIIIIhhhhBBBBBBB16sBhhhhI", ''.join([chr(x) for x in data]))

        self.start_rec = datetime(start_year, start_month, start_mday, start_hour, start_min, start_sec)
        duration = self.num_data_rec * self.interval
        self.end_rec = self.start_rec + timedelta(seconds=duration)
        self.logger_name = self.logger_name.replace('\00','')

    def write_config(self, name, num_data, interval, start):
        """ Write the configuration. """

        # Construct configuration data
        now = datetime.now()

        if start == 'A':
            self.logger_start = 2
        else:
            self.logger_start = 1

        buf = pack("IIIIIhhhhBBBBBBB16sBhhhhI", 0xce, num_data, \
        0, interval, now.year, 0, self.thresh_temp_low, 0, self.thresh_temp_high, \
        now.month, now.day, now.hour, now.minute, now.second, self.temp_fahrenheit, self.led_conf, \
        name, self.logger_start, 0, self.thresh_rh_low, 0, self.thresh_rh_high, 0xce)

        # Configuration writing request
        msg=[0x01, 0x40, 0x00]
        # Ask for configuration write
        ret = self.handle.bulkWrite(Dl120th.BULK_OUT_EP, msg, 1000)
        print "Config return:", ret

        if (ret):
            # Send the configuration
            ret = self.handle.bulkWrite(Dl120th.BULK_OUT_EP, buf, 1000)

        if (ret):
            # Read the response
            data = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)

            if (data):
                #print "Return code:", data[0] & 0xff
                if (data[0] & 0xff) != 0xff :
                    print "Error writing configuration", hex(data[0])
                    sys.exit(1)

    def print_config(self):
        """ Print the configuration. """
        print "Configuration begin"
        print "\t>State: ", hex(self.logger_state)
        print "\t>Number of data conf: ", self.num_data_conf
        print "\t>Number of data rec: ", self.num_data_rec
        print "\t>Interval: ", self.interval
        print "\t>Start of recording:", str(self.start_rec)
        print "\t>End of recording:", str(self.end_rec)
        if self.temp_fahrenheit == 1 :
            print "\t>Farenheit conf: True (", hex(self.temp_fahrenheit), ")"
        else:
            print "\t>Farenheit conf: False °C (", hex(self.temp_fahrenheit), ")"
        print "\t>Led conf:", hex(self.led_conf)
        print "\t>Name:", self.logger_name, ": length=", len(self.logger_name)
        if self.logger_start == 1 :
            print "\t>Start logging: Manual (you need to press the red button to start logging)"
        else:
            print "\t>Start logging: Automatic"
        print "\t>Threshold temp low:", THRESHOLD.index(self.thresh_temp_low)
        print "\t>Threshold temp high:", THRESHOLD.index(self.thresh_temp_high)
        print "\t>Threshold rh low:", THRESHOLD.index(self.thresh_rh_low)
        print "\t>Threshold rh high:", THRESHOLD.index(self.thresh_rh_high)
        print "\t>logger end:", hex(self.logger_end)
        print "Configuration end\n"

    def read_data(self):
        """ Read data recorded. """
        # No data to read
        if (self.num_data_rec == 0):
            return

        # Ask for the data
        msg=[0x00, 0x00, 0x40]
        sent_bytes = self.handle.bulkWrite(Dl120th.BULK_OUT_EP, msg, 1000)

        #  Read the response (Status)
        if (sent_bytes):
            data = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)
            print "Status:", data, " - ", len(data)

        # Read the data
        data = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)

        # Unpack the data
        temp00, rh00, temp01, rh01, temp02, rh02, temp03, rh03, \
        temp04, rh04, temp05, rh05, temp06, rh06, temp07, rh07, \
        temp08, rh08, temp09, rh09, temp10, rh10, temp11, rh11, \
        temp12, rh12, temp13, rh13, temp14, rh14, temp15, rh15= \
        unpack("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh", ''.join([chr(x) for x in data]))
        self.rh.extend([rh00, rh01, rh02, rh03, rh04, rh05, rh06, rh07, rh08])
        self.rh.extend([rh08, rh09, rh10, rh11, rh12, rh13, rh14, rh15])
        self.temp.extend([temp00, temp01, temp02, temp03, temp04, temp05, temp06, temp07])
        self.temp.extend([temp08, temp09, temp10, temp11, temp12, temp13, temp14, temp15])
        self.num_data += 16

        while self.num_data < self.num_data_rec :
            if (self.num_data_rec - self.num_data < 16):
                print "data to read : ", self.num_data_rec - self.num_data

            # Read the data
            data = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)
            #print "Data:", hex(data), " - ", len(data)

            # Unpack the data
            temp00, rh00, temp01, rh01, temp02, rh02, temp03, rh03, \
            temp04, rh04, temp05, rh05, temp06, rh06, temp07, rh07, \
            temp08, rh08, temp09, rh09, temp10, rh10, temp11, rh11, \
            temp12, rh12, temp13, rh13, temp14, rh14, temp15, rh15= \
            unpack("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh", ''.join([chr(x) for x in data]))
            self.rh.extend([rh00, rh01, rh02, rh03, rh04, rh05, rh06, rh07])
            self.rh.extend([rh08, rh09, rh10, rh11, rh12, rh13, rh14, rh15])
            self.temp.extend([temp00, temp01, temp02, temp03, temp04, temp05, temp06, temp07])
            self.temp.extend([temp08, temp09, temp10, temp11, temp12, temp13, temp14, temp15])
            self.num_data += 16

            # Every 1024 data, send a keep alive message
            if self.num_data % 1024 == 0:
                # Keep alive message
                msg=[0x00, 0x01, 0x40]
                sent_bytes = self.handle.bulkWrite(Dl120th.BULK_OUT_EP, msg, 1000)

                # Read the response (Status)
                if (sent_bytes):
                    data = self.handle.bulkRead(Dl120th.BULK_IN_EP, Dl120th.PACKET_LENGTH, 1000)

    def print_data(self):
        """ Print the data """
        for i in range(self.num_data_rec):
            data_datetime = self.start_rec + timedelta(seconds=(i*self.interval))
            print i, str(data_datetime), data_datetime.strftime("%s"), self.temp[i] / 10.0, self.rh[i] / 10.0

    def save_data_to_file(self, fn):
        """ Save data in text file. """
        print "Filename:", fn
        datafile = open(fn, "w", 4096)
        line = "# %s [%s] %i points @ %i sec\n" % (self.logger_name, self.start_rec.strftime("%Y-%m-%d %H:%M:%S"), self.num_data_rec, self.interval)
        datafile.write(line)

        for i in range(self.num_data_rec):
            data_datetime = self.start_rec + timedelta(seconds=(i*self.interval))
            line = data_datetime.strftime("%s") + " " + data_datetime.strftime("%Y-%m-%d %H:%M:%S") + " " + \
            str(self.temp[i] / 10.0) + " " + str(self.rh[i] / 10.0) + '\n'
            datafile.write(line)
        datafile.close()


    def save_data_to_db(self, db):
        """ Save data in SQLite database. """
        print "Database:", db
        #datafile = open(fn, "w", 4096)
        line = "# %s [%s] %i points @ %i sec\n" % (self.logger_name, self.start_rec.strftime("%Y-%m-%d %H:%M:%S"), self.num_data_rec, self.interval)
        #datafile.write(line)

        for i in range(self.num_data_rec):
            data_datetime = self.start_rec + timedelta(seconds=(i*self.interval))
            line = data_datetime.strftime("%s") + " " + data_datetime.strftime("%Y-%m-%d %H:%M:%S") + " " + \
            str(self.temp[i] / 10.0) + " " + str(self.rh[i] / 10.0) + '\n'
            #datafile.write(line)
        #datafile.close()

    def write(self, msg):
        sent_bytes = self.handle.bulkWrite(Dl120th.BULK_OUT_EP, msg, 1000)
        print "sent_bytes: ", sent_bytes

    def read(self):
        try:
            data = self.handle.interruptRead(Dl120th.BULK_OUT_EP, Dl120th.PACKET_LENGTH, 1000)
            print "data length: ", len(data), " data: ", data
            return data
        except usb.USBError:
            if usb.USBError.args != ('No error',): # http://bugs.debian.org/476796
                raise usb.USBError


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Interface to the data logger Voltcraft DL-120TH.',
        prog='dl-120th.py', version='0.1')
    parser.add_argument('-c','--command', help='Command for the data logger.',
        choices=('info', 'save', 'reset', 'config', 'print'), required=True)
    parser.add_argument('-l', '--logname', help='Name of the data logger.')
    parser.add_argument('-n', '--numdata', help='Number of data to collect (between 50 and 16000).', type=int)
    parser.add_argument('-i', '--interval', help='Interval between data collect in seconds. (between 2 and 86400)', type=int)
    parser.add_argument('-s', '--start', help='Automatic (A) or manual (M) start.')
    parser.add_argument('-o', '--output', help='Filename to store the data')

    args = parser.parse_args()

    #print "Command ", args.command
    #print "Logger ", args.logname
    #print "Number of data", args.numdata
    #print "Interval", args.interval

    # Initialization of the device
    dl120th = Dl120th()
    dl120th.open()
    dl120th.read_config()

    commandOk = True

    if args.command == 'config':
        if args.logname == None:
            print "Logname is mandatory in config mode."
            commandOk = False
        if args.numdata == None:
            print "Numdata is mandatory in config mode."
            commandOk = False
        if args.interval == None:
            print "Interval is mandatory in config mode."
            commandOk = False
        if len(args.logname) < 1:
            print "Logname is mandatory in config mode."
            commandOk = False
        if len(args.logname) > 15:
            print "Logname length should be less or equals than 15."
            commandOk = False
        if args.numdata < 50 or args.numdata > 16000:
            print "The number of data to record should be between 50 and 16000."
            commandOk = False
        if args.interval < 2 or args.numdata > 86400:
            print "The interval of data collected should be between 2s and 86400s (24h)."
            commandOk = False
        if args.start != None and args.start != 'A' and args.start != 'M' :
            print "Start should be A (Automatic) or M (Manual)."
            commandOk = False

    if args.command == 'reset':
        dl120th.read_config()
        if args.logname != None and len(args.logname) > 15:
            print "Logname length should be less or equals than 15."
            commandOk = False
        else:
            dl120th.logger_name = args.logname
        if args.numdata != None and (args.numdata < 50 or args.numdata > 16000):
            print "The number of data to record should be between 50 and 16000."
            commandOk = False
        else:
            dl120th.num_data_conf = args.numdata
        if args.interval != None and (args.interval < 2 or args.numdata > 86400):
            print "The interval of data collected should be between 2s and 86400s (24h)."
            commandOk = False
        else:
            dl120th.interval = args.interval
        if args.start != None and args.start != 'A' and args.start != 'M' :
            print "Start should be A (Automatic) or M (Manual)."
            commandOk = False
        else:
            if args.start == 'A' :
                dl120th.logger_start = 2
            if args.start == 'M' :
                dl120th.logger_start = 1
            
    if not commandOk:
        print "Command line error..."
        sys.exit(2)

    if args.command == 'config':
        print args.command, " Logger=", args.logname, " numdata=", args.numdata, "@", args.interval, " sec. "
        dl120th.write_config(args.logname, args.numdata, args.interval, args.logger_start)

    if args.command == 'reset':
        print args.command, " Logger=", args.logname, " numdata=", args.numdata, "@", args.interval, " sec. "
        dl120th.write_config(dl120th.logger_name, dl120th.num_data_conf, dl120th.interval, dl120th.logger_start)

    if args.command == 'info':
        dl120th.print_config()

    if args.command == 'print':
        print args.command
        dl120th.read_data()
        dl120th.print_data()

    if args.command == 'save':
        dl120th.read_data()
        if args.output == None :
            fn = dl120th.logger_name.rstrip('\0') + "_" + dl120th.start_rec.strftime("%Y%m%d-%H%M%S") + ".dat"
        else :
            fn = args.output
        print args.command, " output=", fn
        dl120th.save_data_to_file(fn)

    dl120th.close()

sys.exit(0)
