# -*- coding: utf-8 -*-
##############################################################################
#
# LACAN Technologies Sp. z o.o.
# al. Jerzego Waszyngtona 146
# 04-076 Warszawa
#
# Copyright (C) 2014-2018 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
#
##############################################################################
from lacan_tools.lacan_tools import lacan_round
from lacan_tools.lacan_tools import custom_append_dict
from osv import fields, osv
from optparse import Values


class hr2_payroll_register(osv.osv):
    _inherit = 'hr2.payroll.register'

    def calculate_salary_PL(self,
                            conf,   #słownik konfiguracji
                            elements,
                            #GENERAL
                            contract_type,  #char - etat/cywilnoprawna (e/c)
                            civil_law_contract_with_own_employee,   #bool - czy zawarta jest umowa cywilnoprawca z własnym pracownikiem

                            #ABSENCES
                            sick_days_so_far,           #int - ilość dni choroby do tej pory

                            #ZUS
                            podstawa_wymiaru_skladek_od_pocz_roku, #float
                            calculate_FP,   #bool - czy liczyć składkę FP
                            calculate_FGSP, #bool - czy liczyć składkę FGŚP
                            calculate_emr,  #bool - czy liczyć składkę emerytalną
                            calculate_rent, #bool - czy liczyć składkę rentową
                            calculate_chor, #bool - czy liczyć składkę chorobową
                            calculate_wyp,  #bool - czy liczyć składkę wypadkową
                            calculate_zdr,
                            addition_ZUS,   # float - wartość dodatków, z których trzeba wyliczyć składki ZUS.

                            #PIT, NFZ
                            calculate_tax_exemption,        #bool - czy rozliczać kwotę wolną
                            tax_scale,                      #lista list [[zł od, %],[zł od, %], ... ] - skala podatkowa
                            PIT_income_since_start_of_year, #float - dochód PIT od początku roku
                            tax_deduction,                  #lista [%wyn, kwota, procent]
                            is_not_resident,                #boolean - czy rozliczany pracownik nie jest rezydentem
                            external_tax,                   #float - zaliczka na podatek odprowadzany za granicą

                            #DO WYPŁATY
                            suma_kup_50_ten_rok,
                            deductions_config,
                            absences_list=[[],[]],              #lista list słowników [[{dane nieobecności}],[]], jedna lista to jeden miesiąc, jeden słownik to jedna nieobecność
                            previous_month_data={},        #słownik - dane poprzedniego miesiąca
                            paid_leave_sum=0
                            ):
        """
        return: lista parametrów wyjściowych zgodnie z plikiem paramery.ods
        """

        values = {}

        # value1 = elements['values']['value1']
        # value2 = elements['values']['value2']

        sick_pay = elements.get('sick_pay', 0)
        sick_benefit = elements.get('sick_benefit',0)
        sick_pay_wk = elements.get('sick_pay_without_kup', 0)
        sick_benefit_wk = elements.get('sick_benefit_without_kup',0)
        holidays_payment = elements.get('holidays_payment', 0)
        value3 = elements.get('value3')
        ekwiwalent = elements.get('ekwiwalent', 0)
        additions = elements.get('additions')
        additions_payment = elements.get('additions_payment')
        for addition in additions:
            if not additions_payment:
                addition['procent'] = 0.0
            else:
                addition['procent'] = addition['value'] / additions_payment


        ##### Korekty za zeszły miesiąc #####
        prev_sick_leave_base = previous_month_data.get('sick_leave_base', False)
        prev_gross_salary = previous_month_data.get('gross_salary', False)
        correction = self.calculate_leaves_absences_correction(conf,
                                                               absences_list,
                                                               tax_deduction,
                                                               prev_gross_salary,
                                                               prev_sick_leave_base,
                                                               sick_days_so_far,
                                                               value3)
        corrects = correction.get('corrects', {})
        corrections = correction.get('corrections', {})

        ##### Sumowanie wartości pośrednich #####
        brutto = value3 + additions_payment + holidays_payment + sick_pay + sick_benefit - corrects.get('R', 0)
        if (value3 + additions_payment + holidays_payment) != 0:
            procent_wyplaty_za_dodatki = additions_payment / (value3 + additions_payment + holidays_payment)
            procent_wyplaty_za_prace = value3 / (value3 + additions_payment + holidays_payment) # Potrzebne do heurystyki liczenia Kupów
        else:
            procent_wyplaty_za_dodatki = 0
            procent_wyplaty_za_prace = 0
        if brutto !=0:
            procent_wyplaty_za_zasilki = (sick_benefit + sick_pay) / brutto
        else:
            procent_wyplaty_za_zasilki = 0
        value3 += holidays_payment + additions_payment
        value4 = value3 + sick_pay + sick_benefit


        ##### Czy ryczałt, oblicz ryczał #####
        ryczalt = self.calculate_lump_sum_tax(conf,
                                              value4,
                                              civil_law_contract_with_own_employee,
                                              contract_type)
        if ryczalt and conf['liczenie_malych_umow'] and not is_not_resident:
            ##### ryczałt return #####
            values['podatek_PIT8A'] = ryczalt['podatek_PIT8A']
            values['do_wyplaty'] = ryczalt['do_wyplaty'] - ryczalt['podatek_PIT8A']

            ##### reszta return = 0 #####
            values['wartosc3'] = 0
            values['dochod'] = 0
            values['koszty_uzyskania_przychodu'] = 0
            values['brutto'] = value4
            values['podstawa_wymiaru_skladek'] = 0
            values['skladka_zdrowotna'] = 0
            values['skladka_zdrowotna_odliczona'] = 0
            values['skladka_zdrowotna_od_netto'] = 0
            values['kwota_zaliczki_na_PIT'] = ryczalt['podatek_PIT8A']
            values['do_wyplaty'] = ryczalt['do_wyplaty']
            values['netto'] = 0
            values['kwota_NFZ'] = 0
            values['kwota_US'] = ryczalt['podatek_PIT8A']
            values['chor_pracownik'] = 0
            values['emr_pracownik'] = 0
            values['rent_pracownik'] = 0
            values['emr_pracodawca'] = 0
            values['rent_pracodawca'] = 0
            values['wyp_pracodawca'] = 0
            values['FP'] = 0
            values['FGSP'] = 0
            values['koszty_uzyskania_autorskie'] = 0
            values['potracenia'] = 0
            values['correction_list'] = []
        else:
            values['podatek_PIT8A'] = 0


            ##### ZUS #####
            ZUS = self.calculate_ZUS(conf,
                                     corrects,
                                     podstawa_wymiaru_skladek_od_pocz_roku,
                                     calculate_FP,
                                     calculate_FGSP,
                                     calculate_emr,
                                     calculate_rent,
                                     calculate_chor,
                                     calculate_wyp,
                                     value3,
                                     value4,
                                     addition_ZUS)
            uaktualniona_podstawa_wymiaru_skladek_od_pocz_roku = ZUS['uaktualniona_podstawa_wymiaru_skladek_od_pocz_roku']
            emr_employee_contribution = ZUS.get('emr_employee_contribution', 0)
            emr_employer_contribution = ZUS.get('emr_employer_contribution', 0)
            rent_employee_contribution = ZUS.get('rent_employee_contribution', 0)
            rent_employer_contribution = ZUS.get('rent_employer_contribution', 0)
            chor_employee_contribution = ZUS.get('chor_employee_contribution', 0)
            wyp_employer_contribution = ZUS.get('wyp_employer_contribution', 0)
            FP_contribution = ZUS.get('FP')
            FGSP_contribution = ZUS.get('FGSP')
            value4 = ZUS.get('value4')

            ##### Dla paid_leave bez KUP, odejmuję wartość nieobecności tego typu od value
            ##### Po co? Po to, żeby nie było niepotrzebnej nadwyżki przy liczeniu KUP #####
            if paid_leave_sum:
                temp_value3 = value3 - paid_leave_sum
                temp_value4 = temp_value3 + sick_pay + sick_benefit
                ZUS_temp = self.calculate_ZUS(conf,
                                        corrects,
                                        podstawa_wymiaru_skladek_od_pocz_roku,
                                        calculate_FP,
                                        calculate_FGSP,
                                        calculate_emr,
                                        calculate_rent,
                                        calculate_chor,
                                        calculate_wyp,
                                        temp_value3,
                                        temp_value4,
                                        addition_ZUS)
                temp_value4 = ZUS_temp.get('value4')
            else:
                temp_value4 = value4
            #### Koszty uzyskania przychodu #####
            cost_of_income = self.calculate_cost_of_income(tax_deduction,
                                                           temp_value4,
                                                           suma_kup_50_ten_rok,
                                                           conf['limit_kup_50'],
                                                           conf['koszty_uzyskania'],
                                                           procent_wyplaty_za_prace,
                                                           additions,
                                                           procent_wyplaty_za_dodatki,
                                                           sick_pay_wk,
                                                           sick_benefit_wk,
                                                           external_tax,
                                                           complete_value4=value4
                                                           )
            income = lacan_round(cost_of_income.get('income') + elements.get('bonus', 0), 0) - corrects.get('income')
            income_cost = 0 if is_not_resident else cost_of_income.get('income_cost') - corrects.get('income_cost')
            value4 -= corrects.get('val4', 0)
                     
            ##### PIT i NFZ #####
            PIT_NFZ = self.calculate_PIT_NFZ(conf,
                                          calculate_zdr,
                                          sick_benefit,
                                          value4,
                                          contract_type,
                                          calculate_tax_exemption,
                                          PIT_income_since_start_of_year,
                                          tax_scale,
                                          income,
                                          brutto,
                                          is_not_resident,
                                          addition_ZUS,
                                          external_tax)
            PIT_contribution = PIT_NFZ.get('PIT_contribution')
            skladka_zdr_PIT = PIT_NFZ.get('skladka_zdr_PIT')
            NFZ_payment = PIT_NFZ.get('NFZ_payment')
            US_payment = PIT_NFZ.get('US_payment')
            value6 = PIT_NFZ.get('value6')

            # Odlicz zaliczkę na zagraniczny podatek.
            if external_tax:
                value6 -= external_tax

            ##### Potrącenia #####
            potracenia = self.calculate_deductions(value6, deductions_config, additions, procent_wyplaty_za_dodatki, procent_wyplaty_za_zasilki)
            wyplata = self.calculate_payout(potracenia, value6)
            payout = wyplata.get('payout')


            ##### return #####
            values['wartosc3'] = value3
            values['brutto'] = lacan_round(brutto, 2)
            values['dochod'] = income
            values['koszty_uzyskania_przychodu'] = income_cost
            values['podstawa_wymiaru_skladek'] = uaktualniona_podstawa_wymiaru_skladek_od_pocz_roku
            values['skladka_zdrowotna_odliczona'] = skladka_zdr_PIT
            values['skladka_zdrowotna_od_netto'] = NFZ_payment - skladka_zdr_PIT
            values['kwota_zaliczki_na_PIT'] = PIT_contribution
            values['do_wyplaty'] = payout + ekwiwalent
            values['netto'] = value6
            values['kwota_NFZ'] = NFZ_payment
            values['kwota_US'] = US_payment
            values['chor_pracownik'] = chor_employee_contribution
            values['emr_pracownik'] = emr_employee_contribution
            values['rent_pracownik'] = rent_employee_contribution
            values['emr_pracodawca'] = emr_employer_contribution
            values['rent_pracodawca'] = rent_employer_contribution
            values['wyp_pracodawca'] = wyp_employer_contribution
            values['FP'] = FP_contribution
            values['FGSP'] = FGSP_contribution
            values['koszty_uzyskania_autorskie'] = cost_of_income.get('koszty_autorskie')
            values['potracenia'] = potracenia
            values['corrections'] = corrections
            values['zmniejszenie_zaliczki'] = conf['kwota_wolna'] if not external_tax else 0
        return values

    def calculate_leaves_absences_correction(self,
                                             conf,
                                             absences_list,
                                             tax_deduction,
                                             prev_gross_salary,
                                             prev_sick_base,
                                             sick_days_so_far,
                                             value3):
        """ Oblicza korekty za nierozliczone chorobowe z zeszłego miesiąca.
            @param conf: parametry konfiguracyjne,
            @param absences_list: lista dwóch list słowników [[{dane nieobecności}],[]],
            @param tax_deduction: lista, informacje na temat kosztów uzyskania przychodu [%wyn, kwota, procent],
            @param prev_gross_salary: float,
            @param prev_sick_base: float,
            @param sick_days_so_far: int,
            @param value3: float,
            @return: słownik zawierający wartości korekt. """
        paid_sick_leave_limit = conf['paid_sick_leave_limit']

        minus_za_chor = 0
        R = 0
        correction_list = []
        deductions = []
        for absence in absences_list[:-1][0]:
            if absence['type'] in ['sick_leave', 'child_care']:
                days = absence['days']
                sick_days_so_far += days

                P = 0
                Z = 0   # Wynagrodzenie chorobowe (P) czy zasiłek (Z)?

                if absence['type'] == 'child_care':
                    Z = float(days)
                elif paid_sick_leave_limit - sick_days_so_far > days:
                    P = float(days)
                elif paid_sick_leave_limit - sick_days_so_far > 0:
                    P = days - (paid_sick_leave_limit - sick_days_so_far)
                    Z = days - P
                elif paid_sick_leave_limit - sick_days_so_far < days:
                    Z = float(days)

                if P > 0:   # Tworzenie listy linii korekt.
                    sick_pay = lacan_round(prev_sick_base * absence['paid_leave_rate']/30, 2) * P
                    correction_list.append({
                        'base': prev_sick_base,
                        'value': sick_pay,
                        'absence_id': absence['absence_id'],
                        'date_start': absence['date_from'],
                        'date_stop': absence['date_to'],
                        'p_days': P})
                if Z > 0:
                    sick_benefit = lacan_round(prev_sick_base * absence['paid_leave_rate']/30, 2) * Z
                    correction_list.append({
                        'base': prev_sick_base,
                        'value': sick_benefit,
                        'absence_id': absence['absence_id'],
                        'date_start': absence['date_from'],
                        'date_stop': absence['date_to'],
                        'z_days': Z})

                # Obliczanie pomniejszeń.
                R += lacan_round(P/30.0 * prev_sick_base * absence['paid_leave_rate'], 2)
                deduction = lacan_round(days/30.0 * prev_gross_salary, 2)
                minus_za_chor += deduction
                deductions.append(-deduction)

        # Korekty składek.
        Re = minus_za_chor * conf['stawka_emr_pracownik']
        Rep = minus_za_chor * conf['stawka_emr_pracodawca']
        Rch = minus_za_chor * conf['stawka_chor_pracownik']
        Rw = minus_za_chor * conf['ubezpieczenie_wpadkowe']
        Rr = minus_za_chor * conf['stawka_rent_pracownik']
        Rrp = minus_za_chor * conf['stawka_rent_pracodawca']
        Rfgps = minus_za_chor * conf['stawka_FGSP']
        Rfp = minus_za_chor * conf['stawka_FP']

        # Pozostałe korekty.
        new_value3 = value3 - minus_za_chor
        if tax_deduction[2]:    # Procentowe koszty uzyskania.
            income_cost = - (-minus_za_chor + Re + Rr + Rch) * (1 - tax_deduction[0]) * tax_deduction[2]
            income = minus_za_chor - income_cost - R - Re - Rr - Rch
            val4 = minus_za_chor - R - Re - Rr - Rch
        else:                   # Kwotowe koszty uzyskania.
            income_cost = 0
            val4 = income = minus_za_chor - R - Re - Rr - Rch
        minus_za_chor -= R

        # Return dict.
        values = {
            'corrections': {
                'value3': new_value3,
                'correction_list': correction_list,
                'deductions': deductions,
            },
            'corrects': {
                'R': lacan_round(minus_za_chor, 2),
                'Re': Re,
                'Rep': Rep,
                'Rch': Rch,
                'Rw': Rw,
                'Rr': Rr,
                'Rrp': Rrp,
                'Rfgps': Rfgps,
                'Rfp': Rfp,
                'income_cost': lacan_round(income_cost, 2),
                'income': lacan_round(income, 0),
                'val4': lacan_round(val4, 2),
            },
        }
        return values

    def calculate_lump_sum_tax(self,
                               conf,
                               value3,
                               civil_law_contract_with_own_employee,
                               contract_type):
        """funkcja odpowiada za obliczenia podatku zryczałtowanego

        @param conf - słownik wszyskich parametrów konfiguracyjnych zgodnie z formatem funkcji get_hrconf()
        @param value3 - float
        @param civil_law_contract_with_own_employee - bool

        ryczalt - bool, czy umowa jest umową opodatkowaną podatkiem zryczałtowanym
        podatek_PIT8A - float, podatek
        do_wyplaty - float, kwota do wyplaty
        """

        if contract_type == 'c' and value3 <= conf['granica_kwoty_um_cywilpraw_do_podat_zrycz'] and not civil_law_contract_with_own_employee:
            ryczalt = True

            podatek_PIT8A = lacan_round(value3 * conf['stawka_podatku_ryczalt'], 0)
            do_wyplaty = value3 - podatek_PIT8A

            return {'ryczalt' : ryczalt,
                    'podatek_PIT8A' : podatek_PIT8A,
                    'do_wyplaty' : do_wyplaty}


    def calculate_ZUS(self,
                      conf,
                      corrects,
                      podstawa_wymiaru_skladek_od_pocz_roku,
                      calculate_FP,
                      calculate_FGSP,
                      calculate_emr,
                      calculate_rent,
                      calculate_chor,
                      calculate_wyp,
                      value3,
                      value4,
                      addition_ZUS):
        """funkcja odpowiada za obliczenia składek ZUS

        @param conf - słownik wszyskich parametrów konfiguracyjnych zgodnie z formatem funkcji get_hrconf()
        @param podstawa_wymiaru_skladek_od_pocz_roku - float
        @param calculate_FP - bool
        @param calculate_FGSP - bool
        @param calculate_emr - bool
        @param calculate_rent - bool
        @param calculate_chor - bool
        @param calculate_wyp - bool
        @param value3 - float
        @param value4 - float
        @param addition_ZUS - float, wartość dodatków, z których muszą zostać wyliczone składki ZUS (niezależnie od innych parametrów).

        return:
        FP - float, składka FP
        FGSP - float, składka FGŚP
        emr_employee_contribution - float, składka emerytalna pracownika
        emr_employer_contribution - float, składka emerytalna pracodawcy
        rent_employee_contribution - float, składka rentowa pracownika
        rent_employer_contribution - float, składka rentowa pracodawcy
        chor_employee_contribution - float, składka chorobowa
        wyp_employer_contribution - float, składka wypadkowa
        uaktualniona_podstawa_wymiaru_skladek_od_pocz_roku - float """
        values = {}

        # Składki chorobowe, wypadkowe, FGSP, FP.
        values['chor_employee_contribution'] = conf['stawka_chor_pracownik'] * value3 if calculate_chor else 0
        values['wyp_employer_contribution'] = conf['ubezpieczenie_wpadkowe'] * value3 if calculate_wyp else 0
        values['FGSP'] = conf['stawka_FGSP'] * value3 if calculate_FGSP else 0
        values['FP'] = conf['stawka_FP'] * value3 if calculate_FP else 0

        if (calculate_emr or calculate_rent) and podstawa_wymiaru_skladek_od_pocz_roku < conf['maks_rocz_pdstwa_wymiaru_dla_ubzp_emr_i_rent']:
            if (podstawa_wymiaru_skladek_od_pocz_roku + value3) < conf['maks_rocz_pdstwa_wymiaru_dla_ubzp_emr_i_rent']:
                value31 = value3
            else:
                value31 = conf['maks_rocz_pdstwa_wymiaru_dla_ubzp_emr_i_rent'] - podstawa_wymiaru_skladek_od_pocz_roku

            # Składki emerytalne, rentowe.
            if calculate_emr:
                values['emr_employee_contribution'] = conf['stawka_emr_pracownik'] * value31
                values['emr_employer_contribution'] = conf['stawka_emr_pracodawca'] * value31
            if calculate_rent:
                values['rent_employee_contribution'] = conf['stawka_rent_pracownik'] * value31
                values['rent_employer_contribution'] = conf['stawka_rent_pracodawca'] * value31
            values['uaktualniona_podstawa_wymiaru_skladek_od_pocz_roku'] = podstawa_wymiaru_skladek_od_pocz_roku + value31
        else:
            values['emr_employee_contribution'] = 0
            values['emr_employer_contribution'] = 0
            values['rent_employee_contribution'] = 0
            values['rent_employer_contribution'] = 0
            values['uaktualniona_podstawa_wymiaru_skladek_od_pocz_roku'] = podstawa_wymiaru_skladek_od_pocz_roku

        if addition_ZUS:    # Wylicz składki z dodatków obciążonych przez ZUS.
            values['emr_employee_contribution'] += conf['stawka_emr_pracownik'] * addition_ZUS
            values['emr_employer_contribution'] += conf['stawka_emr_pracodawca'] * addition_ZUS
            values['chor_employee_contribution'] += conf['stawka_chor_pracownik'] * addition_ZUS
            values['wyp_employer_contribution'] += conf['ubezpieczenie_wpadkowe'] * addition_ZUS
            values['rent_employee_contribution'] += conf['stawka_rent_pracownik'] * addition_ZUS
            values['rent_employer_contribution'] += conf['stawka_rent_pracodawca'] * addition_ZUS
            values['FGSP'] += conf['stawka_FGSP'] * addition_ZUS
            values['FP'] += conf['stawka_FP'] * addition_ZUS

        # Pomniejszenie value4 o składki pracownika.
        employee = ['emr_employee_contribution', 'chor_employee_contribution', 'rent_employee_contribution']
        for field in employee:
            if field in values:
                    value4 -= lacan_round(values[field], 2)
        values['value4'] = value4

        # Pomniejszanie o korekty.
        values['emr_employee_contribution'] = values.get('emr_employee_contribution', 0) - corrects.get('Re', 0)
        values['emr_employer_contribution'] = values.get('emr_employer_contribution', 0) - corrects.get('Rep', 0)
        values['rent_employee_contribution'] = values.get('rent_employee_contribution', 0) - corrects.get('Rr', 0)
        values['rent_employer_contribution'] = values.get('rent_employer_contribution', 0) - corrects.get('Rrp', 0)
        values['chor_employee_contribution'] = values.get('chor_employee_contribution', 0) - corrects.get('Rch', 0)
        values['wyp_employer_contribution'] = values.get('wyp_employer_contribution', 0) - corrects.get('Rw', 0)
        values['FGSP'] = values.get('FGSP', 0) - corrects.get('Rfgsp', 0)
        values['FP'] = values.get('FP', 0) - corrects.get('Rfp', 0)

        # Zaokrąglanie składek do 2 miejsc po przecinku.
        for k, v in values.items():
            values[k] = lacan_round(v, 2)

        return values
    
    def calculate_cost_of_income(self,
                                 tax_deduction,
                                 value4,
                                 suma_kup_50_ten_rok,
                                 limit_kup_50,
                                 koszty_uzyskania_conf,
                                 procent_wyplaty_za_prace,
                                 additions,
                                 procent_wyplaty_za_dodatki,
                                 sick_pay,
                                 sick_benefit,
                                 external_tax,
                                 complete_value4=None
                                 ):
        """
        Funkcja obliczająca dochód i koszty uzyskania przychodu

        @param tax_deduction - lista zawierająca informacje o kosztach uzyskania przychodu - float
        pierwszy element zawiera informacje o procencie pensji objętej kosztami liniowymi w postaci ułamka dziesiętnego
        drugi kwote kosztu uzyskania liniowego
        trzeci procent uzyskania kosztów w postaci ułamka dziesiętnego
        @param value4 - float
        @param suma_kup_50_ten_rok - float
        @param limit_kup_50 - float
        return:
        income - float, dochód
        income_costs - float, koszt uzyskania przychodu (kwota)
        koszty_autorskie - float, koszty uzyskania od praw autorskich
        """
        if external_tax:
            # Pomiń naliczanie KUP.
            return {
                'income': value4,
                'income_cost': 0.0,
                'koszty_autorskie': 0.0,
            }

        values = {}
        sumakup = suma_kup_50_ten_rok
        additions_value_jak_podstawa = 0
        '''Uaktualniam kwoty dodatkow sumuje dodatki liczace sie jak podstawa'''
        additions_value = (value4 - sick_benefit - sick_pay)*procent_wyplaty_za_dodatki
        for addition in additions:
            addition['value'] = addition['procent'] * additions_value

            if addition['licz_kup_jak_podstawa'] and addition['value'] > 0 and 'etat' in addition and addition['etat']['inne_koszty'] != 0:
                if addition['value'] < addition['etat']['inne_koszty']:
                    additions_value_jak_podstawa += addition['value']
                else:
                    additions_value_jak_podstawa += addition['etat']['inne_koszty']

            elif 'etat' in addition and addition['etat']['inne_koszty'] == 0 and addition['etat']['wynagrodzenie_z_procentowym_kosztem'] == 100:

                if koszty_uzyskania_conf < addition['etat']['inne_koszty']:
                    additions_value_jak_podstawa += koszty_uzyskania_conf
                else:
                    additions_value_jak_podstawa += addition['etat']['inne_koszty']
            elif addition['licz_kup_jak_podstawa']:
                additions_value_jak_podstawa += addition['value']

        podstawa =(value4 - sick_benefit - sick_pay)*procent_wyplaty_za_prace
        ''' Koszty uzyskania przychodu kwotowe'''
        kup_kwota=tax_deduction[1]
        '''Koszty uzyskania procentowe'''
        if tax_deduction[2] == 0.5:
            koszty_autorskie = lacan_round(tax_deduction[2] * (podstawa+additions_value_jak_podstawa)*(1-tax_deduction[0]), 2)
            sumakup += koszty_autorskie
            if sumakup > limit_kup_50:
                koszty_autorskie=limit_kup_50-sumakup+koszty_autorskie
                koszty_autorskie = lacan_round(koszty_autorskie, 2)
                kup_kwota += koszty_autorskie
            elif sumakup == limit_kup_50:
                koszty_autorskie = 0
            else:
                kup_kwota += koszty_autorskie

        else:
            kup_kwota += lacan_round(tax_deduction[2] * (podstawa+additions_value_jak_podstawa)*(1-tax_deduction[0]), 2)
            koszty_autorskie = 0


        # Jeżeli w tym okresie u pracownika były paid_leave, value4 który wszedł do funkcji nie zawiera ich wartości.
        # real_value4 to niezmodyfikowane value4, które zawiera już w sobie wartość paid_leavów.
        if complete_value4:
            value4 = complete_value4

        ### Dochód ###
        values['income_cost'] = lacan_round(kup_kwota, 2)
        values['income'] = value4 - values['income_cost']
        values['koszty_autorskie'] = lacan_round(koszty_autorskie, 2)

        return values


    def calculate_PIT_NFZ(self,
                          conf,
                          calculate_zdr,
                          sick_benefit,
                          value4,
                          contract_type,
                          calculate_tax_exemption,
                          PIT_income_since_start_of_year,
                          tax_scale,
                          income,
                          brutto,
                          is_not_resident,
                          addition_ZUS,
                          external_tax,
                          ):
        """funkcja odpowiada za obliczenia składek PIT i NFZ

        @params conf - słownik wszyskich parametrów konfiguracyjnych zgodnie z formatem funkcji get_hrconf()
        @params calculate_emr - bool
        @params calculate_rent - bool
        @params sick_benefit - float
        @params value4 - float
        @params tax_deduction - lista dwóch list [[%wynagrodzenia, kwota, procent],[%wynagrodzenia, kwota, procent]]
        @params contract_type - char
        @params calculate_tax_exemption - bool
        @params total_absences_days - int
        @params days_to_fill - int
        @params PIT_income_since_start_of_year - float
        @params tax_scale - lista list [[zł od, %],[zł od, %], ... ]
        @params limit_contribution_to_advance_payment - bool
        @params kwota wolna - float
        @params addition_ZUS - float, wartość dodatków obciążonych ZUS (do doliczenia do zaliczki na podatek dochodowy)

        return:
        PIT_contribution - float, zaliczka PIT
        US_payment - float, kwota podatku do US
        skladka_zdr_PIT - float, kwota skladki zdrowotnej PIT
        skladka_zdr_pracownik - float, kwota skladki zdrowotnej pracownika
        health_contribution - float, składka zdrowotna cała
        NFZ_payment - float, kwota skladki do NFZ
        income - float, dochód
        income_costs - float, koszty uzyskania dochodu
        value6 - float
        """

        ### Składka zdrowotna ###
        skladka_zdr_od_netto = conf['stawka_zdr_pracownik'] * (value4 + addition_ZUS - sick_benefit) if calculate_zdr else 0
        skladka_zdr_PIT = conf['stawka_zdr_PIT'] * (value4 + addition_ZUS - sick_benefit) if calculate_zdr else 0

        if not external_tax:
            ##### Ustal kwotę zaliczki #####
            stawka = 0
            if contract_type == 'e':
                for prog in tax_scale:
                    if prog[0] > PIT_income_since_start_of_year:
                        break
                    stawka = prog[1]

                if calculate_tax_exemption:
                    PIT_contribution = stawka * income - conf['kwota_wolna']
                    if PIT_contribution < 0:
                        PIT_contribution = 0
                else:
                    PIT_contribution = stawka * income
            else:
                for prog in tax_scale:
                    if prog[0] <= income:
                        stawka = prog[1]/100.0
                        break
                if is_not_resident:
                    PIT_contribution = stawka * brutto
                else:
                    PIT_contribution = stawka * income
        else:
            PIT_contribution = 0

        ### Podatki ###
        if is_not_resident:
            US_payment = lacan_round(PIT_contribution,0)
            NFZ_payment = skladka_zdr_od_netto + skladka_zdr_PIT
        else:
            if (skladka_zdr_od_netto + skladka_zdr_PIT) > PIT_contribution and conf['ograniczenie_skladki_do_wysokosci_zaliczki']:
                #Zaliczka na PIT mniejsza od ubezpieczenia zdrowotnego
                if skladka_zdr_PIT > PIT_contribution:
                    US_payment = 0
                    NFZ_payment = PIT_contribution
                    skladka_zdr_PIT = PIT_contribution
                    skladka_zdr_od_netto = 0
                else:
                    #Składka do odliczenia mniejsza od zaliczki na PIT
                    skladka_zdr_od_netto = PIT_contribution - skladka_zdr_PIT
                    US_payment = lacan_round((PIT_contribution - skladka_zdr_PIT), 0)
                    NFZ_payment = PIT_contribution
            else:
                #Wszystko normalnie
                US_payment = lacan_round(PIT_contribution - skladka_zdr_PIT, 0)
                NFZ_payment = skladka_zdr_od_netto + skladka_zdr_PIT

        ### Netto ###
        value6 = value4 - US_payment - NFZ_payment
        return {
                'PIT_contribution': lacan_round(PIT_contribution, 2),
                'skladka_zdr_PIT': lacan_round(skladka_zdr_PIT, 2),
                'NFZ_payment': lacan_round(NFZ_payment, 2),
                'US_payment': US_payment,
                'value6': lacan_round(value6, 2),
                }

    def calculate_deductions(self, value6, deduction_config, additions, procent_wyplaty_za_dodatki, procent_wyplaty_za_zasilki):
        """funkcja odpowiada za obliczanie potracen od wyplaty
        @params value6 - float
        @params deduction_config - lista słowników gdzie każdy słownik powinien zawierać elementy
        "%egzekucji" - % wypłaty podlegającej egzekucji w postaci ułamka dziesiętnego- float
        "kwota_wolna" - kwota_wolna od potrącenia - float
        "kwota" - kwota potrącenia - float
        "code" - kod potrącenia - string
        lub 0 jeśli nie ma potrąceń
        return:
        słownik gdzie kluczami są kody potrąceń a wartościami obliczone kwoty potrącone z wypłaty"""

        '''Uaktualniam kwoty dodatkow'''

        zasilki_value = value6 * procent_wyplaty_za_zasilki
        dodatki_value = (value6 - zasilki_value) * procent_wyplaty_za_dodatki
        wyplata_bez_zasilkow = value6 - zasilki_value
        podstawa_kwoty_wolnej = wyplata_bez_zasilkow
        suma_potracen = 0
        suma_potracen_alimenty = 0

        for addition in additions:
            addition['value'] = addition['procent'] * dodatki_value
        values = {}
        if not deduction_config['deductions']:
             return values

        if deduction_config['typ'] == 'e':
            for deduction in deduction_config['deductions']:
                values[deduction['code']] = 0
                '''Potracenia z dodatkow'''
                potracenie_laczne = 0
                for addition in additions:
                    if lacan_round(addition['value'],2) ==0:
                        continue
                    if addition['code'] in deduction['special1_code_list']:
                        kwota_max1 = deduction['%special1']/100 * addition['value']-suma_potracen+suma_potracen_alimenty
                    elif addition['code'] in deduction['special2_code_list']:
                        kwota_max1 = deduction['%special2']/100 * addition['value']-suma_potracen+suma_potracen_alimenty
                    else:
                        kwota_max1=deduction['%egzekucji'] * addition['value']-suma_potracen+suma_potracen_alimenty
                    kwota_max1 = lacan_round(kwota_max1,2)
                    kwota_max2 = podstawa_kwoty_wolnej-deduction['kwota_wolna']-suma_potracen
                    kwota_max2 = lacan_round(kwota_max2, 2)
                    if deduction['type_code']==deduction_config['kara_code']:
                        potracenie = min([kwota_max1,deduction['kwota']])
                    else:
                        potracenie = min([kwota_max1, kwota_max2, deduction['kwota']])
                    if potracenie < 0:
                        potracenie = 0
                    addition['value'] -= potracenie
                    deduction['kwota'] -= potracenie
                    potracenie_laczne += potracenie
                    if deduction['type_code']==deduction_config['alimenty_code']:
                        suma_potracen_alimenty += potracenie
                        suma_potracen+=potracenie
                    else:
                        suma_potracen+= potracenie
                    if deduction['kwota'] == 0:
                        break
                '''Potracenie z podstawy wynagrodzenia'''
                kwota_max1 = deduction['%egzekucji'] * wyplata_bez_zasilkow - suma_potracen +suma_potracen_alimenty
                kwota_max1 = lacan_round(kwota_max1, 2)
                kwota_max2 = podstawa_kwoty_wolnej-deduction['kwota_wolna']-suma_potracen
                kwota_max2 = lacan_round(kwota_max2, 2)
                kwota_max3 = 0.6 * wyplata_bez_zasilkow - suma_potracen
                kwota_max3 = lacan_round(kwota_max3, 2)
                if deduction['type_code']==deduction_config['kara_code']:
                    potracenie = min([kwota_max1,deduction['kwota']])
                else:
                    potracenie = min([kwota_max1, kwota_max2, kwota_max3, deduction['kwota']])
                if potracenie < 0:
                        potracenie = 0
                if deduction['type_code']==deduction_config['alimenty_code']:
                        suma_potracen_alimenty += potracenie
                        suma_potracen+=potracenie
                else:
                        suma_potracen+= potracenie
                deduction['kwota'] -= potracenie
                potracenie_laczne += potracenie
                values[deduction['code']] = potracenie_laczne
                if deduction['kwota'] == 0:
                    continue
            suma_potracen_alimenty = 0
            suma_potracen=0
            '''Potracenia z zasilkow'''
            for deduction in deduction_config['deductions']:
                    kwota_max1 = deduction['%zus']/100 * zasilki_value - suma_potracen + suma_potracen_alimenty
                    kwota_max1 = lacan_round(kwota_max1,2)
                    kwota_max2 = zasilki_value - deduction['kwota_wolna_zus']-suma_potracen
                    kwota_max3 = 0.6 * wyplata_bez_zasilkow - suma_potracen_alimenty
                    kwota_max3 = lacan_round(kwota_max3, 2)
                    if deduction['type_code']==deduction_config['kara_code']:
                        potracenie = min([kwota_max1,deduction['kwota']])
                    else:
                        potracenie = min([kwota_max1, kwota_max2, kwota_max3, deduction['kwota']])
                    if deduction['type_code']==deduction_config['alimenty_code']:
                        suma_potracen_alimenty += potracenie
                        suma_potracen+=potracenie
                    else:
                        suma_potracen+= potracenie
                    if potracenie < 0:
                        potracenie = 0
                    deduction['kwota'] -= potracenie
                    potracenie_laczne += potracenie
                    values[deduction['code']] += potracenie
        elif deduction_config['typ'] == 'c':
            for deduction in deduction_config['deductions']:
                kwota_max1 = value6 - deduction['kwota_wolna']
                kwota_max1 = lacan_round(kwota_max1,2)
                kwota_max2 = value6 * deduction['%egzekucji']
                kwota_max2 = lacan_round(kwota_max2, 2)
                kwota_max3 = deduction['kwota']
                kwota_max3 = lacan_round(kwota_max3, 2)
                potracenie = min([kwota_max1, kwota_max2, kwota_max3])
                values[deduction['code']] = potracenie
                value6 -= potracenie
        return values

    def calculate_payout(self,
                         salary_deductions,
                         value6):
        """Oblicza kwotę do wypłaty odejmując od niej potrącenia

        @params salary_deductions - słownik gdzie kluczami są kody potrąceń a wartościami potrącenia
        @params value6 - float

        return:
        payout - float, kwota do wypłaty
        """
        values = {}
        if not salary_deductions:
            salary_deduction = 0
        else:
            salary_deduction = sum(salary_deductions.values())
        if salary_deduction != 0:
            if value6 - salary_deduction:
                values['payout'] = value6 - salary_deduction
        else:
            values['payout'] = value6

        return values


