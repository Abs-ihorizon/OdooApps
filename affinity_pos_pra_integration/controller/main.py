import json

import requests

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class PRAController(http.Controller):
    @http.route('/pos/pra/push', type='json', auth='user')
    def pra_push(self):
        config = request.env['pos.config'].sudo().search([('id', '=', request.params.get('config_id'))])
        if not config:
            return False

        if not (config.enable_pra_integration and config.pra_api_token and config.pra_api_url):
            return False

        partner = request.env['res.users'].sudo().search([('id', '=', request.params.get('partner_id'))], limit=1)
        payload = {
            'InvoiceNumber': request.params.get('invoice_number'),
            'POSID': config.pra_registration_number,
            'USIN': f'USIN-{request.params.get("order_id")}',
            'DateTime': str(request.params.get('date_order')),
            'BuyerPNTN': None,
            'BuyerCNIC': None,
            'BuyerName': partner.name if partner else None,
            'BuyerPhoneNumber': partner.phone if partner else None,
            'TotalBillAmount': 0.0,
            'TotalQuantity': 0,
            'TotalSaleValue': 0.0,
            'TotalTaxCharged': 0.0,
            'Discount': 0.0,
            'TotalDiscount': 0.0,
            'FurtherTax': 0.0,
            'PaymentMode': 1,
            'RefUSIN': None,
            'InvoiceType': 1,
            'Items': []
        }

        total_tax = 0.0
        total_discount = 0.0
        total_qty = 0
        total_sale_value = 0.0

        for line in request.params.get('lines', []):
            product = request.env['product.product'].sudo().browse(line.get('product_id'))

            price_unit = line.get('price_unit', 0.0)
            qty = line.get('qty', 0.0)
            tax_ids = line.get('tax_ids', [])
            tax_percent = 0.0

            if tax_ids:
                taxes = request.env['account.tax'].browse(tax_ids)
                tax_percent = sum(tax.amount for tax in taxes)
            discount_percent = line.get('discount', 0.0)

            original_total = price_unit * qty
            tax_amount = round(original_total * tax_percent / 100, 2)
            total_incl_tax = original_total + tax_amount
            discount_amount = round(total_incl_tax * discount_percent / 100, 2)
            total_amount = round(total_incl_tax - discount_amount, 2)
            tax_after_discount = round(tax_amount * (1 - discount_percent / 100), 2)
            sale_value_after_discount = round(total_amount - tax_after_discount, 2)

            total_discount += discount_amount
            total_tax += tax_after_discount
            total_qty += qty
            total_sale_value += sale_value_after_discount

            payload['Items'].append({
                'ItemCode': product.default_code or f'P{product.id}',
                'ItemName': product.name,
                'Quantity': qty,
                'PCTCode': '00000000',
                'TaxRate': round(tax_percent, 2),
                'SaleValue': sale_value_after_discount,
                'TotalAmount': total_amount,
                'TaxCharged': tax_after_discount,
                'Discount': discount_amount,
                'FurtherTax': 0.0,
                'InvoiceType': 1,
                'RefUSIN': None
            })

        payload['TotalTaxCharged'] = round(total_tax, 2)
        payload['TotalDiscount'] = round(total_discount, 2)
        payload['Discount'] = round(total_discount, 2)
        payload['TotalBillAmount'] = round(total_sale_value + total_tax, 2)
        payload['TotalQuantity'] = total_qty
        payload['TotalSaleValue'] = round(total_sale_value, 2)

        headers = {
            'Authorization': f'Bearer {config.pra_api_token}',
            'Content-Type': 'application/json'
        }

        try:
            res = requests.post(
                config.pra_api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=(10, 30)
            )
        except requests.exceptions.Timeout as e:
            raise UserError(f'Connection to PRA timed out: {e}')
        except requests.exceptions.RequestException as e:
            raise UserError(f'Connection to PRA failed. Error: {e}')
        except Exception as e:
            raise UserError(f'Connection to PRA failed. Error: {e}')

        try:
            res_json = res.json()
        except json.JSONDecodeError:
            res_json = None

        return {
            'status_code': res.status_code,
            'text': res.text,
            'InvoiceNumber': res_json.get('InvoiceNumber') if res_json else None,
            'pra_push_failed': res.status_code != 200,
        }
