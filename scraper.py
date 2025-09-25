import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class FacturaParkScraper:
    def __init__(self):
        self.login_endpoint = "https://facturaandino.gopass.com.co/api/accc_auth/login"
        self.pending_urls = [
            "https://facturaandino.gopass.com.co/console/associatesManagement/invoicing/pendingEmit",
            "https://facturapark.centroandino.com.co/console/associatesManagement/invoicing/pendingEmit"
        ]
        self.session = requests.Session()
        self.auth_token = None

    def login(self, username: str, password: str, debug: bool = False) -> Dict:
        """
        Realiza POST con JSON {email, password}.
        Devuelve dict con keys: ok (bool), status_code, json (si aplica), text.
        """
        payload = {"email": username, "password": password}
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        result = {"ok": False, "status_code": None, "json": None, "text": None}

        try:
            r = self.session.post(self.login_endpoint, json=payload, headers=headers, timeout=12)
            result["status_code"] = r.status_code
            result["text"] = r.text[:500]  # truncar para logs

            # intentar parse JSON
            try:
                j = r.json()
                result["json"] = j
            except Exception:
                j = None

            # caso 200 -> analizar respuesta
            if r.status_code == 200:
                # buscar token en json
                token = None
                if isinstance(j, dict):
                    for k in ("token", "access_token", "accessToken", "data"):
                        if k in j and isinstance(j[k], str):
                            token = j[k]
                            break
                    if token is None and isinstance(j.get("data"), dict):
                        for tk in ("token", "access_token", "accessToken"):
                            if tk in j["data"]:
                                token = j["data"][tk]
                                break
                    # si backend devuelve success true
                    if token is None and (j.get("success") or j.get("ok") or j.get("status") in ("success", "ok")):
                        result["ok"] = True

                # si encontramos token
                if token:
                    self.auth_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    result["ok"] = True

                # fallback textual
                if not result["ok"] and ("console/home" in r.text or "console" in r.text):
                    result["ok"] = True

            return result

        except Exception as e:
            result["text"] = f"EXCEPTION: {e}"
            return result

    def get_pending_invoices(self) -> List[Dict]:
        for url in self.pending_urls:
            try:
                r = self.session.get(url, timeout=12)
            except Exception:
                continue
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator="\n")
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            for i, line in enumerate(lines):
                if "ANDINO" in line.upper():
                    for j in range(i+1, min(i+8, len(lines))):
                        nxt = lines[j]
                        digits = "".join([c for c in nxt if c.isdigit()])
                        if digits:
                            return [{"comercio": "ANDINO", "total_pendientes": digits, "source_url": url}]
                    digits = "".join([c for c in line if c.isdigit()])
                    if digits:
                        return [{"comercio": "ANDINO", "total_pendientes": digits, "source_url": url}]
        return []
