"""
╔══════════════════════════════════════════════════════════╗
║                  MAIK — Server v8.0                      ║
║   AI locale con GUI futuristica 3D nel browser           ║
║   Memoria avanzata: episodica, semantica, emotiva        ║
╚══════════════════════════════════════════════════════════╝

COME SI AVVIA:
  1. Ollama acceso + modello scaricato:  ollama pull llama3.1
  2. Avvia:  python maik_server.py
  3. Si apre da solo nel browser.

Solo librerie standard Python — niente pip.

NOVITÀ v8.0 — PIÙ INTELLIGENTE:
  • Apprendimento con l'IA: dopo ogni messaggio il modello estrae da solo
    fatti nuovi su di te (JSON), non solo con le frasi fisse
  • Memoria rilevante: nel prompt entrano i ricordi legati a ciò di cui parli
  • Azioni vere, anche offline: timer, promemoria con orario che SUONANO,
    calcoli, ora nel mondo, lista della spesa, note, dado/moneta, meteo
  • Briefing del giorno (meteo, promemoria, obiettivi, lista, frase del giorno)
  • 6 personalità: amico, coach, prof, comico, zen, genio
  • Supporto modelli che "ragionano" (deepseek-r1, qwen3): il <think> viene
    mostrato a parte e non finisce né nella voce né nella memoria
  • Nuovi endpoint: /promemoria, /promemoria/scaduti, /lista, /personalita,
    /briefing, /appreso

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
import ast
import json
import math
import time
import uuid
import random
import shutil
import operator
import datetime
import threading
import unicodedata
import webbrowser
import urllib.request
import urllib.parse
import urllib.error
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
    "modello_visione": _env("MAIK_MODELLO_VISIONE", "llava"),  # multimodale per la webcam (llava: massima compatibilità)
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
    "file_promemoria": "promemoria.json",
    "file_lista":     "lista.json",
    # apprendimento con l'IA (un'estrazione JSON dopo ogni messaggio personale)
    "apprendimento_ia": _env("MAIK_APPRENDIMENTO_IA", "1") not in ("0", "no", "false"),
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
GIORNI_LUNGHI = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
MESI_IT = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
           "luglio","agosto","settembre","ottobre","novembre","dicembre"]

def data_it(d):
    """Data in italiano indipendente dal locale del sistema (Windows compreso)."""
    return f"{GIORNI_LUNGHI[d.weekday()]} {d.day} {MESI_IT[d.month-1]} {d.year}"

def _senza_accenti(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")

def _normalizza(s):
    return re.sub(r"[^a-z0-9 ]+", " ", _senza_accenti(s).lower()).strip()

_STOP = set(("il lo la i gli le un uno una di da in con su per tra fra e o ma che chi non mi ti si "
             "ci vi ho hai ha abbiamo avete hanno sono sei siamo siete era del della dei delle al "
             "alla ai alle dal dalla nel nella sul sulla come cosa quando dove perche anche piu "
             "molto poco questo questa quello quella mio mia tuo tua suo sua cui se poi gia "
             "ancora sempre mai oggi ieri domani fatto fare essere stato tutto tutti").split())

def _token(s):
    """Parole significative (senza accenti, senza stop-word, troncate per gestire plurali/verbi)."""
    return {w[:6] for w in _normalizza(s).split() if len(w) > 2 and w not in _STOP}

_PAROLE_TAGLIO = set(("e ed ma con che ho sono sto dove perche perché pero però quando per mi ti ci poi anche "
                      "se come da del della nel nella in a al alla oggi ieri domani adesso ora molto tanto "
                      "ma insieme vicino").split())

def _taglia_frase(frase, max_parole=3):
    """Prende l'inizio di una frase fermandosi a congiunzioni e simili (la prima parola resta sempre)."""
    parole = re.sub(r"[^\wà-ÿ' ]+", " ", frase).split()
    out = []
    for i, w in enumerate(parole):
        if i and (w in _PAROLE_TAGLIO or len(out) >= max_parole):
            break
        out.append(w)
    return " ".join(out).strip(" '")

def pulisci_pensiero(testo):
    """Toglie il blocco <think>…</think> dei modelli che ragionano (deepseek-r1, qwen3…)."""
    t = re.sub(r"<think>.*?</think>", "", testo or "", flags=re.S | re.I)
    t = re.sub(r"<think>.*\Z", "", t, flags=re.S | re.I)   # pensiero rimasto aperto
    return t.strip()

_UMORI_POSITIVI = {"felice", "contento", "ottimo", "bene", "euforico", "sereno", "rilassato",
                   "eccitato", "entusiasta", "innamorato", "soddisfatto"}

def valenza_umore(umore, intensita=5):
    """0 = molto giù, 10 = al settimo cielo (per il grafico dell'umore)."""
    try:
        i = float(intensita)
    except (TypeError, ValueError):
        i = 5.0
    v = 5 + i / 2 if (umore or "").lower() in _UMORI_POSITIVI else 5 - i / 2
    return round(max(0.0, min(10.0, v)), 1)

