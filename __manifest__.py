# Developed by Info"Lib. See LICENSE file for full copyright and licensing details.
{
    "name": "Point Of Sale",
    "version": "1.0",
    "author": "Aung Moe Wai",
    "summary": "Modifying the existing view to new design changing.",
    "description": " ",  # Non-empty string to avoid loading the README file.
    "depends": ["base", "web", "point_of_sale"],
    "data": [
        # 'views/assets_dinger.xml',
        'views/pos_payment_method_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        "point_of_sale._assets_pos": [
            '/pos_payment_dinger/static/src/prebuilt_popup/prebuilt_popup.js',
            '/pos_payment_dinger/static/src/prebuilt_popup/prebuilt_popup.xml',
            '/pos_payment_dinger/static/src/prebuilt_popup/prebuilt_popup.scss',
            '/pos_payment_dinger/static/src/app/overrides/models/models.js',
            '/pos_payment_dinger/static/src/app/payment_dinger.js',
            '/pos_payment_dinger/static/src/app/screens/payment_screen/payment_screen.xml',
            '/pos_payment_dinger/static/src/app/screens/payment_screen/payment_screen.scss',
            # '/pos_payment_dinger/static/src/lib/qrcode.min.js',
        ]

    },
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
