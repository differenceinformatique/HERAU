# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from ...difodoo_fichiers_base.controllers import di_ctrl_print
from odoo.addons import decimal_precision as dp

# from difodoo.addons_gesprim.difodoo_ventes.models import di_inherited_stock_move 


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"    
    
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False)
    di_qte_un_saisie= fields.Float(string='Quantité en unité de saisie',store=True)
    di_un_saisie    = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie",store=True)
    di_type_palette_id  = fields.Many2one('product.packaging', string='Palette') 
    di_nb_pieces    = fields.Integer(string='Nb pièces' ,compute="_compute_qte_aff",store=True)
    di_nb_colis     = fields.Integer(string='Nb colis',compute="_compute_qte_aff",store=True)
    di_nb_palette   = fields.Float(string='Nb palettes',compute="_compute_qte_aff",store=True)
    di_poin         = fields.Float(string='Poids net',compute="_compute_qte_aff",store=True)
    di_poib         = fields.Float(string='Poids brut',store=True)
    di_tare         = fields.Float(string='Tare',store=True)
    di_un_prix      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix",store=True)

    di_qte_un_saisie_liv = fields.Float(string='Quantité reçue en unité de saisie',compute='_compute_qty_received',store=True)
    di_un_saisie_liv     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie reçue",store=True)
    di_type_palette_liv_id  = fields.Many2one('product.packaging', string='Palette reçue',store=True) 
    di_nb_pieces_liv     = fields.Integer(string='Nb pièces reçues',compute='_compute_qty_received',store=True)
    di_nb_colis_liv      = fields.Integer(string='Nb colis reçus',compute='_compute_qty_received',store=True)
    di_nb_palette_liv    = fields.Float(string='Nb palettes reçues',compute='_compute_qty_received',store=True)
    di_poin_liv          = fields.Float(string='Poids net reçu',compute='_compute_qty_received',store=True)
    di_poib_liv          = fields.Float(string='Poids brut reçu',compute='_compute_qty_received',store=True)
    di_tare_liv          = fields.Float(string='Tare reçue',compute='_compute_qty_received',store=True)
    di_product_packaging_liv_id=fields.Many2one('product.packaging', string='Colis reçu',store=True)
    
    di_qte_un_saisie_fac = fields.Float(string='Quantité facturée en unité de saisie',compute='_compute_qty_invoiced',store=True)
    di_un_saisie_fac     = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de saisie facturés",store=True)
    di_type_palette_fac_id  = fields.Many2one('product.packaging', string='Palette facturée',store=True) 
    di_nb_pieces_fac     = fields.Integer(string='Nb pièces facturées',store=True)
    di_nb_colis_fac      = fields.Integer(string='Nb colis facturés',store=True)
    di_nb_palette_fac    = fields.Float(string='Nb palettes facturées',store=True)
    di_poin_fac          = fields.Float(string='Poids net facturé',store=True)
    di_poib_fac          = fields.Float(string='Poids brut facturé',store=True)
    di_tare_fac          = fields.Float(string='Tare facturée',store=True)
    di_product_packaging_fac_id=fields.Many2one('product.packaging', string='Colis facturé',store=True)
    di_un_prix_fac      = fields.Selection([("PIECE", "Pièce"), ("COLIS", "Colis"),("PALETTE", "Palette"),("KG","Kg")], string="Unité de prix facturé",store=True)
 
    di_spe_saisissable = fields.Boolean(string='Champs spé saisissables',default=False,compute='_di_compute_spe_saisissable',store=True)
    
    di_dern_prix = fields.Float(string='Dernier prix', digits=dp.get_precision('Product Price'),compute='_di_compute_dernier_prix',store=True)
    
    def _get_dernier_prix(self):
        prix = 0.0
        l = self.search(['&', ('product_id', '=', self.product_id.id), ('partner_id', '=', self.partner_id.id),('date_order','<',self.date_order)], limit=1).sorted(key=lambda t: t.date_order,reverse=True)
        if l.price_unit:
            prix = l.price_unit            
        return prix
    
    @api.one
    @api.depends('product_id','partner_id','date_order')
    def _di_compute_dernier_prix(self):        
        self.di_dern_prix =self._get_dernier_prix()
    
    @api.one
    @api.depends('product_id.di_spe_saisissable')
    def _di_compute_spe_saisissable(self):        
        self.di_spe_saisissable =self.product_id.di_spe_saisissable
       

    @api.depends('product_qty', 'price_unit', 'taxes_id','di_qte_un_saisie','di_nb_pieces','di_nb_colis','di_nb_palette','di_poin','di_poib','di_tare','di_un_prix')
    def _compute_amount(self):
        # copie standard
        """
        Compute the amounts of the SO line.
        """
        for line in self:            
             
            di_qte_prix = 0.0
            if line.di_un_prix == "PIECE":
                di_qte_prix = line.di_nb_pieces
            elif line.di_un_prix == "COLIS":
                di_qte_prix = line.di_nb_colis
            elif line.di_un_prix == "PALETTE":
                di_qte_prix = line.di_nb_palette
            elif line.di_un_prix == "KG":
                di_qte_prix = line.di_poin
            elif line.di_un_prix == False or line.di_un_prix == '':
                di_qte_prix = line.product_qty
              
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, di_qte_prix, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })    
             
        
        
    @api.depends('order_id.state', 'move_ids.state', 'move_ids.product_uom_qty','move_ids.di_qte_un_saisie','move_ids.di_nb_pieces','move_ids.di_nb_colis','move_ids.di_nb_palette','move_ids.di_poin','move_ids.di_poib')
    def _compute_qty_received(self):
        
        for line in self:
            if line.order_id.state not in ['purchase', 'done']:
                line.di_qte_un_saisie_liv = 0.0
                line.di_nb_pieces_liv = 0.0
                line.di_nb_colis_liv = 0.0
                line.di_nb_palette_liv = 0.0
                line.di_poin_liv = 0.0
                line.di_poib_liv = 0.0
                continue
            if line.product_id.type not in ['consu', 'product']:
                line.di_qte_un_saisie_liv = line.di_qte_un_saisie
                line.di_nb_pieces_liv = line.di_nb_pieces
                line.di_nb_colis_liv = line.di_nb_colis
                line.di_nb_palette_liv = line.di_nb_palette
                line.di_poin_liv = line.di_poin
                line.di_poib_liv = line.di_poib
                continue
            total_qte_un_saisie_liv = 0.0
            total_nb_pieces_liv = 0.0
            total_nb_colis_liv = 0.0
            total_nb_palette_liv = 0.0
            total_poin_liv = 0.0
            total_poib_liv = 0.0
            for move in line.move_ids:
                if move.state == 'done':
                    if move.location_dest_id.usage == "supplier":
                        if move.to_refund:
                            total_qte_un_saisie_liv -= move.di_qte_un_saisie
                            total_nb_pieces_liv -= move.di_nb_pieces
                            total_nb_colis_liv -= move.di_nb_colis
                            total_nb_palette_liv -= move.di_nb_palette
                            total_poin_liv -= move.di_poin
                            total_poib_liv -= move.di_poib
                    else:
                        total_qte_un_saisie_liv += move.di_qte_un_saisie
                        total_nb_pieces_liv += move.di_nb_pieces
                        total_nb_colis_liv += move.di_nb_colis
                        total_nb_palette_liv += move.di_nb_palette
                        total_poin_liv += move.di_poin
                        total_poib_liv += move.di_poib
                                          
                line.di_type_palette_liv_id  = move.di_type_palette_id
                line.di_un_saisie_liv     = move.di_un_saisie
                line.di_product_packaging_liv_id = move.di_product_packaging_id
                line.di_tare_liv          = move.di_tare                
                  
            line.di_qte_un_saisie_liv = total_qte_un_saisie_liv
            line.di_nb_pieces_liv = total_nb_pieces_liv
            line.di_nb_colis_liv = total_nb_colis_liv
            line.di_nb_palette_liv = total_nb_palette_liv
            line.di_poin_liv = total_poin_liv
            line.di_poib_liv = total_poib_liv            
        super(PurchaseOrderLine, self)._compute_qty_received() 
            
           
    @api.one
    @api.depends('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','di_poib','di_tare','product_packaging')
    def _compute_qte_aff(self):
        #if self.ensure_one():
        if self.di_un_saisie == "PIECE":
            self.di_nb_pieces = self.di_qte_un_saisie            
            if self.product_packaging.qty != 0.0 :
                self.di_nb_colis = self.product_qty / self.product_packaging.qty
            else:      
                self.di_nb_colis = self.product_qty             
            if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.product_qty * self.product_id.weight             
                    
        elif self.di_un_saisie == "COLIS":
            self.di_nb_colis = self.di_qte_un_saisie            
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
            if self.di_type_palette_id.di_qte_cond_inf !=0.0:                
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_palette = self.di_nb_colis
            self.di_poin = self.product_qty * self.product_id.weight             
                                   
        elif self.di_un_saisie == "PALETTE":            
            self.di_nb_palette = self.di_qte_un_saisie
            if self.di_type_palette_id.di_qte_cond_inf!=0.0:
                self.di_nb_colis = self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf
            else:
                self.di_nb_colis = self.di_nb_palette
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis            
            self.di_poin = self.product_qty * self.product_id.weight             
              
        elif self.di_un_saisie == "KG":
            self.di_poin = self.di_qte_un_saisie                        
            if self.product_packaging.qty !=0.0:
                self.di_nb_colis = self.product_qty / self.product_packaging.qty
            else:
                self.di_nb_colis = self.product_qty
            if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
              
        else:
            self.di_poin = self.di_qte_un_saisie            
            self.product_qty = self.di_poin
            if self.product_packaging.qty !=0.0:
                self.di_nb_colis = self.product_qty / self.product_packaging.qty
            else:
                self.di_nb_colis = self.product_qty
            if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
            else:  
                self.di_nb_palette = self.di_nb_colis
            self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
     
    @api.multi
    @api.onchange('product_id')
    def _di_charger_valeur_par_defaut(self):
        if self.ensure_one():
            if self.product_id.id != False:
                self.di_un_saisie = self.product_id.di_un_saisie
                self.di_type_palette_id = self.product_id.di_type_palette_id
                self.product_packaging = self.product_id.di_type_colis_id    
                self.di_un_prix = self.product_id.di_un_prix        
                

    @api.multi    
    @api.onchange('di_qte_un_saisie', 'di_un_saisie','di_type_palette_id','di_poib','di_tare','product_packaging')
    def _di_recalcule_quantites(self):
        if self.ensure_one():
            if self.di_un_saisie == "PIECE":
                self.di_nb_pieces = self.di_qte_un_saisie
                self.product_qty = self.product_id.di_get_type_piece().qty * self.di_nb_pieces
                if self.product_packaging.qty != 0.0 :
                    self.di_nb_colis = self.product_qty / self.product_packaging.qty
                else:      
                    self.di_nb_colis = self.product_qty             
                if self.di_type_palette_id.di_qte_cond_inf != 0.0:
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.product_qty * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                       
            elif self.di_un_saisie == "COLIS":
                self.di_nb_colis = self.di_qte_un_saisie
                self.product_qty = self.product_packaging.qty * self.di_nb_colis
                self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:                
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_palette = self.di_nb_colis
                self.di_poin = self.product_qty * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                                      
            elif self.di_un_saisie == "PALETTE":            
                self.di_nb_palette = self.di_qte_un_saisie
                if self.di_type_palette_id.di_qte_cond_inf!=0.0:
                    self.di_nb_colis = self.di_nb_palette / self.di_type_palette_id.di_qte_cond_inf
                else:
                    self.di_nb_colis = self.di_nb_palette
                self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
                self.product_qty = self.product_packaging.qty * self.di_nb_colis
                self.di_poin = self.product_qty * self.product_id.weight 
                self.di_poib = self.di_poin + self.di_tare
                 
            elif self.di_un_saisie == "KG":
                self.di_poin = self.di_qte_un_saisie
                self.di_poib = self.di_poin + self.di_tare
                self.product_qty = self.di_poin
                if self.product_packaging.qty !=0.0:
                    self.di_nb_colis = self.product_qty / self.product_packaging.qty
                else:
                    self.di_nb_colis = self.product_qty
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
                 
            else:
                self.di_poin = self.di_qte_un_saisie
                self.di_poib = self.di_poin + self.di_tare
                self.product_qty = self.di_poin
                if self.product_packaging.qty !=0.0:
                    self.di_nb_colis = self.product_qty / self.product_packaging.qty
                else:
                    self.di_nb_colis = self.product_qty
                if self.di_type_palette_id.di_qte_cond_inf !=0.0:    
                    self.di_nb_palette = self.di_nb_colis / self.di_type_palette_id.di_qte_cond_inf
                else:  
                    self.di_nb_palette = self.di_nb_colis
                self.di_nb_pieces = self.product_packaging.di_qte_cond_inf * self.di_nb_colis
               
         
    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity','invoice_lines.di_qte_un_saisie','invoice_lines.di_nb_pieces','invoice_lines.di_nb_colis','invoice_lines.di_nb_palette','invoice_lines.di_poin','invoice_lines.di_poib')
    def _compute_qty_invoiced(self):
        for line in self:
            qty = 0.0
            poib = 0.0
            nbpieces=0.0
            nbcol = 0.0
            nbpal=0.0
            poin=0.0
            for inv_line in line.invoice_lines:
                if inv_line.invoice_id.state not in ['cancel']:
                    if inv_line.invoice_id.type == 'in_invoice':
                        qty += inv_line.di_qte_un_saisie
                        poib += inv_line.di_poib
                        nbpieces += inv_line.di_nb_pieces
                        nbcol += inv_line.di_nb_colis
                        nbpal += inv_line.di_nb_palette
                        poin += inv_line.di_poin
                    elif inv_line.invoice_id.type == 'in_refund':
                        qty -= inv_line.di_qte_un_saisie
                        poib -= inv_line.di_poib
                        nbpieces -= inv_line.di_nb_pieces
                        nbcol -= inv_line.di_nb_colis
                        nbpal -= inv_line.di_nb_palette
                        poin -= inv_line.di_poin
            line.di_qte_un_saisie_fac = qty
            line.di_poib = poib
            line.di_nb_pieces = nbpieces
            line.di_nb_colis = nbcol
            line.di_nb_palette = nbpal
            line.di_poin = poin
                    
        super(PurchaseOrderLine, self)._compute_qty_invoiced()


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    di_demdt = fields.Date(string='Date demandée', copy=False, help="Date de réception souhaitée",
                           default=lambda wdate : datetime.today().date()+timedelta(days=1))
    
    @api.multi
    @api.onchange('di_demdt')
    def modif_demdt(self):
        if datetime.strptime(self.di_demdt,'%Y-%m-%d').date()<datetime.today().date():
            return {'warning': {'Erreur date demandée': _('Error'), 'message': _('La date de reception souhaitée ne peut être inférieure à la date du jour !'),},}       
        self.date_planned = datetime.strptime(self.di_demdt,'%Y-%m-%d')

    
    @api.multi
    def imprimer_etiquettes(self):         
        param = self.env['di.param'].search([('di_company_id','=',self.env.user.company_id.id)])
        if param.di_label_ach_id and param.di_label_ach_id.file is not None and param.di_label_ach_id.file != "":
            if param.di_printer_ach_id : #and param.di_printer_id.adressip is not None and param.di_printer_id.adressip != "":
                if param.di_printer_ach_id.realname is not None and param.di_printer_ach_id.realname != "":
                    printer = param.di_printer_ach_id.realname
                    label = param.di_label_ach_id.file
                    data = ''
                    for po in self:
                        for pol in po.order_line:
                            if pol.product_id.barcode : 
                                barcode = pol.product_id.barcode
                            else:
                                barcode="0000000000000"
                            if pol.move_ids:
                                for sm in pol.move_ids: 
                                    if sm.move_line_ids:
                                        for sml in sm.move_line_ids:
                                            qteform = "000000"
                                            qteform =str(int(sml.qty_done*100)) 
                                            qteform=qteform.rjust(6,'0')            
                                            if sml.lot_id:
                                                informations=[
                                                    ("codeart",pol.product_id.default_code),
                                                    ("des",pol.product_id.product_tmpl_id.name),
                                                    ("qte",sml.qty_done),                                       
                                                    ("codebarre",">802"+barcode+">83102"+qteform+">810"+">6"+sml.lot_id.name),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform+"(10)"+sml.lot_id.name),
                                                    ("lot",sml.lot_id.name)
                                                    ]
                                            else:
                                                informations=[
                                                    ("codeart",pol.product_id.default_code),
                                                    ("des",pol.product_id.product_tmpl_id.name),
                                                    ("qte",sml.qty_done),                                        
                                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                                    ("lot"," ")                                                                                                                                   
                                                    ]     
                                            data =data+ di_ctrl_print.format_data(label, '[', informations)                                                                                       
                                    else:
                                        qteform = "000000"
                                        qteform =str(int(sm.product_qty*100)) 
                                        qteform=qteform.rjust(6,'0')
                                        informations=[
                                                    ("codeart",pol.product_id.default_code),
                                                    ("des",pol.product_id.product_tmpl_id.name),
                                                    ("qte",sm.product_qty),                                                                                
                                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                                    ("lot"," ")                                                                                                                                                      
                                                    ]              
                                        data =data+ di_ctrl_print.format_data(label, '[', informations)                                   
#                                         di_ctrl_print.printlabelonwindows(printer,label,'[',informations)                                            
                            else:
                                qteform = "000000"
                                qteform =str(int(pol.product_uom_qty*100))
                                qteform=qteform.rjust(6,'0')
                                informations=[
                                    ("codeart",pol.product_id.default_code),
                                    ("des",pol.product_id.product_tmpl_id.name),
                                    ("qte",pol.product_uom_qty),
                                    #("codebarre",sol.product_id.barcode),                                            
                                    ("codebarre",">802"+barcode+">83102"+qteform),
                                    ("txtcb","(02)"+barcode+"(3102)"+qteform),
                                    ("lot"," ")                                                                                                                          
                                    ]
                                data =data+ di_ctrl_print.format_data(label, '[', informations) 
#                                 
                        di_ctrl_print.printlabelonwindows(printer,data)