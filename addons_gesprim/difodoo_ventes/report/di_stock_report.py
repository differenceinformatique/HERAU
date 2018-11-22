# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class DiStockReport(models.Model):
    _name = "di.stock.report"
    _description = "Statistiques stock"
    _auto = False
    _rec_name = 'date'

    date = fields.Datetime(readonly=True)
    product_id = fields.Many2one('product.product', string='Article', readonly=True)
    di_qte_entree = fields.Float(string='Quantité entrée', readonly=True)    
    categ_id = fields.Many2one('product.category', string='Catégorie article', readonly=True)    
    company_id = fields.Many2one('res.company', string='Société', readonly=True)
    di_perte = fields.Float(string='Perte', readonly=True)
     

    _order = 'date desc'

    _depends = {
        'stock.picking': [
            'company_id',
            'date_done',            
            'state', 'picking_type_id',
        ],
        'stock.move': [
            'picking_id', 'product_id',
            'product_qty',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
    }

    def _select(self):
        select_str = """
            SELECT sub.id, sub.date, 
                sub.company_id, sub.state,
                sub.categ_id,
                sub.product_id,
                sub.di_qte_entree as di_qte_entree,            
                sub.di_perte as di_perte
        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT pr.id AS id,
                    sm.date AS date,
                    sm.product_id,                     
                    sm.company_id,
                    sm.state, pt.categ_id,
                    SUM ( Case when stock_type.sign = 1 then sm.product_qty else 0 end) AS di_qte_entree,
                    SUM ( Case when stock_type.sign <> 1 and sm.inventory_id <> 0 then sm.product_qty  else 0 end) AS di_perte

        """
        return select_str

    def _from(self):
        from_str = """
                FROM product_product pr
                LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
                INNER JOIN stock_move sm ON sm.product_id = pr.id                
                LEFT JOIN ( SELECT sloc.id,
                        CASE
                            WHEN sloc.usage::text = ANY (ARRAY['internal'::character varying::text]) THEN 1
                            ELSE '-1'::integer
                        END AS sign
                   FROM stock_location sloc) stock_type ON stock_type.id = sm.location_dest_id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY pr.id, sm.id,  sm.date,                     
                    sm.company_id, sm.location_dest_id, stock_type.sign, sm.state, pt.categ_id                    
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
