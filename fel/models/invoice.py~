# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    uuid = fields.Char("Numero Autorizacion", readonly=True, states={'draft': [('readonly', False)]})
    serie = fields.Char("Serie", readonly=True, states={'draft': [('readonly', False)]})
    numero_dte = fields.Char("Numero DTE", readonly=True, states={'draft': [('readonly', False)]})
    dte_fecha = fields.Datetime("Fecha Autorizacion", readonly=True, states={'draft': [('readonly', False)]})
    cae = fields.Text("CAE", readonly=True, states={'draft': [('readonly', False)]})
    letras = fields.Text("Total Letras", readonly=True, states={'draft': [('readonly', False)]})
    tipo_f = fields.Selection([
        ('normal', 'Factura Normal'),
        ('cambiaria', 'Factura Cambiaria'),
        ('especial', 'Factura Especial'),        
        ], string='Tipo Factura', default='normal', readonly=True, states={'draft': [('readonly', False)]})
    regimen_antiguo = fields.Boolean(string="Nota de credito rebajando regimen antiguo", readonly=True, states={'draft': [('readonly', False)]}, default=False)
    nota_abono = fields.Boolean(string="Nota de Abono", readonly=True, states={'draft': [('readonly', False)]}, default=False)
    retencion = fields.Float(string="Retencion", readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def ver_factura(self):
        for invoice in self:
            uuid = invoice.uuid
            if not uuid:
                return False 
        sitio ={  'name'     : 'Ver Factura',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'new',
                  'url'      : 'https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid='+uuid
               }
        return sitio
        
AccountInvoice()

