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
from datetime import datetime, timedelta

from osv import osv
from report import report_sxw
from tools import DEFAULT_SERVER_DATE_FORMAT
from tools.translate import _


class records_of_employment(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(records_of_employment, self).__init__(cr, uid, name, context=context)

        wiz_id = context.get('active_id')
        if not wiz_id:
            raise osv.except_osv(_('Error'),
                                 _('An error occurred! Close the form and try again.'))

        year_obj = self.pool.get('hr2.records.of.employment.wizard').browse(cr, uid, wiz_id, context=context).fiscal_year
        self.localcontext.update({
            'datas': self.gather_data(cr, uid, year_obj, context=context),
            'year': year_obj.code,
        })

    def gather_data(self, cr, uid, year_obj, context=None):
        address_pool = self.pool.get('res.partner.address')

        # Gather all etat data.
        date_start = year_obj.date_start
        date_stop = year_obj.date_stop
        query = """ SELECT employee_id, sign_date, discharge_date
                    FROM hr2_etat
                    WHERE (discharge_date IS NULL OR discharge_date >= '{}')
                      AND sign_date <= '{}'
                    ORDER BY employee_id, id"""
        cr.execute(query.format(date_start, date_stop))
        etat_data = cr.fetchall()

        # Group data.
        grouped_data = {}
        for line in etat_data:
            if line[0] not in grouped_data:
                grouped_data[line[0]] = [[line[1], line[2]]]
            else:
                grouped_data[line[0]].append([line[1], line[2]])

        datas = []
        for employee_id, data in grouped_data.items():
            start = data[0][0]
            end = data[-1][1]

            # Multiple lines in etat data = possible gaps.
            gaps = []
            if len(data) > 1:
                indexes = range(len(data))
                for index in indexes:
                    if index + 1 in indexes:
                        discharge = datetime.strptime(data[index][1], DEFAULT_SERVER_DATE_FORMAT)
                        sign = datetime.strptime(data[index + 1][0], DEFAULT_SERVER_DATE_FORMAT)
                        if discharge + timedelta(days=1) < sign:
                            after_discharge = (discharge + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                            before_sign = (sign - timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                            gaps.append(after_discharge + ' - ' + before_sign)

            # Get all other employee's data.
            query = """ SELECT hed.employee_name,
                               hed.second_name,
                               hed.surname,
                               he.father_name,
                               he.mother_name,
                               he.ssnid,
                               he.sinid,
                               hed.address_reg_id,
                               hed.address_home_id
                        FROM hr2_employee_data hed
                        LEFT JOIN hr_employee he ON he.id = hed.employee_id
                        WHERE hed.employee_id = {}
                          AND hed.date_from <= '{}'
                        ORDER BY hed.date_from DESC LIMIT 1"""
            cr.execute(query.format(employee_id, date_stop))
            employee_data = cr.dictfetchall()
            if not employee_data:
                employee = self.pool.get('hr.employee').read(cr, uid, employee_id, ['name'], context=context)['name']
                raise osv.except_osv(_('Error'), _('Employee {} has missing data for period before {}!').format(employee, date_stop))
            else:
                employee_data = employee_data[0]

            # Get address string.
            address_id = employee_data['address_home_id'] or employee_data['address_reg_id']
            address = address_pool.name_get(cr, uid, [address_id], context=context)
            address = address[0][1] if address else ''

            # Add line to main data variable.
            datas.append([
                ' '.join([x for x in [employee_data['employee_name'], employee_data['second_name'], employee_data['surname']] if x]),
                ', '.join([x for x in [employee_data['father_name'], employee_data['mother_name']] if x]),
                address,
                employee_data['ssnid'] or '',
                employee_data['sinid'] or '',
                start,
                end or '',
                'W okresie: ' + ', '.join(gaps) if gaps else '',
            ])

        # Sort by surname and name.
        datas.sort(key=lambda row: (row[0].split(' ')[-1], row[0].split(' ')[0]))
        datas = [[x[0]] + x[1] for x in enumerate(datas, start=1)]  # Add numeration.
        return datas

report_sxw.report_sxw('report.report_records_of_employment',
                      'hr2.records.of.employment.wizard',
                      'hr_payroll_pl/report/records_of_employment.mako',
                      parser=records_of_employment)
