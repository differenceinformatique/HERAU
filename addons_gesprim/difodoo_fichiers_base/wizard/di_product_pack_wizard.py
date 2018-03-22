# # -*- coding: utf-8 -*-
# 
# from odoo import api, fields, models, _
# 
# class DiProdPackWiz(models.TranscientModel):
#     _name = "di.prodpack_wiz"
#     _description = 'Generation Conditionnements'
#     
#     cond_ids = fields.One2many("di.conddefaut","wizard_id",string="Conditionnements")
#     
#     @api.multi
#     def create_price_item(self):
#         cond_ids = self.env.context.get('active_ids', [])
#         for p in self.env['di.conddefaut'].sudo().browse(cond_ids):
#             cond_count = 0
#             company_id = self.company_id.id
#             query_args = { 'company_id': company_id}
#             query = """SELECT di_conddefaut.name, di_conddefaut.di_des, di_conddefaut.di_type_cond
#                         FROM di_conddefaut
#                         WHERE di_conddefaut.di_company_id = %(company_id)s  
#                         ORDER BY di_conddefaut.name"""
# 
#             self.env.cr.execute(query, query_args)
#             ids = [(r[0], r[1], r[2]) for r in self.env.cr.fetchall()]
#             
#             for cond_name, cond_des, cond_type in ids:
#                 cond_vals = {'name' : cond_name, 'di_des' : cond_des, 'product_id' : self.id, 'di_type_cond' : cond_type}
# 
#                 self.env['product.packaging'].create(cond_vals)
#                 product_count = product_count + 1
#         
#         view_id = self.env["ir.model.data"].get_object_reference("difodoo", "wiz_create_producpack")
#         self.message = "Création conditionnements"
#         return {"type":"ir.actions.act_window",
#                 "view_mode":"form",
#                 "view_type":"form",
#                 "views":[(view_id[1], "form")],
#                 "res_id":self.id,
#                 "target":"new",
#                 "res_model":"di.ProdPack_wiz"                
#                 }
# 
#     
#     @api.model
#     def default_get(self, fields):        
#         res = super(DiProdPackWiz, self).default_get(fields)
#         res["cond_ids"] = self.env.context["active_ids"]
#         if not self.env.context["active_ids"]:
#             raise ValidationError("No select record")
#         return res           
#         