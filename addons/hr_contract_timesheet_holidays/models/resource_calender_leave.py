# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.osv import expression


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves.filtered(lambda l: not l.resource_id)._assign_timesheets_for_public_holiday()
        return leaves

    def write(self, vals):
        leaves = super().write(vals)
        fields_to_check = {'date_from', 'date_to', 'calendar_id'}
        if any(field for field in fields_to_check if field in vals):
            self._assign_timesheets_for_public_holiday()
        return leaves

    def _assign_timesheets_for_public_holiday(self):
        """
        For each Public Leave in self, find employees who either:
            - have NO contract at all (permanent employees), or
            - have at least one 'open' contract whose start/end bracket [start,end],
        then call existing _generate_public_time_off_timesheets() to generate timesheets for the public leave.
        """
        public_leaves = self.filtered_domain([('resource_id', '=', False)])
        if not public_leaves:
            return

        for leave in public_leaves:
            domain_no_contract = [
                ('company_id', '=', leave.company_id.id),
                ('contract_ids', '=', False),
            ]

            domain_with_contract = [
                ('company_id', '=', leave.company_id.id),
                ('contract_ids.state', '=', 'open'),
                ('contract_ids.date_start', '<=', leave.date_from.date()),
                '|',
                    ('contract_ids.date_end', '=', False),
                    ('contract_ids.date_end', '>=', leave.date_to.date()),
            ]

            employees = self.env['hr.employee'].search(expression.OR([domain_no_contract, domain_with_contract]))
            leave._generate_public_time_off_timesheets(employees)

    def _generate_timesheeets(self):
        pass
