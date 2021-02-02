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

import fiscal
import random
import string
import logging

from time import sleep

logger1 = logging.getLogger('fiscal_printer')

class FiscalPrinterInnovaProfitEJ(fiscal.FiscalPrinter):
    """
    Klasa sterująca drukarką Innova Profit EJ
    """
    def __init__(self, port_nr, ip, port2_nr, PASS, timeout=1, debug=False):
        """
        Nawiązanie łączności z drukarką
        """
        super(FiscalPrinterInnovaProfitEJ, self).__init__(port_nr, ip, port2_nr, PASS, timeout=timeout, debug=debug)
        self.encoding='mazovia'
    
    errors = {
            'NIEZAIMPLEMENTOWANE':"Niezaimplementowane - 'read_response'",
            '1#E0':False,
            '1#E1':'Nie zainicjowany zegar RTC',
            '1#E2':'Nieprawidłowy bajt kontrolny',
            '1#E3':'Nieprawidłowa ilość parametrów',
            '1#E4':'Błąd danych',
            '1#E5':'Błąd operacji z zegarem RTC',
            '1#E6':'Błąd operacji z modułem fiskalnym',
            '1#E7':'Nieprawidłowa data',
            '1#E8':'Błąd operacji - niezerowe totalizery',
            '1#E9':'Błąd operacji wejścia/wyjścia',
            '1#E10':'Próba niedozwolonego ustawienia zegara',
            '1#E11':'Zła ilość wartości PTU, błąd liczby',
            '1#E12':'Nieprawidłowy nagłówek',
            '1#E13':'Nie można refiskalizować urządzenia',
            '1#E14':'Błędny format NIP przy próbie fiskalizacji',
            '1#E15':'Błędna nazwa (pusta lub za długa)',
            '1#E16':'Nieprawidłowa nazwa towaru',
            '1#E17':'Nieprawidłowa ilość',
            '1#E18':'Nieprawidłowa stawka PTU towaru',
            '1#E19':'Nieprawidłowa cena towaru',
            '1#E20':'Błąd wartości BRUTTO lub RABAT',
            '1#E21':'Paragon nie został rozpoczęty',
            '1#E22':'Błąd operacji storno',
            '1#E23':'Nieprawidłowa ilość linii paragonu',
            '1#E24':'Przepełnienie bufora wydruku',
            '1#E25':'Nieprawidłowy tekst lub nazwa kasjera',
            '1#E26':'Nieprawidłowa wartość płatności',
            '1#E27':'Nieprawidłowa wartość całkowita',
            '1#E28':'Przepełnienie totalizera sprzedaży',
            '1#E29':'Próba zakończenia nierozpoczętego paragonu',
            '1#E30':'Nieprawidłowa wartość płatności 2',
            '1#E31':'Przepełnienie stanu kasy',
            '1#E32':'Ujemny stan kasy został zastąpiony zerowym',
            '1#E33':'Nieprawidłowy tekst zmiany',
            '1#E34':'Nieprawidłowa wartość lub tekst',
            '1#E35':'Zerowe totalizery sprzedaży',
            '1#E36':'Rekord już istnieje',
            '1#E37':'Anulowane przez użytkownika',
            '1#E38':'Nieprawidłowa nazwa',
            '1#E39':'Błąd oznaczenia PTU',
            '1#E40':'Blokada sekwencji',
            '1#E41':'Błąd blokujący tryb fiskalny. Skontaktuj się z serwisem producenta',
            '1#E42':'Błąd napisu NUMER_KASJERA',
            '1#E43':'Błąd napisu NUMER_PAR',
            '1#E44':'Błąd napisu KONTRAHENT',
            '1#E45':'Błąd napisu TERMINAL',
            '1#E46':'Błąd napisu NAZWA_KARTY',
            '1#E47':'Błąd napisu NUMER_KARTY',
            '1#E48':'Błąd napisu DATA_M',
            '1#E49':'Błąd napisu DATA_R',
            '1#E50':'Błąd napisu KOD_AUTORYZUJĄCY',
            '1#E51':'Błąd wartości KWOTA',
            '1#E83':'Nieokreślone stawki PTU',
            '1#E84':'Przekroczenie maksymalnej ilości zmian stawek PTU',
            '1#E85':'Zapełnienie wartości towarowej',
            '1#E90':'Operacja tylko z kaucjami - nie można wysyłać towarów',
            '1#E91':'Była wysłana forma płatności - nie można wysyłać towarów4',
            '1#E92':'Przepełnienie bazy towarowej. Skontaktuj się z serwisem',
            '1#E93':'Błąd anulowania formy płatności',
            '1#E94':'Przekroczenie maksymalnej kwoty sprzedaży',
            '1#E95':'Drukarka w tybie transakcji - operacja niedozwolona',
            '1#E96':'Przekroczony limit czasu na wydruk paragonu (20 minut)',
            '1#E98':'Blokada sprzedaży z powodu założenia zwory serwisowej. Skontaktuj się z działem wsparcia',
            '1#E99':'Inny błąd #99',
        }
    
    def beep(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz wydania sygnału dźwiękowego.
        @return [True, False]
        """
        b = bytearray([7])
        logger1.info("Beep method")
        self.serial.write(b)
        self.serial.flush()
        return [True, False]
    
    def anuluj_transakcje(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz anulowania transakcji
        @return [True,False]
        """
        r = "0$e"
        self.wyslij_komende(r)
        return [True, False]
    
    def add_control_sum(self, l):
        """
        Funkcja oblicza i dodaje do rozkazu jego sumę kontrolną
        @param l: String rozkazu
        @return l - String rozkazu powiększony o jego sumę kontrolną
        """
        r = 255
        for i in l:
            r = r ^ i
        
        rh = "%02.x" % (r)
            
        l.append(ord(rh[0]))
        l.append(ord(rh[1]))
        return l
    
    def wyslij_komende(self, r, kod=True):
        '''
        Funkcja dodaje do rozkazu niezbędne, wspólne dla wszystkich rozkazów, znaczniki (<ESC>P ... <ESC>/)
        i wysyła rozkaz do drukarki
        UWAGA: Windows i Linux w inny sposób odbierają znaki specjalne.
        \r w linuxie tłumaczone jest na 13 (dobrze), w windowsie na 10
        @param r: String rozkazu
        @return True        
        '''
        logger1.info('Send command')
        logger1.debug('Sequence %s'%(r))
        znaki = []
        for sign in r:
            d = self.encode(sign)
            d = ord(d[0])
            if (self.platform == 'Windows') and (d == 10):
                d = 13
            znaki.append(d)
        if kod:
            znaki = self.add_control_sum(znaki)
            pass
        r3 = [27, 80] + znaki + [27, 92]
        logger1.debug('Bytearray sequence %s'%(r3))
        self.serial.write(bytearray(r3))
        self.serial.flush()
        return True
    
    def wyplac_z_kasy(self, kwota, *args):
        """
        Funkcja wysyłą do drukarki rozkaz "wypłata z kasy"
        @param kwota: Kwota jaka ma zostać wypłacona
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        if isinstance(kwota, tuple):
            kwota = kwota[0]
        if not (isinstance(kwota, float) or isinstance(kwota, int)): return [False, 'Błędne dane wejściowe']
        r = "0#d%s/" % (kwota)
        ref = self.wyslij_komendy(r)
        return ref
    
    def wplac_do_kasy(self, kwota):
        """
        Funkcja wysyłą do drukarki rozkaz "wpłata do kasy"
        @param kwota: Kwota jaka ma zostać wpłacona
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        if isinstance(kwota, tuple):
            kwota = kwota[0]
        if not (isinstance(kwota, float) or isinstance(kwota, int)): return [False, 'Błędne dane wejściowe']
        r = "0#i%s/" % (kwota)
        ref = self.wyslij_komendy(r)
        return ref
    
    def pobierz_kod_bledu(self,*args):
        """
        Funkcja wysyła rozkaz pobrania ostatniego błedu do drukarki
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        komenda = "1#n"
        self.wyslij_komende(komenda)
        for i in range (0, self.timeout):
            response = self.read_response()                
            if response: break
            sleep(1)
        if not response:
            return [False, False]
        error = self.sprawdz_kod_bledu(response)
        if error:
            self.anuluj_transakcje()
            return [False, error]
        return [True, False]    
    
    def read_response(self):
        """
        Funkcja pobiera i zwraca kod błędu z drukarki
        @return: odp (kod błędu) 
        """
        l = []
        a = "1"
        while a != "\\":
            a = self.serial.read()
            if not a:
                return False
                #break
                #raise Exception("brak odpowiedzi")
            if a:
                l.append(ord(a))
        #TODO: sprawdzic sume kontrolna    
        odp = ""
        for znak in l[2:-2]:
            odp += chr(znak)        
        return odp

    def przetwarzaj_naglowek(self, naglowek, komendy, dane):
        """
        Funkcja przetwarza dane otrzymane z klienta na rozkaz nagłówka zrozumiały dla drukarki
        @param naglowek: Słownik z parametrami nagłówka
        @return komendy: String zawierający komendę dla drukarki
        """
        linii_stopki = naglowek.get('linii_stopki', False)
        linie_stopki = naglowek.get('linie_stopki', False)

        r = "0;%d$h#%s\r"%(linii_stopki, linie_stopki)
        komendy.append(r)
        return komendy, dane
    
    def przetwarzaj_linie_paragonu(self, linie_paragonu, komendy, dane):
        """
        @param naglowek: Słownik z parametrami linni paragonu
        @return komendy: String zawierający komendę dla drukarki
        """
        for i in range(len(linie_paragonu)):
            linia = linie_paragonu[i]
            if not isinstance(linia, dict):
                return [False, "Błędne dane wejściowe"]
            rabat_str=str(linia['rabat'])            
            if rabat_str == '-0.0': rabat_str = '0.0'
            if linia['rodzaj_rabatu'] == '0':
                r="%i$l%s\r%s\r%s/%s/%s/" % (i+1, linia['nazwa'], str(linia['ilosc']), linia['PTU'], str(linia['cena_jednostkowa_brutto']), str(linia['suma_brutto']))
            else:
                r="%i;%s$l%s\r%s\r%s/%s/%s/%s/" % (i+1, linia['rodzaj_rabatu'], linia['nazwa'], str(linia['ilosc']), linia['PTU'], str(linia['cena_jednostkowa_brutto']), str(linia['suma_brutto']), rabat_str)
            komendy.append(r)
            
        return komendy, dane
    
    def przetwarzaj_stopke(self, stopka, komendy, dane):
        """
        @param naglowek: Słownik z parametrami stopki
        @return komendy: String zawierający komendę dla drukarki
        """
        total = stopka['razem']
        r="1;0;0;0$e%s\r0/%s/" % (stopka['kod_kasjera'], total)
        komendy.append(r)
        return komendy, dane
    
    

