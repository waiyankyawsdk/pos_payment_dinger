from odoo import http
from odoo.http import request

class PosOrderController(http.Controller):

    # Here dinger make return url and need to modify prebuilt_popup of qr image with check mark
    @http.route('/pos/order/payment_methods', type='json', auth='user',csrf=False, methods=["GET"])
    def render_order_types(self):
        payment_methods = request.env['pos.payment.method'].sudo().search_read(
            [('parent_method_id', '!=', False)], ['id', 'name']
        )
        return {'payment_methods': payment_methods}  #Return JSON