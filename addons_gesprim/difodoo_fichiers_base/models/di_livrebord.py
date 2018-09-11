# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
    
class DiLivreBord(models.Model):
    _name = "di.livrebord"
    _description = "Livre de bord"
    _order = "name"
    
    company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)             
    message = fields.Char(string="Message", required=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, default=lambda self: self.env.user)
    name = fields.Datetime(string="Date", required=True, default=fields.Datetime.now())
    
    def ecrire(self, mess):
        """
        pour écrire dans le livre de bord
        utiliser les commandes suivantes pour écrire
        lb = self.env['di.livrebord']
        lb.ecrire("message test")
        """
        self.env['di.livrebord'].create({'message' : mess})
        