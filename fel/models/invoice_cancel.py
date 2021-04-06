# -*- encoding: UTF-8 -*-

from odoo import api, models, fields, _
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta
from lxml import etree
import datetime as dt
import dateutil.parser
from dateutil.tz import gettz
from dateutil import parser
from odoo.addons.fel import numero_a_texto
import json
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
import base64
import requests
from json import loads
from random import randint
import re

#_logger = logging.getLogger(__name__)

@api.multi
def set_data_for_invoice_cancel(self):
        xmlns = "http://www.sat.gob.gt/dte/fel/0.1.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "http://www.sat.gob.gt/dte/fel/0.1.0"
        version = "0.1"
        ns = "{xsi}"
        DTE= "dte"
        cno = "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"

        root = ET.Element("{" + xmlns + "}GTAnulacionDocumento", Version="0.1", attrib={"{" + xsi + "}schemaLocation" : schemaLocation})
        doc = ET.SubElement(root, "{" + xmlns + "}SAT")
        dte = ET.SubElement(doc, "{" + xmlns + "}AnulacionDTE", ID="DatosCertificados")
        date_invoice = self.dte_fecha or datetime.now()
        date_invoice = datetime.strptime(str(date_invoice), '%Y-%m-%d %H:%M:%S')
        racion_de_6h = timedelta(hours=6)
        date_invoice = date_invoice - racion_de_6h
        formato1 = "%Y-%m-%dT%H:%M:%S.%f"
        date_invoice = date_invoice.strftime(formato1)[:-3]
        if self.partner_id.vat:
           vat = self.partner_id.vat
           vat = re.sub('\ |\?|\.|\!|\/|\;|\:|\-', '', vat)
           vat = vat.upper()
        else:
            vat = "CF"
        fecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        dge = ET.SubElement(dte, "{" + xmlns + "}DatosGenerales", FechaEmisionDocumentoAnular=date_invoice, FechaHoraAnulacion=fecha_emision, ID="DatosAnulacion", IDReceptor=vat, MotivoAnulacion="Anulación", NITEmisor=self.company_id.vat, NumeroDocumentoAAnular=str(self.uuid))

        cont = ET.tostring(root, encoding="UTF-8", method='xml')
        buscar = "ns0"
        rmpl = "dte"
        cont = cont.decode('utf_8')
        cont = cont.replace(buscar, rmpl)
        cont = cont.encode('utf_8')
        dat = base64.b64encode(cont)
        return dat

@api.multi
def send_data_api_cancel(self, xml_data):
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
                     'es_anulacion': 'S'}

        response = requests.request("POST", url, data=data_send)
        rp = response.json()

        dt = rp["archivo"]
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

        url = api.url_anulacion
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
