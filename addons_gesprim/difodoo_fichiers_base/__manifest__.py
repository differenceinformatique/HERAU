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
    'depends': ['base','sale','product'],

    # always loaded
    'data': [
        "data/di_vues_defaut_article.xml",
        "views/di_inherited_product_view.xml",
        # 'security/ir.model.access.csv',
      
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
}