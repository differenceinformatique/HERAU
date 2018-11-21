# -*- coding: utf-8 -*-
{
    'name': "difodoo_achats",

    'summary': """
        difodoo_achats""",

    'description': """
        Surcharge de Purchase, Purchase order, purchase order line
    """,

    'author': "Difference informatique",
    'website': "http://www.pole-erp-pgi.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'difodoo',
    'version': '0.1',

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
        'base_optional_quick_create',
        'eradicate_quick_create',
        'difodoo_fichiers_base',
        'difodoo_ventes',
#         'web_sheet_full_width',   # pas utile en enterprise
#         'prt_report_attachment_preview',
#         'report_intrastat',# le module n'existe plus en v12
        ],


    # always loaded
    'data': [        
        "views/di_inh_purchase_view.xml",
        "wizard/di_grille_achat_wiz.xml",        
        "report/di_purchase_quotation_templates.xml",
        "report/di_purchase_order_templates.xml"
#         "views/di_inherited_picking_view.xml",
#         "views/di_inherited_account_view.xml",
        # 'security/ir.model.access.csv',
      
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
}