# -*- coding: utf-8 -*-
##############################################################################
# 
# LACAN Technologies Sp. z o.o. 
# al. Jerzego Waszyngtona 146
# 04-076 Warszawa 
# 
# Copyright (C) 2014-2017 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>). 
# All Rights Reserved 
# 
# 
##############################################################################

from datetime import datetime, date, timedelta
import dateutil.relativedelta as relativedelta
import time
import re
import calendar

from osv import fields, osv
from osv import osv
from tools.translate import _
from lacan_tools.lacan_tools import lacan_round
from lacan_tools.lacan_tools import ids_for_execute
import tools
from lacan_tools import lacan_tools

'''Hardcoded values for executing the method'''
hardcoded_params = {}
hardcoded_params['umowa_cywilnoprawna_z_wlasnym_pracownikiem'] = False  #bool
hardcoded_params['czy_zwolnienie_nieprzerwanie_od_90_dni_kalendarzowych'] = False   #bool
hardcoded_params['czy_posiada_ubezpieczenie_chorobowe'] = True                      #bool

######Payslip, payslip_line type, payslip_line and payslip_line_line


class hr2_payslip(osv.osv):
    _name = "hr2.payslip"
    _description = "Payslip"
    _inherit = 'company.related.class'
    _columns =  {
              'employee_id': fields.many2one('hr.employee', 'Employee', required=True, ondelete='restrict'),
              'register_id': fields.many2one('hr2.payroll.register', 'Payroll register', required=True, ondelete='restrict'),
              'cywilnoprawna_id': fields.many2one('hr2.contract', 'Contract'),
              'etat_id': fields.many2one('hr2.etat', 'Umowa o pracę'),
              'payslip_line_ids': fields.one2many('hr2.payslip.line', 'payslip_id', 'Składnik wynagrodzenia'),
              'deductions_ids': fields.one2many('hr2.payslip.deduction', 'payslip_id', 'Potrącenia'),
              'brutto':fields.float('Brutto'),
              'chor_pracownik': fields.float('Składka chorobowa pracownika'),
              'emr_pracownik': fields.float('Składka emerytalna pracownika'),
              'rent_pracownik': fields.float('Składka rentowa pracownika'),
              'skladki_ZUS_pracownika': fields.float('ZUS pracownika'),
              'koszty_uzyskania': fields.float('Koszty uzyskania - naliczone'),
              'zmniejszenie_zaliczki': fields.float('Zmniejszenie zaliczki na PIT'),
              'skladka_zdrowotna_odliczona': fields.float('Składka zdrowotna odliczona'),
              'skladka_zdrowotna_od_netto': fields.float('Składka zdrowotna od netto'),
              'skladka_zdrowotna_pracownika': fields.float('Składka zdrowotna pracownika'),
              'kwota_NFZ': fields.float('Kwota NFZ'),
              'kwota_US': fields.float('Podatek do wpłaty'),
              'do_wyplaty': fields.float('Kwota do wypłaty'),
              'emr_pracodawca': fields.float('Składka emerytalna pracodawcy'),
              'rent_pracodawca': fields.float('Składka rentowa pracodawcy'),
              'wyp_pracodawca': fields.float('Składka wypadkowa pracodawcy'),
              'fp': fields.float('FP'),
              'fgsp': fields.float('FGŚP'),
              'kwota_zaliczki_na_PIT': fields.float('Kwota zaliczki na PIT'),
              'dochod': fields.float('Dochód'),
              'value3': fields.float('Value 3'),
              'koszty_uzyskania_autorskie': fields.float('Koszty uzyskania za prawa autorskie'),
              'wyplata_przed_potraceniami': fields.float('Wynagrodzenie netto'),
              }

    def _check_post_contract(self, cr, uid, ids, context=None):
        """Checks if the month value exceeds the allowed range
        @param ids: Register ID
        """
        payslip_list = self.browse(cr,uid,ids)
        for payslip in payslip_list:
            if not payslip.etat_id and not payslip.cywilnoprawna_id:
                raise osv.except_osv('Błąd!', 'Pasek listy płac musi mieć wypełnione pole etat lub umowa cywilno-prawna.')
        return True

    _constraints = [(_check_post_contract, '', ['']), ]

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for record in self.read(cr, uid, ids, ['employee_id', 'register_id'], context=context):
            if record['register_id']:
                if record['employee_id']:
                    name = record['register_id'][1] + ' ' + record['employee_id'][1]
                    res.append((record['id'], name))
        return res
    
    
    def unlink(self, cr, uid, ids, context=None):
        """ Metoda nadpisana aby wywołać unlinka na powiązanych rekordach z obiektu hr2.payslip.line.line
            oraz hr2.payment.register.line """
        pay_line_pool = self.pool.get('hr2.payment.register.line')
        res = False
         
        for payslip_id in ids:
            
            cr.execute("SELECT id FROM hr2_payslip_line_line WHERE payslip_line_id IN \
                        (SELECT id FROM hr2_payslip_line WHERE payslip_id = %s)",(payslip_id, ))
            
            lines = map(lambda x: x[0], cr.fetchall())
            self.pool.get('hr2.payslip.line.line').unlink(cr, uid, lines, context=context)
            
        pay_lines = pay_line_pool.search(cr, uid, [('payslip_id', 'in', ids)], context=context)
        pay_line_pool.unlink(cr, uid, pay_lines, context=context)
        return super(hr2_payslip, self).unlink(cr, uid, ids, context=context)


hr2_payslip()


class hr2_payslip_line_type(osv.osv):
    _name = "hr2.payslip.line.type"
    _description = "Payslip line type"
    _columns = {
                'name':fields.char('Name', translate=True, readonly=True),
                'application':fields.selection([('addition', 'Dodatek'), 
                                                ('work_time', 'Czas przepracowany'), 
                                                ('absence', 'Nieobecność'), 
                                                ('correction', 'Korekta za poprzedni miesiąc')],
                                               'Application', readonly=True),
                'is_benefit':fields.boolean('Czy linia jest zasiłkiem', readonly=True),
                'company_id' : fields.many2one('res.company', 'Company', readonly=True)
                }
    
    _defaults = { 'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c)

    }
hr2_payslip_line_type()


class hr2_payslip_line(osv.osv):
    _name = "hr2.payslip.line"
    _description = "Payslip Line"
    _inherit = 'company.related.class'
    _columns = {
                'payslip_id': fields.many2one('hr2.payslip', 'Payslip', required=True, ondelete='cascade'),
                'type_id': fields.many2one('hr2.payslip.line.type', 'Line type', required=True, ondelete='restrict'),
                'number': fields.integer('Number'),
                'base': fields.float('Base'),
                'number_of_days': fields.integer('Number of days'),
                'date_start': fields.date('Date start', required=True),
                'date_stop': fields.date('Date stop', required=True),
                'value': fields.float('Value'),
                'percent': fields.float('Percent'),
                'addition_id': fields.many2one('hr2.salary.addition', 'Dodatek'),
                'addition_type': fields.many2one('hr2.salary.addition.type', 'Typ dodatku'),
                'licz_KUP_jak_podstawa': fields.boolean('Licz KUP jak dla podstawy?'),
                'payslip_line_line_ids': fields.one2many('hr2.payslip.line.line', 'payslip_line_id', 'Wyliczenie składnika wynagrodzenia'),
                'wymaga_korekty': fields.boolean('Linia wymaga korekty'),
                'register_id': fields.many2one('hr2.payroll.register', 'Register id'), #pole potrzebne do domaina w liscie dodatkow
                'absence_id': fields.many2one('hr2.absence', 'Nieobecność'),
               }

    _defaults = {
                'wymaga_korekty': False,
                }

    def _check_date(self, cr, uid, ids, context=None):
        """Funkcja sprawdza czy data payslip line jest poprawna"""
        line_list = self.browse(cr,uid,ids)

        for line in line_list:
            date_start = line.date_start
            date_stop = line.date_stop
            line_application = line.type_id.application
            register_month = line.payslip_id.register_id.register_month
            register_year = line.payslip_id.register_id.register_year
            if date_start > date_stop:
                raise osv.except_osv('Błąd!', 'Data początku nie może być po dacie końca.')
            date_start_month = int(date_start.split("-")[1])
            date_stop_month = int(date_stop.split("-")[1])
            if ((date_start_month != register_month) | (date_stop_month != register_month)) & (line_application != 'correction'):
                raise osv.except_osv('Błąd!', 'Miesiąc linii nie zgadza się z miesiącem listy płac')
            date_start_year = int(date_start.split("-")[0])
            date_stop_year = int(date_stop.split("-")[0])
            if ((date_start_year != register_year) | (date_stop_year != register_year)) & (line_application != 'correction'):
                raise osv.except_osv('Błąd!', 'Rok linii nie zgadza się z rokiem listy płac')
        return True

    _constraints = [(_check_date, '', ['']), ]
    
    
    def is_add_type_invisible(self, cr, uid, type_id=None, context=None):
        '''Metoda dynamicznej domeny pokazująca pole Typ dodatku, jeśli Typ elemntu to Dodatek'''
        
        if not type_id:
            return True
        type_app = self.pool.get('hr2.payslip.line.type').read(cr, uid, type_id, ['application'], context=context)
        if type_app['application'] == 'addition':
            return False
        else:
            return True
        

    def on_change_addition (self, cr, uid, ids, addition_id):
        addition_type_id = self.pool.get('hr2.salary.addition').read(cr, uid, addition_id, ['addition_type_id'])['addition_type_id'][0]
        return {
                'value':{
                        'addition_type':addition_type_id
                        }
                }


    def on_change_correction_line(self, cr, uid, ids, base, value, type_id, context=None):
        """Unchecks 'requires correction' when the value and base of the sick pay or sick benefit
        line has been manually corrected by the user
        @param ids: [payslip_line id] """
        if not ids:
            return {'value': {'base': base, 'value': value}}
        context = context or {}

        sick_pay_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_pay')[1]
        sick_benefit_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_benefit')[1]
        child_care_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_child_care')[1]
        if type_id in [sick_pay_type_id, sick_benefit_type_id, child_care_type_id]:
            if base != 0 and value != 0:
                context['update_absences'] = True
                self.write(cr, uid, ids[0], {'wymaga_korekty': False, 'base': base, 'value': value}, context=context) #Both write and value are used, because otherwise values tend to reset back to their original values
                return {'value':{'wymaga_korekty':False}}
            else:
                self.write(cr, uid, ids[0], {'wymaga_korekty': True}, context=context)
                return {'value':{'wymaga_korekty':True}}

        vals = {'base': base, 'value': value}
        if value:
            vals['wymaga_korekty'] = False
        return {'value': vals}


    def on_change_correction_line_for_boolean(self, cr, uid, ids, base, value, type_id, context=None):
        """Unchecks 'requires correction' when the value and base of the sick pay or sick benefit
        line has been manually corrected by the user
        @param ids: [payslip_line id] """
        context = context or {}

        sick_pay_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_pay')[1]
        sick_benefit_type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_benefit')[1]
        if type_id in [sick_pay_type_id, sick_benefit_type_id]:
            if base != 0 and value != 0:
                context['update_absences'] = True
                self.write(cr, uid, ids[0], {'wymaga_korekty': False, 'base': base, 'value': value}, context=context)
                return {'value':{'wymaga_korekty':False}, 'warning': {'title': 'Uwaga!', 'message': 'Korekty należy dokonać na polach podstawy i wartości.'}}
            elif base == 0 or value == 0:
                self.write(cr, uid, ids[0], {'wymaga_korekty': True}, context=context)
                return {'value':{'wymaga_korekty':True}, 'warning': {'title': 'Uwaga!', 'message': 'Korekty należy dokonać na polach podstawy i wartości.'}}

        # Coś nie pozwalało zapisać linii po ręcznej korekcie.
        self.write(cr, uid, ids[0], {'base': base, 'value': value}, context=context)
        return {'value': {'base': base, 'value': value}}

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        if not vals.get('wymaga_korekty') and vals.get('base') and context.get('update_absences'):
            self.update_line_absences(cr, uid, ids, vals, context=context)
        return super(hr2_payslip_line, self).write(cr, uid, ids, vals, context=context)
    
    def update_line_absences(self, cr, uid, ids, vals, context=None):
        # Uaktualnij skorygowaną podstawę chorobowego w nieobecnościach z tego miesiąca.
        abs_pool = self.pool.get('hr2.absence')
        abs_type_pool = self.pool.get('hr2.absence.type')
        register_pool = self.pool.get('hr2.payroll.register')
        sick_types = abs_type_pool.search(cr, uid, [('type', 'in', ['sick_leave', 'child_care'])], context=context)

        if isinstance(ids, list):
            ids = ids[0]    # Korygowana ręcznie może być i tak tylko jedna linia na raz.
        line_obj = self.browse(cr, uid, ids, context=context)
        employee_id = line_obj.payslip_id.employee_id.id
        date_start = datetime.strptime(line_obj.date_start, tools.DEFAULT_SERVER_DATE_FORMAT)
        date_start = datetime.strftime(date(date_start.year, date_start.month, 01), tools.DEFAULT_SERVER_DATE_FORMAT)
        date_stop = datetime.strptime(line_obj.date_stop, tools.DEFAULT_SERVER_DATE_FORMAT)
        date_stop = datetime.strftime(register_pool.last_day_of_month(date_stop.year, date_stop.month), tools.DEFAULT_SERVER_DATE_FORMAT)

        abs_ids = abs_pool.search(cr, uid, ['&', '&', '|',
                                            '&', ('date_from', '>=', date_start), ('date_from', '<=', date_stop),
                                            '&', ('date_to', '>=', date_start), ('date_to', '<=', date_stop),
                                            ('holiday_status_id', 'in', sick_types),
                                            ('employee_id', '=', employee_id)], context=context)
        with tools.context_scope(context, {'not_validate': True}):
            abs_pool.write(cr, uid, abs_ids, vals, context=context)
        return True

    def correct_line(self, cr, uid, ids, context=None):
        """ Otwiera wizarda korygowania linii. """
        context = context or {}
        model_pool = self.pool.get('ir.model.data')
        line_id = ids[0]

        sick_pay_type_id = model_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_pay')[1]
        sick_benefit_type_id = model_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_sick_benefit')[1]
        child_care_type_id = model_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_child_care')[1]
        line_obj = self.browse(cr, uid, line_id, context=context)
        if line_obj.type_id.id not in [sick_pay_type_id, sick_benefit_type_id, child_care_type_id]:
            raise osv.except_osv('Błąd!', 'Tylko linie powstałe z powodu nieobecności mogą wymagać korekt tą metodą.')

        register_obj = line_obj.payslip_id.register_id
        month = register_obj.register_month
        year = register_obj.register_year
        year_back = (date(year, month, 1) - relativedelta.relativedelta(years=1))

        # Przekaż dane w kontekście.
        context.update({
            'payslip_line_id': line_id,
            'value': line_obj.value,
            'base': line_obj.base,
            'base_month_start': year_back.month,
            'base_year_start': year_back.year,
            'base_month_stop': month,
            'base_year_stop': year,
        })
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('model', '=', 'hr2.payslip.line.correction.wizard'),
                                                               ('name', '=', 'hr2.payslip.line.correction.wizard.form')],
                                                     context=context)
        return {
            'name': 'Korekta',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr2.payslip.line.correction.wizard',
            'res_id': [],
            'view_id': view_id,
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }

hr2_payslip_line()


class hr2_payslip_line_temp(osv.osv_memory):
    _name = "hr2.payslip.line.temp"
    _inherit = "hr2.payslip.line"
    _columns = {
                'payslip_id': fields.many2one('hr2.payslip', 'Payslip', required=True, ondelete='cascade'),
                'type_id': fields.many2one('hr2.payslip.line.type', 'Line type', required=True, ondelete='restrict'),
                'date_start': fields.date('Date start'),
                'date_stop': fields.date('Date stop'),
                'value': fields.float('Value'),
                'percent': fields.float('Percent'),
                'addition_type': fields.many2one('hr2.salary.addition.type', 'Typ dodatku'),
                'licz_KUP_jak_podstawa': fields.boolean('Licz KUP jak dla podstawy?'),
                'register_id': fields.many2one('hr2.payroll.register', 'Register id')
                }

hr2_payslip_line_temp()


class hr2_payslip_line_line(osv.osv):
    _name ="hr2.payslip.line.line"
    _description = "Subject of the hr2_payslip_line"
    _inherit = 'company.related.class'
    
    def init(self,cr):
        cr.execute("""select lanname from pg_language where lanname ='plpgsql'""")
        language = cr.fetchall()
        if not language:
            cr.execute('create language plpgsql')
                          
        cr.execute(              
                   """
                CREATE OR REPLACE FUNCTION function_trigger_sum_payslip_line_line() RETURNS TRIGGER AS $$
                DECLARE
                    amount float;
                BEGIN
                    IF (TG_OP = 'UPDATE') OR (TG_OP = 'INSERT') THEN
                        amount = (SELECT SUM(pll.value) FROM hr2_payslip_line_line AS pll
                                                    WHERE pll.payslip_line_id = NEW.payslip_line_id); 
                        IF amount < 0 THEN
                            amount = 0.0;
                        END IF;
                        UPDATE hr2_payslip_line AS hpl 
                                SET value = amount WHERE hpl.id = NEW.payslip_line_id;
                        RETURN NULL;
                    ELSE
                        amount = (SELECT SUM(pll.value) FROM hr2_payslip_line_line AS pll
                                                    WHERE pll.payslip_line_id = OLD.payslip_line_id); 
                        IF amount < 0 THEN
                            amount = 0.0;
                        END IF;
                        UPDATE hr2_payslip_line AS hpl 
                                SET value = amount WHERE hpl.id = OLD.payslip_line_id;
                        RETURN NULL;
                    END IF;
                END;
                $$ LANGUAGE plpgsql;
                   """
                  )
          
        cr.execute("""SELECT tgname FROM pg_trigger WHERE tgname='sum_payslip_line_line'""")
        trigger = cr.fetchall()
        if not trigger:
            cr.execute(""" CREATE TRIGGER sum_payslip_line_line AFTER DELETE OR UPDATE OF value OR INSERT ON hr2_payslip_line_line
                           FOR ROW
                           EXECUTE PROCEDURE function_trigger_sum_payslip_line_line();""")

        return
    
    _columns = {
                'payslip_line_id': fields.many2one('hr2.payslip.line', 'Składnik wynagrodzenia', required=True, ondelete='cascade'),
                'name': fields.char('Name', readonly=True),
                'number': fields.integer('Number'),
                'base': fields.float('Base'),
                'days': fields.integer('Number of days'),
                'hours': fields.integer('Number of hours'),
                'value': fields.float('Value'),
                'addition_type': fields.many2one('hr2.salary.addition.type', 'Typ dodatku'),
                'addition_percent': fields.float('Percent of total addition sum'),
                'type': fields.selection([('work_time', 'Work time'),('addition','Addition'),('deduction','Deduction')], 'Typ')
               }
    _order = 'number asc'
    
    def unlink(self, cr, uid, ids, context=None):
        """
        Metoda orm-owa nadpisana ze wzgledu na przywrócenie stanu 'approved' dla rekordów hr2.overtime,
        które są nadgodzinami powiązanymi z usuwanymi liniami
        """
        res = False
        
        # sprawdzamy czy usuwana linia to nadgodzina
        for line_id in ids:
            line_browse = self.browse(cr, uid, line_id, context=context)
            
            if line_browse.type == 'addition' and line_browse.name == 'Nadgodziny':
                # sprawdzamy czy naliczanie nadgodzin nie jest uproszczone (wartość parametru konfiguracji = False)
                try:
                    conf_value = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Uproszczone naliczanie nadgodzin')
                except ValueError:
                    pass
        
                if conf_value:
                    res = super(hr2_payslip_line_line, self).unlink(cr, uid, line_id, context=context)
                
                else:
                    date_start = line_browse.payslip_line_id.date_start
                    date_stop = line_browse.payslip_line_id.date_stop
                    employee_id = line_browse.payslip_line_id.payslip_id.employee_id.id
                    
                    overtimes = self.pool.get('hr2.overtime').search(cr, uid, [
                                                                   ('date_from','>=',date_start),
                                                                   ('date_to','<=',date_stop),
                                                                   ('employee_id','=',employee_id),
                                                                   ('state','=','closed')
                                                                   ], context=context)
                    
                    for overtime in overtimes:
                        cr.execute("UPDATE hr2_overtime SET state='approved' WHERE id = %s", ([overtime]))
                    
                    res = super(hr2_payslip_line_line, self).unlink(cr, uid, line_id, context=context)
                    
        return res
   
    
hr2_payslip_line_line()

class ir_sequence(osv.osv):
    _name="hr2.ir.sequence"
    _description = "Sequence"
    _inhertis = "ir_sequence"
ir_sequence()

class hr_payslip_config(osv.osv):
    _name = "hr2.payslip.config"
    _description = "Payslip configuration"
    _inherit = 'company.related.class'
    _columns = {
                'sequence': fields.many2one('ir.sequence', 'Sequence', required=True),
                'name': fields.char('Configuration name', required=True),
                'code': fields.char('Configuration code'),
                'contract_type': fields.many2many('hr2.contract.type','hr_contract_type2_rel','config_id','contract_type_id', 'Contract type'),
                'department': fields.many2many('hr2.dzial', 'hr_dzial2_rel','config_id','department_id', 'Department'),
                'transfer_type': fields.selection([('credit','Credit'),('debit','Debit')]),
                'use_contract_only': fields.boolean('Use contracts'),
                'use_post_only': fields.boolean('Use posts'),
                'journal_id': fields.many2one('account.journal', 'Dziennik'),
                'debit_accounts': fields.one2many('hr2.payslip.config.accounts', 'config_id', 'Konta Winien'),
                'credit_accounts': fields.one2many('hr2.payslip.config.accounts', 'config_id', 'Konta Ma'),
                }

    def default_field_values(self, cr, uid, context=None):
        sequence_id = self.pool.get('ir.sequence').search(cr, uid, [('code','=','payroll.register.sequence'),('name','=',"Payroll register sequence")])
        if sequence_id:
            sequence_id = sequence_id[0]
        return sequence_id

    _defaults = {

                 'sequence': lambda obj,cr,uid,context: obj.default_field_values(cr, uid ,context=context),
                }
    
    
    def create(self, cr, uid, vals, context=None):
        '''Metoda tworzy dodatkowe rekordy w tabeli hr2_payslip_config_accounts dla utworzonej konfiguracji'''
        
        if not context: context={}
        
        conf_id = super(hr_payslip_config, self).create(cr, uid, vals, context=context)
        
        list = [{'side':'debit', 'type':'cost', 'percent': 100, 'config_id':conf_id},
                {'side':'credit', 'type':'salary', 'config_id':conf_id},
                {'side':'credit', 'type':'tax_office', 'config_id':conf_id},
                {'side':'credit', 'type':'social_insurance', 'config_id':conf_id},
                {'side':'credit', 'type':'fp_fgsp', 'config_id':conf_id},
                {'side':'credit', 'type':'nfz', 'config_id':conf_id},
                {'side':'credit', 'type':'deduction', 'config_id':conf_id}]
        
        for element in list:
            self.pool.get('hr2.payslip.config.accounts').create(cr, uid, element, context=context)
        
        return conf_id
    
    
hr_payslip_config()
######End of payslip block

class hr2_insurance_codes(osv.osv):
    '''Provides insurance codes functionality, related to Płatnik app'''

    _name = "hr2.insurance.codes"
    _description = "Insurance codes"
    _columns = {
        'description'     : fields.text('Description', required=True),
        'name'            : fields.char('Code', size=4, required=True),
        'reg_posts'       : fields.one2many('hr2.etat.data', 'insurance_code', 'Regular Posts'),
        'contracts'       : fields.one2many('hr2.contract', 'insurance_code', 'Contracts'),
    }

    def onchange_insurance_code(self, cr, uid, ids, code, context=None):
        '''Prevents from having invalid insurance codes values'''

        res = {}
        warning = {}
        if code:
            regex = re.compile("^\d{4}$")
            r = regex.search(code)
            if r == None:
                res['name'] = ''
                warning['title'] = _('Error')
                warning['message'] = _('Correct the invalid values')
                return { 'value' : res, 'warning' : warning }
        return {}

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context.get('date_from'):
            configuration = self.pool.get('hr2.payslip.config').znajdz_konfiguracje_dladaty(cr, uid, date=context.get('date_from')[:10])
        return super(hr2_insurance_codes, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context, count=count)

hr2_insurance_codes()

class hr2_benefit_codes(osv.osv):
    '''Provides benefit codes functionality, related to Płatnik app'''

    _name = "hr2.benefit.codes"
    _description = "Benefit codes"
    _columns = {
        'description'   : fields.text('Description', required=True),
        'name'          : fields.char('Code', size=3, required=True),
        'is_benefit'    : fields.boolean('Is benefit'),
        'absence_ids'   : fields.many2many('hr2.absence.type', 'absence_benefit_rel', 'benefit_codes', 'absence', 'Absence types'),
    }

    def onchange_benefit_code(self, cr, uid, ids, code, context=None):
        '''Prevents from having invalid benefit codes values'''

        res = {}
        warning = {}
        if code:
            regex = re.compile("^\d{3}$")
            r = regex.search(code)
            if r == None:
                res['name'] = ''
                warning['title'] = _('Error')
                warning['message'] = _('Correct the invalid values')
                return { 'value' : res, 'warning' : warning }
        return {}

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context.get('date_from'):
            configuration = self.pool.get('hr2.payslip.config').znajdz_konfiguracje_dladaty(cr, uid, date=context.get('date_from')[:10])
        return super(hr2_benefit_codes, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context, count=count)

hr2_benefit_codes()


class hr2_nfz(osv.osv):

    _name = "hr2.nfz"
    _description = "NFZ codes"
    _columns = {
        'name' : fields.char('Code', size=3, required=True),
    }

hr2_nfz()


class hr2_obsolete_reason(osv.osv):

    _name = "hr2.obsolete.reason"
    _description = "Obsolete reason"
    _columns = {
        'name' : fields.char('Code', size=3, required=True),
        'description' : fields.char('Description', required=True),
    }

hr2_obsolete_reason()


class hr2_absence_type(osv.osv):
    _name = "hr2.absence.type"
    _inherit = "hr2.absence.type"

    _columns = {
                'benefit_ids': fields.many2many('hr2.benefit.codes', 'absence_benefit_rel', 'absence', 'benefit_codes', 'Benefit Codes'),
                'kup': fields.boolean('Naliczaj dla etatów % KUP za czas nieobecności'),
                }
    _defaults = {
                'kup':False,
                }
hr2_absence_type()

class hr2_etat(osv.osv):
    _name = "hr2.etat"
    _inherit = "hr2.etat"
    
    def get_etat_data_for_date(self, cr, uid, etat_id, date, context = False):
        'Returns insurance data and job time for given etat object and date'
        context = context or {}
        result = {}
        if etat_id:
            date = date or time.strftime('%Y-%m-%d')
            etat_obj = self.browse(cr, uid, etat_id, context=context) 
            date_list = [etat_data.date_from for etat_data in etat_obj.etat_data]
        if len(date_list) > 0:
            date_list.sort(reverse=True)
            for single_date in date_list:
                if single_date < date:
                    etat_data_ids = self.pool.get('hr2.etat.data').search(cr, uid, [('etat_id','=', etat_obj.id),('date_from','=',single_date)],
                                                                          context = context)
                    result = self.pool.get('hr2.etat.data').read(cr, uid, etat_data_ids, 
                                    ['insurance_code', 'work_time_licz', 'work_time_mian', 'calculate_emr', 'calculate_chor',
                                     'calculate_rent', 'calculate_zdr', 'calculate_wyp'],
                                     context = context)[0]
                    result['insurance_code'] = result['insurance_code'] and result['insurance_code'][1]
                    return result
        return {'insurance_code': None,
                'work_time_licz': None,
                'work_time_mian': None,
                'calculate_emr': None,
                'calculate_chor': None,
                'calculate_rent': None,
                'calculate_zdr': None,
                'calculate_wyp': None
                }
    
hr2_etat()

class hr2_etat_data(osv.osv):
    _name = "hr2.etat.data"
    _inherit = "hr2.etat.data"
    _columns = {
                'insurance_code':fields.many2one('hr2.insurance.codes', 'Insurance code', select=True),
                }
    
    _defaults = {
                 "insurance_code": lambda obj,cr,uid,context: obj.default_field_values(cr, uid, 'insurance_code',context=context)['insurance_code'][0],
                 }
    
    def default_field_values(self, cr, uid, fields, context=None):
        '''Provides default field values, taken from the latest etat_data object.
        @param fields: names of the fields
        @return: Computed fields value.
        '''
                
        employee_id = context.get('employee_id')
        active_id = context.get('active_id')
        generate_from_button = context.get('generate_from_button', False)
        if not employee_id:
            if active_id:
                return False
            '''By having employee_id, we're looking for post and then post_data'''
        etat_data_list = []
        if context.has_key('post_id'):
            etat_id = context.get('post_id')
            if etat_id and isinstance(etat_id, (int, long)):
                etat_id = [etat_id]
        else:
            etat_id = self.pool.get('hr2.etat').search(cr, uid, [('employee_id','=',employee_id)], context=context)
        etat_data_list = self.pool.get('hr2.etat.data').search(cr, uid, [('etat_id','in',etat_id)], order='date_from', context=context)

        '''Searching for etat_data'''
        if etat_data_list:
            if not isinstance(fields, (list, dict)): fields = [fields]
            newest_etat = etat_data_list[len(etat_data_list)-1]
            res = self.pool.get('hr2.etat.data').read(cr, uid, newest_etat, fields, context=context)
            if not isinstance(res, (list, dict)): res[fields] = res
            return res           
        else:
            if fields in ['calculate_fp', 'calculate_fgsp', 'calculate_rent', 'calculate_emr', 'calculate_wyp', 'calculate_chor']:                
                return True
            elif fields == 'insurance_code':
                code_ids = {}
                code_ids['insurance_code'] = self.pool.get('hr2.insurance.codes').search(cr, uid, [('name','=','0110')], context=context)
                return code_ids or False
            else:
                return super(hr2_etat_data, self).default_field_values(cr, uid, fields, context=context)
