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
    'depends': ['base','sale','product','sale_stock'],

    # always loaded
    'data': [
        "wizard/di_grille_vente_wiz.xml",
        "wizard/di_consignes_wiz.xml",         
        "views/di_inherited_sale_view.xml",
        "views/di_inherited_account_view.xml",
        "views/di_stock_picking_views.xml",
        "views/di_stock_inventory_views.xml",
        "views/di_stock_production_views.xml",
        "static/di_webclient_templates.xml",
        "report/di_sale_report_templates.xml",
        "report/di_report_deliveryslip.xml",
        "report/di_report_stock_inventory.xml",
        "report/di_report_invoice.xml",
        "report/di_invoice_report.xml"
        # 'security/ir.model.access.csv',
      
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
}