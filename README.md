# MAIK // CORE V7.0

Assistente AI personale in un **singolo file HTML**. Nessuna installazione, nessun build: apri `index.html` nel browser e funziona. Si connette a un modello locale tramite **Ollama** e ricorda tutto in `localStorage`.

## Avvio rapido

1. Apri `index.html` nel browser (doppio click, oppure servilo con `python3 -m http.server`).
2. (Opzionale ma consigliato) avvia Ollama per le risposte AI complete:
   ```bash
   ollama serve
   ollama pull llama3.2        # o un altro modello a tua scelta
   ```
3. In MAIK apri **⚙ Impostazioni** → scegli il modello rilevato → **Salva**.

Senza Ollama, MAIK funziona comunque in modalità offline (memoria, profilo, meteo, promemoria, voce).

## Novità rispetto alla V6.0

- **Risposte in streaming** token-per-token, con pulsante **■ Stop**.
- **Auto-rilevamento dei modelli** installati su Ollama (niente più nome hardcoded) + selettore nelle impostazioni.
- **Pannello Impostazioni**: URL Ollama, modello, persona/personalità, creatività (temperature), TTS on/off, scelta voce, ascolto continuo, colore accento.
- **Memoria strutturata**: fatti, gusti (mi piace / non mi piace), profilo, persone, obiettivi e **promemoria** — tutto iniettato nel prompt.
- **Estrazione automatica** di nome, età, città, lavoro, gusti, insegnamenti e promemoria dalle frasi.
- **Cronologia conversazione persistente**: riapri MAIK e ritrovi la chat.
- **Rendering Markdown** nelle risposte (grassetto, elenchi, codice, link).
- **Rilevamento volto reale** via `FaceDetector` API dove disponibile (fallback simulato altrove).
- **Backup**: esporta/importa tutti i dati in JSON.
- **Analisi emozioni** più ricca con barra d'intensità.
- **Riconoscimento vocale** con risultati intermedi e modalità ascolto continuo.
- Layout **responsive** per mobile e migliorie di robustezza/errore.

## Privacy

Tutti i dati restano nel tuo browser (`localStorage`). Le uniche chiamate di rete sono: Ollama (in locale) e `wttr.in` per il meteo.

## Frasi che MAIK impara da solo

- `Mi chiamo Maik` → salva il nome
- `Ho 28 anni` → salva l'età
- `Vivo a Roma` → salva la città
- `Mi piace la pizza` / `Odio il traffico` → salva i gusti
- `Ti insegno che ...` → memorizza un fatto
- `Ricordami di chiamare il dottore domani alle 9` → crea un promemoria
