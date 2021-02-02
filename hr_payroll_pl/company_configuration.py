# -*- coding: utf-8 -*-
##############################################################################
#
# LACAN Technologies Sp. z o.o.
# Al. Jerzege Waszyngtona 146, 7 piętro
# 04-076 Warszawa
#
# Copyright (C) 2009-2014 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
#
##############################################################################

from osv import osv, fields

class company_configuration(osv.osv_memory):
    _inherit = 'company.configuration'

    _columns = {
                'new_company_short_name': fields.char("New company's short name", required=True)
                }

    def copy_accounting_configuration(self,cr,uid,ids,context=None):
        """Overrides original function to add short_name do the company create function"""

        if context:
            context = context.copy()
            context.update({'new_company_short_name': True})
        else:
            context = {'new_company_short_name': True}
        return super(company_configuration, self).copy_accounting_configuration(cr, uid, ids, context=context)

company_configuration()
