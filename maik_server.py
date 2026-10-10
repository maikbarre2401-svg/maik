"""
╔══════════════════════════════════════════════════════════╗
║                  MAIK — Server v10.0                     ║
║   AI locale con GUI futuristica 3D nel browser           ║
║   Memoria avanzata: episodica, semantica, emotiva        ║
╚══════════════════════════════════════════════════════════╝

COME SI AVVIA:
  1. Ollama acceso + modello scaricato:  ollama pull llama3.1
  2. Avvia:  python maik_server.py
  3. Si apre da solo nel browser.

Solo librerie standard Python — niente pip.

NOVITÀ v10.0 — AGENTE, DOCUMENTI, CHAT, AMICO VERO, APP:
  • 🤖 Agente: il modello decide da solo di usare gli strumenti (promemoria, timer,
    lista, note, obiettivi, meteo, ora nel mondo, calcoli, ricerca nei documenti e
    nella memoria). Tag invisibili [[azione:{...}]] controllati ed eseguiti dal server;
    per meteo/calcoli/ricerche c'è un secondo giro con i dati veri.
  • 📚 I tuoi documenti: carichi file di testo, Maik li spezza e li cerca (BM25) e
    risponde citando la fonte [nome file].
  • 💬 Più conversazioni separate (nuova, rinomina, elimina), con la stessa memoria.
  • 🔁 Follow-up da amico: «domani ho l'esame» → il giorno dopo «com'è andato?».
  • 📲 App installabile (manifest + service worker + icone generate dal server).
  • Nuovi endpoint: /sessioni*, /documenti*, /seguiti*, /manifest.webmanifest, /sw.js;
    /chat/stream accetta "sessione" e restituisce "azioni", "fonti", "seguito".
  • Variabili: MAIK_AGENTE=0 spegne l'agente · MAIK_SEGUITI_RITARDO=secondi (demo)

NOVITÀ v9.0 — GRAFICA E SISTEMA:
  • Nucleo neurale 3D nitido su ogni schermo (sinapsi, impulsi, anelli HUD,
    onde d'urto), reagisce alla voce parola per parola e al microfono
  • 6 temi completi (Neon, Synthwave, Matrix, Solar, Ice, Ruby), aurora, vetro
  • Avvio con controlli reali · palette comandi Ctrl+K · codice evidenziato
  • 📎 Allegati: immagini (le guarda il modello visione) e file di testo
  • Velocità vera del modello (token/s, prima parola), ■ stop che tiene il testo,
    ↻ rigenera, copia, ascolta · parola di attivazione «Maik»
  • Memoria completa consultabile, con «dimentica»
  • Nuovi endpoint: /imparato/elimina, /episodio/elimina, /riassunto/elimina;
    /chat/stream accetta "allegato" e "rigenera" e restituisce "stat"

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
import struct
import zlib
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
    "file_sessioni":  "sessioni.json",     # v10: più conversazioni, stessa memoria
    "file_documenti": "documenti.json",    # v10: i tuoi documenti (ricerca con fonti)
    "file_seguiti":   "seguiti.json",      # v10: "com'è andato l'esame?"
    # agente: il modello può usare gli strumenti (promemoria, lista, meteo, calcoli…) da solo
    "agente": _env("MAIK_AGENTE", "1") not in ("0", "no", "false"),
    # follow-up: dopo quanti secondi richiedere com'è andata (0 = automatico, dopo l'evento)
    "seguiti_ritardo": int(_env("MAIK_SEGUITI_RITARDO", "0")),
    # apprendimento con l'IA (un'estrazione JSON dopo ogni messaggio personale)
    "apprendimento_ia": _env("MAIK_APPRENDIMENTO_IA", "1") not in ("0", "no", "false"),
    "ogni_n_riassumi": 8,
    "timeout_chat":   int(_env("MAIK_TIMEOUT", "300")),
    # Open-Meteo (gratuito, no key)
    "meteo_geo_url":      "https://geocoding-api.open-meteo.com/v1/search",
    "meteo_forecast_url": "https://api.open-meteo.com/v1/forecast",
}

VERSIONE  = "10.0"
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

_STOP_DOMANDE = set(("quanto quanta quanti quante quale quali qual dimmi sai sapere puoi potresti vorrei voglio "
                     "posso devo fammi spiegami ciao grazie maik dire detto cosa cose qualcosa ecco allora "
                     "nostro nostra loro essere avere").split())

def _parole(s):
    """Come _token ma in lista (con le ripetizioni) e con i numeri: serve alla ricerca BM25."""
    return [w[:6] for w in _normalizza(s).split()
            if (len(w) > 2 or w.isdigit()) and w not in _STOP and w not in _STOP_DOMANDE]

def _titolo_chat(testo):
    """Titolo automatico di una chat dalla prima domanda: corto e tagliato a parola intera."""
    t = re.sub(r"\s+", " ", re.sub(r"\[📎[^\]]*\]", "", testo)).strip(" ?!.,")
    if len(t) > 42:
        t = t[:42].rsplit(" ", 1)[0] + "…"
    return (t[:1].upper() + t[1:]) if t else "Nuova chat"

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
        self.sessioni  = self._carica(CONFIG["file_sessioni"],  [])
        self.documenti = self._carica(CONFIG["file_documenti"], [])
        self.seguiti   = self._carica(CONFIG["file_seguiti"],   [])
        self._segna_giorno()
        self._assicura_principale()
        self._indicizza_documenti()

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
    def salva_scambio(self, tu, ai, sessione=None, extra=None):
        """Salva uno scambio nel diario. `sessione` = la chat a cui appartiene (v10);
        `extra` = azioni/fonti da mostrare di nuovo quando riapri la chat."""
        with self._lock:
            sid = sessione or self.PRINCIPALE
            voce = {
                "quando": datetime.datetime.now().isoformat(timespec="seconds"),
                "tu": tu[:4000],      # niente file interi nel diario: resta leggero e veloce
                "ai": ai[:6000],
                "sessione": sid,
            }
            if extra:
                voce.update({k: v for k, v in extra.items() if v})
            self.diario.append(voce)
            if len(self.diario) > 2000:
                self.diario = self.diario[-2000:]
            self._salva(CONFIG["file_diario"], self.diario)
            s = self._sessione(sid)
            if s:
                s["aggiornata"] = datetime.datetime.now().isoformat(timespec="milliseconds")
                if s.get("auto") and tu.strip():          # la chat prende il nome dalla prima domanda
                    s["titolo"], s["auto"] = _titolo_chat(tu), False
                self._salva(CONFIG["file_sessioni"], self.sessioni)

    def rimuovi_ultimo_scambio(self, tu=None, sessione=None):
        """Per «rigenera»: toglie l'ultimo scambio della chat se è proprio quella domanda."""
        with self._lock:
            sid = sessione or self.PRINCIPALE
            for i in range(len(self.diario) - 1, -1, -1):
                if (self.diario[i].get("sessione") or self.PRINCIPALE) != sid:
                    continue
                if tu is None or self.diario[i].get("tu", "").strip() == tu.strip()[:4000].strip():
                    self.diario.pop(i)
                    self._salva(CONFIG["file_diario"], self.diario)
                    return True
                return False
            return False

    def dimentica_elemento(self, tipo, indice):
        """Cancella un ricordo («imparato») o un momento («episodio») dalla memoria completa."""
        lista, file_ = {"imparato": (self.imparato, "file_imparato"), "episodio": (self.episodi, "file_episodi")}.get(tipo, (None, None))
        with self._lock:
            if lista is None or not (0 <= indice < len(lista)):
                return False
            lista.pop(indice)
            self._salva(CONFIG[file_], lista)
            return True

    def ultimi_scambi(self, n=6, sessione=None):
        with self._lock:
            if sessione is None:
                return list(self.diario[-n:])
            return [x for x in self.diario if (x.get("sessione") or self.PRINCIPALE) == sessione][-n:]

    # ── Conversazioni (v10): più chat, una sola memoria ──────
    PRINCIPALE = "principale"

    def _sessione(self, sid):
        for s in self.sessioni:
            if s.get("id") == sid:
                return s
        return None

    def _assicura_principale(self):
        with self._lock:
            if not self._sessione(self.PRINCIPALE):
                ultimo = self.diario[-1]["quando"] if self.diario else datetime.datetime.now().isoformat(timespec="seconds")
                self.sessioni.insert(0, {"id": self.PRINCIPALE, "titolo": "Chat principale",
                                         "creata": ultimo, "aggiornata": ultimo})
                self._salva(CONFIG["file_sessioni"], self.sessioni)

    def sessione_valida(self, sid):
        with self._lock:
            return sid if sid and self._sessione(sid) else self.PRINCIPALE

    def sessioni_elenco(self):
        with self._lock:
            self._assicura_principale()
            conta, ultima = {}, {}
            for sc in self.diario:
                sid = sc.get("sessione") or self.PRINCIPALE
                conta[sid] = conta.get(sid, 0) + 1
                if sc.get("tu"):
                    ultima[sid] = sc["tu"][:70]
            out = [dict(s, n=conta.get(s["id"], 0), anteprima=ultima.get(s["id"], "")) for s in self.sessioni]
        return sorted(out, key=lambda s: s.get("aggiornata") or "", reverse=True)

    def crea_sessione(self, titolo=""):
        titolo = re.sub(r"\s+", " ", str(titolo or "")).strip()[:60]
        ora = datetime.datetime.now().isoformat(timespec="milliseconds")
        with self._lock:
            s = {"id": uuid.uuid4().hex[:10], "titolo": titolo or "Nuova chat",
                 "creata": ora, "aggiornata": ora, "auto": not titolo}
            self.sessioni.append(s)
            if len(self.sessioni) > 200:             # tiene le 200 chat più recenti
                vecchie = sorted((x for x in self.sessioni if x["id"] != self.PRINCIPALE),
                                 key=lambda x: x.get("aggiornata") or "")[:len(self.sessioni) - 200]
                via = {x["id"] for x in vecchie}
                self.sessioni = [x for x in self.sessioni if x["id"] not in via]
                self.diario = [x for x in self.diario if x.get("sessione") not in via]
                self._salva(CONFIG["file_diario"], self.diario)
            self._salva(CONFIG["file_sessioni"], self.sessioni)
            return dict(s, n=0, anteprima="")

    def rinomina_sessione(self, sid, titolo):
        titolo = re.sub(r"\s+", " ", str(titolo or "")).strip()[:60]
        with self._lock:
            s = self._sessione(sid)
            if not s or not titolo:
                return False
            s["titolo"], s["auto"] = titolo, False
            self._salva(CONFIG["file_sessioni"], self.sessioni)
            return True

    def elimina_sessione(self, sid):
        """Cancella una chat e i suoi messaggi (la memoria su di te resta). La principale si svuota soltanto."""
        with self._lock:
            if not self._sessione(sid):
                return False
            prima = len(self.diario)
            self.diario = [x for x in self.diario if (x.get("sessione") or self.PRINCIPALE) != sid]
            if len(self.diario) != prima:
                self._salva(CONFIG["file_diario"], self.diario)
            if sid == self.PRINCIPALE:
                self._sessione(sid)["aggiornata"] = datetime.datetime.now().isoformat(timespec="seconds")
            else:
                self.sessioni = [x for x in self.sessioni if x["id"] != sid]
            self._salva(CONFIG["file_sessioni"], self.sessioni)
            return True

    def storia_sessione(self, sid, n=150):
        with self._lock:
            sid = sid if self._sessione(sid) else self.PRINCIPALE
            voci = [x for x in self.diario if (x.get("sessione") or self.PRINCIPALE) == sid][-n:]
            return [{k: x[k] for k in ("quando", "tu", "ai", "azioni", "fonti", "seguito") if k in x} for x in voci]

    # ── Documenti (v10): la tua base di conoscenza, con fonti ─
    MAX_DOC_CARATTERI = 400_000
    MAX_DOC_TOTALE = 4_000_000

    @staticmethod
    def _spezza(testo, dim=900, sovrapp=150):
        """Divide un testo in pezzi di ~dim caratteri, tagliando a fine paragrafo/frase quando si può."""
        testo = re.sub(r"\r\n?", "\n", testo)
        testo = re.sub(r"[ \t]+", " ", testo)
        testo = re.sub(r"\n{3,}", "\n\n", testo).strip()
        pezzi, i, n = [], 0, len(testo)
        while i < n:
            fine = min(n, i + dim)
            if fine < n:
                fin = testo[i:fine]
                taglio = max(fin.rfind("\n\n"), fin.rfind(". "), fin.rfind("\n"), fin.rfind("? "), fin.rfind("! "))
                if taglio > dim * 0.5:
                    fine = i + taglio + 1
            pezzo = testo[i:fine].strip()
            if pezzo:
                pezzi.append(pezzo)
            if fine >= n:
                break
            nuovo = max(fine - sovrapp, i + 1)
            spazio = testo.find(" ", nuovo, fine)
            i = spazio + 1 if spazio >= 0 else nuovo
        return pezzi

    def _indicizza_documenti(self):
        """Indice BM25 in memoria (si ricostruisce in un attimo: niente da salvare)."""
        with self._lock:
            indice, df = [], {}
            for d in self.documenti:
                nome_tok = _parole(re.sub(r"\.\w{1,5}$", "", d.get("nome", "")).replace("_", " ").replace("-", " "))
                for j, p in enumerate(d.get("pezzi", [])):
                    tf = {}
                    for w in _parole(p) + nome_tok:
                        tf[w] = tf.get(w, 0) + 1
                    indice.append((d["id"], d.get("nome", ""), j, tf, sum(tf.values()) or 1, p))
                    for w in tf:
                        df[w] = df.get(w, 0) + 1
            self._doc_indice, self._doc_df = indice, df
            self._doc_media = (sum(x[4] for x in indice) / len(indice)) if indice else 1

    def cerca_documenti(self, query, k=3, rigida=True):
        """I pezzi di documento più pertinenti (BM25). `rigida`: solo quelli davvero legati alla domanda."""
        q = set(_parole(query))
        with self._lock:
            indice, df, media = self._doc_indice, self._doc_df, self._doc_media
        if not q or not indice:
            return []
        N, k1, b = len(indice), 1.4, 0.75
        punti = []
        for did, nome, j, tf, lung, testo in indice:
            s, comuni = 0.0, 0
            for w in q:
                f = tf.get(w)
                if f:
                    comuni += 1
                    n = df[w]
                    s += math.log(1 + (N - n + 0.5) / (n + 0.5)) * f * (k1 + 1) / (f + k1 * (1 - b + b * lung / media))
            # rigida: conta QUANTE parole della domanda ci sono (l'IDF da solo inganna con pochi documenti)
            if s > 0 and (not rigida or (comuni >= min(2, len(q)) and comuni / len(q) >= 0.3)):
                punti.append((s, comuni, did, nome, j, testo))
        punti.sort(key=lambda x: (-x[0], x[3], x[4]))
        return [{"doc": did, "nome": nome, "pezzo": j + 1, "testo": testo, "punteggio": round(s, 2)}
                for s, comuni, did, nome, j, testo in punti[:k]]

    @staticmethod
    def _info_doc(d):
        pezzi = d.get("pezzi", [])
        return {"id": d["id"], "nome": d.get("nome", ""), "aggiunto": d.get("aggiunto", ""),
                "caratteri": d.get("caratteri", 0), "n_pezzi": len(pezzi),
                "anteprima": (pezzi[0][:160] if pezzi else "")}

    def documenti_elenco(self):
        with self._lock:
            return [self._info_doc(d) for d in reversed(self.documenti)]

    def aggiungi_documento(self, nome, contenuto):
        """Ritorna (info, errore). Stesso nome = nuova versione dello stesso documento."""
        nome = re.sub(r"[\r\n\t]+", " ", str(nome or "")).strip()[:80] or "documento.txt"
        contenuto = str(contenuto or "").replace("\x00", "")
        if len(contenuto.strip()) < 2:
            return None, "Il documento è vuoto."
        tagliato = len(contenuto) > self.MAX_DOC_CARATTERI
        contenuto = contenuto[:self.MAX_DOC_CARATTERI]
        with self._lock:
            altri = [d for d in self.documenti if d.get("nome") != nome]
            if sum(d.get("caratteri", 0) for d in altri) + len(contenuto) > self.MAX_DOC_TOTALE:
                return None, "Spazio documenti esaurito: elimina qualche documento vecchio."
            doc = {"id": uuid.uuid4().hex[:10], "nome": nome,
                   "aggiunto": datetime.datetime.now().isoformat(timespec="seconds"),
                   "caratteri": len(contenuto), "pezzi": self._spezza(contenuto)}
            self.documenti = altri + [doc]
            self._salva(CONFIG["file_documenti"], self.documenti)
            self._indicizza_documenti()
            return dict(self._info_doc(doc), tagliato=tagliato), None

    def elimina_documento(self, did):
        with self._lock:
            prima = len(self.documenti)
            self.documenti = [d for d in self.documenti if d.get("id") != did]
            if len(self.documenti) == prima:
                return False
            self._salva(CONFIG["file_documenti"], self.documenti)
            self._indicizza_documenti()
            return True

    # ── Follow-up (v10): «com'è andato l'esame?» ─────────────
    def aggiungi_seguito(self, evento, quando, chiedi, domanda, fonte=""):
        with self._lock:
            chiave = _normalizza(evento)
            for s in self.seguiti:      # stesso evento già in attesa (o stesso messaggio) → aggiorna
                if not s.get("chiesto") and (_normalizza(s.get("evento", "")) == chiave
                                             or (fonte and s.get("fonte") == fonte[:300])):
                    s.update(evento=evento, quando=quando.isoformat(timespec="minutes"),
                             chiedi=chiedi.isoformat(timespec="seconds"), domanda=domanda or s.get("domanda", ""))
                    self._salva(CONFIG["file_seguiti"], self.seguiti)
                    return dict(s)
            s = {"id": uuid.uuid4().hex[:8], "evento": evento[:90], "domanda": domanda[:160],
                 "quando": quando.isoformat(timespec="minutes"), "chiedi": chiedi.isoformat(timespec="seconds"),
                 "fonte": fonte[:300], "creato": datetime.datetime.now().isoformat(timespec="seconds"),
                 "chiesto": None}
            self.seguiti.append(s)
            if len(self.seguiti) > 200:
                self.seguiti = self.seguiti[-200:]
            self._salva(CONFIG["file_seguiti"], self.seguiti)
            return dict(s)

    def aggiorna_seguito_da_fonte(self, fonte, domanda):
        with self._lock:
            for s in reversed(self.seguiti):
                if not s.get("chiesto") and s.get("fonte") == fonte[:300]:
                    s["domanda"] = domanda[:160]
                    self._salva(CONFIG["file_seguiti"], self.seguiti)
                    return True
            return False

    def seguiti_in_attesa(self):
        with self._lock:
            return sorted((dict(s) for s in self.seguiti if not s.get("chiesto")), key=lambda s: s["chiedi"])

    def seguiti_scaduti(self):
        """I follow-up arrivati al momento giusto: li segna come chiesti e li ritorna.
        Se sono passati più di 4 giorni li lascia perdere (sarebbe strano chiederlo ora)."""
        ora = datetime.datetime.now()
        out = []
        with self._lock:
            cambiato = False
            for s in self.seguiti:
                if s.get("chiesto"):
                    continue
                try:
                    chiedi = datetime.datetime.fromisoformat(s["chiedi"])
                except (KeyError, ValueError):
                    chiedi = ora
                if chiedi <= ora:
                    s["chiesto"] = ora.isoformat(timespec="seconds")
                    cambiato = True
                    if (ora - chiedi).days < 4:
                        out.append(dict(s))
            if cambiato:
                self._salva(CONFIG["file_seguiti"], self.seguiti)
        return out

    def elimina_seguito(self, sid):
        with self._lock:
            prima = len(self.seguiti)
            self.seguiti = [s for s in self.seguiti if s.get("id") != sid]
            if len(self.seguiti) != prima:
                self._salva(CONFIG["file_seguiti"], self.seguiti)
                return True
            return False

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
            ora = datetime.datetime.now()
            arrivo = [s for s in self.seguiti if not s.get("chiesto")][-5:]
            if arrivo:
                ev = "\n".join(f"- {s['evento']} ({fmt_quando(datetime.datetime.fromisoformat(s['quando']), ora)})"
                               for s in arrivo)
                parti.append(f"EVENTI IN ARRIVO NELLA SUA VITA (fai il tifo, chiedi come si sente):\n{ev}")
            appena = [s for s in self.seguiti if s.get("chiesto") and
                      (ora - datetime.datetime.fromisoformat(s["chiesto"])).total_seconds() < 6 * 3600][-2:]
            if appena:
                ev = "\n".join(f"- {s['evento']}" for s in appena)
                parti.append("GLI HAI APPENA CHIESTO COM'È ANDATA (se ne parla, reagisci davvero: "
                             f"festeggia o consola):\n{ev}")
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
                "sessioni":  self.sessioni,
                "documenti": self.documenti,
                "seguiti":   self.seguiti,
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
            "sessioni":  ("file_sessioni",  "sessioni"),
            "documenti": ("file_documenti", "documenti"),
            "seguiti":   ("file_seguiti",   "seguiti"),
        }
        with self._lock:
            for chiave, (cfg_key, attr) in mapping.items():
                if chiave in dati:
                    setattr(self, attr, dati[chiave])
                    self._salva(CONFIG[cfg_key], dati[chiave])
            self._assicura_principale()
            self._indicizza_documenti()

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
            "documenti": ("file_documenti", "documenti", []),
            "seguiti":   ("file_seguiti",   "seguiti",   []),
        }
        with self._lock:
            if categoria in mapping:
                cfg_key, attr, default = mapping[categoria]
                nuovo = json.loads(json.dumps(default))
                setattr(self, attr, nuovo)
                self._salva(CONFIG[cfg_key], nuovo)
                if categoria == "documenti":
                    self._indicizza_documenti()
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
                "riassunto":         self.ricordi.get("riassunto", ""),
                "n_promemoria":      len([p for p in self.promemoria if not p.get("fatto")]),
                "n_lista":           len([x for x in self.lista if not x.get("fatto")]),
                "n_documenti":       len(self.documenti),
                "n_sessioni":        len(self.sessioni),
                "n_seguiti":         len([s for s in self.seguiti if not s.get("chiesto")]),
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

    def pensa_stream(self, system_prompt, messaggi, on_token, stat=None):
        """Streaming token-per-token. Chiama on_token(chunk) e ritorna il testo completo.
        Se passi un dict `stat`, lo riempie con la velocità vera: token/s, prima parola, durata."""
        req = urllib.request.Request(
            CONFIG["ollama_url"],
            data=self._payload(system_prompt, messaggi, True),
            headers={"Content-Type": "application/json"},
        )
        full = []
        t0, ttft = time.perf_counter(), 0.0
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
                        if not ttft:
                            ttft = time.perf_counter() - t0
                        full.append(chunk)
                        on_token(chunk)
                    if obj.get("done"):
                        if stat is not None:
                            totale = time.perf_counter() - t0
                            n, ns = obj.get("eval_count") or 0, obj.get("eval_duration") or 0
                            tps = n / (ns / 1e9) if n and ns else (n / max(1e-3, totale - ttft) if n else 0)
                            stat.update(tps=round(tps, 1), ttft_ms=round((ttft or totale) * 1000),
                                        totale_ms=round(totale * 1000), token=n)
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
    elif giorno or settimana:                    # (settimana: "sabato" detto di sabato → quello dopo)
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
🤖 E puoi chiedermelo anche a parole tue: «stasera pasta, metti in lista gli ingredienti»,
   «mi fai il conto di 23 per 17?», «che tempo fa a Napoli?» — uso i miei strumenti da solo.