hr2_etat_data()
        
class hr2_contract(osv.osv):
    _name = "hr2.contract"
    _inherit = "hr2.contract"
    _columns = {
                'insurance_code': fields.many2one('hr2.insurance.codes', 'Insurance code', select=True),
                }

hr2_contract()


class hr2_payroll_register(osv.osv):
    _name = "hr2.payroll.register"
    _description = "Payroll register"
    _inherit = 'company.related.class'

    def init(self, cr):
        cr.execute('''CREATE OR REPLACE FUNCTION function_set_register_period() RETURNS TRIGGER AS $$
                        BEGIN
                            IF (TG_OP = 'UPDATE') AND NEW.date_computed != OLD.date_computed THEN
                                UPDATE hr2_payroll_register
                                    SET period_id = (SELECT id FROM account_period
                                                    WHERE date_stop >= NEW.date_computed
                                                        AND period_type = 'regular'
                                                    ORDER BY date_stop LIMIT 1)
                                    WHERE id = NEW.id;
                            ELSIF (TG_OP = 'INSERT') THEN
                                UPDATE hr2_payroll_register
                                    SET period_id = (SELECT id FROM account_period
                                                    WHERE date_stop >= NEW.date_computed
                                                        AND period_type = 'regular'
                                                    ORDER BY date_stop LIMIT 1)
                                    WHERE id = NEW.id;
                            END IF;
                            RETURN NULL;
                        END;
                        $$ LANGUAGE plpgsql; ''')
        cr.execute("""SELECT tgname FROM pg_trigger WHERE tgname='set_register_period'""")
        trigger = cr.fetchall()
        if not trigger:
            cr.execute(""" CREATE TRIGGER set_register_period AFTER INSERT OR UPDATE ON hr2_payroll_register
                            FOR ROW
                            EXECUTE PROCEDURE function_set_register_period();""")
        return True

    def _calculate_payment_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for id in ids:
            month = self.browse(cr, uid, id, context=context).date[5:7]
            year = self.browse(cr, uid, id, context=context).date[:4]
            res[id] = {
                'payment_month': month,
                'payment_year': year,
            }

        return res


    def multisearch_hr_payroll_register_1(self, cr, uid, args_dict, context=None):
        """Finds the payroll registers based on the date range specified by the user
        Registers have a hidden field (date_computed), based on the month and the year, always with the 1st day of the month
        To adapt to the situation, the multisearch ignores the day specified by the user, always setting it to '1' (only months and years count).
        @param cr: database cursor
        @param uid: user id
        @param args_dict: dictionary of filter values (containing one key, date_range, which is a list of two dates)
        @return: list of hr2.payroll.register ids fitting into requirements specified by the user
        """
        date_range = args_dict.get('date_range', '')
        register_ids = []
        search_command = 'SELECT id from hr2_payroll_register WHERE'

        additional_commands = []
        attributes_list = []
        counter = 0

        if date_range:
            date_from = date_range[0] and datetime.strptime(date_range[0], tools.DEFAULT_SERVER_DATE_FORMAT)
            date_to = date_range[1] and datetime.strptime(date_range[1], tools.DEFAULT_SERVER_DATE_FORMAT)

            if date_from:
                #Ignoring days by setting them to 1 by default
                date_from = datetime.strptime(str(date_from.year)+'-'+str(date_from.month)+'-01', tools.DEFAULT_SERVER_DATE_FORMAT).date()
                additional_commands.append('date_computed >= %s')
                attributes_list.append(str(date_from))
            if date_to:
                date_to = datetime.strptime(str(date_to.year)+'-'+str(date_to.month)+'-01', tools.DEFAULT_SERVER_DATE_FORMAT).date()
                additional_commands.append('date_computed <= %s')
                attributes_list.append(str(date_to))

        #Gathering the data
        if additional_commands:
            for command in additional_commands:
                if counter > 0:
                    search_command += ' AND'
                search_command += ' ' + command
                counter += 1

            attributes_list = tuple(attributes_list) #If additional_commands list isn't empty, attributes_list won't be as well
            cr.execute(search_command,attributes_list)
            register_ids = cr.fetchall()
            register_ids = zip(*register_ids) and zip(*register_ids)[0]
        return register_ids

    def generate_month_year(self, cr, uid, ids, field_name, arg, context=None):
        """Method for fields.function - generates mm/yyyy information based on the month
        and year from the hr2.payroll.register object
        @param cr: database cursor
        @param uid: user id
        @param ids: ids of the objects, for which the field value is being computed
        @param field_name: name of the field for which value is generated
        @param arg: arguements (None in this case)
        @return: dict of ids with their own dicts, which include values"""
        res = {}
        browse_list = self.browse(cr, uid, ids, context=context)
        for object in browse_list:
            res[object.id] = {}
            res[object.id] = str(object.register_month)+'/'+str(object.register_year)
        return res

    _columns =  {
                   'name': fields.char('Number'),
                   'date': fields.date('Date of payment', required=True),
                   'register_month': fields.integer('Month', required=True),
                   'register_year': fields.integer('Year', nosep=True, required=True),
                   'config': fields.many2one('hr2.payslip.config','Configuration', required=True, ondelete='restrict'),
                   'payslip_ids': fields.one2many('hr2.payslip', 'register_id', 'Pasek listy płac', ondelete='cascade'),
                   'process_prev_month': fields.boolean('Should previous month be processed?'),
                   'sequence': fields.integer('Sequence'),
                   'state': fields.selection((('new','New'),('additions','Additions'), ('elements','Elements'), ('draft','Draft'), ('confirmed','Confirmed'), ('closed','Closed')),
                                             'State'),
                   'payment_month': fields.function(_calculate_payment_date, method=True, multi="payment_date"),
                   'payment_year': fields.function(_calculate_payment_date, method=True, multi="payment_date"),
                   # column period_id need for evaluating product and/or project manufacturing cost
                   'period_id': fields.many2one('account.period', 'Account period', ondelete='restrict'),
                   'date_computed': fields.date('Date'),
                   'view_month_year': fields.function(generate_month_year, method=True, type="char", string='Month / Year')
                   }

    _defaults = {
                 'register_year': lambda *a: int(time.strftime('%Y')),
                 'state': 'new',
                 }

    _order = 'register_year desc,register_month desc'

    def _check_month(self, cr, uid, ids, context=None):
        '''Checks if the month value exceeds the allowed range
        @param ids: Register ID
        '''
        register_list = self.browse(cr,uid,ids)
        for register in register_list:
            month = register.register_month
            if month not in range(1,13):
                raise osv.except_osv(_('Warning!'),_('The month should be a number in range 1-12.'))
        return True

    _constraints = [(_check_month, 'Error: Month should be a value between 1-12', ['numbers_of_days_temp']), ]


    def calculate_additions_pre(self, cr, uid, id, payslip_id, month, year, typ, period_start=0, period_stop=0, context=None):
        '''Funkcja tworzy obiekty payslip_line dla dodatkow w danym aneksie'''
        number = 1

        '''Wyszukanie id dodatków odpowiednich dla danego aneksu'''
        if typ == 'e':
            sql_query = """SELECT id FROM hr2_salary_addition
                          WHERE etat_data_id = {etat_id}
                                AND (year_start < {year} OR (year_start = {year} AND month_start <= {month}))
                                AND ((year_stop > {year} OR (year_stop = {year} AND month_stop > {month})) OR year_stop = 0)"""
            cr.execute(sql_query.format(etat_id=id, year=year, month=month))
            additions_ids = [add_id[0] for add_id in cr.fetchall()]
        elif typ == 'c':
           additions_ids = self.pool.get('hr2.salary.addition').search(cr, uid, ['&','&','&',('contract_id','=',id),('year_start','<=',year),
                                                                                 ('month_start','<=',month),'|',('year_stop','=','0'),'&',
                                                                                 ('year_stop','>=',year),('month_stop','>',month)],
                                                                       context=context)

        additions_list = self.pool.get('hr2.salary.addition').browse(cr, uid, additions_ids, context=context)
        for addition in additions_list:
            vals = {}


            '''Dodatkowe sprawdzenie czy dodatki przysluguja na dany miesiac'''
            if addition.addition_type_id.okresowy:
                if addition.addition_type_id.co_ile_powtarzac != 1:
                    date_start = addition.year_start * 12 + addition.month_start
                    date_now = year * 12 + month
                    date_delta = date_now-date_start
                    if date_delta % addition.addition_type_id.co_ile_powtarzac != 0:
                        continue
            elif (addition.year_start != year) | (addition.month_start != month):
                continue

            '''Zebranie danych do stworzenia payslip.line'a'''
            vals['payslip_id'] = payslip_id
            vals['type_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_addition')[1]
            vals['number'] = number
            vals['date_start'] = period_start
            vals['date_stop'] = period_stop
            if addition.kwota != 0:
                vals['base'] = addition.kwota
                vals['value'] = addition.kwota
            elif addition.procent_podstawy != 0:
                if typ == 'e':
                    podstawa = self.pool.get('hr2.etat.data').read(cr, uid, id, ['month_pay'], context=context)['month_pay']
                    vals['base'] = lacan_round(addition.procent_podstawy /100 * podstawa, 2)
                    vals['value'] = vals['base']
                elif typ == 'c':
                    podstawa = self.pool.get('hr2.contract').read(cr, uid, id, ['month_pay'], context=context)['month_pay']
                    vals['base'] = lacan_round(addition.procent_podstawy /100 * podstawa, 2)
                    vals['value'] = vals['base']
            else:
                vals['base'] = 0
                vals['value'] = 0
            vals['addition_id'] = addition.id
            vals['addition_type'] = addition.addition_type_id.id
            vals['licz_KUP_jak_podstawa'] = addition.addition_type_id.licz_kup_jak_podstawa
            number += 1

            self.pool.get('hr2.payslip.line').create(cr, uid, vals, context=context)
        return True

    def get_period(self, cr, uid, month, year, context=None):
        month = str(month)
        year = str(year)

        if len(month)<2:
            month = '0' + month

        period_id = self.pool.get('account.period').search(cr, uid, [('name', '=', month + '/' + year)], context=context)
        if period_id:
            period_id = period_id[0]
        else:
            raise osv.except_osv('Błąd!', 'Brak okresu rozliczeniowego na '+ month + '/' + year +'.')
        return period_id

    def compute_additions(self, cr, uid, ids, context=None):
        '''Function executed after pressing calculate additions button in payroll.register view
        function creates payslips for employees and add payslip lines for every addition'''
        context = context or {}
        self.write(cr, uid, ids, {'state': 'additions'}, context=context)
        data_payslip = []
        employee_ids = []

        '''Method should be executed only for a single payroll'''
        if len(ids) > 1:
            raise osv.except_osv(_('Error!'), _('Cannot compute more than one payroll at a given time.'))
        #Check is previous payroll validated
        # config_id = self.read(cr, uid, ids[0], ['config'], context=context)['config'][0]
        # payroll_list = self.search(cr, uid, [('config','=',config_id)], context=context)
        # payroll_list.remove(ids[0])
        # payrolls_state = self.read(cr, uid, payroll_list, ['state'], context=context)
        # for payroll in payrolls_state:
        #     if payroll['state'] != 'confirmed':
        #         raise osv.except_osv(_('Błąd!'), _('Istnieją niezatwierdzone listy płac z tą konfiguracją '))

        register_data = self.read(cr, uid, ids[0], ['config', 'register_month', 'register_year'], context=context)
        month = register_data['register_month']
        year = register_data['register_year']

        config_id = register_data['config'][0]
        config_obj = self.pool.get('hr2.payslip.config').read(cr, uid, config_id,
                                                              ['sequence', 'contract_type', 'use_post_only', 'use_contract_only', 'department'],
                                                              context=context)

        ctx = context.copy()
        ctx['period_id'] = self.get_period(cr, uid, month, year, context)

        sequence_id = config_obj['sequence'][0]
        number = self.pool.get('ir.sequence').get_number(cr, uid, sequence_id, date(year, month, 1), context=ctx)

        ctx['employee_list_date'] = self.read(cr, uid, ids[0], ['date'],context=context)['date']
        ctx['shift_list_date'] = self.read(cr, uid, ids[0], ['date'], context=context)['date']
        ctx['register_id'] = ids[0]

        '''Calling the method returning id for contracts and post that are supposed to be computed'''
        ids_to_compute = self.condition_check(cr, uid, ids, month, year, config_obj, context=ctx)
        register_vals = self.pool.get('hr2.payroll.register').read(cr, uid, ids[0],
                                                                   ['register_year', 'register_month', 'process_prev_month'], context=context)
        
        # Create sorted list of employees for the payroll register
        for contract in ids_to_compute['contract_ids']:
            data_id = self.pool.get('hr2.contract').read(cr, uid, contract, ['id', 'employee_id'], context=ctx)
            data_payslip.append(data_id)
        for post in ids_to_compute['post_ids']:
            data_id = self.pool.get('hr2.etat').read(cr, uid, post, ['id', 'employee_id'], context=ctx)
            data_payslip.append(data_id)
        data_payslip = sorted(data_payslip, key=lambda data_payslip:data_payslip['employee_id'][1])
        
        for employee in data_payslip:
            employee_id = employee['employee_id'][0]
            employee_ids.append(employee_id)
            if employee['id'] in ids_to_compute['contract_ids']: 
                test = self.pool.get('hr2.contract').read(cr, uid, employee['id'], ['employee_id'], context=ctx)['employee_id']
                if test and test[0] == employee_id:                 
                    '''Computing selected contract'''                
                    write_data = {}
                    payslip_id = int(self.pool.get('hr2.payslip').create(cr, uid, {'employee_id': employee_id, 'register_id': ids[0],
                                                                           'cywilnoprawna_id': employee['id']}, context=ctx))
                    write_data['cywilnoprawna_id'] = employee['id']
                    write_data['register_id'] = ids[0]
                    period_start = date(year, month, 1)
                    last_day_of_month = self.last_day_of_month(year, month).day
                    period_stop = date(year, month, last_day_of_month)
                    self.pool.get('hr2.payslip').write(cr, uid, payslip_id, write_data, context=ctx)
                    self.calculate_additions_pre(cr, uid, employee['id'], payslip_id, month, year, 'c', period_start=period_start,
                                                 period_stop=period_stop, context=ctx)

            if employee['id'] in ids_to_compute['post_ids']: 
                test = self.pool.get('hr2.etat').read(cr, uid, employee['id'], ['employee_id'], context=ctx)['employee_id']
                if test and test[0] == employee_id:
                    '''Computing selected post'''        
                    write_data = {}
                    payslip_id = int(self.pool.get('hr2.payslip').create(cr, uid, 
                                                                    {'employee_id': employee_id, 'register_id': ids[0], 'etat_id': employee['id']}, 
                                                                    context=ctx))
                    write_data['etat_id'] = employee['id']
                    write_data['register_id'] = ids[0]
                    self.pool.get('hr2.payslip').write(cr, uid, payslip_id, write_data, context=ctx)
    
                    '''Tworzenie list okresów pracy pracownika'''
                    period_list = self.generate_periods(cr, uid, employee['id'], register_vals)
    
                    '''Tworzenie dodatków dla każdego okresu pracy'''
                    for period in period_list['work_time_list']:
                        etat_data_id = period['etat_data_id']
                        if type(etat_data_id) is list:
                            etat_data_id = etat_data_id[0]
                        self.calculate_additions_pre(cr, uid, etat_data_id, payslip_id, month, year, 'e',
                                                    period_start=period['date_start'], period_stop=period['date_stop'], context=ctx)
    
        self.pool.get('hr2.payroll.register').write(cr, uid, ids[0], {'name':number}, context=context)

        current_day = str(datetime.strptime(str(register_data['register_year']) + '-' + str(register_data['register_month']) + '-01', 
                                            tools.DEFAULT_SERVER_DATE_FORMAT).date())
        if employee_ids:
            self.pool.get('hr2.employee.date').create_hr_employee_dates(cr, uid, employee=employee_ids, date=current_day, context=context)
        return True

    def compute_elements(self, cr, uid, ids, context=None):
        '''function executed after pressing calculate elements in payroll view'''
        if not context:
            context = {}
        '''Method should be executed only for a single payroll'''
        if len(ids) > 1:
            raise osv.except_osv(_('Error!'),_('Cannot compute more than one payroll at a given time.'))

        ctx = context.copy()
        ctx['employee_list_date'] = self.read(cr, uid, ids[0], ['date'],context=context)['date']
        ctx['shift_list_date'] = self.read(cr, uid, ids[0], ['date'], context=context)['date']
        ctx['register_id'] = ids[0]
        
        reg_dict = self.read(cr, uid, ids[0], ['register_month','register_year'])
        month = reg_dict['register_month']
        year = reg_dict['register_year']
        
        if month == 1:
            is_january = True
        else:
            is_january = False
        
        # sprawdź parametr 'Uproszczone naliczanie nadgodzin'
        try:
            conf_value = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Uproszczone naliczanie nadgodzin')
        except ValueError:
            pass
        
        periods = []
        
        if conf_value:
            # jeśli parametr 'Uproszczone naliczanie nadgodzin' jest True, sprawdź 'Okres rozliczania nadgodzin'
            # rozlicz nadgodziny za pomocą funkcji count_overtime_hours jeśli jest to odpowiedni miesiąc
            try:
                related_conf_value = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Okres rozliczania nadgodzin')
            except ValueError:
                pass
            
            if related_conf_value != 1:
                
                months_list = [] # lista miesiecy, w których rozliczamy nadgodziny
                helper = related_conf_value # zmienna pomocnicza
                
                while helper <= 12:
                    months_list.append(helper)
                    helper += related_conf_value
                
                if month in months_list:
                    # jeśli jest to miesiąc rozliczania nadgodzin to zwróć 
                    # odpowiednią listę miesięcy (periods), z których mają być liczone nadgodziny
                    helper = related_conf_value # zmienna pomocnicza
                    
                    while helper > 0:
                        
                        if month < 10:
                            periods.append(str(year) + '-0' + str(month))
                        else:
                            periods.append(str(year) + '-' + str(month))
                        
                        month -= 1
                        helper -= 1
                        
            else:
                # jeśli related_conf_value ma wartość 1 to rozliczaj bieżący miesiąc
                if month < 10:
                    periods.append(str(year) + '-0' + str(month))
                else:
                    periods.append(str(year) + '-' + str(month))
                    
        else:
                # jeśli parametr Uproszczone naliczanie nadgodzin ma wartość False to rozliczaj bieżący miesiąc
                if month < 10:
                    periods.append(str(year) + '-0' + str(month))
                else:
                    periods.append(str(year) + '-' + str(month))
                    
        ids_to_compute = self.pool.get('hr2.payslip').search(cr, uid, [('register_id','=',ids[0])], context=context)
        payslips = self.pool.get('hr2.payslip').browse(cr, uid, ids_to_compute, context=context)
        for payslip in payslips:
            if payslip.etat_id:

                self.calculate_elements_post(cr, uid, payslip.etat_id.id, payslip.id, periods, is_january, context=ctx)
                # employee_ids.append(write_data['employee_id'])
                # self.pool.get('hr2.payslip').write(cr,uid,payslip.id, write_data,context=context)

            if payslip.cywilnoprawna_id:
                self.calculate_elements_contract(cr, uid ,payslip.cywilnoprawna_id.id, payslip.id, context=ctx)
                # employee_ids.append(write_data['employee_id'])
                # self.pool.get('hr2.payslip').write(cr,uid,payslip.id, write_data,context=context)
        return True


    def compute_taxes(self, cr, uid, ids, context=None):
        '''function executed after pressing calculate taxes in payroll view'''
        self.check_correction(cr, uid, ids[0], context=context)
        self.write(cr, uid, ids, {'state':'draft'}, context=context)
        if not context:
            context = {}
        '''Method should be executed only for a single payroll'''
        '''Zebranie ids typów linii występujących na payslipach'''
        type_pool = self.pool.get('hr2.payslip.line.type')

        date_planned = self.read(cr, uid, ids[0], ['date'], context=context)['date']
        conf = self.gather_config_data(cr, uid, date_planned, context=context)

        # Double check application and name to prevent possible mismatch after user changes done in types configuration
        worktime_type_id = type_pool.search(cr, uid, [('application', '=', 'work_time'), ('name', '=', 'Work time')], context=context)
        if worktime_type_id:
            worktime_type_id = worktime_type_id[0]
        else:
            raise osv.except_osv('Błąd!', 'Nie ma poprawnie zdefiniowanego typu składnika paska listy płac wynagrodzenia za czas pracy.')
        absence_type_id = type_pool.search(cr, uid, [('application', '=', 'absence'), ('name', '=', 'Absence')], context=context)
        if absence_type_id:
            absence_type_id = absence_type_id[0]
        else:
            raise osv.except_osv('Błąd!', 'Nie ma poprawnie zdefiniowanego typu składnika paska listy płac dla pomniejszenia za czas nieobecności.')
        addition_type_id = type_pool.search(cr, uid, [('application', '=', 'addition'), ('name', '=', 'Addition')], context=context)
        if addition_type_id:
            addition_type_id = addition_type_id[0]
        else:
            raise osv.except_osv('Błąd!', 'Nie ma poprawnie zdefiniowanego typu składnika paska listy płac dla dodatków.')
        sick_leave_types = ['hr2_payslip_line_type_sick_pay']
        
        if len(ids) > 1:
            raise osv.except_osv(_('Error!'),_('Cannot compute more than one payroll at a given time.'))

        employee_ids = []

        ctx = context.copy()
        ctx['employee_list_date'] = date_planned
        ctx['shift_list_date'] = date_planned
        ctx['register_id'] = ids[0]

        ids_to_compute = self.pool.get('hr2.payslip').search(cr, uid, [('register_id','=',ids[0])], context=context)
        payslips = self.pool.get('hr2.payslip').browse(cr, uid, ids_to_compute, context=context)
        for payslip in payslips:
            if payslip.etat_id:
                write_data = self.update_payslip_for_post(cr, uid, payslip.etat_id.id, payslip.id, worktime_type_id, absence_type_id,
                                                          addition_type_id, sick_leave_types, conf, context=ctx)
                employee_ids.append(write_data['employee_id'])
                self.pool.get('hr2.payslip').write(cr, uid, payslip.id, write_data, context=context)

            elif payslip.cywilnoprawna_id:
                write_data = self.update_payslip_for_contract(cr, uid, payslip.cywilnoprawna_id.id, payslip.id, worktime_type_id,
                                                              absence_type_id, addition_type_id, sick_leave_types, conf, context=ctx)
                employee_ids.append(write_data['employee_id'])
                self.pool.get('hr2.payslip').write(cr, uid, payslip.id, write_data, context=context)

            if write_data['potracenia']:
                for deduction in write_data['potracenia']:
                    if write_data['potracenia'][deduction] == 0:
                        continue
                    potracenie = {}
                    potracenie['payslip_id'] = payslip.id
                    potracenie['employee_id'] = write_data['employee_id']
                    potracenie['deduction_id'] = deduction
                    potracenie['deduction_type'] = self.pool.get('hr2.salary.deduction').read(cr,uid,deduction,['deduction_type'], context=context)['deduction_type'][0]
                    potracenie['amount'] = write_data['potracenia'][deduction]
                    self.pool.get('hr2.payslip.deduction').create(cr,uid, potracenie, context=context)

        return True


    def _import_external_addition(self, cr, uid, ids, values, context=None):
        '''Funkcja zapisujaca wartosci na liniach dodatków typu brutto importowane wg podanego słownika {'employee_id':'amount'}'''
        
        payslip_line = self.pool.get('hr2.payslip.line')
        payroll_state = self.read(cr, uid, ids[0], ['state'], context=context)['state']
        # lista obsłużonych payslipów do późniejszego porównania; 
        # jest potrzebne takie jej zastosowanie żeby uwzglednić że więcej niż jedna 
        # linia z dodatkiem typu brutto importowane mogła zostać dodana
        handled_payslip_lines = []
        lista = []
        
        if payroll_state != 'elements':
            raise osv.except_osv('Błąd!', 'Lista płac musi być w stanie Elementy!')
        
        # lista dodatków typu brutto importowane
        additions = self.pool.get('hr2.salary.addition.type').search(cr, uid, [('application','=','brutto_importowane')], context=context)
        
        for key, value in values.items():
            
            if additions:
                employee_payslip_lines = payslip_line.search(cr, uid, [('register_id','=',ids[0]),
                                                                                            ('payslip_id.employee_id','=',key),
                                                                                            ('addition_type','in',additions)], context=context)
                
                handled_payslip_lines += employee_payslip_lines
                
                if employee_payslip_lines:
                    
                    # zakładamy, że jest tylo jedna linia z dodatkiem brutto importowane, a jeśli jest wiecej to zostawiamy
                    cr.execute("UPDATE hr2_payslip_line SET value = %s WHERE id = %s", (value, employee_payslip_lines[0]))
                
                else:
                    employee_name = self.pool.get('hr.employee').read(cr, uid, key, ['name'], context=context)['name']
                    
                    raise osv.except_osv('Błąd!',
                                         "Brak paska listy płac lub dodatku na pasku listy płac, w którym kwota jest typu brutto importowane dla pracownika %s!"
                                          % (employee_name))
                
            else:
                raise osv.except_osv('Błąd!', 'Nie zdefiniowano żadnych dodatków, w których kwota dodatku jest typu brutto importowane!')

        # sprawdzenie czy żadnych pracowników mających linię z dodatkiem typu brutto importowane nie ominięto w podanym słowniku
        register_payslip_lines = payslip_line.search(cr, uid, [('register_id','=',ids[0]),
                                                                ('addition_type','in',additions)], context=context)
        
        unhandled_payslip_lines = list(set(register_payslip_lines).difference(handled_payslip_lines))
        
        for line in unhandled_payslip_lines:
        
            payslip_id = payslip_line.read(cr, uid, line, ['payslip_id'], context=context)['payslip_id'][0]
            lista.append(self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['employee_id'], context=context)['employee_id'][0])
        
        return lista
    
    
    def import_external_components(self, cr, uid, ids, values, context=None):
        '''Sends data from wizard to internal method which changes them into components'''

        # values = {'employee_id':'amount'}
        list = self._import_external_addition(cr, uid, ids, values, context=context)

        return True

    def import_external_components_wiz(self, cr, uid, ids, context=None):
        ''' Calls a wizard importing csv file'''

        context['register_id'] = ids
        return {
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'hr.external.elements.csv',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': context,
                }


    def check_correction(self, cr, uid, register_id, context=None):
        '''Checks if any payslip_lines require correction. If they do, an error is raised'''
        payslip_pool = self.pool.get('hr2.payslip')
        line_pool = self.pool.get('hr2.payslip.line')

        payslip_ids = payslip_pool.search(cr, uid, [('register_id', '=', register_id)], context=context)
        employee_list = ''
        for payslip in payslip_ids:
            line_ids = line_pool.search(cr, uid, [('payslip_id', '=', payslip)], context=context)
            for line in line_ids:
                if line_pool.read(cr, uid, line, ['wymaga_korekty'], context=context)['wymaga_korekty']:
                    employee_name = payslip_pool.read(cr, uid, payslip, ['employee_id'], context=context)['employee_id'][1]
                    employee_list += '\n'+employee_name

        if employee_list:
            raise osv.except_osv('Błąd!', 'Linie pasków listy płac wymagają manualnej korekty \n dla następujących pracowników:'+employee_list+'\n')

        return True


    def create_payment_registers(self, cr, uid, ids, payment_register_ids, payslip, bank, date, type, amount, cash, month_settled,
                                 year_settled, company_id, context=None):
        """ Metoda tworzy rekordy w modelu payment.register i payment.register.line na podstawie payslipów """
        #register
        if not payment_register_ids[type]:
            new_date = date[5:7] + '/' + date[:4]
            period_id = self.pool.get('account.period').search(cr, uid, [('name', '=', new_date)], context=context)
            if period_id:
                period_id = period_id[0]
            else:
                raise osv.except_osv('Błąd!', 'Brak okresu rozliczeniowego na '+ new_date + '.')
            date_start = self.pool.get('account.period').read(cr, uid, period_id, ['date_start'], context=context)['date_start']

            ctx = context.copy()
            ctx['period_id'] = period_id
            values = {
                        'name': self.pool.get('ir.sequence').get_number(cr, uid,self.pool.get('lacan.configuration').
                                                                        get_confvalue(cr, uid, 'Numeracja rejestru wypłat').id,
                                                                        date_start, context=ctx),
                        'bank_id': self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Konto przelewów wychodzących dla pracowników').id,
                        'payroll_register_id': ids[0],
                        'type': type,
                        'group': 'salary',
                        'state': 'open',
                        'planned_payment_date': date,
                        'month_settled': month_settled,
                        'year_settled': year_settled,
                        'company_id': company_id,
                    }
            payment_register_ids[type] = self.pool.get('hr2.payment.register').create(cr, uid, values, context=context)

        account_number = False
        if type == 'cash':
            bank = False
        else:
            bank = bank[0]
            if bank:
                account_number = self.pool.get('res.partner.bank').read(cr, uid, bank, ['acc_number'], context=context)['acc_number']

        if month_settled < 10:
            month_settled = '0' + str(month_settled)
        else:
            month_settled = str(month_settled)

        reciver = self.pool.get('hr2.payslip').read(cr, uid, payslip['id'], ['employee_id'], context=context)['employee_id'][1]
        description = 'Odbiorca: ' + reciver + '\nWynagrodzenie za ' + month_settled + '/' + str(year_settled) + '.'


        #register.line
        values = {
            'payslip_id': payslip['id'],
            'payment_register_id': payment_register_ids[type],
            'amount': amount,
            'out_bank_id': bank,
            'account_number': account_number,
            'state': 'unpaid',
            'cash': cash,
            'description': description,
            }
        self.pool.get('hr2.payment.register.line').create(cr, uid, values, context=context)

        return True


    def validate_payroll(self, cr, uid, payroll_register_id, context=None):
        '''
        Metoda wywoływana przy zamykaniu listy płac.
        Tworzy rekordy w modelu payment.register dla wypłat, rozliczeń z ZUS i US oraz potrąceń na podstawie każdego payslipu.

        @param payroll_register_id: payroll.register id
        @return: True
        '''

        if not context:
            context = {}
        contracts_to_confirm = []
        #change payroll's state
        register_data = self.read(cr, uid, payroll_register_id, ['name', 'state', 'date', 'register_month', 'register_year', 'payslip_ids','config'],
                                  context=context)[0]
        state = register_data['state']
        date = register_data['date']
        month_settled = register_data['register_month']
        year_settled = register_data['register_year']
        write_data = False

        if state == 'draft':
            self.write(cr, uid, payroll_register_id, {'state': 'confirmed'}, context=context)
            write_data = True

        if write_data:
            #get current company
            user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
            company_id = user.company_id.id
            if not company_id:
                company_id = False

            #get payslip data
            payslips_ids = self.read(cr, uid, payroll_register_id, ['payslip_ids'], context=context)[0]['payslip_ids']
            payslips_data = self.pool.get('hr2.payslip').read(cr, uid, payslips_ids, ['employee_id', 'etat_id', 'cywilnoprawna_id', 'do_wyplaty'],
                                                              context=context)

            payment_register_ids = {'cash': False, 'transfer': False}

            #create payment.registers and payment.register.lines
            for payslip in payslips_data:
                post = payslip['etat_id']
                contract = payslip['cywilnoprawna_id']
                payout = payslip['do_wyplaty']

                if post:
                    pay_data = self.pool.get('hr2.etat').read(cr, uid, post[0], ['bank_id', 'cash', 'cash_amount', 'cash_percent'], context=context)
                else:
                    pay_data = self.pool.get('hr2.contract').read(cr, uid, contract[0], ['bank_id', 'cash', 'cash_amount', 'cash_percent'], context=context)
                    contract and contracts_to_confirm.append(contract[0])
                cash = pay_data['cash']
                bank = pay_data['bank_id']
                if bank == False:
                    bank = [False, False]

                #payout in cash
                if cash:
                    type = 'cash'
                    cash_percent = pay_data['cash_percent']
                    cash_amount = pay_data['cash_amount']

                    if cash_amount > 0 or cash_percent > 0:
                        amount = cash_amount
                        amount += payout * (cash_percent/100.0)

                        if amount > payout:
                            amount = payout

                        self.create_payment_registers(cr, uid, payroll_register_id, payment_register_ids, payslip, bank, date, type, amount, True, month_settled, year_settled, company_id, context=context)
                        payout -= amount

                #payout transfer
                if payout > 0:
                    type = 'transfer'
                    self.create_payment_registers(cr, uid, payroll_register_id, payment_register_ids, payslip, bank, date, type, payout, False, month_settled, year_settled, company_id, context=context)


        ### Rozliczenia z urzędami ###
        month_settled = date[5:7]
        year_settled = date[:4]
        ZUS = [0, 0, 0]
        US = {}
        deductions_ids = []
        types_id = self.pool.get('hr2.payslip.line.type').search(cr, uid, [('name','in',('Sick pay','Sick benefit','Child care'))], context=context)
        lm = (datetime.strptime(year_settled + '-' + month_settled + '-01', tools.DEFAULT_SERVER_DATE_FORMAT) - relativedelta.relativedelta(months=1)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        lmpreg = self.pool.get('hr2.payment.register').search(cr,uid,[('month_settled','=', lm[5:7]),('year_settled','=',lm[0:4])])
        lmpreglines = self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id','in', lmpreg),
                                                                                  ('description','like', 'Składki ZUS za')],
                                                                                  context=context)
        cr.execute("""
                    SELECT id
                    FROM   hr2_payment_register_line
                    WHERE  payment_register_id IN (SELECT id
                                                   FROM   hr2_payment_register
                                                   WHERE  ( month_settled > %s
                                                            AND year_settled = %s )
                                                           OR ( year_settled > %s )
                                                           ORDER BY month_settled,year_settled)
                                                   AND description LIKE %s """,
                (month_settled, year_settled, year_settled, "Składki ZUS za %"))
        fpregl_id = cr.fetchall()
        for payslip in register_data['payslip_ids']:
            deductions_ids.extend(self.pool.get('hr2.payslip.deduction').search(cr, uid, [('payslip_id', '=', payslip)], context=context))

            payslip_data = self.pool.get('hr2.payslip').read(cr, uid, payslip,
                                                             ['skladki_ZUS_pracownika', 'emr_pracodawca', 'rent_pracodawca',
                                                              'wyp_pracodawca', 'fp', 'fgsp', 'kwota_NFZ', 'kwota_US', 'etat_id',
                                                              'cywilnoprawna_id', 'employee_id'], context=context)
            ZUS[0] += payslip_data['skladki_ZUS_pracownika'] + payslip_data['emr_pracodawca'] + payslip_data['rent_pracodawca'] + payslip_data['wyp_pracodawca']
            ZUS[1] += payslip_data['fp'] + payslip_data['fgsp']
            ZUS[2] += payslip_data['kwota_NFZ']
            
            ##### ZUS #####
            # odejmowanie wartości zasiłków
            wz = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Czy pracodawca sam wyplaca zasilki z ubezp. spol.')
            if wz:
                payslip_lines_id=self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip)], context=context)
                
                for line in payslip_lines_id:
                    val_line = self.pool.get('hr2.payslip.line').read(cr, uid, line)['value']
                    line_type = self.pool.get('hr2.payslip.line').read(cr, uid, line)['type_id']
                    if line_type and (line_type[0] in types_id):
                        ZUS[0] -= val_line
                liness = self.pool.get('hr2.payment.register.line').read(cr, uid, lmpreglines)        
                for line2 in liness:
                    if line2['amount'] <= 0:
                        ZUS[0] += line2['amount']
            employee_obj = self.pool.get('hr.employee').browse(cr, uid, payslip_data['employee_id'][0], context=context)
            employee_data = self.pool.get('hr.employee').read(cr, uid, payslip_data['employee_id'][0], context=context)
            acc_nr = employee_obj.company_id.tax_office_id.account_number3

            if US.has_key(acc_nr):
                US[acc_nr] += payslip_data['kwota_US']
            else:
                US[acc_nr] = payslip_data['kwota_US']



        if month_settled < 10:
            month_settled = '0' + str(month_settled)
        else:
            month_settled = str(month_settled)

        ##### ZUS #####
        # register
        ZUS_ids = self.pool.get('hr2.payment.register').search(cr, uid, [('group', '=', 'ZUS'), ('month_settled', '=', month_settled),
                                                                         ('year_settled', '=', year_settled)], context=context)
        if not ZUS_ids:
            ZUS_day = str(self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Dzień miesiąca do zapłaty ZUS'))
            ZUS_month = register_data['register_month']
            ZUS_year = register_data['register_year']
            if ZUS_month == 12:
                ZUS_year +=1
                ZUS_month = 1
            else:
                ZUS_month += 1
            ZUS_date = str(ZUS_year) + '-' + str(ZUS_month) + '-' + ZUS_day

            period_id = self.get_period(cr, uid, ZUS_month, ZUS_year)
            date_start = self.pool.get('account.period').read(cr, uid, period_id, ['date_start'], context=context)['date_start']
            ctx = context.copy()
            ctx['period_id'] = period_id
            values = {
                        'name': self.pool.get('ir.sequence').get_number(cr, uid, self.pool.get('lacan.configuration').
                                                                        get_confvalue(cr, uid, 'Numeracja rejestru wypłat').id,
                                                                        date_start, context=ctx),
                        'bank_id': self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Konto przelewów wychodzących do ZUS').id,
                        'type': 'transfer',
                        'group': 'ZUS',
                        'state': 'open',
                        'planned_payment_date': ZUS_date,
                        'month_settled': month_settled,
                        'year_settled': year_settled,
                        'czy_uwzgledniac_planowane_wyplaty': True,
                        'company_id': company_id,
                    }
            payment_register_id = self.pool.get('hr2.payment.register').create(cr, uid, values, context=context)
        else:
            payment_register_id = ZUS_ids[0]

        # register line
        date_settled_string = month_settled + '/' + str(year_settled) + '.'
        description = [
            'Składki na ubezpieczenie społeczne za ',
            'Składki FP i FGŚP za ',
            'Składki na ubezpieczenie zdrowotne za '
        ]
        ZUS_id = self.pool.get('tax.office').search(cr, uid, [('type', '=', 'zus')], context=context)[0]
        ZUS_account = self.pool.get('tax.office').read(cr, uid, ZUS_id, ['account_number1'], context=context)['account_number1']
        for n in range(3):
            values = {
                    'payment_register_id': payment_register_id,
                    'amount': ZUS[n],
                    'account_number': ZUS_account,
                    'state': 'unpaid',
                    'description': description[n] + date_settled_string 
                    }
            payment_line_id = self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id', '=', payment_register_id),
                                                                                          ('description', 'ilike', description[n])],
                                                                                context=context)
            if not payment_line_id:
                self.pool.get('hr2.payment.register.line').create(cr, uid, values, context=context)
            else:
                payment_line_id = payment_line_id[0]
                values['amount'] += self.pool.get('hr2.payment.register.line').read(cr, uid, payment_line_id, ['amount'], context=context)['amount']
                self.pool.get('hr2.payment.register.line').write(cr, uid, payment_line_id, values, context=context)

            ###Odejmowanie od przyszłych miesięcy####
            if n == 0:
                valz = values['amount']
                if valz <= 0:  
                    fpreglineval = self.pool.get('hr2.payment.register.line').read(cr, uid, fpregl_id, ['amount'], context=context)
                    zus = valz
                    for fline in fpreglineval:
                        if zus < 0:
                            zus += fline['amount']
                        self.pool.get('hr2.payment.register.line').write(cr, uid, [fline['id']], {'amount': zus}, context=context)
        ##### US #####
        payment_register_id = self.pool.get('hr2.payment.register').search(cr, uid, [('group', '=', 'US'),
                                                                                     ('month_settled', '=', month_settled),
                                                                                     ('year_settled', '=', year_settled)],
                                                                           context=context)
        if not payment_register_id:
            US_month = register_data['register_month']
            US_year = register_data['register_year']
            if US_month == 12:
                US_year += 1
                US_month = 1
            else:
                US_month += 1
            US_date = str(US_year) + '-' + str(US_month) + '-' + '20'

            period_id = self.get_period(cr, uid, US_month, US_year)
            date_start = self.pool.get('account.period').read(cr, uid, period_id, ['date_start'], context=context)['date_start']
            ctx = context.copy()
            ctx['period_id'] = period_id
            values = {
                        'name': self.pool.get('ir.sequence').get_number(cr, uid, self.pool.get('lacan.configuration').
                                                                        get_confvalue(cr, uid, 'Numeracja rejestru wypłat').id,
                                                                        date_start, context=ctx),
                        'bank_id': self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Konto przelewów wychodzących do US').id,
                        'type': 'transfer',
                        'group': 'US',
                        'state': 'open',
                        'planned_payment_date': US_date,
                        'month_settled': month_settled,
                        'year_settled': year_settled,
                        'czy_uwzgledniac_planowane_wyplaty': True,
                        'company_id': company_id,
                    }
            payment_register_id = self.pool.get('hr2.payment.register').create(cr, uid, values, context=context)
        else:
            payment_register_id = payment_register_id[0]

        description = 'Zaliczka na podatek dochodowy za ' + month_settled + '/' + str(year_settled) + '.'
        for line in US.items():
            values = {
                'payment_register_id': payment_register_id,
                'amount': line[1],
                'account_number': line[0],
                'state': 'unpaid',
                'description': description
                }
            payment_line_id = self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id', '=', payment_register_id),
                                                                                          ('account_number', '=', line[0])], context=context)
            if not payment_line_id:
                self.pool.get('hr2.payment.register.line').create(cr, uid, values, context=context)
            else:
                payment_line_id = payment_line_id[0]
                values['amount'] += self.pool.get('hr2.payment.register.line').read(cr, uid, payment_line_id, ['amount'], context=context)['amount']
                self.pool.get('hr2.payment.register.line').write(cr, uid, payment_line_id, values, context=context)


        ##### Potrącenia #####
        if deductions_ids:
            payment_register_id = self.pool.get('hr2.payment.register').search(cr, uid, [('group', '=', 'deductions'),
                                                                                         ('month_settled', '=', month_settled),
                                                                                         ('year_settled', '=', year_settled)],
                                                                               context=context)
            if not payment_register_id:
                deductions_date = date[5:7] + '/' + date[:4]
                period_id = self.pool.get('account.period').search(cr, uid, [('name', '=', deductions_date)], context=context)
                if period_id:
                    period_id = period_id[0]
                else:
                    raise osv.except_osv('Błąd!', 'Brak okresu rozliczeniowego na '+ deductions_date + '.')
                date_start = self.pool.get('account.period').read(cr, uid, period_id, ['date_start'], context=context)['date_start']

                ctx = context.copy()
                ctx['period_id'] = period_id
                values = {
                            'name': self.pool.get('ir.sequence').get_number(cr, uid, self.pool.get('lacan.configuration').
                                                                            get_confvalue(cr, uid, 'Numeracja rejestru wypłat').id,
                                                                            date_start, context=ctx),
                            'bank_id': self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Konto przelewów wychodzących dla pracowników').id,
                            'type': 'transfer',
                            'group': 'deductions',
                            'state': 'open',
                            'planned_payment_date': date,
                            'month_settled': month_settled,
                            'year_settled': year_settled,
                        }
                payment_register_id = self.pool.get('hr2.payment.register').create(cr, uid, values, context=context)
            else:
                payment_register_id = payment_register_id[0]

            payslip_deduction_datas = self.pool.get('hr2.payslip.deduction').read(cr, uid, deductions_ids,
                                                                                  ['amount', 'deduction_id', 'deduction_type', 'employee_id'],
                                                                                  context=context)
            for payslip_deduction_data in payslip_deduction_datas:
                salary_deduction_data = self.pool.get('hr2.salary.deduction').read(cr, uid, payslip_deduction_data['deduction_id'][0],
                                                                                   ['bank_account_number', 'partner_id'], context=context)

                if salary_deduction_data['partner_id']:
                    out_bank = self.pool.get('res.partner.bank').search(cr, uid, [('partner_id', '=', salary_deduction_data['partner_id'][0])],
                                                                        context=context)[0]
                else:
                    out_bank = False

                description = payslip_deduction_data['employee_id'][1] + ', ' + payslip_deduction_data['deduction_type'][1] + '.'
                values = {
                    'payment_register_id': payment_register_id,
                    'amount': payslip_deduction_data['amount'],
                    'out_bank_id': out_bank,
                    'account_number': salary_deduction_data['bank_account_number'],
                    'state': 'unpaid',
                    'description': description
                    }
                self.pool.get('hr2.payment.register.line').create(cr, uid, values, context=context)
        if contracts_to_confirm:
            if len(contracts_to_confirm) == 1:
                param = '= %s' % contracts_to_confirm[0]
            else:
                param = 'in %s' % str(tuple(contracts_to_confirm))
            query = "UPDATE hr2_contract SET czy_rozliczona=True WHERE id " + param
            cr.execute(query)
        return True


    def create_tmp_addition_lines(self, cr, uid, payslip_id, payslip_line_ids, context=None):
        '''Metoda tworzy rekordy w tabeli tymczasowej w modelu hr2.ksiegowanie.wynagrodzen'''
        
        payslip_lines_ids = []
        
        cr.execute("SELECT id, value, addition_type, payslip_line_id FROM hr2_payslip_line_line \
                    WHERE payslip_line_id IN {}".format(ids_for_execute(payslip_line_ids)))
        
        line_line_datas = cr.dictfetchall()
        
        ksiegowanie_pool = self.pool.get('hr2.ksiegowanie.wynagrodzen')
        
        for line_line_data in line_line_datas:
            line_line_values = {
                           'payslip_id': payslip_id,
                           'payslip_line_line_id': line_line_data['id'],
                           'addition_type': line_line_data['addition_type'],
                           'value': line_line_data['value']
                           }
            
            ksiegowanie_pool.create(cr, uid, line_line_values, context=context)
            payslip_lines_ids.append(line_line_data['payslip_line_id'])
            
        
        cr.execute("SELECT id, value, addition_type FROM hr2_payslip_line \
                WHERE payslip_id={} AND id NOT IN {}".format(payslip_id,ids_for_execute(payslip_lines_ids)))
                
        line_datas = cr.dictfetchall()
        
        for line_data in line_datas:
            line_values = {
                           'payslip_id': payslip_id,
                           'payslip_line_id': line_data['id'],
                           'addition_type': line_data['addition_type'],
                           'value': line_data['value']
                           }
            
            ksiegowanie_pool.create(cr, uid, line_values, context=context)
            
        return True
 

    def post_additions_with_accounts(self, cr, uid, ids, default_vals, context=None):
        '''Funkcja księgująca po stronie debit dodatki, których typ ma konto konfiguracyjne powiązane z kontem księgowym'''
        
        posted_on_debit = 0
        
        for payslip_id in ids:
            # stworzenie rekordów w pomocniczej tabeli dla payslip.line.line
            
            payslip_line_ids = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['payslip_line_ids'], context=context)['payslip_line_ids']
            self.create_tmp_addition_lines(cr, uid, payslip_id, payslip_line_ids, context=context)
                
        cr.execute("SELECT hkw.id, hkw.value, hkw.addition_type, hca.account_id, hca.adimension1_id, hca.adimension2_id, \
                    hca.adimension3_id, hca.adimension4_id, hca.adimension5_id, hca.analytics_id \
                    FROM hr2_ksiegowanie_wynagrodzen hkw \
                    LEFT JOIN hr2_salary_addition_type hsat ON hkw.addition_type = hsat.id \
                    LEFT JOIN hr2_payslip_config_accounts hca ON hca.id = hsat.account_id \
                    WHERE hkw.payslip_id IN {} AND hsat.account_id is not null AND hca.account_id is not null".format(ids_for_execute(ids)))
        
        addition_line_datas = cr.dictfetchall()
        
        if addition_line_datas:
        
            addition_values_dict = {} # słownik z kwota do zaksiegowania
            addition_accounts_dict = {} # słownik z kontem księgowym dla danego typu dodatku
            addition_analytic_dict = {} # słownik z danymi analityki - wymiarami i dystrybucją
            ids_to_remove_after_post = []
            
            for addition_line_data in addition_line_datas: # grupowanie linii i sumowanie wartości pola value
                type = addition_line_data['addition_type']
                ids_to_remove_after_post.append(addition_line_data['id'])
                
                if type not in addition_values_dict:
                    addition_values_dict[type] = addition_line_data['value']
                    addition_accounts_dict[type] = addition_line_data['account_id']
                    addition_analytic_dict[type] = {
                                                    'adimension1_id': addition_line_data['adimension1_id'],
                                                    'adimension2_id': addition_line_data['adimension2_id'],
                                                    'adimension3_id': addition_line_data['adimension3_id'],
                                                    'adimension4_id': addition_line_data['adimension4_id'],
                                                    'adimension5_id': addition_line_data['adimension5_id'],
                                                    'analytics_id': addition_line_data['analytics_id'],
                                                    }
                else:
                    addition_values_dict[type] += addition_line_data['value']
                        
            # tworzenie pozycji zapisów dla dodatków
            for key, value in addition_values_dict.items():
                
                addition_vals = default_vals.copy()
                
                addition_vals.update({
                            'account_id': addition_accounts_dict[key],
                            'debit': value,
                            })
                
                addition_vals.update(addition_analytic_dict[key])
                    
                self.pool.get('account.move.line').create(cr, uid, addition_vals, context=context)
                posted_on_debit += value
            
            cr.execute("DELETE FROM hr2_ksiegowanie_wynagrodzen WHERE id IN {}".format(ids_for_execute(ids_to_remove_after_post)))    

        return posted_on_debit

    def open_payroll(self, cr, uid, ids, context=None):
        
        if not context: context = {}
        
        for id in ids:
            cr.execute("UPDATE hr2_payroll_register SET state='confirmed' where id=%s", (id,))
    
        return True


    def on_change_date(self, cr, uid, ids, register_month, register_year, context=None):
        ''' On change of month or year in the view returns new date of payment
            based on payment day configuration'''
        res = {'value': {}}
        if register_month not in range(1,13):
            register_month = int(time.strftime('%m'))
        if register_year < 1900:
            register_year = int(time.strftime('%Y'))
        new_date = self.last_day_of_month(register_year, register_month)
        day = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Dzień wypłaty wynagrodzeń (względem końca bieżącego miesiąca)')
        new_date += timedelta(days=day)

        #if new_date = weekend -> new_date -= 1
        while 5 <= new_date.weekday():
            new_date -= timedelta(days=1)

        #Saving to the hidden date file for use with the filters
        if register_month and register_year:
            date_computed = datetime.strptime(str(register_year) + '-' + str(register_month) + '-01', tools.DEFAULT_SERVER_DATE_FORMAT).date()
            res['value']['date_computed'] = str(date_computed)
        res['value']['date'] = str(new_date)
        res['value']['register_month'] = register_month
        res['value']['register_year'] = register_year
        return res


    def last_day_of_month(self, year, month):
        '''Returns the full date with the last day of the given month
        @param month: month provided in the register
        @param year: month provided in the register
        @return: last day of the given month
        '''
        possible_last_days = [31, 30, 29, 28, 27]
        for day in possible_last_days:
                try:
                        last_day = datetime(year, month, day)
                except ValueError:
                        continue
                else:
                        return last_day.date()
        return None


    def condition_check(self, cr, uid, ids, month, year, condition_vals, context=None):
        '''Checks which posts and contracts should be computed
        @param month: Month from the hr2.payroll.register object
        @param month: Year from the hr2.payroll.register object
        @param condition_vals: Condition values from the hr2.payroll.register.config connected to the register
        @return: res dict with ids of posts and contracts that passed the provided conditions
        '''

        res = {}
        res['post_ids'] = []
        res['contract_ids'] = []


        '''Contracts'''
        if (not condition_vals['use_contract_only'] and condition_vals['use_post_only'] == False) or condition_vals['use_contract_only']:
            res['contract_ids'] = self.get_contract_ids(cr, uid, ids, month, year, 
                                                        department=condition_vals['department'], type=condition_vals['contract_type'],
                                                        context=context)

        '''Posts'''
        if (not condition_vals['use_contract_only'] and condition_vals['use_post_only'] == False) or condition_vals['use_post_only']:
            res['post_ids'] = self.get_post_ids(cr, uid, ids, month, year, department=condition_vals['department'], context=context)
        return res


    def gather_config_data(self, cr, uid, date_planned=False, context=None):
        '''Funkcja zbiera dane z konfiguracji płacowej i tworzy z nich słownik'''
        res = {}
        cfg_pool = self.pool.get('lacan.configuration')

        '''Zebranie danych z konfiguracji'''
        res['kwota_wolna'] = cfg_pool.get_confvalue(cr, uid, 'Miesięczna kwota wolna od podatku',
                                                    data_str = date_planned, context=context)
        res['stawka_zdr_pracownik'] = cfg_pool.get_confvalue(cr, uid, 'Stawka składki zdrowotnej pracownika',
                                                             data_str = date_planned, context=context)
        res['stawka_zdr_PIT'] = cfg_pool.get_confvalue(cr, uid, 'Stawka składki zdrowotnej PIT',
                                                       data_str = date_planned, context=context)
        res['stawka_chor_pracownik'] = cfg_pool.get_confvalue(cr, uid, 'Stawka Chorobowa',
                                                              data_str = date_planned, context=context)
        res['stawka_rent_pracownik'] = cfg_pool.get_confvalue(cr, uid, 'Stawka Rentowa (Pracownik)',
                                                              data_str = date_planned, context=context)
        res['stawka_rent_pracodawca'] = cfg_pool.get_confvalue(cr, uid, 'Stawka Rentowa (Pracodawca)',
                                                               data_str = date_planned, context=context)
        res['stawka_emr_pracownik'] = cfg_pool.get_confvalue(cr, uid, 'Stawka Emerytalna (Pracownik)',
                                                             data_str = date_planned, context=context)
        res['stawka_emr_pracodawca'] = cfg_pool.get_confvalue(cr, uid, 'Stawka Emerytalna (Pracodawca)',
                                                              data_str = date_planned, context=context)
        res['ubezpieczenie_wpadkowe'] = cfg_pool.get_confvalue(cr, uid, 'Stawka Wypadkowa',
                                                               data_str = date_planned, context=context)
        res['stawka_FP'] = cfg_pool.get_confvalue(cr, uid, 'Stawka FP',
                                                  data_str = date_planned, context=context)
        res['stawka_FGSP'] = cfg_pool.get_confvalue(cr, uid, 'Stawka FGŚP',
                                                    data_str = date_planned, context=context)
        res['granica_kwoty_um_cywilpraw_do_podat_zrycz'] = cfg_pool.get_confvalue(cr, uid, 'Granica kwoty umowy cywilnoprawnej do podatku zryczaltowanego',
                                                                                  data_str = date_planned, context=context)
        res['maks_rocz_pdstwa_wymiaru_dla_ubzp_emr_i_rent'] = cfg_pool.get_confvalue(cr, uid, 'Maks. roczna podstawa wymiaru dla ubezp. emer. i rent.',
                                                                                     data_str = date_planned, context=context)
        res['stawka_podatku_ryczalt'] = cfg_pool.get_confvalue(cr, uid, 'Stawka podatku do zryczałtowanej umowy cywilnoprawnej',
                                                               data_str = date_planned, context=context)
        res['paid_sick_leave_limit'] = cfg_pool.get_confvalue(cr, uid, 'Dni zwol. lekarskiego fin. przez pracodawce ponizej granicy',
                                                              data_str = date_planned, context=context)
        res['limit_kup_50'] = cfg_pool.get_confvalue(cr, uid, 'Roczny limit kosztów uzyskania od praw autorskich',
                                                     data_str = date_planned, context=context)
        res['ograniczenie_skladki_do_wysokosci_zaliczki'] = cfg_pool.get_confvalue(cr, uid, 'Czy ograniczyć składkę zdrowotną do wysokości zaliczki PIT',
                                                                                   data_str = date_planned, context=context)
        res['liczenie_malych_umow'] = cfg_pool.get_confvalue(cr, uid, 'Specjalne liczenie małych umów cywilno-prawnych',
                                                             date_planned, context=context)
        res['koszty_uzyskania'] = cfg_pool.get_confvalue(cr, uid, 'Koszty uzyskania', date_planned,
                                                         context=context)
        res['koszty_uzyskania_podwyższone'] = cfg_pool.get_confvalue(cr, uid, 'Koszty uzyskania podwyższone', data_str = date_planned,
                                                         context=context)
        return res


    def get_contract_ids(self, cr, uid, ids, month, year, department=None, type=None, context=None):
        '''Checks which contracts need to be computed and returns their ids
        @param month - month provided in the contract
        @param year - month provided in the contract
        @param type - type of contract
        @return: list of contract ids for computing
        '''
        contract_list = []
        final_contract_list = []
        if type:
            type_list = []
            for type_id in type:
                type_list.append(type_id)
            contract_list = self.pool.get('hr2.contract').search(cr, uid, [('czy_rozliczona','!=',True), ('miesiac_rozliczenia','=',month), 
                                                                ('rok_rozliczenia','=',year), ('contract_type_id','in',type_list)], context=context)
        else:
            '''If Contract Type field is empty or the type_list is empty, the search does not check the contract type requirement'''
            contract_list = self.pool.get('hr2.contract').search(cr, uid, [('czy_rozliczona','!=',True), ('miesiac_rozliczenia','=',month),
                                                                           ('rok_rozliczenia','=',year)], context=context)

        '''
        A separate loop for the department filter, executing after the contracts have passed the first condition check and we have their list
        '''
        if len(contract_list) > 0:
            if department:
                for contract in contract_list:
                    employee_id = self.pool.get('hr2.contract').read(cr, uid, contract, ['employee_id'], context=context)['employee_id'][0]
                    if self.pool.get('hr.employee').read(cr, uid, employee_id, ['department_id'], context=context)['department_id'][0] in department:
                        final_contract_list.append(contract)
                return final_contract_list
            '''If no department has been selected, the method returns the list of contract ids fetched so far'''
        return contract_list


    def get_post_ids(self, cr, uid, ids, month, year, department=None, context=None):
        """Checks which posts need to be computed and returns their ids
        @param month - month provided in the register
        @param year - month provided in the register
        @return: list of post ids for computing
        """

        last_day_of_month = str(self.last_day_of_month(year, month))
        post_ids = self.pool.get('hr2.etat').search(cr, uid, [('sign_date', '<=', last_day_of_month)], context=context)
        register_list_ids = self.pool.get('hr2.payroll.register').search(cr, uid, [('register_year', '=', year), ('register_month', '=', month)])
        post_list = []
        for post in post_ids:
            compute = True
            discharge_date = self.pool.get('hr2.etat').read(cr, uid, post, ['discharge_date'], context=context)['discharge_date']
            if discharge_date:
                if discharge_date < str(datetime.strptime(str(year)+ '-' + str(month) + '-01', tools.DEFAULT_SERVER_DATE_FORMAT).date()):
                    continue
            for register in register_list_ids:
                '''Checking if the payslip should be computed for a given post'''
                payslip_ids = self.pool.get('hr2.payroll.register').read(cr, uid, register, ['payslip_ids'], context=context)['payslip_ids']
                for payslip in payslip_ids:
                    if not self.pool.get('hr2.payslip').read(cr, uid, payslip, ['etat_id'], context=context)['etat_id']:
                        continue
                    if post == self.pool.get('hr2.payslip').read(cr, uid, payslip, ['etat_id'], context=context)['etat_id'][0]:
                        compute = False
            if compute:
                post_list.append(post)
        '''
        A separate loop filtering the records based on their department, executing after the posts have passed the first condition check and we have their list
        If no department has been selected, the method returns the list of post ids fetched so far
        '''
        final_post_list = []
        if department:
            for post in post_list:
                employee_id = self.pool.get('hr2.etat').read(cr, uid, post, ['employee_id'],context=context)['employee_id'][0]
                if self.pool.get('hr.employee').read(cr, uid, employee_id, ['department_id'],context=context)['department_id']:
                    if self.pool.get('hr.employee').read(cr, uid, employee_id, ['department_id'],context=context)['department_id'][0] in department:
                        final_post_list.append(post)
            return final_post_list
        return post_list


    def compute_payslip_sum_this_year(self, cr, uid, employee_id, register_month, register_year, context=None):
        '''Wylicza podstawę wymiaru składek, sumę PIT oraz sumę KUP od praw autorskich i  zwraca ich wartości
        @param type: Defines if obj_id stands for contract or post ('e' or 'c')
        @param obj_id: contract or post id, depending on the type parameter
        @param register_month: month entered in the register
        @param register_year: year entered in the register
        @return: "podstawa_wymiaru_skladek" - "podstawa wymiaru składek od początku roku"
                 "suma_kup_50" - "suma KUP z praw autorskich od początku roku"
                 "suma_PIT" - "suma PIT od początku roku"
        '''
        value = 0
        values = {}
        koszty_uzyskania_50 = 0
        kwota_zaliczki_PIT = 0

        '''Fetching payslips depending on the object type (contract or post)'''
        payslip_list = self.pool.get('hr2.payslip').search(cr, uid, [('register_id.register_year', '=', register_year),
                                                                     ('register_id.register_month', '<=', register_month),
                                                                     ('employee_id', '=', employee_id),
                                                                    ], context=context)
        '''Fetching data from payslips'''
        if payslip_list:
            for payslip in payslip_list:
                sumy = self.pool.get('hr2.payslip').read(cr, uid, payslip, ['value3', 'koszty_uzyskania_autorskie','dochod'], context=context)
                koszty_uzyskania_50 += sumy['koszty_uzyskania_autorskie']
                value += sumy['value3']
                kwota_zaliczki_PIT += sumy['dochod']
        '''Fetching data from other employers'''
        other_zus_base = self.pool.get('hr2.etat.zus.base').search(cr,uid, [('employee_id', '=', employee_id), ('year', '=', register_year), ('month', '<=', register_month)], context=context)
        for data in other_zus_base:
            value += self.pool.get('hr2.etat.zus.base').read(cr, uid, data, ['amount'], context=context)['amount']
        values['podstawa_wymiaru_skladek'] = value
        values['suma_kup_50'] = koszty_uzyskania_50
        values['suma_PIT'] = kwota_zaliczki_PIT
        return values


    def compute_koszt_uzyskania_przychodu(self, cr, uid, typ, obj_id, conf, context=None):
        """Tworzy listę z konfiguracją obliczania kosztów uzyskania przychodów dla danego kontraktu lub etatu
        @param typ: Defines if obj_id stands for contract or post ('e' or 'c')
        @param obj_id: contract or post id, depending on the type parameter
        Return:
        lista zawierająca informacje o kosztach uzyskania przychodu - float
        pierwszy element zawiera informacje o procencie pensji objętej kosztami liniowymi w postaci ułamka dziesiętnego
        drugi kwote kosztu uzyskania liniowego
        trzeci procent uzyskania kosztów w postaci ułamka dziesiętnego
        """
        koszt_uzyskania = 0.0
        procent_pensji = 1.0
        procent_uzyskania = 0.0
        cfg_pool = self.pool.get('lacan.configuration')

        if typ == 'c':
            procent_pensji = self.pool.get('hr2.contract').read(cr, uid, obj_id, ['wynagrodzenie_z_procentowym_kosztem'],
                                                                context=context)['wynagrodzenie_z_procentowym_kosztem']
            procent_pensji /= 100
            procent_uzyskania = self.pool.get('hr2.contract').read(cr, uid, obj_id, ['procent_uzyskania'], context=context)['procent_uzyskania']
            procent_uzyskania /= 100
            koszt_uzyskania_select = self.pool.get('hr2.contract').read(cr, uid, obj_id, ['koszty_uzyskania'], context=context)['koszty_uzyskania']
            if koszt_uzyskania_select == 'standardowe':
                koszt_uzyskania = conf['koszty_uzyskania']
            elif koszt_uzyskania_select == 'podwyzszone':
                koszt_uzyskania = conf['koszty_uzyskania_podwyższone']
            elif koszt_uzyskania_select == 'inne':
                koszt_uzyskania = self.pool.get('hr2.contract').read(cr, uid, obj_id, ['inne_koszty'], context=context)['inne_koszty']
        elif typ =='e':
            procent_pensji = self.pool.get('hr2.etat').read(cr, uid, obj_id, ['wynagrodzenie_z_procentowym_kosztem'],
                                                            context=context)['wynagrodzenie_z_procentowym_kosztem']
            procent_pensji /= 100
            procent_uzyskania = self.pool.get('hr2.etat').read(cr, uid, obj_id, ['procent_uzyskania'], context=context)['procent_uzyskania']
            procent_uzyskania /= 100
            koszt_uzyskania_select = self.pool.get('hr2.etat').read(cr, uid, obj_id, ['koszty_uzyskania'], context=context)['koszty_uzyskania']
            if koszt_uzyskania_select == 'standardowe':
                koszt_uzyskania = conf['koszty_uzyskania']
            elif koszt_uzyskania_select == 'podwyzszone':
                koszt_uzyskania = conf['koszty_uzyskania_podwyższone']
            elif koszt_uzyskania_select == 'inne':
                koszt_uzyskania = self.pool.get('hr2.etat').read(cr, uid, obj_id, ['inne_koszty'], context=context)['inne_koszty']
        koszt_uzyskania_laczny = [lacan_round(1.0 - procent_pensji, 2), koszt_uzyskania, procent_uzyskania]
        return koszt_uzyskania_laczny


    def gather_payslip_data(self, cr, uid, payslip_id, type, worktime_type_id, absence_type_id, addition_type_id, sick_leave_types, context=None):
        """Pulls values from the database necessary for computing salary
        @param payslip_id: Self-explanatory
        @return: dictionary with values prepared for the calculate_elements method
        """
        data_dict = {}
        holidays_payment_sum = 0
        total_absence_days = 0
        additions_payment_sum = 0
        value3_sum = 0
        sick_pay_sum = 0
        sick_benefit_sum = 0
        sick_pay_sum_without_kup = 0
        sick_benefit_sum_without_kup = 0
        ekwiwalent_sum = 0
        swiadczenie_sum =0
        additions = []

        sick_leave_ids = []
        for leave_type in sick_leave_types:
            sick_leave_ids.append(self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', leave_type)[1])
        child_care_types = ['hr2_payslip_line_type_child_care', 'hr2_payslip_line_type_sick_benefit']
        child_care_ids = []
        for child_care_type in child_care_types:
            child_care_ids.append(self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', child_care_type)[1])
        '''Obliczenia kontraktów'''
        if type == 'c':
            contract_value_id = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','=',worktime_type_id)],
                                                                         context=context)[0]
            value3_sum = self.pool.get('hr2.payslip.line').read(cr, uid, contract_value_id, ['value'], context=context)['value']
            additions_lines_ids = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','=',addition_type_id)],
                                                                           context=context)
            additions_lines = self.pool.get('hr2.payslip.line').browse(cr, uid, additions_lines_ids, context=context)
            for addition_line in additions_lines:
                if addition_line.addition_type.application == 'ekwiwalent':
                    ekwiwalent_sum += addition_line.value
                    continue
                elif addition_line.addition_type.application == 'swiadczenie':
                    swiadczenie_sum += addition_line.value
                    continue
                addition = {'value': addition_line.value, 'code': addition_line.addition_type.code,
                            'licz_kup_jak_podstawa': addition_line.addition_type.licz_kup_jak_podstawa}
                additions.append(addition)
                additions_payment_sum += addition['value']
            data_dict['additions'] = additions
            data_dict['additions_payment'] = additions_payment_sum
            data_dict['holidays_payment'] = holidays_payment_sum
            data_dict['total_absence_days'] = total_absence_days
            data_dict['value3'] = value3_sum
            data_dict['sick_pay'] = sick_pay_sum
            data_dict['sick_benefit'] = sick_benefit_sum
            data_dict['ekwiwalent'] = ekwiwalent_sum
            data_dict['bonus'] = swiadczenie_sum
            return data_dict

        '''Dodatki należne za czas nieobecności dla etatów'''
        additions = []
        additions_lines_ids = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','=',addition_type_id)],
                                                                       context=context)
        additions_lines = self.pool.get('hr2.payslip.line').browse(cr, uid, additions_lines_ids, context=context)
        etat_id = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['etat_id'], context=context)['etat_id'][0]
        etat_dict = self.pool.get('hr2.etat').read(cr, uid, etat_id, ['inne_koszty','wynagrodzenie_z_procentowym_kosztem'], context=context)
        for addition_line in additions_lines:
            if addition_line.addition_type.application == 'ekwiwalent':
                ekwiwalent_sum += addition_line.value
                continue
            elif addition_line.addition_type.application == 'swiadczenie':
                swiadczenie_sum += addition_line.value
                continue
            addition = {'value': addition_line.value, 'code': addition_line.addition_type.code,
                            'licz_kup_jak_podstawa': addition_line.addition_type.licz_kup_jak_podstawa,
                            'etat': etat_dict }
            additions.append(addition)
            additions_payment_sum += addition['value']
        '''Zbieram i dekomponuję wartości wynagrodzeń z różnych składników dla każdego okresu'''
        value3_lines_worktime = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','=',worktime_type_id)],
                                                                         context=context)
        for line_id in value3_lines_worktime:
            period_start = self.pool.get('hr2.payslip.line').read(cr,uid,line_id,['date_start'])['date_start']
            period_stop = self.pool.get('hr2.payslip.line').read(cr,uid,line_id,['date_stop'])['date_stop']

            '''Wynagrodzenie za czas przepracowany'''
            value3 = self.pool.get('hr2.payslip.line').read(cr,uid,line_id,['value'])['value']

            '''Wynagrodzenie urlopowe'''
            holidays_payment = 0
            absence_lines = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','=',absence_type_id),
                                                                               ('date_start','>=',period_start),('date_stop','<=',period_stop)],
                                                                     context=context)
            for absence_line_id in absence_lines:
                holidays_payment += self.pool.get('hr2.payslip.line').read(cr, uid, absence_line_id, ['value'],context=context)['value']
                total_absence_days += self.pool.get('hr2.payslip.line').read(cr, uid, absence_line_id, ['number_of_days'],
                                                                             context=context)['number_of_days']

            '''Wynagrodzenie chorobowe'''
            sick_pay = 0
            sick_lines = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','in',sick_leave_ids),
                                                                            ('date_start','>=',period_start),('date_stop','<=',period_stop)],
                                                                  context=context)
            for sick_line in sick_lines:
                val_s = self.pool.get('hr2.payslip.line').read(cr, uid, sick_line, ['value'], context=context)['value']
                sick_pay += val_s
                if not self.pool.get('hr2.payslip.line').read(cr, uid, sick_line, ['licz_KUP_jak_podstawa'], context=context)['licz_KUP_jak_podstawa']:
                    sick_pay_sum_without_kup += val_s

            '''Zasiłek chorobowy'''
            sick_benefit = 0
            child_care_lines = self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id),('type_id','in',child_care_ids),
                                                                                  ('date_start','>=',period_start),('date_stop','<=',period_stop)],
                                                                        context=context)
            for child_care in child_care_lines:
                val_b = self.pool.get('hr2.payslip.line').read(cr, uid, child_care, ['value'],context=context)['value']
                sick_benefit += val_b
                if not self.pool.get('hr2.payslip.line').read(cr, uid, child_care, ['licz_KUP_jak_podstawa'],context = context)['licz_KUP_jak_podstawa']:
                    sick_pay_sum_without_kup += val_b

            '''Dekompozycja kwoty za czas przepracowany w celu uzyskania faktycznej wartości dodatków nienależnych za czas nieobecności i kwoty za prace'''
            work_time_line_line_id = self.pool.get('hr2.payslip.line.line').search(cr, uid, [('payslip_line_id','=',line_id),
                                                                                           ('type','=','work_time')], context=context)[0]
            work_time_value = self.pool.get('hr2.payslip.line.line').read(cr, uid, work_time_line_line_id, ['value'], context=context)['value']
            DNZCN_ids = self.pool.get('hr2.payslip.line.line').search(cr, uid, [('payslip_line_id','=',line_id),('type','=','addition')],
                                                                      context=context)
            DNZCNvalue = 0
            additions_payment = 0
            for addition in DNZCN_ids:
                DNZCNvalue += self.pool.get('hr2.payslip.line.line').read(cr, uid, addition, ['value'], context=context)['value']
            newDNZCNvalue = value3 * DNZCNvalue / (DNZCNvalue+work_time_value)
            for addition_id in DNZCN_ids:
                addition = {}
                addition['value'] = self.pool.get('hr2.payslip.line.line').read(cr, uid, addition_id, ['value'], context=context)['value']
                addition['value'] = addition['value'] * newDNZCNvalue / DNZCNvalue
                addition_type_id = self.pool.get('hr2.payslip.line.line').read(cr, uid, addition_id, ['addition_type'],
                                                                               context=context)['addition_type'][0]
                addition_type = self.pool.get('hr2.salary.addition.type').read(cr, uid, addition_type_id, ['code', 'licz_kup_jak_podstawa'],
                                                                               context=context)
                addition['code'] = addition_type['code']
                addition['licz_kup_jak_podstawa'] = addition_type['licz_kup_jak_podstawa']
                additions.append(addition)
                additions_payment += addition['value']
            value3 -= newDNZCNvalue

            '''Dodawanie wartości z pojedyńczych okresów do sumy payslipa'''
            holidays_payment_sum += holidays_payment
            additions_payment_sum += additions_payment
            value3_sum += value3
            sick_pay_sum += sick_pay
            sick_benefit_sum += sick_benefit

        data_dict['additions'] = additions
        data_dict['additions_payment'] = additions_payment_sum
        data_dict['holidays_payment'] = holidays_payment_sum
        data_dict['total_absence_days'] = total_absence_days
        data_dict['value3'] = value3_sum
        data_dict['sick_pay'] = sick_pay_sum
        data_dict['sick_benefit'] = sick_benefit_sum
        data_dict['sick_pay_without_kup'] = sick_pay_sum_without_kup
        data_dict['sick_benefit_without_kup'] = sick_benefit_sum_without_kup
        data_dict['ekwiwalent'] = ekwiwalent_sum
        data_dict['bonus'] = swiadczenie_sum
        return data_dict


    def create_payslip_line(self, cr, uid, elements, payslip_id, addition_dict_list=[], periods=[], context=None):
        '''
        ###Value3 - Wartość za czas przepracowany
        ###Value2 - Wszystkie dodatki
        '''

        number = 1
        line_number = 2
        
        line_line_pool = self.pool.get('hr2.payslip.line.line')

        '''Post'''
        if elements['contract_type'] == 'e':
            if elements.get('work_time_list'):
                for data in elements['work_time_list']:
                    base_without_additions_scaled = data.pop('base_without_additions_scaled')
                    base_without_additions = data.pop('base_without_additions')
                    vals = {'payslip_id': payslip_id,
                            'register_id': data['register_id'],
                            'type_id':self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl',
                                                                            'hr2_payslip_line_type_work_time')[1],
                            'number': number, 
                            'base': data['base'], 
                            'value': data['value3'],
                            'date_start': data['date_start'], 
                            'date_stop': data['date_stop'],
                            'number_of_days': data.get('number_of_days')}
                    # vals['name'] = data['name']
                    number += 1

                    line_id = self.pool.get('hr2.payslip.line').create(cr, uid, vals, context=context)
                    #Tworzę dodatki do czasu pracy
                    for addition in addition_dict_list:
                        if addition['etat_data_id'] == data['etat_data_id']:
                            addition.pop('etat_data_id')
                            line_vals = addition
                            line_vals['payslip_line_id'] = line_id
                            line_vals['number'] = line_number
                            line_vals['name'] = _('Addition')
                            line_vals['type'] = 'addition'
                            addition_line_line_id = line_line_pool.create(cr, uid, line_vals, context=context)
                            line_number += 1

                    value_after_deduction = data['value1']
                    for deduction in data['deduction_list']:
                        line_vals = {}
                        line_vals['number'] = line_number
                        line_vals['payslip_line_id'] = line_id                        
                        if value_after_deduction > deduction['value']:
                            line_vals['value'] = -deduction['value']
                            value_after_deduction -= line_vals['value']
                        else:
                            line_vals['value'] = -value_after_deduction
                            value_after_deduction = 0
                        line_vals['name'] = 'Pomniejszenie'
                        line_vals['hours'] = deduction.get('hours')
                        line_number+=1
                        line_line_id = line_line_pool.create(cr, uid, line_vals, context=context)

                    base_line_id = line_line_pool.create(cr, uid, {'value': base_without_additions_scaled,
                                                                    'base': base_without_additions,
                                                                    'payslip_line_id': line_id,
                                                                    'number': 1,
                                                                    'hours': data.get('hours'),
                                                                    'name': _('Working time'),
                                                                    'type': 'work_time'}, context=context)

                    '''Overtime'''
                    payslip = self.pool.get('hr2.payslip').browse(cr, uid, payslip_id, context=context)
                    emp = payslip.employee_id
                    reg_dict = self.read(cr, uid, context['register_id'], ['register_month','register_year'])
                    month = reg_dict['register_month']
                    year = reg_dict['register_year']
                    overtime_res = {}
                    
                    if periods:
                        overtime_res = self.count_overtime_hours(cr, uid, line_id, emp.id, periods, number, context=context)
                
                    if overtime_res:
                        number += 1
                        if not payslip.etat_id.per_hour:
                            base_vals = line_line_pool.read(cr, uid, base_line_id, ['hours', 'value'])
                            hours = base_vals['hours']
                            val = hours*base_vals['value']/(hours - overtime_res['overtime'])
                            base_line_new_vals = { 
                                                  'value': val,
                                                  'base': val
                                                  } 
                            line_line_pool.write(cr, uid, base_line_id, base_line_new_vals)
            
            '''Contract'''
        elif elements['contract_type'] == 'c':
            if not elements['date_stop']:
                employee_id = self.pool.get('hr2.payslip').browse(cr, uid, payslip_id, context=context).employee_id.name
                raise osv.except_osv(_('Błąd!'),_('Brak daty końca umowy cywilnoprawnej dla pracownika ' + str(employee_id) + '.'))

            vals = {}
            vals['payslip_id'] = payslip_id
            vals['register_id'] = elements['register_id'],
            vals['type_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_work_time')[1]
            vals['number'] = number
            # vals['name'] = 'Umowa cywilnoprawna'
            vals['value'] = elements['value']
            vals['base'] = elements['base']
            vals['date_start'] = elements['date_start']
            vals['date_stop'] = elements['date_stop']
            # vals['number_of_days'] = data.get('number_of_days')
            number += 1

            line_id = self.pool.get('hr2.payslip.line').create(cr, uid, vals, context=context)

        '''Absences'''
        if elements.get('absences_list'):

            for absence in elements['absences_list']:
                vals = {}
                vals['payslip_id'] = payslip_id
                vals['type_id'] = absence['type_id']
                vals['absence_id'] = absence['absence_id']
                vals['number'] = number
                vals['base'] = absence.get('base')
                vals['value'] = absence['value']
                vals['number_of_days'] = absence['days']
                vals['date_start'] = absence['date_from']
                vals['date_stop'] = absence['date_to']
                vals['wymaga_korekty'] = absence.get('wymaga_korekty', False)
                vals['licz_KUP_jak_podstawa'] = absence.get('kup', False)
                number+=1

                line_id = self.pool.get('hr2.payslip.line').create(cr, uid, vals, context=context)

        return payslip_id

    def uzupelnienie_pensji(self, cr, uid, payslip_data, post, payslip_id,
                            year, month, wymiar_pracy, employee_id, context=None):
        """ Metoda sprawdzająca czy pracownik nie otrzymuje wynagrodzenia niższego
            niż minimalne i uzupełniająca wynagrodzenie do pensji minimalnej. """

        # Zebranie danych do obliczen.
        first_day_of_month = str(datetime.strptime(str(year) + '-' + str(month) + '-01', "%Y-%m-%d").date())
        etat_data = self.pool.get('hr2.etat').read(cr, uid, post, ['sign_date', 'discharge_date'], context=context)
        sign_date = etat_data['sign_date']
        discharge_date = etat_data['discharge_date']
        last_day_of_month = str(self.last_day_of_month(year, int(month)))
        last_day_to_check = min(discharge_date, last_day_of_month) if discharge_date else last_day_of_month

        # Obliczanie pensji minimalnej dla danego pracownika z uwzględnieniem nieobecności.
        godz_do_przepracowania = self.work_time_hours(cr, uid, employee_id, first_day_of_month, first_day_of_month,
                                                      last_day_of_month, ['multiple', 'working', 'absence'])
        if godz_do_przepracowania > 0:
            pensja_minimalna_na_caly_etat = self.pool.get(
                'hr.employee').get_pensja_minimalna(cr, uid, employee_id, month, year)
            godz_przepracowane = self.work_time_hours(cr, uid, employee_id, sign_date, first_day_of_month,
                                                      last_day_to_check, ['multiple', 'working'], search_type='filled')
            pensja_minimalna = pensja_minimalna_na_caly_etat * wymiar_pracy * godz_przepracowane/godz_do_przepracowania
            pensja_minimalna = lacan_round(pensja_minimalna, 2)
        else:
            pensja_minimalna = 0.00

        pensja = sum([payslip_data['value3'], payslip_data['holidays_payment'],
                      payslip_data['additions_payment'], payslip_data['sick_pay']])

        # Oblicz brakująca część i stwórz uzupełnienie.
        if pensja < pensja_minimalna:
            model_pool = self.pool.get('ir.model.data')
            do_uzupelnienia = pensja_minimalna - pensja
            self.pool.get('hr2.payslip.line').create(cr, uid, {
                'payslip_id': payslip_id,
                'number': 0,
                'licz_KUP_jak_podstawa': True,
                'base': do_uzupelnienia,
                'value': do_uzupelnienia,
                'date_start': last_day_to_check,
                'date_stop': last_day_to_check,
                'type_id': model_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_payslip_line_type_supplement')[1],
                'addition_type': model_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'hr2_salary_addition_type_supplement')[1],
            }, context=context)

            payslip_data['value3'] += do_uzupelnienia   # Dodanie uzupełnienia do listy payslip_data.
        return payslip_data


    def compute_deductions_config(self, cr, uid, employee_id, typ, register_date, wymiar_pracy=1, context=None):
        deductions_config = {}
        deductions_config['deductions']=[]
        if typ == 'e':
            deductions_id = self.pool.get('hr2.salary.deduction').search(cr,uid,[('employee_id','=',employee_id),
                                                                                 ('execution_date_start','<=',register_date),'|',
                                                                                 ('execution_date_stop','>',register_date),
                                                                                 ('execution_date_stop','=',False)],
                                                                         order = 'priority', context=context)
            deductions = self.pool.get('hr2.salary.deduction').browse(cr, uid, deductions_id, context=context)
            for deduction in deductions:
                special1_code_list = []
                special2_code_list = []
                kod = deduction['number']
                type_code = deduction.deduction_type.deduction_computation_type_id.id
                if deduction.amount_type:
                    kwota = deduction['amount']
                else:
                    kwota = deduction['amount'] - deduction['amount_paid']
                '''wartości domyślne'''
                minimalna_pensja = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Minimalna pensja netto', 
                                                                                      data_str = context.get('employee_list_date', False),
                                                                                      context=context)
                kwota_wolna = deduction.deduction_type.deduction_computation_type_id.amount_free * minimalna_pensja * wymiar_pracy / 100
                procent_egzekucji = deduction.deduction_type.deduction_computation_type_id.percent_normal / 100
                '''wartości specjalne'''
                special1_procent_egzekucji = deduction.deduction_type.deduction_computation_type_id.percent_special_1
                for addition in deduction.deduction_type.deduction_computation_type_id.special_1_additions:
                    special1_code_list.append(addition.code)
                special2_procent_egzekucji = deduction.deduction_type.deduction_computation_type_id.percent_special_2
                for addition in deduction.deduction_type.deduction_computation_type_id.special_2_additions:
                    special2_code_list.append(addition.code)
                '''wartości dla zasiłków'''
                procent_zus = deduction.deduction_type.deduction_computation_type_id.percent_ZUS
                minimalna_emerytura = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Minimalna emerytura netto',
                                                                                         data_str = context.get('employee_list_date', False),
                                                                                         context=context)
                kwota_wolna_zus = deduction.deduction_type.deduction_computation_type_id.percent_ZUS_free * minimalna_emerytura * wymiar_pracy / 100
                deductions_config['deductions'].append({'%egzekucji': procent_egzekucji,
                                                        'type_code': type_code,
                                                        'code': kod,
                                                        'kwota': kwota,
                                                        'kwota_wolna': kwota_wolna,
                                                        '%special1': special1_procent_egzekucji,
                                                        '%special2': special2_procent_egzekucji,
                                                        'special1_code_list': special1_code_list,
                                                        'special2_code_list': special2_code_list,
                                                        '%zus': procent_zus,
                                                        'kwota_wolna_zus': kwota_wolna_zus})
        elif typ == 'c':
            deductions_id = self.pool.get('hr2.salary.deduction').search(cr,uid,[('employee_id','=',employee_id),
                                                                                 ('execution_date_start','<=',register_date),'|',
                                                                                 ('execution_date_stop','>',register_date),
                                                                                 ('execution_date_stop','=',False),
                                                                                 ('execution_from_contracts','=',True)],
                                                                         order = 'priority', context=context)
            deductions = self.pool.get('hr2.salary.deduction').browse(cr, uid, deductions_id, context=context)
            for deduction in deductions:
                kod = deduction['number']
                type_code = deduction.deduction_type.deduction_computation_type_id.id
                if deduction.amount_type:
                    kwota = deduction['amount']
                else:
                    kwota = deduction['amount'] - deduction['amount_paid']
                kwota_wolna = 0
                procent_egzekucji = 1
                if deduction['execution_from_contracts_restrictions'] == 'wolny_procent':
                    procent_egzekucji = deduction['contracts_restrictions_value'] / 100
                elif deduction['execution_from_contracts_restrictions'] == 'wolna_kwota':
                    kwota_wolna = deduction['contracts_restrictions_value']

                deductions_config['deductions'].append({'%egzekucji': procent_egzekucji,
                                                        'code': kod,
                                                        'type_code': type_code,
                                                        'kwota': kwota,
                                                        'kwota_wolna': kwota_wolna})
        deductions_config['alimenty_code']=self.pool.get('hr2.salary.deduction.computation.type').search(cr, uid,
                                                                                                         [('name','=','Grupa potrąceń alimentacyjnych')])[0]
        deductions_config['kara_code']=self.pool.get('hr2.salary.deduction.computation.type').search(cr, uid,
                                                                                                     [('name','=','Grupa finansowych kar porządkowych')])[0]
        deductions_config['typ'] = typ
        return deductions_config


    def get_contract_dates(self, cr, uid, register_month, register_year, contract_start, contract_stop, context=None):
        dates={}
        ostatni_dzien_roboczy = self.last_day_of_month(register_year, register_month)
        poczatek_miesiaca_rozliczenia = str(date(register_year, register_month, 1))
        koniec_miesiaca_rozliczenia = str(ostatni_dzien_roboczy)

        while True:
            if ostatni_dzien_roboczy.weekday() in range(5):
                break
            ostatni_dzien_roboczy -= timedelta(days = 1)

        if not contract_stop:
            contract_stop = str(ostatni_dzien_roboczy)

        if (poczatek_miesiaca_rozliczenia > contract_stop) | (koniec_miesiaca_rozliczenia < contract_start):
            dates['date_start'] = dates['date_stop'] = ostatni_dzien_roboczy
        elif poczatek_miesiaca_rozliczenia >= contract_start:
            dates['date_start'] = poczatek_miesiaca_rozliczenia
            if koniec_miesiaca_rozliczenia < contract_stop:
                dates['date_stop'] = ostatni_dzien_roboczy
            else:
                dates['date_stop'] = contract_stop
        elif poczatek_miesiaca_rozliczenia < contract_start:
            dates['date_start'] = contract_start
            if koniec_miesiaca_rozliczenia < contract_stop:
                dates['date_stop'] = ostatni_dzien_roboczy
            else:
                dates['date_stop'] = contract_stop
        return dates

    def calculate_elements_contract(self, cr, uid, contract, payslip_id, context=None):
        '''Generates data necessary for updating the hr2.payslip object for a given contract
        @param contract: ID of hr2.contract object
        @return: value dictionary'''
        register_id = context.get('register_id')
        self.write(cr, uid, register_id, {'state':'elements'}, context=context)
        register_vals = self.pool.get('hr2.payroll.register').read(cr, uid, register_id,
                                                                   ['register_year', 'register_month', 'process_prev_month'],
                                                                   context=context)


        vals = self.pool.get('hr2.contract').read(cr,uid,contract,
                                                  ['month_pay', 'employee_id', 'calculate_fp', 'calculate_fgsp', 'calculate_emr', 'date_start', 
                                                   'date_to', 'calculate_rent', 'calculate_chor', 'calculate_wyp', 'rozliczac_kwote_wolna'],
                                                  context=context)
        '''Computing the salary elements'''
        elements = self.compute_elements_contract(cr, uid, vals['month_pay'],)

        contract_dates = self.get_contract_dates(cr, uid, register_vals['register_month'], register_vals['register_year'],
                                                 vals['date_start'], vals['date_to'], context=context)
        elements['date_start'] = contract_dates['date_start']
        elements['date_stop'] = contract_dates['date_stop']
        elements['register_id'] = register_id
        '''Creating payslip lines'''
        self.create_payslip_line(cr, uid, elements, payslip_id, context=context)
        return True


    def calculate_elements_post(self, cr, uid, post, payslip_id, periods, is_january, context=None):
        """Generates data necessary for calculating elements the hr2.payslip object for a given post
        @param post: ID of hr2.etat object
        @param hardcoded_params: temporary hardcoded parameters (present until everything is fetched from the database
        @return: value dictionary"""
        register_id = context.get('register_id')
        self.write(cr, uid, register_id, {'state':'elements'}, context=context)
        register_vals = self.pool.get('hr2.payroll.register').read(cr, uid, register_id,
                                                                   ['id','register_year', 'register_month', 'process_prev_month', 'date'],
                                                                   context=context)
        year = register_vals['register_year']
        month = register_vals['register_month']
        payment_date = register_vals['date']
        vals = self.pool.get('hr2.etat').read(cr,uid,post, ['month_pay','per_hour','work_time','employee_id'], context=context)

        if not self.pool.get('hr2.etat.data').search(cr, uid, [('etat_id', '=', vals['id']), ('date_from', '<=', payment_date)],
                                                     order='date_from desc', context=context):
            raise osv.except_osv('Błąd!', 'Brak historii zatrudnienia dla pracownika ' + str(vals['employee_id'][1]) + '.')

        actual_etat_data_id = self.pool.get('hr2.etat.data').search(cr, uid, [('etat_id', '=', vals['id']), ('date_from', '<=', payment_date)],
                                                                    order='date_from desc', context=context)[0]
        actual_etat_data = self.pool.get('hr2.etat.data').read(cr, uid, actual_etat_data_id,
                                                               ['calculate_fp', 'calculate_fgsp', 'calculate_emr', 'calculate_rent', 'calculate_chor',
                                                                'calculate_wyp', 'rozliczac_kwote_wolna'], context=context)
        vals.update(actual_etat_data)

        paid_sick_leave_limit = self.get_paid_sick_leave_limit(cr, uid, vals['employee_id'][0], context=context)

        additions = 0
        additions_id=self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id)], context=context)
        for id in additions_id:
            cr.execute("UPDATE hr2_payslip_line SET register_id = %s WHERE id = %s", (register_vals['id'], id))
            additions += self.pool.get('hr2.payslip.line').read(cr, uid, id, ['value'], context=context)['value']

        sick_days_this_year = self.get_sick_days_so_far(cr, uid, vals['employee_id'][0], year, month, context=None)

        context['hours_work'] = {'work_time':vals['work_time'], 'per_hour':vals['per_hour']}
        context['payslip_id'] = payslip_id

        '''Computing the salary elements'''
        elements = self.calculate_elements(cr, uid,
                                            'e', #char - etat/cywilnoprawna (e/c)
                                            vals['month_pay'],
                                            post,
                                            register_vals,
                                            #Absences
                                            sick_days_this_year,
                                            paid_sick_leave_limit,
                                            hardcoded_params['czy_zwolnienie_nieprzerwanie_od_90_dni_kalendarzowych'],
                                            hardcoded_params['czy_posiada_ubezpieczenie_chorobowe'],
                                            #Uzywane dane ZUS/PIT
                                            vals['calculate_chor'], #bool
                                            is_january, #bool
                                            context=context,
                                            )
        # correction_list = elements.get('correction_list')
        addition_dict_list = elements['addition_dict_list']
        '''Creating payslip lines'''
        self.create_payslip_line(cr, uid, elements, payslip_id, addition_dict_list=addition_dict_list, periods=periods, context=context)

        # Wizard do wyświetlenia informacji o konieczności korekty. Zakomentowane, chwilowo w systemie funkcjonuje tylko raise
        # przy próbie wyliczenia podatków.

        # if correction_list:
        #     res = mod_obj.get_object_reference(cr, uid, 'hr_payroll_pl', 'wizard_correct_payslip_form')
        #     res_id = res and res[1] or False
        #     ctx = context.copy()
        #     return {
        #        'name': _('Correct payslips'),
        #        'view_type': 'form',
        #        'view_id': res_id,
        #        'context': ctx,
        #        'view_mode': 'form',
        #        'res_model': 'wizard.correct.payslip',
        #        'type': 'ir.actions.act_window',
        #        'target': 'new',
        #        }
        # else:
        return True

    def get_paid_sick_leave_limit(self, cr, uid, employee_id, context=None):
        """ Metoda sprawdza czy pracownik przekroczył wiek graniczny powyżej którego pracodawca finansuje
            mniejszą ilość dni zwolnienia chorobowego czy nie, po czym zwraca odpowiednią ilość dni.
            @param employee_id: ID pracownika.
            @return: int, liczba dni zwolnienia chorobowego, które finansuje pracodawca. """
        conf_pool = self.pool.get('lacan.configuration')
        employee_pool = self.pool.get('hr.employee')

        list_date = context.get('employee_list_date') or datetime.strftime(datetime.now().date(),
                                                                           tools.DEFAULT_SERVER_DATETIME_FORMAT)
        now_date = datetime.strptime(list_date, tools.DEFAULT_SERVER_DATE_FORMAT)
        birthday = employee_pool.read(cr, uid, employee_id, ['birthday'], context=context)['birthday']
        if not birthday:
            employee_name = employee_pool.read(cr, uid, employee_id, ['name'], context=context)['name']
            raise osv.except_osv('Błąd!', 'Pracownik {e} nie ma wypełnionej daty urodzenia.'.format(e=employee_name))
        else:
            birthday = datetime.strptime(birthday, tools.DEFAULT_SERVER_DATE_FORMAT)

            age_limit = conf_pool.get_confvalue(cr, uid, 'Wiek granicy ilosci dni zwol. lekarskiego fin. przez pracodawce',
                                                data_str=list_date, context=context)

            # Po przekroczeniu X lat pracodawca finansuje mniejszą ilość dni od rozpoczęcia następnego roku kalendarzowego.
            if now_date.year > (birthday.year + age_limit):
                conf = 'Dni zwol. lekarskiego fin. przez pracodawce powyzej granicy'
            else:
                conf = 'Dni zwol. lekarskiego fin. przez pracodawce ponizej granicy'
        return conf_pool.get_confvalue(cr, uid, conf, data_str=list_date, context=context)


    def update_payslip_for_contract(self, cr, uid, contract, payslip_id, worktime_type_id, absence_type_id, addition_type_id, sick_leave_types,
                                    conf, context=None):
        """Generates data necessary for updating the hr2.payslip object for a given contract
        @param contract: ID of hr2.contract object
        @param hardcoded_params: temporarily hardcoded parameters (present until everything is fetched from the database)
        @return: value dictionary"""
        register_id = context.get('register_id')
        register_vals = self.pool.get('hr2.payroll.register').read(cr, uid, register_id, ['register_year', 'register_month', 'process_prev_month', 'date'],
                                                                   context=context)
        year = register_vals['register_year']
        month = register_vals['register_month']
        register_date = register_vals['date']

        vals = self.pool.get('hr2.contract').read(cr,uid,contract, ['month_pay', 'employee_id', 'calculate_fp', 'calculate_fgsp', 'calculate_emr',
                                                                    'calculate_rent', 'calculate_chor', 'calculate_wyp', 'rozliczac_kwote_wolna',
                                                                    'calculate_zdr', 'contract_type_id'], context=context)
        deductions_config = self.compute_deductions_config(cr, uid, vals['employee_id'][0], 'c', register_date, context=context)
        compute_payslip_sum_wynik = self.compute_payslip_sum_this_year(cr, uid, vals['employee_id'][0], register_vals['register_month'],
                                                                       register_vals['register_year'], context=context)
        podstawa_wymiaru_skladek_od_pocz_roku = compute_payslip_sum_wynik['podstawa_wymiaru_skladek']
        PIT_income_since_start_of_year = compute_payslip_sum_wynik['suma_PIT']

        suma_kup_50_ten_rok = compute_payslip_sum_wynik['suma_kup_50']
        tax_deduction = self.compute_koszt_uzyskania_przychodu(cr, uid, 'c', contract, conf, context=context)
        podatek = self.pool.get('hr2.contract').read(cr, uid, contract, ['procent_zaliczki_PIT'], context=context)
        tax_scale = [[0, podatek['procent_zaliczki_PIT']]]
        
        '''Gathering data'''
        elements = self.gather_payslip_data(cr, uid, payslip_id, 'c', worktime_type_id, absence_type_id, addition_type_id, sick_leave_types,
                                            context=context)
        sick_days_so_far = self.get_sick_days_so_far(cr, uid, vals['employee_id'][0], year, month, context=None)
        is_not_resident = self.is_not_resident(cr, uid, vals['contract_type_id'][0], context=None)

        # Sprawdź czy są dodatki obciążone przez ZUS.
        addition_ZUS = self.ZUS_additions(cr, uid, payslip_id, context=context)

        '''Creating payslip'''
        computed_data = self.calculate_salary_PL(conf,
                                            elements,
                                            'c', #char - etat/cywilnoprawna (e/c)
                                            hardcoded_params['umowa_cywilnoprawna_z_wlasnym_pracownikiem'], #bool

                                            #ABSENCES
                                            sick_days_so_far,

                                            #ZUS
                                            podstawa_wymiaru_skladek_od_pocz_roku, #float
                                            vals['calculate_fp'], #bool
                                            vals['calculate_fgsp'], #bool
                                            vals['calculate_emr'], #bool
                                            vals['calculate_rent'], #bool
                                            vals['calculate_chor'], #bool
                                            vals['calculate_wyp'], #bool
                                            vals['calculate_zdr'],
                                            addition_ZUS,           # float

                                            #PIT, NFZ
                                            False, #rozliczanie kwoty wolnej
                                            tax_scale, #lista list
                                            PIT_income_since_start_of_year,
                                            tax_deduction,
                                            is_not_resident,
                                            False,

                                            #DO WYPŁATY
                                            suma_kup_50_ten_rok, #float
                                            deductions_config
                                           )
        '''Returning write data'''
        return  {
                'fp': computed_data['FP'],
                'fgsp': computed_data['FGSP'],

                'skladka_zdrowotna_odliczona': computed_data['skladka_zdrowotna_odliczona'],
                'skladka_zdrowotna_od_netto': computed_data['skladka_zdrowotna_od_netto'],

                'chor_pracownik': computed_data['chor_pracownik'],
                'emr_pracownik': computed_data['emr_pracownik'],
                'rent_pracownik': computed_data['rent_pracownik'],
                'emr_pracodawca': computed_data['emr_pracodawca'],
                'rent_pracodawca': computed_data['rent_pracodawca'],
                'wyp_pracodawca': computed_data['wyp_pracodawca'],
                'cywilnoprawna_id': contract,
                'employee_id': vals['employee_id'][0],
                'skladki_ZUS_pracownika': (computed_data['chor_pracownik'] + computed_data['emr_pracownik'] + computed_data['rent_pracownik']),
                'koszty_uzyskania': computed_data['koszty_uzyskania_przychodu'],
                'do_wyplaty': computed_data['do_wyplaty'],
                'kwota_zaliczki_na_PIT': computed_data['kwota_zaliczki_na_PIT'],
                'dochod': computed_data['dochod'],
                'value3': computed_data['wartosc3'],
                'koszty_uzyskania_autorskie': computed_data['koszty_uzyskania_autorskie'],
                'potracenia': computed_data['potracenia'],
                'wyplata_przed_potraceniami': computed_data['netto'],

                'kwota_NFZ': computed_data['kwota_NFZ'],
                'kwota_US': computed_data['kwota_US'],
                'brutto': computed_data['brutto']
               }

    def get_unsettled_absences(self, cr, uid, employee_id, month, year, context=None):
        line_pool = self.pool.get('hr2.payslip.line')
        date_pool = self.pool.get('hr2.employee.date')

        date_from = str(date(year, month, 1))
        date_to = str(self.last_day_of_month(year, month))
        absences_list = date_pool.generate_employee_absences(cr, uid, date_from, date_to, employee_id, context=context)
        absences_list = sorted(absences_list, key=lambda k: k['date_from'])

        absence_lines = line_pool.search(cr, uid, [('date_start', '>=', date_from),
                                                   ('date_stop', '<=', date_to),
                                                   ('type_id.application', '=', 'absence')], context=context)
        absence_lines = line_pool.browse(cr, uid, absence_lines, context=context)
        for settled_absence in absence_lines:
            for i in range(len(absences_list)):
                if settled_absence.absence_id == absences_list[i]['absence_id']:
                    del absences_list[i]
                    break

        res = [absences_list, []]
        return res

    def create_correction_lines(self, cr, uid, corrections, payslip_id, context=None):
        """Funkcja tworzy linie payslipa dla korekty z poprzedniego miesiąca
        oraz aktualizuje wartość linii wynagrodzenia za pracę"""
        if isinstance(payslip_id, (list,dict)):
            payslip_id = payslip_id[0]
        conf_pool = self.pool.get('lacan.configuration')
        type_pool = self.pool.get('hr2.payslip.line.type')
        line_pool = self.pool.get('hr2.payslip.line')
        lineline_pool = self.pool.get('hr2.payslip.line.line')

        payment_type = type_pool.search(cr, uid, [('application', '=', 'correction'),('is_benefit', '=', False)], context=context)
        if payment_type:
            payment_type = payment_type[0]
        else:
            raise osv.except_osv(_('Błąd!'),_('Nie ma zdefiniowanego typu składnika paska listy płac dla korekty wynagrodzenia chorobowego.'))
        benefit_type = type_pool.search(cr, uid, [('application', '=', 'correction'),('is_benefit', '=', True)], context=context)
        if benefit_type:
            benefit_type = benefit_type[0]
        else:
            raise osv.except_osv('Błąd!', 'Nie ma zdefiniowanego typu składnika paska listy płac dla korekty zasiłku.')
        work_time_type = type_pool.search(cr, uid, [('application', '=', 'work_time'),('is_benefit', '=', False)], context=context)[0]
        work_time_id = line_pool.search(cr, uid, [('type_id', '=', work_time_type),
                                                  ('payslip_id', '=', payslip_id)], context=context)

        # Zaktualizuj wartość czasu pracy.
        line_pool.write(cr, uid, work_time_id, {'value': corrections['value3']}, context=context)

        # Utwórz pomniejszenie za zeszły miesiąc w wynagrodzeniu za czas pracy.
        for deduction in corrections['deductions']:
            if isinstance(work_time_id, list):
                work_time_id = work_time_id[0]

            cr.execute("SELECT number FROM hr2_payslip_line_line "
                       "WHERE payslip_line_id = {id} "
                       "ORDER BY number DESC".format(id=work_time_id))
            number = cr.fetchone()[0]
            lineline_pool.create(cr, uid, {'name': 'Pomniejszenie za zeszły miesiąc',
                                           'value': deduction,
                                           'payslip_line_id': work_time_id,
                                           'number': number + 1}, context=context)

        # Utwórz linie wynagrodzenia lub zasiłku chorobowego.
        for correction_line in corrections['correction_list']:
            vals = {}
            if correction_line.get('p_days'):
                vals['type_id'] = payment_type
                vals['number_of_days'] = correction_line['p_days']
            elif correction_line.get('z_days'):
                if not conf_pool.get_confvalue(cr, uid, 'Czy pracodawca sam wyplaca zasilki z ubezp. spol.'):
                    correction_line['value'] = 0.0
                vals['type_id'] = benefit_type
                vals['number_of_days'] = correction_line['z_days']
            vals['payslip_id'] = payslip_id
            vals['base'] = correction_line['base']
            vals['value'] = correction_line['value']
            vals['absence_id'] = correction_line['absence_id']
            vals['date_start'] = correction_line['date_start']
            vals['date_stop'] = correction_line['date_stop']
            line_pool.create(cr, uid, vals, context=context)
        return True
    
    def update_payslip_for_post(self, cr, uid, post, payslip_id, worktime_type_id, absence_type_id, addition_type_id, sick_leave_types, conf, context=None):
        """Generates data necessary for updating the hr2.payslip object for a given post
        @param post: ID of hr2.etat object
        @return: value dictionary"""
        register_id = context.get('register_id')
        register_vals = self.pool.get('hr2.payroll.register').read(cr, uid, register_id,
                                                                   ['id','register_year', 'register_month', 'process_prev_month', 'date'],
                                                                   context=context)
        year = register_vals['register_year']
        month = register_vals['register_month']
        payment_date = register_vals['date']

        wymiar_pracy = self.pool.get('hr2.etat').read(cr, uid, post, ['work_time_licz','work_time_mian'], context=context)
        work_time_licz = float(wymiar_pracy.get('work_time_licz'))
        work_time_mian = float(wymiar_pracy.get('work_time_mian'))
        if not (work_time_licz and work_time_mian):
            wymiar_pracy = 1
        else:
            wymiar_pracy = work_time_licz/work_time_mian
        vals = self.pool.get('hr2.etat').read(cr, uid, post, ['month_pay', 'employee_id'], context=context)

        actual_etat_data_id = self.pool.get('hr2.etat.data').search(cr, uid,
                                                                    [('etat_id', '=', vals['id']),
                                                                     ('date_from', '<=', payment_date)],
                                                                    order='date_from desc', context=context)[0]
        actual_etat_data = self.pool.get('hr2.etat.data').read(cr, uid, actual_etat_data_id,
                                                                ['calculate_fp', 'calculate_fgsp', 'calculate_emr',
                                                                 'calculate_rent', 'calculate_chor', 'calculate_wyp',
                                                                 'rozliczac_kwote_wolna', 'calculate_zdr'],
                                                               context=context)
        vals.update(actual_etat_data)

        deductions_config = self.compute_deductions_config(cr,uid,vals['employee_id'][0], 'e', payment_date, wymiar_pracy=wymiar_pracy,
                                                           context=context)

        compute_payslip_sum_wynik = self.compute_payslip_sum_this_year(cr, uid, vals['employee_id'][0],
                                                                       register_vals['register_month'], register_vals['register_year'],
                                                                       context=context)
        podstawa_wymiaru_skladek_od_pocz_roku = compute_payslip_sum_wynik['podstawa_wymiaru_skladek']
        PIT_income_since_start_of_year = compute_payslip_sum_wynik['suma_PIT']

        suma_kup_50_ten_rok = compute_payslip_sum_wynik['suma_kup_50']
        tax_deduction = self.compute_koszt_uzyskania_przychodu(cr, uid, 'e', post, conf, context=context)

        additions = 0
        payslip_lines_pool = self.pool.get('hr2.payslip.line')
        additions_id = payslip_lines_pool.search(cr, uid, [('payslip_id','=',payslip_id)], context=context)
        for add in payslip_lines_pool.read(cr, uid, additions_id, ['value', 'absence_id'], context=context):
            # Funkcjonalność modułu hr_abroad_employees (unika liczenia zewnętrznego podatku jako dodatku).
            if add['id'] in context.get('external_tax', {}).get(post, {}).get('lines', []):
                continue

            additions += add['value']
            payslip_lines_obj = payslip_lines_pool.browse(cr, uid, add['id'], context=context)
            if add['absence_id'] and payslip_lines_obj.licz_KUP_jak_podstawa == True:
                absence_pool = self.pool.get('hr2.absence')
                absence_kup = absence_pool.browse(cr, uid, add['absence_id'][0], context=context).holiday_status_id.kup
                if absence_kup == False:
                    payslip_lines_pool.write(cr, uid, add['id'], {'licz_KUP_jak_podstawa':False}, context=context)

        progi_conf = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Konfiguracja progów podatkowych', 
                                                                        data_str = context.get('employee_list_date', False), 
                                                                        context=context)
        tax_scale=[]
        for prog in progi_conf.prog_line_ids:
            tax_scale.append([prog.value_from, float(prog.percent)/100])


        '''Gathering data'''
        elements = self.gather_payslip_data(cr, uid, payslip_id, 'e', worktime_type_id, absence_type_id, addition_type_id,
                                            sick_leave_types, context=context)
        sick_days_so_far = self.get_sick_days_so_far(cr, uid, vals['employee_id'][0], year, month, context=None)

        '''Uzupelnienie do pensji minimalnej'''
        self.uzupelnienie_pensji(cr, uid, elements, post, payslip_id, year, month, wymiar_pracy,vals['employee_id'][0],
                                 context=context)

        #Zebranie wartości dla korekty z poprzedniego miesiąca
        absences_list = [[],[]]
        previous_month_data = {}
        if register_vals['process_prev_month']:
            month -= 1
            if month == 0:
                year-=1
                month=12
            employee_id = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['employee_id'], context=context)['employee_id'][0]
            absences_list = self.get_unsettled_absences(cr, uid, employee_id, month, year, context=context)

            prev_payslip_id = self.pool.get('hr2.payslip').search(cr, uid,
                                                                  [('employee_id','=',employee_id), ('register_id.register_month','=',month),
                                                                   ('register_id.register_year','=',year)],
                                                                  context=context)
            prev_gross_salary_id = self.pool.get('hr2.payslip.line').search(cr, uid,
                                                                            [('payslip_id','in',prev_payslip_id),
                                                                             ('type_id.application','=','work_time')],
                                                                            limit=1, context=context)
            prev_gross_salary = self.pool.get('hr2.payslip.line').read(cr, uid, prev_gross_salary_id[0], ['base'], context=context)['base']

            sick_base_leave = self.wylicz_podstawe_chorobowego(cr, uid, {'register_year': year, 'register_month': month}, 
                                                               employee_id, context=context)[0]
            if sick_base_leave == 0:
                sick_base_leave = self.wylicz_podstawe_chorobowego(cr, uid, {'register_year': year, 'register_month': month+1},
                                                               employee_id, context=context)[0]
            previous_month_data = {'gross_salary': prev_gross_salary, 'sick_leave_base': sick_base_leave}

        # Sprawdź czy są dodatki obciążone przez ZUS.
        addition_ZUS = self.ZUS_additions(cr, uid, payslip_id, context=context)

        # Pobierz sumę wartości nieobecności płatnych dla payslipa
        cr.execute('''SELECT sum(value) from hr2_payslip_line_temp WHERE payslip_id = {}'''.format(payslip_id))
        paid_leave_sum = cr.fetchone()
        paid_leave_sum = paid_leave_sum and paid_leave_sum[0] or 0

        cr.execute('''DELETE FROM hr2_payslip_line_temp WHERE payslip_id = {}'''.format(payslip_id))
        '''Creating payslip'''
        computed_data = self.calculate_salary_PL(conf,
                                                elements,
                                                'e', #char - etat/cywilnoprawna (e/c)
                                                hardcoded_params['umowa_cywilnoprawna_z_wlasnym_pracownikiem'], #bool

                                                #ABSENCES
                                                sick_days_so_far,

                                                #ZUS
                                                podstawa_wymiaru_skladek_od_pocz_roku, #float
                                                vals['calculate_fp'], #bool
                                                vals['calculate_fgsp'], #bool
                                                vals['calculate_emr'], #bool
                                                vals['calculate_rent'], #bool
                                                vals['calculate_chor'], #bool
                                                vals['calculate_wyp'], #bool
                                                vals['calculate_zdr'],
                                                addition_ZUS,           # float

                                                #PIT, NFZ
                                                vals['rozliczac_kwote_wolna'], #bool
                                                tax_scale, #lista list
                                                PIT_income_since_start_of_year,
                                                tax_deduction,
                                                False, # zmienna is_not_resident nie ma zastosowania dla umów o pracę
                                                context.get('external_tax', {}).get(post, {}).get('value'),

                                                #DO WYPŁATY
                                                suma_kup_50_ten_rok, #float
                                                deductions_config,
                                                absences_list,
                                                previous_month_data,
                                                paid_leave_sum
                                               )
        if len(computed_data['corrections']['correction_list']) > 0:
            self.create_correction_lines(cr, uid, computed_data['corrections'], payslip_id, context=context)
        '''Returning write data'''
        return  {
                'fp': computed_data['FP'],
                'fgsp': computed_data['FGSP'],

                'skladka_zdrowotna_odliczona': computed_data['skladka_zdrowotna_odliczona'],
                'skladka_zdrowotna_od_netto': computed_data['skladka_zdrowotna_od_netto'],

                'chor_pracownik': computed_data['chor_pracownik'],
                'emr_pracownik': computed_data['emr_pracownik'],
                'rent_pracownik': computed_data['rent_pracownik'],

                'emr_pracodawca': computed_data['emr_pracodawca'],
                'rent_pracodawca': computed_data['rent_pracodawca'],
                'wyp_pracodawca': computed_data['wyp_pracodawca'],
                'etat_id': post,
                'employee_id': vals['employee_id'][0],
                'skladki_ZUS_pracownika': (computed_data['chor_pracownik'] + computed_data['emr_pracownik'] + computed_data['rent_pracownik']),
                'koszty_uzyskania': computed_data['koszty_uzyskania_przychodu'],
                'do_wyplaty': computed_data['do_wyplaty'],
                'kwota_zaliczki_na_PIT': computed_data['kwota_zaliczki_na_PIT'],
                'dochod': computed_data['dochod'],
                'value3': computed_data['wartosc3'],
                'koszty_uzyskania_autorskie': computed_data['koszty_uzyskania_autorskie'],
                'potracenia': computed_data['potracenia'],
                'wyplata_przed_potraceniami': computed_data['netto'],

                'kwota_NFZ': computed_data['kwota_NFZ'],
                'kwota_US': computed_data['kwota_US'],
                'zmniejszenie_zaliczki': computed_data['zmniejszenie_zaliczki'],
                'brutto': computed_data['brutto']
               }

    def show_addition_lines(self, cr, uid, ids, context=None):
        '''metoda wyświetla listę payslip.line typu dodatek dla danego payrolla'''
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model','=','ir.ui.view'),('name','=','view_payslip_additions_line_tree')],
                                        context=context)
        tree_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        model_data_ids = mod_obj.search(cr, uid, [('model','=','ir.ui.view'),('name','=','view_payslip_additions_line_form')],
                                        context=context)
        form_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        type_id = self.pool.get('hr2.payslip.line.type').search(cr, uid, [('name','=','Addition')], context=context)[0]
        context['default_register_id'] = ids[0]
        context['default_type_id'] = type_id
        return {
            'name': 'Dodatki',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr2.payslip.line',
            'type': 'ir.actions.act_window',
            'target': 'new tab',
            'domain': [('payslip_id.register_id', '=', ids[0]),('type_id.name','=','Addition')],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'context': context
        }

    def get_sick_days_so_far(self, cr, uid, employee_id, year, month, context=None):
        """ Metoda zlicza ilośc dni zwolnienia chorobowego od początku danego roku. """
        first_day_of_year = str(datetime.strptime(str(year)+'-01-01', "%Y-%m-%d").date())
        first_day_of_month = str(datetime(year, month, 1).date())

        sick_leave_days = self.pool.get('hr2.employee.date').search(
            cr, uid, [('date', '>=', first_day_of_year), ('date', '<', first_day_of_month),
                      ('employee_id', '=', employee_id), ('absence_id.holiday_status_id.type', '=', 'sick_leave')],
            context=context)
        return len(sick_leave_days)

    def is_not_resident(self, cr, uid, contract_type_id, context=None):
        """ Zwraca True jeżeli typ umowy cywilnoprawnej o podanym ID ma zaznaczone pole "not_resident". """
        data = self.pool.get('hr2.contract.type').read(cr, uid, contract_type_id, ['not_resident'], context=context)
        res = True if data and 'not_resident' in data and data['not_resident'] else False
        return res

    def ZUS_additions(self, cr, uid, payslip_id, context=None):
        """ Sprawdza czy na dany miesiąc dla danego payslip_id są dodatki obciążone przez ZUS.
            Jeżeli tak - zwraca ich sumaryczną wartość. Jeżeli nie - zwraca 0. """
        sql_query = """SELECT application, calculate_zus, pl.value FROM hr2_payslip_line pl
                       LEFT JOIN hr2_salary_addition_type sat ON sat.id = pl.addition_type
                       WHERE pl.payslip_id = {payslip}""".format(payslip=payslip_id)
        cr.execute(sql_query)

        add_val = 0
        for line in cr.fetchall():
            # Dolicz wartość dodatku jeżeli calculate_zus == True
            # i dodatek nie jest typu brutto (liczone oddzielnie w calculate_salary_PL).
            if line[0] not in ('brutto', 'brutto_importowane') and line[1]:
                add_val += line[1]
        return add_val

    def unlink(self, cr, uid, ids, context=None):
        """ Metoda nadpisana aby wywołać unlinka na powiązanych rekordach z obiektu hr2.payment.register. """
        payreg_pool = self.pool.get('hr2.payment.register')
        payreg_ids = payreg_pool.search(cr, uid, [('payroll_register_id', 'in', ids)], context=context)
        payreg_pool.unlink(cr, uid, payreg_ids, context=context)
        return super(hr2_payroll_register, self).unlink(cr, uid, ids, context=context)

