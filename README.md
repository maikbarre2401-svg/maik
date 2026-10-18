# MAIK PRIME — assistente AI personale

Due modi di usare MAIK, scegli quello che preferisci:

| | **`index.html`** (client) | **`maikprime.py`** (server) |
|---|---|---|
| Avvio | apri il file nel browser | `python maikprime.py` |
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
ollama pull llava        # visione (per far "vedere" MAIK e, dalla V18, leggere foto e scansioni) — compatibile ovunque
ollama pull nomic-embed-text   # (V16-18, facoltativo) ricerca per significato nei documenti e nelle chiacchierate
```

- Nel **client** (`index.html`): scegli il modello chat e quello visione in **⚙ Impostazioni**.
- Nel **server** (`maikprime.py`): variabili d'ambiente `MAIK_MODELLO` (chat) e `MAIK_MODELLO_VISIONE` (webcam).
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

## 🛡️ Novità V23 — MAIK PRIME affidabile: annulla, autodiagnosi, copie di sicurezza, «pensaci meglio» (versione server)

Tutto quello che c'era, ma che **funziona meglio**: se sbaglio si torna indietro, se qualcosa non va te lo dico (con il rimedio) e i tuoi dati sono al sicuro.

| | Cosa fa |
|---|---|
| ↩ **Annulla** | Per ogni domanda mi segno com'erano i dati che cambio (promemoria, lista, spese, calendario, cose da fare, abitudini, routine, automazioni, obiettivi, invenzioni, documenti, quello che so di te). Sotto la risposta compare **↩ Annulla (⏰ promemoria)**; oppure scrivi «**annulla**», oppure premi **Ctrl+Z** (fuori dalla casella di testo). «**cosa posso annullare?**» → le ultime modifiche, ognuna col suo bottone. Se dopo hai già cambiato di nuovo la stessa cosa, la modifica vecchia non la tocco e te lo spiego. Le azioni già fatte sul PC (aprire un programma…) non si possono annullare. |
| 🩺 **Autodiagnosi** | «**funziona tutto?**», «controllati», «cosa non funziona?» → controllo il cervello (Ollama acceso? versione?), i modelli (chat, visione, ricerca per significato), la velocità, i file dei dati (leggibili? file a metà?), lo spazio sul disco, le copie di sicurezza, internet, la voce e i comandi del PC. Per ogni problema: cosa succede, **come si sistema** e, se serve, il **comando da copiare** (es. `ollama pull llava`). Il pannello **🩺 Diagnosi, copie e annulla** (barra a sinistra, o Ctrl+K «diagnosi») controlla anche il **browser**: microfono, webcam, voce italiana, grafica 3D, notifiche, pagina sicura. |
| 🔧 **Ripara** | Nel pannello: i **file dei dati rovinati** li metto da parte (`nome.json.rotto-…`, non cancello mai niente) e li recupero dall'ultima copia di sicurezza; i **file a metà** (dopo uno spegnimento brusco) li tolgo. E adesso un file rovinato **non viene più sovrascritto** da uno vuoto: lo sposto prima, così i dati restano lì. |
| 💾 **Copie di sicurezza** | Ogni giorno faccio da sola una copia di tutti i tuoi dati (uno zip in `dati_maik/backup`, tengo le ultime 7). «**fai un backup**» → una copia subito; «**i miei backup**» → l'elenco; «**ripristina il backup di ieri**» (o «del 12 ottobre», «più recente») → ti propongo la copia giusta e **chiedo sempre conferma**; prima di ripristinare faccio una copia di come sono adesso, così puoi tornare indietro. Dal pannello: «Fai una copia adesso» e «↩ Ripristina» (con conferma nella riga stessa). |
| 🎯 **Pensaci meglio** | Per le domande difficili: «**pensaci bene: …**» (anche «rifletti bene: …», «rispondi con calma: …»), oppure il bottone **🎯 pensaci meglio** sotto l'ultima risposta. Scrivo una **bozza**, la rileggo come un **revisore severo** (fatti, numeri, conti, cose mancanti) e ti do solo la **versione finale**, segnata «🎯 RILETTA DA UN REVISORE». Mentre lavoro vedi «📝 Scrivo una prima bozza… → 🔍 La rileggo…». Ci metto un po' di più (due passaggi), per questo lo fai partire tu. |
| 🔤 **Capisco anche se scrivi in fretta** | «ricodami di chiamare mamma», «agiungi il latte alla lista», «apri il calendraio», «xke nn funziona», «cmq»… correggo i **refusi dei comandi** e te lo faccio vedere («🔤 Ho capito: «ricordami di …»»). Solo correzioni sicure: le parole vere («chiedi», «credimi», «scrivo»…), i nomi, i testi da scrivere («digita …»), le citazioni e i link restano come sono, e al modello arriva comunque il tuo testo originale. |
| 🔁 **Il cervello che si riprende da solo** | Se Ollama inciampa prima di rispondere (occupato, si sta riavviando) **riprovo da solo**; se il modello che hai scelto non c'è più, ne uso uno che hai installato (e lo scrivo nel terminale). Se Ollama è proprio **spento**, in alto compare la barra **🔌 Il mio cervello è spento** con 🔁 Riprova e 🩺 Diagnosi: appena torna, **ti rimando la domanda da solo**. |
| ⚡ **Risposte più fluide** | Il testo che arriva lo disegno al massimo ~25 volte al secondo invece che a ogni pezzetto (prima rifacevo tutto il testo per ogni parola): con i modelli veloci e le risposte lunghe la pagina non si impunta più. E se stai leggendo più su, non ti trascino in fondo. |

- Nuove variabili: `MAIK_BACKUP=0` (niente copie automatiche), `MAIK_BACKUP_GIORNI` (quante copie automatiche tengo, default `7`), `MAIK_DIAGNOSI_WEB` (l'indirizzo che uso per controllare internet).
- Nuovi endpoint: `GET /diagnosi` (`?veloce=1` senza internet né file) · `POST /diagnosi/ripara {cosa: json|tmp|backup}` · `GET /annulla` · `POST /annulla {id?}` · `GET /backup` · `POST /backup/crea` · `POST /backup/ripristina {nome}`. Le richieste che cambiano qualcosa sono accettate solo dalla GUI di MAIK. `/chat/stream` accetta `"accurato": true`, manda gli eventi `"accurato"` (le fasi) e restituisce `"annullabile"`, `"capito"`, `"accurato"`, `"offline"`, `"diagnosi"`, `"backup"`, `"backup_ripristina"`.
- I dati: le copie in `dati_maik/backup/maik-AAAA-MM-GG_HHMMSS-(auto|manuale|prima-del-ripristino).zip` (tutti i `.json`, tranne gli indici di ricerca che si ricalcolano da soli).

## ⚡ Novità V22 — MAIK PRIME più veloce, e più attento quando ti vede (versione server)

Prima: la prima risposta ci metteva tanto, e con la webcam accesa tutto rallentava. Ora:

| | Cosa fa |
|---|---|
| 🧠 **Il cervello sempre pronto** | Il modello **resta caricato** in Ollama tra una domanda e l'altra (`keep_alive`, 30 minuti; la visione 10), la **memoria di lavoro è fissa** (`num_ctx` 6144: cambiarla a ogni domanda faceva ricaricare il modello a Ollama; si allarga solo se il discorso è davvero lungo), e le istruzioni hanno la **parte fissa davanti** (carattere + strumenti) e quella che cambia (ora, ricordi, documenti) in fondo, così Ollama riusa il lavoro già fatto e la prima parola arriva prima. |
| 🔥 **Riscaldamento** | All'avvio (e quando cambi personalità) MAIK **scalda il modello in sottofondo**: quando fai la prima domanda è già pronto. Se il modello configurato non è installato, ne scelgo da solo uno che hai (e lo scrivo nel terminale). |
| 🐢➡️🐇 **Impara quando sei in pausa** | Le cose «pesanti» dopo la risposta (imparare fatti su di te, riassunti) aspettano che tu smetta di scrivere per qualche secondo: non rubano più il modello mentre mi fai la domanda dopo. |
| ⚡ **«quanto vai veloce?»** | Ti dico il modello, quanti **token al secondo** fa sul tuo PC, dopo quanto arriva la **prima parola**, se il riscaldamento è andato, e **consigli** concreti se va piano (un modello più piccolo, `MAIK_EMBED=0`…). Anche «perché sei così lento?», «le tue prestazioni». |
| 📊 **Pannello ⚡ Prestazioni e benessere** | Nella barra a sinistra (e dalla palette): 4 riquadri — 🧠 Cervello (token/s), ⏱️ Prima parola, 🤖 Zep (fotogrammi al secondo e risoluzione), 📷 Webcam (quanto costa ogni controllo). Opzioni: **🪶 modalità leggera**, qualità automatica di Zep, avvisi di benessere, «ti ricordo la pausa dopo N minuti di fila». |
| 🤖 **Zep più leggero** | La **risoluzione si adatta** a quanto ce la fa il tuo PC (scende se i fotogrammi calano, risale quando il PC respira), **30 fotogrammi al secondo quando è tranquillo** e 60 solo quando si muove/parla, e una **modalità leggera** per i PC più vecchi. Se il PC fatica davvero, te la propongo io. |
| 📷 **Webcam molto più leggera** | Il riconoscimento del viso lavora su un'immagine piccola (320 px) e **si regola da solo**: controlla più spesso se il PC è veloce, meno se è lento (da 130 a 450 ms); le mani una volta su tre. Niente più scatti quando accendi la webcam. |
| 📖 **«leggi quello che ti mostro»** | Avvicina un foglio, un biglietto, un'etichetta, uno scontrino alla webcam: conto alla rovescia 3… 2… 1…, scatto, e ti scrivo **cosa c'è scritto** in un riquadro, con **📋 Copia**, **🔊 Leggimelo** e **📚 Salva nei documenti**. Anche «leggi questo biglietto», «leggimi l'etichetta». |
| 🖐️ **«cosa ho in mano?»** | Mostra un oggetto: 3… 2… 1…, e il modello visione ti dice cos'è (anche «cosa ti sto mostrando?», «indovina cosa ho in mano»). |
| 🙂 **«come mi vedi?»** | Ti dico come ti vedo negli ultimi minuti: se sorridi, se sembri stanco o concentrato, se hai sbadigliato. Lo calcolo **sul tuo PC** dai movimenti del viso (niente foto mandate, niente modello). |
| 💚 **Quando ti vedo** | Con la webcam accesa: se **sbadigli** 2 volte in poco tempo ti propongo una pausa (e a volte sbadiglia anche Zep 😄); se sei **troppo vicino** allo schermo te lo dico; dopo **50 minuti di fila** (lo scegli tu) ti ricordo di alzarti e bere un bicchiere d'acqua, con il bottone **⏱️ Pausa di 5 minuti**. Gli avvisi non arrivano mentre sei in concentrazione, in riunione, mentre leggo o faccio da interprete. Si spengono nel pannello ⚡. |
| ⏱️ **«da quanto sono al pc?»** | Ti dico da quanto sei davanti al PC **di fila**, **oggi** e nella **settimana**. Al server arrivano solo i secondi in cui ti vedo, mai le immagini. |

- **Cosa non fa:** MAIK **non riconosce chi sei dal viso** (non identifica le persone) e i **comandi del PC restano quelli di prima**, sempre con la tua conferma.
- Se il PC è lento: un modello più piccolo (`MAIK_MODELLO=llama3.2:3b`), `MAIK_EMBED=0` (un modello in meno in memoria), la modalità leggera di Zep. Il pannello ⚡ ti dice dove sta il collo di bottiglia.
- Nuove variabili: `MAIK_KEEP_ALIVE` (default `30m`), `MAIK_KEEP_ALIVE_VISIONE` (`10m`), `MAIK_NUM_CTX` (`6144`; più alto = ricorda discorsi più lunghi ma usa più memoria), `MAIK_RISCALDA=0` (niente riscaldamento all'avvio), `MAIK_PAUSA_APPRENDIMENTO` (secondi di pausa prima di imparare dalle tue frasi, default `6`).
- Nuovi endpoint: `GET /prestazioni` · `GET /presenza` · `POST /presenza {secondi}`. `/chat/stream` restituisce anche `"prestazioni"`, `"presenza"` e `"webcam"` (cosa fare con la webcam: leggere, guardare o dirti come ti vedo).
- I dati: il tempo davanti al PC in `dati_maik/presenza.json` (solo i secondi per giorno).

## 🌀 Novità V21 — MAIK PRIME Multiverso: il consiglio delle altre dimensioni, il laboratorio delle invenzioni, gli aiutanti lampo (versione server)

Ispirata alle cose che fa uno scienziato pazzo dei cartoni (portali, invenzioni nel garage, versioni di sé da altri universi), ma con nomi e grafica tutti nostri.

| | Cosa fa |
|---|---|
| 🌀 **Il Consiglio del multiverso** | «**chiedi al multiverso: devo cambiare lavoro?**», «consiglio dei maik: meglio Roma o Milano?», «cosa ne pensano i maik di comprare un'auto elettrica»: Zep apre un **portale verde** e da 4 dimensioni arrivano 4 versioni di Maik, ognuna col suo carattere — 🧪 **Scienziato** (fatti e numeri), 🛡️ **Prudente** (i rischi), 🎨 **Visionario** (idee audaci), 🔧 **Pratico** (cosa fare domani). Le vedi comparire una alla volta (con il codice della dimensione, es. «dimensione S-978»), poi Maik scrive il **verdetto**: su cosa sono d'accordo, dove no, e il primo passo. Serve il modello (Ollama): ogni Maik è il modello che ragiona da un punto di vista diverso. |
| 🔬 **Il laboratorio delle invenzioni** | «**inventami un timer per il tè**», «**costruiscimi un generatore di password**», «**creami un gioco del tris**», «fammi un'app per dividere il conto», «laboratorio: un quiz sulle capitali»: Maik **scrive una piccola app vera** (un solo file HTML, con grafica e codice) e te la fa usare **subito dentro la chat**. Mentre la costruisce vedi «📐 Progetto… ⌨️ Scrivo il codice · 42 righe… 🧪 Collaudo» e Zep lavora alla tastiera, poi l'invenzione esce dal portale. Bottoni: **⛶ Apri in grande**, **🔧 Miglioralo** («migliora l'invenzione: aggiungi un suono»), **↩ Versione prima** (tengo le ultime 5), **&lt;/&gt; Codice**, **⬇ Scarica** (il file .html da tenere). Senza il modello ne so montare 6 **di serie**: ⏱️ timer, 🎲 dadi, 🔐 password, ⭕ tris, 🔁 convertitore di unità, 🔢 contatore. Tutte le invenzioni nella finestra **🔬 Laboratorio** (tasto **L**, o il bottone 🔬 in alto). |
| 🔒 **La gabbia** | Le invenzioni girano in una **gabbia di sicurezza** (iframe *sandbox* + *Content-Security-Policy* con origine opaca): non possono leggere i tuoi dati di MAIK né la pagina, non possono caricare script, immagini o dati da internet, non hanno cookie né localStorage e non possono usare i comandi del PC. Se un'invenzione prova ad aprire un'altra pagina dentro il suo riquadro, la rimetto subito a posto (e te lo dico). Le richieste che creano o cambiano invenzioni sono accettate solo dalla GUI di MAIK (non da altri siti aperti nel browser). |
| 🧪 **Gli aiutanti lampo** | «**chiama un aiutante per cercare un regalo per mia sorella**», «manda un aiutante a controllare quanto ho speso», oppure più insieme: «**aiutanti: quanto ho speso questo mese; cosa ho domani; cerca su internet le offerte dei voli per Parigi**». Ogni aiutante fa **un compito in sottofondo** (al massimo 3 insieme, gli altri in fila) mentre tu continui a parlare con me: sul palco compare la sua **bollicina** «🧪 #3 …» che gira finché lavora. Quando ha finito arriva il messaggio **🧪 AIUTANTE #3** con il risultato (con le schede: spese, fonti, notizie…), Zep fa 👍, e la bollicina sparisce con un *puf*. I risultati restano nella chat «🧪 Aiutanti». «i miei aiutanti» per vedere chi sta facendo cosa. Come le automazioni: **niente comandi del PC** e niente altri aiutanti dentro un aiutante. |
| 📺 **La TV del multiverso** | «**accendi la tv del multiverso**»: un vecchio televisore con 3 programmi assurdi che vanno in onda nelle altre dimensioni (li inventa il modello; senza modello ne ho 12 di scorta). ◀ ▶ per cambiare canale, 🔄 per altri canali. |
| 🧪 **Lo Scienziato** e il tema **Portale** | Una nuova personalità, **🧪 Scienziato**: geniale, veloce, un po' sarcastico ma affezionato, spiega con la scienza vera e propone soluzioni ingegnose (mai volgare). E un nuovo tema colori **Portale** (verde acido). |

- Il tasto **L** ora apre il laboratorio (mentre ti leggo una pagina resta pausa / riprendi). I suggerimenti sotto la chat stanno su 3 righe (il resto scorrendo), con le novità per prime, così i messaggi hanno più spazio.
- Di domenica «impegni di questa settimana» mostra anche la settimana che arriva.
- Nuovi endpoint: `GET /laboratorio` · `GET /laboratorio/app?id=` (l'app, con la gabbia; `&scarica=1` per salvarla) · `POST /laboratorio/crea {testo}` · `/laboratorio/migliora {id, testo}` · `/laboratorio/indietro {id}` · `/laboratorio/elimina {id}` · `GET /aiutanti` · `GET /aiutanti/avvisi` · `POST /aiutanti/chiama {compito}` · `GET /tv`. `/chat/stream` manda gli eventi `"multiverso"` e `"laboratorio"` e restituisce `"multiverso"`, `"invenzione"`, `"invenzioni"`, `"aiutanti"`, `"tv"`.
- I dati: `dati_maik/laboratorio.json` (le invenzioni, con le versioni); i risultati degli aiutanti nella chat «🧪 Aiutanti».

## 🏆 Novità V20 — MAIK PRIME pensa in grande: obiettivi con le tappe, la tua settimana, le tendenze del mese (versione server)

| | Cosa fa |
|---|---|
| 🎯 **Obiettivi con le tappe** | Dimmi un obiettivo con una scadenza: «**voglio imparare lo spagnolo entro giugno**», «**nuovo obiettivo: correre una mezza maratona in 4 mesi**», «il mio obiettivo è risparmiare 2000 euro entro dicembre», «leggere 12 libri entro fine anno», «finire la tesi entro il 15/3». MAIK lo divide in **3–6 tappe concrete** (le pensa il modello; senza modello usa tappe generiche), ognuna con la sua data, e mette **la prima nelle cose da fare** (con il progetto dell'obiettivo). Quando la spunti, passa da solo alla tappa dopo. «voglio una pizza per stasera» o «devo finire entro domani» **non** diventano obiettivi. |
| 🏆 **Il trofeo** | A ogni tappa fatta arriva il messaggio **🏆 Tappa 2 di 6 completata … Prossima: …**, con i coriandoli, la notifica e la voce, e **Zep alza una coppa d'oro** (anche il tuo personaggio VRM). All'ultima tappa: **🏆🎉 Obiettivo raggiunto!** Funziona sia che spunti la cosa da fare (dalla lista, dal centro di controllo, dalla chat), sia che dica «**ho finito la tappa dello spagnolo**». |
| 🎯 **Seguirli** | «**i miei obiettivi**», «**a che punto sono con lo spagnolo?**» (percentuale, tappe, giorni che mancano e il **ritmo**: 🚀 in anticipo, ✅ in linea, ⚠️ un po' indietro), «cancella l'obiettivo della maratona». Con **⚙️ Controllo ogni lunedì** MAIK crea un'automazione che ogni lunedì alle 9 ti dice a che punto sei. Ha anche ↩ Annulla. |
| 🗓️ **Il piano della settimana** | «**pianificami la settimana**» (o «organizza la mia settimana»): MAIK divide le cose da fare nei prossimi 7 giorni **attorno ai tuoi impegni del calendario**: quelle che scadono questa settimana (e quelle urgenti) il prima possibile, quelle senza fretta verso la fine, le altre dove c'è più spazio; il **weekend più leggero** e la pausa pranzo libera. Ogni giorno mostra le ore e una barra del carico. Se qualcosa non ci sta prima della scadenza te lo dice. **📌 Fissa i giorni** dà la data alle cose che non l'avevano, e da lì restano in quel giorno. |
| 📈 **Le tendenze** | «**come sto andando questo mese?**», «le mie tendenze», «i miei progressi»: i **5 numeri del mese** (spese con ▲▼ rispetto allo stesso periodo del mese scorso, abitudini fatte, cose fatte, pomodori, umore medio) e **quello che si nota** («hai speso il 40% in meno 👍», la voce più grossa, l'abitudine che tieni meglio e quella da rinforzare, il giorno più produttivo, l'umore in salita, gli obiettivi indietro). |
| 🛰️ **Centro di controllo a schede** | Il tasto **Y** ora ha 4 schede: **⚡ Oggi** (come prima, più il riquadro degli obiettivi), **🎯 Obiettivi** (crea, ✓ tappa fatta, controllo ogni lunedì, i 🏆 raggiunti), **🗓️ Settimana** e **📈 Tendenze** con i **grafici di 30 giorni**: spese al giorno, abitudini (%), pomodori, umore, e le spese per voce rispetto al mese scorso. Passa sopra con il mouse e vedi il valore di ogni giorno; c'è anche **la tabella con tutti i dati**. Se un grafico non ha ancora dati, te lo dice e ti spiega come riempirlo. |

- L'agente ha un nuovo strumento, `obiettivo_tappe`: se nella conversazione dici «mi piacerebbe imparare la chitarra entro marzo», lo può creare da solo.
- Nuovi endpoint: `GET /obiettivi[?tutti=1]` · `GET /obiettivi/avvisi` · `POST /obiettivi/crea {testo}` o `{titolo, scadenza}` · `POST /obiettivi/tappa {id}` · `POST /obiettivi/elimina {id}` · `GET /prime/settimana` · `POST /settimana/applica {assegna: [{id, data}]}` (solo per le cose senza data) · `GET /prime/tendenze?giorni=30` (7–90). `/attivita/fatta` dice anche se era una tappa. `/chat/stream` restituisce `"obiettivo"`, `"obiettivi"`, `"obiettivo_eventi"`, `"piano_settimana"` e `"tendenze"`.
- I dati: `dati_maik/obiettivi_prime.json`; le tappe sono normali cose da fare in `attivita.json`.

## ⚡ Novità V19 — MAIK PRIME: lavora da solo, fa ricerche approfondite, ti mostra tutta la giornata (versione server)

> **Nuovo nome:** il programma ora si chiama **MAIK PRIME** e il file è **`maikprime.py`** → `python maikprime.py`.
> I tuoi dati restano gli stessi (cartella `dati_maik/`). Il vecchio `maik_server.py` c'è ancora, ma solo come lanciatore: avvia `maikprime.py`.

| | Cosa fa |
|---|---|
| ⚙️ **Automazioni** | Dimmi cosa fare e quando, e MAIK lo fa **da solo**: «**ogni mattina alle 8 dimmi il meteo e le notizie**», «**ogni lunedì alle 9 dimmi quanto ho speso la settimana scorsa**», «**nei giorni feriali alle 7:30 cosa devo fare oggi?**», «**ogni sera alle 22 chiudiamo la giornata**», «ogni venerdì alle 18 com'è andata la settimana?», «nel weekend alle 10 …», «ogni lunedì e giovedì alle 18:30 …», «**ogni 2 ore ricordami di bere**». Può fare tutto quello che gli chiederesti in chat (spese, cose da fare, piano, notizie, meteo, ricerche, domande al modello…). Il risultato arriva come messaggio **⚙️ AUTOMAZIONE** (con le sue schede, la notifica e la voce) e resta nella chat **«⚙️ Automazioni»**. Zep si carica con l'**anello di energia** ⚡. |
| ⚙️ **Gestirle** | In chat: «le mie automazioni», «sospendi / riattiva / cancella / esegui l'automazione delle notizie». Oppure il tasto **X**: crea scrivendo come parli, accendi/sospendi, ▶ prova adesso, ✕ cancella, e gli ultimi risultati. Se il PC era spento all'ora giusta, MAIK non recupera la valanga di arretrati: aspetta la volta dopo. **Mai comandi del PC nelle automazioni**: quelli li confermi sempre tu. |
| 🔬 **Ricerca approfondita** | «**fai una ricerca approfondita sulle auto elettriche**», «ricerca approfondita: pannelli solari», «studia bene la storia di Roma», «fammi un rapporto sul mercato del lavoro»: MAIK prepara 3-4 ricerche diverse, legge le fonti su internet (senza doppioni) e scrive un **rapporto** con titolo, «in breve», sezioni, consigli e le **citazioni [1] [2]** cliccabili. Mentre lavora vedi **🔬 Ricerca 2 di 3 · «…»** e **✍️ Scrivo il rapporto**: Zep cerca con la lente e poi scrive sul blocco note. Il rapporto viene **salvato nei documenti** («📚 Ricerca — auto elettriche.md»), così dopo puoi chiedere «cosa diceva la ricerca sulle auto elettriche?». |
| 🛰️ **Centro di controllo** | Tasto **Y**, il bottone 🛰️ in alto, o in chat «**centro di controllo**», «**come sto andando oggi?**», «il mio punteggio»: tutta la giornata in un colpo d'occhio, con il **punteggio Prime** (0–100: cose fatte, abitudini, concentrazione), le cose di oggi da **spuntare**, le abitudini da **segnare con un tocco**, le spese (oggi, mese, budget), l'agenda di oggi e domani, i pomodori, l'**umore degli ultimi 7 giorni**, le prossime automazioni, idee, ricordi e promemoria. Si aggiorna da solo. |
| ⚡ **Zep Prime** | Nuovo gesto «**prime**»: si carica con i pugni stretti, un anello di energia gli sale dai piedi alla testa e alla fine alza le braccia al cielo. Lo fa quando finisce un'automazione o una ricerca. Va bene anche con il tuo personaggio VRM. |

- L'agente ha un nuovo strumento, `automazione`: se gli chiedi «ricordami ogni venerdì di …» o «tienimi aggiornato ogni mattina su …», la può creare da solo.
- Nuovi endpoint: `GET /automazioni` (con gli ultimi risultati) · `GET /automazioni/avvisi` · `POST /automazioni/crea {testo}` o `{comando, giorni, ora | ogni_min}` · `POST /automazioni/attiva {id, attiva}` · `POST /automazioni/esegui {id}` · `POST /automazioni/elimina {id}` · `GET /prime/oggi`. `/chat/stream` manda gli eventi `"ricerca"` (le fasi) e restituisce `"automazione"`, `"automazioni"`, `"prime"` e `"ricerca"`.
- I dati: `dati_maik/automazioni.json`; i rapporti delle ricerche nei documenti.

---

## 💡 Novità V18 — MAIK pensa avanti: ricorda le chiacchierate, ti propone idee, ragiona a più passi, legge le foto (versione server)

| | Cosa fa |
|---|---|
| 🧠 **Ricorda le chiacchierate** | «**ti ricordi cosa ti avevo detto su mio fratello?**», «cosa ti avevo detto ieri sul lavoro?», «ti ho mai parlato di Luca?», «cosa avevamo deciso per le vacanze?»: MAIK ritrova le chiacchierate giuste (anche di settimane fa, in qualsiasi chat) e ti risponde con le date. Sotto c'è la scheda dei ricordi con **💬 Riapri** per tornare a quella chat. Con `nomic-embed-text` le trova **per significato**: «il lavoro» trova «il mio capo mi ha promesso una promozione». |
| 🗓️ **Di cosa abbiamo parlato** | «**di cosa abbiamo parlato ieri?**», «cosa ci siamo detti la settimana scorsa?», «… lunedì», «… il 3 ottobre»: le chat di quel giorno con le domande principali e **💬 Riapri**. |
| 🧠 **Ricordi da solo** | Quando dici qualcosa che c'entra con una chiacchierata vecchia (in un'altra chat o di tanto tempo fa), MAIK se la ricorda e la usa («come mi avevi detto il 3 ottobre…»). Sotto la risposta compare il chip **🧠** con quel ricordo: un clic e riapri la chat. |
| 💡 **Idee proattive** | MAIK ti scrive lui quando serve, con i pulsanti per farlo subito: la sera, se una **serie di abitudini** sta per spezzarsi (✓ Fatto!); se **domani scade** qualcosa (🍅 Ci lavoro ora); se domattina hai un **impegno presto** (⏰ promemoria un'ora prima); se una **bolletta** scade entro 3 giorni (✓ Già pagata · ⏰ Ricordamelo domani); se di questo passo **sfori il budget** del mese (quanto puoi spendere al giorno); la mattina, se hai **cose in ritardo** (➡️ Sposta a domani); e se ti ha sentito giù per un paio di giorni, ti chiede come stai. Zep alza il dito e **gli si accende una lampadina** 💡. |
| 🔕 **Mai troppe** | Al massimo 4 al giorno, mai nelle **ore di silenzio** (22–8), e ogni idea una volta sola. «**basta consigli**» le spegne, «**riattiva i consigli**» le riaccende, **🔕 Non per questo** spegne solo quel tipo. «**hai qualche idea per me?**» te le dà subito, a qualsiasi ora. |
| 💡 **Idee e ricordi** | Tasto **U** o il bottone 💡 in alto: idee accese/spente, i 7 tipi di idea uno per uno, quante oggi, e la **ricerca nelle chiacchierate** (anche per significato) con 💬 Riapri. |
| 🤖 **Agente a più passi** | Per le domande difficili MAIK lavora in più giri: cerca, legge una fonte, fa i conti con i numeri trovati… e solo alla fine risponde. Mentre lavora vedi **🤖 Passo 2 di 4 · 🧮**, alla fine **🤖 3 passi** e i chip di ogni strumento. Nuovo strumento dell'agente: `cerca_chat` (le chiacchierate passate). |
| 📷 **Foto → testo** | Allega la **foto di uno scontrino o di una bolletta** e scrivi «**aggiungilo alle spese**» (o tocca **💶 alle spese** sull'allegato): MAIK legge la foto con il modello della visione, segna la spesa (e la scadenza della bolletta in calendario) e ti mostra il testo che ha letto. «**trascrivi il testo di questa foto**» (o **📝 testo**): il testo in un riquadro, con 📋 Copia e 📚 Salva nei documenti. Anche dalla finestra 💶 Spese («Da una bolletta o uno scontrino») ora vanno bene le foto. |
| 📄 **PDF scansionati** | Un PDF senza testo (una scansione) non è più un problema: la GUI lo legge **pagina per pagina** con il modello della visione (fino a 8 pagine), come allegato o nei documenti. |

- Per leggere le foto serve un modello della visione (`ollama pull llava`), lo stesso di 👁️ Guarda. Per i ricordi per significato `ollama pull nomic-embed-text` (senza, MAIK cerca per parole).
- Funziona **senza Ollama**: le idee, «di cosa abbiamo parlato ieri?» e i ricordi trovati (detti così come sono).
- Nuovi endpoint: `GET /proattivo` (le idee nuove) · `GET /proattivo/stato` · `POST /proattivo/azione {azione, dati}` · `POST /proattivo/imposta {attivo?, regola?, on?}` · `POST /proattivo/controlla` · `GET /ricordi?q=&quando=` · `GET /ricordi/giorno?q=ieri` · `POST /ocr {immagine, scopo?: "spesa", domanda?, nome?}`. `/chat/stream` manda anche gli eventi `"passo"` e restituisce `"idee"`, `"ricordi"`, `"ricordati"`, `"passi"`.
- Variabili: `MAIK_PROATTIVO=0` (niente idee) · `MAIK_PROATTIVO_MAX` (4 al giorno) · `MAIK_PROATTIVO_OGNI` (ogni quanti secondi guardare, 300) · `MAIK_SILENZIO` (ore di silenzio, `22-8`; `0` = mai) · `MAIK_SERA` (da che ora è «sera», 20) · `MAIK_AGENTE_PASSI` (giri massimi dell'agente, 4) · `MAIK_RICORDI_SOGLIA` (0.6). I dati restano in `dati_maik/proattivo.json` e `dati_maik/ricordi_vettori.json`.

---

## 🍅 Novità V17 — MAIK ti aiuta a fare le cose: cose da fare, concentrazione, il piano della giornata (versione server)

| | Cosa fa |
|---|---|
| 📋 **Cose da fare** | «**aggiungi alle cose da fare: chiamare il commercialista entro venerdì, urgente #lavoro**», «metti pagare il bollo oggi nelle cose da fare», «devo finire la relazione entro domani», più cose insieme separate da «;». MAIK capisce **scadenza** («oggi», «domani alle 15», «entro venerdì», «il 3 novembre», «12/1», «fine mese», «la prossima settimana»), **priorità** («urgente», «quando ho tempo»), **progetto** (#lavoro) e **durata** («(30 min)»). Poi: «**cosa devo fare oggi?**» (con gli impegni del calendario e le abitudini, quelle in ritardo per prime), «cosa devo fare domani?», «le mie cose da fare», «**fatto: commercialista**» (o «ho fatto la spesa»), «sposta la relazione a lunedì», «cancella l'attività …». |
| 📋 **La finestra** | Tasto **K** o il bottone 📋: **Oggi / Tutte / Fatte**, aggiungi scrivendo come parli, ✓ per spuntare, ▶ per concentrarti su quella, ✕ per eliminare. Anche in chat le cose da fare si spuntano con un clic. |
| 🍅 **Modalità concentrazione** | «**concentrazione 25 minuti sulla relazione**», «pomodoro», tasto **Q** o il bottone 🍅: un timer ad anello sul palco e **Zep si mette le cuffie e lavora al suo portatile** con te 🎧💻. Alla fine ti avvisa (suono, notifica, voce), si stiracchia e partono **5 minuti di pausa** (15 ogni 4 pomodori); poi «▶ Prossimo pomodoro». ⏸ per fermare il tempo, ✓ per chiudere prima, ⏹ per smettere. Il tempo che resta compare anche nel titolo della finestra. I pomodori vengono salvati e legati all'attività (🍅 accanto): «**quanti pomodori ho fatto oggi?**». |
| 🗓️ **Il piano della giornata** | «**pianificami la giornata**»: MAIK mette in fila gli impegni del calendario (fissi), le abitudini con un orario, il pranzo, e negli spazi liberi le cose da fare (prima quelle in ritardo, in scadenza e urgenti), con le pause. Su ogni attività c'è **▶ Inizia** (parte il pomodoro). Quello che non ci sta te lo dice, con **➡️ Sposta a domani**. La sera prepara il piano di domani. |
| 🌙 **Chiudiamo la giornata** | «**chiudiamo la giornata**» / «com'è andata oggi?»: le cose fatte, i pomodori, le abitudini, le spese di oggi, cosa resta (con **➡️ Sposta a domani**) e gli impegni di domani. |
| 📝 **Dalle riunioni** | Nelle cose da fare di una riunione c'è anche **📋 In lista**: va tra le tue cose da fare, con chi e quando. |

- Il **briefing** del mattino dice cosa c'è da fare oggi (e quante cose sono in ritardo); il riepilogo della **settimana** conta anche le cose fatte e i pomodori.
- Funziona tutto **senza Ollama** (il piano e la chiusura della giornata sono fatti da MAIK con le sue regole). L'agente ha due strumenti nuovi: `aggiungi_attivita` e `attivita`.
- Nuovi endpoint: `GET /attivita?filtro=oggi|domani|settimana|ritardo|tutte|fatte` · `POST /attivita/aggiungi {testo, quando?}` · `POST /attivita/fatta {id, fatta}` · `POST /attivita/modifica` · `POST /attivita/rimanda {ids, a}` · `POST /attivita/elimina {id}` · `POST /attivita/trova {testo}` · `GET /focus` · `POST /focus/sessione {minuti, attivita, testo, completa}` · `GET /piano` · `GET /giornata`. `/chat/stream` restituisce anche `"attivita"`, `"attivita_lista"`, `"piano"`, `"giornata"` e `"focus"`.
- Variabili: `MAIK_GIORNATA` (la tua giornata per il piano, es. `8-18`; di default `9-19`). I dati restano in `dati_maik/attivita.json`.
- La barra dei bottoni sul palco ora sta su due righe: le scorciatoie da tastiera si aprono con **?** o dalla palette (Ctrl+K).

---

## 🗂️ Novità V16 — MAIK ti organizza la vita: spese, abitudini, la tua settimana (versione server)

| | Cosa fa |
|---|---|
| 💶 **Spese** | Basta dirlo: «**ho speso 23,50 € di benzina**», «spesi 40 euro al supermercato», «ho pagato la bolletta della luce 87,40», «ieri ho speso 18 euro di pizza». MAIK capisce importo, cosa e quando, e mette la spesa nella **categoria giusta** (🛒 spesa, 🚗 trasporti, 💡 bollette, 🍕 mangiare fuori, 💊 salute…). Le domande: «**quanto ho speso questo mese?**», «quanto ho speso di benzina?», «… in bollette», «il mese scorso», «a settembre», «oggi», con il confronto con il periodo prima. Zep fa il conto con la sua **calcolatrice** 🧮 e sul display c'è il totale. Ogni spesa ha il suo **↩ Annulla**. |
| 🎯 **Budget** | «**imposta il budget a 800 euro**» (o «budget trasporti 150 euro» per una categoria): MAIK ti avvisa all'**80%** ⚠️ e quando lo **superi** 🚨, e ti dice quanto ti resta al giorno fino a fine mese. Il budget compare anche nel briefing del mattino. |
| 💡 **Bollette e scontrini** | Allega una bolletta in PDF (o Word) e dimmi «**aggiungila alle spese**», oppure premi **💶 alle spese** sull'allegato: MAIK trova **importo** e **scadenza** («entro il 15 novembre 2026», «Scadenza: 05/12/2026») e mette la scadenza **in calendario**, quindi quel giorno ti avvisa. Funziona anche con gli scontrini («aggiungi questo scontrino alle spese»). |
| 💶 **La finestra delle spese** | Tasto **D** o il bottone 💶: il mese con i suoi totali, la barra del budget, le categorie, le spese giorno per giorno, l'elenco (con ✕), il modulo per una spesa nuova e il bottone **📄 Da una bolletta o uno scontrino**. |
| ✅ **Abitudini** | «**nuova abitudine: bere 8 bicchieri d'acqua al giorno**», «palestra lun mer ven alle 19», «voglio leggere ogni sera alle 22», «andare a correre 3 volte a settimana». Poi «**ho fatto palestra**», «ho bevuto 2 bicchieri», «ho letto»: MAIK segna e conta i **giorni di fila** 🔥, con il record (i giorni di riposo non spezzano la serie). Ai **traguardi** (3, 7, 14, 30… giorni) Zep festeggia con i **coriandoli** 🎉. Se hai messo un orario e non l'hai ancora fatta, te lo **ricorda** con un bottone «✓ Fatto!». Tasto **O** per la finestra con i 7 giorni, i bottoni +/− e il modulo. |
| 📊 **La tua settimana** | «**com'è andata la settimana?**» (o tasto **W**): spese con il confronto, abitudini (percentuale e serie), impegni fatti e in arrivo, riunioni, documenti, umore. C'è anche **🔊 Leggimela**. Il lunedì te lo ricorda il briefing. |
| 🧠 **Ricerca per significato** | Nei 📚 documenti MAIK ora cerca anche **per significato**: chiedi «dove ho lasciato la macchina?» e trova «la mia auto è in garage», anche senza parole in comune. Usa gli embedding di Ollama: `ollama pull nomic-embed-text` (una volta). Senza quel modello la ricerca per parole funziona come prima, e la finestra dei documenti ti dice come attivarla. |
| 📖 **Letture in altre lingue** | «leggimi questo articolo https://…» su una pagina **in inglese, spagnolo, francese o tedesco**: Zep la legge con una **voce di quella lingua**, se ce n'è una installata sul PC (sennò con quella italiana). Nel riquadro della lettura compare la bandierina. |

- **Senza Ollama** funzionano lo stesso spese, budget, bollette (importo e scadenza li legge MAIK da sé), abitudini e riepilogo della settimana. Ollama serve solo per le bollette scritte in modo strano e per la ricerca per significato.
- **Privacy**: tutto resta sul tuo PC, in `dati_maik/spese.json`, `abitudini.json` e `vettori.json`.
- Nuovi endpoint: `GET /spese?mese=AAAA-MM` · `POST /spese/aggiungi {importo, descrizione, categoria?, data?}` · `POST /spese/elimina {id}` · `POST /spese/budget {importo, categoria?}` · `POST /spese/documento {testo, nome, scontrino?}` · `GET /abitudini` · `POST /abitudini/crea {testo}` o `{nome, emoji, giorni, ora, obiettivo, settimanale}` · `POST /abitudini/segna {id, n, data?}` · `POST /abitudini/elimina {id}` · `GET /abitudini/avvisi` · `GET /settimana`. `GET /documenti` dice anche lo stato della ricerca per significato (`"semantica"`). `/chat/stream` restituisce anche `"spesa"`, `"spese"`, `"budget"`, `"abitudine"`, `"abitudini"` e `"settimana"`. Nuovi strumenti dell'agente: `aggiungi_spesa`, `spese`, `abitudini`.
- Variabili: `MAIK_EMBED=0` (spegne la ricerca per significato) · `MAIK_MODELLO_EMBED` (`nomic-embed-text`) · `MAIK_EMBED_SOGLIA` (0.62: più alta = più severa).

---

## 📖 Novità V15 — MAIK legge tutto: PDF, Word, link, il tuo calendario, e ti fa da interprete (versione server)

| | Cosa fa |
|---|---|
| 📄 **PDF e Word** | Trascina un **PDF**, un **Word** (.docx) o un file **OpenOffice** (.odt) nei **📚 documenti** o come **📎 allegato**, poi chiedi «quanto devo pagare?», «riassumimi il contratto». I PDF li legge **pdf.js** nel browser; se non c'è (offline) o per Word/OpenOffice c'è il **lettore del server**, in puro Python (anche PDF compressi, con accenti ed €, più pagine). Un PDF **scansionato** (solo immagini) o **protetto da password** te lo dice. |
| 🔗 **Link** | «**riassumi questa pagina** https://…», «di cosa parla https://…», o mandi **solo il link**: MAIK apre la pagina (anche un **PDF online**) e risponde citandola **[1]**. Mentre la legge, Zep prende il **tablet** 📱. Se la pagina è privata o non si apre, te lo dice e ti suggerisce «riassumi quello che ho copiato». |
| 📖 **Lettura a voce** | «**leggimi questo articolo** https://…» oppure il bottone **📖** accanto a ogni fonte web: Zep legge **dal tablet**, frase per frase, con il riquadro che mostra titolo, frase e avanzamento. Puoi dire o scrivere «**pausa**», «**continua**», «**salta**», «**indietro**», «**ripeti**», «**basta**», o usare ⏸ ⏭ ⏮ e il tasto **L**. Se fai un'altra domanda o arriva un avviso, la lettura **va in pausa** e riparte dalla stessa frase. |
| 📅 **Calendario** | Tasto **E** o il bottone 📅: la **settimana**, ⬆️ **importa il file .ics** di **Google Calendar**, **Outlook** o **iPhone** (ricorrenze, eccezioni, fusi orari, eventi di tutto il giorno; reimportarlo **aggiorna** gli eventi, niente doppioni), ＋ nuovo impegno, ✕ elimina. In chat: «**cosa ho domani?**», «impegni di questa settimana», «agenda», «**aggiungi al calendario** cena da Marco venerdì alle 20 in via Roma» (con **↩ Annulla**), «cancella dal calendario palestra». Ti **avvisa 15 minuti prima** (messaggio, voce, notifica) e il **briefing** del mattino dice gli impegni del giorno. Anche l'agente lo usa da solo. |
| 🗣️ **Interprete** | Tasto **T**, il bottone 🗣️ o «**fammi da interprete in inglese**» (spagnolo, francese, tedesco, portoghese, rumeno, albanese, polacco, ucraino, russo, arabo, cinese, giapponese): premi **🎤 Parlo io** e parli italiano, Zep lo ripete **nell'altra lingua con una voce di quella lingua**; premi **🎤 English** quando risponde l'altra persona e te lo dice in italiano. Con «**a turno**» ascolta da solo una volta per uno. Puoi anche scrivere. Quando chiudi («basta interprete») la conversazione tradotta resta in chat. |

- **Cosa serve**: per tradurre e riassumere serve Ollama acceso (senza Ollama il link mostra comunque l'inizio della pagina, e calendario, PDF e lettura a voce funzionano lo stesso). Per l'interprete a voce serve **Chrome o Edge** e, per ogni lingua, una **voce installata** sul PC (Windows: Impostazioni → Ora e lingua → Voce); se manca, la traduzione resta scritta.
- **Sicurezza**: i link si aprono solo verso indirizzi **pubblici** (mai la rete di casa), come per la ricerca web. I file Word/OpenOffice con DOCTYPE/ENTITY («bombe» XML) vengono rifiutati. Il calendario resta sul tuo PC in `dati_maik/calendario.json`.
- Nuovi endpoint: `POST /documenti/file` e `POST /documenti/estrai` (file grezzo, header `X-Nome`, fino a 25 MB) · `GET /calendario?da=AAAA-MM-GG&giorni=7` · `GET /calendario/avvisi` · `POST /calendario/importa` (file .ics grezzo) · `POST /calendario/evento {titolo, inizio | quando, durata?, luogo?, tutto_giorno?}` · `POST /calendario/elimina {id}` · `POST /traduci {testo, da, a}` · `POST /pagina {url}`. `/chat/stream` restituisce anche `"pagina"`, `"agenda"` ed `"evento"`. Nuovi strumenti dell'agente: `leggi_pagina`, `calendario`, `aggiungi_evento`.
- Variabili: `MAIK_CAL_AVVISO` (minuti di anticipo degli avvisi, 15). pdf.js (4.10.38) viene scaricato una volta dal CDN e poi resta in locale, come Three.js.

---

## 🌍 Novità V14 — MAIK legge internet, le notizie e ti fa da segretario (versione server)

| | Cosa fa |
|---|---|
| 🌍 **Ricerca su internet con le fonti** | «**cerca su internet chi ha vinto il Giro d'Italia**», «cerca online il prezzo della PS5»: MAIK cerca (DuckDuckGo, poi Bing, poi Wikipedia — **senza chiavi né account**), **legge le pagine** (solo il testo utile, le parti che c'entrano con la domanda) e risponde citando le fonti **[1] [2]**: i numeri e le fonti sotto la risposta sono **link cliccabili**. Anche **da solo**, quando gli chiedi fatti recenti, prezzi, risultati o cose che non sa con certezza. Mentre legge, Zep prende la **lente d'ingrandimento** 🔍. |
| 📰 **Notizie** | «**notizie**», «**ultime notizie di sport**», «notizie di tecnologia / economia / mondo…», «cosa succede nel mondo»: i titoli ANSA con l'ora, clic per l'articolo, 🌍 per approfondire, 🔊 per sentirli. Tre titoli anche nel **briefing** del mattino. |
| 📝 **Modalità riunione** | Tasto **N**, il bottone 📝 o «**modalità riunione**»: Zep prende il **blocco note** e ascolta, la **trascrizione** compare dal vivo (pausa, note scritte a mano). Alla fine (✓ o «fine riunione») ti dà **riassunto, punti chiave, decisioni e cose da fare** con chi e quando, e per ogni cosa un **⏰ Ricordamelo**. La riunione finisce nei **📚 documenti**: dopo puoi chiedere «cosa abbiamo deciso alla riunione sul sito?». Le riunioni lunghe le riassume a pezzi; se chiudi la pagina a metà, la **bozza** non si perde. Durante la riunione Zep **non parla** (finirebbe negli appunti). |
| 📋 **Quello che hai copiato** | «**riassumi quello che ho copiato**», «**traduci in inglese** quello che ho copiato», «correggi quello che ho copiato»: legge gli appunti del PC (il browser ti chiede il permesso la prima volta) e lavora sul testo. |

- **Sicurezza**: MAIK legge solo indirizzi **pubblici** http(s) — mai la rete di casa o il PC stesso, nemmeno dopo un redirect. I feed con DOCTYPE/ENTITY vengono rifiutati. `MAIK_WEB=0` spegne internet del tutto. Le domande vanno a DuckDuckGo/Bing/Wikipedia come se le cercassi tu.
- **Senza Ollama** la ricerca mostra comunque i risultati con gli estratti, e la riunione ha un riassunto «a regole» (prime frasi, decisioni, compiti con chi e quando).
- Con prompt lunghi (fonti web, trascrizioni) MAIK chiede a Ollama **più contesto** in automatico, così non perde l'inizio della domanda.
- Nuovi endpoint: `GET /notizie?cat=sport` · `POST /riunione {testo, durata, titolo?}` · `POST /promemoria/aggiungi {testo, quando?}`. `/chat/stream` restituisce anche `"fonti_web"` e `"notizie"`, e durante la ricerca manda `{"lavoro": …}`. Nuovi strumenti dell'agente: `cerca_internet`, `notizie`.
- Variabili: `MAIK_WEB=0` · `MAIK_WEB_MOTORI` (es. `duckduckgo,wikipedia`) · `MAIK_WEB_CAR_FONTE` (testo per fonte, 2500) · `MAIK_NOTIZIE_URL` · `MAIK_WEB_DDG_URL` / `_BING_URL` / `_WIKI_URL`.

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
Si usa con `maikprime.py` su un **PC** (Chrome o Edge, schermo largo). Su telefono e su schermi piccoli resta la sfera di sempre,
e `index.html` rimane la versione V10 che funziona ovunque.

```bash
python maikprime.py            # si apre come finestra-app (Chrome/Edge), non come una scheda
python maikprime.py --no-app   # oppure in una scheda normale
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
| 📲 **App installabile** (server) | `maikprime.py` ora è una **PWA**: icona generata dal server (nucleo + M), manifest, service worker. In Chrome/Edge: **📲 Installa MAIK come app** nella barra laterale (o dal menu del browser) → si apre in una finestra sua, come un programma. |
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

## MAIK PRIME — Server V23 — `maikprime.py`

Server in **puro Python (solo libreria standard, niente pip; Piper per la voce neurale è facoltativo)** con memoria avanzata salvata su disco. Serve la GUI nel browser e fa da ponte verso Ollama.

```bash
ollama pull llama3.1      # una volta
python maikprime.py     # si apre da solo nel browser su :8137
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
MAIK_MODELLO=llama3.2 MAIK_PORTA=9000 python maikprime.py
MAIK_APPRENDIMENTO_IA=0 python maikprime.py     # spegne l'apprendimento con l'IA
MAIK_AGENTE=0 python maikprime.py               # spegne gli strumenti dell'agente
MAIK_SEGUITI_RITARDO=30 python maikprime.py     # demo: chiede «com'è andata?» dopo 30 secondi
MAIK_KEEP_ALIVE=2h MAIK_NUM_CTX=8192 python maikprime.py   # V22: modello pronto per 2 ore, memoria di lavoro più grande
MAIK_BACKUP_GIORNI=30 python maikprime.py     # V23: tengo un mese di copie di sicurezza automatiche
```

> 📲 Per installarlo sul **telefono** come app serve HTTPS (i browser lo chiedono per i service worker); sul computer
> con `localhost` funziona subito. Per usarlo dal telefono in casa: `MAIK_HOST=0.0.0.0 python maikprime.py`
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
