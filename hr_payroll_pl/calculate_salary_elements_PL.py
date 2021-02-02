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
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import calendar

import tools
from lacan_tools import lacan_tools
from lacan_tools.lacan_tools import lacan_round
from osv import osv
from tools.translate import _


class hr2_payroll_register(osv.osv):
    _inherit = 'hr2.payroll.register'

    '''START of the [calculate_elements] block for posts'''
    def calculate_elements(self, cr, uid,
                          contract_type,                    #char - etat/cywilnoprawna (e/c)
                          gross_salary,                     #float - kwota brutto z umowy
                          post,
                          register_vals,
                          #Absences
                          sick_days_so_far,                 #int - ilość dni choroby do tej pory
                          paid_sick_leave_limit,            #int - ilość dni choroby za które wynagrodzenie finansuje pracodawca
                          sick_leave_over_90,               #bool - czy jest nieobecność trwają ponad 90 dni
                          valid_sickness_insurance,         #bool - czy posiada ubezpieczenie chorobowe
                          #Uzywane dane ZUS/PIT
                          calculate_chor,                   #bool - czy liczyć składkę chorobową
                          is_january,                       #bool - czy rozliczany miesiąc to styczeń
                          context=None,
                                  ):

        post_data = self.pool.get('hr2.etat').read(cr, uid, post,['employee_id', 'sign_date', 'discharge_date'])
        employee_id = post_data['employee_id'][0]
        return_data = {}

        '''Generating periods'''
        period_list = self.generate_periods(cr, uid, post, register_vals, context=context)
        hours_to_fill = period_list['hours_to_fill'] #Hours that should be filled by the employee in the current month

        '''Adding hours filled in every working period'''
        new_period_list = []
        for period in period_list['work_time_list']:
            period['hours'] = self.work_time_hours(cr, uid, employee_id, period['date_start'], period['date_start'],
                                                   period['date_stop'], ['multiple','working'], search_type='filled', context=context)
            new_period_list.append(period)

        if new_period_list:
            period_list['work_time_list'] = new_period_list #Substituting the periods with the periods containing hours
        
        '''Get the parameter value'''
        try:
            liczba_miesiecy_do_wyliczenia_podstawy_urlopu = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Liczba miesięcy do wyliczenia podstawy urlopu')
        except ValueError:
            pass
        
        first_day_month = date(register_vals['register_year'],int(register_vals['register_month']),01)
        full_month = True if post_data['sign_date'][0] <= first_day_month.strftime('%Y-%m-%d') else False
        if full_month and post_data['discharge_date']:
            if post_data['discharge_date'][0] <= (first_day_month + relativedelta(months=1) - timedelta(days=1)).strftime('%Y-%m-%d'):
                full_month = False

        holidays_dict = {
            'first_day': str(first_day_month - relativedelta(months=liczba_miesiecy_do_wyliczenia_podstawy_urlopu)),
            'last_day': str(first_day_month - timedelta(days=1)),
            'liczba_miesiecy_do_wyliczenia_podstawy_urlopu': liczba_miesiecy_do_wyliczenia_podstawy_urlopu,
            'post': post,
            'post_sign_date': post_data['sign_date'],
            'employee_id': employee_id,
        }

        '''Fetching absences'''
        '''Managing paid leaves.'''
        current_absences_list = self.get_absences(cr, uid, period_list['work_time_list'], employee_id, context=context)
        current_paid_leaves = [leave for leave in current_absences_list if leave['type'] == 'paid_leave']

        if current_paid_leaves:
            for numerator, work_time_period in enumerate(period_list['work_time_list']):
                period_paid_leaves = [ppl['hours'] for ppl in current_paid_leaves if ppl['etat_data_id'] == work_time_period['etat_data_id']]
                ppl_hours = sum(period_paid_leaves)
                period_list['work_time_list'][numerator]['hours'] += ppl_hours



        '''Generating base_salary (value1) for each period'''
        base_salary = self.compute_base_salary(cr, uid, post, register_vals, hours_to_fill, gross_salary, period_list['work_time_list'], context['hours_work'])
        value1 = base_salary['value1']
        addition_dict_list = base_salary['addition_dict_list']
        
        for addition_element in addition_dict_list:
            addition_element['register_id'] = register_vals['id'] 

        #If base_salary computed value1, updated work_time_list is being returned.
        if base_salary['work_time_list']:
            work_time_list = base_salary['work_time_list']
        else:
            work_time_list = period_list['work_time_list']

        current_absences_list = [current_abs for current_abs in current_absences_list if current_abs['type'] != 'paid_leave']
        '''Sick leave base'''
        podstawa_chorobowego = False
        wymaga_korekty = False
        for absence in current_absences_list:
            if absence['type'] in ['sick_leave', 'child_care']:
                podstawa_chorobowego, wymaga_korekty = self.wylicz_podstawe_chorobowego(cr, uid, register_vals, employee_id, context=context)
                podstawa_chorobowego = lacan_round(podstawa_chorobowego, 2)
                break
        self.uaktualnij_podstawe(cr, uid, current_absences_list, podstawa_chorobowego, context=context)

        if wymaga_korekty:
            correction_index = 0
            for absence in current_absences_list:
                current_absences_list[correction_index]['wymaga_korekty'] = True
                correction_index += 1

        '''Absences'''
        '''Computing absences in regard to every work_time_period
        NOTE: This also creates deduction list for every work_time, passing it for viewing in payslip view
        Holidays_payment and sick_benefit are added in calculate_salary_PL
        '''
        final_work_time_list = []
        final_absences_list = []
        value3 = 0
        holidays_payment = 0
        sick_pay = 0
        sick_benefit = 0

        for work_time_period in work_time_list:
            work_time_period['value'] = 0
            '''Dodać wyjątek, gdzie za cały miesiąc spędzony na chorobie nie dostaje się wynagrodzenia za czas przepracowany (tylko w lutym)'''
            absences = self.calculate_leaves_absences(cr,
                                                      uid,
                                                      full_month,
                                                      current_absences_list, #previously absences_list[-1]
                                                      work_time_period['working_hours'],
                                                      calculate_chor,
                                                      sick_days_so_far,
                                                      paid_sick_leave_limit,
                                                      podstawa_chorobowego,
                                                      sick_leave_over_90,
                                                      valid_sickness_insurance,
                                                      work_time_period['value1'],
                                                      work_time_period,
                                                      holidays_dict,
                                                      base_salary['in_month_discharge'])

            # Temporary insert of paid_leaves into the database has to occur here.
            # I am so, so sorry. Paid_leaves are later, fetched, kind-of used
            # and deleted in [update_payslip_for_post] method
            if current_paid_leaves:
                paid_leaves_now = self.calculate_leaves_absences(cr,
                                                          uid,
                                                          full_month,
                                                          current_paid_leaves,
                                                          work_time_period['working_hours'],
                                                          calculate_chor,
                                                          sick_days_so_far,
                                                          paid_sick_leave_limit,
                                                          podstawa_chorobowego,
                                                          sick_leave_over_90,
                                                          valid_sickness_insurance,
                                                          work_time_period['value1'],
                                                          work_time_period,
                                                          holidays_dict,
                                                          base_salary['in_month_discharge'])
                for cpl in paid_leaves_now['absences_list']:
                    value = self.calculate_holidays(cr,
                                                  uid,
                                                  work_time_period['value1'],
                                                  cpl['hours'],
                                                  hours_to_fill,
                                                  holidays_dict)
                    data_dict = {'payslip_id': context['payslip_id'],
                                 'type_id': cpl['type_id'],
                                 'value': value,
                                 'licz_KUP_jak_podstawa': cpl['kup']}
                    cr.execute('''
                            INSERT INTO hr2_payslip_line_temp
                            (payslip_id, type_id, value, "licz_KUP_jak_podstawa")
                            VALUES ({payslip_id}, {type_id}, {value}, {licz_KUP_jak_podstawa})'''.format(**data_dict))

            work_time_period['value3'] = absences['value3']
            value3 += work_time_period['value3']
            work_time_period['deduction_list'] = absences['deduction_list']
            work_time_period['register_id'] = register_vals['id']
            
            for calculated_absence in absences['absences_list']:
                calculated_absence['register_id'] = register_vals['id']
                final_absences_list.append(calculated_absence)
            
            holidays_payment += absences['holidays_payment']
            sick_pay += absences['sick_pay']
            sick_benefit += absences['sick_benefit']
            final_work_time_list.append(work_time_period)

        if podstawa_chorobowego:
            return_data['podstawa_chorobowego'] = podstawa_chorobowego

        return_data['absences_list'] = final_absences_list
        return_data['work_time_list'] = final_work_time_list
        return_data['value3'] = value3
        return_data['contract_type'] = contract_type
        return_data['value1'] = value1
        return_data['holidays_payment'] = holidays_payment
        return_data['sick_pay'] = sick_pay
        return_data['sick_benefit'] = sick_benefit
        return_data['wymaga_korekty'] = wymaga_korekty
        return_data['addition_dict_list'] = addition_dict_list

        self.update_post_additions(cr, uid, final_work_time_list, context['payslip_id'])

        return return_data

    def calculate_leaves_absences(self,
                                  cr,
                                  uid,
                                  full_month,
                                  current_absences_list,
                                  hours_to_fill,
                                  calculate_chor,
                                  sick_days_so_far,
                                  paid_sick_leave_limit,
                                  sick_leave_base,
                                  sick_leave_over_90,
                                  valid_sickness_insurance,
                                  value1,
                                  work_time_period,
                                  holidays_dict,
                                  in_month_discharge):
        """Funkcja odpowiada za obliczanie nieobecności

        @param current_absences_list - lista słowników [{dane nieobecności}, {}]
        @param hours_to_fill - float
        @param calculate_chor - bool
        @param sick_days_so_far - int
        @param paid_sick_leave_limit - int
        @param sick_leave_base - float
        @param sick_leave_over_90 - bool
        @param valid_sickness_insurance - bool
        @param value1 - float
        @param holidays_dict - słownik z danymi do obliczeń stawki urlopu

        return:
        value3 - float
        holidays_payment - float, wynagrodzenie za urlop
        total_absence_days - int, ilość dni nieobecności
        sick_days - int, ilość dni choroby
        sick_pay - float, wynagrodzenie chorobowe
        sick_benefit - float, zasiłek chorobowy
        """
        absences_list = []
        deduction_list = []
        absence_total_data = {  'holidays_days'     : 0,  # total number of days spent on holidays
                                'absence_days'      : 0,  # total number of days spent on absences of all \
    #                                                     types (except holidays and sick leaves, which are defined below)
                                'sick_days'         : 0,  # total number of days spent on sick leaves
                                'holidays_payment'  : 0,  # total amount paid for the holidays
                                'sick_benefit'      : 0,  # total sick benefit
                                'sick_pay'          : 0,  # total sick pay
                              }
        hours_sum = 0
        sick_leave_data = {}
        sick_pay_type = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_pay')[1]
        sick_benefit_type = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_benefit')[1]
        '''Iterating through absences_list'''
        if calculate_chor:
            valid_sickness_insurance = True
        for absence in current_absences_list:
            if absence['settled'] == True:
                continue

            else:
                '''Stara metoda dodawania godzin została zakomentowana'''
                if absence['etat_data_id'] == work_time_period['etat_data_id']:
                    #     hours_sum += absence['hours']
                    name = False
                    days = absence['days']
                    if absence.get('type') in ['sick_leave','child_care']:
                        name = "Sick pay"
                        local_paid_sick_leave_limit = paid_sick_leave_limit
                        if absence.get('type') == 'child_care':
                            name = "Child care"
                            local_paid_sick_leave_limit = 0


                        '''Using the calculate_sick_leave method for each absence and adding the returned values into one, coherent dictionary
                        Checks (with the use of counter) if the calculations should be done for the previous month or the current one
                        '''

                        # Sprawdź czy mamy ciągłą nieobecność z zeszłego roku,
                        # jeżeli tak to licz dni chorobowego razem z zeszłym rokiem.
                        previous_year_sick_benefit = False
                        if absence['type'] == 'sick_leave':
                            previous_year = str(int(work_time_period['date_start'][:4])-1)

                            # Wyszukaj przerwy w zwolnieniu od 31 grudnia.
                            query = """SELECT id
                                       FROM hr2_employee_date AS hed
                                       WHERE employee_id = {employee_id}
                                         AND (day_type != 'absence'
                                              OR
                                                (SELECT id
                                                 FROM hr2_absence AS ha
                                                 WHERE hed.absence_id=ha.id
                                                   AND
                                                     (SELECT TYPE
                                                      FROM hr2_absence_type AS hat
                                                      WHERE hat.id=ha.holiday_status_id) != 'sick_leave') IS NOT NULL)
                                         AND hed.date <= '{last_absence_day}'
                                         AND hed.date >= '{last_day_prev_year}'"""
                            cr.execute(query.format(employee_id=holidays_dict['employee_id'],
                                                    last_absence_day=absence['date_to'],
                                                    last_day_prev_year=previous_year + '-12-31'))
                            if not cr.fetchall():
                                # Licz dni chorobowego razem z zeszłym rokiem.
                                prev_year_sick_leave_days = self.pool.get('hr2.employee.date').search(
                                        cr, uid, [('date', '>=', previous_year + '-01-01'),
                                                  ('date', '<=', absence['date_to']),
                                                  ('employee_id', '=', holidays_dict['employee_id']),
                                                  ('absence_id.holiday_status_id.type', '=', 'sick_leave')])

                                if len(prev_year_sick_leave_days) > paid_sick_leave_limit:
                                    previous_year_sick_benefit = True

                        # Oblicz dane nieobecności.
                        sick_leave_data = self.calculate_sick_leave(sick_leave_over_90,
                                                                    absence['paid_leave_rate'],
                                                                    local_paid_sick_leave_limit,
                                                                    sick_days_so_far,
                                                                    sick_leave_base,
                                                                    days,
                                                                    previous_year_sick_benefit)
                        if absence.get('type') == 'sick_leave':
                            sick_days_so_far += days
                        absence_total_data['sick_days'] += days
                        '''Adding a deduction every turn of the loop'''
                        # In deduction for sick_leaves,
                        # value is always "Days of sick_leave / 30"
                        to_deduct = value1 if full_month else work_time_period['base']
                        deduction_list.append({'value':lacan_round((absence['days']/30.0) * to_deduct, 2), 'days': days, 'date_from':absence['date_from'],
                                               'date_to':absence['date_to'], 'type_id':absence['type_id'], 'name': 'Proportional deduction', 'base':sick_leave_base})
                        if valid_sickness_insurance:
                            '''Adding the absence to the absences list'''
                            if sick_leave_data['P'] != 0:
                                absences_list.append({
                                    'value': sick_leave_data['sick_pay'],
                                    'days': sick_leave_data['P'],
                                    'date_from': absence['date_from'],
                                    'date_to': absence['date_to'],
                                    'type_id': sick_pay_type,
                                    'absence_id': absence['absence_id'],
                                    'name': name,
                                    'base': sick_leave_base,
                                    'wymaga_korekty': absence.get('wymaga_korekty', False),
                                    'kup': absence.get('kup', False),
                                })

                            if sick_leave_data['Z'] != 0:
                                czy_pracodawca_wyplaca_zasilki = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Czy pracodawca sam wyplaca zasilki z ubezp. spol.')
                                absences_list.append({
                                    'value': czy_pracodawca_wyplaca_zasilki and sick_leave_data['sick_benefit'] or 0.0,
                                    'days': sick_leave_data['Z'],
                                    'date_from': absence['date_from'],
                                    'date_to': absence['date_to'],
                                    'type_id': sick_benefit_type,
                                    'absence_id': absence['absence_id'],
                                    'name': name,
                                    'base': sick_leave_base,
                                    'wymaga_korekty': absence.get('wymaga_korekty', False),
                                    'kup': absence.get('kup', False),
                                })
                            absence_total_data['sick_benefit'] += sick_leave_data['sick_benefit']
                            absence_total_data['sick_pay'] += sick_leave_data['sick_pay']
                        
                    elif absence['type'] == 'holidays':
                        hours_sum += absence['hours']
                        absence_payment = self.calculate_holidays(cr,
                                                                  uid,
                                                                  work_time_period['value1'],
                                                                  absence['hours'],
                                                                  hours_to_fill,
                                                                  holidays_dict)
                        absence_total_data['holidays_payment'] += absence_payment
                        '''Adding data for return'''
                        name = 'Holidays'

                        '''Adding the absence to the absences list'''
                        #TO DO Dodać procent, jakim m być liczone wynagrodzenie

                        if absence.get('paid_leave_rate') > 0.0:
                            absences_list.append({
                                'value': absence_payment,
                                'days': days,
                                'date_from': absence['date_from'],
                                'date_to':absence['date_to'],
                                'type_id': absence['type_id'],
                                'absence_id': absence['absence_id'],
                                'name': name,
                                'kup': absence.get('kup', False),
                            })
                    
                        '''Adding the absence to the deduction list (to show what has been deducted from the value3
                        and to absences, so that i.e. holidays_payment may be passed on to Calculate_Salary_PL'''
                        deduction_list.append({'value':lacan_round((absence['hours']/hours_to_fill) * value1, 2), 'days': days, 'date_from':absence['date_from'],
                                               'date_to':absence['date_to'], 'type_id':absence['type_id'],'name': name})

                    # Przy paid_leave pomniejszam godziny do przepracowania
                    # i godziny przepracowane o tę samą liczbę
                    elif absence['type'] == 'paid_leave':
                        absence_payment = self.calculate_holidays(cr,
                                                                  uid,
                                                                  work_time_period['value1'],
                                                                  absence['hours'],
                                                                  hours_to_fill,
                                                                  holidays_dict)

                        absences_list.append({'value':absence_payment, 'days': days, 'date_from':absence['date_from'],
                                                'hours': absence['hours'], 'date_to':absence['date_to'], 'type_id': absence['type_id'],'name': name, 'kup':absence.get('kup', False)})

        # Oblicz stosunek dni chorobowego do dni przepracowanych.
        if sum([a['hours'] for a in current_absences_list if a['type'] == 'sick_leave']) >= hours_to_fill:
            # Jeżeli pracownik chorował cały miesiąc utwórz zbiorcze pomniejszenie i ustaw wypłątę = 0.
            sick_days_ratio = 1
            deduction_list = [{'value': value1, 'name': 'Proportional deduction', 'base': sick_leave_base}]
        else:
            sick_days_ratio = absence_total_data['sick_days'] / 30.0
        other_leaves_ratio = hours_sum / hours_to_fill

        # Jeśli pracownik chorował przez 30 dni, nawet w miesiącu z 31 dniami, daj 0 za czas przepracowany.
        if sick_days_ratio >= 1:
            value3 = 0
        elif in_month_discharge:
            work_part = (hours_to_fill - work_time_period['hours']) / hours_to_fill
            value3 = value1 - lacan_round(work_part * value1, 2)
        else:
            value3 = value1 - lacan_round((sick_days_ratio + other_leaves_ratio) * value1, 2) #Pomniejszenie

        '''Joining data for return into one dictionary'''
        return_dict = {
                'absences_list':absences_list,
                'deduction_list': deduction_list,
                'value3':value3,
                'holidays_payment':absence_total_data['holidays_payment'],
                'sick_pay':absence_total_data['sick_pay'],
                'sick_benefit':absence_total_data['sick_benefit'],

               }
        # return_dict = custom_append_dict(sick_leave_data, return_dict) #Dane chorobowe wprowadzam bezpośrednio do return_dict
        return return_dict


    def calculate_holidays(self,
                           cr,
                           uid,
                           base_salary,
                           hours,
                           hours_to_fill,
                           holidays_dict):
        '''Funkcja odpowiada obliczeniom w grupie "nieobecnosci/chorobowe
        na diagramie procesów podproces urlop
        @params base_salary - float
        @params hours - int
        @params hours_to_fill - int
        @params holidays_dict - słownik danych potrzebnych do obliczeń
        @return: float, wynagrodzenie za urlop
        '''
        
        # sprawdź czy w okresie, dla którego liczymy (3 m-ce lub 12 m-cy) występują w payslipach dodatki brutto
        addition_line_line_values = [] # brutto nienależne za czas nieobecności (obiekt hr2.payslip.line.line)
        addition_line_values = [] # brutto nienależne za czas nieobecności (obiekt hr2.payslip.line)
        
        date1 = date(*map(int, holidays_dict['first_day'].split("-")))
        
        for i in range(0,holidays_dict['liczba_miesiecy_do_wyliczenia_podstawy_urlopu']):
            
            date2 = str(date1 + relativedelta(months=i))
            
            month = int(date2[5:7])
            year = int(date2[:4])
            
            payslip_line_ids = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id.employee_id','=',holidays_dict['employee_id']),
                                                                             ('register_id.register_month','=',month),
                                                                             ('register_id.register_year','=',year)])
            
            sql_query_add_line_line = "SELECT pll.value FROM hr2_payslip_line pl, hr2_payslip_line_line pll, hr2_salary_addition_type add \
                                WHERE pl.id=pll.payslip_line_id \
                                AND add.id=pl.type_id \
                                AND pll.type='addition' \
                                AND pl.id IN {payslip_line_ids}"
            
            cr.execute(sql_query_add_line_line.format(payslip_line_ids=lacan_tools.ids_for_execute(payslip_line_ids)))
            addition_line_line_values += [payslip_line_id[0] for payslip_line_id in cr.fetchall()]
            
            sql_query_add_line = "SELECT value \
                                    FROM hr2_payslip_line \
                                    WHERE id IN {payslip_line_ids} \
                                    AND addition_type IN \
                                    (SELECT id FROM hr2_salary_addition_type WHERE application IN ('brutto','brutto_importowane') \
                                                                                    AND NOT nalezny_za_okres_nieobecnosci)"
            
            cr.execute(sql_query_add_line.format(payslip_line_ids=lacan_tools.ids_for_execute(payslip_line_ids)))
            addition_line_values += [payslip_line_id[0] for payslip_line_id in cr.fetchall()]
            
        per_hour_sum = float(base_salary) / hours_to_fill
        
        # wykonaj obliczenia jeśli są dodatki brutto
        if addition_line_values or addition_line_line_values:
            
            addition_line_values = sum(addition_line_values)
            addition_line_line_values = sum(addition_line_line_values)
        
        
            hours_to_fill_holidays = self.work_time_hours(cr, uid, holidays_dict['employee_id'], holidays_dict['post_sign_date'],
                                                     holidays_dict['first_day'], holidays_dict['last_day'], ['multiple','working', 'absence'])
            
            hours_for_holidays = self.work_time_hours(cr, uid, holidays_dict['employee_id'], holidays_dict['post_sign_date'], holidays_dict['first_day'],
                                                       holidays_dict['last_day'], ['multiple','working'], search_type='filled')
            
            per_hour_sum += addition_line_values / hours_to_fill_holidays # dodatki brutto należne za czas nieobecności / total godzin w okresie (hours_to_fill_holidays)
            
            per_hour_sum += addition_line_line_values / hours_for_holidays # dodatki brutto nienależne za czas nieobecności / ilość godzin przepracowanych w okresie (hours_for_holidays)

        return lacan_round(per_hour_sum*(hours), 2)


    def calculate_sick_leave(self,
                             sick_leave_over_90,
                             paid_leave_rate,
                             paid_sick_leave_limit,
                             sick_days_so_far,
                             sick_leave_base,
                             days,
                             previous_year_sick_benefit):
        """funkcja odpowiada za obliczenia zwolnien chorobowych w aktualnym miesiacu

        @param sick_leave_over_90 - bool
        @param paid_leave_rate - float
        @param paid_sick_leave_limit - int
        @param sick_days_so_far - int
        @param sick_leave_base - float
        @param days - int
        @param previous_year_sick_benefit - bool

        return:
        sick_days - int, ilość dni choroby
        sick_pay - float, wynagrodzenie chorobowe
        sick_benefit - float, zasiłek chorobowy
        """

        return_data = {
                       'sick_pay': 0,
                       'sick_benefit':0
                       }

        if sick_leave_over_90 == True:
            return_data['korekta_reczna'] = True

            return return_data
        else:
            return_data['korekta_reczna'] = False

            '''Computing which days should be paid by the employer and which should not'''
            sick_days_available = paid_sick_leave_limit - sick_days_so_far
            if sick_days_available >= days and not previous_year_sick_benefit:
                P = days
                Z = 0
            else:
                if 0 < sick_days_available and not previous_year_sick_benefit:
                    P = float(sick_days_available)
                    Z = float(days - sick_days_available)
                else:
                    P = 0
                    Z = days

            if P != 0:
                stawka_dzienna=sick_leave_base * paid_leave_rate/30 #Wcześniej zaokrąglane lacan_roundem do 2 miejsc po przecinku
                return_data['sick_pay'] = lacan_round(stawka_dzienna*P,2)
            else:
                return_data['sick_pay'] = 0
            if Z != 0:
                stawka_dzienna=sick_leave_base * paid_leave_rate/30 #Wcześniej zaokraglane lacan_roundem do 2 miejsc po przecinku
                return_data['sick_benefit'] = lacan_round(stawka_dzienna*Z,2)
            else:
                return_data['sick_benefit'] = 0
            return_data['P'] = P
            return_data['Z'] = Z
            return return_data
    '''END of the calculate elements block'''


    def compute_base_salary(self, cr, uid, post, register_vals, hours_to_fill, gross_salary, work_time_list, hours_work):
        '''Oblicza wynagrodzenie za czas przepracowany w oparciu o podane okresy.
        UWAGA: Funkcja dodaje tu do podstawy dodatki nienależne za czas choroby.
        '''
        etat_vals = self.pool.get('hr2.etat').read(cr,uid,post,['employee_id', 'sign_date', 'discharge_date'])

        in_month_discharge = False
        if etat_vals['discharge_date']:
            discharge = datetime.strptime(etat_vals['discharge_date'], tools.DEFAULT_SERVER_DATE_FORMAT).date()
            last_day = self.last_day_of_month(register_vals['register_year'], int(register_vals['register_month']))
            first_day = date(register_vals['register_year'], int(register_vals['register_month']), 1)
            if first_day <= discharge < last_day:
                in_month_discharge = True

        if hours_work['per_hour']:
            for work_time in work_time_list:
                work_time['base'] = work_time['base'] * (hours_to_fill * hours_work['work_time'])

        if register_vals['register_month'] in range(1,10):
            register_vals['register_month'] = '0'+str(register_vals['register_month'])
        addition_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_addition')[1]
        new_work_time_list = []

        annex_in_current_month = False
        for work_time_check in work_time_list:
            if work_time_check['current_month'] == True:
                annex_in_current_month=True

        value1 = 0
        addition_dict_list = []
        '''Computing value1 from every work_time_list item and adding it together'''
        addition_lines = []
        if annex_in_current_month:
            for work_time in work_time_list:
                new_work_time = work_time
                new_work_time['base_without_additions'] = work_time['base']
                new_work_time['base_without_additions_scaled'] = lacan_round(((work_time['working_hours']/hours_to_fill)*(work_time['base'])),2)
                addition_lines = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id.employee_id','=',etat_vals['employee_id'][0]),
                                                                                    ('type_id','=',addition_type_id),
                                                                                    ('date_start','=',work_time['date_start']),
                                                                                    ('date_stop','=',work_time['date_stop']),
                                                                                    ('addition_id.addition_type_id.nalezny_za_okres_nieobecnosci','=',False),
                                                                                    ('addition_id.addition_type_id.application','!=','ekwiwalent')])

                addition_dict_list, addition_sum = self.create_addition_data(cr, uid, addition_lines, work_time['etat_data_id'])

                new_work_time['value1'] = lacan_round(((work_time['working_hours']/hours_to_fill)*(work_time['base']+addition_sum)),2)
                value1 += lacan_round(((work_time['working_hours']/hours_to_fill)*(work_time['base']+addition_sum)),2)
                new_work_time_list.append(new_work_time)

        else:
            value1 = gross_salary
            if len(work_time_list) == 1:
                new_work_time = work_time_list[0]
                new_work_time['value1'] = value1
                new_work_time_list.append(new_work_time)
                new_work_time['base_without_additions'] = value1
                new_work_time['base_without_additions_scaled'] = lacan_round(((work_time_list[0]['working_hours']/hours_to_fill)*(work_time_list[0]['base'])),2)
                addition_lines = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id.employee_id','=',etat_vals['employee_id'][0]),
                                                                                    ('type_id','=',addition_type_id),
                                                                                    ('date_start','=',work_time_list[0]['date_start']),
                                                                                    ('date_stop','=',work_time_list[0]['date_stop']),
                                                                                    ('addition_id.addition_type_id.nalezny_za_okres_nieobecnosci','=',False),
                                                                                    ('addition_id.addition_type_id.application','!=','ekwiwalent')])

                addition_dict_list, addition_sum = self.create_addition_data(cr, uid, addition_lines, work_time_list[0]['etat_data_id'])

                new_work_time['value1'] = lacan_round(((work_time_list[0]['working_hours']/hours_to_fill)*(work_time_list[0]['base']+addition_sum)),2)
                value1 += lacan_round(((work_time_list[0]['working_hours']/hours_to_fill)*(work_time_list[0]['base']+addition_sum)),2)
        if addition_lines:
            self.pool.get('hr2.payslip.line').unlink(cr,uid,addition_lines)
        return {'value1':value1,
                'work_time_list':new_work_time_list,
                'addition_dict_list':addition_dict_list,
                'in_month_discharge': in_month_discharge,
                }


    def generate_periods(self, cr, uid, post, register_vals, context=None):
        '''
        Generates work_time periods divided by annexes.
        :param post: post_id
        :param register_vals: Values present in the hr2.payroll.register object
        :return: list of computed work_time periods
        '''
        etat_data_pool = self.pool.get('hr2.etat.data')
        etat_vals = self.pool.get('hr2.etat').read(cr,uid,post,['employee_id', 'sign_date', 'discharge_date'])

        if register_vals['register_month'] in range(1,10):
            register_vals['register_month'] = '0'+str(register_vals['register_month'])
        first_day_of_current_month = str(register_vals['register_year'])+'-'+str(register_vals['register_month'])+'-01'
        last_day_of_current_month = str(self.last_day_of_month(register_vals['register_year'], (int(register_vals['register_month']))))

        post_data_ids = etat_data_pool.search(cr, uid, [('etat_id', '=',post), ('date_from','>=',first_day_of_current_month),
                                                        ('date_from','<=',last_day_of_current_month)], order='date_from asc')

        hours_to_fill = self.work_time_hours(cr, uid, etat_vals['employee_id'][0], first_day_of_current_month,
                                                 first_day_of_current_month, last_day_of_current_month, ['multiple','working', 'absence'])

        discharge_date = etat_vals['discharge_date']

        work_time_list = []

        '''New block for periods'''
        '''Searching hr2.etat.data ids based on first day of the month'''
        first_etat_data = etat_data_pool.search(cr,uid,[('date_from','<=',first_day_of_current_month),
                                                        ('etat_id','=',post)], order='date_from desc', limit=1)

        '''Searching for hr2.etat.data ids based on the last day of the month'''
        last_etat_data = etat_data_pool.search(cr,uid,[('date_from','<=',last_day_of_current_month),
                                                        ('etat_id','=',post)], order='date_from desc', limit=1)

        '''If there is no change, using the selected etat_data to create work_time_list element'''
        if last_etat_data and first_etat_data == last_etat_data:
            if discharge_date and discharge_date < last_day_of_current_month:
                last_day_of_current_month = discharge_date
            last_etat_data_vals = self.pool.get('hr2.etat.data').read(cr, uid, last_etat_data[0], ['month_pay'])
            working_hours = self.work_time_hours(cr, uid, etat_vals['employee_id'][0], etat_vals['sign_date'],
                                                 first_day_of_current_month, last_day_of_current_month, ['multiple','working', 'absence'], context=context)

            if working_hours:
                work_time_list.append({'base':last_etat_data_vals['month_pay'], 'name':'Work time', 'working_hours':working_hours, 'etat_data_id':last_etat_data,
                               'date_start': first_day_of_current_month, 'date_stop': last_day_of_current_month, 'current_month':True, 'deduction_list': []})

            '''If there is a change, it means annexes have been added during the current month'''
        elif last_etat_data and post_data_ids:
            for post_data in post_data_ids:

                '''Gathering annexes from the current month and the newest annex from before the current month
                '''
                etat_data_data = etat_data_pool.read(cr, uid, post_data, ['date_from', 'month_pay'])
                prev_post_data_ids = etat_data_pool.search(cr, uid, [('etat_id', '=',post),
                                                                                          ('date_from','<',etat_data_data['date_from'])], order='date_from desc', limit=1)

                '''Adding a period for the beginning of the month (with the month_pay of the previous annex), if the first annex
                from the current month has been added after the first day of the month
                '''
                if post_data_ids.index(post_data) == 0 and etat_data_data['date_from'] > str(first_day_of_current_month) and prev_post_data_ids:
                    #Extracting one day from the limit_date, as the condition check is inclusive and should not include the date_from of the next post
                    first_limit_date = (datetime.strptime(etat_data_data['date_from'], '%Y-%m-%d') - (timedelta(days=1))).strftime('%Y-%m-%d')
                    prev_post_data = etat_data_pool.read(cr, uid, prev_post_data_ids[0], ['date_from', 'month_pay'])

                    working_hours = self.work_time_hours(cr, uid, etat_vals['employee_id'][0], etat_vals['sign_date'],
                                                         first_day_of_current_month, first_limit_date, ['multiple','working', 'absence'], context=context)

                    if working_hours > 0:
                        work_time_list.append({'base':prev_post_data['month_pay'], 'name':'Work time', 'working_hours':working_hours, 'etat_data_id':prev_post_data_ids[0],
                                       'date_start': first_day_of_current_month, 'date_stop': first_limit_date, 'current_month':True, 'deduction_list': []})

                '''
                Now dealing with the post from the current month
                Setting the limit date (end date) for the current post, which is
                   the day before the start of the next post'''
                if post_data_ids.index(post_data) == post_data_ids.index(post_data_ids[-1]):
                    limit_date = last_day_of_current_month
                else:
                    next_index = (post_data_ids.index(post_data))+1
                    limit_date = etat_data_pool.read(cr, uid, post_data_ids[next_index], ['date_from'])['date_from']
                    #Extracting one day from the limit_date, as the condition check is inclusive and should not include the date_from of the next post
                    limit_date = (datetime.strptime(limit_date, '%Y-%m-%d') - (timedelta(days=1))).strftime('%Y-%m-%d')

                '''Taking discharge date into consideration'''
                if discharge_date and limit_date > discharge_date:
                    limit_date = discharge_date

                working_hours = self.work_time_hours(cr, uid, etat_vals['employee_id'][0], etat_vals['sign_date'],
                                     etat_data_data['date_from'], limit_date, ['multiple','working', 'absence'], context=context)
                
                if working_hours:
                    work_time_list.append({'name':'Work time', 'base':etat_data_data['month_pay'], 'working_hours': working_hours, 'etat_data_id': post_data,
                               'date_start': etat_data_data['date_from'], 'date_stop': limit_date, 'current_month':True, 'deduction_list': []})


        return {
                'work_time_list': work_time_list,
                'hours_to_fill': hours_to_fill
                }

    def work_time_hours(self, cr, uid, employee_id, sign_date, date_from, date_to, day_type, search_type=None, context=None):
        working_hours = 0
        working_days_list = self.pool.get('hr2.employee.date').search(cr, uid, [('employee_id','=',employee_id), ('day_type','in',day_type),
                                                                    ('date', '>=', sign_date),('date','>=',date_from),('date', '<=', date_to)], context=context)
        working_hours = self.pool.get('hr2.employee.date').compute_working_hours(cr, uid, working_days_list, search_type=search_type, context=context)
        return working_hours


    def get_absences(self, cr, uid, work_time_list, employee_id, context=None):
        '''Fetches absences for specific work_time periods
        @param work_time_list: list of the work_time periods
        @param employee_id: id of the employee
        '''
        absences_list = []
        for work_time in work_time_list:
            absence_dict = {}
            generated_absences = self.pool.get('hr2.employee.date').generate_employee_absences(cr, uid, work_time['date_start'], work_time['date_stop'], employee_id, context=context)
            for absence in generated_absences:
                absence_dict = absence
                absence_dict['etat_data_id'] = work_time['etat_data_id']
                absences_list.append(absence_dict)

        return absences_list

    def compute_elements_contract(self, cr, uid,
                          gross_salary,                     #float - kwota brutto z umowy
                                  ):

        return_data = {}

        value1 = gross_salary

        return_data['base'] = value1
        return_data['contract_type'] = 'c'
        return_data['value'] = value1


        return return_data


    def update_post_additions (self, cr, uid, final_work_time_list, payslip_id):
        """ Metoda na podstawie listy rekordów w hr2.payslip.line szuka dodatków i sprawdza czy są należne
            za czas nieobecności czy nie. Jeżeli są to aktualizuje ich wartość na payslipie. Jeżeli nie są,
            to skaluje ich wartość tylko do czasu przepracowanego i aktualizuje ją na payslipie.
            @param work_line_ids: lista ID rekordów hr2.payslip.line,
            @param payslip_id: ID payslipu,
            @return: True. """
        for period in final_work_time_list:
            addition_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_addition')[1]
            payslip_line_additions_ids = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','=',addition_type_id)])
            payslip_line_additions = self.pool.get('hr2.payslip.line').browse(cr, uid, payslip_line_additions_ids)
            for addition_line in payslip_line_additions:
                # Second case, addition_type is not obligatory in manual additions, so if only base was settled should be wrote to line as value
                if not addition_line.addition_type or addition_line.addition_type.nalezny_za_okres_nieobecnosci:
                     if not addition_line.value:
                         self.pool.get('hr2.payslip.line').write(cr, uid, addition_line.id, {'value': addition_line.base})
                else:
                    addition_value = lacan_round(period['hours'] / period['working_hours'] * addition_line.base, 2)
                    self.pool.get('hr2.payslip.line').write(cr, uid, addition_line.id, {'value': addition_value})
        return True


    def wylicz_podstawe_chorobowego(self, cr, uid, register_vals, employee_id, context=None):
        '''Wylicza podstawę wynagrodzenia chorobowego
        @param register_vals: słownik z danymi listy płac (payroll_register)
        @param employee_id: id pracownika
        '''
        work_time_id    = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_work_time')[1]
        line_pool       = self.pool.get('hr2.payslip.line')
        post_pool       = self.pool.get('hr2.etat')
        reg_pool        = self.pool.get('hr2.payroll.register')
        payslip_pool    = self.pool.get('hr2.payslip')
        abs_pool = self.pool.get('hr2.absence')
        abs_type_pool = self.pool.get('hr2.absence.type')

        wymaga_korekty = False #If True, the user needs to enter some values individually
        podstawa = 0
        new_base = False #If false, there was no work_time format change
        merged_periods = []

        #Przygotowuję dane do obliczeń w różnych formatach (w zależności od potrzeb)
        year  = int(register_vals['register_year'])
        month = int(register_vals['register_month'])
        register_date = str(year)+'-'+str(month)+'-01'
        register_datetime = datetime.strptime(register_date, "%Y-%m-%d").date()

        #Wydzielam daty graniczne na [rok_temu] -> [teraz]
        etat_data = post_pool.search(cr,uid,[('employee_id','=',employee_id)], order='date_from desc')[-1]
        sign_date = post_pool.read(cr, uid, etat_data, [('sign_date')])['sign_date']
        sign_date = datetime.strptime(sign_date, "%Y-%m-%d").date()
        month_end = register_datetime.month
        year_end = register_datetime.year
        '''Start tymczasowo zakodowany jako data 12 miesięcy temu'''
        start_datetime = datetime.strptime(str(year_end-1)+"-"+str(month_end)+"-01", "%Y-%m-%d").date()
        end_datetime = datetime.strptime(str(year_end)+"-"+str(month_end)+"-01", "%Y-%m-%d").date()
        start_date = max(start_datetime, sign_date) #TODO Taking sign date, not first post date

        month_start = start_date.month
        year_start = start_date.year

        sick_leave_types_ids = []
        sick_leave_types =['hr2_payslip_line_type_sick_pay', 'hr2_payslip_line_type_sick_benefit', 'hr2_payslip_line_type_child_care']
        for leave_type in sick_leave_types:
            sick_leave_types_ids.append(self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', leave_type)[1])

        # Sprawdź czy liczenie nowej podstawy jest konieczne.
        sick_types = abs_type_pool.search(cr, uid, [('type', 'in', ['sick_leave', 'child_care'])], context=context)

        _year, _month = self.get_prev_month(year, month)    # Data końca poprzedniego miesiąca.
        end_abs_date = datetime.strftime(self.last_day_of_month(_year, _month), tools.DEFAULT_SERVER_DATE_FORMAT)
        for count in range(2):      # Data początku trzeciego miesiąca wstecz.
            _year, _month = self.get_prev_month(_year, _month)
        start_abs_date = datetime.strftime(date(_year, _month, 01), tools.DEFAULT_SERVER_DATE_FORMAT)

        # Jeżeli wśród ostatnich 3 miesięcy są zwolnienia - użyj starej podstawy. Jeżeli nie - wylicz nową.
        prev_abs_ids = abs_pool.search(cr, uid, ['&', '&', '|',
                                                 '&', ('date_from', '>=', start_abs_date), ('date_from', '<=', end_abs_date),
                                                 '&', ('date_to', '>=', start_abs_date), ('date_to', '<=', end_abs_date),
                                                 ('holiday_status_id', 'in', sick_types),
                                                 ('employee_id', '=', employee_id)], context=context)
        if prev_abs_ids:
            prev_abs_ids.reverse()
            prev_abs_data = abs_pool.read(cr, uid, prev_abs_ids, ['base'], context=context)
            for absence in prev_abs_data:
                if absence['base']:
                    base = absence['base']
                    return base, wymaga_korekty

        # Funkcja idzie dalej, czyli od końca poprzedniego zwolnienia upłynęły 3 miesiące.
        # Sprawdzam w etatach, czy zmienił się wymiar pracy w ciągu ostatnich 12 miesięcy
        wymiar_pracy_data = self.check_work_time_change(cr, uid, year, month, employee_id)

        # Pracownik miał zmieniony wymiar czasu, dlatego
        # weź wynagrodzenie ustalone dla nowego wymiaru czasu pracy
        if wymiar_pracy_data['wymiar_pracy_change']:#and post_data_ids - zakomentowane po podzieleniu na mniejsze funkcje
            new_base = wymiar_pracy_data['new_base']

            #Przy zmianie czasu pracy, należy też ustalić przeciętne
            # wynagrodzenie dla umów cywilnoprawnych z ostatnich 12 miesięcy


        # Jeśli od końca poprzedniego zwolnienia minęły 3 miesiące, a wymiar pracy się nie zmienił, sprawdzam:
        # Czy pracownik miał umowy cywilnoprawne z ubezpieczeniem chorobowym
        # między którymi przerwa nie przekraczała 30 dni lub był zatrudniony
        # (w tym samym wymiarze czasu pracy) przez co najmniej 12 miesięcy?

        else: #if not wymiar_pracy_change

            date_list = self.contract_post_periods(cr, uid, start_date, end_datetime, register_datetime, employee_id)

            #Searching for a 30 days long break
            if date_list: #If False, he didn't work at all
                date_list = sorted(date_list, key=lambda x: x[0], reverse=True)

                #Merging the date_list before checking it
                merged_periods = self.merge_dates(cr, uid, date_list)
                new_start_date = ''

                #Continuing the search for a 30 days long break after the merge
                period_index = 0
                period_len = len(merged_periods)

            #Looking for a break longer than 30 days in the merged periods. If there are no merged periods, this is his first month
            new_start_date = False
            start_date_check = False
            one_full_month = False
            if merged_periods:

                for period in merged_periods:
                    if period_len == 1 and ((end_datetime-datetime.strptime(period[1],'%Y-%m-%d').date()).days <= 1): #If he worked continuously                        
                        new_start_date = datetime.strptime(period[0], "%Y-%m-%d").date()
                        start_date_check = new_start_date
                        break
                    if period_index==(period_len-1):
                        start_date_check = datetime.strptime(period[0], "%Y-%m-%d").date()
                        break
                    if abs((datetime.strptime(merged_periods[period_index][0], "%Y-%m-%d").date()-datetime.strptime(merged_periods[period_index+1][1],"%Y-%m-%d").date()).days) > 30:
                        new_start_date = datetime.strptime(period[0], "%Y-%m-%d").date() #Odrzucam czas przed tą przerwą. Jeśli pętla tutaj nie wejdzie, brany jest cały rok.
                        start_date_check = new_start_date
                        break
                    period_index += 1

                #Datę startowa ustawiam na czas po przerwie
                if new_start_date:
                    month_start = new_start_date.month
                    year_start = new_start_date.year
                    if new_start_date.day > 1:
                        year_start,month_start = self.get_next_month(year_start, month_start)

                #Now properly checking the one full month
                if self.check_full_month(end_datetime, start_date_check):
                    one_full_month = True
                else:
                    one_full_month = False

                #If worked at least one month (or one year without gaps), use the below function with proper dates, depending on the case
            if one_full_month:
                podstawa = self.podstawa_chorobowego_dla_miesiecy(cr, uid, employee_id, month_start, year_start, month_end, year_end, sick_leave_types_ids, new_base=new_base, context=context)
                if not podstawa:
                    wymaga_korekty = True
            else:
                if merged_periods:
                #If he hadn't worked a single full month, computing the data
                #This works only if employee has one post at the time (as only one payslip is being looked for)
                #For multiple posts, month and year should be read from the payslip and then payslip_lines should be fetched based
                #on that data.
                    first_payslip_lines = line_pool.search(cr, uid, [('payslip_id.employee_id','=',employee_id),
                                                                    ('date_start','>=',str(new_start_date)),
                                                                    ('payslip_id.register_id.state','=','confirmed')], order='date_start asc')
                    if first_payslip_lines:
                        payslip_id = line_pool.read(cr, uid, first_payslip_lines[0], ['payslip_id'], context=context)['payslip_id'][0]
                        connected_lines = line_pool.search(cr, uid, [('payslip_id','=',payslip_id),
                                                                     ('type_id','=',work_time_id)], context=context)

                        register_id = payslip_pool.read(cr, uid, payslip_id, ['register_id'], context=context)['register_id'][0]
                        register_data = reg_pool.read(cr, uid, register_id, ['register_month', 'register_year'], context=context)
                        last_day_of_register_month = str(datetime.strptime(str(self.last_day_of_month(register_data['register_year'], register_data['register_month'])), '%Y-%m-%d').date())
                        first_day_of_register_month = str(datetime.strptime(str(register_data['register_year'])+'-'+str(register_data['register_month'])+'-01','%Y-%m-%d').date())
                        total_worked_value = 0
                        total_worked_hours = 0

                        for payslip_line in connected_lines:
                            payslip_line_data = line_pool.read(cr, uid, payslip_line,['value', 'hours'], context=context)
                            payslip_line_line_ids = self.pool.get('hr2.payslip.line.line').search(cr, uid, [('value', '>', 0),
                                                                                                            ('payslip_line_id','=',payslip_line_data['id']),
                                                                                                            ('payslip_line_id.type_id','=',work_time_id)],
                                                                                                            context=context)
                            hours = self.pool.get('hr2.payslip.line.line').read(cr, uid, payslip_line_line_ids[0], ['hours'], context=context)['hours']
                            total_worked_value += payslip_line_data['value']
                            total_worked_hours += hours

                        if total_worked_value and total_worked_hours:
                            hours_to_work = self.work_time_hours(cr, uid, employee_id, first_day_of_register_month, first_day_of_register_month, last_day_of_register_month, ['working','multiple','absence'], context=context)
                            scaled_value = total_worked_value / total_worked_hours * hours_to_work
                            #A teraz odejmuję składki
                            suma_skladek = self.suma_hipotetycznych_skladek_spolecznych(cr, uid, scaled_value, context=context)
                            final_value = scaled_value - suma_skladek
                            return final_value, wymaga_korekty


                else: #If there are no work_time payslips at all
                    podstawa = 0 #ZAŻĄDAJ KWOTY OD UŻYTKOWNIKA ZE WZGLĘDU NA BRAK JAKIEGOKOLWIEK WYNAGRODZENIA
                    wymaga_korekty = True
        # if not wymaga_korekty:
        #     przyrownaj_do_minimalnej = self.porownaj_z_placa_minimalna(cr, uid, podstawa, employee_id, month, year, context=None)
        return podstawa, wymaga_korekty


    def podstawa_chorobowego_dla_miesiecy(self, cr, uid, employee_id, month_start, year_start, month_end, year_end, sick_leave_types_ids, new_base=False, context=None):
        '''Wylicza podstawę chorobowego dla podanych miesięcy
        Wszystkie dane są intami'''
        payslip_pool    = self.pool.get('hr2.payslip')
        line_pool       = self.pool.get('hr2.payslip.line')
        contract_pool   = self.pool.get('hr2.contract')
        add_type_pool = self.pool.get('hr2.salary.addition.type')
        work_time_id    = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_work_time')[1]
        addition_type_id= self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_addition')[1]
        periodical_addition_ids = add_type_pool.search(cr, uid, [('okresowy', '=', True)], context=context)
        ignore_addition_ids = add_type_pool.search(cr, uid, [('wlicz_do_pdst_chor', '=', False)], context=context)
        if not ignore_addition_ids:
            raise osv.except_osv(_('Błąd!'),_('Brak zdefiniowanego typu dodatku Ekwiwalent nienależny za czas nieobecności\n Sprawdź czy nazwa się zgadza i czy jest poprawnie zdefiniowany'))

        rejecting = True #rejecting months, during which the employee was absent for more than half of the working days. If all months are rejecting because of this, the loop is repeated with "False" in this place
        finished = False #Is the averaging finished? This flag is needed in order to repeat the computation in the case of all months being rejected
        suma_wynagrodzenia = 0
        start_date_string = str(year_start)+'-'+str(month_start)+'-01'
        start_datetime = datetime.strptime(start_date_string, '%Y-%m-%d').date()

        #Checking if the employee has been working for 12 months
        no_of_months = 0
        # _year = year_end
        # _month = month_end

        while not finished:
            _year,_month=year_end,month_end

            while True:
                _year,_month=self.get_prev_month(_year,_month)
                _payslip_ids = payslip_pool.search(cr,uid,[('register_id.register_year','=',_year),
                                                        ('register_id.register_month','=',_month),
                                                        ('employee_id','=',employee_id),
                                                        ])
                end_string = str(_year)+'-'+str(_month)+'-01'
                end_datetime = datetime.strptime(end_string, '%Y-%m-%d').date()
                if not _payslip_ids or end_datetime < start_datetime:
                    #no more past payroll registers (payslips) for the employee
                    finished=True
                    break
                else:

                ####### we check here if there are any payslips with etats that have additions of types with application different than brutto
                      # if so we take base from etat data          
                    base_from_etat_data = []
                    for payslip_id in _payslip_ids:
                        etat_id = payslip_pool.read(cr, uid, payslip_id, ['etat_id'], context=context)['etat_id']
                        if etat_id:
                            etat_anex_ids = self.pool.get('hr2.etat.data').search(cr,uid, [('etat_id','=',etat_id[0]),('date_from','<',start_datetime)], order='date_from desc', limit=1, context=context)
                            etat_anex_ids += self.pool.get('hr2.etat.data').search(cr,uid, [('etat_id','=',etat_id[0]),('date_from','>=',start_datetime)], context=context)
                            etat_addition_sets = self.pool.get('hr2.etat.data').read(cr, uid, etat_anex_ids, ['dodatki'])
                            simplified_method = True
                            for anex_additions in etat_addition_sets:
                                addition_types = self.pool.get('hr2.salary.addition').read(cr, uid, anex_additions['dodatki'], ['addition_type_id'], context=context)
                                addition_types = [addition_type['addition_type_id'][0] for addition_type in addition_types]
                                addition_type_applications = add_type_pool.read(cr, uid, addition_types, ['application'], context=context)
                                addition_type_applications = [addition_type_application['application'] for addition_type_application in addition_type_applications]
                                if addition_type_applications.count('brutto') >= 0:
                                    simplified_method = False
                                    break
                            if simplified_method:
                                base_from_etat_data.append(payslip_id)

                ######HERE STARTS THE PERIODICAL ADDITION CODE#####
                    if rejecting == True: #Used, so that the periodical additions will add only once
                        for payslip_id in _payslip_ids:
                            if payslip_id not in base_from_etat_data: # if base is taken from etat data we don't add any additions to it
                                payslip_line_ids = line_pool.search(cr, uid, [('type_id','=', addition_type_id),
                                                                            ('payslip_id','=',payslip_id)], context=context)
                                for addition_line in payslip_line_ids:
                                    addition_line_data = self.pool.get('hr2.payslip.line').read(cr, uid, addition_line, ['addition_id','value'], context=context)
                                    addition_data = self.pool.get('hr2.salary.addition').read(cr, uid, addition_line_data['addition_id'][0], ['addition_type_id'], context=context)
                                    if addition_data['addition_type_id'][0] in periodical_addition_ids \
                                            and addition_data['addition_type_id'][0] not in ignore_addition_ids:
                                        # podstawa -= addition_line_data['value'] #Składnik odejmuję od wynagrodzenia
                                        addition_type_data = add_type_pool.read(cr, uid, addition_data['addition_type_id'][0], ['co_ile_powtarzac'], context=context)
                                        additions_per_year = 12/addition_type_data['co_ile_powtarzac'] # N
                                        etat_id = payslip_pool.read(cr, uid, payslip_id, ['etat_id'], context=context)['etat_id'][0]
                                        if etat_id:
                                            previous_additions = self.pool.get('hr2.payslip.line').search(cr, uid, [('addition_id', '=', addition_line_data['addition_id'][0]),
                                                                                                                ('payslip_id.employee_id','=',employee_id),
                                                                                                                ('payslip_id.etat_id','=',etat_id)],
                                                                                                                limit=additions_per_year, order='date_from desc',
                                                                                                                context=context) #Zbierz kwoty tego składnika wypłacone N razy
                                        else:
                                            contract_id = payslip_pool.read(cr, uid, payslip_id, ['cywilnoprawna_id'], context=context)['cywilnoprawna_id'][0]
                                            previous_additions = self.pool.get('hr2.payslip.line').search(cr, uid, [('addition_id', '=', addition_line_data['addition_id'][0]),
                                                                                                                ('payslip_id.employee_id','=',employee_id),
                                                                                                                ('payslip_id.cywilnoprawna_id','=',contract_id)],
                                                                                                                limit=additions_per_year, order='date_from desc',
                                                                                                                context=context)
                                            
                                        for addition in previous_additions:
                                            suma_wynagrodzenia += self.pool.get('hr2.payslip.line').read(cr, uid, addition, ['value'], context=context)['value']/12
                    #####HERE ENDS THE PERIODICAL ADDITION CODE####
                    date_start_list = []
                    date_stop_list = []
                    for payslip in _payslip_ids:

                        #Generuję datę początku i końca sprawdzanego miesiąca
                        date_start_list.append(str(datetime.strptime(str(_year)+"-"+str(_month)+"-01", "%Y-%m-%d").date()))
                        date_stop_list.append(str(datetime.strptime(str(self.last_day_of_month(_year, _month)), "%Y-%m-%d").date()))

                    _date_start = min(date_start_list)
                    _date_stop = max(date_stop_list)

                    #Sprawdzam, czy pracownik przepracował przynajmniej połowę miesiąca
                    _tot_hours_to_fill = self.work_time_hours(cr, uid, employee_id, _date_start,
                                             _date_start, _date_stop, ['multiple','working', 'absence'])
                    _tot_hours_worked =  self.work_time_hours(cr, uid, employee_id, _date_start,
                                            _date_start, _date_stop, ['multiple','working'], search_type='filled')
                    if ((_tot_hours_worked <= _tot_hours_to_fill/2.) and rejecting):
                        continue
                    else:
                        #this month is taken into average
                        no_of_months += 1
                        for payslip in _payslip_ids:
                            payslip_data = payslip_pool.read(cr, uid, payslip, ['etat_id','cywilnoprawna_id'], context=context)
                            _work_line_ids = line_pool.search(cr, uid,[('payslip_id','=',payslip),
                                                                      ('type_id','=',work_time_id)
                                                                    ])
                            if payslip_data['cywilnoprawna_id']: #If payslip's for a contract, checking if it includes proper insurance
                                if not contract_pool.read(cr, uid, payslip_data['cywilnoprawna_id'][0], ['calculate_chor'])['calculate_chor']:
                                    continue

                            suma_skladek_spolecznych=self.suma_skladek_spolecznych(cr, uid, payslip, context=context)

                            if new_base: #if wymiar_pracy_change -> take the base from the moment of changing work_time:
                                suma_hipotetycznych_skladek = self.suma_hipotetycznych_skladek_spolecznych(cr, uid, new_base, context=context)
                                suma_wynagrodzenia += (new_base-suma_hipotetycznych_skladek)
                            else:
                                # if etat and forbidden additions found in etat we take value from etat data    
                                if payslip_data['etat_id'] and payslip_data['id'] in base_from_etat_data:
                                    period_list = self.generate_periods(cr, uid, payslip_data['etat_id'][0], {'register_month': _month, 'register_year': _year}, context=None)
                                    for period in period_list['work_time_list']:
                                        suma_wynagrodzenia += period['base']
                                        suma_hipotetycznych_skladek = self.suma_hipotetycznych_skladek_spolecznych(cr, uid, period['base'], context=context)
                                        suma_wynagrodzenia -= suma_hipotetycznych_skladek
                                # else if etat we take values from payslip lines and scale it up
                                elif payslip_data['etat_id']:
                                    if _work_line_ids:
                                        suma_wynagrodzenia += self.przeskaluj_do_pelnego_miesiaca(cr, uid, _work_line_ids, employee_id, context=context)

                                # else if contract we don't scale
                                else:
                                    for work_line_id in _work_line_ids:
                                        # suma_wynagrodzenia += line_pool.read(cr, uid, work_line_id, ['value'])['value']
                                        wartosc_brutto_okres = line_pool.read(cr, uid, work_line_id, ['value'])['value'] #wziąć wartość dla work_line_id
                                        suma_wynagrodzenia += wartosc_brutto_okres-suma_skladek_spolecznych
                            #
                            # # Dodatki nienalezne za czas choroby
                            # # oblicz wklad identycznie, jak dla czasu przepracowanego, ale bez skalowania
                            # #

                            #WYKOMENTOWANE - przy skalowaniu do pełnego miesiąca, dodatki nienależne za czas choroby znajdują się już w wynagrodzeniu

                            # suma_dodatki_nienalezne = self.skladniki_okresowe_nienalezne(cr, uid, payslip, context=context)
                            # suma_skladnikow = 0 #Suma wszystkich składników, od których liczymy składki
                            # linie_skladnikow = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip),
                            #     ('type_id','in',[absence_id,addition_type_id,work_time_id])])
                            # for skladnik in linie_skladnikow:
                            #     suma_skladnikow += line_pool.read(cr, uid, skladnik, ['value'])['value'] #id było wcześniej work_line_id
                            # suma_wynagrodzenia += suma_dodatki_nienalezne-suma_skladek_spolecznych*suma_dodatki_nienalezne/suma_skladnikow
                        #


                        #DLA OKRESOWYCH liczę dokładnie tak samo, jak w dwóch poprzednich przypadkach (bez skalowania), ALE:
                        # nie odrzucam miesięcy, nie skaluję, dzielisz nie przez liczbę miesięcy z których licczysz, ale przez okresowość danego dodatku dla każdego dodatku (w każdej pętli)
        if no_of_months:
            return suma_wynagrodzenia/float(no_of_months)
        else:
            return suma_wynagrodzenia

    def uaktualnij_podstawe(self, cr, uid, absences, podstawa_chorobowego, context=None):
        """ Przypisuje podaną podstawę chorobowego do zwolnień z tego miesiąca podanych w liście nieobecności.
            @param absences: lista, lista nieobecności,
            @param podstawa_chorobowego: float, wysokość podstawy chorobowego,
            @return: True. """
        to_update = []
        for absence in absences:
            if absence['type'] in ['sick_leave', 'child_care']:
                to_update.append(absence['id'])

        with tools.context_scope(context, {'not_validate': True}):
            self.pool.get('hr2.absence').write(cr, uid, to_update, {'base': podstawa_chorobowego}, context=context)
        return True

    def suma_skladek_spolecznych(self, cr, uid, payslip_id, context=None):
        '''Wylicza sumę składek społecznych (emerytalnej i rentowej pracownika)
        @param payslip_id: payslip, dla którego dokonujemy obliczeń
        @return: suma składek'''
        skladki = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['emr_pracownik','rent_pracownik','chor_pracownik'], context=None)
        suma = (skladki['emr_pracownik'] or 0) + (skladki['rent_pracownik'] or 0) + (skladki['chor_pracownik'] or 0)
        return suma

    def porownaj_z_placa_minimalna(self, cr, uid, kwota, employee_id, month, year, context=None):
        pensja_minimalna = self.get_pensja_minimalna(cr,uid,employee_id,month,year,context=context)
        skladki_pensji_minimalnej = self.suma_hipotetycznych_skladek_spolecznych(cr, uid, pensja_minimalna, context=context)
        pomniejszona_pensja_minimalna = pensja_minimalna - skladki_pensji_minimalnej

        kwota = max(kwota, pomniejszona_pensja_minimalna) #Jeśli podstawa pomniejszona o składki jest mniejsza od kwoty minimalnej, zastępuję kwotą minimalną


        return kwota


    def suma_hipotetycznych_skladek_spolecznych(self, cr, uid, new_base, context=None):
        '''Wylicza sumę hipotetycznych składek społecznych w oparciu o podaną podstawę wynagrodzenia
        @param new_base: Podstawa, dla której mamy dokonać obliczeń
        @return: suma składek'''
        cfg_pool = self.pool.get('lacan.configuration')
        stawka_chor = cfg_pool.get_confvalue(cr, uid, 'Stawka Chorobowa', context=context)
        stawka_rent = cfg_pool.get_confvalue(cr, uid, 'Stawka Rentowa (Pracownik)', context=context)
        stawka_emr = cfg_pool.get_confvalue(cr, uid, 'Stawka Emerytalna (Pracownik)', context=context)

        suma = lacan_round(new_base*(stawka_chor+stawka_rent+stawka_emr),2)
        return suma

    def suma_brutto_skladnikow(self, cr, uid, payslip_id, context=None):
        '''Funkcja obliczająca sumę brutto składników dla danego payslipa'''
        line_pool = self.pool.get('hr2.payslip.line')
        work_time_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_work_time')[1]
        addition_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_addition')[1]
        _line_ids = []
        suma = 0
        _work_line_ids = line_pool.search(cr, uid,[('payslip_id','=',payslip_id),
                                                  ('type_id','=',work_time_id)
                                                ])
        _addition_line_ids = line_pool.search(cr, uid,[('payslip_id','=',payslip_id),
                                                  ('type_id','=',addition_id),
                                                    ('addition_id.addition_type_id.nalezny_za_okres_nieobecnosci','!=',True),
                                                ])
        for work_line in _work_line_ids:
            _line_ids.append(work_line)
        for addition_line in _addition_line_ids:
            _line_ids.append(addition_line)

        for line in _line_ids:
            suma += line_pool.read(cr, uid, line, ['value'], context=context)['value']
        return suma


    def skladniki_okresowe_nienalezne(self, cr, uid, payslip_id, context=None):
        '''Wylicza wartość dodatków nienależnych za czas choroby'''
        suma = 0
        line_pool = self.pool.get('hr2.payslip.line')
        addition_line_ids = line_pool.search(cr, uid, [('addition_id.addition_type_id.nalezny_za_okres_nieobecnosci', '!=',True),
                                                       ('payslip_id','=',payslip_id),
                                                       ('addition_id.addition_type_id.okresowy', '!=',True)
                                                       ])
        for addition in addition_line_ids:
            suma += line_pool.read(cr, uid, addition, ['value'])['value']
        return suma



    # def skladniki_okresowe_dla_miesiecy(self, cr, uid, employee_id, podstawa, month_start, year_start, month_end, year_end, context=None):
    #     '''Dodatek przypisany do aneksu - ta sama premia mogła
    #     być wypłacona przed aneksem, stąd zwykła podwyżka może zmienić działanie funkcji'''
    #     payslip_pool = self.pool.get('hr2.payslip')
    #     line_pool = self.pool.get('hr2.payslip.line')
    #     addition_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_addition')[1]
    #     total_additions = 0
    #     periodical_addition_ids = self.pool.get('hr2.salary.addition.type').search(cr, uid, [('okresowy','=',True)], context=context)
    #     finished = False
    #     while not finished:
    #         _year,_month=year_end,month_end
    #
    #         while True:
    #             _year,_month=self.get_prev_month(_year,_month)
    #             _payslip_ids = payslip_pool.search(cr,uid,[('register_id.register_year','=',_year),
    #                                                     ('register_id.register_month','=',_month),
    #                                                     ('employee_id','=',employee_id)
    #                                                     ])
    #             if _year < year_start and _month < month_start:
    #                 #no more past payroll registers (payslips) for the employee
    #                 finished=True
    #                 break
    #             payslip_line_ids = line_pool.search(cr, uid, [('type_id','=', addition_type_id),
    #                                                           ('payslip_id','in',_payslip_ids)], context=context)
    #
    #             for addition_line in payslip_line_ids:
    #                 addition_line_data = self.pool.get('hr2.payslip.line').read(cr, uid, addition_line, ['addition_id','value'], context=context)
    #                 addition_data = self.pool.get('hr2.salary.addition').read(cr, uid, addition_line_data['addition_id'], ['addition_type_id'], context=context)
    #                 if addition_data['addition_type_id'] in periodical_addition_ids:
    #                     # podstawa -= addition_line_data['value'] #Składnik odejmuję od wynagrodzenia
    #                     addition_type_data = self.pool.get('hr2.salary.addition').read(cr, uid, ['co_ile_powtarzac'], context=context)
    #                     addition_per_year = 12/addition_type_data['co_ile_powtarzac'] # N
    #                     previous_additions = self.pool.get('hr2.payslip.line').search(cr, uid, [('addition_id', '=', addition_line_data['addition_id']),
    #                                                                                             ('payslip_id.employee_id','=',employee_id)],
    #                                                                                             limit=additions_per_year, order='date_from desc',
    #                                                                                             context=context) #Zbierz kwoty tego składnika wypłacone N razy
    #                     for addition in previous_additions:
    #                         podstawa += self.pool.get('hr2.payslip.line').read(cr, uid, addition, ['value'], context=context)['value']/12
    #
    #     return podstawa

    def przeskaluj_do_pelnego_miesiaca(self, cr, uid, work_line_ids, employee_id, context=None):
        """ Metoda na podstawie linii payslipa skaluje wartość pracy pracownika do pełnego miesiąca (Gdy są nieobecności
            liczy wartość na zasadzie "gdyby pracował pełen miesiąc"). Użyawna do wyliczania elementów do obliczenia
            podstawy chorobowego.
            @param work_line_ids: lista ID rekordów hr2.payslip.line,
            @param employee_id: ID pracownika,
            @return: float, przeskalowana wartość pomniejszona o hipotetyczne składki. """
        line_pool = self.pool.get('hr2.payslip.line')
        etat_pool = self.pool.get('hr2.etat')
        register_pool = self.pool.get('hr2.payroll.register')
        value_scaled = 0

        sign_date = etat_pool.read(cr, uid,
                                   etat_pool.search(cr, uid, [('employee_id', '=', employee_id)], context=context)[0],
                                   ['sign_date'], context=context)['sign_date']
        sign_date = datetime.strptime(sign_date, tools.DEFAULT_SERVER_DATE_FORMAT).date()

        # Przeskaluj do pełnego miesiąca dodając potrącenia do wynagrodzenia za czas pracy.
        for work_line in line_pool.browse(cr, uid, work_line_ids, context=context):
            local_value_scaled = work_line.value
            worked_hours = 0
            for line in work_line.payslip_line_line_ids:
                if not line.type:
                    local_value_scaled += abs(line.value)
                elif line.type == 'work_time':
                    worked_hours += line.hours

            # Sprawdź czy pierwszy miesiąc pracy, jeżeli tak to przeskaluj na godzinach zamiast na pomniejszeniach.
            date_start = datetime.strptime(work_line['date_start'], tools.DEFAULT_SERVER_DATE_FORMAT).date()
            first_day = date(date_start.year, date_start.month, 1)
            if date_start.month == sign_date.month and date_start > first_day:
                last_day = register_pool.last_day_of_month(date_start.year, date_start.month)

                hours_to_fill = self.work_time_hours(cr, uid, employee_id, first_day, first_day, last_day,
                                                     ['multiple', 'working', 'absence'])
                local_value_scaled = work_line.value * hours_to_fill / worked_hours
            value_scaled += local_value_scaled
        value_scaled -= self.suma_hipotetycznych_skladek_spolecznych(cr, uid, value_scaled, context=context)

        return value_scaled

    def contract_post_periods(self, cr, uid, start_date, end_datetime, register_datetime, employee_id, values=False):
        '''Provides time periods for contracts and post.
        When parameter 'value' is True, returns average values for the contracts'''
        line_pool = self.pool.get('hr2.payslip.line')
        month_end = register_datetime.month
        year_end = register_datetime.year
        date_list = []
        value = 0
        insured_contract_ids = self.pool.get('hr2.contract').search(cr,uid, [('employee_id','=',employee_id),('calculate_chor','=',True),
                                                                            ('date_to','>=',start_date),('date_start','<',str(end_datetime))
                                                                             ]) #Make sure the contracts don't start later than previous month
        contract_objs = self.pool.get('hr2.contract').browse(cr, uid, insured_contract_ids)
        for contract in contract_objs:
            c_date_from = contract.date_start
            c_date_to = contract.date_to
            c_value = contract.month_pay
            value += c_value
            date_list.append((c_date_from, c_date_to))

        if values:
            return value
        #Going back in time month by month and adding limit dates of periods
        #Later, periods are being merged
        no_of_months = 0
        _year = year_end
        _month = month_end

        for i in range(12):
            if no_of_months >= 12:
                break
            _year, _month = self.get_prev_month(_year, _month)
            _payslip_line_ids = line_pool.search(cr, uid, [('payslip_id.register_id.register_month','=', _month),
                                                         ('payslip_id.register_id.register_year','=', _year),
                                                         ('payslip_id.register_id.state','in',['confirmed','closed']), #Only for confirmed payroll registers
                                                         ('payslip_id.employee_id','=',employee_id),])
                                                         # ('type_id','=',work_time_id)],)
            _line_obj = line_pool.browse(cr, uid, _payslip_line_ids)
            if _payslip_line_ids:
                for _line in _line_obj:
                    date_from = _line.date_start
                    date_to = _line.date_stop
                    date_list.append((date_from, date_to))
                no_of_months +=1
            # else:
            #     break #No more past payslips, which means the employee didn't work then
        return date_list

    def check_full_month(self, end_datetime, start_date_check):
        '''Checks if there is one full month between the dates'''
        if not start_date_check:
            raise osv.except_osv(_('Błąd!'),_('Proszę zatwierdzić poprzednią listę płac.'))
        start_month = start_date_check.month
        start_year = start_date_check.year
        if start_date_check.day > 1: #If this is not the first day of the month, this month is not full
            start_year,start_month = self.get_next_month(start_year,start_month)
        start_date = datetime.strptime(str(start_year)+'-'+str(start_month)+'-'+str(start_date_check.day), '%Y-%m-%d').date()

        one_full_month = False

        while start_date < end_datetime:
            checked_month = start_date.month
            checked_year = start_date.year
            first_day = datetime.strptime(str(checked_year)+'-'+str(checked_month)+'-01', '%Y-%m-%d').date()
            last_day = datetime.strptime(str(self.last_day_of_month(int(checked_year), int(checked_month))),'%Y-%m-%d').date()


            full_month_check_start, full_month_check_stop = self.czescwspolnadat(str(start_date),str(end_datetime), str(first_day), str(last_day))
            full_month_check_start = full_month_check_start.date()
            full_month_check_stop = full_month_check_stop.date()


            if (full_month_check_start,full_month_check_stop) == (first_day, last_day):
                one_full_month = True
                break
            else:
                start_date = self.get_next_month(start_year,start_month)
                start_date = datetime.strptime(str(start_date[0])+'-'+str(start_date[1])+'-01', '%Y-%m-%d').date()

        return one_full_month

    def check_work_time_change(self, cr, uid,  year, month, employee_id, context=None):
        '''
        Checks if the work time format has changed
        :param year: Current year
        :param month: Current month
        :param employee_id: Employee id for which the change is being checked
        :return: dictionary:
            'wymiar_pracy_change' - indicates wether work_time format has changed
            'wymiar_pracy' - shows what is the new work_time format
            'new_base' - base from the post data changing the work_time format
        '''

        post_data_pool = self.pool.get('hr2.etat.data')
        year_ago = year-1
        date_year_ago = str(datetime.strptime(str(year_ago)+'-'+str(month)+'-01', "%Y-%m-%d").date())
        old_post_data = post_data_pool.search(cr,uid,[('date_from','<',date_year_ago), #szukam na wypadek, gdyby aneks zaczął się przed podaną datą i wciąż był aktualny
                                              ('etat_id.employee_id','=',employee_id)], order='date_from desc', limit=1)

        post_data_ids = post_data_pool.search(cr,uid,[('date_from','>=',date_year_ago), #data from the last 12months
                                                            ('etat_id.employee_id','=',employee_id)], order='date_from desc')
        if old_post_data:
            post_data_ids.append(old_post_data[0])

        wymiar_pracy = False
        wymiar_pracy_change = False #Jeśli True, wymiar pracy został zmieniony
        new_base = 0

        for data in post_data_ids:
            wymiar_pracy_data = post_data_pool.read(cr,uid, data,['work_time_licz', 'work_time_mian', 'month_pay'], context=context)
            wymiar_pracy_licz = wymiar_pracy_data['work_time_licz']
            wymiar_pracy_mian = wymiar_pracy_data['work_time_mian']
            post_wymiar_pracy = float(wymiar_pracy_licz)/float(wymiar_pracy_mian)
            if wymiar_pracy:
                if wymiar_pracy == post_wymiar_pracy:
                    continue
                else:
                    wymiar_pracy_change = True
                    new_base = wymiar_pracy_data['month_pay']
                    break
            else:
                wymiar_pracy = post_wymiar_pracy
        return {
                'wymiar_pracy_change': wymiar_pracy_change,
                'wymiar_pracy': wymiar_pracy,
                'new_base': new_base
                }



    def get_prev_month(self,year,month,times=1):
        """year and month are ints """
        for i in range(times):
            res_month = month - 1
            res_year = year
            if res_month < 1 :
                res_month = 12
                res_year-=1
        return res_year,res_month

    def get_next_month(self,year,month,times=1):
        """year and month are ints """
        for i in range(times):
            res_month = month + 1
            res_year = year
            if res_month >= 13 :
                res_month = 1
                res_year+=1
        return res_year,res_month

    def merge_dates(self, cr, uid, date_list, firstiter=True):
        '''Merges the list of tuples of dates (date_start, date_stop) together into c packs.
        Packs may be separated by gaps
        The list is sorted from newest to oldest periods
        '''
        
        new_date_list = []
        if not date_list:
            return []
        if len(date_list) == 1:
            return date_list
        elif len(date_list) > 1:
            if (False, False) in date_list: #Niektóre dodatki nie mają czasem dat granicznych. Kasuję puste zakresy.
                date_list.remove((False, False))
            period_length = len(date_list)
            period_index = -1
            current_merged_period = date_list[0]

            for date in date_list:
                period_index += 1
                if period_index==(period_length-1): #If the last element of the list, add the merged periods to the new list and end the loop
                    if new_date_list == [] or new_date_list[-1] != current_merged_period:
                        new_date_list.append(current_merged_period)
                    break

                current_date_start = datetime.strptime(current_merged_period[0],"%Y-%m-%d").date()
                current_date_end = datetime.strptime(current_merged_period[1], "%Y-%m-%d").date()
                prev_date_start = datetime.strptime(date_list[period_index+1][0],"%Y-%m-%d").date()
                prev_date_end = datetime.strptime(date_list[period_index+1][1], "%Y-%m-%d").date()
                shared_part = self.czescwspolnadat(str(prev_date_start), str(prev_date_end), str(current_date_start), str(current_date_end))

                if not shared_part == (False, False): #Means they have a shared part of days
                    new_start_date = min(current_date_start,prev_date_start)
                    new_end_date = max(current_date_end,prev_date_end)
                    current_merged_period = (str(new_start_date), str(new_end_date))
                    continue
                elif (current_date_start-prev_date_end).days <= 1: #The previous period ends just before the current one
                    new_start_date = prev_date_start
                    new_end_date = current_date_end
                    current_merged_period = (str(new_start_date), str(new_end_date))
                    continue
                else:
                    new_period = (str(prev_date_start),str(prev_date_end))  #If no shared parts, two periods are separate.
                                                                            # Taking the new period for computation and adding
                                                                            # the already achieved merged period to the new_date_list.
                    new_date_list.append(current_merged_period)
                    current_merged_period = new_period
                    continue
        
        if firstiter and len(new_date_list) > 1: #Checking if the date doesn't need further merging
            firstiter = False
            double_check = self.merge_dates(cr, uid, new_date_list, False)
        return new_date_list

    def czescwspolnadat(self, data11,data12,data21,data22):
        '''zwraca okres bedacy czescia wspolna dwoch okresow
        UWAGA! Jesli nie ma wspolnego okresu to zwroci Falsy
        UWAGA! Otrzymywane daty są stringami %Y-%m-%d
        @param data11: data 1 pierwszego okresu
        @param data11: data 2 pierwszego okresu
        @param data11: data 1 drugiego okresu
        @param data11: data 2 drugiego okresu
        @return: datastart,datastop : daty wspolnego okresu'''


        data11dt = datetime.strptime(data11, "%Y-%m-%d")
        data12dt = datetime.strptime(data12, "%Y-%m-%d")
        data21dt = datetime.strptime(data21, "%Y-%m-%d")
        data22dt = datetime.strptime(data22, "%Y-%m-%d")

        if (data11dt <= data21dt <= data22dt <= data12dt):
            return data21dt,data22dt
        elif (data11dt <= data21dt <= data12dt):
            return data21dt,data12dt
        elif (data11dt <= data22dt <= data12dt):
            return data11dt,data22dt
        elif (data21dt <= data11dt <= data12dt <= data22dt):
            return data11dt, data12dt
        else:
            return False,False

    def create_addition_data(self, cr, uid, addition_lines, etat_data_id, context=None):
        addition_sum = 0
        addition_dict_list = []
        for addition in addition_lines:
            addition_sum += self.pool.get('hr2.payslip.line').read(cr, uid, addition, ['base'])['base']
        for addition in addition_lines:
            addition_data = self.pool.get('hr2.payslip.line').read(cr, uid, addition, ['value', 'base', 'addition_type'])
            percent = (addition_data['base'])/float(addition_sum) #Uzyskuję procent dodatku względem sumy wszystkich dodatków nienależnych za czas choroby
            addition_dict_list.append({'value':addition_data['value'],
                                       'addition_percent':percent,
                                       'addition_type':addition_data['addition_type'][0],
                                       'etat_data_id':etat_data_id,
                                       })
        return addition_dict_list, addition_sum
        
    def count_overtime_hours(self, cr, uid, line_id, employee_id, periods, number, context=None):
        '''Funkcja porównuje czas przepracowany w okresie z czasem normatywnym,
           oblicza nadgodziny oraz wynagrodzenie zasadnicze
           @param line_id: linia payslipu, do której będziemy zapisywać nadgodziny
           @param employee_id: pracownik dla którego obliczamy powyższe wartości
           @param periods: okresy (w postaci listy) dla których wykonujemy obliczenia
           @param numer ostatniego obiektu w payslip_line_line
           @return: słownik {liczba nadgodzin, wynagrodzenie za nadgodziny} '''
               
        if context == None:
            context = {}
            
        if not isinstance(periods, list):
            periods = tuple(periods)
        else:
            periods.sort()
            periods = tuple(periods)
            
        try:
            conf_value = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Uproszczone naliczanie nadgodzin')
        except ValueError:
            pass
        
        if conf_value:

            #Obliczenie czasu normatywnego dla danego okresu
            norm_time = 0
            for period in periods[1:]:
                #Ilość dni pracujących w wybranym miesiącu
                cr.execute('''SELECT count(id) FROM hr2_employee_date 
                        WHERE employee_id = {} 
                        AND to_char(date,'YYYY-MM') = '{}'
                        AND day_type = 'working' '''.format(employee_id, period))     
                working_amount = cr.fetchone()
                if not working_amount:
                    raise osv.except_osv('Błąd', 'Brak danych w kalendarzu pracownika!')       
                working_amount = working_amount[0]   
                  
                #Część etatu w danym miesiącu
                cr.execute('''SELECT CAST(hed.work_time_licz AS float)/CAST(hed.work_time_mian AS float)
                            FROM hr2_etat_data hed LEFT JOIN hr2_etat he ON he.id = hed.etat_id 
                            WHERE he.employee_id = {} AND to_char(date_from, 'YYYY-MM') <= '{}'
                            LIMIT 1
                '''.format(employee_id, period))
                etat = cr.fetchone()
                if not etat:
                    raise osv.except_osv('Błąd!', 'Brak danych z umowy o pracę') 
                norm_time += 8 * working_amount * etat[0]
                
                #Dane z ostatniego miesiąca
                if period == periods[-1]:
                    norm_time_part = 8 * working_amount * etat[0]
            
            #Obliczenie rzeczywistego czasu pracy
            last_day = calendar.monthrange(int(periods[-1][:4]), int(periods[-1][5:]))[1]
            real_time = self.work_time_hours(cr, uid, employee_id, periods[1]+'-01',
                                              periods[1]+'-01', periods[-1]+'-'+str(last_day), ('working','-1'), context)
                               
            #Sprawdzanie czy są jakieś nadgodziny
            overtime = real_time - norm_time
            if overtime <= 0.00:
                return False
            else:
                #Obliczenie stawki godzinowej - base_per_hour
                cr.execute('''SELECT per_hour,month_pay
                            FROM hr2_etat_data hed LEFT JOIN hr2_etat he ON he.id = hed.etat_id 
                            WHERE he.employee_id = {} AND to_char(date_from, 'YYYY-MM') <= '{}'
                            LIMIT 1'''.format(employee_id, periods[-1]))
                last_month_etat_data = cr.fetchone()
                base_per_hour = last_month_etat_data[0] and last_month_etat_data[1] or last_month_etat_data[1]/norm_time_part
    
                #Ilość godzin przepracowana podczas świąt
                holiday_hours = self.work_time_hours(cr, uid, employee_id, periods[1]+'-01',
                                              periods[1]+'-01', periods[-1]+'-'+str(last_day), ('holiday','-1'), context)
                if holiday_hours > overtime:
                    amount = overtime * base_per_hour
                else:
                    amount = base_per_hour*(holiday_hours/2 + float(overtime)/2)
                           
                #Wpisywanie do hr2_payslip_line_line
                payslip_line_pool = self.pool.get('hr2.payslip.line')
                line_company_id = payslip_line_pool.browse(cr, uid, line_id).company_id.id
                addition_type_pool = self.pool.get('hr2.salary.addition.type')
                addition_type_id = addition_type_pool.search(cr, uid, [('company_id', '=', line_company_id),
                                                                       ('application', '=', 'brutto'),
                                                                       ('name', '=', 'Nadgodziny')])
                if not len(addition_type_id):
                    raise osv.except_osv('Błąd!',
                     'Dla firmy {} nie zdefiniowano dodatku typu nadgodziny'.format(payslip_line_pool.browse(cr, uid, line_id).company_id.name))
                    
                line_line_values = {
                                    'name': 'Nadgodziny',
                                    'type': 'addition',
                                    'number': number,
                                    'value': amount,
                                    'base': amount,
                                    'hours': overtime,
                                    'days': 0.00,
                                    'addition_percent': 0.00,
                                    'payslip_line_id': line_id,
                                    'company_id': line_company_id,
                                    'addition_type': addition_type_id[0]
      
                                    }    
                self.pool.get('hr2.payslip.line.line').create(cr, uid, line_line_values, context)
                
                res = overtime
                
        else:
            
            overtime_pool = self.pool.get('hr2.overtime')
            payslip_line_browse = self.pool.get('hr2.payslip.line').browse(cr, uid, line_id, context=context)
            
            # data początku okresu rozliczeniowego
            period_start = periods[0] + '-' + '01'
            date_start = datetime.strptime(period_start, tools.DEFAULT_SERVER_DATE_FORMAT)
            
            # data końca okresu rozliczeniowego
            period_end = periods[-1] + '-' + '01'
            date = datetime.strptime(period_end, tools.DEFAULT_SERVER_DATE_FORMAT)
            date_end = (date + relativedelta(months=1)) - relativedelta(seconds=1)
            date_end = str(date_end)
            
            overtimes = overtime_pool.lacan_search_read(cr, uid, [
                                                                ('state','=','approved'),
                                                                ('employee_id','=',employee_id),
                                                                ('date_to','<=',date_end)
                                                                ], 
                                                                ['hours'], context=context)
            
            sum_overtime = 0
            sum_overtime_holiday = 0
            
            # wyliczenie nadgodzin
            for overtime in overtimes:
                sum_overtime += overtime['hours']
    
            if sum_overtime <= 0:
                return False
            else:
                res = sum_overtime
                
            # wyliczenie wynagrodzenia za godzinę
            etat_data = payslip_line_browse.payslip_id.etat_id and payslip_line_browse.payslip_id.etat_id.etat_data[-1]
            per_hour = etat_data.per_hour
            
            if per_hour:
                base_per_hour = round(etat_data.month_pay,2)
            else:
                hours_to_fill = self.work_time_hours(cr, uid, employee_id, date_start, date_start,
                                       date_end[:10], ['multiple','working', 'absence'], search_type='filled', context=context)
                base_per_hour_without_precision = (etat_data.month_pay / hours_to_fill) if hours_to_fill else 0
                base_per_hour = round(base_per_hour_without_precision,2)
                
            # świąteczne nadgodziny
            holiday_overtimes_ids = self.pool.get('hr2.employee.date').lacan_search_read(cr, uid, [
                                                                            ('day_type','=','holiday'),
                                                                            ('employee_id','=',employee_id),
                                                                            ('date','>=',date),
                                                                            ('date','<=',date_end),
                                                                            ('overtime_id','!=',False)
                                                                            ], 
                                                                            ['overtime_id'], context=context)
            
            for holiday_overtime_id in holiday_overtimes_ids:
                 hours = overtime_pool.read(cr, uid, holiday_overtime_id['overtime_id'], ['hours'], context=context)['hours']
                 sum_overtime_holiday += hours
                 
            # amount to wynagrodzenie za nadgodziny
            if sum_overtime_holiday < sum_overtime:
                amount = sum_overtime_holiday * base_per_hour
            
            sum_overtime -= sum_overtime_holiday
            
            if sum_overtime > 0:
                amount += sum_overtime / 2 * base_per_hour
                
            addition_type_id = self.pool.get('hr2.salary.addition.type').search(cr, uid, [
                                                                              ('company_id','=',payslip_line_browse.company_id.id),
                                                                              ('application','=','brutto'),
                                                                              ('name','=','Nadgodziny')
                                                                              ], context=context)
            
            if not addition_type_id:
                raise osv.except_osv(_('Błąd !'), _('Dla firmy %s nie zdefiniowano dodatku Nadgodziny' % (payslip_line_browse.company_id.name)))
            
            values = {'name': 'Nadgodziny',
                      'payslip_line_id': line_id,
                      'base': amount,
                      'days': 0,
                      'hours': res,
                      'value': amount,
                      'addition_type': addition_type_id[0],
                      'addition_percent': 0,
                      'type': 'addition',
                      'number': number
                    }
                   
            self.pool.get('hr2.payslip.line.line').create(cr, uid, values, context=context)
            
            # ustawienie na rekordach hr2.overtime wziętych do liczenia nadgodzin stanu close
            for overtime in overtimes:
                cr.execute("UPDATE hr2_overtime SET state='closed' WHERE id = %s", ([overtime['id']]))
                        
        return {'overtime': res, 'amount': amount}
       
        
hr2_payroll_register()