hr2_payroll_register()


class hr2_salary_addition_type(osv.osv):
    _name = 'hr2.salary.addition.type'
    _description = 'Typ dodatkow'
    _inherit = 'company.related.class'
    def _calculate_code(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for id in ids:
            res[id] = id
        return res

    _columns = {
                'name': fields.char('Nazwa dodatku'),
                'code': fields.function(_calculate_code, method=True, string='Kod', readonly=True),
                'application': fields.selection([('ekwiwalent', 'ekwiwalent'), ('brutto', 'brutto'), ('swiadczenie', 'świadczenie'), ('brutto_importowane', 'brutto importowane')], 'Jakiego typu jest kwota dodatku'),
                'licz_kup_jak_podstawa': fields.boolean('Czy liczyć KUP tak jak podstawa wynagrodzenia'),
                'okresowy': fields.boolean('Czy dodatek jest okresowy'),
                'co_ile_powtarzac': fields.integer('Co ile miesięcy liczyć dodatek'),
                'nalezny_za_okres_nieobecnosci': fields.boolean('Czy dodatek należy za okres nieobecności'),
                'calculate_zus': fields.boolean('Dodatek obciążony ZUS'),
                'wlicz_do_pdst_chor': fields.boolean('Wlicz do podstawy chorobowego'),
                'account_id': fields.many2one('hr2.payslip.config.accounts', 'Konto'),
                }

    def on_change_application(self, cr, uid, ids, application, context=None):
        """ Zmienia wartosci pól w związku ze zmianą typu dodatku. """
        res = {}
        if application == 'brutto_importowane':
            res.update({
                'co_ile_powtarzac': 1,
                'licz_kup_jak_podstawa': True,
                'okresowy': True,
                'nalezny_za_okres_nieobecnosci': True,
            })
        res.update(self._get_application_field_vals(application))
        return {'value': res}

    def _get_application_field_vals(self, application):
        return {
            'calculate_zus': True,
            'wlicz_do_pdst_chor': True,
        } if application not in ('ekwiwalent', 'swiadczenie') else {}

    def create(self, cr, uid, values, context=None):
        if values.get('application'):
            values.update(self._get_application_field_vals(values.get('application')))
        return super(hr2_salary_addition_type, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('application'):
            values.update(self._get_application_field_vals(values.get('application')))
        return super(hr2_salary_addition_type, self).write(cr, uid, ids, values, context=context)

hr2_salary_addition_type()


class hr2_salary_addition(osv.osv):
    _name = 'hr2.salary.addition'
    _description = 'Dodatki'
    _inherit = 'company.related.class'

    _columns = {
                'name': fields.char('Opis dodatku', required = True),
                'addition_type_id': fields.many2one('hr2.salary.addition.type', 'Typ dodatku', required=True),
                'etat_data_id': fields.many2one('hr2.etat.data', 'Umowa o pracę', on_delete='cascade'),
                'contract_id': fields.many2one('hr2.contract', 'Umowa cywilno-prawna'),
                'kwota': fields.float('Kwota dodatku'),
                'procent_podstawy': fields.float('Procent podstawy'),
                'year_start': fields.integer('Rok od którego wliczać dodatek', required=True),
                'month_start': fields.integer('Miesiąc od którego wliczać dodatek', required=True),
                'year_stop': fields.integer('Rok w którym skończyć wliczać dodatek'),
                'month_stop': fields.integer('Miesiąc w którym skończyć wliczać dodatek'),
                }

    def _check_post_contract(self, cr, uid, ids, context=None):
        '''Checks if the addition has post or contract'''
        addition_list = self.browse(cr, uid, ids, context=context)
        for addition in addition_list:
            if not addition.etat_data_id and not addition.contract_id:
                raise osv.except_osv('Błąd!', 'Dodatek musi mieć wypełnione pole etat lub umowa cywilno-prawna.')
        return True

    _constraints = [(_check_post_contract, '', ['']), ]
hr2_salary_addition()

class hr2_salary_deduction_computation_type(osv.osv):
    _name = 'hr2.salary.deduction.computation.type'
    _description = 'Typ potraceń'
    _inherit = 'company.related.class'
    _columns = {
                'name': fields.char('Nazwa potrącenia'),
                'percent_normal': fields.float('Wynagrodzenia podlegają egzekucji do'),
                'percent_special_1': fields.float('Podlegające egzekucji do %'),
                'special_1_additions': fields.many2many('hr2.salary.addition.type','hr2_salary_addition_type_rel1','config_id1','special1_id','Składniki'),
                'percent_special_2': fields.float("Podlegające egzekucji do %"),
                'special_2_additions': fields.many2many('hr2.salary.addition.type', 'hr2_salary_addition_type_rel2','config_id2','special2_id','Składniki'),
                'amount_free': fields.float('Kwota wolna od potrąceń'),
                'amount_free_proportional': fields.boolean('Proporcjonalnie do wymiaru etatu'),
                'percent_ZUS': fields.float('Podlegające egzekucji do %'),
                'percent_ZUS_free': fields.float('Kwota wolna od potrąceń')
                }
hr2_salary_deduction_computation_type()


class hr2_salary_deduction_type(osv.osv):

    _name = 'hr2.salary.deduction.type'
    _description = 'Typ potrąceń z priorytetami'
    _inherit = 'company.related.class'

    def _calculate_code(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for id in ids:
            res[id] = id
        return res

    _columns = {
                'name': fields.char('Nazwa', required=True),
                'code': fields.function(_calculate_code, method=True, string='Kod', readonly=True),
                'priority': fields.integer('Priorytet'),
                'limit': fields.float('Limit'),
                'code_overlimit': fields.integer('Kod potrącenia powyżej limitu'),
                'deduction_computation_type_id': fields.many2one('hr2.salary.deduction.computation.type', 'Grupa potrąceń', required=True)
                }
hr2_salary_deduction_type()


class hr2_salary_deduction(osv.osv):
    _name = 'hr2.salary.deduction'
    _description = 'Potracenie'
    _inherit = 'company.related.class'


    def _calculate_code(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for id in ids:
            res[id] = id
        return res


    def _calculate_amount_paid(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for id in ids:
            amount = 0
            payslip_deductions_ids = self.pool.get('hr2.payslip.deduction').search(cr, uid, [('deduction_id','=',id)], context=context)
            payslip_deductions = self.pool.get('hr2.payslip.deduction').read(cr, uid, payslip_deductions_ids, ['amount'], context=context)
            for deduction in payslip_deductions:
                amount += deduction['amount']
            res[id] = amount
        return res


    _columns = {
                'name': fields.char('Nazwa', required=True),
                'employee_id': fields.many2one('hr.employee', 'Pracownik', required=True, ondelete='restrict'),
                'number': fields.function(_calculate_code, method=True, string='Kod', readonly=True),
                'decision_date': fields.date('Data decyzji o potrąceniu'),
                'bank_account_number': fields.integer('Numer konta bankowego'),
                'deduction_type': fields.many2one('hr2.salary.deduction.type', 'Typ potrącenia', required=True, ondelete='restrict'),
                'execution_date_start': fields.date('Początek potrącania', required=True),
                'execution_date_stop': fields.date('Koniec potrącania'),
                'amount_type': fields.boolean('Czy potrącenie jest odnawialne'),
                'amount': fields.float('Kwota potrącenia', required=True),
                'amount_paid': fields.function(_calculate_amount_paid, method=True, string='Spłacona kwota potrącenia', readonly=True, ),
                'execution_from_contracts': fields.boolean('Czy potrącać z kontraktów'),
                'execution_from_contracts_restrictions': fields.selection([('brak','brak'),('wyplata','Do wysokości kwoty wypłaty'),
                                                                           ('wolna_kwota','Wolna od potrąceń kwota netto'),
                                                                           ('wolny_procent','Wolny od potrąceń procent kwoty netto')],
                                                                          'Ograniczenie potrąceń od kontraktów'),
                'contracts_restrictions_value': fields.float('Wartość ograniczenia kontraktów'),
                'notes': fields.text('Uwagi'),
                'partner_id': fields.many2one('res.partner', 'Komornik'),
                'account_id': fields.many2one('account.account', 'Konto księgowe'),
                }

    _defaults = {
        'execution_date_start': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
        'decision_date': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                }

    def _check_deduction_amount(self, cr, uid, ids, context=None):
        """Funkcja sprawdzajaca czy wartosc potracenia nie jest nizsza od wartosci aktualnie zaplaconej
        @param ids: Register ID
        """
        deduction_list = self.browse(cr, uid, ids, context=context)
        for deduction in deduction_list:
            if (deduction.amount < deduction.amount_paid) & (deduction.amount_type == False):
                raise osv.except_osv('Błąd!', 'Nie można zapisać potrącenia o wartości mniejszej niż dotychczasowa kwota spłacona')
        return True

    _constraints = [(_check_deduction_amount, '', ['']), ]

#zostawiam bo moze sie przydac
#     def onchange_amount_type(self, cr, uid, ids, amount_paid, amount_type):
#         if amount_paid != 0:
#             amount_type = not amount_type
#             return {'warning':{'title':'AAA','message':'Ratunku'},'value':{'amount_type':amount_type}}
#         return True

hr2_salary_deduction()


class hr2_payslip_deduction(osv.osv):
    _name = 'hr2.payslip.deduction'
    _description = 'Potracenia od wyplaty'
    _inherit = 'company.related.class'

    _columns = {
                'payslip_id': fields.many2one('hr2.payslip', 'Rachunek', readonly = True, ondelete='cascade'),
                'employee_id': fields.many2one('hr.employee', 'Pracownik', readonly = True),
                'deduction_id': fields.many2one('hr2.salary.deduction', 'Potrącenie', readonly = True, ondelete='restrict'),
                'deduction_type': fields.many2one('hr2.salary.deduction.type', 'Typ potrącenia', readonly = True),
                'amount': fields.float('Kwota potrącenia', readonly = True)
                }

hr2_payslip_deduction()

class payroll_employee_list_wizard(osv.osv_memory):
    """
    Asks the user for a date, then uses a created domain to view thw employee list
    """

    _name = "payroll.employee.list.wizard"
    _columns = {
                'date':fields.date('Data')
                 }

    _defaults = {
        'date': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                }

    def view_employee_list(self, cr, uid, ids, context=None):
        """ Button, which passes the date entered by the user in context,
            @param ids: Wizard ID.
            @return: Action opening employee tree with the date in context. """
        ir_pool = self.pool.get('ir.model.data')

        # Set date domain for the employees list.
        ctx = context.copy()
        ctx['employee_list_date'] = self.read(cr, uid, ids[0], ['date'], context=context)['date']

        # Check user's access rights and set proper domain for the view.
        user_groups = self.pool.get('res.users').read(cr, uid, uid, ['groups_ids'], context=context)['groups_id']
        recruiter_id = ir_pool.get_object_reference(cr, uid, 'hr', 'group_hr_recruiter')[1]
        manager_id = ir_pool.get_object_reference(cr, uid, 'hr', 'group_hr_manager')[1]
        recruiter = True if recruiter_id in user_groups else False
        manager = True if manager_id in user_groups else False
        if manager and recruiter:
            domain = ""
        elif recruiter:
            domain = "[('emp_state','!=','employee')]"
        elif manager:
            domain = "[('emp_state','!=','candidate')]"
        else:
            # Case for situation when employees list got somehow opened but user isn't recruiter or manager.
            # This should never happen, but we don't like unhandled errors.
            raise osv.except_osv(_('Error!'), _("You don't have access rights to this view."))

        # Get proper views.
        view_id = ir_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'view_payroll_employee_tree')[1]
        view_id_form = ir_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'view_payroll_employee_form')[1]
        search_id = ir_pool.get_object_reference(cr, uid, 'hr_payroll_pl', 'view_payroll_employee_filter')[1]

        return {
            'name': _('Employee list'),
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'hr.employee',
            'views': [(view_id, 'tree'), (view_id_form, 'form')],
            'search_view_id': search_id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'current',
            'domain': domain,
        }

payroll_employee_list_wizard()


class payroll_shift_list_wizard(osv.osv_memory):
    """
    Asks the user for a date, then uses a proper domain to show a specific employee list
    """

    _name = "payroll.shift.list.wizard"
    _columns = {
                'date':fields.date('Data')
                 }

    _defaults = {
        'date': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                }


    def view_shift_list(self, cr, uid, ids, context=None):
        '''Button, which passes the date entered by the user in context
        @param ids: id of the wizard
        @return: Action for post view
        '''
        ctx = context.copy()
        date = self.pool.get('payroll.shift.list.wizard').read(cr, uid, ids[0], ['date'], context=context)['date']
        ctx['shift_list_date'] = date

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'view_payroll_etat2_tree')[1]
        view_id_form = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl', 'view_payroll_etat2_form')[1]
        return {
                'name': _('Post list'),
                'view_type': 'form',
                'view_mode': 'tree, form',
                'res_model': 'hr2.etat',
                'views': [(view_id, 'tree'),(view_id_form, 'form')],
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'current',
                }

payroll_shift_list_wizard()


class res_partner_bank(osv.osv):
    _inherit = "res.partner.bank"
    _columns={
        'employee_id': fields.many2one('hr.employee', 'Employee', ondelete='cascade', select=True),
    }
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('type', False) and vals['type'] == 'employee':
            employee_id = self.pool.get('hr.employee').search(cr, uid, [('code', '=', vals['owner_name'])], context=None)
            if employee_id:
                vals['employee_id'] = employee_id[0]
        return super(res_partner_bank, self).create(cr, uid, vals, context=context)
    
res_partner_bank()


class hr2_payment_register(osv.osv):
    _name = "hr2.payment.register"
    _inherit = 'company.related.class'


    def _get_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}

        for id in ids:
            state = True
            date = time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)

            payment_ids = self.pool.get('hr2.payment.register.payment.line').search(cr, uid, [('payment_register_id', '=', id)], context=context)
            for payment_id in payment_ids:
                new_date = self.pool.get('hr2.payment.register.payment.line').read(cr, uid, payment_id, ['date'], context=context)['date']
                if new_date > date:
                    date = new_date

            line_ids = self.read(cr, uid, id, ['payment_register_line_id'], context=context)['payment_register_line_id']
            for line in line_ids:
                if self.pool.get('hr2.payment.register.line').read(cr, uid, line, ['state'], context=context)['state'] == 'unpaid':
                    state = False
                    date = False
                    break;

            res[id] = {}
            res[id]['czy_zaplacono'] = state
            res[id]['payment_date'] = date
        return res


    def _update_state_payment_line(self, cr, uid, ids, context=None):
        res = []

        for id in ids:
            if self.read(cr, uid, id, ['payment_register_id'], context=context)['payment_register_id']:
                res.append(self.read(cr, uid, id, ['payment_register_id'], context=context)['payment_register_id'][0])

        return res


    def _update_state_line(self, cr, uid, ids, context=None):
        res =[]

        for id in ids:
            id = self.pool.get('hr2.payment.register.line').read(cr, uid, id, ['payment_register_id'], context=context)['payment_register_id']
            if id:
                res.append(id[0])

        return res

    _columns = {
        'name': fields.char('Name', size=64),
        'company_id': fields.many2one('res.company', 'Company'),
        'type': fields.selection((('transfer', 'Transfer'),('cash', 'Cash')), 'Type', required=True),
        'payment_date': fields.function(_get_state,
                                type='date',
                                method=True,
                                multi='payment_state',
                                string='Payment date',
                                store = {
                                         'hr2.payment.register.payment.line': (_update_state_payment_line,
                                                                ['payslip_id',
                                                                'payment_register_id',
                                                                'amount',
                                                                'out_bank_id',
                                                                'payment_register_line_id'],
                                                                20),
                                         'hr2.payment.register.line': (_update_state_line,
                                                                ['amount'],
                                                                20),
                                         }
                                 ),
        'planned_payment_date': fields.date('Planned payment date'),
        'bank_id': fields.many2one('res.partner.bank', 'Out bank'),
        'state': fields.selection((('open', 'Open'), ('closed', 'Closed')), 'State'),
        'payroll_register_id': fields.many2one('hr2.payroll.register', 'Payroll register'),
        'payment_register_line_id': fields.one2many('hr2.payment.register.line', 'payment_register_id', 'Payment register lines'),
        'payment_register_payment_line_id': fields.one2many('hr2.payment.register.payment.line', 'payment_register_id', 'Payment register payment lines'),
        'group': fields.selection((('salary','Wynagrodzenia'), ('ZUS','ZUS'), ('US','US'), ('deductions','Potrącenia')), 'Typ'),
        'month_settled': fields.integer('Month settled'),
        'year_settled': fields.integer('Year settled'),
        'czy_uwzgledniac_planowane_wyplaty': fields.boolean('Czy uwzględniać planowane wypłaty?'),
        'czy_zaplacono': fields.function(_get_state,
                                type='boolean',
                                method=True,
                                multi='payment_state',
                                string='Czy rejestr został opłacony?',
                                store = {
                                         'hr2.payment.register.payment.line': (_update_state_payment_line,
                                                                ['payslip_id',
                                                                'payment_register_id',
                                                                'amount',
                                                                'out_bank_id',
                                                                'payment_register_line_id'],
                                                                20),
                                         'hr2.payment.register.line': (_update_state_line,
                                                                ['amount'],
                                                                20),
                                         }
                                 ),

    }

    _order = "planned_payment_date desc"


    def validate_payment_register(self, cr, uid, ids, context=None):
        '''Executes after pushing the wizard button'''
        '''@return: view action dictionary'''

        ctx = context.copy()
        ctx['register_id'] = ids[0]

        return {
               'name': _('Zatwierdź rejestr wypłat'),
               'view_type': 'form',
               'context': ctx,
               'view_mode': 'form',
               'res_model': 'hr2.wizard.payment.pay',
               'type': 'ir.actions.act_window',
               'target': 'new'
               }


    def przelicz_ponownie_zus(self, cr, uid, ids, context=None):
        """Przelicza ponownie rejestr ZUS"""
        obj = self.browse(cr, uid, ids[0], context=context)

        if obj.state == 'closed':
            raise osv.except_osv('Błąd!', 'Nie można przeliczyć zamkniętego rejestru.')

        start_date = str(obj.year_settled) + '-' + str(obj.month_settled) + '-' + '01'
        end_date = str(self.pool.get('hr2.payroll.register').last_day_of_month(obj.year_settled, obj.month_settled))
        register_ids = self.pool.get('hr2.payment.register').search(cr, uid, [('planned_payment_date', '>=', start_date), ('planned_payment_date', '<=', end_date), ('group', '=', 'salary')], context=context)

        types_id = self.pool.get('hr2.payslip.line.type').search(cr,uid,[('name','in',('Sick pay','Sick benefit','Child care'))])
        lm = (datetime.strptime(str(obj.year_settled) + '-' + str(obj.month_settled) + '-01',
                                tools.DEFAULT_SERVER_DATE_FORMAT) - relativedelta.relativedelta(months=1)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        lmpreg = self.pool.get('hr2.payment.register').search(cr, uid, [('month_settled','=', lm[5:7]),('year_settled','=',lm[0:4])], context=context)
        lmpreglines = self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id','in', lmpreg),
                                                                                  ('description','like', 'Składki ZUS za')],
                                                                        context=context)
        cr.execute("""
                    SELECT id
                    FROM   hr2_payment_register_line
                    WHERE  payment_register_id IN (SELECT id
                                                   FROM   hr2_payment_register
                                                   WHERE  ( month_settled > %s
                                                            AND year_settled = %s )
                                                           OR ( year_settled > %s )
                                                           ORDER BY month_settled,year_settled)
                                                   AND description LIKE %s """,
                (obj.month_settled,obj.year_settled,obj.year_settled,"Składki ZUS za %"))
        fpregl_id = cr.fetchall()

        ZUS = [0, 0, 0]
        line_objs = []
        payslip_ids = {}
        for register_id in register_ids:
            line_objs.extend(self.pool.get('hr2.payment.register').browse(cr, uid, register_id, context=context).payment_register_line_id)

        for line_obj in line_objs:
            if line_obj.payslip_id.id not in payslip_ids.keys():
                payslip_ids[line_obj.payslip_id.id] = [line_obj.id]
            else:
                payslip_ids[line_obj.payslip_id.id].append(line_obj.id)

        if obj.czy_uwzgledniac_planowane_wyplaty:
            for payslip_id in payslip_ids.keys():
                payslip_data = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['skladki_ZUS_pracownika', 'emr_pracodawca',
                                                                                       'rent_pracodawca', 'wyp_pracodawca', 'fp',
                                                                                       'fgsp', 'kwota_NFZ', 'kwota_US'], context=context)
                ZUS[0] += payslip_data['skladki_ZUS_pracownika'] + payslip_data['emr_pracodawca'] + payslip_data['rent_pracodawca'] + payslip_data['wyp_pracodawca']
                ZUS[1] += payslip_data['fp'] + payslip_data['fgsp']
                ZUS[2] += payslip_data['kwota_NFZ']
        else:
            for payslip_id, line_ids in payslip_ids.items():
                paid = []
                for line_id in line_ids:
                    if self.pool.get('hr2.payment.register.line').read(cr, uid, line_id, ['state'], context=context)['state'] == 'paid':
                        paid.append(line_id)

                for line in paid:
                    payslip_data = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['skladki_ZUS_pracownika', 'emr_pracodawca',
                                                                                           'rent_pracodawca', 'wyp_pracodawca', 'fp', 'fgsp',
                                                                                           'kwota_NFZ', 'kwota_US', 'do_wyplaty'], context=context)
                    amount_paid = self.pool.get('hr2.payment.register.line').read(cr, uid, line, ['amount'], context=context)['amount']
                    ratio = amount_paid / payslip_data['do_wyplaty']

                    ZUS[0] += (payslip_data['skladki_ZUS_pracownika'] + payslip_data['emr_pracodawca'] + payslip_data['rent_pracodawca'] + payslip_data['wyp_pracodawca']) * ratio
                    ZUS[1] += (payslip_data['fp'] + payslip_data['fgsp']) * ratio
                    ZUS[2] += (payslip_data['kwota_NFZ']) * ratio
        
        ##### ZUS #####
        # odejmowanie wartości zasiłków
                
        wz = self.pool.get('lacan.configuration').get_confvalue(cr, uid, 'Czy pracodawca sam wyplaca zasilki z ubezp. spol.')
        if wz:
            for payslip_id in payslip_ids.keys():
                payslip_lines_id=self.pool.get('hr2.payslip.line').search(cr, uid, [('payslip_id','=',payslip_id)], context=context)
                for line in payslip_lines_id:
                    val_line=self.pool.get('hr2.payslip.line').read(cr, uid, line, context=context)['value']
                    line_type=self.pool.get('hr2.payslip.line').read(cr, uid, line, context=context)['type_id']
                    if line_type and (line_type[0] in types_id):
                        ZUS[0] -= val_line
            liness = self.pool.get('hr2.payment.register.line').read(cr, uid, lmpreglines)
            for line2 in liness:
                if line2['amount'] <= 0:
                    ZUS[0] += line2['amount']
        
        description = [
            'Składki na ubezpieczenie społeczne za ' + str(obj.month_settled) + '/' + str(obj.year_settled) + '.',
            'Składki FP i FGŚP za ' + str(obj.month_settled) + '/' + str(obj.year_settled) + '.',
            'Składki na ubezpieczenie zdrowotne za ' + str(obj.month_settled) + '/' + str(obj.year_settled) + '.'
        ]
        line_ids = self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id', '=', ids[0])], context=context)
        for n in range(len(line_ids)):
            line_id = line_ids.pop()
            values = {
            'amount': ZUS[n],
            'state': 'unpaid',
            'description': description[n]
            }

            self.pool.get('hr2.payment.register.line').write(cr, uid, line_id, values, context=context)

        return True


    def przelicz_ponownie_us(self, cr, uid, ids, context=None):
        """Przelicza ponownie rejestr US"""
        obj = self.browse(cr, uid, ids[0], context=context)

        start_date = str(obj.year_settled) + '-' + str(obj.month_settled) + '-' + '01'
        end_date = str(self.pool.get('hr2.payroll.register').last_day_of_month(obj.year_settled, obj.month_settled))
        register_ids = self.pool.get('hr2.payment.register').search(cr, uid, [('planned_payment_date', '>=', start_date),
                                                                              ('planned_payment_date', '<=', end_date), ('group', '=', 'salary')],
                                                                    context=context)

        US = {}
        line_objs = []
        payslip_ids = {}
        for register_id in register_ids:
            line_objs.extend(self.pool.get('hr2.payment.register').browse(cr, uid, register_id, context=context).payment_register_line_id)

        for line_obj in line_objs:
            if line_obj.payslip_id.id not in payslip_ids.keys():
                payslip_ids[line_obj.payslip_id.id] = [line_obj.id]
            else:
                payslip_ids[line_obj.payslip_id.id].append(line_obj.id)

        if obj.czy_uwzgledniac_planowane_wyplaty:
            for payslip_id in payslip_ids.keys():
                payslip_data = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['kwota_US', 'etat_id', 'employee_id'], context=context)
                employee_obj = self.pool.get('hr.employee').browse(cr, uid, payslip_data['employee_id'][0], context=context)
                acc_nr = employee_obj.company_id.tax_office_id.account_number3

                if US.has_key(acc_nr):
                    US[acc_nr] += payslip_data['kwota_US']
                else:
                    US[acc_nr] = payslip_data['kwota_US']
        else:
            for payslip_id, line_ids in payslip_ids.items():
                paid = []
                for line_id in line_ids:
                    if self.pool.get('hr2.payment.register.line').read(cr, uid, line_id, ['state'], context=context)['state'] == 'paid':
                        paid.append(line_id)

                for line in paid:
                    payslip_data = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['kwota_US', 'etat_id', 'employee_id', 'do_wyplaty'],
                                                                     context=context)
                    employee_obj = self.pool.get('hr.employee').browse(cr, uid, payslip_data['employee_id'][0], context=context)
                    amount_paid = self.pool.get('hr2.payment.register.line').read(cr, uid, line, ['amount'], context=context)['amount']
                    ratio = amount_paid / payslip_data['do_wyplaty']

                    acc_nr = employee_obj.company_id.tax_office_id.account_number3

                    if US.has_key(acc_nr):
                        US[acc_nr] += payslip_data['kwota_US'] * ratio
                    else:
                        US[acc_nr] = payslip_data['kwota_US'] * ratio

        for line in US.items():
            description = 'Zaliczka na podatek dochodowy za ' + str(obj.month_settled) + '/' + str(obj.year_settled) + '.'
            values = {
                'payment_register_id': ids[0],
                'amount': line[1],
                'account_number': line[0],
                'state': 'unpaid',
                'description': description
                }
            if not self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id', '=', ids[0]), ('account_number', '=', line[0])],
                                                                     context=context):
                self.pool.get('hr2.payment.register.line').create(cr, uid, values, context=context)
            else:
                payment_line_id = self.pool.get('hr2.payment.register.line').search(cr, uid, [('payment_register_id', '=', ids[0]),
                                                                                              ('account_number', '=', line[0])], context=context)[0]
                self.pool.get('hr2.payment.register.line').write(cr, uid, payment_line_id, values, context=context)

        return True


    def close_payment_register(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)

        if not obj.czy_zaplacono:
            raise osv.except_osv(_('Błąd!'),_('Rejestr nie może zostać zamknięty, jeżeli posiada nieopłacone linie.'))
        else:
            self.write(cr, uid, ids[0], {'state': 'closed'}, context=context)
        return True


    def open_payment_register(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state': 'open'}, context=context)
        return True

hr2_payment_register()


class hr2_payment_register_line(osv.osv):
    _name = "hr2.payment.register.line"
    _inherit = 'company.related.class'


    def _get_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}

        for id in ids:
            state = 'unpaid'
            amount = self.read(cr, uid, id, ['amount'], context=context)['amount']
            payment_line_ids = self.pool.get('hr2.payment.register.payment.line').search(cr, uid, [('payment_register_line_id', '=', id)], context=context)

            paid = 0
            for payment_line_id in payment_line_ids:
                paid += self.pool.get('hr2.payment.register.payment.line').read(cr, uid, payment_line_id, ['amount'], context=context)['amount']

            if paid >= amount:
                state = 'paid'

            res[id] = state
        return res


    def _update_state_payment_line(self, cr, uid, ids, context=None):
        res = []

        for id in ids:
            if self.read(cr, uid, id, ['payment_register_line_id'], context=context)['payment_register_line_id']:
                res.append(self.read(cr, uid, id, ['payment_register_line_id'], context=context)['payment_register_line_id'][0])

        return res


    def _update_state_self(self, cr, uid, ids, context=None):
        return ids

    _columns = {
        'payslip_id': fields.many2one('hr2.payslip', 'Payslip'),
        'payment_register_id': fields.many2one('hr2.payment.register', 'Payment register', required=True, ondelete='cascade'),
        'amount': fields.float('Amount', required=True),
        'out_bank_id': fields.many2one('res.partner.bank', 'Bank'),
        'account_number': fields.char('Bank account number'),
        'state': fields.function(_get_state,
                                type='selection',
                                method=True,
                                selection=[('paid', 'Paid'),
                                           ('unpaid', 'Unpaid')],
                                string='State',
                                store = {
                                         'hr2.payment.register.payment.line': (_update_state_payment_line,
                                                                ['payslip_id',
                                                                'payment_register_id',
                                                                'amount',
                                                                'out_bank_id',
                                                                'payment_register_line_id'],
                                                                10),
                                         'hr2.payment.register.line': (_update_state_self,
                                                                ['amount'],
                                                                10),
                                         }
                                 ),
        'payment_register_payment_line_id': fields.one2many('hr2.payment.register.payment.line', 'payment_register_line_id', 'Payment register payment line'),
        'cash': fields.boolean('Cash'),
        'description': fields.text('Description'),
    }

    _defaults = {
        'state': 'unpaid',
    }


    def on_change_out_bank_id(self, cr, uid, ids, out_bank_id, context):
        """ Metoda, która w momencie zmiany banku na widoku sprawdza, czy etat/umowa cywilnpoprawna posiada wpisany bank.
            Jeżeli nie, to wpisuje tam bank ustawiony na widoku. """
        if ids:
            if self.read(cr, uid, ids[0], ['payslip_id'], context=context)['payslip_id']:

                etat_id = self.browse(cr, uid, ids[0], context=context).payslip_id.etat_id.id
                if etat_id:
                    if not self.pool.get('hr2.etat').read(cr, uid, etat_id, ['bank_id'], context=context)['bank_id']:
                        self.pool.get('hr2.etat').write(cr, uid, [etat_id], {'bank_id': out_bank_id}, context=context)
                else:
                    contract_id = self.browse(cr, uid, ids[0], context=context).payslip_id.cywilnoprawna_id.id
                    if not self.pool.get('hr2.contract').read(cr, uid, contract_id, ['bank_id'], context=context)['bank_id']:
                        self.pool.get('hr2.contract').write(cr, uid, contract_id, {'bank_id': out_bank_id}, context=context)

        if out_bank_id:
            account_number = self.pool.get('res.partner.bank').browse(cr, uid, out_bank_id, context=context).acc_number
        else:
            account_number = False

        return {'value': {'out_bank_id': out_bank_id, 'account_number': account_number}}

    def multisearch_hr2_payment_register_date(self, cr, uid, args_dict, context=None):
        '''Finds the payroll registers based on the date range specified by the user
        Registers have a hidden field (date_computed), based on the month and the year, always with the 1st day of the month
        To adapt to the situation, the multisearch ignores the day specified by the user, always setting it to '1' (only months and years count).
        @param cr: database cursor
        @param uid: user id
        @param args_dict: dictionary of filter values (containing one key, date_range, which is a list of two dates)
        @return: list of hr2.payroll.register ids fitting into requirements specified by the user
        '''
        date_range = args_dict.get('date', '')
        register_ids = []
        search_command = 'SELECT id from hr2_payment_register_payment_line WHERE'

        additional_commands = []
        attributes_list = []
        counter = 0
        if date_range:
            date_from = date_range[0] and datetime.strptime(date_range[0], tools.DEFAULT_SERVER_DATE_FORMAT)
            date_to = date_range[1] and datetime.strptime(date_range[1], tools.DEFAULT_SERVER_DATE_FORMAT)

            if date_from:
                date_from = datetime.strptime(str(date_from.year)+'-'+str(date_from.month)+'-01', tools.DEFAULT_SERVER_DATE_FORMAT).date() #Ignoring days by setting them to 1 by default
                additional_commands.append('date >= %s')
                attributes_list.append(str(date_from))
            if date_to:
                date_to = datetime.strptime(str(date_to.year)+'-'+str(date_to.month)+'-01', tools.DEFAULT_SERVER_DATE_FORMAT).date()
                additional_commands.append('date <= %s')
                attributes_list.append(str(date_to))

        #Gathering the data
        if additional_commands:
            for command in additional_commands:
                if counter > 0:
                    search_command += ' AND'
                search_command+=' '+command
                counter += 1

            attributes_list = tuple(attributes_list) #If additional_commands list isn't empty, attributes_list won't be as well
            cr.execute(search_command,attributes_list)
            register_ids = cr.fetchall()
            register_ids = zip(*register_ids) and zip(*register_ids)[0]
        return register_ids

    def get_employee_name_domain(self, cr, uid, payslip_id=None, context=None):
        if payslip_id:
            name = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['employee_id'], context=context)['employee_id'][0]
            name = self.pool.get('hr.employee').read(cr, uid, name, ['code'], context=context)['code']
            return name
        return False

    def build_context_for_line(self, cr, uid, payslip_id, payment_register_id, amount, account_number, out_bank_id, cash, context=None):
        context = context or {}
        ctx = context.copy()
        ctx.update({'payment_register_line_id': self.pool.get('hr2.payment.register.line').search(cr, uid, [('payslip_id','=',payslip_id)],
                                                                                            context=context)[0],
                    'payslip_id': payslip_id,
                    'payment_register_id': payment_register_id,
                    'account_number': account_number,
                    'out_bank_id': out_bank_id,
                    'cash': cash})

        cr.execute("SELECT SUM(amount) FROM hr2_payment_register_payment_line WHERE payment_register_line_id = {}"
                   .format(ctx['payment_register_line_id']))
        paid = cr.fetchone()
        if paid[0]:
            ctx['amount'] = amount - paid[0]
        return ctx

    def build_context_hr(self, cr, uid, payslip_id, context=None):
        '''Automatycznie wypełnia dane nt właściciela konta bankowego.'''
        context = context or {}
        ctx = context.copy()
        ctx['employee_bank'] = True

        if payslip_id:
            employee_id = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['employee_id'], context=context)['employee_id'][0]
            employee_data = self.pool.get('hr.employee').read(cr, uid, employee_id, ['address_home_id'], context=context)
            if employee_data['address_home_id']:
                address = self.pool.get('res.partner.address').read(cr, uid, employee_data['address_home_id'][0],
                                                                    ['street', 'zip', 'city', 'state_id', 'country_id'], context=context)

                if address['state_id']:
                    ctx['default_state_id'] = address['state_id'][0]
                if address['country_id']:
                    ctx['default_country_id'] = address['country_id'][0]
                ctx['default_street'] = address['street']
                ctx['default_city'] = address['city']
                ctx['default_zip'] = address['zip']
        return ctx


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for record in self.read(cr, uid, ids, ['payslip_id', 'amount', 'payment_register_id'], context=context):
            if not record['payslip_id']:
                record['payslip_id'] = record['payment_register_id']
            name = record['payslip_id'][1] + ', ' + str(record['amount'])
            res.append((record['id'], name))
        return res

