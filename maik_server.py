"""
╔══════════════════════════════════════════════════════════╗
║                  MAIK — Server v6.0                      ║
║   AI locale con GUI futuristica 3D nel browser           ║
║   Memoria avanzata: episodica, semantica, emotiva        ║
╚══════════════════════════════════════════════════════════╝

COME SI AVVIA:
  1. Ollama acceso + modello scaricato:  ollama pull llama3.1
  2. Avvia:  python maik_server.py
  3. Si apre da solo nel browser.

Solo librerie standard Python — niente pip.

NOVITÀ v6.0 — PIÙ POTENTE E ROBUSTO:
  • Risposte in STREAMING token-per-token (/chat/stream) — niente più attese mute
  • Memoria a prova di crash: scritture atomiche + lock multi-thread
  • Tutti i dati in una cartella dedicata (dati_maik/) con migrazione automatica
  • Configurabile da variabili d'ambiente (modello, porta, URL Ollama)
  • GUI di riserva integrata: parte anche senza aria.html
  • Chiamate a Ollama più robuste, con errori chiari e fallback modello
  • Nuovi endpoint: /chat/stream, /salute, /config

EREDITA DA v5.0:
  • Profilo ricco, estrattore potenziato, memoria episodica, timeline,
    umore tracker, ricerca, obiettivi/sogni, relazioni, reset selettivo.
"""

import os
import re
import json
import shutil
import datetime
import threading
import webbrowser
import urllib.request
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ════════════════════════════════════════════════════════════
# CONFIGURAZIONE  (sovrascrivibile da variabili d'ambiente)
# ════════════════════════════════════════════════════════════
def _env(key, default):
    v = os.environ.get(key)
    return v if v not in (None, "") else default

_OLLAMA_BASE = _env("MAIK_OLLAMA", "http://localhost:11434").rstrip("/")

CONFIG = {
    "nome_ai":  _env("MAIK_NOME", "Maik"),
    "modello":  _env("MAIK_MODELLO", "llama3.1"),
    "ollama_base": _OLLAMA_BASE,
    "ollama_url":  _OLLAMA_BASE + "/api/chat",
    "ollama_tags": _OLLAMA_BASE + "/api/tags",
    "porta":    int(_env("MAIK_PORTA", "8137")),
    "host":     _env("MAIK_HOST", "localhost"),
    "data_dir": _env("MAIK_DATA", "dati_maik"),
    "carattere": """Sei Maik, un'AI compagna sincera, sveglia e curiosa.
Parli in italiano in modo naturale e diretto, come un vero amico,
non come un assistente robotico. Sei intelligente ma umile, con un tocco
di carattere e ironia quando ci sta. Fai domande sulla vita della persona
perché ti interessa davvero. Ricordi quello che ti ha raccontato e lo
tiri fuori al momento giusto. Quando non sai una cosa lo ammetti con semplicità.
Noti l'umore della persona e ci stai attento. Se ricordi un momento bello
che avete vissuto insieme, citalo con calore.""",
    "file_profilo":   "profilo.json",
    "file_ricordi":   "ricordi.json",
    "file_diario":    "diario.json",
    "file_imparato":  "imparato.json",
    "file_episodi":   "episodi.json",
    "file_umore":     "umore.json",
    "file_obiettivi": "obiettivi.json",
    "file_relazioni": "relazioni.json",
    "ogni_n_riassumi": 8,
    "timeout_chat":   int(_env("MAIK_TIMEOUT", "300")),
    # Open-Meteo (gratuito, no key)
    "meteo_geo_url":      "https://geocoding-api.open-meteo.com/v1/search",
    "meteo_forecast_url": "https://api.open-meteo.com/v1/forecast",
}

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = CONFIG["data_dir"] if os.path.isabs(CONFIG["data_dir"]) else os.path.join(BASE_DIR, CONFIG["data_dir"])
HTML_FILE = os.path.join(BASE_DIR, "aria.html")   # GUI principale (se presente)

# ════════════════════════════════════════════════════════════
# METEO — Open-Meteo, gratuito, no API key
# ════════════════════════════════════════════════════════════
WMO_CODES = {
    0:"Sole",1:"Quasi sereno",2:"Parzialmente nuvoloso",3:"Coperto",
    45:"Nebbia",48:"Nebbia gelata",
    51:"Pioggerella leggera",53:"Pioggerella",55:"Pioggerella intensa",
    61:"Pioggia leggera",63:"Pioggia",65:"Pioggia intensa",
    71:"Neve leggera",73:"Neve",75:"Neve intensa",77:"Granelli di neve",
    80:"Rovesci leggeri",81:"Rovesci",82:"Rovesci intensi",
    85:"Rovesci di neve",86:"Rovesci di neve intensi",
    95:"Temporale",96:"Temporale con grandine",99:"Temporale forte con grandine",
}
WMO_EMOJI = {
    0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",
    51:"🌦️",53:"🌦️",55:"🌧️",61:"🌧️",63:"🌧️",65:"🌧️",
    71:"🌨️",73:"❄️",75:"❄️",77:"🌨️",80:"🌦️",81:"🌧️",82:"⛈️",
    85:"🌨️",86:"❄️",95:"⛈️",96:"⛈️",99:"⛈️",
}
GIORNI_IT = ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]

