import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper
from scraper_fontanar import FacturaFontanarScraper
from scraper_arkadia import FacturaArkadiaScraper
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊", layout="wide")
st.title("📊 FacturaPark Scraper")

# Credenciales desde secrets
USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]
ARKADIA_USER = st.secrets["arkadia"]["USERNAME"]
ARKADIA_PASS = st.secrets["arkadia"]["PASSWORD"]

# Inicializar session_state
for key in ["andino", "bulevar", "fontanar", "arkadia"]:
    if key not in st.session_state:
        st.session_state[key] = {"ok": False, "data": None, "jobs": None, "invoices": None}

def run_scraper(name, scraper_class, username, password):
    scraper = scraper_class()
    ok = scraper.login(username, password)
    result = {"ok": ok, "data": None, "jobs": None, "invoices": None}
    if ok:
        result["data"] = scraper.get_pending_invoices()
        result["jobs"] = scraper.get_jobs_config()
        result["invoices"] = scraper.get_invoices()
    return name, result

if st.button("Ejecutar scraping de todos los centros comerciales"):
    with st.spinner("🔑 Ejecutando scrapers en paralelo..."):
        futures = []
        with ThreadPoolExecutor() as executor:
            futures.append(executor.submit(run_scraper, "andino", FacturaParkScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "bulevar", FacturaBulevarScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "fontanar", FacturaFontanarScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "arkadia", FacturaArkadiaScraper, ARKADIA_USER, ARKADIA_PASS))

            for future in as_completed(futures):
                name, result = future.result()
                st.session_state[name] = result

# ===========================
# PESTAÑAS
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
        if state["data"] is not None and not state["data"].empty:
            st.table(state["data"])
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if state["jobs"] is not None and not state["jobs"].empty:
            st.table(state["jobs"])
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
        st.error(f"❌ Error al iniciar sesión en {display_name}")
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
