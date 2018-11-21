# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
    
class DiCodeDest(models.Model):
    _name = "di.code.dest"
    _description = "Code destination"
    _order = "name"
    
    name = fields.Char(string="Code Destination", compute='_compute_name', store=True, readonly=True)
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    di_des = fields.Char(string="Désignation", required=True)
    di_code_dest = fields.Char(string='Code destination', required=True, help="Code destination pour les grilles transporteurs")
    country_id = fields.Many2one('res.country', string='Pays', required=True, help="Pays correspondant au code destination") 
    
    @api.multi
    @api.depends('country_id', 'di_code_dest')
    def _compute_name(self):
        for code in self:
            if code.country_id and code.di_code_dest:
                code.name = code.country_id.code + '_' + code.di_code_dest 