# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _

    
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
    
    di_prc_com_avec_court = fields.Float(string='% commission OP avec metteur en marche ',help="""Pourcentage de commission que prendra l'OP sur la ligne si un metteur en marche a fait la vente. """, default=0.0)
    di_prc_com_sans_court = fields.Float(string='% commission OP sans metteur en marche',help="""Pourcentage de commission que prendra l'OP sur la ligne si l'OP a fait la vente directe. """, default=0.0)
    
    di_art_com  =   fields.Many2one('product.product',string="Article commission",help="""Article qui va servir pour la facturation des commissions. """)
    
     
                       
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