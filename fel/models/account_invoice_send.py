# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen
import requests
import base64

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.composer_id:
            self.composer_id.template_id = self.template_id.id
            self.composer_id.onchange_template_id_wrapper()
            ids = self.adjuntar_fel()
            self.attachment_ids = [(6,0,[ids])]

    @api.multi
    def _print_document(self):
        """ to override for each type of models that will use this composer."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': 'FEL',
            'url': '/web/content/%s?download=true' % (self.attachment_ids.id),
        }

    @api.multi
    def adjuntar_fel(self):
        invoice = self.env['account.invoice'].search([('id', '=', self.invoice_ids.id)], limit=1)
        url = 'https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid='+invoice.uuid
        myfile = requests.get(url)
        var = open('FACTURA-FEL.pdf', 'wb').write(myfile.content)
        doc = open('FACTURA-FEL.pdf', 'rb')
        docs = base64.encodebytes(doc.read())
        ids = self.env['ir.attachment'].create({'name': 'FEL.pdf',
                                                'mimetype': 'application/pdf',
                                                'datas_fname': 'FEL.pdf',
                                                'datas': docs})

        return ids.id
