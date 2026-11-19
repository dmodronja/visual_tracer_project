# TRACERT.PY - script di tracciamento posizione host
import os
import re
import gzip
import shutil
import socket
import urllib.request
from flask import Flask, render_template, jsonify, request
import geoip2.database
import geoip2.errors
import webbrowser

app = Flask(__name__)
print("STATIC FOLDER:", app.static_folder)
print("ESISTE:", os.path.isfile(os.path.join(app.static_folder, "leaflet", "leaflet.js")))
if os.path.isdir(os.path.join(app.static_folder, "leaflet")):
    print("CONTENUTO:", os.listdir(os.path.join(app.static_folder, "leaflet")))

# Cartella corrente dello script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database IP GeoLite e percorsi
DATABASE_DIR = os.path.join(BASE_DIR, "..", "database")
DB_FILE_NAME = 'GeoLite2-City.mmdb'
DB_PATH = os.path.join(DATABASE_DIR, DB_FILE_NAME)
URL_DATABASE = "https://cdn.jsdelivr.net/npm/geolite2-city/GeoLite2-City.mmdb.gz"

# Dizionario città principali
DIZIONARIO_CITTA_HOST = {
    "mil": {"lat": 45.4642, "lon": 9.1900, "city": "Milano (Dorsale)"},
    "milan": {"lat": 45.4642, "lon": 9.1900, "city": "Milano (Dorsale)"},
    "mxp": {"lat": 45.6301, "lon": 8.7231, "city": "Milano Malpensa"},
    "lin": {"lat": 45.4451, "lon": 9.2777, "city": "Milano Linate"},
    
    "rm": {"lat": 41.9028, "lon": 12.4964, "city": "Roma (Dorsale)"},
    "rom": {"lat": 41.9028, "lon": 12.4964, "city": "Roma (Dorsale)"},
    "rome": {"lat": 41.9028, "lon": 12.4964, "city": "Roma (Dorsale)"},
    "fco": {"lat": 41.8003, "lon": 12.2389, "city": "Roma Fiumicino"},
    
    "tor": {"lat": 45.0703, "lon": 7.6869, "city": "Torino (Nodo)"},
    "trn": {"lat": 45.2008, "lon": 7.6496, "city": "Torino Caselle"},
    
    "bol": {"lat": 44.4949, "lon": 11.3426, "city": "Bologna (Nodo)"},
    "blq": {"lat": 44.5308, "lon": 11.2887, "city": "Bologna Borgo P."},
    
    "nap": {"lat": 40.8518, "lon": 14.2681, "city": "Napoli (Nodo)"},
    "naples": {"lat": 40.8518, "lon": 14.2681, "city": "Napoli (Nodo)"},
    
    "ven": {"lat": 45.4408, "lon": 12.3155, "city": "Venezia (Nodo)"},
    "vce": {"lat": 45.5053, "lon": 12.3519, "city": "Venezia Tessera"},
    
    "gen": {"lat": 44.4056, "lon": 8.9463, "city": "Genova (Nodo)"},
    "goa": {"lat": 44.4133, "lon": 8.8475, "city": "Genova Sestri"},
    
    "fir": {"lat": 43.7696, "lon": 11.2558, "city": "Firenze"},
    "flr": {"lat": 43.8086, "lon": 11.2012, "city": "Firenze Peretola"},
    
    "pal": {"lat": 38.1157, "lon": 13.3615, "city": "Palermo"},
    "pmo": {"lat": 38.1820, "lon": 13.1034, "city": "Palermo Punta Raisi"},
    
    "cta": {"lat": 37.4703, "lon": 15.0658, "city": "Catania Fontanarossa"},
    "bri": {"lat": 41.1389, "lon": 16.7606, "city": "Bari Palese"},
    "cag": {"lat": 39.2515, "lon": 9.0543, "city": "Cagliari Elmas"},
    
    "fra": {"lat": 50.1109, "lon": 8.6821, "city": "Francoforte (DE)"},
    "frankfurt": {"lat": 50.1109, "lon": 8.6821, "city": "Francoforte (DE)"},
    
    "ams": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam (NL)"},
    "amsterdam": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam (NL)"},
    
    "lon": {"lat": 51.5074, "lon": -0.1278, "city": "Londra (UK)"},
    "london": {"lat": 51.5074, "lon": -0.1278, "city": "Londra (UK)"},
    "lhr": {"lat": 51.4700, "lon": -0.4543, "city": "Londra Heathrow"},
    
    "par": {"lat": 48.8566, "lon": 2.3522, "city": "Parigi (FR)"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "city": "Parigi (FR)"},
    "cdg": {"lat": 49.0097, "lon": 2.5479, "city": "Parigi CDG"},
    
    "mad": {"lat": 40.4168, "lon": -3.7038, "city": "Madrid (ES)"},
    "madrid": {"lat": 40.4168, "lon": -3.7038, "city": "Madrid (ES)"},
    
    "bar": {"lat": 41.3851, "lon": 2.1734, "city": "Barcellona (ES)"},
    "bcn": {"lat": 41.2974, "lon": 2.0833, "city": "Barcellona El Prat"},
    
    "zur": {"lat": 47.3769, "lon": 8.5417, "city": "Zurigo (CH)"},
    "zrh": {"lat": 47.4582, "lon": 8.5555, "city": "Zurigo Airport"},
    
    "vie": {"lat": 48.2082, "lon": 16.3738, "city": "Vienna (AT)"},
    
    "nyc": {"lat": 40.7128, "lon": -74.0060, "city": "New York City (US)"},
    "jfk": {"lat": 40.6413, "lon": -73.7781, "city": "New York JFK"},
    "ash": {"lat": 39.0438, "lon": -77.4875, "city": "Ashburn / Virginia (US Data Center Hub)"},
    "sfo": {"lat": 37.6190, "lon": -122.3748, "city": "San Francisco (US)"},
    "lax": {"lat": 33.9416, "lon": -118.4085, "city": "Los Angeles (US)"},

    "marseille": {"lat": 43.2965, "lon": 5.3698, "city": "Marsiglia (Hub Cavi Sottomarini Med)"},
    "mrs": {"lat": 43.2965, "lon": 5.3698, "city": "Marsiglia (Hub Cavi Sottomarini Med)"},
    "palermo": {"lat": 38.1157, "lon": 13.3615, "city": "Palermo (Approdo cavo ME-WE-WE)"},
    "pmo": {"lat": 38.1157, "lon": 13.3615, "city": "Palermo (Approdo cavo ME-WE-WE)"},
    "bilbao": {"lat": 43.2630, "lon": -2.9350, "city": "Bilbao (Spagna - Cavo Marea di Microsoft/Meta)"},
    "bio": {"lat": 43.2630, "lon": -2.9350, "city": "Bilbao (Spagna - Cavo Marea)"},
    "bude": {"lat": 50.8262, "lon": -4.5436, "city": "Bude (UK - Approdo Transatlantico)"},
    "ashburn": {"lat": 39.0438, "lon": -77.4875, "city": "Ashburn (USA - Il centro di internet mondiale)"},
    "ash": {"lat": 39.0438, "lon": -77.4875, "city": "Ashburn (USA)"}
}

# Metodo di verifica match hostname con dizionario
def analizza_hostname(hostname):
    hostname_lower = hostname.lower()
    parti = re.split(r'[^a-zA-Z0-9]', hostname_lower)
    
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