hr2_payment_register_line()


class hr2_payment_register_payment_line(osv.osv):
    _name = "hr2.payment.register.payment.line"
    _inherit = 'company.related.class'

    _columns = {
        'payslip_id': fields.many2one('hr2.payslip', 'Payslip'),
        'payment_register_id': fields.many2one('hr2.payment.register', 'Payment register', required=True, ondelete='restrict'),
        'amount': fields.float('Amount', required=True),
        'out_bank_id': fields.many2one('res.partner.bank', 'Bank'),
        'payment_register_line_id': fields.many2one('hr2.payment.register.line', 'Payment register line', ondelete='set null'),
        'cash': fields.boolean('Cash'),
        'account_number': fields.char('Account number'),
        'date': fields.date('Date', required=True),
    }

    _defaults = {
        'date': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
        'payslip_id': lambda self, cr, uid, c: c.get('payslip_id', False),
        'payment_register_id': lambda self, cr, uid, c: c.get('payment_register_id', False),
        'payment_register_line_id': lambda self, cr, uid, c: c.get('payment_register_line_id', False),
        'cash': lambda self, cr, uid, c: c.get('cash', False),
        'out_bank_id': lambda self, cr, uid, c: c.get('out_bank_id', False),
        'account_number': lambda self, cr, uid, c: c.get('account_number', False),
        'amount': lambda self, cr, uid, c: c.get('amount', False),
    }

    
    def get_employee_name_domain(self, cr, uid, payslip_id=None, context=None):
        if payslip_id:
            name = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['employee_id'], context=context)['employee_id'][0]
            name = self.pool.get('hr.employee').read(cr, uid, name, ['code'], context=context)['code']
            return name
        return False

    def build_context_hr(self, cr, uid, payslip_id, context=None):
        """Automatycznie wypełnia dane nt właściciela konta bankowego."""
        context = context or {}
        ctx = context.copy()
        ctx['employee_bank'] = True

        employee_id = self.pool.get('hr2.payslip').read(cr, uid, payslip_id, ['employee_id'], context=context)['employee_id'][0]
        employee_data = self.pool.get('hr.employee').read(cr, uid, employee_id, ['address_home_id'], context=context)
        if employee_data['address_home_id']:
            address = self.pool.get('res.partner.address').read(cr, uid, employee_data['address_home_id'][0],
                                                                ['street', 'zip', 'city', 'state_id', 'country_id'], context=context)

            if address['state_id']:
                ctx['default_state_id'] = address['state_id'][0]
            if address['country_id']:
                ctx['default_country_id'] = address['country_id'][0]
            ctx['default_street'] = address['street']
            ctx['default_city'] = address['city']
            ctx['default_zip'] = address['zip']
        return ctx

    def on_change_out_bank_id(self, cr, uid, ids, out_bank_id, context):
        """ Metoda, która w momencie zmiany banku na widoku sprawdza, czy etat/umowa cywilnpoprawna posiada wpisany bank.
            Jeżeli nie, to wpisuje tam bank ustawiony na widoku. """
        if ids:
            if self.read(cr, uid, ids[0], ['payslip_id'], context=context)['payslip_id']:
                etat_id = self.browse(cr, uid, ids[0], context=context).payslip_id.etat_id.id
                if etat_id:
                    if not self.pool.get('hr2.etat').read(cr, uid, etat_id, ['bank_id'], context=context)['bank_id']:
                        self.pool.get('hr2.etat').write(cr, uid, [etat_id], {'bank_id': out_bank_id}, context=context)
                else:
                    contract_id = self.browse(cr, uid, ids[0], context=context).payslip_id.cywilnoprawna_id.id
                    if not self.pool.get('hr2.contract').read(cr, uid, contract_id, ['bank_id'], context=context)['bank_id']:
                        self.pool.get('hr2.contract').write(cr, uid, contract_id, {'bank_id': out_bank_id}, context=context)

        if out_bank_id:
            account_number = self.pool.get('res.partner.bank').browse(cr, uid, out_bank_id, context=context).acc_number
        else:
            account_number = False

        return {'value': {'out_bank_id': out_bank_id, 'account_number': account_number}}

