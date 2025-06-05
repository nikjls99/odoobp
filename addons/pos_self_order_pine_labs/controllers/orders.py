from odoo import http
from odoo.addons.pos_self_order.controllers.orders import PosSelfOrderController
from werkzeug.exceptions import NotFound


class PosSelfOrderPineLabsController(PosSelfOrderController):
    @http.route('/pos-self-order/pine-labs-fetch-payment-status/', auth='public', type='jsonrpc', website=True)
    def pine_labs_payment_status(self, access_token, order_id, payment_data, payment_method_id):
        pos_config = self._verify_pos_config(access_token)
        order = pos_config.env['pos.order'].search([('id', '=', order_id), ('config_id', '=', pos_config.id)], limit=1)

        if not order:
            raise NotFound()

        payment_method = pos_config.env['pos.payment.method'].browse(payment_method_id)
        pine_labs_status_response = payment_method.pine_labs_fetch_payment_status(payment_data)
        payment_status = pine_labs_status_response.get('status')
        if payment_status == "TXN APPROVED":
            data = pine_labs_status_response.get('data')
            order.add_payment({
                'amount': order.amount_total,
                'payment_method_id': payment_method.id,
                'cardholder_name': data.get('Card Holder Name'),
                'transaction_id': data.get('TransactionLogId'),
                'payment_status': 'done',
                'pos_order_id': order.id,
                'payment_method_authcode': data.get('ApprovalCode'),
                'card_brand': data.get('Card Type'),
                'payment_method_issuer_bank': data.get('Acquirer Name'),
                'card_no': data.get('Card Number') and data.get('Card Number')[-4:],
                'payment_method_payment_mode': data.get('PaymentMode'),
                'payment_ref_no': payment_data.get('payment_ref_no'),
                'pine_labs_plutus_transaction_ref': pine_labs_status_response.get('plutusTransactionReferenceID'),
            })
            order.action_pos_order_paid()
            self.call_bus_service(order, payment_result='Success')
        elif pine_labs_status_response.get('error') or not payment_status:
            self.call_bus_service(order, payment_result='fail')
        return pine_labs_status_response

    @http.route("/pos-self-order/pine-labs-cancel-transaction/", auth="public", type="jsonrpc", website=True)
    def pine_labs_cancel_status(self, access_token, order_id, payment_data, payment_method_id):
        pos_config = self._verify_pos_config(access_token)
        order = pos_config.env['pos.order'].search([('id', '=', order_id), ('config_id', '=', pos_config.id)], limit=1)

        if not order:
            raise NotFound()

        payment_data.update({
            'amount': order.amount_total * 100,  # Pine Labs accepts amounts in paisa
        })
        payment_method = pos_config.env['pos.payment.method'].browse(payment_method_id)
        pine_labs_cancel_response = payment_method.pine_labs_cancel_payment_request(payment_data)
        cancel_status = pine_labs_cancel_response.get('notification')
        if cancel_status:
            self.call_bus_service(order, payment_result='fail')
        return pine_labs_cancel_response

    def call_bus_service(self, order, payment_result):
        order.config_id._notify('PAYMENT_STATUS', {
            'payment_result': payment_result,
            'data': {
                'pos.order': order.read(order._load_pos_self_data_fields(order.config_id.id), load=False),
                'pos.order.line': order.lines.read(order._load_pos_self_data_fields(order.config_id.id), load=False),
            }
        })
