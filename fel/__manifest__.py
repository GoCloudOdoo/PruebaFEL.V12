# -*- encoding: UTF-8 -*-

{
    'name': 'Factura Electronica',
    'summary': """Web service integrado con Infile S.A""",
    'version': '12.0.1.0.',
    'description': """Factura Electronica para Guatemala.""",
    'author': 'Osmin Cano --> osmincano@gmail.com',
    'maintainer': 'Osmin Cano',
    'website': 'http://odoo.com',
    'category': 'account',
    'depends': ['account'],
    'license': 'AGPL-3',
    'data': [
                'security/ir.model.access.csv',
                'views/api_view.xml',
                'views/account_journal_view.xml',
                'views/account_invoice_view.xml',
            ],
    'demo': [],
    'sequence': 1,
    'installable': True,
    'auto_install': False,
    'application': False,


}
