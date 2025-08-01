# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.json import scriptsafe as json_safe

from odoo.addons.account_payment.controllers import portal as account_payment_portal
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal


class PaymentPortal(payment_portal.PaymentPortal):
    @http.route('/donation/pay', type='http', methods=['GET', 'POST'], auth='public', website=True, sitemap=False)
    def donation_pay(self, **kwargs):
        """ Behaves like PaymentPortal.payment_pay but for donation

        :param dict kwargs: As the parameters of in payment_pay, with the additional:
            - str donation_options: The options settled in the donation snippet
            - str donation_descriptions: The descriptions for all prefilled amounts
        :return: The rendered donation form
        :rtype: str
        :raise: werkzeug.exceptions.NotFound if the access token is invalid
        """
        kwargs['is_donation'] = True
        kwargs['currency_id'] = self._cast_as_int(kwargs.get('currency_id')) or request.env.company.currency_id.id
        kwargs['amount'] = self._cast_as_float(kwargs.get('amount')) or 25.0
        kwargs['donation_options'] = kwargs.get('donation_options', json_safe.dumps(dict(customAmount="freeAmount")))

        if request.env.user._is_public():
            kwargs['partner_id'] = request.env.user.partner_id.id
            kwargs['access_token'] = payment_utils.generate_access_token(kwargs['partner_id'], kwargs['amount'], kwargs['currency_id'])

        return self.payment_pay(**kwargs)

    @http.route('/donation/transaction/<minimum_amount>', type='json', auth='public', website=True, sitemap=False)
    def donation_transaction(self, amount, currency_id, partner_id, access_token, minimum_amount=0, **kwargs):
        if float(amount) < float(minimum_amount):
            raise ValidationError(_('Donation amount must be at least %.2f.', float(minimum_amount)))
        use_public_partner = request.env.user._is_public() or not partner_id
        if use_public_partner:
            details = kwargs['partner_details']
            if not details.get('name'):
                raise ValidationError(_('Name is required.'))
            if not details.get('email'):
                raise ValidationError(_('Email is required.'))
            if not details.get('country_id'):
                raise ValidationError(_('Country is required.'))
            partner_id = request.website.user_id.partner_id.id
            del kwargs['partner_details']
        else:
            partner_id = request.env.user.partner_id.id

        self._validate_transaction_kwargs(kwargs, additional_allowed_keys=(
            'donation_comment', 'donation_recipient_email', 'partner_details', 'reference_prefix'
        ))
        if use_public_partner:
            kwargs['custom_create_values'] = {'tokenize': False}
        tx_sudo = self._create_transaction(
            amount=amount, currency_id=currency_id, partner_id=partner_id, **kwargs
        )
        tx_sudo.is_donation = True
        if use_public_partner:
            tx_sudo.update({
                'partner_name': details['name'],
                'partner_email': details['email'],
                'partner_country_id': int(details['country_id']),
            })
        elif not tx_sudo.partner_country_id:
            tx_sudo.partner_country_id = int(kwargs['partner_details']['country_id'])
        # the user can change the donation amount on the payment page,
        # therefor we need to recompute the access_token
        access_token = payment_utils.generate_access_token(
            tx_sudo.partner_id.id, tx_sudo.amount, tx_sudo.currency_id.id
        )
        self._update_landing_route(tx_sudo, access_token)

        # Send a notification to warn that a donation has been made
        recipient_email = kwargs['donation_recipient_email']
        comment = kwargs['donation_comment']
        tx_sudo._send_donation_email(True, comment, recipient_email)

        return tx_sudo._get_processing_values()

    def _get_extra_payment_form_values(
        self, donation_options=None, donation_descriptions=None, is_donation=False, **kwargs
    ):
        rendering_context = super()._get_extra_payment_form_values(
            donation_options=donation_options,
            donation_descriptions=donation_descriptions,
            is_donation=is_donation,
            **kwargs,
        )
        if is_donation:
            user_sudo = request.env.user
            logged_in = not user_sudo._is_public()
            # If the user is logged in, take their partner rather than the partner set in the params.
            # This is something that we want, since security rules are based on the partner, and created
            # tokens should not be assigned to the public user. This should have no impact on the
            # transaction itself besides making reconciliation possibly more difficult (e.g. The
            # transaction and invoice partners are different).
            partner_sudo = user_sudo.partner_id
            partner_details = {}
            if logged_in:
                partner_details = {
                    'name': partner_sudo.name,
                    'email': partner_sudo.email,
                    'country_id': partner_sudo.country_id.id,
                }

            countries = request.env['res.country'].sudo().search([])
            descriptions = request.httprequest.form.getlist('donation_descriptions')

            donation_options = json_safe.loads(donation_options) if donation_options else {}
            donation_amounts = json_safe.loads(donation_options.get('donationAmounts', '[]'))

            rendering_context.update({
                'is_donation': True,
                'partner': partner_sudo,
                'submit_button_label': _("Donate"),
                'transaction_route': '/donation/transaction/%s' % donation_options.get('minimumAmount', 0),
                'partner_details': partner_details,
                'error': {},
                'countries': countries,
                'donation_options': donation_options,
                'donation_amounts': donation_amounts,
                'donation_descriptions': descriptions,
            })
        return rendering_context

    def _get_payment_page_template_xmlid(self, **kwargs):
        if kwargs.get('is_donation'):
            return 'website_payment.donation_pay'
        return super()._get_payment_page_template_xmlid(**kwargs)

    @staticmethod
    def _compute_show_tokenize_input_mapping(providers_sudo, **kwargs):
        """ Override of `payment` to hide the "Save my payment details" input in the payment form
        when its a donation and user is not logged in.

        :param payment.provider providers_sudo: The providers for which to determine whether the
                                                tokenization input should be shown or not.
        :param dict kwargs: The optional data passed to the helper methods.
        :return: The mapping of the computed value for each provider id.
        :rtype: dict
        """
        res = super(PaymentPortal, PaymentPortal)._compute_show_tokenize_input_mapping(
            providers_sudo, **kwargs
        )
        if kwargs.get('is_donation') and request.env.user._is_public():
            for provider_sudo in providers_sudo:
                res[provider_sudo.id] = False
        return res


class PortalAccount(account_payment_portal.PortalAccount):
    def _invoice_get_page_view_values(self, *args, **kwargs):
        """Override of `account_payment` to make the providers filtering website-aware."""
        return super()._invoice_get_page_view_values(*args, website_id=request.website.id, **kwargs)