📚 Carica i tuoi documenti (barra laterale) e chiedimi cosa c'è dentro: ti cito la fonte.
💬 Più chat separate, una sola memoria · 🔁 se mi dici «domani ho l'esame», dopo ti chiedo com'è andata.
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


# ════════════════════════════════════════════════════════════
# FOLLOW-UP (v10) — "domani ho l'esame" → il giorno dopo: "com'è andato?"
# ════════════════════════════════════════════════════════════
_QUANDO_EV = (r"dopodomani|domani(?:\s+mattina|\s+pomeriggio|\s+sera)?|stasera|stamattina|stanotte|"
              r"oggi\s+pomeriggio|questo\s+pomeriggio|oggi|"
              r"(?:questo\s+|questa\s+|il\s+prossimo\s+|prossimo\s+)?(?:luned[iì]|marted[iì]|mercoled[iì]|"
              r"gioved[iì]|venerd[iì]|sabato|domenica)")
_VERBI_EV = (r"ho|avr[oò]|c'[eè]|ci\s+sar[aà]|devo|dovr[oò]|faccio|far[oò]|vado|andr[oò]|parto|partir[oò]|"
             r"inizio|comincio|esco|uscir[oò]|gioco|giocher[oò]|sostengo|discuto|incontro|vedo|vedr[oò]|"
             r"mi\s+sposo|mi\s+laureo|mi\s+opero|torno|cambio")
_RE_EVENTO = re.compile(r"\b(?P<quando>" + _QUANDO_EV + r")\b(?P<mezzo>[^.!?\n]{0,30}?)\s*\b(?P<verbo>" + _VERBI_EV +
                        r")\b(?:\s+(?P<cosa>[^.!?\n]{2,90}))?", re.I)
_RE_EVENTO_DOPO = re.compile(r"\b(?P<verbo>ho|avr[oò]|c'[eè])\s+(?P<cosa>[^.!?\n]{3,60}?)\s+(?P<quando>" + _QUANDO_EV +
                             r")\b(?P<orario>\s+(?:alle|verso le|ore)\s+\d{1,2}(?:[:.]\d{2})?)?", re.I)
_NON_EVENTI = re.compile(r"^(?:fame|sete|sonno|freddo|caldo|voglia|paura|tempo|bisogno|ragione|torto|niente|nulla|"
                         r"da fare|mal di|un po|poco|tanto|troppo|sempre|ancora|gia|già|deciso|capito|"
                         r"(?:\w+(?:ato|uto|ito|ata|uta|ita))\b)", re.I)
_SOLO_VERBO = {"mi sposo", "mi laureo", "mi opero", "parto", "partiro", "partirò", "torno"}


def _domanda_seguito(verbo, cosa):
    """La domanda da amico, giusta per il tipo di evento."""
    v = re.sub(r"\s+", " ", verbo.lower())
    c = re.sub(r"^(?:fare|sostenere|avere)\s+", "", cosa).strip()
    if v == "mi sposo":
        return "Allora, com'è andato il matrimonio?! 💍"
    if v == "mi laureo":
        return "Allora, com'è andata la laurea?! 🎓"
    if v == "mi opero":
        return "Come stai dopo l'operazione? Com'è andata?"
    if v.startswith(("vado", "andr")):
        return f"Com'è andata {c}?" if c else "Com'è andata?"
    if v.startswith("part"):
        return f"Com'è andato il viaggio{' ' + c if c else ''}?"
    if v.startswith(("esco", "uscir")):
        return f"Com'è andata l'uscita{' ' + c if c else ''}?"
    if v.startswith("gioc"):
        return "Com'è andata la partita?"
    if v.startswith(("incontro", "vedo", "vedr")):
        return f"Com'è andato l'incontro con {c}?" if c else "Com'è andato l'incontro?"
    if v.startswith("torno"):
        return f"Com'è andato il ritorno{' ' + c if c else ''}?"
    return f"Com'è andata con {c}?" if c else "Com'è andata?"


def calcola_chiedi(quando, con_orario, ora=None):
    """Quando chiedere com'è andata: un paio d'ore dopo l'evento, o la sera/la mattina dopo."""
    ora = ora or datetime.datetime.now()
    if CONFIG["seguiti_ritardo"] > 0:                     # per demo/test: dopo N secondi
        return ora + datetime.timedelta(seconds=CONFIG["seguiti_ritardo"])
    if con_orario:
        chiedi = quando + datetime.timedelta(hours=2)
    elif quando.hour < 15:
        chiedi = quando.replace(hour=18, minute=0)
    elif quando.hour < 18:
        chiedi = quando.replace(hour=21, minute=0)
    else:
        chiedi = (quando + datetime.timedelta(days=1)).replace(hour=10, minute=0)
    return max(chiedi, ora + datetime.timedelta(hours=1))


def rileva_evento(testo, ora=None):
    """Trova un evento futuro della persona ("domani ho l'esame di storia", "giovedì vado dal dentista").
    Ritorna {"evento", "domanda", "quando", "chiedi"} oppure None. Niente LLM: funziona anche offline."""
    t = (testo or "").strip()
    if not t or t.endswith("?") or len(t) > 400:
        return None
    for rx in (_RE_EVENTO, _RE_EVENTO_DOPO):
        for m in rx.finditer(t):
            verbo = re.sub(r"\s+", " ", m.group("verbo")).lower()
            cosa = (m.group("cosa") or "").strip()
            if re.search(r"\bnon\b", (m.groupdict().get("mezzo") or "") + " " + t[max(0, m.start("verbo") - 5):m.start("verbo")], re.I):
                continue
            cosa = re.split(r"\s+(?:e poi|ma|però|pero|perch[eé]|quindi|cos[iì]|anche se|e\s+(?:sono|ho|mi|non|sto|spero|poi|devo))\b|[,;:()]",
                            cosa, maxsplit=1, flags=re.I)[0].strip(" '\"")
            cosa = re.sub(r"\s+(?:alle|verso le|ore|entro le)\s+\d{1,2}(?:[:.]\d{2})?\s*$", "", cosa, flags=re.I)
            cosa = re.sub(r"\s+(?:" + _QUANDO_EV + r")\s*$", "", cosa, flags=re.I).strip()
            if not cosa and verbo not in _SOLO_VERBO:
                continue
            if cosa and (_NON_EVENTI.search(_senza_accenti(cosa).lower()) or len(cosa) < 3):
                continue
            if verbo in ("devo", "dovro", "dovrò") and re.match(r"(?:ricordar|dir|chieder|pensar|capir|andare a dormire)", cosa, re.I):
                continue
            cosa = cosa[:70]
            pezzo = m.group(0)
            ora_ = ora or datetime.datetime.now()
            quando, _ = parse_quando(pezzo, ora_)
            if re.match(r"oggi|stamattina|stasera|stanotte|questo\s+pomeriggio", m.group("quando"), re.I) \
                    and (not quando or quando.date() != ora_.date()):
                quando = max(quando.replace(day=ora_.day, month=ora_.month, year=ora_.year) if quando else ora_, ora_)
            if not quando:
                continue
            con_orario = bool(re.search(r"\b(?:alle|ore|verso le)\s+\d", t[m.start():m.end() + 25], re.I))
            if con_orario:
                q2, _ = parse_quando(t[m.start():m.end() + 25], ora)
                quando = q2 or quando
            evento = cosa if verbo in ("ho", "avrò", "avro", "c'è", "c'e", "ci sarà", "ci sara", "devo", "dovrò", "dovro") \
                else (verbo + (" " + cosa if cosa else ""))
            evento = re.sub(r"^(?:fare|sostenere)\s+", "", evento).strip()
            return {"evento": evento, "domanda": _domanda_seguito(verbo, cosa), "quando": quando,
                    "chiedi": calcola_chiedi(quando, con_orario, ora)}
    return None


# ════════════════════════════════════════════════════════════
# AGENTE (v10) — il modello usa gli strumenti da solo
# ════════════════════════════════════════════════════════════
# Il modello scrive nella risposta un tag invisibile:  [[azione:{"tipo":"promemoria", ...}]]
# Il server lo toglie dal testo, lo controlla e lo esegue davvero. Per gli strumenti
# "informativi" (meteo, calcoli, documenti…) c'è un secondo giro: il modello riceve i
# risultati e finisce la risposta con i dati veri.
_RE_TAG = re.compile(r"\[\[\s*(?:azione|action|tool|strumento)\s*:?\s*(\{.*?\})\s*\]\]", re.S | re.I)
_RE_TAG_APERTO = re.compile(r"\[\[\s*(?:azione|action|tool|strumento)\b.*\Z", re.S | re.I)

PROMPT_AGENTE = """STRUMENTI — puoi AGIRE davvero, non solo parlare.
Quando la persona ti chiede (anche in modo indiretto) di fare qualcosa, scrivi in fondo alla risposta,
ognuno su una riga, uno o più tag come questi (la persona NON li vede, li esegue il sistema):
[[azione:{"tipo":"promemoria","testo":"chiamare Luca","quando":"domani alle 9"}]]
[[azione:{"tipo":"timer","durata":"10 minuti"}]]
[[azione:{"tipo":"lista","aggiungi":["latte","pane"]}]]   ·   [[azione:{"tipo":"lista","togli":"latte"}]]
[[azione:{"tipo":"nota","testo":"il codice del cancello è 4521"}]]
[[azione:{"tipo":"obiettivo","testo":"correre 5 km"}]]
Se ti servono dati che non sai, scrivi SOLO il tag e fermati: riceverai i risultati e poi risponderai.
[[azione:{"tipo":"meteo","citta":"Milano"}]]   [[azione:{"tipo":"ora","citta":"Tokyo"}]]
[[azione:{"tipo":"calcola","espressione":"(1200*0.22)+35"}]]
[[azione:{"tipo":"cerca_documenti","q":"parole chiave"}]]   [[azione:{"tipo":"cerca_memoria","q":"parole chiave"}]]
Regole: usa i tag solo quando servono; JSON valido su una riga; "quando" in italiano semplice
(«tra 20 minuti», «domani alle 9», «venerdì alle 18:30»). Non dire mai di aver fatto qualcosa senza il tag."""

STRUMENTI_INFO = {"meteo", "ora", "calcola", "cerca_documenti", "cerca_memoria"}
ICONE_STRUMENTI = {"promemoria": "⏰", "timer": "⏱️", "lista": "🛒", "nota": "📝", "obiettivo": "🎯",
                   "personalita": "🎭", "meteo": "🌤️", "ora": "🕒", "calcola": "🧮",
                   "cerca_documenti": "📚", "cerca_memoria": "🧠"}


class FiltroTag:
    """Avvolge on_token: lascia passare il testo e trattiene i tag [[azione:…]] (anche spezzati tra chunk)."""

    def __init__(self, on_token):
        self.out, self.buf = on_token, ""

    PAROLE = ("azione", "action", "tool", "strumento")

    def __call__(self, chunk):
        self.buf += chunk
        while self.buf:
            i = self.buf.find("[[")
            if i < 0:
                tieni = 1 if self.buf.endswith("[") else 0          # forse è l'inizio di "[["
                if len(self.buf) > tieni:
                    self.out(self.buf[:len(self.buf) - tieni])
                self.buf = self.buf[len(self.buf) - tieni:]
                return
            if i:
                self.out(self.buf[:i])
                self.buf = self.buf[i:]
            testa = self.buf[2:].lstrip()[:12].lower()
            if not any(testa.startswith(p) for p in self.PAROLE):
                if any(p.startswith(testa) for p in self.PAROLE) and len(self.buf) < 40:
                    return                                          # ancora non si capisce: aspetta
                self.out(self.buf[:2])                              # non è un tag: mostralo
                self.buf = self.buf[2:]
                continue
            j = self.buf.find("]]")
            if j < 0:
                if len(self.buf) > 1500:                            # tag mai chiuso: lascia perdere
                    self.buf = ""
                return
            self.buf = self.buf[j + 2:]

    def fine(self):
        if self.buf and not _RE_TAG_APERTO.match(self.buf):
            self.out(self.buf)
        self.buf = ""


class Agente:

    @staticmethod
    def estrai(testo):
        """Ritorna (testo senza tag, [richieste]). Tollera JSON con apici singoli e tag lasciati aperti."""
        richieste, viste = [], set()
        corpi = [m.group(1) for m in _RE_TAG.finditer(testo)]
        aperto = _RE_TAG_APERTO.search(_RE_TAG.sub("", testo))
        if aperto:
            m = re.search(r"\{.*\}", aperto.group(0), re.S)
            if m:
                corpi.append(m.group(0))
        for corpo in corpi:
            a = None
            for prova in (corpo, corpo.replace("'", '"')):
                try:
                    a = json.loads(prova)
                    break
                except Exception:
                    continue
            if isinstance(a, dict) and isinstance(a.get("tipo"), str):
                chiave = json.dumps(a, sort_keys=True, ensure_ascii=False)
                if chiave not in viste:
                    viste.add(chiave)
                    richieste.append(a)
        pulito = _RE_TAG_APERTO.sub("", _RE_TAG.sub("", testo))
        pulito = re.sub(r"[ \t]+\n", "\n", pulito)
        pulito = re.sub(r"\n{3,}", "\n\n", pulito).strip()
        return pulito, richieste[:6]

    @staticmethod
    def esegui(a, memoria):
        """Esegue una richiesta dopo averla controllata. Ritorna {tipo, ok, icona, esito, [dati], [fonti]}."""
        tipo = str(a.get("tipo", "")).strip().lower().replace("-", "_")
        tipo = {"reminder": "promemoria", "spesa": "lista", "calcolo": "calcola", "calc": "calcola",
                "documenti": "cerca_documenti", "memoria": "cerca_memoria", "orario": "ora"}.get(tipo, tipo)
        s = lambda k, n=200: re.sub(r"\s+", " ", str(a.get(k) or "")).strip()[:n]
        r = {"tipo": tipo, "ok": False, "icona": ICONE_STRUMENTI.get(tipo, "🔧"), "esito": ""}
        try:
            if tipo == "promemoria":
                testo, qt = s("testo", 120) or s("cosa", 120), s("quando", 60)
                if len(testo) < 2:
                    return dict(r, esito="promemoria senza testo")
                quando = None
                if qt:
                    quando, _ = parse_quando(qt)
                    if not quando and re.fullmatch(r"\d{1,2}(?:[:.]\d{2})?", qt):
                        quando, _ = parse_quando("alle " + qt)
                q_iso = quando.isoformat(timespec="seconds") if quando else None
                poco_fa = (datetime.datetime.now() - datetime.timedelta(minutes=10)).isoformat(timespec="seconds")
                if any(p["testo"].lower() == testo.lower() and (p.get("quando") == q_iso or p.get("creato", "") >= poco_fa)
                       for p in memoria.promemoria_attivi()):
                    return dict(r, ok=True, esito=f"«{testo}» era già impostato")
                memoria.aggiungi_promemoria(testo, quando, "promemoria")
                return dict(r, ok=True, esito=f"«{testo}» " + (fmt_quando(quando) if quando else "(senza orario)"))
            if tipo == "timer":
                sec = parse_durata(s("durata", 40))
                if not sec and isinstance(a.get("secondi"), (int, float)):
                    sec = int(a["secondi"])
                if not 0 < sec <= 2 * 86400:
                    return dict(r, esito="durata del timer non valida")
                quando = datetime.datetime.now() + datetime.timedelta(seconds=sec)
                memoria.aggiungi_promemoria(f"Timer di {fmt_durata(sec)}", quando, "timer")
                return dict(r, ok=True, esito=f"timer di {fmt_durata(sec)} (suona alle {quando.strftime('%H:%M:%S')})")
            if tipo == "lista":
                agg = a.get("aggiungi", a.get("voci", a.get("voce")))
                agg = [agg] if isinstance(agg, str) else (agg if isinstance(agg, list) else [])
                agg = [re.sub(r"\s+", " ", str(v)).strip()[:80] for v in agg[:12] if str(v).strip()]
                togli = a.get("togli", a.get("rimuovi"))
                togli = [togli] if isinstance(togli, str) else (togli if isinstance(togli, list) else [])
                fatto = []
                if agg:
                    nuove = memoria.lista_aggiungi(agg)
                    fatto.append("aggiunto " + ", ".join(nuove) if nuove else "era già tutto in lista")
                for v in togli[:6]:
                    if memoria.lista_rimuovi(str(v)):
                        fatto.append(f"tolto {v}")
                if not fatto:
                    return dict(r, esito="niente da cambiare nella lista")
                return dict(r, ok=True, esito="; ".join(fatto))
            if tipo == "nota":
                testo = s("testo", 300)
                if len(testo) < 2:
                    return dict(r, esito="nota vuota")
                if not any(x.get("cosa", "").lower() == testo.lower() for x in memoria.imparato[-50:]):
                    memoria.impara_cosa(testo, "nota")
                return dict(r, ok=True, esito=f"annotato «{testo[:60]}»")
            if tipo == "obiettivo":
                testo = s("testo", 120)
                if len(testo) < 3:
                    return dict(r, esito="obiettivo vuoto")
                memoria.aggiungi_obiettivo(testo, "obiettivo")
                return dict(r, ok=True, esito=f"nuovo obiettivo: {testo}")
            if tipo == "personalita":
                k = s("chiave", 20).lower() or s("modalita", 20).lower()
                k = "prof" if k.startswith("prof") else k
                if not imposta_personalita(k, memoria):
                    return dict(r, esito=f"personalità «{k}» sconosciuta")
                return dict(r, ok=True, esito=f"modalità {PERSONALITA[k][1]}")
            if tipo == "meteo":
                citta = s("citta", 40) or s("città", 40) or memoria.get_valore_profilo("citta") or "Roma"
                d = ottieni_meteo(citta, timeout=6)
                if d.get("errore"):
                    return dict(r, esito=f"meteo di {citta} non disponibile", dati=f"meteo di {citta}: non disponibile (offline?)")
                prev = "; ".join(f"{p['giorno']}: {p['min']}°/{p['max']}° {p['emoji']}"
                                 for p in (d.get("previsioni") or [])[:3])
                dati = (f"meteo a {d['citta']} adesso: {d['temp']}°C, {d['descrizione'].lower()}, percepiti {d['percepita']}°, "
                        f"umidità {d['umidita']}%, vento {d['vento']} km/h. Prossimi giorni: {prev}")
                return dict(r, ok=True, esito=f"{d['citta']} {d['temp']}°C {d['emoji']}", dati=dati)
            if tipo == "ora":
                citta = s("citta", 40) or s("città", 40)
                k = trova_citta(citta) if citta else None
                if citta and not k:
                    d = datetime.datetime.now()
                    return dict(r, esito=f"fuso di {citta} sconosciuto",
                                dati=f"fuso orario di {citta} sconosciuto; qui sono le {d.strftime('%H:%M')}")
                d = ora_in(k) if k else datetime.datetime.now()
                dove = k.title() if k else "qui"
                return dict(r, ok=True, esito=f"{dove} {d.strftime('%H:%M')}",
                            dati=f"ora a {dove}: {d.strftime('%H:%M')} di {GIORNI_LUNGHI[d.weekday()]} {d.day} {MESI_IT[d.month-1]}")
            if tipo == "calcola":
                espr = s("espressione", 120) or s("expr", 120)
                v = calcola(espr)
                if v is None:
                    return dict(r, esito="calcolo non valido", dati=f"«{espr}» non è un calcolo valido")
                return dict(r, ok=True, esito=f"{espr} = {fmt_num(v)}", dati=f"{espr} = {fmt_num(v)}")
            if tipo == "cerca_documenti":
                q = s("q", 120) or s("query", 120)
                trovati = memoria.cerca_documenti(q, k=4, rigida=False)
                if not trovati:
                    return dict(r, ok=True, esito=f"«{q}»: niente nei documenti", dati=f"nei documenti non c'è niente su «{q}»")
                dati = "\n".join(f"[{x['nome']} · parte {x['pezzo']}] {x['testo'][:900]}" for x in trovati)
                return dict(r, ok=True, esito=f"«{q}»: {len(trovati)} risultati", dati=dati,
                            fonti=[{"nome": x["nome"], "pezzo": x["pezzo"], "anteprima": x["testo"][:200]} for x in trovati])
            if tipo == "cerca_memoria":
                q = s("q", 80) or s("query", 80)
                trovati = memoria.cerca(q)
                if not trovati:
                    for w in sorted(_token(q), key=len, reverse=True)[:3]:   # riprova parola per parola
                        trovati = memoria.cerca(w)
                        if trovati:
                            break
                righe = []
                for x in trovati[:8]:
                    righe.append(" · ".join(str(v)[:120] for k, v in x.items() if k != "tipo"))
                return dict(r, ok=True, esito=f"«{q}»: {len(trovati)} ricordi",
                            dati=("\n".join(righe) if righe else f"nessun ricordo su «{q}»"))
            return dict(r, esito=f"strumento «{tipo}» sconosciuto")
        except ZeroDivisionError:
            return dict(r, esito="divisione per zero", dati="divisione per zero: impossibile")
        except Exception as e:
            return dict(r, esito=f"errore: {e}"[:120])


