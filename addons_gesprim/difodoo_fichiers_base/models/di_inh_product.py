# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT
from suds import null
from odoo.tools.float_utils import float_round
import time

class ProductTemplate(models.Model):
    _inherit = "product.template"
      
    di_lavage = fields.Boolean(string="Lavage", default=False)
    di_prixmin = fields.Float(string="Prix minimum")
    di_prixmax = fields.Float(string="Prix maximum")
    di_des = fields.Char(string="Désignation") # ????
    
    di_categorie_id = fields.Many2one("di.categorie",string="Catégorie")    
    di_categorie_di_des = fields.Char(related='di_categorie_id.di_des')#, store='False')
    
    di_origine_id = fields.Many2one("di.origine",string="Origine")
    di_origine_di_des = fields.Char(related='di_origine_id.di_des')#, store='False')
    
    di_marque_id = fields.Many2one("di.marque",string="Marque")
    di_marque_di_des = fields.Char(related='di_marque_id.di_des')#, store='False')
    
    di_calibre_id = fields.Many2one("di.calibre",string="Calibre")
    di_calibre_di_des = fields.Char(related='di_calibre_id.di_des')#, store='False')
    
#     di_station_id = fields.Many2one("di.station",string="Station")
#     di_station_di_des = fields.Char(related='di_station_id.di_des')#, store='False')
    di_station_id = fields.Many2one("stock.location",string="Station")
    di_station_di_des = fields.Char(related='di_station_id.name')#, store='False')
    
    di_producteur_id = fields.Many2one("res.partner",string="Producteur")
    di_producteur_nom = fields.Char(related='di_producteur_id.display_name')#, store='False')  

    di_un_saisie        = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Type unité saisie",
                                           help="Si vide, saisie dans la colonne quantité commandée")
    di_type_palette_id     = fields.Many2one('product.packaging', string='Palette par défaut', copy=False)   
    di_type_colis_id       = fields.Many2one('product.packaging', string='Colis par défaut', copy=False)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Type unité prix",
                                       help="Si vide, prix unitaire en unité de mesure")
    
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
    di_param_seq_art = fields.Boolean(string='Codification auto.',compute='_di_compute_seq_art',store=False)
    
