from flask import Flask, jsonify, request
import psycopg2
from datetime import datetime, timedelta
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Esto permite que Streamlit se comunique con el API

# Configuración de la base de datos
DB_CONFIG = {
    "host": "34.72.44.63",
    "port": 5432,
    "user": "powerbi",
    "password": "tu_password_de_la_base",  # Cambia esto
    "database": "nombre_de_tu_base_datos"  # Cambia esto
}

def get_db_connection():
    """Crea conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def home():
    return jsonify({"message": "API Intermedio para Facturación", "status": "active"})

@app.route('/transacciones-sin-cufe')
def get_transacciones_sin_cufe():
    """Endpoint para obtener transacciones sin CUFE del día anterior"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            COUNT(*) AS transacciones_sin_cufe
        FROM 
            trns.transactions t
        INNER JOIN 
            trns.transactionstatus t2 ON t2.idstatus = t.status
        INNER JOIN 
            trns.invoices i ON i.idtransaction = t.idtransaction 
        INNER JOIN 
            trns.invcseriecons i2 ON i2.idseriecons = i.idseriecons
        INNER JOIN 
            trns.invcseries i3 ON i3.idserie = i2.idserie
        INNER JOIN 
            assc.commerces c ON c.idcommerce = t.idcommerce
        INNER JOIN 
            assc.associates a ON a.idassociate = c.idassociate 
        INNER JOIN 
            assc.services s ON s.idservice = t.idservice
        INNER JOIN 
            gpus.users u ON u.iduser = t.iduser 
        WHERE 
            DATE(i.createdat) = (CURRENT_DATE - INTERVAL '1 day')
            AND i3.seriename NOT IN ('FEV1', 'VCP')
            AND (i.cufe IS NULL OR TRIM(i.cufe) = '');
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Obtener fecha de ayer para el reporte
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        
        return jsonify({
            "transacciones_sin_cufe": result[0] if result else 0,
            "fecha_consulta": fecha_ayer,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/health')
def health_check():
    """Endpoint para verificar que el API está funcionando"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
