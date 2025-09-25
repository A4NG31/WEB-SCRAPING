import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class FacturaParkScraper:
    def __init__(self):
        # Endpoint observado en DevTools
        self.login_endpoint = "https://facturaandino.gopass.com.co/api/accc_auth/login"
        # Página de facturas pendientes (intento en el dominio público)
        self.pending_urls = [
            "https://facturaandino.gopass.com.co/console/associatesManagement/invoicing/pendingEmit",
            "https://facturapark.centroandino.com.co/console/associatesManagement/invoicing/pendingEmit"
        ]
        self.session = requests.Session()
        self.auth_token = None

    def _try_post_login(self, payload: dict, as_json=True) -> Optional[requests.Response]:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            if as_json:
                r = self.session.post(self.login_endpoint, json=payload, headers=headers, timeout=10)
            else:
                r = self.session.post(self.login_endpoint, data=payload, headers=headers, timeout=10)
            return r
        except Exception:
            return None

    def login(self, username: str, password: str) -> bool:
        """Intenta login probando varios payloads comunes y busca token en la respuesta."""
        candidates = [
            {"username": username, "password": password},
            {"email": username, "password": password},
            {"user": username, "password": password},
            {"email": username, "password": password, "remember": "true"},
        ]

        for payload in candidates:
            # probar como JSON
            r = self._try_post_login(payload, as_json=True)
            if r is None:
                continue

            # Si recibimos 200, intentar detectar token
            if r.status_code == 200:
                # 1) intentar JSON parse
                try:
                    j = r.json()
                except Exception:
                    j = None

                # buscar claves comunes de token
                token = None
                if isinstance(j, dict):
                    for k in ("token", "access_token", "accessToken", "data"):
                        if k in j and isinstance(j[k], str):
                            token = j[k]
                            break
                    # si data es dict con token dentro
                    if token is None and isinstance(j.get("data"), dict):
                        for tk in ("token", "access_token", "accessToken"):
                            if tk in j["data"]:
                                token = j["data"][tk]
                                break

                    # algunas APIs devuelven {success: True}
                    if token is None and (j.get("success") or j.get("ok") or j.get("status") == "success"):
                        # asumimos login correcto si hay success
                        self.auth_token = None
                        return True

                # 2) si hay token, guardarlo en headers
                if token:
                    self.auth_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    return True

                # 3) si no hay JSON pero r.text contiene indicador 'console' o 'home', considerarlo éxito
                if "console/home" in r.text or "console" in r.text:
                    return True

            # si status != 200 quizá hay mensaje de error; continuar probando
        return False

    def get_pending_invoices(self) -> List[Dict]:
        """Intenta acceder a la(s) URL(s) de pendientes y extraer monto ANDINO."""
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
                    # buscar números en siguientes líneas
                    for j in range(i+1, min(i+8, len(lines))):
                        nxt = lines[j]
                        digits = "".join([c for c in nxt if c.isdigit()])
                        if digits:
                            return [{"comercio": "ANDINO", "total_pendientes": digits, "source_url": url}]
                    # si no, intentar extraer de la misma línea
                    digits = "".join([c for c in line if c.isdigit()])
                    if digits:
                        return [{"comercio": "ANDINO", "total_pendientes": digits, "source_url": url}]
        return []
