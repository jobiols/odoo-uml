{
    'name': "Odoo UML",
    "development_status": "Alpha",  # "Alpha|Beta|Production/Stable|Mature"
    'summary': "Ingeniería Inversa con diagramas UML.",
    'author': "Ing. Armando Robert Lobo",
    'website': "http://www.github.com/arobertlobo5",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    
    'category': 'Tools',
    'version': '11.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/inherited_module_views.xml'
    ]
}
