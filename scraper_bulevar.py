import requests
from typing import List, Dict, Any

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
        self.invoices_api = (
            "https://facturabulevar.gopass.com.co/api/trns_transparking/getcustom"
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
            rows = r.json().get("data", {}).get("rows", [])
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
            rows = r.json().get("data", {}).get("rows", [])
            return [
                {"nombre_job": row.get("jobname"), "ultima_actualizacion": row.get("updatedat")}
                for row in rows
            ]
        except Exception:
            return []

    def get_invoices(self) -> Dict[str, Any]:
        try:
            r = self.session.get(self.invoices_api, timeout=15)
            if r.status_code != 200:
                return {}
            j = r.json()
            total = j.get("data", {}).get("totalItems", 0)
            rows = j.get("data", {}).get("rows", [])
            if not rows:
                return {"total_facturas": total, "factura_reciente": {}}
            return {"total_facturas": total, "factura_reciente": rows[0]}
        except Exception:
            return {}
