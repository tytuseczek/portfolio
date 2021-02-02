# -*- coding: utf-8 -*-
##############################################################################
#
# LACAN Technologies Sp. z o.o.
# al. Jerzego Waszyngtona 146, 3 piętro
# 04-076 Warszawa
#
# Copyright (C) 2017 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
##############################################################################
from osv import fields, osv


class hr2_kwota_wolna_report(osv.osv):
    _name = "hr2.kwota.wolna.report"
    _auto = False
    _columns = {
        'year': fields.char('Rok'),
        'employee_id': fields.many2one('hr.employee', 'Pracownik'),
        'dochod': fields.float('Dochód od początku roku'),
        'podatek': fields.float('Zaliczka na podatek'),
        'kwota_wolna_payslip': fields.float('Odliczona kwota wolna'),
        'kwota_wolna_calc': fields.float('Wyliczona kwota wolna'),
        'diff': fields.float('Różnica'),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        # Odśwież dane w trakcie budowania widoku.
        cr.execute("""DROP TABLE IF EXISTS hr2_kwota_wolna_report;
                      CREATE TABLE hr2_kwota_wolna_report as (
                      SELECT employee_id AS id,
                             to_char(register_year, '9999') AS YEAR,
                             employee_id,
                             sum("kwota_US") AS podatek,
                             sum(dochod) AS dochod,
                             sum(zmniejszenie_zaliczki) AS kwota_wolna_payslip,
                             0.0 AS kwota_wolna_calc,
                             0.0 AS diff
                       FROM hr2_payslip ps
                       LEFT JOIN hr2_payroll_register pr ON pr.id = ps.register_id
                       WHERE state IN ('confirmed', 'closed')
                         AND register_year >= 2017
                       GROUP BY register_year, employee_id)""")
        self.calc_diff(cr, uid, context=context)
        return super(hr2_kwota_wolna_report, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

    def calc_diff(self, cr, uid, context=None):
        lines = self.read(cr, uid, self.search(cr, uid, [], context=context), ['year', 'dochod', 'podatek', 'kwota_wolna_payslip'], context=context)
        all_tax_free_thresholds = {year: self.pool.get('hr2.config.kwota.wolna').get_list(cr, uid, year, context=context) for year in set([x['year'] for x in lines])}

        for line in lines:
            tax_free_thresholds = all_tax_free_thresholds.get(line['year'])
            if not tax_free_thresholds:
                continue

            income = line['dochod']
            tax_free_threshold = ([tax_free_thresholds[tax_free_thresholds.index(x) - 1] for x in tax_free_thresholds if income < x[0]] or [tax_free_thresholds[-1]])[0]
            if not tax_free_threshold[2]:    # Jeżeli nie jest to próg przejściowy to zwróć pomniejszenie.
                amount = tax_free_threshold[1]
            else:
                # Jeżeli jest to próg przejściowy oblicz pomniejszenie.
                # [0] = kwota od której zaczyna się próg
                # [1] = kwota pomniejszenia
                index = tax_free_threshold.index(tax_free_threshold)
                prev = tax_free_threshold[index-1]
                next = tax_free_threshold[index+1]
                amount = prev[1] - ((prev[1] - next[1]) * (income - tax_free_threshold[0] - 1) / (next[0] - tax_free_threshold[0]))

            if amount > line['podatek']:
                diff = line['kwota_wolna_payslip'] - line['podatek']
            else:
                diff = line['kwota_wolna_payslip'] - amount
            cr.execute("""UPDATE hr2_kwota_wolna_report
                          SET kwota_wolna_calc = {}, diff = {}
                          WHERE id = {}""".format(amount, diff, line['id']))
        return True
