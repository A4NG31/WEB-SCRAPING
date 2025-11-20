result = {"ok": ok, "data": None, "jobs": None, "invoices": None}
    
    if ok:
        # Obtenemos datos según cada scraper
        data = scraper.get_pending_invoices()
        
        # Convertir listas a DataFrame para que la UI las muestre
        if isinstance(data, list):
            try:
                result["data"] = pd.DataFrame(data) if len(data) > 0 else pd.DataFrame()
            except Exception:
                try:
                    result["data"] = pd.DataFrame([data])
                except Exception:
                    result["data"] = pd.DataFrame()
        elif isinstance(data, pd.DataFrame):
            result["data"] = data
        else:
            try:
                result["data"] = pd.DataFrame(data) if data else pd.DataFrame()
            except Exception:
                result["data"] = pd.DataFrame()
        
        jobs = scraper.get_jobs_config()
        
        # Convertimos jobs a DataFrame si es lista
        if isinstance(jobs, list):
            try:
                jobs = pd.DataFrame(jobs) if len(jobs) > 0 else pd.DataFrame()
            except Exception:
                jobs = pd.DataFrame()
        
        # Filtro especial SOLO para Arkadia
        if name == "arkadia" and isinstance(jobs, pd.DataFrame) and not jobs.empty:
            jobs = jobs.rename(columns={
                "jobname": "NOMBRE",
                "raiseevents": "AUMENTO DE EVENTOS",
                "enabled": "HABILITADO",
                "updatedat": "FECHA DE ACTUALIZACIÓN"
            })
            jobs = jobs[["NOMBRE", "AUMENTO DE EVENTOS", "HABILITADO", "FECHA DE ACTUALIZACIÓN"]]
        
        result["jobs"] = jobs
        result["invoices"] = scraper.get_invoices()
    
    return name, result

# ===========================
# FORMATO DE FECHA
# ===========================
def format_fecha(fecha):
    """Convierte la fecha a formato dd/mm/yyyy HH:MM"""
    try:
        return pd.to_datetime(fecha).strftime("%d/%m/%Y %H:%M")
    except:
        return str(fecha)

# ===========================
# INTERFAZ PRINCIPAL
# ===========================
if st.button("Ejecutar scraping de todos los centros comerciales"):
    with st.spinner("🔑 Ejecutando scrapers en paralelo..."):
        futures = []
        with ThreadPoolExecutor() as executor:
            futures.append(executor.submit(run_scraper, "andino", FacturaParkScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "bulevar", FacturaBulevarScraper, USERNAME, PASSWORD))
            futures.append(executor.submit(run_scraper, "fontanar", FacturaFontanarScraper, FONTANAR_USER, FONTANAR_PASS))
            futures.append(executor.submit(run_scraper, "arkadia", FacturaArkadiaScraper, ARKADIA_USER, ARKADIA_PASS))
            
            for future in as_completed(futures):
                name, result = future.result()
                st.session_state[name] = result
        
        st.session_state["scraping_done"] = True

# ===========================
# TAB PESTAÑAS
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
        if isinstance(state["data"], pd.DataFrame) and not state["data"].empty:
            st.table(state["data"])
        else:
            st.warning("⚠️ No se encontraron facturas pendientes")
        
        st.subheader("🕒 ULTIMA ACTUALIZACIÓN DE JOBS")
        jobs = state["jobs"]
        if isinstance(jobs, pd.DataFrame) and not jobs.empty:
            st.table(jobs)
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
        st.info(f" 👆 Oprime el boton para inciar el proceso ")
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

# ===========================
# BOTÓN GENERAR MENSAJE WHATSAPP
# ===========================
if st.session_state.get("scraping_done", False):
    if st.button("📩 Generar mensaje de WhatsApp"):
        with st.spinner("🌐 Obteniendo datos de Power BI..."):
            powerbi_data = get_powerbi_data()
            
            if powerbi_data is None:
                st.error("❌ No se pudieron obtener los datos de Power BI. No se puede generar el mensaje.")
                st.stop()
            
            mensaje = (
                "Buen día, se realiza informe de facturación electrónica, al momento no contamos con facturación pendiente.\n\n"
                "Se realiza de igual forma revisión de motores FE:\n\n"
            )
            
            for name, display_name in {
                "andino": "Motor Andino",
                "bulevar": "Motor Bulevar",
                "fontanar": "Motor Fontanar",
                "arkadia": "Motor Arkadia"
            }.items():
                state = st.session_state[name]
                
                if state["ok"]:
                    pendientes = 0
                    data = state["data"]
                    
                    # Diferenciamos Arkadia vs los demás
                    if name == "arkadia":
                        if isinstance(data, pd.DataFrame) and not data.empty:
                            if "pending" in data.columns:
                                pendientes = data.iloc[0]["pending"]
                            elif "total_pendientes" in data.columns:
                                pendientes = data.iloc[0]["total_pendientes"]
                        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            pendientes = data[0].get("pending") or data[0].get("total_pendientes", 0)
                    else:
                        # Andino, Bulevar y Fontanar usan "total_pendientes"
                        if isinstance(data, pd.DataFrame) and not data.empty and "total_pendientes" in data.columns:
                            pendientes = data.iloc[0]["total_pendientes"]
                        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            pendientes = data[0].get("total_pendientes", 0)
                    
                    # Facturas hoy
                    total_hoy = state["invoices"]["total_facturas"] if state["invoices"] else 0
                    
                    # Fecha jobs
                    fecha_jobs = "Sin fecha"
                    if isinstance(state["jobs"], pd.DataFrame) and not state["jobs"].empty:
                        if name == "arkadia" and "FECHA DE ACTUALIZACIÓN" in state["jobs"].columns:
                            fecha_jobs = format_fecha(state["jobs"].iloc[0]["FECHA DE ACTUALIZACIÓN"])
                        elif "ultima_actualizacion" in state["jobs"].columns:
                            fecha_jobs = format_fecha(state["jobs"].iloc[0]["ultima_actualizacion"])
                    
                    mensaje += (
                        f"* {display_name} {'con ' + str(pendientes) + ' facturas pendientes' if int(pendientes) else 'sin facturas pendientes'}, "
                        f"con {total_hoy} facturas del día de hoy, con sus Jobs actualizados ({fecha_jobs})\n\n"
                    )
            
            # Añadir los datos de Power BI al mensaje
            mensaje += f"\nFacturas sin CUFE: (BI actualizado: {powerbi_data['fecha_analizada']})\n\n"
            mensaje += f"Parqueaderos: {powerbi_data['parqueaderos']:,}\n"
            mensaje += f"Peajes: {powerbi_data['peajes']:,}"
            
            # NUEVO: Añadir sección de asociados
            if powerbi_data.get('asociados'):
                mensaje += f"\n\nTransacciones Sin Factura por asociado: (BI actualizado: {powerbi_data['fecha_analizada']})\n\n"
                
                for asociado in powerbi_data['asociados']:
                    nombre = asociado['nombre']
                    cantidad = asociado['cantidad']
                    mensaje += f"{nombre}: {cantidad}\n"
                
                # Añadir total
                mensaje += f"\nTOTAL: {powerbi_data['total_asociados']:,}"
            
            st.text_area("Mensaje generado", mensaje, height=500)
