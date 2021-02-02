# -*- coding: utf-8 -*-
##############################################################################
# 
# LACAN Technologies Sp. z o.o. 
# Ul. Gocławska 11
# 03-810 Warszawa 
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
logger3 = logging.getLogger('fiscal_printer')

def logger2(info_msg =''):
    logger3.info(info_msg)

class FiscalPrinterPosnetThermalFJ(fiscal.FiscalPrinter):
    """
    Klasa sterująca drukarką Emar Printo 57T
    """

    def __init__(self, port_nr, ip, port2_nr, PASS, timeout=1, debug=False):
        """
        Nawiązanie łączności z drukarką
        """
        super(FiscalPrinterPosnetThermalFJ, self).__init__(port_nr, ip, port2_nr, PASS, timeout=timeout, debug=debug)
        self.encoding='ascii'
    
    errors = {
            '0000': False,
            '0001':'Nierozpoznana komenda',
            '0002':'Brak obowiązkowego pola',
            '0003':'Brak konwersji pola',
            '0004':'Błędny token',
            '0005':'Zła suma kontrolna',
            '0006':'Puste pole',
            '0007':'Niewłaściwa długość nazwy rozkazu',
            '0008':'Niewłaściwa długość tokena',
            '0009':'Niewłaściwa długość sumy kontrolnej',
            '0010':'Niewłaściwa długość pola danych',
            '0011':'Zapełniony bufor odbiorczy',
            '0012':'Nie można wykonać rozkazu w trybie natychmiastowym',
            '0013':'Nie znaleziono rozkazu o podanym tokenie',
            '0014':'Zapełniona kolejka wejściowa',
            '0015':'Błąd budowy ramki',
            '0030':'Błąd nietypowy - rezygnacja,przerwanie funkcji',
            '0050':'Błąd wykonywania operacji przez kasę',
            '0051':'Błąd wykonywania operacji przez kasę',
            '0052':'Błąd wykonywania operacji przez kasę',
            '0053':'Błąd wykonywania operacji przez kasę',
            '0054':'Błąd wykonywania operacji przez kasę',
            '0055':'Błąd wykonywania operacji przez kasę',
            '0056':'Błąd wykonywania operacji przez kasę',
            '0323':'Funkcja zablokowana w konfiguracji',
            '0360':'Znaleziono zworę systemową',
            '0361':'Nie znaleziono zwory',
            '0362':'Błąd weryfikacji danych klucza',
            '0363':'Upłynął czas na odpowiedź od klucza',
            '0382':'Próba wykonania raportu zerowego',
            '0383':'Brak raportu dobowego',
            '0384':'Brak rekordu w pamięci',
            '0400':'Błędna wartość',
            '0404':'Wprowadzono nieprawidłowy kod kontrolny',
            '0460':'Błąd zegara w trybie fiskalnym',
            '0461':'Błąd zegara w trybie niefiskalnym',
            '0480':'Drukarka już autoryzowana, bezterminowo',
            '0481':'Nie rozpoczęto jeszcze autoryzacji',
            '0482':'Kod już wprowadzony',
            '0483':'Próba wprowadzenia błędnych wartości',
            '0484':'Minął czas pracy kasy, sprzedaż zablokowana',
            '0485':'Błędny kod autoryzacji',
            '0486':'Blokada autoryzacji. Wprowadź kod z klawiatury.',
            '0487':'Użyto już maksymalnej liczby kodów',
            '0500':'Przepełnienie statystyki minimalnej',
            '0501':'Przepełnienie statystyki maksymalnej',
            '0502':'Przepełnienie stanu kasy',
            '0503':'Wartość stanu kasy po wypłacie staje się ujemna',
            '0700':'Błędny adres IP',
            '0701':'Błąd numeru tonu',
            '0702':'Błąd długości impulsu szuflady',
            '0703':'Błąd stawki VAT',
            '0704':'Błąd czasu wylogowania',
            '0705':'Błąd czasu uśpienia',
            '0706':'Błąd czasu wyłączenia',
            '0713':'Błędne parametry konfiguracji',
            '0714':'Błędna wartość kontrastu wyświetlacza',
            '0715':'Błędna wartość podświetlenia wyświetlacza',
            '0716':'Błędna wartość czasu zaniku podświetlenia',
            '0717':'Za długa linia nagłówka albo stopki',
            '0718':'Błędna konfiguracja komunikacji',
            '0719':'Błędna konfiguracja protokołu kom.',
            '0720':'Błędna identyfikator portu',
            '0721':'Błędny numer tekstu reklamowego',
            '0722':'Podany czas wychodzi poza wymagany zakres',
            '0723':'Podana data/czas niepoprawne',
            '0724':'Inna godzina w różnicach czasowych 0<=>23',
            '0726':'Błędna zawartość tekstu w linii wyświetlacza',
            '0727':'Błędna wartość dla przewijania na wyświetlaczu',
            '0728':'Błędna konfiguracja portu',
            '0729':'Błędna konfiguracja monitora transakcji',
            '0738':'Nieprawidłowa konfiguracja Ethernetu',
            '0739':'Nieprawidłowy typ wyświetlacza',
            '0740':'Dla tego typu wyświetlacza nie można ustawić czasu zaniku podświetlenia',
            '0820':'Negatywny wynik testu',
            '0821':'Brak testowanej opcji w konfiguracji',
            '0857':'Brak pamięci na inicjalizację bazy drukarkowej',
            '1000':'Błąd fatalny modułu fiskalnego',
            '1001':'Wypięta pamięć fiskalna',
            '1002':'Błąd zapisu',
            '1003':'Błąd nie ujęty w specyfikacji bios',
            '1004':'Błędne sumy kontrolne',
            '1005':'Błąd w pierwszym bloku kontrolnym',
            '1006':'Błąd w drugim bloku kontrolnym',
            '1007':'Błędny id rekordu',
            '1008':'Błąd inicjalizacji adresu startowego',
            '1009':'Adres startowy zainicjalizowany',
            '1010':'Numer unikatowy już zapisany',
            '1011':'Brak numeru w trybie fiskalnym',
            '1012':'Błąd zapisu numeru unikatowego',
            '1013':'Przepełnienie numerów unikatowych',
            '1014':'Błędny język w numerze unikatowym',
            '1015':'Więcej niż jeden NIP',
            '1016':'Drukarka w trybie do odczytu bez rekordu fiskalizacji',
            '1017':'Przekroczono liczbę zerowań RAM',
            '1018':'Przekroczono liczbę raportów dobowych',
            '1019':'Błąd weryfikacji numeru unikatowego',
            '1020':'Błąd weryfikacji statystyk z RD',
            '1021':'Błąd odczytu danych z NVR do weryfikacji FM',
            '1022':'Błąd zapisu danych z NVR do weryfikacji FM',
            '1023':'Pamięć fiskalna jest mała',
            '1024':'Nie zainicjalizowany obszar danych w pamięci fiskalnej',
            '1025':'Błędny format numeru unikatowego',
            '1026':'Za dużo błędnych bloków w FM',
            '1027':'Błąd oznaczenia błędnego bloku',
            '1028':'Rekord w pamięci fiskalnej nie istnieje - obszar pusty',
            '1029':'Rekord w pamięci fiskalnej z datą późniejszą od poprzedniego',
            '1030':'Błąd odczytu skrótu raportu dobowego',
            '1031':'Błąd zapisu skrótu raportu dobowego',
            '1032':'Błąd odczytu informacji o weryfikacji skrótu raportu dobowego',
            '1033':'Błąd zapisu informacji o weryfikacji skrótu raportu dobowego',
            '1034':'Błąd odczytu etykiety nośnika',
            '1035':'Błąd zapisu etykiety nośnika',
            '1036':'Niezgodność danych kopii elektronicznej',
            '1037':'Błędne dane w obszarze bitów faktur, brak ciągłości, zaplątany gdzieś bit lub podobne',
            '1038':'Błąd w obszarze faktur. Obszar nie jest pusty.',
            '1039':'Brak miejsca na nowe faktury',
            '1040':'Suma faktur z raportów dobowych jest większa od licznika faktur',
            '1041':'Błąd w obszarze ID modułu kopii',
            '1042':'Błąd zapisu ID modułu kopii',
            '1043':'Obszar ID modułu kopii zapełniony',
            '1950':'Przekroczony zakres totalizerów paragonu',
            '1951':'Wpłata formą płatności przekracza max wpłatę',
            '1952':'Suma form płatności przekracza max wpłatę',
            '1953':'Formy płatności pokrywają już do zapłaty',
            '1954':'Wpłata reszty przekracza max wpłatę',
            '1955':'Suma form płatności przekracza max wpłatę',
            '1956':'Przekroczony zakres total',
            '1957':'Przekroczony maksymalny zakres paragonu',
            '1958':'Przekroczony zakres wartości opakowań',
            '1959':'Przekroczony zakres wartości opakowań przy stornowaniu',
            '1961':'Wpłata reszty zbyt duża',
            '1962':'Wpłata formą płatności wartości 0',
            '1980':'Przekroczony zakres kwoty bazowej rabatu/narzutu',
            '1981':'Przekroczony zakres kwoty po rabacie/narzucie',
            '1982':'Błąd obliczania rabatu/narzutu',
            '1983':'Wartość bazowa ujemna lub równa 0',
            '1984':'Wartość rabatu/narzutu zerowa',
            '1985':'Wartość po rabacie ujemna lub równa 0',
            '1990':'Niedozwolone stornowanie towaru. Błędny stan transakcji.',
            '1991':'Niedozwolony rabat/narzut. Błędny stan transakcji.',
            '2000':'Błąd pola VAT (błędny numer stawki lub nieaktywna stawka)',
            '2002':'Brak nagłówka',
            '2003':'Zaprogramowany nagłówek',
            '2004':'Brak aktywnych stawek VAT',
            '2005':'Brak trybu transakcji',
            '2006':'Błąd pola cena (cena <= 0 )',
            '2007':'Błąd pola ilość (ilość <=0)',
            '2008':'Błąd kwoty total',
            '2009':'Błąd kwoty total (total = 0)',
            '2010':'Przekroczony zakres totalizerów dobowych',
            '2021':'Próba ponownego ustawienia zegara',
            '2022':'Zbyt duża różnica dat',
            '2023':'Różnica większa niż godzina w trybie użytkownika w trybie fiskalnym',
            '2024':'Zły format daty',
            '2025':'Data wcześniejsza od ostatniego zapisu do modułu',
            '2026':'Błąd zegara',
            '2027':'Przekroczono maksymalną liczbę zmian stawek VAT',
            '2028':'Próba zdefiniowania identycznych stawek VAT',
            '2029':'Błędne wartości stawek VAT',
            '2030':'Próba zdefiniowania stawek VAT wszystkich nieaktywnych',
            '2031':'Błąd pola NIP',
            '2032':'Błąd numeru unikatowego pamięci fiskalnej',
            '2033':'Urządzenie w trybie fiskalnym',
            '2034':'Urządzenie w trybie niefiskalnym',
            '2035':'Niezerowe totalizery',
            '2036':'Urządzenie w stanie tylko do odczytu',
            '2037':'Urządzenie nie jest w stanie tylko do odczytu',
            '2038':'Urządzenie w trybie transakcji',
            '2039':'Zerowe totalizery',
            '2040':'Błąd obliczeń walut, przepełnienie przy mnożeniu lub dzieleniu',
            '2041':'Próba zakończenia pozytywnego paragonu z wartością 0',
            '2042':'Błędny format daty początkowej',
            '2043':'Błędny format daty końcowej',
            '2044':'Próba wykonania raportu miesięcznego w danym miesiącu',
            '2045':'Data początkowa późniejsza od bieżącej daty',
            '2046':'Data końcowa wcześniejsza od daty fiskalizacji',
            '2047':'Numer początkowy lub końcowy równy 0',
            '2048':'Numer początkowy większy od numeru końcowego',
            '2049':'Numer raportu zbyt duży',
            '2050':'Data początkowa późniejsza od daty końcowej',
            '2051':'Brak pamięci w buforze tekstów',
            '2052':'Brak pamięci w buforze transakcji',
            '2054':'Formy płatności nie pokrywają kwoty do zapłaty lub reszty',
            '2055':'Błędna linia',
            '2056':'Tekst pusty',
            '2057':'Przekroczony rozmiar lub przekroczona liczba znaków formatujących',
            '2058':'Błędna liczba linii',
            '2060':'Błędny stan transakcji',
            '2062':'Jest wydrukowana część jakiegoś dokumentu',
            '2063':'Błąd parametru',
            '2064':'Brak rozpoczęcia wydruku lub transakcji',
            '2067':'Błąd ustawień konfiguracyjnych wydrukół/drukarki',
            '2070':'Data przeglądu wcześniejsza od systemowej',
            '2101':'Zapełnienie bazy',
            '2102':'Stawka nieaktywna',
            '2103':'Nieprawidłowa stawka VAT',
            '2104':'Błąd nazwy',
            '2105':'Błąd przypisania stawki',
            '2106':'Towar zablokowany',
            '2107':'Nie znaleziono w bazie drukarkowej',
            '2200':'Błąd autoryzacji',
            '2501':'Błędny identyfikator raportu',
            '2502':'Błędny identyfikator linii raportu',
            '2503':'Błędny identyfikator nagłówka raportu',
            '2504':'Zbyt mało parametrów raportu',
            '2505':'Raport nie rozpoczęty',
            '2506':'Raport rozpoczęty',
            '2507':'Błędny identyfikator komendy',
            '2521':'Raport już rozpoczęty',
            '2522':'Raport nie rozpoczęty',
            '2523':'Błędna stawka VAT',
            '2532':'Błędna liczba kopii faktur',
            '2533':'Pusty numer faktury',
            '2600':'Błędny typ rabatu/narzutu',
            '2601':'Wartość rabatu/narzutu spoza zakresu',
            '2701':'Błąd identyfikatora stawki podatkowej',
            '2702':'Błędny identyfikator dodatkowej stopki',
            '2703':'Przekroczona liczba dodatkowych stopek',
            '2704':'Zbyt słaby akumulator',
            '2705':'Błędny identyfikator typu formy płatności',
            '2710':'Usługa o podanym identyfikatorze nie jest uruchomiona',
            '2801':'Błąd weryfikacji wartości rabatu/narzutu',
            '2802':'Błąd weryfikacji wartości linii sprzedaży',
            '2803':'Błąd weryfikacji wartości opakowania',
            '2804':'Błąd weryfikacji wartości formy płatności',
            '2805':'Błąd weryfikacji wartości fiskalnej',
            '2806':'Błąd weryfikacji wartości opakowań dodatnich',
            '2807':'Błąd weryfikacji wartości opakowań ujemnych',
            '2808':'Błąd weryfikacji wartości wpłaconych form płatności',
            '2809':'Błąd weryfikacji wartości reszt',
            '2851':'Błąd stornowania, błędna ilość',
            '2852':'Błąd stornowania, błędna wartość',
            '2900':'Stan kopii elektronicznej nie pozwala na wydrukowanie tego dokumentu',
            '2901':'Brak nośnika lub operacja na nośniku trwa',
            '2903':'Pamięć podręczna kopii elektronicznej zawiera zbyt dużą ilość danych',
            '2911':'Brak pliku na nośniku',
            '2913':'Nieprawidłowy wynik testu',
            '3051':'Nie można zmienić 2 raz waluty ewidencyjnej po RD',
            '3052':'Próba ustawienia już ustawionej waluty',
            '3053':'Błędna nazwa waluty',
            '3054':'Automatyczna zmiana waluty',
            '3055':'Błędna wartość przelicznika kursu',
            '3056':'Przekroczono maksymalną liczbę zmian walut',
            '3080':'Próba zdefiniowania stawek VAT ze starą datą',
            '3084':'Automatyczna zmiana stawek VAT',
            '3085':'Brak pola daty',
            '3100':'Błędne parametry w bloku 1',
            '3101':'Błędne parametry w bloku 2',
            '3102':'Za krótka nazwa parametru destination',
            '3103':'Za krótka nazwa parametru transition',
            '3104':'Niedozwolone znaki w porcie docelowym',
            '3105':'Niedozwolone znaki w porcie tranzytowym',
            }
    
    def beep(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz wydania sygnału dźwiękowego.
        @return [True, False]
        """
        b = bytearray([7])
        logger2(info_msg = b)
        self.serial.write(b)
        self.serial.flush()
        return [True, False]
    
    def anuluj_transakcje(self, *args):
        """
        Funkcja wysyła do drukarki rozkaz anulowania transakcji
        @return [True,False]
        """
        r = "prncancel\t"
        self.wyslij_komende(r)
        return [True, False]
    
    def add_control_sum(self, l):
        """
        Funkcja oblicza i dodaje do rozkazu jego sumę kontrolną
        @param l: String rozkazu
        @return r - Rozkaz z sumą kontrolną rozkazu poprzedzona hashem (#) - wynik w formie bitów
        """

        crc16htab=[0x00,0x10,0x20,0x30,0x40,0x50,0x60,0x70,
                   0x81,0x91,0xa1,0xb1,0xc1,0xd1,0xe1,0xf1,
                   0x12,0x02,0x32,0x22,0x52,0x42,0x72,0x62,
                   0x93,0x83,0xb3,0xa3,0xd3,0xc3,0xf3,0xe3,
                   0x24,0x34,0x04,0x14,0x64,0x74,0x44,0x54,
                   0xa5,0xb5,0x85,0x95,0xe5,0xf5,0xc5,0xd5,
                   0x36,0x26,0x16,0x06,0x76,0x66,0x56,0x46,
                   0xb7,0xa7,0x97,0x87,0xf7,0xe7,0xd7,0xc7,
                   0x48,0x58,0x68,0x78,0x08,0x18,0x28,0x38,
                   0xc9,0xd9,0xe9,0xf9,0x89,0x99,0xa9,0xb9,
                   0x5a,0x4a,0x7a,0x6a,0x1a,0x0a,0x3a,0x2a,
                   0xdb,0xcb,0xfb,0xeb,0x9b,0x8b,0xbb,0xab,
                   0x6c,0x7c,0x4c,0x5c,0x2c,0x3c,0x0c,0x1c,
                   0xed,0xfd,0xcd,0xdd,0xad,0xbd,0x8d,0x9d,
                   0x7e,0x6e,0x5e,0x4e,0x3e,0x2e,0x1e,0x0e,
                   0xff,0xef,0xdf,0xcf,0xbf,0xaf,0x9f,0x8f,
                   0x91,0x81,0xb1,0xa1,0xd1,0xc1,0xf1,0xe1,
                   0x10,0x00,0x30,0x20,0x50,0x40,0x70,0x60,
                   0x83,0x93,0xa3,0xb3,0xc3,0xd3,0xe3,0xf3,
                   0x02,0x12,0x22,0x32,0x42,0x52,0x62,0x72,
                   0xb5,0xa5,0x95,0x85,0xf5,0xe5,0xd5,0xc5,
                   0x34,0x24,0x14,0x04,0x74,0x64,0x54,0x44,
                   0xa7,0xb7,0x87,0x97,0xe7,0xf7,0xc7,0xd7,
                   0x26,0x36,0x06,0x16,0x66,0x76,0x46,0x56,
                   0xd9,0xc9,0xf9,0xe9,0x99,0x89,0xb9,0xa9,
                   0x58,0x48,0x78,0x68,0x18,0x08,0x38,0x28,
                   0xcb,0xdb,0xeb,0xfb,0x8b,0x9b,0xab,0xbb,
                   0x4a,0x5a,0x6a,0x7a,0x0a,0x1a,0x2a,0x3a,
                   0xfd,0xed,0xdd,0xcd,0xbd,0xad,0x9d,0x8d,
                   0x7c,0x6c,0x5c,0x4c,0x3c,0x2c,0x1c,0x0c,
                   0xef,0xff,0xcf,0xdf,0xaf,0xbf,0x8f,0x9f,
                   0x6e,0x7e,0x4e,0x5e,0x2e,0x3e,0x0e,0x1e]
        
        crc161tab=[0x00,0x21,0x42,0x63,0x84,0xa5,0xc6,0xe7,
                   0x08,0x29,0x4a,0x6b,0x8c,0xad,0xce,0xef,
                   0x31,0x10,0x73,0x52,0xb5,0x94,0xf7,0xd6,
                   0x39,0x18,0x7b,0x5a,0xbd,0x9c,0xff,0xde,
                   0x62,0x43,0x20,0x01,0xe6,0xc7,0xa4,0x85,
                   0x6a,0x4b,0x28,0x09,0xee,0xcf,0xac,0x8d,
                   0x53,0x72,0x11,0x30,0xd7,0xf6,0x95,0xb4,
                   0x5b,0x7a,0x19,0x38,0xdf,0xfe,0x9d,0xbc,
                   0xc4,0xe5,0x86,0xa7,0x40,0x61,0x02,0x23,
                   0xcc,0xed,0x8e,0xaf,0x48,0x69,0x0a,0x2b,
                   0xf5,0xd4,0xb7,0x96,0x71,0x50,0x33,0x12,
                   0xfd,0xdc,0xbf,0x9e,0x79,0x58,0x3b,0x1a,
                   0xa6,0x87,0xe4,0xc5,0x22,0x03,0x60,0x41,
                   0xae,0x8f,0xec,0xcd,0x2a,0x0b,0x68,0x49,
                   0x97,0xb6,0xd5,0xf4,0x13,0x32,0x51,0x70,
                   0x9f,0xbe,0xdd,0xfc,0x1b,0x3a,0x59,0x78,
                   0x88,0xa9,0xca,0xeb,0x0c,0x2d,0x4e,0x6f,
                   0x80,0xa1,0xc2,0xe3,0x04,0x25,0x46,0x67,
                   0xb9,0x98,0xfb,0xda,0x3d,0x1c,0x7f,0x5e,
                   0xb1,0x90,0xf3,0xd2,0x35,0x14,0x77,0x56,
                   0xea,0xcb,0xa8,0x89,0x6e,0x4f,0x2c,0x0d,
                   0xe2,0xc3,0xa0,0x81,0x66,0x47,0x24,0x05,
                   0xdb,0xfa,0x99,0xb8,0x5f,0x7e,0x1d,0x3c,
                   0xd3,0xf2,0x91,0xb0,0x57,0x76,0x15,0x34,
                   0x4c,0x6d,0x0e,0x2f,0xc8,0xe9,0x8a,0xab,
                   0x44,0x65,0x06,0x27,0xc0,0xe1,0x82,0xa3,
                   0x7d,0x5c,0x3f,0x1e,0xf9,0xd8,0xbb,0x9a,
                   0x75,0x54,0x37,0x16,0xf1,0xd0,0xb3,0x92,
                   0x2e,0x0f,0x6c,0x4d,0xaa,0x8b,0xe8,0xc9,
                   0x26,0x07,0x64,0x45,0xa2,0x83,0xe0,0xc1,
                   0x1f,0x3e,0x5d,0x7c,0x9b,0xba,0xd9,0xf8,
                   0x17,0x36,0x55,0x74,0x93,0xb2,0xd1,0xf0]
        hi=0
        lo=0
        for i in l:
            index = hi^i
            hi = lo^crc16htab[index]
            lo = crc161tab[index]
 
        hi2=((hi<<8)|lo)
        r1="%04X" % hi2
        
        #tłumaczenie hex na bit
        suma_bit=[]
        for znak in r1:
            d = ord(znak)
            suma_bit.append(d)
        r=l+[ord('#')]+suma_bit
        return r
    

    
    def wyslij_komende(self, r, kod=True):
        '''
        Funkcja dodaje do rozkazu niezbędne, wspólne dla wszystkich rozkazów, znaczniki (<ESC>P ... <ESC>/)
        i wysyła rozkaz do drukarki
        UWAGA: Windows i Linux w inny sposób odbierają znaki specjalne.
        \r w linuxie tłumaczone jest na 13 (dobrze), w windowsie na 10
        @param r: String rozkazu
        @return True        
        '''
        logger2(info_msg = ("wysylam: %s" % (r)))
        znaki = []
        for znak in r:
            d = ord(znak)
            if (self.platform == 'Windows') and (d == 10):
                d = 13
            znaki.append(d)
        znaki = self.add_control_sum(znaki)
        
        r3=[2]+znaki+[3]

        logger2(info_msg = r3)
        self.serial.write(bytearray(r3))
        self.serial.flush()
        return True
    
    def wyplac_z_kasy(self, kwota, *args):
        """
        Funkcja wysyła do drukarki rozkaz "wypłata z kasy"
        @param kwota: Kwota jaka ma zostać wypłacona
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        if isinstance(kwota, tuple):
            kwota = kwota[0]
        if not (isinstance(kwota, float) or isinstance(kwota, int)): return [False, 'Błędne dane wejściowe']
        kwota_str = str(int(round(kwota*100)))
        r = "cash\tkw%s\twp0\t" % (kwota_str)
        ref = self.wyslij_komendy(r)
        return ref
    
    def wplac_do_kasy(self, kwota):
        """
        Funkcja wysyła do drukarki rozkaz "wpłata do kasy"
        @param kwota: Kwota jaka ma zostać wpłacona
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """
        if isinstance(kwota, tuple):
            kwota = kwota[0]
        if not (isinstance(kwota, float) or isinstance(kwota, int)): return [False, 'Błędne dane wejściowe']
        kwota_str = round(kwota*100)
        r = "cash\tkw%.0f\twp1\t" % (kwota_str)
        ref = self.wyslij_komendy(r)
        return ref
    
    def pobierz_kod_bledu(self,*args):
        """
        Funkcja wysyła rozkaz pobrania ostatniego błedu do drukarki
        @return: ref (listę z dwoma wartościami boolean sygnalizującymi powodzenie operacji)
        """

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
        else:
            return [True, False]    
    
    def read_response(self):
        """
        Funkcja pobiera i zwraca kod błędu z drukarki
        @return: odp (kod błędu) 
        """
        
        response=""
        r=""
        while r !="#":
            r = self.serial.read()
            response=response+r
        if not response:
            return False
        if len(response)>7 and response[len(response)-7]=="?":
            code =""
            for i in range ((len(response)-6),(len(response)-2)):
                code=code+response[i]
            return code
        else: 
            return '0000'
    
    def przetwarzaj_naglowek(self, naglowek, komendy, dane):
        """
        Funkcja drukuje nagłówek na paragonie
        @return komendy: String zawierający komendę dla drukarki
        """
        r = "hdrget\t"
        komendy.append(r)
        return komendy, dane
    
    def przetwarzaj_linie_paragonu(self, linie_paragonu, komendy, dane):
        """
        @param naglowek: Słownik z parametrami linni paragonu
        @return komendy: String zawierający komendę dla drukarki
        """
        start = 'trinit\tbm0\t'
        komendy.append(start)
        suma = 0.0
        for i in range(len(linie_paragonu)):
            discount = False
            linia = linie_paragonu[i]
            if not isinstance(linia, dict):
                return [False, "Błędne dane wejściowe"]
            ptu_str=str(linia['PTU'])
            ptu={'A':'0',
            'B':'1',
            'C':'2',
            'D':'3',
            'E':'4',
            'F':'5',
            'G':'6' }[ptu_str]     
            if linia['rodzaj_rabatu'] != '0':
                r="trline\tna%s\til%.0f\tvt%s\tpr%.0f\twa%.0f\trp%.0f\trd1\t" % (linia['nazwa'], linia['ilosc'], ptu,linia['cena_jednostkowa_brutto']*100, linia['suma_brutto']*100,linia['rabat_proc']*100)
                discount="trfiscntvat\tvt%s\trd1\trp%.0f\t" % (ptu, linia['rabat_proc']*100)
                suma = suma+linia['suma_brutto']*(1-linia['rabat_proc']/100)
                
            else:
                r="trline\tna%s\til%.0f\tvt%s\tpr%.0f\twa%.0f\t" % (linia['nazwa'], linia['ilosc'], ptu, linia['cena_jednostkowa_brutto']*100, linia['suma_brutto']*100)
                suma = suma+linia['suma_brutto']         
            komendy.append(r)
            if discount:
                komendy.append(discount)    
        do_zaplaty = (round(suma*100))
        end='trend\tto%.0f\tfe0\t' %(do_zaplaty)
        komendy.append(end)
            
        return komendy, dane
    
    def przetwarzaj_stopke(self, stopka, komendy, dane):
        """
        @param naglowek: Słownik z parametrami stopki
        @return komendy: String zawierający komendę dla drukarki
        """
        total = stopka['razem']
         #te 4 linijki dodają nam linię stopki na końcu paragonu, z tekstem "Dziękujemy zapraszamy ponownie"
#         setftr="ftrinfoset\ttx&c&bDZIEKUJEMY\n&c&bZAPRASZAMY PONOWNIE\t"
#         komendy.append(setftr)
#         thx="ftrinfoget\t"
#         komendy.append(thx)
        kwota="trftrln\tid36\tna%s\t" % (str(total))
        komendy.append(kwota)
         #te 2 linijki dodają kod kasjera w stopce
#         kasjer="trftrln\tid8\tna%s\t" % (stopka['kod_kasjera'])
#         komendy.append(kasjer)
        endftr="trftrend\t"
        komendy.append(endftr)
        return komendy, dane
    