#     def di_action_afficher_cond(self):
#         product=self.env['product.product'].search([('product_tmpl_id','=',self.id)])
#         return {
#             "type": "ir.actions.act_window",
#             "res_model": "product.packaging",
#             "views": [[False, "tree"], [False, "form"]],
#             "domain": (["product_id", "=", product.id]), 
#             "name": "Conditionnements",
#         }

    def action_view_stock_move_lines(self):
        self.ensure_one()
        action = self.env.ref('difodoo_ventes.di_stock_move_line_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action

    def action_open_quants(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1,'search_default_positive': 1,'search_default_negative': 1}
        return action
         
    def di_action_afficher_cond(self):
        self.ensure_one()
        product=self.env['product.product'].search([('product_tmpl_id','=',self.id)])
        action = self.env.ref('difodoo_fichiers_base.di_action_product_packaging').read()[0]
        action['domain'] = [('product_id', '=', product.id)]
        action['context'] = [('default_product_id', '=', product.id)]
        return action
    
    @api.multi
    @api.depends('di_un_saisie', 'di_un_prix')
    def _di_compute_spe_saisissable(self):
        for prod in self:
            if prod.di_un_prix is not False or prod.di_un_saisie is not False : # ????
                prod.di_spe_saisissable =True
            else:
                prod.di_spe_saisissable=False
            
    @api.multi
    @api.depends('company_id')
    def _di_compute_seq_art(self):
        for prod in self:
            if prod.company_id and prod.company_id.di_param_id:
                prod.di_param_seq_art = prod.company_id.di_param_id.di_seq_art
            else:
                prod.di_param_seq_art = False          
    
#     @api.multi
#     def write(self, vals):
#         # TODO faire le parcours dans self de tous les enregs                             
#         for key in vals.items():  # vals est un dictionnaire qui contient les champs modifiés, on va lire les différents enregistrements                      
#             if key[0] == "di_un_prix":  # si on a modifié sale_line_id
#                 if vals['di_un_prix'] == False:
#                     vals['di_un_saisie']=False
#                     break
#             elif key[0] == "di_un_saisie":
#                 if vals['di_un_saisie'] == False:
#                     vals['di_un_prix']=False 
#                     break                                    
#         res = super(ProductTemplate, self).write(vals)
#         return res   
#     
#     @api.multi
#     def write(self, vals):
#         if 'di_un_prix' in vals and not vals['di_un_prix'] and vals.get('di_un_saisie'):
#             vals['di_un_saisie'] = False        
#         if 'di_un_saisie' in vals and not vals.get('di_un_saisie') and vals.get('di_un_prix'):
#             vals['di_un_prix'] = False                                    
#         return super(ProductTemplate, self).write(vals)

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for product in self:
            if product.di_un_prix and not product.di_un_saisie:
                product.di_un_prix = False
            if product.di_un_saisie and not product.di_un_prix:
                product.di_un_saisie = False
        return res
    
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('default_code', '=like', u"{}%_Copie".format(self.default_code))])
        if not copied_count:
            new_name = u"{}_Copie".format(self.default_code)            
        else:
            new_name = u"{}_Copie({})".format(self.default_code, copied_count)

        default['default_code'] = new_name
        return super(ProductTemplate, self).copy(default)
    
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    di_flg_avec_ventes = fields.Boolean("Avec ventes non clôturées", default=False)
    
    default_code = fields.Char('Internal Reference', index=True)
        
    di_reftiers_ids = fields.Many2many('res.partner', 'di_referencement_article_tiers', 'product_id','partner_id', string='Référencement article')
    di_tarifs_ids = fields.One2many('di.tarifs', 'id',string='Tarifs de l\'article')
    
    
    di_prix_vente_moyen = fields.Float(compute='_di_compute_resserre_values', string='Prix de vente moyen')
    di_prix_achat_moyen = fields.Float(compute='_di_compute_resserre_values', string="Prix d'achat moyen")
    
    di_val_ven = fields.Float(string='Valeur vente', compute='_di_compute_resserre_values')
    di_val_stock = fields.Float(string='Valeur stock', compute='_di_compute_resserre_values')
    di_val_marge = fields.Float(string='Valeur marge', compute='_di_compute_resserre_values')
    di_marge_prc = fields.Float(compute='_di_compute_resserre_values', string='Marge %')
    
    di_col_stock = fields.Float(string='Colis en stock', compute='_di_compute_resserre_values')
    di_qte_stock = fields.Float(string='Quantité en stock', compute='_di_compute_resserre_values')

    di_poib_stock = fields.Float(string='Poids brut en stock', compute='_di_compute_resserre_values')
    di_poin_stock = fields.Float(string='Poids net en stock', compute='_di_compute_resserre_values')
    
    di_col_ven = fields.Float(string='Colis vendus', compute='_di_compute_resserre_values')
    di_qte_ven = fields.Float(string='Quantité vendue', compute='_di_compute_resserre_values')
    di_poib_ven = fields.Float(string='Poids brut vendu', compute='_di_compute_resserre_values')
    di_poin_ven = fields.Float(string='Poids net vendu', compute='_di_compute_resserre_values')  
    
    di_col_ach = fields.Float(string='Colis achetés', compute='_di_compute_resserre_values')
    di_qte_ach = fields.Float(string='Quantité achetée', compute='_di_compute_resserre_values')
    di_poib_ach = fields.Float(string='Poids brut acheté', compute='_di_compute_resserre_values')
    di_poin_ach = fields.Float(string='Poids net acheté', compute='_di_compute_resserre_values')  
    
    di_col_regul_entree = fields.Float(string='Colis régul.entrée', compute='_di_compute_resserre_values')
    di_qte_regul_entree = fields.Float(string='Quantité régul. entrée', compute='_di_compute_resserre_values')
    di_poib_reg_ent = fields.Float(string='Poids brut régul. entrée', compute='_di_compute_resserre_values')
    di_poin_reg_ent = fields.Float(string='Poids net régul. entrée', compute='_di_compute_resserre_values')
    
      
    di_col_regul_sortie = fields.Float(string='Colis régul. sortie', compute='_di_compute_resserre_values')
    di_qte_regul_sortie = fields.Float(string='Quantité régul. sortie', compute='_di_compute_resserre_values')
    di_poib_reg_sort = fields.Float(string='Poids brut régul. sortie', compute='_di_compute_resserre_values')
    di_poin_reg_sort = fields.Float(string='Poids net régul. sortie', compute='_di_compute_resserre_values')
    di_val_regul_sortie = fields.Float(string='Valeur régul. sortie', compute='_di_compute_resserre_values')
    di_val_marge_ap_regul_sortie = fields.Float(string='Valeur marge après régul. sortie', compute='_di_compute_resserre_values')
    
