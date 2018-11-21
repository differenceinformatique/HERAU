# -*- coding: utf-8 -*-
{
    'name': "difodoo_fichiers_base",

    'summary': """
        difodoo_fichiers_base""",

    'description': """
        Surcharge des fichiers de base
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
#         'web_sheet_full_width',   # pas utile en enterprise
#         'prt_report_attachment_preview',
#         'report_intrastat',# le module n'existe plus en v12
        ],


    # always loaded
    'data': [
        "views/di_printer_views.xml",
        "views/di_label_model_views.xml",
        "views/di_inh_product_view.xml",
        "views/di_inh_res_partner_view.xml",        
        "views/di_tables_view.xml",
		"views/di_ref_art_tiers_view.xml",
        "views/di_inh_product_view.xml",
        "views/di_inh_delivery_view.xml",
        "views/di_livrebord_view.xml",       
        "report/di_impression_tarifs.xml",
        "report/di_tarifs_report.xml",
        "report/di_etiquettes.xml",
        "wizard/di_wiz_referencer_article.xml",
        "wizard/di_product_pack_wizard.xml",
        "wizard/di_imprim_tar_wizard.xml",
        "wizard/di_saisie_code_wizard.xml",
        "wizard/di_generer_tarifs_wizard.xml",
        "wizard/di_generer_couts_wizard.xml",
        "wizard/di_popup_wizard.xml",
        "wizard/di_maj_codedest.xml",
        "wizard/di_etiquette_lot_wizard.xml",
        "security/ir.model.access.csv",
        "data/di_param_data.xml"              
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
}