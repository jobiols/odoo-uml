# UML Reverse Engineering for Odoo.


[![Build Status](https://travis-ci.com/jobiols/odoo_uml.svg?branch=11.0)](https://travis-ci.com/jobiols/odoo_uml) [![Maintainability](https://api.codeclimate.com/v1/badges/cfc58a90c3f2423c2e11/maintainability)](https://codeclimate.com/github/jobiols/odoo_uml/maintainability) [![codecov](https://codecov.io/gh/jobiols/odoo-uml/branch/11.0/graph/badge.svg)](https://codecov.io/gh/jobiols/odoo-uml)

This is a developer-oriented module on odoo technologies, which aims to
assist in making the main design decisions thanks to different UML diagrams.

## Main Features

- Dependency view
  - Provides a view of module dependencies. It supports some configurations 
    to facilitate the visualization:
- Show internal structure, model classes and views.
- Relations between internal elements (shows the relations between classes)
- Relations with external elements (shows relations between classes and views with other modules)
- Class Diagram "Models": provides a view of the data managed in the module.

## Credits

This module is based on the work of Ing. Armando Robert Lobo http://www.github.com/arobertlobo5

## Requirements

### java

We need java installed on server to run plantuml

    # apt-get update && apt-get install default-jdk -y

## Warning

This module is still under development, is not fully functional yet. Stay tuned.