#     di_avec_stock = fields.Boolean("Avec stock", default=False, compute='_di_compute_avec_stock', search="_di_search_avec_stock")
#     
#     def _di_compute_avec_stock(self):
#         for art in self:              
#             if (art.di_col_stock and art.di_col_stock != 0.0) or (art.di_qte_stock and art.di_qte_stock != 0.0) or (art.di_poib_stock and art.di_poib_stock != 0.0) or (art.di_poin_stock and art.di_poin_stock != 0.0):
#                 art.di_avec_stock = True
#             else:
#                 art.di_avec_stock = False
#     
#     def _di_search_avec_stock(self, operator, value):        
#                     
#         product_ids = []
#         prods = self.env['product.product'].search([])
#         for prod in prods:                         
#             (nbcol, nbpal, nbpiece, poids, qte_std, poib) = self.env['stock.move.line'].di_qte_spe_en_stock(prod,False,False,'internal')
#             if nbcol != 0.0 or nbpal != 0.0 or nbpiece != 0.0 or poids != 0.0 or qte_std != 0.0 or poib != 0.0 : 
#                 product_ids.append(prod.id)
#         return [('id', 'in', product_ids)]        
                
    
#     def _qte_stock_search(self, operator, value):
#         domain = [('di_qte_stock', operator, value)]
#         product_ids = self.env['product.product'].search(domain)
#         return [('product_ids', 'in', product_ids.ids)]   
#     
#     @api.multi
#     def _qte_stock_search(self, operator, value):
#         recs = self.search([]).filtered(lambda x : x.di_qte_stock >= 0.0 )    
#         if recs:
#             return [('id', 'in', [x.id for x in recs])]
#         
#     def _search_qte_stock(self, operator, value):       
#         product_ids = self.env['product.product']._get_ids_avec_stock()
#         return [('id','in', product_ids)]    
#     
#     def _get_ids_avec_stock(self):
#             

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         """
#             Inherit read_group to calculate the sum of the non-stored fields, as it is not automatically done anymore through the XML.
#         """
#         res = super(ProductProduct, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
#         fields_list = ['di_prix_vente_moyen', 'di_prix_achat_moyen', 'di_val_stock', 'di_val_ven', 'di_val_marge',
#                        'di_marge_prc', 'di_col_stock', 'di_qte_stock', 'di_poib_stock', 'di_poin_stock', 'di_col_ven',
#                        'di_qte_ven', 'di_poib_ven', 'di_poin_ven','di_col_ach','di_qte_ach', 'di_poib_ach', 'di_poin_ach',
#                        'di_col_regul_entree', 'di_qte_regul_entree', 'di_poib_reg_ent', 'di_poin_reg_ent',
#                        'di_col_regul_sortie', 'di_qte_regul_sortie', 'di_poib_reg_sort', 'di_poin_reg_sort','di_val_regul_sortie','di_val_marge_ap_regul_sortie']
#             
#         if any(x in fields for x in fields_list):
#             # Calculate first for every product in which line it needs to be applied
#             re_ind = 0
#             prod_re = {}
#             tot_products = self.browse([])
#             for re in res:
#                 if re.get('__domain'):
#                     products = self.search(re['__domain'])
#                     tot_products |= products
#                     for prod in products:
#                         prod_re[prod.id] = re_ind
#                 re_ind += 1
#             res_val = tot_products._di_compute_resserre_values(field_names=[x for x in fields if fields in fields_list])
#             for key in res_val:
#                 for l in res_val[key]:
#                     re = res[prod_re[key]]
#                     if re.get(l):
#                         re[l] += res_val[key][l]
#                     else:
#                         re[l] = res_val[key][l]
#         return res

#     def _di_compute_resserre_values(self, field_names=None):

    def di_get_qte_cde(self):
        qtecde=0.0
        lines = self.env['sale.order.line'].search(['&',('state', 'in', ('draft','sent','sale')),('invoice_status','=','no'),('product_id','=',self.id)]).filtered(lambda s: s.order_id.invoice_status == 'no')
        for line in lines:
            qtecde = qtecde+line.product_uom_qty
        return qtecde
        
    def action_view_stock_move_lines(self):
        self.ensure_one()
        action = self.env.ref('difodoo_ventes.di_stock_move_line_action').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action
    
    
    def _di_compute_resserre_values(self):  
        di_date_to = self.env.context.get('di_date_to', time.strftime('%Y-%m-%d'))
        affven = self.env.context.get('di_aff_ven')
        affperte = self.env.context.get('di_aff_pertes')
        listecpt = self.env.context.get('di_liste_comptage')
