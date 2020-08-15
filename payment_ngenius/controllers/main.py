# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request
import requests
_logger = logging.getLogger(__name__)


class NgeniusController(http.Controller):
    @http.route(['/payment/ngenius/return', '/payment/ngenius/cancel'], type='http', auth='public', csrf=False)
    def ngenius_return(self, **post):
        """ Ngenius."""
        ref=post.get('ref')
        auth_response={}
        txnid=''
        if ref:
            ngenius = request.env['payment.acquirer'].sudo().search([('provider', '=', 'ngenius')])
            base_payment_url = ngenius.ngenius_get_form_action_url()
            token_url = werkzeug.urls.url_join(base_payment_url, '/identity/auth/access-token')
            access_token = ngenius._ngenius_generate_access_token(token_url, ngenius.ngenius_api_key)
            url = "https://api-gateway.sandbox.ngenius-payments.com/transactions/outlets/%s/orders/%s" % (
                ngenius.ngenius_outlet_id,ref)
            headers = {'accept': 'application/vnd.ni-payment.v2+json',
                       'content-type': "application/vnd.ni-payment.v2+json",
                       'authorization': "Bearer %s" % (access_token)
                       }
            response = requests.request("GET", url, headers=headers)
            auth_response=response.json().get('_embedded').get('payment')[0].get('authResponse',{})
            txnid=response.json().get('merchantOrderReference','')
        _logger.info(
            'Ngenius: entering form_feedback with post data %s', pprint.pformat(post))
        auth_response.update({
            'txnid': txnid
        })
        if auth_response:

            request.env['payment.transaction'].sudo().form_feedback(auth_response, 'ngenius')
        return werkzeug.utils.redirect('/payment/process')
