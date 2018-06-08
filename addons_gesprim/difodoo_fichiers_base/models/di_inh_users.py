# -*- coding: utf-8 -*-

# from odoo.exceptions import Warning
from odoo import models , api

class Users(models.Model):
    _inherit = "res.users"

    @api.model
    def create(self, vals):
        user = super(Users, self).create(vals)
        # l'utilisateur n'est ni client ni fournisseur par défaut
        user.customer = 0
        user.supplier = 0
        return user