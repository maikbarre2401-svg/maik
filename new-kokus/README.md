# New Kokus — Sito Web 🌴

Sito web del ristorante **New Kokus** (Cucina Latinoamericana, Roma): città 3D al neon, percorso 3D "Come arrivare", menù, prenotazioni via WhatsApp.

## Com'è fatto

- `index.html` — la porta d'ingresso (apre il sito)
- `New_Kokus.dc.html` — la pagina del sito
- `support.js` — il motore che fa funzionare la pagina
- `vendor/` — la libreria grafica (React), inclusa: il sito non dipende da server esterni
- `fonts/` — i caratteri del marchio (Bricolage Grotesque, Manrope, Caveat), inclusi
- `assets/` — immagini e icone

Tutto è dentro la cartella: il sito si apre anche **con doppio clic senza internet** (solo le mappe Google richiedono la connessione).

## Cosa c'è nel sito

**Effetti 3D**
- Volo 3D nella città di notte all'apertura, con insegna al neon, palme e lucciole
- Parallasse col mouse (e col giroscopio sui telefoni Android)
- Card che si inclinano in 3D al passaggio del mouse, sezioni che entrano con una rotazione 3D
- Percorso 3D "Come arrivare" a 9 tappe, attraverso portali al neon

**Funzioni professionali**
- **Schermata di caricamento** con il logo NK
- **Aperto ora / Chiuso**: il sito calcola da solo se il locale è aperto, sull'ora di Roma (orari: 12:00–15:30 e 18:30–23:30, martedì riposo)
- **Menù a schede**: Tutto, Entradas, Segundos, De la casa, Arepas, Dulces & Bebidas
- **Locali con Foto / Mappa**: la mappa Google si carica solo quando il cliente la chiede
- **Galleria** con ingrandimento a schermo intero: frecce, tasti ← → Esc, e scorrimento col dito sul telefono
- **Prenotazione**: campi obbligatori controllati, data minima oggi, campo note (allergie, compleanni…), il messaggio arriva pronto su WhatsApp
- **Sul telefono**: menù a tutto schermo e barra in basso con Chiama · WhatsApp · Arrivare · Prenota
- **Sul computer**: il menù in alto evidenzia la sezione in cui ti trovi
- Modalità leggera automatica sui telefoni (niente lag) e animazioni in pausa quando non sono sullo schermo

## Gestione del menù (piatti e prezzi) ✎

Il pulsante di modifica è **nascosto ai clienti**. Per vederlo apri il sito aggiungendo `?admin` alla fine dell'indirizzo, per esempio:

`https://newkokus.netlify.app/New_Kokus.dc.html?admin`

⚠️ Le modifiche fatte così si salvano **solo sul dispositivo dove le fai** (i clienti non le vedono). Per cambiare il menù per tutti bisogna modificare i piatti nel file `New_Kokus.dc.html` (cerca `defaultMenu`) e ripubblicare.

## Partita IVA

In Italia il sito di un'attività deve mostrare la Partita IVA. Nel file `New_Kokus.dc.html` cerca `partitaIva` e scrivila al posto delle virgolette vuote dopo `default`:
`&quot;default&quot;: &quot;01234567890&quot;` → apparirà da sola in fondo alla pagina.

## Le tue foto 📸

Le immagini in `assets/` sono **illustrazioni disegnate** che fanno da segnaposto: il sito è già presentabile così, ma con le foto vere è molto meglio. Sostituiscile usando **gli stessi nomi file**:

| File | Cosa metterci |
|---|---|
| `storefront.png` | La vetrina del locale (verticale, ~480×854) |
| `storefront-night.png` | Il locale di sera |
| `interior.png` | La sala interna |
| `arepas.png` | Foto delle arepas |
| `desayunos.png` | I desayunos latinos |
| `terrazza.png` | La Terrazza del Kokus |
| `combo.png` | Il Combo 3 (verticale) |
| `menudia.png` | Il menù del día |

### Il percorso "Come arrivare" (9 foto, in quest'ordine)

| File | La tua foto |
|---|---|
| `percorso-1.png` | Metro A Cornelia / Circonvallazione Cornelia |
| `percorso-2.png` | Attraversamento al semaforo — Circonvallazione Cornelia 104 |
| `percorso-3.png` | Via di Boccea 114 — marciapiede Intersport/Cisalfa |
| `percorso-4.png` | Via di Boccea 139 — incrocio |
| `percorso-5.png` | Via Federico Galeotti 2 — inizio della via |
| `percorso-6.png` | Via Federico Galeotti 26 — prosegui dritto |
| `percorso-7.png` | Via Federico Galeotti 30 — angolo con Via G. Tamassia |
| `percorso-8.png` | Via Giovanni Tamassia 42 — quasi arrivato |
| `percorso-9.png` | Via Giovanni Tamassia 32 — la vetrina del New Kokus 2! |

Consiglio: meglio foto scattate da te col telefono lungo il percorso. Le schermate di Google Maps/Street View contengono immagini © Google che non andrebbero pubblicate sul proprio sito.

## Come metterlo ONLINE (gratis, 2 minuti) 🌐

Il modo più facile è **Netlify Drop** — non serve saper programmare:

1. Vai su **https://app.netlify.com/drop**
2. **Trascina l'intera cartella `new-kokus`** dentro la pagina
3. Fine! Ti dà subito un indirizzo tipo `https://nome-a-caso.netlify.app` da condividere su WhatsApp e Instagram
4. (Facoltativo) Registrandoti gratis puoi cambiare il nome, es. `newkokus.netlify.app`, o collegare un dominio tuo tipo `newkokus.it`

Alternative che funzionano uguale: **Vercel**, **GitHub Pages**, o qualsiasi hosting: basta caricare la cartella così com'è.

### Dopo la pubblicazione: anteprima su WhatsApp

Perché WhatsApp e Facebook mostrino l'immagine di anteprima quando condividi il link, nel file `New_Kokus.dc.html` cerca `og:image` e sostituisci `assets/og-image.png` con l'indirizzo completo, per esempio:
`https://newkokus.netlify.app/assets/og-image.png`

## SEO già incluso ✅

- Titolo e descrizione per Google
- Anteprima social (Open Graph) con immagine dedicata `assets/og-image.png`
- Scheda ristorante (dati strutturati schema.org) con indirizzi, telefono e orari dei due locali
- Favicon e icona per la schermata Home dell'iPhone

## Licenze

I caratteri in `fonts/` sono sotto licenza SIL Open Font License (`fonts/OFL-LICENSE.txt`); React in `vendor/` è sotto licenza MIT.