PROMPT_ESTRAZIONE = """Sei il modulo di memoria di un assistente personale.
Leggi il MESSAGGIO dell'utente ed estrai SOLO informazioni NUOVE, personali e durature su di lui/lei
(nome, età, città, lavoro/studio, gusti, abitudini, persone care con il loro ruolo, obiettivi, eventi importanti).
Ignora saluti, domande generiche, opinioni passeggere e tutto ciò che è già noto.

GIÀ NOTO: {noto}

MESSAGGIO: {messaggio}

Rispondi SOLO con un oggetto JSON con queste chiavi:
{{"profilo": {{"chiave": "valore"}}, "fatti": ["frase breve in terza persona"], "persone": [{{"nome": "...", "ruolo": "..."}}], "obiettivi": ["..."], "eventi": [{{"cosa": "esame di storia", "quando": "domani alle 9", "domanda": "Com'è andato l'esame di storia?"}}]}}
"eventi" = solo cose FUTURE che la persona deve fare o vivere (esami, colloqui, visite, viaggi, partite,
appuntamenti), con "quando" in italiano semplice e la domanda che un amico le farebbe DOPO.
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

    def _system_prompt(self, query="", fonti=None):
        ora = datetime.datetime.now()
        oggi = f"{data_it(ora)}, ore {ora.strftime('%H:%M')}"
        documenti = ""
        if fonti:
            blocchi = "\n\n".join(f"[{f['nome']} · parte {f['pezzo']}]\n{f['testo']}" for f in fonti)
            documenti = (f"\n\n--- DAI DOCUMENTI DELLA PERSONA (usali solo se c'entrano con la domanda; quando li usi "
                         f"cita la fonte tra parentesi quadre, es. [{fonti[0]['nome']}]) ---\n{blocchi}\n--- FINE DOCUMENTI ---")
        if CONFIG["agente"]:
            nomi = [d.get("nome", "") for d in self.memoria.documenti[-12:]]
            strumenti = PROMPT_AGENTE + (f"\nDocumenti caricati dalla persona: {', '.join(nomi)}." if nomi else "")
        else:
            strumenti = ("Le azioni pratiche (timer, promemoria, lista, calcoli, ora nel mondo, briefing) le fai quando "
                         "te le chiedono con frasi come «metti un timer di 10 minuti» o «ricordami alle 18 di…»: "
                         "se te le chiedono in modo vago, suggerisci la frase giusta. "
                         "Non dire mai di aver impostato qualcosa se non è successo davvero.")
        return f"""{CONFIG['carattere']}

Oggi è {oggi}.

--- LA TUA MEMORIA DI QUESTA PERSONA ---
{self.memoria.costruisci_contesto(query)}
--- FINE MEMORIA ---{documenti}

Usa questa memoria con naturalezza, senza elencarla meccanicamente.
Se noti che la persona è di umore negativo, sii empatico e presente.
Se ha obiettivi o sogni, tienili a mente e incoraggiala.

{strumenti}"""

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
            for e in ((dati or {}).get("eventi") or [])[:2]:
                s = self._seguito_da_ia(e, testo)
                if s:
                    appreso.append("🔁 " + s["evento"])
            if appreso:
                self.appreso_log.append({"ts": time.time(), "cosa": ", ".join(appreso[:3])})
                self.appreso_log = self.appreso_log[-30:]
            return appreso
        finally:
            self._ia_lock.release()

    def _seguito_da_ia(self, e, fonte):
        """Un evento trovato dal modello: migliora la domanda del follow-up già creato
        dalle regole, oppure ne crea uno nuovo. Ritorna il follow-up nuovo (o None)."""
        if not isinstance(e, dict):
            return None
        pulisci = lambda x, n: re.sub(r"\s+", " ", str(x or "")).strip()[:n]
        cosa, domanda, qt = pulisci(e.get("cosa"), 70), pulisci(e.get("domanda"), 160), pulisci(e.get("quando"), 60)
        if not domanda.endswith("?"):
            domanda = ""
        if any(s.get("fonte") == fonte[:300] for s in self.memoria.seguiti_in_attesa()):
            if domanda:
                self.memoria.aggiorna_seguito_da_fonte(fonte, domanda)
            return None
        if len(cosa) < 3 or not qt:
            return None
        ora = datetime.datetime.now()
        quando, _ = parse_quando(qt, ora)
        if not quando or not (ora < quando < ora + datetime.timedelta(days=15)):
            return None
        chiedi = calcola_chiedi(quando, bool(re.search(r"\d", qt)), ora)
        return self.memoria.aggiungi_seguito(cosa, quando, chiedi, domanda or f"Com'è andata con {cosa}?", fonte)

    def messaggio_seguito(self, s):
        """Il messaggio che Maik manda da solo quando è il momento di chiedere com'è andata."""
        nome = self.memoria.get_valore_profilo("nome")
        apertura = random.choice(["Ehi", "Ciao", "Allora"]) + (f" {nome}" if nome else "")
        domanda = s.get("domanda") or "Com'è andata?"
        return f"{apertura}! 🤞 {domanda} Raccontami tutto!"

    def seguiti_da_chiedere(self, sessione=None):
        """Follow-up arrivati: diventano messaggi di Maik nella chat (e nel diario)."""
        sid = self.memoria.sessione_valida(sessione)
        out = []
        for s in self.memoria.seguiti_scaduti():
            testo = self.messaggio_seguito(s)
            self.memoria.salva_scambio("", testo, sid, extra={"seguito": s["evento"]})
            out.append({"id": s["id"], "evento": s["evento"], "testo": testo})
        return out

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

    def _costruisci_messaggi(self, testo, sessione=None):
        messaggi = []
        for s in self.memoria.ultimi_scambi(6, sessione or Memoria.PRINCIPALE):
            if s.get("tu"):                       # i follow-up di Maik non hanno una domanda
                messaggi.append({"role": "user", "content": s["tu"]})
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
        azioni = []
        if CONFIG["agente"]:
            risposta, richieste = Agente.estrai(risposta)
            azioni = [Agente.esegui(a, self.memoria) for a in richieste if a.get("tipo") not in STRUMENTI_INFO]
        self.memoria.salva_scambio(testo, pulisci_pensiero(risposta) or risposta)
        threading.Thread(target=self._dopo_risposta, args=(testo,), daemon=True).start()
        return self._meta(ok=True, risposta=risposta, imparato=imparato, azioni=azioni)

    def _nota_seguito(self, testo):
        """Regole veloci: se racconti un evento futuro, Maik si segna di chiederti com'è andata."""
        ev = rileva_evento(testo)
        if not ev:
            return None
        s = self.memoria.aggiungi_seguito(ev["evento"], ev["quando"], ev["chiedi"], ev["domanda"], testo)
        return {"evento": s["evento"], "quando": fmt_quando(ev["quando"]), "chiedi": s["chiedi"]}

    def rispondi_stream(self, testo, on_token, allegato=None, rigenera=False, sessione=None, on_evento=None):
        """Versione in streaming: chiama on_token(chunk) e ritorna i metadati finali.
        allegato = {"nome", "contenuto"}: un file di testo che va al modello ma NON alle azioni/estrattori.
        rigenera = True: rifà l'ultima risposta (toglie lo scambio precedente dal diario).
        sessione = la chat (v10). on_evento(dict) = avvisi in diretta (es. strumento usato dall'agente)."""
        sid = self.memoria.sessione_valida(sessione)
        avvisa = on_evento or (lambda e: None)
        if rigenera:
            self.memoria.rimuovi_ultimo_scambio(testo, sid)
        if not allegato:
            cmd = self._gestisci_comando(testo)
            if cmd:
                return {"done": True, "comando": cmd}
            azione = Azioni.prova(testo, self.memoria)   # azioni pratiche: istantanee, anche offline
            if azione:
                on_token(azione)
                self.memoria.salva_scambio(testo, azione, sid)
                return self._meta(done=True, ok=True, azione=True, sessione=sid)
        nuovo = bool(testo) and not rigenera
        imparato = Estrattore.analizza(testo, self.memoria) if nuovo else None
        seguito = self._nota_seguito(testo) if nuovo and not allegato else None
        msg, nome = testo, ""
        if allegato:
            nome = str(allegato.get("nome") or "file")[:80]
            contenuto = str(allegato.get("contenuto") or "")[:12000]
            msg = (f"{testo or 'Analizza questo file e dimmi cosa contiene.'}\n\n"
                   f"📎 File «{nome}»:\n```\n{contenuto}\n```")
        fonti = self.memoria.cerca_documenti(testo, k=3) if testo and not allegato else []
        system = self._system_prompt(testo or nome, fonti)
        messaggi = self._costruisci_messaggi(msg, sid)
        stat = {}
        agente = CONFIG["agente"]
        filtro = FiltroTag(on_token) if agente else on_token
        risposta = self.cervello.pensa_stream(system, messaggi, filtro, stat)
        if agente:
            filtro.fine()
        if not risposta or risposta.startswith("__ERRORE"):
            return {"done": True, "ok": False,
                    "risposta": "Ollama non risponde. Controlla che sia acceso."}
        finale, azioni = pulisci_pensiero(risposta) or risposta, []
        if agente:
            finale, richieste = Agente.estrai(pulisci_pensiero(risposta))
            info = [a for a in richieste if str(a.get("tipo", "")).lower() in STRUMENTI_INFO][:3]
            for a in richieste:
                if a not in info:
                    azioni.append(Agente.esegui(a, self.memoria))
            if info:
                # secondo giro: il modello riceve i risultati veri e finisce la risposta
                risultati = []
                for a in info:
                    r = Agente.esegui(a, self.memoria)
                    risultati.append(r)
                    azioni.append(r)
                    avvisa({"strumento": {k: r.get(k) for k in ("tipo", "ok", "icona", "esito")}})
                    for f in r.get("fonti") or []:
                        if not any(f["nome"] == x["nome"] and f["pezzo"] == x["pezzo"] for x in fonti):
                            fonti.append(dict(f, testo=f.get("anteprima", "")))
                dati = "\n".join(f"- {r['tipo']}: {r.get('dati') or r['esito']}" for r in risultati)
                seguito_msg = messaggi + [
                    {"role": "assistant", "content": finale or "(controllo…)"},
                    {"role": "user", "content": "[RISULTATI DEGLI STRUMENTI — la persona non li vede]\n" + dati +
                     "\n\nOra continua la risposta alla persona usando questi dati, in modo naturale e senza "
                     "ripetere quello che hai già scritto. Non scrivere altri tag per meteo/ora/calcoli/ricerche."}]
                if finale:
                    on_token("\n\n")
                filtro2, stat2 = FiltroTag(on_token), {}
                r2 = self.cervello.pensa_stream(system, seguito_msg, filtro2, stat2)
                filtro2.fine()
                if r2 and not r2.startswith("__ERRORE"):
                    testo2, rich2 = Agente.estrai(pulisci_pensiero(r2))
                    for a in rich2:
                        if str(a.get("tipo", "")).lower() not in STRUMENTI_INFO:
                            azioni.append(Agente.esegui(a, self.memoria))
                    finale = (finale + "\n\n" + testo2).strip()
                    if stat2.get("tps"):
                        stat.update(tps=stat2["tps"], token=(stat.get("token") or 0) + (stat2.get("token") or 0),
                                    totale_ms=(stat.get("totale_ms") or 0) + (stat2.get("totale_ms") or 0))
                elif not finale:
                    finale = "Ecco cosa ho trovato:\n" + "\n".join(f"- {r['icona']} {r['esito']}" for r in risultati)
                    on_token(finale)
            if not finale and azioni:
                finale = "Fatto! ✅"
                on_token(finale)
        chip = [{k: a.get(k) for k in ("tipo", "ok", "icona", "esito")} for a in azioni]
        fonti_meta = [{"nome": f["nome"], "pezzo": f["pezzo"], "anteprima": f.get("testo", "")[:200],
                       "citata": f["nome"].lower() in finale.lower()} for f in fonti]
        # in memoria va la risposta senza il "ragionamento" <think> e senza tag (risparmia contesto)
        self.memoria.salva_scambio(testo + (f" [📎 {nome}]" if allegato else ""), finale, sid,
                                   extra={"azioni": chip, "fonti": [{"nome": f["nome"], "pezzo": f["pezzo"]} for f in fonti_meta]})
        if nuovo:
            threading.Thread(target=self._dopo_risposta, args=(testo,), daemon=True).start()
        titolo = (self.memoria._sessione(sid) or {}).get("titolo", "")
        return self._meta(done=True, ok=True, imparato=imparato, stat=stat, azioni=chip, fonti=fonti_meta,
                          seguito=seguito, sessione=sid, titolo=titolo)

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
            "agente":      CONFIG["agente"],
            "versione":    VERSIONE,
        }


# ════════════════════════════════════════════════════════════
# APP INSTALLABILE (v10) — manifest, service worker, icone PNG generate
# ════════════════════════════════════════════════════════════
MANIFEST = {
    "name": "MAIK — la tua AI personale", "short_name": "MAIK", "lang": "it",
    "description": "Assistente personale locale con memoria, voce e strumenti.",
    "start_url": "/", "scope": "/", "display": "standalone", "orientation": "any",
    "background_color": "#050a0f", "theme_color": "#050a0f",
    "icons": [{"src": f"/icona-{n}.png", "sizes": f"{n}x{n}", "type": "image/png", "purpose": p}
              for n in (192, 512) for p in ("any", "maskable")],
}

SERVICE_WORKER = """// MAIK service worker: l'interfaccia si apre anche quando la rete fa i capricci.
// Le API (chat, memoria…) vanno SEMPRE al server: in cache c'è solo il guscio dell'app.
const CACHE = 'maik-v""" + VERSIONE + """';
const GUSCIO = ['/', '/manifest.webmanifest', '/icona-192.png', '/icona-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(GUSCIO)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (!GUSCIO.includes(u.pathname) && u.pathname !== '/index.html') return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const copia = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copia)); }
    return r;
  }).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
});
"""

_ICONE, _ICONE_LOCK = {}, threading.Lock()


def _png(w, h, righe):
    """PNG RGB minimale con la sola libreria standard (zlib + struct)."""
    def blocco(tipo, dati):
        return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati) & 0xFFFFFFFF)
    grezzo = b"".join(b"\x00" + bytes(r) for r in righe)
    return (b"\x89PNG\r\n\x1a\n" + blocco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + blocco(b"IDAT", zlib.compress(grezzo, 9)) + blocco(b"IEND", b""))