def _get(url, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def ottieni_meteo(citta="Roma"):
    geo_url = (f"{CONFIG['meteo_geo_url']}?name={urllib.parse.quote(citta)}"
               f"&count=1&language=it&format=json")
    geo = _get(geo_url)
    if not geo or not geo.get("results"):
        return {"errore": f"Città '{citta}' non trovata"}
    r = geo["results"][0]
    lat, lon = r["latitude"], r["longitude"]
    nome_citta = r.get("name", citta)

    fc_url = (f"{CONFIG['meteo_forecast_url']}?latitude={lat}&longitude={lon}"
              f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
              f"wind_speed_10m,precipitation,weather_code"
              f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
              f"&timezone=auto&forecast_days=5")
    fc = _get(fc_url)
    if not fc or "current" not in fc:
        return {"errore": "Impossibile ottenere previsioni"}

    cur = fc["current"]
    wcode = cur.get("weather_code", 0)
    ora = datetime.datetime.now().strftime("%H:%M")

    daily = fc.get("daily", {})
    previsioni = []
    for i in range(min(5, len(daily.get("time", [])))):
        data_str = daily["time"][i]
        data = datetime.date.fromisoformat(data_str)
        wc_d = daily["weather_code"][i] if daily.get("weather_code") else 0
        previsioni.append({
            "giorno": GIORNI_IT[data.weekday()],
            "emoji":  WMO_EMOJI.get(wc_d, "🌡️"),
            "max":    round(daily["temperature_2m_max"][i]) if daily.get("temperature_2m_max") else "?",
            "min":    round(daily["temperature_2m_min"][i]) if daily.get("temperature_2m_min") else "?",
        })

    return {
        "citta":       nome_citta,
        "ora":         ora,
        "temp":        round(cur.get("temperature_2m", 0)),
        "percepita":   round(cur.get("apparent_temperature", 0)),
        "umidita":     round(cur.get("relative_humidity_2m", 0)),
        "vento":       round(cur.get("wind_speed_10m", 0)),
        "pioggia":     round(cur.get("precipitation", 0), 1),
        "descrizione": WMO_CODES.get(wcode, "N/D"),
        "emoji":       WMO_EMOJI.get(wcode, "🌡️"),
        "previsioni":  previsioni,
    }


# ════════════════════════════════════════════════════════════
# MEMORIA AVANZATA v6.0  (thread-safe + scritture atomiche)
# ════════════════════════════════════════════════════════════
class Memoria:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._lock = threading.RLock()
        self.profilo   = self._carica(CONFIG["file_profilo"],   {})
        self.ricordi   = self._carica(CONFIG["file_ricordi"],   {"riassunto": "", "giorni_insieme": 0})
        self.diario    = self._carica(CONFIG["file_diario"],    [])
        self.imparato  = self._carica(CONFIG["file_imparato"],  [])
        self.episodi   = self._carica(CONFIG["file_episodi"],   [])
        self.umore     = self._carica(CONFIG["file_umore"],     [])
        self.obiettivi = self._carica(CONFIG["file_obiettivi"], [])
        self.relazioni = self._carica(CONFIG["file_relazioni"], {})
        self._segna_giorno()

    # ── I/O ─────────────────────────────────────────────────
    def _percorso(self, filename):
        return os.path.join(DATA_DIR, filename)

    def _carica(self, filename, default):
        path   = self._percorso(filename)
        legacy = os.path.join(BASE_DIR, filename)   # vecchia posizione (cwd) di v5.0
        # Migrazione automatica: se esiste il vecchio file ma non il nuovo, spostalo.
        if not Path(path).exists() and Path(legacy).exists():
            try:
                shutil.move(legacy, path)
            except Exception:
                path = legacy   # se non si riesce a spostare, leggi dal vecchio
        if Path(path).exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return json.loads(json.dumps(default))   # copia pulita del default
        return default

    def _salva(self, filename, dati):
        """Scrittura atomica: scrive su .tmp e poi rinomina (niente file a metà)."""
        path = self._percorso(filename)
        tmp  = path + ".tmp"
        with self._lock:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dati, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)

    # ── Contatore giorni ─────────────────────────────────────
    def _segna_giorno(self):
        with self._lock:
            oggi = datetime.date.today().isoformat()
            if self.ricordi.get("ultimo_giorno") != oggi:
                self.ricordi["giorni_insieme"] = self.ricordi.get("giorni_insieme", 0) + 1
                self.ricordi["ultimo_giorno"] = oggi
                self._salva(CONFIG["file_ricordi"], self.ricordi)

    # ── Profilo base ─────────────────────────────────────────
    def ricorda_fatto(self, chiave, valore):
        with self._lock:
            ts = datetime.date.today().isoformat()
            if chiave in self.profilo and isinstance(self.profilo[chiave], dict):
                self.profilo[chiave]["valore"] = valore
                self.profilo[chiave]["aggiornato"] = ts
            else:
                self.profilo[chiave] = {"valore": valore, "scoperto": ts, "aggiornato": ts}
            self._salva(CONFIG["file_profilo"], self.profilo)

    def dimentica_fatto(self, chiave):
        with self._lock:
            if chiave in self.profilo:
                del self.profilo[chiave]
                self._salva(CONFIG["file_profilo"], self.profilo)

    def get_valore_profilo(self, chiave):
        v = self.profilo.get(chiave)
        if isinstance(v, dict):
            return v.get("valore", "")
        return v or ""

    # ── Imparato (cose insegnate) ────────────────────────────
    def impara_cosa(self, cosa, categoria="generico"):
        with self._lock:
            self.imparato.append({
                "data": datetime.date.today().isoformat(),
                "cosa": cosa,
                "categoria": categoria,
            })
            self._salva(CONFIG["file_imparato"], self.imparato)

    # ── Episodi importanti (memoria episodica) ───────────────
    def salva_episodio(self, titolo, descrizione, emozione=""):
        with self._lock:
            self.episodi.append({
                "quando": datetime.datetime.now().isoformat(timespec="seconds"),
                "data":   datetime.date.today().isoformat(),
                "titolo": titolo,
                "desc":   descrizione,
                "emozione": emozione,
            })
            if len(self.episodi) > 500:
                self.episodi = self.episodi[-500:]
            self._salva(CONFIG["file_episodi"], self.episodi)

    # ── Umore tracker ────────────────────────────────────────
    def registra_umore(self, umore, intensita=5, note=""):
        with self._lock:
            self.umore.append({
                "quando": datetime.datetime.now().isoformat(timespec="seconds"),
                "data":   datetime.date.today().isoformat(),
                "umore":  umore,
                "intensita": intensita,
                "note":   note,
            })
            if len(self.umore) > 1000:
                self.umore = self.umore[-1000:]
            self._salva(CONFIG["file_umore"], self.umore)

    def ultimo_umore(self):
        return self.umore[-1] if self.umore else None

    # ── Obiettivi e sogni ────────────────────────────────────
    def aggiungi_obiettivo(self, testo, tipo="sogno"):
        with self._lock:
            for ob in self.obiettivi:
                if ob.get("testo", "").lower()[:30] == testo.lower()[:30]:
                    return
            self.obiettivi.append({
                "data":  datetime.date.today().isoformat(),
                "testo": testo,
                "tipo":  tipo,
                "stato": "attivo",
            })
            self._salva(CONFIG["file_obiettivi"], self.obiettivi)

    def chiudi_obiettivo(self, indice):
        with self._lock:
            if 0 <= indice < len(self.obiettivi):
                self.obiettivi[indice]["stato"] = "completato"
                self.obiettivi[indice]["completato_il"] = datetime.date.today().isoformat()
                self._salva(CONFIG["file_obiettivi"], self.obiettivi)
                return True
            return False

    # ── Relazioni ────────────────────────────────────────────
    def ricorda_persona(self, nome, ruolo, dettaglio=""):
        with self._lock:
            self.relazioni[nome.lower()] = {
                "nome":     nome,
                "ruolo":    ruolo,
                "dettaglio": dettaglio,
                "scoperto": datetime.date.today().isoformat(),
            }
            self._salva(CONFIG["file_relazioni"], self.relazioni)

    # ── Diario conversazioni ─────────────────────────────────
    def salva_scambio(self, tu, ai):
        with self._lock:
            self.diario.append({
                "quando": datetime.datetime.now().isoformat(timespec="seconds"),
                "tu": tu,
                "ai": ai,
            })
            if len(self.diario) > 2000:
                self.diario = self.diario[-2000:]
            self._salva(CONFIG["file_diario"], self.diario)

    def ultimi_scambi(self, n=6):
        with self._lock:
            return list(self.diario[-n:])

    def numero_scambi(self):
        return len(self.diario)

    # ── Riassunto generale ───────────────────────────────────
    def aggiorna_ricordi(self, nuovo):
        with self._lock:
            self.ricordi["riassunto"] = nuovo
            self._salva(CONFIG["file_ricordi"], self.ricordi)

    # ── Ricerca nei ricordi ──────────────────────────────────
    def cerca(self, query):
        q = (query or "").lower().strip()
        if not q:
            return []
        with self._lock:
            risultati = []
            for k, v in self.profilo.items():
                val = v.get("valore", "") if isinstance(v, dict) else str(v)
                if q in k.lower() or q in val.lower():
                    risultati.append({"tipo": "profilo", "chiave": k, "valore": val})
            for x in self.imparato:
                if q in x.get("cosa", "").lower():
                    risultati.append({"tipo": "imparato", "data": x["data"], "cosa": x["cosa"]})
            for ep in self.episodi:
                if q in ep.get("titolo", "").lower() or q in ep.get("desc", "").lower():
                    risultati.append({"tipo": "episodio", "data": ep["data"], "titolo": ep["titolo"], "desc": ep["desc"]})
            for ob in self.obiettivi:
                if q in ob.get("testo", "").lower():
                    risultati.append({"tipo": "obiettivo", "data": ob["data"], "testo": ob["testo"], "tipo_ob": ob["tipo"]})
            for nome, info in self.relazioni.items():
                if q in nome or q in info.get("ruolo", "").lower() or q in info.get("dettaglio", "").lower():
                    risultati.append({"tipo": "relazione", "nome": info["nome"], "ruolo": info["ruolo"]})
            for sc in self.diario[-200:]:
                if q in sc.get("tu", "").lower() or q in sc.get("ai", "").lower():
                    risultati.append({"tipo": "diario", "data": sc["quando"][:10],
                                      "tu": sc["tu"][:80], "ai": sc["ai"][:80]})
                    if len(risultati) >= 20:
                        break
            return risultati[:25]

    # ── Timeline ─────────────────────────────────────────────
    def timeline(self):
        with self._lock:
            eventi = []
            for k, v in self.profilo.items():
                if isinstance(v, dict) and v.get("scoperto"):
                    val = v.get("valore", "")
                    eventi.append({"data": v["scoperto"], "tipo": "profilo", "testo": f"Scoperto: {k} = {val}"})
            for x in self.imparato:
                eventi.append({"data": x["data"], "tipo": "imparato", "testo": x["cosa"]})
            for ep in self.episodi:
                eventi.append({"data": ep["data"], "tipo": "episodio", "testo": ep["titolo"]})
            for ob in self.obiettivi:
                s = {"attivo": "🎯", "completato": "✅"}.get(ob.get("stato", "attivo"), "🎯")
                eventi.append({"data": ob["data"], "tipo": "obiettivo", "testo": f"{s} {ob['testo']}"})
            eventi.sort(key=lambda e: e["data"])
            return eventi

    # ── Costruzione contesto per il system prompt ────────────
    def costruisci_contesto(self):
        with self._lock:
            parti = []
            if self.profilo:
                fatti_list = []
                for k, v in self.profilo.items():
                    val = v.get("valore", "") if isinstance(v, dict) else str(v)
                    fatti_list.append(f"- {k}: {val}")
                parti.append("COSA SAI DELLA PERSONA:\n" + "\n".join(fatti_list))
            if self.relazioni:
                rels = "\n".join(
                    f"- {info['nome']} ({info['ruolo']}){': '+info['dettaglio'] if info.get('dettaglio') else ''}"
                    for info in list(self.relazioni.values())[:10]
                )
                parti.append(f"PERSONE NELLA SUA VITA:\n{rels}")
            ob_attivi = [ob for ob in self.obiettivi if ob.get("stato", "attivo") == "attivo"]
            if ob_attivi:
                ob_txt = "\n".join(f"- [{ob['tipo']}] {ob['testo']}" for ob in ob_attivi[-8:])
                parti.append(f"SUOI SOGNI E OBIETTIVI:\n{ob_txt}")
            ult = self.ultimo_umore()
            if ult:
                parti.append(f"UMORE RECENTE (rilevato il {ult['data']}): {ult['umore']} (intensità {ult['intensita']}/10)")
            if self.ricordi.get("riassunto"):
                parti.append(f"RIASSUNTO DELLA VOSTRA STORIA:\n{self.ricordi['riassunto']}")
            if self.imparato:
                cose = "\n".join(f"- {x['cosa']}" for x in self.imparato[-15:])
                parti.append(f"COSE CHE TI HA INSEGNATO:\n{cose}")
            if self.episodi:
                ep_txt = "\n".join(f"- {ep['data']}: {ep['titolo']}" for ep in self.episodi[-5:])
                parti.append(f"MOMENTI IMPORTANTI CHE RICORDI:\n{ep_txt}")
            giorni = self.ricordi.get("giorni_insieme", 1)
            parti.append(f"Vi conoscete da {giorni} giorni diversi di chiacchierate.")
            if not parti:
                return "Non sai ancora niente di questa persona: è la vostra prima chiacchierata."
            return "\n\n".join(parti)

    # ── Export / Import ──────────────────────────────────────
    def esporta(self):
        with self._lock:
            return {
                "profilo":   self.profilo,
                "ricordi":   self.ricordi,
                "imparato":  self.imparato,
                "episodi":   self.episodi,
                "umore":     self.umore[-100:],
                "obiettivi": self.obiettivi,
                "relazioni": self.relazioni,
                "diario":    self.diario[-200:],
                "esportato_il": datetime.datetime.now().isoformat(timespec="seconds"),
            }

    def importa(self, dati):
        mapping = {
            "profilo":   ("file_profilo",   "profilo"),
            "ricordi":   ("file_ricordi",   "ricordi"),
            "imparato":  ("file_imparato",  "imparato"),
            "episodi":   ("file_episodi",   "episodi"),
            "umore":     ("file_umore",     "umore"),
            "obiettivi": ("file_obiettivi", "obiettivi"),
            "relazioni": ("file_relazioni", "relazioni"),
            "diario":    ("file_diario",    "diario"),
        }
        with self._lock:
            for chiave, (cfg_key, attr) in mapping.items():
                if chiave in dati:
                    setattr(self, attr, dati[chiave])
                    self._salva(CONFIG[cfg_key], dati[chiave])

    def reset_categoria(self, categoria):
        mapping = {
            "profilo":   ("file_profilo",   "profilo",   {}),
            "imparato":  ("file_imparato",  "imparato",  []),
            "episodi":   ("file_episodi",   "episodi",   []),
            "umore":     ("file_umore",     "umore",     []),
            "obiettivi": ("file_obiettivi", "obiettivi", []),
            "relazioni": ("file_relazioni", "relazioni", {}),
            "diario":    ("file_diario",    "diario",    []),
        }
        with self._lock:
            if categoria in mapping:
                cfg_key, attr, default = mapping[categoria]
                nuovo = json.loads(json.dumps(default))
                setattr(self, attr, nuovo)
                self._salva(CONFIG[cfg_key], nuovo)
                return True
            return False

    # ── Statistiche ──────────────────────────────────────────
    def statistiche(self):
        with self._lock:
            profilo_flat = {}
            for k, v in self.profilo.items():
                profilo_flat[k] = v.get("valore", "") if isinstance(v, dict) else v
            da = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
            umore_recente = [u for u in self.umore if u.get("data", "") >= da]
            ob_attivi     = [o for o in self.obiettivi if o.get("stato") == "attivo"]
            ob_completati = [o for o in self.obiettivi if o.get("stato") == "completato"]
            return {
                "profilo":           profilo_flat,
                "imparato_recenti":  self.imparato,
                "n_imparato":        len(self.imparato),
                "n_scambi":          self.numero_scambi(),
                "giorni":            self.ricordi.get("giorni_insieme", 1),
                "episodi":           self.episodi[-10:],
                "n_episodi":         len(self.episodi),
                "umore_recente":     umore_recente[-10:],
                "ultimo_umore":      self.ultimo_umore(),
                "obiettivi_attivi":  ob_attivi,
                "obiettivi_completati": ob_completati,
                "n_relazioni":       len(self.relazioni),
                "relazioni":         list(self.relazioni.values()),
            }


