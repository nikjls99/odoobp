# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from . import models
from . import wizard


def _post_init_hook(env):
    env['account.journal'].search([('type', '=', 'bank')])._create_check_sequence()

    for company in env['res.company'].search([]):
        env['account.payment.method'].create({
            'name': 'Checks',
            'code': 'check_printing',
            'payment_type': 'outbound',
            'company_id': company.id,
        })
