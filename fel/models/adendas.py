# -*- encoding: UTF-8 -*-

from odoo import api
from datetime import datetime



@api.multi
def set_adendas(self, ET, doc, xmlns):

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
    ET.SubElement(ade, "DIAS_CREDITO").text = self.payment_term_id.name
    ET.SubElement(ade, "NOTAS").text = self.comment
    ET.SubElement(ade, "REFERENCIA").text = self.reference
    ET.SubElement(ade, "INCOTERM").text = self.incoterm_id.name
    ET.SubElement(ade, "ORIGEN").text = self.origin
    ET.SubElement(ade, "VENDEDOR").text = self.user_id.name
    ET.SubElement(ade, "NUMERO-INTERNO").text = self.number
    ET.SubElement(ade, "REFERENCIA-CLIENTE").text = self.name
    ET.SubElement(ade, "TELEFONO").text = telefono

    return ET
