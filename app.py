import streamlit as st
from scraper import FacturaParkScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊")
st.title("📊 FacturaPark Scraper")

USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

if st.button("Ejecutar scraping"):
    scraper = FacturaParkScraper()
    with st.spinner("🔑 Intentando login..."):
        ok = scraper.login(USERNAME, PASSWORD)
    if not ok:
        st.error("❌ Error al iniciar sesión (creds o método de login no coinciden). Revisa DevTools y comparte el payload si quieres que lo adapte.")
    else:
        with st.spinner("🔎 Extrayendo facturas pendientes..."):
            data = scraper.get_pending_invoices()
        if data:
            st.success("✅ Datos obtenidos")
            st.json(data)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes (o la página requiere JS avanzado).")
