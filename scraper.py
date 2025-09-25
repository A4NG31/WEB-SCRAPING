import requests
from typing import List, Dict


class FacturaParkScraper:
    def __init__(self):
        self.login_endpoint = "https://facturaandino.gopass.com.co/api/accc_auth/login"
        self.pending_api = "https://facturaandino.gopass.com.co/api/invoicing/pendingEmit?top=10&skip=0"
        self.session = requests.Session()

    def login(self, username: str, password: str) -> bool:
        """Inicia sesión contra el endpoint de login"""
        payload = {"email": username, "password": password}
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        try:
            r = self.session.post(self.login_endpoint, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                j = r.json()
                # si viene token en la respuesta, agregarlo al header
                token = None
                if isinstance(j, dict):
                    token = j.get("token") or j.get("access_token") or j.get("accessToken")
                    if not token and isinstance(j.get("data"), dict):
                        token = j["data"].get("token")
                if token:
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                return True
            return False
        except Exception:
            return False

    def get_pending_invoices(self) -> List[Dict]:
        """Consulta facturas pendientes vía API y retorna lista de dicts"""
        try:
            r = self.session.get(self.pending_api, timeout=10)
            if r.status_code != 200:
                return []
            j = r.json()
            data = j.get("data", {})
            rows = data.get("rows", [])
            result = []
            for row in rows:
                result.append({
                    "comercio": row.get("name"),
                    "total_pendientes": row.get("pending"),
                    "id_comercio": row.get("idcommerce")
                })
            return result
        except Exception:
            return []