#             di_date_to  =  val.di_date_to.strftime('%Y-%m-%d')      
        di_date_to = di_date_to + ' 23:59:59'   
        for art in self:                    
                        
            if not listecpt:
                if affven:
                    if affperte:
                        sqlstr = """
                                select
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,                                
                                    SUM ( Case when sml.di_usage_loc_dest = 'internal' then cmp.di_cmp*sml.qty_done else -1*cmp.di_cmp*sml.qty_done end) AS di_val_stock                                                            
                                from stock_move_line sml                                
                                LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                                (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)                
                                LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id                              
                                LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                                where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false
                                """             
                        self.env.cr.execute(sqlstr, (art.id, di_date_to))
                        result = self.env.cr.fetchall()[0]
                        art.di_col_stock = result[0] and result[0] or 0.0
                        art.di_qte_stock = result[1] and result[1] or 0.0
                        art.di_poib_stock = result[2] and result[2] or 0.0
                        art.di_poin_stock = result[3] and result[3] or 0.0
                        art.di_val_stock = result[4] and result[4] or 0.0
                        art.di_col_ven =  0.0
                        art.di_qte_ven =  0.0
                        art.di_poib_ven =  0.0
                        art.di_poin_ven =  0.0
                        art.di_val_ven = 0.0
                        art.di_col_regul_sortie =0.0
                        art.di_qte_regul_sortie = 0.0
                        art.di_poib_reg_sort = 0.0
                        art.di_poin_reg_sort = 0.0
                    else:
                        sqlstr = """
                            select
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                                
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then cmp.di_cmp*sml.qty_done else -1*cmp.di_cmp*sml.qty_done end) AS di_val_stock,
                                                            
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.di_nb_colis else 0 end) AS di_col_regul_sortie,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.qty_done else 0 end) AS di_qte_regul_sortie,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.di_poib else 0 end) AS di_poib_reg_sort,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.di_poin else 0 end) AS di_poin_reg_sort                                  
                                                                  
                            from stock_move_line sml                                
                            LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                            (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)                
                            LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id                          
                            LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                            where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false
                            """
        
                        self.env.cr.execute(sqlstr, (art.id, di_date_to))
                        result = self.env.cr.fetchall()[0]
                        art.di_col_stock = result[0] and result[0] or 0.0
                        art.di_qte_stock = result[1] and result[1] or 0.0
                        art.di_poib_stock = result[2] and result[2] or 0.0
                        art.di_poin_stock = result[3] and result[3] or 0.0
                        art.di_val_stock = result[4] and result[4] or 0.0
                        art.di_col_ven = 0.0
                        art.di_qte_ven =0.0
                        art.di_poib_ven =0.0
                        art.di_poin_ven = 0.0
                        art.di_val_ven = 0.0
                        art.di_col_regul_sortie = result[5] and result[5] or 0.0
                        art.di_qte_regul_sortie = result[6] and result[6] or 0.0
                        art.di_poib_reg_sort = result[7] and result[7] or 0.0
                        art.di_poin_reg_sort = result[8] and result[8] or 0.0
                        
                else:
                    if affperte:
                        sqlstr = """
                            select
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                                
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then cmp.di_cmp*sml.qty_done else -1*cmp.di_cmp*sml.qty_done end) AS di_val_stock,
                                
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.di_nb_colis when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.di_nb_colis  else   0 end) AS di_col_ven,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.qty_done when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.qty_done else 0 end) AS di_qte_ven,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.di_poib when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1* sml.di_poib else 0 end) AS di_poib_ven,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.di_poin when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.di_poin else 0 end) AS di_poin_ven,
                                
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.qty_done*sol.price_unit when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.qty_done*sol.price_unit else 0 end) AS di_val_ven                                                                                                                                            
                               
                            from stock_move_line sml                                
                            LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                            (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)                
                            LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id  
                            LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id     
                            LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                            where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false
                            """
          
                       
                        self.env.cr.execute(sqlstr, (art.id, di_date_to))
                        result = self.env.cr.fetchall()[0]
                        art.di_col_stock = result[0] and result[0] or 0.0
                        art.di_qte_stock = result[1] and result[1] or 0.0
                        art.di_poib_stock = result[2] and result[2] or 0.0
                        art.di_poin_stock = result[3] and result[3] or 0.0
                        art.di_val_stock = result[4] and result[4] or 0.0
                        art.di_col_ven = result[5] and result[5] or 0.0
                        art.di_qte_ven = result[6] and result[6] or 0.0
                        art.di_poib_ven = result[7] and result[7] or 0.0
                        art.di_poin_ven = result[8] and result[8] or 0.0
                        art.di_val_ven = result[9] and result[9] or 0.0
                        art.di_col_regul_sortie = 0.0
                        art.di_qte_regul_sortie = 0.0
                        art.di_poib_reg_sort = 0.0
                        art.di_poin_reg_sort = 0.0
                    else:
               
                        sqlstr = """
                            select
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else -1*sml.di_nb_colis end) AS di_col_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.qty_done else -1*sml.qty_done end) AS di_qte_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poib else -1*sml.di_poib end) AS di_poib_stock,
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then sml.di_poin else -1*sml.di_poin end) AS di_poin_stock,
                                
                                SUM ( Case when sml.di_usage_loc_dest = 'internal' then cmp.di_cmp*sml.qty_done else -1*cmp.di_cmp*sml.qty_done end) AS di_val_stock,
                                
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.di_nb_colis when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.di_nb_colis  else   0 end) AS di_col_ven,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.qty_done when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.qty_done else 0 end) AS di_qte_ven,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.di_poib when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1* sml.di_poib else 0 end) AS di_poib_ven,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.di_poin when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.di_poin else 0 end) AS di_poin_ven,
                                
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'customer' and sml.di_flg_cloture is not true then sml.qty_done*sol.price_unit when sml.di_usage_loc = 'customer' and sml.di_usage_loc_dest = 'internal' and sml.di_flg_cloture is not true then -1*sml.qty_done*sol.price_unit else 0 end) AS di_val_ven,                                                                                                                                            
                                
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.di_nb_colis else 0 end) AS di_col_regul_sortie,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.qty_done else 0 end) AS di_qte_regul_sortie,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.di_poib else 0 end) AS di_poib_reg_sort,
                                SUM ( Case when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest <> 'customer' and sml.di_flg_cloture is not true and sml.di_perte is true then sml.di_poin else 0 end) AS di_poin_reg_sort                                  
                                                                  
                            from stock_move_line sml                                
                            LEFT JOIN (select di_cout.di_cmp,di_cout.id,di_cout.di_product_id from di_cout ) cmp on cmp.id = 
                            (select id from di_cout where di_product_id = sml.product_id order by di_date desc limit 1)                
                            LEFT JOIN (select sm.sale_line_id, sm.id  from stock_move sm) sm on sm.id = sml.move_id  
                            LEFT JOIN (select sol.price_unit, sol.id from sale_order_line sol) sol on sol.id = sm.sale_line_id     
                            LEFT JOIN stock_production_lot lot on lot.id = sml.lot_id            
                            where sml.product_id = %s and sml.state ='done'  and sml.date <=%s and lot.di_fini is false
                            """
                            
            #                 SUM ( Case when sml.di_usage_loc = 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'supplier' then -1*sml.di_nb_colis else 0 end) AS di_col_ach,
            #                     SUM ( Case when sml.di_usage_loc = 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.qty_done when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'supplier' then -1*sml.qty_done  else 0 end) AS di_qte_ach,
            #                     SUM ( Case when sml.di_usage_loc = 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.di_poib when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'supplier' then -1*sml.di_poib  else 0 end) AS di_poib_ach,
            #                     SUM ( Case when sml.di_usage_loc = 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.di_poin when sml.di_usage_loc = 'internal' and  sml.di_usage_loc_dest = 'supplier' then -1*sml.di_poin  else 0 end) AS di_poin_ach,
            # SUM ( Case when sml.di_usage_loc <> 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.di_nb_colis else 0 end) AS di_col_regul_entree,
            #                     SUM ( Case when sml.di_usage_loc <> 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.qty_done else 0 end) AS di_qte_regul_entree,
            #                     SUM ( Case when sml.di_usage_loc <> 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.di_poib else 0 end) AS di_poib_reg_ent,
            #                     SUM ( Case when sml.di_usage_loc <> 'supplier' and  sml.di_usage_loc_dest = 'internal' then sml.di_poin else 0 end) AS di_poin_reg_ent,
            #             
                        self.env.cr.execute(sqlstr, (art.id, di_date_to))
                        result = self.env.cr.fetchall()[0]
                        art.di_col_stock = result[0] and result[0] or 0.0
                        art.di_qte_stock = result[1] and result[1] or 0.0
                        art.di_poib_stock = result[2] and result[2] or 0.0
                        art.di_poin_stock = result[3] and result[3] or 0.0
                        art.di_val_stock = result[4] and result[4] or 0.0
                        art.di_col_ven = result[5] and result[5] or 0.0
                        art.di_qte_ven = result[6] and result[6] or 0.0
                        art.di_poib_ven = result[7] and result[7] or 0.0
                        art.di_poin_ven = result[8] and result[8] or 0.0
                        art.di_val_ven = result[9] and result[9] or 0.0
                        art.di_col_regul_sortie = result[10] and result[10] or 0.0
                        art.di_qte_regul_sortie = result[11] and result[11] or 0.0
                        art.di_poib_reg_sort = result[12] and result[12] or 0.0
                        art.di_poin_reg_sort = result[13] and result[13] or 0.0
            #             art.di_col_ach = result[10] and result[10] or 0.0
            #             art.di_qte_ach = result[11] and result[11] or 0.0
            #             art.di_poib_ach = result[12] and result[12] or 0.0
            #             art.di_poin_ach = result[13] and result[13] or 0.0
            #             art.di_col_regul_entree = result[14] and result[14] or 0.0
            #             art.di_qte_regul_entree = result[15] and result[15] or 0.0
            #             art.di_poib_reg_ent = result[16] and result[16] or 0.0
            #             art.di_poin_reg_ent = result[17] and result[17] or 0.0
            #             art.di_col_regul_sortie = result[18] and result[18] or 0.0
            #             art.di_qte_regul_sortie = result[19] and result[19] or 0.0
            #             art.di_poib_reg_sort = result[20] and result[20] or 0.0
            #             art.di_poin_reg_sort = result[21] and result[21] or 0.0
                
                
            else:
                art.di_col_stock = 0.0
                art.di_qte_stock = 0.0
                art.di_poib_stock = 0.0
                art.di_poin_stock = 0.0
                art.di_val_stock = 0.0
                art.di_col_ven = 0.0
                art.di_qte_ven = 0.0
                art.di_poib_ven = 0.0
                art.di_poin_ven = 0.0
                art.di_val_ven = 0.0
                art.di_col_regul_sortie = 0.0
                art.di_qte_regul_sortie = 0.0
                art.di_poib_reg_sort = 0.0
                art.di_poin_reg_sort = 0.0
            
            if art.di_qte_stock != 0.0:
                art.di_prix_achat_moyen = art.di_val_stock / art.di_qte_stock
            else:
                art.di_prix_achat_moyen = art.product_tmpl_id.standard_price
                
            art.di_val_marge = art.di_val_ven - (art.di_qte_ven*art.di_prix_achat_moyen)
                
            if art.di_qte_ven != 0.0:
                art.di_prix_vente_moyen = art.di_val_ven / art.di_qte_ven
            else:
                art.di_prix_vente_moyen =0.0
                
            if art.di_val_ven != 0.0:    
                art.di_marge_prc = art.di_val_marge * 100 / art.di_val_ven
            else:
                art.di_marge_prc = 0.0
                
            art.di_val_regul_sortie =  art.di_prix_achat_moyen *  art.di_qte_regul_sortie
            art.di_val_marge_ap_regul_sortie =  art.di_val_marge -  art.di_val_regul_sortie
          
                
    
    
    def di_get_dernier_cmp(self,date):
        couts=self.env['di.cout'].search([('di_product_id', '=', self.id)]).filtered(lambda c: c.di_date<=date).sorted(key=lambda k: k.di_date,reverse=True)
        dernier_cmp = 0.0
        for cout in couts:
            dernier_cmp = cout.di_cmp
            break
        if dernier_cmp == 0.0 :
            achats=self.env['purchase.order.line'].search(['&',('product_id','=',self.id),('price_unit','>',0.0)]).filtered(lambda a: a.order_id.date_order.date()<=date).sorted(key=lambda k: k.order_id.date_order,reverse=True)
            for achat in achats:
                if achat.product_uom_qty != 0.0:
                    dernier_cmp = round((achat.price_subtotal / achat.product_uom_qty),2)
