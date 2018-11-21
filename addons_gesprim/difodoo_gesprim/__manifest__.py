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
        'product',
        'sale',
        'sale_management',
        'stock',
        'sale_stock',
        'delivery',                     
        'purchase',
        'sale_margin',
        'account',                           
        'l10n_fr_sale_closing',
        'difodoo_fichiers_base',
        'difodoo_ventes',
        'difodoo_achats',                             
        'base_optional_quick_create',
        'eradicate_quick_create',
#         'web_sheet_full_width',   # pas utile en enterprise
#         'prt_report_attachment_preview',
#         'report_intrastat',# le module n'existe plus en v12
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
