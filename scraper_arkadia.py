import requests
import pandas as pd

class FacturaArkadiaScraper:
    def __init__(self):
        self.base_url = "https://facturaelectronica.arkadiacentrocomercial.com/"
        self.login_url = "https://facturaelectronica.gopass.com.co/api/accc_auth/login"
        self.invoices_pending_url = "https://facturaelectronica.gopass.com.co/api/trns_invoices/pendingEmit?$top=10&$skip=0&$select=pending,idcomemrce,name&$orderby=idserietype%20asc&additionalQuery="
        self.invoices_url = "https://facturaelectronica.gopass.com.co/api/trns_transparking/getcustom?$top=10&$skip=0&additionalQuery=t.transdate%20between%20%272025-09-26%2000%3A00%3A00%20-5%3A00%27%20and%20%272025-09-26%2023:59:59%20-5:00%27&headers=false"
        self.jobs_url = "https://facturaelectronica.gopass.com.co/api/genc_jobsconfig?$top=10&$skip=0&$select=idjob,jobname,scheduletype,repeatinterval,maxconcurrent,startdate,enddate,restartable,eventqueuename,jobpriority,runcount,maxruns,failurecount,maxfailures,retrycount,laststartdate,lastrunduration,nextrundate,maxrunduration,logginglevel,raiseevents,enabled,email,sms,createduser,createdat,updateduser,updatedat&$orderby=idjob%20asc"
        self.session = requests.Session()
        self.token = None

    def login(self, username, password):
        payload = {"email": username, "password": password}
        try:
            response = self.session.post(self.login_url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.token = data["tokens"]["access"]["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        except Exception as e:
            print(f"Error login Arkadia: {e}")
            return False

    def get_pending_invoices(self):
        try:
            resp = self.session.get(self.invoices_pending_url)
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("rows", [])
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error fetching pending invoices Arkadia: {e}")
            return pd.DataFrame()

    def get_jobs_config(self):
        try:
            resp = self.session.get(self.jobs_url)
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("rows", [])
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error fetching jobs Arkadia: {e}")
            return pd.DataFrame()

    def get_invoices(self):
        try:
            resp = self.session.get(self.invoices_url)
            resp.raise_for_status()
            data = resp.json()
            # Aquí puedes ajustar según cómo quieres procesar las facturas recientes
            total_facturas = len(data.get("data", {}).get("rows", []))
            factura_reciente = data.get("data", {}).get("rows", [{}])[0] if total_facturas > 0 else None
            return {"total_facturas": total_facturas, "factura_reciente": factura_reciente}
        except Exception as e:
            print(f"Error fetching invoices Arkadia: {e}")
            return {"total_facturas": 0, "factura_reciente": None}