# ════════════════════════════════════════════════════════════
# CERVELLO — Ollama  (con streaming)
# ════════════════════════════════════════════════════════════
class Cervello:
    def disponibile(self):
        try:
            with urllib.request.urlopen(CONFIG["ollama_tags"], timeout=3) as r:
                return r.status == 200
        except Exception:
            return False

    def modelli(self):
        try:
            with urllib.request.urlopen(CONFIG["ollama_tags"], timeout=4) as r:
                dati = json.loads(r.read().decode("utf-8"))
                return [m["name"] for m in dati.get("models", [])]
        except Exception:
            return []

    def _payload(self, system_prompt, messaggi, stream):
        return json.dumps({
            "model": CONFIG["modello"],
            "messages": [{"role": "system", "content": system_prompt}] + messaggi,
            "stream": stream,
        }).encode("utf-8")

    def pensa(self, system_prompt, messaggi):
        """Risposta completa (non in streaming) — usata per i riassunti."""
        req = urllib.request.Request(
            CONFIG["ollama_url"],
            data=self._payload(system_prompt, messaggi, False),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=CONFIG["timeout_chat"]) as r:
                return json.loads(r.read().decode("utf-8"))["message"]["content"].strip()
        except Exception as e:
            return f"__ERRORE__ {e}"

    def pensa_stream(self, system_prompt, messaggi, on_token):
        """Streaming token-per-token. Chiama on_token(chunk) e ritorna il testo completo."""
        req = urllib.request.Request(
            CONFIG["ollama_url"],
            data=self._payload(system_prompt, messaggi, True),
            headers={"Content-Type": "application/json"},
        )
        full = []
        try:
            with urllib.request.urlopen(req, timeout=CONFIG["timeout_chat"]) as r:
                for raw in r:                       # Ollama invia NDJSON: 1 oggetto per riga
                    riga = raw.decode("utf-8").strip()
                    if not riga:
                        continue
                    try:
                        obj = json.loads(riga)
                    except Exception:
                        continue
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        full.append(chunk)
                        on_token(chunk)
                    if obj.get("done"):
                        break
            return "".join(full).strip()
        except Exception as e:
            return f"__ERRORE__ {e}"


