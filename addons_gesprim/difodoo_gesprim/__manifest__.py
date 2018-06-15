# -*- coding: utf-8 -*-
{
    'name': "difodoo_gesprim",

    'summary': """
        difodoo_gesprim""",

    'description': """
        Gesprim description
    """,

    'author': "Difference informatique",
    'website': "http://www.pole-erp-pgi.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'difodoo',
    'version': '0.1',

    # any module necessary for this one to work correctly
        # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'sale_stock',
        'sale_margin',
        'purchase',
        'product',
        'difodoo_fichiers_base',
        'difodoo_ventes',
        'difodoo_achats',
        'web_sheet_full_width'
        , 'report_intrastat'
        , 'l10n_fr_sale_closing',
        'base_optional_quick_create',
        'eradicate_quick_create',
        ],

    # always loaded
    'data': [
        "gesprim_menu.xml",
        
       
        # 'security/ir.model.access.csv',
      
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
