# -*- coding: utf-8 -*-
##############################################################################
#
# LACAN Technologies Sp. z o.o.
# Al. Stanow Zjednoczonych 53
# 04-028 Warszawa
#
# Copyright (C) 2009-2014 Lacan Technologies Sp. z o.o. (<http://www.lacan.com.pl>).
# All Rights Reserved
#
#
##############################################################################

from osv import fields, osv
import httplib, urllib
import base64
import xml.dom.minidom
from openerp.tools.translate import _

#Inheriting the Partner Address Model to add button.
class res_partner(osv.osv):
    _inherit = "res.partner"
    
    _defaults = {
        'name' : 'Set a name or import form CSO',
    }
    
    def show_cso(self,cr,uid,ids,context=None):
        '''
        @note: Method called when clicking the button in Partner Address form. Shows the Captcha Image from CSO Website.
        @return: Wizard that shows the form with captcha
        '''
        address_obj = self.browse(cr,uid,ids,context=context)[0]
        
        context.update({
            'partner_id':address_obj.id,
            'form_view_ref': 'lacan_cso.view_lacan_cso_form'
        })
        
        writeDict = {
            'name': address_obj.vat,
            'picture': self.pool.get('lacan.cso')._get_nip_captcha(cr,uid,ids,context)
        }

        wizard_id = self.pool.get('lacan.cso').create(cr,uid,writeDict,context=context)
        
        # Show the wizard with information
        return {
            'name':"NIP Captcha",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_id':wizard_id,
            'res_model': 'lacan.cso',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
        
# Model for the wizard that shows captcha. Model has all the methods to send request to CSO website and get the values back
class lacan_cso (osv.osv_memory):
    _name = 'lacan.cso'
    _description='CSO NIP Wizard'
    
    #Set Default headers
    headers = {
        'referer':'http://stat.gov.pl/regon/',
        'useragent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20130224 Firefox/21.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'pl,en-us;q=0.7,en;q=0.3',
        'compress':True,
        'redirect':3,
        'connecttimeout':10,
        'timeout':10
    }
    
    cookie_info = {}
    
    def _get_nip_captcha (self,cr,uid,ids,context=None):
        '''
        @note: Sends a request to get the initial cookies and then gets the captcha image. This is called from the "_defaults" for captcha
        @return: Captcha Image from CSO website
        '''
        ini_params = {}
        
        try:
            #Initialize Connection to CSO webstie
            conn_ini = httplib.HTTPConnection("stat.gov.pl")
            conn_ini.request("GET", "/regon/name", headers=self.headers)
            response_ini = conn_ini.getresponse()
            headers_ini = response_ini.getheader('set-cookie')
        except:
            raise osv.except_osv(_('Error!'), _('Could not connect to server. Please check your Internet connection'))
        
        #Cookies are processed here
        self.parse_cookies(cr,uid,ids,headers_ini,context=context)
        self.generate_cookie_string(cr,uid,ids,context=context)
        
        data = ""
        
        #Send another request for Captcha with the headers collected earlier
        try:
            conn = httplib.HTTPConnection("stat.gov.pl")
            conn.request("GET", "/regon/Captcha.jpg", headers=self.headers)
            r1 = conn.getresponse()
            
            if r1.status <> 200 and r1.status <> 301:
                raise osv.except_osv(_('Error Occurred'), _(r1.reason))
            
            data = base64.b64encode(r1.read())
            headers_captcha = r1.getheader('set-cookie')
            
            if headers_captcha:
                self.parse_cookies(cr,uid,ids,headers_captcha,context=context)
        except:
            raise osv.except_osv(_('Error!'), _('Could not connect to server. Please check your Internet connection'))

        conn.close()
                
        return data
    
    def parse_cookies(self,cr,uid,ids,cookie,context=None):
        '''
        @note: Method to parse strings and store it in dictionary
        @param cookie: Cookie info collected from the connection object
        '''
        if cookie is not None:
            cookie_list = cookie.split(",")
            
            for x in cookie_list:
                x_split = x.split(";")
                y = x_split[0].split("=")
                self.cookie_info[y[0].strip()] = y[1].strip()
        
    def generate_cookie_string(self,cr,uid,ids,context=None):
        '''
        @note: Method to parse cookie dictionary and convert it in to string
        '''
        cookie = self.cookie_info
        cookie_string = ""
        
        for key in cookie.iterkeys():
            if cookie_string:
                cookie_string = cookie_string+"; "+str(key)+"="+str(cookie[key])
            else:
                cookie_string = str(key)+"="+str(cookie[key])
        
        self.headers['Cookie'] = cookie_string
    
    _columns = {
        'name':fields.char('VAT/PESEL',size=50),
        'picture':fields.binary('Captcha'),
        'captcha':fields.char('Captcha Code',size=50),        
        'partner_name':fields.char('Partner\'s Company Name',size=200),
        'partner_id':fields.many2one('res.partner','Selected Partner',size=200),
        'address_id':fields.many2one('res.partner.address','Select Address to Update',size=200),
        'street':fields.char('Street',size=200),
        'state_id':fields.many2one('res.country.state','State',size=200),
        'city':fields.char('City',size=200),
        'zip':fields.char('Zip',size=200),
        'municipality':fields.char('Municipality',size=200),
        'description':fields.text('Description'),
    }
    
    def reload_captcha(self,cr,uid,ids,context=None):
        '''
        @note: Method to Reload Captcha
        '''
        writeDict = {
            'picture': self._get_nip_captcha(cr,uid,ids,context),
            'captcha':''
        }
        
        context.update({
            'form_view_ref': 'lacan_cso.view_lacan_cso_form'
        })

        self.write(cr,uid,ids,writeDict,context=context)

        return {
            'name':"NIP Captcha",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_id':ids[0],
            'res_model': 'lacan.cso',
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
        
    
    def find_state_id(self,cr,uid,state_text,context=None):
        '''
        @note: Method to find the state. If available, id is given, else a new state is created
        '''
        
        state_obj = self.pool.get('res.country.state')
        
        #Check if the state is already available. Else create it
        state_ids = state_obj.search(cr,uid,[('name','ilike',state_text)],context=context)
        
        if len(state_ids) > 0:
            return state_ids[0]
        else:
            c_id = self.pool.get('res.country').search(cr,uid,[('code','=','PL')],context=context)[0]
            return state_obj.create(cr,uid,{'code':'00','name':state_text,'country_id':c_id},context=context)
        
    def find_default_address(self,cr,uid,zip_text,city,partner_id,context=None):
        '''
        @note: Method to find the default address using zip and city for a partner
        '''
        #Search for address which matches
        if partner_id:
            res = self.pool.get('res.partner.address').search(cr,uid,[('city','ilike',city),('zip','ilike',zip_text),('partner_id','=',partner_id)],limit=1,context=context)
            #If matching address not found, then suggest the default address
            if not res:
                res = self.pool.get('res.partner.address').search(cr,uid,[('partner_id','=',partner_id)],limit=1,context=context)
            return res
        else:
            return False
        
    
    def fetch_nip(self,cr,uid,ids,context=None):
        '''
        @note: Method called from the wizard after captcha given by the user. Gets information from CSO website
        '''
        data = ""
        partner_obj = self.pool.get('res.partner').browse(cr,uid,context.get('partner_id',''),context=context)
        
        nip_number = context.get('nip_number','')

        if not self.pool.get('res.partner').write(cr,uid,context.get('partner_id',''),{'vat':nip_number},context=context):
            return False
        
        captcha = context.get('captcha','')
        
        if not nip_number:
            raise osv.except_osv(_('Error!'), _("Please enter VAT/PESEL number"))

        if not captcha:
            raise osv.except_osv(_('Error!'), _("Please enter captcha"))
        
        self.cookie_info['lastCritIx'] = 1
        self.cookie_info['isAmbiguousAnswer'] = 'false'
        self.cookie_info['toGenerNewVerifCode'] = 'false'
        self.cookie_info['cCodeHistory'] = captcha
        self.cookie_info['openingPageType'] = '""'
        self.cookie_info['focusedObjIdGlobal'] = 'verifCodeTF'
        self.cookie_info['focusedObjCursorPos'] = 5
        self.cookie_info['lastCCode'] = captcha
        self.cookie_info['criterion1TF'] = nip_number
        self.cookie_info['browser'] = "CH-32.0.1700.107 X-Window"
        self.cookie_info['testCookie'] = ""
        self.cookie_info['httpMethod'] = 'POST'
        self.cookie_info['l_lokalnych'] = '1'
        
        self.generate_cookie_string(cr,uid,ids,context=context)
        
        # Parameters that need to be sent via POST
        params = urllib.urlencode({'queryTypeRBSet': '1nip', captcha+'00': '', captcha+'11': nip_number, 'verifCodeTF': captcha})
        
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['Host'] = 'stat.gov.pl'
        self.headers['Origin'] = 'http://stat.gov.pl'
        
        # Send final request to get partner information with Captcha value entered by the user and Vat from the database
        try:
            conn = httplib.HTTPConnection("stat.gov.pl")
            conn.request("POST", "/regon/",params, self.headers)
            r1 = conn.getresponse()
            if r1.status <> 200:
                raise osv.except_osv(_('Error Occurred'), _(r1.reason))
            
            data = r1.read()
        except:
            raise osv.except_osv(_('Error!'), _('Could not connect to server. Please check your Internet connection'))
        
        # Parse Data as XML
        try:
            dom = xml.dom.minidom.parseString(data)
        except:
            # If there is error in VAT number entered, the resulting HTML that comes from CSO has errors.
            raise osv.except_osv(_('Error!'), _('Please check the VAT number you entered.'))
        
        td_list = dom.getElementsByTagName("td")
        td_string_list = []
        
        # Collect all values in td tag in a list. There should be a better way. But there is no ids for td. Seems to be the only way for now.
        for td in td_list:
            rc = []
            for node in td.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            td_string_list.append(''.join(rc))
        
        opDict = {}
        writeDict = {}
        
        # Collect information and store it in a Dictionary
        for i, val in enumerate(td_string_list):
            if i < 30:
                if val.strip() == u'Województwo':
                    opDict['Województwo'] = td_string_list[i+1].strip()
                elif val.strip() == u'Nazwa':
                    opDict['Nazwa'] = td_string_list[i+1].strip()
                elif val.strip() == u'Powiat':
                    opDict['Powiat'] = td_string_list[i+1].strip()
                elif val.strip() == u'Gmina/Dzielnica lub Delegatura':
                    opDict['Gmina/Dzielnica lub Delegatura'] = td_string_list[i+1].strip()
                elif val.strip() == u'Ulica, miejscowość':
                    opDict['Ulica, miejscowość'] = td_string_list[i+1].strip()
                elif val.strip() == u'Poczta':
                    opDict['Poczta'] = td_string_list[i+1].strip()
        
        # If there is error in Captcha entered, then 'Nazwa' will not be in TD. Any other dictionary key can also be checked.
        if opDict.get('Nazwa','') == '':
            raise osv.except_osv(_('Error!'), _("Please check the captcha entered. Click the 'Reload Captcha' button to continue."))
        
        for key in opDict:
            if key == 'Województwo':
                writeDict['state_id'] = self.find_state_id(cr,uid,opDict['Województwo'],context=context)
            elif key == 'Nazwa':
                writeDict['partner_name'] =  opDict['Nazwa']
            elif key == 'Powiat':
                writeDict['city'] = opDict['Powiat']
            elif key == 'Gmina/Dzielnica lub Delegatura':
                writeDict['municipality'] = opDict['Gmina/Dzielnica lub Delegatura']
            elif key == 'Ulica, miejscowość':
                writeDict['street'] = opDict['Ulica, miejscowość']
            elif key == 'Poczta':
                writeDict['zip'] = opDict['Poczta']
        
        if opDict['Nazwa'] <> partner_obj.name.strip():
            writeDict['description'] = "Partner's name entered and the one from the CSO website are not matching!"
        
        writeDict['partner_id'] = context.get('partner_id','')
        writeDict['name'] = nip_number
        selected_address =  self.find_default_address(cr,uid,writeDict['zip'],writeDict['city'],writeDict['partner_id'],context=context)
        if selected_address and len(selected_address) > 0:
            writeDict['address_id'] = selected_address[0]

        wizard_id = self.pool.get('lacan.cso').create(cr,uid,writeDict,context=context)
        
        context.update({
            'cso_id':wizard_id,
            'form_view_ref': 'lacan_cso.view_lacan_cso_next_form'
        })
        
        #Return wizard to send confirmation to the user if he wants to update the data
        return {
            'name':"Update/Create Address",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'lacan.cso',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'new',
            'domain': '[]',
            'context': context,
            'dialog_relative_width':0.45
        }
    
    def create_update_address(self,cr,uid,context=None):
        '''
        @note: Common Method to create or update address
        '''
        if context.get('cso_id',""):
            read_data = self.read(cr,uid,context.get('cso_id',""),['partner_id','partner_name','street','state_id','city','zip','address_id'],context=context)

            #Find Poland's id from res.country
            c_id = self.pool.get('res.country').search(cr,uid,[('code','=','PL')],context=context)[0]
            read_data['country_id'] = c_id
            
            partner_data = self.pool.get('res.partner').browse(cr,uid,read_data['partner_id'],context=context)
            if partner_data.name == 'Set a name or import form CSO':
                #Update Partner Name
                self.pool.get('res.partner').write(cr,uid,read_data['partner_id'],{'name':read_data['partner_name']},context=context)
                
            if context.get("update_type","") == 'create':
                self.pool.get('res.partner.address').create(cr,uid,read_data,context=context)
            else:
                update_address_id = read_data['address_id']
                if not update_address_id:
                    raise osv.except_osv(_('Error!'), _('You need to select an address to update!'))
            
                del read_data['address_id']
                self.pool.get('res.partner.address').write(cr,uid,update_address_id,read_data,context=context)

        return {'type':'ir.actions.act_window_close' }
    
    def create_record(self,cr,uid,ids,context=None):
        '''
        @note: Method called by button from the wizard to create new address
        '''
        context.update({
            'update_type':'create'
        })
        return self.create_update_address(cr,uid,context=context)
    
    def update_record(self,cr,uid,ids,context=None):
        '''
        @note: Method called by button from the wizard to update the address database
        '''
        context.update({
            'update_type':'update'
        })
        return self.create_update_address(cr,uid,context=context)

lacan_cso()