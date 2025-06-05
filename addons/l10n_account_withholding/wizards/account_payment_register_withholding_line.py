# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class AccountPaymentRegisterWithholdingLine(models.TransientModel):
    _name = 'account.payment.register.withholding.line'
    _inherit = "account.withholding.line"
    _description = 'Payment register withholding line'

    # ------------------
    # Fields declaration
    # ------------------

    payment_register_id = fields.Many2one(
        comodel_name='account.payment.register',
        required=True,
        ondelete='cascade',
    )

    # --------------------------------
    # Compute, inverse, search methods
    # --------------------------------

    def _get_default_base_amount_when_no_source_currency(self):
        self.ensure_one()
        return self.payment_register_id.amount

    @api.depends('payment_register_id.amount')
    def _compute_original_amounts(self):
        # Extended to add the dependency
        super()._compute_original_amounts()

    @api.depends('payment_register_id.payment_type')
    def _compute_type_tax_use(self):
        for line in self:
            line.type_tax_use = 'sale' if line.payment_register_id.payment_type == 'inbound' else 'purchase'

    @api.depends('payment_register_id.amount', 'payment_register_id.can_edit_wizard', 'payment_register_id.should_withhold_tax')
    def _compute_comodel_percentage_paid_factor(self):
        for wizard, lines in self.grouped('payment_register_id').items():
            if not wizard.can_edit_wizard:
                lines.comodel_percentage_paid_factor = 0.0
                continue

            total_amounts_to_pay = wizard._get_total_amounts_to_pay(wizard.batches)
            moves_total_amount = wizard._get_total_amount_in_wizard_currency()
            if total_amounts_to_pay['full_amount']:
                # We need to care about partial payment; for example if paid in two times.
                # In this case, the full amount is going to be the residual amount; and the factor would be wrongly "1"
                split_factor = abs(total_amounts_to_pay['full_amount'] / moves_total_amount)
                lines.comodel_percentage_paid_factor = abs(wizard.amount / total_amounts_to_pay['full_amount']) * split_factor
            else:
                lines.comodel_percentage_paid_factor = 0.0

    @api.depends('payment_register_id.payment_date')
    def _compute_comodel_date(self):
        for line in self:
            line.comodel_date = line.payment_register_id.payment_date

    @api.depends('payment_register_id.payment_type')
    def _compute_comodel_payment_type(self):
        for line in self:
            line.comodel_payment_type = line.payment_register_id.payment_type

    @api.depends('payment_register_id.company_id')
    def _compute_company_id(self):
        for line in self:
            line.company_id = line.payment_register_id.company_id

    @api.depends('payment_register_id.currency_id')
    def _compute_comodel_currency_id(self):
        for line in self:
            line.comodel_currency_id = line.payment_register_id.currency_id

    # -----------------------
    # CRUD, inherited methods
    # -----------------------

    def _prepare_withholding_amls_create_values(self):
        # EXTEND to assert that all lines in self have the same payment register when preparing the data to create the payment lines.
        assert len(self.payment_register_id) == 1, self.env._("All withholding lines in self must have the same payment register.")
        return super()._prepare_withholding_amls_create_values()

    # ----------------
    # Business methods
    # ----------------

    def _get_valid_liquidity_accounts(self):
        """ Get the valid liquidity accounts for the payment; we need to ensure that the line account does not match any of them. """
        return (
            self.payment_register_id.journal_id.default_account_id |
            self.payment_register_id.payment_method_line_id.payment_account_id |
            self.payment_register_id.journal_id.inbound_payment_method_line_ids.payment_account_id |
            self.payment_register_id.journal_id.outbound_payment_method_line_ids.payment_account_id |
            self.payment_register_id.withholding_outstanding_account_id
        )

    def _get_original_percentage_paid_factor(self):
        """ To extend in order to return the original paid factor of the comodel, if any. """
        total_amount_values = self.payment_register_id._get_total_amounts_to_pay(self.payment_register_id.batches)
        return abs(total_amount_values['amount_by_default'] / total_amount_values['full_amount'])
