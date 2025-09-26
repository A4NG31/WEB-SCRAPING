import streamlit as st
import pandas as pd
from scraper import FacturaParkScraper
from scraper_bulevar import FacturaBulevarScraper
from scraper_fontanar import FacturaFontanarScraper

st.set_page_config(page_title="FacturaPark Scraper", page_icon="📊", layout="wide")
st.title("📊 FacturaPark Scraper")

USERNAME = st.secrets["credentials"]["USERNAME"]
PASSWORD = st.secrets["credentials"]["PASSWORD"]

# Inicializar session_state
for key in ["andino", "bulevar", "fontanar"]:
    if key not in st.session_state:
        st.session_state[key] = {"ok": False, "data": None, "jobs": None, "invoices": None}

# Botón general para ejecutar los 3 scrapers
if st.button("Ejecutar scraping de todos los centros comerciales"):
    with st.spinner("🔑 Iniciando sesión en todos los centros comerciales..."):
        # Andino
        scraper_andino = FacturaParkScraper()
        st.session_state["andino"]["ok"] = scraper_andino.login(USERNAME, PASSWORD)
        if st.session_state["andino"]["ok"]:
            st.session_state["andino"]["data"] = scraper_andino.get_pending_invoices()
            st.session_state["andino"]["jobs"] = scraper_andino.get_jobs_config()
            st.session_state["andino"]["invoices"] = scraper_andino.get_invoices()

        # Bulevar
        scraper_bulevar = FacturaBulevarScraper()
        st.session_state["bulevar"]["ok"] = scraper_bulevar.login(USERNAME, PASSWORD)
        if st.session_state["bulevar"]["ok"]:
            st.session_state["bulevar"]["data"] = scraper_bulevar.get_pending_invoices()
            st.session_state["bulevar"]["jobs"] = scraper_bulevar.get_jobs_config()
            st.session_state["bulevar"]["invoices"] = scraper_bulevar.get_invoices()

        # Fontanar
        scraper_fontanar = FacturaFontanarScraper()
        st.session_state["fontanar"]["ok"] = scraper_fontanar.login("admin@fontanar.com", "gopass2023")
        if st.session_state["fontanar"]["ok"]:
            st.session_state["fontanar"]["data"] = scraper_fontanar.get_pending_invoices()
            st.session_state["fontanar"]["jobs"] = scraper_fontanar.get_jobs_config()
            st.session_state["fontanar"]["invoices"] = scraper_fontanar.get_invoices()

# ===========================
# TAB ANDINO
# ===========================
tab_andino, tab_bulevar, tab_fontanar = st.tabs([
    "🏢 Centro Comercial Andino", 
    "🏢 Centro Comercial Bulevar",
    "🏢 Centro Comercial Fontanar"
])

with tab_andino:
    st.header("🏢 Centro Comercial Andino")
    if st.session_state["andino"]["ok"]:
        st.subheader("📦 Facturas Pendientes")
        if st.session_state["andino"]["data"]:
            st.table(st.session_state["andino"]["data"])
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if st.session_state["andino"]["jobs"]:
            st.table(st.session_state["andino"]["jobs"])
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS")
        invoices = st.session_state["andino"]["invoices"]
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
    elif st.session_state["andino"]["ok"] == False:
        st.error("❌ Error al iniciar sesión en Andino")
    else:
        st.info("Presiona 'Ejecutar scraping de todos los centros comerciales' para cargar datos.")

# ===========================
# TAB BULEVAR
# ===========================
with tab_bulevar:
    st.header("🏢 Centro Comercial Bulevar")
    if st.session_state["bulevar"]["ok"]:
        st.subheader("📦 Facturas Pendientes")
        if st.session_state["bulevar"]["data"]:
            st.table(st.session_state["bulevar"]["data"])
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if st.session_state["bulevar"]["jobs"]:
            st.table(st.session_state["bulevar"]["jobs"])
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS")
        invoices = st.session_state["bulevar"]["invoices"]
        if invoices and invoices.get("factura_reciente"):
            st.metric("Total de facturas (Bulevar)", invoices["total_facturas"])
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
    elif st.session_state["bulevar"]["ok"] == False:
        st.error("❌ Error al iniciar sesión en Bulevar")
    else:
        st.info("Presiona 'Ejecutar scraping de todos los centros comerciales' para cargar datos.")

# ===========================
# TAB FONTANAR
# ===========================
with tab_fontanar:
    st.header("🏢 Centro Comercial Fontanar")
    if st.session_state["fontanar"]["ok"]:
        st.subheader("📦 Facturas Pendientes")
        if st.session_state["fontanar"]["data"]:
            st.table(st.session_state["fontanar"]["data"])
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")

        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        if st.session_state["fontanar"]["jobs"]:
            st.table(st.session_state["fontanar"]["jobs"])
        else:
            st.warning("⚠️ No se encontraron jobs")

        st.subheader("🧾 FACTURAS")
        invoices = st.session_state["fontanar"]["invoices"]
        if invoices and invoices.get("factura_reciente"):
            st.metric("Total de facturas (Fontanar)", invoices["total_facturas"])
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
    elif st.session_state["fontanar"]["ok"] == False:
        st.error("❌ Error al iniciar sesión en Fontanar")
    else:
        st.info("Presiona 'Ejecutar scraping de todos los centros comerciales' para cargar datos.")
