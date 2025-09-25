import streamlit as st
from scraper import FacturaParkScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊")
st.title("📊 FacturaPark Scraper")

USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

debug = st.checkbox("Mostrar debug del login (respuesta API)", value=False)

if st.button("Ejecutar scraping"):
    scraper = FacturaParkScraper()
    with st.spinner("🔑 Intentando login..."):
        res = scraper.login(USERNAME, PASSWORD, debug=debug)
    if not res.get("ok"):
        st.error("❌ Error al iniciar sesión (creds o método de login no coinciden).")
        if debug:
            st.write("**Debug login:**")
            st.write(f"Status: {res.get('status_code')}")
            st.write("JSON (si aplica):")
            st.write(res.get("json"))
            st.write("Text (truncado):")
            st.text(res.get("text"))
    else:
        st.success("✅ Login exitoso")
        with st.spinner("🔎 Extrayendo facturas pendientes..."):
            data = scraper.get_pending_invoices()
        if data:
            st.success("✅ Datos obtenidos")
            st.json(data)
        else:
            st.warning("⚠️ No se encontraron facturas pendientes (o la página requiere JS).")

