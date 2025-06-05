# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import models, api
from odoo.osv import expression


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        contracts.filtered(lambda c: c.state in ('open', 'close'))._update_timesheets_for_public_holidays()
        return contracts

    def write(self, vals):
        res = super().write(vals)
        employees = self.mapped('employee_id')

        if vals.get('date_start') or vals.get('date_end'):

            company_ids = employees.mapped('company_id').ids
            domain = [
                ('company_id', 'in', company_ids),
                ('resource_id', '=', False),
            ]

            if vals.get('date_start'):
                domain = expression.AND([domain, [('date_from', '>=', vals['date_start'])]])
            if vals.get('date_end'):
                domain = expression.AND([domain, [('date_to', '<=', vals['date_end'])]])

            future_leaves = self.env['resource.calendar.leaves'].search(domain)
            if future_leaves:
                future_leaves._generate_public_time_off_timesheets(employees)

        if vals.get('state') in ('open', 'close'):
            self._update_timesheets_for_public_holidays()

        return res

    @api.model
    def _update_timesheets_for_public_holidays(self):
        """ Removes timesheet entries linked to public holidays if they fall outside
            an employee's contract period. """

        employees = self.mapped('employee_id')
        if not employees:
            return

        all_contracts_data = self.env['hr.contract'].sudo().search_read(
            [('employee_id', 'in', employees.ids),
            ('state', 'in', ['open', 'close'])],
            ['employee_id', 'date_start', 'date_end']
        )

        for emp_id, contracts in groupby(all_contracts_data, key=lambda c: c['employee_id'][0]):
            intervals = [
                (contract['date_start'], contract['date_end'] or None)
                for contract in contracts
            ]

        for emp in employees:
            domain = expression.AND([
                        [('employee_id', '=', emp.id)],
                        [('global_leave_id', '!=', False)],
                        expression.AND([
                            expression.OR([
                                [('date', '<', start)],
                                [('date', '>', end)]
                            ]) for start, end in intervals
                        ])
                    ])

        to_remove = self.env['account.analytic.line'].sudo().search(domain)

        if to_remove:
            to_remove.write({'global_leave_id': False})
            to_remove.unlink()
