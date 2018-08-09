# -*- coding: utf-8 -*-
 
from odoo import api, fields, models

    
class DiParam(models.Model):
    _name = "di.param"
    _description = "Parametres"
    _order = "name"
        
    di_company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Name',readonly=True,default=lambda self: self.env.user.company_id.name)
#     di_act_grille_vente = fields.Boolean(string="Activer la grille de vente",help="""Permet l'activation de la grille de vente pour 
#     une saisie plus rapide sur cadencier.""", default=False)
    di_horizon = fields.Integer(string="Horizon",help="""Horizon en jours pour la grille de vente. """)
    di_printer_id = fields.Many2one('di.printer',string="Imprimante étiquette")
    di_label_id = fields.Many2one('di.labelmodel',string="Modèle étiquette")
    di_printer_ach_id = fields.Many2one('di.printer',string="Imprimante étiquette achats")
    di_label_ach_id = fields.Many2one('di.labelmodel',string="Modèle étiquette achats")
    di_seuil_marge_prc = fields.Float(string='Taux de marge minimal',help="""Taux de marge en vente, en dessous duquel vous serez averti. """, default=0.0)
    
    di_compta_prg   = fields.Selection([("INTERNE", "Interne"), ("DIVALTO", "Divalto"),("EBP", "EBP"),("SAGE","Sage")], string="Logiciel de comptabilité",
                                           help="Permet de savoir vers quel logiciel de comptabilité on va exporter (ou non) les écritures.",default="INTERNE")
    di_dos_divalto = fields.Char(string='Dossier Divalto',default="",help="""Dossier d'intégration sur Divalto.""")
    di_etb_divalto = fields.Char(string='Etablissement Divalto',default="",help="""Etablissement d'intégration sur Divalto.""")        
    di_nom_exp_ecr_compta = fields.Char(string='Nom fichier export écritures',default="ecritures.csv",help="""Nom par défaut du fichier d'export des écritures comptables.""")
     
                       
    #unicité 
    @api.one
    @api.constrains('di_company_id')
    def _check_di_company_id(self):
        if self.di_company_id:
            di_company_id = self.search([
                ('id', '!=', self.id),
                ('di_company_id', '=', self.di_company_id.id)], limit=1)
            if di_company_id:
                raise Warning("Le paramétrage pour ce dossier existe déjà.")