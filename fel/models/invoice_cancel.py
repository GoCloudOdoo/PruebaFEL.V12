# -*- encoding: UTF-8 -*-

from odoo import api
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta
import datetime as dt
from dateutil.tz import gettz
import base64
import re

# _logger = logging.getLogger(__name__)


@api.multi
def set_data_for_invoice_cancel(self):
    xmlns = "http://www.sat.gob.gt/dte/fel/0.1.0"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    schemalocation = "http://www.sat.gob.gt/dte/fel/0.1.0"

    root = ET.Element(
        "{" + xmlns + "}GTAnulacionDocumento",
        Version="0.1",
        attrib={"{" + xsi + "}schemaLocation": schemalocation},
    )
    doc = ET.SubElement(root, "{" + xmlns + "}SAT")
    dte = ET.SubElement(doc, "{" + xmlns + "}AnulacionDTE", ID="DatosCertificados")
    date_invoice = self.dte_fecha or datetime.now()
    date_invoice = datetime.strptime(str(date_invoice), "%Y-%m-%d %H:%M:%S")
    racion_de_6h = timedelta(hours=6)
    date_invoice = date_invoice - racion_de_6h
    formato1 = "%Y-%m-%dT%H:%M:%S.%f"
    date_invoice = date_invoice.strftime(formato1)[:-3]
    if self.partner_id.vat:
        vat = self.partner_id.vat
        vat = re.sub(r"[\?!:/;. -]","", vat)
        vat = vat.upper()
    else:
        vat = "CF"
    fecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3]
    ET.SubElement(
        dte,
        "{" + xmlns + "}DatosGenerales",
        FechaEmisionDocumentoAnular=date_invoice,
        FechaHoraAnulacion=fecha_emision,
        ID="DatosAnulacion",
        IDReceptor=vat,
        MotivoAnulacion="Anulación",
        NITEmisor=self.company_id.vat,
        NumeroDocumentoAAnular=str(self.uuid),
    )

    cont = ET.tostring(root, encoding="UTF-8", method="xml")
    buscar = "ns0"
    rmpl = "dte"
    cont = cont.decode("utf_8")
    cont = cont.replace(buscar, rmpl)
    cont = cont.encode("utf_8")
    dat = base64.b64encode(cont)
    return dat
