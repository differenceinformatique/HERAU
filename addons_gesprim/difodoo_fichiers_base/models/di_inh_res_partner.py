
# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    #référencement article 
    di_refarticle_ids = fields.Many2many('product.product', 'di_referencement_article_tiers', 'partner_id','product_id', string='Référencement article')
    di_code_tarif_id = fields.Many2one('di.code.tarif', string="Code tarif", help="Sans code tarif, c'est le tarif de la fiche article qui est repris")
    ref = fields.Char(string='Internal Reference', index=True, copy=False)
    di_period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
    di_regr_fact = fields.Boolean(string="Regroupement sur Facture", default=True)
    di_pres_bl = fields.Selection([('CHIFFRE','Chiffré'),('NONCHIFFRE','Non Chiffré')], default="NONCHIFFRE", string="Présentation BL",
                                   help="Choix de la présentation du bon de livraison")
     
    #unicité du code tiers
    @api.one
    @api.constrains('ref')
    def _check_ref(self):
        if self.ref:
            default_code = self.search([
                ('id', '!=', self.id),
                ('ref', '=', self.ref)], limit=1)
            if default_code:
                raise Warning("Le code existe déjà.")

    @api.multi
    def name_get(self):
        res = super(ResPartner,self).name_get()
        res2 = []   # on recrée une liste qui contiendra les éléments non modifiés + ceux que l'on modifie
        for partner_id, name in res:
            partner=self.env["res.partner"].browse(partner_id)
            if partner.type in ['invoice', 'delivery', 'other']:
                # On renomme les adresses car nom identique si 2 adresses
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                name = name + ', ' + partner.city
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
                if self._context.get('show_address_only'):
                    name = partner._display_address(without_company=True)
                if self._context.get('show_address'):
                    name = name + "\n" + partner._display_address(without_company=True)
                name = name.replace('\n\n', '\n')
                name = name.replace('\n\n', '\n')
                if self._context.get('show_email') and partner.email:
                    name = "%s <%s>" % (name, partner.email)
                if self._context.get('html_format'):
                    name = name.replace('\n', '<br/>')
            res2.append((partner_id, name))
        return res2              