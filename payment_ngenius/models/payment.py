# -*- coding: utf-8 -*-

import json

import logging
import requests
from werkzeug import urls

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirerNgenius(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('ngenius', 'Ngenius')])
    ngenius_api_key = fields.Char(string='Api Key', required_if_provider='ngenius', groups='base.group_user')
    ngenius_outlet_id = fields.Char(string='Outlet ID', required_if_provider='ngenius', groups='base.group_user')

    def _get_ngenius_urls(self, environment):
        """ Ngenius URLs"""
        if environment == 'prod':
            return {'ngenius_form_url': ' https://api-gateway.ngenius-payments.com'}
        else:
            return {'ngenius_form_url': 'https://api-gateway.sandbox.ngenius-payments.com'}

    def _ngenius_generate_access_token(self, url, api_key):
        headers = {
            'accept': "application/vnd.ni-identity.v1+json",
            'authorization': "Basic %s" % (api_key),
            'content-type': "application/vnd.ni-identity.v1+json"
        }
        response = requests.request("POST", url, headers=headers)
        access_token = response.json().get('access_token')
        return access_token

    def ngenius_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.get_base_url()
        ngenius = self.search([('provider', '=', 'ngenius')])
        base_payment_url = ngenius.ngenius_get_form_action_url()
        token_url = urls.url_join(base_payment_url, '/identity/auth/access-token')
        access_token = self._ngenius_generate_access_token(token_url, ngenius.ngenius_api_key)
        payload = {
            'action': 'SALE',
            'amount': {'currencyCode': 'AED', 'value': int(float(values['amount']) * 100)},
            'emailAddress': values.get('partner_email', ''),
            'merchantAttributes': {'cancelUrl': urls.url_join(base_url, '/payment/ngenius/cancel'),
                                   'redirectUrl': urls.url_join(base_url, '/payment/ngenius/return'),
                                   'cancelText': 'Back To Cart'},
            'merchantOrderReference': values['reference'],
            'billingAddress': {'firstName': values.get('partner_name', ''), 'lastname': values.get('partner_name', ''),
                               'address1': values.get('partner_phone', '')},
            'shippingAddress': {'firstName': values.get('partner_name', ''), 'lastname': values.get('partner_name', ''),
                                'address1': values.get('partner_phone', '')},
        }
        payload = json.dumps(payload)
        headers = {
            'accept': "application/vnd.ni-payment.v2+json",
            'content-type': "application/vnd.ni-payment.v2+json",
            'authorization': "Bearer %s" % (access_token)
        }
        order_url = urls.url_join(base_payment_url, '/transactions/outlets/%s/orders' % (ngenius.ngenius_outlet_id))

        response = requests.request("POST", order_url, data=payload, headers=headers)
        payment_url = response.json().get('_links').get('payment').get('href')
        payment_code = payment_url.split('?')[1].split('=')[1]
        final_payment_url = payment_url.split('?')[0]
        ngenius_values = dict(values, payment_url=final_payment_url, code=payment_code)
        return ngenius_values

    def ngenius_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_ngenius_urls(environment)['ngenius_form_url']


PaymentAcquirerNgenius()


class PaymentTransactionNgenius(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _ngenius_form_get_tx_from_data(self, data):
        reference = data.get('txnid')
        transaction = self.search([('reference', '=', reference)])
        return transaction

    def _ngenius_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        return invalid_parameters

    def _ngenius_form_validate(self, data):
        status = data.get('success')
        result = self.write({
            'acquirer_reference': data.get('authorizationCode', '') + '-'
                                  + data.get('rrn', '') + '-' + data.get('mid', ''),
            'date': fields.Datetime.now(),
        })
        if status:
            self._set_transaction_done()
        else:
            self._set_transaction_cancel()
        return result


PaymentTransactionNgenius()
