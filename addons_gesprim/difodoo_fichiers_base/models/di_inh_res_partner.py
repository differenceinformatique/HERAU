
# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    #référencement article 
    di_refarticle_ids = fields.Many2many('product.product', 'di_referencement_article_tiers', 'partner_id','product_id', string='Référencement article')
    di_code_tarif_id = fields.Many2one('di.code.tarif', string="Code tarif", help="Sans code tarif, c'est le tarif de la fiche article qui est repris")
    ref = fields.Char(string='Internal Reference', index=True, copy=False,help="Code Tiers")  # modif attribut copy + ajout help
    di_period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
    di_regr_fact = fields.Boolean(string="Regroupement sur Facture", default=True, help="Permet de filtrer lors de la facturation")
    di_pres_bl = fields.Selection([('CHIFFRE','Chiffré'),('NONCHIFFRE','Non Chiffré')], default="NONCHIFFRE", string="Présentation BL",
                                   help="Choix de la présentation du bon de livraison")
    is_company = fields.Boolean(string='Is a Company', default=True, help="Check if the contact is a company, otherwise it is a person")  # modif attribut default    
    di_defaut_adr = fields.Boolean(string="Adresse par défaut", default=False, help="Sera selectionnée automatiquement en saisie de pièces")
    
    di_is_court = fields.Boolean(string='Est un metteur en marche', default=False, help=""" Le tiers est un metteur en marche et peut donc recevoir des commissions """)  # modif attribut default
    di_prc_com_avec_court = fields.Float(string='% commission',help="""Pourcentage de commission que le metteur en marche récupère sur une vente. """, default=0.0)
    
    
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
    
    
    @api.multi
    def address_get(self, adr_pref=None):
        # Copie du standard pour pouvoir mettre une adresse de fact/liv par défaut
        """ Find contacts/addresses of the right type(s) by doing a depth-first-search
        through descendants within company boundaries (stop at entities flagged ``is_company``)
        then continuing the search at the ancestors that are within the same company boundaries.
        Defaults to partners of type ``'default'`` when the exact type is not found, or to the
        provided partner itself if no type ``'default'`` is found either. """
        adr_pref = set(adr_pref or [])
        if 'contact' not in adr_pref:
            adr_pref.add('contact')
        result = {}
        visited = set()
        for partner in self:
            current_partner = partner
            while current_partner:
                to_scan = [current_partner]
                # Scan descendants, DFS
                while to_scan:
                    record = to_scan.pop(0)
                    visited.add(record)
                    if record.type in adr_pref and not result.get(record.type):
                        result[record.type] = record.id
                    if len(result) == len(adr_pref):
                        return result
                    to_scan = [c for c in record.child_ids
                                 if c not in visited
                                 if not c.is_company] + to_scan
                    # difodoo - on trie la liste afin de mettre les adresses pas défaut en début de liste
                    to_scan.sort(key=lambda l:l.di_defaut_adr,reverse=True)

                # Continue scanning at ancestor if current_partner is not a commercial entity
                if current_partner.is_company or not current_partner.parent_id:
                    break
                current_partner = current_partner.parent_id

        # default to type 'contact' or the partner itself
        default = result.get('contact', self.id or False)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or default
        return result
