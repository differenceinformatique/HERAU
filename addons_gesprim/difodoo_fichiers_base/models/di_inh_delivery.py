# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from math import ceil

class PriceRule(models.Model):
    _inherit = "delivery.price.rule"
    _order = 'carrier_name,di_code_dest_id,variable,operator,max_value'
    
    # on change les décimales sur les prix
    list_base_price = fields.Float(string='Sale Base Price', digits=(16,4), required=True, default=0.0)
    list_price = fields.Float('Sale Price', digits=(16,4), required=True, default=0.0)
    name = fields.Char(compute='_compute_name', store=True)
    di_code_dest_id = fields.Many2one('di.code.dest', string='Code destination', help="Code destination pour les grilles transporteurs")
    carrier_name = fields.Char(string="Nom Transporteur", related='carrier_id.name', store=True)
    # ajout du calcul à la palette     
    variable = fields.Selection([('weight', 'Weight'), ('volume', 'Volume'), ('wv', 'Weight * Volume'), ('price', 'Price'), ('quantity', 'Quantity'), ('palette', 'Palette')], required=True, default='weight')
    variable_factor = fields.Selection([('weight', 'Weight'), ('volume', 'Volume'), ('wv', 'Weight * Volume'), ('price', 'Price'), ('quantity', 'Quantity'), ('palette', 'Palette')], 'Variable Factor', required=True, default='weight')
     
    @api.depends('variable', 'operator', 'max_value', 'list_base_price', 'list_price', 'variable_factor')
    def _compute_name(self):
        # traduction en français
        for rule in self:
            if rule.di_code_dest_id.name:
                codedest = rule.di_code_dest_id.name
            else:
                codedest = ''
            name = '%s si %s %s %s alors' % (codedest, _(dict(self.fields_get(allfields=['variable'])['variable']['selection'])[rule.variable]), rule.operator, rule.max_value)
            if rule.list_base_price and not rule.list_price:
                name = '%s prix fixe %s' % (name, rule.list_base_price)
            elif rule.list_price and not rule.list_base_price:
                name = '%s %s fois le %s' % (name, rule.list_price, _(dict(self.fields_get(allfields=['variable_factor'])['variable_factor']['selection'])[rule.variable_factor]))
            else:
                name = '%s prix fixe %s + %s fois le %s' % (name, rule.list_base_price, rule.list_price, _(dict(self.fields_get(allfields=['variable_factor'])['variable_factor']['selection'])[rule.variable_factor]))
            rule.name = name

class ProviderGrid(models.Model):
    _inherit = "delivery.carrier"
            
    def _get_price_available(self, order):
        self.ensure_one()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        palette = ceil(order.di_nbpal)    # difodoo
        code_dest_id = order.partner_shipping_id.di_code_dest_id
        total = (order.amount_total or 0.0) - total_delivery

        total = order.currency_id.with_context(date=order.date_order).compute(total, order.company_id.currency_id)
        #return self._get_price_from_picking(total, weight, volume, quantity)
        return self._get_price_from_picking(total, weight, volume, quantity, palette, code_dest_id)
                     
    #def _get_price_from_picking(self, total, weight, volume, quantity):
    def _get_price_from_picking(self, total, weight, volume, quantity, palette, code_dest_id):
        price = 0.0
        criteria_found = False
        #price_dict = {'price': total, 'volume': volume, 'weight': weight, 'wv': volume * weight, 'quantity': quantity}
        price_dict = {'price': total, 'volume': volume, 'weight': weight, 'wv': volume * weight, 'quantity': quantity, 'palette': palette}
        for line in self.price_rule_ids:
            # récupération du code destination            
            if line.di_code_dest_id == code_dest_id:
                test = safe_eval(line.variable + line.operator + str(line.max_value), price_dict)
                if test:
                    price = line.list_base_price + line.list_price * price_dict[line.variable_factor]
                    criteria_found = True
                    break
        if not criteria_found:
            raise UserError(_("No price rule matching this order; delivery cost cannot be computed."))

        return price