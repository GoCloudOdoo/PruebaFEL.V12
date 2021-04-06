# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class APIModelConfiguration(models.Model):
    _name = "api.data.configuration"
    _description = """Configuration FEL"""

    client_code = fields.Char(string="Client Code", required=False, default="56515219")
    user_code = fields.Char(string="User Code", required=False, default="ADMIN")
    vendor_nit = fields.Char(string="Vendor NIT", required=False, default="56515219")
    eface_store_number = fields.Char(string="EFACE store number", default="2")
    gov_auth_number = fields.Char(string="Gov authorization number", default="2017-5-1081890-481")
    company_id = fields.Many2one('res.company', 'Empresa')
    user = fields.Char(string="Usuario", required=True)
    key_firma = fields.Char(string="Llave Firma xml", required=True)
    url_firma = fields.Char(string="URL Firma xml", required=True)
    key_certificado = fields.Char(string="Llave Certificacion", required=True)
    url_certificado = fields.Char(string="URL Certificacion", required=True)
    url_anulacion = fields.Char(string="URL Anulacion", required=True)
    code_est = fields.Char(string="Codigo Establecimiento", required=True)


class ResCompany(models.Model):
    _inherit = "res.company"

    tipo = fields.Char(string="Tipo", default="1")
    codigo = fields.Char(string="Codigo", default="2")
    codigo_consignatario = fields.Char(string="Codigo de Consignatario o Destinatario")
    codigo_exportador = fields.Char(string="Codigo Exportador")

class ResPartner(models.Model):
    _inherit = "res.partner"

    codigo_comprador = fields.Char(string="Codigo Comprador")
    tax_partner = fields.Boolean('No Incluye IVA', required=False, help="Marque si algunos productos a facturar no incluye IVA")

class ProductTemplate(models.Model):
    _inherit = "product.template"

    tax_product = fields.Boolean('No Incluye IVA', required=False, help="Marque si el producto no incluye IVA")