def _get(url, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def ottieni_meteo(citta="Roma", timeout=8):
    geo_url = (f"{CONFIG['meteo_geo_url']}?name={urllib.parse.quote(citta)}"
               f"&count=1&language=it&format=json")
    geo = _get(geo_url, timeout)
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
    fc = _get(fc_url, timeout)
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
        self.promemoria = self._carica(CONFIG["file_promemoria"], [])
        self.lista     = self._carica(CONFIG["file_lista"],     [])
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

    def imposta_ricordo(self, chiave, valore):
        with self._lock:
            self.ricordi[chiave] = valore
            self._salva(CONFIG["file_ricordi"], self.ricordi)

    # ── Promemoria con orario (suonano davvero) ──────────────
    def aggiungi_promemoria(self, testo, quando=None, tipo="promemoria"):
        with self._lock:
            item = {
                "id":        uuid.uuid4().hex[:8],
                "testo":     testo,
                "quando":    quando.isoformat(timespec="seconds") if quando else None,
                "tipo":      tipo,
                "creato":    datetime.datetime.now().isoformat(timespec="seconds"),
                "notificato": False,
                "fatto":     False,
            }
            self.promemoria.append(item)
            eccesso = len(self.promemoria) - 300
            if eccesso > 0:   # butta via i più vecchi tra quelli già chiusi
                vecchi = {id(p) for p in [p for p in self.promemoria if p.get("fatto")][:eccesso]}
                self.promemoria = [p for p in self.promemoria if id(p) not in vecchi]
            self._salva(CONFIG["file_promemoria"], self.promemoria)
            return item

    def promemoria_attivi(self):
        with self._lock:
            attivi = [p for p in self.promemoria if not p.get("fatto")]
        return sorted(attivi, key=lambda p: p.get("quando") or "9999")

    def promemoria_scaduti(self):
        """Ritorna (e segna come notificati) i promemoria arrivati all'orario."""
        ora = datetime.datetime.now()
        scaduti = []
        with self._lock:
            for p in self.promemoria:
                if p.get("quando") and not p.get("notificato"):
                    try:
                        if datetime.datetime.fromisoformat(p["quando"]) <= ora:
                            p["notificato"] = True
                            if p.get("tipo") == "timer":
                                p["fatto"] = True
                            scaduti.append(dict(p))
                    except ValueError:
                        p["notificato"] = True
            if scaduti:
                self._salva(CONFIG["file_promemoria"], self.promemoria)
        return scaduti

    def promemoria_di_oggi(self):
        oggi = datetime.date.today().isoformat()
        return [p for p in self.promemoria_attivi() if (p.get("quando") or "")[:10] == oggi]

    def chiudi_promemoria(self, pid=None, tutti=False):
        with self._lock:
            n = 0
            for p in self.promemoria:
                if not p.get("fatto") and (tutti or p.get("id") == pid):
                    p["fatto"] = True
                    n += 1
            if n:
                self._salva(CONFIG["file_promemoria"], self.promemoria)
            return n

    # ── Lista della spesa / cose da fare ─────────────────────
    def lista_aggiungi(self, voci):
        aggiunte = []
        with self._lock:
            presenti = {x["testo"].lower() for x in self.lista if not x.get("fatto")}
            for v in voci:
                v = v.strip(" .,;!?").strip()
                if v and v.lower() not in presenti and len(v) <= 80:
                    self.lista.append({"testo": v, "fatto": False})
                    presenti.add(v.lower())
                    aggiunte.append(v)
            if aggiunte:
                self._salva(CONFIG["file_lista"], self.lista)
        return aggiunte

    def lista_rimuovi(self, testo):
        t = testo.lower().strip(" .,;!?")
        with self._lock:
            prima = len(self.lista)
            self.lista = [x for x in self.lista if t not in x["testo"].lower()]
            if len(self.lista) != prima:
                self._salva(CONFIG["file_lista"], self.lista)
            return prima - len(self.lista)

    def lista_modifica(self, azione, indice=-1, testo=""):
        with self._lock:
            if azione == "aggiungi" and testo:
                self.lista.append({"testo": testo.strip()[:80], "fatto": False})
            elif azione == "toggle" and 0 <= indice < len(self.lista):
                self.lista[indice]["fatto"] = not self.lista[indice].get("fatto")
            elif azione == "elimina" and 0 <= indice < len(self.lista):
                self.lista.pop(indice)
            elif azione == "pulisci":
                self.lista = [x for x in self.lista if not x.get("fatto")]
            elif azione == "svuota":
                self.lista = []
            else:
                return False
            self._salva(CONFIG["file_lista"], self.lista)
            return True

    # ── Apprendimento con l'IA ───────────────────────────────
    ALIAS_CHIAVI = {"città": "citta", "city": "citta", "name": "nome", "eta": "età", "age": "età",
                    "job": "lavoro", "professione": "lavoro", "mestiere": "lavoro"}

    def gia_noto(self):
        """Riassunto compatto di ciò che si sa già (per non far reimparare le stesse cose)."""
        with self._lock:
            prof = {k: (v.get("valore") if isinstance(v, dict) else v) for k, v in self.profilo.items()}
            return json.dumps({"profilo": prof,
                               "fatti": [x["cosa"] for x in self.imparato[-25:]],
                               "persone": [i["nome"] for i in self.relazioni.values()][:20]},
                              ensure_ascii=False)[:2500]

    def impara_da_ia(self, dati):
        """Unisce in memoria i fatti estratti dal modello. Ritorna cosa ha imparato davvero."""
        appreso = []
        if not isinstance(dati, dict):
            return appreso
        pulisci = lambda s: re.sub(r"\s+", " ", str(s or "")).strip()[:90]
        vuoto = re.compile(r"^(sconosciut|non\s|n/?a$|null|none|nessun|-$)", re.I)

        prof = dati.get("profilo")
        if isinstance(prof, dict):
            for k, v in list(prof.items())[:5]:
                k = pulisci(k).lower().replace(" ", "_")[:20]
                k = self.ALIAS_CHIAVI.get(k, k)
                v = pulisci(v)
                if not k or not v or vuoto.search(v) or self.get_valore_profilo(k).lower() == v.lower():
                    continue
                self.ricorda_fatto(k, v)
                appreso.append(f"{k}: {v}")

        noti = {_normalizza(x.get("cosa", "")) for x in self.imparato}
        for f in (dati.get("fatti") or [])[:4]:
            f = pulisci(f)
            n = _normalizza(f)
            if len(f) > 4 and n not in noti and not any(n in m or m in n for m in noti if m):
                self.impara_cosa(f, "ia")
                noti.add(n)
                appreso.append(f)

        for p in (dati.get("persone") or [])[:3]:
            if not isinstance(p, dict):
                continue
            nome, ruolo = pulisci(p.get("nome"))[:30], pulisci(p.get("ruolo"))[:30]
            if nome and not vuoto.search(nome) and nome.lower() not in self.relazioni:
                self.ricorda_persona(nome, ruolo or "persona")
                appreso.append(nome + (f" ({ruolo})" if ruolo else ""))

        for o in (dati.get("obiettivi") or [])[:2]:
            o = pulisci(o)
            if len(o) > 3 and not any(o.lower()[:30] == x.get("testo", "").lower()[:30] for x in self.obiettivi):
                self.aggiungi_obiettivo(o, "obiettivo")
                appreso.append("🎯 " + o)
        return appreso

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

    # ── Ricordi rilevanti per l'argomento corrente ───────────
    @staticmethod
    def _rilevanti(elementi, testo_di, query, k=6, recenti=4):
        """I `recenti` più nuovi + fino a `k` più pertinenti alla domanda (sovrapposizione di parole)."""
        if not elementi:
            return []
        scelti = list(range(max(0, len(elementi) - recenti), len(elementi)))
        q = _token(query)
        if q:
            punteggi = []
            for i, el in enumerate(elementi):
                comuni = len(q & _token(testo_di(el)))
                if comuni:
                    punteggi.append((comuni + i / (len(elementi) * 2), i))
            for _, i in sorted(punteggi, reverse=True)[:k]:
                if i not in scelti:
                    scelti.append(i)
        return [elementi[i] for i in sorted(scelti)]

    # ── Costruzione contesto per il system prompt ────────────
    def costruisci_contesto(self, query=""):
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
                sel = self._rilevanti(self.imparato, lambda x: x.get("cosa", ""), query, k=8, recenti=6)
                cose = "\n".join(f"- {x['cosa']}" for x in sel)
                parti.append(f"COSE CHE SAI DI LEI/LUI (le più pertinenti ora):\n{cose}")
            if self.episodi:
                sel = self._rilevanti(self.episodi, lambda e: e.get("titolo", "") + " " + e.get("desc", ""),
                                      query, k=4, recenti=3)
                ep_txt = "\n".join(f"- {ep['data']}: {ep['titolo']}" for ep in sel)
                parti.append(f"MOMENTI IMPORTANTI CHE RICORDI:\n{ep_txt}")
            attivi = [p for p in self.promemoria if not p.get("fatto")][:6]
            if attivi:
                pr = "\n".join(f"- {p['testo']}" + (f" ({p['quando'].replace('T', ' ')[:16]})" if p.get("quando") else "")
                               for p in attivi)
                parti.append(f"PROMEMORIA ATTIVI:\n{pr}")
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
                "promemoria": self.promemoria,
                "lista":     self.lista,
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
            "promemoria": ("file_promemoria", "promemoria"),
            "lista":     ("file_lista",     "lista"),
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
            "promemoria": ("file_promemoria", "promemoria", []),
            "lista":     ("file_lista",     "lista",     []),
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
                "umore_grafico":     [{"data": u.get("data", ""), "umore": u.get("umore", ""),
                                       "v": valenza_umore(u.get("umore", ""), u.get("intensita", 5))}
                                      for u in self.umore[-20:]],
                "n_promemoria":      len([p for p in self.promemoria if not p.get("fatto")]),
                "n_lista":           len([x for x in self.lista if not x.get("fatto")]),
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

    def pensa_json(self, prompt, timeout=120):
        """Chiede al modello una risposta in JSON (format: json) e la restituisce come dict, o None."""
        req = urllib.request.Request(
            CONFIG["ollama_url"],
            data=json.dumps({
                "model": CONFIG["modello"],
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0, "num_predict": 300},
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                testo = pulisci_pensiero(json.loads(r.read().decode("utf-8"))["message"]["content"])
            m = re.search(r"\{.*\}", testo, re.S)   # tollera testo attorno al JSON
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None

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

    def vedi(self, img_b64, prompt=""):
        """Manda un fotogramma della webcam a un modello multimodale e ritorna la descrizione.
        Prova più modelli compatibili in cascata (utile se uno non è installato o
        se Ollama è troppo vecchio per certe architetture, es. 'mllama')."""
        istr = prompt or ("Guardi attraverso una webcam la persona con cui chiacchieri. "
                          "Descrivi in modo amichevole e naturale cosa vedi (la persona, l'espressione, "
                          "l'ambiente), in italiano, in 1-2 frasi, come farebbe un amico. Niente elenchi.")
        candidati = []
        for mdl in (CONFIG["modello_visione"], "llava", "moondream", "llama3.2-vision"):
            if mdl and mdl not in candidati:
                candidati.append(mdl)
        ultimo_err = ""
        for mdl in candidati:
            payload = json.dumps({
                "model": mdl,
                "messages": [{"role": "user", "content": istr, "images": [img_b64]}],
                "stream": False,
            }).encode("utf-8")
            req = urllib.request.Request(CONFIG["ollama_url"], data=payload,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=CONFIG["timeout_chat"]) as r:
                    testo = json.loads(r.read().decode("utf-8"))["message"]["content"].strip()
                    if mdl != CONFIG["modello_visione"]:
                        CONFIG["modello_visione"] = mdl   # ricorda quello che ha funzionato
                    return testo
            except urllib.error.HTTPError as e:
                try:    corpo = e.read().decode("utf-8", "ignore")
                except Exception: corpo = str(e)
                ultimo_err = corpo
                low = corpo.lower()
                # modello assente o architettura non supportata → prova il prossimo
                if "not found" in low or "architecture" in low or "mllama" in low:
                    continue
                return f"__ERRORE__ {corpo}"
            except Exception as e:
                return f"__ERRORE__ {e}"     # errore di rete: inutile insistere
        return f"__ERRORE_VIS__ {ultimo_err}"


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
        # (si ferma a "e/con/che/…": "vivo a Milano e ho un cane" → "Milano")
        m = re.search(r"\b(vivo a|abito a|sono di|vengo da|mi trovo a)\s+([a-zà-ÿ' ]{2,40})", tl)
        if m:
            citta = _taglia_frase(m.group(2), 3).title()
            if citta and citta.lower() not in Estrattore.STOP_NOMI:
                memoria.ricorda_fatto("citta", citta)
                salvati.append(f"dove vivi ({citta})")

        # ── 4. LAVORO / STUDIO ───────────────────────────────
        # niente "sono un/una": "sono un po' triste" non è un mestiere
        m = re.search(r"\b(lavoro come|faccio il|faccio la|faccio lo|di mestiere faccio|lavoro in|lavoro presso|"
                      r"studio|frequento)\s+([a-zà-ÿ' ]{3,40})", tl)
        if m and len(tl.split()) <= 12:
            lavoro = _taglia_frase(m.group(2), 4)
            chiave = "studio" if m.group(1) in ("studio", "frequento") else "lavoro"
            if len(lavoro) >= 3:
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
# PERSONALITÀ
# ════════════════════════════════════════════════════════════
CARATTERE_BASE = CONFIG["carattere"]
PERSONALITA = {
    "amico":  ("🫂", "Amico",  CARATTERE_BASE),
    "coach":  ("💪", "Coach",  "Sei Maik in modalità COACH motivazionale. Energico, diretto e positivo: spingi "
                                "la persona all'azione con passi piccoli e concreti, celebri ogni progresso, non "
                                "accetti scuse ma sempre con affetto. In italiano, frasi brevi e cariche."),
    "prof":   ("🎓", "Prof",   "Sei Maik in modalità PROFESSORE. Spieghi in modo chiaro e ordinato, con esempi "
                                "semplici e analogie di tutti i giorni; alla fine fai una piccola domanda per "
                                "verificare che sia tutto chiaro. Paziente e preciso, in italiano."),
    "comico": ("😂", "Comico", "Sei Maik in modalità COMICO. Ironico e brillante, fai battute e giochi di parole "
                                "in italiano, ma resti gentile e davvero utile. Mai volgare né offensivo."),
    "zen":    ("🧘", "Zen",    "Sei Maik in modalità ZEN. Calmo, lento e rassicurante: aiuti a respirare, a "
                                "ridimensionare i problemi e a stare nel presente. Frasi brevi e tono morbido, in italiano."),
    "genio":  ("🧠", "Genio",  "Sei Maik in modalità GENIO. Ragioni passo dopo passo con rigore, consideri pro, "
                                "contro e casi particolari, e dai risposte approfondite e ben organizzate (titoletti ed "
                                "elenchi quando aiutano). In italiano, chiaro anche quando l'argomento è complesso."),
}
CONFIG["personalita"] = "amico"

def imposta_personalita(chiave, memoria=None):
    if chiave not in PERSONALITA:
        return False
    CONFIG["carattere"] = PERSONALITA[chiave][2]
    CONFIG["personalita"] = chiave
    if memoria is not None:
        memoria.imposta_ricordo("personalita", chiave)
    return True


# ════════════════════════════════════════════════════════════
# TEMPO: durate, orari, fusi orari (solo libreria standard)
# ════════════════════════════════════════════════════════════
_NUMERI_PAROLE = {"un": 1, "uno": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6,
                  "sette": 7, "otto": 8, "nove": 9, "dieci": 10, "quindici": 15, "venti": 20,
                  "trenta": 30, "quaranta": 40, "cinquanta": 50, "mezz": 0.5, "mezzo": 0.5, "mezza": 0.5}
_RE_DURATA = re.compile(
    r"\b(\d+(?:[.,]\d+)?|un|uno|una|due|tre|quattro|cinque|sei|sette|otto|nove|dieci|quindici|venti|"
    r"trenta|quaranta|cinquanta|mezz|mezzo|mezza)\s*'?\s*(secondi|secondo|sec|minuti|minuto|min|ore|ora|h|giorni|giorno)\b")

def _secondi_unita(u):
    return 1 if u.startswith("sec") else 60 if u.startswith("min") else 86400 if u.startswith("giorn") else 3600

def _durata_iniziale(seg):
    """Durata espressa all'inizio di `seg` ("10 minuti", "un'ora e mezza"). Ritorna (secondi, caratteri usati)."""
    tot, pos = 0.0, 0
    for m in _RE_DURATA.finditer(seg):
        if seg[pos:m.start()].strip() not in ("", "e"):
            break
        q, u = m.group(1), m.group(2)
        n = _NUMERI_PAROLE.get(q)
        n = float(q.replace(",", ".")) if n is None else n
        tot += n * _secondi_unita(u)
        pos = m.end()
        mm = re.match(r"\s+e\s+mezz[oa]\b", seg[pos:])
        if mm:
            tot += _secondi_unita(u) / 2
            pos += mm.end()
    return int(tot), pos

def parse_durata(testo):
    """Somma tutte le durate nel testo: "1 ora e 30 minuti" → 5400."""
    t = testo.lower()
    for m in _RE_DURATA.finditer(t):
        sec, _ = _durata_iniziale(t[m.start():])
        if sec:
            return sec
    return 0

def fmt_durata(sec):
    sec = int(round(sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    parti = []
    if h:
        parti.append("1 ora" if h == 1 else f"{h} ore")
    if m:
        parti.append("1 minuto" if m == 1 else f"{m} minuti")
    if s and not h:
        parti.append("1 secondo" if s == 1 else f"{s} secondi")
    return " e ".join(parti) or "0 secondi"

def fmt_quando(d, ora=None):
    ora = ora or datetime.datetime.now()
    hh = d.strftime("%H:%M")
    giorni = (d.date() - ora.date()).days
    secondi = (d - ora).total_seconds()
    if 0 <= secondi < 3600:
        return f"tra {fmt_durata(secondi)} (alle {d.strftime('%H:%M:%S') if secondi < 120 else hh})"
    if giorni == 0:
        return f"oggi alle {hh}"
    if giorni == 1:
        return f"domani alle {hh}"
    if 1 < giorni < 7:
        return f"{GIORNI_LUNGHI[d.weekday()]} alle {hh}"
    return f"il {d.day} {MESI_IT[d.month-1]} alle {hh}"

_GIORNI_SETT_RE = [(r"luned[iì]", 0), (r"marted[iì]", 1), (r"mercoled[iì]", 2), (r"gioved[iì]", 3),
                   (r"venerd[iì]", 4), (r"sabato", 5), (r"domenica", 6)]
_FASCE = [(r"stamattina|questa mattina|di mattina|la mattina|in mattinata", (9, 0)),
          (r"oggi pomeriggio|questo pomeriggio|nel pomeriggio|di pomeriggio", (15, 0)),
          (r"stasera|questa sera|di sera|la sera|in serata", (20, 0)),
          (r"stanotte|questa notte", (23, 0)),
          (r"a mezzogiorno|mezzogiorno", (12, 0)),
          (r"a mezzanotte|mezzanotte", (0, 0))]

def _rimuovi_span(testo, spans):
    out, pos = [], 0
    for a, b in sorted(spans):
        if a < pos:
            continue
        out.append(testo[pos:a])
        pos = b
    out.append(testo[pos:])
    return re.sub(r"\s{2,}", " ", "".join(out)).strip()

def parse_quando(testo, ora=None):
    """Capisce quando in italiano ("tra 10 minuti", "domani alle 9", "stasera", "lunedì alle 18:30").
    Ritorna (datetime | None, testo senza le parole di tempo)."""
    ora = ora or datetime.datetime.now()
    tl = testo.lower()            # stessa lunghezza dell'originale: gli indici valgono per entrambi
    spans = []

    # 1) relativo: "tra 10 minuti", "fra un'ora e mezza", "tra mezz'ora"
    for m in re.finditer(r"\b(?:tra|fra)\s+", tl):
        sec, lung = _durata_iniziale(tl[m.end():])
        if sec > 0:
            return ora + datetime.timedelta(seconds=sec), _rimuovi_span(testo, [(m.start(), m.end() + lung)])

    giorno, settimana, fascia = None, False, None
    for rx, g in ((r"\bdopodomani\b", 2), (r"\bdomani\b", 1), (r"\boggi\b", 0)):
        m = re.search(rx, tl)
        if m:
            giorno = g
            spans.append(m.span())
            break
    for rx, wd in _GIORNI_SETT_RE:
        m = re.search(r"\b(?:(?:il|di|questo|questa|prossimo|prossima)\s+)?" + rx + r"(?:\s+prossim[oa])?\b", tl)
        if m:
            giorno, settimana = (wd - ora.weekday()) % 7, True
            spans.append(m.span())
            break
    for rx, hm in _FASCE:
        m = re.search(r"\b(?:" + rx + r")\b", tl)
        if m:
            fascia = hm
            spans.append(m.span())
            break

    m = re.search(r"\b(?:(?:alle|per le|verso le|entro le)(?:\s+ore)?|ore)\s+(\d{1,2})(?:[:.](\d{2}))?\b", tl)
    mu = re.search(r"\ball'una(?:\s+e\s+mezza)?\b", tl)
    if m:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        spans.append(m.span())
        if fascia and fascia[0] >= 12 and h < 12:
            h += 12                              # "stasera alle 8" → 20:00
        elif not fascia and 1 <= h <= 6:
            h += 12                              # "alle 3" di solito è pomeriggio
    elif mu:
        h, mi = 13, (30 if "mezza" in mu.group(0) else 0)
        spans.append(mu.span())
    elif fascia:
        h, mi = fascia
        if fascia == (0, 0) and giorno is None:
            giorno = 1
    elif giorno:
        h, mi = 9, 0                             # "domani" senza orario → alle 9
    else:
        return None, testo
    if h > 23 or mi > 59:
        return None, testo

    d = (ora + datetime.timedelta(days=giorno or 0)).replace(hour=h, minute=mi, second=0, microsecond=0)
    if d <= ora:
        if giorno is None and not fascia and h < 12 and d.replace(hour=h + 12) > ora:
            d = d.replace(hour=h + 12)           # "alle 8" detto alle 10 → le 20
        else:
            d += datetime.timedelta(days=7 if settimana else 1)
    return d, _rimuovi_span(testo, spans)

# città → (fuso IANA, offset standard in ore, regola ora legale) — fallback senza tzdata (Windows)
CITTA_FUSI = {}
for _nomi, _fuso in (
    (("roma", "milano", "napoli", "torino", "italia", "parigi", "francia", "madrid", "barcellona", "spagna",
      "berlino", "germania", "amsterdam", "olanda", "bruxelles", "vienna", "zurigo", "svizzera", "varsavia",
      "praga", "stoccolma", "oslo", "copenaghen"), ("Europe/Rome", 1, "eu")),
    (("londra", "inghilterra", "regno unito", "dublino", "irlanda", "lisbona", "portogallo"), ("Europe/London", 0, "eu")),
    (("atene", "grecia", "kiev", "ucraina", "bucarest", "romania", "helsinki"), ("Europe/Athens", 2, "eu")),
    (("istanbul", "turchia"), ("Europe/Istanbul", 3, None)),
    (("mosca", "russia"), ("Europe/Moscow", 3, None)),
    (("il cairo", "cairo", "egitto", "johannesburg", "sudafrica"), ("Africa/Johannesburg", 2, None)),
    (("lagos", "nigeria", "casablanca", "marocco"), ("Africa/Lagos", 1, None)),
    (("dubai", "emirati", "abu dhabi"), ("Asia/Dubai", 4, None)),
    (("delhi", "nuova delhi", "mumbai", "india"), ("Asia/Kolkata", 5.5, None)),
    (("bangkok", "thailandia", "giacarta", "indonesia"), ("Asia/Bangkok", 7, None)),
    (("singapore", "hong kong", "pechino", "shanghai", "cina", "manila", "filippine"), ("Asia/Shanghai", 8, None)),
    (("tokyo", "giappone", "seoul", "corea"), ("Asia/Tokyo", 9, None)),
    (("sydney", "melbourne", "australia"), ("Australia/Sydney", 10, "au")),
    (("new york", "nyc", "miami", "boston", "washington", "toronto", "canada", "america", "stati uniti", "usa",
      "havana", "cuba"), ("America/New_York", -5, "us")),
    (("chicago", "dallas", "houston"), ("America/Chicago", -6, "us")),
    (("los angeles", "san francisco", "las vegas", "seattle", "california"), ("America/Los_Angeles", -8, "us")),
    (("citta del messico", "messico"), ("America/Mexico_City", -6, None)),
    (("bogota", "colombia", "lima", "peru", "panama", "ecuador", "quito"), ("America/Bogota", -5, None)),
    (("caracas", "venezuela", "santo domingo", "repubblica dominicana", "puerto rico", "la paz", "bolivia"),
     ("America/Caracas", -4, None)),
    (("buenos aires", "argentina", "san paolo", "rio", "rio de janeiro", "brasile", "montevideo", "uruguay",
      "santiago", "cile"), ("America/Sao_Paulo", -3, None)),
):
    for _n in _nomi:
        CITTA_FUSI[_n] = _fuso

def _domenica(anno, mese, n):
    """n-esima domenica del mese (n=-1 → l'ultima)."""
    if n > 0:
        d = datetime.date(anno, mese, 1)
        d += datetime.timedelta(days=(6 - d.weekday()) % 7 + 7 * (n - 1))
        return d
    d = (datetime.date(anno + (mese == 12), mese % 12 + 1, 1) - datetime.timedelta(days=1))
    return d - datetime.timedelta(days=(d.weekday() - 6) % 7)

def _ora_legale(regola, utc):
    y = utc.year
    if regola == "eu":
        return (datetime.datetime.combine(_domenica(y, 3, -1), datetime.time(1)) <= utc <
                datetime.datetime.combine(_domenica(y, 10, -1), datetime.time(1)))
    if regola == "us":
        return (datetime.datetime.combine(_domenica(y, 3, 2), datetime.time(7)) <= utc <
                datetime.datetime.combine(_domenica(y, 11, 1), datetime.time(6)))
    if regola == "au":
        return not (datetime.datetime.combine(_domenica(y, 4, 1), datetime.time(16)) <= utc <
                    datetime.datetime.combine(_domenica(y, 10, 1), datetime.time(16)))
    return False

def trova_citta(nome):
    n = _normalizza(nome)
    n = re.sub(r"^(?:a|ad|in|nel|nella|negli|nelle)\s+", "", n).strip()
    if n in CITTA_FUSI:
        return n
    for k in sorted(CITTA_FUSI, key=len, reverse=True):   # "a new york adesso" → "new york"
        if re.search(r"\b" + re.escape(k) + r"\b", n):
            return k
    return None

def ora_in(chiave):
    iana, off, regola = CITTA_FUSI[chiave]
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo(iana)).replace(tzinfo=None)
    except Exception:
        utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        return utc + datetime.timedelta(hours=off + (1 if regola and _ora_legale(regola, utc) else 0))


# ════════════════════════════════════════════════════════════
# CALCOLATRICE SICURA (niente eval: albero sintattico controllato)
# ════════════════════════════════════════════════════════════
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}

def _valuta(nodo):
    if isinstance(nodo, ast.Expression):
        return _valuta(nodo.body)
    if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPS:
        a, b = _valuta(nodo.left), _valuta(nodo.right)
        if isinstance(nodo.op, ast.Pow) and (abs(b) > 100 or abs(a) > 1e6):
            raise ValueError("numero troppo grande")
        return _OPS[type(nodo.op)](a, b)
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
        v = _valuta(nodo.operand)
        return -v if isinstance(nodo.op, ast.USub) else v
    if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id == "sqrt"
            and len(nodo.args) == 1 and not nodo.keywords):
        return math.sqrt(_valuta(nodo.args[0]))
    raise ValueError("espressione non valida")

def calcola(espr):
    """Valuta un'espressione scritta anche a parole ("15% di 230", "3 per 4", "radice di 144").
    Ritorna il numero, oppure None se non è un calcolo. Solleva ZeroDivisionError."""
    s = espr.lower().strip()
    s = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", s)                 # 1.000 → 1000
    s = s.replace(",", ".")
    s = re.sub(r"(\d+(?:\.\d+)?)\s*%\s*(?:di|del|dello|della|dei|degli|delle|su)\s*(\d+(?:\.\d+)?)", r"(\1/100*\2)", s)
    s = re.sub(r"radice(?:\s+quadrata)?(?:\s+di)?\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", s)
    s = re.sub(r"\bal\s+quadrato\b", "^2", s)
    s = re.sub(r"\bal\s+cubo\b", "^3", s)
    s = re.sub(r"\belevato\s+(?:alla|a)\b", "^", s)
    s = re.sub(r"\bdiviso(?:\s+per)?\b", "/", s)
    s = re.sub(r"\b(?:moltiplicato\s+)?per\b", "*", s)
    s = re.sub(r"(?<=[\d)])\s*[x×]\s*(?=[\d(])", "*", s)
    s = re.sub(r"\bpi[uù]\b", "+", s)
    s = re.sub(r"\bmeno\b", "-", s)
    s = s.replace("÷", "/").replace(":", "/").replace("^", "**")
    if not re.fullmatch(r"(?:[\d\s.+\-*/()]|sqrt)+", s) or not re.search(r"[+\-*/]|sqrt", s):
        return None
    try:
        return _valuta(ast.parse(s.strip(), mode="eval"))
    except ZeroDivisionError:
        raise
    except Exception:
        return None

def fmt_num(v):
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        v = int(v)
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    s = f"{v:,.6f}".rstrip("0").rstrip(".")
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ════════════════════════════════════════════════════════════
# AZIONI INTELLIGENTI — MAIK fa le cose (funziona anche offline)
# ════════════════════════════════════════════════════════════
FRASI_DEL_GIORNO = [
    "Un piccolo passo oggi vale più di un grande piano rimandato.",
    "Non serve essere perfetti: serve essere costanti.",
    "Ogni giorno è una pagina nuova: scrivila a modo tuo.",
    "Le cose difficili si fanno un pezzetto alla volta.",
    "Sii gentile con te stesso: stai facendo del tuo meglio.",
    "La fatica di oggi è la forza di domani.",
    "Una giornata storta non è una vita storta.",
    "Respira. Una cosa sola. Poi la prossima.",
    "Il momento migliore per iniziare era ieri. Il secondo migliore è adesso.",
    "Credi in te almeno quanto ci credo io. 💚",
]

AIUTO = """Ecco cosa so fare al volo (anche senza Ollama):
- ⏱️ «metti un timer di 10 minuti» · «annulla il timer»
- ⏰ «ricordami alle 18 di chiamare la mamma» · «…tra 20 minuti…» · «che promemoria ho?»
- 🛒 «aggiungi latte e pane alla lista» · «cosa c'è nella lista?» · «svuota la lista»
- 🧮 «quanto fa 15% di 230» · «radice di 144» · «3 per 4 più 2»
- 🕒 «che ore sono a Tokyo?» · «che giorno è?»
- 🌤️ «che tempo fa a Milano?»
- ☀️ «briefing» — il riepilogo della tua giornata
- 🎲 «lancia un dado» · «testa o croce» · «numero a caso tra 1 e 50»
- 📝 «prendi nota: …»
- 🎭 «modalità coach / prof / comico / zen / genio / amico»
Per tutto il resto, chiacchieriamo! 💚"""

_RE_TRIGGER_PROMEMORIA = re.compile(
    r"\b(?:per favore\s+)?(?:puoi\s+)?(?:ricordami|ricordarmi|avvisami|fammi ricordare|"
    r"mettimi un promemoria|metti un promemoria|imposta un promemoria|crea un promemoria|promemoria)\b[:,]?", re.I)


class Azioni:
    """Router deterministico: capisce i comandi pratici e li esegue subito, senza LLM."""

    @staticmethod
    def prova(testo, memoria):
        t = testo.strip()
        tl = t.lower()
        for gestore in (Azioni._aiuto, Azioni._personalita, Azioni._timer, Azioni._promemoria,
                        Azioni._lista, Azioni._nota, Azioni._ora_data, Azioni._calcolo,
                        Azioni._caso, Azioni._meteo, Azioni._briefing):
            try:
                r = gestore(t, tl, memoria)
            except ZeroDivisionError:
                return "🧮 Non si può dividere per zero! 😅"
            if r:
                return r
        return None

    @staticmethod
    def _aiuto(t, tl, memoria):
        if re.fullmatch(r"\s*(?:aiuto|help|comandi|cosa sai fare|che cosa sai fare|cosa puoi fare|"
                        r"che cosa puoi fare)\s*[?!.]*\s*", tl):
            return AIUTO

    @staticmethod
    def _personalita(t, tl, memoria):
        m = re.search(r"\b(?:modalit[aà]|personalit[aà]|diventa|fai il|fai la|fai lo|sii|comportati da)\s+"
                      r"(amico|coach|prof|professore|comico|zen|genio)\b", tl)
        if not m:
            return None
        chiave = "prof" if m.group(1).startswith("prof") else m.group(1)
        imposta_personalita(chiave, memoria)
        em, nome, _ = PERSONALITA[chiave]
        saluti = {
            "amico": "Eccomi, sono di nuovo il tuo amico di sempre. Raccontami tutto!",
            "coach": "Pronti? Oggi si fa sul serio: dimmi un obiettivo e lo spacchiamo in passi!",
            "prof": "Lezione aperta: chiedimi qualunque cosa e te la spiego per bene.",
            "comico": "Attenzione: da adesso le mie risposte potrebbero contenere tracce di battute.",
            "zen": "Facciamo un bel respiro insieme… Ecco. Sono qui, con calma.",
            "genio": "Cervello al massimo: fammi una domanda difficile e ragioniamo a fondo.",
        }
        return f"{em} Modalità **{nome}** attivata! {saluti[chiave]}"

    @staticmethod
    def _timer(t, tl, memoria):
        if re.search(r"\b(?:ferma|annulla|cancella|stoppa|elimina)\b.*\b(?:timer|sveglia)\b", tl):
            n = 0
            for p in memoria.promemoria_attivi():
                if p.get("tipo") == "timer":
                    n += memoria.chiudi_promemoria(p["id"])
            return "⏹️ Timer annullato." if n else "Non c'è nessun timer attivo."
        # serve un comando vero: "sono sveglia da 3 ore" o "il timer del forno è rotto" non sono timer
        comando = re.search(r"\b(?:metti|mettimi|imposta|avvia|fai partire|crea|setta|parti|punta)\b", tl)
        breve = len(tl.split()) <= 8
        if not ((re.search(r"\b(?:timer|countdown|conto alla rovescia)\b", tl) and (comando or breve))
                or re.search(r"\bsvegliami\b", tl)
                or (comando and re.search(r"\bsveglia\b", tl))):
            return None
        sec = parse_durata(tl)
        if sec:
            if sec > 2 * 86400:
                return "⏱️ Massimo 48 ore per un timer: per cose più lontane usa un promemoria («ricordami…»)."
            quando = datetime.datetime.now() + datetime.timedelta(seconds=sec)
            durata = fmt_durata(sec)
            memoria.aggiungi_promemoria(f"Timer di {durata}", quando, "timer")
            return f"⏱️ Timer di **{durata}** avviato! Suonerà alle {quando.strftime('%H:%M:%S')}."
        if re.search(r"\bsveglia|svegliami\b", tl):
            quando, _ = parse_quando(t)
            if quando:
                memoria.aggiungi_promemoria("Sveglia! ☀️", quando, "timer")
                return f"⏰ Sveglia impostata per **{fmt_quando(quando)}**."
        if re.search(r"\b(?:metti|imposta|avvia|fai partire|crea|setta)\b", tl):
            return "⏱️ Di quanto tempo? Dimmi per esempio «metti un timer di 10 minuti»."
        return None

    @staticmethod
    def _promemoria(t, tl, memoria):
        if not re.search(r"\b(?:ricordami|ricordarmi|avvisami|fammi ricordare|promemoria)\b", tl):
            return None
        if re.search(r"\b(?:cancella|elimina|togli|annulla|svuota)\b.*\bpromemoria\b", tl):
            n = memoria.chiudi_promemoria(tutti=True)
            return f"🗑️ Ho cancellato {n} promemoria." if n else "Non hai promemoria attivi."
        if (re.search(r"\b(?:che|quali|quanti|i miei|elenca|mostra|leggi|dimmi)\b.*\bpromemoria\b", tl)
                and not re.search(r"\b(?:ricordami|ricordarmi|avvisami)\b", tl)):
            attivi = memoria.promemoria_attivi()
            if not attivi:
                return "📭 Non hai promemoria attivi."
            righe = []
            for p in attivi[:10]:
                q = p.get("quando")
                quando = fmt_quando(datetime.datetime.fromisoformat(q)) if q else "senza orario"
                righe.append(f"- {p['testo']} — {quando}")
            return "⏰ I tuoi promemoria:\n" + "\n".join(righe)
        # per CREARE serve un comando esplicito ("ho perso il promemoria" non è un comando)
        if not re.search(r"\b(?:ricordami|ricordarmi|avvisami|fammi ricordare|"
                         r"(?:metti|mettimi|imposta|crea|aggiungi)\s+un\s+promemoria)\b", tl):
            return None
        quando, resto = parse_quando(t)
        cosa = _RE_TRIGGER_PROMEMORIA.sub(" ", resto)
        cosa = re.sub(r"^\s*(?:maik[,!]?\s*)?", "", cosa, flags=re.I)
        cosa = re.sub(r"^\s*(?:di|che|per|:|,|-)\s+", "", cosa.strip(), flags=re.I).strip(" .,!?:;")
        if len(cosa) < 2:
            return "Certo! Cosa devo ricordarti, e quando? Es: «ricordami alle 18 di chiamare la mamma»."
        memoria.aggiungi_promemoria(cosa, quando, "promemoria")
        if quando:
            return f"⏰ Fatto! Ti ricorderò di **{cosa}** {fmt_quando(quando)}."
        return (f"📌 Segnato: **{cosa}**. Se vuoi che suoni, dimmi anche quando "
                f"(«…alle 18» o «…tra 20 minuti»).")

    @staticmethod
    def _lista(t, tl, memoria):
        if "lista" not in tl:
            return None
        def riepilogo():
            aperte = [x["testo"] for x in memoria.lista if not x.get("fatto")]
            return (f"Ora ci sono {len(aperte)} voci: {', '.join(aperte[:12])}{'…' if len(aperte) > 12 else ''}."
                    if aperte else "La lista è vuota.")
        if re.search(r"\b(?:svuota|azzera|cancella|elimina)\s+(?:tutta\s+)?(?:la\s+)?(?:mia\s+)?lista\b", tl):
            memoria.lista_modifica("svuota")
            return "🧹 Lista svuotata."
        m = re.search(r"\b(?:togli|rimuovi|cancella|elimina|leva)\s+(.+?)\s+dalla\s+(?:mia\s+)?lista\b", tl)
        if m:
            n = memoria.lista_rimuovi(t[m.start(1):m.end(1)])
            return (f"✂️ Tolto dalla lista. {riepilogo()}" if n else
                    f"Non trovo «{t[m.start(1):m.end(1)]}» nella lista.")
        m = re.search(r"\b(?:aggiungi|metti|segna|inserisci|scrivi)\s+(.+?)\s+(?:alla|nella|in)\s+(?:mia\s+)?lista\b", tl)
        if m:
            voci = re.split(r"\s*,\s*|\s+(?:e|ed)\s+", t[m.start(1):m.end(1)])
            aggiunte = memoria.lista_aggiungi(voci)
            if not aggiunte:
                return f"Era già tutto in lista! {riepilogo()}"
            return f"🛒 Aggiunto alla lista: **{', '.join(aggiunte)}**. {riepilogo()}"
        # "dimmi una lista di 5 film" è per l'IA: qui solo "la/nella (mia) lista" a fine frase
        if (re.search(r"\b(?:cosa c'?[eè]|che c'?[eè]|leggi(?:mi)?|mostra(?:mi)?|dimmi|com'?[eè]|vedi)\s+"
                      r"(?:nella|la)\s+(?:mia\s+)?lista(?:\s+della\s+spesa)?\s*[?!.]*\s*$", tl)
                or re.fullmatch(r"\s*(?:la\s+)?(?:mia\s+)?lista(?:\s+della\s+spesa)?\s*[?!.]*\s*", tl)):
            aperte = [x["testo"] for x in memoria.lista if not x.get("fatto")]
            if not aperte:
                return "🛒 La tua lista è vuota. Dimmi «aggiungi … alla lista»!"
            return "🛒 Nella tua lista:\n" + "\n".join(f"- {v}" for v in aperte)
        return None

    @staticmethod
    def _nota(t, tl, memoria):
        m = re.match(r"\s*(?:maik[,!]?\s*)?(?:prendi nota|prendi appunti|annota|annotati|segnati|scrivi una nota)"
                     r"\s*(?:che|di|:|,|-)?\s*(.+)", t, re.I)
        if not m or len(m.group(1).strip()) < 2:
            return None
        nota = m.group(1).strip(" .")
        memoria.impara_cosa(nota, "nota")
        return f"📝 Annotato: «{nota}». Me lo ricorderò."

    @staticmethod
    def _ora_data(t, tl, memoria):
        m = re.search(r"\b(?:che ore sono|che ora [eè]|che ore fanno|dimmi l'ora|l'ora esatta)\b"
                      r"(?:\s+(?:adesso|ora))?(?:\s+(.+))?", tl)
        if m:
            luogo = (m.group(1) or "").strip(" ?!.")
            if luogo:
                k = trova_citta(luogo)
                if k:
                    d = ora_in(k)
                    return f"🕒 A **{k.title()}** sono le **{d.strftime('%H:%M')}** ({GIORNI_LUNGHI[d.weekday()]})."
                return (f"🕒 Non conosco il fuso orario di «{luogo}», ma qui sono le "
                        f"**{datetime.datetime.now().strftime('%H:%M')}**.")
            return f"🕒 Sono le **{datetime.datetime.now().strftime('%H:%M')}**."
        if re.search(r"\b(?:che giorno [eè]|che data [eè]|quanti ne abbiamo|in che giorno siamo)\b", tl):
            return f"📅 Oggi è **{data_it(datetime.date.today())}**."
        return None

    @staticmethod
    def _calcolo(t, tl, memoria):
        m = re.match(r"\s*(?:maik[,!]?\s*)?(?:quanto fa|quanto vale|quanto viene|quant'?[eè]|calcola(?:mi)?|"
                     r"risolvi|fammi il calcolo(?:\s+di)?)\s+(.+?)[\s?!.=]*$", tl)
        if m:
            espr = m.group(1)
        elif re.fullmatch(r"[\d\s.,+\-*/x×÷:()^%=?]+", tl) and re.search(r"\d\s*[-+*/x×÷:^%]\s*\d", tl):
            espr = tl.strip(" =?")
        elif re.match(r"\s*(?:\d+(?:[.,]\d+)?\s*%\s*(?:di|del|della|su)|radice)\b", tl):
            espr = tl.strip(" =?")
        else:
            return None
        v = calcola(espr)
        if v is None:
            return None
        return f"🧮 {espr.strip()} = **{fmt_num(v)}**"

    @staticmethod
    def _caso(t, tl, memoria):
        m = re.search(r"\blancia(?:mi)?\s+(?:(un|il|due|2|tre|3)\s+)?dad[oi]\b", tl)
        if m:
            n = {"due": 2, "2": 2, "tre": 3, "3": 3}.get(m.group(1) or "", 1)
            tiri = [random.randint(1, 6) for _ in range(n)]
            return "🎲 " + " + ".join(map(str, tiri)) + (f" = **{sum(tiri)}**" if n > 1 else "")
        if re.search(r"\b(?:testa o croce|lancia(?:mi)? (?:una|la) moneta)\b", tl):
            return "🪙 " + random.choice(["**Testa!**", "**Croce!**"])
        m = re.search(r"\bnumero\s+(?:casuale|a caso)\s+(?:tra|da|fra)\s+(-?\d+)\s+(?:e|a)\s+(-?\d+)", tl)
        if m:
            a, b = sorted((int(m.group(1)), int(m.group(2))))
            return f"🎲 Il numero è **{random.randint(a, b)}**."
        return None

    @staticmethod
    def _meteo(t, tl, memoria):
        if len(tl.split()) > 9 or not re.search(
                r"\b(?:che tempo fa|com'?[eè] il (?:meteo|tempo)|meteo|previsioni(?: del tempo)?|piove|nevica|"
                r"fa freddo|fa caldo)\b", tl):
            return None
        citta = None
        m = re.search(r"\b(?:a|ad|in|per)\s+([a-zà-ÿ' ]{2,30}?)\s*(?:oggi|domani|adesso|ora)?\s*[?!.]*$", tl)
        if m:
            citta = m.group(1).strip().title()
        citta = citta or memoria.get_valore_profilo("citta") or "Roma"
        d = ottieni_meteo(citta, timeout=5)
        if d.get("errore"):
            return f"🌥️ Non riesco a recuperare il meteo per {citta} in questo momento (sei offline?)."
        testo = (f"{d['emoji']} A **{d['citta']}** ora: **{d['temp']}°C**, {d['descrizione'].lower()} "
                 f"(percepiti {d['percepita']}°). Umidità {d['umidita']}%, vento {d['vento']} km/h.")
        prev = d.get("previsioni") or []
        if len(prev) > 1:
            p = prev[1]
            testo += f"\nDomani: {p['emoji']} {p['min']}° / {p['max']}°."
        return testo

    @staticmethod
    def _briefing(t, tl, memoria):
        if re.search(r"\b(?:briefing|riepilogo (?:della|di) (?:giornata|oggi)|com'?[eè] la mia giornata|"
                     r"cosa ho (?:in programma )?oggi|buongiorno maik)\b", tl):
            return Azioni.briefing(memoria)
        return None

    @staticmethod
    def briefing(memoria, meteo=True):
        ora = datetime.datetime.now()
        nome = memoria.get_valore_profilo("nome")
        saluto = "Buongiorno" if ora.hour < 12 else "Buon pomeriggio" if ora.hour < 18 else "Buonasera"
        righe = [f"{saluto}{' ' + nome if nome else ''}! ☀️ Ecco il tuo briefing.",
                 f"📅 Oggi è **{data_it(ora)}**, sono le {ora.strftime('%H:%M')}."]
        if meteo:
            citta = memoria.get_valore_profilo("citta") or "Roma"
            d = ottieni_meteo(citta, timeout=4)
            if not d.get("errore"):
                righe.append(f"{d['emoji']} A {d['citta']}: {d['temp']}°C, {d['descrizione'].lower()}.")
        oggi = memoria.promemoria_di_oggi()
        if oggi:
            righe.append("⏰ Oggi:\n" + "\n".join(
                f"- {p['testo']} ({p['quando'][11:16]})" for p in oggi[:6]))
        else:
            righe.append("⏰ Nessun promemoria con orario per oggi.")
        senza = [p for p in memoria.promemoria_attivi() if not p.get("quando")]
        if senza:
            righe.append("📌 Da non dimenticare: " + ", ".join(p["testo"] for p in senza[:4]) + ".")
        ob = [o for o in memoria.obiettivi if o.get("stato", "attivo") == "attivo" and o.get("tipo") != "paura"]
        if ob:
            righe.append(f"🎯 Obiettivo da tenere a mente: *{random.choice(ob)['testo']}*")
        lista = [x["testo"] for x in memoria.lista if not x.get("fatto")]
        if lista:
            righe.append(f"🛒 In lista: {', '.join(lista[:6])}{'…' if len(lista) > 6 else ''}")
        u = memoria.ultimo_umore()
        if u and valenza_umore(u.get("umore"), u.get("intensita", 5)) < 4:
            righe.append("💙 L'ultima volta eri un po' giù: oggi andiamo con calma, ci sono io.")
        righe.append("💬 " + random.choice(FRASI_DEL_GIORNO))
        return "\n\n".join(righe)


PROMPT_ESTRAZIONE = """Sei il modulo di memoria di un assistente personale.
Leggi il MESSAGGIO dell'utente ed estrai SOLO informazioni NUOVE, personali e durature su di lui/lei
(nome, età, città, lavoro/studio, gusti, abitudini, persone care con il loro ruolo, obiettivi, eventi importanti).
Ignora saluti, domande generiche, opinioni passeggere e tutto ciò che è già noto.

GIÀ NOTO: {noto}

MESSAGGIO: {messaggio}

Rispondi SOLO con un oggetto JSON con queste chiavi:
{{"profilo": {{"chiave": "valore"}}, "fatti": ["frase breve in terza persona"], "persone": [{{"nome": "...", "ruolo": "..."}}], "obiettivi": ["..."]}}
Se non c'è niente di nuovo usa oggetti e liste vuoti."""

_RE_PERSONALE = re.compile(
    r"\b(?:io|mi|mio|mia|miei|mie|ho|sono|sto|vivo|abito|lavoro|studio|voglio|vorrei|amo|adoro|odio|"
    r"piace|piacciono|preferisco|faccio|mamma|pap[aà]|fratello|sorella|ragazz[oa]|moglie|marito|"
    r"figli[oa]?|amic[oa]|cane|gatto|compleanno|nato|nata)\b", re.I)


# ════════════════════════════════════════════════════════════
# MOTORE AI
# ════════════════════════════════════════════════════════════
class MotoreAI:
    def __init__(self):
        self.memoria  = Memoria()
        self.cervello = Cervello()
        self.appreso_log = []                 # cosa ha imparato l'IA (per i toast della GUI)
        self._ia_lock = threading.Lock()      # una sola estrazione alla volta
        p = self.memoria.ricordi.get("personalita")
        if p in PERSONALITA:
            imposta_personalita(p)

    def _system_prompt(self, query=""):
        ora = datetime.datetime.now()
        oggi = f"{data_it(ora)}, ore {ora.strftime('%H:%M')}"
        return f"""{CONFIG['carattere']}

Oggi è {oggi}.

--- LA TUA MEMORIA DI QUESTA PERSONA ---
{self.memoria.costruisci_contesto(query)}
--- FINE MEMORIA ---

Usa questa memoria con naturalezza, senza elencarla meccanicamente.
Se noti che la persona è di umore negativo, sii empatico e presente.
Se ha obiettivi o sogni, tienili a mente e incoraggiala.
Sai anche fare azioni pratiche quando te le chiedono con frasi come «metti un timer di 10 minuti»,
«ricordami alle 18 di…», «aggiungi latte alla lista», «quanto fa 15% di 80», «che ore sono a Tokyo»,
«briefing». Se te le chiedono in modo vago, suggerisci la frase giusta. Non dire mai di aver
impostato qualcosa se non è successo davvero."""

    def _impara_con_ia(self, testo):
        """Estrazione di fatti con il modello (JSON). Gira in background dopo la risposta."""
        if not CONFIG["apprendimento_ia"] or len(testo.split()) < 4 or not _RE_PERSONALE.search(testo):
            return []
        if not self._ia_lock.acquire(blocking=False):
            return []
        try:
            dati = self.cervello.pensa_json(PROMPT_ESTRAZIONE.format(noto=self.memoria.gia_noto(),
                                                                     messaggio=testo[:800]))
            appreso = self.memoria.impara_da_ia(dati) if dati else []
            if appreso:
                self.appreso_log.append({"ts": time.time(), "cosa": ", ".join(appreso[:3])})
                self.appreso_log = self.appreso_log[-30:]
            return appreso
        finally:
            self._ia_lock.release()

    def _dopo_risposta(self, testo):
        self._forse_riassumi()
        self._impara_con_ia(testo)

    def briefing(self, auto=False):
        oggi = datetime.date.today().isoformat()
        if auto and (self.memoria.ricordi.get("ultimo_briefing") == oggi
                     or (not self.memoria.numero_scambi() and not self.memoria.profilo)):
            return None                       # già fatto oggi, o primo incontro
        self.memoria.imposta_ricordo("ultimo_briefing", oggi)
        return Azioni.briefing(self.memoria)

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
            nuovo = pulisci_pensiero(self.cervello.pensa("Riassumi.", [{"role": "user", "content": prompt}]))
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

    def _meta(self, **extra):
        return dict(giorni=self.memoria.ricordi.get("giorni_insieme", 1),
                    scambi=self.memoria.numero_scambi(), **extra)

    def rispondi(self, testo):
        """Risposta classica (completa). Mantenuta per compatibilità."""
        cmd = self._gestisci_comando(testo)
        if cmd:
            return cmd
        azione = Azioni.prova(testo, self.memoria)
        if azione:
            self.memoria.salva_scambio(testo, azione)
            return self._meta(ok=True, risposta=azione, azione=True)
        imparato = Estrattore.analizza(testo, self.memoria)
        risposta = self.cervello.pensa(self._system_prompt(testo), self._costruisci_messaggi(testo))
        if risposta.startswith("__ERRORE"):
            return {"ok": False, "risposta": "Ollama non risponde. Controlla che sia acceso."}
        self.memoria.salva_scambio(testo, pulisci_pensiero(risposta) or risposta)
        threading.Thread(target=self._dopo_risposta, args=(testo,), daemon=True).start()
        return self._meta(ok=True, risposta=risposta, imparato=imparato)

    def rispondi_stream(self, testo, on_token):
        """Versione in streaming: chiama on_token(chunk) e ritorna i metadati finali."""
        cmd = self._gestisci_comando(testo)
        if cmd:
            return {"done": True, "comando": cmd}
        azione = Azioni.prova(testo, self.memoria)   # azioni pratiche: istantanee, anche offline
        if azione:
            on_token(azione)
            self.memoria.salva_scambio(testo, azione)
            return self._meta(done=True, ok=True, azione=True)
        imparato = Estrattore.analizza(testo, self.memoria)
        risposta = self.cervello.pensa_stream(self._system_prompt(testo), self._costruisci_messaggi(testo), on_token)
        if not risposta or risposta.startswith("__ERRORE"):
            return {"done": True, "ok": False,
                    "risposta": "Ollama non risponde. Controlla che sia acceso."}
        # in memoria va la risposta senza il "ragionamento" <think> (risparmia contesto)
        self.memoria.salva_scambio(testo, pulisci_pensiero(risposta) or risposta)
        threading.Thread(target=self._dopo_risposta, args=(testo,), daemon=True).start()
        return self._meta(done=True, ok=True, imparato=imparato)

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
            "personalita": CONFIG["personalita"],
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
                            "modello_visione": CONFIG["modello_visione"],
                            "modelli": MOTORE.cervello.modelli(), "carattere": CONFIG["carattere"],
                            "ollama": CONFIG["ollama_base"],
                            "apprendimento_ia": CONFIG["apprendimento_ia"],
                            "personalita": CONFIG["personalita"],
                            "personalita_disponibili": [{"chiave": k, "emoji": v[0], "nome": v[1]}
                                                        for k, v in PERSONALITA.items()]})
            elif base == "/promemoria":
                self._json({"promemoria": MOTORE.memoria.promemoria_attivi()})
            elif base == "/promemoria/scaduti":
                self._json({"scaduti": MOTORE.memoria.promemoria_scaduti()})
            elif base == "/lista":
                self._json({"lista": MOTORE.memoria.lista})
            elif base == "/briefing":
                self._json({"testo": MOTORE.briefing(auto=qs.get("auto") == "1")})
            elif base == "/appreso":
                try:
                    dopo = float(qs.get("dopo", "0"))
                except ValueError:
                    dopo = 0.0
                self._json({"appreso": [x for x in MOTORE.appreso_log if x["ts"] > dopo], "ora": time.time()})
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

            elif base == "/personalita":
                k = self._read_json_body().get("chiave", "").strip()
                ok = imposta_personalita(k, MOTORE.memoria)
                self._json({"ok": ok, "personalita": CONFIG["personalita"],
                            "nome": PERSONALITA[k][1] if ok else "", "emoji": PERSONALITA[k][0] if ok else ""})

            elif base == "/lista":
                c = self._read_json_body()
                try:
                    indice = int(c.get("indice", -1))
                except (TypeError, ValueError):
                    indice = -1
                ok = MOTORE.memoria.lista_modifica(c.get("azione", ""), indice, str(c.get("testo", "")))
                self._json({"ok": ok, "lista": MOTORE.memoria.lista})

            elif base == "/promemoria/completa":
                n = MOTORE.memoria.chiudi_promemoria(self._read_json_body().get("id", ""))
                self._json({"ok": bool(n)})

            elif base == "/vedi":
                c = self._read_json_body()
                img = c.get("immagine", "")
                if "," in img:                       # togli il prefisso data:image/...;base64,
                    img = img.split(",", 1)[1]
                if not img:
                    self._json({"ok": False, "errore": "nessuna immagine"}); return
                testo = MOTORE.cervello.vedi(img, c.get("prompt", "").strip())
                if testo.startswith("__ERRORE"):
                    low = testo.lower()
                    if "mllama" in low or "architecture" in low:
                        msg = ("Il tuo Ollama è troppo vecchio per llama3.2-vision (errore 'mllama'). "
                               "Soluzione veloce:  ollama pull llava   —  oppure aggiorna Ollama "
                               "all'ultima versione da https://ollama.com/download")
                    elif "not found" in low:
                        msg = "Nessun modello visione installato. Esegui:  ollama pull llava"
                    else:
                        msg = "Modello visione non raggiungibile. Prova:  ollama pull llava"
                    self._json({"ok": False, "errore": msg})
                else:
                    self._json({"ok": True, "testo": testo})

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
# GUI integrata di riserva (usata solo se manca aria.html):
# sfera 3D animata + chat in streaming + pannello strumenti, collegata
# agli endpoint del server (memoria su disco).
GUI_FALLBACK = r"""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>MAIK // Server</title>
<style>
  :root{--cyan:#00f5ff;--bg:#050a0f;--bg2:#080d14;--panel:rgba(8,20,35,.92);--border:rgba(0,245,255,.18);--text:#c8e8f0;--dim:#5a7a8a;--green:#00ff88;--red:#ff3355;--purple:#a855f7;}
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--text);font-family:'Rajdhani',system-ui,Segoe UI,sans-serif;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
  header{display:flex;align-items:center;gap:12px;padding:0 14px;height:48px;border-bottom:1px solid var(--border);font-size:13px;flex-shrink:0}
  .logo{font-weight:800;letter-spacing:5px;font-family:'Orbitron',monospace;white-space:nowrap}.logo span{color:var(--cyan)}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--red);box-shadow:0 0 8px var(--red)}.dot.on{background:var(--green);box-shadow:0 0 8px var(--green)}.dot.busy{background:var(--purple);box-shadow:0 0 8px var(--purple)}
  .hbtn{background:transparent;border:1px solid var(--border);color:var(--cyan);padding:5px 9px;border-radius:4px;cursor:pointer;font-family:'Share Tech Mono',monospace;font-size:11px;white-space:nowrap}
  .hbtn:hover{background:rgba(0,245,255,.12)}.hbtn.on{background:rgba(0,255,136,.15);border-color:var(--green);color:var(--green)}
  #wrap{flex:1;display:flex;overflow:hidden}
  #side{width:250px;border-right:1px solid var(--border);padding:14px;overflow:auto;font-size:13px;background:var(--panel);flex-shrink:0;transition:width .25s}
  #side.hidden{width:0;padding:0;overflow:hidden}
  #side h3{font-size:10px;letter-spacing:2px;color:var(--cyan);margin:16px 0 6px;text-transform:uppercase}
  #side h3:first-child{margin-top:0}
  .kv{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(0,245,255,.06);gap:8px}
  .kv span:last-child{color:#fff;text-align:right}
  .sfield{width:100%;background:rgba(0,245,255,.05);border:1px solid var(--border);border-radius:4px;padding:7px 10px;color:var(--text);font-size:13px;outline:none;font-family:inherit}
  .sfield:focus{border-color:var(--cyan)}
  .memhit{background:rgba(0,245,255,.05);border-left:2px solid var(--cyan);padding:4px 8px;font-size:11px;border-radius:0 4px 4px 0;margin-top:4px}
  #main{flex:1;display:flex;flex-direction:column;overflow:hidden}
  #sphere-area{flex:1;position:relative;overflow:hidden;min-height:120px}
  #sphere-wrap{position:absolute;cursor:grab;user-select:none;touch-action:none}
  #fbadge{display:none;position:absolute;top:10px;left:50%;transform:translateX(-50%);align-items:center;gap:7px;background:rgba(5,10,20,.85);border:1px solid var(--green);color:var(--green);padding:4px 12px;border-radius:14px;z-index:30;font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;box-shadow:0 0 16px rgba(0,255,136,.25)}
  .fbdot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pl 1.5s infinite}@keyframes pl{0%,100%{opacity:1}50%{opacity:.4}}
  #cambox{display:none;position:absolute;top:10px;right:10px;width:160px;aspect-ratio:4/3;border-radius:8px;overflow:hidden;border:1px solid var(--border);z-index:30;background:#000}
  #cambox video{width:100%;height:100%;object-fit:cover}
  #fstat{position:absolute;bottom:0;left:0;right:0;background:rgba(5,10,20,.8);padding:2px 6px;font-size:9px;font-family:'Share Tech Mono',monospace;color:var(--dim);letter-spacing:1px}
  #msgs{height:54%;overflow:auto;padding:16px;display:flex;flex-direction:column;gap:11px;border-top:1px solid var(--border)}
  .m{max-width:80%;padding:10px 14px;border-radius:10px;line-height:1.5;white-space:pre-wrap;word-break:break-word;animation:in .2s ease}
  @keyframes in{from{opacity:0;transform:translateY(5px)}to{opacity:1}}
  .m.ai{align-self:flex-start;background:rgba(0,245,255,.07);border:1px solid rgba(0,245,255,.2);border-radius:4px 12px 12px 12px}
  .m.me{align-self:flex-end;background:rgba(0,245,255,.14);color:#fff;border-radius:12px 4px 12px 12px}
  #bar{display:flex;gap:8px;padding:11px 12px;border-top:1px solid var(--border);flex-shrink:0;align-items:center}
  .micbtn{background:rgba(0,245,255,.06);border:1px solid var(--border);color:var(--cyan);width:42px;height:42px;border-radius:50%;font-size:15px;cursor:pointer;flex-shrink:0}
  .micbtn.on{background:rgba(255,51,85,.15);border-color:var(--red);color:var(--red)}
  #inp{flex:1;background:rgba(0,245,255,.05);border:1px solid var(--border);border-radius:20px;padding:11px 16px;color:#fff;font-size:14px;outline:none;font-family:inherit;min-width:0}
  #inp:focus{border-color:var(--cyan)}
  .send{background:var(--cyan);border:none;color:#050a0f;width:44px;height:44px;border-radius:50%;font-size:16px;cursor:pointer;font-weight:700;flex-shrink:0}
  .send:disabled{opacity:.4}
  .quick{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 10px}
  .quick button{background:transparent;border:1px solid rgba(0,245,255,.2);color:var(--dim);padding:4px 10px;border-radius:12px;font-size:12px;cursor:pointer;font-family:inherit}
  .quick button:hover{color:var(--cyan);border-color:var(--cyan)}
  .cursor{display:inline-block;width:7px;height:14px;background:var(--cyan);vertical-align:middle;animation:bl 1s infinite}@keyframes bl{50%{opacity:.3}}
  .note{color:var(--dim);font-size:11px;margin-top:14px;line-height:1.5}
  .ov{position:fixed;inset:0;background:rgba(2,6,12,.8);backdrop-filter:blur(4px);z-index:1000;display:none;align-items:center;justify-content:center;padding:16px}
  .ov.open{display:flex}
  .mod{background:var(--bg2);border:1px solid var(--border);border-radius:8px;width:100%;max-width:470px;max-height:88vh;overflow:auto}
  .modh{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg2)}
  .modt{font-family:'Orbitron',monospace;font-size:13px;letter-spacing:2px;color:#fff}
  .ib{background:rgba(0,245,255,.08);border:1px solid var(--border);color:var(--cyan);width:28px;height:28px;border-radius:4px;cursor:pointer}
  .modb{padding:16px}
  .tgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .tcard{background:rgba(0,245,255,.05);border:1px solid var(--border);border-radius:8px;padding:14px 8px;text-align:center;cursor:pointer;transition:.15s;display:flex;flex-direction:column;align-items:center;gap:6px}
  .tcard:hover{background:rgba(0,245,255,.12);border-color:var(--cyan);transform:translateY(-2px)}
  .tcard .ic{font-size:25px}.tcard .nm{font-size:11px}
  #tpanel h4{font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:2px;color:var(--cyan);margin-bottom:10px;text-transform:uppercase}
  .tout{background:rgba(0,0,0,.35);border:1px solid var(--border);border-radius:6px;padding:12px;font-family:'Share Tech Mono',monospace;color:var(--cyan);margin-top:10px;word-break:break-word;min-height:20px;font-size:14px}
  .tbig{font-family:'Orbitron',monospace;font-size:30px;color:#fff;text-align:center;letter-spacing:1px}
  .trow{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
  .tbtn{flex:1;min-width:64px;background:rgba(0,245,255,.08);border:1px solid var(--border);color:var(--cyan);padding:9px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:13px;font-weight:600}
  .tbtn:hover{background:rgba(0,245,255,.15)}.tbtn.solid{background:var(--cyan);color:#050a0f;border:none}
  .tfield{width:100%;background:rgba(0,245,255,.05);border:1px solid var(--border);border-radius:6px;padding:9px 11px;color:var(--text);font-size:14px;font-family:inherit;outline:none;margin-top:8px}
  .tfield:focus{border-color:var(--cyan)}
  .cg{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}
  .cg button{background:rgba(0,245,255,.06);border:1px solid var(--border);color:var(--text);padding:12px 0;border-radius:6px;cursor:pointer;font-size:16px;font-family:inherit}
  .cg button:hover{background:rgba(0,245,255,.12)}.cg button.op{color:var(--cyan)}.cg button.eq{background:var(--cyan);color:#050a0f;grid-column:span 2}.cg button.s2{grid-column:span 2}
  .crow{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(0,245,255,.07)}.crow .c{color:var(--dim)}.crow .t{font-family:'Orbitron',monospace;color:#fff}
  .nitem{background:rgba(0,245,255,.04);border-left:2px solid var(--cyan);padding:7px 9px;border-radius:0 6px 6px 0;margin-top:6px;font-size:13px;display:flex;justify-content:space-between;gap:8px}
  .nx{background:none;border:none;color:var(--dim);cursor:pointer}.nx:hover{color:var(--red)}
  #toast{position:fixed;top:58px;right:16px;z-index:2000;display:flex;flex-direction:column;gap:6px}
  .tst{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--cyan);padding:8px 14px;border-radius:4px;font-size:12px;max-width:280px}
  .tst.ok{border-left-color:var(--green)}.tst.err{border-left-color:var(--red)}
  .m.ai{white-space:normal}.m b{color:#fff}.m ul{margin:4px 0 4px 18px}.m li{margin:2px 0}
  .m code{background:rgba(0,245,255,.1);padding:1px 5px;border-radius:3px;font-family:'Share Tech Mono',monospace;font-size:.92em}
  .think{background:rgba(168,85,247,.08);border:1px solid rgba(168,85,247,.3);border-radius:6px;padding:4px 8px;margin-bottom:6px;font-size:12px;color:#b9a3d9}
  .think summary{cursor:pointer;color:var(--purple);font-family:'Share Tech Mono',monospace;letter-spacing:1px}
  .think div{white-space:pre-wrap;margin-top:4px;max-height:180px;overflow:auto}
  .m.alarm{border-color:var(--green)!important;box-shadow:0 0 18px rgba(0,255,136,.25);animation:ring .25s ease 6}
  @keyframes ring{0%,100%{transform:translateX(0)}25%{transform:translateX(-3px)}75%{transform:translateX(3px)}}
  .pchips{display:flex;flex-wrap:wrap;gap:5px}
  .pchip{background:rgba(0,245,255,.05);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:12px;font-size:11px;cursor:pointer;font-family:inherit}
  .pchip:hover{border-color:var(--cyan)}.pchip.on{background:rgba(0,245,255,.18);border-color:var(--cyan);color:#fff}
  .pr{display:flex;justify-content:space-between;gap:6px;align-items:flex-start;padding:5px 0;border-bottom:1px solid rgba(0,245,255,.06);font-size:12px}
  .pr small{display:block;color:var(--dim);font-size:10px}
  @media(max-width:480px){header{padding:0 10px;gap:8px}.logo span,#stato,.hx{display:none}.hbtn{padding:5px 7px}}
  header>div:last-child{flex-shrink:0}
  @media(max-width:760px){#side{position:absolute;top:48px;bottom:0;left:0;z-index:200;box-shadow:4px 0 20px rgba(0,0,0,.5)}.tgrid{grid-template-columns:repeat(2,1fr)}.logo{font-size:11px;letter-spacing:3px}}
</style></head>
<body>
<header>
  <div class="logo">M A I K <span>// V8</span></div>
  <span class="dot" id="dot"></span><span id="stato">verifico…</span>
  <div style="margin-left:auto;display:flex;gap:6px">
    <button class="hbtn" id="fbtn" onclick="toggleFriend()" title="Modalità Amico">🫂<span class="hx"> AMICO</span></button>
    <button class="hbtn" onclick="guarda()" title="MAIK guarda dalla webcam">👁️</button>
    <button class="hbtn" onclick="openTools()">🧰</button>
    <button class="hbtn" onclick="toggleSide()">≡</button>
  </div>
</header>
<div id="toast"></div>
<div id="wrap">
  <div id="side">
    <h3>Stato</h3>
    <div class="kv"><span>Modello</span><span id="s-mod">—</span></div>
    <div class="kv"><span>Visione</span><span id="s-vis">—</span></div>
    <div class="kv"><span>Giorni</span><span id="s-gg">—</span></div>
    <div class="kv"><span>Scambi</span><span id="s-sc">—</span></div>
    <div class="kv"><span>Utente</span><span id="s-ut">—</span></div>
    <h3>🎭 Personalità</h3>
    <div class="pchips" id="pers"></div>
    <h3>⏰ Promemoria</h3>
    <div id="prlist"><div class="note" style="margin:0">—</div></div>
    <h3>💙 Umore</h3>
    <div id="moodc"></div>
    <h3>Profilo</h3>
    <div id="profilo" style="color:var(--dim)">—</div>
    <h3>Cerca nella memoria</h3>
    <input class="sfield" id="memq" placeholder="Cerca un ricordo..." oninput="cercaMem()">
    <div id="memres"></div>
    <div class="note">Memoria su disco. MAIK impara da solo mentre parlate 🧠 · scrivi <b>aiuto</b> per vedere le azioni (timer, promemoria, lista, calcoli…). <b>🫂 AMICO</b>: ti vede e ti parla. <b>👁️</b>: guarda la webcam.</div>
  </div>
  <div id="main">
    <div id="sphere-area">
      <div id="fbadge"><span class="fbdot"></span> MAIK · MODALITÀ AMICO</div>
      <div id="cambox"><video id="cam" autoplay muted playsinline></video><div id="fstat">webcam</div></div>
      <div id="sphere-wrap"><canvas id="sph" width="200" height="200"></canvas></div>
    </div>
    <div id="msgs"></div>
    <div class="quick">
      <button onclick="qs('briefing')">☀️ briefing</button>
      <button onclick="q('Metti un timer di 5 minuti')">⏱️ timer</button>
      <button onclick="q('Ricordami alle 18 di ')">⏰ ricordami…</button>
      <button onclick="qs('Cosa c\'è nella lista?')">🛒 lista</button>
      <button onclick="guarda()">👁️ guardami</button>
      <button onclick="q('Mi chiamo ')">mi chiamo…</button>
      <button onclick="qs('aiuto')">❓ aiuto</button>
    </div>
    <div id="bar">
      <button class="micbtn" id="mic" onclick="toggleMic()" title="Voce">🎤</button>
      <input id="inp" placeholder="Scrivi a Maik…" onkeydown="if(event.key==='Enter')invia()">
      <button class="send" id="send" onclick="invia()">➤</button>
    </div>
  </div>
</div>

<div class="ov" id="tmodal">
  <div class="mod">
    <div class="modh">
      <div class="modt" id="ttitle">🧰 STRUMENTI</div>
      <div style="display:flex;gap:6px">
        <button class="ib" id="tback" onclick="toolsHome()" style="display:none">←</button>
        <button class="ib" onclick="closeTools()">✕</button>
      </div>
    </div>
    <div class="modb"><div id="tgrid" class="tgrid"></div><div id="tpanel" style="display:none"></div></div>
  </div>
</div>

<script>
const $=s=>document.querySelector(s);
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function toast(m,t){const d=document.createElement('div');d.className='tst '+(t||'');d.textContent=m;$('#toast').appendChild(d);setTimeout(()=>d.remove(),3000);}
function q(t){$('#inp').value=t;$('#inp').focus();}
function qs(t){$('#inp').value=t;invia();}
function toggleSide(){$('#side').classList.toggle('hidden');}
let pName='';

// ---------- MARKDOWN + RAGIONAMENTO (<think>) ----------
function md(s){
  s=esc(s||'');
  s=s.replace(/`([^`\n]+)`/g,'<code>$1</code>');
  s=s.replace(/\*\*([^*\n]+)\*\*/g,'<b>$1</b>');
  s=s.replace(/(^|[^*])\*([^*\n]+)\*/g,'$1<i>$2</i>');
  s=s.replace(/(?:^|\n)((?:- .+(?:\n|$))+)/g,(m,l)=>'\n<ul>'+l.trim().split('\n').map(x=>'<li>'+x.replace(/^- /,'')+'</li>').join('')+'</ul>');
  return s.replace(/\n/g,'<br>').replace(/<br><ul>/g,'<ul>').replace(/<\/ul><br>/g,'</ul>');
}
function splitThink(t){const m=(t||'').match(/<think>([\s\S]*?)(<\/think>|$)/i);if(!m)return{think:'',ans:t||'',open:false};return{think:m[1].trim(),ans:m[2]?t.replace(m[0],'').trim():'',open:!m[2]};}
function stripThink(t){return /<think>/i.test(t||'')?splitThink(t).ans:(t||'');}
function renderAI(t){
  if(!/<think>/i.test(t||''))return md(t);
  const s=splitThink(t);
  return '<details class="think"'+(s.open?' open':'')+'><summary>💭 '+(s.open?'Sto ragionando…':'Ragionamento')+'</summary><div>'+esc(s.think)+'</div></details>'+md(s.ans);
}

// ---------- PERSONALITÀ ----------
let PERS=[],persCur='amico';
function renderPers(){$('#pers').innerHTML=PERS.map(p=>'<button class="pchip'+(p.chiave===persCur?' on':'')+'" onclick="setPers(\''+p.chiave+'\')">'+p.emoji+' '+p.nome+'</button>').join('');}
async function setPers(k){try{const r=await (await fetch('/personalita',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chiave:k})})).json();if(r.ok){persCur=k;renderPers();toast(r.emoji+' Modalità '+r.nome,'ok');}}catch(e){}}

// ---------- UMORE (grafico) ----------
function drawMood(arr){
  const el=$('#moodc');if(!el)return;
  if(!arr||arr.length<2){el.innerHTML='<div class="note" style="margin:0">Parlami di come stai: qui vedrai il tuo andamento 💙</div>';return;}
  const W=220,H=56,n=arr.length,pts=arr.map((u,i)=>[(i/(n-1))*(W-8)+4,H-4-(u.v/10)*(H-8)]);
  const last=arr[n-1],col=last.v>=6?'var(--green)':last.v>=4?'var(--cyan)':'#5a9bd4';
  el.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" width="100%" height="'+H+'"><line x1="4" x2="'+(W-4)+'" y1="'+(H/2)+'" y2="'+(H/2)+'" stroke="rgba(0,245,255,.15)" stroke-dasharray="3 3"/><polyline points="'+pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')+'" fill="none" stroke="'+col+'" stroke-width="2" stroke-linejoin="round"/>'+pts.map(p=>'<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="2.2" fill="'+col+'"/>').join('')+'</svg><div class="note" style="margin:2px 0 0">Ultimo: <b>'+esc(last.umore||'')+'</b></div>';
}

// ---------- PROMEMORIA + ALLARMI ----------
function fmtQ(iso){const d=new Date(iso),o=new Date(),hh=d.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'});if(d.toDateString()===o.toDateString())return 'oggi '+hh;const dm=new Date(o);dm.setDate(o.getDate()+1);if(d.toDateString()===dm.toDateString())return 'domani '+hh;return d.toLocaleDateString('it-IT',{weekday:'short',day:'numeric',month:'short'})+' '+hh;}
async function loadPr(){try{const r=await (await fetch('/promemoria')).json();const a=r.promemoria||[];$('#prlist').innerHTML=a.length?a.slice(0,8).map(p=>'<div class="pr"><span>'+(p.tipo==='timer'?'⏱️ ':'⏰ ')+esc(p.testo)+(p.quando?'<small>'+fmtQ(p.quando)+'</small>':'<small>senza orario</small>')+'</span><button class="nx" onclick="prDone(\''+p.id+'\')" title="Fatto">✓</button></div>').join(''):'<div class="note" style="margin:0">Nessun promemoria</div>';}catch(e){}}
async function prDone(id){try{await fetch('/promemoria/completa',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});}catch(e){}loadPr();}
function notify(t,b){try{if('Notification' in window&&Notification.permission==='granted')new Notification(t,{body:b});}catch(e){}}
function askNotify(){try{if('Notification' in window&&Notification.permission==='default')Notification.requestPermission();}catch(e){}}
function fireAlarm(p){
  const msg=p.tipo==='timer'?'⏱️ '+p.testo+': tempo scaduto!':'⏰ Promemoria: **'+p.testo+'**';
  add('ai',msg,'alarm');beep(3);toast(msg.replace(/\*\*/g,''),'ok');notify('MAIK',msg.replace(/\*\*/g,''));
  const was=ttsOn;ttsOn=true;say(msg);ttsOn=was;
}
async function checkScaduti(){try{const r=await (await fetch('/promemoria/scaduti')).json();const s=r.scaduti||[];s.forEach(fireAlarm);if(s.length)loadPr();}catch(e){}}

// ---------- COSA HA IMPARATO L'IA ----------
let lastLearn=0;
async function checkLearn(){try{const r=await (await fetch('/appreso?dopo='+lastLearn)).json();const a=r.appreso||[];if(lastLearn)a.forEach(x=>toast('🧠 Ho capito: '+x.cosa,'ok'));lastLearn=r.ora||lastLearn;if(a.length)profilo();}catch(e){}}

// ---------- STATO / PROFILO / MEMORIA ----------
async function stato(){
  try{const s=await (await fetch('/stato')).json();
    $('#dot').className='dot'+(s.online?' on':'');
    $('#stato').textContent=s.online?'ollama online':'ollama offline';
    $('#s-mod').textContent=s.modello;$('#s-gg').textContent=s.giorni;$('#s-sc').textContent=s.scambi;$('#s-ut').textContent=s.nome_utente||'—';
    pName=s.nome_utente||'';
    if(s.personalita&&s.personalita!==persCur){persCur=s.personalita;renderPers();}
  }catch(e){$('#stato').textContent='server non raggiungibile';}
}
async function cfg(){try{const c=await (await fetch('/config')).json();$('#s-vis').textContent=c.modello_visione||'—';PERS=c.personalita_disponibili||[];persCur=c.personalita||'amico';renderPers();}catch(e){}}
async function profilo(){
  try{const s=await (await fetch('/statistiche')).json();const p=s.profilo||{};const k=Object.keys(p);
    $('#profilo').innerHTML=k.length?k.map(x=>`<div class="kv"><span>${esc(x)}</span><span>${esc(String(p[x]))}</span></div>`).join(''):'nessun dato ancora';
    drawMood(s.umore_grafico);
  }catch(e){}
}
let memT;
function cercaMem(){clearTimeout(memT);memT=setTimeout(async()=>{
  const v=$('#memq').value.trim();const box=$('#memres');
  if(!v){box.innerHTML='';return;}
  try{const r=await (await fetch('/cerca?q='+encodeURIComponent(v))).json();const h=r.risultati||[];
    box.innerHTML=h.length?h.slice(0,8).map(x=>`<div class="memhit">${esc(JSON.stringify(x).slice(0,90))}</div>`).join(''):'<div class="note">Nessun ricordo</div>';
  }catch(e){}
},250);}

// ---------- CHAT (streaming SSE) ----------
function add(role,txt,extra){const d=document.createElement('div');d.className='m '+role+(extra?' '+extra:'');if(role==='ai')d.innerHTML=renderAI(txt);else d.textContent=txt;$('#msgs').appendChild(d);$('#msgs').scrollTop=1e9;return d;}
let busy=false;
async function invia(){
  const t=$('#inp').value.trim();if(!t||busy)return;
  $('#inp').value='';$('#send').disabled=true;busy=true;lastAct=Date.now();
  if(/ricordami|avvisami|timer|sveglia|svegliami|promemoria/i.test(t))askNotify();
  add('me',t);
  SPH.state='thinking';$('#dot').className='dot busy';
  const bubble=add('ai','');bubble.innerHTML='<span class="cursor"></span>';
  let full='';
  try{
    const resp=await fetch('/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({testo:t})});
    const reader=resp.body.getReader();const dec=new TextDecoder();let buf='';
    while(true){
      const {done,value}=await reader.read();if(done)break;
      buf+=dec.decode(value,{stream:true});let i;
      while((i=buf.indexOf('\n\n'))>=0){
        const line=buf.slice(0,i).trim();buf=buf.slice(i+2);
        if(!line.startsWith('data:'))continue;
        let obj;try{obj=JSON.parse(line.slice(5).trim());}catch(e){continue;}
        if(obj.t){full+=obj.t;SPH.state=splitThink(full).open?'thinking':'speaking';bubble.innerHTML=renderAI(full)+'<span class="cursor"></span>';$('#msgs').scrollTop=1e9;}
        if(obj.done){
          if(obj.comando){bubble.textContent='['+obj.comando.tipo+'] '+JSON.stringify(obj.comando).slice(0,500);}
          else if(obj.ok===false){bubble.textContent=obj.risposta||'Errore.';}
          else{
            bubble.innerHTML=renderAI(full);say(full);
            if(obj.imparato)toast('💡 Ho imparato: '+obj.imparato,'ok');
            if(obj.azione){loadPr();}else{setTimeout(checkLearn,4000);setTimeout(checkLearn,12000);}
          }
          stato();profilo();
        }
      }
    }
  }catch(e){bubble.textContent='Errore di connessione: '+e.message;}
  SPH.state='idle';$('#dot').className='dot on';busy=false;$('#send').disabled=false;
  if(!friend)$('#inp').focus();
}

// ---------- SFERA 3D ----------
const cv=$('#sph'),cx=cv.getContext('2d'),wrap=$('#sphere-wrap'),area=$('#sphere-area');
const SPH={size:200,x:0,y:0,vx:.7,vy:.45,t:0,rx:.5,ry:0,state:'idle',drag:false,ox:0,oy:0,nodes:[]};
function buildNodes(n){SPH.nodes=[];const inc=Math.PI*(3-Math.sqrt(5));for(let i=0;i<n;i++){const y=1-(i/(n-1))*2,r=Math.sqrt(Math.max(0,1-y*y)),p=i*inc;SPH.nodes.push({x:Math.cos(p)*r,y,z:Math.sin(p)*r});}}
function sphSize(){const a=area.getBoundingClientRect();let s=Math.round(Math.min(a.width*.6,a.height*.7));if(!s||s<0)s=180;SPH.size=Math.max(120,Math.min(240,s));cv.width=SPH.size;cv.height=SPH.size;cv.style.width=SPH.size+'px';cv.style.height=SPH.size+'px';}
function sphInit(){buildNodes(130);sphSize();const a=area.getBoundingClientRect();SPH.x=Math.max(8,(a.width-SPH.size)/2);SPH.y=Math.max(8,(a.height-SPH.size)/2);sphPos();}
function sphPos(){wrap.style.left=SPH.x+'px';wrap.style.top=SPH.y+'px';}
function sphLoop(){
  SPH.t+=.02;const a=area.getBoundingClientRect();const mx=a.width-SPH.size,my=a.height-SPH.size;
  if(!SPH.drag&&mx>4&&my>4){SPH.x+=SPH.vx;SPH.y+=SPH.vy;if(SPH.x<=0||SPH.x>=mx){SPH.vx*=-1;SPH.x=Math.max(0,Math.min(mx,SPH.x));}if(SPH.y<=0||SPH.y>=my){SPH.vy*=-1;SPH.y=Math.max(0,Math.min(my,SPH.y));}sphPos();}
  sphDraw();requestAnimationFrame(sphLoop);
}
function sphDraw(){
  const w=cv.width,h=cv.height,c=w/2,m=h/2,R=w*.40,k=w/200;cx.clearRect(0,0,w,h);
  let cr=0,cg=245,cb=255,sp=.006,pa=0;
  if(SPH.state==='thinking'){cr=168;cg=85;cb=247;sp=.020;}
  else if(SPH.state==='speaking'){sp=.013;pa=.10;}
  else if(SPH.state==='detecting'){cr=0;cg=255;cb=136;sp=.011;}
  SPH.ry+=sp;SPH.rx+=sp*.35;
  const br=1+Math.sin(SPH.t*2)*.02+(SPH.state==='speaking'?Math.abs(Math.sin(SPH.t*9))*pa:0);
  const gR=R*1.55,g=cx.createRadialGradient(c,m,R*.35,c,m,gR);
  g.addColorStop(0,'rgba('+cr+','+cg+','+cb+','+(.18+Math.sin(SPH.t*2)*.06)+')');g.addColorStop(1,'rgba('+cr+','+cg+','+cb+',0)');
  cx.beginPath();cx.arc(c,m,gR,0,Math.PI*2);cx.fillStyle=g;cx.fill();
  const cosY=Math.cos(SPH.ry),sinY=Math.sin(SPH.ry),cosX=Math.cos(SPH.rx),sinX=Math.sin(SPH.rx);
  const pts=new Array(SPH.nodes.length);
  for(let i=0;i<SPH.nodes.length;i++){const p=SPH.nodes[i];let x=p.x*cosY-p.z*sinY;let z=p.x*sinY+p.z*cosY;let y=p.y*cosX-z*sinX;z=p.y*sinX+z*cosX;const pe=1/(1.8-z);pts[i]={sx:c+x*R*pe*br,sy:m+y*R*pe*br,z};}
  cx.beginPath();for(let i=0;i<pts.length;i++){if(i===0)cx.moveTo(pts[i].sx,pts[i].sy);else cx.lineTo(pts[i].sx,pts[i].sy);}cx.strokeStyle='rgba('+cr+','+cg+','+cb+',.10)';cx.lineWidth=.6;cx.stroke();
  const ord=pts.slice().sort((a,b)=>a.z-b.z);
  for(const p of ord){const d=(p.z+1)/2,sz=(.5+d*1.9)*k,al=.22+d*.68;cx.beginPath();cx.arc(p.sx,p.sy,sz,0,Math.PI*2);cx.fillStyle='rgba('+(Math.min(255,cr+70*d)|0)+','+(Math.min(255,cg+70*d)|0)+','+(Math.min(255,cb+70*d)|0)+','+al+')';cx.fill();}
  const coR=(7+Math.sin(SPH.t*4)*3)*k,co=cx.createRadialGradient(c,m,0,c,m,coR*2.4);
  co.addColorStop(0,'rgba(255,255,255,.95)');co.addColorStop(.4,'rgba('+cr+','+cg+','+cb+',.7)');co.addColorStop(1,'rgba(0,0,0,0)');
  cx.beginPath();cx.arc(c,m,coR*2.4,0,Math.PI*2);cx.fillStyle=co;cx.fill();
  if(SPH.state==='speaking'){const rr=R*1.08;for(let i=0;i<16;i++){const an=(i/16)*Math.PI*2,bh=(7+Math.abs(Math.sin(SPH.t*9+i))*14)*k;cx.beginPath();cx.moveTo(c+Math.cos(an)*rr,m+Math.sin(an)*rr);cx.lineTo(c+Math.cos(an)*(rr+bh),m+Math.sin(an)*(rr+bh));cx.strokeStyle='rgba('+cr+','+cg+','+cb+',.7)';cx.lineWidth=2;cx.stroke();}}
}
wrap.addEventListener('mousedown',e=>{SPH.drag=true;const r=wrap.getBoundingClientRect();SPH.ox=e.clientX-r.left;SPH.oy=e.clientY-r.top;});
document.addEventListener('mousemove',e=>{if(!SPH.drag)return;const a=area.getBoundingClientRect();SPH.x=Math.max(0,Math.min(a.width-SPH.size,e.clientX-a.left-SPH.ox));SPH.y=Math.max(0,Math.min(a.height-SPH.size,e.clientY-a.top-SPH.oy));sphPos();});
document.addEventListener('mouseup',()=>{if(SPH.drag){SPH.drag=false;SPH.vx=(Math.random()-.5)*1.6;SPH.vy=(Math.random()-.5)*1.6;}});
wrap.addEventListener('touchstart',e=>{const t=e.touches[0];SPH.drag=true;const r=wrap.getBoundingClientRect();SPH.ox=t.clientX-r.left;SPH.oy=t.clientY-r.top;},{passive:true});
document.addEventListener('touchmove',e=>{if(!SPH.drag)return;const t=e.touches[0];const a=area.getBoundingClientRect();SPH.x=Math.max(0,Math.min(a.width-SPH.size,t.clientX-a.left-SPH.ox));SPH.y=Math.max(0,Math.min(a.height-SPH.size,t.clientY-a.top-SPH.oy));sphPos();},{passive:true});
document.addEventListener('touchend',()=>{SPH.drag=false;});

// ---------- WEBCAM + PRESENZA ----------
let camOn=false,camStream=null,faceTimer=null,present=false,awaySince=Date.now();
async function startCam(){if(camOn)return true;try{camStream=await navigator.mediaDevices.getUserMedia({video:true});camOn=true;$('#cam').srcObject=camStream;$('#cambox').style.display='block';SPH.state='detecting';detectPresence();return true;}catch(e){toast('Webcam: '+e.message,'err');return false;}}
function stopCam(){if(camStream)camStream.getTracks().forEach(t=>t.stop());camStream=null;camOn=false;$('#cambox').style.display='none';clearInterval(faceTimer);present=false;if(SPH.state==='detecting')SPH.state='idle';}
function detectPresence(){
  let fd=null;if('FaceDetector' in window){try{fd=new FaceDetector({fastMode:true,maxDetectedFaces:1});}catch(e){}}
  const off=document.createElement('canvas');off.width=64;off.height=48;const oc=off.getContext('2d',{willReadFrequently:true});
  let prev=null,lastMo=0;present=false;awaySince=Date.now();
  faceTimer=setInterval(async()=>{
    const v=$('#cam');if(!camOn||v.readyState<2)return;let pr=false;
    if(fd){try{pr=(await fd.detect(v)).length>0;}catch(e){fd=null;}}
    if(!fd){try{oc.drawImage(v,0,0,64,48);const cur=oc.getImageData(0,0,64,48).data;if(prev){let d=0;for(let i=0;i<cur.length;i+=4)d+=Math.abs(cur[i]-prev[i]);d/=(cur.length/4);if(d>7)lastMo=Date.now();}prev=cur;pr=(Date.now()-lastMo)<9000;}catch(e){}}
    onPresence(pr);
  },700);
}
function onPresence(pr){const s=$('#fstat');if(pr){if(!present){present=true;const away=Date.now()-awaySince;if(s){s.textContent='✓ ti vedo';s.style.color='var(--green)';}if(SPH.state==='idle')SPH.state='detecting';if(friend&&away>20000)greetBack();}}else{if(present){present=false;awaySince=Date.now();if(s){s.textContent='nessun volto';s.style.color='var(--dim)';}if(SPH.state==='detecting')SPH.state='idle';}}}

// ---------- VISIONE (👁️ Guarda) ----------
function snap(){const v=$('#cam');const c=document.createElement('canvas');c.width=v.videoWidth||320;c.height=v.videoHeight||240;c.getContext('2d').drawImage(v,0,0,c.width,c.height);return c.toDataURL('image/jpeg',0.7);}
let visionBroken=false;
async function guarda(){
  if(busy)return;
  if(!camOn){const ok=await startCam();if(!ok)return;await new Promise(r=>setTimeout(r,900));}
  const img=snap();busy=true;SPH.state='thinking';
  const b=add('ai','');b.innerHTML='👁️ <span class="cursor"></span>';
  try{
    const r=await (await fetch('/vedi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({immagine:img})})).json();
    if(r.ok){b.textContent='👁️ '+r.testo;say(r.testo);}
    else{b.textContent='👁️ '+(r.errore||'Non riesco a vedere');visionBroken=true;}
  }catch(e){b.textContent='Errore visione: '+e.message;}
  SPH.state='idle';busy=false;
}
async function autoGlance(){
  if(busy||speaking||!camOn||visionBroken)return;
  const img=snap();if(!img)return;busy=true;SPH.state='thinking';
  try{
    const r=await (await fetch('/vedi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({immagine:img})})).json();
    if(r.ok){add('ai','👁️ '+r.testo);say(r.testo);}else{visionBroken=true;}
  }catch(e){}
  SPH.state='idle';busy=false;
}

// ---------- VOCE (riconoscimento) ----------
let reco=null,listening=false,micFatal=false;
function initReco(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)return;reco=new SR();reco.lang='it-IT';reco.continuous=false;reco.interimResults=true;let fin='';
  reco.onresult=e=>{let it='';for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal)fin+=e.results[i][0].transcript;else it+=e.results[i][0].transcript;}$('#inp').value=(fin+it).trim();};
  reco.onend=()=>{listening=false;$('#mic').classList.remove('on');const val=$('#inp').value.trim();if(val)invia();else if(friend&&!speaking&&!busy&&!micFatal)setTimeout(startReco,700);fin='';};
  reco.onerror=e=>{listening=false;$('#mic').classList.remove('on');if(e.error==='no-speech'){if(friend&&!speaking&&!busy&&!micFatal)setTimeout(startReco,500);return;}if(e.error==='aborted')return;if(['not-allowed','service-not-allowed','audio-capture'].includes(e.error)){micFatal=true;toast('Microfono non disponibile — scrivi pure','err');return;}toast('Errore microfono: '+e.error,'err');};
}
function startReco(){if(!reco||listening||busy||speaking||micFatal)return;try{listening=true;reco.start();$('#mic').classList.add('on');}catch(e){}}
function toggleMic(){if(!reco){toast('Voce non supportata dal browser','err');return;}if(listening){reco.stop();}else{micFatal=false;startReco();}}

// ---------- TTS (voce di MAIK) ----------
let ttsOn=false,speaking=false;
function say(t){if(!ttsOn||!window.speechSynthesis)return;speechSynthesis.cancel();const p=stripThink(t).replace(/[#*_`>]/g,'').replace(/<[^>]+>/g,'').replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}]/gu,'').slice(0,400);if(!p.trim())return;const u=new SpeechSynthesisUtterance(p);u.lang='it-IT';u.rate=1;u.pitch=1.1;const v=speechSynthesis.getVoices().find(x=>x.lang&&x.lang.startsWith('it'));if(v)u.voice=v;u.onstart=()=>{speaking=true;SPH.state='speaking';if(listening){try{reco.stop();}catch(e){}}};u.onend=()=>{speaking=false;if(SPH.state==='speaking')SPH.state='idle';if(friend&&!busy&&!speaking)setTimeout(()=>{if(friend)startReco();},400);};speechSynthesis.speak(u);}

// ---------- MODALITÀ AMICO ----------
let friend=false,lastAct=Date.now(),proTimer=null,proGap=90000;
function toggleFriend(){friend?exitFriend():enterFriend();}
async function enterFriend(){
  friend=true;ttsOn=true;micFatal=false;
  $('#fbtn').classList.add('on');$('#fbtn').innerHTML='🫂<span class="hx"> AMICO ON</span>';$('#fbadge').style.display='flex';
  await startCam();
  if(reco){setTimeout(()=>{if(friend&&!speaking&&!busy)startReco();},1200);}else toast('Voce non supportata: potrai scrivere','err');
  const nm=pName?' '+pName:'';
  const hi='Ehi'+nm+'! Da ora ti tengo compagnia: ti vedo, ti ascolto e chiacchieriamo come amici. Dimmi pure 😊';
  setTimeout(()=>{add('ai',hi);say(hi);},500);
  lastAct=Date.now();proGap=80000;startPro();toast('🫂 Modalità Amico attiva','ok');
}
function exitFriend(){friend=false;clearInterval(proTimer);if(listening){try{reco.stop();}catch(e){}}if(window.speechSynthesis)speechSynthesis.cancel();stopCam();$('#fbtn').classList.remove('on');$('#fbtn').innerHTML='🫂<span class="hx"> AMICO</span>';$('#fbadge').style.display='none';toast('Modalità Amico disattivata');}
function startPro(){clearInterval(proTimer);proTimer=setInterval(()=>{if(!friend||busy||speaking||listening)return;if($('#tmodal').classList.contains('open'))return;if(Date.now()-lastAct>=proGap){if(camOn&&!visionBroken&&Math.random()<0.35)autoGlance();else sayPro();lastAct=Date.now();proGap=70000+Math.random()*80000;}},5000);}
function sayPro(){const nm=pName?' '+pName:'';const h=new Date().getHours();const pool=['Allora'+nm+', come va la giornata?','A cosa stai pensando'+nm+'?','Ti va di raccontarmi qualcosa?','Sono qui'+nm+', se vuoi parlare ci sono.','Hai fatto qualcosa di bello oggi?','Come ti senti'+nm+'?','Se potessi fare una cosa qualsiasi adesso, cosa faresti?'];if(h<11)pool.push('Buongiorno'+nm+'! Come hai dormito?');else if(h>=21)pool.push('Si è fatta sera'+nm+'… com\'è stata la giornata?');const line=pool[Math.floor(Math.random()*pool.length)];add('ai',line);say(line);}
function greetBack(){if(busy||speaking)return;const nm=pName?' '+pName:'';const line='Bentornato'+nm+'! Ti rivedo 😊';add('ai',line);say(line);}

// ---------- STRUMENTI ----------
const TOOLS=[
 {ic:'🧮',nm:'Calcolatrice',fn:tCalc},{ic:'⏱️',nm:'Timer',fn:tTimer},{ic:'⏲️',nm:'Cronometro',fn:tStop},
 {ic:'🎲',nm:'Random',fn:tRand},{ic:'🔄',nm:'Convertitore',fn:tConv},{ic:'🌍',nm:'Orologi',fn:tClock},
 {ic:'📝',nm:'Note',fn:tNotes},{ic:'🔑',nm:'Password',fn:tPass},{ic:'🔢',nm:'Conta testo',fn:tCount},{ic:'🎯',nm:'Scegli per me',fn:tDecide},{ic:'✅',nm:'Lista/Spesa',fn:tCheck}
];
let TICK=[];function tick(){TICK.forEach(f=>{try{f();}catch(e){}});}function clearTick(){TICK=[];}
setInterval(()=>{if($('#tmodal').classList.contains('open'))tick();},1000);
function openTools(){toolsHome();$('#tmodal').classList.add('open');}
function closeTools(){$('#tmodal').classList.remove('open');clearTick();}
function toolsHome(){clearTick();$('#ttitle').textContent='🧰 STRUMENTI';$('#tback').style.display='none';const g=$('#tgrid');g.style.display='grid';g.innerHTML='';$('#tpanel').style.display='none';TOOLS.forEach(t=>{const d=document.createElement('div');d.className='tcard';d.innerHTML='<div class="ic">'+t.ic+'</div><div class="nm">'+t.nm+'</div>';d.onclick=()=>openTool(t);g.appendChild(d);});}
function openTool(t){clearTick();$('#tgrid').style.display='none';$('#tback').style.display='flex';$('#ttitle').textContent=t.ic+' '+t.nm.toUpperCase();const p=$('#tpanel');p.style.display='block';p.innerHTML='';t.fn(p);}
function elx(h){const d=document.createElement('div');d.innerHTML=h.trim();return d.firstChild;}

let _calc='';
function tCalc(p){p.innerHTML='<div class="tbig" id="cd" style="text-align:right;min-height:40px">0</div><div class="cg">'+
 '<button class="op" onclick="cP(\'C\')">C</button><button class="op" onclick="cP(\'(\')">(</button><button class="op" onclick="cP(\')\')">)</button><button class="op" onclick="cP(\'/\')">÷</button>'+
 '<button onclick="cP(\'7\')">7</button><button onclick="cP(\'8\')">8</button><button onclick="cP(\'9\')">9</button><button class="op" onclick="cP(\'*\')">×</button>'+
 '<button onclick="cP(\'4\')">4</button><button onclick="cP(\'5\')">5</button><button onclick="cP(\'6\')">6</button><button class="op" onclick="cP(\'-\')">−</button>'+
 '<button onclick="cP(\'1\')">1</button><button onclick="cP(\'2\')">2</button><button onclick="cP(\'3\')">3</button><button class="op" onclick="cP(\'+\')">+</button>'+
 '<button class="s2" onclick="cP(\'0\')">0</button><button onclick="cP(\'.\')">.</button><button class="eq" onclick="cP(\'=\')">=</button></div>';_calc='';}
function cP(k){const d=$('#cd');if(!d)return;if(k==='C'){_calc='';d.textContent='0';return;}if(k==='='){try{const e=_calc.replace(/×/g,'*').replace(/÷/g,'/');if(!/^[0-9+\-*/(). ]+$/.test(e))throw 0;const r=Function('"use strict";return ('+e+')')();d.textContent=Math.round(r*1e10)/1e10;_calc=String(r);}catch(x){d.textContent='Errore';_calc='';}return;}_calc+=k;d.textContent=_calc;}

let _tEnd=0,_tRun=false,_tMin=25;
function tTimer(p){p.innerHTML='<h4>Timer / Pomodoro</h4><div class="tbig" id="td">25:00</div><div class="trow"><button class="tbtn" onclick="tPre(5)">5m</button><button class="tbtn" onclick="tPre(10)">10m</button><button class="tbtn" onclick="tPre(25)">25m</button><button class="tbtn" onclick="tCust()">⚙</button></div><div class="trow"><button class="tbtn solid" id="tg" onclick="tTog()">Avvia</button><button class="tbtn" onclick="tRes()">Reset</button></div>';tRen(_tMin*60);TICK.push(tTick);}
function tRen(s){const d=$('#td');if(!d)return;const m=Math.floor(s/60),x=s%60;d.textContent=(''+m).padStart(2,'0')+':'+(''+x).padStart(2,'0');}
function tPre(m){_tRun=false;_tMin=m;tRen(m*60);const g=$('#tg');if(g)g.textContent='Avvia';}
function tCust(){const m=parseInt(prompt('Minuti?','15'));if(m>0)tPre(m);}
function tTog(){const g=$('#tg');if(_tRun){_tRun=false;g.textContent='Riprendi';_tMin=Math.ceil((_tEnd-Date.now())/60000);}else{_tRun=true;g.textContent='Pausa';_tEnd=Date.now()+_tMin*60000;}}
function tRes(){_tRun=false;const g=$('#tg');if(g)g.textContent='Avvia';tRen(_tMin*60);}
function tTick(){if(!_tRun)return;const l=Math.round((_tEnd-Date.now())/1000);if(l<=0){_tRun=false;tRen(0);beep(3);toast('⏰ Timer finito!','ok');const g=$('#tg');if(g)g.textContent='Avvia';return;}tRen(l);}

let _sS=0,_sE=0,_sR=false;
function tStop(p){p.innerHTML='<h4>Cronometro</h4><div class="tbig" id="sd">00:00.0</div><div class="trow"><button class="tbtn solid" id="sg" onclick="sTog()">Avvia</button><button class="tbtn" onclick="sRes()">Reset</button></div>';sRen();TICK.push(()=>{if(_sR)sRen();});}
function sRen(){const d=$('#sd');if(!d)return;const ms=_sE+(_sR?Date.now()-_sS:0),m=Math.floor(ms/60000),s=Math.floor(ms/1000)%60,t=Math.floor(ms/100)%10;d.textContent=(''+m).padStart(2,'0')+':'+(''+s).padStart(2,'0')+'.'+t;}
function sTog(){const g=$('#sg');if(_sR){_sE+=Date.now()-_sS;_sR=false;g.textContent='Riprendi';}else{_sS=Date.now();_sR=true;g.textContent='Stop';}sRen();}
function sRes(){_sR=false;_sE=0;const g=$('#sg');if(g)g.textContent='Avvia';sRen();}

function tRand(p){p.innerHTML='<h4>Generatore casuale</h4><div class="tout" id="ro" style="text-align:center;font-size:22px">—</div><div class="trow"><button class="tbtn" onclick="rD()">🎲 Dado</button><button class="tbtn" onclick="rC()">🪙 Moneta</button></div><input class="tfield" id="rmin" type="number" value="1"><input class="tfield" id="rmax" type="number" value="100"><div class="trow"><button class="tbtn solid" onclick="rR()">Numero casuale</button></div>';}
function rD(){$('#ro').textContent='🎲 '+(1+Math.floor(Math.random()*6));}
function rC(){$('#ro').textContent=Math.random()<.5?'🪙 Testa':'🪙 Croce';}
function rR(){const a=parseInt($('#rmin').value),b=parseInt($('#rmax').value);$('#ro').textContent=(isNaN(a)||isNaN(b)||a>b)?'Intervallo non valido':a+Math.floor(Math.random()*(b-a+1));}

const CONV={Lunghezza:{m:1,km:1000,cm:.01,mm:.001,mi:1609.34,yd:.9144,ft:.3048,in:.0254},Peso:{kg:1,g:.001,mg:1e-6,lb:.453592,oz:.0283495,t:1000},Volume:{L:1,mL:.001,m3:1000,gal:3.78541}};
function tConv(p){p.innerHTML='<h4>Convertitore</h4><select class="tfield" id="ccat" onchange="cFill()"></select><input class="tfield" id="cval" type="number" value="1" oninput="cGo()"><div class="trow" style="margin-top:8px"><select class="tfield" id="cf" style="margin-top:0" onchange="cGo()"></select><select class="tfield" id="ct" style="margin-top:0" onchange="cGo()"></select></div><div class="tout" id="cout">—</div>';const cat=$('#ccat');Object.keys(CONV).forEach(x=>cat.appendChild(new Option(x,x)));cat.appendChild(new Option('Temperatura','Temperatura'));cFill();}
function cFill(){const cat=$('#ccat').value,f=$('#cf'),t=$('#ct');f.innerHTML='';t.innerHTML='';const u=cat==='Temperatura'?['°C','°F','K']:Object.keys(CONV[cat]);u.forEach(x=>{f.appendChild(new Option(x,x));t.appendChild(new Option(x,x));});t.selectedIndex=Math.min(1,u.length-1);cGo();}
function cGo(){const cat=$('#ccat').value,v=parseFloat($('#cval').value),f=$('#cf').value,t=$('#ct').value,o=$('#cout');if(isNaN(v)){o.textContent='—';return;}let r;if(cat==='Temperatura'){let c=f==='°C'?v:f==='°F'?(v-32)*5/9:v-273.15;r=t==='°C'?c:t==='°F'?c*9/5+32:c+273.15;}else r=v*CONV[cat][f]/CONV[cat][t];o.textContent=v+' '+f+' = '+(Math.round(r*1e6)/1e6)+' '+t;}

const CLK=[['Roma','Europe/Rome'],['Londra','Europe/London'],['New York','America/New_York'],['Los Angeles','America/Los_Angeles'],['Tokyo','Asia/Tokyo'],['Dubai','Asia/Dubai'],['Sydney','Australia/Sydney']];
function tClock(p){p.innerHTML='<h4>Orologi mondiali</h4><div id="clkl"></div>';const r=()=>{const l=$('#clkl');if(!l)return;l.innerHTML='';CLK.forEach(([c,tz])=>{let tm='—';try{tm=new Intl.DateTimeFormat('it-IT',{timeZone:tz,hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date());}catch(e){}l.appendChild(elx('<div class="crow"><span class="c">'+c+'</span><span class="t">'+tm+'</span></div>'));});};r();TICK.push(r);}

function tNotes(p){p.innerHTML='<h4>Note rapide</h4><textarea class="tfield" id="ni" style="min-height:70px" placeholder="Scrivi una nota..."></textarea><div class="trow"><button class="tbtn solid" onclick="nAdd()">+ Aggiungi</button></div><div id="nl" style="margin-top:6px"></div>';nRen();}
function notes(){try{return JSON.parse(localStorage.getItem('maik_srv_notes')||'[]');}catch(e){return[];}}
function nRen(){const l=$('#nl');if(!l)return;const a=notes();l.innerHTML=a.length?'':'<div class="note">Nessuna nota</div>';a.forEach((n,i)=>l.appendChild(elx('<div class="nitem"><span>'+esc(n)+'</span><button class="nx" onclick="nDel('+i+')">✕</button></div>')));}
function nAdd(){const v=$('#ni').value.trim();if(!v)return;const a=notes();a.unshift(v);localStorage.setItem('maik_srv_notes',JSON.stringify(a));$('#ni').value='';nRen();}
function nDel(i){const a=notes();a.splice(i,1);localStorage.setItem('maik_srv_notes',JSON.stringify(a));nRen();}

function tPass(p){p.innerHTML='<h4>Generatore password</h4><div class="tout" id="po" style="font-size:16px;text-align:center">—</div><label style="display:flex;align-items:center;color:var(--dim);font-size:13px;margin-top:10px">Lunghezza<input type="range" id="pl" min="6" max="40" value="16" oninput="$(\'#plv\').textContent=this.value" style="flex:1;margin:0 8px;accent-color:var(--cyan)"><span id="plv">16</span></label><label style="display:flex;justify-content:space-between;color:var(--dim);font-size:13px;margin-top:6px">Simboli<input type="checkbox" id="ps" checked style="accent-color:var(--cyan)"></label><div class="trow"><button class="tbtn solid" onclick="pGen()">Genera</button><button class="tbtn" onclick="pCopy()">Copia</button></div>';pGen();}
function pGen(){const n=parseInt($('#pl').value),sy=$('#ps').checked;let ch='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';if(sy)ch+='!@#$%^&*()-_=+[]{}?';const a=new Uint32Array(n);crypto.getRandomValues(a);let pw='';for(let i=0;i<n;i++)pw+=ch[a[i]%ch.length];$('#po').textContent=pw;}
function pCopy(){const t=$('#po').textContent;navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>toast('Copiata','ok'),()=>toast('Copia non riuscita','err'));}

function tCount(p){p.innerHTML='<h4>Conta testo</h4><textarea class="tfield" id="wi" style="min-height:110px" placeholder="Incolla qui il testo..." oninput="wGo()"></textarea><div class="tout" id="wo">Parole: 0 · Caratteri: 0 · Righe: 0</div>';}
function wGo(){const t=$('#wi').value,w=(t.trim().match(/\S+/g)||[]).length,l=t?t.split(/\n/).length:0;$('#wo').textContent='Parole: '+w+' · Caratteri: '+t.length+' · Righe: '+l;}

function tDecide(p){p.innerHTML='<h4>Scegli per me</h4><textarea class="tfield" id="di" style="min-height:90px" placeholder="Una opzione per riga, o separate da virgola"></textarea><div class="trow"><button class="tbtn solid" onclick="dGo()">🎯 Scegli!</button></div><div class="tout" id="do" style="text-align:center;font-size:18px">—</div>';}
function dGo(){const o=$('#di').value.split(/[\n,]/).map(s=>s.trim()).filter(Boolean);$('#do').textContent=o.length?'👉 '+o[Math.floor(Math.random()*o.length)]:'Aggiungi opzioni';}

function tCheck(p){p.innerHTML='<h4>Lista / Spesa</h4><div style="display:flex;gap:6px"><input class="tfield" id="cki" style="margin-top:0" placeholder="Aggiungi voce..." onkeydown="if(event.key===\'Enter\')ckAdd()"><button class="tbtn solid" style="flex:0 0 auto;min-width:60px;margin-top:0" onclick="ckAdd()">+</button></div><div id="ckl" style="margin-top:8px"></div><div class="trow"><button class="tbtn" onclick="ckClr()">Rimuovi completati</button></div>';ckRen();}
async function ckApi(body){try{const r=await (await fetch('/lista',body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:undefined)).json();return r.lista||[];}catch(e){return [];}}
async function ckRen(a){const l=$('#ckl');if(!l)return;a=a||await ckApi();l.innerHTML=a.length?'':'<div class="note">Lista vuota (anche «aggiungi latte alla lista» in chat!)</div>';a.forEach((it,i)=>{const d=elx('<div class="nitem"><label style="display:flex;gap:8px;align-items:center;flex:1;'+(it.fatto?'opacity:.5;text-decoration:line-through':'')+'"><input type="checkbox" '+(it.fatto?'checked':'')+' style="accent-color:var(--cyan)"><span>'+esc(it.testo)+'</span></label><button class="nx">✕</button></div>');d.querySelector('input').onchange=async()=>ckRen(await ckApi({azione:'toggle',indice:i}));d.querySelector('.nx').onclick=async()=>ckRen(await ckApi({azione:'elimina',indice:i}));l.appendChild(d);});}
async function ckAdd(){const v=$('#cki').value.trim();if(!v)return;$('#cki').value='';ckRen(await ckApi({azione:'aggiungi',testo:v}));}
async function ckClr(){ckRen(await ckApi({azione:'pulisci'}));}

function beep(n){try{const c=new (window.AudioContext||window.webkitAudioContext)();for(let i=0;i<(n||1);i++){const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=880;o.type='sine';const t=c.currentTime+i*.25;g.gain.setValueAtTime(.001,t);g.gain.exponentialRampToValueAtTime(.3,t+.02);g.gain.exponentialRampToValueAtTime(.001,t+.2);o.start(t);o.stop(t+.2);}}catch(e){}}

// ---------- INIT ----------
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeTools();});
$('#tmodal').addEventListener('click',e=>{if(e.target.id==='tmodal')closeTools();});
window.addEventListener('resize',()=>{sphSize();const a=area.getBoundingClientRect();SPH.x=Math.max(0,Math.min(SPH.x,a.width-SPH.size));SPH.y=Math.max(0,Math.min(SPH.y,a.height-SPH.size));sphPos();});
if(window.speechSynthesis){speechSynthesis.getVoices();speechSynthesis.onvoiceschanged=()=>speechSynthesis.getVoices();}
initReco();sphInit();sphLoop();stato();cfg();profilo();loadPr();checkLearn();
setInterval(stato,15000);setInterval(checkScaduti,4000);setInterval(checkLearn,20000);setInterval(loadPr,30000);
(async()=>{try{const r=await (await fetch('/briefing?auto=1')).json();if(r.testo){add('ai',r.testo);return;}}catch(e){}
  add('ai','Ciao! Sono **Maik**, versione 8 🧠 Imparo da solo mentre parliamo e so fare azioni vere: timer, promemoria che suonano, lista della spesa, calcoli… Scrivi **aiuto** per vederle tutte. Premi 🫂 AMICO per farmi vedere e parlare 💚');})();
</script>
</body></html>"""


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("""
╔══════════════════════════════════════════════════╗
║           MAIK 8.0 — Server avviato             ║
║   Impara da solo · azioni · promemoria · voce    ║
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
        print(f"  Ollama online  ·  chat: {CONFIG['modello']}  ·  visione: {CONFIG['modello_visione']}")
        if mod:
            print(f"  Modelli pronti: {', '.join(mod)}")
            if CONFIG["modello"] not in mod:
                print(f"  ⚠  '{CONFIG['modello']}' non installato →  ollama pull {CONFIG['modello']}")
            if CONFIG["modello_visione"] not in mod:
                print(f"  ⚠  modello visione '{CONFIG['modello_visione']}' non installato "
                      f"(serve per 👁️ Guarda) →  ollama pull {CONFIG['modello_visione']}")

    print("""
  ── MODELLI CONSIGLIATI ──────────────────────────────────────
   PC potente (>=16GB RAM / GPU):  chat  qwen2.5:14b  ·  visione  llava:13b
   PC medio   (~8-12GB):           chat  llama3.1     ·  visione  llava
   PC leggero (<=8GB):             chat  llama3.2:3b  ·  visione  moondream
   Installa:  ollama pull <nome>   ·   imposta con MAIK_MODELLO / MAIK_MODELLO_VISIONE

   ⚠  llama3.2-vision dà 'unknown model architecture: mllama' su Ollama vecchi.
      Per la webcam usa  llava  (va ovunque):   ollama pull llava
      Per llama3.2-vision serve Ollama >= 0.4 (aggiorna da ollama.com/download).
  ─────────────────────────────────────────────────────────────""")

    url = f"http://{CONFIG['host']}:{CONFIG['porta']}"
    gui = "aria.html" if os.path.exists(HTML_FILE) else "GUI integrata di riserva"
    print(f"\n  GUI:  {gui}")
    print(f"  Pronto su:  {url}")
    print(f"  Premi Ctrl+C per chiudere\n")
    print(f"  Apprendimento con l'IA: {'ATTIVO' if CONFIG['apprendimento_ia'] else 'spento'}"
          f"  ·  personalità: {CONFIG['personalita']}")
    print(f"  Endpoint principali:")
    print(f"    POST /chat/stream   — chat in streaming (+ azioni: timer, promemoria, calcoli…)")
    print(f"    POST /vedi          — visione: descrive un frame webcam")
    print(f"    GET  /promemoria /promemoria/scaduti · GET/POST /lista      [NUOVO]")
    print(f"    GET  /briefing · POST /personalita · GET /appreso            [NUOVO]")
    print(f"    GET  /salute /config /timeline /cerca?q=testo")
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