#                 if achat.di_un_prix =="PIECE":
#                     if achat.di_nb_pieces != 0.0:
#                         dernier_cmp = achat.price_subtotal / achat.di_nb_pieces
#                     else:
#                         dernier_cmp = achat.price_unit
#                 elif achat.di_un_prix == "COLIS":
#                     if achat.di_nb_colis != 0.0:
#                         dernier_cmp = achat.price_subtotal / achat.di_nb_colis
#                     else:
#                         dernier_cmp = achat.price_unit
#                 elif achat.di_un_prix == "PALETTE":
#                     if achat.di_nb_palette != 0.0:
#                         dernier_cmp = achat.price_subtotal / achat.di_nb_palette
#                     else:
#                         dernier_cmp = achat.price_unit
#                 elif achat.di_un_prix == "KG":
#                     if achat.di_poin != 0.0:
#                         dernier_cmp = achat.price_subtotal / achat.di_poin
#                     else:
#                         dernier_cmp = achat.price_unit
#                 elif achat.di_un_prix == False or achat.di_un_prix == '':                    
#                     dernier_cmp = achat.price_unit
                break
        if dernier_cmp == 0.0 :
            dernier_cmp = self.standard_price
        
    
        return dernier_cmp
    
                           
    
#     def di_action_afficher_cond(self):
#         self.ensure_one()        
#         action = self.env.ref('difodoo_fichiers_base.di_action_product_packaging').read()[0]
#         action['domain'] = [('product_id', '=', self.id)]
#         action['context'] = [('default_product_id', '=', self.id)]
#         return action
#     
    def di_get_type_piece(self):
        ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'PIECE')])
        return ProductPack
    
    #unicité du code article
    @api.multi
    @api.constrains('default_code')
    def _check_default_code(self):
        for prod in self:
            if prod.default_code:
                default_code = prod.search([
                    ('id', '!=', prod.id),
                    ('default_code', '=', prod.default_code)], limit=1)
                if default_code:
                    raise Warning("Le code existe déjà.")
                     
    @api.multi
    def write(self, vals):     
                         
        # à l'écriture de l'article on va recalculer les quantités entre conditionnements
        # on commence par parcourir les emballages de type pièces, puis colis, puis palette
        for ProductPack in self.packaging_ids:
            if ProductPack.di_type_cond == 'PIECE':
                ProductPack.di_type_cond_inf_id = ''
                ProductPack.di_qte_cond_inf = 1
        for ProductPack in self.packaging_ids:
            if ProductPack.di_type_cond == 'COLIS':
                PP_Piece = self.env['product.packaging'].search(['&', ('product_id', '=', self.id), ('di_type_cond', '=', 'PIECE')], limit=1)
                if PP_Piece:
                    ProductPack.di_type_cond_inf_id = PP_Piece.id
                    ProductPack.qty = PP_Piece.qty*ProductPack.di_qte_cond_inf 
        for ProductPack in self.packaging_ids:
            if ProductPack.di_type_cond == 'PALETTE':
                PP_Colis = self.env['product.packaging'].browse(ProductPack.di_type_cond_inf_id).id
                if PP_Colis:
                    ProductPack.qty = PP_Colis.qty*ProductPack.di_qte_cond_inf 
        res = super(ProductProduct, self).write(vals)
        return res
    
    @api.model
    def create(self, values):
        pp = super(ProductProduct, self).create(values)
        if (pp.default_code == False) and (pp.di_param_seq_art):            
            if 'company_id' in values:
                pp.default_code = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code('ART_SEQ') or _('New')
            else:
                pp.default_code = self.env['ir.sequence'].next_by_code('ART_SEQ') or _('New')
        return pp        

