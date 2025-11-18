import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper
from scraper_fontanar import FacturaFontanarScraper
from scraper_arkadia import FacturaArkadiaScraper
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json
import re
import time

# ===========================
# CONFIGURACIÓN GENERAL
# ===========================
st.set_page_config(page_title="FacturaPark Scraper", page_icon="🧾", layout="wide")

# ===========================
# ESTILOS CSS
# ===========================
st.markdown("""
<style>
body {
    background-color: #f9fafc;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
h1 {
    text-align: center;
    color: #2c3e50;
    font-weight: 700;
}
.stButton button {
    background-color: #2ecc71;
    color: white;
    font-weight: bold;
    border-radius: 12px;
    padding: 10px 20px;
    border: none;
    transition: 0.3s;
}
.stButton button:hover {
    background-color: #27ae60;
}
.block-container {
    padding-top: 1rem;
}
.card {
    background: white;
    padding: 1.5rem;
    margin: 1rem 0;
    border-radius: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}
.tab-header {
    font-size: 1.3rem;
    font-weight: 600;
    color: #34495e;
    margin-bottom: 1rem;
}
.textarea-mensaje textarea {
    background: #ecf0f1 !important;
    color: #2c3e50 !important;
    font-size: 1rem !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# Logo de GoPass con contenedor estilizado
st.markdown("""
<div class="logo-container">
    <img src="https://i.imgur.com/z9xt46F.jpeg"
         style="width: 60%; border-radius: 10px; display: block; margin: 0 auto;" 
         alt="Logo Gopass">
</div>
""", unsafe_allow_html=True)

st.title("🧾 Validador Motores de Facturación")

# Credenciales
USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]
ARKADIA_USER = st.secrets["arkadia"]["USERNAME"]
ARKADIA_PASS = st.secrets["arkadia"]["PASSWORD"]
FONTANAR_USER = st.secrets["Fontanar"]["USERNAME"]
FONTANAR_PASS = st.secrets["Fontanar"]["PASSWORD"]

# Inicializar session_state
for key in ["andino", "bulevar", "fontanar", "arkadia"]:
    if key not in st.session_state:
        st.session_state[key] = {"ok": False, "data": None, "jobs": None, "invoices": None}

def get_powerbi_data():
    """Obtiene los datos de facturas sin CUFE del reporte de Power BI con múltiples estrategias"""
    try:
        POWERBI_URL = "https://app.powerbi.com/view?r=eyJrIjoiMjUyNTBjMTItOWZlNy00YTY2LWIzMTQtNmM3OGU4ZWM1ZmQxIiwidCI6ImY5MTdlZDFiLWI0MDMtNDljNS1iODBiLWJhYWUzY2UwMzc1YSJ9"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        st.info("🌐 Conectando con Power BI...")
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Hacer la petición
        response = session.get(POWERBI_URL, timeout=60)
        response.raise_for_status()
        
        # Parsear el HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        parqueaderos = None
        peajes = None
        
        # ESTRATEGIA 1: Buscar en scripts que contengan datos estructurados
        st.info("🔍 Buscando datos en scripts...")
        scripts = soup.find_all('script')
        
        for i, script in enumerate(scripts):
            if script.string:
                script_content = script.string
                
                # Buscar datos en formato JSON
                if 'Parqueaderos' in script_content or 'Peajes' in script_content:
                    # Intentar encontrar objetos JSON
                    json_patterns = [
                        r'\{[^{}]*["\']?Parqueaderos["\']?\s*:\s*["\']?(\d+)["\']?[^{}]*\}',
                        r'\{[^{}]*["\']?Peajes["\']?\s*:\s*["\']?(\d+)["\']?[^{}]*\}',
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.finditer(pattern, script_content)
                        for match in matches:
                            json_str = match.group(0)
                            if 'Parqueaderos' in json_str and parqueaderos is None:
                                num_match = re.search(r'"Parqueaderos"\s*:\s*"(\d+)"', json_str)
                                if num_match:
                                    parqueaderos = int(num_match.group(1))
                                    st.success(f"✅ Parqueaderos encontrado en JSON: {parqueaderos}")
                            
                            if 'Peajes' in json_str and peajes is None:
                                num_match = re.search(r'"Peajes"\s*:\s*"(\d+)"', json_str)
                                if num_match:
                                    peajes = int(num_match.group(1))
                                    st.success(f"✅ Peajes encontrado en JSON: {peajes}")
        
        # ESTRATEGIA 2: Buscar en elementos visuales específicos de Power BI
        st.info("🔍 Buscando en elementos visuales...")
        
        # Power BI usa divs con clases específicas para visualizaciones
        powerbi_elements = soup.find_all(['div', 'span', 'td', 'li'])
        
        for element in powerbi_elements:
            element_text = element.get_text(strip=True)
            
            # Buscar patrones específicos de tabla
            if 'Parqueaderos' in element_text and parqueaderos is None:
                # Buscar el número asociado
                parent = element.parent
                if parent:
                    siblings = parent.find_all(['div', 'span', 'td'])
                    for sibling in siblings:
                        sibling_text = sibling.get_text(strip=True)
                        if sibling_text.isdigit() and sibling != element:
                            parqueaderos = int(sibling_text)
                            st.success(f"✅ Parqueaderos encontrado en elemento hermano: {parqueaderos}")
                            break
                
                # Buscar en el mismo texto
                numbers = re.findall(r'Parqueaderos\s*(\d+)', element_text)
                if numbers:
                    parqueaderos = int(numbers[0])
                    st.success(f"✅ Parqueaderos encontrado en mismo elemento: {parqueaderos}")
            
            if 'Peajes' in element_text and peajes is None:
                parent = element.parent
                if parent:
                    siblings = parent.find_all(['div', 'span', 'td'])
                    for sibling in siblings:
                        sibling_text = sibling.get_text(strip=True)
                        if sibling_text.isdigit() and sibling != element:
                            peajes = int(sibling_text)
                            st.success(f"✅ Peajes encontrado en elemento hermano: {peajes}")
                            break
                
                numbers = re.findall(r'Peajes\s*(\d+)', element_text)
                if numbers:
                    peajes = int(numbers[0])
                    st.success(f"✅ Peajes encontrado en mismo elemento: {peajes}")
        
        # ESTRATEGIA 3: Buscar en tablas específicamente
        st.info("🔍 Buscando en tablas...")
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                
                for i, cell in enumerate(cells):
                    if 'Parqueaderos' in cell and parqueaderos is None:
                        # Buscar en celdas adyacentes
                        if i + 1 < len(cells) and cells[i + 1].isdigit():
                            parqueaderos = int(cells[i + 1])
                            st.success(f"✅ Parqueaderos encontrado en tabla: {parqueaderos}")
                    
                    if 'Peajes' in cell and peajes is None:
                        if i + 1 < len(cells) and cells[i + 1].isdigit():
                            peajes = int(cells[i + 1])
                            st.success(f"✅ Peajes encontrado en tabla: {peajes}")
        
        # ESTRATEGIA 4: Buscar en todo el texto de la página
        st.info("🔍 Buscando en todo el contenido...")
        all_text = soup.get_text()
        
        # Buscar patrones específicos
        patterns = [
            r'Parqueaderos\s*:\s*(\d+)',
            r'Parqueaderos\s+(\d+)',
            r'"Parqueaderos"\s*:\s*"(\d+)"',
            r'Parqueaderos["\']\s*,\s*["\']?(\d+)',
        ]
        
        for pattern in patterns:
            if parqueaderos is None:
                matches = re.findall(pattern, all_text)
                if matches:
                    parqueaderos = int(matches[0])
                    st.success(f"✅ Parqueaderos encontrado con patrón {pattern}: {parqueaderos}")
                    break
        
        patterns_peajes = [
            r'Peajes\s*:\s*(\d+)',
            r'Peajes\s+(\d+)',
            r'"Peajes"\s*:\s*"(\d+)"',
            r'Peajes["\']\s*,\s*["\']?(\d+)',
        ]
        
        for pattern in patterns_peajes:
            if peajes is None:
                matches = re.findall(pattern, all_text)
                if matches:
                    peajes = int(matches[0])
                    st.success(f"✅ Peajes encontrado con patrón {pattern}: {peajes}")
                    break
        
        # ESTRATEGIA 5: Si no encontramos, mostrar error específico
        if parqueaderos is None or peajes is None:
            st.error("❌ No se pudieron encontrar los datos en Power BI")
            st.info("""
            **Posibles causas:**
            - El Power BI requiere autenticación
            - Los datos se cargan dinámicamente con JavaScript
            - La estructura del reporte cambió
            
            **Solución temporal:**
            Por favor ingresa los valores manualmente:
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                parqueaderos = st.number_input("Parqueaderos sin CUFE", min_value=0, value=0, key="parq_input")
            with col2:
                peajes = st.number_input("Peajes sin CUFE", min_value=0, value=0, key="peajes_input")
            
            if st.button("Usar valores manuales"):
                return {
                    "parqueaderos": parqueaderos,
                    "peajes": peajes
                }
            else:
                # Esperar a que el usuario ingrese los valores
                st.stop()
        
        return {
            "parqueaderos": parqueaderos,
            "peajes": peajes
        }
        
    except Exception as e:
        st.error(f"❌ Error crítico al obtener datos de Power BI: {e}")
        st.info("Por favor ingresa los valores manualmente:")
        
        col1, col2 = st.columns(2)
        with col1:
            parqueaderos = st.number_input("Parqueaderos sin CUFE", min_value=0, value=0, key="parq_error")
        with col2:
            peajes = st.number_input("Peajes sin CUFE", min_value=0, value=0, key="peajes_error")
        
        if st.button("Usar valores manuales", key="manual_btn"):
            return {
                "parqueaderos": parqueaderos,
                "peajes": peajes
            }
        else:
            st.stop()

def run_scraper(name, scraper_class, username, password):
    scraper = scraper_class()
    ok = scraper.login(username, password)
    result = {"ok": ok, "data": None, "jobs": None, "invoices": None}
    if ok:
        # Obtenemos datos según cada scraper
        data = scraper.get_pending_invoices()
        # --- CORRECCIÓN: convertir listas a DataFrame para que la UI las muestre ---
        if isinstance(data, list):
            try:
                result["data"] = pd.DataFrame(data) if len(data) > 0 else pd.DataFrame()
            except Exception:
                # fallback: intentar construir DataFrame de forma segura
                try:
                    result["data"] = pd.DataFrame([data])
                except Exception:
                    result["data"] = pd.DataFrame()
        elif isinstance(data, pd.DataFrame):
            result["data"] = data
        else:
            # si el scraper devuelve dict o None, intentar transformar a DataFrame
            try:
                result["data"] = pd.DataFrame(data) if data else pd.DataFrame()
            except Exception:
                result["data"] = pd.DataFrame()

        jobs = scraper.get_jobs_config()
        # Convertimos jobs a DataFrame si es lista
        if isinstance(jobs, list):
            try:
                jobs = pd.DataFrame(jobs) if len(jobs) > 0 else pd.DataFrame()
            except Exception:
                jobs = pd.DataFrame()

        # ✅ Filtro especial SOLO para Arkadia
        if name == "arkadia" and isinstance(jobs, pd.DataFrame) and not jobs.empty:
            jobs = jobs.rename(columns={
                "jobname": "NOMBRE",
                "raiseevents": "AUMENTO DE EVENTOS",
                "enabled": "HABILITADO",
                "updatedat": "FECHA DE ACTUALIZACIÓN"
            })
            jobs = jobs[["NOMBRE", "AUMENTO DE EVENTOS", "HABILITADO", "FECHA DE ACTUALIZACIÓN"]]

        result["jobs"] = jobs
        result["invoices"] = scraper.get_invoices()
    return name, result

if st.button("Ejecutar scraping de todos los centros comerciales"):
    with st.spinner("🔑 Ejecutando scrapers en paralelo..."):
        futures = []
        with ThreadPoolExecutor() as executor:
            futures.append(executor.submit(run_scraper, "andino", FacturaParkScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "bulevar", FacturaBulevarScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "fontanar", FacturaFontanarScraper, FONTANAR_USER, FONTANAR_PASS))
            futures.append(executor.submit(run_scraper, "arkadia", FacturaArkadiaScraper, ARKADIA_USER, ARKADIA_PASS))

            for future in as_completed(futures):
                name, result = future.result()
                st.session_state[name] = result

    st.session_state["scraping_done"] = True

# ===========================
# TAB PESTAÑAS
# ===========================
tab_andino, tab_bulevar, tab_fontanar, tab_arkadia = st.tabs([
    "🏢 Centro Comercial Andino", 
    "🏢 Centro Comercial Bulevar",
    "🏢 Centro Comercial Fontanar",
    "🏢 Centro Comercial Arkadia"
])

def display_tab(name, display_name):
    st.header(f"🏢 {display_name}")
    state = st.session_state[name]
    if state["ok"]:
        st.subheader("📦 Facturas Pendientes")
        if isinstance(state["data"], pd.DataFrame) and not state["data"].empty:
            st.table(state["data"])
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        jobs = state["jobs"]
        if isinstance(jobs, pd.DataFrame) and not jobs.empty:
            st.table(jobs)
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS")
        invoices = state["invoices"]
        if invoices and invoices.get("factura_reciente"):
            st.metric(f"Total de facturas ({display_name})", invoices["total_facturas"])
            factura = invoices["factura_reciente"]
            campos_clave = {
                "ID": factura.get("idinvoice"),
                "Id Factura": factura.get("idtransaction"),
                "Id Transacción": factura.get("idtransparking"),
                "Fecha Factura": factura.get("fecha_factura"),
                "Valor Neto": f"${factura.get('valor_neto_factura'):,}" if factura.get("valor_neto_factura") else None,
                "Valor Total": f"${factura.get('valor_factura'):,}" if factura.get("valor_factura") else None,
                "Tercero": factura.get("nombretercero"),
                "Fecha Salida": factura.get("outdate"),
                "Estado": factura.get("invoicestatus"),
                "CUFE": factura.get("cufe"),
                "Factura": factura.get("id_unico"),
            }
            st.dataframe(pd.DataFrame([campos_clave]), use_container_width=True)
        else:
            st.warning("⚠️ No se encontraron facturas")
    elif state["ok"] == False:
        st.info(f" 👆 Oprime el boton para inciar el proceso ")
    else:
        st.info("Presiona 'Ejecutar scraping de todos los centros comerciales' para cargar datos.")

with tab_andino:
    display_tab("andino", "Centro Comercial Andino")

with tab_bulevar:
    display_tab("bulevar", "Centro Comercial Bulevar")

with tab_fontanar:
    display_tab("fontanar", "Centro Comercial Fontanar")

with tab_arkadia:
    display_tab("arkadia", "Centro Comercial Arkadia")

# ===========================
# BOTÓN GENERAR MENSAJE WHATSAPP
# ===========================
def format_fecha(fecha):
    """Convierte la fecha a formato dd/mm/yyyy HH:MM"""
    try:
        return pd.to_datetime(fecha).strftime("%d/%m/%Y %H:%M")
    except:
        return str(fecha)

if st.session_state.get("scraping_done", False):
    if st.button("📩 Generar mensaje de WhatsApp"):
        with st.spinner("🌐 Obteniendo datos de Power BI..."):
            powerbi_data = get_powerbi_data()
        
        mensaje = (
            "Buen día, se realiza informe de facturación electrónica, al momento no contamos con facturación pendiente.\n\n"
            "Se realiza de igual forma revisión de motores FE:\n\n"
        )
        for name, display_name in {
            "andino": "Motor Andino",
            "bulevar": "Motor Bulevar",
            "fontanar": "Motor Fontanar",
            "arkadia": "Motor Arkadia"
        }.items():
            state = st.session_state[name]
            if state["ok"]:
                pendientes = 0
                data = state["data"]

                # ✅ Diferenciamos Arkadia vs los demás
                if name == "arkadia":
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        if "pending" in data.columns:
                            pendientes = data.iloc[0]["pending"]
                        elif "total_pendientes" in data.columns:
                            pendientes = data.iloc[0]["total_pendientes"]
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        pendientes = data[0].get("pending") or data[0].get("total_pendientes", 0)
                else:  # Andino, Bulevar y Fontanar usan "total_pendientes"
                    if isinstance(data, pd.DataFrame) and not data.empty and "total_pendientes" in data.columns:
                        pendientes = data.iloc[0]["total_pendientes"]
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        pendientes = data[0].get("total_pendientes", 0)

                # Facturas hoy
                total_hoy = state["invoices"]["total_facturas"] if state["invoices"] else 0

                # Fecha jobs
                fecha_jobs = "Sin fecha"
                if isinstance(state["jobs"], pd.DataFrame) and not state["jobs"].empty:
                    if name == "arkadia" and "FECHA DE ACTUALIZACIÓN" in state["jobs"].columns:
                        fecha_jobs = format_fecha(state["jobs"].iloc[0]["FECHA DE ACTUALIZACIÓN"])
                    elif "ultima_actualizacion" in state["jobs"].columns:
                        fecha_jobs = format_fecha(state["jobs"].iloc[0]["ultima_actualizacion"])

                mensaje += (
                    f"* {display_name} {'con ' + str(pendientes) + ' facturas pendientes' if int(pendientes) else 'sin facturas pendientes'}, "
                    f"con {total_hoy} facturas del día de hoy, con sus Jobs actualizados ({fecha_jobs})\n\n"
                )
        
        # Añadir los datos de Power BI al mensaje
        mensaje += f"\nFacturas sin CUFE:\n\nParqueaderos: {powerbi_data['parqueaderos']}\nPeajes: {powerbi_data['peajes']}"

        st.text_area("Mensaje generado", mensaje, height=300)
