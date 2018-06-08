# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class DiInvoiceReport(models.Model):
    _name = "di.invoice.report"
    _description = "Invoices Statistics"
    _auto = False
    _rec_name = 'date'

    date = fields.Date(readonly=True)
    product_id = fields.Many2one('product.product', string='Article', readonly=True)
    di_qte_achat = fields.Float(string='Quantité achat', readonly=True)
    di_qte_vente = fields.Float(string='Quantité vente', readonly=True)
    categ_id = fields.Many2one('product.category', string='Catégorie article', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Tiers', readonly=True)    
    company_id = fields.Many2one('res.company', string='Société', readonly=True)
    di_mt_achat = fields.Float(string='Montant achat', readonly=True)
    di_mt_vente = fields.Float(string='Montant vente', readonly=True)
#     di_prix_achat = fields.Float(string='Prix achat', readonly=True, group_operator="avg")
#     di_prix_vente = fields.Float(string='Prix vente', readonly=True, group_operator="avg")
    di_marge_mt = fields.Float(string='Marge en montant', readonly=True, group_operator="avg")
#     di_marge_prc = fields.Float(string='Marge en pourcentage', readonly=True, group_operator="avg")

    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
        ], readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True)   

    _order = 'date desc'

    _depends = {
        'account.invoice': [
            'company_id',
            'date_invoice',
            'partner_id',
            'state', 'type',
        ],
        'account.invoice.line': [
            'invoice_id', 'price_subtotal', 'product_id',
            'quantity',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
    }

    def _select(self):
        select_str = """
            SELECT sub.id, sub.date, sub.product_id, sub.partner_id,
                sub.company_id,  sub.type, sub.state,
                sub.categ_id,
                sub.di_qte_achat as di_qte_achat,
                sub.di_qte_vente as di_qte_vente,sub.di_mt_achat as di_mt_achat, sub.di_mt_vente as di_mt_vente,                
                sub.di_marge_mt as di_marge_mt                
        """
#         sub.di_prix_achat as di_prix_achat, sub.di_prix_vente as di_prix_vente,
#         case when di_mt_achat <> 0 then sub.di_marge_mt * 100 / sub.di_mt_achat else 100 end as di_marge_prc
#         sub.di_marge_mt as di_marge_mt, sub.di_marge_prc as di_marge_prc
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT ail.id AS id,
                    ai.date_invoice AS date,
                    ail.product_id, ai.partner_id,
                    ai.company_id,
                    ai.type, ai.state, pt.categ_id,
                    SUM ( Case when invoice_type.sign <> 1 then ail.quantity else 0 end) AS di_qte_achat,
                    SUM ( Case when invoice_type.sign = 1 then ail.quantity  else 0 end) AS di_qte_vente,
                    SUM (case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end ) AS di_mt_achat,
                    SUM (case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end ) AS di_mt_vente,                                        
                    (SUM (case when invoice_type.sign = 1 then ail.price_subtotal_signed else 0 end ) - SUM (case when invoice_type.sign <> 1 then ail.price_subtotal_signed else 0 end )) as di_marge_mt
                    

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
                FROM account_invoice_line ail
                JOIN account_invoice ai ON ai.id = ail.invoice_id                
                LEFT JOIN product_product pr ON pr.id = ail.product_id
                LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
                JOIN (
                    -- Temporary table to decide if the qty should be added or retrieved (Invoice vs Credit Note)
                    SELECT id,(CASE
                         WHEN ai.type::text = ANY (ARRAY['in_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN -1
                            ELSE 1
                        END) AS sign
                    FROM account_invoice ai
                ) AS invoice_type ON invoice_type.id = ai.id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY ail.id, ail.product_id,  ai.date_invoice, ai.id,
                    ai.partner_id,
                    ai.company_id, ai.type, invoice_type.sign, ai.state, pt.categ_id                    
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as
            %s
            FROM (
                %s %s %s
            ) AS sub
        """ % (
                    self._table, self._select(), self._sub_select(), self._from(), self._group_by()))
