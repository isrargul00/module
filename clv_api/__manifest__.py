# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "Warehouse 15 for Odoo (barcode mobile app)",
    'author': "Cleverence",
    'summary': "Mobile Warehouse Automation Kit",
    'website': "https://www.cleverence.com/solutions/welcome-wms-odoo-owners/",
    'category': 'Inventory',
    'version': '17.0.1.218',
    'depends': ['stock'],
    'data': [
        'views/clv_stock_picking_view.xml',
        'views/clv_api_settings.xml'
    ],
    'images': ['static/images/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_install_hook',
    'uninstall_hook': 'pre_uninstall_hook'
}
