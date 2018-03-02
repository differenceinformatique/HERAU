# -*- coding: utf-8 -*-
from odoo import models, fields, api

def di_recherche_prix_unitaire(prixOrig, tiers, article, di_un_prix , qte, date):    
    prixFinal = 0.0
# TODO : Voir si on gère une table spécifique pour les tarifs ou si on utilise les listes de prix en standard dans Odoo en ajoutant
# les notions d'unité de prix, quantité seuil etc...
# TODO : Quand on aura la table des tarifs, faire la recherche sur cette table         
    if prixFinal == 0.0:
        prixFinal = prixOrig
    return prixFinal