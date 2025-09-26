import requests
from typing import List, Dict, Any

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
        self.invoices_api = (
            "https://facturaandino.gopass.com.co/api/trns_transparking/getcustom"
            "?$top=10&$skip=0&additionalQuery=t.transdate%20between%20%272025-09-25%2000%3A00%3A00%20-5%3A00%27"
            "%20and%20%272025-09-25%2023:59:59%20-5:00%27&headers=false"
        )
        self.session = requests.Session()

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
        """Devuelve la factura más reciente y el total de facturas, con campos normalizados."""
        try:
            r = self.session.get(self.invoices_api, timeout=15)
            if r.status_code != 200:
                return {}
            j = r.json()
            total = int(j.get("data", {}).get("totalItems", 0))
            rows = j.get("data", {}).get("rows", [])

            if not rows:
                return {"total_facturas": total, "factura_reciente": {}}

            factura = rows[0]  # la más reciente (viene ordenada)

            factura_normalizada = {
                "idinvoice": factura.get("idinvoice"),
                "idtransaction": factura.get("idtransaction"),
                "idtransparking": factura.get("idtransparking"),
                "fecha_factura": factura.get("transdate") or factura.get("fecha_factura"),
                "valor_neto_factura": factura.get("valorneto") or factura.get("valor_neto_factura"),
                "valor_factura": factura.get("valortotal") or factura.get("valor_factura"),
                "nombretercero": factura.get("tercero") or factura.get("nombretercero"),
                "outdate": factura.get("outdate"),
                "invoicestatus": factura.get("invoicestatus"),
                "cufe": factura.get("cufe"),
                "id_unico": factura.get("id_unico") or factura.get("idinvoice"),
            }

            return {"total_facturas": total, "factura_reciente": factura_normalizada}
        except Exception as e:
            return {}

