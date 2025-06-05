import uuid
from odoo import models, api
from odoo.osv import expression


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _payment_request_from_kiosk(self, order):
        if self.use_payment_terminal != 'pine_labs':
            return super()._payment_request_from_kiosk(order)
        reference_prefix = order.config_id.name.replace(' ', '')
        data = {
            'amount': order.amount_total * 100,  # Pine Labs accepts amounts in paisa
            'transactionNumber': f'{reference_prefix}/{order.id}/{uuid.uuid4().hex}',
            'sequenceNumber': '1'
        }
        payment_response = self.pine_labs_make_payment_request(data)
        payment_response.update({
            'payment_ref_no': data.get('transactionNumber'),
        })
        return payment_response

    @api.model
    def _load_pos_self_data_domain(self, data):
        domain = super()._load_pos_self_data_domain(data)
        if data['pos.config'][0]['self_ordering_mode'] == 'kiosk':
            domain = expression.OR([[('use_payment_terminal', '=', 'pine_labs')], domain])
        return domain
