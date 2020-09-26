{
    'name': "Odoo UML",
    'version': '13.0.0.0.0',
    "development_status": "Alpha",  # "Alpha|Beta|Production/Stable|Mature"
    'summary': "Ingeniería Inversa con diagramas UML.",
    'author': "Ing. Jorge Obiols, Ing. Armando Robert Lobo",
    'website': "http://www.github.com/jobiols",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'depends': ['base'],
    'data': [
        'views/inherited_module_views.xml'
    ]
}
