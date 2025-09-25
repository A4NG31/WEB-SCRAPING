import requests
from bs4 import BeautifulSoup


class FacturaParkScraper:
    def __init__(self):
        self.base_url = "https://facturapark.centroandino.com.co"
        self.session = requests.Session()

    def login(self, username: str, password: str) -> bool:
        """Inicia sesión en el portal"""
        try:
            # 1. Obtener cookies iniciales
            r = self.session.get(self.base_url)
            if r.status_code != 200:
                return False

            # 2. Enviar credenciales
            payload = {"email": username, "password": password}
            login_url = f"{self.base_url}/auth/login"

            r = self.session.post(login_url, data=payload)

            # Considerar login válido si redirige al home
            return r.ok and "console/home" in r.text

        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False

    def get_pending_invoices(self):
        """Navega a facturas pendientes y extrae datos"""
        try:
            pending_url = f"{self.base_url}/console/associatesManagement/invoicing/pendingEmit"
            r = self.session.get(pending_url)
            if r.status_code != 200:
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            for i, line in enumerate(lines):
                if "ANDINO" in line.upper():
                    for j in range(i + 1, min(i + 10, len(lines))):
                        next_line = lines[j]
                        digits = "".join([c for c in next_line if c.isdigit()])
                        if digits:
                            return [{"comercio": "ANDINO", "total_pendientes": digits}]

            return []

        except Exception as e:
            print(f"❌ Error extrayendo datos: {e}")
            return []
