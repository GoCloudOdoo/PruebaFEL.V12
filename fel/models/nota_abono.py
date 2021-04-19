# -*- encoding: UTF-8 -*-

from odoo import api
import xml.etree.cElementTree as ET
import datetime as dt
from dateutil.tz import gettz
from . import adendas
import logging
import base64
import re

_logger = logging.getLogger(__name__)


@api.multi
def set_data_for_invoice_abono(self):
    xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    schemalocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
    root = ET.Element(
        "{" + xmlns + "}GTDocumento",
        Version="0.1",
        attrib={"{" + xsi + "}schemaLocation": schemalocation},
    )
    doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
    dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
    dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
    fecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3]
    ET.SubElement(
        dem,
        "{" + xmlns + "}DatosGenerales",
        CodigoMoneda="GTQ",
        FechaHoraEmision=fecha_emision,
        Tipo="NABN",
    )
    api_fel = self.env["api.data.configuration"].search(
        [("code_est", "=", self.journal_id.code_est)], limit=1
    )
    if not api_fel:
        return False
    emi = ET.SubElement(
        dem,
        "{" + xmlns + "}Emisor",
        AfiliacionIVA="GEN",
        CodigoEstablecimiento=api_fel.code_est,
        CorreoEmisor=self.company_id.email,
        NITEmisor=self.company_id.vat,
        NombreComercial=api_fel.nombre,
        NombreEmisor=self.company_id.name,
    )
    dire_a = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
    ET.SubElement(dire_a, "{" + xmlns + "}Direccion").text = api_fel.direccion
    ET.SubElement(dire_a, "{" + xmlns + "}CodigoPostal").text = (
        self.company_id.zip or "01009"
    )
    ET.SubElement(dire_a, "{" + xmlns + "}Municipio").text = (
        self.company_id.city or "Guatemala"
    )
    ET.SubElement(dire_a, "{" + xmlns + "}Departamento").text = (
        self.company_id.state_id.name or "Guatemala"
    )
    ET.SubElement(dire_a, "{" + xmlns + "}Pais").text = (
        self.company_id.country_id.code or "GT"
    )

    if self.partner_id.vat:
        vat = self.partner_id.vat
        vat = re.sub(r"[\?!:/;. -]","", vat)
        vat_a = vat.upper()
    else:
        vat_a = "CF"

    rece = ET.SubElement(
        dem,
        "{" + xmlns + "}Receptor",
        CorreoReceptor=self.partner_id.email or "",
        IDReceptor=vat_a,
        NombreReceptor=self.partner_id.name,
    )
    direc_a = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
    ET.SubElement(direc_a, "{" + xmlns + "}Direccion").text = (
        self.partner_id.street or "Ciudad"
    )
    ET.SubElement(direc_a, "{" + xmlns + "}CodigoPostal").text = (
        self.partner_id.zip or "01009"
    )
    ET.SubElement(direc_a, "{" + xmlns + "}Municipio").text = (
        self.partner_id.city or "Guatemala"
    )
    ET.SubElement(direc_a, "{" + xmlns + "}Departamento").text = (
        self.partner_id.state_id.name or "Guatemala"
    )
    ET.SubElement(direc_a, "{" + xmlns + "}Pais").text = (
        self.partner_id.country_id.code or "GT"
    )

    invoice_ln = self.invoice_line_ids
    items = ET.SubElement(dem, "{" + xmlns + "}Items")
    cnt = 0
    # LineasFactura
    for line in invoice_ln:
        cnt += 1
        bien = "B"
        if line.product_id.type == "service":
            bien = "S"

        # Item
        item = ET.SubElement(
            items, "{" + xmlns + "}Item", BienOServicio=bien, NumeroLinea=str(cnt)
        )

        ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
        ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
        ET.SubElement(item, "{" + xmlns + "}Descripcion").text = (
            str(line.product_id.default_code) + "|" + str(line.product_id.name)
        )
        ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(line.price_unit)
        ET.SubElement(item, "{" + xmlns + "}Precio").text = str(
            line.quantity * line.price_unit
        )
        ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(
            round((line.discount * (line.quantity * line.price_unit)) / 100, 2)
        )

        ET.SubElement(item, "{" + xmlns + "}Total").text = str(
            round(line.price_total, 2)
        )
    # Totales
    totales = ET.SubElement(dem, "{" + xmlns + "}Totales")
    ET.SubElement(totales, "{" + xmlns + "}GranTotal").text = str(
        round(self.amount_total, 2)
    )

    # Adenda
    et = adendas.set_adendas(self, ET, doc, xmlns)

    cont = et.tostring(root, encoding="UTF-8", method="xml")
    buscar = "ns0"
    rmpl = "dte"
    cont = cont.decode("utf_8")
    cont = cont.replace(buscar, rmpl)
    cont = cont.encode("utf_8")
    dat = base64.b64encode(cont)
    return dat
