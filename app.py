import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊", layout="wide")
st.title("📊 FacturaPark Scraper")

USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

# Crear pestañas
tab_andino, tab_bulevar = st.tabs(["🏢 Centro Comercial Andino", "🏢 Centro Comercial Bulevar"])

# Botón general para ejecutar ambos scrapers
if st.button("Ejecutar scraping Andino y Bulevar"):
    with st.spinner("🔑 Iniciando sesión en ambos centros comerciales..."):
        # Scraper Andino
        scraper_andino = FacturaParkScraper()
        ok_andino = scraper_andino.login(USERNAME, PASSWORD)
        if ok_andino:
            data_andino = scraper_andino.get_pending_invoices()
            jobs_andino = scraper_andino.get_jobs_config()
            invoices_andino = scraper_andino.get_invoices()
        else:
            data_andino, jobs_andino, invoices_andino = None, None, None

        # Scraper Bulevar
        scraper_bulevar = FacturaBulevarScraper()
        ok_bulevar = scraper_bulevar.login(USERNAME, PASSWORD)
        if ok_bulevar:
            data_bulevar = scraper_bulevar.get_pending_invoices()
            jobs_bulevar = scraper_bulevar.get_jobs_config()
            invoices_bulevar = scraper_bulevar.get_invoices()
        else:
            data_bulevar, jobs_bulevar, invoices_bulevar = None, None, None

# ===========================
# TAB ANDINO
# ===========================
with tab_andino:
    st.header("🏢 Centro Comercial Andino")

    if 'ok_andino' in locals() and ok_andino:
        st.subheader("📦 Facturas Pendientes")
        if data_andino:
            st.table(data_andino)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if jobs_andino:
            st.table(jobs_andino)
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS")
        if invoices_andino and invoices_andino.get("factura_reciente"):
            st.metric("Total de facturas", invoices_andino["total_facturas"])
            factura = invoices_andino["factura_reciente"]
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
    elif 'ok_andino' in locals() and not ok_andino:
        st.error("❌ Error al iniciar sesión en Andino")
    else:
        st.info("Presiona 'Ejecutar scraping Andino y Bulevar' para cargar datos.")

# ===========================
# TAB BULEVAR
# ===========================
with tab_bulevar:
    st.header("🏢 Centro Comercial Bulevar")

    if 'ok_bulevar' in locals() and ok_bulevar:
        st.subheader("📦 Facturas Pendientes")
        if data_bulevar:
            st.table(data_bulevar)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS (Bulevar)")
        if jobs_bulevar:
            st.table(jobs_bulevar)
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS (Bulevar)")
        if invoices_bulevar and invoices_bulevar.get("factura_reciente"):
            st.metric("Total de facturas (Bulevar)", invoices_bulevar["total_facturas"])
            factura_b = invoices_bulevar["factura_reciente"]
            campos_clave_b = {
                "ID": factura_b.get("idinvoice"),
                "Id Factura": factura_b.get("idtransaction"),
                "Id Transacción": factura_b.get("idtransparking"),
                "Fecha Factura": factura_b.get("fecha_factura"),
                "Valor Neto": f"${factura_b.get('valor_neto_factura'):,}" if factura_b.get("valor_neto_factura") else None,
                "Valor Total": f"${factura_b.get('valor_factura'):,}" if factura_b.get("valor_factura") else None,
                "Tercero": factura_b.get("nombretercero"),
                "Fecha Salida": factura_b.get("outdate"),
                "Estado": factura_b.get("invoicestatus"),
                "CUFE": factura_b.get("cufe"),
                "Factura": factura_b.get("id_unico"),
            }
            st.dataframe(pd.DataFrame([campos_clave_b]), use_container_width=True)
        else:
            st.warning("⚠️ No se encontraron facturas")
    elif 'ok_bulevar' in locals() and not ok_bulevar:
        st.error("❌ Error al iniciar sesión en Bulevar")
    else:
        st.info("Presiona 'Ejecutar scraping Andino y Bulevar' para cargar datos.")
