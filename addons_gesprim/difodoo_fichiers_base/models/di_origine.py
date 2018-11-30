
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
    
class DiOrigine(models.Model):
    _name = "di.origine"
    _description = "Origine"
    _order = "name"
    
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)         
    di_des = fields.Char(string="Désignation", required=True)
    name = fields.Char(string="Code", required=True)
    
    # on définie la fonction name_search pour améliorer l'import excel     
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        firsts_records = self.search([('di_des', '=ilike', name)] + args, limit=limit)
        search_domain = [('name', operator, name)]
        search_domain.append(('id', 'not in', firsts_records.ids))
        records = firsts_records + self.search(search_domain + args, limit=limit)
        return [(record.id, record.display_name) for record in records]