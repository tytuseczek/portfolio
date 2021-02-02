# -*- coding: utf-8 -*-

import time
import calendar
import datetime
from tools.translate import _
from report import report_sxw
from lacan_tools.lacan_tools import custom_append_dict

class payslip_list(report_sxw.rml_parse):
    def payslip_data(self, payslip):
        dodatki = 0
        swiadczenia = 0
        chorobowe = 0
        zasilki = 0
        ekwiwalenty = 0
        potracenia = 0
        wynagrodzenie_praca = 0
        pomniejszenie_za_nieobecnosc = 0
        podstawa = 0
        for line in payslip.payslip_line_ids:
            if line.type_id.application == 'work_time':
                podstawa = line.base
                wynagrodzenie_praca += line.value
                for line_line in line.payslip_line_line_ids:
                    if line_line.name == 'Pomniejszenie':
                        pomniejszenie_za_nieobecnosc += line_line.value
            elif line.type_id.application == 'addition':
                if line.addition_type.application in ['brutto','brutto_importowane']:
                    dodatki += line.value
                elif line.addition_type.application == 'swiadczenie':
                    swiadczenia += line.value
                elif line.addition_type.application == 'ekwiwalent':
                    ekwiwalenty += line.value
            elif line.type_id.application == 'absence' or 'correction':
                if line.type_id.is_benefit:
                    zasilki += line.value
                else:
                    chorobowe += line.value
        for deduction in payslip.deductions_ids:
            potracenia += deduction.amount
        return {
            'podstawa': podstawa,
            'pomniejszenie_za_nieobecnosc': pomniejszenie_za_nieobecnosc,
            'dodatki': dodatki,
            'wynagrodzenie_praca': wynagrodzenie_praca,
            'chorobowe': chorobowe,
            'zasilki': zasilki,
            'swiadczenia': swiadczenia,
            'ekwiwalenty': ekwiwalenty,
            'potracenia': potracenia,
        }
    def sum_values(self, payslip_data_values, payslip_sum_values, payslip):
        if not payslip_sum_values:
            payslip_data_values['emr_pracownik'] = payslip.emr_pracownik
            payslip_data_values['rent_pracownik'] = payslip.rent_pracownik
            payslip_data_values['chor_pracownik'] = payslip.chor_pracownik
            payslip_data_values['koszty_uzyskania'] = payslip.koszty_uzyskania
            payslip_data_values['zmniejszenie_zaliczki'] = payslip.zmniejszenie_zaliczki
            payslip_data_values['skladka_zdrowotna_odliczona'] = payslip.skladka_zdrowotna_odliczona
            payslip_data_values['skladka_zdrowotna_od_netto'] = payslip.skladka_zdrowotna_od_netto
            payslip_data_values['kwota_zaliczki_na_PIT'] = payslip.kwota_US
            payslip_data_values['wyplata_przed_potraceniami'] = payslip.wyplata_przed_potraceniami
            payslip_data_values['do_wyplaty'] = payslip.do_wyplaty
            return payslip_data_values
        payslip_data_values = custom_append_dict(payslip_data_values, payslip_sum_values)
        payslip_data_values['emr_pracownik'] += payslip.emr_pracownik
        payslip_data_values['rent_pracownik'] += payslip.rent_pracownik
        payslip_data_values['chor_pracownik'] += payslip.chor_pracownik
        payslip_data_values['koszty_uzyskania'] += payslip.koszty_uzyskania
        payslip_data_values['zmniejszenie_zaliczki'] += payslip.zmniejszenie_zaliczki
        payslip_data_values['skladka_zdrowotna_odliczona'] += payslip.skladka_zdrowotna_odliczona
        payslip_data_values['skladka_zdrowotna_od_netto'] += payslip.skladka_zdrowotna_od_netto
        payslip_data_values['kwota_zaliczki_na_PIT'] += payslip.kwota_US
        payslip_data_values['wyplata_przed_potraceniami'] += payslip.wyplata_przed_potraceniami
        payslip_data_values['do_wyplaty'] += payslip.do_wyplaty
        return payslip_data_values
    
    
    def  get_employee_name(self, payslip):
        
        employee_datas = {}
        employee_data_pool = self.pool.get('hr2.employee.data')
        
        month = int(payslip.register_id.payment_month)
        year = int(payslip.register_id.payment_year)
        
        last_day = calendar.monthrange(year, month)[1]
        date_str = str(year)+"-"+str(month)+"-"+str(last_day)
        date = datetime.date(*map(int, date_str.split("-")))
        
        employee_data = employee_data_pool.search(self.cr, self.uid, [('employee_id','=',payslip.employee_id.id),('date_from','<=',date)], order='date_from')
        employee_data_id = employee_data and employee_data[-1]
        
        if employee_data_id:
            employee_datas.update(employee_data_pool.read(self.cr, self.uid, employee_data_id, ['employee_name','surname']))
        
        return employee_datas.get('employee_name','')+' '+employee_datas.get('surname','')
    
    
    def __init__(self, cr, uid, name, context=None):
        super(payslip_list, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'payslip_data': self.payslip_data,
            'sum_values': self.sum_values,
            'employee_name': self.get_employee_name,
        })

report_sxw.report_sxw('report.payslip.webkit.register', 'hr2.payslip', 'addons/hr_payroll_pl/report/payslip_list_report.mako', parser=payslip_list, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: