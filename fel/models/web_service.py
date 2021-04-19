# -*- encoding: UTF-8 -*-

from odoo import api, _
from random import randint
import requests
import json
from odoo.exceptions import UserError


@api.multi
def web_service(self, xml_data, cancel):
    api_fel = self.env["api.data.configuration"].search(
        [("code_est", "=", self.journal_id.code_est)], limit=1
    )
    if not api_fel:
        return False
    xml = xml_data
    url = api_fel.url_firma
    ran = str(randint(1, 99999))
    if cancel is True:
        anular = "S"
        url_cert = api_fel.url_anulacion
    else:
        anular = "N"
        url_cert = api_fel.url_certificado
    data_send = {
        "llave": api_fel.key_firma,
        "archivo": xml,
        "codigo": ran,
        "alias": api_fel.user,
        "es_anulacion": anular,
    }

    response = requests.request("POST", url, data=data_send)
    rp = response.json()

    dt = rp["archivo"]
    payload = {
        "nit_emisor": self.company_id.vat,
        "correo_copia": self.company_id.email,
        "xml_dte": dt,
    }

    ident = str(randint(1111111, 9999999))
    headers = {
        "usuario": api_fel.user,
        "llave": api_fel.key_certificado,
        "content-type": "application/json",
        "identificador": ident,
    }

    response = requests.request("POST", url_cert, data=json.dumps(payload), headers=headers)

    rp = response.json()
    uuid = rp["uuid"]
    serie = rp["serie"]
    numero_dte = rp["numero"]
    dte_fecha = rp["fecha"]
    cantidad_errores = rp["cantidad_errores"]
    descripcion_errores = rp["descripcion_errores"]
    if cantidad_errores > 0:
        raise UserError(
            _(
                "No se puede certificar la factura\n Error No:%s\n %s."
                % (cantidad_errores, descripcion_errores)
            )
        )
    return uuid, serie, numero_dte, dte_fecha
