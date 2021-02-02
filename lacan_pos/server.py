# -*- coding: utf-8 -*-
##############################################################################
# 
# LACAN Technologies Sp. z o.o. 
# Al. Stanow Zjednoczonych 53 
# 04-028 Warszawa 
# 
# Copyright (C) 2009-2013 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>). 
# All Rights Reserved 
# 
# 
##############################################################################
import logging

import fiscal_novitus_vivo as fiscal_case
import fiscal_innova_profit_ej as fiscal_case_innova
import fiscal_emar_printo_57T as fiscal_case_emar
import fiscal_posnet_thermal as fiscal_posnet
#import fiscal as fiscal_case

'''
serial port: Numer portu szeregowego do którego podłączono drukarkę. Przeważnie 0 lub 1, może jednak zmieniać się w zależności od komputera.
ip_address: Adres IP komputera do którego podłączyliśmy drukarkę.
ip_port: Numer portu IP po którym komunikować będą się serwer drukarki i klient OpenERP.
PASS: Ustanawiamy hasło do serwera drukarki.
'''


if __name__ == '__main__':
    logging.basicConfig()
    
    '''
    UWAGA: Do znalezienia oprowiedniego portu najlepiej uzyc kodu:

from serial.tools import list_ports
print(
    "\n".join(
        [
            port.device + ': ' + port.description
            for port in list_ports.comports()
        ]))
        
        http://stackoverflow.com/questions/6176485/pyserial-enumerate-ports  
    
    
    
    Podłączone urządzenia można także znaleźć za pomocą programu USBDeview http://www.nirsoft.net/utils/usb_devices_view.html
    
    '''

    serial_port = '/dev/ttyUSB0' #Jeżeli drukarka fiskalna jest podłączona pod port USB
    #serial_port = '/dev/ttyACM0' #przypadek drukarki Innova Profit podłącznona do portu USB
    #serial_port = 11 #Jeżeli drukarka fiskalna jest podłączona pod port RS232
    ip_address = "10.146.1.59"
    ip_port = 8999
    PASS = 'xxxxx'
    loglevel=logging.DEBUG
    #according to https://docs.python.org/2/library/logging.html
    #CRITICAL
    #ERROR
    #WARNING
    #INFO
    #DEBUG
    #NOTSET
    
    logger = logging.getLogger('fiscal_printer')
    logger.setLevel(logging.DEBUG)
    
    debug = False # Jeśli True, serwer automatycznie zwróci informację o powodzeniu operacji.
    
    # Create server
    #printer = fiscal_case.FiscalPrinterNovitusVivo(serial_port, ip_address, ip_port, PASS, debug=debug)
    #printer = fiscal_case_innova.FiscalPrinterInnovaProfitEJ(serial_port, ip_address, ip_port, PASS, debug=debug)
#     printer = fiscal_case_emar.FiscalPrinterEmarPrinto57T(serial_port, ip_address, ip_port, PASS, debug=debug)
    printer = fiscal_posnet.FiscalPrinterPosnetThermalFJ(serial_port, ip_address, ip_port, PASS, debug=debug)
    
    logger.info("Starting server... A new log line 'Printer connection established' should be present confirming that server has connection with the printer")
    printer.beep()

    kod_bledu=printer.pobierz_kod_bledu()
    logger.info('kod_bledu: %s' %(kod_bledu))
    logger.info("Printer connection established")
#     linijka do programowania nagłówka paragonu PosnetThermal
#     printer.wyslij_komende("hdrset\ttx&c&bCENTRUM HANDLOWE\n&c&bDOM I WNETRZE\n&cTOMASZ REMBECKI\n&c09-100 PLONSK,UL.WYSZOGRODZKA 51C\n&cTEL.023-664-01-20,664-01-21\n\n&cNIP 566-149-14-57\t")
    printer.server.serve_forever()
    logger.info( "Server is not running somehow.")

        