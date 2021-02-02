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

import logging
logger2 = logging.getLogger('fiscal_printer')

class FiscalPrinterEmarPrinto57T(fiscal.FiscalPrinter):
    """
    Klasa sterująca drukarką Emar Printo 57T
    """

    def __init__(self, port_nr, ip, port2_nr, PASS, timeout=1, debug=False):
        """
        Nawiązanie łączności z drukarką
        """
        super(FiscalPrinterEmarPrinto57T, self).__init__(port_nr, ip, port2_nr, PASS, timeout=timeout, debug=debug)
        self.encoding='mazovia'
    
    errors = {
            'NIEZAIMPLEMENTOWANE':"Niezaimplementowane - 'read_response'",
            '1#E0':False,
            '1#E1':'Nie zainicjowany zegar drukarki',
            '1#E2':'Błąd bajtu kontrolnego przesyłanej sekwencji',
            '1#E3':'Błędna ilość parametrów sekwencji sterującej',
            '1#E4':'Błędny parametr sterujący',
            '1#E5':'Błąd zegara RTC',
            '1#E6':'Błąd pamięci fiskalnej',
            '1#E7':'Nieprawidłowa data',
            '1#E8':'Błąd operacji - niezerowe totalizery',
            '1#E9':'Nieznany błąd',
            '1#E10':'Nieznany błąd',
            '1#E11':'Błędny zakres lib ilość programowanych stawek.',
            '1#E12':'Nieprawidłowy nagłówek',
            '1#E13':'Nieznany błąd',
            '1#E14':'Nieznany bład',
            '1#E15':'Bład dodatkowych linni tekstu lub pozycji zamówienia',
            '1#E16':'Nieprawidłowa nazwa towaru/usługi',
            '1#E17':'Nieprawidłowa ilość',
            '1#E18':'Nieprawidłowa stawka PTU towaru',
            '1#E19':'Nieprawidłowa cena towaru',
            '1#E20':'Błąd wartości BRUTTO lub RABAT',
            '1#E21':'Paragon nie został rozpoczęty',
            '1#E22':'Błąd operacji storno',
            '1#E23':'Nieprawidłowa ilość linii paragonu',
            '1#E24':'Nieznany błąd',
            '1#E25':'Nieprawidłowy tekst/nazwa kasjera/numer kasy lub terminala',
            '1#E26':'Nieprawidłowa wartość płatności',
            '1#E27':'Nieprawidłowa wartość całkowita lub rabat',
            '1#E28':'Przepełnienie totalizera sprzedaży',
            '1#E29':'Próba zakończenia nierozpoczętego paragonu',
            '1#E30':'Nieprawidłowa wartość wpłaty/wypłaty',
            '1#E31':'Przepełnienie rejsetru kasowego',
            '1#E32':'Podczas wypłaty wystąpił ujemny stan kasy.\n Wartość licznika zostanie wyzerowana',
            '1#E33':'Nieprawidłowy tekst zmiany',
            '1#E34':'Błąd parametru kasjer/numer kasy lub błąd jednego z parametrów rozkazów rozszerzeonych raportów kasy/zmiany',
            '1#E35':'Zerowe totalizery sprzedaży',
            '1#E36':'Nieznany bład',
            '1#E37':'Anulowane przez użytkownika',
            '1#E38':'Nieprawidłowa nazwa towaru/usługi w bazie towarowej lub kaucji w pozycji paragonu',
            '1#E39':'Błąd oznaczenia PTU',
            '1#E40':'Nieznany błąd',
            '1#E41':'Błęd napisu NUMER_KASY',
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
            '1#E82':'Rozkaz "rabat/narzut w trakcie transakcji" nie może być przyjęty dla aktualnego stanu drukarki',
            '1#E83':'Błąd parametru w sekwencji "Dodatkowe linie po numerze unikatowym"',
            '1#E84':'Nieznany błąd',
            '1#E85':'Nieznany błąd',
            '1#E90':'Drukarka jes w stanie wydruku rozliczania kaucji - można wysyłać tylko pozycje kaucji',
            '1#E91':'Błąd obsługi form płatności',
            '1#E92':'Przepełnienie bazy towarowej. Skontaktuj się z serwisem',
            '1#E93':'Błąd anulowania formy płatności',
            '1#E124':'Brak zaprogramowanej waluty ewidencyjnej',
            '1#E125':'Czujnik obudowy górnej jest włączony. Załóż obudowę drukarki',
            '1#E126':'Wykonaj pełny raport miesięczny za ostani miesiąc',
            '1#E127':'Wymagany jest numer paragonu, z którym wydruk jest powiązany',
            '1#E128':'Ten kod amortyzacyjny był już wykorzystany',
            '1#E129':'Korekta zegara nie powinna być większa niż o 60 minut',
            '1#E130':'Przekroczono maksymalną ilość zerowań RAM. Skontaktuj się z serwisem',
            '1#E131':'Nowo programowane stawki są identyczne ze starymi',
            '1#E132':'Przekroczono maksymalną liczbę pozycji paragonu',
            '1#E133':'Wydruk raportu miesięcznego w danym miesiącu nie jest możliwy przed jego zakończeniem',
            '1#E134':'Brak zaprogramowanych stawek PTU',
            '1#E135':'Błędny format daty',
            '1#E136':'Korekta zegara jest możliwa tylko po raporcie dobowym',
            '1#E137':'Błędny kod autoryzacyjny',
            '1#E138':'Przekroczono ilość pób zapisu kodu amortyzacyjnego. Po wykonaniu raportu dobowego możliwe są tylko 3 próby.',
            '1#E139':'Nie można zablokować drukarki odblokowanej kodem autoryzacyjnym',
            '1#E140':'Wykonanie tej operacji nie jest możliwe przed zakończeniem transakcji',
            '1#E141':'Nastąpiła niedozwolona zmiana stawki PTU dla tego towaru. Towar zablokowany',
            '1#E142':'Przekroczono liczbę zapisów rekordów stawek PTU w pamięci fiskalnej',
            '1#E143':'Błędny numer nip/ numer unikatowy',
            '1#E144':'Nie można zapisać ponownie numeru unikatowego/numeru nip w trybie fiskalnym',
            '1#E145':'Brak zapisanego numeru unikatowego drukarki. Skontaktuj się z serwisem',
            '1#E146':'Brak zaprogramowanego numeru NIP',
            '1#E147':'Brak zaprogramowanego nagłówka',
            '1#E148':'Wykonanie tej operacji wymaga wyłączenia trybu serwisowego. Skontaktuj się z serwisem',
            '1#E149':'Pamieć fiskalna drukarki została zamknięta',
            '1#E150':'Błąd nieznany',
            '1#E151':'Brak komunikacji z pamięcią EEPROM',
            '1#E152':'W bazie towarowej drukarki występują błędne dane. Skontaktuj się z serwisem',
            '1#E153':'Skasowano bazę towarową. Wykonaj raport dobowy',
            '1#E154':'Błąd totalizerów. Wykonaj raport dobowy',
            '1#E155':'Przed wykonaniem operacji wykonaj raport dobowy.',
            '1#E156':'Przepełnienie totalizera. Wykonaj raport dobowy.',
            '1#E157':'Błędny klucz pamięci fiskalnej. Skontaktuj się z serwisem',
            '1#E158':'Podano błędny klucz',
            '1#E159':'Wykonanie tej operacji możliwe jest tylko w trybie serwisowym',
            '1#E160':'Brak podłączonego wyświetlacza klienta. Skontaktuj się z serwisem',
            '1#E161':'Nie można zmienić poprawnego klucza',
            '1#E162':'Wystąpił restart drukarki',
            '1#E163':'Paragon nie został zakończony przed upływem 20 minut i został anulowany',
            '1#E164':'Podczas wydruku wystąpiła zakłucenie danych paragonu i został on anulwoany',
            '1#E255':'Rozkaz nierozpoznany',
            
            
        }
    
    def beep(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz wydania sygnału dźwiękowego.
        @return [True, False]
        """
        b = bytearray([7])
        logger2.debug("beep, bytearray: %s" %str(b))
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
        logger2.debug("wysylam komendę: %s" % (r))
        znaki = []
        for sign in r:
            d = self.encode(sign)
            d = ord(d[0])
            if (self.platform == 'Windows') and (d == 10):
                d = 13
            znaki.append(d)
        if kod:
            znaki = self.add_control_sum(znaki)
        r3 = [27, 80] + znaki + [27, 92]
        logger2.debug("komenda w bitach: %s" %str(r3))
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
        r = "0;0#d%s/" % (kwota)
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
        r = "0;0#i%s/" % (kwota)
        ref = self.wyslij_komendy(r)
        return ref
    
    def pobierz_kod_bledu(self,*args):
        """
        Funkcja wysyła rozkaz pobrania ostatniego błedu do drukarki
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        komenda = "1#n"
        self.wyslij_komende(komenda, False)
        for i in range (0, self.timeout):
            response = self.read_response()                
            if response: break
            sleep(1)
        if not response:
            return [False, False]
        error = self.sprawdz_kod_bledu(response)
        logger2.debug("Response : %s"%response)
        logger2.debug("Response error: %s"%error)
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
                r="%i$l%s\r%s\r%s/%s/%s/" % (i+1, self.encode(linia['nazwa']), str(linia['ilosc']), linia['PTU'], str(linia['cena_jednostkowa_brutto']), str(linia['suma_brutto']))
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
    
    

