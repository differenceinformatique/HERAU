# -*- coding: utf-8 -*-

from odoo import api, fields, models

import calendar
import datetime
 
class DiCtrlTrpWiz(models.TransientModel):
    _name = "di.ctrltrp.wiz"
    _description = "Impression contrôle transporteur"
    
    company_id = fields.Many2one('res.company', string='Société', readonly=True,  default=lambda self: self.env.user.company_id)
    date_debut = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, 1), string="Date Début")
    date_fin = fields.Date(required=True, default=datetime.date(datetime.date.today().year, datetime.date.today().month, calendar.mdays[datetime.date.today().month]), string="Date Fin")
    
    transp_deb = fields.Char(default=" ", string="Transporteur Début")
    transp_fin = fields.Char(required=True, default="zzzzzzzz", string="Transporteur Fin")
    stock_picking_ids = fields.Many2many('stock.picking', string='Bons de livraisons')
    
    @api.multi
    def edit_controle_trp(self):
        # on récupére les livraisons du jour
        wdate = self.date_debut
        date_d = datetime.datetime(wdate.year,wdate.month,wdate.day,0,0,0,0).strftime("%Y-%m-%d %H:%M:%S")
        wdate = self.date_fin
        date_f = datetime.datetime(wdate.year,wdate.month,wdate.day,23,59,59,0).strftime("%Y-%m-%d %H:%M:%S")
        stock_pickings1 = self.env['stock.picking'].search([('date_done','>',date_d),('date_done','<',date_f)])
        # on filtre sur les expéditions
        stock_pickings2 = stock_pickings1.filtered(lambda sp: sp.picking_type_id.code == 'outgoing')
        # on filtre sur les transporteurs de la sélection
        if self.transp_deb==" ":
            # si pas de selection début, on va prendre les expéditions sans transporteur et inférieur é transporteur fin
            stock_pickings3 = stock_pickings2.filtered(lambda sp: sp.carrier_id.name == False or sp.carrier_id.name <= self.transp_fin)
        else:
            # sinon on teste transporteur début/transporteur fin
            stock_pickings3 = stock_pickings2.filtered(lambda sp: sp.carrier_id.name >= self.transp_deb and sp.carrier_id.name <= self.transp_fin)
        self.stock_picking_ids=stock_pickings3
        if self.stock_picking_ids:
            return self.env.ref('difodoo_ventes.di_wiz_report_ctrltrp').report_action(self)
        return {}
    
    
    
    
    
    