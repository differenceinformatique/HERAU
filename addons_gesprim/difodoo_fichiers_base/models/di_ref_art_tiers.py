
# -*- coding: utf-8 -*-
from odoo.exceptions import Warning
from odoo import models, fields, api

class DiRefArtTiers(models.Model):
    _name = "di.ref.art.tiers"
    _description = "Referencement tiers"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)
    name                = fields.Char(string="Name",compute="_compute_name",store=True)     
    di_partner_id       = fields.Many2one('res.partner',String='Tiers',required=True)
    di_product_id       = fields.Many2one('product.product',String='Article', required=True)
    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie par défaut")
    di_type_palette_id  = fields.Many2one('product.packaging', string='Palette par défaut')   
    di_type_colis_id    = fields.Many2one('product.packaging', string='Colis par défaut')
    di_un_prix          = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix par défaut")
    di_reftiers         = fields.Char(string="Référence tiers",default="")
    di_destiers         = fields.Char(string="Désignation tiers",default="")
    di_eantiers         = fields.Char(string="EAN tiers",default="")
    di_station_id       = fields.Many2one("stock.location",string="Station par défaut")
    di_station_di_des   = fields.Char(related='di_station_id.name')    
        
    @api.onchange('di_product_id')
    def di_charge_val_art(self):
        if self.di_product_id:
            self.di_un_saisie = self.di_product_id.di_un_saisie
            self.di_type_palette_id = self.di_product_id.di_type_palette_id
            self.di_type_colis_id = self.di_product_id.di_type_colis_id
            self.di_un_prix = self.di_product_id.di_un_prix
            self.di_eantiers = self.di_product_id.barcode
            self.di_station_id = self.di_product_id.di_station_id 
            
    @api.depends('di_product_id', 'di_partner_id')
    def _compute_name(self):
        for refart in self:
            if refart.di_partner_id and refart.di_product_id:
                refart.name=refart.di_partner_id.name+' '+refart.di_product_id.name+' '+refart.di_reftiers+' '+refart.di_destiers+' '+refart.di_eantiers
            

    #unicité 
    @api.one
    @api.constrains('di_product_id', 'di_partner_id')
    def _check_primary_key(self):
        if self.di_product_id and self.di_partner_id:
            ref = self.search([('id', '!=', self.id),('di_partner_id','=',self.di_partner_id.id),('di_product_id','=',self.di_product_id.id)],limit=1)            
            if ref:
                raise Warning("Le couple tiers/article existe déjà.")