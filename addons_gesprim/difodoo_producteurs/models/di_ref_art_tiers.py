
# -*- coding: utf-8 -*-
from odoo.exceptions import Warning
from odoo import models, fields, api

class DiRefArtTiers(models.Model):
    _inherit = "di.ref.art.tiers"
          
    di_station_id       = fields.Many2one("stock.location",string="Station par défaut")
    di_station_di_des   = fields.Char(related='di_station_id.name')    
        
    @api.onchange('di_product_id')
    def di_charge_val_art(self):        
        super(DiRefArtTiers, self).di_charge_val_art()        
        if self.di_product_id:           
            self.di_station_id = self.di_product_id.di_station_id             