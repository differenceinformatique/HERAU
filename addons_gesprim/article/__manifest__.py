# -*- coding: utf-8 -*-
{
    'name': "Article_gesprim",

    'summary': """
        Article""",

    'description': """
        Article
    """,

    'author': "Difference informatique",
    'website': "http://www.pole-erp-pgi.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Article',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','product'],

    # always loaded
    'data': [
        "views/di_inherited_product_view.xml",
        # 'security/ir.model.access.csv',
      
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
}