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
        with st.spinner("🔎 Consultando facturas pendientes..."):
            data = scraper.get_pending_invoices()
        if data:
            st.success("✅ Datos obtenidos")
            st.table(data)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")
