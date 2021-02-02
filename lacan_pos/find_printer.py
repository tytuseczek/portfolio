# -*- coding: utf-8 -*-
##############################################################################
#
# LACAN Technologies Sp. z o.o.
# al. Jerzego Waszyngtona 146, 7 piętro
# 04-076 Warszawa
#
# Copyright (C) 2009-2015 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
#
##############################################################################

import sys
import serial


def ask_all(data, endchar, available):
    ''' Function that sends given command on each port and check for response
    @param data: bytearray with command that gets type and version of printer
    @param endchar: char that will be recognized as end of response for given protocol
    @param available: list of available ports
    @return: printer response or False if nothing was found'''

    for port in available:
        try:
            print "Testing port: %s" % port
            ser = serial.Serial(port, timeout=1)
            ser.write(data)
            msg = ''
            while True:
                a = ser.read()
                if a == endchar or not a:
                    break
                msg = msg+a
            if not a:
                msg = False
            ser.close()
            if msg:
                return msg
        except serial.serialutil.SerialException:
            continue
    return False


if __name__ == '__main__':
    print """This program will try to find and identify fiscal printers connected to serial or USB ports.
Before proceeding make sure your printer is properly connected to this machine.

WARNING: Program will be sending commands to every open port until it get valid response. It can interfere with
other devices connected to this machine. You should disconnect other serial devices before proceeding\n"""
    raw_input("If You are ready to continue, then press Enter\n")

    print "Getting available ports.\n"
    available = []
    if sys.platform.startswith('linux'):
        import glob
        available.extend(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyS*'))
    else:
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append(i)
                s.close()
            except serial.SerialException:
                pass

    print "Ask if there is a POSNET printer"
    res = ask_all(bytearray([2, 115, 105, 100, 9, 35, 56, 65, 57, 52, 3]), '#', available)  # POSNET
    if not res:
        print "\nAsk if there is a EMAR like printer"
        res = ask_all(bytearray([27, 80, 35, 118, 27, 92]), '\\', available)  # EMAR

    # cleanup result
    if res:
        res = res.replace('1`', '')
        if res.startswith('sid\tnm'):
            res = res[7:]
        elif res.startswith('P1#'):
            res = res[5:-1]
        print res

    print '\nDone!'