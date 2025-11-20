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
            st.info("🔄 Configurando ChromeDriver con webdriver-manager...")
            
            # Instalar chromedriver compatible con chromium
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            
            # Especificar la ubicación de chromium
            chrome_options.binary_location = "/usr/bin/chromium"
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            st.success("✅ ChromeDriver configurado exitosamente")
            return driver
            
        except Exception as e1:
            st.warning(f"⚠️ Método 1 falló: {e1}")
            
            # MÉTODO 2: Sin especificar chrome_type
            try:
                st.info("🔄 Intentando método alternativo...")
                
                service = Service(ChromeDriverManager().install())
                chrome_options.binary_location = "/usr/bin/chromium"
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                st.success("✅ ChromeDriver configurado con método alternativo")
                return driver
                
            except Exception as e2:
                st.error(f"❌ Método 2 también falló: {e2}")
                
                # MÉTODO 3: Usar chromedriver del sistema directamente
                try:
                    st.info("🔄 Intentando con chromedriver del sistema...")
                    
                    import subprocess
                    import os
                    
                    # Buscar chromedriver en el sistema
                    result = subprocess.run(['which', 'chromedriver'], 
                                          capture_output=True, text=True)
                    chromedriver_path = result.stdout.strip()
                    
                    if chromedriver_path and os.path.exists(chromedriver_path):
                        st.info(f"📍 ChromeDriver encontrado en: {chromedriver_path}")
                        
                        # Hacer ejecutable
                        os.chmod(chromedriver_path, 0o755)
                        
                        service = Service(executable_path=chromedriver_path)
                        chrome_options.binary_location = "/usr/bin/chromium"
                        
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                        
                        st.success("✅ ChromeDriver del sistema configurado")
                        return driver
                    else:
                        st.error("❌ ChromeDriver no encontrado en el sistema")
                        return None
                        
                except Exception as e3:
                    st.error(f"❌ Método 3 falló: {e3}")
                    
                    # Mostrar información de debug
                    with st.expander("🔍 Información de Debug"):
                        import subprocess
                        
                        st.text("=== Verificando Chromium ===")
                        try:
                            result = subprocess.run(['which', 'chromium'], 
                                                  capture_output=True, text=True, timeout=5)
                            st.text(f"which chromium: {result.stdout}")
                            st.text(f"stderr: {result.stderr}")
                        except Exception as e:
                            st.text(f"Error: {e}")
                        
                        st.text("\n=== Verificando ChromeDriver ===")
                        try:
                            result = subprocess.run(['which', 'chromedriver'], 
                                                  capture_output=True, text=True, timeout=5)
                            st.text(f"which chromedriver: {result.stdout}")
                            st.text(f"stderr: {result.stderr}")
                        except Exception as e:
                            st.text(f"Error: {e}")
                        
                        st.text("\n=== Archivos en /usr/bin ===")
                        try:
                            result = subprocess.run(['ls', '-la', '/usr/bin/chrom*'], 
                                                  capture_output=True, text=True, timeout=5, shell=True)
                            st.text(result.stdout)
                        except Exception as e:
                            st.text(f"Error: {e}")
                        
                        st.text("\n=== Verificando dependencias ===")
                        try:
                            result = subprocess.run(['ldd', '/usr/bin/chromium'], 
                                                  capture_output=True, text=True, timeout=5)
                            st.text(result.stdout[:500])  # Primeras líneas
                        except Exception as e:
                            st.text(f"Error: {e}")
                    
                    return None
        
    except Exception as e:
        st.error(f"❌ Error crítico al configurar ChromeDriver: {e}")
        import traceback
        st.error(traceback.format_exc())
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
        
        # ESTRATEGIA 1: Buscar en líneas consecutivas
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Buscar "Parqueaderos"
            if 'parqueaderos' in line_clean.lower() and parqueaderos is None:
                
                # Buscar número en la misma línea
                num = extract_number_from_text(line_clean)
                if num:
                    parqueaderos = num
                else:
                    # Buscar en las siguientes 5 líneas
                    for offset in range(1, 6):
                        if i + offset < len(lines):
                            next_line = lines[i + offset].strip()
                            num = extract_number_from_text(next_line)
                            if num:
                                parqueaderos = num
                                break
            
            # Buscar "Peajes"
            if 'peajes' in line_clean.lower() and peajes is None:
                
                # Buscar número en la misma línea
                num = extract_number_from_text(line_clean)
                if num:
                    peajes = num
                else:
                    # Buscar en las siguientes 5 líneas
                    for offset in range(1, 6):
                        if i + offset < len(lines):
                            next_line = lines[i + offset].strip()
                            num = extract_number_from_text(next_line)
                            if num:
                                peajes = num
                                break
            
            # Buscar fecha en formato MM/DD/YYYY o DD/MM/YYYY
            if fecha_analizada is None:
                # Buscar patrones de fecha comunes en Power BI
                fecha_patterns = [
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY o DD/MM/YYYY
                    r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY o DD-MM-YYYY
                    r'\b\d{4}/\d{1,2}/\d{1,2}\b',  # YYYY/MM/DD
                ]
                
                for pattern in fecha_patterns:
                    fecha_match = re.search(pattern, line_clean)
                    if fecha_match:
                        fecha_cruda = fecha_match.group(0)
                        
                        # Verificar si es una fecha válida (no parte de un número grande)
                        if not re.search(r'\d{5,}', fecha_cruda):  # Evitar números grandes como 12345/67/89
                            try:
                                # Convertir a datetime para validar
                                fecha_obj = None
                                
                                # Intentar diferentes formatos
                                for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']:
                                    try:
                                        fecha_obj = datetime.strptime(fecha_cruda, fmt)
                                        break
                                    except:
                                        continue
                                
                                if fecha_obj:
                                    # Formatear a DD/MM/YYYY
                                    fecha_analizada = fecha_obj.strftime('%d/%m/%Y')
                                    st.success(f"📅 Fecha analizada encontrada: {fecha_analizada}")
                                    break
                            except:
                                pass
        
        # ESTRATEGIA 2: Buscar por elementos HTML si la estrategia 1 falló
        if parqueaderos is None or peajes is None or fecha_analizada is None:
            
            # Buscar todos los elementos que contengan "Parqueaderos"
            if parqueaderos is None:
                try:
                    parq_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Parqueaderos') or contains(text(), 'parqueaderos') or contains(text(), 'PARQUEADEROS')]")
                    
                    for elem in parq_elements:
                        if elem.is_displayed():
                            # Buscar en el contenedor padre
                            try:
                                parent = elem.find_element(By.XPATH, "./..")
                                parent_text = parent.text
                                num = extract_number_from_text(parent_text)
                                if num:
                                    parqueaderos = num
                                    break
                            except:
                                pass
                            
                            # Buscar en elementos hermanos
                            try:
                                parent = elem.find_element(By.XPATH, "./..")
                                siblings = parent.find_elements(By.XPATH, "./*")
                                for sibling in siblings:
                                    if sibling != elem:
                                        sibling_text = sibling.text.strip()
                                        num = extract_number_from_text(sibling_text)
                                        if num:
                                            parqueaderos = num
                                            break
                            except:
                                pass
                except Exception as e:
                    st.warning(f"⚠️ Error en búsqueda de Parqueaderos: {e}")
            
            # Buscar todos los elementos que contengan "Peajes"
            if peajes is None:
                try:
                    peaj_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Peajes') or contains(text(), 'peajes') or contains(text(), 'PEAJES')]")
                    
                    for elem in peaj_elements:
                        if elem.is_displayed():
                            # Buscar en el contenedor padre
                            try:
                                parent = elem.find_element(By.XPATH, "./..")
                                parent_text = parent.text
                                num = extract_number_from_text(parent_text)
                                if num:
                                    peajes = num
                                    break
                            except:
                                pass
                            
                            # Buscar en elementos hermanos
                            try:
                                parent = elem.find_element(By.XPATH, "./..")
                                siblings = parent.find_elements(By.XPATH, "./*")
                                for sibling in siblings:
                                    if sibling != elem:
                                        sibling_text = sibling.text.strip()
                                        num = extract_number_from_text(sibling_text)
                                        if num:
                                            peajes = num
                                            break
                            except:
                                pass
                except Exception as e:
                    st.warning(f"⚠️ Error en búsqueda de Peajes: {e}")
            
            # Buscar fecha en elementos específicos
            if fecha_analizada is None:
                try:
                    # Buscar elementos que contengan fechas
                    fecha_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '/202') or contains(text(), '-202')]")
                    
                    for elem in fecha_elements:
                        if elem.is_displayed():
                            elem_text = elem.text.strip()
                            # Buscar patrones de fecha
                            fecha_patterns = [
                                r'\b\d{1,2}/\d{1,2}/202\d\b',
                                r'\b\d{1,2}-\d{1,2}-202\d\b',
                            ]
                            
                            for pattern in fecha_patterns:
                                fecha_match = re.search(pattern, elem_text)
                                if fecha_match:
                                    fecha_cruda = fecha_match.group(0)
                                    try:
                                        # Intentar diferentes formatos
                                        for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y']:
                                            try:
                                                fecha_obj = datetime.strptime(fecha_cruda, fmt)
                                                fecha_analizada = fecha_obj.strftime('%d/%m/%Y')
                                                st.success(f"📅 Fecha encontrada en elemento: {fecha_analizada}")
                                                break
                                            except:
                                                continue
                                        if fecha_analizada:
                                            break
                                    except:
                                        pass
                except Exception as e:
                    st.warning(f"⚠️ Error en búsqueda de fecha: {e}")
        
        # ESTRATEGIA 3: Búsqueda por patrones regex en todo el texto
        if parqueaderos is None or peajes is None or fecha_analizada is None:
            
            if parqueaderos is None:
                # Buscar patrón "Parqueaderos" seguido de número
                match = re.search(r'[Pp]arqueaderos[^\d]*(\d{1,3}(?:,\d{3})*)', page_text)
                if match:
                    parqueaderos = match.group(1)
            
            if peajes is None:
                # Buscar patrón "Peajes" seguido de número
                match = re.search(r'[Pp]eajes[^\d]*(\d{1,3}(?:,\d{3})*)', page_text)
                if match:
                    peajes = match.group(1)
            
            if fecha_analizada is None:
                # Buscar fechas en todo el texto
                fecha_match = re.search(r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/(202[4-9])\b', page_text)
                if fecha_match:
                    try:
                        mes, dia, año = fecha_match.groups()
                        fecha_analizada = f"{int(dia):02d}/{int(mes):02d}/{año}"
                        st.success(f"📅 Fecha encontrada con regex: {fecha_analizada}")
                    except:
                        pass
        
        # ESTRATEGIA 4: Buscar en contexto de tabla específica
        if parqueaderos is None or peajes is None or fecha_analizada is None:
            
            # Buscar secciones que contengan ambos términos
            sections_with_both = []
            for i, line in enumerate(lines):
                window = ' '.join(lines[max(0, i-5):min(len(lines), i+5)])
                if 'parqueaderos' in window.lower() and 'peajes' in window.lower():
                    sections_with_both.append((i, window))
            
            if sections_with_both:
                st.info(f"📋 Encontradas {len(sections_with_both)} secciones con ambos términos")
                
                for idx, section in sections_with_both:
                    # Extraer todos los números de la sección
                    numbers = re.findall(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{3,}\b', section)
                    
                    if len(numbers) >= 2:
                        # Asumir que el primer número es Parqueaderos y el segundo Peajes
                        if parqueaderos is None:
                            parqueaderos = numbers[0]
                        if peajes is None:
                            peajes = numbers[1]
                    
                    # Buscar fecha en la sección
                    if fecha_analizada is None:
                        fecha_match = re.search(r'\b\d{1,2}/\d{1,2}/202[4-9]\b', section)
                        if fecha_match:
                            try:
                                fecha_cruda = fecha_match.group(0)
                                for fmt in ['%m/%d/%Y', '%d/%m/%Y']:
                                    try:
                                        fecha_obj = datetime.strptime(fecha_cruda, fmt)
                                        fecha_analizada = fecha_obj.strftime('%d/%m/%Y')
                                        break
                                    except:
                                        continue
                            except:
                                pass
                    
                    if parqueaderos and peajes and fecha_analizada:
                        break
        
        # BUSCAR ASOCIADOS Y SUS CANTIDADES
        try:
            # Buscar la sección de asociados en el texto
            asociados_section_found = False
            total_asociados = 0
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Buscar líneas que parezcan asociados con cantidades
                # Patrón: texto (asociado) seguido de número
                if line_clean and not any(keyword in line_clean.lower() for keyword in 
                                         ['servicio', 'cantidad', 'asociado', 'sum of', 'total', 'scroll', 'microsoft']):
                    
                    # Buscar si la línea tiene un formato de asociado: texto + número
                    asociado_match = re.match(r'^([A-Za-z\s]+?)\s+(\d{1,3}(?:,\d{3})*|\d+)$', line_clean)
                    if asociado_match:
                        asociado_nombre = asociado_match.group(1).strip()
                        asociado_cantidad = asociado_match.group(2)
                        
                        # Filtrar nombres que no son asociados reales
                        if (asociado_nombre and 
                            len(asociado_nombre) > 2 and 
                            not asociado_nombre.isdigit() and
                            not any(keyword in asociado_nombre.lower() for keyword in 
                                   ['select', 'row', 'scroll', 'up', 'down', 'left', 'right'])):
                            
                            asociados_data[asociado_nombre] = asociado_cantidad
                            asociados_section_found = True
                            
                            # Sumar al total
                            try:
                                total_asociados += int(asociado_cantidad.replace(',', ''))
                            except:
                                pass
            
            # Si no encontramos asociados con el método anterior, buscar por contexto de tabla
            if not asociados_section_found:
                # Buscar después de la palabra "Asociado" en el texto
                for i, line in enumerate(lines):
                    if 'asociado' in line.lower():
                        # Buscar en las siguientes 20 líneas
                        for j in range(i+1, min(i+21, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and not any(keyword in next_line.lower() for keyword in 
                                                   ['total', 'servicio', 'cantidad', 'scroll']):
                                
                                # Intentar extraer asociado y cantidad
                                parts = next_line.split()
                                if len(parts) >= 2:
                                    # El último elemento debería ser la cantidad
                                    posible_cantidad = parts[-1]
                                    if re.match(r'^\d{1,3}(?:,\d{3})*$', posible_cantidad):
                                        asociado_nombre = ' '.join(parts[:-1]).strip()
                                        if (asociado_nombre and 
                                            len(asociado_nombre) > 2 and 
                                            not any(keyword in asociado_nombre.lower() for keyword in 
                                                   ['select', 'row'])):
                                            
                                            asociados_data[asociado_nombre] = posible_cantidad
                                            asociados_section_found = True
                                            
                                            try:
                                                total_asociados += int(posible_cantidad.replace(',', ''))
                                            except:
                                                pass
            
            if asociados_section_found:
                st.success(f"📊 Encontrados {len(asociados_data)} asociados con un total de {total_asociados:,}")
            else:
                st.warning("⚠️ No se encontraron datos de asociados en el BI")
                
        except Exception as e:
            st.warning(f"⚠️ Error al buscar asociados: {e}")
        
        # Verificación final
        if parqueaderos is None:
            st.error("❌ No se pudo encontrar el valor de Parqueaderos")
        
        if peajes is None:
            st.error("❌ No se pudo encontrar el valor de Peajes")
        
        if fecha_analizada is None:
            st.warning("⚠️ No se pudo encontrar la fecha analizada en el BI")
            # Usar fecha actual como fallback
            fecha_analizada = datetime.now().strftime('%d/%m/%Y')
            st.info(f"📅 Usando fecha actual: {fecha_analizada}")
        
        return parqueaderos, peajes, fecha_analizada, asociados_data
        
    except Exception as e:
        st.error(f"❌ Error durante la búsqueda: {str(e)}")
        return None, None, None, {}

def get_powerbi_data():
    """
    Obtiene los datos de facturas sin CUFE del reporte de Power BI usando Selenium
    VERSIÓN MEJORADA que también extrae la fecha analizada y los asociados
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
            time.sleep(15)  # Espera para que se renderice el contenido
            
            # Tomar screenshot para debug
            try:
                driver.save_screenshot("powerbi_screenshot.png")
            except:
                pass
            
            # Buscar los valores de Parqueaderos, Peajes, Fecha y Asociados
            parqueaderos, peajes, fecha_analizada, asociados_data = find_parqueaderos_peajes_values(driver)
            
            # Mostrar el texto completo de la página para debug (solo primeras líneas)
            with st.expander("🔍 Ver texto extraído de la página (primeras 50 líneas)"):
                page_text = driver.find_element(By.TAG_NAME, "body").text
                lines = page_text.split('\n')[:50]
                st.text('\n'.join(lines))
            
            if parqueaderos is None or peajes is None:
                st.error("❌ No se pudieron extraer los valores del dashboard")
                st.warning("💡 Verifica que el dashboard esté público y los datos sean visibles")
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
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
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
