# -*- coding: utf-8 -*-
{
    'name': "Odoo UML",

    'summary': """
        Ingeniería Inversa con diagramas UML.""",

    'description': """
Ingeniería Inversa con diagramas UML
====================================

El presente es un módulo orientado a los desarrolladores sobre las tecnologías de Odoo, persigue el:

**Objetivo**: Representar las principales decisiones de diseño tomadas en el desarrollo de un módulo a través de
diferentes diagramas UML.

Principales Características
---------------------------

#.  Diagrama de Paquetes "Dependencias del módulo": provee una vista de las dependencias del módulo. Admite algunas
    configuraciones para facilitar la vizualización:
        *   Mostrar estructura interna, clases del modelo y vistas.
        *   Relaciones entre elementos internos (muestra las relaciones entre clases)
        *   Relaciones con elementos externos (muestra relaciones entre clases y vistas con otros módulos)
#.  Diagrama de Clases "Modelos": provee una vista de los datos gestionados en el módulo.

    """,

    'author': "Ing. Armando Robert Lobo",
    'website': "http://www.github.com/arobertlobo5",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/inherited_module_views.xml'
    ]
}
