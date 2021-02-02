# -*- coding: utf-8 -*-
###############################################################################
#
# LACAN Technologies Sp. z o.o.
# al. Jerzego Waszyngtona 146, 3 piętro
# 04-076 Warszawa
#
# Copyright (C) 2016 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
###############################################################################

from osv import osv
from report import report_sxw
from tools.translate import _
from calendar import month_name


class annual_salaries_card(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(annual_salaries_card, self).__init__(cr, uid, name, context=context)

        wiz_id = context.get('active_id')
        if not wiz_id:
            raise osv.except_osv(_('Error'),
                                 _('An error occurred! Close the form and try again.'))

        wiz_obj = self.pool.get('hr2.annual.salaries.card.wizard').browse(cr, uid, wiz_id, context=context)
        year_obj = wiz_obj.fiscal_year
        if wiz_obj.employee_ids:
            employee_objs = wiz_obj.employee_ids
        else:
            employee_pool = self.pool.get('hr.employee')
            employee_ids = employee_pool.search(cr, uid, [], context=context)
            employee_objs = employee_pool.browse(cr, uid, employee_ids, context=context)

        self.localcontext.update({
            'datas': self.gather_datas(cr, uid, year_obj, employee_objs, context=context),
            'year': year_obj.code,
        })

    def gather_datas(self, cr, uid, year_obj, employee_objs, context=None):
        data_pool = self.pool.get('hr2.employee.data')
        employee_pool = self.pool.get('hr.employee')
        payment_pool = self.pool.get('hr2.payment.register')

        # Gather data for report.
        datas = []
        for employee in employee_objs:
            query = """ SELECT ROW_NUMBER() OVER (ORDER BY hpr.register_month),
                               hpr.register_month,
                               sum(hp.brutto),
                               sum(hp.koszty_uzyskania),
                               sum(hp.emr_pracownik),
                               sum(hp.rent_pracownik),
                               sum(hp.chor_pracownik),
                               sum(hp.dochod),
                               'dochod_od_pocz_roku',
                               sum("kwota_zaliczki_na_PIT"),
                               sum("kwota_NFZ"),
                               sum(hp.skladka_zdrowotna_odliczona),
                               sum("kwota_US")
                        FROM hr2_payslip hp
                        LEFT JOIN hr2_payroll_register hpr ON hpr.id = hp.register_id
                        WHERE hp.employee_id = {}
                          AND hpr.register_year = '{}'
                          AND hp.brutto > 0
                        GROUP BY hpr.register_month
                        ORDER BY hpr.register_month"""
            cr.execute(query.format(employee.id, year_obj.code))
            lines = [list(x) for x in cr.fetchall()]

            if lines:
                # Get employee's details.
                employee_data_id = data_pool.search(cr, uid, [('date_from', '<=', year_obj.date_stop),
                                                              ('employee_id', '=', employee.id)],
                                                    order='date_from desc', limit=1, context=context)
                if not employee_data_id:
                    employee = employee_pool.read(cr, uid, employee.id, ['name'], context=context)['name']
                    raise osv.except_osv(_('Error'), _('Employee {} has missing data for period before {}!').format(employee, year_obj.date_stop))
                employee_data = data_pool.read(cr, uid, employee_data_id[0], ['employee_name', 'second_name', 'surname'], context=context)
                employee_data.update(employee_pool.read(cr, uid, employee.id, ['ssnid', 'sinid'], context=context))
                employee_details = [
                    ' '.join([x for x in [employee_data['employee_name'], employee_data['second_name'], employee_data['surname']] if x]),
                    employee_data['sinid'] or '',
                    employee_data['ssnid'] or '',
                    ]

                # Sum lines.
                summary = [0 for x in range(len(lines[0]))]
                cincome = 0
                for line in lines:
                    # Calculate cumulative income.
                    cincome += line[7]
                    line[8] = cincome

                    for index in range(len(line)):
                        summary[index] += line[index]
                summary[8] = cincome
                del summary[:2]     # Line num, month num.

                # Get US advance payment date.
                for line in lines:
                    register_id = payment_pool.search(cr, uid, [('month_settled', '=', line[1]),
                                                                ('year_settled', '=', year_obj.code),
                                                                ('group', '=', 'US')], context=context)
                    if register_id:
                        payment_date = payment_pool.read(cr, uid, register_id[0], ['payment_date'], context=context)['payment_date']
                    else:
                        payment_date = False
                    line.append(payment_date or _('not payed'))

                # Change month numbers to words.
                lines = [[month_name[int(x)].capitalize() if line.index(x) == 1 else x for x in line] for line in lines]

                datas.append([employee_details, lines, summary])

        # Sort by employee
        datas = sorted(datas, key=lambda line: (line[0][0].split(' ')[-1], line[0][0].split(' ')[0]))
        return datas

report_sxw.report_sxw('report.report_annual_salaries_card',
                      'hr2.annual.salaries.card.wizard',
                      'hr_payroll_pl/report/annual_salaries_card.mako',
                      parser=annual_salaries_card)
