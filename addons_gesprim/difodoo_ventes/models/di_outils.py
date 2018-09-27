
# -*- coding: utf-8 -*-
from odoo import models, fields, api

def di_rechercher_lot_qte_libre(self, product_id, location_id):   
                
 
    # recheche du prix avec un client spécifique
    query_args = {'product_id': product_id.id}
    query = """ SELECT  id 
                    FROM stock_production_lot                         
                    WHERE product_id = %(product_id)s                   
                    ORDER BY create_date                     
                    """

    self.env.cr.execute(query, query_args)
    lot_ids = [(r[0]) for r in self.env.cr.fetchall()]
    # r= self.env.cr.fetchall()
    lotsqtes = {}
    for lot_id in lot_ids:
        lot = self.env['stock.production.lot'].browse(lot_id)                    
        lotsqtes.update({
            
              lot_id: self.env['stock.quant']._get_available_quantity(product_id, location_id, lot)                                      
                                    })
#           
               
    return lotsqtes


def replace_accent(self, s):
    if s:
        s = s.replace('ê', 'e') \
             .replace('è', 'e') \
             .replace('é', 'e') \
             .replace('à', 'a') \
             .replace('ô', 'o') \
             .replace('ö', 'o') \
             .replace('î', 'i')
    return s                 
