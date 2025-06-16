# Developed by Info"Lib. See LICENSE file for full copyright and licensing details.
{
    "name": "Point Of Sale",
    "version": "1.0",
    "author": "Aung Moe Wai",
    "summary": "Modifying the existing view to new design changing.",
    "description": "To serve an online payment prvider in pos to use myanmar banking with QR only",
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
