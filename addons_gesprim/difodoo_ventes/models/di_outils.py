# -*- coding: utf-8 -*-
from odoo import models, fields, api


def di_recherche_prix_unitaire(self,prixOrig, tiers, article, di_un_prix , qte, date):    
    prixFinal = 0.0       
    prixFinal =self.env["di.tarifs"]._di_get_prix(tiers,article,di_un_prix,qte,date)
    if prixFinal == 0.0:
        prixFinal = prixOrig
    return prixFinal