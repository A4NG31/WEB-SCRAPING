import streamlit as st
from scraper import FacturaParkScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊")
st.title("📊 FacturaPark Scraper")

USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

if st.button("Ejecutar scraping"):
    scraper = FacturaParkScraper()
    with st.spinner("🔑 Iniciando sesión..."):
        ok = scraper.login(USERNAME, PASSWORD)
    if not ok:
        st.error("❌ Error al iniciar sesión")
    else:
        # Facturas pendientes
        with st.spinner("🔎 Consultando facturas pendientes..."):
            data = scraper.get_pending_invoices()
        st.subheader("📦 Facturas Pendientes")
        if data:
            st.table(data)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        # Última actualización de Jobs
        with st.spinner("🛠 Consultando jobs..."):
            jobs = scraper.get_jobs_config()
        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if jobs:
            st.table(jobs)
        else:
            st.warning("⚠️ No se encontraron jobs")

        # Facturas (más reciente y total)
        with st.spinner("🧾 Consultando facturas..."):
            invoices = scraper.get_invoices()
        st.subheader("🧾 FACTURAS")
        if invoices and invoices.get("factura_reciente"):
            st.metric("Total de facturas", invoices["total_facturas"])
            st.json(invoices["factura_reciente"])
        else:
            st.warning("⚠️ No se encontraron facturas")
