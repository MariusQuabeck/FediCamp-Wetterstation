# 🌤️ FediCamp Wetterstation

Ein einfaches, aber funktionsreiches Web-Frontend für Wetterstationen, optimiert für das FediCamp 2025.  
Die App empfängt Wetterdaten per HTTP POST, speichert sie im CSV-Format und bietet verschiedene Webansichten – inklusive Live-Charts, Light/Dark-Modus und mobiler Optimierung.

---

## 🚀 Features

- 🌐 Web-Oberfläche mit Desktop- und Mobilansicht (`/desktop`, `/mobile`)
- 📊 Diagrammseite mit Chart.js (`/charts`)
- 🌓 Light- und Darkmode inklusive automatischer Logo-Umschaltung
- 📦 Speicherung empfangener Wetterdaten in `wetterdaten.csv`
- 🔐 Absicherung des POST-Empfangs durch einen konfigurierbaren `PASSKEY`
- 🧭 Windrichtung auch als Klartext (z. B. „Nord-Ost“)
- ⚠️ Fehleranzeige im Frontend bei Problemen mit der Datenverbindung
- 🔄 Automatischer Reload bei Netzwerkfehlern
- 🔁 Anzeige-Update alle 30 Sekunden

---

## 📷 Screenshots

![Dashboard](https://github.com/user-attachments/assets/b9ab69e6-abc6-4913-997b-e038db9d2c23)

![Charts](https://github.com/user-attachments/assets/1df84b47-cbd9-4c9e-9eb4-fc6d5a25d166)


---

## 📡 Unterstützte Wetterstation

Verwendet wird das Modell **Ecowitt GW1101 (Wi-Fi Wetter-Gateway)**.  
Dieses Gateway empfängt Daten von kompatiblen Funksensoren (z. B. WH65, WH32, WH40) und sendet sie per HTTP POST weiter.

Du kannst dieses Setup aber auch mit anderen Ecowitt-kompatiblen Gateways (z. B. GW2000, WH2650) nutzen – vorausgesetzt sie unterstützen das **"Customized Upload"** Feature.

![Wetterstation_FediCamp2025](https://github.com/user-attachments/assets/311f6f32-da6c-4ec0-8e40-873d281e93e5)
---

## 🔐 PASSKEY einrichten

## 🔑 Passkey herausfinden

Die Wetterstation sendet Daten über das Ecowitt-Protokoll mit einem **Passkey**. Wenn dieser nicht im Webinterface sichtbar ist, kannst du ihn folgendermaßen auslesen:

1. Öffne das Webinterface der GW1101.
2. Gehe zu **Customized → Weather Services**.
3. Stelle ein:
   - **Protocol**: Ecowitt  
   - **Server IP/Hostname**: IP deines Raspberry Pi (z. B. `192.168.178.42`)  
   - **Path**: `/`  
   - **Port**: `8000`
4. Nach dem Speichern einige Minuten warten.
5. Schaue auf dem Pi in die Datei `debug_post.log`:

   ```bash
   tail -n 5 debug_post.log
   ```

   Beispiel:
   ```
   2025-07-17T12:34:56 {'PASSKEY': 'AB12CD34EF56GH78', ...}
   ```

6. Lege diesen Passkey in eine Datei `passkey.txt` im Projektordner – nur der Schlüssel, ohne Zeilenumbruch.


⚠️ Wenn kein gültiger `PASSKEY` gesetzt ist, werden alle POST-Anfragen **abgelehnt**.

---

## ⚙️ Einrichtung der Wetterstation (GW1101)

### Schritt 1: Webinterface öffnen

1. Stelle sicher, dass dein Computer und das GW1101 im gleichen Netzwerk sind.
2. Öffne das Webinterface des GW1101, z. B. via `http://GW1101.local/` oder IP-Adresse im Browser.

### Schritt 2: Customized Upload konfigurieren

Gehe zu:

**`Settings → Customized Upload`**  
Aktiviere den Haken bei **"Enable"** und trage folgende Werte ein:

- **Upload Protocol**: `Ecowitt`
- **Upload Interval**: `30` Sekunden (empfohlen)
- **Server IP / Hostname**: IP oder Domain deines Raspberry Pi/Webservers
- **Path**: `/`
- **Port**: `8000` (oder dein eigener Port)
- **Upload Interval** `30`

Beispiel:
```
Server: 192.168.1.42
Path: /
Port: 8000
Upload Interval: 30
```

💾 Speichern und Gateway neu starten, falls nötig.

---

## 🛠️ Installation

```bash
git clone https://github.com/MariusQuabeck/FediCamp-Wetterstation.git
cd fedicamp-wetterstation
python3 -m venv wetter-venv
source wetter-venv/bin/activate
pip install flask
```

> Optional: Installiere `gunicorn` für produktiven Betrieb

---

## 🔃 Starten

```bash
python wetter.py
```

Die App läuft nun unter `http://localhost:8000/`

Sie leitet Besucher je nach Gerät automatisch auf `/desktop` oder `/mobile` weiter.  
Die Diagrammseite ist über `/charts` erreichbar.

---

## 📁 Dateien und Struktur

```txt
wetter.py              # Hauptserver (Flask)
wetterdaten.csv        # CSV-Datenbank mit Wetterwerten
debug_post.log         # Logfile für POST-Debugging
passkey.txt            # Enthält deinen geheimen Schlüssel
/static/               # Logos & Grafiken (Light/Dark-Modi)
```

---

## 🤝 Credits

- Erstellt für das [FediCamp 2025](https://fedi.camp)
- Entwickelt mit ❤️ von [@marius](https://social.nerdzoom.media/@marius)
- Mit freundlicher Unterstützung von [KABI.tk](https://kabi.tk)
