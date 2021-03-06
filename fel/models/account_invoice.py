# -*- encoding: UTF-8 -*-

from odoo import api, models, fields, _
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta
import datetime as dt
import dateutil.parser
from dateutil.tz import gettz
from . import credit_note, invoice_cancel, nota_abono
import json
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
import base64
import requests
from json import loads
from random import randint
import re

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    uuid = fields.Char("Numero Autorizacion", readonly=True, states={'draft': [('readonly', False)]})
    serie = fields.Char("Serie", readonly=True, states={'draft': [('readonly', False)]})
    numero_dte = fields.Char("Numero DTE", readonly=True, states={'draft': [('readonly', False)]})
    dte_fecha = fields.Datetime("Fecha Autorizacion", readonly=True, states={'draft': [('readonly', False)]})
    cae = fields.Text("CAE", readonly=True, states={'draft': [('readonly', False)]})
    letras = fields.Text("Total Letras", readonly=True, states={'draft': [('readonly', False)]})
    tipo_f = fields.Selection([
        ('normal', 'Factura Normal'),
        ('cambiaria', 'Factura Cambiaria'),
        ], string='Tipo Factura', default='normal', readonly=True, states={'draft': [('readonly', False)]})
    regimen_antiguo = fields.Boolean(string="Nota de credito rebajando regimen antiguo", readonly=True, states={'draft': [('readonly', False)]}, default=False)
    nota_abono = fields.Boolean(string="Nota de Abono", readonly=True, states={'draft': [('readonly', False)]}, default=False)
    retencion = fields.Float(string="Retencion", readonly=True, states={'draft': [('readonly', False)]})
    tipo_s = fields.Selection([
        ('especial', 'Factura Especial'),
        ], string='Tipo Factura', readonly=True, states={'draft': [('readonly', False)]})

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

    @api.multi
    def action_invoice_open(self):
        if self.journal_id.is_eface == False:
           return super(AccountInvoice, self).action_invoice_open()
        res = super(AccountInvoice, self).action_invoice_open()
        if self.type == "out_invoice":
           if self.tipo_f == 'normal':
              xml_data = self.set_data_for_invoice()
              self.letras = self.l10n_gt_edi_amount_to_text()
              uuid, serie, numero_dte, dte_fecha =self.send_data_api(xml_data)
              message = _("Facturacion Electronica %s: Serie %s  Numero %s") % (self.tipo_f, serie, numero_dte)
              self.message_post(body=message)
              self.uuid = uuid
              self.serie = serie
              self.numero_dte = numero_dte
              myTime = dateutil.parser.parse(dte_fecha)
              racion_de_6h = timedelta(hours=6)
              myTime = myTime + racion_de_6h
              formato2 = "%Y-%m-%d %H:%M:%S"
              myTime = myTime.strftime(formato2)
              self.dte_fecha = myTime

           if self.tipo_f == 'cambiaria':
              xml_data = self.set_data_for_invoice_cambiaria()
              self.letras = self.l10n_gt_edi_amount_to_text()
              uuid, serie, numero_dte, dte_fecha =self.send_data_api_cambiaria(xml_data)
              message = _("Facturacion Electronica %s: Serie %s  Numero %s") % (self.tipo_f, serie, numero_dte)
              self.message_post(body=message)
              self.uuid = uuid
              self.serie = serie
              self.numero_dte = numero_dte
              myTime = dateutil.parser.parse(dte_fecha)
              racion_de_6h = timedelta(hours=6)
              myTime = myTime + racion_de_6h
              formato2 = "%Y-%m-%d %H:%M:%S"
              myTime = myTime.strftime(formato2)
              self.dte_fecha = myTime

        if self.type == "in_invoice":
           if self.tipo_s == 'especial':
              xml_data = self.set_data_for_invoice_special()
              self.letras = self.l10n_gt_edi_amount_to_text()
              uuid, serie, numero_dte, dte_fecha =self.send_data_api_special(xml_data)
              message = _("Facturacion Electronica Especial: Serie %s  Numero %s") % (serie, numero_dte)
              self.message_post(body=message)
              self.uuid = uuid
              self.serie = serie
              self.numero_dte = numero_dte
              myTime = dateutil.parser.parse(dte_fecha)
              racion_de_6h = timedelta(hours=6)
              myTime = myTime + racion_de_6h
              formato2 = "%Y-%m-%d %H:%M:%S"
              myTime = myTime.strftime(formato2)
              self.dte_fecha = myTime

        if self.type == "out_refund" and self.refund_invoice_id.uuid:
           xml_data = credit_note.set_data_for_invoice_credit(self)
           self.letras = self.l10n_gt_edi_amount_to_text()
           uuid, serie, numero_dte, dte_fecha =credit_note.send_data_api_credit(self, xml_data)
           message = _("Nota de Credito: Serie %s  Numero %s") % (serie, numero_dte)
           self.message_post(body=message)
           self.uuid = uuid
           self.serie = serie
           self.numero_dte = numero_dte
           myTime = dateutil.parser.parse(dte_fecha)
           racion_de_6h = timedelta(hours=6)
           myTime = myTime + racion_de_6h
           formato2 = "%Y-%m-%d %H:%M:%S"
           myTime = myTime.strftime(formato2)
           self.dte_fecha = myTime

        if self.type == "out_refund" and self.nota_abono == True:
           xml_data = nota_abono.set_data_for_invoice_abono(self)
           self.letras = self.l10n_gt_edi_amount_to_text()
           uuid, serie, numero_dte, dte_fecha =nota_abono.send_data_api_abono(self, xml_data)
           message = _("Nota de Abono: Serie %s  Numero %s") % (serie, numero_dte)
           self.message_post(body=message)
           self.uuid = uuid
           self.serie = serie
           self.numero_dte = numero_dte
           myTime = dateutil.parser.parse(dte_fecha)
           racion_de_6h = timedelta(hours=6)
           myTime = myTime + racion_de_6h
           formato2 = "%Y-%m-%d %H:%M:%S"
           myTime = myTime.strftime(formato2)
           self.dte_fecha = myTime

        return res

    @api.multi
    def action_invoice_cancel(self):
        if self.journal_id.is_eface == False:
           return super(AccountInvoice, self).action_invoice_cancel()
        res = super(AccountInvoice, self).action_invoice_cancel()
        if self.type == "out_invoice" and self.uuid:
           xml_data = invoice_cancel.set_data_for_invoice_cancel(self)
           uuid, serie, numero_dte, dte_fecha =invoice_cancel.send_data_api_cancel(self, xml_data)
           message = _("Factura Cancelada: Serie %s  Numero %s") % (serie, numero_dte)
           self.message_post(body=message)

        if self.type == "out_refund" and self.uuid:
           xml_data = invoice_cancel.set_data_for_invoice_cancel(self)
           uuid, serie, numero_dte, dte_fecha =invoice_cancel.send_data_api_cancel(self, xml_data)
           message = _("Nota Cancelada: Serie %s  Numero %s") % (serie, numero_dte)
           self.message_post(body=message)

        return res

    @api.multi
    def set_data_for_invoice(self):

        xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
        version = "0.1"
        ns = "{xsi}"
        DTE= "dte"

        root = ET.Element("{" + xmlns + "}GTDocumento", Version="0.1", attrib={"{" + xsi + "}schemaLocation" : schemaLocation})
        doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
        dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
        dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
        fecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        dge = ET.SubElement(dem, "{" + xmlns + "}DatosGenerales", CodigoMoneda="GTQ",  FechaHoraEmision=fecha_emision, Tipo="FACT")
        api = self.env['api.data.configuration'].search([('code_est', '=', self.journal_id.code_est)], limit=1)
        if not api:
            return False
        emi = ET.SubElement(dem, "{" + xmlns + "}Emisor", AfiliacionIVA="GEN", CodigoEstablecimiento=api.code_est, CorreoEmisor=self.company_id.email or '', NITEmisor=self.company_id.vat or '', NombreComercial=api.nombre, NombreEmisor=self.company_id.name)
        dire = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
        ET.SubElement(dire, "{" + xmlns + "}Direccion").text = api.direccion or ''
        ET.SubElement(dire, "{" + xmlns + "}CodigoPostal").text = self.company_id.zip or "01009"
        ET.SubElement(dire, "{" + xmlns + "}Municipio").text = self.company_id.city or "Guatemala"
        ET.SubElement(dire, "{" + xmlns + "}Departamento").text = self.company_id.state_id.name or "Guatemala"
        ET.SubElement(dire, "{" + xmlns + "}Pais").text = self.company_id.country_id.code or "GT"

        if self.partner_id.vat:
           vat = self.partner_id.vat
           vat = re.sub('\ |\?|\.|\!|\/|\;|\:|\-', '', vat)
           vat = vat.upper()
        else:
            vat = "CF"

        rece = ET.SubElement(dem, "{" + xmlns + "}Receptor", CorreoReceptor=self.partner_id.email or "", IDReceptor=vat, NombreReceptor=self.partner_id.name)
        direc = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
        ET.SubElement(direc, "{" + xmlns + "}Direccion").text = self.partner_id.street or "Ciudad"
        ET.SubElement(direc, "{" + xmlns + "}CodigoPostal").text = self.partner_id.zip or "01009"
        ET.SubElement(direc, "{" + xmlns + "}Municipio").text = self.partner_id.city or "Guatemala"
        ET.SubElement(direc, "{" + xmlns + "}Departamento").text = self.partner_id.state_id.name or "Guatemala"
        ET.SubElement(direc, "{" + xmlns + "}Pais").text = self.partner_id.country_id.code or "GT"

        #Frases
        fra = ET.SubElement(dem, "{" + xmlns + "}Frases")
        ET.SubElement(fra, "{" + xmlns + "}Frase", TipoFrase=self.company_id.tipo, CodigoEscenario=self.company_id.codigo)
        invoice_line = self.invoice_line_ids
        cg = 0
        for line_id in invoice_line:
            if self.partner_id.tax_partner == True and line_id.product_id.tax_product == True:
               if cg == 0:
                  ET.SubElement(fra, "{" + xmlns + "}Frase", TipoFrase="4", CodigoEscenario="11")
                  cg+=1

        items = ET.SubElement(dem, "{" + xmlns + "}Items")
        tax_in_ex = 1
        cnt = 0
        #LineasFactura
        for line in invoice_line:
            cnt += 1
            p_type = 0
            BoS = "B"
            if line.product_id.type == 'service':
                p_type = 1
                BoS = "S"
            for tax in line.invoice_line_tax_ids:
                if tax.price_include:
                    tax_in_ex = 0

            # Item
            item = ET.SubElement(items, "{" + xmlns + "}Item", BienOServicio=BoS, NumeroLinea=str(cnt))

            ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
            ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = str(line.product_id.default_code) + " |" + str(line.product_id.name)
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(round(line.quantity * line.price_unit, 2))
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(round((line.discount * (line.quantity * line.price_unit))/100,2))

            tax = "IVA"
            if line.invoice_line_tax_ids:
               tax = "IVA"
            elif self.partner_id.tax_partner == True and line.product_id.tax_product == True:
                 tax = "IVA"
            else:
                raise UserError(_("Las l??neas de Factura deben de llevar impuesto (IVA)."))

            impuestos = ET.SubElement(item, "{" + xmlns + "}Impuestos")
            impuesto = ET.SubElement(impuestos, "{" + xmlns + "}Impuesto")
            price_tax = line.price_total - line.price_subtotal
            price_tax = str(round(price_tax,2))
            UnidadGravable = "1"
            SubTotal = str(round(line.price_subtotal,2))
            if self.partner_id.tax_partner == True and line.product_id.tax_product == True:
               UnidadGravable = "2"
               price_tax = "0.00"
            ET.SubElement(impuesto, "{" + xmlns + "}NombreCorto").text = tax
            ET.SubElement(impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = UnidadGravable
            ET.SubElement(impuesto, "{" + xmlns + "}MontoGravable").text = SubTotal
            ET.SubElement(impuesto, "{" + xmlns + "}MontoImpuesto").text = price_tax
            ET.SubElement(item, "{" + xmlns + "}Total").text = str(round(line.price_total,2))
        #Totales
        totales = ET.SubElement(dem, "{" + xmlns + "}Totales")
        timpuestos = ET.SubElement(totales, "{" + xmlns + "}TotalImpuestos")
        tim = ET.SubElement(timpuestos, "{" + xmlns + "}TotalImpuesto", NombreCorto="IVA", TotalMontoImpuesto=str(round(self.amount_tax,2)))
        ET.SubElement(totales, "{" + xmlns + "}GranTotal").text = str(round(self.amount_total,2))

        #Adenda
        ade = ET.SubElement(doc, "{" + xmlns + "}Adenda")
        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), '%Y-%m-%d')
        formato2 = "%d-%m-%Y"
        date_due = date_due.strftime(formato2)
        phone = " "
        mobile = " "
        if self.partner_id.phone:
           phone = self.partner_id.phone
        if self.partner_id.mobile:
           mobile = self.partner_id.mobile
        telefono = phone + " " + mobile
        ET.SubElement(ade, "FECHA_VENCIMIENTO").text = date_due or ''
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name or ''
        ET.SubElement(ade, "NOTAS").text = self.comment or ''
        ET.SubElement(ade, "REFERENCIA").text = self.reference or ''
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name or ''
        ET.SubElement(ade, "ORIGEN").text = self.origin or ''
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name or ''
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number or ''
        ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name or ''
        ET.SubElement(ade, "TELEFONO").text = telefono
        cont = ET.tostring(root, encoding="UTF-8", method='xml')
        buscar = "ns0"
        rmpl = "dte"
        cont = cont.decode('utf_8')
        cont = cont.replace(buscar, rmpl)
        cont = cont.encode('utf_8')
        dat = base64.b64encode(cont)
        return dat

    @api.multi
    def send_data_api(self, xml_data=None):
        api = self.env['api.data.configuration'].search([('code_est', '=', self.journal_id.code_est)], limit=1)
        if not api:
            return False
        XML = xml_data
        url = api.url_firma
        ran = str(randint(1,99999))
        data_send = {'llave': api.key_firma,
                     'archivo': XML,
                     'codigo': ran,
                     'alias': api.user,
                     'es_anulacion': 'N'}

        response = requests.request("POST", url, data=data_send)
        rp = response.json()

        dt = rp["archivo"]
        url = api.url_certificado
        payload = {
            'nit_emisor': self.company_id.vat,
            'correo_copia': self.company_id.email,
            'xml_dte': dt,
            }

        ident = str(randint(1111111,9999999))
        headers = {
            'usuario': api.user,
            'llave': api.key_certificado,
            'content-type': "application/json",
            'identificador': ident,
            }
        response = requests.request("POST", url, data=json.dumps(payload), headers=headers)

        rp = response.json()
        uuid = rp["uuid"]
        serie = rp["serie"]
        numero_dte = rp["numero"]
        dte_fecha = rp["fecha"]
        cantidad_errores = rp["cantidad_errores"]
        descripcion_errores = rp["descripcion_errores"]
        if cantidad_errores>0:
            raise UserError(_("You cannot validate an invoice\n Error No:%s\n %s."% (cantidad_errores,descripcion_errores)))
        return uuid, serie, numero_dte, dte_fecha

    @api.multi
    def set_data_for_invoice_cambiaria(self):

        xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
        version = "0.1"
        ns = "{xsi}"
        DTE= "dte"
        cno = "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0"
        uri = "http://www.sat.gob.gt/fel/cambiaria.xsd"

        root = ET.Element("{" + xmlns + "}GTDocumento", Version="0.1", attrib={"{" + xsi + "}schemaLocation" : schemaLocation})
        doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
        dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
        dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
        fecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        dge = ET.SubElement(dem, "{" + xmlns + "}DatosGenerales", CodigoMoneda="GTQ",  FechaHoraEmision=fecha_emision, Tipo="FCAM")
        api = self.env['api.data.configuration'].search([('code_est', '=', self.journal_id.code_est)], limit=1)
        if not api:
            return False
        emi = ET.SubElement(dem, "{" + xmlns + "}Emisor", AfiliacionIVA="GEN", CodigoEstablecimiento=api.code_est, CorreoEmisor=self.company_id.email or '', NITEmisor=self.company_id.vat or '', NombreComercial=api.nombre, NombreEmisor=self.company_id.name)
        dire = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
        ET.SubElement(dire, "{" + xmlns + "}Direccion").text = api.direccion
        ET.SubElement(dire, "{" + xmlns + "}CodigoPostal").text = self.company_id.zip or "01009"
        ET.SubElement(dire, "{" + xmlns + "}Municipio").text = self.company_id.city or "Guatemala"
        ET.SubElement(dire, "{" + xmlns + "}Departamento").text = self.company_id.state_id.name or "Guatemala"
        ET.SubElement(dire, "{" + xmlns + "}Pais").text = self.company_id.country_id.code or "GT"

        if self.partner_id.vat:
           vat = self.partner_id.vat
           vat = re.sub('\ |\?|\.|\!|\/|\;|\:|\-', '', vat)
           vat = vat.upper()
        else:
            vat = "CF"

        rece = ET.SubElement(dem, "{" + xmlns + "}Receptor", CorreoReceptor=self.partner_id.email or "", IDReceptor=vat, NombreReceptor=self.partner_id.name)
        direc = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
        ET.SubElement(direc, "{" + xmlns + "}Direccion").text = self.partner_id.street or "Ciudad"
        ET.SubElement(direc, "{" + xmlns + "}CodigoPostal").text = self.partner_id.zip or "01009"
        ET.SubElement(direc, "{" + xmlns + "}Municipio").text = self.partner_id.city or "Guatemala"
        ET.SubElement(direc, "{" + xmlns + "}Departamento").text = self.partner_id.state_id.name or "Guatemala"
        ET.SubElement(direc, "{" + xmlns + "}Pais").text = self.partner_id.country_id.code or "GT"

        #Frases
        fra = ET.SubElement(dem, "{" + xmlns + "}Frases")
        ET.SubElement(fra, "{" + xmlns + "}Frase", TipoFrase=self.company_id.tipo, CodigoEscenario=self.company_id.codigo)

        invoice_line = self.invoice_line_ids
        items = ET.SubElement(dem, "{" + xmlns + "}Items")
        tax_in_ex = 1
        cnt = 0
        #LineasFactura
        for line in invoice_line:
            cnt += 1
            p_type = 0
            BoS = "B"
            if line.product_id.type == 'service':
                p_type = 1
                BoS = "S"
            for tax in line.invoice_line_tax_ids:
                if tax.price_include:
                    tax_in_ex = 0

            # Item
            item = ET.SubElement(items, "{" + xmlns + "}Item", BienOServicio=BoS, NumeroLinea=str(cnt))

            ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
            ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = str(line.product_id.default_code) + " |" + str(line.product_id.name)
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(line.quantity * line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(round((line.discount * (line.quantity * line.price_unit))/100,2))

            if line.invoice_line_tax_ids:
               tax = "IVA"
            else:
                raise UserError(_("Las l??neas de Factura deben de llevar impuesto (IVA)."))

            impuestos = ET.SubElement(item, "{" + xmlns + "}Impuestos")
            impuesto = ET.SubElement(impuestos, "{" + xmlns + "}Impuesto")
            price_tax = line.price_total - line.price_subtotal
            ET.SubElement(impuesto, "{" + xmlns + "}NombreCorto").text = tax
            ET.SubElement(impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = "1"
            ET.SubElement(impuesto, "{" + xmlns + "}MontoGravable").text = str(round(line.price_subtotal,2))
            ET.SubElement(impuesto, "{" + xmlns + "}MontoImpuesto").text = str(round(price_tax,2))
            ET.SubElement(item, "{" + xmlns + "}Total").text = str(round(line.price_total,2))
        #Totales
        totales = ET.SubElement(dem, "{" + xmlns + "}Totales")
        timpuestos = ET.SubElement(totales, "{" + xmlns + "}TotalImpuestos")
        tim = ET.SubElement(timpuestos, "{" + xmlns + "}TotalImpuesto", NombreCorto="IVA", TotalMontoImpuesto=str(round(self.amount_tax,2)))
        ET.SubElement(totales, "{" + xmlns + "}GranTotal").text = str(round(self.amount_total,2))

        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), '%Y-%m-%d')
        formato2 = "%Y-%m-%d"
        date_due = date_due.strftime(formato2)
        complementos = ET.SubElement(dem, "{" + xmlns + "}Complementos")
        complemento = ET.SubElement(complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1,99999)), NombreComplemento="AbonosFacturaCambiaria", URIComplemento=uri)
        retenciones = ET.SubElement(complemento, "{" + cno + "}AbonosFacturaCambiaria", Version="1")
        abono = ET.SubElement(retenciones, "{" + cno + "}Abono")
        ET.SubElement(abono, "{" + cno + "}NumeroAbono").text = "1"
        ET.SubElement(abono, "{" + cno + "}FechaVencimiento").text =  date_due
        ET.SubElement(abono, "{" + cno + "}MontoAbono").text = str(round(self.amount_total,2))
        #Adenda
        ade = ET.SubElement(doc, "{" + xmlns + "}Adenda")
        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), '%Y-%m-%d')
        formato2 = "%d-%m-%Y"
        date_due = date_due.strftime(formato2)
        phone = " "
        mobile = " "
        if self.partner_id.phone:
           phone = self.partner_id.phone
        if self.partner_id.mobile:
           mobile = self.partner_id.mobile
        telefono = phone + " " + mobile
        ET.SubElement(ade, "FECHA_VENCIMIENTO").text = date_due
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name or ''
        ET.SubElement(ade, "NOTAS").text = self.comment or ''
        ET.SubElement(ade, "REFERENCIA").text = self.reference or ''
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name or ''
        ET.SubElement(ade, "ORIGEN").text = self.origin or ''
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number or ''
        ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name
        ET.SubElement(ade, "TELEFONO").text = telefono

        cont = ET.tostring(root, encoding="UTF-8", method='xml')
        buscar = "ns0"
        buscar2 = "ns2"
        rmpl = "dte"
        rmpl2 = "cfc"
        cont = cont.decode('utf_8')
        cont = cont.replace(buscar, rmpl)
        cont = cont.replace(buscar2, rmpl2)
        cont = cont.encode('utf_8')
        dat = base64.b64encode(cont)
        return dat

    @api.multi
    def send_data_api_cambiaria(self, xml_data=None):
        api = self.env['api.data.configuration'].search([('code_est', '=', self.journal_id.code_est)], limit=1)
        if not api:
            return False
        XML = xml_data
        url = api.url_firma
        ran = str(randint(1,99999))
        data_send = {'llave': api.key_firma,
                     'archivo': XML,
                     'codigo': ran,
                     'alias': api.user,
                     'es_anulacion': 'N'}

        response = requests.request("POST", url, data=data_send)
        rp = response.json()

        dt = rp["archivo"]
        url = api.url_certificado
        payload = {
            'nit_emisor': self.company_id.vat,
            'correo_copia': self.company_id.email,
            'xml_dte': dt,
            }

        ident = str(randint(1111111,9999999))
        headers = {
            'usuario': api.user,
            'llave': api.key_certificado,
            'content-type': "application/json",
            'identificador': ident,
            }
        response = requests.request("POST", url, data=json.dumps(payload), headers=headers)

        rp = response.json()
        uuid = rp["uuid"]
        serie = rp["serie"]
        numero_dte = rp["numero"]
        dte_fecha = rp["fecha"]
        cantidad_errores = rp["cantidad_errores"]
        descripcion_errores = rp["descripcion_errores"]
        if cantidad_errores>0:
            raise UserError(_("You cannot validate an invoice\n Error No:%s\n %s."% (cantidad_errores,descripcion_errores)))
        return uuid, serie, numero_dte, dte_fecha

    @api.multi
    def set_data_for_invoice_special(self):

        xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
        version = "0.1"
        ns = "{xsi}"
        DTE= "dte"
        #cno = "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"
        cno = "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0"

        root = ET.Element("{" + xmlns + "}GTDocumento", Version="0.1", attrib={"{" + xsi + "}schemaLocation" : schemaLocation})
        doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
        dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
        dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
        #fecha_emision = dt.datetime.now(gettz("America/Guatemala")).isoformat()   #dt.datetime.now().isoformat()
        fecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        dge = ET.SubElement(dem, "{" + xmlns + "}DatosGenerales", CodigoMoneda="GTQ",  FechaHoraEmision=fecha_emision, Tipo="FESP")
        api = self.env['api.data.configuration'].search([('code_est', '=', self.journal_id.code_est)], limit=1)
        if not api:
            return False
        emi = ET.SubElement(dem, "{" + xmlns + "}Emisor", AfiliacionIVA="GEN", CodigoEstablecimiento=api.code_est, CorreoEmisor=self.company_id.email or '', NITEmisor=self.company_id.vat or '', NombreComercial=api.nombre, NombreEmisor=self.company_id.name)
        dire = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
        ET.SubElement(dire, "{" + xmlns + "}Direccion").text = api.direccion
        ET.SubElement(dire, "{" + xmlns + "}CodigoPostal").text = self.company_id.zip or "01009"
        ET.SubElement(dire, "{" + xmlns + "}Municipio").text = self.company_id.city or "Guatemala"
        ET.SubElement(dire, "{" + xmlns + "}Departamento").text = self.company_id.state_id.name or "Guatemala"
        ET.SubElement(dire, "{" + xmlns + "}Pais").text = self.company_id.country_id.code or "GT"

        if self.partner_id.vat:
           vat = self.partner_id.vat
           vat = re.sub('\ |\?|\.|\!|\/|\;|\:|\-', '', vat)
           vat = vat.upper()
        else:
            vat = "CF"

        rece = ET.SubElement(dem, "{" + xmlns + "}Receptor", CorreoReceptor=self.partner_id.email or "", IDReceptor=vat, NombreReceptor=self.partner_id.name)
        direc = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
        ET.SubElement(direc, "{" + xmlns + "}Direccion").text = self.partner_id.street or "Ciudad"
        ET.SubElement(direc, "{" + xmlns + "}CodigoPostal").text = self.partner_id.zip or "01009"
        ET.SubElement(direc, "{" + xmlns + "}Municipio").text = self.partner_id.city or "Guatemala"
        ET.SubElement(direc, "{" + xmlns + "}Departamento").text = self.partner_id.state_id.name or "Guatemala"
        ET.SubElement(direc, "{" + xmlns + "}Pais").text = self.partner_id.country_id.code or "GT"

        invoice_line = self.invoice_line_ids
        items = ET.SubElement(dem, "{" + xmlns + "}Items")
        tax_in_ex = 1
        cnt = 0
        #LineasFactura
        for line in invoice_line:
            cnt += 1
            p_type = 0
            BoS = "B"
            if line.product_id.type == 'service':
                p_type = 1
                BoS = "S"
            for tax in line.invoice_line_tax_ids:
                if tax.price_include:
                    tax_in_ex = 0

            # Item
            item = ET.SubElement(items, "{" + xmlns + "}Item", BienOServicio=BoS, NumeroLinea=str(cnt))

            ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
            ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = str(line.product_id.default_code) + " |" + str(line.product_id.name)
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(line.quantity * line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(round((line.discount * (line.quantity * line.price_unit))/100,2))

            if line.invoice_line_tax_ids:
               tax = "IVA"
            else:
                raise UserError(_("Las l??neas de Factura deben de llevar impuesto (IVA)."))

            impuestos = ET.SubElement(item, "{" + xmlns + "}Impuestos")
            impuesto = ET.SubElement(impuestos, "{" + xmlns + "}Impuesto")
            price_tax = line.price_total - line.price_subtotal
            ET.SubElement(impuesto, "{" + xmlns + "}NombreCorto").text = tax
            ET.SubElement(impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = "1"
            ET.SubElement(impuesto, "{" + xmlns + "}MontoGravable").text = str(round(line.price_subtotal,2))
            ET.SubElement(impuesto, "{" + xmlns + "}MontoImpuesto").text = str(round(price_tax,2))
            ET.SubElement(item, "{" + xmlns + "}Total").text = str(round(line.price_total,2))
        #Totales
        totales = ET.SubElement(dem, "{" + xmlns + "}Totales")
        timpuestos = ET.SubElement(totales, "{" + xmlns + "}TotalImpuestos")
        tim = ET.SubElement(timpuestos, "{" + xmlns + "}TotalImpuesto", NombreCorto="IVA", TotalMontoImpuesto=str(round(self.amount_tax,2)))
        ET.SubElement(totales, "{" + xmlns + "}GranTotal").text = str(round(self.amount_total,2))

        #Complementos
        complementos = ET.SubElement(dem, "{" + xmlns + "}Complementos")
        complemento = ET.SubElement(complementos, "{" + xmlns + "}Complemento", IDComplemento=str(randint(1,99999)), NombreComplemento="FacturaEspecial", URIComplemento=cno)
        retenciones = ET.SubElement(complemento, "{" + cno + "}RetencionesFacturaEspecial", Version="1")
        ET.SubElement(retenciones, "{" + cno + "}RetencionISR").text = str(round(self.retencion,2))
        ET.SubElement(retenciones, "{" + cno + "}RetencionIVA").text = str(round(self.amount_tax,2))
        ET.SubElement(retenciones, "{" + cno + "}TotalMenosRetenciones").text = str(round(self.amount_untaxed - self.retencion,2))
        #Adenda
        ade = ET.SubElement(doc, "{" + xmlns + "}Adenda")
        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), '%Y-%m-%d')
        formato2 = "%d-%m-%Y"
        date_due = date_due.strftime(formato2)
        phone = " "
        mobile = " "
        if self.partner_id.phone:
           phone = self.partner_id.phone
        if self.partner_id.mobile:
           mobile = self.partner_id.mobile
        telefono = phone + " " + mobile
        ET.SubElement(ade, "FECHA_VENCIMIENTO").text = date_due
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name or ''
        ET.SubElement(ade, "NOTAS").text = self.comment or ''
        ET.SubElement(ade, "REFERENCIA").text = self.reference or ''
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name or ''
        ET.SubElement(ade, "ORIGEN").text = self.origin or ''
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number or ''
        ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name
        ET.SubElement(ade, "TELEFONO").text = telefono


        cont = ET.tostring(root, encoding="UTF-8", method='xml')
        buscar = "ns0"
        rmpl = "dte"
        buscar2 = "ns2"
        rmpl2 = "cfe"
        cont = cont.decode('utf_8')
        cont = cont.replace(buscar, rmpl)
        cont = cont.replace(buscar2, rmpl2)
        cont = cont.encode('utf_8')
        dat = base64.b64encode(cont)
        return dat

    @api.multi
    def send_data_api_special(self, xml_data=None):
        api = self.env['api.data.configuration'].search([('code_est', '=', self.journal_id.code_est)], limit=1)
        if not api:
            return False
        XML = xml_data
        url = api.url_firma
        ran = str(randint(1,99999))
        data_send = {'llave': api.key_firma,
                     'archivo': XML,
                     'codigo': ran,
                     'alias': api.user,
                     'es_anulacion': 'N'}

        response = requests.request("POST", url, data=data_send)
        rp = response.json()

        dt = rp["archivo"]
        url = api.url_certificado
        payload = {
            'nit_emisor': self.company_id.vat,
            'correo_copia': self.company_id.email,
            'xml_dte': dt,
            }

        ident = str(randint(1111111,9999999))
        headers = {
            'usuario': api.user,
            'llave': api.key_certificado,
            'content-type': "application/json",
            'identificador': ident,
            }
        response = requests.request("POST", url, data=json.dumps(payload), headers=headers)

        #print(response.text)
        rp = response.json()
        uuid = rp["uuid"]
        serie = rp["serie"]
        numero_dte = rp["numero"]
        dte_fecha = rp["fecha"]
        cantidad_errores = rp["cantidad_errores"]
        descripcion_errores = rp["descripcion_errores"]
        if cantidad_errores>0:
            raise UserError(_("You cannot validate an invoice\n Error No:%s\n %s."% (cantidad_errores,descripcion_errores)))
        return uuid, serie, numero_dte, dte_fecha

    @api.multi
    def l10n_gt_edi_amount_to_text(self):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words GT format for invoices
        :rtype: str
        """
        self.ensure_one()
        # Split integer and decimal part
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i)
        invoice_words = '%(words)s %(amount_d)02d/100' % dict(
            words=words, amount_d=amount_d)
        return invoice_words
