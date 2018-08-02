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
    'depends': ['base','purchase','product','difodoo_ventes'],

    # always loaded
    'data': [        
        "views/di_inh_purchase_view.xml",
        "views/di_apportprod_view.xml",
        "wizard/di_valider_apport_wizard.xml",
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