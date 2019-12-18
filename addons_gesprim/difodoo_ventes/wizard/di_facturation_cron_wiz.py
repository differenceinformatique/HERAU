# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class DiFactCronWiz(models.TransientModel):
    _name = "di.fact.cron.wiz"
    _description = "Wizard de facturation en arrière plan"    
    
    date_fact = fields.Date(required=True, default=datetime.datetime.today().date(), string="Date de facturation")
    period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
    date_debut = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, 1), string="Date Début")
    date_fin = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, calendar.mdays[datetime.date.today().month]), string="Date Fin")
    ref_debut = fields.Char(required=True, default=" ", string="Code Tiers Début")
    ref_fin = fields.Char(required=True, default="ZZZZZZZZZZ", string="Code Tiers Fin")
    
    di_avec_fact = fields.Boolean("Avec facture",default=False)
    
    
#     @api.multi
#     def di_create_invoices(self, ids):       
#         sale_orders = self.env['sale.order'].browse(ids)
#         
#         sale_orders_group = sale_orders.filtered(lambda so: so.partner_id.di_regr_fact == True)
#         if sale_orders_group:
#             sale_orders_group.action_invoice_create(grouped=False,final=True)
#             
#         sale_orders_non_group = sale_orders.filtered(lambda so: so.partner_id.di_regr_fact == False)
#         if sale_orders_non_group:
#             sale_orders_non_group.action_invoice_create(grouped=True,final=True)       
#                             
#         for s_o in sale_orders: #pour passer en complètement facturé les commandes avec reliquat
#             s_o.action_done()
#             
#         invoices = sale_orders.mapped('invoice_ids')
#         param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
#         if param.di_autovalid_fact_ven:
#                 invoices.action_invoice_open()
#         invoices.write({'date_invoice':self.date_fact})  
    
# #     si séparation par client -> OK mais lent
#     @api.multi
#     def di_create_invoices(self, ids, regr, date_fact):       
#         sale_orders = self.env['sale.order'].browse(ids)
#         if sale_orders:
#             sale_orders.action_invoice_create(grouped=not regr,final=True)       
#                              
#         for s_o in sale_orders: #pour passer en complètement facturé les commandes avec reliquat
#             s_o.action_done()
#              
#         invoices = sale_orders.mapped('invoice_ids')
#         param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
#         if param.di_autovalid_fact_ven:
#                 invoices.action_invoice_open()
#         invoices.write({'date_invoice':date_fact})    
#         

#     si séparation par client + rappel create cron
    @api.multi
    def di_create_invoices(self, ids, regr, date_fact, period_fact, date_debut, date_fin, ref_debut, ref_fin, di_avec_fact):       
        sale_orders = self.env['sale.order'].browse(ids)
        if sale_orders:
            self._cr.execute('SAVEPOINT create_invoices')            
            try:                
                sale_orders.action_invoice_create(grouped=not regr,final=True) 
                self._cr.commit()  
                for s_o in sale_orders: #pour passer en complètement facturé les commandes avec reliquat
                    self._cr.execute('SAVEPOINT done_sale')
                    try:
                        s_o.action_done() 
                        self._cr.commit()  
                    except Exception as e:
                        self._cr.execute('ROLLBACK TO SAVEPOINT done_sale') 
                        self.env['ir.logging'].sudo().create({
                                'name': 'creation_facture',
                                'type': 'server',
                                'level': 'ERROR',
                                'dbname': self.env.cr.dbname,
                                'message': 'Erreur done commande',
                                'func': 'di_create_invoices',
                                'path': '',
                                'line': '0',
                            })  
            except Exception as e:
                self._cr.execute('ROLLBACK TO SAVEPOINT create_invoices') 
                self.env['ir.logging'].sudo().create({
                        'name': 'creation_facture',
                        'type': 'server',
                        'level': 'ERROR',
                        'dbname': self.env.cr.dbname,
                        'message': 'Erreur creation factures',
                        'func': 'di_create_invoices',
                        'path': '',
                        'line': '0',
                    })   
                             
                                    
        invoices = sale_orders.mapped('invoice_ids')
        draft_invoices = invoices.filtered(lambda f: f.state == 'draft')
        draft_invoices.write({'date_invoice':date_fact})
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        if param.di_autovalid_fact_ven:            
            #draft_invoices.action_invoice_open()
            for draft_invoice in draft_invoices:
                self._cr.execute('SAVEPOINT validate_invoice')
                try:
                    draft_invoice.action_invoice_open()                    
                    self._cr.commit()
                except Exception as e:
                    self._cr.execute('ROLLBACK TO SAVEPOINT validate_invoice')
                    # log error in ir.logging for a visibility on the error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Validation_facture',
                        'type': 'server',
                        'level': 'ERROR',
                        'dbname': self.env.cr.dbname,
                        'message': 'Erreur validation facture',
                        'func': 'di_create_invoices',
                        'path': '',
                        'line': '0',
                    })
                                    
                        
        if not di_avec_fact:    
            if draft_invoices:
                di_avec_fact = True  
                
                
                
                
                
        query_args = {'periodicity_invoice': period_fact,'date_debut' : date_debut,'date_fin' : date_fin, 'ref_debut': ref_debut,'ref_fin':ref_fin}
        query = """ SELECT  so.id 
                        FROM sale_order so
                        INNER JOIN res_partner rp on rp.id = so.partner_id 
                        WHERE so.invoice_status = 'to invoice' 
                        AND di_livdt between %(date_debut)s AND %(date_fin)s                            
                        AND rp.ref is not null
                        AND rp.di_period_fact = %(periodicity_invoice)s
                        AND rp.ref between %(ref_debut)s AND %(ref_fin)s                                                                     
                        """
 
        self.env.cr.execute(query, query_args)
        ids = [r[0] for r in self.env.cr.fetchall()]
        if ids:                     
            new_wiz=self.env['di.fact.cron.wiz'].create({'date_fact':date_fact,'period_fact':period_fact,'date_debut':date_debut,'date_fin':date_fin,'ref_debut':ref_debut,'ref_fin':ref_fin,'di_avec_fact':di_avec_fact})            
            new_wiz.create_cron_fact()
        else:
            mail_fin = self.env['mail.mail'].create({"subject":"Facturation terminée","email_to":self.env.user.email,"body_html":"La facturation est terminée.","body":"La facturation est terminée."})
            mail_fin.send() 
        

#     def create_cron_fact(self):                
#         self.env.cr.execute("""SELECT id FROM ir_model 
#                                   WHERE model = %s""", (str(self._name),))            
#         info = self.env.cr.dictfetchall()  
#         if info:
#             model_id = info[0]['id']     
#         sale_orders = self.env['sale.order']                    
#         query_args = {'periodicity_invoice': self.period_fact,'date_debut' : self.date_debut,'date_fin' : self.date_fin, 'ref_debut': self.ref_debut,'ref_fin':self.ref_fin}
#         query = """ SELECT  so.id 
#                         FROM sale_order so
#                         INNER JOIN res_partner rp on rp.id = so.partner_id 
#                         WHERE so.invoice_status = 'to invoice' 
#                         AND di_livdt between %(date_debut)s AND %(date_fin)s                            
#                         AND rp.ref is not null
#                         AND rp.di_period_fact = %(periodicity_invoice)s
#                         AND rp.ref between %(ref_debut)s AND %(ref_fin)s                                             
#                         order by so.partner_id
#                         """
# 
#         self.env.cr.execute(query, query_args)
#         ids = [r[0] for r in self.env.cr.fetchall()]
#         sale_orders = self.env['sale.order'].search([('id', 'in', ids)])
#         if sale_orders:                                
#             dateheure = datetime.datetime.today()                                                         
#             dateheureexec = dateheure+datetime.timedelta(minutes=2)                    
#             self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
#                                         'active':True, 
#                                         'user_id':self.env.user.id, 
#                                         'interval_number':1, 
#                                         'interval_type':'days', 
#                                         'numbercall':1, 
#                                         'doall':1, 
#                                         'nextcall':dateheureexec, 
#                                         'model_id': model_id, 
#                                         'code': 'model.di_create_invoices(('+str(sale_orders.ids).strip('[]')+'))', 
#                                         'state':'code',
#                                         'priority':0})                                                                      
                
#     # séparé par paquet de 30 clients -> OK mais trop lent
#     def create_cron_fact(self):                
#         self.env.cr.execute("""SELECT id FROM ir_model 
#                                   WHERE model = %s""", (str(self._name),))            
#         info = self.env.cr.dictfetchall()  
#         if info:
#             model_id = info[0]['id']     
#         sale_orders = self.env['sale.order']                    
#         query_args = {'periodicity_invoice': self.period_fact,'date_debut' : self.date_debut,'date_fin' : self.date_fin, 'ref_debut': self.ref_debut,'ref_fin':self.ref_fin}
#         query = """ SELECT  so.id 
#                         FROM sale_order so
#                         INNER JOIN res_partner rp on rp.id = so.partner_id 
#                         WHERE so.invoice_status = 'to invoice' 
#                         AND di_livdt between %(date_debut)s AND %(date_fin)s                            
#                         AND rp.ref is not null
#                         AND rp.di_period_fact = %(periodicity_invoice)s
#                         AND rp.ref between %(ref_debut)s AND %(ref_fin)s 
#                         AND rp.di_regr_fact is true                       
#                         order by so.partner_id
#                         """
#  
#         self.env.cr.execute(query, query_args)
#         ids = [r[0] for r in self.env.cr.fetchall()]
#         sale_orders = self.env['sale.order'].search([('id', 'in', ids)])
#         if sale_orders:
#             partners = sale_orders.mapped('partner_id')
#             cptpart = 0
#             to_invoice = self.env['sale.order']
#             dateheureexec =False
#             for partner in partners:      
#                 cptpart +=1                  
#                 partner_orders = sale_orders.filtered(lambda so: so.partner_id.id == partner.id)
#                 dateheure = datetime.datetime.today()                              
#                 to_invoice+=partner_orders
#                 if cptpart == 30:
#                     cptpart =0
#                     if not dateheureexec:
#                         dateheureexec = dateheure+datetime.timedelta(minutes=2)
#                     else:
#                         dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
#                     self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
#                                                 'active':True, 
#                                                 'user_id':self.env.user.id, 
#                                                 'interval_number':1, 
#                                                 'interval_type':'days', 
#                                                 'numbercall':1, 
#                                                 'doall':1, 
#                                                 'nextcall':dateheureexec, 
#                                                 'model_id': model_id, 
#                                                 'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s")' % (True , self.date_fact),
#                                                 'state':'code',
#                                                 'priority':0})    
#                     to_invoice = self.env['sale.order']           
#                  
#                      
#             if cptpart > 0:
#                 if not dateheureexec:
#                     dateheureexec = dateheure+datetime.timedelta(minutes=2)
#                 else:
#                     dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
#                 self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
#                                             'active':True, 
#                                             'user_id':self.env.user.id, 
#                                             'interval_number':1, 
#                                             'interval_type':'days', 
#                                             'numbercall':1, 
#                                             'doall':1, 
#                                             'nextcall':dateheureexec, 
#                                             'model_id': model_id, 
#                                             'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s")' % (True , self.date_fact),
#                                             'state':'code',
#                                             'priority':0})    
#                 to_invoice = self.env['sale.order'] 
#                  
#                  
#                  
#         sale_orders = self.env['sale.order']                    
#         query_args = {'periodicity_invoice': self.period_fact,'date_debut' : self.date_debut,'date_fin' : self.date_fin, 'ref_debut': self.ref_debut,'ref_fin':self.ref_fin}
#         query = """ SELECT  so.id 
#                         FROM sale_order so
#                         INNER JOIN res_partner rp on rp.id = so.partner_id 
#                         WHERE so.invoice_status = 'to invoice' 
#                         AND di_livdt between %(date_debut)s AND %(date_fin)s                            
#                         AND rp.ref is not null
#                         AND rp.di_period_fact = %(periodicity_invoice)s
#                         AND rp.ref between %(ref_debut)s AND %(ref_fin)s 
#                         AND rp.di_regr_fact is false                       
#                         order by so.partner_id
#                         """
#  
#         self.env.cr.execute(query, query_args)
#         ids = [r[0] for r in self.env.cr.fetchall()]
#         sale_orders = self.env['sale.order'].search([('id', 'in', ids)])
#         if sale_orders:
#             partners = sale_orders.mapped('partner_id')
#             cptpart = 0
#             to_invoice = self.env['sale.order']
#              
#             for partner in partners:      
#                 cptpart +=1                  
#                 partner_orders = sale_orders.filtered(lambda so: so.partner_id.id == partner.id)
#                 dateheure = datetime.datetime.today()                
#                  
#                 to_invoice+=partner_orders
#                 if cptpart == 30:
#                     cptpart =0
#                     if not dateheureexec:
#                         dateheureexec = dateheure+datetime.timedelta(minutes=2)
#                     else:
#                         dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
#                     self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
#                                                 'active':True, 
#                                                 'user_id':self.env.user.id, 
#                                                 'interval_number':1, 
#                                                 'interval_type':'days', 
#                                                 'numbercall':1, 
#                                                 'doall':1, 
#                                                 'nextcall':dateheureexec, 
#                                                 'model_id': model_id, 
#                                                 'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s")' % (False , self.date_fact),
#                                                 'state':'code',
#                                                 'priority':0})    
#                     to_invoice = self.env['sale.order']           
#                  
#                      
#             if cptpart > 0:
#                 if not dateheureexec:
#                     dateheureexec = dateheure+datetime.timedelta(minutes=2)
#                 else:
#                     dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
#                 self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
#                                             'active':True, 
#                                             'user_id':self.env.user.id, 
#                                             'interval_number':1, 
#                                             'interval_type':'days', 
#                                             'numbercall':1, 
#                                             'doall':1, 
#                                             'nextcall':dateheureexec, 
#                                             'model_id': model_id, 
#                                             'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s")' % (False , self.date_fact),
#                                             'state':'code',
#                                             'priority':0})    
#                 to_invoice = self.env['sale.order'] 
#                  



 # séparé par paquet de 30 clients
    def create_cron_fact(self):     
        fini = False           
        self.env.cr.execute("""SELECT id FROM ir_model 
                                  WHERE model = %s""", (str(self._name),))            
        info = self.env.cr.dictfetchall()  
        if info:
            model_id = info[0]['id']     
        sale_orders = self.env['sale.order']                    
        query_args = {'periodicity_invoice': self.period_fact,'date_debut' : self.date_debut,'date_fin' : self.date_fin, 'ref_debut': self.ref_debut,'ref_fin':self.ref_fin}
        query = """ SELECT  so.id 
                        FROM sale_order so
                        INNER JOIN res_partner rp on rp.id = so.partner_id 
                        WHERE so.invoice_status = 'to invoice' 
                        AND di_livdt between %(date_debut)s AND %(date_fin)s                            
                        AND rp.ref is not null
                        AND rp.di_period_fact = %(periodicity_invoice)s
                        AND rp.ref between %(ref_debut)s AND %(ref_fin)s 
                        AND rp.di_regr_fact is true                       
                        order by so.partner_id
                        """
 
        self.env.cr.execute(query, query_args)
        ids = [r[0] for r in self.env.cr.fetchall()]
        sale_orders = self.env['sale.order'].search([('id', 'in', ids)])
        if sale_orders:
            partners = sale_orders.mapped('partner_id')
            cptpart = 0
            to_invoice = self.env['sale.order']
            dateheureexec =False
            for partner in partners:      
                cptpart +=1                  
                partner_orders = sale_orders.filtered(lambda so: so.partner_id.id == partner.id)
                dateheure = datetime.datetime.today()                              
                to_invoice+=partner_orders
                if cptpart == 30:
                    cptpart =0
                    if not dateheureexec:
                        dateheureexec = dateheure+datetime.timedelta(minutes=1)
                    else:
                        dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
                    self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
                                                'active':True, 
                                                'user_id':self.env.user.id, 
                                                'interval_number':1, 
                                                'interval_type':'days', 
                                                'numbercall':1, 
                                                'doall':1, 
                                                'nextcall':dateheureexec, 
                                                'model_id': model_id, 
                                                'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s","%s","%s","%s","%s","%s",%s)' % (True , self.date_fact,self.period_fact, self.date_debut, self.date_fin, self.ref_debut, self.ref_fin, self.di_avec_fact),
                                                'state':'code',
                                                'priority':0})    
                    to_invoice = self.env['sale.order']  
                    fini=True  
                    break       
                 
                      
                    
            if cptpart > 0 and not fini:
                if not dateheureexec:
                    dateheureexec = dateheure+datetime.timedelta(minutes=1)
                else:
                    dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
                self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
                                            'active':True, 
                                            'user_id':self.env.user.id, 
                                            'interval_number':1, 
                                            'interval_type':'days', 
                                            'numbercall':1, 
                                            'doall':1, 
                                            'nextcall':dateheureexec, 
                                            'model_id': model_id, 
                                            'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s","%s","%s","%s","%s","%s",%s)' % (True , self.date_fact,self.period_fact, self.date_debut, self.date_fin, self.ref_debut, self.ref_fin, self.di_avec_fact),
                                            'state':'code',
                                            'priority':0})    
                to_invoice = self.env['sale.order'] 
                fini=True
                 
                 
        else:    
            if not fini:     
                sale_orders = self.env['sale.order']                    
                query_args = {'periodicity_invoice': self.period_fact,'date_debut' : self.date_debut,'date_fin' : self.date_fin, 'ref_debut': self.ref_debut,'ref_fin':self.ref_fin}
                query = """ SELECT  so.id 
                                FROM sale_order so
                                INNER JOIN res_partner rp on rp.id = so.partner_id 
                                WHERE so.invoice_status = 'to invoice' 
                                AND di_livdt between %(date_debut)s AND %(date_fin)s                            
                                AND rp.ref is not null
                                AND rp.di_period_fact = %(periodicity_invoice)s
                                AND rp.ref between %(ref_debut)s AND %(ref_fin)s 
                                AND rp.di_regr_fact is false                       
                                order by so.partner_id
                                """
         
                self.env.cr.execute(query, query_args)
                ids = [r[0] for r in self.env.cr.fetchall()]
                sale_orders = self.env['sale.order'].search([('id', 'in', ids)])
                if sale_orders:
                    partners = sale_orders.mapped('partner_id')
                    cptpart = 0
                    to_invoice = self.env['sale.order']
                    dateheureexec =False
                    for partner in partners:      
                        cptpart +=1                  
                        partner_orders = sale_orders.filtered(lambda so: so.partner_id.id == partner.id)
                        dateheure = datetime.datetime.today()                
                         
                        to_invoice+=partner_orders
                        if cptpart == 30:
                            cptpart =0
                            if not dateheureexec:
                                dateheureexec = dateheure+datetime.timedelta(minutes=1)
                            else:
                                dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
                            self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
                                                        'active':True, 
                                                        'user_id':self.env.user.id, 
                                                        'interval_number':1, 
                                                        'interval_type':'days', 
                                                        'numbercall':1, 
                                                        'doall':1, 
                                                        'nextcall':dateheureexec, 
                                                        'model_id': model_id, 
                                                        'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s","%s","%s","%s","%s","%s",%s)' % (False , self.date_fact,self.period_fact, self.date_debut, self.date_fin, self.ref_debut, self.ref_fin, self.di_avec_fact),
                                                        'state':'code',
                                                        'priority':0})    
                            to_invoice = self.env['sale.order']    
                            fini=True       
                            break
                         
                             
                    if cptpart > 0 and not fini:
                        if not dateheureexec:
                            dateheureexec = dateheure+datetime.timedelta(minutes=1)
                        else:
                            dateheureexec = dateheureexec+datetime.timedelta(minutes=15)
                        self.env['ir.cron'].create({'name':'Fact. '+dateheure.strftime("%m/%d/%Y %H:%M:%S"), 
                                                    'active':True, 
                                                    'user_id':self.env.user.id, 
                                                    'interval_number':1, 
                                                    'interval_type':'days', 
                                                    'numbercall':1, 
                                                    'doall':1, 
                                                    'nextcall':dateheureexec, 
                                                    'model_id': model_id, 
                                                    'code': 'model.di_create_invoices(('+str(to_invoice.ids).strip('[]')+'),%s, "%s","%s","%s","%s","%s","%s",%s)' % (False , self.date_fact,self.period_fact, self.date_debut, self.date_fin, self.ref_debut, self.ref_fin, self.di_avec_fact),
                                                    'state':'code',
                                                    'priority':0})    
                        to_invoice = self.env['sale.order'] 
#         if not fini: # on n'a plus de commande à facturer   
#             if self.di_avec_fact:      
# #                 mail_fin = self.env['mail.mail'].create({"subject":"Facturation terminée","email_to":self.env.user.email,"body_html":"La facturation est terminée.","body":"La facturation est terminée."})
# #                 mail_fin.send()
#             else: