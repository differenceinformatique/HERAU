# -*- coding: utf-8 -*-
{
    'name': "Gesprim",

    'summary': """
        Gesprim""",

    'description': """
        Gesprim description
    """,

    'author': "Difference informatique",
    'website': "http://www.pole-erp-pgi.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Gesprim',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','product','article','web_sheet_full_width'],

    # always loaded
    'data': [
       
        # 'security/ir.model.access.csv',
      
    ],
    # only loaded in demonstration mode
    'demo': [
       
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}