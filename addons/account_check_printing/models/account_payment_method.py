# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    check_manual_sequencing = fields.Boolean(
        string='Manual Numbering',
        default=False,
        help="Check this option if your pre-printed checks are not numbered.",
    )
    check_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Check Sequence',
        readonly=True,
        copy=False,
        help="Checks numbering sequence.",
    )
    check_next_number = fields.Char(
        string='Next Check Number',
        compute='_compute_check_next_number',
        inverse='_inverse_check_next_number',
        help="Sequence number of the next printed check.",
    )

    bank_check_printing_layout = fields.Selection(
        selection='_get_check_printing_layouts',
        string="Check Layout",
    )

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['check_printing'] = {'type': ('bank',)}
        return res

    def _get_check_printing_layouts(self):
        """ Returns available check printing layouts for the company, excluding disabled options """
        selection = self.company_id._fields['account_check_printing_layout'].selection
        return [(value, label) for value, label in selection if value != 'disabled']

    @api.depends('check_manual_sequencing')
    def _compute_check_next_number(self):
        for method in self:
            sequence = method.check_sequence_id
            if sequence:
                method.check_next_number = sequence.get_next_char(sequence.number_next_actual)
            else:
                method.check_next_number = 1
