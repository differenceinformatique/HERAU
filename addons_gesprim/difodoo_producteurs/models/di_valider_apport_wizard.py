
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, timedelta, datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class DiValidApportWiz(models.TransientModel):
    _name = "di.valid.apport.wiz"
    _description = "Wizard de validation des apports producteur"
    
        
    di_apport_id = fields.Many2one("di.apportprod", string="Apport")
    di_lot_prod = fields.Char(string="Lot producteur", required=True)
    di_producteur_id = fields.Many2one("res.partner", string="Producteur")
    di_station_id = fields.Many2one("stock.location", string="Station")
    di_product_id = fields.Many2one('product.product', string='Article', required=True)
    di_qte_theo = fields.Float(string="Quantité théorique en unité de référence", required=True, default=0.0)
    di_exploitation = fields.Char(string="Exploitation d'origine", required=True)
    di_date_estim = fields.Date(string="Date de réception estimée")
    
    di_date_recept = fields.Date(string="Date de réception")
    di_qte_recept = fields.Float(string="Quantité receptionnée en unité de référence", default=0.0)
   
    
    #                     TODO : En cours validation apport avec entrée en stock
    @api.multi
    def valider_apport(self):
        for validapp in self :
            apport = self.env["di.apportprod"].browse(validapp.di_apport_id.id)
            if apport :     
                if not apport.di_apport_valide:
                    data = { 'di_qte_recept' : validapp.di_qte_recept,
                            'di_date_recept' : validapp.di_date_recept,
                            'di_apport_valide' : True
                        }
                      
                    apport.update(data) 
                      
                    validapp.generer_entree_stock(apport)                
  
              
    def generer_entree_stock(self, apport):
        
        inventory = self.env['stock.inventory']
        inventory_line = self.env['stock.inventory.line']
          
        if apport.di_qte_recept:
            if apport.di_qte_recept > 0.0:
                
                data_inventory = { 
                'name':'Apport prod.'+apport.di_lot_prod,                
                'location_id': apport.di_station_id.id,                
                'state': 'draft',
                'filter':'none',
                'di_type_inv':'appprod',                        
                        }
                
                codelot = apport.di_lot_prod
                cpt = 0
                lot = self.env['stock.production.lot'].search(['&',('name','=',codelot),('product_id','=',apport.di_product_id.id)],limit=1)  
                while lot and lot.id:
                    cpt= cpt+1
                    codelot = apport.di_lot_prod+'-'+str(cpt)
                    lot = self.env['stock.production.lot'].search(['&',('name','=',codelot),('product_id','=',apport.di_product_id.id)],limit=1)
                    
                data_lot = {
                            'name': codelot,
                            'product_id' : apport.di_product_id.id                                      
                            }
                    
                lot.create(data_lot) 
                self.env.cr.commit()  
                lot = self.env['stock.production.lot'].search(['&',('name','=',codelot),('product_id','=',apport.di_product_id.id)],limit=1)     
                data_inventory_line={
                    'inventory_id':inventory.create(data_inventory).id,
                    'di_lot_prod':apport.di_lot_prod,
                    'product_id': apport.di_product_id.id,
                    'product_name': apport.di_product_id.display_name,
                    'product_uom_id':apport.di_product_id.uom_id.id ,
                    'product_code':apport.di_product_id.default_code,
                    'product_qty': apport.di_qte_recept,
                    'location_id': apport.di_station_id.id,  
                    'location_name': apport.di_station_id.name,  
                    'prod_lot_id': lot.id ,
                    'prodlot_name': lot.name ,
                    'theoretical_qty': 0.0,                    
                    }                                                                                                                                                                                                                                                                                   
                
                inventory_line.create(data_inventory_line)
                self.env.cr.commit()
                inventaire = self.env['stock.inventory'].browse(data_inventory_line['inventory_id'])
                inventaire.action_done()
                                                                            
    @api.model
    def default_get(self, fields):
        res = super(DiValidApportWiz, self).default_get(fields) 
        
        res["di_apport_id"] = self.env.context["active_id"]
        
        Apport = self.env["di.apportprod"].browse(res["di_apport_id"]) 
        res['di_lot_prod'] = Apport.di_lot_prod
        res['di_producteur_id'] = Apport.di_producteur_id.id
        res['di_station_id'] = Apport.di_station_id.id
        res['di_product_id'] = Apport.di_product_id.id
        res['di_qte_theo'] = Apport.di_qte_theo
        res['di_exploitation'] = Apport.di_exploitation
        res['di_date_estim'] = Apport.di_date_estim
        res['di_date_recept'] = datetime.today().date()
        res['di_qte_recept'] = Apport.di_qte_theo
    
        
        # on vérifie qu'on a bien un apport sélectionné
        if not self.env.context["active_id"]:
            raise ValidationError("Pas d'enregistrement selectionné.")
        return res
               
