# Developed by Info"Lib. See LICENSE file for full copyright and licensing details.
{
    "name": "Point Of Sale",
    "version": "1.0",
    "author": "SMEI",
    "summary": "Integrate Dinger QR payment with Odoo POS for seamless Myanmar digital payments.",
    "description": "This module enables Odoo POS to accept payments via Dinger QR, allowing customers to pay easily using Myanmar digital wallets and banks. It provides a smooth integration for QR-based transactions, automatic payment status tracking, and is designed for businesses operating in Myanmar.",
    "depends": ["base", "web", "point_of_sale"],
    "data": [
        'views/pos_payment_method_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_payment_status_views.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        "point_of_sale._assets_pos": [
            '/pos_payment_dinger/static/src/prebuilt_popup/prebuilt_popup.xml',
            '/pos_payment_dinger/static/src/prebuilt_popup/prebuilt_popup.js',
            '/pos_payment_dinger/static/src/prebuilt_popup/prebuilt_popup.scss',
            '/pos_payment_dinger/static/src/app/overrides/models/models.js',
            '/pos_payment_dinger/static/src/app/payment_dinger.js',
            '/pos_payment_dinger/static/src/app/screens/payment_screen/payment_screen.xml',
            '/pos_payment_dinger/static/src/app/screens/payment_screen/payment_screen.scss',
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
