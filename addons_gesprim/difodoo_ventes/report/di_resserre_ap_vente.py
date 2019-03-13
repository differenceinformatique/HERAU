# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class DiResserreDet(models.Model):
    _name = "di.resserre.det"
    _description = "Resserre détaillée"
    _auto = False
    _rec_name = 'date'

    date = fields.Datetime(readonly=True)
    product_id = fields.Many2one('product.product', string='Article', readonly=True)    
    categ_id = fields.Many2one('product.category', string='Catégorie article', readonly=True)    
    company_id = fields.Many2one('res.company', string='Société', readonly=True)
    di_col_stock = fields.Float(string='Colis en stock', readonly=True)
    di_qte_stock = fields.Float(string='Quantité en stock', readonly=True)
    di_poib_stock = fields.Float(string='Poids brut en stock', readonly=True)
    di_poin_stock = fields.Float(string='Poids net en stock', readonly=True)
    
    di_col_ven = fields.Float(string='Colis vendus', readonly=True)
    di_qte_ven = fields.Float(string='Quantité vendue', readonly=True)
    di_poib_ven = fields.Float(string='Poids brut vendu', readonly=True)
    di_poin_ven = fields.Float(string='Poids net vendu', readonly=True)
    
#     di_pv = fields.Float(string='Prix vente', readonly=True, group_operator="avg")
    di_val_ven = fields.Float(string='Valeur vente', readonly=True)
#     di_val_marge = fields.Float(string='Valeur marge', readonly=True)
    
    di_col_ach = fields.Float(string='Colis achetés', readonly=True)
    di_qte_ach = fields.Float(string='Quantité achetée', readonly=True)
    di_poib_ach = fields.Float(string='Poids brut acheté', readonly=True)
    di_poin_ach = fields.Float(string='Poids net acheté', readonly=True)
    
