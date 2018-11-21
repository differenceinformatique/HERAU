# -*- coding: utf-8 -*-
 
from odoo import fields, models, api
from datetime import datetime, timedelta
    
class DiCout(models.Model):
    _name = "di.cout"
    _description = "Coût moyen pondéré"
    _order = "name"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True, default=lambda self: self.env.user.company_id)                 
    name = fields.Char(string="Name", compute='_compute_name', store=True)
    di_product_id = fields.Many2one('product.product', string='Article')
    di_cmp = fields.Float(string="Coût moyen")
    di_qte = fields.Float(string="Quantité en stock")
    di_nbcol = fields.Float(string="Colis théoriques en stock")
    di_nbpal = fields.Float(string="Palettes théoriques en stock")
    di_nbpiece = fields.Float(string="Pièces théoriques en stock")
    di_poin = fields.Float(string="Poids théorique en stock")     
    di_mont = fields.Float(string="Valorisation du stock")
    di_date = fields.Date(string="Date coût")
    
    @api.multi
    @api.depends('di_product_id', 'di_date')
    def _compute_name(self):
        for cout in self:
            cout.name = cout.di_product_id.display_name + ' ' + cout.di_date.strftime('%d/%m/%Y')
        
    def di_get_cout_uom(self, product_id, date):        
        dernier_mouv_achat = self.env['purchase.order.line'].new()
        # recherche du cmp à la date
        cout = self.search(['&', ('di_product_id', '=', product_id), ('di_date', '=', date)], limit=1).di_cmp
        if not cout or cout == 0.0:
            # si pas de cmp à la date, on prend le dernier prix d'achat
            # date de commande inférieure ou égale à la date saisie
            
            mouvs_achat = self.env['purchase.order.line'].search([('product_id', '=', product_id), ('price_total', '!=', 0.0), ('state', '=', 'purchase')]) \
            .filtered(lambda m: m.order_id.date_order.date() <= date) \
            .sorted(key=lambda m: m.order_id.date_order, reverse=True)
            
             
            for dernier_mouv_achat in mouvs_achat:
                break            
            if dernier_mouv_achat.product_qty != 0.0:         
                cout = dernier_mouv_achat.price_total / dernier_mouv_achat.product_qty                
            else:
                cout = dernier_mouv_achat.price_total 
                
        
        return cout
            
