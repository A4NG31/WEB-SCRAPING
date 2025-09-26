import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote

# Intentar usar zoneinfo (py3.9+). Si no está, caerá a UTC-5 manual.
try:
    from zoneinfo import ZoneInfo
    BOGOTA_TZ = ZoneInfo("America/Bogota")
except Exception:
    BOGOTA_TZ = None


class FacturaParkScraper:
    def __init__(self):
        self.login_endpoint = "https://facturaandino.gopass.com.co/api/accc_auth/login"
        self.pending_api = (
            "https://facturaandino.gopass.com.co/api/trns_invoices/pendingEmit"
            "?$top=10&$skip=0&$select=pending,idcommerce,name&$orderby=idserietype%20asc&additionalQuery="
        )
        self.jobs_api = (
            "https://facturaandino.gopass.com.co/api/genc_jobsconfig"
            "?$top=10&$skip=0&$select=jobname,updatedat&$orderby=idjob%20asc"
        )
        # invoices_api será construida dinámicamente en get_invoices()
        self.session = requests.Session()

    def _invoices_url_for_date(self, date_obj: datetime.date) -> str:
        """
        Construye la URL para consultar facturas para la fecha dada (date_obj).
        Usa el mismo formato de query que venías usando, con proper URL-encoding.
        """
        start = f"{date_obj.strftime('%Y-%m-%d')} 00:00:00 -5:00"
        end = f"{date_obj.strftime('%Y-%m-%d')} 23:59:59 -5:00"
        query = f"t.transdate between '{start}' and '{end}'"
        encoded = quote(query, safe="")
        url = (
            "https://facturaandino.gopass.com.co/api/trns_transparking/getcustom"
            f"?$top=10&$skip=0&additionalQuery={encoded}&headers=false"
        )
        return url

    def login(self, username: str, password: str) -> bool:
        payload = {"email": username, "password": password}
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        try:
            r = self.session.post(self.login_endpoint, json=payload, headers=headers, timeout=10)
            if r.status_code != 200:
                return False
            j = r.json()
            token = j.get("tokens", {}).get("access", {}).get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                return True
            return False
        except Exception:
            return False

    def get_pending_invoices(self) -> List[Dict]:
        try:
            r = self.session.get(self.pending_api, timeout=10)
            if r.status_code != 200:
                return []
            j = r.json()
            rows = j.get("data", {}).get("rows", [])
            return [
                {
                    "comercio": row.get("name"),
                    "total_pendientes": row.get("pending"),
                    "id_comercio": row.get("idcommerce"),
                }
                for row in rows
            ]
        except Exception:
            return []

    def get_jobs_config(self) -> List[Dict]:
        try:
            r = self.session.get(self.jobs_api, timeout=10)
            if r.status_code != 200:
                return []
            j = r.json()
            rows = j.get("data", {}).get("rows", [])
            return [
                {
                    "nombre_job": row.get("jobname"),
                    "ultima_actualizacion": row.get("updatedat"),
                }
                for row in rows
            ]
        except Exception:
            return []

    def get_invoices(self) -> Dict[str, Any]:
        """
        Devuelve la factura más reciente y el total de facturas para la FECHA ACTUAL (Bogotá).
        Normaliza los nombres de campo esperados por app.py.
        """
        try:
            # obtener "hoy" en zona Bogotá; si no está zoneinfo, restar 5h a UTC como fallback
            if BOGOTA_TZ:
                now = datetime.now(BOGOTA_TZ)
            else:
                now = datetime.utcnow() - timedelta(hours=5)
            today = now.date()

            url = self._invoices_url_for_date(today)
            r = self.session.get(url, timeout=20)
            if r.status_code != 200:
                return {}

            j = r.json()
            total_raw = j.get("data", {}).get("totalItems", 0)
            # normalizar total a int cuando venga como string
            try:
                total = int(total_raw)
            except Exception:
                try:
                    total = int(str(total_raw))
                except Exception:
                    total = total_raw

            rows = j.get("data", {}).get("rows", [])
            if not rows:
                return {"total_facturas": total, "factura_reciente": {}}

            factura = rows[0]  # la factura más reciente (según la respuesta)

            # Normalizar campos para app.py
            factura_normalizada = {
                "idinvoice": factura.get("idinvoice") or factura.get("id"),
                "idtransaction": factura.get("idtransaction"),
                "idtransparking": factura.get("idtransparking"),
                # transdate o fecha_factura dependiendo del payload
                "fecha_factura": factura.get("transdate") or factura.get("fecha_factura") or factura.get("transdateformat"),
                # valores numéricos/strings en distintos keys según el motor
                "valor_neto_factura": factura.get("valorneto") or factura.get("valor_neto_factura") or factura.get("netvalue"),
                "valor_factura": factura.get("valortotal") or factura.get("valor_factura") or factura.get("totalvalue"),
                "nombretercero": factura.get("tercero") or factura.get("nombretercero") or factura.get("name"),
                "outdate": factura.get("outdate"),
                "invoicestatus": factura.get("invoicestatus"),
                "cufe": factura.get("cufe"),
                # id_unico puede no venir; fallback a idinvoice
                "id_unico": factura.get("id_unico") or factura.get("idinvoice") or factura.get("id"),
            }

            return {"total_facturas": total, "factura_reciente": factura_normalizada}
        except Exception:
            return {}
