# -*- encoding: UTF-8 -*-

from odoo import api, models, fields, _
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta
from lxml import etree
import datetime as dt
import dateutil.parser
from dateutil.tz import gettz
from dateutil import parser
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
        api = self.env['api.data.configuration'].search([('user_id', '=', self.user_id.id)], limit=1)
        if not api:
            return False          
        emi = ET.SubElement(dem, "{" + xmlns + "}Emisor", AfiliacionIVA="GEN", CodigoEstablecimiento=api.code_est, CorreoEmisor=self.company_id.email, NITEmisor=self.company_id.vat, NombreComercial=api.nombre, NombreEmisor=self.company_id.name)
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
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = line.name or " "
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(line.quantity * line.price_unit)
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(round((line.discount * (line.quantity * line.price_unit))/100,2))

            if line.invoice_line_tax_ids:
               tax = "IVA"
            else:
                raise UserError(_("Las líneas de Factura deben de llevar impuesto (IVA)."))

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
        ET.SubElement(ade, "FECHA_VENCIMIENTO").text = date_due
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name        
        ET.SubElement(ade, "NOTAS").text = self.comment
        ET.SubElement(ade, "REFERENCIA").text = self.reference
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name
        ET.SubElement(ade, "ORIGEN").text = self.origin
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number
        ET.SubElement(ade, "TELEFONO").text = self.partner_id.phone + " " + self.partner_id.mobile

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
        api = self.env['api.data.configuration'].search([('user_id', '=', self.user_id.id)], limit=1)        
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
