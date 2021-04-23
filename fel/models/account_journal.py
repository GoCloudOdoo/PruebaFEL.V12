# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountJournal(models.Model):
        _inherit = "account.journal"

        is_eface = fields.Boolean('Factura Electronica', required=False, help="Marque si este diario utilizara emision de facturas electronica")
        code_est = fields.Char(string="Codigo Establecimiento", required=True, default="0")
        
        @api.onchange('is_eface')
        def _onchange_eface(self):
            if self.is_eface == True:
               api = self.env['api.data.configuration'].search([('id', '>', 0)], limit=1)
               if not api:
                   raise UserError(_("Antes de marcar la casilla Factura Electronica, debe existir al menos una configuración FEL."))        

AccountJournal()