def icona_png(n):
    """L'icona dell'app: nucleo neurale con la M luminosa, disegnata pixel per pixel (poi resta in cache)."""
    with _ICONE_LOCK:
        if n in _ICONE:
            return _ICONE[n]
        c = (n - 1) / 2
        punti = [(c + x * n, c + y * n) for x, y in ((-0.15, 0.11), (-0.15, -0.11), (0.0, 0.045), (0.15, -0.11), (0.15, 0.11))]
        tratti = [(ax, ay, bx - ax, by - ay, (bx - ax) ** 2 + (by - ay) ** 2) for (ax, ay), (bx, by) in zip(punti, punti[1:])]
        spessore, alone, margine = 0.03 * n, 0.035 * n, 0.12 * n   # oltre il margine l'alone è ~0: niente "riquadro"
        x0, x1 = int(c - 0.15 * n - margine), int(c + 0.15 * n + margine) + 1
        y0, y1 = int(c - 0.11 * n - margine), int(c + 0.11 * n + margine) + 1
        righe = []
        for y in range(n):
            riga = bytearray(3 * n)
            dy = y - c
            for x in range(n):
                dx = x - c
                d = math.sqrt(dx * dx + dy * dy) / n                     # 0 al centro, ~0.7 negli angoli
                t = min(1.0, d / 0.7)
                r, g, b = 12 - 8 * t, 28 - 19 * t, 44 - 31 * t           # sfondo blu notte
                if d < 0.30:                                            # sfera del nucleo
                    k = d / 0.30
                    r, g, b = 8 + 40 * k * k, 34 - 10 * k, 56 + 60 * k * k
                orbita = math.exp(-((d - 0.405) / 0.006) ** 2) * 0.55   # orbita viola sottile
                bordo = math.exp(-((d - 0.30) / 0.011) ** 2)            # luce sul bordo
                aura = math.exp(-((d - 0.30) / 0.055) ** 2) * 0.38
                r += 124 * orbita + 60 * bordo
                g += 58 * orbita + 245 * (bordo + aura)
                b += 237 * orbita + 255 * (bordo + aura)
                if x0 <= x <= x1 and y0 <= y <= y1:                     # la M (distanza dai segmenti)
                    dist = 1e9
                    for ax, ay, vx, vy, l2 in tratti:
                        u = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / l2))
                        ex, ey = x - ax - u * vx, y - ay - u * vy
                        dist = min(dist, ex * ex + ey * ey)
                    dist = math.sqrt(dist)
                    pieno = max(0.0, min(1.0, spessore - dist + 0.5))
                    luce = math.exp(-((dist - spessore) / alone) ** 2) * 0.45 if dist > spessore else 0.45
                    g += 245 * luce
                    b += 255 * luce
                    r = r * (1 - pieno) + 225 * pieno
                    g = g * (1 - pieno) + 255 * pieno
                    b = b * (1 - pieno) + 255 * pieno
                i = 3 * x
                riga[i], riga[i + 1], riga[i + 2] = min(255, int(r)), min(255, int(g)), min(255, int(b))
            righe.append(riga)
        _ICONE[n] = _png(n, n, righe)
        return _ICONE[n]


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

    def _invia(self, corpo, tipo, cache=None):
        if isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        if cache:
            self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(corpo)

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
        if lung <= 0 or lung > 12_000_000:        # niente corpi giganti
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
            # ── v10: conversazioni, documenti, follow-up ──
            elif base == "/sessioni":
                self._json({"sessioni": MOTORE.memoria.sessioni_elenco()})
            elif base == "/sessioni/storia":
                sid = MOTORE.memoria.sessione_valida(qs.get("id", ""))
                self._json({"sessione": sid, "scambi": MOTORE.memoria.storia_sessione(sid)})
            elif base == "/documenti":
                docs = MOTORE.memoria.documenti_elenco()
                self._json({"documenti": docs, "caratteri": sum(d["caratteri"] for d in docs),
                            "limite": Memoria.MAX_DOC_TOTALE})
            elif base == "/documenti/cerca":
                q = qs.get("q", "").strip()
                self._json({"risultati": MOTORE.memoria.cerca_documenti(q, k=6, rigida=False) if q else []})
            elif base == "/seguiti":
                self._json({"seguiti": MOTORE.memoria.seguiti_in_attesa()})
            elif base == "/seguiti/scaduti":
                self._json({"seguiti": MOTORE.seguiti_da_chiedere(qs.get("sessione"))})
            # ── v10: app installabile ──
            elif base == "/manifest.webmanifest":
                self._invia(json.dumps(MANIFEST, ensure_ascii=False), "application/manifest+json; charset=utf-8")
            elif base == "/sw.js":
                self._invia(SERVICE_WORKER, "application/javascript; charset=utf-8", "no-cache")
            elif base in ("/icona-192.png", "/icona-512.png", "/favicon.ico", "/apple-touch-icon.png"):
                n = 512 if "512" in base else 192
                self._invia(icona_png(n), "image/png", "public, max-age=86400")
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

            elif base in ("/imparato/elimina", "/episodio/elimina"):
                try:
                    indice = int(self._read_json_body().get("indice", -1))
                except (TypeError, ValueError):
                    indice = -1
                self._json({"ok": MOTORE.memoria.dimentica_elemento(base.split("/")[1], indice)})

            elif base == "/riassunto/elimina":
                MOTORE.memoria.aggiorna_ricordi(""); self._json({"ok": True})

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

            elif base == "/sessioni/nuova":
                self._json({"ok": True, "sessione": MOTORE.memoria.crea_sessione(self._read_json_body().get("titolo", ""))})

            elif base == "/sessioni/rinomina":
                c = self._read_json_body()
                self._json({"ok": MOTORE.memoria.rinomina_sessione(str(c.get("id", "")), c.get("titolo", ""))})

            elif base == "/sessioni/elimina":
                self._json({"ok": MOTORE.memoria.elimina_sessione(str(self._read_json_body().get("id", "")))})

            elif base == "/documenti":
                c = self._read_json_body()
                info, errore = MOTORE.memoria.aggiungi_documento(c.get("nome", ""), c.get("contenuto", ""))
                self._json({"ok": bool(info), "documento": info, "errore": errore})

            elif base == "/documenti/elimina":
                self._json({"ok": MOTORE.memoria.elimina_documento(str(self._read_json_body().get("id", "")))})

            elif base == "/seguiti/elimina":
                self._json({"ok": MOTORE.memoria.elimina_seguito(str(self._read_json_body().get("id", "")))})

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
        corpo = self._read_json_body()
        testo = str(corpo.get("testo", "")).strip()
        allegato = corpo.get("allegato") if isinstance(corpo.get("allegato"), dict) else None
        rigenera = bool(corpo.get("rigenera"))
        sessione = str(corpo.get("sessione") or "")[:40] or None
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

        if not testo and not allegato:
            invia({"done": True, "ok": False, "risposta": "..."})
            return
        try:
            meta = MOTORE.rispondi_stream(testo, lambda chunk: invia({"t": chunk}), allegato=allegato,
                                          rigenera=rigenera, sessione=sessione, on_evento=invia)
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
<title>MAIK // Server V10</title>
<meta name="theme-color" content="#050a0f">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" type="image/png" href="/icona-192.png">
<link rel="apple-touch-icon" href="/icona-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@700;900&display=swap');
  :root{--accent:#00f5ff;--accent-rgb:0,245,255;--accent2:#7c3aed;--accent2-rgb:124,58,237;--bg-rgb:5,10,15;--cyan:var(--accent);--bg:#050a0f;--bg2:#080d14;--panel:rgba(var(--bg-rgb),.78);--border:rgba(var(--accent-rgb),.18);--text:#c8e8f0;--dim:#5a7a8a;--green:#00ff88;--red:#ff3355;--purple:#a855f7;}
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--text);font-family:'Rajdhani',system-ui,Segoe UI,sans-serif;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
  header{display:flex;align-items:center;gap:12px;padding:0 14px;height:48px;border-bottom:1px solid var(--border);font-size:13px;flex-shrink:0}
  .logo{font-weight:800;letter-spacing:5px;font-family:'Orbitron',monospace;white-space:nowrap}.logo span{color:var(--cyan)}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--red);box-shadow:0 0 8px var(--red)}.dot.on{background:var(--green);box-shadow:0 0 8px var(--green)}.dot.busy{background:var(--purple);box-shadow:0 0 8px var(--purple)}
  .hbtn{background:transparent;border:1px solid var(--border);color:var(--cyan);padding:5px 9px;border-radius:4px;cursor:pointer;font-family:'Share Tech Mono',monospace;font-size:11px;white-space:nowrap}
  .hbtn:hover{background:rgba(var(--accent-rgb),.12)}.hbtn.on{background:rgba(0,255,136,.15);border-color:var(--green);color:var(--green)}
  #wrap{flex:1;display:flex;overflow:hidden}
  #side{width:250px;border-right:1px solid var(--border);padding:14px;overflow:auto;font-size:13px;background:var(--panel);flex-shrink:0;transition:width .25s}
  #side.hidden{width:0;padding:0;overflow:hidden}
  #side h3{font-size:10px;letter-spacing:2px;color:var(--cyan);margin:16px 0 6px;text-transform:uppercase}
  #side h3:first-child{margin-top:0}
  .kv{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(var(--accent-rgb),.06);gap:8px}
  .kv span:last-child{color:#fff;text-align:right}
  .sfield{width:100%;background:rgba(var(--accent-rgb),.05);border:1px solid var(--border);border-radius:4px;padding:7px 10px;color:var(--text);font-size:13px;outline:none;font-family:inherit}
  .sfield:focus{border-color:var(--cyan)}
  .memhit{background:rgba(var(--accent-rgb),.05);border-left:2px solid var(--cyan);padding:4px 8px;font-size:11px;border-radius:0 4px 4px 0;margin-top:4px}
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
  .m.ai{align-self:flex-start;background:rgba(var(--accent-rgb),.07);border:1px solid rgba(var(--accent-rgb),.2);border-radius:4px 12px 12px 12px}
  .m.me{align-self:flex-end;background:rgba(var(--accent-rgb),.14);color:#fff;border-radius:12px 4px 12px 12px}
  #bar{display:flex;gap:8px;padding:11px 12px;border-top:1px solid var(--border);flex-shrink:0;align-items:center}
  .micbtn{background:rgba(var(--accent-rgb),.06);border:1px solid var(--border);color:var(--cyan);width:42px;height:42px;border-radius:50%;font-size:15px;cursor:pointer;flex-shrink:0}
  .micbtn.on{background:rgba(255,51,85,.15);border-color:var(--red);color:var(--red)}
  #inp{flex:1;background:rgba(var(--accent-rgb),.05);border:1px solid var(--border);border-radius:20px;padding:11px 16px;color:#fff;font-size:14px;outline:none;font-family:inherit;min-width:0}
  #inp:focus{border-color:var(--cyan)}
  .send{background:var(--cyan);border:none;color:#050a0f;width:44px;height:44px;border-radius:50%;font-size:16px;cursor:pointer;font-weight:700;flex-shrink:0}
  .send:disabled{opacity:.4}
  .quick{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 10px}
  .quick button{background:transparent;border:1px solid rgba(var(--accent-rgb),.2);color:var(--dim);padding:4px 10px;border-radius:12px;font-size:12px;cursor:pointer;font-family:inherit}
  .quick button:hover{color:var(--cyan);border-color:var(--cyan)}
  .cursor{display:inline-block;width:7px;height:14px;background:var(--cyan);vertical-align:middle;animation:bl 1s infinite}@keyframes bl{50%{opacity:.3}}
  .note{color:var(--dim);font-size:11px;margin-top:14px;line-height:1.5}
  .ov{position:fixed;inset:0;background:rgba(2,6,12,.8);backdrop-filter:blur(4px);z-index:1000;display:none;align-items:center;justify-content:center;padding:16px}
  .ov.open{display:flex}
  .mod{background:var(--bg2);border:1px solid var(--border);border-radius:8px;width:100%;max-width:470px;max-height:88vh;overflow:auto}
  .modh{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg2)}
  .modt{font-family:'Orbitron',monospace;font-size:13px;letter-spacing:2px;color:#fff}
  .ib{background:rgba(var(--accent-rgb),.08);border:1px solid var(--border);color:var(--cyan);width:28px;height:28px;border-radius:4px;cursor:pointer}
  .modb{padding:16px}
  .tgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .tcard{background:rgba(var(--accent-rgb),.05);border:1px solid var(--border);border-radius:8px;padding:14px 8px;text-align:center;cursor:pointer;transition:.15s;display:flex;flex-direction:column;align-items:center;gap:6px}
  .tcard:hover{background:rgba(var(--accent-rgb),.12);border-color:var(--cyan);transform:translateY(-2px)}
  .tcard .ic{font-size:25px}.tcard .nm{font-size:11px}
  #tpanel h4{font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:2px;color:var(--cyan);margin-bottom:10px;text-transform:uppercase}
  .tout{background:rgba(0,0,0,.35);border:1px solid var(--border);border-radius:6px;padding:12px;font-family:'Share Tech Mono',monospace;color:var(--cyan);margin-top:10px;word-break:break-word;min-height:20px;font-size:14px}
  .tbig{font-family:'Orbitron',monospace;font-size:30px;color:#fff;text-align:center;letter-spacing:1px}
  .trow{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
  .tbtn{flex:1;min-width:64px;background:rgba(var(--accent-rgb),.08);border:1px solid var(--border);color:var(--cyan);padding:9px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:13px;font-weight:600}
  .tbtn:hover{background:rgba(var(--accent-rgb),.15)}.tbtn.solid{background:var(--cyan);color:#050a0f;border:none}
  .tfield{width:100%;background:rgba(var(--accent-rgb),.05);border:1px solid var(--border);border-radius:6px;padding:9px 11px;color:var(--text);font-size:14px;font-family:inherit;outline:none;margin-top:8px}
  .tfield:focus{border-color:var(--cyan)}
  .cg{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}
  .cg button{background:rgba(var(--accent-rgb),.06);border:1px solid var(--border);color:var(--text);padding:12px 0;border-radius:6px;cursor:pointer;font-size:16px;font-family:inherit}
  .cg button:hover{background:rgba(var(--accent-rgb),.12)}.cg button.op{color:var(--cyan)}.cg button.eq{background:var(--cyan);color:#050a0f;grid-column:span 2}.cg button.s2{grid-column:span 2}
  .crow{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(var(--accent-rgb),.07)}.crow .c{color:var(--dim)}.crow .t{font-family:'Orbitron',monospace;color:#fff}
  .nitem{background:rgba(var(--accent-rgb),.04);border-left:2px solid var(--cyan);padding:7px 9px;border-radius:0 6px 6px 0;margin-top:6px;font-size:13px;display:flex;justify-content:space-between;gap:8px}
  .nx{background:none;border:none;color:var(--dim);cursor:pointer}.nx:hover{color:var(--red)}
  #toast{position:fixed;top:58px;right:16px;z-index:2000;display:flex;flex-direction:column;gap:6px}
  .tst{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--cyan);padding:8px 14px;border-radius:4px;font-size:12px;max-width:280px}
  .tst.ok{border-left-color:var(--green)}.tst.err{border-left-color:var(--red)}
  .m.ai{white-space:normal}.m b{color:#fff}.m ul{margin:4px 0 4px 18px}.m li{margin:2px 0}
  .m code{background:rgba(var(--accent-rgb),.1);padding:1px 5px;border-radius:3px;font-family:'Share Tech Mono',monospace;font-size:.92em}
  .think{background:rgba(168,85,247,.08);border:1px solid rgba(168,85,247,.3);border-radius:6px;padding:4px 8px;margin-bottom:6px;font-size:12px;color:#b9a3d9}
  .think summary{cursor:pointer;color:var(--purple);font-family:'Share Tech Mono',monospace;letter-spacing:1px}
  .think div{white-space:pre-wrap;margin-top:4px;max-height:180px;overflow:auto}
  .m.alarm{border-color:var(--green)!important;box-shadow:0 0 18px rgba(0,255,136,.25);animation:ring .25s ease 6}
  @keyframes ring{0%,100%{transform:translateX(0)}25%{transform:translateX(-3px)}75%{transform:translateX(3px)}}
  .pchips{display:flex;flex-wrap:wrap;gap:5px}
  .pchip{background:rgba(var(--accent-rgb),.05);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:12px;font-size:11px;cursor:pointer;font-family:inherit}
  .pchip:hover{border-color:var(--cyan)}.pchip.on{background:rgba(var(--accent-rgb),.18);border-color:var(--cyan);color:#fff}
  .pr{display:flex;justify-content:space-between;gap:6px;align-items:flex-start;padding:5px 0;border-bottom:1px solid rgba(var(--accent-rgb),.06);font-size:12px}
  .pr small{display:block;color:var(--dim);font-size:10px}
  @media(max-width:480px){header{padding:0 10px;gap:8px}.logo span,#stato,.hx{display:none}.hbtn{padding:5px 7px}}
  header>div:last-child{flex-shrink:0}
  /* ===== V9: aurora, vetro, bolle, azioni, allegati, memoria, temi ===== */
  body::before{content:'';position:fixed;inset:-20%;z-index:0;pointer-events:none;
    background:radial-gradient(40% 35% at 20% 25%,rgba(var(--accent-rgb),.10),transparent 70%),radial-gradient(35% 40% at 80% 70%,rgba(var(--accent2-rgb),.12),transparent 70%);
    animation:aurora 26s ease-in-out infinite alternate}
  @keyframes aurora{from{transform:translate3d(-3%,-2%,0)}to{transform:translate3d(3%,2%,0) rotate(8deg)}}
  header,#wrap{position:relative;z-index:1}
  header{background:rgba(var(--bg-rgb),.72);backdrop-filter:blur(14px) saturate(140%);-webkit-backdrop-filter:blur(14px) saturate(140%)}
  #side{background:rgba(var(--bg-rgb),.62);backdrop-filter:blur(16px) saturate(140%);-webkit-backdrop-filter:blur(16px) saturate(140%)}
  #msgs{background:rgba(var(--bg-rgb),.4)}
  .logo span{color:var(--accent);text-shadow:0 0 14px rgba(var(--accent-rgb),.6)}
  .m.ai{position:relative;margin-left:34px;background:linear-gradient(135deg,rgba(var(--accent-rgb),.10),rgba(var(--accent2-rgb),.07));border-color:rgba(var(--accent-rgb),.22);box-shadow:0 6px 22px rgba(0,0,0,.25)}
  .m.ai::before{content:'';position:absolute;left:-34px;top:6px;width:24px;height:24px;border-radius:50%;
    background:radial-gradient(circle,#fff 0 12%,rgba(var(--accent-rgb),.9) 22%,rgba(var(--accent2-rgb),.35) 55%,transparent 72%);box-shadow:0 0 14px rgba(var(--accent-rgb),.45);animation:av 3.2s ease-in-out infinite}
  @keyframes av{0%,100%{transform:scale(.92);opacity:.85}50%{transform:scale(1.05);opacity:1}}
  .m.me{background:linear-gradient(135deg,rgba(var(--accent-rgb),.24),rgba(var(--accent-rgb),.12));border:1px solid rgba(var(--accent-rgb),.32)}
  .m img.att{display:block;max-width:min(240px,100%);border-radius:8px;margin-bottom:6px;border:1px solid rgba(var(--accent-rgb),.3)}
  .fchip{display:inline-block;background:rgba(0,0,0,.25);border:1px solid rgba(var(--accent-rgb),.3);border-radius:7px;padding:2px 8px;font-size:12px;margin-bottom:6px;font-family:'Share Tech Mono',monospace}
  .acts{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin-top:0;max-height:0;overflow:hidden;opacity:0;transition:opacity .2s,max-height .2s,margin .2s}
  .m.ai:hover .acts,.m.ai:focus-within .acts,.m.ai.last .acts{opacity:1;max-height:60px;margin-top:6px}
  @media(hover:none){.acts{opacity:.7;max-height:60px;margin-top:6px}}
  .acts button{white-space:nowrap;background:rgba(var(--accent-rgb),.06);border:1px solid rgba(var(--accent-rgb),.18);color:var(--dim);border-radius:6px;font-size:11px;padding:2px 7px;cursor:pointer;font-family:inherit}
  .acts button:hover{color:var(--accent);border-color:var(--accent)}.acts .act-regen{display:none}.m.ai.last .act-regen{display:inline-block}
  .acts .meta{font-family:'Share Tech Mono',monospace;font-size:9.5px;letter-spacing:1px;color:var(--dim);margin-left:4px}.acts .meta b{color:var(--accent);font-weight:400}
  .mc .md-h{display:block;color:#fff;margin:6px 0 2px}
  #attbtn,#stopbtn{width:42px;height:42px;border-radius:50%;cursor:pointer;flex-shrink:0;font-size:15px;background:rgba(var(--accent-rgb),.06);border:1px solid var(--border);color:var(--accent)}
  #stopbtn{display:none;background:rgba(255,51,85,.15);border-color:var(--red);color:var(--red)}
  #attprev{display:none;align-items:center;gap:8px;margin:0 12px 8px;padding:6px 8px;border-radius:10px;background:rgba(var(--accent-rgb),.07);border:1px dashed rgba(var(--accent-rgb),.35);font-size:12px}
  #attprev.on{display:flex}#attprev img{width:38px;height:38px;object-fit:cover;border-radius:6px}#attprev .x{margin-left:auto;background:none;border:none;color:var(--dim);cursor:pointer;font-size:14px}
  #main.drop{outline:2px dashed var(--accent);outline-offset:-8px}
  .thsw{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
  .thsw button{display:flex;align-items:center;gap:6px;border:1px solid var(--border);background:rgba(0,0,0,.25);color:var(--text);border-radius:8px;padding:5px 6px;font-size:10px;cursor:pointer;font-family:'Share Tech Mono',monospace}
  .thsw button i{width:14px;height:14px;border-radius:50%;flex-shrink:0}.thsw button.on{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent);color:#fff}
  .opt{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:12px;padding:4px 0}
  .memrow{display:flex;gap:8px;align-items:flex-start;padding:7px 2px;border-bottom:1px solid rgba(var(--accent-rgb),.08);font-size:13px}
  .memrow .tag{font-family:'Share Tech Mono',monospace;font-size:9px;letter-spacing:1px;padding:1px 6px;border-radius:8px;flex-shrink:0;margin-top:2px;background:rgba(var(--accent-rgb),.12);color:var(--accent);text-transform:uppercase}
  .memrow .tag.ia{background:rgba(var(--accent2-rgb),.2);color:#d8c8ff}.memrow .txt{flex:1}
  .memsum{background:rgba(var(--accent2-rgb),.08);border:1px solid rgba(var(--accent2-rgb),.25);border-radius:8px;padding:8px 10px;font-size:13px;margin-bottom:10px;white-space:pre-wrap}
  :focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
  @media(max-width:760px){#side{background:rgba(var(--bg-rgb),.97)}.m.ai{margin-left:28px}.m.ai::before{left:-28px;width:20px;height:20px}.m{max-width:90%}}
  @media(max-width:760px){#side{position:absolute;top:0;bottom:0;left:0;z-index:200;box-shadow:4px 0 20px rgba(0,0,0,.5)}.tgrid{grid-template-columns:repeat(2,1fr)}.logo{font-size:11px;letter-spacing:3px}}
  /* ===== V10: chat, documenti, agente, follow-up, installa ===== */
  .sideh{display:flex;align-items:center;justify-content:space-between;margin:0 0 6px}
  #side .sideh h3{margin:0}
  .newchat{background:rgba(var(--accent-rgb),.1);border:1px solid var(--border);color:var(--accent);border-radius:6px;font-size:11px;padding:3px 9px;cursor:pointer;font-family:inherit;font-weight:600}
  .newchat:hover{background:rgba(var(--accent-rgb),.2)}
  #chats{display:flex;flex-direction:column;gap:3px;max-height:230px;overflow:auto}
  .chat{display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:7px;cursor:pointer;border:1px solid transparent;font-size:12.5px;transition:background .15s}
  .chat:hover{background:rgba(var(--accent-rgb),.06)}
  .chat.on{background:rgba(var(--accent-rgb),.13);border-color:rgba(var(--accent-rgb),.35);color:#fff}
  .chat .ct{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .chat small{color:var(--dim);font-size:10px;font-family:'Share Tech Mono',monospace}
  .chat .cb{visibility:hidden;background:none;border:none;color:var(--dim);cursor:pointer;font-size:12px;padding:0 2px}
  .chat:hover .cb,.chat.on .cb,.chat .cb:focus-visible{visibility:visible}
  .chat .cb:hover{color:var(--accent)}.chat .cb.del:hover{color:var(--red)}
  @media(hover:none){.chat .cb{visibility:visible}}
  .ag{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}
  .ag:empty{display:none}
  .agc{display:inline-flex;align-items:center;gap:4px;max-width:100%;font-size:11.5px;line-height:1.3;padding:3px 9px;border-radius:999px;background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.35);color:#c9ffe6;animation:in .25s ease;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .agc.ko{background:rgba(255,51,85,.08);border-color:rgba(255,51,85,.4);color:#ffc9d2}
  .agc.src{background:rgba(var(--accent2-rgb),.12);border-color:rgba(var(--accent2-rgb),.45);color:#e3d8ff;cursor:help}
  .agc.src.cit{border-color:rgba(var(--accent2-rgb),.9);box-shadow:0 0 10px rgba(var(--accent2-rgb),.3)}
  .agc.fu{background:rgba(255,176,32,.08);border-color:rgba(255,176,32,.45);color:#ffe2a8}
  .m.seguito{border-color:rgba(255,176,32,.55)!important;box-shadow:0 0 18px rgba(255,176,32,.16)}
  .m.seguito .mc::before{content:'🔁 COME PROMESSO';display:block;font-family:'Share Tech Mono',monospace;font-size:9px;letter-spacing:1.5px;color:#ffb020;margin-bottom:4px}
  .ddrop{border:1.5px dashed rgba(var(--accent-rgb),.4);border-radius:10px;padding:16px;text-align:center;font-size:13px;color:var(--dim);display:flex;flex-direction:column;align-items:center;gap:10px;transition:.15s}
  .ddrop.on{background:rgba(var(--accent-rgb),.08);border-color:var(--accent);color:var(--text)}
  .ddrop .tbtn{flex:0 0 auto}
  .dpaste{margin-top:10px;font-size:13px}.dpaste summary{cursor:pointer;color:var(--accent)}
  .dmeta{display:block;color:var(--dim);font-size:10.5px;font-family:'Share Tech Mono',monospace;margin-top:2px}
  .dhit{background:rgba(var(--accent2-rgb),.07);border-left:2px solid rgba(var(--accent2-rgb),.7);padding:6px 9px;border-radius:0 6px 6px 0;margin-top:6px;font-size:12px;line-height:1.45}
  .dhit b{color:#e3d8ff}.dhit mark{background:rgba(var(--accent-rgb),.25);color:#fff;border-radius:2px}
  #instbtn{display:none}
  .cite{display:inline-block;font-size:.82em;font-family:'Share Tech Mono',monospace;padding:0 6px;border-radius:6px;background:rgba(var(--accent2-rgb),.16);border:1px solid rgba(var(--accent2-rgb),.45);color:#e3d8ff;white-space:nowrap}
</style></head>
<body>
<header>
  <div class="logo">M A I K <span>// V10</span></div>
  <span class="dot" id="dot"></span><span id="stato">verifico…</span><span id="speed" class="hx" style="color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:11px"></span>
  <div style="margin-left:auto;display:flex;gap:6px">
    <button class="hbtn hx" onclick="openPalette()" title="Palette comandi (Ctrl+K)" aria-label="Palette comandi">⌘K</button>
    <button class="hbtn" id="fbtn" onclick="toggleFriend()" title="Modalità Amico" aria-label="Modalità Amico">🫂<span class="hx"> AMICO</span></button>
    <button class="hbtn" onclick="guarda()" title="MAIK guarda dalla webcam" aria-label="MAIK guarda dalla webcam">👁️</button>
    <button class="hbtn" onclick="openTools()" title="Strumenti" aria-label="Strumenti">🧰</button>
    <button class="hbtn" id="sidebtn" onclick="toggleSide()" title="Barra laterale" aria-label="Mostra o nascondi la barra laterale">≡</button>
  </div>
</header>
<div id="toast"></div>
<div id="wrap">
  <div id="side">
    <div class="sideh"><h3>💬 Chat</h3><button class="newchat" onclick="newChat()" title="Nuova chat" aria-label="Nuova chat">＋ Nuova</button></div>
    <div id="chats"></div>
    <h3>Stato</h3>
    <div class="kv"><span>Modello</span><span id="s-mod">—</span></div>
    <div class="kv"><span>Visione</span><span id="s-vis">—</span></div>
    <div class="kv"><span>Giorni</span><span id="s-gg">—</span></div>
    <div class="kv"><span>Scambi</span><span id="s-sc">—</span></div>
    <div class="kv"><span>Utente</span><span id="s-ut">—</span></div>
    <div class="kv"><span>Agente</span><span id="s-ag">—</span></div>
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
    <button class="tbtn" style="width:100%;margin-top:8px" onclick="openMem()">🧠 Memoria completa</button>
    <button class="tbtn" style="width:100%;margin-top:6px" onclick="openDocs()">📚 I tuoi documenti<span id="doccount"></span></button>
    <h3>🎨 Tema</h3>
    <div class="thsw" id="themes"></div>
    <h3>⚙ Opzioni</h3>
    <label class="opt">👂 Modalità Amico: solo se dico «Maik»<input type="checkbox" id="optwake" onchange="setOpt('wake',this.checked)"></label>
    <label class="opt">✨ Animazione di avvio<input type="checkbox" id="optboot" onchange="setOpt('boot',this.checked)"></label>
    <button class="tbtn solid" id="instbtn" style="width:100%;margin-top:8px" onclick="installa()">📲 Installa MAIK come app</button>
    <div class="note">Memoria su disco, condivisa da tutte le chat. MAIK impara da solo 🧠 e <b>agisce da solo</b> 🤖: chiedigli le cose a parole tue («stasera pasta, metti in lista gli ingredienti»). <b>📚</b> legge i tuoi documenti e cita la fonte · <b>🔁</b> si ricorda di chiederti com'è andata · <b>🫂 AMICO</b>: ti vede e ti parla.</div>
  </div>
  <div id="main">
    <div id="sphere-area">
      <div id="fbadge"><span class="fbdot"></span> MAIK · MODALITÀ AMICO</div>
      <div id="cambox"><video id="cam" autoplay muted playsinline></video><div id="fstat">webcam</div></div>
      <div id="sphere-wrap"><canvas id="sph" width="200" height="200"></canvas></div>
    </div>
    <div id="msgs"></div>
    <div class="quick">
      <button onclick="newChat()">💬 nuova chat</button>
      <button onclick="qs('briefing')">☀️ briefing</button>
      <button onclick="q('Metti un timer di 5 minuti')">⏱️ timer</button>
      <button onclick="q('Ricordami alle 18 di ')">⏰ ricordami…</button>
      <button onclick="qs('Cosa c\'è nella lista?')">🛒 lista</button>
      <button onclick="openDocs()">📚 documenti</button>
      <button onclick="guarda()">👁️ guardami</button>
      <button onclick="q('Mi chiamo ')">mi chiamo…</button>
      <button onclick="qs('aiuto')">❓ aiuto</button>
    </div>
    <div id="attprev" aria-live="polite"></div>
    <div id="bar">
      <button id="attbtn" onclick="$('#attin').click()" title="Allega un'immagine (MAIK la guarda) o un file di testo" aria-label="Allega un file">📎</button>
      <input type="file" id="attin" accept="image/*,.txt,.md,.csv,.tsv,.json,.js,.ts,.py,.html,.htm,.css,.xml,.yml,.yaml,.ini,.toml,.log,.sql,.java,.c,.h,.cpp,.cs,.go,.rs,.rb,.php,.sh,.bat,.ps1,.r" style="display:none" onchange="onAttIn(event)">
      <button class="micbtn" id="mic" onclick="toggleMic()" title="Voce" aria-label="Parla con MAIK">🎤</button>
      <input id="inp" placeholder="Scrivi a Maik…" onkeydown="if(event.key==='Enter')invia()">
      <button id="stopbtn" onclick="stopGen()" title="Ferma" aria-label="Ferma la risposta">■</button>
      <button class="send" id="send" onclick="invia()" aria-label="Invia">➤</button>
    </div>
  </div>
</div>

<div class="ov" id="mmodal">
  <div class="mod" style="max-width:560px">
    <div class="modh"><div class="modt">🧠 MEMORIA DI MAIK</div><button class="ib" onclick="closeMem()" aria-label="Chiudi">✕</button></div>
    <div class="modb"><input class="sfield" id="memf" placeholder="Filtra i ricordi…" oninput="renderMem()" style="margin-bottom:10px"><div id="membody"></div></div>
  </div>
</div>

<div class="ov" id="dmodal">
  <div class="mod" style="max-width:600px">
    <div class="modh"><div class="modt">📚 I TUOI DOCUMENTI</div><button class="ib" onclick="closeDocs()" aria-label="Chiudi">✕</button></div>
    <div class="modb">
      <div class="ddrop" id="ddrop"><span>⬆️ Trascina qui i tuoi file di testo (appunti, ricette, contratti, manuali, codice…)</span>
        <button class="tbtn solid" type="button" onclick="$('#docin').click()">📂 Scegli i file</button>
        <input type="file" id="docin" multiple accept=".txt,.md,.csv,.tsv,.json,.js,.ts,.py,.html,.htm,.css,.xml,.yml,.yaml,.ini,.toml,.log,.sql,.java,.c,.h,.cpp,.cs,.go,.rs,.rb,.php,.sh,.bat,.ps1,.r,.srt,.tex,.rtf,text/*" style="display:none" onchange="docFiles(this.files);this.value=''"></div>
      <details class="dpaste"><summary>✍️ oppure incolla un testo</summary>
        <input class="tfield" id="dpn" placeholder="Titolo (es. appunti di biologia)">
        <textarea class="tfield" id="dpt" style="min-height:90px" placeholder="Incolla qui il testo…"></textarea>
        <div class="trow"><button class="tbtn solid" type="button" onclick="docPaste()">📚 Salva nei documenti</button></div></details>
      <div class="note" style="margin-top:10px">MAIK li divide in pezzi e, quando gli fai una domanda, usa i pezzi giusti e <b>cita la fonte</b>. Restano sul tuo computer.</div>
      <input class="sfield" id="docq" placeholder="🔎 Prova a cercare nei documenti…" oninput="docSearch()" style="margin-top:10px">
      <div id="docres"></div>
      <div id="doclist"></div>
      <div id="docspace" class="note"></div>
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
/* ============================================================
   MAIK KIT v9 — grafica e componenti condivisi
   (identico in index.html e nella GUI del server)
   · Neural Core: nucleo neurale 3D nitido su ogni schermo (HiDPI)
   · Temi coerenti (--accent-rgb) · Avvio con controlli reali
   · Palette comandi Ctrl+K · Evidenziazione del codice · Microfono
   ============================================================ */
const MaikKit = (() => {
  const reduceMotion = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  const touch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  const hexRgb = h => { h = String(h || '#00f5ff').replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join('');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // ---------------- TEMI ----------------
  const THEMES = {
    neon:      { nm: 'Neon',      accent: '#00f5ff', accent2: '#7c3aed', bg: '#050a0f' },
    synthwave: { nm: 'Synthwave', accent: '#ff4fd8', accent2: '#6d28d9', bg: '#0a0612' },
    matrix:    { nm: 'Matrix',    accent: '#00ff88', accent2: '#0891b2', bg: '#030a06' },
    solar:     { nm: 'Solar',     accent: '#ffb020', accent2: '#ff3d6e', bg: '#0d0805' },
    ice:       { nm: 'Ice',       accent: '#a5f3fc', accent2: '#6366f1', bg: '#060912' },
    ruby:      { nm: 'Ruby',      accent: '#ff3d5a', accent2: '#f59e0b', bg: '#0d0507' },
  };
  function applyTheme(key) {
    const t = THEMES[key] || THEMES.neon, s = document.documentElement.style;
    const a = hexRgb(t.accent), a2 = hexRgb(t.accent2), b = hexRgb(t.bg);
    s.setProperty('--accent', t.accent);   s.setProperty('--accent-rgb', a.join(','));
    s.setProperty('--accent2', t.accent2); s.setProperty('--accent2-rgb', a2.join(','));
    s.setProperty('--bg', t.bg);           s.setProperty('--bg-rgb', b.join(','));
    const meta = document.querySelector('meta[name=theme-color]'); if (meta) meta.setAttribute('content', t.bg);
    return { key: THEMES[key] ? key : 'neon', accent: a, accent2: a2 };
  }

  // ---------------- NEURAL CORE ----------------
  const STATE_COL = { thinking: [168, 85, 247], listening: [0, 255, 136], detecting: [0, 255, 136], alarm: [255, 196, 0] };
  function core(canvas, opts = {}) {
    const ctx = canvas.getContext('2d');
    const light = opts.light ?? (touch || innerWidth < 700);
    const NO = light ? 84 : 132, NI = light ? 26 : 40;
    const nodes = [], links = [], signals = [], waves = [];
    // due gusci (Fibonacci): esterno + interno, per dare profondità al "cervello"
    const shell = (n, r) => { const inc = Math.PI * (3 - Math.sqrt(5)), off = nodes.length;
      for (let i = 0; i < n; i++) { const y = 1 - (i / (n - 1)) * 2, rr = Math.sqrt(Math.max(0, 1 - y * y)), p = i * inc;
        nodes.push({ x: Math.cos(p) * rr * r, y: y * r, z: Math.sin(p) * rr * r, inner: r < 1, flash: 0, sx: 0, sy: 0, d: 0 }); } return off; };
    shell(NO, 1); shell(NI, 0.55);
    // collegamenti tra vicini (calcolati una volta sola)
    const seen = new Set();
    nodes.forEach((a, i) => {
      nodes.map((b, j) => [j, (a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2]).filter(x => x[0] !== i)
        .sort((p, q) => p[1] - q[1]).slice(0, 3).forEach(([j]) => { const key = i < j ? i + '-' + j : j + '-' + i;
          if (!seen.has(key)) { seen.add(key); links.push([Math.min(i, j), Math.max(i, j)]); } });
    });
    const nbr = nodes.map(() => []); links.forEach(([a, b], li) => { nbr[a].push(li); nbr[b].push(li); });

    let W = 200, state = 'idle', t = 0, rotX = 0.45, rotY = 0, level = 0, levelT = 0, word = 0, lastWave = 0;
    const col = [0, 245, 255], accent = [0, 245, 255], accent2 = [124, 58, 237];

    function resize(px) {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.round(px * dpr); canvas.height = Math.round(px * dpr);
      canvas.style.width = px + 'px'; canvas.style.height = px + 'px'; W = canvas.width;
    }
    function setAccent(a, a2) { accent.splice(0, 3, ...a); accent2.splice(0, 3, ...(a2 || a)); }
    function setState(s) { if (s === state) return; state = s; if (s === 'thinking' || s === 'speaking' || s === 'alarm') wave(); }
    function setLevel(v) { levelT = Math.max(0, Math.min(1, v || 0)); }
    function pulse(k = 1) { word = Math.min(1.6, word + 0.55 * k); }
    function wave() { if (!reduceMotion) { waves.push({ r: 0.35, a: 0.7 }); if (waves.length > 5) waves.shift(); } }
    function spawn(from) {
      if (signals.length > (light ? 26 : 44)) return;
      const ls = from == null ? null : nbr[from];
      const li = ls && ls.length ? ls[(Math.random() * ls.length) | 0] : (Math.random() * links.length) | 0;
      const [a, b] = links[li], dir = from == null ? (Math.random() < 0.5 ? 1 : -1) : (a === from ? 1 : -1);
      signals.push({ li, p: 0, dir, v: 0.025 + Math.random() * 0.035 });
    }

    function frame() {
      const now = performance.now();
      t += reduceMotion ? 0.004 : 0.016;
      const tgt = STATE_COL[state] || accent;
      for (let i = 0; i < 3; i++) col[i] += (tgt[i] - col[i]) * 0.07;          // cambi di colore morbidi
      level += (levelT - level) * 0.3; word *= 0.9;
      const energy = state === 'thinking' ? 1 : state === 'speaking' ? 0.55 + word * 0.5 : state === 'alarm' ? 0.9
                   : state === 'listening' ? 0.25 + level * 1.3 : state === 'detecting' ? 0.35 : 0.14;
      const spin = (reduceMotion ? 0.3 : 1) * (state === 'thinking' ? 0.016 : state === 'speaking' ? 0.009 : 0.0045);
      rotY += spin; rotX += spin * 0.32;
      if (!reduceMotion && Math.random() < energy * 0.55) spawn(null);
      if (state === 'alarm' && now - lastWave > 650) { wave(); lastWave = now; }
      draw(energy);
    }

    function draw(energy) {
      const cx = W / 2, cy = W / 2, R = W * 0.315, k = W / 200, [r, g, b] = col.map(v => v | 0);
      const rgba = (a, c = col) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
      const breath = 1 + Math.sin(t * 2) * 0.014 + word * 0.045 + level * 0.07;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, W);
      ctx.globalCompositeOperation = 'lighter';

      // 1) aura
      let gr = ctx.createRadialGradient(cx, cy, R * 0.2, cx, cy, R * 1.95);
      gr.addColorStop(0, rgba(0.20 + energy * 0.12)); gr.addColorStop(0.55, rgba(0.07, accent2)); gr.addColorStop(1, rgba(0));
      ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(cx, cy, R * 1.95, 0, 6.2832); ctx.fill();

      // 2) anelli HUD (ellissi tratteggiate in movimento + quadrante con tacche + scanner)
      ctx.lineWidth = 1 * k;
      ctx.setLineDash([6 * k, 9 * k]); ctx.lineDashOffset = -t * 30 * k; ctx.strokeStyle = rgba(0.32);
      ctx.beginPath(); ctx.ellipse(cx, cy, R * 1.38, R * 0.42, t * 0.12, 0, 6.2832); ctx.stroke();
      ctx.setLineDash([2 * k, 12 * k]); ctx.lineDashOffset = t * 22 * k; ctx.strokeStyle = rgba(0.28, accent2);
      ctx.beginPath(); ctx.ellipse(cx, cy, R * 1.52, R * 0.6, 1.05 - t * 0.08, 0, 6.2832); ctx.stroke();
      ctx.setLineDash([]);
      const RR = R * 1.72, rot = t * 0.05;
      for (let i = 0; i < 72; i++) {                                   // quadrante con tacche
        const an = rot + i * 0.08727, long = i % 6 === 0, l = (long ? 7 : 3) * k;
        ctx.strokeStyle = rgba(long ? 0.45 : 0.18); ctx.lineWidth = (long ? 1.4 : 0.8) * k;
        ctx.beginPath(); ctx.moveTo(cx + Math.cos(an) * RR, cy + Math.sin(an) * RR);
        ctx.lineTo(cx + Math.cos(an) * (RR - l), cy + Math.sin(an) * (RR - l)); ctx.stroke();
      }
      const sc = t * (state === 'thinking' ? 2.6 : 0.9);              // arco "scanner"
      ctx.lineWidth = 2.2 * k; ctx.lineCap = 'round';
      for (let i = 0; i < 10; i++) { ctx.strokeStyle = rgba(0.06 * (i + 1)); ctx.beginPath();
        ctx.arc(cx, cy, RR + 5 * k, sc + i * 0.06, sc + i * 0.06 + 0.07); ctx.stroke(); }
      ctx.lineCap = 'butt';

      // 3) proiezione 3D dei nodi
      const cY = Math.cos(rotY), sY = Math.sin(rotY), cX = Math.cos(rotX), sX = Math.sin(rotX);
      for (const n of nodes) {
        let x = n.x * cY - n.z * sY, z = n.x * sY + n.z * cY; const y = n.y * cX - z * sX; z = n.y * sX + z * cX;
        const p = 1 / (1.85 - z * 0.85);
        n.sx = cx + x * R * p * breath; n.sy = cy + y * R * p * breath; n.d = (z + 1) / 2; n.flash *= 0.92;
      }
      // 4) collegamenti, raggruppati per luminosità (pochi stroke = veloce)
      const bins = [[], [], [], []];
      for (const [a, c] of links) { const d = (nodes[a].d + nodes[c].d) / 2; bins[Math.min(3, (d * 4) | 0)].push(a, c); }
      bins.forEach((arr, bi) => { if (!arr.length) return; ctx.strokeStyle = rgba((0.06 + bi * 0.075) * (0.75 + energy * 0.5));
        ctx.lineWidth = (0.55 + bi * 0.2) * k; ctx.beginPath();
        for (let i = 0; i < arr.length; i += 2) { const A = nodes[arr[i]], B = nodes[arr[i + 1]]; ctx.moveTo(A.sx, A.sy); ctx.lineTo(B.sx, B.sy); }
        ctx.stroke(); });
      // 5) nodi
      for (const n of nodes) {
        const f = n.inner ? 0.55 : 1, a = (0.18 + n.d * 0.62) * f + n.flash * 0.8, s = (0.45 + n.d * 1.25) * k * (n.inner ? 0.75 : 1) + n.flash * 1.6 * k;
        ctx.fillStyle = `rgba(${Math.min(255, r + 80 * n.d) | 0},${Math.min(255, g + 80 * n.d) | 0},${Math.min(255, b + 80 * n.d) | 0},${Math.min(1, a)})`;
        ctx.beginPath(); ctx.arc(n.sx, n.sy, s, 0, 6.2832); ctx.fill();
      }
      // 6) impulsi che corrono lungo le sinapsi
      for (let i = signals.length - 1; i >= 0; i--) {
        const sg = signals[i]; sg.p += sg.v; const [a, c] = links[sg.li];
        const A = nodes[sg.dir > 0 ? a : c], B = nodes[sg.dir > 0 ? c : a];
        if (sg.p >= 1) { B.flash = 1; signals.splice(i, 1); if (Math.random() < 0.45 * energy + 0.1) spawn(nodes.indexOf(B)); continue; }
        const x = A.sx + (B.sx - A.sx) * sg.p, y = A.sy + (B.sy - A.sy) * sg.p;
        ctx.fillStyle = rgba(0.18); ctx.beginPath(); ctx.arc(x, y, 3.2 * k, 0, 6.2832); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.beginPath(); ctx.arc(x, y, 1.1 * k, 0, 6.2832); ctx.fill();
      }
      // 7) nucleo
      const cr = R * (0.13 + Math.sin(t * 3.2) * 0.012 + word * 0.05 + level * 0.07);
      gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, cr * 2.3);
      gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.22, rgba(0.55)); gr.addColorStop(1, rgba(0));
      ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(cx, cy, cr * 2.3, 0, 6.2832); ctx.fill();
      ctx.setLineDash([3 * k, 5 * k]); ctx.lineDashOffset = t * 20 * k; ctx.strokeStyle = rgba(0.55); ctx.lineWidth = 1 * k;
      ctx.beginPath(); ctx.arc(cx, cy, cr * 1.75, 0, 6.2832); ctx.stroke(); ctx.setLineDash([]);

      // 8) anello voce: barre quando parla, onda morbida quando ascolta
      if (state === 'speaking' || state === 'listening') {
        const base = R * 1.12, M = 72;
        if (state === 'speaking') {
          ctx.lineWidth = 2 * k; ctx.strokeStyle = rgba(0.75); ctx.beginPath();
          for (let i = 0; i < M; i++) { const an = i / M * 6.2832;
            const h = (2 + (0.4 + 0.6 * Math.abs(Math.sin(t * 7 + i * 0.7) * Math.cos(t * 3.3 + i * 0.23))) * (6 + word * 13)) * k;
            ctx.moveTo(cx + Math.cos(an) * base, cy + Math.sin(an) * base); ctx.lineTo(cx + Math.cos(an) * (base + h), cy + Math.sin(an) * (base + h)); }
          ctx.stroke();
        } else {
          for (let ring = 0; ring < 2; ring++) {
            ctx.lineWidth = (ring ? 1 : 1.6) * k; ctx.strokeStyle = rgba(ring ? 0.35 : 0.75); ctx.beginPath();
            for (let i = 0; i <= M; i++) { const an = i / M * 6.2832;
              const rr = base + ring * 7 * k + (1.5 + level * 11 * (0.55 + 0.45 * Math.sin(i * 0.52 + t * 8 + ring * 2)) * (0.6 + 0.4 * Math.sin(i * 0.13 - t * 3))) * k;
              const x = cx + Math.cos(an) * rr, y = cy + Math.sin(an) * rr; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
            ctx.stroke();
          }
        }
      }
      // 9) onde d'urto ai cambi di stato
      for (let i = waves.length - 1; i >= 0; i--) {
        const w = waves[i]; w.r += 0.035; w.a *= 0.955;
        if (w.a < 0.02) { waves.splice(i, 1); continue; }
        ctx.strokeStyle = rgba(w.a); ctx.lineWidth = 2 * k; ctx.beginPath(); ctx.arc(cx, cy, R * w.r * 1.6, 0, 6.2832); ctx.stroke();
      }
      ctx.globalCompositeOperation = 'source-over';
    }
    resize(opts.size || 200);
    return { resize, setAccent, setState, setLevel, pulse, wave, frame, get state() { return state; } };
  }

  // ---------------- LIVELLO DEL MICROFONO (solo desktop: sul telefono può disturbare il riconoscimento vocale) ----------------
  function mic() {
    let stream = null, an = null, ac = null, buf = null, on = false, starting = false;
    async function start() {
      if (on || starting || touch) return on; starting = true;
      try {
        if (navigator.permissions) { const p = await navigator.permissions.query({ name: 'microphone' }).catch(() => null); if (p && p.state !== 'granted') return false; }
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        ac = new (window.AudioContext || window.webkitAudioContext)(); an = ac.createAnalyser(); an.fftSize = 512;
        buf = new Uint8Array(an.fftSize); ac.createMediaStreamSource(stream).connect(an); on = true;
      } catch (e) { on = false; } finally { starting = false; }
      return on;
    }
    function level() { if (!on) return 0; an.getByteTimeDomainData(buf); let s = 0;
      for (let i = 0; i < buf.length; i++) { const v = (buf[i] - 128) / 128; s += v * v; } return Math.min(1, Math.sqrt(s / buf.length) * 5); }
    function stop() { if (stream) stream.getTracks().forEach(tr => tr.stop()); if (ac) ac.close().catch(() => {}); stream = an = ac = null; on = false; }
    return { start, stop, level, get on() { return on; } };
  }

  // ---------------- STILI DEI COMPONENTI (iniettati una volta) ----------------
  const CSS = `
  .mk-boot{position:fixed;inset:0;z-index:5000;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:18px;
    background:radial-gradient(ellipse at center,rgba(var(--accent-rgb,0,245,255),.10),transparent 60%),var(--bg,#050a0f);transition:opacity .45s ease;cursor:pointer}
  .mk-boot.out{opacity:0;pointer-events:none}
  .mk-boot-logo{font-family:'Orbitron',monospace;font-weight:900;font-size:clamp(28px,7vw,54px);letter-spacing:.45em;padding-left:.45em;color:#fff;
    text-shadow:0 0 18px rgba(var(--accent-rgb,0,245,255),.8),0 0 42px rgba(var(--accent-rgb,0,245,255),.35);animation:mkFlick 2.2s ease-in-out infinite}
  .mk-boot-ver{font-family:'Share Tech Mono',monospace;color:var(--accent,#00f5ff);letter-spacing:.5em;font-size:11px;margin-top:-10px}
  .mk-boot-list{font-family:'Share Tech Mono',monospace;font-size:12px;color:#9fb8c4;min-width:min(340px,86vw);display:flex;flex-direction:column;gap:6px}
  .mk-boot-row{display:flex;justify-content:space-between;gap:12px;opacity:0;transform:translateY(4px);transition:all .25s ease}
  .mk-boot-row.in{opacity:1;transform:none}.mk-boot-row b{font-weight:400}.mk-ok{color:#00ff88}.mk-warn{color:#ffcc00}.mk-wait{color:var(--accent,#00f5ff)}
  .mk-boot-bar{width:min(340px,86vw);height:2px;background:rgba(var(--accent-rgb,0,245,255),.15);border-radius:2px;overflow:hidden}
  .mk-boot-bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--accent,#00f5ff),var(--accent2,#7c3aed));transition:width .3s ease;box-shadow:0 0 12px var(--accent,#00f5ff)}
  .mk-boot-skip{font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:2px;color:#4f6b78}
  @keyframes mkFlick{0%,100%{opacity:1}92%{opacity:1}93%{opacity:.55}94%{opacity:1}96%{opacity:.75}97%{opacity:1}}
  .mk-pal{position:fixed;inset:0;z-index:4000;background:rgba(2,5,10,.62);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:none;align-items:flex-start;justify-content:center;padding:12vh 16px 16px}
  .mk-pal.open{display:flex}
  .mk-pal-box{width:min(560px,100%);background:rgba(var(--bg-rgb,5,10,15),.92);border:1px solid rgba(var(--accent-rgb,0,245,255),.35);border-radius:14px;overflow:hidden;
    box-shadow:0 20px 60px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.03),0 0 40px rgba(var(--accent-rgb,0,245,255),.12);animation:mkPop .16s ease}
  @keyframes mkPop{from{opacity:0;transform:translateY(-8px) scale(.98)}to{opacity:1;transform:none}}
  .mk-pal-in{width:100%;background:transparent;border:none;border-bottom:1px solid rgba(var(--accent-rgb,0,245,255),.18);padding:16px 18px;color:#fff;font-size:16px;outline:none;font-family:inherit}
  .mk-pal-list{max-height:min(52vh,420px);overflow:auto;padding:6px}
  .mk-pal-item{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:9px;cursor:pointer;color:#c8e8f0;font-size:14px}
  .mk-pal-item .ic{width:22px;text-align:center}.mk-pal-item .hint{margin-left:auto;font-size:11px;color:#5a7a8a;font-family:'Share Tech Mono',monospace}
  .mk-pal-item.sel{background:rgba(var(--accent-rgb,0,245,255),.14);color:#fff;box-shadow:inset 2px 0 0 var(--accent,#00f5ff)}
  .mk-pal-foot{display:flex;gap:14px;padding:8px 14px;border-top:1px solid rgba(var(--accent-rgb,0,245,255),.12);font-size:10px;color:#5a7a8a;font-family:'Share Tech Mono',monospace}
  .mk-pal-empty{padding:18px;text-align:center;color:#5a7a8a;font-size:13px}
  .codeblock{margin:8px 0;border:1px solid rgba(var(--accent-rgb,0,245,255),.22);border-radius:9px;overflow:hidden;background:rgba(0,0,0,.42)}
  .cb-head{display:flex;justify-content:space-between;align-items:center;padding:5px 10px;background:rgba(var(--accent-rgb,0,245,255),.07);
    font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:1.5px;color:var(--accent,#00f5ff);text-transform:uppercase}
  .cb-copy{background:none;border:1px solid rgba(var(--accent-rgb,0,245,255),.3);color:var(--accent,#00f5ff);border-radius:5px;padding:2px 8px;font-size:10px;cursor:pointer;font-family:inherit}
  .cb-copy:hover{background:rgba(var(--accent-rgb,0,245,255),.15)}
  .codeblock pre{margin:0!important;border:none!important;border-radius:0!important;background:none!important;padding:10px 12px!important;overflow-x:auto}
  .codeblock code{font-family:'Share Tech Mono',ui-monospace,monospace;font-size:12.5px;line-height:1.55;color:#d6e9f2;background:none!important;padding:0!important}
  .hl-k{color:#c792ea}.hl-s{color:#c3e88d}.hl-n{color:#f78c6c}.hl-c{color:#5f7e8c;font-style:italic}.hl-f{color:#82aaff}
  `;
  function injectCSS() { if (document.getElementById('mk-css')) return; const s = document.createElement('style'); s.id = 'mk-css'; s.textContent = CSS; document.head.appendChild(s); }

  // ---------------- AVVIO (controlli reali, una volta per sessione) ----------------
  function boot({ version = 'V9', checks = [], key = 'maik_boot_v9', force = false } = {}) {
    injectCSS();
    let seen = false; try { seen = sessionStorage.getItem(key) === '1'; } catch (e) {}
    if (seen && !force) return Promise.resolve(false);
    try { sessionStorage.setItem(key, '1'); } catch (e) {}
    const el = document.createElement('div'); el.className = 'mk-boot'; el.setAttribute('role', 'status'); el.setAttribute('aria-label', 'Avvio di MAIK');
    el.innerHTML = `<div class="mk-boot-logo">MAIK</div><div class="mk-boot-ver">${esc(version)} · SISTEMA</div>
      <div class="mk-boot-list"></div><div class="mk-boot-bar"><i></i></div><div class="mk-boot-skip">CLIC O INVIO PER SALTARE</div>`;
    document.body.appendChild(el);
    const list = el.querySelector('.mk-boot-list'), bar = el.querySelector('.mk-boot-bar i');
    let done = false, resolveP;
    const close = () => { if (done) return; done = true; el.classList.add('out'); document.removeEventListener('keydown', onKey);
      setTimeout(() => el.remove(), 480); resolveP(true); };
    const onKey = e => { if (['Escape', 'Enter', ' '].includes(e.key)) close(); };
    el.addEventListener('click', close); document.addEventListener('keydown', onKey);
    const pause = ms => new Promise(r => setTimeout(r, reduceMotion ? 0 : ms));
    return new Promise(async res => {
      resolveP = res;
      for (let i = 0; i < checks.length && !done; i++) {
        const row = document.createElement('div'); row.className = 'mk-boot-row';
        row.innerHTML = `<span>▸ ${esc(checks[i].label)}</span><b class="mk-wait">…</b>`; list.appendChild(row);
        requestAnimationFrame(() => row.classList.add('in'));
        let r = { ok: null, text: '' };
        try { r = await Promise.race([checks[i].run(), new Promise(z => setTimeout(() => z({ ok: false, text: 'timeout' }), 2500))]) || r; } catch (e) { r = { ok: false, text: 'errore' }; }
        const st = row.querySelector('b'); st.className = r.ok === false ? 'mk-warn' : 'mk-ok'; st.textContent = (r.text || (r.ok === false ? 'non disponibile' : 'ok')) + (r.ok === false ? ' ⚠' : ' ✓');
        bar.style.width = ((i + 1) / checks.length * 100) + '%';
        await pause(140);
      }
      await pause(550); close();
    });
  }

  // ---------------- PALETTE COMANDI (Ctrl+K) ----------------
  function palette(getCommands) {
    injectCSS();
    const el = document.createElement('div'); el.className = 'mk-pal'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-label', 'Palette comandi');
    el.innerHTML = `<div class="mk-pal-box"><input class="mk-pal-in" placeholder="Cerca un comando… (es. tema, timer, briefing)" aria-label="Cerca un comando">
      <div class="mk-pal-list" role="listbox"></div><div class="mk-pal-foot"><span>↑↓ scegli</span><span>⏎ esegui</span><span>esc chiudi</span><span style="margin-left:auto">CTRL+K</span></div></div>`;
    document.body.appendChild(el);
    const input = el.querySelector('input'), list = el.querySelector('.mk-pal-list');
    let cmds = [], shown = [], sel = 0;
    const norm = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const score = (c, q) => { if (!q) return 1; const h = norm(c.label + ' ' + (c.keywords || '') + ' ' + (c.hint || ''));
      if (h.includes(q)) return 3 - (h.indexOf(q) === 0 ? 0 : 1); let i = 0; for (const ch of h) if (ch === q[i]) i++; return i === q.length ? 1 : 0; };
    function render() {
      const q = norm(input.value.trim());
      shown = cmds.map(c => [c, score(c, q)]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).map(x => x[0]).slice(0, 60);
      sel = Math.min(sel, Math.max(0, shown.length - 1));
      list.innerHTML = shown.length ? shown.map((c, i) => `<div class="mk-pal-item${i === sel ? ' sel' : ''}" role="option" data-i="${i}"><span class="ic">${c.ic || '•'}</span><span>${esc(c.label)}</span><span class="hint">${esc(c.hint || '')}</span></div>`).join('')
                                 : '<div class="mk-pal-empty">Nessun comando trovato</div>';
      const s = list.querySelector('.sel'); if (s) s.scrollIntoView({ block: 'nearest' });
    }
    function open() { cmds = getCommands(); input.value = ''; sel = 0; render(); el.classList.add('open'); input.focus(); }   // focus subito: niente tasti persi
    function close() { el.classList.remove('open'); }
    function run(i) { const c = shown[i]; if (!c) return; close(); setTimeout(() => c.run(), 10); }
    input.addEventListener('input', () => { sel = 0; render(); });
    input.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { sel = Math.min(shown.length - 1, sel + 1); render(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { sel = Math.max(0, sel - 1); render(); e.preventDefault(); }
      else if (e.key === 'Enter') { run(sel); e.preventDefault(); }
      else if (e.key === 'Escape') { close(); e.preventDefault(); }
    });
    list.addEventListener('click', e => { const it = e.target.closest('.mk-pal-item'); if (it) run(+it.dataset.i); });
    el.addEventListener('click', e => { if (e.target === el) close(); });
    document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); el.classList.contains('open') ? close() : open(); } });
    return { open, close, get isOpen() { return el.classList.contains('open'); } };
  }

  // ---------------- EVIDENZIAZIONE DEL CODICE ----------------
  const KW = new Set(('const let var function return if else for while do switch case break continue new class extends import from export default try catch finally throw ' +
    'async await yield def lambda pass None True False null undefined true false self this in of not and or is elif with as print public private protected static ' +
    'void int float double char bool boolean string struct enum interface type select insert update delete where join create table echo fn mut impl use pub match').split(' '));
  function highlight(code, lang = '') {
    lang = String(lang || '').toLowerCase();
    const hashComments = !lang || /^(python|py|bash|sh|shell|zsh|yaml|yml|ruby|rb|r|perl|toml|ini|conf|cfg|dockerfile|makefile|powershell|ps1|text|txt)$/.test(lang);
    const re = new RegExp([
      '(\\/\\/[^\\n]*|\\/\\*[\\s\\S]*?\\*\\/|<!--[\\s\\S]*?-->' + (hashComments ? '|#[^\\n]*' : '') + ')',   // commenti
      '("(?:\\\\.|[^"\\\\\\n])*"|\'(?:\\\\.|[^\'\\\\\\n])*\'|`(?:\\\\.|[^`\\\\])*`)',                       // stringhe
      '\\b(\\d+(?:\\.\\d+)?)\\b',                                                                            // numeri
      '\\b([A-Za-z_][\\w]*)(?=\\s*\\()',                                                                     // funzioni
      '\\b([A-Za-z_][\\w]*)\\b',                                                                             // parole
    ].join('|'), 'g');
    let out = '', last = 0, m;
    while ((m = re.exec(code))) {
      out += esc(code.slice(last, m.index)); last = re.lastIndex;
      if (m[1]) out += `<span class="hl-c">${esc(m[1])}</span>`;
      else if (m[2]) out += `<span class="hl-s">${esc(m[2])}</span>`;
      else if (m[3]) out += `<span class="hl-n">${m[3]}</span>`;
      else if (m[4]) out += KW.has(m[4]) ? `<span class="hl-k">${m[4]}</span>` : `<span class="hl-f">${m[4]}</span>`;
      else out += KW.has(m[5]) ? `<span class="hl-k">${m[5]}</span>` : m[5];
      if (m[0] === '') re.lastIndex++;
    }
    return out + esc(code.slice(last));
  }
  function codeBlock(code, lang) {
    return `<div class="codeblock"><div class="cb-head"><span>${esc(lang || 'codice')}</span><button class="cb-copy" type="button" aria-label="Copia il codice">Copia</button></div><pre><code>${highlight(code, lang)}</code></pre></div>`;
  }
  // copia del codice (un solo listener per tutta la pagina)
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('.cb-copy'); if (!b) return;
    const code = b.closest('.codeblock').querySelector('code').textContent;
    (navigator.clipboard ? navigator.clipboard.writeText(code) : Promise.reject()).then(() => { b.textContent = 'Copiato ✓'; setTimeout(() => b.textContent = 'Copia', 1500); },
      () => { b.textContent = 'Errore'; setTimeout(() => b.textContent = 'Copia', 1500); });
  });

  // immagine → JPEG ridimensionato (per la visione: payload leggero)
  function shrinkImage(file, max = 1024) {
    return new Promise((res, rej) => {
      const fr = new FileReader();
      fr.onload = () => { const img = new Image(); img.onload = () => {
        const s = Math.min(1, max / Math.max(img.width, img.height)), c = document.createElement('canvas');
        c.width = Math.round(img.width * s); c.height = Math.round(img.height * s); c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        res(c.toDataURL('image/jpeg', 0.85)); }; img.onerror = rej; img.src = fr.result; };
      fr.onerror = rej; fr.readAsDataURL(file);
    });
  }
  const TEXT_EXT = /\.(txt|md|markdown|csv|tsv|json|js|mjs|ts|jsx|tsx|py|html?|css|scss|xml|ya?ml|ini|cfg|toml|log|sql|java|kt|c|h|cpp|hpp|cs|go|rs|rb|php|sh|bat|ps1|swift|r)$/i;

  // parola di attivazione «Maik» (il riconoscimento vocale italiano la scrive in vari modi)
  const WAKE = /(?:^|[\s,.!?])(?:(?:ehi|hey|ok|ciao)\s+)?(maik|maic|mike|maike|maich|mayk|myke|meik|maicol)(?=$|[\s,.!?])[\s,.!?]*/i;
  function wake(text) { const m = String(text || '').match(WAKE); if (!m) return null; return (text.slice(0, m.index) + ' ' + text.slice(m.index + m[0].length)).replace(/\s{2,}/g, ' ').trim(); }

  return { THEMES, applyTheme, hexRgb, core, mic, boot, palette, highlight, codeBlock, shrinkImage, TEXT_EXT, wake, reduceMotion, touch, injectCSS };
})();
</script>
<script>
const $=s=>document.querySelector(s);
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function escA(s){return esc(s).replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
const postJ=(u,b)=>fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})}).then(r=>r.json());
function toast(m,t){const d=document.createElement('div');d.className='tst '+(t||'');d.textContent=m;$('#toast').appendChild(d);setTimeout(()=>d.remove(),3000);}
function q(t){$('#inp').value=t;$('#inp').focus();}
function qs(t){$('#inp').value=t;invia();}
function toggleSide(){$('#side').classList.toggle('hidden');}
let pName='';

// ---------- MARKDOWN + RAGIONAMENTO (<think>) ----------
function md(s){
  s=s||'';if(((s.match(/```/g)||[]).length)%2)s+='\n```';   // ``` ancora aperto durante lo streaming
  const blocks=[];s=s.replace(/```([\w+#.-]*)[^\S\n]*\n?([\s\S]*?)```/g,(_,l,c)=>{blocks.push([l,c.replace(/\n$/,'')]);return '\u0000CB'+(blocks.length-1)+'\u0000';});
  s=esc(s);
  s=s.replace(/^#{1,3}\s+(.+)$/gm,'<b class="md-h">$1</b>');
  s=s.replace(/`([^`\n]+)`/g,'<code>$1</code>');
  s=s.replace(/\[([^\[\]\n]{1,80}\.[A-Za-z0-9]{1,5})(?: · parte \d+)?\]/g,'<span class="cite">📄 $1</span>');   // fonti citate [nome.txt]
  s=s.replace(/\*\*([^*\n]+)\*\*/g,'<b>$1</b>');
  s=s.replace(/(^|[^*])\*([^*\n]+)\*/g,'$1<i>$2</i>');
  s=s.replace(/(?:^|\n)((?:- .+(?:\n|$))+)/g,(m,l)=>'\n<ul>'+l.trim().split('\n').map(x=>'<li>'+x.replace(/^- /,'')+'</li>').join('')+'</ul>');
  s=s.replace(/\n/g,'<br>').replace(/<br><ul>/g,'<ul>').replace(/<\/ul><br>/g,'</ul>');
  return s.replace(/(?:<br>)*\u0000CB(\d+)\u0000(?:<br>)*/g,(_,i)=>MaikKit.codeBlock(blocks[i][1],blocks[i][0]));
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
  el.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" width="100%" height="'+H+'"><line x1="4" x2="'+(W-4)+'" y1="'+(H/2)+'" y2="'+(H/2)+'" style="stroke:rgba(var(--accent-rgb),.15)" stroke-dasharray="3 3"/><polyline points="'+pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')+'" fill="none" stroke="'+col+'" stroke-width="2" stroke-linejoin="round"/>'+pts.map(p=>'<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="2.2" fill="'+col+'"/>').join('')+'</svg><div class="note" style="margin:2px 0 0">Ultimo: <b>'+esc(last.umore||'')+'</b></div>';
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
  SPH.state='alarm';setTimeout(()=>{if(SPH.state==='alarm')SPH.state='idle';},2500);
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
    pName=s.nome_utente||'';$('#s-ag').textContent=s.agente?'🤖 attivo':'spento';
    if(s.personalita&&s.personalita!==persCur){persCur=s.personalita;renderPers();}
  }catch(e){$('#stato').textContent='server non raggiungibile';}
}
async function cfg(){try{const c=await (await fetch('/config')).json();$('#s-vis').textContent=c.modello_visione||'—';PERS=c.personalita_disponibili||[];persCur=c.personalita||'amico';renderPers();}catch(e){}}
async function profilo(){
  try{const s=await (await fetch('/statistiche')).json();const p=s.profilo||{};const k=Object.keys(p);
    $('#profilo').innerHTML=k.length?k.map(x=>`<div class="kv"><span>${esc(x)}</span><span>${esc(String(p[x]))}</span></div>`).join(''):'nessun dato ancora';
    drawMood(s.umore_grafico);$('#doccount').textContent=s.n_documenti?' ('+s.n_documenti+')':'';
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
function add(role,txt,extra,opt){const d=document.createElement('div');d.className='m '+role+(extra?' '+extra:'');
  if(role==='ai')d.innerHTML='<div class="mc">'+renderAI(txt)+'</div>';
  else{opt=opt||{};d.innerHTML=(opt.img?'<img class="att" src="'+opt.img+'" alt="Immagine allegata">':'')+(opt.file?'<div class="fchip">📄 '+esc(opt.file)+'</div><br>':'');d.appendChild(document.createTextNode(txt));}
  $('#msgs').appendChild(d);$('#msgs').scrollTop=1e9;return d;}
function mc(d){return d.querySelector('.mc')||d;}
function fmtStats(st){if(!st||!st.tps)return '';const t=ms=>ms<1000?Math.round(ms)+' ms':(ms/1000).toLocaleString('it-IT',{maximumFractionDigits:1})+' s';
  return '⚡ <b>'+st.tps.toLocaleString('it-IT',{maximumFractionDigits:1})+'</b> tok/s · prima parola '+t(st.ttft_ms)+' · totale '+t(st.totale_ms);}
// azioni sotto la risposta: copia, ascolta, rigenera (solo l'ultima) + velocità vera del modello
function finalize(d,raw,st,q){d.dataset.raw=raw;if(q!=null)d.dataset.q=q;let a=d.querySelector('.acts');if(!a){a=document.createElement('div');a.className='acts';d.appendChild(a);}
  a.innerHTML='<button type="button" data-act="copy">⧉ copia</button><button type="button" data-act="speak">🔊</button>'+(q!=null?'<button type="button" class="act-regen" data-act="regen">↻ rigenera</button>':'')+(st&&st.tps?'<span class="meta">'+fmtStats(st)+'</span>':'');markLast();}
function markLast(){document.querySelectorAll('#msgs .m.ai.last').forEach(x=>x.classList.remove('last'));const all=[...document.querySelectorAll('#msgs .m')];const l=all[all.length-1];if(l&&l.classList.contains('ai')&&l.dataset.raw!=null)l.classList.add('last');}
let busy=false,ctl=null,att=null;
async function invia(opt){
  opt=opt||{};const regen=!!opt.regen;
  const t=(opt.text!=null?opt.text:$('#inp').value).trim();const A=regen?null:att;
  if((!t&&!A)||busy)return;
  if(!regen){$('#inp').value='';clearAtt();}
  $('#send').disabled=true;busy=true;lastAct=Date.now();
  if(/ricordami|avvisami|timer|sveglia|svegliami|promemoria/i.test(t))askNotify();
  if(!regen)add('me',t,null,{img:A&&A.kind==='image'?A.dataUrl:null,file:A&&A.kind==='text'?A.name:null});
  SPH.state='thinking';$('#dot').className='dot busy';
  const bubble=add('ai','');mc(bubble).innerHTML='<span class="cursor"></span>';
  // 🖼️ immagine allegata → modello visione, con la domanda scritta
  if(A&&A.kind==='image'){
    try{const r=await (await fetch('/vedi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({immagine:A.dataUrl,
        prompt:t?'Guarda attentamente questa immagine e rispondi in italiano, in modo chiaro e amichevole, a questa domanda: '+t:'Descrivi questa immagine in italiano, in modo chiaro e amichevole (3-4 frasi): cosa si vede, i dettagli interessanti e l\'eventuale testo leggibile.'})})).json();
      const out=r.ok?'🖼️ '+r.testo:'👁️ '+(r.errore||'Non riesco a vedere');mc(bubble).innerHTML=renderAI(out);finalize(bubble,out,null,null);if(r.ok)say(r.testo);}
    catch(e){mc(bubble).textContent='Errore visione: '+e.message;}
    SPH.state='idle';$('#dot').className='dot on';busy=false;$('#send').disabled=false;return;
  }
  let full='';ctl=new AbortController();$('#stopbtn').style.display='inline-block';
  try{
    const body={testo:t,sessione:CUR};if(regen)body.rigenera=true;if(A&&A.kind==='text')body.allegato={nome:A.name,contenuto:A.content};
    const resp=await fetch('/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:ctl.signal});
    const reader=resp.body.getReader();const dec=new TextDecoder();let buf='';
    while(true){
      const {done,value}=await reader.read();if(done)break;
      buf+=dec.decode(value,{stream:true});let i;
      while((i=buf.indexOf('\n\n'))>=0){
        const line=buf.slice(0,i).trim();buf=buf.slice(i+2);
        if(!line.startsWith('data:'))continue;
        let obj;try{obj=JSON.parse(line.slice(5).trim());}catch(e){continue;}
        if(obj.t){full+=obj.t;SPH.state=splitThink(full).open?'thinking':'speaking';mc(bubble).innerHTML=renderAI(full)+'<span class="cursor"></span>';$('#msgs').scrollTop=1e9;}
        if(obj.strumento){agEl(bubble).insertAdjacentHTML('beforeend',chipH(obj.strumento));if(core)core.pulse(1);$('#msgs').scrollTop=1e9;}   // 🤖 l'agente sta usando uno strumento
        if(obj.done){
          if(obj.comando){mc(bubble).textContent='['+obj.comando.tipo+'] '+JSON.stringify(obj.comando).slice(0,500);}
          else if(obj.ok===false){mc(bubble).textContent=obj.risposta||'Errore.';}
          else{
            mc(bubble).innerHTML=renderAI(full);say(full);finalize(bubble,full,obj.stat,A?null:t);
            addChips(bubble,obj.azioni,obj.fonti,obj.seguito);
            if(obj.azioni&&obj.azioni.length)loadPr();
            if(obj.seguito)toast('🔁 Ti chiederò com\'è andata: '+obj.seguito.evento,'ok');
            if(obj.sessione&&obj.sessione!==CUR){CUR=obj.sessione;LS.set('maik_srv_chat',CUR);}
            loadChats();
            if(obj.stat&&obj.stat.tps)$('#speed').textContent='⚡ '+obj.stat.tps.toLocaleString('it-IT')+' tok/s';
            if(obj.imparato)toast('💡 Ho imparato: '+obj.imparato,'ok');
            if(obj.azione){loadPr();}else{setTimeout(checkLearn,4000);setTimeout(checkLearn,12000);}
          }
          stato();profilo();
        }
      }
    }
  }catch(e){
    if(e.name==='AbortError'){const out=(full?full+'\n\n':'')+'*(interrotta)*';mc(bubble).innerHTML=renderAI(out);finalize(bubble,out,null,null);}   // tieni ciò che aveva scritto
    else mc(bubble).textContent='Errore di connessione: '+e.message;
  }
  ctl=null;$('#stopbtn').style.display='none';
  SPH.state='idle';$('#dot').className='dot on';busy=false;$('#send').disabled=false;
  if(!friend)$('#inp').focus();
}
function stopGen(){if(ctl)ctl.abort();if(window.speechSynthesis)speechSynthesis.cancel();}
function regen(d){if(busy)return;const q=d.dataset.q;if(q==null){toast('Questa risposta non si può rigenerare','err');return;}d.remove();invia({text:q,regen:true});}

// ---------- ALLEGATI (📎, trascina e rilascia, incolla) ----------
async function attachFile(f){if(!f)return;try{
  if(/^image\//.test(f.type))att={kind:'image',name:f.name||'immagine',dataUrl:await MaikKit.shrinkImage(f)};
  else if(MaikKit.TEXT_EXT.test(f.name||'')||/^text\//.test(f.type)){if(f.size>400000){toast('File troppo grande (massimo 400 KB)','err');return;}const raw=await f.text();att={kind:'text',name:f.name,content:raw.slice(0,12000),cut:raw.length>12000,full:raw};}
  else{toast('Posso leggere immagini e file di testo (txt, md, csv, codice…)','err');return;}
  renderAtt();$('#inp').focus();}catch(e){toast('Non riesco a leggere il file','err');}}
function onAttIn(e){attachFile(e.target.files[0]);e.target.value='';}
function renderAtt(){const el=$('#attprev');if(!att){el.classList.remove('on');el.innerHTML='';return;}el.classList.add('on');
  el.innerHTML=(att.kind==='image'?'<img src="'+att.dataUrl+'" alt="">':'<span style="font-size:22px">📄</span>')+'<span>'+esc(att.name)+' · '+(att.kind==='image'?'MAIK la guarderà 👁️':att.content.length.toLocaleString('it-IT')+' caratteri'+(att.cut?' (tagliato)':''))+'</span>'+(att.kind==='text'?'<button class="tbtn" type="button" id="att2doc" style="flex:0 0 auto;min-width:0;padding:3px 9px;font-size:11px;margin-left:auto" onclick="attToDocs()" title="Così MAIK lo ricorda sempre e lo cita">📚 salva nei documenti</button>':'')+'<button class="x" type="button" onclick="clearAtt()" aria-label="Rimuovi l\'allegato"'+(att.kind==='text'?' style="margin-left:4px"':'')+'>✕</button>';}
function clearAtt(){att=null;renderAtt();}

// ---------- NUCLEO NEURALE (MaikKit.core: nitido su ogni schermo, reagisce a voce e stati) ----------
const cv=$('#sph'),wrap=$('#sphere-wrap'),area=$('#sphere-area');
const SPH={size:200,x:0,y:0,vx:.45,vy:.3,state:'idle',drag:false,ox:0,oy:0};
let core=null,themeRGB=MaikKit.applyTheme('neon');const micMeter=MaikKit.mic();
function sphSize(){const a=area.getBoundingClientRect();let s=Math.round(Math.min(a.width*.62,a.height*.85));if(!s||s<0)s=180;SPH.size=Math.max(140,Math.min(MaikKit.touch?260:320,s));if(core)core.resize(SPH.size);}
function sphInit(){core=MaikKit.core(cv,{size:200});core.setAccent(themeRGB.accent,themeRGB.accent2);sphSize();const a=area.getBoundingClientRect();SPH.x=Math.max(8,(a.width-SPH.size)/2);SPH.y=Math.max(8,(a.height-SPH.size)/2);sphPos();}
function sphPos(){wrap.style.left=SPH.x+'px';wrap.style.top=SPH.y+'px';}
let sphT=0;
function sphLoop(){
  sphT+=.02;const a=area.getBoundingClientRect();const mx=a.width-SPH.size,my=a.height-SPH.size;
  if(!SPH.drag&&!MaikKit.reduceMotion&&mx>4&&my>4){SPH.x+=SPH.vx;SPH.y+=SPH.vy;if(SPH.x<=0||SPH.x>=mx){SPH.vx*=-1;SPH.x=Math.max(0,Math.min(mx,SPH.x));}if(SPH.y<=0||SPH.y>=my){SPH.vy*=-1;SPH.y=Math.max(0,Math.min(my,SPH.y));}sphPos();}
  const st=SPH.state!=='idle'?SPH.state:(listening?'listening':'idle');core.setState(st);
  if(st==='listening')core.setLevel(micMeter.on?micMeter.level():.15+Math.abs(Math.sin(sphT*3))*.2);
  core.frame();requestAnimationFrame(sphLoop);
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
  const b=add('ai','');mc(b).innerHTML='👁️ <span class="cursor"></span>';
  try{
    const r=await (await fetch('/vedi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({immagine:img})})).json();
    if(r.ok){mc(b).textContent='👁️ '+r.testo;finalize(b,'👁️ '+r.testo,null,null);say(r.testo);}
    else{mc(b).textContent='👁️ '+(r.errore||'Non riesco a vedere');visionBroken=true;}
  }catch(e){mc(b).textContent='Errore visione: '+e.message;}
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
  reco.onend=()=>{listening=false;$('#mic').classList.remove('on');let val=$('#inp').value.trim();fin='';
    if(val&&friend&&OPT.wake){const rest=MaikKit.wake(val);if(rest===null){$('#inp').value='';val='';}else{$('#inp').value=rest||'Ciao!';val=$('#inp').value;}}   // senza «Maik» non rispondo
    if(val)invia();else if(friend&&!speaking&&!busy&&!micFatal)setTimeout(startReco,700);
    if(!friend)setTimeout(()=>{if(!listening)micMeter.stop();},1500);};
  reco.onerror=e=>{listening=false;$('#mic').classList.remove('on');if(e.error==='no-speech'){if(friend&&!speaking&&!busy&&!micFatal)setTimeout(startReco,500);return;}if(e.error==='aborted')return;if(['not-allowed','service-not-allowed','audio-capture'].includes(e.error)){micFatal=true;toast('Microfono non disponibile — scrivi pure','err');return;}toast('Errore microfono: '+e.error,'err');};
}
function startReco(){if(!reco||listening||busy||speaking||micFatal)return;try{listening=true;reco.start();$('#mic').classList.add('on');micMeter.start();}catch(e){}}
function toggleMic(){if(!reco){toast('Voce non supportata dal browser','err');return;}if(listening){reco.stop();}else{micFatal=false;startReco();}}

// ---------- TTS (voce di MAIK) ----------
let ttsOn=false,speaking=false;
function say(t){if(!ttsOn||!window.speechSynthesis)return;speechSynthesis.cancel();const p=stripThink(t).replace(/[#*_`>]/g,'').replace(/<[^>]+>/g,'').replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}]/gu,'').slice(0,400);if(!p.trim())return;const u=new SpeechSynthesisUtterance(p);u.lang='it-IT';u.rate=1;u.pitch=1.1;const v=speechSynthesis.getVoices().find(x=>x.lang&&x.lang.startsWith('it'));if(v)u.voice=v;u.onboundary=()=>{if(core)core.pulse(1);};u.onstart=()=>{speaking=true;SPH.state='speaking';if(listening){try{reco.stop();}catch(e){}}};u.onend=()=>{speaking=false;if(SPH.state==='speaking')SPH.state='idle';if(friend&&!busy&&!speaking)setTimeout(()=>{if(friend)startReco();},400);};speechSynthesis.speak(u);}

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
function exitFriend(){friend=false;clearInterval(proTimer);micMeter.stop();if(listening){try{reco.stop();}catch(e){}}if(window.speechSynthesis)speechSynthesis.cancel();stopCam();$('#fbtn').classList.remove('on');$('#fbtn').innerHTML='🫂<span class="hx"> AMICO</span>';$('#fbadge').style.display='none';toast('Modalità Amico disattivata');}
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

// ---------- V9: TEMI · OPZIONI · MEMORIA COMPLETA · PALETTE · AVVIO ----------
const LS={get:(k,d)=>{try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v);}catch(e){return d;}},set:(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}};
const OPT=Object.assign({wake:false,boot:true,theme:'neon'},LS.get('maik_srv_opt',{}));
function setOpt(k,v){OPT[k]=v;LS.set('maik_srv_opt',OPT);}
function setTheme(k){themeRGB=MaikKit.applyTheme(k);if(core)core.setAccent(themeRGB.accent,themeRGB.accent2);setOpt('theme',k);renderThemes();}
function renderThemes(){$('#themes').innerHTML=Object.entries(MaikKit.THEMES).map(([k,t])=>'<button type="button" class="'+(k===OPT.theme?'on':'')+'" onclick="setTheme(\''+k+'\')"><i style="background:linear-gradient(135deg,'+t.accent+','+t.accent2+')"></i>'+t.nm+'</button>').join('');}
let MEM=null;
async function openMem(){$('#memf').value='';$('#mmodal').classList.add('open');$('#membody').innerHTML='<div class="note">Carico…</div>';try{MEM=await (await fetch('/statistiche')).json();}catch(e){MEM=null;}renderMem();}
function closeMem(){$('#mmodal').classList.remove('open');}
function renderMem(){
  if(!MEM){$('#membody').innerHTML='<div class="note">Server non raggiungibile</div>';return;}
  const q=($('#memf').value||'').toLowerCase(),imp=MEM.imparato_recenti||[],ep=MEM.episodi||[],off=(MEM.n_episodi||ep.length)-ep.length;
  let h='';
  if(MEM.riassunto)h+='<h4 style="margin-bottom:6px">Riassunto della vostra storia <button class="nx" onclick="forget(\'riassunto\')" title="Cancella" aria-label="Cancella il riassunto">✕</button></h4><div class="memsum">'+esc(MEM.riassunto)+'</div>';
  const rows=imp.map((x,i)=>({x,i})).filter(o=>!q||(o.x.cosa||'').toLowerCase().includes(q)).reverse();
  h+='<h4 style="margin:6px 0">Ricordi ('+imp.length+')</h4>'+(rows.length?rows.map(o=>'<div class="memrow"><span class="tag'+(o.x.categoria==='ia'?' ia':'')+'">'+esc(o.x.categoria||'fatto')+'</span><span class="txt">'+esc(o.x.cosa||'')+'</span><button class="nx" onclick="forget(\'imparato\','+o.i+')" title="Dimentica" aria-label="Dimentica questo ricordo">✕</button></div>').join(''):'<div class="note">Nessun ricordo</div>');
  const eps=ep.map((x,i)=>({x,i:off+i})).filter(o=>!q||((o.x.titolo||'')+' '+(o.x.desc||'')).toLowerCase().includes(q)).reverse();
  if(eps.length)h+='<h4 style="margin:12px 0 6px">Momenti importanti</h4>'+eps.map(o=>'<div class="memrow"><span class="tag">'+esc(o.x.data||'')+'</span><span class="txt">'+esc(o.x.titolo||'')+'</span><button class="nx" onclick="forget(\'episodio\','+o.i+')" title="Dimentica" aria-label="Dimentica questo momento">✕</button></div>').join('');
  $('#membody').innerHTML=h;
}
async function forget(tipo,i){const url=tipo==='riassunto'?'/riassunto/elimina':'/'+tipo+'/elimina';
  try{await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({indice:i})});MEM=await (await fetch('/statistiche')).json();renderMem();toast('Dimenticato','ok');profilo();}catch(e){toast('Errore','err');}}
let pal=null;
function openPalette(){if(pal)pal.open();}
function palCmds(){const c=(ic,label,run,hint,kw)=>({ic,label,run,hint:hint||'',keywords:kw||''});const go=t=>()=>qs(t);
  const L=[c('☀️','Briefing del giorno',go('briefing'),'azione'),c('⏱️','Timer di 5 minuti',go('metti un timer di 5 minuti'),'azione','sveglia'),
    c('⏰','Crea un promemoria…',()=>q('Ricordami alle 18 di '),'azione','ricordami'),c('🛒','Mostra la lista della spesa',go("cosa c'è nella lista?"),'azione','spesa'),
    c('❓','Cosa sai fare?',go('aiuto'),'azione','aiuto help'),c('🫂',friend?'Esci dalla Modalità Amico':'Modalità Amico',()=>toggleFriend(),'webcam + voce'),
    c('👁️','Guarda dalla webcam',()=>guarda(),'visione'),c('📎','Allega immagine o file',()=>$('#attin').click(),'allegato'),
    c('🧠','Memoria completa',()=>openMem(),'ricordi'),c('🧰','Strumenti',()=>openTools(),'calcolatrice, timer…'),
    c('🎤','Parla con MAIK',()=>toggleMic(),'microfono'),c('≡','Mostra / nascondi la barra laterale',()=>toggleSide(),''),
    c('💬','Nuova chat',()=>newChat(),'conversazione'),c('📚','I tuoi documenti',()=>openDocs(),'fonti, file, carica'),
    c('📲','Installa MAIK come app',()=>installa(),'pwa','installa app telefono')];
  CHATS.filter(x=>x.id!==CUR).slice(0,8).forEach(x=>L.push(c('💬','Vai alla chat: '+x.titolo,()=>switchChat(x.id),'chat','conversazione')));
  Object.entries(MaikKit.THEMES).forEach(([k,t])=>L.push(c('🎨','Tema: '+t.nm,()=>{setTheme(k);toast('🎨 Tema '+t.nm,'ok');},'tema','colore')));
  PERS.forEach(p=>L.push(c(p.emoji,'Personalità: '+p.nome,()=>setPers(p.chiave),'personalità','modalità')));
  return L;}
function runBoot(){if(OPT.boot===false)return;
  MaikKit.boot({version:'V10 · SERVER',key:'maik_boot_v10',checks:[
    {label:'Server',run:async()=>{try{const r=await (await fetch('/salute')).json();window.__bootSalute=r;return{ok:true,text:'attivo'};}catch(e){return{ok:false,text:'non risponde'};}}},
    {label:'Ollama',run:async()=>{const r=window.__bootSalute;return r&&r.online?{ok:true,text:'online · '+r.modello}:{ok:false,text:'offline'};}},
    {label:'Memoria su disco',run:async()=>{try{const s=await (await fetch('/statistiche')).json();return{ok:true,text:(s.n_imparato||0)+' ricordi · '+(s.n_scambi||0)+' scambi'};}catch(e){return{ok:false,text:'errore'};}}},
    {label:'Agente e strumenti',run:async()=>{try{const s=await (await fetch('/stato')).json();return s.agente?{ok:true,text:'attivo · 10 strumenti'}:{ok:false,text:'spento (MAIK_AGENTE=0)'};}catch(e){return{ok:false,text:'errore'};}}},
    {label:'Documenti',run:async()=>{try{const r=await (await fetch('/documenti')).json();const n=(r.documenti||[]).length;return{ok:true,text:n?n+' document'+(n===1?'o':'i'):'nessuno (caricali con 📚)'};}catch(e){return{ok:false,text:'errore'};}}},
    {label:'Promemoria',run:async()=>{try{const r=await (await fetch('/promemoria')).json();const n=(r.promemoria||[]).length;return{ok:true,text:n?n+' attiv'+(n===1?'o':'i'):'nessuno'};}catch(e){return{ok:false,text:'errore'};}}},
    {label:'Voce italiana',run:async()=>{const v=await new Promise(r=>{const x=window.speechSynthesis?speechSynthesis.getVoices():[];if(x.length)return r(x);setTimeout(()=>r(window.speechSynthesis?speechSynthesis.getVoices():[]),900);});return v.some(x=>x.lang&&x.lang.startsWith('it'))?{ok:true,text:'disponibile'}:{ok:false,text:'non trovata'};}},
    {label:'Nucleo neurale',run:async()=>({ok:true,text:'pronto · tema '+(MaikKit.THEMES[OPT.theme]||MaikKit.THEMES.neon).nm})}]});}

// ---------- V10: CHAT MULTIPLE (stessa memoria) ----------
let CUR=LS.get('maik_srv_chat','principale'),CHATS=[];
const WELCOME='Ciao! Sono **Maik**, versione 10 🤖 Ora **agisco da solo**: chiedimi le cose a parole tue («stasera pasta, metti in lista gli ingredienti», «che tempo fa a Milano?») e uso i miei strumenti. Leggo i tuoi **📚 documenti** e cito la fonte, tengo **più chat** separate e mi ricordo di chiederti **com\'è andata** 🔁. Scrivi **aiuto** oppure premi **Ctrl+K** 💚';
const NUOVA='✨ **Nuova chat!** Ricordo comunque tutto di te. Di cosa parliamo?';
async function loadChats(){try{CHATS=(await (await fetch('/sessioni')).json()).sessioni||[];}catch(e){return;}
  if(!CHATS.some(c=>c.id===CUR)){CUR='principale';LS.set('maik_srv_chat',CUR);}
  $('#chats').innerHTML=CHATS.map(c=>'<div class="chat'+(c.id===CUR?' on':'')+'" data-id="'+escA(c.id)+'" title="'+escA(c.anteprima||c.titolo)+'" role="button" tabindex="0"><span class="ct">'+(c.id==='principale'?'⭐ ':'💬 ')+esc(c.titolo)+'</span><small>'+(c.n||0)+'</small><button class="cb" data-a="ren" title="Rinomina" aria-label="Rinomina la chat">✎</button><button class="cb del" data-a="del" title="'+(c.id==='principale'?'Svuota':'Elimina')+'" aria-label="'+(c.id==='principale'?'Svuota':'Elimina')+' la chat">✕</button></div>').join('');}
async function loadHistory(){let r;try{r=await (await fetch('/sessioni/storia?id='+encodeURIComponent(CUR))).json();}catch(e){return 0;}
  const sc=r.scambi||[];
  sc.forEach(x=>{if(x.tu){const m=x.tu.match(/^([\s\S]*?)\s*\[📎 ([^\]]+)\]$/);add('me',m?m[1]:x.tu,null,{file:m?m[2]:null});}
    const d=add('ai',x.ai,x.seguito?'seguito':null);finalize(d,x.ai,null,x.tu&&!/\[📎/.test(x.tu)?x.tu:null);addChips(d,x.azioni,x.fonti);});
  $('#msgs').scrollTop=1e9;return sc.length;}
async function switchChat(id,force){if(busy){toast('Aspetta che finisca di rispondere','err');return;}if(id===CUR&&!force)return;
  CUR=id;LS.set('maik_srv_chat',id);$('#msgs').innerHTML='';loadChats();
  if(!(await loadHistory()))add('ai',CUR==='principale'?WELCOME:NUOVA);
  if(innerWidth<=760)$('#side').classList.add('hidden');if(!friend)$('#inp').focus();}
async function newChat(){if(busy)return;const cur=CHATS.find(c=>c.id===CUR);
  if(cur&&cur.id!=='principale'&&!cur.n){toast('Sei già in una chat nuova ✨');$('#inp').focus();return;}
  try{const r=await postJ('/sessioni/nuova');await switchChat(r.sessione.id);}catch(e){toast('Non riesco a creare la chat','err');}}
async function renameChat(id){const c=CHATS.find(x=>x.id===id);const t=prompt('Nuovo nome della chat:',c?c.titolo:'');if(!t||!t.trim())return;
  try{await postJ('/sessioni/rinomina',{id,titolo:t.trim()});}catch(e){}loadChats();}
async function delChat(id){const c=CHATS.find(x=>x.id===id),pr=id==='principale';
  if(!confirm((pr?'Svuotare':'Eliminare')+' la chat «'+(c?c.titolo:'')+'»?\nI messaggi spariscono, la memoria su di te resta.'))return;
  try{await postJ('/sessioni/elimina',{id});}catch(e){toast('Errore','err');return;}
  toast('🗑️ Chat '+(pr?'svuotata':'eliminata'),'ok');if(id===CUR)await switchChat('principale',true);else loadChats();}

// ---------- V10: AGENTE · FONTI · FOLLOW-UP (chip sotto la risposta) ----------
function agEl(d){let g=d.querySelector('.ag');if(!g){g=document.createElement('div');g.className='ag';d.insertBefore(g,d.querySelector('.acts'));}return g;}
function chipH(a){return '<span class="agc'+(a.ok===false?' ko':'')+'" title="'+escA((a.tipo||'')+': '+(a.esito||''))+'">'+(a.icona||'🔧')+' '+esc(a.esito||a.tipo||'')+'</span>';}
function addChips(d,az,fo,fu){let h='';(az||[]).forEach(a=>h+=chipH(a));
  (fo||[]).forEach(f=>h+='<span class="agc src'+(f.citata?' cit':'')+'" title="'+escA(f.anteprima||f.nome)+'">📄 '+esc(f.nome)+' · parte '+f.pezzo+'</span>');
  if(fu)h+='<span class="agc fu" title="'+escA('Evento: '+fu.evento+' ('+fu.quando+')')+'">🔁 ti chiederò com\'è andata</span>';
  if(h||d.querySelector('.ag'))agEl(d).innerHTML=h;}
async function checkSeguiti(){if(busy)return;try{const r=await (await fetch('/seguiti/scaduti?sessione='+encodeURIComponent(CUR))).json();const a=r.seguiti||[];
  a.forEach(x=>{const d=add('ai',x.testo,'seguito');finalize(d,x.testo,null,null);toast('🔁 '+x.evento,'ok');notify('MAIK',x.testo);if(core)core.pulse(1.5);say(x.testo);});
  if(a.length){beep(1);loadChats();}}catch(e){}}

// ---------- V10: I TUOI DOCUMENTI ----------
function fmtD(iso){try{return new Date(iso).toLocaleDateString('it-IT',{day:'numeric',month:'short'});}catch(e){return '';}}
async function openDocs(){$('#dmodal').classList.add('open');$('#docq').value='';$('#docres').innerHTML='';await loadDocs();}
function closeDocs(){$('#dmodal').classList.remove('open');}
async function loadDocs(){let r;try{r=await (await fetch('/documenti')).json();}catch(e){$('#doclist').innerHTML='<div class="note">Server non raggiungibile</div>';return;}
  const D=r.documenti||[];$('#doccount').textContent=D.length?' ('+D.length+')':'';
  $('#doclist').innerHTML=D.length?'<h4 style="margin:14px 0 4px">Documenti ('+D.length+')</h4>'+D.map(d=>'<div class="memrow doc" data-id="'+escA(d.id)+'"><span class="tag">'+esc(((/\.(\w{1,4})$/.exec(d.nome)||[])[1]||'txt'))+'</span><span class="txt"><b>'+esc(d.nome)+'</b><small class="dmeta">'+d.caratteri.toLocaleString('it-IT')+' caratteri · '+d.n_pezzi+' pezz'+(d.n_pezzi===1?'o':'i')+' · '+fmtD(d.aggiunto)+'</small></span><button class="nx" onclick="docDel(\''+escA(d.id)+'\')" title="Elimina" aria-label="Elimina il documento">✕</button></div>').join(''):'<div class="note">Ancora nessun documento: caricane uno e poi chiedi a MAIK di quello che c\'è dentro.</div>';
  $('#docspace').textContent=r.caratteri?'Spazio usato: '+Math.max(1,Math.round(100*r.caratteri/r.limite))+'%':'';}
async function docSave(nome,contenuto){try{const r=await postJ('/documenti',{nome,contenuto});
  if(r.ok){toast('📚 '+r.documento.nome+': '+r.documento.n_pezzi+' pezz'+(r.documento.n_pezzi===1?'o':'i')+(r.documento.tagliato?' (tagliato)':''),'ok');return true;}
  toast(r.errore||'Documento non salvato','err');}catch(e){toast('Errore di rete','err');}return false;}
async function docFiles(files){const L=[...(files||[])].slice(0,10);for(const f of L){
  if(!(MaikKit.TEXT_EXT.test(f.name||'')||/^text\//.test(f.type))){toast('«'+f.name+'»: solo file di testo','err');continue;}
  if(f.size>2000000){toast('«'+f.name+'» è troppo grande (max 2 MB)','err');continue;}
  await docSave(f.name,await f.text());}loadDocs();}
async function docPaste(){const t=$('#dpt').value.trim();if(!t){toast('Incolla prima un testo','err');return;}
  let n=$('#dpn').value.trim()||('appunti '+new Date().toLocaleDateString('it-IT'));if(!/\.\w{1,5}$/.test(n))n+='.txt';
  if(await docSave(n,t)){$('#dpt').value='';$('#dpn').value='';$('.dpaste').open=false;loadDocs();}}
async function docDel(id){if(!confirm('Eliminare questo documento?'))return;try{await postJ('/documenti/elimina',{id});}catch(e){}loadDocs();}
let docT;
function docSearch(){clearTimeout(docT);docT=setTimeout(async()=>{const v=$('#docq').value.trim(),box=$('#docres');if(!v){box.innerHTML='';return;}
  try{const r=await (await fetch('/documenti/cerca?q='+encodeURIComponent(v))).json();const h=r.risultati||[];
    const words=v.split(/\s+/).filter(w=>w.length>2).map(w=>w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));const rx=words.length?new RegExp('('+words.join('|')+')','gi'):null;
    box.innerHTML=h.length?h.slice(0,4).map(x=>{let t=esc(x.testo.slice(0,260))+(x.testo.length>260?'…':'');if(rx)t=t.replace(rx,'<mark>$1</mark>');return '<div class="dhit"><b>📄 '+esc(x.nome)+' · parte '+x.pezzo+'</b><br>'+t+'</div>';}).join(''):'<div class="note">Nessun risultato</div>';}catch(e){}},250);}
async function attToDocs(){if(!att||att.kind!=='text')return;if(await docSave(att.name,att.full||att.content)){const b=$('#att2doc');if(b){b.textContent='✓ nei documenti';b.disabled=true;}profilo();}}

// ---------- V10: APP INSTALLABILE ----------
let instEv=null;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();instEv=e;$('#instbtn').style.display='block';});
window.addEventListener('appinstalled',()=>{instEv=null;$('#instbtn').style.display='none';toast('📲 MAIK installato! Lo trovi tra le tue app','ok');});
async function installa(){if(!instEv){toast(matchMedia('(display-mode: standalone)').matches?'MAIK è già installato ✓':'Dal menu del browser scegli «Installa app» oppure «Aggiungi a schermata Home» 📲');return;}
  instEv.prompt();try{await instEv.userChoice;}catch(e){}instEv=null;$('#instbtn').style.display='none';}
if('serviceWorker' in navigator&&/^https?:$/.test(location.protocol))navigator.serviceWorker.register('/sw.js').catch(()=>{});

// ---------- INIT ----------
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeTools();closeMem();closeDocs();}});
$('#dmodal').addEventListener('click',e=>{if(e.target.id==='dmodal')closeDocs();});
['dragenter','dragover'].forEach(ev=>$('#ddrop').addEventListener(ev,e=>{e.preventDefault();$('#ddrop').classList.add('on');}));
['dragleave','drop'].forEach(ev=>$('#ddrop').addEventListener(ev,()=>$('#ddrop').classList.remove('on')));
$('#ddrop').addEventListener('drop',e=>{e.preventDefault();docFiles(e.dataTransfer.files);});
$('#chats').addEventListener('click',e=>{const row=e.target.closest('.chat');if(!row)return;e.stopPropagation();const b=e.target.closest('.cb'),id=row.dataset.id;
  if(b){if(b.dataset.a==='ren')renameChat(id);else delChat(id);return;}switchChat(id);});
$('#chats').addEventListener('keydown',e=>{const row=e.target.closest('.chat');if(row&&e.key==='Enter'&&!e.target.closest('.cb'))switchChat(row.dataset.id);});
$('#tmodal').addEventListener('click',e=>{if(e.target.id==='tmodal')closeTools();});
$('#mmodal').addEventListener('click',e=>{if(e.target.id==='mmodal')closeMem();});
window.addEventListener('resize',()=>{sphSize();const a=area.getBoundingClientRect();SPH.x=Math.max(0,Math.min(SPH.x,a.width-SPH.size));SPH.y=Math.max(0,Math.min(SPH.y,a.height-SPH.size));sphPos();});
themeRGB=MaikKit.applyTheme(OPT.theme);renderThemes();$('#optwake').checked=!!OPT.wake;$('#optboot').checked=OPT.boot!==false;
runBoot();pal=MaikKit.palette(palCmds);
// sul telefono si parte con la chat libera; toccando la chat la barra laterale si richiude
if(innerWidth<=760)$('#side').classList.add('hidden');
$('#main').addEventListener('click',()=>{if(innerWidth<=760&&!$('#side').classList.contains('hidden'))toggleSide();});
// azioni sui messaggi
$('#msgs').addEventListener('click',e=>{const b=e.target.closest('.acts button');if(!b)return;const d=b.closest('.m'),raw=d.dataset.raw||'';
  if(b.dataset.act==='copy')(navigator.clipboard?navigator.clipboard.writeText(stripThink(raw)):Promise.reject()).then(()=>toast('Copiato ✓','ok'),()=>toast('Copia non riuscita','err'));
  else if(b.dataset.act==='speak'){const w=ttsOn;ttsOn=true;say(raw);ttsOn=w;}
  else if(b.dataset.act==='regen')regen(d);});
// allegati: trascina e rilascia, incolla un'immagine
['dragenter','dragover'].forEach(ev=>$('#main').addEventListener(ev,e=>{if(e.dataTransfer&&[...e.dataTransfer.types].includes('Files')){e.preventDefault();$('#main').classList.add('drop');}}));
['dragleave','drop'].forEach(ev=>$('#main').addEventListener(ev,()=>$('#main').classList.remove('drop')));
$('#main').addEventListener('drop',e=>{e.preventDefault();const f=e.dataTransfer.files&&e.dataTransfer.files[0];if(f)attachFile(f);});
$('#inp').addEventListener('paste',e=>{const it=[...((e.clipboardData&&e.clipboardData.items)||[])].find(x=>x.type.startsWith('image/'));if(it){e.preventDefault();attachFile(it.getAsFile());}});
if(window.speechSynthesis){speechSynthesis.getVoices();speechSynthesis.onvoiceschanged=()=>speechSynthesis.getVoices();}
initReco();sphInit();sphLoop();stato();cfg();profilo();loadPr();checkLearn();
setInterval(stato,15000);setInterval(checkScaduti,4000);setInterval(checkLearn,20000);setInterval(loadPr,30000);setInterval(checkSeguiti,20000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkSeguiti();});
(async()=>{await loadChats();const n=await loadHistory();      // riapre la chat dov'eri rimasto
  let brief=null;try{brief=(await (await fetch('/briefing?auto=1')).json()).testo;}catch(e){}
  if(brief)add('ai',brief);else if(!n)add('ai',CUR==='principale'?WELCOME:NUOVA);
  setTimeout(checkSeguiti,2500);})();
</script>
</body></html>"""


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("""
╔══════════════════════════════════════════════════╗
║           MAIK 10.0 — Server avviato            ║
║  Agente · documenti · chat · follow-up · app     ║
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
          f"  ·  agente: {'ATTIVO' if CONFIG['agente'] else 'spento'}"
          f"  ·  personalità: {CONFIG['personalita']}")
    print(f"  Endpoint principali:")
    print(f"    POST /chat/stream   — chat in streaming (+ azioni: timer, promemoria, calcoli…)")
    print(f"    POST /vedi          — visione: descrive un frame webcam")
    print(f"    GET  /sessioni · POST /sessioni/nuova /rinomina /elimina   [NUOVO v10]")
    print(f"    GET/POST /documenti · GET /documenti/cerca?q= · /seguiti   [NUOVO v10]")
    print(f"    GET  /promemoria /promemoria/scaduti · GET/POST /lista")
    print(f"    GET  /briefing · POST /personalita · GET /appreso")
    print(f"    GET  /salute /config /timeline /cerca?q=testo")
    print(f"    POST /episodio /obiettivo /relazione /reset /importa\n")

    threading.Thread(target=lambda: [icona_png(n) for n in (192, 512)], daemon=True).start()   # icone pronte
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    server = ThreadingHTTPServer((CONFIG["host"], CONFIG["porta"]), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Chiudo Maik. A presto! 💚")
        server.shutdown()


if __name__ == "__main__":
    main()
