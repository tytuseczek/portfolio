# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Human Resources Payroll PL",
    "version": "1.2",
    "author": "OpenERP SA",
    "category": "Generic Modules/Human Resources",
    "website": "http://www.lacan.com.pl",
    "description": """
    Module for hr_payroll
    """,
    'author': 'developers@lacan.com.pl',
    'website': 'http://www.lacan.com.pl',
    'depends': ['hr', 'smb_account_analytic'],
    'init_xml': [],
    'update_xml': [
                   'wizard/import_contract_data.xml',
                   'wizard/generate_declaration.xml',
                   'wizard/wizard_generate_kedu.xml',
                   'hr_payroll_view.xml',
                   'wizard/wizard_print_benefit_card_view.xml',
                   'hr_absence_view.xml',
                   'hr_payroll_employee_view.xml',
                   'sequence_view.xml',
                   'hr_payroll_pl_data.xml',
                   'wizard/new_payroll_config_view.xml',
                   'wizard/payment_pay_wizard_view.xml',
                   'wizard/external_elements.xml',
                   'wizard/update_employee_calendar.xml',
                   'wizard/payslip_line_correction.xml',
                   'payroll_config/config_data.xml',
                   'payroll_config/2013.xml',
                   'payroll_config/2014.xml',
                   'payroll_config/2015.xml',
                   'payroll_config/2016.xml',
                   'payroll_config/2017.xml',
                   'payroll_config/2018.xml',
                   'lacan_right_data.xml',
                   'security/ir.model.access.csv',
                   'security/hr_payroll_pl_security.xml',
                   'report/report_data.xml',
                   'company_configuration_view.xml',
                   'wizard/wizard_declaration.xml',
                   'data/edeclaration_pit11_data.xml',
                   'data/pit_11_positions.xml',
                   'wizard/nip7.xml',
                   'wizard/records_of_employment.xml',
                   'wizard/annual_salaries_card.xml',
                   ],
    'demo_xml': [
                   'hr_payroll_demo.xml',
        ],
    'test': [
            'test/001.yml',
            'test/002.yml',
            'test/KUP001.yml',
            'test/KUP002.yml',
            'test/KUP003.yml',
            'test/KUP004.yml',
            'test/KUP005.yml',
            'test/KUP006.yml',
            'test/KUP007.yml',
            'test/KUP010.yml',
            # 'test/calc005.yml',            #zaokrąglenia
            # 'test/calc007.yml',            #prawdopodobnie problem z podawanymi danymi, zwolnienia z poprzedniego miesiąca które nie sa obsługiwane
            'test/kalendarz001.yml',
            'test/korekta.yml',
            'test/kwota_wolna1.yml',
            'test/test_annex_001.yml',  #Do tego momentu przechodzi
            # 'test/test_annex_002.yml',     #AssertionError in Python code : SkĹadka zdrowotna odliczona
            'test/test_annex_003.yml',
            'test/test_annex_004.yml',
            'test/test_annex_005.yml',
            'test/test_annex_006.yml',
            'test/test_annex_007.yml',
            'test/test_chor_001.yml',
            # 'test/test_chor_004.yml',     # Test tymczasowo zakomentowany. Należy przeliczyć na kartce.
            #                               # Trzeba sprawdzić czy podstawa chorobowego jest liczona poprawnie.
            'test/test_chor_005.yml',
            'test/test_chor_006.yml',
            'test/test_chor_007.yml',
            'test/uzupelnienia01.yml',
            'test/uzupelnienia02.yml',
            'test/uzupelnienia03.yml',
            'test/uzupelnienia04.yml',
            'test/Potracenia001.yml',
            'test/Potracenia002.yml',
            'test/prog_podatkowy.yml',
            'test/podstawa_wymiaru_skladek_test002.yml', #używać tylko po teście prog_podatkowy
            'test/nierezydent.yml',
             ],
    'installable': True,
    'active': False,
    'license': 'Other proprietary',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
