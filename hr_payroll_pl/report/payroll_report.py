# -*- coding: utf-8 -*-
##############################################################################
# 
# LACAN Technologies Sp. z o.o. 
# al. Jerzego Waszyngtona 146, 7 piętro
# 04-076 Warszawa 
# 
# Copyright (C) 2015-2016 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>). 
# All Rights Reserved 
# 
# 
##############################################################################

import time
from tools.translate import _
from report import report_sxw
from lacan_tools.lacan_tools import custom_append_dict

class payroll(report_sxw.rml_parse):
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
    def __init__(self, cr, uid, name, context=None):
        super(payroll, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'payslip_data': self.payslip_data,
            'sum_values': self.sum_values,
        })

report_sxw.report_sxw('report.payroll.webkit.register', 'hr2.payroll.register', 'core/hr/hr_payroll_pl/report/payroll_report.mako', parser=payroll, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: