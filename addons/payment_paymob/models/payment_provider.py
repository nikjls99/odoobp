# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import pprint
from datetime import timedelta

import requests
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_paymob import const
from odoo.addons.payment_paymob.controllers.main import PaymobController


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('paymob', "Paymob")], ondelete={'paymob': 'set default'}
    )
    paymob_account_country_id = fields.Many2one(
        string="Paymob Country",
        help="The country of the Paymob account",
        comodel_name='res.country',
        inverse='_inverse_paymob_account_country',
        readonly=False,
        domain=f'''[("code", "in", {
            [config.get('country_code') for config in const.PAYMOB_CONFIG.values()]
        })]''',
        required_if_provider='paymob',
    )
    paymob_public_key = fields.Char(string="Paymob Public Key", required_if_provider='paymob')
    paymob_secret_key = fields.Char(
        string="Paymob Secret Key",
        required_if_provider='paymob',
        groups='base.group_system',
    )
    paymob_hmac_key = fields.Char(string="Paymob HMAC Key", required_if_provider='paymob')
    paymob_api_key = fields.Char(string="Paymob API Key", required_if_provider='paymob')
    paymob_access_token = fields.Char(groups='base.group_system')
    paymob_access_token_expiry = fields.Datetime(default='1970-01-01', groups='base.group_system')

    # ==== CONSTRAINT METHODS === #

    @api.constrains('available_currency_ids', 'state')
    def _limit_available_country_currency_ids(self):
        for provider in self.filtered(lambda p: p.code == 'paymob'):
            if len(provider.available_currency_ids) > 1 and provider.state != 'disabled':
                raise ValidationError(_("Only one currency can be selected by Paymob account."))
            if (
                provider.available_currency_ids and
                provider.available_currency_ids.name not in const.PAYMOB_CONFIG
            ):
                raise ValidationError(_("Only currencies supported by paymob can be selected"))

    # === COMPUTE METHODS === #

    def _inverse_paymob_account_country(self):
        for provider in self.filtered(lambda p: p.code == 'paymob'):
            provider.available_currency_ids = provider._get_paymob_account_currency()

    # === ACTION METHODS === #

    def _match_paymob_payment_methods(self, paymob_payment_methods):
        """ Paymob returns all available payment methods on the account, the payment methods are
        filtered depending on which ones are enabled on Odoo.

        :return: All the matched payment methods between paymob and Odoo
        :rtype: list
        """
        available_payment_method_codes = self.payment_method_ids.mapped('code')
        matched_payment_methods = list(filter(
            lambda pm: (
                const.PAYMOB_PAYMENT_METHODS_MAPPING.get(pm.get('gateway_type'))
                in available_payment_method_codes and (
                    not pm.get('integration_name') or not (
                        'apple' in pm.get('integration_name').lower() or
                        'google' in pm.get('integration_name').lower()
                    ))),
            # Apple Pay and Google Pay not supported for now because we don't have mobile only
            # payment methods.
            paymob_payment_methods
        ))

        return matched_payment_methods

    def action_sync_paymob_payment_methods(self):
        """ Synchronize the payment methods with the ones on the paymob portal, the integration_name
        needs to be set to be able to communicate with the `payment_method.code` when the intention
        is created.

        :return: Notification with the status of the action
        :rtype: dict
        """
        endpoint = '/api/ecommerce/integrations'
        is_live = self.state == 'enabled'
        params = {
            'is_plugin': 'true',
            'page_size': 500,
            'is_deprecated': 'false',
            'is_standalone': 'false',
            'is_live': json.dumps(is_live),
        }
        self.paymob_access_token = None
        paymob_payment_methods = self._paymob_make_request(
            endpoint,
            params=params,
            method='GET',
            is_client_request=False,
        )['results']
        matched_payment_methods = self._match_paymob_payment_methods(paymob_payment_methods)

        displayed_notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {},
        }
        if len(matched_payment_methods) < len(self.payment_method_ids):
            displayed_notification['params'].update({
                'title': _("Payment methods not found"),
                'message': _("Not all enabled payment methods were found on your account"),
            })
            return displayed_notification

        base_url = self.get_base_url()
        redirect_url = urls.url_join(base_url, PaymobController._return_url)
        webhook_url = urls.url_join(base_url, PaymobController._webhook_url)

        # Update the name and return urls of payment methods on the paymob portal
        for payment_method in matched_payment_methods:
            payment_method_code = const.PAYMOB_PAYMENT_METHODS_MAPPING[
                payment_method.get('gateway_type')
            ]
            if payment_method_code == 'card' and payment_method.get('installments'):
                installment_payment_method = self.env['payment.method'].search(
                    [('code', '=', 'installments')], limit=1
                )
                if not installment_payment_method:
                    continue
                payment_method_code = 'installments'
            live_tag = 'live' if is_live else 'test'
            data = {
                'integration_name': payment_method_code + live_tag,
                'transaction_processed_callback': webhook_url,
                'transaction_response_callback': redirect_url,
            }
            self._paymob_make_request(
                f'{endpoint}/{payment_method["id"]}',
                method='PUT',
                data=data,
                is_client_request=False,
            )
        # All payment methods were updated successfully
        displayed_notification['params'].update({
            'type': 'success',
            'title': _("Successfully synchronized with Paymob"),
            'message': _("Payment methods have been successfully set up!"),
        })
        return displayed_notification

    # === BUSINESS METHODS === #

    def _paymob_make_request(
        self, endpoint, data=None, method='POST', is_refresh_token_request=False,
        is_client_request=True, params=None,
    ):
        """ Make a request to Paymob API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict data: The string payload of the request.
        :param bool is_refresh_token_request: Whether the request is for refreshing the access
                                              token.
        :param bool is_client_request: Whether the request is a client request or a backend request,
                                       it will depend what auth will be sent the access token
                                       generated from the api_key or the secret_key.
        :return: The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        url = self._paymob_get_api_url() + endpoint
        auth = ''
        if not is_refresh_token_request and is_client_request:
            auth = payment_utils.normalize_text(self.paymob_secret_key)
        elif not is_refresh_token_request:
            auth = self._paymob_fetch_access_token()
        headers = {'Authorization': f'Bearer {auth}'}

        try:
            response = requests.request(
                method, url, headers=headers, params=params, json=data, timeout=10
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                # Paymob errors https://developers.paymob.com/egypt/error-codes
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
                )
                msg = response.text
                error_msg = _(
                    "%(provider)s The communication with the API failed. Details: %(msg)s",
                    provider="Paymob:",
                    msg=msg,
                )
                if "This field may not be blank" in msg:
                    missing_fields = ", ".join(json.loads(msg).get('billing_data', {}).keys())
                    error_msg = _(
                        "%(provider)s The following fields must be filled: %(fields)s",
                        provider="Paymob:",
                        fields=missing_fields,
                    )
                raise ValidationError(error_msg)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(_("%s Could not establish the connection to the API.", "Paymob:"))
        return response.json()

    # === BUSINESS METHODS - GETTERS === #

    def _get_paymob_account_currency(self):
        """ Get the currency code according to the provider country.

        :return: The paymob account currency
        :rtype: res.currency
        """
        currency = [
            currency for currency, currency_config
            in const.PAYMOB_CONFIG.items()
            if currency_config['country_code'] == self.paymob_account_country_id.code
        ]
        Currency = self.env['res.currency']
        if currency:
            return Currency.with_context(
                    active_test=False,
                ).search([('name', '=', currency[0])], limit=1)
        return Currency

    def _paymob_get_api_url(self):
        """ Get the API URL according to the provider country.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        api_prefix = const.PAYMOB_CONFIG[self.available_currency_ids.name]['api_prefix']
        url = f"https://{api_prefix}.paymob.com"
        return url

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'paymob':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _paymob_fetch_access_token(self):
        """ Generate a new access token if it's expired, otherwise return the existing access token.
        Paymob's access tokens expire every hour.

        :return: A valid access token.
        :rtype: str
        :raise ValidationError: If the access token can not be fetched.
        """
        if not self.paymob_access_token or fields.Datetime.now() > self.paymob_access_token_expiry:
            response_content = self._paymob_make_request(
                '/api/auth/tokens',
                data={'api_key': self.paymob_api_key},
                is_refresh_token_request=True,
                is_client_request=False,
            )
            access_token = response_content['token']
            if not access_token:
                raise ValidationError(
                    _("%(provider)s Could not generate a new access token.", provider="Paymob:")
                )
            self.write({
                'paymob_access_token': access_token,
                'paymob_access_token_expiry': fields.Datetime.now() + timedelta(minutes=55),
            })
        return self.paymob_access_token
