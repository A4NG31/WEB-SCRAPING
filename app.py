import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper
from scraper_fontanar import FacturaFontanarScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊", layout="wide")
st.title("📊 FacturaPark Scraper")

USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

# Crear pestañas
tab_andino, tab_bulevar, tab_fontanar = st.tabs([
    "🏢 Centro Comercial Andino", 
    "🏢 Centro Comercial Bulevar",
    "🏢 Centro Comercial Fontanar"
])

# Botón general para ejecutar los 3 scrapers
if st.button("Ejecutar scraping de todos los centros comerciales"):
    with st.spinner("🔑 Iniciando sesión en todos los centros comerciales..."):
        # Andino
        scraper_andino = FacturaParkScraper()
        ok_andino = scraper_andino.login(USERNAME, PASSWORD)
        data_andino = scraper_andino.get_pending_invoices() if ok_andino else None
        jobs_andino = scraper_andino.get_jobs_config() if ok_andino else None
        invoices_andino = scraper_andino.get_invoices() if ok_andino else None

        # Bulevar
        scraper_bulevar = FacturaBulevarScraper()
        ok_bulevar = scraper_bulevar.login(USERNAME, PASSWORD)
        data_bulevar = scraper_bulevar.get_pending_invoices() if ok_bulevar else None
        jobs_bulevar = scraper_bulevar.get_jobs_config() if ok_bulevar else None
        invoices_bulevar = scraper_bulevar.get_invoices() if ok_bulevar else None

        # Fontanar
        scraper_fontanar = FacturaFontanarScraper()
        ok_fontanar = scraper_fontanar.login("admin@fontanar.com", "gopass2023")
        data_fontanar = scraper_fontanar.get_pending_invoices() if ok_fontanar else None
        jobs_fontanar = scraper_fontanar.get_jobs_config() if ok_fontanar else None
        invoices_fontanar = scraper_fontanar.get_invoices() if ok_fontanar else None

# ===========================
# TAB FONTANAR
# ===========================
with tab_fontanar:
    st.header("🏢 Centro Comercial Fontanar")

    if 'ok_fontanar' in locals() and ok_fontanar:
        st.subheader("📦 Facturas Pendientes")
        if data_fontanar:
            st.table(data_fontanar)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if jobs_fontanar:
            st.table(jobs_fontanar)
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS")
        if invoices_fontanar and invoices_fontanar.get("factura_reciente"):
            st.metric("Total de facturas (Fontanar)", invoices_fontanar["total_facturas"])
            factura = invoices_fontanar["factura_reciente"]
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
    elif 'ok_fontanar' in locals() and not ok_fontanar:
        st.error("❌ Error al iniciar sesión en Fontanar")
    else:
        st.info("Presiona 'Ejecutar scraping de todos los centros comerciales' para cargar datos.")
