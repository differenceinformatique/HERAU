
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime

class DiConsignesWiz(models.TransientModel):
    _name = "di.consignes.wiz"
    _description = "Wizard de visualisation des consignes chez le client avec retour de consigne et MAJ suivi lot"
    
    di_cons_ids = fields.Many2many("di.cons.line.wiz", string="Consignes chez le client")
    
    @api.multi           
    def di_plus_suivi(self):
        """Marque le numéro de lot comme n'étant plus à suivre afin qu'il n'apparaisse plus dans la liste des emballages chez les clients."""
        for cons in self:
            for line in cons.di_cons_ids:
                if line.di_select:
                    line.di_lot_id.update({'di_plus_suivi':True})
            # Suppression des lignes de consignes générées par l'utilisateur car sinon on les retrouve quand on réouvre le wizard même si elles n'ont pas lieu d'être
            self._cr.execute("DELETE FROM di_cons_line_wiz WHERE create_uid=%s ", [self.env.user.id])        
            self.env.cr.commit()
                       
    @api.multi
    def di_retourner_consigne(self):
        """Créé un inventaire de type retour consigne avec les lignes sélectionnées pour en faire le retour en stock. """
        for cons in self:
            for line in self.di_cons_ids:
                inventory = self.env['stock.inventory']
                inventory_line = self.env['stock.inventory.line']
                                          
                data_inventory = { 
                                    'name':'Retour consigne '+line.di_lot_name+' '+line.di_product_name+' '+line.di_partner_name+' '+datetime.today().date().strftime('%d/%m/%Y'),                
                                    'location_id': line.di_sml_id.location_id.id,                
                                    'state': 'draft',
                                    'filter':'none',
                                    'di_type_inv':'retcons',                        
                                }
                                                                     
                data_inventory_line={
                                        'inventory_id':inventory.create(data_inventory).id,                        
                                        'product_id': line.di_sml_id.product_id.id,
                                        'product_name': line.di_sml_id.product_id.display_name,
                                        'product_uom_id':line.di_sml_id.product_id.uom_id.id ,
                                        'product_code':line.di_sml_id.product_id.default_code,
                                        'product_qty': line.di_sml_id.qty_done,
                                        'location_id': line.di_sml_id.location_id.id,  
                                        'location_name': line.di_sml_id.location_id.name,  
                                        'prod_lot_id': line.di_sml_id.lot_id.id ,
                                        'prodlot_name': line.di_sml_id.lot_id.name ,
                                        'theoretical_qty': 0.0,                    
                                    }                                                                                                                                                                                                                                                                                   
                        
                inventory_line.create(data_inventory_line)
                self.env.cr.commit()
                inventaire = self.env['stock.inventory'].browse(data_inventory_line['inventory_id'])
                inventaire.action_done()
                # suppression des lignes de consignes générées par l'utilisateur car sinon on les retrouve quand on réouvre le wizard même si elles n'ont pas lieu d'être
                self._cr.execute("DELETE FROM di_cons_line_wiz WHERE create_uid=%s ", [self.env.user.id])        
                self.env.cr.commit()
    
    
    @api.model
    def default_get(self, fields):

        cons_line = self.env['di.cons.line.wiz']
        # recherche des stock_move_line (lignes de mouvements de stock) dont l'article est un emballage consigné, le statut est fait, le lot est suivi et c'est une sortie
        sml_ids = self.env['stock.move.line'].search(['&', ('product_id.di_cons', '=', True), ('state', '=', 'done'), ('lot_id', '!=', False), ('lot_id.di_plus_suivi', '=', False), ('picking_id', '!=', False), ('picking_id.picking_type_id.code', '=', 'outgoing')])         
                 
        for sml in sml_ids:   
            #calcul de la quantité en stock sur le lot
            (nbcol,nbpal,nbpiece,poids,qte_std) = self.env['stock.move.line'].di_qte_spe_en_stock(sml.product_id,False,sml.lot_id)
            if qte_std <=0.0:   # si le stock est négatif, cela veut dire que l'article se trouve encore chez le client, on va l'afficher     
                cons_line.create({
                    'di_lot_id' :sml.lot_id.id, 
                    'di_product_id'  :sml.product_id.id,                                        
                    'di_parter_id':sml.picking_id.partner_id.id,
                    'di_sml_id':sml.id,                                       
                    'di_select':False,    
                    })   
                
        self.env.cr.commit()         
                                  
        cons_ids = self.env['di.cons.line.wiz'].search([('create_uid','=',self.env.user.id)])

        res = super(DiConsignesWiz, self).default_get(fields)
        res['di_cons_ids'] =cons_ids.ids                 
        return res    