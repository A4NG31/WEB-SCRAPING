import requests
from typing import List, Dict

class FacturaParkScraper:
    def __init__(self):
        self.login_endpoint = "https://facturaandino.gopass.com.co/api/accc_auth/login"
        self.pending_api = (
            "https://facturaandino.gopass.com.co/api/trns_invoices/pendingEmit"
            "?$top=10&$skip=0&$select=pending,idcommerce,name&$orderby=idserietype%20asc&additionalQuery="
        )
        self.session = requests.Session()

    def login(self, username: str, password: str) -> bool:
        """Login con email y password, guarda el Bearer token en headers."""
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
        """Consulta facturas pendientes vía API trns_invoices."""
        try:
            r = self.session.get(self.pending_api, timeout=10)
            if r.status_code != 200:
                return []
            j = r.json()
            rows = j.get("data", {}).get("rows", [])
            result = []
            for row in rows:
                result.append({
                    "comercio": row.get("name"),
                    "total_pendientes": row.get("pending"),
                    "id_comercio": row.get("idcommerce"),
                })
            return result
        except Exception:
            return []