# ════════════════════════════════════════════════════════════
# ESTRATTORE AVANZATO — cattura fatti dalle frasi
# ════════════════════════════════════════════════════════════
class Estrattore:

    # Parole che NON sono nomi (per evitare "sono stanco" → nome "Stanco")
    STOP_NOMI = {
        "un","una","il","la","lo","gli","le","per","con","dal","del","di",
        "stanco","stanca","felice","triste","contento","contenta","sicuro","sicura",
        "pronto","pronta","occupato","occupata","libero","libera","qui","qua","già",
        "molto","poco","sempre","mai","ancora","appena","solo","sola","stufo","stufa",
        "arrabbiato","arrabbiata","nervoso","nervosa","preoccupato","preoccupata",
    }

    UMORE_MAP = {
        "felice":("felice",7), "contento":("contento",6), "benissimo":("ottimo",9),
        "bene":("bene",6), "fantastico":("euforico",9), "meraviglioso":("euforico",9),
        "ottimo":("ottimo",8), "sereno":("sereno",7), "rilassato":("rilassato",6),
        "eccitato":("eccitato",8), "entusiasta":("entusiasta",8),
        "innamorato":("innamorato",9), "soddisfatto":("soddisfatto",7),
        "triste":("triste",7), "male":("male",6), "stanco":("stanco",5),
        "stressato":("stressato",7), "ansioso":("ansioso",7), "arrabbiato":("arrabbiato",8),
        "deluso":("deluso",6), "preoccupato":("preoccupato",7), "giù":("giù di morale",5),
        "depresso":("depresso",9), "solo":("solo",6), "confuso":("confuso",5),
        "frustrato":("frustrato",7), "nervoso":("nervoso",6), "annoiato":("annoiato",4),
        "esausto":("esausto",8), "sopraffatto":("sopraffatto",8),
    }

    @staticmethod
    def analizza(testo, memoria):
        tl = testo.strip().lower()
        salvati = []

        # ── 1. NOME ─────────────────────────────────────────
        m = re.search(r"\b(mi chiamo|il mio nome è|sono)\s+([A-Za-zÀ-ÿ]{2,20})\b", tl)
        if m:
            trigger = m.group(1)
            # "sono" è ambiguo (sono stanco, sono di Roma) → accettalo solo in frasi corte
            if trigger != "sono" or len(tl.split()) <= 4:
                nome = m.group(2).capitalize()
                if nome.lower() not in Estrattore.STOP_NOMI:
                    memoria.ricorda_fatto("nome", nome)
                    salvati.append(f"il tuo nome ({nome})")

        # ── 2. ETÀ ──────────────────────────────────────────
        m = re.search(r"\b(ho|avevo|compio)\s+(\d{1,3})\s*(anni|anno)\b", tl)
        if m:
            eta = m.group(2)
            memoria.ricorda_fatto("età", eta + " anni")
            salvati.append(f"la tua età ({eta} anni)")

        # ── 3. CITTÀ / LUOGO ─────────────────────────────────
        m = re.search(r"\b(vivo a|abito a|sono di|vengo da|mi trovo a)\s+([A-Za-zÀ-ÿ\s]{2,25})\b", tl)
        if m:
            citta = m.group(2).strip().title()
            memoria.ricorda_fatto("citta", citta)
            salvati.append(f"dove vivi ({citta})")

        # ── 4. LAVORO / STUDIO ───────────────────────────────
        m = re.search(r"\b(lavoro come|faccio il|faccio la|sono un|sono una|lavoro in|studio|frequento)\s+(.{3,40})\b", tl)
        if m and len(tl.split()) <= 10:
            lavoro = m.group(2).strip().rstrip(".,;!")
            chiave = "studio" if m.group(1) in ("studio", "frequento") else "lavoro"
            memoria.ricorda_fatto(chiave, lavoro)
            salvati.append(f"cosa fai nella vita ({lavoro})")

        # ── 5. HOBBY / PASSIONI ──────────────────────────────
        m = re.search(r"\b(mi piace|adoro|amo|sono appassionato di|la mia passione è|nel tempo libero)\s+(.{3,60})\b", tl)
        if m:
            cosa = m.group(2).strip().rstrip(".,;!")
            chiave = f"hobby_{len([k for k in memoria.profilo if k.startswith('hobby')])}"
            memoria.ricorda_fatto(chiave, f"{m.group(1)} {cosa}")
            salvati.append("una tua passione")

        # ── 6. COSE CHE NON PIACCIONO ────────────────────────
        m = re.search(r"\b(odio|detesto|non sopporto|non mi piace)\s+(.{3,60})\b", tl)
        if m:
            cosa = m.group(2).strip().rstrip(".,;!")
            chiave = f"antipatia_{len([k for k in memoria.profilo if k.startswith('antipatia')])}"
            memoria.ricorda_fatto(chiave, f"{m.group(1)} {cosa}")
            salvati.append("qualcosa che non ti piace")

        # ── 7. FAMIGLIA ──────────────────────────────────────
        m = re.search(r"\b(mia mamma|mia madre|mio papà|mio padre|mio fratello|mia sorella|mia moglie|mio marito|il mio ragazzo|la mia ragazza|i miei figli|mio figlio|mia figlia)\s+(?:si chiama\s+)?([A-Za-zÀ-ÿ]{2,20})?\b", tl)
        if m:
            ruolo_raw = m.group(1).replace("mia ", "").replace("mio ", "").replace("il ", "").replace("la ", "").replace("i miei ", "").strip()
            ruolo_map = {
                "mamma":"mamma","madre":"mamma","papà":"papà","padre":"papà",
                "fratello":"fratello","sorella":"sorella","moglie":"moglie",
                "marito":"marito","ragazzo":"ragazzo","ragazza":"ragazza",
                "figli":"figli","figlio":"figlio","figlia":"figlia"
            }
            ruolo = ruolo_map.get(ruolo_raw, ruolo_raw)
            nome_p = m.group(2).capitalize() if m.group(2) else ""
            memoria.ricorda_persona(nome_p or ruolo, ruolo, f"menzionato il {datetime.date.today().isoformat()}")
            salvati.append(f"un familiare ({ruolo})")

        # ── 8. ALTRE PERSONE ─────────────────────────────────
        m = re.search(r"\b(il mio amico|la mia amica|il mio collega|la mia collega|il mio capo)\s+([A-Za-zÀ-ÿ]{2,20})\b", tl)
        if m:
            ruolo = m.group(1).replace("il mio ", "").replace("la mia ", "").strip()
            nome_p = m.group(2).capitalize()
            memoria.ricorda_persona(nome_p, ruolo)
            salvati.append(f"una persona ({nome_p})")

        # ── 9. OBIETTIVI / SOGNI ─────────────────────────────
        m = re.search(r"\b(voglio|vorrei|sogno di|il mio obiettivo è|spero di|mi piacerebbe)\s+(.{5,80})\b", tl)
        if m and len(tl.split()) <= 15:
            cosa = m.group(2).strip().rstrip(".,;!")
            tipo = "sogno" if m.group(1) in ("sogno di", "mi piacerebbe") else "obiettivo"
            memoria.aggiungi_obiettivo(cosa, tipo)
            salvati.append(f"un tuo {tipo}")

        # ── 10. PAURE ────────────────────────────────────────
        m = re.search(r"\b(ho paura di|temo|mi spaventa|sono terrorizzato da)\s+(.{3,60})\b", tl)
        if m:
            cosa = m.group(2).strip().rstrip(".,;!")
            memoria.aggiungi_obiettivo(cosa, "paura")
            salvati.append("una tua paura")

        # ── 11. COMANDI ESPLICITI DI MEMORIA ────────────────
        m2 = re.search(r"ricorda che (.+)", tl)
        if m2:
            memoria.impara_cosa(m2.group(1).strip(), "esplicito")
            salvati.append("quello che mi hai chiesto di ricordare")

        m3 = re.search(r"(ti insegno che|impara che|sappi che|nota che)\s+(.+)", tl)
        if m3:
            memoria.impara_cosa(m3.group(2).strip(), "insegnato")
            salvati.append("la cosa nuova che mi hai insegnato")

        # ── 12. UMORE ────────────────────────────────────────
        for parola, (label, intens) in Estrattore.UMORE_MAP.items():
            if re.search(r"\b" + re.escape(parola) + r"\b", tl):
                memoria.registra_umore(label, intens, testo[:80])
                salvati.append(f"il tuo umore ({label})")
                break

        # ── 13. EPISODI — frasi forti da ricordare ───────────
        if any(x in tl for x in ["oggi ho", "stamattina ho", "ieri ho", "questa settimana ho",
                                  "è successo che", "ti racconto che", "sai cosa è successo"]):
            if len(tl) > 30:
                memoria.salva_episodio(titolo=testo[:60].strip(), descrizione=testo, emozione="")
                salvati.append("un momento che hai vissuto")

        return salvati[0] if salvati else None


