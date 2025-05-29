# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import controllers
from . import models


def post_init_hook(env):
    module = env["ir.module.module"].search([("name", "=", "website_payment")])
    env["website.technical.page"].Import_static_url(module_id=module.id)


def uninstall_hook(env):
    module = env["ir.module.module"].search([("name", "=", "website_payment")])
    env["website.technical.page"].sudo().search([("module_id", "=", module.id)]).unlink()
