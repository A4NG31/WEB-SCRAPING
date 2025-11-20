import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper
from scraper_fontanar import FacturaFontanarScraper
from scraper_arkadia import FacturaArkadiaScraper
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import re


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

# ===========================
# FUNCIONES DE SELENIUM
# ===========================

def setup_driver():
    """Configurar ChromeDriver para Selenium - Compatible con Streamlit Cloud"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        
        chrome_options = Options()
        
        # Opciones críticas para Streamlit Cloud
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--single-process")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent real
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # MÉTODO 1: Usar webdriver-manager con CHROMIUM
        try:
            # Instalar chromedriver compatible con chromium
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            
            # Especificar la ubicación de chromium
            chrome_options.binary_location = "/usr/bin/chromium"
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e1:
            # MÉTODO 2: Sin especificar chrome_type
            try:
                service = Service(ChromeDriverManager().install())
                chrome_options.binary_location = "/usr/bin/chromium"
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                return driver
                
            except Exception as e2:
                # MÉTODO 3: Usar chromedriver del sistema directamente
                try:
                    import subprocess
                    import os
                    
                    # Buscar chromedriver en el sistema
                    result = subprocess.run(['which', 'chromedriver'], 
                                          capture_output=True, text=True)
                    chromedriver_path = result.stdout.strip()
                    
                    if chromedriver_path and os.path.exists(chromedriver_path):
                        # Hacer ejecutable
                        os.chmod(chromedriver_path, 0o755)
                        
                        service = Service(executable_path=chromedriver_path)
                        chrome_options.binary_location = "/usr/bin/chromium"
                        
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                        
                        return driver
                    else:
                        return None
                        
                except Exception as e3:
                    return None
        
    except Exception as e:
        return None

def extract_number_from_text(text):
    """Extrae un número del texto, manejando formatos con comas"""
    try:
        # Buscar números con comas (formato: 1,234 o 12,345)
        match = re.search(r'\b\d{1,3}(?:,\d{3})+\b', text)
        if match:
            return match.group(0)
        
        # Buscar números simples
        match = re.search(r'\b\d+\b', text)
        if match:
            return match.group(0)
        
        return None
    except:
        return None

def find_parqueaderos_peajes_values(driver):
    """
    Buscar los valores de Parqueaderos y Peajes en el Power BI
    Y también extraer la fecha analizada y los asociados
    """
    try:
        # Esperar a que la página cargue completamente
        time.sleep(8)
        
        # Obtener todo el texto visible de la página
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Dividir en líneas para análisis
        lines = page_text.split('\n')
        
        parqueaderos = None
        peajes = None
        fecha_analizada = None
        asociados_data = {}
        
        # Buscar en líneas consecutivas
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Buscar "Parqueaderos"
            if 'parqueaderos' in line_clean.lower() and parqueaderos is None:
                num = extract_number_from_text(line_clean)
                if num:
                    parqueaderos = num
                else:
                    for offset in range(1, 6):
                        if i + offset < len(lines):
                            next_line = lines[i + offset].strip()
                            num = extract_number_from_text(next_line)
                            if num:
                                parqueaderos = num
                                break
            
            # Buscar "Peajes"
            if 'peajes' in line_clean.lower() and peajes is None:
                num = extract_number_from_text(line_clean)
                if num:
                    peajes = num
                else:
                    for offset in range(1, 6):
                        if i + offset < len(lines):
                            next_line = lines[i + offset].strip()
                            num = extract_number_from_text(next_line)
                            if num:
                                peajes = num
                                break
            
            # Buscar fecha en formato MM/DD/YYYY o DD/MM/YYYY
            if fecha_analizada is None:
                fecha_patterns = [
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    r'\b\d{1,2}-\d{1,2}-\d{4}\b',
                    r'\b\d{4}/\d{1,2}/\d{1,2}\b',
                ]
                
                for pattern in fecha_patterns:
                    fecha_match = re.search(pattern, line_clean)
                    if fecha_match:
                        fecha_cruda = fecha_match.group(0)
                        if not re.search(r'\d{5,}', fecha_cruda):
                            try:
                                fecha_obj = None
                                for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']:
                                    try:
                                        fecha_obj = datetime.strptime(fecha_cruda, fmt)
                                        break
                                    except:
                                        continue
                                
                                if fecha_obj:
                                    fecha_analizada = fecha_obj.strftime('%d/%m/%Y')
                                    break
                            except:
                                pass
        
        # BUSCAR ASOCIADOS
        try:
            # Buscar la sección de "Asociado" en el texto
            start_index = -1
            for i, line in enumerate(lines):
                if 'asociado' in line.lower():
                    start_index = i
                    break
            
            if start_index != -1:
                # Buscar desde la sección de Asociado hacia adelante
                asociados_encontrados = 0
                current_asociado = None
                
                for i in range(start_index + 1, min(start_index + 30, len(lines))):
                    line_clean = lines[i].strip()
                    
                    # Si encontramos "Total" después de algunos asociados, terminamos
                    if 'total' in line_clean.lower() and asociados_encontrados > 0:
                        break
                    
                    # Saltar líneas vacías o de encabezados/controles
                    if (not line_clean or 
                        any(keyword in line_clean.lower() for keyword in 
                            ['asociado', 'sum of cantidad', 'scroll', 'select row', 'servicio', 'cantidad', 'row selection', 'microsoft'])):
                        continue
                    
                    # Si la línea parece ser un nombre de asociado (texto sin números)
                    if (re.match(r'^[A-Za-z\s]+$', line_clean) and 
                        len(line_clean) > 2 and
                        not any(keyword in line_clean.lower() for keyword in ['up', 'down', 'left', 'right'])):
                        
                        current_asociado = line_clean
                    
                    # Si la línea parece ser un número y tenemos un asociado pendiente
                    elif (current_asociado and 
                          re.match(r'^\d{1,6}$', line_clean) and
                          line_clean not in ['-', '+', '130']):
                        
                        asociados_data[current_asociado] = line_clean
                        asociados_encontrados += 1
                        current_asociado = None
            
            # Si no encontramos con el método anterior, intentar método alternativo
            if not asociados_data:
                # Buscar patrones específicos en el texto completo
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    
                    # Buscar líneas que sean solo números (cantidades)
                    if re.match(r'^\d{1,6}$', line_clean) and line_clean not in ['0', '467', '1292']:
                        # Buscar hacia atrás para encontrar el asociado
                        for j in range(max(0, i-5), i):
                            prev_line = lines[j].strip()
                            if (prev_line and 
                                re.match(r'^[A-Z][A-Za-z\s]+$', prev_line) and
                                len(prev_line) > 2 and
                                not any(keyword in prev_line.lower() for keyword in 
                                       ['scroll', 'select', 'row', 'servicio', 'cantidad', 'asociado', 'total', 'parqueaderos', 'peajes'])):
                                
                                asociados_data[prev_line] = line_clean
                                break
                
        except Exception as e:
            pass
        
        # Búsqueda por patrones regex en todo el texto
        if parqueaderos is None or peajes is None or fecha_analizada is None:
            
            if parqueaderos is None:
                match = re.search(r'[Pp]arqueaderos[^\d]*(\d{1,3}(?:,\d{3})*)', page_text)
                if match:
                    parqueaderos = match.group(1)
            
            if peajes is None:
                match = re.search(r'[Pp]eajes[^\d]*(\d{1,3}(?:,\d{3})*)', page_text)
                if match:
                    peajes = match.group(1)
            
            if fecha_analizada is None:
                fecha_match = re.search(r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/(202[4-9])\b', page_text)
                if fecha_match:
                    try:
                        mes, dia, año = fecha_match.groups()
                        fecha_analizada = f"{int(dia):02d}/{int(mes):02d}/{año}"
                    except:
                        pass
        
        # Verificación final
        if parqueaderos is None:
            st.error("❌ No se pudo encontrar el valor de Parqueaderos")
        
        if peajes is None:
            st.error("❌ No se pudo encontrar el valor de Peajes")
        
        if fecha_analizada is None:
            # Usar fecha actual como fallback
            fecha_analizada = datetime.now().strftime('%d/%m/%Y')
        
        return parqueaderos, peajes, fecha_analizada, asociados_data
        
    except Exception as e:
        return None, None, None, {}

def get_powerbi_data():
    """
    Obtiene los datos de facturas sin CUFE del reporte de Power BI usando Selenium
    """
    try:
        POWERBI_URL = "https://app.powerbi.com/view?r=eyJrIjoiMjUyNTBjMTItOWZlNy00YTY2LWIzMTQtNmM3OGU4ZWM1ZmQxIiwidCI6ImY5MTdlZDFiLWI0MDMtNDljNS1iODBiLWJhYWUzY2UwMzc1YSJ9"
        
        # Configurar el driver
        driver = setup_driver()
        if not driver:
            st.error("❌ No se pudo inicializar el driver de Selenium")
            return None
        
        try:
            # Navegar al reporte
            driver.get(POWERBI_URL)
            
            # Esperar a que cargue la página
            time.sleep(15)
            
            # Buscar los valores de Parqueaderos, Peajes, Fecha y Asociados
            parqueaderos, peajes, fecha_analizada, asociados_data = find_parqueaderos_peajes_values(driver)
            
            if parqueaderos is None or peajes is None:
                st.error("❌ No se pudieron extraer los valores del dashboard")
                return None
            
            # Convertir a enteros
            try:
                parqueaderos_num = int(parqueaderos.replace(',', ''))
                peajes_num = int(peajes.replace(',', ''))
                
                return {
                    "parqueaderos": parqueaderos_num,
                    "peajes": peajes_num,
                    "fecha_analizada": fecha_analizada,
                    "asociados": asociados_data
                }
            except ValueError as e:
                st.error(f"❌ Error convirtiendo valores a números: {e}")
                return None
            
        finally:
            driver.quit()
        
    except Exception as e:
        st.error(f"❌ Error crítico al obtener datos de Power BI: {str(e)}")
        return None

# ===========================
# FUNCIONES DE SCRAPING
# ===========================

def run_scraper(name, scraper_class, username, password):
    scraper = scraper_class()
    ok = scraper.login(username, password)
    result = {"ok": ok, "data": None, "jobs": None, "invoices": None}
    if ok:
        # Obtenemos datos según cada scraper
        data = scraper.get_pending_invoices()
        # Convertir listas a DataFrame para que la UI las muestre
        if isinstance(data, list):
            try:
                result["data"] = pd.DataFrame(data) if len(data) > 0 else pd.DataFrame()
            except Exception:
                try:
                    result["data"] = pd.DataFrame([data])
                except Exception:
                    result["data"] = pd.DataFrame()
        elif isinstance(data, pd.DataFrame):
            result["data"] = data
        else:
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

        # Filtro especial SOLO para Arkadia
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

# ===========================
# FORMATO DE FECHA
# ===========================

def format_fecha(fecha):
    """Convierte la fecha a formato dd/mm/yyyy HH:MM"""
    try:
        return pd.to_datetime(fecha).strftime("%d/%m/%Y %H:%M")
    except:
        return str(fecha)

# ===========================
# INTERFAZ PRINCIPAL
# ===========================

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

if st.session_state.get("scraping_done", False):
    if st.button("📩 Generar mensaje de WhatsApp"):
        with st.spinner("🌐 Obteniendo datos de Power BI..."):
            powerbi_data = get_powerbi_data()
        
        if powerbi_data is None:
            st.error("❌ No se pudieron obtener los datos de Power BI. No se puede generar el mensaje.")
            st.stop()
        
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

                # Diferenciamos Arkadia vs los demás
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
        mensaje += f"\nFacturas sin CUFE: (BI actualizado: {powerbi_data['fecha_analizada']})\n\nParqueaderos: {powerbi_data['parqueaderos']:,}\nPeajes: {powerbi_data['peajes']:,}"
        
        # Añadir los asociados al mensaje
        if powerbi_data.get('asociados'):
            mensaje += f"\n\nTransacciones Sin Factura por asociado: (BI actualizado: {powerbi_data['fecha_analizada']})\n\n"
            
            # Calcular total de asociados
            total_asociados = 0
            for asociado, cantidad in powerbi_data['asociados'].items():
                try:
                    total_asociados += int(cantidad.replace(',', ''))
                except:
                    pass
                
                mensaje += f"{asociado}: {cantidad}\n"
            
            mensaje += f"\nTOTAL: {total_asociados:,}"

        st.text_area("Mensaje generado", mensaje, height=400)
