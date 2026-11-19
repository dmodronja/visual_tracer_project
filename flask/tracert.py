# TRACERT.PY - script di tracciamento posizione host
import os
import re
import json
import gzip
import shutil
import socket
import urllib.request
from flask import Flask, render_template, jsonify, request
import geoip2.database
import geoip2.errors
import webbrowser

app = Flask(__name__)

# Cartella corrente dello script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database IP GeoLite e percorsi
DATABASE_DIR = os.path.join(BASE_DIR, "..", "database")
DB_FILE_NAME = 'GeoLite2-City.mmdb'
DB_PATH = os.path.join(DATABASE_DIR, DB_FILE_NAME)
URL_DATABASE = "https://cdn.jsdelivr.net/npm/geolite2-city/GeoLite2-City.mmdb.gz"

# Percorso lista città
LIST_PATH = os.path.join(BASE_DIR, "city_list.json")

# Metodo di verifica match hostname con dizionario
def analizza_hostname(hostname):
    hostname_lower = hostname.lower()
    parti = re.split(r'[^a-zA-Z0-9]', hostname_lower)
    
    # Caricamento lista da json
    with open(LIST_PATH, "r", encoding="utf-8") as f:
        DIZIONARIO_CITTA_HOST = json.load(f)

    for parte in parti:
        if parte in DIZIONARIO_CITTA_HOST:
            return DIZIONARIO_CITTA_HOST[parte]
    return None

# Funzione di lettura file configurazione utente
def leggi_configurazione():
    variabili = {}
    config = os.path.join(BASE_DIR, "..", "user/user.config")
    with open(config, "r", encoding="utf-8") as f:
        for riga in f:
            if ' = ' in riga:
                nome, valore = riga.split(" = ", 1)
                variabili[nome.strip()] = valore.strip()
        return variabili.get("LAT"), variabili.get("LONG")

# Funzione controllo database IP
def controlla_e_scarica_database():
    if not os.path.exists(DB_PATH):
        print("⚠️ Database degli IP non trovato.")
        print("Download (64 MB)...")
        
        file_compresso = os.path.join(BASE_DIR, 'GeoLite2-City.mmdb.gz')
        
        try:
            with urllib.request.urlopen(URL_DATABASE) as response, open(file_compresso, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print("Download completato. Estrazione database...")
            
            with gzip.open(file_compresso, 'rb') as f_in, open(DB_PATH, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
            os.remove(file_compresso)
            print(f"Database salvato in: {DB_PATH}")
            
        except Exception as e:
            print(f"Errore durante il download.")
    else:
        print(f"Database degli IP esistente.")

# Funzione di localizzazione IP
def localizza_IP(ip, hostname=None):
    # Ottiene la posizione dell'utente da file user.config
    # (se l'IP è privato mostra questa) 
    LAT, LONG = leggi_configurazione()

    # Definizione della posizione corrente
    if ip.startswith(("10.0.", "10.10.", "192.168.", "172.0.", "127.0.")):
        return {"lat": LAT, "lon": LONG, "city": "MyCity (mia LAN)", "ip": ip}
        
    # Controllo e scarto degli IP privati
    IP_PRIMI_SALTI = ["192.168.2.14", "192.168.255.2"]
    if ip in IP_PRIMI_SALTI:
        return {"lat": LAT, "lon": LONG, "city": "Centrale di Prossimità", "ip": ip}

    # Controllo tramite Hostname
    if hostname:
        info_citta = analizza_hostname(hostname)
        if info_citta:
            return {
                "lat": info_citta["lat"],
                "lon": info_citta["lon"],
                "city": info_citta["city"],
                "ip": f"{ip} ({hostname})"
            }

    # Fallback su MaxMind locale
    try:
        with geoip2.database.Reader(DB_PATH) as reader:
            response = reader.city(ip)
            citta = response.city.name if response.city.name else response.country.name
            
            # Aggiunta di organizzazione o ISP senza API
            if response.traits.isp:
                citta = f"{citta if citta else 'Nodo'} ({response.traits.isp})"
            elif not citta: 
                citta = "Nodo Internet"
                
            return {
                "lat": response.location.latitude,
                "lon": response.location.longitude,
                "city": citta,
                "ip": ip
            }
    except Exception:
        return None

# Comando traceroute
def traceroute(target):
    comando = f"tracert {target}" 
    print(f"Tracciamento verso: {target} in corso...")
    
    output = os.popen(comando).read()
    percorso_geografico = []
    
    for riga in output.splitlines():
        ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', riga)
        if ip_match:
            ip = ip_match.group(0)
            
            riga_pulita = riga.replace(f"[{ip}]", "").replace(ip, "")
            parti_testo = riga_pulita.split()
            
            hostname = None
            if parti_testo and not parti_testo[-1].endswith('ms') and parti_testo[-1] != '*':
                hostname = parti_testo[-1]
            
            if not hostname or hostname.replace('.','').isdigit():
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except Exception:
                    hostname = None

            info = localizza_IP(ip, hostname) 
            if info and info not in percorso_geografico:
                percorso_geografico.append(info)
                
    return percorso_geografico

# =========================================================================
# ROTTE DI FLASK
# =========================================================================
@app.route('/')
def home():
    # Caricamento interfaccia web
    return render_template('index.html')

@app.route('/traccia', methods=['POST'])
def ricevi_richiesta():
    # Riceve la richiesta JSON inviata via JavaScript dal browser
    dati = request.get_json()
    target = dati.get('target', 'google.com')
    
    # Esegue il tracciamento e restituisce la lista di coordinate al frontend
    risultato = traceroute(target)
    return jsonify(risultato)

if __name__ == '__main__':
    # Controllo database IP e avvio applicazione
    controlla_e_scarica_database()
    webbrowser.open_new("http://127.0.0.1:5000")
    app.run(debug=False, port=5000)