#     di_pa = fields.Float(string='Prix achat', readonly=True, group_operator="avg")
    di_val_stock = fields.Float(string='Valeur stock', readonly=True)
    di_val_marge = fields.Float(string='Valeur marge', readonly=True)
    
    di_col_regul_entree = fields.Float(string='Colis régul.entrée', readonly=True)
    di_qte_regul_entree = fields.Float(string='Quantité régul. entrée', readonly=True)
    di_poib_reg_ent = fields.Float(string='Poids brut régul. entrée', readonly=True)
    di_poin_reg_ent = fields.Float(string='Poids net régul. entrée', readonly=True)
    
      
    di_col_regul_sortie = fields.Float(string='Colis régul. sortie', readonly=True)
    di_qte_regul_sortie = fields.Float(string='Quantité régul. sortie', readonly=True)
    di_poib_reg_sort = fields.Float(string='Poids brut régul. sortie', readonly=True)
    di_poin_reg_sort = fields.Float(string='Poids net régul. sortie', readonly=True)    
    
    _order = 'date desc'

    _depends = {
        
        'stock.move.line': [
            'picking_id', 'product_id',
            'product_qty',
        ],
        'stock.location': [
            'usage',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
    }

    def _select(self):
        select_str = """
            SELECT sub.id, sub.date, 
                sub.state,
                sub.categ_id,
                sub.product_id,
                
                sub.di_col_stock as di_col_stock,            
                sub.di_qte_stock as di_qte_stock,
                sub.di_poib_stock as di_poib_stock,
                sub.di_poin_stock as di_poin_stock,
                
                sub.di_val_stock as di_val_stock,                            

                sub.di_col_ven as di_col_ven,
                sub.di_qte_ven as di_qte_ven,                
                sub.di_poib_ven as di_poib_ven,
                sub.di_poin_ven as di_poin_ven,
                sub.di_val_ven as di_val_ven,
                
                (sub.di_val_ven - sub.di_val_stock) as di_val_marge,                                                                  
                
                sub.di_col_ach as di_col_ach,
                sub.di_qte_ach as di_qte_ach,
                sub.di_poib_ach as di_poib_ach,
                sub.di_poin_ach as di_poin_ach,
                                
                sub.di_col_regul_entree as di_col_regul_entree,
                sub.di_qte_regul_entree as di_qte_regul_entree,
                sub.di_poib_reg_ent as di_poib_reg_ent,
                sub.di_poin_reg_ent as di_poin_reg_ent,
                
                sub.di_col_regul_sortie as di_col_regul_sortie,
                sub.di_qte_regul_sortie as di_qte_regul_sortie,
                sub.di_poib_reg_sort as di_poib_reg_sort,
                sub.di_poin_reg_sort as di_poin_reg_sort

        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT pr.id AS id,
                    sm.date AS date,
                    sm.product_id,                                         
                    sm.state, pt.categ_id,
                    SUM ( Case when stock_type.usage = 'internal' then sm.di_nb_colis else -1*sm.di_nb_colis end) AS di_col_stock,
                    SUM ( Case when stock_type.usage = 'internal' then sm.qty_done else -1*sm.qty_done end) AS di_qte_stock,
                    SUM ( Case when stock_type.usage = 'internal' then sm.di_poib else -1*sm.di_poib end) AS di_poib_stock,
                    SUM ( Case when stock_type.usage = 'internal' then sm.di_poin else -1*sm.di_poin end) AS di_poin_stock,
                    
                    SUM ( Case when stock_type.usage = 'internal' then cmp.di_cmp*sm.qty_done else -1*cmp.di_cmp*sm.qty_done end) AS di_val_stock,                                                                                                        
                    
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage = 'customer' then sm.di_nb_colis else 0 end) AS di_col_ven,
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage = 'customer' then sm.qty_done else 0 end) AS di_qte_ven,
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage = 'customer' then sm.di_poib else 0 end) AS di_poib_ven,
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage = 'customer' then sm.di_poin else 0 end) AS di_poin_ven,
                    
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage = 'customer' then sm.qty_done*sol.price_unit else 0 end) AS di_val_ven,                                        
                    
                    SUM ( Case when orig_type.usage = 'supplier' and  stock_type.usage = 'internal' then sm.di_nb_colis else 0 end) AS di_col_ach,
                    SUM ( Case when orig_type.usage = 'supplier' and  stock_type.usage = 'internal' then sm.qty_done else 0 end) AS di_qte_ach,
                    SUM ( Case when orig_type.usage = 'supplier' and  stock_type.usage = 'internal' then sm.di_poib else 0 end) AS di_poib_ach,
                    SUM ( Case when orig_type.usage = 'supplier' and  stock_type.usage = 'internal' then sm.di_poin else 0 end) AS di_poin_ach,
                    
                    SUM ( Case when orig_type.usage <> 'supplier' and  stock_type.usage = 'internal' then sm.di_nb_colis else 0 end) AS di_col_regul_entree,
                    SUM ( Case when orig_type.usage <> 'supplier' and  stock_type.usage = 'internal' then sm.qty_done else 0 end) AS di_qte_regul_entree,
                    SUM ( Case when orig_type.usage <> 'supplier' and  stock_type.usage = 'internal' then sm.di_poib else 0 end) AS di_poib_reg_ent,
                    SUM ( Case when orig_type.usage <> 'supplier' and  stock_type.usage = 'internal' then sm.di_poin else 0 end) AS di_poin_reg_ent,
                    
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage <> 'customer' then sm.di_nb_colis else 0 end) AS di_col_regul_sortie,
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage <> 'customer' then sm.qty_done else 0 end) AS di_qte_regul_sortie,
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage <> 'customer' then sm.di_poib else 0 end) AS di_poib_reg_sort,
                    SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage <> 'customer' then sm.di_poin else 0 end) AS di_poin_reg_sort
                    
                    
                    

        """
        return select_str
# --SUM ( Case when orig_type.usage = 'internal' and  stock_type.usage = 'customer' then sm.qty_done*sol.price_unit else 0 end) - SUM ( Case when stock_type.usage = 'internal' then cmp.di_cmp*sm.qty_done else -1*cmp.di_cmp*sm.qty_done end) as di_val_marge,
    def _from(self):
        from_str = """
                FROM product_product pr
                LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
                INNER JOIN stock_move_line sm ON sm.product_id = pr.id                
                LEFT JOIN ( SELECT sloc.id,sloc.usage FROM stock_location sloc) stock_type ON stock_type.id = sm.location_dest_id
                LEFT JOIN ( SELECT sloc.id,sloc.usage FROM stock_location sloc) orig_type ON orig_type.id = sm.location_id
                LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout order by di_date desc limit 1) cmp on cmp.di_product_id = sm.product_id
                LEFT JOIN stock_move on stock_move.id = sm.move_id
                LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = stock_move.sale_line_id
                
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY pr.id, sm.id,  sm.date,sm.state, pt.categ_id                   
        """
        return group_by_str
    def _where(self):
        where_str = """
                Where sm.state = 'done'                 
        """
        return where_str

    @api.model_cr
    def init(self):
#         self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as
            %s
            FROM (
                %s %s %s %s
            ) AS sub
        """ % (
                    self._table, self._select(), self._sub_select(), self._from(),self._where(), self._group_by()))
