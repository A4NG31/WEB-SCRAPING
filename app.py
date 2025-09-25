import streamlit as st
from scraper import FacturaParkScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊")

st.title("📊 FacturaPark Scraper")

# Leer credenciales desde secrets
USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

if st.button("Ejecutar scraping"):
    scraper = FacturaParkScraper()
    with st.spinner("🔑 Iniciando sesión..."):
        if scraper.login(USERNAME, PASSWORD):
            data = scraper.get_pending_invoices()
            if data:
                st.success("✅ Datos obtenidos exitosamente")
                st.json(data)
            else:
                st.warning("⚠️ No se encontraron facturas pendientes")
        else:
            st.error("❌ Error al iniciar sesión")
