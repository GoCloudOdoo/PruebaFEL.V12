# -*- encoding: UTF-8 -*-

from odoo import api, models, fields, _
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta
import datetime as dt
import dateutil.parser
from dateutil.tz import gettz
from . import credit_note, invoice_cancel, nota_abono, web_service
from odoo.exceptions import UserError
import logging
import base64
from random import randint
import re

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    uuid = fields.Char(
        "Numero Autorizacion", readonly=True, states={"draft": [("readonly", False)]}
    )
    serie = fields.Char("Serie Fel", readonly=True, states={"draft": [("readonly", False)]})
    numero_dte = fields.Char(
        "Numero DTE", readonly=True, states={"draft": [("readonly", False)]}
    )
    dte_fecha = fields.Datetime(
        "Fecha Autorizacion", readonly=True, states={"draft": [("readonly", False)]}
    )
    cae = fields.Text("CAE", readonly=True, states={"draft": [("readonly", False)]})
    letras = fields.Text(
        "Total Letras", readonly=True, states={"draft": [("readonly", False)]}
    )
    tipo_f = fields.Selection(
        [
            ("normal", "Factura Normal"),
            ("cambiaria", "Factura Cambiaria"),
        ],
        string="Tipo Factura",
        default="normal",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    regimen_antiguo = fields.Boolean(
        string="Nota de credito rebajando regimen antiguo",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=False,
    )
    nota_abono = fields.Boolean(
        string="Nota de Abono",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=False,
    )
    retencion = fields.Float(
        string="Retencion ISR", readonly=True, states={"draft": [("readonly", False)]}
    )
    tipo_s = fields.Selection(
        [
            ("especial", "Factura Especial"),
        ],
        string="Tipo Factura Especial",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.multi
    def ver_factura(self):
        for invoice in self:
            uuid = invoice.uuid
            if not uuid:
                return False
        sitio = {
            "name": "Ver Factura",
            "res_model": "ir.actions.act_url",
            "type": "ir.actions.act_url",
            "target": "new",
            "url": "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid="
            + uuid,
        }
        return sitio

    @api.multi
    def action_invoice_open(self):
        if self.journal_id.is_eface is False:
            return super(AccountInvoice, self).action_invoice_open()
        res = super(AccountInvoice, self).action_invoice_open()
        if self.type == "out_invoice":
            if self.tipo_f == "normal":
                xml_data = self.set_data_for_invoice()
                self.letras = self.l10n_gt_edi_amount_to_text()
                cancel = False
                uuid, serie, numero_dte, dte_fecha = web_service.web_service(self,
                    xml_data, cancel
                )
                message = _("Facturacion Electronica %s: Serie %s  Numero %s") % (
                    self.tipo_f,
                    serie,
                    numero_dte,
                )
                self.message_post(body=message)
                self.uuid = uuid
                self.serie = serie
                self.numero_dte = numero_dte
                mytime = dateutil.parser.parse(dte_fecha)
                racion_de_6h = timedelta(hours=6)
                mytime = mytime + racion_de_6h
                formato2 = "%Y-%m-%d %H:%M:%S"
                mytime = mytime.strftime(formato2)
                self.dte_fecha = mytime

            if self.tipo_f == "cambiaria":
                xml_data = self.set_data_for_invoice_cambiaria()
                self.letras = self.l10n_gt_edi_amount_to_text()
                cancel = False
                uuid, serie, numero_dte, dte_fecha = web_service.web_service(self,
                    xml_data, cancel
                )
                message = _("Facturacion Electronica %s: Serie %s  Numero %s") % (
                    self.tipo_f,
                    serie,
                    numero_dte,
                )
                self.message_post(body=message)
                self.uuid = uuid
                self.serie = serie
                self.numero_dte = numero_dte
                mytime = dateutil.parser.parse(dte_fecha)
                racion_de_6h = timedelta(hours=6)
                mytime = mytime + racion_de_6h
                formato2 = "%Y-%m-%d %H:%M:%S"
                mytime = mytime.strftime(formato2)
                self.dte_fecha = mytime

        if self.type == "in_invoice":
            if self.tipo_s == "especial":
                xml_data = self.set_data_for_invoice_special()
                self.letras = self.l10n_gt_edi_amount_to_text()
                cancel = False
                uuid, serie, numero_dte, dte_fecha = web_service.web_service(self,
                    xml_data, cancel
                )
                message = _("Facturacion Electronica Especial: Serie %s  Numero %s") % (
                    serie,
                    numero_dte,
                )
                self.message_post(body=message)
                self.uuid = uuid
                self.serie = serie
                self.numero_dte = numero_dte
                mytime = dateutil.parser.parse(dte_fecha)
                racion_de_6h = timedelta(hours=6)
                mytime = mytime + racion_de_6h
                formato2 = "%Y-%m-%d %H:%M:%S"
                mytime = mytime.strftime(formato2)
                self.dte_fecha = mytime

        if self.type == "out_refund" and self.refund_invoice_id.uuid:
            xml_data = credit_note.set_data_for_invoice_credit(self)
            self.letras = self.l10n_gt_edi_amount_to_text()
            cancel = False
            uuid, serie, numero_dte, dte_fecha = web_service.web_service(
                self, xml_data, cancel
            )
            message = _("Nota de Credito: Serie %s  Numero %s") % (serie, numero_dte)
            self.message_post(body=message)
            self.uuid = uuid
            self.serie = serie
            self.numero_dte = numero_dte
            mytime = dateutil.parser.parse(dte_fecha)
            racion_de_6h = timedelta(hours=6)
            mytime = mytime + racion_de_6h
            formato2 = "%Y-%m-%d %H:%M:%S"
            mytime = mytime.strftime(formato2)
            self.dte_fecha = mytime

        if self.type == "out_refund" and self.nota_abono is True:
            xml_data = nota_abono.set_data_for_invoice_abono(self)
            self.letras = self.l10n_gt_edi_amount_to_text()
            cancel = False
            uuid, serie, numero_dte, dte_fecha = web_service.web_service(
                self, xml_data, cancel
            )
            message = _("Nota de Abono: Serie %s  Numero %s") % (serie, numero_dte)
            self.message_post(body=message)
            self.uuid = uuid
            self.serie = serie
            self.numero_dte = numero_dte
            mytime = dateutil.parser.parse(dte_fecha)
            racion_de_6h = timedelta(hours=6)
            mytime = mytime + racion_de_6h
            formato2 = "%Y-%m-%d %H:%M:%S"
            mytime = mytime.strftime(formato2)
            self.dte_fecha = mytime

        return res

    @api.multi
    def action_invoice_cancel(self):
        if self.journal_id.is_eface is False:
            return super(AccountInvoice, self).action_invoice_cancel()
        res = super(AccountInvoice, self).action_invoice_cancel()
        if self.type == "out_invoice" and self.uuid:
            xml_data = invoice_cancel.set_data_for_invoice_cancel(self)
            cancel = True
            uuid, serie, numero_dte, dte_fecha = web_service.web_service(
                self, xml_data, cancel
            )
            message = _("Factura Cancelada: Serie %s  Numero %s") % (serie, numero_dte, uuid, dte_fecha)
            self.message_post(body=message)

        if self.type == "out_refund" and self.uuid:
            xml_data = invoice_cancel.set_data_for_invoice_cancel(self)
            cancel = True
            uuid, serie, numero_dte, dte_fecha = web_service.web_service(
                self, xml_data, cancel
            )
            message = _("Nota Cancelada: Serie %s  Numero %s") % (serie, numero_dte)
            self.message_post(body=message)

        return res

    @api.multi
    def set_data_for_invoice(self):

        xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemalocationn = "http://www.sat.gob.gt/dte/fel/0.2.0"
        root = ET.Element(
            "{" + xmlns + "}GTDocumento",
            Version="0.1",
            attrib={"{" + xsi + "}schemaLocation": schemalocationn},
        )
        doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
        dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
        dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
        fecha_emisionn = dt.datetime.now(gettz("America/Guatemala")).__format__(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        ET.SubElement(
            dem,
            "{" + xmlns + "}DatosGenerales",
            CodigoMoneda="GTQ",
            FechaHoraEmision=fecha_emisionn,
            Tipo="FACT",
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
            CorreoEmisor=self.company_id.email or "",
            NITEmisor=self.company_id.vat or "",
            NombreComercial=api_fel.nombre,
            NombreEmisor=self.company_id.name,
        )
        dire = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
        ET.SubElement(dire, "{" + xmlns + "}Direccion").text = api_fel.direccion or ""
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
            vat = self.partner_id.vat
            vat = re.sub(r"[\?!:/;. -]","", vat)
            nit = vat.upper()
        else:
            vat = "CF"

        rece = ET.SubElement(
            dem,
            "{" + xmlns + "}Receptor",
            CorreoReceptor=self.partner_id.email or "",
            IDReceptor=nit,
            NombreReceptor=self.partner_id.name,
        )
        direc_n = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
        ET.SubElement(direc_n, "{" + xmlns + "}Direccion").text = (
            self.partner_id.street or "Ciudad"
        )
        ET.SubElement(direc_n, "{" + xmlns + "}CodigoPostal").text = (
            self.partner_id.zip or "01009"
        )
        ET.SubElement(direc_n, "{" + xmlns + "}Municipio").text = (
            self.partner_id.city or "Guatemala"
        )
        ET.SubElement(direc_n, "{" + xmlns + "}Departamento").text = (
            self.partner_id.state_id.name or "Guatemala"
        )
        ET.SubElement(direc_n, "{" + xmlns + "}Pais").text = (
            self.partner_id.country_id.code or "GT"
        )

        # Frases
        fra = ET.SubElement(dem, "{" + xmlns + "}Frases")
        ET.SubElement(
            fra,
            "{" + xmlns + "}Frase",
            TipoFrase=self.company_id.tipo,
            CodigoEscenario=self.company_id.codigo,
        )
        invoice_line = self.invoice_line_ids
        cg = 0
        for line_id in invoice_line:
            if (
                self.partner_id.tax_partner is True
                and line_id.product_id.tax_product is True
            ):
                if cg == 0:
                    ET.SubElement(
                        fra, "{" + xmlns + "}Frase", TipoFrase="4", CodigoEscenario="11"
                    )
                    cg += 1

        items = ET.SubElement(dem, "{" + xmlns + "}Items")
        cnt = 0
        # LineasFactura
        for line in invoice_line:
            cnt += 1
            bo = "B"
            if line.product_id.type == "service":
                bo = "S"

            # Item
            item = ET.SubElement(
                items, "{" + xmlns + "}Item", BienOServicio=bo, NumeroLinea=str(cnt)
            )

            ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
            ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = (
                str(line.product_id.default_code) + "|" + str(line.product_id.name)
            )
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(
                line.price_unit
            )
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(
                round(line.quantity * line.price_unit, 2)
            )
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(
                round((line.discount * (line.quantity * line.price_unit)) / 100, 2)
            )

            tax = "IVA"
            if line.invoice_line_tax_ids:
                tax = "IVA"
            elif (
                self.partner_id.tax_partner is True
                and line.product_id.tax_product is True
            ):
                tax = "IVA"
            else:
                raise UserError(
                    _("Las líneas de Factura deben de llevar impuesto (IVA).")
                )

            impuestos = ET.SubElement(item, "{" + xmlns + "}Impuestos")
            impuesto = ET.SubElement(impuestos, "{" + xmlns + "}Impuesto")
            price_tax = line.price_total - line.price_subtotal
            price_tax = str(round(price_tax, 2))
            unidadgravable = "1"
            subtotal = str(round(line.price_subtotal, 2))
            if (
                self.partner_id.tax_partner is True
                and line.product_id.tax_product is True
            ):
                unidadgravable = "2"
                price_tax = "0.00"
            ET.SubElement(impuesto, "{" + xmlns + "}NombreCorto").text = tax
            ET.SubElement(
                impuesto, "{" + xmlns + "}CodigoUnidadGravable"
            ).text = unidadgravable
            ET.SubElement(impuesto, "{" + xmlns + "}MontoGravable").text = subtotal
            ET.SubElement(impuesto, "{" + xmlns + "}MontoImpuesto").text = price_tax
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

        # Adenda
        ade = ET.SubElement(doc, "{" + xmlns + "}Adenda")
        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), "%Y-%m-%d")
        formato2 = "%d-%m-%Y"
        date_due = date_due.strftime(formato2)
        phone = " "
        mobile = " "
        if self.partner_id.phone:
            phone = self.partner_id.phone
        if self.partner_id.mobile:
            mobile = self.partner_id.mobile
        telefono = phone + " " + mobile
        ET.SubElement(ade, "FECHA_VENCIMIENTO").text = date_due or ""
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name or ""
        ET.SubElement(ade, "NOTAS").text = self.comment or ""
        ET.SubElement(ade, "REFERENCIA").text = self.reference or ""
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name or ""
        ET.SubElement(ade, "ORIGEN").text = self.origin or ""
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name or ""
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number or ""
        ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name or ""
        ET.SubElement(ade, "TELEFONO").text = telefono
        cont = ET.tostring(root, encoding="UTF-8", method="xml")
        buscar = "ns0"
        rmpl = "dte"
        cont = cont.decode("utf_8")
        cont = cont.replace(buscar, rmpl)
        cont = cont.encode("utf_8")
        dat = base64.b64encode(cont)
        return dat

    @api.multi
    def set_data_for_invoice_cambiaria(self):

        xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        sschemalocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
        cno = "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0"
        uri = "http://www.sat.gob.gt/fel/cambiaria.xsd"

        root = ET.Element(
            "{" + xmlns + "}GTDocumento",
            Version="0.1",
            attrib={"{" + xsi + "}schemaLocation": sschemalocation},
        )
        doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
        dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
        dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
        ffecha_emision = dt.datetime.now(gettz("America/Guatemala")).__format__(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        ET.SubElement(
            dem,
            "{" + xmlns + "}DatosGenerales",
            CodigoMoneda="GTQ",
            FechaHoraEmision=ffecha_emision,
            Tipo="FCAM",
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
            CorreoEmisor=self.company_id.email or "",
            NITEmisor=self.company_id.vat or "",
            NombreComercial=api_fel.nombre,
            NombreEmisor=self.company_id.name,
        )
        dire_c = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
        ET.SubElement(dire_c, "{" + xmlns + "}Direccion").text = api_fel.direccion
        ET.SubElement(dire_c, "{" + xmlns + "}CodigoPostal").text = (
            self.company_id.zip or "01009"
        )
        ET.SubElement(dire_c, "{" + xmlns + "}Municipio").text = (
            self.company_id.city or "Guatemala"
        )
        ET.SubElement(dire_c, "{" + xmlns + "}Departamento").text = (
            self.company_id.state_id.name or "Guatemala"
        )
        ET.SubElement(dire_c, "{" + xmlns + "}Pais").text = (
            self.company_id.country_id.code or "GT"
        )

        if self.partner_id.vat:
            vat = self.partner_id.vat
            vat = re.sub(r"[\?!:/;. -]","", vat)
            vt = vat.upper()
        else:
            vt = "CF"

        rece = ET.SubElement(
            dem,
            "{" + xmlns + "}Receptor",
            CorreoReceptor=self.partner_id.email or "",
            IDReceptor=vt,
            NombreReceptor=self.partner_id.name,
        )
        direc_c = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
        ET.SubElement(direc_c, "{" + xmlns + "}Direccion").text = (
            self.partner_id.street or "Ciudad"
        )
        ET.SubElement(direc_c, "{" + xmlns + "}CodigoPostal").text = (
            self.partner_id.zip or "01009"
        )
        ET.SubElement(direc_c, "{" + xmlns + "}Municipio").text = (
            self.partner_id.city or "Guatemala"
        )
        ET.SubElement(direc_c, "{" + xmlns + "}Departamento").text = (
            self.partner_id.state_id.name or "Guatemala"
        )
        ET.SubElement(direc_c, "{" + xmlns + "}Pais").text = (
            self.partner_id.country_id.code or "GT"
        )

        # Frases
        fra = ET.SubElement(dem, "{" + xmlns + "}Frases")
        ET.SubElement(
            fra,
            "{" + xmlns + "}Frase",
            TipoFrase=self.company_id.tipo,
            CodigoEscenario=self.company_id.codigo,
        )

        invoice_line = self.invoice_line_ids
        items = ET.SubElement(dem, "{" + xmlns + "}Items")
        cnt = 0
        # LineasFactura
        for line in invoice_line:
            cnt += 1
            bos = "B"
            if line.product_id.type == "service":
                bos = "S"

            # Item
            item = ET.SubElement(
                items, "{" + xmlns + "}Item", BienOServicio=bos, NumeroLinea=str(cnt)
            )

            ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
            ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = (
                str(line.product_id.default_code) + " |" + str(line.product_id.name)
            )
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(
                line.price_unit
            )
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(
                line.quantity * line.price_unit
            )
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(
                round((line.discount * (line.quantity * line.price_unit)) / 100, 2)
            )

            if line.invoice_line_tax_ids:
                tax = "IVA"
            else:
                raise UserError(
                    _("Las líneas de Factura deben de llevar impuesto (IVA).")
                )

            impuestosss = ET.SubElement(item, "{" + xmlns + "}Impuestos")
            impuest = ET.SubElement(impuestosss, "{" + xmlns + "}Impuesto")
            price_tax = line.price_total - line.price_subtotal
            ET.SubElement(impuest, "{" + xmlns + "}NombreCorto").text = tax
            ET.SubElement(impuest, "{" + xmlns + "}CodigoUnidadGravable").text = "1"
            ET.SubElement(impuest, "{" + xmlns + "}MontoGravable").text = str(
                round(line.price_subtotal, 2)
            )
            ET.SubElement(impuest, "{" + xmlns + "}MontoImpuesto").text = str(
                round(price_tax, 2)
            )
            ET.SubElement(item, "{" + xmlns + "}Total").text = str(
                round(line.price_total, 2)
            )
        # Totales
        tootales = ET.SubElement(dem, "{" + xmlns + "}Totales")
        timpuestos = ET.SubElement(tootales, "{" + xmlns + "}TotalImpuestos")
        ET.SubElement(
            timpuestos,
            "{" + xmlns + "}TotalImpuesto",
            NombreCorto="IVA",
            TotalMontoImpuesto=str(round(self.amount_tax, 2)),
        )
        ET.SubElement(tootales, "{" + xmlns + "}GranTotal").text = str(
            round(self.amount_total, 2)
        )

        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), "%Y-%m-%d")
        formato2 = "%Y-%m-%d"
        date_due = date_due.strftime(formato2)
        complementos = ET.SubElement(dem, "{" + xmlns + "}Complementos")
        complemento = ET.SubElement(
            complementos,
            "{" + xmlns + "}Complemento",
            IDComplemento=str(randint(1, 99999)),
            NombreComplemento="AbonosFacturaCambiaria",
            URIComplemento=uri,
        )
        retenciones = ET.SubElement(
            complemento, "{" + cno + "}AbonosFacturaCambiaria", Version="1"
        )
        abono = ET.SubElement(retenciones, "{" + cno + "}Abono")
        ET.SubElement(abono, "{" + cno + "}NumeroAbono").text = "1"
        ET.SubElement(abono, "{" + cno + "}FechaVencimiento").text = date_due
        ET.SubElement(abono, "{" + cno + "}MontoAbono").text = str(
            round(self.amount_total, 2)
        )
        # Adenda
        ade = ET.SubElement(doc, "{" + xmlns + "}Adenda")
        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), "%Y-%m-%d")
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
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name or ""
        ET.SubElement(ade, "NOTAS").text = self.comment or ""
        ET.SubElement(ade, "REFERENCIA").text = self.reference or ""
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name or ""
        ET.SubElement(ade, "ORIGEN").text = self.origin or ""
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number or ""
        ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name
        ET.SubElement(ade, "TELEFONO").text = telefono

        cont = ET.tostring(root, encoding="UTF-8", method="xml")
        buscar = "ns0"
        buscar2 = "ns2"
        rmpl = "dte"
        rmpl2 = "cfc"
        cont = cont.decode("utf_8")
        cont = cont.replace(buscar, rmpl)
        cont = cont.replace(buscar2, rmpl2)
        cont = cont.encode("utf_8")
        dat = base64.b64encode(cont)
        return dat

    @api.multi
    def set_data_for_invoice_special(self):

        xmlns = "http://www.sat.gob.gt/dte/fel/0.2.0"
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        scheemalocation = "http://www.sat.gob.gt/dte/fel/0.2.0"
        cno = "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0"

        root = ET.Element(
            "{" + xmlns + "}GTDocumento",
            Version="0.1",
            attrib={"{" + xsi + "}schemaLocation": scheemalocation},
        )
        doc = ET.SubElement(root, "{" + xmlns + "}SAT", ClaseDocumento="dte")
        dte = ET.SubElement(doc, "{" + xmlns + "}DTE", ID="DatosCertificados")
        dem = ET.SubElement(dte, "{" + xmlns + "}DatosEmision", ID="DatosEmision")
        fechaa_emision = dt.datetime.now(gettz("America/Guatemala")).__format__(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        ET.SubElement(
            dem,
            "{" + xmlns + "}DatosGenerales",
            CodigoMoneda="GTQ",
            FechaHoraEmision=fechaa_emision,
            Tipo="FESP",
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
            CorreoEmisor=self.company_id.email or "",
            NITEmisor=self.company_id.vat or "",
            NombreComercial=api_fel.nombre,
            NombreEmisor=self.company_id.name,
        )
        dire_s = ET.SubElement(emi, "{" + xmlns + "}DireccionEmisor")
        ET.SubElement(dire_s, "{" + xmlns + "}Direccion").text = api_fel.direccion
        ET.SubElement(dire_s, "{" + xmlns + "}CodigoPostal").text = (
            self.company_id.zip or "01009"
        )
        ET.SubElement(dire_s, "{" + xmlns + "}Municipio").text = (
            self.company_id.city or "Guatemala"
        )
        ET.SubElement(dire_s, "{" + xmlns + "}Departamento").text = (
            self.company_id.state_id.name or "Guatemala"
        )
        ET.SubElement(dire_s, "{" + xmlns + "}Pais").text = (
            self.company_id.country_id.code or "GT"
        )

        if self.partner_id.vat:
            vat = self.partner_id.vat
            vat = re.sub(r"[\?!:/;. -]","", vat)
            vat_nit = vat.upper()
        else:
            vat_nit = "CF"

        rece = ET.SubElement(
            dem,
            "{" + xmlns + "}Receptor",
            CorreoReceptor=self.partner_id.email or "",
            IDReceptor=vat_nit,
            NombreReceptor=self.partner_id.name,
        )
        direc_s = ET.SubElement(rece, "{" + xmlns + "}DireccionReceptor")
        ET.SubElement(direc_s, "{" + xmlns + "}Direccion").text = (
            self.partner_id.street or "Ciudad"
        )
        ET.SubElement(direc_s, "{" + xmlns + "}CodigoPostal").text = (
            self.partner_id.zip or "01009"
        )
        ET.SubElement(direc_s, "{" + xmlns + "}Municipio").text = (
            self.partner_id.city or "Guatemala"
        )
        ET.SubElement(direc_s, "{" + xmlns + "}Departamento").text = (
            self.partner_id.state_id.name or "Guatemala"
        )
        ET.SubElement(direc_s, "{" + xmlns + "}Pais").text = (
            self.partner_id.country_id.code or "GT"
        )

        invoice_l = self.invoice_line_ids
        items = ET.SubElement(dem, "{" + xmlns + "}Items")
        cnt = 0
        # LineasFactura
        for line in invoice_l:
            cnt += 1
            bss = "B"
            if line.product_id.type == "service":
                bss = "S"

            # Item
            item = ET.SubElement(
                items, "{" + xmlns + "}Item", BienOServicio=bss, NumeroLinea=str(cnt)
            )

            ET.SubElement(item, "{" + xmlns + "}Cantidad").text = str(line.quantity)
            ET.SubElement(item, "{" + xmlns + "}UnidadMedida").text = "UND"
            ET.SubElement(item, "{" + xmlns + "}Descripcion").text = (
                str(line.product_id.default_code) + "|" + str(line.product_id.name)
            )
            ET.SubElement(item, "{" + xmlns + "}PrecioUnitario").text = str(
                line.price_unit
            )
            ET.SubElement(item, "{" + xmlns + "}Precio").text = str(
                line.quantity * line.price_unit
            )
            ET.SubElement(item, "{" + xmlns + "}Descuento").text = str(
                round((line.discount * (line.quantity * line.price_unit)) / 100, 2)
            )

            if line.invoice_line_tax_ids:
                tax = "IVA"
            else:
                raise UserError(
                    _("Las líneas de Factura deben de llevar impuesto (IVA).")
                )

            impuestoss = ET.SubElement(item, "{" + xmlns + "}Impuestos")
            impuestoo = ET.SubElement(impuestoss, "{" + xmlns + "}Impuesto")
            price_tax = line.price_total - line.price_subtotal
            ET.SubElement(impuestoo, "{" + xmlns + "}NombreCorto").text = tax
            ET.SubElement(impuestoo, "{" + xmlns + "}CodigoUnidadGravable").text = "1"
            ET.SubElement(impuestoo, "{" + xmlns + "}MontoGravable").text = str(
                round(line.price_subtotal, 2)
            )
            ET.SubElement(impuestoo, "{" + xmlns + "}MontoImpuesto").text = str(
                round(price_tax, 2)
            )
            ET.SubElement(item, "{" + xmlns + "}Total").text = str(
                round(line.price_total, 2)
            )
        # Totales
        totaless = ET.SubElement(dem, "{" + xmlns + "}Totales")
        timpuestos = ET.SubElement(totaless, "{" + xmlns + "}TotalImpuestos")
        ET.SubElement(
            timpuestos,
            "{" + xmlns + "}TotalImpuesto",
            NombreCorto="IVA",
            TotalMontoImpuesto=str(round(self.amount_tax, 2)),
        )
        ET.SubElement(totaless, "{" + xmlns + "}GranTotal").text = str(
            round(self.amount_total, 2)
        )

        # Complementos
        complementos = ET.SubElement(dem, "{" + xmlns + "}Complementos")
        complemento = ET.SubElement(
            complementos,
            "{" + xmlns + "}Complemento",
            IDComplemento=str(randint(1, 99999)),
            NombreComplemento="FacturaEspecial",
            URIComplemento=cno,
        )
        retenciones = ET.SubElement(
            complemento, "{" + cno + "}RetencionesFacturaEspecial", Version="1"
        )
        ET.SubElement(retenciones, "{" + cno + "}RetencionISR").text = str(
            round(self.retencion, 2)
        )
        ET.SubElement(retenciones, "{" + cno + "}RetencionIVA").text = str(
            round(self.amount_tax, 2)
        )
        ET.SubElement(retenciones, "{" + cno + "}TotalMenosRetenciones").text = str(
            round(self.amount_untaxed - self.retencion, 2)
        )
        # Adenda
        ade = ET.SubElement(doc, "{" + xmlns + "}Adenda")
        date_due = self.date_due
        date_due = datetime.strptime(str(date_due), "%Y-%m-%d")
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
        ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name or ""
        ET.SubElement(ade, "NOTAS").text = self.comment or ""
        ET.SubElement(ade, "REFERENCIA").text = self.reference or ""
        ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name or ""
        ET.SubElement(ade, "ORIGEN").text = self.origin or ""
        ET.SubElement(ade, "VENDEDOR").text = self.user_id.name
        ET.SubElement(ade, "NUMERO-INTERNO").text = self.number or ""
        ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name
        ET.SubElement(ade, "TELEFONO").text = telefono

        cont = ET.tostring(root, encoding="UTF-8", method="xml")
        buscar = "ns0"
        rmpl = "dte"
        buscar2 = "ns2"
        rmpl2 = "cfe"
        cont = cont.decode("utf_8")
        cont = cont.replace(buscar, rmpl)
        cont = cont.replace(buscar2, rmpl2)
        cont = cont.encode("utf_8")
        dat = base64.b64encode(cont)
        return dat

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
        words = self.currency_id.with_context(
            lang=self.partner_id.lang or "es_ES"
        ).amount_to_text(amount_i)
        invoice_words = "%(words)s %(amount_d)02d/100" % dict(
            words=words, amount_d=amount_d
        )
        return invoice_words
