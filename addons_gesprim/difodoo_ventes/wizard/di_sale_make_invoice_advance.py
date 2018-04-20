# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    di_date_fact = fields.Date(required=True, default=lambda self: self._context.get('date', fields.Date.context_today(self)), string="Date de facturation")
    di_period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
         
    @api.multi
    def create_invoices(self):
        # on surcharge le widget de facturation pour permettre le regroupement de commande sur facture selon paramétrage client           
        if self.advance_payment_method == 'delivered':
            # le regroupement n'est pertinent que dans le cas où il y a plusieurs commandes, donc uniquement méthode "delivered"     
            # on récupère les commandes cochées
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            wPartnerId = 0
            wRegr = True
            # on les parcourt par triées par partner_id
            for order in sale_orders.sorted(key=lambda so: so.partner_id.id):
                if order.partner_id.di_period_fact == self.di_period_fact:
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
            for invoice in invoices:
                invoice.date_invoice=self.di_date_fact
                
            # comme en standard, on lance l'affichage des factures si demandé  
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
        else:
            # dans les autres cas, on laisse le standard faire son travail
            resSuper = super(SaleAdvancePaymentInv, self).create_invoices()
            return resSuper
        #TODO date facture sur facturation std
