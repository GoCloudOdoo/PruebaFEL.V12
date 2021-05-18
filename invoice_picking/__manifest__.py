# -*- encoding: UTF-8 -*-

{
    'name': 'Logistica factura-picking',
    'summary': """añade el numero de factura al picking""",
    'version': '12.0.1.0.',
    'author': 'Osmin Cano --> ocano@imeqmo.com',
    'maintainer': 'Osmin Cano',
    'website': 'http://imeqmo.com',
    'category': 'account',
    'depends': ['account', 'stock'],
    'license': 'AGPL-3',
    'data': [
                'views/picking_view.xml',
            ],
    'demo': [],
    'sequence': 12,
    'installable': True,
    'auto_install': False,
    'application': False,


}
