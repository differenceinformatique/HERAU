# -*- coding: utf-8 -*-
{
    'name': "difodoo_ventes",

    'summary': """
        difodoo_ventes""",

    'description': """
        Surcharge de Sale, Sale order, sale order line
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
#         'web_sheet_full_width',   # pas utile en enterprise
#         'prt_report_attachment_preview',
#         'report_intrastat',# le module n'existe plus en v12
        ],

    # always loaded
    'data': [
        "static/di_webclient_templates.xml",
        "wizard/di_grille_vente_wiz.xml",
        "wizard/di_transfertcompta_wiz.xml",
        "wizard/di_bord_trp_wiz.xml",
        "wizard/di_ctrl_trp_wiz.xml",
        "wizard/di_supp_lig_zero_wiz.xml",
        "wizard/di_cloturer_ventes_wiz.xml",
        "wizard/di_cloturer_lots_wiz.xml",
        "wizard/di_imprim_releves_wiz.xml",
        "wizard/di_livr_directe_wiz.xml",
        "wizard/di_regul_art_lot_wiz.xml",
        "wizard/di_facturation_cron_wiz.xml",
        "wizard/di_imp_manquants_wiz.xml",
        "wizard/di_ctrl_mont_fac.xml",                                                   
        "views/di_inherited_sale_view.xml",
        "views/di_inherited_account_view.xml",
        "views/di_stock_picking_views.xml",
        "views/di_stock_inventory_views.xml",                
        "report/di_sale_report_templates.xml",
        "report/di_report_deliveryslip.xml",
        "report/di_report_stock_inventory.xml",
        "report/di_report_stock_traceability.xml",
        "report/di_report_invoice.xml",
        "report/di_invoice_report.xml",
        "report/di_stock_report.xml",
        "report/di_resserre_ap_vente.xml",
        "report/di_report_bordtrp.xml",
        "report/di_report_ctrltrp.xml",
        "report/di_report_invoice_preimp.xml",
        "report/di_report_releves.xml",
        "report/di_imp_manquants.xml",
        "report/di_ctrl_mont_fac_report.xml",        
        "security/ir.model.access.csv"
              
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
    'installable': True,
}