# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = "stock.picking"

    factura_id = fields.Many2one('account.invoice', string='Factura')
    estado_factura = fields.Selection([
            ('draft','Borrador'),
            ('open', 'Abierto'),
            ('in_payment', 'En proceso de pago'),
            ('paid', 'Pagado'),
            ('cancel', 'Cancelado'),
        ], string='Estado Factura', related='factura_id.state')
    plazo_de_pago = fields.Many2one('account.payment.term', string='Plazo de Pago', related='sale_id.payment_term_id.name')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if self.origin:
           origin = self.origin
           origin = origin.split(",")
           for name in origin:
               inv = self.env["stock.picking"].search([("origin","=",name.strip())])
               if inv:
                  for picking in inv:
                      picking.write({'factura_id': self.id})
        return res

