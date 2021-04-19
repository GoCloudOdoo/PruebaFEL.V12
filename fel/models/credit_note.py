# -*- encoding: UTF-8 -*-

from odoo import api, _
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta
import datetime as dt
from dateutil.tz import gettz
from odoo.exceptions import UserError
from . import adendas
import base64
from random import randint
import re


@api.multi
def set_data_for_invoice_credit(self):
    xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    schemalocatiion = "http://www.sat.gob.gt/dte/fel/0.2.0"
    cno = "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"

    root = ET.Element(
        "{" + xmlns + "}GTDocumento",
        Version="0.1",
        attrib={"{" + xsi + "}schemaLocation": schemalocatiion},
    )
    doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
    dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
    dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
    fecha_eemision = dt.datetime.now(gettz("America/Guatemala")).__format__(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3]
    ET.SubElement(
        dem,
        "{" + xmlns + "}DatosGenerales",
        CodigoMoneda="GTQ",
        FechaHoraEmision=fecha_eemision,
        Tipo="NCRE",
    )
    api_credit = self.env["api.data.configuration"].search(
        [("code_est", "=", self.journal_id.code_est)], limit=1
    )
    if not api_credit:
        return False
    emi = ET.SubElement(
        dem,
        "{" + xmlns + "}Emisor",
        AfiliacionIVA="GEN",
        CodigoEstablecimiento=api_credit.code_est,
        CorreoEmisor=self.company_id.email,
        NITEmisor=self.company_id.vat,
        NombreComercial=api_credit.nombre,
        NombreEmisor=self.company_id.name,
    )
    dire = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
    ET.SubElement(dire, "{" + xmlns + "}Direccion").text = api_credit.direccion
    ET.SubElement(dire, "{" + xmlns + "}CodigoPostal").text = (
        self.company_id.zip or "01009"
    )
    ET.SubElement(dire, "{" + xmlns + "}Municipio").text = (
        self.company_id.city or "Guatemala"
    )
    ET.SubElement(dire, "{" + xmlns + "}Departamento").text = (
        self.company_id.state_id.name or "Guatemala"
    )
    ET.SubElement(dire, "{" + xmlns + "}Pais").text = (
        self.company_id.country_id.code or "GT"
    )

    if self.partner_id.vat:
        nit = self.partner_id.vat
        vat = re.sub(r"[\?!:/;. -]","", nit)
        vat = vat.upper()
    else:
        vat = "CF"

    rece = ET.SubElement(
        dem,
        "{" + xmlns + "}Receptor",
        CorreoReceptor=self.partner_id.email or "",
        IDReceptor=vat,
        NombreReceptor=self.partner_id.name,
    )
    direc = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
    ET.SubElement(direc, "{" + xmlns + "}Direccion").text = (
        self.partner_id.street or "Ciudad"
    )
    ET.SubElement(direc, "{" + xmlns + "}CodigoPostal").text = (
        self.partner_id.zip or "01010"
    )
    ET.SubElement(direc, "{" + xmlns + "}Municipio").text = (
        self.partner_id.city or "Guatemala"
    )
    ET.SubElement(direc, "{" + xmlns + "}Departamento").text = (
        self.partner_id.state_id.name or "Guatemala"
    )
    ET.SubElement(direc, "{" + xmlns + "}Pais").text = (
        self.partner_id.country_id.code or "GT"
    )

    invoice_line = self.invoice_line_ids
    items = ET.SubElement(dem, "{" + xmlns + "}Items")
    cnt = 0
    # LineasFactura
    for line in invoice_line:
        cnt += 1
        bs = "B"
        if line.product_id.type == "service":
            bs = "S"

        # Item
        item = ET.SubElement(
            items, "{" + xmlns + "}Item", BienOServicio=bs, NumeroLinea=str(cnt)
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

        if line.invoice_line_tax_ids:
            tax = "IVA"
        else:
            raise UserError(_("Las líneas de Factura deben de llevar impuesto (IVA)."))

        impuestos = ET.SubElement(item, "{" + xmlns + "}Impuestos")
        impuesto = ET.SubElement(impuestos, "{" + xmlns + "}Impuesto")
        price_tax = line.price_total - line.price_subtotal
        ET.SubElement(impuesto, "{" + xmlns + "}NombreCorto").text = tax
        ET.SubElement(impuesto, "{" + xmlns + "}CodigoUnidadGravable").text = "1"
        ET.SubElement(impuesto, "{" + xmlns + "}MontoGravable").text = str(
            round(line.price_subtotal, 2)
        )
        ET.SubElement(impuesto, "{" + xmlns + "}MontoImpuesto").text = str(
            round(price_tax, 2)
        )
        ET.SubElement(item, "{" + xmlns + "}Total").text = str(
            round(line.price_total, 2)
        )
    # Totales
    totales = ET.SubElement(dem, "{" + xmlns + "}Totales")
    timpuestos = ET.SubElement(totales, "{" + xmlns + "}TotalImpuestos")
    ET.SubElement(
        timpuestos,
        "{" + xmlns + "}TotalImpuesto",
        NombreCorto="IVA",
        TotalMontoImpuesto=str(round(self.amount_tax, 2)),
    )
    ET.SubElement(totales, "{" + xmlns + "}GranTotal").text = str(
        round(self.amount_total, 2)
    )

    # Complementos
    dte_fecha = self.refund_invoice_id.dte_fecha
    dte_fecha = datetime.strptime(str(dte_fecha), "%Y-%m-%d %H:%M:%S")
    racion_de_6h = timedelta(hours=6)
    dte_fecha = dte_fecha - racion_de_6h
    formato2 = "%Y-%m-%d"
    dte_fecha = dte_fecha.strftime(formato2)
    complementos = ET.SubElement(dem, "{" + xmlns + "}Complementos")
    complemento = ET.SubElement(
        complementos,
        "{" + xmlns + "}Complemento",
        IDComplemento=str(randint(1, 99999)),
        NombreComplemento=self.name,
        URIComplemento=cno,
    )
    if self.regimen_antiguo is False:
        ET.SubElement(
            complemento,
            "{" + cno + "}ReferenciasNota",
            FechaEmisionDocumentoOrigen=dte_fecha,
            MotivoAjuste=self.name,
            NumeroAutorizacionDocumentoOrigen=str(self.refund_invoice_id.uuid),
            NumeroDocumentoOrigen=str(self.refund_invoice_id.numero_dte),
            SerieDocumentoOrigen=str(self.refund_invoice_id.serie),
            Version="0.1",
        )
    if self.regimen_antiguo is True:
        ET.SubElement(
            complemento,
            "{" + cno + "}ReferenciasNota",
            FechaEmisionDocumentoOrigen=dte_fecha,
            RegimenAntiguo="Antiguo",
            MotivoAjuste=self.name,
            NumeroAutorizacionDocumentoOrigen=str(self.refund_invoice_id.uuid),
            NumeroDocumentoOrigen=str(self.refund_invoice_id.numero_dte),
            SerieDocumentoOrigen=str(self.refund_invoice_id.serie),
            Version="0.1",
        )
    # Adenda
    et = adendas.set_adendas(self, ET, doc, xmlns)
    cont = et.tostring(root, encoding="UTF-8", method="xml")
    buscar = "ns0"
    buscar2 = "ns2"
    rmpl = "dte"
    rmpl2 = "cno"
    cont = cont.decode("utf_8")
    cont = cont.replace(buscar, rmpl)
    cont = cont.replace(buscar2, rmpl2)
    cont = cont.encode("utf_8")
    dat = base64.b64encode(cont)
    return dat
