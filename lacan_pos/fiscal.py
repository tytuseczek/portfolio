# -*- coding: utf-8 -*-
##############################################################################
# 
# LACAN Technologies Sp. z o.o. 
# Al. Stanow Zjednoczonych 53 
# 04-028 Warszawa 
# 
# Copyright (C) 2009-2011 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>). 
# All Rights Reserved 
# 
# 
##############################################################################


from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import SocketServer

#from Crypto.PublicKey import RSA

import serial

import random
import string
from time import sleep

import platform

import mazovia
import sys
import codecs

import json

import logging
logger2 = logging.getLogger('fiscal_printer')

class SimpleThreadedXMLRPCRequestHandler(SimpleXMLRPCRequestHandler,object):
    rpc_paths = ('/RPC2',)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", self.headers.get("Access-Control-Request-Headers", "")) # Respond that they can send whatever headers they request to send
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS") 
        self.send_header("Access-Control-Max-Age", str(60*60*24*7)) # Cache answer for up to seven days
        self.send_header("Content-Length", "0") # Response body must be empty
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def do_POST(self):
        # Check that the path is legal
        if not self.is_rpc_path_valid():
            self.report_404()
            return

        try:
            # Get arguments by reading body of request.
            # We read this in chunks to avoid straining
            # socket.read(); around the 10 or 15Mb mark, some platforms
            # begin to have problems (bug #792570).
            max_chunk_size = 10*1024*1024
            size_remaining = int(self.headers["content-length"])
            L = []
            while size_remaining:
                chunk_size = min(size_remaining, max_chunk_size)
                L.append(self.rfile.read(chunk_size))
                size_remaining -= len(L[-1])
            data = ''.join(L)

            data = self.decode_request_content(data)
            if data is None:
                return #response has been sent

            # In previous versions of SimpleXMLRPCServer, _dispatch
            # could be overridden in this class, instead of in
            # SimpleXMLRPCDispatcher. To maintain backwards compatibility,
            # check to see if a subclass implements _dispatch and dispatch
            # using that method if present.
            response = self.server._marshaled_dispatch(
                    data, getattr(self, '_dispatch', None), self.path
                )
        except Exception, e: # This should only happen if the module is buggy
            # internal error, report as HTTP server error
            self.send_response(500)

            # Send information about the exception if requested
            if hasattr(self.server, '_send_traceback_header') and \
                    self.server._send_traceback_header:
                self.send_header("X-exception", str(e))
                self.send_header("X-traceback", traceback.format_exc())

            self.send_header("Content-length", "0")
            self.end_headers()
        else:
            # got a valid XML RPC response
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            if self.encode_threshold is not None:
                if len(response) > self.encode_threshold:
                    q = self.accept_encodings().get("gzip", 0)
                    if q:
                        try:
                            response = xmlrpclib.gzip_encode(response)
                            self.send_header("Content-Encoding", "gzip")
                        except NotImplementedError:
                            pass
            self.send_header("Content-length", str(len(response)))
            
            # By Will:
            # This allows for javascript to make requests from the browser
            self.send_header("Access-Control-Allow-Origin", "*")
            
            self.end_headers()
            self.wfile.write(response)
        
class SimpleThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer, object):    
     def __init__(self, port, allow_none=True, **kwargs):
        super(SimpleThreadedXMLRPCServer, self).__init__(port, requestHandler=SimpleThreadedXMLRPCRequestHandler, allow_none=allow_none, **kwargs)

