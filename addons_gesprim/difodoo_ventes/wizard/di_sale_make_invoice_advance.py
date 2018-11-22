# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    date_fact = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, calendar.mdays[datetime.date.today().month]), string="Date de facturation")
    period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
    date_debut = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, 1), string="Date Début")
    date_fin = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, calendar.mdays[datetime.date.today().month]), string="Date Fin")
    ref_debut = fields.Char(required=True, default="C", string="Code Tiers Début")
    ref_fin = fields.Char(required=True, default="Czzzzzzz", string="Code Tiers Fin")
         
    @api.multi
    def create_invoices(self):
        # on surcharge le widget de facturation pour permettre le regroupement de commande sur facture selon paramétrage client           
        if self.advance_payment_method == 'delivered':
            # le regroupement n'est pertinent que dans le cas où il y a plusieurs commandes, donc uniquement méthode "delivered"     
            # on récupère les commandes cochées
            sale_orders_1 = self.env['sale.order'].browse(self._context.get('active_ids', []))
            if len(sale_orders_1)<=1:
                # si une seule commande, les filtres ne seront pas affichés, on les renseigne en fonction de la commande                 
                self.period_fact = sale_orders_1.partner_id.di_period_fact
                self.date_debut = sale_orders_1.di_livdt
                self.date_fin = sale_orders_1.di_livdt
                self.ref_debut = sale_orders_1.partner_id.ref
                self.ref_fin = sale_orders_1.partner_id.ref
            # on filtre sur la date
            sale_orders_2 = sale_orders_1.filtered(lambda so: so.di_livdt >= self.date_debut and so.di_livdt <= self.date_fin)
            # on filtre sur le code client
            sale_orders = sale_orders_2.filtered(lambda so: so.partner_id.ref >= self.ref_debut and so.partner_id.ref <= self.ref_fin)
            wPartnerId = 0
            wRegr = True
            # on les parcourt, triées par partner_id
            for order in sale_orders.sorted(key=lambda so: so.partner_id.id):
                # on vérifie que la commande correspond à la périodicité et aux dates de selection
                if order.partner_id.di_period_fact == self.period_fact:
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
                order_partner.action_invoice_create(grouped=(not wRegr))
            # on met à jour la date de facture    
            invoices = sale_orders.mapped('invoice_ids')
            param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
            for invoice in invoices:
                invoice.date_invoice=self.date_fact
                if param.di_autovalid_fact_ven:
                    invoice.action_invoice_open()
#                 if param.di_autoimp_fact_ven: # ne fonctionne pas
#                     invoice.invoice_print()
                    
#             return sale_orders.action_print_invoice() # ne fonctionne pas
                
            # comme en standard, on lance l'affichage des factures si demandé  
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
        else:
            # dans les autres cas, on laisse le standard faire son travail
            resSuper = super(SaleAdvancePaymentInv, self).create_invoices()
            return resSuper
        #TODO date facture sur facturation std