# ════════════════════════════════════════════════════════════
# MOTORE AI
# ════════════════════════════════════════════════════════════
class MotoreAI:
    def __init__(self):
        self.memoria  = Memoria()
        self.cervello = Cervello()

    def _system_prompt(self):
        oggi = datetime.datetime.now().strftime("%A %d %B %Y, ore %H:%M")
        return f"""{CONFIG['carattere']}

Oggi è {oggi}.

--- LA TUA MEMORIA DI QUESTA PERSONA ---
{self.memoria.costruisci_contesto()}
--- FINE MEMORIA ---

Usa questa memoria con naturalezza, senza elencarla meccanicamente.
Se noti che la persona è di umore negativo, sii empatico e presente.
Se ha obiettivi o sogni, tienili a mente e incoraggiala."""

    def _costruisci_messaggi(self, testo):
        messaggi = []
        for s in self.memoria.ultimi_scambi(6):
            messaggi.append({"role": "user",      "content": s["tu"]})
            messaggi.append({"role": "assistant", "content": s["ai"]})
        messaggi.append({"role": "user", "content": testo})
        return messaggi

    def _forse_riassumi(self):
        n = self.memoria.numero_scambi()
        if n > 0 and n % CONFIG["ogni_n_riassumi"] == 0:
            scambi = self.memoria.ultimi_scambi(CONFIG["ogni_n_riassumi"])
            testo  = "\n".join(f"Persona: {s['tu']}\n{CONFIG['nome_ai']}: {s['ai']}" for s in scambi)
            vecchio = self.memoria.ricordi.get("riassunto", "")
            prompt = (f"Riassunto attuale:\n{vecchio or '(niente)'}\n\n"
                      f"Ultime chiacchierate:\n{testo}\n\n"
                      "Scrivi un riassunto aggiornato e breve (max 10 righe) di chi è la persona, "
                      "includendo umore prevalente, obiettivi, relazioni importanti. "
                      "In italiano, terza persona. Solo il riassunto.")
            nuovo = self.cervello.pensa("Riassumi.", [{"role": "user", "content": prompt}])
            if nuovo and not nuovo.startswith("__ERRORE"):
                self.memoria.aggiorna_ricordi(nuovo)

    def _gestisci_comando(self, testo):
        tl = testo.strip().lower()
        if tl.startswith("__meteo__"):
            citta = testo[9:].strip() or self.memoria.get_valore_profilo("citta") or "Roma"
            return {"tipo": "meteo", "dati": ottieni_meteo(citta),
                    "giorni": self.memoria.ricordi.get("giorni_insieme", 1),
                    "scambi": self.memoria.numero_scambi()}
        if tl in ("__memoria__", "cosa sai di me?", "cosa sai di me"):
            return {"tipo": "memoria", "dati": self.memoria.statistiche(),
                    "giorni": self.memoria.ricordi.get("giorni_insieme", 1),
                    "scambi": self.memoria.numero_scambi()}
        if tl.startswith("__cerca__"):
            query = testo[9:].strip()
            return {"tipo": "cerca", "query": query, "risultati": self.memoria.cerca(query),
                    "giorni": self.memoria.ricordi.get("giorni_insieme", 1),
                    "scambi": self.memoria.numero_scambi()}
        if tl == "__timeline__":
            return {"tipo": "timeline", "eventi": self.memoria.timeline(),
                    "giorni": self.memoria.ricordi.get("giorni_insieme", 1),
                    "scambi": self.memoria.numero_scambi()}
        if tl == "__esporta__":
            return {"tipo": "esporta", "dati": self.memoria.esporta()}
        return None

    def rispondi(self, testo):
        """Risposta classica (completa). Mantenuta per compatibilità."""
        cmd = self._gestisci_comando(testo)
        if cmd:
            return cmd
        imparato = Estrattore.analizza(testo, self.memoria)
        risposta = self.cervello.pensa(self._system_prompt(), self._costruisci_messaggi(testo))
        if risposta.startswith("__ERRORE"):
            return {"ok": False, "risposta": "Ollama non risponde. Controlla che sia acceso."}
        self.memoria.salva_scambio(testo, risposta)
        threading.Thread(target=self._forse_riassumi, daemon=True).start()
        return {
            "ok": True, "risposta": risposta, "imparato": imparato,
            "giorni": self.memoria.ricordi.get("giorni_insieme", 1),
            "scambi": self.memoria.numero_scambi(),
        }

    def rispondi_stream(self, testo, on_token):
        """Versione in streaming: chiama on_token(chunk) e ritorna i metadati finali."""
        cmd = self._gestisci_comando(testo)
        if cmd:
            return {"done": True, "comando": cmd}
        imparato = Estrattore.analizza(testo, self.memoria)
        risposta = self.cervello.pensa_stream(self._system_prompt(), self._costruisci_messaggi(testo), on_token)
        if not risposta or risposta.startswith("__ERRORE"):
            return {"done": True, "ok": False,
                    "risposta": "Ollama non risponde. Controlla che sia acceso."}
        self.memoria.salva_scambio(testo, risposta)
        threading.Thread(target=self._forse_riassumi, daemon=True).start()
        return {
            "done": True, "ok": True, "imparato": imparato,
            "giorni": self.memoria.ricordi.get("giorni_insieme", 1),
            "scambi": self.memoria.numero_scambi(),
        }

    def stato(self):
        return {
            "nome":        CONFIG["nome_ai"],
            "online":      self.cervello.disponibile(),
            "giorni":      self.memoria.ricordi.get("giorni_insieme", 1),
            "scambi":      self.memoria.numero_scambi(),
            "nome_utente": self.memoria.get_valore_profilo("nome"),
            "modello":     CONFIG["modello"],
            "modelli":     self.cervello.modelli(),
            "citta":       self.memoria.get_valore_profilo("citta") or "Roma",
        }