hr2_payment_register_payment_line()


class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'employee_id': fields.many2one('hr.employee', _('Taxpayer')),
        'zus_id': fields.many2one('tax.office', 'ZUS'),
        'short_name':fields.char('Short name', size=31, required=True, help="Required by Płatnik app to be placed on the SII declarations")
    }
res_company()

class pit_11_positions(osv.osv):

    _name = 'pit.11.positions'
    _columns = {
                'name': fields.char('Name', size = 254, required = True),
                'number': fields.integer('Field number', required = True)
                }
    
pit_11_positions()

class edeclaration_choice(osv.osv):
    _inherit = 'edeclaration.choice'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Pracownik'),
    }

    def generate_tax_declaration_hr(self, cr, uid, ids, emp, context=None):
        '''Generates the edeclaration object and its lines,
        returning the view of declarations
        @param ids: Wizard_obj ids
        @return: id of the created tax.declaration object
        '''
        if not context:
            context = {}
        ctx = context.copy()

        # Creating the tax declaration
        wizard_obj = self.browse(cr, uid, ids[0], context=context)
        
        #Basic data
        values = {
            'name': wizard_obj.edeclaration_id.name,
            'version': wizard_obj.edeclaration_id.version,
            'date': time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),           
            'tax_version_id': wizard_obj.edeclaration_id.id,
        }
        
        #Year and tax payer type
        if 'PIT' in wizard_obj.edeclaration_id.name:
            values['year'] = wizard_obj.fiscalyear_id.name
            ctx['payer_type'] = wizard_obj.tax_payer_type
        else:
            values['year'] =  wizard_obj.period_id[0].fiscalyear_id.name
        values['tax_payer_type'] = wizard_obj.edeclaration_id.tax_payer_type
        #Extracting the number from the year string   
        if len(values['year']) != 4:
            values['year'] = re.search('([0-9]{4})', values['year']).group(0)
        #Period(no period for period_type = year
        if wizard_obj.period_type == 'quarter':
            period_ids = [period.id for period in wizard_obj.period_id]
            if len(period_ids) < 3:
                self.generate_quarter_periods(cr, uid, period_ids, context=context) # 3 months generated when needed for data gathering
            values['period'] = self.fetch_quarter(cr, uid, period_ids, context=context) # Quarter only for the form/xml, not used for data
        elif wizard_obj.period_type == 'month':
            values['period'] = int(wizard_obj.period_id[0].date_start[5:7])

        #Partner and employee (hr fields)
        values['partner_id'] = wizard_obj.company_id.partner_id.id
        values['employee_id'] = emp
        
        tax_declaration_id = self.pool.get('tax.declaration').create(cr, uid, values, context=context)

        # Checking the month validity, sorting (in the case of quarter)
        # and preparing periods for passing in the context
        if wizard_obj.edeclaration_id.period_type == 'month':
            if len(wizard_obj.period_id) != 1:
                raise osv.except_osv(_('Error!'), _('This declaration requires a single period to be selected!'))

        elif wizard_obj.edeclaration_id.period_type == 'quarter':
            # Generating three months for fetching data in case
            # User has selected only one or two months
            kwartal_data = [{'id': period.id, 'name': period.name} for period in wizard_obj.period_id]
            kwartal_data = sorted(kwartal_data, key=lambda kwartal_period: kwartal_period['name'][:2])
            sorted_periods = [x['id'] for x in kwartal_data]


        self.edecl_pit11_23(cr, uid, tax_declaration_id, context=ctx)

        #Hiding the period if the report is for entire year
        if wizard_obj.period_type == 'year':
            context['type_year'] = True
                                                            
        return tax_declaration_id

    def confirm_hr(self, cr, uid, ids, context=None):
        """Wyświetla kolejny stan wizarda
        @return: słownik kolejnego stanu wizarda
        """
        if isinstance(ids, list):
            ids = ids[0]
        name = self.pool.get('edeclaration.choice').browse(cr, uid, ids).edeclaration_id.name
        if not context:
            context = {}
        if 'PIT' in name:
            context['pit'] = True
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('model', '=', 'edeclaration.choice'),
                                                                  ('name', '=', 'edeclaration.choice.parameters.form.hr')])

        return {
            'name': _('Wybór e-deklaracji'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'edeclaration.choice',
            'res_id': ids,
            'view_id': view_id,
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new'
            }    
       
    def confirm2_hr(self, cr, uid, ids, context=None):
        """Generates edeclaration based on the data from the wizards
        and opens the tax.declaration form view
        @param ids: wizard id
        @return: tax.declaration form view with a freshly-generated declaration
        """
        if not context:
            context = {}
        emp_pool = self.pool.get('hr.employee')
        usr_pool = self.pool.get('res.users')   
        usr = usr_pool.browse(cr, uid, uid)   
        partner_contact_pool = self.pool.get('res.partner.contact') 
        partner_address_pool = self.pool.get('res.partner.address')
        wizard_obj = self.browse(cr, uid, ids[0], context=context)
        
        year = wizard_obj.fiscalyear_id.name
        if len(year) != 4:
            year = re.search('([0-9]{4})', year).group(0)
        
        #Selecting the appriopriate employees
        cr.execute('''
            SELECT DISTINCT id
            FROM   (SELECT he.id
                    FROM   hr2_etat hre
                           JOIN hr_employee he
                             ON he.id = hre.employee_id
                    WHERE  hre.discharge_date IS NULL
                           AND EXTRACT(year FROM hre.sign_date) <= {0}
                            OR EXTRACT(year FROM hre.discharge_date) >= {0}
                    UNION ALL
                    SELECT he.id
                    FROM   hr2_contract hrc
                           JOIN hr_employee he
                             ON he.id = hrc.employee_id
                    WHERE  hrc.rok_rozliczenia = {0}) t1 '''.format(int(year)))
        emp_ids = cr.fetchall()
        if not len(emp_ids):
            raise osv.except_osv('Błąd!', 'Brak danych na wybrany rok podatkowy')
        emp_ids = (x[0] for x in emp_ids)

        tax_declaration_list = []
        for emp in emp_ids:
            tax_declaration_id = self.generate_tax_declaration_hr(cr, uid, ids, emp, context=context)
            tax_declaration_list.append(tax_declaration_id)
        
        tree_view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'lacan_edeclaration',
                                                                      'lacan_tax_declaration_tree')[1]
        form_view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll_pl',
                                                                      'hr_declaration_form')[1]                                                                                                                                
        decl_name = wizard_obj.edeclaration_id.name+" "+str(wizard_obj.edeclaration_id.version)  
                      
        return {
            'name': 'Deklaracje',
            'domain': [('id','in',tuple(tax_declaration_list))],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'tax.declaration',
            'views': [(tree_view_id,'tree'),(form_view_id,'form')],
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'current',
            }

        
    def edecl_pit11_23(self, cr, uid, tax_declaration_id, context=None):
        '''Prepares the data for PIT11 version 23 tax_declaration and creates its lines
        @param declaration_id: Declaration ID for which the method creates new lines
        @param emp: id of the employee
        @return: ids of created lines
        '''
        line_ids = []
        declaration = self.pool.get('tax.declaration').browse(cr, uid, tax_declaration_id)
        pit_11_positions = self.pool.get('pit.11.positions')
        partner_contact_pool = self.pool.get('res.partner.contact')
        payslip_pool = self.pool.get('hr2.payslip')
        usr = self.pool.get('res.users').browse(cr, uid, uid)
        emp_pool = self.pool.get('hr.employee')
        partner_id = declaration.partner_id.id
        emp_id = declaration.employee_id.id
        tax_payer = context.get('payer_type') 
        #Getting the employees data
        end_year_date = declaration.year+'-12-31'
        x='''            
            SELECT hd.CODE             AS "5",
                   hd.employee_name     AS "16",
                   hd.surname           AS "15",
                   CASE
                     WHEN he.sinid IS NOT NULL THEN he.sinid
                     WHEN he.ssnid IS NOT NULL THEN he.ssnid
                     WHEN he.passport_id IS NOT NULL THEN '9999999999'
                     ELSE ''
                   END                  AS "11",
                   he.passport_id       AS "12",
                   rc.NAME              AS "14",
                   he.birthday          AS "17"
            FROM   hr_employee AS he
                   LEFT JOIN res_country rc
                          ON rc.id = he.passport_country
                   JOIN (SELECT *
                         FROM   (SELECT DISTINCT ON (h1.employee_id) h1.employee_id,
                                                                     h1.employee_name,
                                                                     h1.surname,
                                                                     tof.CODE
                                 FROM   hr2_employee_data h1
                                        LEFT JOIN tax_office tof
                                               ON tof.id = h1.tax_office_id
                                 WHERE  h1.date_from <= '{0}'
                                 ORDER  BY h1.employee_id,
                                           h1.date_from DESC) t1
                         UNION
                         SELECT *
                         FROM  (SELECT DISTINCT ON (h1.employee_id) h1.employee_id,
                                                                    h1.employee_name,
                                                                    h1.surname,
                                                                    tof.CODE
                                FROM   hr2_employee_data h1
                                       LEFT JOIN tax_office tof
                                              ON tof.id = h1.tax_office_id
                                WHERE  h1.date_from >= '{0}'
                                ORDER  BY h1.employee_id,
                                          h1.date_from) t2) hd
                     ON hd.employee_id = he.id
            WHERE  hd.employee_name IS NOT NULL
                   AND hd.employee_id = {1}'''.format(end_year_date,emp_id)

        cr.execute(x) 
        emp_data = cr.dictfetchone()   
        
        #Writing the data
        if not emp_data:
            return False
            raise osv.except_osv('Błąd!', 'Brak danych pracownika \'{}\', aktualnych na wybrany rok podatkowy'.format(declaration.employee_id.name))
        
        for key in emp_data:
            #Field name
            position_id = pit_11_positions.search(cr, uid, [('number', '=', int(key))])
            name = pit_11_positions.browse(cr, uid, position_id[0]).name
                
            if int(key) == 12:
                if emp_data['11'] == '9999999999':   # employee doesn't have  vat or pesel
                                                     # so passport is used for declaration.
                    val13 = 3       # passport selection id
                else:
                    emp_data['12'] = ''
                    val13 = False           
                #Field 13
                position13_id = pit_11_positions.search(cr, uid, [('number', '=', 13)])
                name13 = pit_11_positions.browse(cr, uid, position13_id[0]).name    
                line_data = {
                'field_id': 13,
                'field_name': name13,
                'tax_declaration_id': tax_declaration_id,
                'field_type': 'integer',
                'field_valuei': val13
                 }
                line_ids.append(self.pool.get('tax.declaration.data').create(cr, uid, line_data, context=context))  
                
                         
            line_data = {
            'field_id': int(key),
            'field_name': name,
            'tax_declaration_id': tax_declaration_id,
            'field_type': 'string',
            'field_txt': emp_data[key] or ''
             }
            line_ids.append(self.pool.get('tax.declaration.data').create(cr, uid, line_data, context=context))           
        #Getting the partner data       
        if tax_payer == 'company':
            number = 8           
            field = (usr.company_id.name or '') + ',' + (usr.company_id.regon or '')
            number2 = 9
            field2= ''
        elif tax_payer == 'employee':
            number = 9            
            partner_contact_id = partner_contact_pool.search(cr, uid, [('partner_id', '=', partner_id)])
            if not len (partner_contact_id):
                raise osv.except_osv('Błąd!', 'Brak partnera!')
            partner_contact = partner_contact_pool.browse(cr, uid, partner_contact_id[0])
            if not partner_contact:
                field = ''
            else:
                field = partner_contact.name or '' + partner_contact.first_name or '' + partner_contact.birtdate or ''
            number2 = 8
            field2= ''
            
        #Names of field 1,8,9
        position_1_id = pit_11_positions.search(cr, uid, [('number', '=', 1)])
        name1 = pit_11_positions.browse(cr, uid, position_1_id[0]).name
        position_f_id = pit_11_positions.search(cr, uid, [('number', '=', number)])
        namef = pit_11_positions.browse(cr, uid, position_f_id[0]).name
        position2_f_id = pit_11_positions.search(cr, uid, [('number', '=', number2)])
        namef2 = pit_11_positions.browse(cr, uid, position2_f_id[0]).name      
        payer_data = {1: (name1, declaration.partner_id.vat), number: (namef, field), number2: (namef2, field2)}
        
        #First, eigth and ninth field 
        for key in payer_data:
                  
            line_data = {
            'field_id':key,
            'field_name': payer_data[key][0],
            'tax_declaration_id': tax_declaration_id,
            'field_type': 'string',
            'field_txt': payer_data[key][1]
             }
            line_ids.append(self.pool.get('tax.declaration.data').create(cr, uid, line_data, context=context))                
        #Getting the res_partner_address_data - data which was correct at the end of year      
        cr.execute('''SELECT CASE WHEN address_home_id IS NOT NULL THEN address_home_id
                    WHEN address_reg_id IS NOT NULL THEN address_reg_id 
                    WHEN address_cor_id IS NOT NULL THEN address_cor_id END 
                    FROM hr2_employee_data 
                    WHERE employee_id = {} 
                    AND date_from <= '{}' 
                    ORDER BY date_from DESC
                    LIMIT 1
                   '''.format(emp_id, end_year_date)) 
        address_id = cr.fetchone()
        if not address_id or None in address_id:
            address_data = {number:'' for number in range(18,28)}
        else:
            cr.execute('''
                SELECT rc.code as "18",
                       rcs.name as "19",
                       rpa.county as "20",
                       rpa.municipality as "21",
                       rpa.street as "22",
                       rpa.street2 as "23",
                       rpa.flat_number as "24",
                       rpa.city as "25",
                       rpa.zip as "26",
                       rpa.post_office as "27"
                FROM   res_partner_address rpa
                       LEFT JOIN res_country rc
                              ON rc.id = rpa.country_id
                       LEFT JOIN res_country_state rcs
                              ON rcs.id = rpa.state_id
                WHERE  type = 'default'
                       AND rpa.id = {}                
                       '''.format(address_id[0]))
            address_data = cr.dictfetchone()
        for key in address_data:
            position_id = pit_11_positions.search(cr, uid, [('number', '=', int(key))])
            name = pit_11_positions.browse(cr, uid, position_id[0]).name      
            line_data = {
                'field_id':key,
                'field_name': name,
                'tax_declaration_id': tax_declaration_id,
                'field_type': 'string',
                'field_txt': address_data[key]
            }
            line_ids.append(self.pool.get('tax.declaration.data').create(cr, uid, line_data, context=context))
                    
        # Getting the float data for last part of declaration.
        field_dict = {number: 0.00 for number in
                      [10, 29, 30, 31, 34, 35, 33, 49, 50, 51, 52, 57, 58, 59, 60, 61, 66, 67, 69, 70, 72]}
        field_dict[6] = 1
        field_dict[76] = 2
        cfg_pool = self.pool.get('lacan.configuration')
        conf_val = cfg_pool.get_confvalue(cr, uid, 'Granica kwoty umowy cywilnoprawnej do podatku zryczaltowanego',
                                          data_str=context.get('employee_list_date', False), context=context)
        rodzaj_obowiazku_podatkowego_value = cfg_pool.get_confvalue(cr, uid, 'Rodzaj obowiązku podatkowego płatnika', context=context)
        
        if rodzaj_obowiazku_podatkowego_value in [1,2]:
            field_dict[10] = rodzaj_obowiazku_podatkowego_value
        else:
            raise osv.except_osv(_('Błąd!'),_("Nieprawidłowa wartość parametru 'Rodzaj obowiązku podatkowego płatnika'. Należy wprowadzić wartość 1 lub 2."))
        
        #Type swiadczenia nieodplatne
        add_id = self.pool.get('hr2.salary.addition.type').search(cr, uid, 
                                [('name', '=', 'Świadczenie nieodpłatne'),('company_id', '=', usr.company_id.id )])
 
        cr.execute('''
            SELECT DISTINCT hp.id
            FROM   hr2_payslip hp
                   LEFT JOIN hr2_payroll_register hpr
                     ON hp.register_id = hpr.id
                   LEFT JOIN hr2_payment_register_payment_line AS pl
                     ON pl.payslip_id = hp.id
            WHERE  Extract(year FROM pl.date) = {}
                   AND hp.employee_id = {}
                   AND hpr.state IN ('confirmed', 'closed')'''.format(declaration.year, emp_id))
        payslip_ids = [x[0] for x in cr.fetchall()]
        payslips = payslip_pool.browse(cr, uid, payslip_ids)     
        for payslip in payslips:
            if payslip.brutto:
                # Najpierw ustalam współczynnik przychodu z praw autorskich w całym przychodzie
                revenue_to_move = payslip.koszty_uzyskania_autorskie * 2 / (1 - payslip.skladki_ZUS_pracownika / payslip.brutto) / payslip.brutto
                revenue_to_move = payslip.brutto * revenue_to_move
            elif payslip.koszty_uzyskania:
                revenue_to_move = 0.0
            else:
                continue
            
            if payslip.etat_id:
                field_dict[29] += self.include_external_tax(cr, uid, payslip.brutto - revenue_to_move, payslip)
                field_dict[30] += payslip.koszty_uzyskania - payslip.koszty_uzyskania_autorskie
                field_dict[33] += round(payslip.kwota_US)
                field_dict[34] += revenue_to_move
                field_dict[35] += payslip.koszty_uzyskania_autorskie
                payslip_lines = payslip.payslip_line_ids
                                   
            if payslip.cywilnoprawna_id and payslip.brutto > conf_val:
                if payslip.cywilnoprawna_id.procent_uzyskania == 50:
                    field_dict[59] += round(payslip.kwota_US)
                else:
                    field_dict[52] += round(payslip.kwota_US)
                
                field_dict[49] += payslip.brutto - revenue_to_move
                field_dict[50] += payslip.koszty_uzyskania - payslip.koszty_uzyskania_autorskie
                field_dict[60] += revenue_to_move
                field_dict[61] += payslip.koszty_uzyskania_autorskie

            field_dict[70] += payslip.skladki_ZUS_pracownika
            field_dict[72] += payslip.skladka_zdrowotna_odliczona

        field_dict[51] += field_dict[49] - field_dict[50]
        field_dict[58] += field_dict[57] - field_dict[61]
        field_dict[31] = field_dict[29] + field_dict[34] - field_dict[30] - field_dict[35]   
        
        #Fields 66 and 67
        if len(add_id):
            add_id = add_id[0]
            cr.execute('''SELECT SUM(base) 
                    FROM hr2_payslip_line 
                    WHERE addition_type = {} 
                    AND payslip_id IN {}'''.format(add_id, ids_for_execute(payslip_ids)))
            add_val = cr.fetchone()
            if add_val[0]:
                field_dict[66] = add_val[0]
                benefits_tax = round(0.18 * add_val[0])
                if benefits_tax < field_dict[33]:
                    field_dict[69] = benefits_tax
                    field_dict[33] -= benefits_tax
                elif field_dict[33] > 0:
                     field_dict[69] = field_dict[33]
                     field_dict[33] = 0
        
                #Multiplicative boolean data
        if field_dict[30] == 0.00:
            field_dict[28] = 0
        else:
            cr.execute('''SELECT hp.id from hr2_payslip hp
                LEFT JOIN hr2_payroll_register hpr ON hp.register_id = hpr.id               
                WHERE hpr.register_year = {} AND hp.employee_id = {} AND hp.etat_id IS NOT NULL
                ORDER BY hpr.register_month DESC'''.format(int(declaration.year), emp_id))
            latest_payslip = cr.fetchone()
            koszty_uzyskania = self.pool.get('hr2.payslip').browse(cr, uid, latest_payslip[0]).etat_id.koszty_uzyskania
            if koszty_uzyskania == 'standardowe':
                field_dict[28] = 1
            elif koszty_uzyskania == 'podwyzszone':
                field_dict[28] = 3
            else:
                field_dict[28] = 0
         
        for key in field_dict:
            position_id = pit_11_positions.search(cr, uid, [('number', '=', key)])
            name = pit_11_positions.browse(cr, uid, position_id[0]).name
            if key in [6,10,28,33,38,42,45,48,52,56,59,65,69,76]:
                line_data = {
                    'field_id': key,
                    'field_name': name,
                    'tax_declaration_id': tax_declaration_id,
                    'field_type': 'integer',
                    'field_valuei': field_dict[key]
                    }
            else:
                line_data = {
                    'field_id': key,
                    'field_name': name,
                    'tax_declaration_id': tax_declaration_id,
                    'field_type': 'float',
                    'field_value': field_dict[key]
                    }

            line_ids.append(self.pool.get('tax.declaration.data').create(cr, uid, line_data, context=context))
        return line_ids

    def include_external_tax(self, cr, uid, value, payslip_obj):
        """ Hook dla modułu hr_abroad_employees. """
        return value

