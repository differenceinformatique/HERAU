# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class DiStockReport(models.Model):
    _name = "di.stock.report"
    _description = "Statistiques stock"
    _auto = False
    _rec_name = 'date'

    date = fields.Date(readonly=True)
    product_id = fields.Many2one('product.product', string='Article', readonly=True)
    di_qte_entree = fields.Float(string='Quantité entrée', readonly=True)    
    categ_id = fields.Many2one('product.category', string='Catégorie article', readonly=True)    
    company_id = fields.Many2one('res.company', string='Société', readonly=True)
    di_perte = fields.Float(string='Perte', readonly=True)
    
#     res.picking_type_id.code=='incoming':
    type = fields.Selection([
        ('incoming', 'Entrée'),
        ('outgoing', 'Sortie'),       
        ], readonly=True)
    
 
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('waiting', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('assigned', 'Prêt'),
        ('done', 'Fait'),
        ('cancel', 'Annulé'),
    ], string='Status', readonly=True)   

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
                sub.di_qte_entree as di_qte_entree,            
                sub.di_perte as di_perte
        """
#         sub.di_prix_achat as di_prix_achat, sub.di_prix_vente as di_prix_vente,
#         case when di_mt_achat <> 0 then sub.di_marge_mt * 100 / sub.di_mt_achat else 100 end as di_marge_prc
#         sub.di_marge_mt as di_marge_mt, sub.di_marge_prc as di_marge_prc
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT pr.id AS id,
                    sp.date_done AS date,                    
                    sp.company_id,
                    sp.picking_type_id, sp.state, pt.categ_id,
                    SUM ( Case when stock_type.sign = 1 then sm.product_qty else 0 end) AS di_qte_entree,
                    SUM ( Case when stock_type.sign <> 1 and sm.inventory_id is not null and sm.inventory_id <> 0 then sm.product_qty  else 0 end) AS di_perte

        """
#         SUM (ABS(Case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end)) / CASE WHEN SUM(ail.quantity) <> 0::numeric THEN SUM(ail.quantity) ELSE 1::numeric END AS di_prix_achat,
#                     SUM (ABS(Case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end)) / CASE WHEN SUM(ail.quantity) <> 0::numeric THEN SUM(ail.quantity) ELSE 1::numeric END AS di_prix_vente,
#         ( SUM (case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end ) - SUM (case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end ) )  as di_marge_mt
#         ( case when SUM ( Case when invoice_type.sign <> 1 then ail.quantity else 0 end) <> 0 then (( SUM (case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end ) - SUM (case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end ) ) * 100 /  SUM ( Case when invoice_type.sign <> 1 then ail.quantity else 0 end)) else ( SUM (case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end ) - SUM (case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end ) ) * 100 end  ) as di_marge_prc
#         SUM ((ABS(Case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end)) / CASE WHEN SUM(ail.quantity) <> 0::numeric THEN SUM(ail.quantity) ELSE 1::numeric END) AS di_prix_achat,
#                     SUM ((ABS(Case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end)) / CASE WHEN SUM(ail.quantity) <> 0::numeric THEN SUM(ail.quantity) ELSE 1::numeric END) AS di_prix_vente,
        return select_str

    def _from(self):
        from_str = """
                FROM product_product pr
                LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
                INNER JOIN stock_move sm ON sm.product_id = pr.id
                LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                LEFT JOIN ( SELECT spt.id,
                        CASE
                            WHEN spt.code::text = ANY (ARRAY['incoming'::character varying::text]) THEN 1
                            ELSE '-1'::integer
                        END AS sign
                   FROM stock_picking_type spt) stock_type ON stock_type.id = sp.picking_type_id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY pr.id, sm.id,  sp.date_done, sp.id,                    
                    sp.company_id, sp.picking_type_id, stock_type.sign, sp.state, pt.categ_id                    
        """
        return group_by_str
    def _where(self):
        where_str = """
                Where sm.state = 'done'                 
        """
        return where_str

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as
            %s
            FROM (
                %s %s %s %s
            ) AS sub
        """ % (
                    self._table, self._select(), self._sub_select(), self._from(),self._where(), self._group_by()))
