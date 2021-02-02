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
from tools import lacan_scripts

class civil_law_contract_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(civil_law_contract_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'kwotaslownie': lacan_scripts.kwotaslownie,
        })

report_sxw.report_sxw('report.civil.law.contract', 'hr2.payroll.register', 'core/hr/hr_payroll_pl/report/civil_law_contract_report.mako', parser=civil_law_contract_report, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: