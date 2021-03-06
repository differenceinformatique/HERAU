# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    date_fact = fields.Date(required=True, default=datetime.datetime.today().date(), string="Date de facturation")
    period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
    date_debut = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, 1), string="Date Début")
    date_fin = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, calendar.mdays[datetime.date.today().month]), string="Date Fin")
    ref_debut = fields.Char(required=True, default=" ", string="Code Tiers Début")
    ref_fin = fields.Char(required=True, default="ZZZZZZZZZZ", string="Code Tiers Fin")
    
    @api.multi
    def create_invoices(self):
        # on surcharge le widget de facturation pour permettre le regroupement de commande sur facture selon paramétrage client           
#         if self.advance_payment_method == 'delivered':
        # le regroupement n'est pertinent que dans le cas où il y a plusieurs commandes, donc uniquement méthode "delivered"     
        # on récupère les commandes cochées
        if self._context.get('active_ids', []):
            sale_orders_1 = self.env['sale.order'].browse(self._context.get('active_ids', [])).filtered(lambda so: so.partner_id.ref != False )
            if len(sale_orders_1)==1:
                # si une seule commande, les filtres ne seront pas affichés, on les renseigne en fonction de la commande                 
                self.period_fact = sale_orders_1.partner_id.di_period_fact
                self.date_debut = sale_orders_1.di_livdt
                self.date_fin = sale_orders_1.di_livdt
                self.ref_debut = sale_orders_1.partner_id.ref
                self.ref_fin = sale_orders_1.partner_id.ref
            # on filtre sur la date
            sale_orders = sale_orders_1.filtered(lambda so: so.di_livdt >= self.date_debut and so.di_livdt <= self.date_fin and so.partner_id.di_period_fact == self.period_fact and so.partner_id.ref >= self.ref_debut and so.partner_id.ref <= self.ref_fin).sorted(key=lambda so: so.partner_id.id)
              # on filtre sur le code client
    #         sale_orders = sale_orders_2.filtered(lambda so: so.partner_id.ref >= self.ref_debut and so.partner_id.ref <= self.ref_fin and so.partner_id.di_period_fact == self.period_fact )
            wPartnerId = 0
            wRegr = True
            # on les parcourt, triées par partner_id
            for order in sale_orders:
                # on vérifie que la commande correspond à la périodicité et aux dates de selection
    #             if order.partner_id.di_period_fact == self.period_fact:
                    # à chaque rupture de partner_id on lance une facturation
                if wPartnerId != order.partner_id.id:
                    if wPartnerId != 0:
                        order_partner = sale_orders.filtered(lambda so: so.partner_id.id == wPartnerId)
                        order_partner.action_invoice_create(grouped=(not wRegr))    # grouped=False pour regrouper par client
                    wPartnerId = order.partner_id.id
                    wRegr = order.partner_id.di_regr_fact
            # fin de boucle on lance la facturation
            if wPartnerId != 0:
                order_partner = sale_orders.filtered(lambda so: so.partner_id.id == wPartnerId)
                order_partner.action_invoice_create(grouped=(not wRegr),final=True)
            # on met à jour la date de facture    
            invoices = sale_orders.mapped('invoice_ids')
            param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
            # //morvan 10/05/2019 - pour test perfs
            for s_o in sale_orders: #pour passer en complètement facturé les commandes avec reliquat
                s_o.action_done()    
            for invoice in invoices:
                invoice.date_invoice=self.date_fact
                if param.di_autovalid_fact_ven:
                    if invoice.state=='draft':
                        invoice.action_invoice_open()
    #                 if param.di_autoimp_fact_ven: # ne fonctionne pas
    #                     invoice.invoice_print()
                    
    #             return sale_orders.action_print_invoice() # ne fonctionne pas
                
            # comme en standard, on lance l'affichage des factures si demandé  
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
    #     else:
    #         # dans les autres cas, on laisse le standard faire son travail
    #         resSuper = super(SaleAdvancePaymentInv, self).create_invoices()
    #         return resSuper
            #TODO date facture sur facturation std

            
        else:           
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
            sale_orders_non_group = self.env['sale.order'].search([('id', 'in', ids)])
            if sale_orders_non_group:
                sale_orders_non_group.action_invoice_create(grouped=False,final=True)     
            
            
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
            sale_orders_group = self.env['sale.order'].search([('id', 'in', ids)])
            if sale_orders_group:
                sale_orders_group.action_invoice_create(grouped=True,final=True)       
            sale_orders = sale_orders_non_group + sale_orders_group
#             sale_orders = self.env['sale.order'].search([('invoice_status','=','to invoice'),('di_livdt','>=',self.date_debut),('di_livdt','<=',self.date_fin)]).filtered(lambda so: so.partner_id.ref != False and so.partner_id.di_period_fact == self.period_fact  and so.partner_id.ref >= self.ref_debut and so.partner_id.ref <= self.ref_fin).sorted(key=lambda so: so.partner_id.id)
            
            # //morvan 10/05/2019 - pour test perfs                    
            for s_o in sale_orders: #pour passer en complètement facturé les commandes avec reliquat
                s_o.action_done()
                
            invoices = sale_orders.mapped('invoice_ids')
            invoices.write({'date_invoice':self.date_fact})
            param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
            if param.di_autovalid_fact_ven:
                if invoice.state=='draft':
                    invoices.action_invoice_open()
                        
#             for invoice in invoices:
#                 invoice.date_invoice=self.date_fact
#                 
    #                 if param.di_autoimp_fact_ven: # ne fonctionne pas
    #                     invoice.invoice_print()
                    
    #             return sale_orders.action_print_invoice() # ne fonctionne pas
                
            # comme en standard, on lance l'affichage des factures si demandé  
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}