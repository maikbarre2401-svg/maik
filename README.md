# MAIK — assistente AI personale

Due modi di usare MAIK, scegli quello che preferisci:

| | **`index.html`** (client) | **`maik_server.py`** (server) |
|---|---|---|
| Avvio | apri il file nel browser | `python maik_server.py` |
| Dipendenze | nessuna | nessuna (solo stdlib Python) |
| Memoria | nel browser (`localStorage`) | su disco in `dati_maik/*.json` |
| Ideale per | uso veloce su un solo dispositivo | memoria persistente e robusta |

Entrambi parlano con un modello locale tramite **Ollama** e rispondono in **streaming**.

## Quali modelli Ollama usare

MAIK usa due modelli: uno per **chattare/ragionare** e uno **multimodale per la webcam** (👁️ Guarda). Scegli in base al tuo PC:

| Il tuo PC | Chat / ragionamento | Visione (webcam) |
|---|---|---|
| 💪 Potente (≥16 GB RAM o GPU) | `qwen2.5:14b` (o `llama3.1:8b`) | `llava:13b` |
| ⚖️ Medio (8–12 GB) | `llama3.1` | `llava` |
| 🪶 Leggero (≤8 GB) | `llama3.2:3b` | `moondream` |

```bash
ollama pull llama3.1     # chat
ollama pull llava        # visione (per far "vedere" MAIK) — compatibile ovunque
```

- Nel **client** (`index.html`): scegli il modello chat e quello visione in **⚙ Impostazioni**.
- Nel **server** (`maik_server.py`): variabili d'ambiente `MAIK_MODELLO` (chat) e `MAIK_MODELLO_VISIONE` (webcam).
- In ogni caso MAIK **prova più modelli visione in cascata** (quello scelto → `llava` → `moondream`), quindi se ne hai almeno uno installato funziona.

> ⚠️ **Errore `unknown model architecture: 'mllama'`** con `llama3.2-vision`?
> Vuol dire che il tuo **Ollama è troppo vecchio** (serve ≥ 0.4). Due soluzioni:
> 1. **Più semplice:** usa `llava` →  `ollama pull llava`
> 2. Aggiorna Ollama all'ultima versione da <https://ollama.com/download>
>
> `llava` e `moondream` funzionano su praticamente tutte le versioni di Ollama.

**Modelli che "ragionano"** (opzionale, serve un Ollama aggiornato): `deepseek-r1:8b` o `qwen3:8b`.
Pensano prima di rispondere: MAIK V8 mostra il loro ragionamento in un riquadro **💭 Ragionamento** a parte,
e non lo legge ad alta voce né lo salva in memoria.

**Per l'agente (V10)** vanno meglio i modelli che seguono bene le istruzioni: `qwen2.5:7b` / `qwen2.5:14b` o `llama3.1`.
I modelli molto piccoli (`llama3.2:1b`) a volte dimenticano i tag degli strumenti: MAIK funziona lo stesso, solo che agisce meno da solo.

---

## 🖐️ Novità V13 — Zep ti vede, parla come una persona, è tuo e fa le cose da solo (sul PC, versione server)

| | Cosa fa |
|---|---|
| 🖐️ **Vede i gesti delle tue mani** | Accendi 👀 (tasto **C** o **G**): con **MediaPipe** (gira sul tuo PC, niente cloud) riconosce la mano. 👋 **saluti** → ti risaluta · 👍 / 👎 · ✌️ · 🤟 (cuore) · ✊ (pugnetto) · ☝️ (guarda in alto) · 🖐️ ferma → **batti cinque** · ✋ mentre parla → **si zittisce**. Ogni gesto scatta una volta sola (niente raffiche). «**conta le mie dita**» → conta le dita che alzi e te le mostra con le sue. |
| 🪞 **Specchio** | Tasto **I** o «fammi da specchio»: copia come **giri e pieghi la testa**, il **sorriso**, la **bocca aperta**, le **sopracciglia** e l'**occhiolino**. |
| ✊✋✌️ **Sasso, carta, forbici** | Tasto **J**, ✊ sul palco o «**giochiamo a sasso carta forbici**». «Sasso… carta… forbici!»: fai la mossa **con la mano davanti alla webcam**, coi bottoni, coi tasti **1 2 3** o scrivendola. Punteggio, rivincita (▶, Invio, 👍 o «ancora»), «basta» per il finale. |
| 🔊 **Voce neurale (Piper)** | Una voce **naturale, gratis e offline**: `pip install piper-tts`, poi in **🎨 Personalizza** scarichi una voce italiana (Paola o Riccardo, una volta sola). La **bocca segue i fonemi veri** con i loro tempi e si **chiude nelle pause** dell'audio. Se Piper non c'è o si rompe, usa la voce del browser da sola. |
| 🎨 **Personalizza** | Tasto **A**: **nome** (anche nella chat e nel titolo), **colore del corpo** e delle **luci**, **accessori** (🎩 cilindro, 🧢 berretto, 🥳 cappellino, 🎧 cuffie, 👓 occhiali, 🕶️ da sole, 🎀 papillon, 🧣 sciarpa), voce del browser, **tono** e **velocità**, animazioni **.vrma** per il tuo .vrm («fai l'animazione saluto»). Il pannello sta di lato: vedi Zep cambiare mentre scegli. |
| ⚡ **Routine e modalità** | Più comandi in uno: «**crea la modalità lavoro: apri gmail, apri google calendar e metti il volume al 30**», poi «**modalità lavoro**». Anche **a orario**: «ogni giorno alle 7:30 fai la routine buongiorno», «…nei giorni feriali». Tasto **R** per crearle, vedere ✓/✗ passo per passo, modificarle, avviarle. Esempi pronti: lavoro, gioco, buongiorno, buonanotte. |
| ⚠️ **Avvisi del PC** | Ti avvisa (in chat, a voce e con una notifica) se la **batteria** è sotto il 20% (o il 10%), il **disco** è quasi pieno, la **RAM** o la **CPU** sono al massimo. Al massimo uno ogni 30 minuti per tipo. |

- **Sicurezza**: una routine si fa **sempre dopo la tua conferma**; «Sì, sempre» vale per quella routine sola e **non esiste** per le routine che scrivono testo. Le routine a orario mandano la loro conferma all'ora giusta. I gesti delle mani **non confermano mai** i comandi del PC.
- Ogni passo di una routine è un comando che già conosci (siti, app, volume, musica, screenshot, «come sta il pc», promemoria, briefing…) oppure «**di' …**» per farti dire una frase. Le frasi da dire o da scrivere tengono le loro virgole.
- Nuovi endpoint: `GET /routine` · `GET /routine/notizie` · `GET /pc/avvisi` · `GET /voce/info` · `GET /animazioni` · `GET /animazioni/<file>` · `POST /routine` `{nome, passi, orario?, giorni?, tipo?}` · `POST /routine/elimina` · `POST /routine/esegui` · `POST /routine/analizza` · `POST /voce` `{testo, velocita?}` (WAV + fonemi) · `POST /voce/scarica` · `POST /voce/imposta` · `POST /animazioni` (file .vrma) · `POST /animazioni/elimina` (le POST solo da questo PC). Nuovo strumento dell'agente: `esegui_routine`.
- Variabili: `MAIK_PIPER` (comando piper, se non usi il modulo Python) · `MAIK_VOCE` · `MAIK_VOCI_URL` · `MAIK_AVVISI=0` (niente avvisi) · `MAIK_AVVISI_OGNI` (secondi, 60) · `MAIK_ROUTINE_OGNI` (secondi, 20) · `MAIK_MODELLO_MANI_URL`.
- La prima volta servono internet per il modello delle mani (MediaPipe, ~8 MB) e per la voce Piper (28–63 MB): poi restano in `dati_maik/` e funziona tutto offline.

---

## 🌱 Novità V12 — Zep parla, gesticola e vive (sul PC, versione server)

| | Cosa fa |
|---|---|
| 👄 **Bocca vera** | Il labiale nasce dal **testo italiano**: ogni suono ha la sua forma — labbra **chiuse** per m/b/p, **denti sul labbro** per f/v, **lingua** per l/n/t/d, labbra **tonde** per o/u, denti per s/z, la «i» muta di *ciao*, le doppie più lunghe, l'accento. I suoni si fondono tra loro (coarticolazione) come in una persona vera. Si **riallinea parola per parola** con la voce del browser e **impara quanto è veloce** la tua voce (anche quelle che non dicono dove sono le parole). |
| 🙌 **Gesti mentre parla** | Sceglie i gesti dalle parole: **saluta** («ciao»), **conta sulle dita** («primo, secondo», «1. 2. 3.»), **indica la chat** («ecco», «qui sotto»), mano sul **petto** («io», «secondo me»), **palmo verso di te** («tu»), braccia **larghe** («tutto», «enorme»), mani **vicine** («un pochino»), **spallucce** («forse», «non so»), **pollice in su** («ottimo»), **festeggia**, si **inchina** («grazie»), **mano al mento** («allora…», «vediamo»). Batte il tempo con la mano sulle parole importanti, alza le **sopracciglia** sulle domande, distoglie lo sguardo mentre "pensa" cosa dire. |
| 🤖 **Zep rifatto** | Il viso è uno **schermo**: occhi che si chiudono, sorridono (^ ^), si arrabbiano, si stupiscono, dormono, vedono stelline o **cuori**, fanno l'occhiolino; **sopracciglia**; bocca con **denti e lingua**. Ha **mani con le dita** (conta, indica, pollice in su). |
| 🧍 **Il tuo personaggio** | Con i tuoi .vrm/.glb muove anche **dita** e **gambe** (cammina); con i modelli **Ready Player Me** usa tutti i **15 visemi**, con i modelli **ARKit** mascella, labbra e sopracciglia. |
| 🌱 **Una vita sua** | Da solo si **guarda attorno**, **canticchia** (♪), **passeggia**, sposta il peso, si guarda la mano. Se non lo usi per un po' **si annoia**, **sbadiglia**, si **stiracchia** e poi **si addormenta** (💤 Zzz). Quando torni (mouse, tastiera o webcam) **si sveglia**: salta, si stropiccia gli occhi e ti saluta. Di notte ha sonno prima. Si spegne con **🌱 Vivo da solo** nella barra laterale. |
| 🕺 **Balla** | Scrivi o di' «**balla!**» (e «smetti di ballare»). Con **B** (o 🎵) **ascolta la tua musica dal microfono**, trova il ritmo e **balla a tempo**, con i colori che cambiano a ogni colpo. |
| 👆 **Toccalo** | Un **clic** su Zep: sulla testa **ride** (solletico), sulla pancia fa un **salto**, sulla mano ti dà il **cinque**. Se esageri **si arrabbia**… e al settimo tocco **gli gira la testa** 😵‍💫. |
| 🌅 **L'ora del giorno** | Luce **calda** la mattina (e si stiracchia quando apri MAIK), **arancione** la sera, **blu** di notte (e sbadiglia). «**Buonanotte**» → ti saluta e va a dormire. |
| 💬 **Reazioni** | Mentre scrivi **guarda la tastiera**; pollice in su quando un'azione riesce, **mano in faccia** quando no; salta e indica quando suona un promemoria; cuori se gli dici che gli vuoi bene. |

### 🖥️ Più comandi del PC (sempre con conferma)

| Di' o scrivi | Cosa fa |
|---|---|
| «**alza il volume**» · «abbassa il volume di 20» · «**volume al 30**» · «**muto**» · «togli il muto» | volume del PC |
| «**metti in pausa la musica**» · «riprendi la musica» · «**canzone successiva**» · «brano precedente» | Spotify, YouTube nel browser, lettori multimediali (tasti multimediali) |
| «**fai uno screenshot**» · «**cosa c'è sul mio schermo?**» | salva lo schermo in *Immagini/MAIK*, lo vedi nella chat e, se chiedi cosa c'è, **lo guarda il modello visione** |
| «**trova il file contratto**» · «dov'è la foto del gatto?» · «**apri il pdf della bolletta**» · «apri ricetta.txt» | cerca **per nome** nelle tue cartelle (desktop, documenti, download, immagini, musica, video, anche OneDrive) e ti mostra i risultati con **📂 Apri** |
| «**digita: ciao a tutti, arrivo tra 5 minuti**» · «scrivi nella finestra «…»» | dopo il sì hai **5 secondi** per cliccare nella finestra giusta, poi scrive **al posto tuo** (anche accenti ed emoji) |
| «**blocca il pc**» | blocca lo schermo (per rientrare serve la tua password) |

- Anche a parole tue: l'agente usa `imposta_volume`, `controlla_musica`, `screenshot`, `cerca_file`, `apri_file`, `scrivi_testo`, `blocca_pc`.
- **Sicurezza**: si aprono solo **file delle tue cartelle personali** e mai **programmi, script o collegamenti** (.exe, .bat, .ps1, .lnk, .sh…). Per **scrivere al posto tuo** non esiste «Sì, sempre»: chiede **ogni volta**. Gli screenshot si vedono solo da questo PC.
- **Come funziona sotto**: su **Windows** tasti multimediali veri e digitazione Unicode (nessun programma da installare; lo screenshot usa PowerShell); su **macOS** AppleScript (`screencapture` per lo screenshot: dai il permesso «Registrazione schermo»; per «digita» il permesso «Accessibilità»); su **Linux** il primo programma installato tra `pactl`/`wpctl`/`amixer` (volume), `playerctl` (musica), `gnome-screenshot`/`spectacle`/`grim`/`scrot` (screenshot), `xdotool`/`wtype` (digitare), `loginctl` (blocco). Se manca, MAIK ti dice quale installare.
- Nuovi endpoint: `GET /pc/file?q=…` · `GET /pc/screenshot/<nome>` · `POST /pc/prepara {tipo, …}` (solo da questo PC). `/chat/stream` restituisce anche `"file"` e `"schermate"`.

---

## 🧍 Novità V11 — Zep, il tuo personaggio 3D (sul PC, versione server)

Al posto della sfera c'è un **personaggio 3D animato** nel browser: il tuo, oppure **Zep**, il robottino integrato.
Si usa con `maik_server.py` su un **PC** (Chrome o Edge, schermo largo). Su telefono e su schermi piccoli resta la sfera di sempre,
e `index.html` rimane la versione V10 che funziona ovunque.

```bash
python maik_server.py            # si apre come finestra-app (Chrome/Edge), non come una scheda
python maik_server.py --no-app   # oppure in una scheda normale
```

| | Cosa fa |
|---|---|
| 🧍 **Il tuo personaggio** | Carica un **.vrm** (es. da **VRoid Studio**, gratis: *Esporta → VRM*) o un **.glb** dalla barra laterale (**📤 Carica**) o **trascinandolo sul personaggio**. Con i VRM usa espressioni, visemi e sguardo veri; con i .glb riconosce le ossa (Mixamo, Blender…), le forme del viso (ARKit/Ready Player Me) e le animazioni contenute nel file. Senza file c'è **Zep**, disegnato da codice. Resta salvato in `dati_maik/avatar/`. |
| 🗣️ **Parla davvero** | Dice la risposta **frase per frase mentre la scrive**, con la **bocca a tempo parola per parola**, i **sottotitoli** sotto di lui, palpebre, respiro, piccoli movimenti della testa, **emozioni** prese dalla risposta e **gesti** (saluta, annuisce, scuote la testa, festeggia, alza le spalle). Il codice non lo legge ad alta voce. |
| 🎙️ **Conversazione a voce** | **M** (o 🎙️): parli e risponde a voce, a mani libere. **Puoi interromperlo** mentre parla (la sua voce nel microfono viene riconosciuta e ignorata). Oppure **tieni premuto Spazio** per parlare e lascialo per mandare. |
| 👀 **Ti guarda** | Segue il **mouse** con lo sguardo. Con la webcam (**C** o 👀) segue **il tuo viso**: con MediaPipe (scaricato la prima volta) si accorge anche quando **sorridi** e ti sorride; altrimenti usa il rilevamento volti del browser o il movimento. Quando torni dopo un po' ti saluta con la mano. |
| 🖥️ **Usa il tuo PC** (con conferma) | «**apri youtube**», «**cerca** la ricetta della carbonara **su youtube**», «**apri la calcolatrice**», «**apri la cartella download**», «**come sta il pc?**» (CPU, RAM, disco, batteria, da quanto è acceso). Anche a parole tue: l'agente usa gli strumenti `apri_sito`, `cerca_web`, `apri_app`, `apri_cartella`, `info_pc`. **Prima di aprire qualcosa chiede sempre conferma** con una scheda **✓ Sì · ✓ Sì, sempre · ✕ No** (o dicendo/scrivendo «sì» / «no»). |
| 🗗 **Sempre a portata** | **P**: **mini-finestra sempre in primo piano** con Zep, sottotitoli e casella per scrivere (Chrome/Edge 116+). **F**: *Solo Zep* a tutto schermo. **S**: *guarda il mio schermo* (una foto dello schermo da far vedere al modello visione). **Z**: inquadratura busto/intero. **?**: tutte le scorciatoie. Sul personaggio: trascina per girarlo, rotellina per lo zoom, doppio clic per rimetterlo a posto. |

**La prima volta serve internet**: Three.js, three-vrm e MediaPipe vengono scaricati dal CDN e salvati in `dati_maik/lib/`; poi il personaggio funziona anche offline.
Se proprio non si possono scaricare, MAIK usa la sfera.

> **ZEPETO**: l'app non permette di esportare i personaggi in 3D. Per un personaggio simile, crealo con **VRoid Studio** (gratis, Windows/Mac)
> ed esportalo in **.vrm**; va bene anche qualsiasi **.glb** (Mixamo, Sketchfab, Blender…).

### Sicurezza dei comandi del PC
- Solo **siti http(s)**, le **app note** (calcolatrice, blocco note, esplora file, impostazioni, Chrome, Edge, Firefox, Spotify, Word, Excel,
  PowerPoint, VS Code, Discord, Steam, posta…) e le **cartelle personali** (desktop, documenti, download, immagini, musica, video). Niente comandi arbitrari.
- Le conferme valgono **solo dalla finestra di MAIK su questo PC**: un altro sito o un altro dispositivo in rete vengono bloccati
  (controllo di Origin e Host, solo indirizzi locali).
- Per aggiungere le tue app crea `dati_maik/app_pc.json`, per esempio: `{"photoshop": "C:/Program Files/Adobe/Photoshop/Photoshop.exe"}`.
- «Sì, sempre» si può annullare: `POST /pc/fiducia {"azzera": true}` (o cancellando `pc_fiducia` da `dati_maik/ricordi.json`).

| Variabile | Effetto |
|---|---|
| `MAIK_PC=0` | spegne i comandi del PC |
| `MAIK_PC_FINTO=1` | prova: le azioni vengono solo registrate, non apre niente |
| `MAIK_PC_REMOTO=1` | permette le conferme anche da altri dispositivi (sconsigliato) |
| `MAIK_APP=0` (o `--no-app`) | apre MAIK in una scheda normale invece che come finestra-app |
| `MAIK_CDN` | da dove scaricare Three.js la prima volta (predefinito: jsDelivr) |
| `MAIK_AVATAR_MAX_MB` | dimensione massima del personaggio (predefinita: 100 MB) |

Nuovi endpoint: `GET /pc/info` · `GET /pc/attesa` · `POST /pc/conferma {id, si, sempre}` · `POST /pc/fiducia` · `GET /pc/registro` ·
`GET/POST /avatar` (il file grezzo, intestazione `X-Nome`) · `GET /avatar/info` · `POST /avatar/elimina` · `GET /lib/…` (librerie in cache).
`/chat/stream` restituisce anche `"conferme"`.

---

## 🤖 Novità V10 — agente, documenti, chat, amico vero, app (client e server)

| | Cosa cambia |
|---|---|
| 🤖 **MAIK agisce da solo** | Non servono più le frasi esatte: chiedi le cose **a parole tue** («stasera pasta, metti in lista gli ingredienti e avvisami tra 20 minuti di buttarla») e il modello usa i suoi **strumenti**: promemoria, timer, lista, note, obiettivi, personalità, **meteo**, **ora nel mondo**, **calcoli**, **ricerca nei documenti** e **nella memoria**. Per i dati che non sa (meteo, calcoli, ricerche) fa un **secondo giro**: riceve i risultati veri e finisce la risposta. Sotto la risposta vedi i **chip** di cosa ha fatto (✓ verde, ✗ rosso se qualcosa non va), anche **in diretta**. Ogni richiesta è controllata prima di essere eseguita (niente codice, calcolatrice sicura, timer max 48 ore, niente doppioni dopo «rigenera»). Si spegne in ⚙ Impostazioni (client) o con `MAIK_AGENTE=0` (server). |
| 📚 **I tuoi documenti** | Carica appunti, ricette, contratti, manuali, codice… (trascina, scegli o incolla il testo; dal 📎 c'è anche «salva nei documenti»). MAIK li divide in pezzi e, quando gli fai una domanda, mette nel prompt **solo i pezzi pertinenti** (ricerca BM25) e **cita la fonte** `[nome file]`, che vedi come badge e come chip 📄 (passa sopra per l'anteprima). Nel client restano nel browser (IndexedDB), nel server su disco. |
| 💬 **Più chat** | Nuova chat, rinomina, elimina, dalla barra laterale o con **Ctrl+K**. Ogni chat ha la sua cronologia e il suo contesto, ma **la memoria su di te è una sola**. Prendono il nome dalla prima domanda e alla riapertura ritrovi la chat dov'eri rimasto. La vecchia conversazione diventa la **⭐ Chat principale** (anche dai backup V9). |
| 🔁 **Follow-up da amico vero** | Se dici «domani ho l'esame di storia», «giovedì vado dal dentista alle 15» o «stasera esco con Giulia», MAIK se lo segna (chip 🔁) e **al momento giusto te lo chiede da solo**: «Ehi! 🤞 Com'è andato l'esame di storia?» — con notifica, voce e suono. Nel frattempo ti fa il tifo, e quando rispondi sa di averti appena chiesto. Le regole capiscono le frasi tipiche anche offline; l'IA migliora la domanda e trova gli eventi detti in altri modi. Non scatta con «domani ho fame», «domani non ho niente», «oggi ho avuto l'esame» o con le domande. |
| 📲 **App installabile** (server) | `maik_server.py` ora è una **PWA**: icona generata dal server (nucleo + M), manifest, service worker. In Chrome/Edge: **📲 Installa MAIK come app** nella barra laterale (o dal menu del browser) → si apre in una finestra sua, come un programma. |
| 🐛 **Bug corretti** | Sul telefono la barra laterale partiva 48 px sotto la barra in alto (client e server); «sabato alle 9» detto di sabato non veniva capito; nel client, con il browser pieno il salvataggio poteva bloccarsi (ora accorcia le chat vecchie e avvisa). |

Esempi da provare:

```text
stasera pasta al pomodoro: mettimi in lista gli ingredienti e ricordami tra 20 minuti di buttarla
mi fai il conto di 1200 più il 22% di IVA?            che ore sono adesso a New York e a Tokyo?
cosa dice il mio contratto sul deposito?              (dopo averlo caricato in 📚)
domani ho l'esame di storia                           → il giorno dopo: «com'è andato?»
```

---

## ✨ Novità V9 — grafica e sistema (client e server)

| | Cosa cambia |
|---|---|
| 🧠 **Nucleo neurale 3D** | Al posto della vecchia sfera: una rete di neuroni con sinapsi e impulsi che corrono, anelli HUD, onde d'urto ai cambi di stato. **Nitido su ogni schermo** (prima era sfocato su telefoni e schermi HiDPI). Colori per stato: viola = pensa, verde = ti ascolta, ambra = allarme. Mentre MAIK parla pulsa **a ogni parola**; mentre ascolta segue il **volume vero del microfono** (sul computer). |
| 🎨 **6 temi completi** | Neon, Synthwave, Matrix, Solar, Ice, Ruby. Cambiano davvero *tutto* (prima ~60 colori restavano ciano fisso), con sfondo ad aurora animata ed effetto vetro. Anteprima dal vivo nelle impostazioni. |
| ⌘ **Palette comandi** | **Ctrl+K** (o il tasto ⌘K): cerca e lancia qualsiasi cosa — briefing, timer, temi, personalità, memoria, strumenti… |
| 🚀 **Avvio con controlli veri** | All'apertura (una volta per sessione) MAIK controlla memoria, Ollama, voce italiana, promemoria e webcam e ti mostra lo stato. Si salta con un clic; si spegne nelle impostazioni. |
| 📎 **Allegati** | Trascina, incolla o allega un'**immagine**: la guarda il modello visione e risponde alla tua domanda («cosa c'è scritto qui?»). Oppure un **file di testo/codice** (txt, md, csv, json, py, js…): va al modello insieme al messaggio. Le immagini non vengono salvate. |
| 💬 **Messaggi migliori** | Codice con **evidenziazione dei colori** e pulsante *Copia*; sotto ogni risposta **⧉ copia · 🔊 ascolta · ↻ rigenera**; **velocità vera** del modello (token/s, tempo della prima parola, durata). Il pulsante **■ stop** ora tiene il testo già scritto. |
| 👂 **Parola di attivazione «Maik»** | In Modalità Amico puoi farlo rispondere solo quando dici «Maik» (es. «Ehi Maik, che ore sono?»): niente risposte alla TV o ad altre persone. |
| 🧠 **Memoria completa** | Una finestra con tutti i ricordi (con l'etichetta di chi li ha imparati: IA, nota, gusti…), il riassunto delle conversazioni e un filtro: puoi **dimenticare** ciò che vuoi. |
| ♿ **Accessibilità e telefono** | Contorni di focus per la tastiera, etichette sui pulsanti a icona, rispetto di «riduci movimento» del sistema. Sul telefono si parte con la chat libera e la barra laterale si chiude toccando la chat. |
| 🐛 **Bug corretti** | ■ stop cancellava la risposta e mostrava `_(generazione interrotta)_`; l'importazione di un backup perdeva note, lista, umore e riassunto; nel server i font non venivano caricati; animazioni che ricalcolavano gli stili a ogni fotogramma. |

---

## 🧠 Novità V8 — più intelligente (client e server)

| | Cosa fa |
|---|---|
| 🧠 **Impara da solo con l'IA** | Dopo ogni frase in cui parli di te, il modello estrae i fatti nuovi (città, lavoro, persone, gusti, obiettivi…) in JSON e li aggiunge alla memoria, senza doppioni. Vedi un avviso *«🧠 Ho capito: …»*. Funziona con frasi normali, non solo con «mi chiamo…». Si spegne in ⚙ Impostazioni (client) o con `MAIK_APPRENDIMENTO_IA=0` (server). |
| 🔎 **Memoria rilevante** | Nel prompt non finiscono più "gli ultimi 15 ricordi" a caso, ma quelli **pertinenti a ciò di cui stai parlando** + i più recenti. Anche un ricordo di mesi fa torna fuori al momento giusto. |
| 📜 **Riassunto a lungo termine** | Ogni 12 scambi il client aggiorna un riassunto di chi sei e dei temi importanti (il server lo faceva già): MAIK non dimentica le conversazioni lunghe. |
| ⚡ **Azioni vere, anche offline** | Timer, **promemoria con orario che suonano davvero** (suono + voce + notifica di sistema, anche quelli scaduti mentre la pagina era chiusa), calcoli, ora nel mondo, lista della spesa, note, dado/moneta, meteo. Scrivi **aiuto** per l'elenco. |
| ☀️ **Briefing del giorno** | Data, meteo, promemoria di oggi, un obiettivo, la lista, una frase del giorno. Parte da solo la prima volta che apri MAIK nella giornata, o scrivi **briefing**. |
| 🎭 **6 personalità** | 🫂 Amico · 💪 Coach · 🎓 Prof · 😂 Comico · 🧘 Zen · 🧠 Genio — con un click nella barra laterale o scrivendo «modalità coach». |
| 💙 **Grafico dell'umore** | L'andamento di come ti senti, nella barra laterale. |
| 💭 **Ragionamento separato** | Supporto ai modelli che pensano (`<think>`), vedi sopra. |
| 🐛 **Bug corretti** | «vivo a Milano e ho un cane…» salvava la città *"Milano E Ho Un Cane Che"*; «sono un po' triste» salvava il lavoro *"po triste"*; «sto a casa…» diventava una città. Ora le frasi si fermano alle congiunzioni. Su telefono l'intestazione non esce più dallo schermo. |

### Cosa puoi dire a MAIK (azioni istantanee)

```text
metti un timer di 10 minuti          · annulla il timer · svegliami domani alle 7
ricordami alle 18 di chiamare la mamma · ricordami tra 20 minuti di girare la pasta
che promemoria ho?                   · cancella i promemoria
aggiungi latte, pane e uova alla lista · cosa c'è nella lista? · togli pane dalla lista
quanto fa 15% di 230                 · radice di 144 · 3 per 4 più 2
che ore sono a Tokyo?                · che giorno è?
che tempo fa a Milano?               · briefing
lancia due dadi · testa o croce · numero a caso tra 1 e 50
prendi nota: il wifi è Casa123
modalità coach / prof / comico / zen / genio / amico
```

Il riconoscimento è prudente: frasi normali come *«sono sveglia da 3 ore»*, *«ho perso il promemoria»* o *«dimmi una lista di 5 film»* vanno all'IA, non diventano comandi.

---

## MAIK // CORE V10 — `index.html`

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

### Sfera 3D + Strumenti (ultimo aggiornamento)

- 🔮 **Nuova sfera 3D**: nuvola di punti che **ruota di continuo** (animata anche da ferma), con nucleo pulsante e barre quando "parla". Cambia colore in base allo stato (idle / pensa / parla / volto rilevato). Ora **si ridimensiona da sola** in base allo spazio: niente più sfera bloccata in un angolo su mobile. La puoi trascinare, bloccare (📌) e ricentrare.
- 🧰 **Pannello Strumenti** (pulsante in alto) con 12 utility:

  | | | |
  |---|---|---|
  | 🧮 Calcolatrice | ⏱️ Timer/Pomodoro | ⏲️ Cronometro |
  | 🎲 Random (dado/moneta/numero) | 🔄 Convertitore (lunghezza, peso, volume, temperatura) | 🌍 Orologi mondiali |
  | 📝 Note rapide | 🔑 Generatore password | 🌐 Traduttore (AI) |
  | 📋 Riassumi testo (AI) | 🔢 Conta parole/caratteri | 🎯 Scegli per me |

  Le utility funzionano **offline**; *Traduttore* e *Riassumi* usano il modello Ollama.

### 🫂 Modalità Amico (compagnia)

Pulsante **🫂 AMICO** in alto: trasforma MAIK in un compagno che **ti vede e ti parla** come un amico vero.

- 📷 **Ti vede davvero**: accende la webcam e rileva la tua **presenza reale** — `FaceDetector` nativo dove c'è, altrimenti rilevamento del **movimento** (differenza tra fotogrammi). Niente più rilevamento finto a caso.
- 👋 **Ti accoglie quando torni**: se sparisci e poi riappari, ti saluta ("Bentornato! Mi eri mancato 😊").
- 🎙️ **Ascolto continuo a mani libere**: parli e MAIK risponde a voce; mentre parla mette in pausa il microfono per non sentirsi da solo, poi riapre le orecchie.
- 💬 **Inizia lui la conversazione**: quando c'è silenzio (ogni ~1–2 min) MAIK ti scrive/parla spontaneamente, usando il contesto (nome, ora, promemoria, obiettivi, meteo). Se Ollama è online a volte genera lui la frase, altrimenti usa frasi calorose pronte.
- 🔊 La voce (TTS) si attiva da sola in questa modalità.

> La webcam e il microfono partono al **click** sul pulsante (richiesto dai browser) e funzionano su `localhost`/HTTPS. Tutto resta in locale.

## Privacy

Tutti i dati restano nel tuo browser (`localStorage`, e i documenti in IndexedDB). Le uniche chiamate di rete sono: Ollama (in locale) e `wttr.in` per il meteo.

---

## MAIK — Server V13 — `maik_server.py`

Server in **puro Python (solo libreria standard, niente pip; Piper per la voce neurale è facoltativo)** con memoria avanzata salvata su disco. Serve la GUI nel browser e fa da ponte verso Ollama.

```bash
ollama pull llama3.1      # una volta
python maik_server.py     # si apre da solo nel browser su :8137
```

Se nella stessa cartella c'è il tuo `aria.html`, il server usa quella interfaccia 3D; altrimenti parte con una **GUI integrata** completa — **sfera 3D animata + chat in streaming + pannello 🧰 strumenti + 🫂 Modalità Amico + 👁️ visione webcam** — collegata agli endpoint del server, così la memoria viene salvata **su disco** (non nel browser). Funziona out-of-the-box senza `aria.html`.

Anche il server ha la **🫂 Modalità Amico** (ti vede, ti ascolta e ti parla) e il pulsante **👁️ Guarda**: cattura un fotogramma dalla webcam e lo manda al modello multimodale (`MAIK_MODELLO_VISIONE`) tramite il nuovo endpoint `POST /vedi`, e MAIK descrive cosa vede.

### Nuovi endpoint V10

| | |
|---|---|
| Chat | `GET /sessioni` · `GET /sessioni/storia?id=` · `POST /sessioni/nuova` `{titolo?}` · `POST /sessioni/rinomina` `{id, titolo}` · `POST /sessioni/elimina` `{id}` |
| Documenti | `GET /documenti` · `POST /documenti` `{nome, contenuto}` · `POST /documenti/elimina` `{id}` · `GET /documenti/cerca?q=` |
| Follow-up | `GET /seguiti` (in attesa) · `GET /seguiti/scaduti?sessione=` (quelli da chiedere ora: diventano messaggi di MAIK) · `POST /seguiti/elimina` `{id}` |
| App | `GET /manifest.webmanifest` · `GET /sw.js` · `GET /icona-192.png` · `GET /icona-512.png` |

`POST /chat/stream` accetta `"sessione"`; durante la risposta può mandare eventi `{"strumento": {...}}` (l'agente sta usando uno strumento)
e alla fine restituisce anche `"azioni"`, `"fonti"`, `"seguito"`, `"sessione"` e `"titolo"`.
Nuovi file in `dati_maik/`: `sessioni.json`, `documenti.json`, `seguiti.json` (inclusi in esporta/importa).

### Nuovi endpoint V9

`POST /imparato/elimina` · `POST /episodio/elimina` · `POST /riassunto/elimina` (per la finestra Memoria).
`POST /chat/stream` accetta anche `"allegato": {"nome", "contenuto"}` (un file di testo: va al modello ma non alle azioni) e
`"rigenera": true`, e nella risposta finale restituisce `"stat"` con token/s, prima parola e durata.
Nel diario ogni domanda è salvata al massimo a 4000 caratteri (i file allegati non finiscono nel diario).

### Nuovi endpoint V8

`GET /promemoria` · `GET /promemoria/scaduti` (la GUI li controlla ogni 4 s e fa suonare l'allarme) · `POST /promemoria/completa` ·
`GET`/`POST /lista` · `GET /briefing` · `POST /personalita` · `GET /appreso` (cosa ha imparato l'IA).
Promemoria e lista sono salvati su disco in `dati_maik/promemoria.json` e `dati_maik/lista.json`.
L'ora nelle altre città funziona anche su Windows senza il pacchetto `tzdata` (regole dell'ora legale integrate).

### Novità V6.0 rispetto a v5.0

- ⚡ **Risposte in streaming** token-per-token (`POST /chat/stream`, SSE) — niente più attese mute.
- 🔒 **Memoria a prova di crash**: scritture atomiche (`.tmp` + `os.replace`) e **lock multi-thread**, niente JSON corrotti con richieste in parallelo.
- 📁 Tutti i dati in una **cartella dedicata** `dati_maik/`, con **migrazione automatica** dai vecchi file di v5.0.
- ⚙️ **Configurabile da variabili d'ambiente**: `MAIK_MODELLO`, `MAIK_PORTA`, `MAIK_OLLAMA`, `MAIK_DATA`, `MAIK_HOST`, `MAIK_NOME`.
- 🐛 **Bug-fix estrattore nomi**: *"sono stanco"* non viene più salvato come nome "Stanco".
- 🩺 Nuovi endpoint `GET /salute` e `GET /config`; chiamate a Ollama più robuste con errori chiari.

Eredita da v5.0: profilo ricco, memoria episodica, timeline, umore tracker, ricerca, obiettivi/sogni, relazioni, reset selettivo, statistiche.

### Esempio configurazione

```bash
MAIK_MODELLO=llama3.2 MAIK_PORTA=9000 python maik_server.py
MAIK_APPRENDIMENTO_IA=0 python maik_server.py     # spegne l'apprendimento con l'IA
MAIK_AGENTE=0 python maik_server.py               # spegne gli strumenti dell'agente
MAIK_SEGUITI_RITARDO=30 python maik_server.py     # demo: chiede «com'è andata?» dopo 30 secondi
```

> 📲 Per installarlo sul **telefono** come app serve HTTPS (i browser lo chiedono per i service worker); sul computer
> con `localhost` funziona subito. Per usarlo dal telefono in casa: `MAIK_HOST=0.0.0.0 python maik_server.py`
> e apri `http://IP-DEL-PC:8137`: chat, documenti e memoria funzionano; microfono, webcam e installazione
> invece vogliono HTTPS (regola dei browser).

## Frasi che MAIK impara da solo

Con la V8 l'IA estrae i fatti da **qualsiasi** frase in cui parli di te. Queste vengono riconosciute anche senza IA:

- `Mi chiamo Maik` → salva il nome
- `Ho 28 anni` → salva l'età
- `Vivo a Roma` → salva la città
- `Mi piace la pizza` / `Odio il traffico` → salva i gusti
- `Ti insegno che ...` → memorizza un fatto
- `Ricordami di chiamare il dottore domani alle 9` → crea un promemoria **che suona domani alle 9**
