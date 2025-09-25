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

# ===========================
# TAB ANDINO
# ===========================
with tab_andino:
    st.header("🏢 Centro Comercial Andino")

    if st.button("Ejecutar scraping Andino"):
        scraper = FacturaParkScraper()
        with st.spinner("🔑 Iniciando sesión..."):
            ok = scraper.login(USERNAME, PASSWORD)
        if not ok:
            st.error("❌ Error al iniciar sesión en Andino")
        else:
            # Facturas pendientes
            with st.spinner("🔎 Consultando facturas pendientes..."):
                data = scraper.get_pending_invoices()
            st.subheader("📦 Facturas Pendientes")
            if data:
                st.table(data)
            else:
                st.warning("⚠️ No se encontraron facturas pendientes")

            # Jobs
            with st.spinner("🛠 Consultando jobs..."):
                jobs = scraper.get_jobs_config()
            st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
            if jobs:
                st.table(jobs)
            else:
                st.warning("⚠️ No se encontraron jobs")

            # Facturas recientes
            with st.spinner("🧾 Consultando facturas..."):
                invoices = scraper.get_invoices()
            st.subheader("🧾 FACTURAS")
            if invoices and invoices.get("factura_reciente"):
                st.metric("Total de facturas", invoices["total_facturas"])
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

# ===========================
# TAB BULEVAR
# ===========================
with tab_bulevar:
    st.header("🏢 Centro Comercial Bulevar")

    if st.button("Ejecutar scraping Bulevar"):
        scraper_b = FacturaBulevarScraper()
        with st.spinner("🔑 Iniciando sesión en Bulevar..."):
            ok = scraper_b.login(USERNAME, PASSWORD)
        if not ok:
            st.error("❌ Error al iniciar sesión en Bulevar")
        else:
            # Facturas pendientes
            with st.spinner("🔎 Consultando facturas pendientes..."):
                data_b = scraper_b.get_pending_invoices()
            st.subheader("📦 Facturas Pendientes (Bulevar)")
            if data_b:
                st.table(data_b)
            else:
                st.warning("⚠️ No se encontraron facturas pendientes")

            # Jobs
            with st.spinner("🛠 Consultando jobs Bulevar..."):
                jobs_b = scraper_b.get_jobs_config()
            st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS (Bulevar)")
            if jobs_b:
                st.table(jobs_b)
            else:
                st.warning("⚠️ No se encontraron jobs")

            # Facturas recientes
            with st.spinner("🧾 Consultando facturas Bulevar..."):
                invoices_b = scraper_b.get_invoices()
            st.subheader("🧾 FACTURAS (Bulevar)")
            if invoices_b and invoices_b.get("factura_reciente"):
                st.metric("Total de facturas (Bulevar)", invoices_b["total_facturas"])
                factura_b = invoices_b["factura_reciente"]
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