edeclaration_choice()

class lacan_edeclaration_version(osv.osv):
    _name = 'lacan.edeclaration.version'
    _inherit = 'lacan.edeclaration.version'
    _description = 'Wersja e-deklaracji'

    def get_render_config_hr(self, cr, uid, tax_declaration_id, template=None, data=None, context=None):
        """Prepares the data for edeclaration .xml file.
        Data is fetched from the tax.declaration object
        
        @param tax_declaration_id: tax_declaration object id
        @param template: Template to be used for generating the .xml
        @param data: additional data
        @return: render data for creating the xml
        """
        if not context:
            context = {}
        render_data = {}
        tax_declaration_obj = self.pool.get('tax.declaration').browse(cr, uid, tax_declaration_id, context=context)

        # Fetching general data of the tax declaration

        year = tax_declaration_obj.year
        #Value for field number 7
        if tax_declaration_obj.tax_payer_type == 'company':
            val7 = 1
        else:
            val7 = 2
        pouczenie = "Za uchybienie obowiązkom płatnika grozi odpowiedzialność przewidziana w Kodeksie karnym skarbowym."
        oswiadczenie = """Oświadczam, że są mi znane przepisy Kodeksu karnego skarbowego o odpowiedzialności za podanie \
            danych niezgodnych z rzeczywistością."""
        render_data.update({
            'year': year,
            'tax_payer_type': val7,
            'oswiadczenie': oswiadczenie,
            'pouczenie': pouczenie,
        })

        # Fetching the data of the lines
        line_ids = self.pool.get('tax.declaration.data').search(cr, uid, [('tax_declaration_id', '=', tax_declaration_id)], context=context)
        for line in self.pool.get('tax.declaration.data').browse(cr, uid, line_ids, context=context):
            key = str(line.field_id)
            if line.field_id == 11:
                key += len(line.field_txt) == 11 and 'pesel' or 'nip' 
            if line.field_type == 'integer':
                if (line.field_id in [6,10,76] and line.field_valuei not in [1,2]) \
                or (line.field_id == 13 and line.field_valuei not in [0,1,2,3,4,8,9]):
                    name = self.pool.get('hr.employee').read(cr, uid, tax_declaration_obj.employee_id.id, ['name'], context=context)['name']
                    raise osv.except_osv('Błąd!', 'Nieprawidłowa wartość w rubryce %s deklaracji dla użytkownika %s!' % (line.field_id, name))
                if line.field_id in [13, 28] and line.field_valuei in [0]:
                    render_data[str(line.field_id)] = ''
                else:
                    render_data[key] = line.field_valuei
            
            elif line.field_type == 'float':
                render_data[key] = line.field_value
                    
            elif line.field_type == 'string':
                render_data[key] = line.field_txt or ''
                       
        data['fields2'] = {}
        
        return render_data

