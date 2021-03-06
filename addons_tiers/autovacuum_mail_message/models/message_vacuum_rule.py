# -*- coding: utf-8 -*-
# Copyright (C) 2018 Akretion
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import date, timedelta

from odoo import _, api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class MessageVacuumRule(models.Model):
    _name = "message.vacuum.rule"
    _description = "Rules Used to delete message historic"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env['res.company']._company_default_get(
            'message.vacuum.rule'))
    message_subtype_ids = fields.Many2many(
        'mail.message.subtype', string="Subtypes",
        help="Message subtypes concerned by the rule. If left empty, the "
             "system won't take the subtype into account to find the "
             "messages to delete")
    empty_subtype = fields.Boolean(
        help="Take also into account messages with no subtypes")
    model_ids = fields.Many2many(
        'ir.model', string="Models",
        help="Models concerned by the rule. If left empty, it will take all "
             "models into account")
    message_type = fields.Selection([
        ('email', 'Email'),
        ('comment', 'Comment'),
        ('notification', 'System notification'),
        ('all', 'All')], required=True)
    retention_time = fields.Integer(
        required=True, default=365,
        help="Number of days the messages concerned by this rule will be "
             "keeped in the database after creation. Once the delay is "
             "passed, they will be automatically deleted.")

#     @api.multi
    @api.constrains('retention_time')
    def retention_time_not_null(self):
        for rule in self:
            if not rule.retention_time:
                raise exceptions.ValidationError(
                    _("The Retention Time can't be 0 days"))

#     @api.multi
    def get_message_domain(self):
        self.ensure_one()
        today = date.today()
        limit_date = today - timedelta(days=self.retention_time)
        limit_date = limit_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        message_domain = [('date', '<', limit_date)]
        if self.message_type != 'all':
            message_domain += [('message_type', '=', self.message_type)]
        if self.model_ids:
            models = self.model_ids.mapped('model')
            message_domain += [('model', 'in', models)]

        subtype_ids = self.message_subtype_ids.ids
        subtype_domain = []
        if subtype_ids and self.empty_subtype:
            subtype_domain = ['|', ('subtype_id', 'in', subtype_ids),
                              ('subtype_id', '=', False)]
        elif subtype_ids and not self.empty_subtype:
            subtype_domain += [('subtype_id', 'in', subtype_ids)]
        elif not subtype_ids and not self.empty_subtype:
            subtype_domain += [('subtype_id', '!=', False)]
        message_domain += subtype_domain
        return message_domain
