# # -*- coding: utf-8 -*-
# # Part of Odoo. See LICENSE file for full copyright and licensing details.
# 
# from odoo import tools
# from odoo import fields, models,api
# 
# 
# class AccountInvoiceReport(models.Model):
#     _inherit = "account.invoice.report"
#     
#     di_qte_achat = fields.Float(string="Quantité achat",readonly=True)
#     di_mt_achat = fields.Float(string="Montant achat",readonly=True)
#     di_prix_moyen_achat = fields.Float(string="Prix moyen achat",readonly=True, group_operator="avg")
#     di_qte_vente = fields.Float(string="Quantité vente",readonly=True)
#     di_mt_vente = fields.Float(string="Montant vente",readonly=True)
#     di_prix_moyen_vente = fields.Float(string="Prix moyen vente",readonly=True, group_operator="avg")
#     di_marge_mt = fields.Float(string="Marge en montant",readonly=True)
#     di_marge_prc = fields.Float(string="Marge en pourcentage",readonly=True, group_operator="avg")#,compute='_compute_marge')
#  
# #     @api.depends('di_marge_mt', 'di_mt_achat')
# #     def _compute_amount_total(self):
# #         if self.di_mt_achat == 0.0:
# #             self.di_marge_prc = 100.0
# #         else:
# #             self.di_marge_prc = self.di_marge_mt*100/self.di_mt_achat
#         
#             
#     def _select(self):        
# #         return super(AccountInvoiceReport, self)._select()
#         return super(AccountInvoiceReport, self)._select() + """,sub.di_qte_achat AS di_qte_achat,sub.di_qte_vente AS di_qte_vente,
#         sub.di_mt_achat AS di_mt_achat,
#         sub.di_mt_vente AS di_mt_vente,
#         sub.di_prix_moyen_achat AS di_prix_moyen_achat,
#         sub.di_prix_moyen_vente AS di_prix_moyen_vente
#                                    
#                 """
#             
# #         sub.di_marge_mt AS di_marge_mt,
# #         sub.di_marge_prc AS di_marge_prc 
#                 
#  
#     def _sub_select(self):        
# #         return super(AccountInvoiceReport, self)._sub_select()
#         return super(AccountInvoiceReport, self)._sub_select() + """,
#         SUM (CASE WHEN invoice_type.sign  <> 1 THEN ((ail.quantity) / u.factor * u2.factor)ELSE 0 END) AS di_qte_achat,        
#         SUM (CASE WHEN invoice_type.sign  <> 1 THEN (ail.price_subtotal_signed) ELSE 0 END) AS di_mt_achat,
#                                              
#         SUM (CASE WHEN invoice_type.sign  = 1 THEN ((ail.quantity) / u.factor * u2.factor)ELSE 0 END) AS di_qte_vente,
#         
#         SUM (CASE WHEN invoice_type.sign  = 1 THEN (ail.price_subtotal_signed) ELSE 0 END) AS di_mt_vente,
#         
#         SUM(ABS(case when invoice_type.sign  = 1 then ail.price_subtotal_signed else 0 end)) / CASE
#                             WHEN SUM(ail.quantity / u.factor * u2.factor) <> 0::numeric
#                                THEN SUM(ail.quantity / u.factor * u2.factor)
#                                ELSE 1::numeric
#                             END AS di_prix_moyen_vente, 
#                             
#         SUM(ABS(case when invoice_type.sign  <> 1 then ail.price_subtotal_signed else 0 end)) / CASE
#                             WHEN SUM(ail.quantity / u.factor * u2.factor) <> 0::numeric
#                                THEN SUM(ail.quantity / u.factor * u2.factor)
#                                ELSE 1::numeric
#                             END AS di_prix_moyen_achat   
#             
#         """
# #         SUM (case when invoice_type.sign  = 1 THEN ((ABS(ail.price_subtotal_signed)) / (CASE
# #                             WHEN SUM(ail.quantity / u.factor * u2.factor) <> 0::numeric
# #                                THEN SUM(ail.quantity / u.factor * u2.factor)
# #                                ELSE 1::numeric
# #                             END)) else 0 end)  AS di_prix_moyen_achat,
# #                             
# #         SUM(ABS(ail.price_subtotal_signed)) / CASE
# #                             WHEN SUM(ail.quantity / u.factor * u2.factor) <> 0::numeric
# #                                THEN SUM(ail.quantity / u.factor * u2.factor)
# #                                ELSE 1::numeric
# #                             END AS di_prix_moyen_vente     
# #            sub.di_mt_vente-sub.di_mt_achat as di_marge_mt,
# #         
# #         case when sub.di_mt_achat <> 0 then ((sub.di_mt_vente-sub.di_mt_achat)*100)/sub.di_mt_achat else 100 end as di_marge_prc                    
# # 
# #     def _from(self):
# #         #return super(HubiAccountInvoiceReport, self)._from()
# #         return super(HubiAccountInvoiceReport, self)._from() + """
# #                     LEFT JOIN hubi_family hfc ON (pt.caliber_id = hfc.id)
# #                     LEFT JOIN hubi_family hfp ON (pt.packaging_id = hfp.id) 
# #                     """
# #                     #LEFT JOIN res_partner_res_partner_category_rel cat ON  ai.commercial_partner_id =cat.partner_id 
# #                     #LEFT JOIN res_partner_category rpc ON (cat.category_id = rpc.id  AND rpc.parent_id is not null)
# #                     
# #     def _group_by(self):
# #         #return super(HubiAccountInvoiceReport, self)._group_by()
# #         return super(HubiAccountInvoiceReport, self)._group_by() + ", ai.carrier_id, hfc.name, hfp.name"