class ProductPackaging(models.Model):
    _inherit = "product.packaging"
    _order = 'product_id,name'
        
    di_qte_cond_inf = fields.Float(string='Quantité conditionnement inférieur')
    di_type_cond = fields.Selection([("PIECE", "Cond. Réf."), ("COLIS", "Colis"),("PALETTE", "Palette")], string="Type de conditionnement")    
    di_type_cond_inf_id = fields.Many2one('product.packaging', string='Conditionnement inférieur')
    di_des = fields.Char(string="Désignation")#, required=True)    # ????
    di_product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    di_search_name = fields.Char(string='Recherche Code',compute='_di_compute_search_name',store=True)
    di_poids = fields.Float(string='Poids',help="""Poids de l'emballage.""")
    
    @api.onchange('product_id')
    def di_oc_product_id(self):
        self.ensure_one()
        if self._context.get('default_product_id'):
            self.product_id = self._context['default_product_id']
    
    @api.multi
    @api.depends('product_id', 'name')
    def _di_compute_search_name(self):
        for pack in self:
            if pack.product_id and pack.name:
                pack.di_search_name = pack.product_id.default_code + "_" + pack.name            
        
    @api.onchange('di_type_cond', 'di_type_cond_inf_id', 'di_qte_cond_inf')
    def onchange_recalc_colisage(self):    #TODO à faire à l'écriture car les enregs ne sont pas à jour tant que l'article n'est pas sauvegardé
        if self.di_type_cond=='PIECE':
            self.di_type_cond_inf_id=''
            self.di_qte_cond_inf=1
        if self.di_type_cond=='COLIS':
            self.di_type_cond_inf_id=self.env['product.packaging'].search(['&',('product_id', '=', self.product_id.id),('di_type_cond', '=', 'PIECE')]).id
            self.qty = self.env['product.packaging'].search(['&',('product_id', '=', self.product_id.id),('di_type_cond', '=', 'PIECE')]).qty*self.di_qte_cond_inf
        if self.di_type_cond=='PALETTE':            
            self.qty = self.env['product.packaging'].search(['&',('product_id', '=', self.product_id.id),('name', '=', self.di_type_cond_inf_id.name)]).qty*self.di_qte_cond_inf
                   
    
    #vérifie qu'on a un seul conditionnement pièce par article
    @api.multi
    @api.constrains('product_id','di_type_cond')
    def _check_cond_piece_article(self):
        for pack in self:
            if pack.di_type_cond=="PIECE":
                ProductPack = pack.search([('name','!=',pack.name),('product_id', '=', pack.product_id.id),('di_type_cond', '=', "PIECE")], limit=1)        
                if ProductPack:
                    raise Warning("Vous ne pouvez pas avoir plusieurs conditionnements de type Pièce pour un même article.") 

    #vérifie l'unicité du nom du conditionnement pour un article
    @api.multi
    @api.constrains('name')
    def _check_nom_unique_article(self):
        for pack in self:
            ProductPack = pack.search([('name','=',pack.name),('product_id', '=', pack.product_id.id),('id','!=',pack.id)], limit=1)        
            if ProductPack:
                raise Warning("Vous ne pouvez pas avoir plusieurs conditionnements avec le même nom pour un même article.") 
    
    # on définie la fonction name_search pour améliorer l'import excel     
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        firsts_records = self.search([('di_search_name', '=ilike', name)] + args, limit=limit)
        search_domain = [('name', operator, name)]
        search_domain.append(('id', 'not in', firsts_records.ids))
        records = firsts_records + self.search(search_domain + args, limit=limit)
        return [(record.id, record.display_name) for record in records]

    @api.multi
    def write(self, vals):        
        res = super(ProductPackaging, self).write(vals)           
        for prodpack in self:    
            if prodpack.di_type_cond=='COLIS':
                product = self.env['product.template'].browse(prodpack.product_id.product_tmpl_id.id)
                if not product.di_type_colis_id :
                    product.update({                
                    'di_type_colis_id': prodpack.id
                })     