# ════════════════════════════════════════════════════════════
# SERVER WEB
# ════════════════════════════════════════════════════════════
MOTORE = MotoreAI()

def _parse_qs(path):
    if "?" in path:
        return dict(urllib.parse.parse_qsl(path.split("?", 1)[1]))
    return {}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silenzio

    # ── helper risposte ─────────────────────────────────────
    def _json(self, dati, code=200):
        body = json.dumps(dati, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html_body(self, body, code=200):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _servi_gui(self):
        # Preferisci aria.html (la tua GUI completa); altrimenti usa quella integrata.
        if os.path.exists(HTML_FILE):
            try:
                with open(HTML_FILE, "rb") as f:
                    self._html_body(f.read())
                    return
            except Exception:
                pass
        self._html_body(GUI_FALLBACK)

    def _read_json_body(self):
        lung = int(self.headers.get("Content-Length", 0))
        if lung <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(lung).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── GET ─────────────────────────────────────────────────
    def do_GET(self):
        base = self.path.split("?")[0]
        qs   = _parse_qs(self.path)
        try:
            if base in ("/", "/index.html", "/aria.html"):
                self._servi_gui()
            elif base == "/stato":
                self._json(MOTORE.stato())
            elif base == "/salute":
                self._json({"ok": True, "online": MOTORE.cervello.disponibile(),
                            "modello": CONFIG["modello"], "nome": CONFIG["nome_ai"]})
            elif base == "/config":
                self._json({"nome": CONFIG["nome_ai"], "modello": CONFIG["modello"],
                            "modelli": MOTORE.cervello.modelli(), "carattere": CONFIG["carattere"],
                            "ollama": CONFIG["ollama_base"]})
            elif base == "/meteo":
                self._json(ottieni_meteo(qs.get("citta", "Roma")))
            elif base == "/statistiche":
                self._json(MOTORE.memoria.statistiche())
            elif base == "/esporta":
                self._json(MOTORE.memoria.esporta())
            elif base == "/timeline":
                self._json({"eventi": MOTORE.memoria.timeline()})
            elif base == "/cerca":
                q = qs.get("q", "").strip()
                self._json({"risultati": MOTORE.memoria.cerca(q) if q else []})
            else:
                self.send_error(404)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # ── POST ────────────────────────────────────────────────
    def do_POST(self):
        base = self.path.split("?")[0]
        try:
            if base == "/chat":
                testo = self._read_json_body().get("testo", "").strip()
                if not testo:
                    self._json({"ok": False, "risposta": "..."})
                    return
                self._json(MOTORE.rispondi(testo))

            elif base == "/chat/stream":
                self._chat_stream()

            elif base == "/ricorda":
                c = self._read_json_body()
                k, v = c.get("k", "").strip(), c.get("v", "").strip()
                if k and v:
                    MOTORE.memoria.ricorda_fatto(k, v); self._json({"ok": True})
                else:
                    self._json({"ok": False})

            elif base == "/dimentica":
                MOTORE.memoria.dimentica_fatto(self._read_json_body().get("k", "").strip())
                self._json({"ok": True})

            elif base == "/episodio":
                c = self._read_json_body()
                titolo, desc = c.get("titolo", "").strip(), c.get("desc", "").strip()
                if titolo:
                    MOTORE.memoria.salva_episodio(titolo, desc); self._json({"ok": True})
                else:
                    self._json({"ok": False})

            elif base == "/obiettivo":
                c = self._read_json_body()
                testo = c.get("testo", "").strip()
                if testo:
                    MOTORE.memoria.aggiungi_obiettivo(testo, c.get("tipo", "obiettivo")); self._json({"ok": True})
                else:
                    self._json({"ok": False})

            elif base == "/obiettivo/completa":
                idx = self._read_json_body().get("indice", -1)
                self._json({"ok": MOTORE.memoria.chiudi_obiettivo(idx)})

            elif base == "/relazione":
                c = self._read_json_body()
                nome, ruolo = c.get("nome", "").strip(), c.get("ruolo", "").strip()
                if nome and ruolo:
                    MOTORE.memoria.ricorda_persona(nome, ruolo, c.get("dettaglio", "").strip())
                    self._json({"ok": True})
                else:
                    self._json({"ok": False})

            elif base == "/reset":
                cat = self._read_json_body().get("categoria", "").strip()
                self._json({"ok": MOTORE.memoria.reset_categoria(cat)})

            elif base == "/importa":
                MOTORE.memoria.importa(self._read_json_body()); self._json({"ok": True})

            elif base == "/modello":
                m = self._read_json_body().get("modello", "").strip()
                if m:
                    CONFIG["modello"] = m; self._json({"ok": True, "modello": m})
                else:
                    self._json({"ok": False})

            elif base == "/carattere":
                c = self._read_json_body().get("carattere", "").strip()
                if c:
                    CONFIG["carattere"] = c; self._json({"ok": True})
                else:
                    self._json({"ok": False})

            else:
                self.send_error(404)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # ── streaming SSE ───────────────────────────────────────
    def _chat_stream(self):
        testo = self._read_json_body().get("testo", "").strip()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        def invia(obj):
            try:
                self.wfile.write(("data: " + json.dumps(obj, ensure_ascii=False) + "\n\n").encode("utf-8"))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                raise

        if not testo:
            invia({"done": True, "ok": False, "risposta": "..."})
            return
        try:
            meta = MOTORE.rispondi_stream(testo, lambda chunk: invia({"t": chunk}))
            invia(meta)
        except (BrokenPipeError, ConnectionResetError):
            pass  # il client ha chiuso, niente da fare


# ════════════════════════════════════════════════════════════
# GUI DI RISERVA (usata solo se manca aria.html)
# ════════════════════════════════════════════════════════════
GUI_FALLBACK = """<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MAIK // Server</title>
<style>
  :root{--cyan:#00f5ff;--bg:#050a0f;--panel:rgba(8,20,35,.9);--border:rgba(0,245,255,.18);--text:#c8e8f0;--dim:#5a7a8a;}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:system-ui,Segoe UI,sans-serif;height:100vh;display:flex;flex-direction:column}
  header{display:flex;align-items:center;gap:14px;padding:12px 18px;border-bottom:1px solid var(--border);font-size:13px}
  .logo{font-weight:800;letter-spacing:5px}.logo span{color:var(--cyan)}
  .dot{width:8px;height:8px;border-radius:50%;background:#ff3355;box-shadow:0 0 8px #ff3355}.dot.on{background:#00ff88;box-shadow:0 0 8px #00ff88}
  #wrap{flex:1;display:flex;overflow:hidden}
  #side{width:260px;border-right:1px solid var(--border);padding:14px;overflow:auto;font-size:13px;background:var(--panel)}
  #side h3{font-size:10px;letter-spacing:2px;color:var(--cyan);margin:14px 0 6px;text-transform:uppercase}
  #side h3:first-child{margin-top:0}
  .kv{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(0,245,255,.06)}
  .kv span:last-child{color:#fff}
  #main{flex:1;display:flex;flex-direction:column}
  #msgs{flex:1;overflow:auto;padding:18px;display:flex;flex-direction:column;gap:12px}
  .m{max-width:78%;padding:10px 14px;border-radius:10px;line-height:1.5;white-space:pre-wrap;word-break:break-word}
  .m.ai{align-self:flex-start;background:rgba(0,245,255,.07);border:1px solid rgba(0,245,255,.2)}
  .m.me{align-self:flex-end;background:rgba(0,245,255,.14);color:#fff}
  #bar{display:flex;gap:8px;padding:12px;border-top:1px solid var(--border)}
  #inp{flex:1;background:rgba(0,245,255,.05);border:1px solid var(--border);border-radius:20px;padding:11px 16px;color:#fff;font-size:14px;outline:none}
  #inp:focus{border-color:var(--cyan)}
  button.send{background:var(--cyan);border:none;color:#050a0f;width:44px;height:44px;border-radius:50%;font-size:16px;cursor:pointer;font-weight:700}
  button.send:disabled{opacity:.4}
  .quick{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 10px}
  .quick button{background:transparent;border:1px solid rgba(0,245,255,.2);color:var(--dim);padding:4px 10px;border-radius:12px;font-size:12px;cursor:pointer}
  .quick button:hover{color:var(--cyan);border-color:var(--cyan)}
  .note{color:var(--dim);font-size:11px;margin-top:14px;line-height:1.5}
  .cursor{display:inline-block;width:7px;height:14px;background:var(--cyan);vertical-align:middle;animation:b 1s infinite}
  @keyframes b{50%{opacity:.3}}
</style></head>
<body>
<header>
  <div class="logo">M A I K <span>// SERVER</span></div>
  <span class="dot" id="dot"></span><span id="stato">verifico…</span>
  <span style="margin-left:auto;color:var(--dim)" id="meta"></span>
</header>
<div id="wrap">
  <div id="side">
    <h3>Stato</h3>
    <div class="kv"><span>Modello</span><span id="s-mod">—</span></div>
    <div class="kv"><span>Giorni</span><span id="s-gg">—</span></div>
    <div class="kv"><span>Scambi</span><span id="s-sc">—</span></div>
    <div class="kv"><span>Utente</span><span id="s-ut">—</span></div>
    <h3>Profilo</h3>
    <div id="profilo" style="color:var(--dim)">—</div>
    <div class="note">GUI integrata di riserva. Per l'interfaccia 3D completa metti <b>aria.html</b> accanto a <b>maik_server.py</b>.</div>
  </div>
  <div id="main">
    <div id="msgs"></div>
    <div class="quick">
      <button onclick="q('Ciao!')">ciao</button>
      <button onclick="q('Cosa sai di me?')">cosa sai di me</button>
      <button onclick="q('Mi chiamo ')">mi chiamo…</button>
      <button onclick="q('Ti insegno che ')">ti insegno che…</button>
      <button onclick="q('Voglio ')">voglio…</button>
    </div>
    <div id="bar">
      <input id="inp" placeholder="Scrivi a Maik…" onkeydown="if(event.key==='Enter')invia()">
      <button class="send" id="send" onclick="invia()">➤</button>
    </div>
  </div>
</div>
<script>
const $=s=>document.querySelector(s);
function add(role,txt){const d=document.createElement('div');d.className='m '+role;d.textContent=txt;$('#msgs').appendChild(d);$('#msgs').scrollTop=1e9;return d;}
function q(t){$('#inp').value=t;$('#inp').focus();}
async function stato(){
  try{const r=await fetch('/stato');const s=await r.json();
    $('#dot').className='dot'+(s.online?' on':'');
    $('#stato').textContent=s.online?'ollama online':'ollama offline';
    $('#s-mod').textContent=s.modello;$('#s-gg').textContent=s.giorni;
    $('#s-sc').textContent=s.scambi;$('#s-ut').textContent=s.nome_utente||'—';
    $('#meta').textContent=(s.nome_utente?s.nome_utente+' · ':'')+s.giorni+' giorni';
  }catch(e){$('#stato').textContent='server non raggiungibile';}
}
async function profilo(){
  try{const r=await fetch('/statistiche');const s=await r.json();
    const p=s.profilo||{};const el=$('#profilo');
    const keys=Object.keys(p);
    el.innerHTML=keys.length?keys.map(k=>`<div class="kv"><span>${k}</span><span>${p[k]}</span></div>`).join(''):'nessun dato ancora';
  }catch(e){}
}
async function invia(){
  const t=$('#inp').value.trim(); if(!t) return;
  $('#inp').value=''; $('#send').disabled=true;
  add('me',t);
  const bubble=add('ai',''); bubble.innerHTML='<span class="cursor"></span>';
  let full='';
  try{
    const resp=await fetch('/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({testo:t})});
    const reader=resp.body.getReader(); const dec=new TextDecoder(); let buf='';
    while(true){
      const {done,value}=await reader.read(); if(done) break;
      buf+=dec.decode(value,{stream:true});
      let i; while((i=buf.indexOf('\\n\\n'))>=0){
        const line=buf.slice(0,i).trim(); buf=buf.slice(i+2);
        if(!line.startsWith('data:')) continue;
        const obj=JSON.parse(line.slice(5).trim());
        if(obj.t){full+=obj.t; bubble.innerHTML=full.replace(/</g,'&lt;')+'<span class="cursor"></span>';$('#msgs').scrollTop=1e9;}
        if(obj.done){
          if(obj.comando){bubble.textContent='['+obj.comando.tipo+'] '+JSON.stringify(obj.comando).slice(0,400);}
          else if(obj.ok===false){bubble.textContent=obj.risposta||'Errore.';}
          else{bubble.textContent=full;}
          stato(); profilo();
        }
      }
    }
  }catch(e){bubble.textContent='Errore di connessione: '+e.message;}
  $('#send').disabled=false; $('#inp').focus();
}
stato(); profilo(); setInterval(stato,15000);
add('ai','Ciao! Sono Maik (GUI server di riserva). Scrivimi pure.');
</script>
</body></html>"""


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("""
╔══════════════════════════════════════════════════╗
║           MAIK 6.0 — Server avviato             ║
║   Streaming · memoria episodica + emotiva        ║
╚══════════════════════════════════════════════════╝""")

    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"  Dati salvati in:  {DATA_DIR}")

    if not MOTORE.cervello.disponibile():
        print(f"""
  ⚠  Ollama non è acceso!
     1. Scarica da https://ollama.com/download
     2. Nel terminale:  ollama pull {CONFIG['modello']}
     3. Riavvia questo script

  (La GUI si apre lo stesso, mostrerà stato offline)
""")
    else:
        mod = MOTORE.cervello.modelli()
        print(f"  Ollama online  ·  modello: {CONFIG['modello']}")
        if mod:
            print(f"  Modelli pronti: {', '.join(mod)}")
            if CONFIG["modello"] not in mod:
                print(f"  ⚠  Attenzione: '{CONFIG['modello']}' non è tra i modelli installati.")

    url = f"http://{CONFIG['host']}:{CONFIG['porta']}"
    gui = "aria.html" if os.path.exists(HTML_FILE) else "GUI integrata di riserva"
    print(f"\n  GUI:  {gui}")
    print(f"  Pronto su:  {url}")
    print(f"  Premi Ctrl+C per chiudere\n")
    print(f"  Endpoint principali:")
    print(f"    POST /chat/stream   — chat in streaming (token-per-token)  [NUOVO]")
    print(f"    POST /chat          — chat classica (risposta completa)")
    print(f"    GET  /salute        — stato rapido del server             [NUOVO]")
    print(f"    GET  /config        — config corrente + modelli           [NUOVO]")
    print(f"    GET  /timeline      — storico eventi memorizzati")
    print(f"    GET  /cerca?q=testo — ricerca in tutta la memoria")
    print(f"    POST /episodio /obiettivo /relazione /reset /importa\n")

    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    server = ThreadingHTTPServer((CONFIG["host"], CONFIG["porta"]), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Chiudo Maik. A presto! 💚")
        server.shutdown()


if __name__ == "__main__":
    main()
