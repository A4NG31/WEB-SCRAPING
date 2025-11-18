import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper
from scraper_fontanar import FacturaFontanarScraper
from scraper_arkadia import FacturaArkadiaScraper
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import psycopg2
from datetime import datetime, timedelta

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

# Credenciales base de datos
DB_HOST = st.secrets["database"]["HOST"]
DB_PORT = st.secrets["database"]["PORT"]
DB_USER = st.secrets["database"]["USER"]
DB_PASS = st.secrets["database"]["PASS"]
DB_NAME = st.secrets["database"]["NAME"]

# Inicializar session_state
for key in ["andino", "bulevar", "fontanar", "arkadia"]:
    if key not in st.session_state:
        st.session_state[key] = {"ok": False, "data": None, "jobs": None, "invoices": None}

def get_transacciones_sin_cufe():
    """Consulta la base de datos para obtener las transacciones sin CUFE del día anterior"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        query = """
        SELECT 
            COUNT(*) AS transacciones_sin_cufe
        FROM 
            trns.transactions t
        INNER JOIN 
            trns.transactionstatus t2 ON t2.idstatus = t.status
        INNER JOIN 
            trns.invoices i ON i.idtransaction = t.idtransaction 
        INNER JOIN 
            trns.invcseriecons i2 ON i2.idseriecons = i.idseriecons
        INNER JOIN 
            trns.invcseries i3 ON i3.idserie = i2.idserie
        INNER JOIN 
            assc.commerces c ON c.idcommerce = t.idcommerce
        INNER JOIN 
            assc.associates a ON a.idassociate = c.idassociate 
        INNER JOIN 
            assc.services s ON s.idservice = t.idservice
        INNER JOIN 
            gpus.users u ON u.iduser = t.iduser 
        WHERE 
            DATE(i.createdat) = (CURRENT_DATE - INTERVAL '1 day')
            AND i3.seriename NOT IN ('FEV1', 'VCP')
            AND (i.cufe IS NULL OR TRIM(i.cufe) = '');
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        st.error(f"Error al consultar la base de datos: {str(e)}")
        return None

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
        with st.spinner("Consultando base de datos..."):
            # Obtener transacciones sin CUFE del día anterior
            transacciones_sin_cufe = get_transacciones_sin_cufe()
            
            # Obtener fecha de ayer
            fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        
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
        
        # Añadir información de transacciones sin CUFE
        if transacciones_sin_cufe is not None:
            mensaje += f"\nFacturas sin CUFE ({fecha_ayer}):\n"
            mensaje += f"Total: {transacciones_sin_cufe}"
        else:
            mensaje += f"\n⚠️ No se pudo obtener la información de facturas sin CUFE"
        
        st.text_area("Mensaje generado", mensaje, height=300)
