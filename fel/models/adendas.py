# -*- encoding: UTF-8 -*-

from odoo import api
from datetime import datetime

@api.multi
def set_adendas(self, et, doc, xmlns):

    ade = et.SubElement(doc, "{" + xmlns + "}Adenda")
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
    et.SubElement(ade, "FECHA_VENCIMIENTO").text = date_due
    et.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name
    et.SubElement(ade, "NOTAS").text = self.comment
    et.SubElement(ade, "REFERENCIA").text = self.reference
    et.SubElement(ade, "INCOTERM").text = self.incoterm_id.name
    et.SubElement(ade, "ORIGEN").text = self.origin
    et.SubElement(ade, "VENDEDOR").text = self.user_id.name
    et.SubElement(ade, "NUMERO-INTERNO").text = self.number
    et.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name
    et.SubElement(ade, "TELEFONO").text = telefono

    return et
