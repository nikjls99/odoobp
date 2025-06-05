# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo.addons.hr_holidays.tests.test_global_leaves import TestGlobalLeaves
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestEmployeeContractTimesheets(TestGlobalLeaves):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.global_leaves = cls.env['resource.calendar.leaves'].create([{
                'name': 'Holiday March 5',
                'date_from': '2025-03-05 00:00:00',
                'date_to': '2025-03-05 23:59:59',
                'company_id': cls.company.id,
            }, {
                'name': 'Holiday April 10',
                'date_from': '2025-04-10 00:00:00',
                'date_to': '2025-04-10 23:59:59',
                'company_id': cls.company.id,
            }, {
                'name': 'Holiday May 7',
                'date_from': '2025-05-07 00:00:00',
                'date_to': '2025-05-07 23:59:59',
                'company_id': cls.company.id,
            },
        ])

        cls.contract = cls.env['hr.contract'].create({
            'name': 'Contract 1',
            'employee_id': cls.employee_emp.id,
            'date_start': datetime(2025, 4, 1),
            'date_end': datetime(2025, 4, 30),
            'resource_calendar_id': cls.calendar_1.id,
            'state': 'open',
            'wage': 1200,
        })

    def test_overlapping_contracts(self):
        """ Testing timesheet allocation for overlapping contracts, we should consider
            all timesheets created for the employee during the contract period"""
        self.env['hr.contract'].create({
            'name': 'March Contract',
            'employee_id': self.employee_emp.id,
            'date_start': datetime(2025, 3, 1),
            'date_end': datetime(2025, 3, 30),
            'resource_calendar_id': self.calendar_1.id,
            'state': 'close',
            'wage': 1000,
        })

        domain = [('employee_id', '=', self.employee_emp.id), ('global_leave_id', 'in', self.global_leaves.ids)]
        timesheets = self.env['account.analytic.line'].search_count(domain)
        self.assertEqual(timesheets, 1, "public holidays should have generated timesheets.")

    def test_no_contract_end_date(self):
        """Test if open-ended contract includes all future public holiday timesheets."""
        self.contract.write({
            'date_start': datetime(2025, 3, 1),
            'date_end': False,
        })

        domain = [('employee_id', '=', self.employee_emp.id), ('global_leave_id', 'in', self.global_leaves.ids)]
        timesheets = self.env['account.analytic.line'].search_count(domain)

        self.assertEqual(timesheets, 3, "All holidays should be counted as the contract is open-ended.")

    def test_contract_with_end_date(self):
        """Test that only holidays within contract period are considered."""
        self.contract.write({
            'date_start': datetime(2025, 4, 1),
            'date_end': datetime(2025, 4, 30),
        })

        domain = [('employee_id', '=', self.employee_emp.id), ('global_leave_id', 'in', self.global_leaves.ids)]
        timesheets = self.env['account.analytic.line'].search_count(domain)
        self.assertEqual(timesheets, 1, "Only the holiday on April 10 should be counted.")

    def test_extending_contract(self):
        """Test that extending a contract regenerates timesheets for future holidays."""
        self.contract.write({
            'date_start': datetime(2025, 3, 1),
            'date_end': datetime(2025, 3, 30),
        })

        domain = [('employee_id', '=', self.employee_emp.id), ('global_leave_id', 'in', self.global_leaves.ids)]
        initial_count = self.env['account.analytic.line'].search_count(domain)
        self.assertEqual(initial_count, 1, "The timesheets should be created for the holidays within the contract period.")

        # Extend the contract to include May
        self.contract.write({'date_end': datetime(2025, 5, 31)})
        updated_count = self.env['account.analytic.line'].search_count(domain)
        self.assertEqual(updated_count, 3, "The timesheets should be updated to include the new holiday.")

    def test_changing_employee_start_date(self):
        """Test timesheet behavior when employee start date changes."""
        self.contract.write({
            'date_start': datetime(2025, 4, 1),
            'date_end': datetime(2025, 5, 31),
        })

        domain = [('employee_id', '=', self.employee_emp.id), ('global_leave_id', 'in', self.global_leaves.ids)]
        original_count = self.env['account.analytic.line'].search_count(domain)
        self.assertEqual(original_count, 2, "Timesheets should be created for all holidays after the contract start date")

        self.contract.write({'date_start': datetime(2025, 3, 1)})
        updated_count = self.env['account.analytic.line'].search_count(domain)
        self.assertEqual(updated_count, 3, "Timesheets should be updated to include all holidays before the new start date")

    def test_create_public_holidays_inside_contract_period(self):
        """Test that public holidays are created correctly."""
        out_side_contract_leave = self.env['resource.calendar.leaves'].create([{
            'name': 'Holiday July 3',
            'date_from': '2025-07-03 00:00:00',
            'date_to': '2025-07-03 23:59:59',
            'calendar_id': self.calendar_1.id,
            'company_id': self.company.id,
        }])

        self.assertFalse(out_side_contract_leave.timesheet_ids, "Timesheets should not be created for outside the contract period")

        # setting the contract end date to False so that the contract is open-ended
        self.contract.write({'date_end': False})

        public_leave_2 = self.env['resource.calendar.leaves'].create([{
            'name': 'Holiday July 8',
            'date_from': '2025-07-08 00:00:00',
            'date_to': '2025-07-08 23:59:59',
            'calendar_id': self.calendar_1.id,
            'company_id': self.company.id,
        }])

        self.assertTrue(public_leave_2.timesheet_ids, "Timesheets should be created for the new public holiday")

    def test_contract_change_with_public_holidays(self):
        """When an employee logs a time-off entry for a past date, the corresponding timesheet should be generated
            using the working calendar from the contract that was active during that particular month."""
        self.env['hr.contract'].create({
            'name': 'March Contract',
            'employee_id': self.employee_emp.id,
            'date_start': datetime(2025, 3, 1),
            'date_end': datetime(2025, 3, 30),
            'resource_calendar_id': self.calendar_2.id,
            'state': 'close',
            'wage': 1000,
        })

        time_off_type = self.env['hr.leave.type'].create({
            'name': 'Time Off Test',
            'requires_allocation': 'no',
            'time_type': 'leave',
        })

        leave = self.env['hr.leave'].create([
            {
                'name': 'Time Off for March',
                'employee_id': self.employee_emp.id,
                'holiday_status_id': time_off_type.id,
                'request_date_from': datetime(2025, 3, 3),
                'request_date_to': datetime(2025, 3, 3),
            },
            {
                'name': 'Time Off for April',
                'employee_id': self.employee_emp.id,
                'holiday_status_id': time_off_type.id,
                'request_date_from': datetime(2025, 4, 8),
                'request_date_to': datetime(2025, 4, 8),
            }
        ])

        leave.action_approve()

        timesheet_1, timesheet_2 = self.env['account.analytic.line'].search([('employee_id', '=', self.employee_emp.id), ('holiday_id', 'in', leave.ids)])
        self.assertEqual(timesheet_1.unit_amount, 8, "The April leave should generate a timesheet for 8 hours")
        self.assertEqual(timesheet_2.unit_amount, 4, "The March leave should generate a timesheet for 4 hours")
