# -*- coding: utf-8 -*-
##############################################################################
# 
# LACAN Technologies Sp. z o.o. 
# ul. Al.Waszyngtona 146
# 04-076 Warszawa
#
#
# Copyright (C) 2009-2014 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>). 
# All Rights Reserved 
# 
# 
##############################################################################

import time
from report import report_sxw
from lacan_tools import lacan_tools

class benefit_card(report_sxw.rml_parse):

    
    def __init__(self, cr, uid, name, context=None):
        
        context = context or {}
        super(benefit_card, self).__init__(cr, uid, name, context=context)
        
        self.localcontext.update({
            'get_data': self.get_data,
            'line_datas': self.line_datas,
            'find_absences': self.find_absences,
            'tax': self.find_tax,
            'format': self.pool.get('res.lang').format,
        })
    
    
    def find_tax(self, employee_id, month, year, data_str, context=None):  
        '''Metoda znajduje stawkę podatkową do pozycji 10
            @return aktualna dla wynagrodzenia stawka podatkowa
        '''
        
        context = context or {}
          
        compute_payslip_sum_wynik = self.pool.get('hr2.payroll.register').compute_payslip_sum_this_year(self.cr, self.uid, employee_id, month, year, context=context)
        PIT_income_since_start_of_year = compute_payslip_sum_wynik['suma_PIT']
        progi_conf = self.pool.get('lacan.configuration').get_confvalue(self.cr, self.uid, 'Konfiguracja progów podatkowych', data_str=data_str, context=context)
        
        tax_scale=[]
        
        for prog in progi_conf.prog_line_ids:
            tax_scale.append([prog.value_from, float(prog.percent)/100])
        
        for prog in tax_scale:
            if prog[0] > PIT_income_since_start_of_year:
                continue
            stawka = prog[1]
            
        return stawka
        
    def find_absences(self, employee_id, date_start, date_stop, context=None):
        '''Metoda znajdująca nieobecności, za które wypłacany jest zasiłek
            @return: słownik z danymi
        '''
    
        res = {}
        context = context or {}
        
        self.cr.execute('''SELECT hat.name,
                                hat.rate,
                                ha.date_from_days,
                                ha.date_to_days,
                                ha.base_month_start,
                                ha.base_year_start,
                                ha.base_month_stop,
                                ha.base_year_stop
                            FROM 
                                hr2_absence ha
                                LEFT JOIN hr2_absence_type hat ON hat.id=ha.holiday_status_id
                            WHERE 
                                ha.employee_id = %s
                            AND 
                                ha.date_from_days <= '%s'
                            AND 
                                '%s' <= ha.date_to_days'''%(employee_id, date_start, date_stop))
        
        res = self.cr.dictfetchall()
        
        return res    
    
        
    def line_datas(self, lines_ids, context=None):
        '''Metoda kompletująca dane do tabelki - daty początkowe zasiłku i końcowe
            @return: słownik z danymi
        '''
        
        res = {}
        context = context or {}
        
        self.cr.execute('''SELECT hpl.id, 
                                hpl.date_start, 
                                hpl.date_stop, 
                                hpl.number, 
                                hpl.base, 
                                hpl.value, 
                                hpl.number_of_days, 
                                hpr.name, 
                                hpr.date,
                                hplt.name "zasilek"
                            FROM 
                                hr2_payslip_line hpl
                                LEFT JOIN hr2_payslip hp ON hp.id=hpl.payslip_id
                                LEFT JOIN hr2_payroll_register hpr ON hpr.id=hp.register_id 
                                LEFT JOIN hr2_payslip_line_type hplt ON hplt.id=hpl.type_id
                            WHERE 
                                hpl.id IN {} 
                                ORDER BY date_start'''.format(lacan_tools.ids_for_execute(lines_ids)))
        
        res = self.cr.dictfetchall()
        
        return res
        
    
    def get_data(self, lines, context=None):
        '''Metoda zbierająca dane niezbędne do wygenerowania karty 
            @return: słownik z danymi
        '''
        
        datas = {}
        context = context or {}
        
        # wybranie id "najmłodszej" linii
        self.cr.execute("SELECT id FROM hr2_payslip_line WHERE id IN {} ORDER BY date_start DESC LIMIT 1"
                   .format(lacan_tools.ids_for_execute(lines)))
        
        line = self.cr.fetchone()[0]
        
        # zbudowanie słownika danych do karty (najbardziej aktualnych na rok, dla którego generujemy kartę)
        self.cr.execute('''SELECT hpl.id, 
                            he.sign_date, 
                            he.discharge_date, 
                            hc.date_start, 
                            hc.date_to, 
                            empl.sinid, 
                            empl.ssnid, 
                            empl.identification_id,
                            empl.passport_id,
                            empl.birthday, 
                            hed.employee_name, 
                            hed.surname,
                            hp.employee_id 
                        FROM 
                            hr2_payslip_line hpl 
                            LEFT JOIN hr2_payslip hp ON hp.id=hpl.payslip_id 
                            LEFT JOIN hr2_etat he ON he.id=hp.etat_id
                            LEFT JOIN hr2_contract hc ON hc.id=hp.cywilnoprawna_id
                            LEFT JOIN hr_employee empl ON empl.id=hp.employee_id
                            LEFT JOIN hr2_employee_data hed ON hed.employee_id=hp.employee_id
                        WHERE 
                            hpl.id={} 
                        AND 
                            hed.date_from <= hpl.date_stop 
                                ORDER BY hed.id DESC LIMIT 1''')
          
        datas = self.cr.dictfetchall()  
        
        if datas:    
        
            datas = datas [0]
            datas['employed_from'] = datas['sign_date'] if datas['sign_date'] != None else datas['start_date']
            
            if datas['discharge_date'] != None:
                datas['employed_to'] = datas['discharge_date'] 
            elif datas['date_to'] != None:
                datas['employed_to'] = datas['date_to'] 
            else:
                datas['employed_to'] = "----------"
                
            if datas['sinid'] == None:
                if datas['identification_id'] == None:
                    if datas['passport_id'] == None:
                        datas['sinid'] = ''
                    else:
                        datas['sinid'] = datas['passport_id']
                else:
                    datas['sinid'] = datas['identification_id']
            
            datas['lines'] = lines
        
        else:
            
            datas = {
                     'employee_id': '----------',
                     'lines': [],
                     'surname': '----------',
                     'employee_name': '----------',
                     'birthday': '----------',
                     'previous_insurance_end': '----------',
                     'ssnid': '----------',
                     'sinid': '----------',
                     'employed_from': '----------',
                     'employed_to': '----------'
                     }
            
        datas['previous_insurance_end'] = '----------' #TODO - missing field in system
            
        return datas
    
        
report_sxw.report_sxw('report.report.hr.benefit_card',
                      'hr.employee',
                      'addons/lacan_hr_holidays/report/benefit_card.mako',
                      parser=benefit_card)