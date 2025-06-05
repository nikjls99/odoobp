from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    allow_cash_out_request = fields.Boolean(default=False, string="Allow Cash Out Request",
        help="Allow employee to request cash out for this leave type.")