class FiscalRoundException(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return(self.value)

class FiscalPrinter(object):    
    
    '''
    Wszystkie funkcje wywoływane przez RPC powinny zwracać listę [bool, string]
    Jeśli funkcja się powiodła: bool=True, string ignorowany 
    Jeśli funkcja zwraca błąd: bool=False, string=Komunikat który wyświetli się w kliencie OpenERP
    
    @errors - Słownik błędów zwracanych przez drukarkę
    '''
    errors = {
            'NIEZAIMPLEMENTOWANE':"Niezaimplementowane - 'read_response'",
            }

    ROUND_METHOD='ROUND'
    '''
    Ustawienie, co robić z zaokrąglanymi wartosciami (jeżeli jakieś wartości są podane z większą precyzją niż 2 miejsca po przecinku)
    Możliwe wartości:
    ERROR - zgłoś wyjątek (nie akceptuj takich wartosci)
    ROUND - zaokrągl automatycznie
    NONE  - nic nie rób (np. drukarka sama sobie radzi z takimi wartosciami)
    '''

    PRECISION={'ilosc':4,
               'cena_jednostkowa_brutto':2,
               'rabat':2,
               'suma_brutto':2,
               'razem':2,
               'wplata':2
               }
    '''
    Ustawienie precyzji obliczeń poszczególnych składników paragonu. Należy dostosować do konkretnego modelu drukarki.
    '''    


    def __init__(self, port_nr, ip, port2_nr, PASS, timeout=1, debug=False):
        self.encoding="ascii"
        self.port_nr = port_nr
        self.PASS = PASS
        self.serial = serial.Serial(port_nr, rtscts=True, timeout=timeout)
        self.server = SimpleThreadedXMLRPCServer((ip, port2_nr,))
        self.server.register_function(self.wykonajRPC)
        
        self.rpcdict = {'generate_password':self.generate_password,
                      'beep':self.beep,
                      'ping':self.ping,
                      'anuluj_transakcje':self.anuluj_transakcje,
                      'drukuj_paragon':self.drukuj_paragon,
                      'drukuj_paragon_odoo':self.drukuj_paragon_odoo,
                      'wyplac_z_kasy':self.wyplac_z_kasy,
                      'wplac_do_kasy': self.wplac_do_kasy,
                      }
        
        self.busy = False
        self.timeout = 30
        self.debug = debug
        
        logger2.debug("fiscal printer initiated")
        
        self.platform = platform.system()

    def plToAng(self,text):
        translate = {u'ą':'a', 
                    u'ć':'c',
                    u'ę':'e', 
                    u'ł':'l', 
                    u'ń':'n', 
                    u'ó':'o', 
                    u'ś':'s', 
                    u'ż':'z',
                    u'ź':'z',
                    u'Ą':'A', 
                    u'Ć':'C',
                    u'Ę':'E', 
                    u'Ł':'L', 
                    u'Ń':'N', 
                    u'Ó':'O', 
                    u'Ś':'S', 
                    u'Ż':'Z',
                    u'Ź':'Z',
                    }
        newText = ''
        for c in text:
            if c in translate:
                    c = translate[c]
            newText = newText + c
        return newText

    
    
    def encode(self,text):
        if self.encoding=='ascii':
            return self.plToAng(text)
        if self.encoding=='mazovia':
            try :
                code = mazovia.Codec()
                text_out = code.encode(text)
            except UnicodeEncodeError:
                print 'Unicode Encode Error in fiscal.py method encode !!'
            except:
                print 'Error in fiscal.py method encode !! ',sys.exc_info()[0]
            return text_out
        else:
            return text.encode(self.encoding)

    def wykonajRPC(self, password, command, *args):
        '''
        Funkcja do której może się odwołać openerp.
        To ona wywołuje pozostałe funkcje, o ile dodano je do słownika
        rpcdict
        '''
        logger2.debug('command RPC: %s %s'% (command,args))
        if password != self.PASS:
            raise Exception("incorrect password")
        else:
            if not self.busy:
                #return [True, 'OK'] #debug
                if self.debug: return [True, 'OK']
                self.busy = True
                response = self.rpcdict[command](args) #czy args jest konieczne?
                if response[0]:
                    response[1] = 'OK'
                else:
                    if not response[1]:
                        response[1] = "Brak kontaktu z drukarką!"
                logger2.debug('server: %s'%(response[1]))
                self.busy = False
                return response
            else: return [False, "Drukarka zajęta"]
    
    def pobierz_kod_bledu(self,*args):
        return [False, "Niezaimplementowane - 'pobierz_kod_bledu'"]
    
    def wyslij_komendy(self, r=[], kod=True):
        if not isinstance(r, list):
            r = [r]
        for komenda in r:
            response = self.wyslij_komende(komenda)
            if not response:
                return [False, False]
            response = self.pobierz_kod_bledu()
            if not response[0]:
                return response
        return [True, False]
     
    def wyslij_komende(self, r, kod=True):
        return [False, "Niezaimplementowane - 'wyslij_komende'"]
    
    def read_response(self):
        return "NIEZAIMPLEMENTOWANE"
  
    def prb(self, byte):
        ''' prints byte in a binary version'''
        s1 = "%s" % (bin(ord(byte))[2:])
        l = len(s1)
        a = ""
        for i in range(8 - l):
            a += "0"
        res = "%s%s" % (a, s1)
        return res

    def ping(self, *args):
        ''' This method is used for checking if pos_server listen on given ip address and port. '''
        return [True, False]

    def beep(self, *args):
        logger2.debug(info_msg = "Niezaimplementowano - 'beep'") 
        #
        #    Zmusza drukarkę do wydania sygnału dźwiękowego.
        #
        return [True, False] 
  
    def zmiana_trybu_obslugi_bledow(self, kod):
        return [False, "Niezaimplementowane - 'zmiana_trybu_obslugi_bledow'"]
    
    def sprawdz_kod_bledu(self, kod):       
        response = self.errors.get(kod, "Nieznany błąd")
        return response
    
    def przetwarzaj_naglowek(self, naglowek, komendy, dane):
        dane['naglowek_niezaimplementowany'] = True
        return komendy, dane
    
    def przetwarzaj_linie_paragonu(self, linie_paragonu, komendy, dane):
        dane['linie_niezaimplementowane'] = True
        return komendy, dane
    
    def przetwarzaj_stopke(self, stopka, komendy, dane):
        dane['stopka_niezaimplementowana'] = True
        return komendy, dane

    def przetwarzaj_dane_wejsciowe_odoo(self, dane_wejsciowe):
        dane_wejsciowe = json.loads(dane_wejsciowe[0])
        discount = False
        
        # header
        linie_stopki = {'linii_stopki': 1,
                        'linie_stopki': dane_wejsciowe['uid']}
        
        # body
        linie = []
        for linia_zam in dane_wejsciowe['orderlines']:
            linia_dane = {
                          'ilosc': linia_zam['quantity'],
                          'rodzaj_rabatu': linia_zam['discount'] and '2' or '0',
                          'nazwa':linia_zam['product_name'],
                          'cena_jednostkowa_brutto': linia_zam['unit_price_with_tax'],
                          'suma_brutto': linia_zam['price_with_tax'],
                          'rabat_proc': linia_zam['discount'],
                          'PTU': linia_zam['ptu'],
                          'rabat': linia_zam['discount'],
                          'kwota_rabatu': linia_zam['discount']
                          }
            linie.append(linia_dane)
            
        # footer
        stopka = {
                  'razem': dane_wejsciowe['total_with_tax'],
                  'internal_number': dane_wejsciowe['uid'],
                  'wplata': dane_wejsciowe['total_paid'],
                  'rodzaj_rabatu': 0, 
                  'linie_stopki': dane_wejsciowe['uid'],
                  'nr_zamowienia': dane_wejsciowe['uid'],
                  'wartosc_rabatu': 0, 
                  'rabat_calosci': 0, 
                  'linii_stopki': 1, 
                  'kod_kasjera': dane_wejsciowe['cashier'],
                  }
        
        return ([linie_stopki,linie,stopka],)
    
    
    def round(self,datas_dicts):
        result=[]
        '''
        Dokonuje zaokrągleń, sprawdza, wszystkie argumenty o typie float i sprawdza ich zaokraglenia 
        @param datas_dicts: lista ze słowników [{'klucz':wartość}]
        '''    
        for d in datas_dicts:
            for key,value in d.items():
                if key in self.PRECISION.keys():
                    if type(value).__name__ in ('int','float'):
                        if self.ROUND_METHOD == 'ROUND':
                            if abs(round(value,self.PRECISION[key])-value)>0.00000000001:
                                d[key]=round(value,self.PRECISION[key])  
                        elif self.ROUND_METHOD == 'ERROR':
                            if abs(round(value,self.PRECISION[key])-value)>0.00000000001:
                                raise FiscalRoundException("Nieprawidłowa precyzja wartosci %f dla klucza %s" %(value,key) )                             
            result.append(d)
        return result

    def drukuj_paragon(self, dane_wejsciowe, *args): 
        '''
        przykładowe dane:
        [{'linii_stopki': 1, 
        'linie_stopki': 'POS/002\r'}
        ,[{'ilosc': 1.0, 
        'suma_brutto': 1.23, 
        'kwota_rabatu': -0.0, 
        'rabat': 0.0, 
        'rodzaj_rabatu': '0', 
        'nazwa': 'kotlet', 
        'cena_jednostkowa_brutto': 1.23, 
        'cena_jednostkowa_netto': 1.0, 
        'PTU': 'A'}],
        {'razem': 1.23, 
        'linie_stopki': '', 
        'rabat_calosci': 0, 
        'kod_kasjera': '000', 
        'wplata': 1.23, 
        'rodzaj_rabatu': 0, 
        'wartosc_rabatu': 0, 
        'linii_stopki': 0}]
        '''
        try:
            logger2.debug('drukuj paragon: %s %s'% (dane_wejsciowe,args))
            #z jakiegos powodu, args zawsze jest wysylane (pusta tupla)
            #Jesli serwer zdalny, wyciagnij dane z tupli
            if isinstance(dane_wejsciowe, tuple):
                dane_wejsciowe = dane_wejsciowe[0]
            else:
                logger2.debug("Błędne dane wejściowe")
                return [False, "Błędne dane wejściowe"]
                
            if not len(dane_wejsciowe)>=3:
                logger2.debug("Błędne dane wejściowe")
                return [False, "Błędne dane wejściowe"]
            
            header = dane_wejsciowe[0]
            linie_paragonu = dane_wejsciowe[1]
            stopka = dane_wejsciowe[2]
            numer = stopka.get('internal_number','0')
    
            logger2.debug("1")
            plik = 'pos123'
            a = open(plik,'r')
            for i in reversed(list(a)):
                j=i.split('\t')
                if j[0] == numer and j[1] =='1':
                    a.close()
                    f = open(plik,'a')
                    f.write('%s\t%s\t%s\t\n'%(numer,0,9999))
                    f.close()
                    logger2.debug('Paragon %s został już wydrukowany!'%(numer))
                    return[False,'Paragon %s został już wydrukowany!'%(numer)]
    
    
            logger2.debug("2")
            if not isinstance(header, dict):
                logger2.debug("Błędne dane wejściowe")
                return [False, "Błędne dane wejściowe"]
            if not isinstance(stopka, dict):
                logger2.debug("Błędne dane wejściowe")
                return [False, "Błędne dane wejściowe"]
            
            komendy = []    #komendy wysłane do drukarki
            dane = {}       #słownik danych dodatkowych
    
            try:
                [header]=self.round([header])
                linie_paragonu=self.round(linie_paragonu)
                [stopka]=self.round([stopka])
            except FiscalRoundException as e:
                logger2.debug("FiscalRoundException")
                return [False, e.value]
    
            #rozpoczecie tranzakcji
            komendy, dane = self.przetwarzaj_naglowek(header, komendy, dane)
            if dane.get('naglowek_niezaimplementowany', False): return [False, "Niezaimplementowano - 'przetwarzaj_naglowek'"]
            komendy, dane = self.przetwarzaj_linie_paragonu(linie_paragonu, komendy, dane)
            if dane.get('linie_niezaimplementowane', False): return [False, "Niezaimplementowano - 'przetwarzaj_linie'"]
            komendy, dane = self.przetwarzaj_stopke(stopka, komendy, dane)
            if dane.get('stopka_niezaimplementowana', False): return [False, "Niezaimplementowano - 'przetwarzaj_stopke'"]
            response = self.wyslij_komendy(komendy)
            #response = [False, "Kotlet"]
            f = open(plik,'a')
            f.write('%s\t%s\t%s\t\n'%(stopka.get('internal_number','0'),int(response[0]),response[1]))
            f.close()

            return response
        except Exception as e: #dorobienie logowania, bo po stronie ERP logowanie jest beznadziejne
            print e
            raise

    def drukuj_paragon_odoo(self, dane_wejsciowe, *args):
        dane_wejsciowe = self.przetwarzaj_dane_wejsciowe_odoo(dane_wejsciowe)
        return self.drukuj_paragon(dane_wejsciowe, *args)

    def anuluj_transakcje(self, *args):
        return [False, "Niezaimplementowano - 'anuluj_transakcje'"]

    def wplac_do_kasy(self, kwota):
        return [False, "Niezaimplementowano - 'wplac_do_kasy'"]
    
    def wyplac_z_kasy(self, kwota, *args):
        return [False, "Niezaimplementowano - 'wyplac_z_kasy'"]

    def generate_password(self, *args):
        return [False, "Niezaimplementowano - 'generate_password'"]