#                 condinf = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'PIECE')])                
#                 if not prodpack.di_type_cond_inf_id:
#                     prodpack.update({'di_type_cond_inf_id' : condinf.id})                                                  
            elif prodpack.di_type_cond=='PALETTE':
                product = self.env['product.template'].browse(prodpack.product_id.product_tmpl_id.id)
                if not product.di_type_palette_id :
                    product.update({                
                    'di_type_palette_id': prodpack.id
                })
            
#             else:
#                 ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'COLIS')])
#                 if not ProductPack.di_type_cond_inf_id:
#                     ProductPack.update({'di_type_cond_inf_id' : prodpack.id})
                

        return res
    
    @api.model
    def create(self, vals):        
        res = super(ProductPackaging, self).create(vals)           
        for prodpack in res:    
            if prodpack.di_type_cond=='COLIS':
                product = self.env['product.template'].browse(prodpack.product_id.product_tmpl_id.id)
                if not product.di_type_colis_id :
                    product.update({                
                    'di_type_colis_id': prodpack.id
                }) 
#                 condinf = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'PIECE')])  
#                 condinf = self.product_id.packaging_ids.filtered(lambda l: l.di_type_cond=='PIECE')              
#                 if not prodpack.di_type_cond_inf_id and condinf:
#                     vals['di_type_cond_inf_id']= condinf.id
# #                     prodpack.update({'di_type_cond_inf_id' : condinf.id})                                                        
            elif prodpack.di_type_cond=='PALETTE':
                product = self.env['product.template'].browse(prodpack.product_id.product_tmpl_id.id)
                if not product.di_type_palette_id :
                    product.update({                
                    'di_type_palette_id': prodpack.id
                })
#             else:
# #                 ProductPack = self.env['product.packaging'].search(['&',('product_id', '=', self.id),('di_type_cond', '=', 'COLIS')])
#                 ProductPack = self.product_id.packaging_ids.filtered(lambda l: l.di_type_cond=='COLIS')
#                 if ProductPack and not ProductPack.di_type_cond_inf_id:
#                     ProductPack.update({'di_type_cond_inf_id' : prodpack.id})

        return res
    