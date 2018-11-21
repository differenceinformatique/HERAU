
# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    #référencement article 
    di_refarticle_ids = fields.Many2many('product.product', 'di_referencement_article_tiers', 'partner_id','product_id', string='Référencement article')
    di_code_tarif_id = fields.Many2one('di.code.tarif', string="Code tarif", help="Sans code tarif, c'est le tarif de la fiche article qui est repris")
    ref = fields.Char(string='Internal Reference', index=True, help="Code Tiers")  # modif attribut copy + ajout help
    di_period_fact = fields.Selection([("DEMANDE", "Demande"), ("SEMAINE", "Semaine"),("DECADE", "Décade"),("QUINZAINE","Quinzaine"),("MOIS","Mois")],
                                      default="DEMANDE", string="Périodicité de Facturation", help="Permet de filtrer lors de la facturation")
    di_regr_fact = fields.Boolean(string="Regroupement sur Facture", default=True, help="Permet de filtrer lors de la facturation")
    di_pres_bl = fields.Selection([('CHIFFRE','Chiffré'),('NONCHIFFRE','Non Chiffré')], default="NONCHIFFRE", string="Présentation BL",
                                   help="Choix de la présentation du bon de livraison")
    is_company = fields.Boolean(string='Is a Company', default=True, help="Check if the contact is a company, otherwise it is a person")  # modif attribut default
    di_defaut_adr = fields.Boolean(string="Adresse par défaut", default=False, help="Sera selectionnée automatiquement en saisie de pièces")
    di_code_dest_id = fields.Many2one('di.code.dest', string='Code destination', help="Code destination pour les grilles transporteurs")
    di_param_seq_cli = fields.Boolean(string='Codification auto.',compute='_di_compute_seq_clifou',store=False)
    di_param_seq_fou = fields.Boolean(string='Codification auto.',compute='_di_compute_seq_clifou',store=False)
    di_ref_required = fields.Boolean(string='Code article obligatoire',compute='_di_compute_ref_required',store=False)
    di_tournee = fields.Char(string='Tournée',help="Pour regroupement sur les bordereaux de transport")
    di_rangtournee = fields.Char(string='Rang dans la tournée',help="Pour ordre de tri sur les bordereaux de transport")
    di_iban = fields.Char(string='IBAN',help="Saisir l'IBAN ",size=34)
    di_naf = fields.Char(string='NAF')
    di_nbex_cde = fields.Integer("Nombre exemplaires commande",help="""Nombre d'exemplaires d'une impression de commande.""",default=1)
    di_nbex_bl = fields.Integer("Nombre exemplaires BL",help="""Nombre d'exemplaires,d'une impression de BL.""",default=1)
    di_nbex_fac = fields.Integer("Nombre exemplaires facture",help="""Nombre d'exemplaires, d'une impression de facture.""",default=1)
    

    @api.onchange('di_iban')
    def _di_controle_iban(self):
        if self.di_iban:
            ibanstr=self.di_iban[4:34].strip()+self.di_iban[:4]
            ibanstr=ibanstr.replace("A","10")
            ibanstr=ibanstr.replace("B","11")
            ibanstr=ibanstr.replace("C","12")
            ibanstr=ibanstr.replace("D","13")
            ibanstr=ibanstr.replace("E","14")
            ibanstr=ibanstr.replace("F","15")
            ibanstr=ibanstr.replace("G","16")
            ibanstr=ibanstr.replace("H","17")
            ibanstr=ibanstr.replace("I","18")
            ibanstr=ibanstr.replace("J","19")
            ibanstr=ibanstr.replace("K","20")
            ibanstr=ibanstr.replace("L","21")
            ibanstr=ibanstr.replace("M","22")
            ibanstr=ibanstr.replace("N","23")
            ibanstr=ibanstr.replace("O","24")
            ibanstr=ibanstr.replace("P","25")
            ibanstr=ibanstr.replace("Q","26")
            ibanstr=ibanstr.replace("R","27")
            ibanstr=ibanstr.replace("S","28")
            ibanstr=ibanstr.replace("T","29")
            ibanstr=ibanstr.replace("U","30")
            ibanstr=ibanstr.replace("V","31")
            ibanstr=ibanstr.replace("W","32")
            ibanstr=ibanstr.replace("X","33")
            ibanstr=ibanstr.replace("Y","34")
            ibanstr=ibanstr.replace("Z","35")        
            try:
                ibanint=int(ibanstr)            
            except:
                ibanint=0
                self.di_iban=''
                raise Warning("L'IBAN saisi est incorrect.")
            
            if ibanint != 0:
                reste=ibanint % 97
                if reste !=1:            
                    self.di_iban=''
                    raise Warning("L'IBAN saisi est incorrect.")
        
        
    @api.multi
    @api.depends('company_id')
    def _di_compute_seq_clifou(self):
        for partner in self:
            if partner.company_id and partner.company_id.di_param_id:
                partner.di_param_seq_cli = partner.company_id.di_param_id.di_seq_cli
                partner.di_param_seq_fou = partner.company_id.di_param_id.di_seq_fou
            else:
                partner.di_param_seq_cli = False   
                partner.di_param_seq_fou = False
            
    @api.multi
    @api.depends('di_param_seq_cli','di_param_seq_fou')
    def _di_compute_ref_required(self):
        for partner in self:
            if partner.customer:
                if partner.di_param_seq_cli:
                    partner.di_ref_required=False
                else:
                    partner.di_ref_required=True
            elif partner.supplier:
                if partner.di_param_seq_fou:
                    partner.di_ref_required=False
                else:
                    partner.di_ref_required=True
            else:
                partner.di_ref_required=False
                 
    #unicité du code tiers
    @api.multi
    @api.constrains('ref')
    def _check_ref(self):
        for partner in self:
            if partner.ref:
                default_code = partner.search([
                    ('id', '!=', partner.id),
                    ('ref', '=', partner.ref)], limit=1)
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

    @api.multi
    @api.onchange('country_id', 'zip')
    def _compute_code_dest(self):
        if self.ensure_one():
            if self.country_id and self.zip:
                search_name = self.country_id.code + '_' + self.zip[:2]
                search_id = self.env['di.code.dest'].search([('name', '=', search_name)],limit=1)
                if search_id:
                    self.di_code_dest_id = search_id

    @api.model
    def create(self, values):
        rp = super(ResPartner, self).create(values)
        if rp.customer:
        # si client, séquence client              
            if (rp.ref == False) and (rp.di_param_seq_cli):            
                if 'company_id' in values:
                    rp.ref = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code('CLI_SEQ') or _('New')
                else:
                    rp.ref = self.env['ir.sequence'].next_by_code('CLI_SEQ') or _('New')
        if rp.supplier:
        # si fournisseur, séquence fournisseur
            if (rp.ref == False) and (rp.di_param_seq_fou):            
                if 'company_id' in values:
                    rp.ref = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code('FOU_SEQ') or _('New')
                else:
                    rp.ref = self.env['ir.sequence'].next_by_code('FOU_SEQ') or _('New')
        return rp

    
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('ref', '=like', u"{}%_Copie".format(self.ref))])
        if not copied_count:
            new_name = u"{}_Copie".format(self.ref)            
        else:
            new_name = u"{}_Copie({})".format(self.ref, copied_count)

        default['ref'] = new_name
        return super(ResPartner, self).copy(default)