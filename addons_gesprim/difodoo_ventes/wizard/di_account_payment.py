# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from collections import defaultdict
from itertools import groupby
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}

class account_payment(models.Model):
    _inherit = "account.payment"
    @api.multi
    def button_invoices(self):
        action = {
            'name': _('Factures payées'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.invoice_ids])],
        }
        if self.partner_type == 'supplier':
            action['views'] = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'), (self.env.ref('account.invoice_supplier_form').id, 'form')]
            action['context'] = {
                'journal_type': 'purchase',
                'type': 'in_invoice',
                'default_type': 'in_invoice',
            }
        else:
            action['views'] = [(self.env.ref('account.invoice_tree').id, 'tree'), (self.env.ref('account.invoice_form').id, 'form')]
        return action
    
class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"
    
    
    @api.multi
    def _compute_payment_amount(self, invoices=None, currency=None):
        # copie standard pour prendre en compte si on a avoir et facture
        '''Compute the total amount for the payment wizard.

        :param invoices: If not specified, pick all the invoices.
        :param currency: If not specified, search a default currency on wizard/journal.
        :return: The total amount to pay the invoices.
        '''

        # Get the payment invoices
        if not invoices:
            invoices = self.invoice_ids

        # Get the payment currency
        if not currency:
            currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or invoices and invoices[0].currency_id
        
        total = 0.0
        groups = groupby(invoices, lambda i: i.currency_id)
        for payment_currency, payment_invoices in groups:
            amount_total = sum([MAP_INVOICE_TYPE_PAYMENT_SIGN[i.type] * i.residual_signed for i in payment_invoices])
            if payment_currency == currency:
                total += amount_total
            else:
                total += payment_currency._convert(amount_total, currency, self.env.user.company_id, self.payment_date or fields.Date.today())
        return total
        # Avoid currency rounding issues by summing the amounts according to the company_currency_id before
#         invoice_datas = invoices.read_group(
#             [('id', 'in', invoices.ids)],
#             ['currency_id', 'type', 'residual_signed'],
#             ['currency_id', 'type'], lazy=False)
#         total = 0.0
#         for invoice_data in invoice_datas:
#             amount_total = MAP_INVOICE_TYPE_PAYMENT_SIGN[invoice_data['type']] * invoice_data['residual_signed']
#             payment_currency = self.env['res.currency'].browse(invoice_data['currency_id'][0])
#             if payment_currency == currency:
#                 total += amount_total
#             else:
#                 total += payment_currency._convert(amount_total, currency, self.env.user.company_id, self.payment_date or fields.Date.today())
#         return total
    
        # Avoid currency rounding issues by summing the amounts according to the company_currency_id before
        total = 0.0
        groups = groupby(invoices, lambda i: i.currency_id)
        for payment_currency, payment_invoices in groups:
            amount_total = sum([MAP_INVOICE_TYPE_PAYMENT_SIGN[i.type] * i.residual_signed for i in payment_invoices])
            if payment_currency == currency:
                total += amount_total
            else:
                total += payment_currency._convert(amount_total, currency, self.env.user.company_id, self.payment_date or fields.Date.today())
        return total
    
    @api.model
    def default_get(self, fields):
        #copie standard
        #pour pouvoir payer sur une facture et un avoir en même temps
#         rec = super(account_abstract_payment, self).default_get(fields)
        self.view_init(fields)

        defaults = {}
        parent_fields = defaultdict(list)
        ir_defaults = self.env['ir.default'].get_model_defaults(self._name)

        for name in fields:
            # 1. look up context
            key = 'default_' + name
            if key in self._context:
                defaults[name] = self._context[key]
                continue

            # 2. look up ir.default
            if name in ir_defaults:
                defaults[name] = ir_defaults[name]
                continue

            field = self._fields.get(name)

            # 3. look up field.default
            if field and field.default:
                defaults[name] = field.default(self)
                continue

            # 4. delegate to parent model
            if field and field.inherited:
                field = field.related_field
                parent_fields[field.model_name].append(field.name)

        # convert default values to the right format
        defaults = self._convert_to_write(defaults)

        # add default values for inherited fields
        for model, names in parent_fields.items():
            defaults.update(self.env[model].default_get(names))

        rec= defaults
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.invoice':
            return rec

        invoices = self.env['account.invoice'].browse(active_ids)

        # Check all invoices are open
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # Check all invoices have the same currency
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they must use the same currency."))
        # Check if, in batch payments, there are not negative invoices and positive invoices
#         dtype = invoices[0].type
#         for inv in invoices[1:]:
#             if inv.type != dtype:
#                 if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
#                         (dtype == 'in_invoice' and inv.type == 'in_refund')):
#                     raise UserError(_("You cannot register payments for vendor bills and supplier refunds at the same time."))
#                 if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
#                         (dtype == 'out_invoice' and inv.type == 'out_refund')):
#                     raise UserError(_("You cannot register payments for customer invoices and credit notes at the same time."))

        # Look if we are mixin multiple commercial_partner or customer invoices with vendor bills
        multi = any(inv.commercial_partner_id != invoices[0].commercial_partner_id
            or MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
            or inv.account_id != invoices[0].account_id
            or inv.partner_bank_id != invoices[0].partner_bank_id
            for inv in invoices)

        currency = invoices[0].currency_id

        total_amount = self._compute_payment_amount(invoices=invoices, currency=currency)

        rec.update({
            'amount': abs(total_amount),
            'currency_id': currency.id,
            'payment_type': total_amount > 0 and 'inbound' or 'outbound',
            'partner_id': False if multi else invoices[0].commercial_partner_id.id,
            'partner_type': False if multi else MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': ' '.join([ref for ref in invoices.mapped('reference') if ref])[:2000],
            'invoice_ids': [(6, 0, invoices.ids)],
            'multi': multi,
        })
        return rec       
