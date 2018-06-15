# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DiEtiquetteLabelModel(models.Model):
    _name = "di.labelmodel"
    _description = "Label model"
    _order = "name"
    
    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Nom", required=True)
    file = fields.Char(sting="Fichier", required=True,help="Chemin du fichier")
    commentary = fields.Text(string="Commentaire")
    
    _sql_constraints = [("uniq_id","unique(code)","Un modèle existe déjà avec ce code, il doit être unique !"),]
    
    