from flask import Flask, request, jsonify, render_template_string, abort, redirect
import csv
import os
from datetime import datetime, timedelta

app = Flask(__name__)
DATA_FILE = "wetterdaten.csv"
LOG_FILE = "debug_post.log"
PASSKEY_FILE = "passkey.txt"

# Versuch, den Passkey aus externer Datei zu laden
if os.path.exists(PASSKEY_FILE):
    with open(PASSKEY_FILE) as f:
        VALID_PASSKEY = f.read().strip()
else:
    VALID_PASSKEY = None
    print("⚠️  WARNUNG: Datei 'passkey.txt' fehlt. POST-Zugriff wird verweigert.")


def windrichtung_text(winddir):
    richtungen = [
        "Nord",
        "Nord-Ost",
        "Osten",
        "Süd-Osten",
        "Süden",
        "Süd-West",
        "Westen",
        "Nord-Westen",
    ]
    idx = round(((winddir % 360) / 45)) % 8
    return richtungen[idx]


@app.route("/", methods=["GET", "POST"])
def receive_data():
    if request.method == "POST":
        if VALID_PASSKEY is None:
            return "Serverfehler: Kein gültiger PASSKEY definiert.", 500

        passkey = request.form.get("PASSKEY")
        if passkey != VALID_PASSKEY:
            abort(403)

        # Logge rohe POST-Daten zur Fehleranalyse
        with open(LOG_FILE, "a") as log:
            log.write(f"{datetime.now().isoformat()} {request.form}\n")

        try:
            # Temperatur: wenn > 50, vermutlich Fahrenheit → umrechnen
            tempf_raw = float(request.form.get("tempf", 0))
            tempf = (tempf_raw - 32) * 5.0 / 9.0 if tempf_raw > 50 else tempf_raw

            # Luftdruck: wenn < 35, vermutlich inHg → umrechnen
            baromrelin_raw = float(request.form.get("baromrelin", 0))
            baromrelin = (
                baromrelin_raw * 33.8639 if baromrelin_raw < 35 else baromrelin_raw
            )

            data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tempf": tempf,
                "humidity": float(request.form.get("humidity", 0)),
                "baromrelin": baromrelin,
                "windspeedmph": float(request.form.get("windspeedmph", 0))
                * 1.60934,  # mph → km/h
                "winddir": float(request.form.get("winddir", 0)),
                "uv": float(request.form.get("uv", 0)),
                "solarradiation": float(request.form.get("solarradiation", 0)),
                "dailyrainin": float(request.form.get("dailyrainin", 0))
                * 25.4,  # inch → mm
                "hourlyrainin": float(request.form.get("hourlyrainin", 0)) * 25.4,
                "rainratein": float(request.form.get("rainratein", 0)) * 25.4,
            }

            file_exists = os.path.isfile(DATA_FILE)
            with open(DATA_FILE, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        except Exception as e:
            with open(LOG_FILE, "a") as log:
                log.write(f"Fehler beim Schreiben: {e}\n")
            abort(500)

        return "OK"
    else:
        # automatische Weiterleitung je nach Gerät
        ua = request.headers.get("User-Agent", "").lower()
        if any(keyword in ua for keyword in ["mobile", "android", "iphone", "ipad"]):
            return redirect("/mobile")
        else:
            return redirect("/desktop")


@app.route("/mobile")
def dashboard():
    return render_template_string(
        """
    <!DOCTYPE html>
    <html lang="de" data-theme="dark">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>🌤️ FediCamp-Wetter</title>
      <style>
        :root {
          color-scheme: dark;
        }

        body {
          font-family: sans-serif;
          margin: 0;
          padding: 1rem;
          background-color: var(--bg);
          color: var(--text);
          transition: background 0.3s, color 0.3s;
        }

        .dark {
          --bg: #121212;
          --card: #1e1e1e;
          --text: #ffffff;
          --shadow: rgba(0, 0, 0, 0.5);
        }

        .light {
          --bg: #f5f5f5;
          --card: #ffffff;
          --text: #000000;
          --shadow: rgba(0, 0, 0, 0.1);
        }

        .header {
          text-align: center;
          margin-bottom: 1.5rem;
        }

        .logo {
          max-width: 200px;
          width: 100%;
          height: auto;
          display: block;
          margin: 0 auto 1rem auto;
        }

        h1 {
          text-align: center;
          margin-bottom: 1.5rem;
          font-size: 2rem;
        }

        .grid {
          display: grid;
          gap: 1rem;
          justify-content: center;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          max-width: 900px;
          margin: 0 auto;
        }

        .card {
          background: var(--card);
          padding: 1rem;
          border-radius: 1rem;
          box-shadow: 0 4px 10px var(--shadow);
          text-align: center;
        }

        .label {
          font-size: 1rem;
          opacity: 0.8;
          margin-bottom: 0.3rem;
        }

        .value {
          font-size: 1.6rem;
          font-weight: bold;
        }

        .footer {
          text-align: center;
          margin-top: 2rem;
          font-size: 0.9rem;
          opacity: 0.7;
        }

        .toggle-wrapper {
          text-align: center;
          margin-top: 1rem;
        }

        .toggle {
          display: inline-block;
          padding: 0.5rem 1rem;
          border: 1px solid var(--text);
          border-radius: 0.5rem;
          background: transparent;
          color: var(--text);
          cursor: pointer;
        }

        img.logo-tile {
          max-width: 100%;
          height: auto;
          border-radius: 0.5rem;
        }
.toggle,
.toggle:link,
.toggle:visited {
  display: inline-block;
  padding: 0.6rem 1.2rem;
  border: 1px solid var(--text);
  border-radius: 0.5rem;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 1rem;
  text-decoration: none;
  text-align: center;
  font-family: inherit;
  line-height: 1.2;
}

      </style>
    </head>
    <body>
      <div class="header">
        <img src="/static/2025_black_bg.svg" alt="Logo" class="logo" id="logo">
        <h1>🌤️ FediCamp-Wetter</h1>
      </div>

      <div class="grid">
        <div class="card"><div class="label">🌡️ Temperatur</div><div class="value" id="temp">--</div></div>
        <div class="card"><div class="label">💧 Luftfeuchtigkeit</div><div class="value" id="hum">--</div></div>
        <div class="card"><div class="label">📈 Luftdruck</div><div class="value" id="press">--</div></div>
        <div class="card"><div class="label">💨 Wind</div><div class="value" id="wind">--</div></div>
        <div class="card"><div class="label">🧭 Windrichtung</div><div class="value" id="winddir">--</div></div>
        <div class="card"><div class="label">🌞 Sonne</div><div class="value" id="solar">--</div></div>
        <div class="card"><div class="label">🔆 UV-Index</div><div class="value" id="uv">--</div></div>
        <div class="card"><div class="label">🌧️ Regenrate</div><div class="value" id="rainrate">--</div></div>
        <div class="card"><div class="label">🌂 Stundenregen</div><div class="value" id="rainhour">--</div></div>
        <div class="card"><div class="label">🌧️ Tagesregen</div><div class="value" id="rainday">--</div></div>

        <div class="card">
          <div class="label"></div>
          <a href="https://social.nerdzoom.media/@marius" target="_blank" rel="noopener">
            <img id="nerdzoom-logo" class="logo-tile" src="/static/nerdzoommedialight.png" alt="NerdZoom Media">
          </a>
        </div>

        <div class="card">
          <div class="label"></div>
          <a href="https://kabi.tk/" target="_blank" rel="noopener">
            <img class="logo-tile" src="/static/kabitk.png" alt="KABI.tk">
          </a>
        </div>
      </div>

<div class="toggle-wrapper">
  <button class="toggle" onclick="toggleTheme()">🌓 Modus wechseln</button>
  <a href="/charts" class="toggle" style="margin-left: 1rem; text-decoration: none;">📊 Diagramme</a>
</div>




      <script>
        function toggleTheme() {
          const html = document.documentElement;
          const current = html.getAttribute("data-theme") || "dark";
          const newTheme = current === "dark" ? "light" : "dark";
          html.setAttribute("data-theme", newTheme);
          html.classList.remove(current);
          html.classList.add(newTheme);
          localStorage.setItem("theme", newTheme);
          updateLogo(newTheme);
        }

        (function initTheme() {
          const saved = localStorage.getItem("theme");
          const defaultTheme = saved === "light" || saved === "dark" ? saved : "dark";
          document.documentElement.setAttribute("data-theme", defaultTheme);
          document.documentElement.classList.add(defaultTheme);
          updateLogo(defaultTheme);
        })();

        function updateLogo(theme) {
          const mainLogo = document.getElementById("logo");
          const nerdzoomLogo = document.getElementById("nerdzoom-logo");

          if (mainLogo) {
            mainLogo.src = theme === "dark"
              ? "/static/2025_black_bg.svg"
              : "/static/2025_white_bg.svg";
          }

          if (nerdzoomLogo) {
            nerdzoomLogo.src = theme === "dark"
              ? "/static/nerdzoommediadark.png"
              : "/static/nerdzoommedialight.png";
          }
        }
function getWindDirectionLabel(degree) {
  const directions = [
    "Nord", "Nord-Ost", "Osten", "Süd-Ost",
    "Süd", "Süd-West", "West", "Nord-West"
  ];
  const index = Math.round(degree / 45) % 8;
  return directions[index];
}

        async function updateData() {
          const res = await fetch("/api/data?range=1h");
          const data = await res.json();
          const last = data.timestamps.at(-1) || "--";

          document.getElementById("temp").textContent = data.tempf.at(-1)?.toFixed(1) + " °C" || "--";
          document.getElementById("hum").textContent = data.humidity.at(-1)?.toFixed(0) + " %" || "--";
          document.getElementById("press").textContent = data.baromrelin.at(-1)?.toFixed(2) + " hPa" || "--";
          document.getElementById("wind").textContent = data.windspeedmph.at(-1)?.toFixed(2) + " km/h" || "--";
          const winddirVal = data.winddir.at(-1);
          const winddirText = winddirVal != null
            ? Math.round(winddirVal) + "° " + getWindDirectionLabel(winddirVal)
            : "--";
          document.getElementById("winddir").textContent = winddirText;
          document.getElementById("solar").textContent = data.solarradiation.at(-1)?.toFixed(1) + " W/m²" || "--";
          document.getElementById("uv").textContent = data.uv.at(-1) || "--";
          document.getElementById("rainrate").textContent = data.rainratein.at(-1)?.toFixed(2) + " mm/h" || "--";
          document.getElementById("rainhour").textContent = data.hourlyrainin.at(-1)?.toFixed(2) + " mm" || "--";
          document.getElementById("rainday").textContent = data.dailyrainin.at(-1)?.toFixed(2) + " mm" || "--";
          document.getElementById("last").textContent = "Letzte Aktualisierung: " + last;
        }

        updateData();
        setInterval(updateData, 30000);
      </script>
    </body>
    </html>
    """
    )


@app.route("/desktop")
def desktop():
    return render_template_string(
        """
    <!DOCTYPE html>
    <html lang="de" data-theme="dark">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>🌤️ FediCamp-Wetter</title>
      <style>
        :root {
          color-scheme: dark;
        }

        body {
          font-family: sans-serif;
          margin: 0;
          padding: 2rem;
          background-color: var(--bg);
          color: var(--text);
          transition: background 0.3s, color 0.3s;
        }

        .dark {
          --bg: #121212;
          --card: #1e1e1e;
          --text: #ffffff;
          --shadow: rgba(0, 0, 0, 0.5);
        }

        .light {
          --bg: #f5f5f5;
          --card: #ffffff;
          --text: #000000;
          --shadow: rgba(0, 0, 0, 0.1);
        }

        .header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .logo {
          max-width: 300px;
          width: 100%;
          height: auto;
          display: block;
          margin: 0 auto 1rem auto;
        }

        h1 {
          text-align: center;
          margin-bottom: 2rem;
          font-size: 2.5rem;
        }

        .grid {
          display: grid;
          gap: 2rem;
          justify-content: center;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          max-width: 1200px;
          margin: 0 auto;
        }

        .card {
          background: var(--card);
          padding: 2rem;
          border-radius: 1rem;
          box-shadow: 0 6px 16px var(--shadow);
          text-align: center;
        }

        .label {
          font-size: 1.1rem;
          opacity: 0.8;
          margin-bottom: 0.5rem;
        }

        .value {
          font-size: 2.2rem;
          font-weight: bold;
        }

        .footer {
          text-align: center;
          margin-top: 3rem;
          font-size: 1rem;
          opacity: 0.7;
        }

        .toggle-wrapper {
          text-align: center;
          margin-top: 1rem;
        }

        .toggle {
          display: inline-block;
          padding: 0.6rem 1.2rem;
          border: 1px solid var(--text);
          border-radius: 0.5rem;
          background: transparent;
          color: var(--text);
          cursor: pointer;
          font-size: 1rem;
        }
.toggle,
.toggle:link,
.toggle:visited {
  display: inline-block;
  padding: 0.6rem 1.2rem;
  border: 1px solid var(--text);
  border-radius: 0.5rem;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 1rem;
  text-decoration: none;
  text-align: center;
  font-family: inherit;
  line-height: 1.2;
}

      </style>
    </head>
    <body>
      <div class="header">
        <img src="/static/2025_black_bg.svg" alt="Logo" class="logo" id="logo">
        <h1>🌤️ FediCamp-Wetter</h1>
      </div>

      <div class="grid">
        <div class="card"><div class="label">🌡️ Temperatur</div><div class="value" id="temp">--</div></div>
        <div class="card"><div class="label">💧 Luftfeuchtigkeit</div><div class="value" id="hum">--</div></div>
        <div class="card"><div class="label">📈 Luftdruck</div><div class="value" id="press">--</div></div>
        <div class="card"><div class="label">💨 Wind</div><div class="value" id="wind">--</div></div>
        <div class="card"><div class="label">🧭 Windrichtung</div><div class="value" id="winddir">--</div></div>
        <div class="card"><div class="label">🌞 Sonne</div><div class="value" id="solar">--</div></div>
        <div class="card"><div class="label">🔆 UV-Index</div><div class="value" id="uv">--</div></div>
        <div class="card"><div class="label">🌧️ Regenrate</div><div class="value" id="rainrate">--</div></div>
        <div class="card"><div class="label">🌂 Stundenregen</div><div class="value" id="rainhour">--</div></div>
        <div class="card"><div class="label">🌧️ Tagesregen</div><div class="value" id="rainday">--</div></div>

        <div class="card">
          <div class="label"></div>
          <a href="https://social.nerdzoom.media/@marius" target="_blank" rel="noopener">
            <img id="nerdzoom-logo" src="/static/nerdzoommediadark.png" alt="NerdZoom Media"
                 style="max-width: 100%; height: auto; border-radius: 0.5rem;">
          </a>
        </div>

        <div class="card">
          <div class="label"></div>
          <a href="https://kabi.tk/" target="_blank" rel="noopener">
            <img src="/static/kabitk.png" alt="KABI.tk"
                 style="max-width: 100%; height: auto; border-radius: 0.5rem;">
          </a>
        </div>
      </div>

      <div class="footer" id="last">Letzte Aktualisierung: --</div>
<div class="footer" id="error" style="color: red; display: none;"></div>
    <div class="toggle-wrapper">
  <button class="toggle" onclick="toggleTheme()">🌓 Modus wechseln</button>
  <a href="/charts" class="toggle" style="margin-left: 1rem; text-decoration: none;">📊 Diagramme</a>
</div>



      <script>
        function toggleTheme() {
          const html = document.documentElement;
          const current = html.getAttribute("data-theme") || "dark";
          const newTheme = current === "dark" ? "light" : "dark";
          html.setAttribute("data-theme", newTheme);
          html.classList.remove(current);
          html.classList.add(newTheme);
          localStorage.setItem("theme", newTheme);
          updateLogo(newTheme);
        }

        (function initTheme() {
          const saved = localStorage.getItem("theme");
          const defaultTheme = saved === "light" || saved === "dark" ? saved : "dark";
          document.documentElement.setAttribute("data-theme", defaultTheme);
          document.documentElement.classList.add(defaultTheme);
          updateLogo(defaultTheme);
        })();

        function updateLogo(theme) {
          const logo = document.getElementById("logo");
          const nerdzoomLogo = document.getElementById("nerdzoom-logo");

          if (logo) {
            logo.src = theme === "dark"
              ? "/static/2025_black_bg.svg"
              : "/static/2025_white_bg.svg";
          }

          if (nerdzoomLogo) {
            nerdzoomLogo.src = theme === "dark"
              ? "/static/nerdzoommediadark.png"
              : "/static/nerdzoommedialight.png";
          }
        }
function getWindDirectionLabel(degree) {
  const directions = [
    "Nord", "Nord-Ost", "Osten", "Süd-Ost",
    "Süd", "Süd-West", "West", "Nord-West"
  ];
  const index = Math.round(degree / 45) % 8;
  return directions[index];
}

async function updateData() {
  const errorElem = document.getElementById("error");
  try {
    const res = await fetch("/api/data?range=1h");
    if (!res.ok) throw new Error("HTTP " + res.status);

    const data = await res.json();
    const last = data.timestamps.at(-1) || "--";

    document.getElementById("temp").textContent = data.tempf.at(-1)?.toFixed(1) + " °C" || "--";
    document.getElementById("hum").textContent = data.humidity.at(-1)?.toFixed(0) + " %" || "--";
    document.getElementById("press").textContent = data.baromrelin.at(-1)?.toFixed(2) + " hPa" || "--";
    document.getElementById("wind").textContent = data.windspeedmph.at(-1)?.toFixed(2) + " km/h" || "--";

    const winddirVal = data.winddir.at(-1);
    const winddirText = winddirVal != null
      ? Math.round(winddirVal) + "° " + getWindDirectionLabel(winddirVal)
      : "--";
    document.getElementById("winddir").textContent = winddirText;

    document.getElementById("solar").textContent = data.solarradiation.at(-1)?.toFixed(1) + " W/m²" || "--";
    document.getElementById("uv").textContent = data.uv.at(-1) || "--";
    document.getElementById("rainrate").textContent = data.rainratein.at(-1)?.toFixed(2) + " mm/h" || "--";
    document.getElementById("rainhour").textContent = data.hourlyrainin.at(-1)?.toFixed(2) + " mm" || "--";
    document.getElementById("rainday").textContent = data.dailyrainin.at(-1)?.toFixed(2) + " mm" || "--";
    document.getElementById("last").textContent = "Letzte Aktualisierung: " + last;

    // Fehleranzeige ausblenden
    if (errorElem) errorElem.style.display = "none";

  } catch (err) {
    console.error("Fehler beim Laden der Daten:", err);
    if (errorElem) {
      errorElem.textContent = "⚠️ Fehler beim Abrufen der Daten. Neuer Versuch in 30 Sekunden …";
      errorElem.style.display = "block";
    }
  }
}

        updateData();
        setInterval(updateData, 30000);
      </script>
    </body>
    </html>
    """
    )


@app.route("/charts")
def charts():
    return render_template_string(
        """
<!DOCTYPE html>
<html lang="de" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <title>Live-Wetterdiagramme</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      color-scheme: dark;
    }

    .dark {
      --bg: #121212;
      --text: #ffffff;
      --card: #1e1e1e;
      --grid: rgba(255, 255, 255, 0.2);
    }

    .light {
      --bg: #ffffff;
      --text: #000000;
      --card: #f5f5f5;
      --grid: rgba(0, 0, 0, 0.1);
    }

    body {
      font-family: sans-serif;
      margin: 0;
      padding: 2rem;
      background: var(--bg);
      color: var(--text);
      transition: background 0.3s, color 0.3s;
    }

    h1 {
      text-align: center;
      margin-bottom: 1rem;
    }

    .container {
      max-width: 1000px;
      margin: auto;
    }

    canvas {
      max-width: 100%;
      margin-bottom: 40px;
    }

    .controls {
      text-align: center;
      margin-bottom: 1rem;
    }

    select, .toggle {
      padding: 0.5rem 1rem;
      font-size: 1rem;
      margin: 0 0.5rem;
      border-radius: 0.5rem;
      border: 1px solid var(--text);
      background: transparent;
      color: var(--text);
      cursor: pointer;
    }
  </style>
</head>

<body>
  <div class="container">
    <h1>📊 Live-Wetterdiagramme</h1>

    <div class="controls">
<button class="toggle" onclick="history.back()">🔙 Zurück</button>
      <label for="range">Zeitraum:</label>
      <select id="range" onchange="loadAllCharts()">
        <option value="1h">Letzte Stunde</option>
        <option value="24h" selected>Letzter Tag</option>
        <option value="7d">Letzte Woche</option>
      </select>

      <button class="toggle" onclick="toggleTheme()">🌓 Modus wechseln</button>
    </div>

    <p style="text-align:center"><b>Aktualisiert:</b> <span id="lastUpdate">–</span></p>

    <canvas id="tempf"></canvas>
    <canvas id="humidity"></canvas>
    <canvas id="baromrelin"></canvas>
    <canvas id="windspeedmph"></canvas>
    <canvas id="uv"></canvas>
    <canvas id="solarradiation"></canvas>
    <canvas id="rainratein"></canvas>
  </div>

  <script>
    const chartTypes = ["tempf", "humidity", "baromrelin", "windspeedmph", "uv", "solarradiation", "rainratein"];
    const chartLabels = {
      tempf: "Temperatur (°C)",
      humidity: "Luftfeuchtigkeit (%)",
      baromrelin: "Luftdruck (hPa)",
      windspeedmph: "Windgeschwindigkeit (km/h)",
      uv: "UV-Index",
      solarradiation: "Sonneneinstrahlung (W/m²)",
      rainratein: "Regenrate (mm/h)"
    };
    const chartColors = {
      tempf: "red",
      humidity: "blue",
      baromrelin: "orange",
      windspeedmph: "green",
      uv: "purple",
      solarradiation: "gold",
      rainratein: "gray"
    };

    let charts = {};

    function getThemeColors() {
      const theme = document.documentElement.getAttribute("data-theme") || "dark";
      const isDark = theme === "dark";
      return {
        text: getComputedStyle(document.body).getPropertyValue('--text').trim(),
        grid: getComputedStyle(document.body).getPropertyValue('--grid').trim(),
        background: getComputedStyle(document.body).getPropertyValue('--bg').trim(),
        dark: isDark
      };
    }

    async function draw(id, label, color) {
      const range = document.getElementById("range").value;
      const res = await fetch(`/api/data?range=${range}`);
      const data = await res.json();
      const themeColors = getThemeColors();

      const ctx = document.getElementById(id).getContext("2d");
      if (charts[id]) charts[id].destroy();

      charts[id] = new Chart(ctx, {
        type: "line",
        data: {
          labels: data.timestamps,
          datasets: [{
            label: label,
            data: data[id],
            borderColor: color,
            backgroundColor: themeColors.text + "33", // leicht transparent
            fill: false,
            tension: 0.3
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { labels: { color: themeColors.text } },
            tooltip: { mode: 'index', intersect: false }
          },
          interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
          },
          scales: {
            x: {
              ticks: { color: themeColors.text },
              grid: { color: themeColors.grid },
              title: { display: true, text: "Zeit", color: themeColors.text }
            },
            y: {
              ticks: { color: themeColors.text },
              grid: { color: themeColors.grid },
              title: { display: true, text: label, color: themeColors.text }
            }
          }
        }
      });
    }

    function loadAllCharts() {
      chartTypes.forEach(id => draw(id, chartLabels[id], chartColors[id]));
      document.getElementById("lastUpdate").textContent = new Date().toLocaleString("de-DE");
    }

    function toggleTheme() {
      const html = document.documentElement;
      const current = html.getAttribute("data-theme") || "dark";
      const newTheme = current === "dark" ? "light" : "dark";
      html.setAttribute("data-theme", newTheme);
      html.classList.remove(current);
      html.classList.add(newTheme);
      localStorage.setItem("theme", newTheme);
      loadAllCharts(); // neu rendern!
    }

    (function initTheme() {
      const saved = localStorage.getItem("theme");
      const defaultTheme = saved === "light" || saved === "dark" ? saved : "dark";
      document.documentElement.setAttribute("data-theme", defaultTheme);
      document.documentElement.classList.add(defaultTheme);
    })();

    setInterval(loadAllCharts, 60000);
    window.onload = loadAllCharts;
  </script>
</body>
</html>

    """
    )


@app.route("/api/data")
def api_data():
    range = request.args.get("range", "24h")
    cutoff = datetime.now()
    if range == "1h":
        cutoff -= timedelta(hours=1)
    elif range == "24h":
        cutoff -= timedelta(days=1)
    elif range == "7d":
        cutoff -= timedelta(days=7)

    result = {
        "timestamps": [],
        "tempf": [],
        "humidity": [],
        "baromrelin": [],
        "windspeedmph": [],
        "winddir": [],
        "uv": [],
        "solarradiation": [],
        "dailyrainin": [],
        "hourlyrainin": [],
        "rainratein": [],
    }

    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if ts >= cutoff:
                        result["timestamps"].append(ts.strftime("%d.%m %H:%M"))
                        for key in result:
                            if key != "timestamps":
                                result[key].append(float(row.get(key, 0)))
                except:
                    continue

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
