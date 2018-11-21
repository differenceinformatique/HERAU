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
    di_mode_grille_ach = fields.Selection([("HORIZON", "Horizon"), ("NBCDE", "Nombre de commande")], string="Mode recherche grille achat",
                                           help="Sélectionne le mode de recherche pour la grille d'achat. Sur un horizon ou sur un nombre de commande.",default="HORIZON")
    di_horizon_ach = fields.Integer(string="Horizon achat",help="""Horizon en jours pour la grille d'achat. """)
    di_nbcde_ach = fields.Integer(string="Nombre de commande",help="""Nombre de commandes pour la grille d'achat. """)
    di_printer_id = fields.Many2one('di.printer',string="Imprimante étiquette")
    di_label_id = fields.Many2one('di.labelmodel',string="Modèle étiquette")
    di_printer_ach_id = fields.Many2one('di.printer',string="Imprimante étiquette achats")
    di_label_ach_id = fields.Many2one('di.labelmodel',string="Modèle étiquette achats")
    di_seuil_marge_prc = fields.Float(string='Taux de marge minimal',help="""Taux de marge en vente, en dessous duquel vous serez averti. """, default=0.0)
    
    di_compta_prg   = fields.Selection([("INTERNE", "Interne"), ("DIVALTO", "Divalto"),("EBP", "EBP"),("SAGE","Sage")], string="Logiciel de comptabilité",
                                           help="Permet de savoir vers quel logiciel de comptabilité on va exporter (ou non) les écritures.",default="INTERNE")
    di_dos_compt = fields.Char(string='Dossier comptable',default="",help="""Dossier d'intégration pour le logiciel de comptabilité.""")
    di_etb_compt = fields.Char(string='Etablissement comptable',default="",help="""Etablissement d'intégration pour le logiciel de comptabilité.""")        
    di_nom_exp_ecr_compta = fields.Char(string='Nom fichier export écritures',default="ecritures.csv",help="""Nom par défaut du fichier d'export des écritures comptables.""")
    di_seq_art  = fields.Boolean(string="Codification automatique article", default=False, help="""Activation de l'affectation automatique du code article""")
    di_seq_cli  = fields.Boolean(string="Codification automatique client", default=False, help="""Activation de l'affectation automatique du code client""")
    di_seq_fou  = fields.Boolean(string="Codification automatique fournisseur", default=False, help="""Activation de l'affectation automatique du code fournisseur""")
    di_autovalid_fact_ven  = fields.Boolean(string="Validation automatique des factures de ventes", default=False, help="""Validation automatique des factures de ventes""")
    di_autoimp_fact_ven  = fields.Boolean(string="Impression automatique des factures de ventes", default=False, help="""Impression automatique des factures de ventes""")
         
                       
    #unicité 
    @api.multi
    @api.constrains('di_company_id')
    def _check_di_company_id(self):
        for param in self:
            if param.di_company_id:
                di_company_id = param.search([
                    ('id', '!=', param.id),
                    ('di_company_id', '=', param.di_company_id.id)], limit=1)
                if di_company_id:
                    raise Warning("Le paramétrage pour ce dossier existe déjà.")