lacan_edeclaration_version()

class hr2_config_prog_podatkowy(osv.osv):
    _name = "hr2.config.prog.podatkowy"
    _inherit = 'company.related.class'

    def name_get(self,cr,uid,ids,context=None):
        reads = self.read(cr, uid, ids, ['year'], context=context)
        res = []
        for record in reads:
            name = 'Konfiguracja progów ' + str(record['year'])
            res.append((record['id'], name))
        return res

    def _get_names(self, cr, uid, ids, field_name, arg, context=None):
        """Function used to fill 'name' function fields"""
        result = {}
        for record in self.read(cr, uid, self.search(cr, uid, [], context=context), ['year'], context=context):
            result[record['id']] = 'Konfiguracja progów ' + str(record['year'])
        return result

    _columns = {
                'year':fields.integer('Rok'),
                'prog_line_ids':fields.one2many('hr2.config.prog.podatkowy.line','prog_id','Progi podatkowe'),
                'name': fields.function(_get_names, method=True, type='char', string="Name"),
                }

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        ids = []
        if name and str(name).startswith('Konfiguracja progów '):
            part_id = int(name.split(' ')[2])
            ids = self.search(cr, user, [('year','=',part_id)], context=context, limit=limit)
        if name and len(str(name)) == 4:
            ids = self.search(cr, user, [('year','=',name)], context=context, limit=limit)
        if not name:
            ids = self.search(cr, user,[('year','!=',0)] ,context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

hr2_config_prog_podatkowy()


class hr2_config_prog_podatkowy_line(osv.osv):
    _name = "hr2.config.prog.podatkowy.line"
    _inherit = 'company.related.class'
    _columns = {
                'prog_id':fields.many2one('hr2.config.prog.podatkowy', 'Prog podatkowy'),
                'value_from':fields.float('Wartość od której zaczyna się próg'),
                'percent':fields.integer('Procent'),
                }
hr2_config_prog_podatkowy_line()


class hr2_config_prog_kwota_wolna(osv.osv):
    _name = "hr2.config.kwota.wolna"
    _inherit = 'company.related.class'
    _columns = {
        'name': fields.integer('Rok', nosep=True, required=True),
        'prog_line_ids': fields.one2many('hr2.config.kwota.wolna.line', 'prog_id', 'Progi kwoty wolnej'),
    }

    def get_list(self, cr, uid, year, context=None):
        prog_ids = self.search(cr, uid, [('name', '=', year)], context=context)
        if not prog_ids:
            return []

        prog_obj = self.browse(cr, uid, prog_ids[0], context=context)
        return [[line_obj.value_from, line_obj.amount, line_obj.transition] for line_obj in prog_obj.prog_line_ids]

hr2_config_prog_kwota_wolna()


class hr2_config_prog_kwota_wolna_line(osv.osv):
    _name = "hr2.config.kwota.wolna.line"
    _inherit = 'company.related.class'
    _columns = {
        'prog_id': fields.many2one('hr2.config.kwota.wolna', required=True),
        'value_from': fields.float('Wartość od której zaczyna się próg'),
        'amount': fields.float('Kwota pomniejszenia'),
        'transition': fields.boolean('Przedział przejściowy'),
    }

hr2_config_prog_kwota_wolna_line()


class wizard_correct_payslip(osv.osv_memory):
    """Informs a user which payslip lines require correction"""

    _name = 'wizard.correct.payslip'
    _columns = {
                    'information':fields.text('Information')
                }


wizard_correct_payslip()


class hr2_employee_data(osv.osv):
    _name = "hr2.employee.data"
    _description = "Historia danych pracownika"
    _inherit = 'hr2.employee.data'

    def init(self,cr):
        '''
        Adds a trigger to database.
        Trigger update employee surname when new record of the employee data is add
        '''
        cr.execute("""SELECT lanname FROM pg_language WHERE lanname ='plpgsql'""")
        language = cr.fetchall()
        if not language:
            cr.execute('CREATE LANGUAGE plpgsql')

        cr.execute("""
                CREATE OR REPLACE FUNCTION function_trigger_update_surname() RETURNS trigger AS $$
                BEGIN
                    UPDATE hr_employee SET surname = NEW.surname WHERE id = NEW.employee_id;
                    UPDATE res_partner_address AS rpa SET employee_id = NEW.employee_id 
                                                WHERE rpa.id IN (NEW.address_home_id, NEW.address_reg_id, NEW.address_cor_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
                """)
        cr.execute("""SELECT tgname FROM pg_trigger WHERE tgname='hr_employee_update_surname'""")
        trigger = cr.fetchall()
        if not trigger:
            cr.execute("""CREATE TRIGGER hr_employee_update_surname AFTER INSERT ON hr2_employee_data
                            FOR ROW
                            EXECUTE PROCEDURE function_trigger_update_surname();""")
        return True

    _columns =  {
                   'address_reg_id':fields.many2one('res.partner.address', 'Adres zameldowania'),
                   'address_cor_id':fields.many2one('res.partner.address', 'Adres korespondencyjny'),
                   'nfz_id':fields.many2one('hr2.nfz', 'Kod oddziału NFZ'),
                 }

hr2_employee_data()

class tax_declaration(osv.osv):

    _name = "tax.declaration"
    _inherit = 'tax.declaration'

    _columns = {
        'employee_id': fields.many2one('hr.employee', _('Taxpayer')),
        'partner_id': fields.many2one('res.partner', _('Taxpayer')),
    }


tax_declaration()
    
    
class hr2_overtime(osv.osv):
    
    _name = "hr2.overtime"
    _description = "Godziny nadliczbowe"
    
    _columns = {
                'employee_id': fields.many2one('hr.employee', 'Pracownik', required=True),
                'company_id': fields.many2one('res.company', 'Firma', required=True),
                'department_id':fields.related('employee_id', 'department_id', string='Dział', type='many2one', relation='hr2.dzial', readonly=True, store=True),
                'date_from': fields.datetime('Data od', required=True),
                'date_to': fields.datetime('Data do', required=True),
                'hours': fields.float('Liczba godzin', required=True),
                'state': fields.selection([('draft','Projekt'),('approved','Zatwierdzony'),('cancel','Anulowany'),('closed','Zamknięty')], 'Stan', readonly=True),    
                }
    
    _defaults = {
                 'state': 'draft',
                 'date_from': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
                 'date_to': lambda *a: time.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
                 'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
                 }
    
    
    def name_get(self,cr,uid,ids,context=None):
        if not ids:
            return []

        overtime_objs = self.browse(cr,uid,ids,context=context)
        date_from = lacan_tools.date_convers_time_zones(overtime_objs[0].date_from, 'UTC', context.get('tz', 'UTC'))
        date_to = ' - ' + lacan_tools.date_convers_time_zones(overtime_objs[0].date_to, 'UTC', context.get('tz', 'UTC'))[:10]

        return [(overtime_obj.id, overtime_obj.employee_id.name + ', ' + date_from[:10] + date_to + ', ' + str(int(overtime_obj.hours))) for overtime_obj in overtime_objs]
    
    
    def get_employees(self, cr, uid, employee_id, context=None):
        '''Metoda dynamicznej domeny wybierajaca id pracowników, którzy przypisani są do działu, 
        którego managerem jest zalogowany user. 
        Taki warunek tylko w przypadku, jeśli zalogowany użytkownik należy do grupy dept manager'''
        
        if not context: context={}
        
        # zwrócenie listy uzytkowników należących do grupy dept manager
        cr.execute("SELECT uid FROM res_groups_users_rel WHERE gid IN (SELECT res_id FROM ir_model_data WHERE name = 'group_hr_manager')")
        users = map(lambda x: x[0], cr.fetchall())
        
        if uid in users or uid == 1:
            all_employees = self.pool.get('hr.employee').search(cr, uid, [], context=context)
            
            return all_employees
        
        # zwrócenie listy pracowników przypisanych do działu, którego managerem jest zalogowany user
        cr.execute("SELECT id FROM hr_employee WHERE department_id IN \
                    (SELECT id FROM hr2_dzial WHERE \
                    manager_id IN (SELECT id FROM resource_resource WHERE user_id = %s))", (uid,))
        employees = map(lambda x: x[0], cr.fetchall())
        
        return employees
    
    
    def get_user_group_or_state(self, cr, uid, state, context=None):
        '''Metoda dynamicznych attrsów sprawdzajaca, czy stan jest approved albo close 
        lub jeśli jest cancel to czy user należy do grupy dept_manager'''
        
        if not context: context = {}
        
        if state in ['approved','closed']:
            return True
        
        if uid == 1:
            return False
        
        if state == 'cancel':
            cr.execute("SELECT uid FROM res_groups_users_rel WHERE gid = (SELECT res_id FROM ir_model_data WHERE name = 'group_dept_manager')")
            users = map(lambda x: x[0], cr.fetchall())
        
            if uid in users:
                return True
        
        return False
    
    
    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        '''Metoda sprawdzajaca czy pracownik jest zatrudniony w dziale kierownika, 
           jeśli uzytkownik uzupełniający nadgodziny jest kierownikiem'''
        
        if not context: context = {}
        
        # zwróć listę pracowników, którym zalogowany user moze wprowadzić nadgodziny
        employees = self.get_employees(cr, uid, employee_id, context=context)
        
        if employee_id in employees:
            
            result = { 'value': 
                            {'employee_id' : employee_id}
                    }
        else:
            result = { 'value': 
                            {'employee_id' : False}
                    }
        
        return result
    
    
    def onchange_date(self, cr, uid, ids, date_from, date_to, context=None):
        '''Metoda wyliczająca ilość godzin do pola hours przy zmianie Daty od lub Daty do'''
        
        if not context: context = {}
        
        d_from = datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        d_to = datetime.strptime(date_to, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        
        diff = relativedelta.relativedelta(d_to, d_from)
        
        if diff.years:
            days = (d_to - d_from).days
        else:
            days = diff.days
            
        hours = diff.hours + days*24
        
        if hours < 0:
            hours = 0
        
        result = { 'value': 
                        {'hours' : hours}
                }
        
        return result
    
    
    def check_permission_range(self, cr, uid, ids, context=None):
        """ Funkcja sprawdzajaca czy użytkownik ma odpowiednie uprawnienia do zatwierdzania/odrzucania nadgodzin"""
        
        query_user = """
        SELECT 
            lacan_right.lacan_hr2_overtime_company_id as lr_company_id, lacan_right.lacan_hr2_overtime_department_id as lr_dzial_id
        FROM
            lacan_right
        WHERE
            right_categ_id
        IN
            (SELECT right_cat_id FROM ir_model_right_category_rel 
            WHERE 
                model_id 
            IN (SELECT id FROM ir_model WHERE model= (%s)))
        AND 
            user_id = (%s)
        AND
            perm_field_hr2_overtime_accept like 'True';
        """
        cr.execute(query_user,(self._name, uid))
        lac_right_user = cr.dictfetchall()
        hr_abs_dict = self.read(cr, uid, ids, ['department_id','company_id'])[0]
        if lac_right_user:
            for r_di in lac_right_user:
                if r_di.get('lr_dzial_id', False):
                    if r_di['lr_dzial_id'] == hr_abs_dict['department_id'][0]:
                        pass
                    else:
                        raise osv.except_osv(_('Nieprawidłowy dział'), _('Nie możesz dokonywać akcji dla tego działu'))
                if r_di.get('lr_company_id', False):
                    if r_di['lr_company_id'] == hr_abs_dict['company_id'][0]:
                        pass
                    else:
                        raise osv.except_osv(_('Nieprawidłowa firma'), _('Nie możesz dokonywać akcji dla tej firmy'))
            return True
            
        query_group = """
                    SELECT id, lacan_right.lacan_hr2_overtime_company_id as lr_company_id, lacan_right.lacan_hr2_overtime_department_id as lr_dzial_id
                        FROM lacan_right WHERE right_categ_id IN (SELECT right_cat_id 
                                                                    FROM 
                                                                        ir_model_right_category_rel 
                                                                    WHERE 
                                                                        model_id 
                                                                    IN (SELECT id FROM ir_model WHERE model = (%s))) AND 
                                                                        (group_id IN (SELECT gid FROM res_groups_users_rel WHERE uid = (%s)))
                        AND perm_field_hr2_overtime_accept LIKE 'True'; 
        """
        cr.execute(query_group,(self._name, uid))
        lac_right_group = cr.dictfetchall()
        hr_abs_dict = self.read(cr, uid, ids, ['department_id','company_id'])[0]
        if lac_right_group:
            for r_di in lac_right_group:
                if r_di.get('lr_dzial_id', False):
                    if r_di['lr_dzial_id'] == hr_abs_dict['department_id'][0]:
                        pass
                    else:
                        raise osv.except_osv(_('Nieprawidłowy dział'), _('Nie możesz dokonywać akcji dla tego działu'))
                if r_di.get('lr_company_id', False):
                    abs_dict_company_id = False
                    if hr_abs_dict.get('company_id', False):
                        abs_dict_company_id = hr_abs_dict['company_id'][0]
                    if r_di['lr_company_id'] == abs_dict_company_id:
                        pass
                    else:
                        raise osv.except_osv(_('Nieprawidłowa firma'), _('Nie możesz dokonywać akcji dla tej firmy'))
            return True    
    
    
    def overtime_hours_confirm(self, cr, uid, ids, *args):
        '''Zatwierdzanie nadgodzin ze sprzawdzeniem lacan rights'''
        
        # check access
        self.pool.get('lacan.right').check_permission_for_action(cr, uid, 
                                                                'perm_field_hr2_overtime_accept',
                                                                 self._name, _('Confirm'),
                                                                 raise_action_exceptions=True)
        self.check_permission_range(cr, uid, ids)
        # ------------
        values = {'state':'approved'}
        
        return self.write(cr, uid, ids, values)
 
 
    def overtime_hours_cancel(self, cr, uid, ids, *args):
        '''Anulowanie nadgodzin'''

        values = {'state':'cancel'}
        
        return self.write(cr, uid, ids, values)
    
    
    def overtime_hours_set_to_draft(self, cr, uid, ids, *args):
        '''Przywracanie do stanu projekt rekordu w stanie Anuluj'''

        values = {'state':'draft'}
        
        return self.write(cr, uid, ids, values)
    
    
    def create(self, cr, uid, vals, context=None):
        '''Nadpisana funkcja orm-owa sprawdzająca, czy dla pracownika, któremu chcemy wpisać nadgodziny istnieje aktualny etat'''
        
        if not context: context = {}
        
        if vals.get('hours', False) <= 0:
            raise osv.except_osv(_('Błąd !'), _('Ilość godzin nadliczbowych musi być większa od zera.'))
            
        date_from = vals.get('date_from', False)
        date_to = vals.get('date_to', False)
        employee_id = vals.get('employee_id', context.get('default_employee_id',False))
    
        cr.execute("SELECT sign_date, discharge_date \
                    FROM hr2_etat WHERE employee_id = %s \
                    AND sign_date <= %s \
                    AND (discharge_date >= %s OR discharge_date is null)", (employee_id, date_from, date_to))
        
        etat_data = cr.dictfetchone()
        
        if not etat_data:
            raise osv.except_osv(_('Błąd !'), _('Nie można wprowadzić nadgodzin dla Pracownika bez umowy o pracę'))
        
        self.pool.get('hr2.employee.date').create_hr_employee_dates(cr, uid, employee=employee_id, date=date_from, context=context)
            
        res = super(hr2_overtime, self).create(cr, uid, vals, context=context)
        
        return res
    
    
    def write(self, cr, uid, ids, vals, context=None):
        '''Nadpisana funkcja orm-owa sprawdzająca, czy dla pracownika, któremu chcemy wpisać nadgodziny istnieje aktualny etat'''
        
        if not context: context = {}
        
        if vals.get('hours', False) < 0:
            raise osv.except_osv(_('Błąd !'), _('Ilość godzin nadliczbowych musi być większa od zera.'))
        
        if vals.get('state', False) == 'cancel':
            return super(hr2_overtime, self).write(cr, uid, ids, vals, context=context)
        
        if isinstance(ids,list):
            ids = ids[0]
        
        data = self.read(cr, uid, ids, ['date_from','date_to','employee_id'])
        
        if 'date_from' in vals or 'date_to' in vals or vals.get('state',False) == 'approved':
            date_from = vals.get('date_from', data['date_from'])
            date_to = vals.get('date_to', data['date_to'])
            employee_id = vals.get('employee_id', data['employee_id'][0])
        
            cr.execute("SELECT sign_date, discharge_date \
                        FROM hr2_etat WHERE employee_id = %s \
                        AND sign_date <= %s \
                        AND (discharge_date >= %s OR discharge_date is null)", (employee_id, date_from, date_to))
            
            etat_data = cr.dictfetchone()
            
            if not etat_data:
                raise osv.except_osv(_('Błąd !'), _('Nie można wprowadzić nadgodzin dla Pracownika bez umowy o pracę'))
        
            self.pool.get('hr2.employee.date').create_hr_employee_dates(cr, uid, employee=employee_id, date=date_from, context=context)
        
        res = super(hr2_overtime, self).write(cr, uid, ids, vals, context=context)
        
        return res
    
    
    def save_and_close(self, cr, uid, ids, context):
        '''Zapisuje godziny nadliczbowe i powraca do widoku dnia kalendarza'''

        if context['parent_id'] and context['active_id']:
            mod_obj = self.pool.get('ir.model.data')

            #form
            model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_hr_payroll_employee_calendar_form')], context=context)
            form_resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

            #calendar
            model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_hr_payroll_employee_calendar_calendar')], context=context)
            calendar_resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

            return {
                'name': 'Kalendarz pracownika',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr2.employee.date',
                'res_id': context['parent_id'],
                'views': [(form_resource_id,'form'),(calendar_resource_id,'calendar')],
                'type': 'ir.actions.act_window',
                'tag': 'reload',
                'target' : 'current',
                'context': context,
                'domain': [('employee_id', '=', context['active_id'])]
            }
            
        return False
        
    
hr2_overtime()


class hr2_employee_date(osv.osv):
    
    _name = "hr2.employee.date"
    _inherit = 'hr2.employee.date'
    
    
    def _get_overtime(self, cr, uid, ids, field_names=None, arg=None, context=None):
        """Metoda dla pola funkcyjnego, zwracająca ID nadgodzin przypadających na dany dzień """
            
        if not context: context = {}
    
        res = {}
  
        for id in ids:
            date_pool = self.pool.get('hr2.employee.date')
            employee_id = date_pool.browse(cr, uid, id, context=context).employee_id.id
  
            date_start = date_pool.browse(cr, uid, id, context=context).date + ' ' + '00:00:00'
            date_start = lacan_tools.date_convers_time_zones(date_start, context.get('tz', 'UTC'), 'UTC')
            date_stop = date_pool.browse(cr, uid, id, context=context).date + ' ' + '23:59:59'
            date_stop = lacan_tools.date_convers_time_zones(date_stop, context.get('tz', 'UTC'), 'UTC')
  
            overtime_pool = self.pool.get('hr2.overtime')
            overtime_id = []
            overtime_id.extend(overtime_pool.search(cr, uid,[('employee_id', '=', employee_id), ('date_from', '>=', date_start), ('date_from', '<=', date_stop), ('state', '=', 'approved')] , context=context))
            overtime_id.extend(overtime_pool.search(cr, uid,[('employee_id', '=', employee_id), ('date_to', '>=', date_start), ('date_to', '<=', date_stop), ('state', '=', 'approved')] , context=context))
            overtime_id.extend(overtime_pool.search(cr, uid,[('employee_id', '=', employee_id), ('date_from', '<=', date_start), ('date_to', '>=', date_start), ('state', '=', 'approved')], context=context))
            overtime_id.extend(overtime_pool.search(cr, uid,[('employee_id', '=', employee_id), ('date_from', '<=', date_stop), ('date_to', '>=', date_stop), ('state', '=', 'approved')] , context=context))
  
            if overtime_id:
                res[id] = overtime_id[0]
            
            else:
                res[id] = False
  
        return res
    
    
    def _update_overtime(self, cr, uid, ids, context=None):
        """ Metoda dla pola funkcyjnego, wywoływana przy zmianie rekordów w hr2.overtime """
        
        if not context: context = {}
        
        res = []
   
        for id in ids:
            overtime = self.pool.get('hr2.overtime').browse(cr, uid, id, context=context)
   
            events_ids = self.pool.get('hr2.employee.date').search(cr, uid, [('employee_id','=',overtime.employee_id.id),('date','>=',overtime.date_from[:-9]),('date','<=',overtime.date_to[:-9])], context=context)
            res.extend(events_ids)
   
            events_ids = self.pool.get('hr2.employee.date').search(cr, uid, [('overtime_id','=',overtime.id)], context=context)
            
            for event_id in events_ids:
                
                if event_id not in res:
                    res.extend([event_id])
                    
        return res
     

    _columns = {
                'overtime_id' : fields.function(_get_overtime,
                                               type='many2one',
                                               method=True,
                                               relation='hr2.overtime',
                                               string='Nadgodziny',
                                               store = {'hr2.overtime': (_update_overtime,
                                                                         ['employee_id',
                                                                          'date_from',
                                                                          'date_to',
                                                                          'state'],
                                                                         5)
                                                         }
                                               ),
                }
    
    
    def employee_calendar_add_overtime(self, cr, uid, ids, context=None):
        """Metoda wyświetla widok dodawania nadgodzin"""
        
        if not context: context={}
 
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','add_overtime_form_view')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
 
        self_data = self.read(cr, uid, ids[0], ['employee_id', 'date', 'overtime_id'], context=context)
        employee_id = self_data['employee_id'][0]
        date = self_data['date'] + ' 00:00:00'
        date_tz = lacan_tools.date_convers_time_zones(date, context.get('tz', 'UTC'), 'UTC')
        
        if self_data['overtime_id']:
            overtime_id = self_data['overtime_id'][0]
        
        else:
            overtime_id = self_data['overtime_id']
 
        return {
            'name': _('Dodaj nadgodziny'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr2.overtime',
            'res_id': overtime_id,
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'tag': 'reload',
            'target' : 'current',
            'context': {"form_view_ref": 'hr_payroll_pl.add_overtime_form_view',
                        "parent_id": ids[0],
                        "default_employee_id": employee_id,
                        "default_date_from": date_tz,
                        "default_date_to": date_tz,
                        'default_state' : 'approved'}
        }
        
        
    def employee_calendar_remove_overtime(self, cr, uid, ids, context):
        """Metoda wyswietla widok usuwania nieobecności, a nastepnie wraca do poprzedniego widoku"""
        
        if not context: context = {}
        
        if context.get('active_id', False):
            #usuń nadgodziny
            overtime_id = self.read(cr, uid, ids[0], ['overtime_id'], context=context)['overtime_id'][0]
            self.pool.get('hr2.overtime').write(cr, uid, overtime_id, {'state': 'cancel'}, context=context)

            #przeładuj widok
            mod_obj = self.pool.get('ir.model.data')
            model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_hr_payroll_employee_calendar_form')], context=context)
            form_resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
            model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_hr_payroll_employee_calendar_calendar')], context=context)
            calendar_resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

            return {
                'name': 'Kalendarz pracownika',
                'view_type': 'form',
                'view_mode': 'form, calendar',
                'res_model': 'hr2.employee.date',
                'res_id': ids[0],
                'views': [(form_resource_id,'form'),(calendar_resource_id,'calendar')],
                'type': 'ir.actions.act_window',
                'tag': 'reload',
                'target' : 'current',
                'context': context,
                'domain': [('employee_id', '=', context['active_id'])]
            }
            
        return False
    

hr2_employee_date()


class hr2_dzial(osv.osv):

    _name = "hr2.dzial"
    _inherit = "hr2.dzial"

    _columns = {
                'account_id': fields.many2one('hr2.payslip.config.accounts', 'Konto'),
                }


hr2_dzial()


class hr2_ksiegowanie_wynagrodzen(osv.osv_memory):

    _name = "hr2.ksiegowanie.wynagrodzen"

    _columns = {
                'payslip_id': fields.many2one('hr2.payslip', 'Lista płac'),
                'payslip_line_id': fields.many2one('hr2.payslip.line', 'Linia'),
                'payslip_line_line_id': fields.many2one('hr2.payslip.line.line', 'Linia'),
                'addition_type': fields.many2one('hr2.salary.addition.type', 'Typ dodatku'),
                'value': fields.integer('Wartość'),
                }


hr2_ksiegowanie_wynagrodzen()


class hr_employee(osv.osv):

    _name = "hr.employee"
    _inherit = "hr.employee"
    
    
    def action_print_nip7(self, cr, uid, ids, context=None):
        '''Wywołuje okno wizarda, z którego generowany jest formularz NIP-7'''
        
        if not context: context = {}
        
        wizard_id = self.pool.get("hr.nip7").create(
                cr, uid, {}, context=dict(context, active_ids=ids))
        
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('model', '=', 'hr.nip7'),
                                                               ('name', '=', 'nip7.form')])
            
        return {
            'name':_("File"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'hr.nip7',
            'res_id': wizard_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': '[]',
            'context': dict(context, active_ids=ids)
        }
        

hr_employee()
