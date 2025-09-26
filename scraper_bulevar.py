import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote

try:
    from zoneinfo import ZoneInfo
    BOGOTA_TZ = ZoneInfo("America/Bogota")
except Exception:
    BOGOTA_TZ = None


class FacturaBulevarScraper:
    def __init__(self):
        self.login_endpoint = "https://facturabulevar.gopass.com.co/api/accc_auth/login"
        self.pending_api = (
            "https://facturabulevar.gopass.com.co/api/trns_invoices/pendingEmit"
            "?$top=10&$skip=0&$select=pending,idcommerce,name&$orderby=idserietype%20asc&additionalQuery="
        )
        self.jobs_api = (
            "https://facturabulevar.gopass.com.co/api/genc_jobsconfig"
            "?$top=10&$skip=0&$select=jobname,updatedat&$orderby=idjob%20asc"
        )
        self.session = requests.Session()

    def _invoices_url_for_date(self, date_obj: datetime.date) -> str:
        start = f"{date_obj.strftime('%Y-%m-%d')} 00:00:00 -5:00"
        end = f"{date_obj.strftime('%Y-%m-%d')} 23:59:59 -5:00"
        query = f"t.transdate between '{start}' and '{end}'"
        encoded = quote(query, safe="")
        return (
            "https://facturabulevar.gopass.com.co/api/trns_transparking/getcustom"
            f"?$top=10&$skip=0&additionalQuery={encoded}&headers=false"
        )

    def login(self, username: str, password: str) -> bool:
        try:
            payload = {"email": username, "password": password}
            r = self.session.post(self.login_endpoint, json=payload, timeout=10)
            if r.status_code != 200:
                return False
            token = r.json().get("tokens", {}).get("access", {}).get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                return True
        except Exception:
            pass
        return False

    def get_pending_invoices(self) -> List[Dict]:
        try:
            r = self.session.get(self.pending_api, timeout=10)
            rows = r.json().get("data", {}).get("rows", [])
            return [
                {"comercio": row.get("name"), "total_pendientes": row.get("pending"), "id_comercio": row.get("idcommerce")}
                for row in rows
            ]
        except Exception:
            return []

    def get_jobs_config(self) -> List[Dict]:
        try:
            r = self.session.get(self.jobs_api, timeout=10)
            rows = r.json().get("data", {}).get("rows", [])
            return [{"nombre_job": row.get("jobname"), "ultima_actualizacion": row.get("updatedat")} for row in rows]
        except Exception:
            return []

    def get_invoices(self) -> Dict[str, Any]:
        try:
            now = datetime.now(BOGOTA_TZ) if BOGOTA_TZ else datetime.utcnow() - timedelta(hours=5)
            url = self._invoices_url_for_date(now.date())
            r = self.session.get(url, timeout=20)
            j = r.json()
            total = int(j.get("data", {}).get("totalItems", 0))
            rows = j.get("data", {}).get("rows", [])
            if not rows:
                return {"total_facturas": total, "factura_reciente": {}}

            f = rows[0]
            factura = {
                "idinvoice": f.get("idinvoice") or f.get("id"),
                "idtransaction": f.get("idtransaction"),
                "idtransparking": f.get("idtransparking"),
                "fecha_factura": f.get("transdate") or f.get("fecha_factura"),
                "valor_neto_factura": f.get("valorneto") or f.get("netvalue"),
                "valor_factura": f.get("valortotal") or f.get("totalvalue"),
                "nombretercero": f.get("tercero") or f.get("nombretercero") or f.get("name"),
                "outdate": f.get("outdate"),
                "invoicestatus": f.get("invoicestatus"),
                "cufe": f.get("cufe"),
                "id_unico": f.get("id_unico") or f.get("idinvoice") or f.get("id"),
            }
            return {"total_facturas": total, "factura_reciente": factura}
        except Exception:
            return {}
