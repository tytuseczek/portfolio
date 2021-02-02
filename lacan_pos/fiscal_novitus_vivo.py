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
from time import sleep
import random
import string

from logger import logger

class FiscalPrinterNovitusVivo(fiscal.FiscalPrinter):
    """
    Klasa sterująca drukarką Novitus Vivo
    """
    def __init__(self, port_nr, ip, port2_nr, PASS, timeout=1, debug=False):
        """
        Nawiązanie łączności z drukarką
        """
        super(FiscalPrinterNovitusVivo, self).__init__(port_nr, ip, port2_nr, PASS, timeout=timeout, debug=debug)
        self.encoding='ascii'
    
    errors = {
            'NIEZAIMPLEMENTOWANE':"Niezaimplementowane - 'read_response'",
            '1#E0':False,
            '1#E1':'Nie zainicjowany zegar RTC',
            '1#E2':'Nieprawidłowy batj kontrolny',
            '1#E3':'Nieprawidłowa ilość parametrów',
            '1#E4':'Nieprawidłowy parametr',
            '1#E5':'Błąd operacji z zegarem RTC',
            '1#E6':'Błąd operacji z modułem fiskalnym',
            '1#E7':'Nieprawidłowa data',
            '1#E8':'Błąd operacji - niezerowe totalizery',
            '1#E9':'Błąd operacji wejścia/wyjścia',
            '1#E10':'Przekroczony zakres danych',
            '1#E11':'Nieprawidłowa ilość stawek PTU',
            '1#E12':'Nieprawidłowy nagłówek',
            '1#E13':'Nie można refiskalizować urządzenia',
            '1#E14':'Nie można zapisać nagłówka',
            '1#E15':'Nieprawidłowe linie dodatkowe',
            '1#E16':'Nieprawidłowa nazwa towaru',
            '1#E17':'Nieprawidłowa ilość',
            '1#E18':'Nieprawidłowa stawka PTU towaru',
            '1#E19':'Nieprawidłowa cena towaru',
            '1#E20':'Nieprawidłowa wartość towaru',
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
            '1#E39':'Nieprawidłowy symbol stawki VAT',
            '1#E40':'Niezaprogramowany nagłówek',
        }
    
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
    
    def pobierz_kod_bledu(self):
        """
        Funkcja wysyła rozkaz pobrania ostatniego błedu do drukarki
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        komenda = "1#n"
        self.wyslij_komende(komenda)
        for i in range (0,self.timeout):
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
        
    def wyslij_komende(self, r, kod=True):
        '''
        Funkcja dodaje do rozkazu niezbędne, wspólne dla wszystkich rozkazów, znaczniki (<ESC>P ... <ESC>/)
        i wysyła rozkaz do drukarki
        UWAGA: Windows i Linux w inny sposób odbierają znaki specjalne.
        \r w linuxie tłumaczone jest na 13 (dobrze), w windowsie na 10
        @param r: String rozkazu
        @return True        
        '''
        logger(info_msg = ("wysylam: %s" % (r)))
        znaki = []
        for znak in r:
            d = ord(znak)
            if (self.platform == 'Windows') and (d == 10):
                d = 13
            znaki.append(d)
        if kod: 
            znaki = self.add_control_sum(znaki)
        r3 = [27, 80] + znaki + [27, 92]
        logger(info_msg = r3)
        self.serial.write(bytearray(r3))
        self.serial.flush()
        return True
    
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
    
    def beep(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz wydania sygnału dźwiękowego.
        @return [True, False]
        """
        b = bytearray([7])
        logger(info_msg = b)
        self.serial.write(b)
        self.serial.flush()
        return [True, False]
    
    def zmiana_trybu_obslugi_bledow(self, kod):
        """
        Funkcja zmienia tryb obsługi błędów w drukarce
        @param kod: kod sposobu obsługi błędu
        @return: res (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        #2 - error jest wyswietlany i zwracany
        r = "%d#e" % (kod)
        res = self.wyslij_komendy(r)
        return res
    
    def przetwarzaj_naglowek(self, naglowek, komendy, dane):
        """
        Funkcja przetwarza dane otrzymane z klienta na rozkaz nagłówka zrozumiały dla drukarki
        @param naglowek: Słownik z parametrami nagłówka
        @return komendy: String zawierający komendę dla drukarki
        """
        linii_stopki = naglowek.get('linii_stopki', False)
        linie_stopki = naglowek.get('linie_stopki', False)
        #Dla drukarek Novitus rozpoczęcie transakcji zawsze wygląda w ten sposób.
        #Wyjątek stanowi sytuacja, w której drukujemy własny nagłówek.
        r = "0;%d$h%s"%(linii_stopki, linie_stopki)
        komendy.append(r)
        return komendy, dane
    
    def przetwarzaj_linie_paragonu(self, linie_paragonu, komendy, dane):
        """
        @param naglowek: Słownik z parametrami linni paragonu
        @return komendy: String zawierający komendę dla drukarki
        """
        kwota_rabatu = 0
        
        for i in range(len(linie_paragonu)):
            linia = linie_paragonu[i]
            if not isinstance(linia, dict):
                return [False, "Błędne dane wejściowe"]
            r = "%d;%s$l%s\r%s\r%s/%s/%s/%s/" % (i + 1, linia['rodzaj_rabatu'], self.encode(linia['nazwa']), str(linia['ilosc']), linia['PTU'], str(linia['cena_jednostkowa_brutto']), str(linia['suma_brutto']), str(linia['rabat']))
            kwota_rabatu += float(linia['kwota_rabatu'])
            komendy.append(r)
        
        dane.update({'kwota_rabatu':kwota_rabatu})
        return komendy, dane
    
    def przetwarzaj_stopke(self, stopka, komendy, dane):
        """
        @param naglowek: Słownik z parametrami stopki
        @return komendy: String zawierający komendę dla drukarki
        """
        wplata = float(stopka['wplata'])
        razem = (stopka['razem'])
        kwota_rabatu = dane.get('kwota_rabatu', 0)
        r = '0;0;1;0;0;0;0;1;0;0;0;0$y01\r%s\r\r%f/%f/10/3/%f/' % (stopka['nr_zamowienia'],wplata, razem, kwota_rabatu)
        #r = "1$e%s\r%f/%f/%f/" % (stopka['kod_kasjera'], wplata, razem, kwota_rabatu)
        komendy.append(r)
        return komendy, dane
    
    def anuluj_transakcje(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz anulowania transakcji
        @return [True,False]
        """
        r = "0$e"
        self.wyslij_komende(r)
        return [True, False]

    def wplac_do_kasy(self, kwota):
        """
        Funkcja wysyłą do drukarki rozkaz "wpłata do kasy"
        @param kwota: Kwota jaka ma zostać wpłacona
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        r = "0#i%s/" % (kwota)
        ref = self.wyslij_komendy(r)
        return ref
    
    def wyplac_z_kasy(self, kwota, *args):
        """
        Funkcja wysyłą do drukarki rozkaz "wypłata z kasy"
        @param kwota: Kwota jaka ma zostać wypłacona
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        if isinstance(kwota, tuple):
            kwota = kwota[0]
        else: return False
        r = "0#d%s/" % (kwota)
        ref = self.wyslij_komendy(r)
        return ref
    

