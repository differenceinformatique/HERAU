# -*- coding: utf-8 -*-
{
    'name': "difodoo_producteurs",

    'summary': """
        difodoo_producteurs""",

    'description': """
        Surcharge de difodoo pour intégrer les besoins producteurs
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
        'sale',
        'sale_stock',
        'sale_margin',
        'purchase',
        'product',
        'difodoo_fichiers_base',
        'difodoo_ventes',
        'difodoo_achats',
        'difodoo_gesprim',
#         'web_sheet_full_width'
#         , 'report_intrastat'
        'l10n_fr_sale_closing',
        'base_optional_quick_create',
        'eradicate_quick_create',
        ],

    # always loaded
    'data': [
        "views/di_apportprod_view.xml",
        "views/di_consignes_wiz.xml",
        "views/di_inh_product_view.xml",
        "views/di_inh_purchase_view.xml",
        "views/di_inh_res_partner_view.xml",
        "views/di_payer_com_wizard.xml",
        "views/di_ref_art_tiers_view.xml",
        "views/di_stock_inventory_views.xml",
        "views/di_stock_picking_views.xml",
        "views/di_stock_production_views.xml",
        "views/di_tables_view.xml",
        "views/di_valider_apport_wizard.xml",  
        "gesprim_producteurs_menu.xml",                    
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
}