# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DiEtiquettePrinter(models.Model):
    _name = "di.printer"
    _description = "Printer"
    _order = "name"
    
    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Nom", required=True)
    realname = fields.Char(string="Nom windows")
    adressip = fields.Char(string="Adresse IP")
    port = fields.Integer(string="Port")
    commentary = fields.Text(string="Commentaire")
    isimpetiq = fields.Boolean(string="Imprimante étiquette",default=False,help="Coché = Imprimante étiquette, Non coché = Imprimante normale")
    
    _sql_constraints = [("uniq_id","unique(code)","Une imprimante existe déjà avec ce code. Il doit être unique !"),]
    