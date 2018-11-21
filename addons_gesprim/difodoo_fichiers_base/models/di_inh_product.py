# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api
from xlrd.formula import FMLA_TYPE_COND_FMT
from suds import null
from odoo.tools.float_utils import float_round

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
#         
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
    default_code = fields.Char('Internal Reference', index=True)
        
    di_reftiers_ids = fields.Many2many('res.partner', 'di_referencement_article_tiers', 'product_id','partner_id', string='Référencement article')
    di_tarifs_ids = fields.One2many('di.tarifs', 'id',string='Tarifs de l\'article')
    
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
