#!/usr/bin/env python3
"""
OfflineGPS 3D v4.0 — Builder COMPLETO con NAVIGAZIONE OFFLINE (routing GraphHopper)
                      + SENTINELLA CIELO (rilevamento passivo droni)

STORICO:
 v2.5  Routing offline vero (GraphHopper sul telefono, profili auto/bici/piedi),
       DownloadActivity con tab MAPPE + ROUTING, NavigationActivity con ricalcolo.
 v2.6  GEOCODING OFFLINE: cerca la destinazione per NOME via/indirizzo
       (indice locale costruito dal .pbf), ricerca fuzzy, AddressSearchActivity.
 v2.7  Civici (addr:housenumber), tolleranza errori di battitura, filtro citta',
       anteprima su mappa, voce TTS italiana, frecce di manovra vettoriali,
       cronologia + preferiti, meteo a destinazione (Open-Meteo).
 v2.8  Stub javax.lang.model.SourceVersion (fix crash GraphHopper su Android),
       strumenti outdoor/SOS, crash-logger, firma v1+v2 (Samsung Knox).
 v2.9  Kit sopravvivenza completo (20+ strumenti), chat Bluetooth mesh,
       scheda emergenza, altimetro barometrico con avviso temporale,
       risparmio batteria estremo, tema futuristico neon.

NOVITA' v3.0 — GUI 3D AVANZATA + NUOVI STRUMENTI:
 * HOME RIDISEGNATA: schede "vetro" con bordo luminoso, pulsanti neon 3D
   (bombati, con ombra e luce), griglia 2 colonne, pulsante EMERGENZA rapido.
 * SPLASH 3D: anello neon che ruota attorno al logo mentre il logo gira
   sull'asse verticale (effetto ologramma).
 * 7 NUOVI STRUMENTI:
     - FASE LUNARE (calcolo offline: illuminazione %, prossima luna piena/nuova)
     - METAL DETECTOR (magnetometro in microtesla con taratura e beep)
     - VISIONE NOTTURNA (schermo rosso regolabile: non rovina l'occhio al buio)
     - TEMPERATURA PERCEPITA (wind chill + heat index con consigli)
     - PRIMO SOCCORSO (guida rapida offline: emorragie, ipotermia, RCP...)
     - TEMPI DI MARCIA (regola di Naismith: distanza+dislivello -> ore)
     - TACHIMETRO HUD (cifre giganti specchiate da riflettere sul parabrezza)
 * IMPORT MAPPA .map DAL FILE MANAGER: ora gestisce i content:// (prima
   falliva con quasi tutti i file manager moderni) copiando il file nell'app.
 * BUILDER MULTIPIATTAFORMA: funziona anche su Linux e macOS (genera sia
   gradlew.bat che gradlew), ricerca JDK/SDK cross-platform.
 * Opzione --solo-progetto (o --no-build): genera il progetto senza compilare.

NOVITA' v3.1 — RICERCA VIE E CIVICI COMPLETA (fix "me ne da' poche"):
 * Ogni via ora compare per OGNI citta' in cui esiste (prima "Via Roma"
   veniva indicizzata una sola volta per tutta la regione).
 * Civici letti anche dagli EDIFICI (way con addr:housenumber), non solo
   dai nodi: in Italia quasi tutti i civici sono sugli edifici, quindi
   prima se ne perdeva la maggior parte.
 * A ogni via viene assegnata la citta' piu' vicina (nodi place OSM):
   il filtro "via roma, milano" ora funziona davvero.
 * La ricerca capisce il numero nel testo: "via roma 10" trova la via
   e poi il civico 10 di QUELLA via (entro 4 km).
 * Indice V2: quelli vecchi vengono ricostruiti automaticamente al primo
   avvio della ricerca (nessuna azione manuale necessaria).

NOVITA' v4.0 (questa versione) — SENTINELLA CIELO + GRAFICA NUOVA:
 * SENTINELLA CIELO: rilevamento PASSIVO dei droni vicini.
     - Scanner REMOTE ID: riceve via Bluetooth (anche long range BT5) e
       Wi-Fi Beacon i messaggi che i droni UE trasmettono per legge
       (ASTM F3411 / EN 4709-002): numero di serie, posizione, quota,
       velocita', classe C0-C6, posizione del pilota, ID operatore.
     - Radar 3D: piano in prospettiva, fascio rotante, droni con stelo
       proporzionale alla quota, scia, rotta, vista 2D/3D, nord o rotta in alto.
     - Avvisi con vibrazione e voce ("drone a 300 metri, direzione nord-est").
     - Modalita' DEMO con 3 droni simulati (codificati e decodificati dallo
       stesso parser dei segnali veri).
 * ASCOLTO DRONI: riconosce il ronzio delle eliche col microfono (FFT,
   pettine armonico, persistenza e regolarita' su 2-3 s) con spettrogramma
   a cascata e indicatore neon. Tutto sul telefono, nessuna registrazione.
   Tarato su segnali sintetici: 0 falsi allarmi su voce, musica, sirene,
   vento, traffico e ronzio di rete nei test.
 * SEGNALA AVVISTAMENTO (SkySpot): diario locale con posizione ARROTONDATA
   a ~1 km, condivisione testo, pulsante 112 (non lo sostituisce).
 * E' DAVVERO UN DRONE?: 6 domande distinguono drone, aereo, elicottero,
   satellite, Starlink, Venere, lanterne, meteore. Guida "cosa fare" e
   consigli per verificare le notizie prima di condividerle.
 * Solo RILEVAMENTO: niente jamming ne' contromisure (vietati ai privati).
 * GRAFICA: home nuova con aurora animata e griglia 3D, radar vivo in
   evidenza, chip di stato, riquadri vetro con icone e ripple; transizioni
   animate fra schermate; pulsanti con effetto molla ed elementi che
   entrano in sequenza in TUTTA l'app; tema scuro coerente (anche i
   dialoghi); percorso sulla mappa con alone luminoso.
 * Rimosse le librerie VTM inutilizzate (APK piu' leggero, niente jitpack).
"""
import os, sys, shutil, subprocess, platform, urllib.request, time
from pathlib import Path

class C:
    OK="\033[92m"; WARN="\033[93m"; ERR="\033[91m"
    BOLD="\033[1m"; CYAN="\033[96m"; RESET="\033[0m"

def ok(m):   print(f"{C.OK}  [OK] {m}{C.RESET}")
def warn(m): print(f"{C.WARN}  [!] {m}{C.RESET}")
def err(m):  print(f"{C.ERR}  [X] {m}{C.RESET}")
def info(m): print(f"      {m}")
def title(m): print(f"\n{C.BOLD}{C.CYAN}{'-'*64}\n  {m}\n{'-'*64}{C.RESET}")
def step(n, total, m): print(f"{C.CYAN}  [{n}/{total}] {m}{C.RESET}")

DESKTOP     = Path.home() / "Desktop"
PROJECT_DIR = DESKTOP / "offlinegps_3d_v3"
PKG_ROOT    = "com/offlinegps/map"
PKG_MAP     = f"{PKG_ROOT}/map"
PKG_GPS     = f"{PKG_ROOT}/gps"
PKG_UI      = f"{PKG_ROOT}/ui"
PKG_DATA    = f"{PKG_ROOT}/data"
PKG_UTIL    = f"{PKG_ROOT}/util"
PKG_ROUTING = f"{PKG_ROOT}/routing"
PKG_SKY     = f"{PKG_ROOT}/sky"

BUILD_GRADLE_PROJECT = """
buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.3.2' }
}
task clean(type: Delete) { delete rootProject.buildDir }
"""

BUILD_GRADLE_APP = """
plugins { id 'com.android.application' }

android {
    namespace 'com.offlinegps.map'
    compileSdk 34

    defaultConfig {
        applicationId "com.offlinegps.map"
        minSdk 26
        targetSdk 34
        versionCode 47
        versionName "4.0.0"
        multiDexEnabled true
        ndk { abiFilters 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64' }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }

    buildFeatures { buildConfig true }

    signingConfigs {
        // Firma esplicita con v1 E v2 abilitate. Molti Samsung (Knox) rifiutano
        // o interrompono l'installazione se manca la firma v2; il Pixel e' piu'
        // permissivo. Riusiamo il keystore di debug standard di Android, ma
        // forziamo entrambe le firme cosi' l'APK si installa anche su Samsung.
        debugV2 {
            storeFile file("${System.properties['user.home']}/.android/debug.keystore")
            storePassword 'android'
            keyAlias 'androiddebugkey'
            keyPassword 'android'
            v1SigningEnabled true
            v2SigningEnabled true
        }
    }

    buildTypes {
        debug   {
            minifyEnabled false
            debuggable true
            signingConfig signingConfigs.debugV2
        }
        release {
            minifyEnabled true
            signingConfig signingConfigs.debugV2
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    lint { abortOnError false; checkReleaseBuilds false }

    packagingOptions {
        pickFirst 'lib/armeabi-v7a/libc++_shared.so'
        pickFirst 'lib/arm64-v8a/libc++_shared.so'
        pickFirst 'lib/x86/libc++_shared.so'
        pickFirst 'lib/x86_64/libc++_shared.so'
        exclude 'META-INF/DEPENDENCIES'
        exclude 'META-INF/LICENSE'
        exclude 'META-INF/NOTICE'
        exclude 'META-INF/*.kotlin_module'
        resources {
            pickFirsts += ['assets/**']
            excludes += ['META-INF/versions/**', 'META-INF/services/**.txt',
                         'META-INF/*.SF', 'META-INF/*.DSA', 'META-INF/*.RSA',
                         'META-INF/LICENSE.md', 'META-INF/LICENSE*.txt',
                         'META-INF/NOTICE.md', 'META-INF/NOTICE*.txt',
                         'META-INF/DEPENDENCIES', 'META-INF/INDEX.LIST',
                         '**/*.proto', 'google/protobuf/**',
                         'module-info.class', 'META-INF/versions/*/module-info.class']
        }
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.7.0'
    implementation 'androidx.multidex:multidex:2.0.1'
    implementation 'com.google.android.material:material:1.12.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    implementation 'androidx.cardview:cardview:1.0.0'
    implementation 'androidx.preference:preference:1.2.1'
    implementation 'androidx.recyclerview:recyclerview:1.3.2'

    def lifecycle_version = "2.7.0"
    implementation "androidx.lifecycle:lifecycle-viewmodel:$lifecycle_version"
    implementation "androidx.lifecycle:lifecycle-livedata:$lifecycle_version"
    implementation "androidx.lifecycle:lifecycle-runtime:$lifecycle_version"

    implementation 'org.mapsforge:mapsforge-core:0.21.0'
    implementation 'org.mapsforge:mapsforge-map:0.21.0'
    implementation 'org.mapsforge:mapsforge-map-reader:0.21.0'
    implementation 'org.mapsforge:mapsforge-map-android:0.21.0'
    implementation 'org.mapsforge:mapsforge-themes:0.21.0'

    // v5.0: VTM = mappa 3D VERA in OpenGL (inclinazione, rotazione, edifici 3D).
    // Da Maven Central (gruppo org.mapsforge): niente jitpack. Le librerie
    // native per ogni processore stanno nei pacchetti "natives-*".
    def vtm_version = "0.25.0"
    implementation "org.mapsforge:vtm:${vtm_version}"
    implementation "org.mapsforge:vtm-themes:${vtm_version}"
    implementation "org.mapsforge:vtm-android:${vtm_version}"
    implementation "org.mapsforge:vtm-android:${vtm_version}:natives-armeabi-v7a"
    implementation "org.mapsforge:vtm-android:${vtm_version}:natives-arm64-v8a"
    implementation "org.mapsforge:vtm-android:${vtm_version}:natives-x86"
    implementation "org.mapsforge:vtm-android:${vtm_version}:natives-x86_64"
    implementation 'com.caverock:androidsvg:1.4'

    def room_version = "2.6.1"
    implementation "androidx.room:room-runtime:$room_version"
    annotationProcessor "androidx.room:room-compiler:$room_version"

    implementation 'com.squareup.okhttp3:okhttp:4.12.0'
    implementation 'androidx.work:work-runtime:2.9.0'

    implementation 'com.google.android.gms:play-services-location:21.3.0'

    // --- Routing offline (navigazione stile Google Maps) ---
    // GraphHopper 6.2: ultima linea che supporta il weighting classico
    // "fastest" via setVehicle/setWeighting, SENZA compilazione Janino a
    // runtime (Janino non funziona su Android: vedi janino issue #191).
    def graphhopper_version = "6.2"
    implementation "com.graphhopper:graphhopper-core:${graphhopper_version}"
    // IMPORTANTE: GraphHopper esclude protobuf-java su Android, ma SENZA di
    // essa la lettura dei file .pbf fallisce con "Unable to read PBF file"
    // (NoClassDefFoundError com.google.protobuf). La aggiungiamo esplicitamente.
    implementation 'com.google.protobuf:protobuf-java:3.25.5'
    // GraphHopper OSMInputFile dichiara throws XMLStreamException (StAX), ma
    // Android non include StAX: aggiungiamo l'API StAX + un'implementazione
    // leggera (Aalto) cosi' il reader OSM compila ed e' usabile su Android.
    implementation 'javax.xml.stream:stax-api:1.0-2'
    implementation 'com.fasterxml:aalto-xml:1.3.2'
    implementation 'org.codehaus.janino:janino:3.1.12'
    implementation 'org.tukaani:xz:1.9'
}
"""

SETTINGS_GRADLE = """
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "OfflineGPS 3D"
include ':app'
"""

GRADLE_WRAPPER_PROPS = r"""distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.6-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""

PROGUARD_RULES = """
-keep class com.offlinegps.map.data.** { *; }
-keep class com.offlinegps.map.routing.** { *; }
-keep @androidx.room.Entity class * { *; }
-keep @androidx.room.Dao interface * { *; }
-keepclassmembers class * extends androidx.room.RoomDatabase { *; }
-keep class org.mapsforge.** { *; }
-keep class org.oscim.** { *; }
-keep class com.graphhopper.** { *; }
-keep class com.google.protobuf.** { *; }
-keep class org.openstreetmap.osmosis.** { *; }
-keep class crosby.binary.** { *; }
-dontwarn com.google.protobuf.**
-dontwarn org.openstreetmap.osmosis.**
-dontwarn org.mapsforge.**
-dontwarn org.oscim.**
-dontwarn org.slf4j.**
-dontwarn com.graphhopper.**
-dontwarn org.codehaus.janino.**
-dontwarn javax.xml.stream.**
-dontwarn com.fasterxml.aalto.**
-dontwarn javax.lang.model.**
-keep class javax.lang.model.** { *; }
-keepattributes *Annotation*
-keepattributes Signature
"""

MANIFEST = """\
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION"/>
    <uses-permission android:name="android.permission.VIBRATE"/>
    <uses-permission android:name="android.permission.WAKE_LOCK"/>
    <uses-permission android:name="android.permission.ACTIVITY_RECOGNITION"/>
    <!-- Chat offline via Bluetooth -->
    <uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30"/>
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30"/>
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT"/>
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN"/>
    <uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <!-- v4.0 Sentinella Cielo: ricezione PASSIVA Remote ID + ascolto eliche -->
    <uses-permission android:name="android.permission.RECORD_AUDIO"/>
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE"/>
    <uses-permission android:name="android.permission.NEARBY_WIFI_DEVICES"/>
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29"/>

    <uses-feature android:name="android.hardware.sensor.accelerometer" android:required="true"/>
    <uses-feature android:name="android.hardware.sensor.compass" android:required="false"/>
    <uses-feature android:name="android.hardware.location.gps" android:required="true"/>
    <uses-feature android:name="android.hardware.bluetooth_le" android:required="false"/>
    <uses-feature android:name="android.hardware.microphone" android:required="false"/>
    <uses-feature android:name="android.hardware.wifi" android:required="false"/>

    <application
        android:name=".OfflineGpsApp"
        android:allowBackup="true"
        android:icon="@drawable/ic_gps"
        android:label="OfflineGPS 3D"
        android:roundIcon="@drawable/ic_gps"
        android:supportsRtl="true"
        android:theme="@style/Theme.OfflineGPS"
        android:hardwareAccelerated="true"
        android:largeHeap="true"
        android:enableOnBackInvokedCallback="true"
        android:usesCleartextTraffic="true">

        <activity android:name=".ui.SplashActivity" android:exported="true"
            android:screenOrientation="portrait" android:theme="@style/Theme.OfflineGPS.Fullscreen">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <activity android:name=".ui.MainActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.MapActivity" android:exported="false"
            android:screenOrientation="portrait" android:configChanges="orientation|screenSize"
            android:theme="@style/Theme.OfflineGPS.Fullscreen"/>
        <activity android:name=".ui.NavigationActivity" android:exported="false"
            android:screenOrientation="portrait" android:configChanges="orientation|screenSize"
            android:theme="@style/Theme.OfflineGPS.Fullscreen"/>
        <activity android:name=".ui.AddressSearchActivity" android:exported="false"
            android:screenOrientation="portrait" android:windowSoftInputMode="adjustResize"/>
        <activity android:name=".ui.DownloadActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.WaypointsActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.StatsActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.ToolsActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SurvivalActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.ProximityToolActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.CoordsToolActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.DaylightToolActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SignalMirrorActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.WhistleActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.BacktrackActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.AreaToolActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.TrackRecorderActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.UnitConvActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.MultiTimerActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SlopeToolActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.MorseActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SurvGuideActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.HydrationActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SunCompassActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.ChecklistActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.GeoNotesActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.GotoCoordsActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.FlashlightActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.CalcActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.NotepadActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.CurrencyActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.QrPositionActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.ChatActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.EmergencyActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.AltimeterActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.BatterySaverActivity" android:exported="false" android:screenOrientation="portrait"/>
        <!-- NUOVI STRUMENTI v3.0 -->
        <activity android:name=".ui.MoonPhaseActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.MetalDetectorActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.NightVisionActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.HeatIndexActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.FirstAidActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.PaceCalcActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SpeedHudActivity" android:exported="false" android:screenOrientation="portrait"
            android:theme="@style/Theme.OfflineGPS.Fullscreen"/>
        <!-- v4.0 SENTINELLA CIELO -->
        <activity android:name=".ui.SkyWatchActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.AcousticDetectorActivity" android:exported="false" android:screenOrientation="portrait"/>
        <activity android:name=".ui.SkySpotActivity" android:exported="false" android:screenOrientation="portrait"
            android:windowSoftInputMode="adjustResize"/>
        <activity android:name=".ui.SightingCheckActivity" android:exported="false" android:screenOrientation="portrait"/>
        <!-- v5.0 MAPPA 3D (OpenGL) -->
        <activity android:name=".ui.Map3DActivity" android:exported="false"
            android:screenOrientation="portrait" android:configChanges="orientation|screenSize"
            android:theme="@style/Theme.OfflineGPS.Fullscreen"/>
        <service android:name=".gps.GpsTrackingService" android:exported="false"
            android:foregroundServiceType="location"/>
    </application>
</manifest>
"""

OFFLINE_GPS_APP = r"""package com.offlinegps.map;

import android.app.Application;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.os.Build;
import androidx.multidex.MultiDex;

public class OfflineGpsApp extends Application {
    public static final String CHANNEL_GPS = "gps_tracking_v2";

    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        MultiDex.install(this);
    }

    @Override
    public void onCreate() {
        super.onCreate();

        // Gestore globale dei crash: salva l'errore in un file leggibile
        // (Download -> VERIFICA FILE lo mostra) invece di chiudere e basta.
        final Thread.UncaughtExceptionHandler prev = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, ex) -> {
            try {
                java.io.File f = new java.io.File(getExternalFilesDir(null), "last_crash.txt");
                java.io.StringWriter sw = new java.io.StringWriter();
                ex.printStackTrace(new java.io.PrintWriter(sw));
                java.io.FileWriter fw = new java.io.FileWriter(f, false);
                fw.write("CRASH " + new java.util.Date().toString() + "\n\n");
                fw.write(sw.toString());
                fw.close();
            } catch (Throwable ignored) {}
            if (prev != null) prev.uncaughtException(thread, ex);
        });

        // IMPORTANTE: la graphic factory di Mapsforge va creata UNA SOLA VOLTA
        // per tutta l'app. Crearla in ogni Activity provoca un crash quando
        // si apre la seconda schermata con mappa. La creiamo qui.
        try {
            org.mapsforge.map.android.graphics.AndroidGraphicFactory.createInstance(this);
        } catch (Throwable ignored) {}

        // v4.0: effetto molla sui pulsanti + ingresso a cascata in tutte le schermate
        com.offlinegps.map.ui.UiFx.install(this);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                CHANNEL_GPS, "GPS Tracking", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("Tracciamento GPS attivo");
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(ch);
        }
    }
}
"""

APP_CONFIG = r"""package com.offlinegps.map;

public final class AppConfig {
    private AppConfig() {}
    public static final int COLOR_BG        = 0xFF050A14;
    public static final int COLOR_SURFACE   = 0xFF0D1421;
    public static final int COLOR_CARD      = 0xFF141E2E;
    public static final int COLOR_PRIMARY   = 0xFF00E5FF;
    public static final int COLOR_SECONDARY = 0xFF00FF88;
    public static final int COLOR_ACCENT    = 0xFFFF6B35;
    public static final int COLOR_WARN      = 0xFFFFD600;
    public static final int COLOR_DANGER    = 0xFFFF1744;
    public static final int COLOR_TEXT      = 0xFFE8F4FD;
    public static final int COLOR_TEXT_DIM  = 0xFF5A7A99;
    public static final int COLOR_TRACK     = 0xCC00FF88;
    public static final int GPS_MIN_TIME_MS = 1000;
    public static final float GPS_MIN_DIST_M = 1.0f;
    public static final double MAP_DEFAULT_LAT = 41.9028;
    public static final double MAP_DEFAULT_LON = 12.4964;
    public static final int MAP_DEFAULT_ZOOM = 15;
    public static final int NOTIF_ID_GPS = 1001;
    public static final String PREFS = "ogps_v2";
    public static final String PREF_LAST_LAT = "last_lat";
    public static final String PREF_LAST_LON = "last_lon";
    public static final String PREF_MAP_FILE = "map_file";
    public static final String PREF_FOLLOW   = "follow_gps";
    public static final String PREF_NIGHT    = "night_mode";
    public static final String PREF_TRACK_ON = "track_recording";
    public static final int REQ_GPS_PERM   = 200;
    public static final int REQ_NOTIF_PERM = 201;
    public static final int REQ_PICK_MAP   = 202;
}
"""

WAYPOINT_ENTITY = r"""package com.offlinegps.map.data;

import androidx.annotation.NonNull;
import androidx.room.*;

@Entity(tableName = "waypoints",
        indices = {@Index(value = "timestamp", orders = {Index.Order.DESC})})
public final class WaypointEntity {
    @PrimaryKey(autoGenerate = true) public long id;
    @NonNull @ColumnInfo(name = "name") public String name = "";
    @ColumnInfo(name = "latitude")  public double latitude  = 0.0;
    @ColumnInfo(name = "longitude") public double longitude = 0.0;
    @ColumnInfo(name = "altitude")  public double altitude  = 0.0;
    @ColumnInfo(name = "accuracy")  public float accuracy   = 0f;
    @ColumnInfo(name = "timestamp") public long timestamp   = 0L;
    @NonNull @ColumnInfo(name = "description") public String description = "";
    @NonNull @ColumnInfo(name = "color") public String color = "#00E5FF";

    @NonNull
    public static WaypointEntity create(String name, double lat, double lon, double alt,
            float acc, String color) {
        WaypointEntity w = new WaypointEntity();
        w.name = name; w.latitude = lat; w.longitude = lon;
        w.altitude = alt; w.accuracy = acc;
        w.timestamp = System.currentTimeMillis(); w.color = color;
        return w;
    }

    public double distanceTo(double lat2, double lon2) {
        final double R = 6371000.0;
        double dLat = Math.toRadians(lat2 - latitude);
        double dLon = Math.toRadians(lon2 - longitude);
        double a = Math.sin(dLat/2)*Math.sin(dLat/2)
            + Math.cos(Math.toRadians(latitude))*Math.cos(Math.toRadians(lat2))
            * Math.sin(dLon/2)*Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    public String formatDistance(double meters) {
        if (meters < 1000) return String.format("%.0f m", meters);
        return String.format("%.2f km", meters / 1000.0);
    }
}
"""

WAYPOINT_DAO = r"""package com.offlinegps.map.data;

import androidx.lifecycle.LiveData;
import androidx.room.*;
import java.util.List;

@Dao
public interface WaypointDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE) long insert(WaypointEntity w);
    @Update void update(WaypointEntity w);
    @Delete void delete(WaypointEntity w);
    @Query("SELECT * FROM waypoints ORDER BY timestamp DESC")
    LiveData<List<WaypointEntity>> getAllLive();
    @Query("SELECT * FROM waypoints ORDER BY timestamp DESC")
    List<WaypointEntity> getAllSync();
    @Query("DELETE FROM waypoints WHERE id = :id") void deleteById(long id);
    @Query("SELECT COUNT(*) FROM waypoints") int count();
}
"""

TRACK_POINT_ENTITY = r"""package com.offlinegps.map.data;

import androidx.room.*;

@Entity(tableName = "track_points",
        indices = {@Index(value = "session_id"), @Index(value = "timestamp")})
public final class TrackPointEntity {
    @PrimaryKey(autoGenerate = true) public long id;
    @ColumnInfo(name = "session_id") public long sessionId = 0L;
    @ColumnInfo(name = "latitude")  public double latitude  = 0.0;
    @ColumnInfo(name = "longitude") public double longitude = 0.0;
    @ColumnInfo(name = "altitude")  public double altitude  = 0.0;
    @ColumnInfo(name = "speed_ms")  public float speedMs = 0f;
    @ColumnInfo(name = "bearing")   public float bearing = 0f;
    @ColumnInfo(name = "accuracy")  public float accuracy = 0f;
    @ColumnInfo(name = "timestamp") public long timestamp = 0L;
}
"""

TRACK_DAO = r"""package com.offlinegps.map.data;

import androidx.room.*;
import java.util.List;

@Dao
public interface TrackDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE) long insert(TrackPointEntity p);
    @Query("SELECT * FROM track_points WHERE session_id = :sid ORDER BY timestamp ASC")
    List<TrackPointEntity> getSessionSync(long sid);
    @Query("SELECT COUNT(*) FROM track_points WHERE session_id = :sid")
    int countSession(long sid);
    @Query("DELETE FROM track_points WHERE session_id = :sid") void deleteSession(long sid);
}
"""

GPS_DATABASE = r"""package com.offlinegps.map.data;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.room.*;

@Database(entities = {WaypointEntity.class, TrackPointEntity.class, HistoryEntity.class},
          version = 2, exportSchema = false)
public abstract class GpsDatabase extends RoomDatabase {
    public abstract WaypointDao waypointDao();
    public abstract TrackDao trackDao();
    public abstract HistoryDao historyDao();

    private static volatile GpsDatabase INSTANCE;

    @NonNull
    public static GpsDatabase getInstance(@NonNull Context ctx) {
        if (INSTANCE != null) return INSTANCE;
        synchronized (GpsDatabase.class) {
            if (INSTANCE != null) return INSTANCE;
            INSTANCE = Room.databaseBuilder(ctx.getApplicationContext(),
                GpsDatabase.class, "offlinegps_v2.db")
                .fallbackToDestructiveMigration().build();
            return INSTANCE;
        }
    }
}
"""

# ============================================================
#  CRONOLOGIA DESTINAZIONI + PREFERITI
# ============================================================
HISTORY_ENTITY = r"""package com.offlinegps.map.data;

import androidx.annotation.NonNull;
import androidx.room.*;

@Entity(tableName = "history")
public class HistoryEntity {
    @PrimaryKey(autoGenerate = true) public long id;
    @NonNull public String label = "";
    public double lat;
    public double lon;
    public long timestamp;
    public boolean favorite;

    public HistoryEntity() {}

    @Ignore
    public HistoryEntity(@NonNull String label, double lat, double lon, long timestamp) {
        this.label = label; this.lat = lat; this.lon = lon;
        this.timestamp = timestamp; this.favorite = false;
    }
}
"""

HISTORY_DAO = r"""package com.offlinegps.map.data;

import androidx.room.*;
import java.util.List;

@Dao
public interface HistoryDao {
    // Evita duplicati: se l'etichetta esiste, la sovrascriviamo con il timestamp nuovo
    @Query("DELETE FROM history WHERE label = :label AND favorite = 0")
    void deleteByLabel(String label);

    @Insert
    void insertRaw(HistoryEntity h);

    @Transaction
    default void insert(HistoryEntity h) {
        deleteByLabel(h.label);
        insertRaw(h);
        trim();
    }

    // Mantiene solo le ultime 30 voci non preferite
    @Query("DELETE FROM history WHERE favorite = 0 AND id NOT IN " +
           "(SELECT id FROM history WHERE favorite = 0 ORDER BY timestamp DESC LIMIT 30)")
    void trim();

    @Query("SELECT * FROM history ORDER BY favorite DESC, timestamp DESC")
    List<HistoryEntity> getAllSync();

    @Query("SELECT * FROM history WHERE favorite = 1 ORDER BY timestamp DESC")
    List<HistoryEntity> getFavoritesSync();

    @Update void update(HistoryEntity h);
    @Delete void delete(HistoryEntity h);
    @Query("DELETE FROM history WHERE favorite = 0") void clearHistory();
}
"""

GPS_SERVICE = r"""package com.offlinegps.map.gps;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.location.*;
import android.os.*;
import android.util.Log;
import androidx.annotation.*;
import androidx.core.app.*;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.location.LocationResult;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.location.Priority;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.OfflineGpsApp;
import com.offlinegps.map.R;
import com.offlinegps.map.data.*;
import com.offlinegps.map.ui.MapActivity;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class GpsTrackingService extends Service {
    private static final String TAG = "GpsService";
    public static final String ACTION_START = "GPS_START";
    public static final String ACTION_STOP  = "GPS_STOP";

    private static final AtomicReference<Location> sLastLocation = new AtomicReference<>();
    private static final AtomicBoolean sRunning = new AtomicBoolean(false);
    private static final AtomicLong sSessionId = new AtomicLong(0L);
    private static volatile LocationCallback sCallback;
    private static final AtomicReference<Float> sMaxSpeed   = new AtomicReference<>(0f);
    private static final AtomicReference<Float> sTotalDistM = new AtomicReference<>(0f);
    private static final AtomicInteger sSatCount = new AtomicInteger(0);
    private static Location sPrevLoc = null;

    private LocationManager locManager;
    private GnssStatus.Callback gnssCallback;
    private FusedLocationProviderClient fusedClient;
    private com.google.android.gms.location.LocationCallback fusedCallback;
    private boolean doRecord = false;
    private final ExecutorService dbExec = Executors.newSingleThreadExecutor();

    public static @Nullable Location getLastLocation() { return sLastLocation.get(); }
    public static boolean isActive()          { return sRunning.get(); }
    public static float getMaxSpeedKmh()      { return sMaxSpeed.get() * 3.6f; }
    public static float getTotalDistM()       { return sTotalDistM.get(); }
    public static int   getSatCount()         { return sSatCount.get(); }
    public static long  getSessionId()        { return sSessionId.get(); }
    public static void  setCallback(LocationCallback cb) { sCallback = cb; }

    public interface LocationCallback {
        void onLocationUpdate(@NonNull Location loc, int satellites);
    }

    private void handleNewLocation(@NonNull Location loc) {
        sLastLocation.set(loc);
        float spd = loc.getSpeed();
        if (spd > sMaxSpeed.get()) sMaxSpeed.set(spd);
        if (sPrevLoc != null) {
            float dist = sPrevLoc.distanceTo(loc);
            if (dist < 500) sTotalDistM.set(sTotalDistM.get() + dist);
        }
        sPrevLoc = loc;
        if (doRecord) savePoint(loc);
        updateNotif(loc);
        LocationCallback cb = sCallback;
        if (cb != null) try { cb.onLocationUpdate(loc, sSatCount.get()); } catch (Exception ignored) {}
    }

    @Override public void onCreate() {
        super.onCreate();
        locManager  = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        fusedClient = LocationServices.getFusedLocationProviderClient(this);
        sRunning.set(true);
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) { stopSelf(); return START_NOT_STICKY; }
        long sid = System.currentTimeMillis();
        sSessionId.set(sid);
        sMaxSpeed.set(0f); sTotalDistM.set(0f); sPrevLoc = null;
        doRecord = intent != null && intent.getBooleanExtra(AppConfig.PREF_TRACK_ON, false);
        startFg(null);
        startUpdates();
        return START_STICKY;
    }

    private void startUpdates() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) return;
        try {
            fusedClient.getLastLocation().addOnSuccessListener(loc -> {
                if (loc != null) handleNewLocation(loc);
            });
        } catch (SecurityException ignored) {}

        LocationRequest req = new LocationRequest.Builder(
                Priority.PRIORITY_HIGH_ACCURACY, AppConfig.GPS_MIN_TIME_MS)
            .setMinUpdateDistanceMeters(AppConfig.GPS_MIN_DIST_M)
            .setMinUpdateIntervalMillis(500L)
            .setWaitForAccurateLocation(false)
            .build();

        fusedCallback = new com.google.android.gms.location.LocationCallback() {
            @Override public void onLocationResult(@NonNull LocationResult result) {
                Location loc = result.getLastLocation();
                if (loc != null) handleNewLocation(loc);
            }
        };
        try {
            fusedClient.requestLocationUpdates(req, fusedCallback, Looper.getMainLooper());
        } catch (SecurityException e) { Log.e(TAG, "fused updates: " + e.getMessage()); }

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                gnssCallback = new GnssStatus.Callback() {
                    @Override public void onSatelliteStatusChanged(@NonNull GnssStatus s) {
                        int used = 0;
                        for (int i = 0; i < s.getSatelliteCount(); i++) if (s.usedInFix(i)) used++;
                        sSatCount.set(used);
                    }
                };
                locManager.registerGnssStatusCallback(gnssCallback, null);
            }
        } catch (Exception e) { Log.e(TAG, "gnss status: " + e.getMessage()); }
    }

    private void savePoint(Location loc) {
        long sid = sSessionId.get();
        dbExec.execute(() -> {
            TrackPointEntity p = new TrackPointEntity();
            p.sessionId = sid; p.latitude = loc.getLatitude(); p.longitude = loc.getLongitude();
            p.altitude = loc.getAltitude(); p.speedMs = loc.getSpeed();
            p.bearing = loc.getBearing(); p.accuracy = loc.getAccuracy();
            p.timestamp = loc.getTime();
            GpsDatabase.getInstance(getApplicationContext()).trackDao().insert(p);
        });
    }

    private void startFg(@Nullable Location loc) {
        Intent pi = new Intent(this, MapActivity.class);
        PendingIntent pIntent = PendingIntent.getActivity(this, 0, pi,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        String txt = loc == null ? "Acquisizione segnale GPS..."
            : String.format("%.5f, %.5f  +/-%.0fm  %d SAT",
                loc.getLatitude(), loc.getLongitude(), loc.getAccuracy(), sSatCount.get());
        Notification n = new NotificationCompat.Builder(this, OfflineGpsApp.CHANNEL_GPS)
            .setSmallIcon(R.drawable.ic_gps).setContentTitle("OfflineGPS 3D")
            .setContentText(txt).setOngoing(true).setContentIntent(pIntent).build();
        startForeground(AppConfig.NOTIF_ID_GPS, n);
    }

    private void updateNotif(Location loc) {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (nm == null) return;
        Intent pi = new Intent(this, MapActivity.class);
        PendingIntent pIntent = PendingIntent.getActivity(this, 0, pi,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        String txt = String.format("%.5f, %.5f  %.1f km/h  %d SAT",
            loc.getLatitude(), loc.getLongitude(), loc.getSpeed()*3.6f, sSatCount.get());
        nm.notify(AppConfig.NOTIF_ID_GPS, new NotificationCompat.Builder(this, OfflineGpsApp.CHANNEL_GPS)
            .setSmallIcon(R.drawable.ic_gps).setContentTitle("OfflineGPS 3D")
            .setContentText(txt).setOngoing(true).setContentIntent(pIntent).build());
    }

    @Override public void onDestroy() {
        super.onDestroy(); sRunning.set(false);
        if (fusedCallback != null) try { fusedClient.removeLocationUpdates(fusedCallback); } catch (Exception ignored) {}
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && gnssCallback != null)
            try { locManager.unregisterGnssStatusCallback(gnssCallback); } catch (Exception ignored) {}
        dbExec.shutdown();
    }
    @Override public @Nullable IBinder onBind(Intent i) { return null; }
}
"""

COMPASS_MANAGER = r"""package com.offlinegps.map.gps;

import android.content.Context;
import android.hardware.*;
import androidx.annotation.*;

public final class CompassManager implements SensorEventListener {
    private static final float ALPHA = 0.12f;
    private final SensorManager sm;
    private final Sensor accel, mag;
    private float[] gravity = new float[3];
    private float[] geomag  = new float[3];
    private float[] rotMat  = new float[9];
    private float[] orient  = new float[3];
    private float azimuth, pitch, roll;
    private boolean hasGravity, hasGeo;
    @Nullable private Listener listener;

    public interface Listener { void onCompass(float azimuth, float pitch, float roll); }

    public CompassManager(@NonNull Context ctx) {
        sm    = (SensorManager) ctx.getSystemService(Context.SENSOR_SERVICE);
        accel = sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        mag   = sm.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
    }

    public void start(@NonNull Listener l) {
        listener = l;
        if (accel != null) sm.registerListener(this, accel, SensorManager.SENSOR_DELAY_UI);
        if (mag   != null) sm.registerListener(this, mag,   SensorManager.SENSOR_DELAY_UI);
    }

    public void stop() { sm.unregisterListener(this); listener = null; }

    @Override public void onSensorChanged(SensorEvent e) {
        if (e.sensor.getType() == Sensor.TYPE_ACCELEROMETER)
            { gravity = lowPass(e.values.clone(), gravity); hasGravity = true; }
        else if (e.sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD)
            { geomag = lowPass(e.values.clone(), geomag); hasGeo = true; }
        if (!hasGravity || !hasGeo) return;
        if (SensorManager.getRotationMatrix(rotMat, null, gravity, geomag)) {
            SensorManager.getOrientation(rotMat, orient);
            azimuth = (float) Math.toDegrees(orient[0]);
            if (azimuth < 0) azimuth += 360f;
            pitch = (float) Math.toDegrees(orient[1]);
            roll  = (float) Math.toDegrees(orient[2]);
            Listener l = listener;
            if (l != null) l.onCompass(azimuth, pitch, roll);
        }
    }

    @Override public void onAccuracyChanged(Sensor s, int a) {}

    private float[] lowPass(float[] in, float[] out) {
        for (int i = 0; i < in.length; i++) out[i] += ALPHA * (in[i] - out[i]);
        return out;
    }

    public float getAzimuth() { return azimuth; }
}
"""

MAP_CONTROLLER = r"""package com.offlinegps.map.map;

import android.content.Context;
import android.util.Log;
import androidx.annotation.*;
import org.mapsforge.core.graphics.*;
import org.mapsforge.core.model.*;
import org.mapsforge.core.util.LatLongUtils;
import org.mapsforge.map.android.graphics.AndroidBitmap;
import org.mapsforge.map.android.graphics.AndroidGraphicFactory;
import org.mapsforge.map.android.util.AndroidUtil;
import org.mapsforge.map.android.view.MapView;
import org.mapsforge.map.layer.cache.TileCache;
import org.mapsforge.map.layer.overlay.*;
import org.mapsforge.map.layer.renderer.TileRendererLayer;
import org.mapsforge.map.reader.MapFile;
import org.mapsforge.map.rendertheme.InternalRenderTheme;
import java.io.File;
import java.util.*;

public final class MapController {
    private static final String TAG = "MapCtrl";
    private final Context ctx;
    private MapView mapView;
    private TileCache tileCache;
    private TileRendererLayer rendererLayer;
    private Marker positionMarker;
    private Circle accuracyCircle;
    private Circle pulseCircle;
    private Polyline trackLine, trackGlow;
    private final List<LatLong> trackPoints = new ArrayList<>();
    private final List<Marker> waypointMarkers = new ArrayList<>();
    @Nullable private MapFile mapFile;
    private boolean mapLoaded = false;
    private float lastBearing = 0f;
    private float pulsePhase  = 0f;

    @Nullable private WaypointTapListener tapListener;
    public interface WaypointTapListener { void onWaypointTap(double lat, double lon, String colorHex); }

    public MapController(@NonNull Context ctx) { this.ctx = ctx; }
    public void setWaypointTapListener(@Nullable WaypointTapListener l) { this.tapListener = l; }

    public void init(@NonNull MapView mv) {
        mapView = mv;
        mapView.setClickable(true);
        mapView.getMapScaleBar().setVisible(true);
        mapView.setBuiltInZoomControls(false);
        mapView.getModel().mapViewPosition.setZoomLevelMax((byte) 19);
        mapView.getModel().mapViewPosition.setZoomLevelMin((byte) 4);
        tileCache = AndroidUtil.createTileCache(ctx, "mapcache_v2",
            mapView.getModel().displayModel.getTileSize(), 1f,
            mapView.getModel().frameBufferModel.getOverdrawFactor(), true);
    }

    public boolean loadMapFile(@NonNull File file) {
        if (!file.exists()) return false;
        try {
            clearRendererLayer();
            mapFile = new MapFile(file);
            rendererLayer = new TileRendererLayer(tileCache, mapFile,
                mapView.getModel().mapViewPosition, AndroidGraphicFactory.INSTANCE);
            rendererLayer.setXmlRenderTheme(InternalRenderTheme.OSMARENDER);
            mapView.getLayerManager().getLayers().add(0, rendererLayer);
            BoundingBox bb = mapFile.boundingBox();
            mapView.getModel().mapViewPosition.setMapPosition(
                new MapPosition(bb.getCenterPoint(), (byte) 15));
            mapLoaded = true;
            Log.d(TAG, "Mappa: " + file.getName());
            return true;
        } catch (Exception e) { Log.e(TAG, "loadMap: " + e.getMessage()); return false; }
    }

    public boolean isMapLoaded() { return mapLoaded; }

    private boolean nightMode = false;
    /** Modo notte: applica un velo scuro sopra la mappa (semplice e affidabile). */
    public void setNightMode(boolean night) {
        this.nightMode = night;
        if (mapView == null) return;
        try {
            mapView.getModel().displayModel.setBackgroundColor(
                night ? 0xFF0A0E1A : 0xFFF0F0F0);
            mapView.invalidate();
        } catch (Exception ignored) {}
    }
    public boolean isNightMode() { return nightMode; }

    public void updatePosition(double lat, double lon, float accuracy) {
        updatePosition(lat, lon, accuracy, lastBearing);
    }

    public void updatePosition(double lat, double lon, float accuracy, float bearing) {
        LatLong pos = new LatLong(lat, lon);
        if (positionMarker == null) {
            lastBearing = bearing;
            accuracyCircle = buildAccuracyCircle(pos, accuracy);
            pulseCircle    = buildPulseCircle(pos);
            positionMarker = new Marker(pos, buildPositionBitmap(bearing), 0, 0);
            mapView.getLayerManager().getLayers().add(accuracyCircle);
            mapView.getLayerManager().getLayers().add(pulseCircle);
            mapView.getLayerManager().getLayers().add(positionMarker);
        } else {
            // Ricreo l'immagine della freccia SOLO se la direzione e' cambiata
            // di almeno 3 gradi: evita di ridisegnarla a ogni aggiornamento GPS
            // quando sei fermo o vai dritto (risparmio CPU e memoria).
            if (Math.abs(bearing - lastBearing) >= 3f) {
                lastBearing = bearing;
                org.mapsforge.core.graphics.Bitmap old = positionMarker.getBitmap();
                positionMarker.setBitmap(buildPositionBitmap(bearing));
                if (old != null) old.decrementRefCount();
            }
            positionMarker.setLatLong(pos);
            accuracyCircle.setLatLong(pos);
            accuracyCircle.setRadius(Math.max(accuracy, 5f));
            pulseCircle.setLatLong(pos);
        }
        mapView.getLayerManager().redrawLayers();
    }

    public void tickPulse() {
        if (pulseCircle == null) return;
        pulsePhase += 0.08f;
        if (pulsePhase > Math.PI * 2) pulsePhase -= (float)(Math.PI * 2);
        float radius = 12f + 10f * (float) Math.abs(Math.sin(pulsePhase));
        pulseCircle.setRadius(radius);
        int alpha = (int)(60 * (1f - Math.abs(Math.sin(pulsePhase))));
        Paint fill = AndroidGraphicFactory.INSTANCE.createPaint();
        fill.setColor((alpha << 24) | 0x0000E5FF); fill.setStyle(Style.FILL);
        pulseCircle.setPaintFill(fill);
        mapView.getLayerManager().redrawLayers();
    }

    public void centerOn(double lat, double lon, boolean animate) {
        LatLong p = new LatLong(lat, lon);
        if (animate) mapView.getModel().mapViewPosition.animateTo(p);
        else         mapView.getModel().mapViewPosition.setCenter(p);
    }

    public void centerOn(double lat, double lon, byte zoom) {
        mapView.getModel().mapViewPosition.setMapPosition(
            new MapPosition(new LatLong(lat, lon), zoom));
    }

    @Nullable private Marker destMarker;
    /** Mostra un marker rosso sulla destinazione cercata. */
    public void setDestinationMarker(double lat, double lon) {
        LatLong p = new LatLong(lat, lon);
        if (destMarker != null) {
            org.mapsforge.core.graphics.Bitmap old = destMarker.getBitmap();
            destMarker.setLatLong(p);
            if (old == null) destMarker.setBitmap(buildDestBitmap());
        } else {
            destMarker = new Marker(p, buildDestBitmap(), 0, -24);
            mapView.getLayerManager().getLayers().add(destMarker);
        }
        mapView.getLayerManager().redrawLayers();
    }

    private org.mapsforge.core.graphics.Bitmap buildDestBitmap() {
        int size = 48;
        android.graphics.Bitmap bmp = android.graphics.Bitmap.createBitmap(
            size, size, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(bmp);
        android.graphics.Paint pin = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        pin.setColor(0xFFFF1744);
        c.drawCircle(size/2f, size/2f, size/2.6f, pin);
        android.graphics.Paint dot = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        dot.setColor(0xFFFFFFFF);
        c.drawCircle(size/2f, size/2f, size/7f, dot);
        return new AndroidBitmap(bmp);
    }

    public void addTrackPoint(double lat, double lon) {
        trackPoints.add(new LatLong(lat, lon));
        refreshTrackLines();
    }

    /** v4.0: aggiunge molti punti con UN solo ridisegno (prima: uno per punto). */
    public void addTrackPoints(java.util.List<double[]> pts) {
        for (double[] p : pts) trackPoints.add(new LatLong(p[0], p[1]));
        refreshTrackLines();
    }

    private void refreshTrackLines() {
        if (trackLine == null) {
            // alone largo e trasparente sotto la linea: effetto neon sulla mappa
            Paint glow = AndroidGraphicFactory.INSTANCE.createPaint();
            glow.setColor(0x4400FF88); glow.setStrokeWidth(20f); glow.setStyle(Style.STROKE);
            glow.setStrokeCap(org.mapsforge.core.graphics.Cap.ROUND);
            glow.setStrokeJoin(org.mapsforge.core.graphics.Join.ROUND);
            trackGlow = new Polyline(glow, AndroidGraphicFactory.INSTANCE);
            mapView.getLayerManager().getLayers().add(trackGlow);
            Paint paint = AndroidGraphicFactory.INSTANCE.createPaint();
            paint.setColor(0xFF00FF88); paint.setStrokeWidth(7f); paint.setStyle(Style.STROKE);
            paint.setStrokeCap(org.mapsforge.core.graphics.Cap.ROUND);
            paint.setStrokeJoin(org.mapsforge.core.graphics.Join.ROUND);
            trackLine = new Polyline(paint, AndroidGraphicFactory.INSTANCE);
            mapView.getLayerManager().getLayers().add(trackLine);
        }
        trackGlow.getLatLongs().clear();
        trackGlow.getLatLongs().addAll(trackPoints);
        trackLine.getLatLongs().clear();
        trackLine.getLatLongs().addAll(trackPoints);
        mapView.getLayerManager().redrawLayers();
    }

    public void clearTrack() {
        trackPoints.clear();
        if (trackGlow != null) trackGlow.getLatLongs().clear();
        if (trackLine != null) { trackLine.getLatLongs().clear(); mapView.getLayerManager().redrawLayers(); }
    }

    public void fitTrackBounds() {
        if (trackPoints.size() < 2) return;
        double minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
        for (LatLong p : trackPoints) {
            minLat = Math.min(minLat, p.latitude); maxLat = Math.max(maxLat, p.latitude);
            minLon = Math.min(minLon, p.longitude); maxLon = Math.max(maxLon, p.longitude);
        }
        BoundingBox bb = new BoundingBox(minLat, minLon, maxLat, maxLon);
        byte zoom = LatLongUtils.zoomForBounds(mapView.getDimension(), bb,
            mapView.getModel().displayModel.getTileSize());
        mapView.getModel().mapViewPosition.setMapPosition(
            new MapPosition(bb.getCenterPoint(), (byte) Math.min(zoom, 17)));
    }

    public void addWaypointMarker(double lat, double lon, String colorHex) {
        LatLong pos = new LatLong(lat, lon);
        final int color = parseAndroidColor(colorHex, 0xFF00E5FF);
        final double wLat = lat, wLon = lon; final String wColor = colorHex;
        Marker m = new Marker(pos, buildWaypointBitmap(color), 0, -21) {
            @Override public boolean onTap(LatLong tapLatLong, Point layerXY, Point tapXY) {
                if (contains(layerXY, tapXY)) {
                    if (tapListener != null) tapListener.onWaypointTap(wLat, wLon, wColor);
                    return true;
                }
                return false;
            }
        };
        waypointMarkers.add(m);
        mapView.getLayerManager().getLayers().add(m);
        mapView.getLayerManager().redrawLayers();
    }

    public void clearWaypointMarkers() {
        for (Marker m : waypointMarkers) mapView.getLayerManager().getLayers().remove(m);
        waypointMarkers.clear();
    }

    public void zoomIn()  { byte z = mapView.getModel().mapViewPosition.getZoomLevel(); if (z<19) mapView.getModel().mapViewPosition.setZoomLevel((byte)(z+1)); }
    public void zoomOut() { byte z = mapView.getModel().mapViewPosition.getZoomLevel(); if (z>4)  mapView.getModel().mapViewPosition.setZoomLevel((byte)(z-1)); }
    public int getZoom()  { return mapView.getModel().mapViewPosition.getZoomLevel(); }

    private org.mapsforge.core.graphics.Bitmap buildPositionBitmap(float bearing) {
        android.graphics.Bitmap rawBmp = android.graphics.Bitmap.createBitmap(
            72, 72, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(rawBmp);
        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        float cx = 36, cy = 36;
        c.save(); c.rotate(bearing, cx, cy);
        // cono di visione (come Google Maps): sfumatura che indica la direzione
        android.graphics.Path cone = new android.graphics.Path();
        cone.moveTo(cx, cy);
        cone.lineTo(cx - 18, cy - 30);
        cone.quadTo(cx, cy - 38, cx + 18, cy - 30);
        cone.close();
        android.graphics.Shader shader = new android.graphics.LinearGradient(
            cx, cy - 32, cx, cy,
            0x5500E5FF, 0x0000E5FF, android.graphics.Shader.TileMode.CLAMP);
        p.setShader(shader);
        c.drawPath(cone, p);
        p.setShader(null);
        c.restore();
        // alone esterno
        p.setColor(0x2200E5FF); c.drawCircle(cx, cy, 16, p);
        // punto centrale bianco bordato (la "perla" di posizione)
        p.setColor(0xFFFFFFFF); c.drawCircle(cx, cy, 9, p);
        p.setColor(0xFF1565C0); c.drawCircle(cx, cy, 7, p);
        p.setColor(0xFF00E5FF); c.drawCircle(cx, cy, 4, p);
        return new AndroidBitmap(rawBmp);
    }

    private Circle buildAccuracyCircle(LatLong pos, float acc) {
        Paint fill = AndroidGraphicFactory.INSTANCE.createPaint();
        fill.setColor(0x1100E5FF); fill.setStyle(Style.FILL);
        Paint stroke = AndroidGraphicFactory.INSTANCE.createPaint();
        stroke.setColor(0x4400E5FF); stroke.setStrokeWidth(2f); stroke.setStyle(Style.STROKE);
        return new Circle(pos, Math.max(acc, 5f), fill, stroke);
    }

    private Circle buildPulseCircle(LatLong pos) {
        Paint fill = AndroidGraphicFactory.INSTANCE.createPaint();
        fill.setColor(0x3300E5FF); fill.setStyle(Style.FILL);
        return new Circle(pos, 12f, fill, null);
    }

    private org.mapsforge.core.graphics.Bitmap buildWaypointBitmap(int color) {
        android.graphics.Bitmap rawBmp = android.graphics.Bitmap.createBitmap(
            32, 42, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(rawBmp);
        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        android.graphics.Path path = new android.graphics.Path();
        path.moveTo(16, 42);
        path.lineTo(4, 18);
        path.arcTo(new android.graphics.RectF(2, 2, 30, 30), 210, 300);
        path.close();
        p.setColor(color); c.drawPath(path, p);
        p.setColor(0xFF050A14); c.drawCircle(16, 16, 7, p);
        return new AndroidBitmap(rawBmp);
    }

    private int parseAndroidColor(String hex, int fallback) {
        try { return android.graphics.Color.parseColor(hex); } catch (Exception e) { return fallback; }
    }

    private void clearRendererLayer() {
        if (rendererLayer != null) {
            mapView.getLayerManager().getLayers().remove(rendererLayer);
            rendererLayer.onDestroy();
            rendererLayer = null;
        }
        if (mapFile != null) { mapFile.close(); mapFile = null; }
        mapLoaded = false;
    }

    public void destroy() {
        clearRendererLayer();
        clearWaypointMarkers();
        if (tileCache != null) { tileCache.destroy(); tileCache = null; }
        if (mapView  != null) { mapView.destroyAll(); mapView = null; }
    }
}
"""

GPX_EXPORTER = r"""package com.offlinegps.map.util;

import android.content.Context;
import androidx.annotation.*;
import com.offlinegps.map.data.*;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;

public final class GpxExporter {
    private GpxExporter() {}

    @WorkerThread @NonNull
    public static File exportSession(@NonNull Context ctx, long sessionId) throws IOException {
        List<TrackPointEntity> points =
            GpsDatabase.getInstance(ctx).trackDao().getSessionSync(sessionId);
        SimpleDateFormat iso = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US);
        iso.setTimeZone(TimeZone.getTimeZone("UTC"));
        File dir = new File(ctx.getExternalFilesDir(null), "tracks"); dir.mkdirs();
        File f = new File(dir, "track_" + sessionId + ".gpx");
        try (PrintWriter pw = new PrintWriter(new FileWriter(f))) {
            pw.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
            pw.println("<gpx version=\"1.1\" creator=\"OfflineGPS 3D v3.0\"");
            pw.println("  xmlns=\"http://www.topografix.com/GPX/1/1\">");
            pw.println("  <trk><name>Track " + iso.format(new Date(sessionId)) + "</name><trkseg>");
            for (TrackPointEntity p : points) {
                pw.printf("    <trkpt lat=\"%.8f\" lon=\"%.8f\">%n", p.latitude, p.longitude);
                pw.printf("      <ele>%.2f</ele>%n", p.altitude);
                pw.printf("      <time>%s</time>%n", iso.format(new Date(p.timestamp)));
                pw.printf("      <speed>%.4f</speed>%n", p.speedMs);
                pw.println("    </trkpt>");
            }
            pw.println("  </trkseg></trk></gpx>");
        }
        return f;
    }
}
"""

ROUTING_ENGINE = r"""package com.offlinegps.map.routing;

import android.content.Context;
import android.util.Log;
import androidx.annotation.*;
import com.graphhopper.GHRequest;
import com.graphhopper.GHResponse;
import com.graphhopper.GraphHopper;
import com.graphhopper.ResponsePath;
import com.graphhopper.config.Profile;
import com.graphhopper.util.Instruction;
import com.graphhopper.util.InstructionList;
import com.graphhopper.util.PointList;
import com.graphhopper.util.Translation;
import com.graphhopper.util.TranslationMap;
import com.graphhopper.util.shapes.GHPoint;
import java.io.File;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

public final class RoutingEngine {
    private static final String TAG = "RoutingEngine";

    public static final String PROFILE_CAR  = "car";
    public static final String PROFILE_BIKE = "bike";
    public static final String PROFILE_FOOT = "foot";

    private static volatile RoutingEngine INSTANCE;
    private static final AtomicBoolean sBuilding = new AtomicBoolean(false);

    private GraphHopper hopper;
    private String loadedRegionTag;
    private final TranslationMap translationMap = new TranslationMap().doImport();

    public interface BuildProgressListener {
        void onProgress(String message, int percentIndeterminate);
        void onDone(boolean success, @Nullable String error);
    }

    public interface RouteCallback {
        void onRouteReady(@NonNull RouteResult result);
        void onRouteError(@NonNull String message);
    }

    private RoutingEngine() {}

    @NonNull
    public static synchronized RoutingEngine getInstance() {
        if (INSTANCE == null) INSTANCE = new RoutingEngine();
        return INSTANCE;
    }

    public static boolean isBuilding() { return sBuilding.get(); }

    public boolean isReady() { return hopper != null; }

    @Nullable public String getLoadedRegionTag() { return loadedRegionTag; }

    @WorkerThread
    public synchronized void buildOrLoad(@NonNull Context ctx, @NonNull File pbfFile,
            @NonNull File graphFolder, @NonNull String regionTag,
            @Nullable BuildProgressListener listener) {

        if (hopper != null && regionTag.equals(loadedRegionTag)) {
            if (listener != null) listener.onDone(true, null);
            return;
        }
        if (hopper != null) { hopper.close(); hopper = null; loadedRegionTag = null; }

        sBuilding.set(true);
        try {
            // v5.0: la rete contiene auto + bici + piedi. Una rete vecchia (solo auto)
            // non ha il marcatore: viene cancellata e ricostruita automaticamente.
            File marker = new File(graphFolder, PROFILES_MARKER);
            boolean alreadyBuilt = graphFolder.exists()
                && new File(graphFolder, "properties").exists() && marker.exists();
            if (graphFolder.exists() && !alreadyBuilt) {
                if (listener != null) listener.onProgress(
                    "Aggiornamento rete stradale per bici e piedi (una volta sola)...", -1);
                deleteRecursive(graphFolder);
            }

            long pbfMB = pbfFile.length() / (1024 * 1024);
            // stima grossolana: ~10-20 secondi per ogni 50 MB sul telefono
            long estMin = Math.max(1, (pbfMB / 50) * 15 / 60);

            if (listener != null) {
                if (alreadyBuilt) {
                    listener.onProgress("Caricamento rete stradale...", -1);
                } else {
                    listener.onProgress("Costruzione rete stradale (" + pbfMB
                        + " MB, prima volta ~" + estMin + "-" + (estMin + 2)
                        + " min). NON chiudere l'app, sta lavorando...", -1);
                }
            }

            // ticker: aggiorna i secondi trascorsi cosi' l'utente vede che lavora
            final boolean showTicker = !alreadyBuilt;
            final long startTime = System.currentTimeMillis();
            final java.util.concurrent.atomic.AtomicBoolean ticking =
                new java.util.concurrent.atomic.AtomicBoolean(showTicker);
            if (showTicker && listener != null) {
                new Thread(() -> {
                    while (ticking.get()) {
                        try { Thread.sleep(3000); } catch (InterruptedException ie) { break; }
                        long sec = (System.currentTimeMillis() - startTime) / 1000;
                        listener.onProgress("Costruzione rete stradale... "
                            + sec + "s trascorsi (NON chiudere, sta lavorando)", -1);
                    }
                }).start();
            }

            GraphHopper gh = new GraphHopper();
            gh.setOSMFile(pbfFile.getAbsolutePath());
            gh.setGraphHopperLocation(graphFolder.getAbsolutePath());

            // GraphHopper 6.2: sistema "classico" senza custom model ne Janino.
            // SENZA Contraction Hierarchies (CH): la CH e' la fase piu' pesante e
            // su telefono richiede molti minuti per ogni profilo. Senza CH i tre
            // profili costano poco in piu' (qualche bit per strada) e il calcolo
            // del singolo percorso resta veloce su distanze normali.
            // v5.0: bici e piedi sono profili VERI (prima si usava sempre l'auto:
            // niente sentieri/zone pedonali e tempi da auto anche a piedi).
            gh.setProfiles(
                new Profile(PROFILE_CAR).setVehicle("car").setWeighting("fastest").setTurnCosts(false),
                new Profile(PROFILE_BIKE).setVehicle("bike").setWeighting("fastest").setTurnCosts(false),
                new Profile(PROFILE_FOOT).setVehicle("foot").setWeighting("fastest").setTurnCosts(false)
            );
            // NIENTE setCHProfiles -> usa l'algoritmo "flessibile" (nessuna
            // preparazione pesante).
            gh.setMinNetworkSize(200);
            gh.setElevationProvider(com.graphhopper.reader.dem.ElevationProvider.NOOP);

            try {
                gh.importOrLoad();
            } finally {
                ticking.set(false);
            }
            if (!marker.exists()) {
                try { marker.createNewFile(); } catch (Exception ignored) {}
            }

            hopper = gh;
            loadedRegionTag = regionTag;
            Log.d(TAG, "Grafo pronto per regione: " + regionTag);

            // v2.6: costruisci/carica l'indice geocoding per questa regione
            try {
                File geoIndex = new File(graphFolder.getParentFile(), regionTag + "-geo.idx");
                OfflineGeocoder.getInstance().loadOrBuild(pbfFile, geoIndex, regionTag, listener);
            } catch (Exception ge) {
                Log.w(TAG, "Indice geocoding non disponibile: " + ge.getMessage());
            }

            if (listener != null) listener.onDone(true, null);

        } catch (Exception e) {
            Log.e(TAG, "buildOrLoad fallita: " + e.getMessage(), e);
            hopper = null; loadedRegionTag = null;
            if (listener != null) listener.onDone(false, e.getMessage());
        } finally {
            sBuilding.set(false);
        }
    }

    private static final String PROFILES_MARKER = "ogps_profiles_car_bike_foot";

    private static boolean deleteRecursive(File f) {
        if (f.isDirectory()) {
            File[] kids = f.listFiles();
            if (kids != null) for (File k : kids) deleteRecursive(k);
        }
        return f.delete();
    }

    /** Ultimo messaggio d'errore leggibile (es. punto lontano da strade). */
    private volatile String lastError = "";
    public String getLastError() { return lastError; }

    @WorkerThread
    @Nullable
    public RouteResult route(double fromLat, double fromLon, double toLat, double toLon,
            @NonNull String profile) {
        lastError = "";
        if (hopper == null) { lastError = "Rete stradale non caricata"; return null; }
        String useProfile = PROFILE_BIKE.equals(profile) || PROFILE_FOOT.equals(profile)
            ? profile : PROFILE_CAR;
        GHRequest req = new GHRequest(
            new GHPoint(fromLat, fromLon), new GHPoint(toLat, toLon));
        req.setProfile(useProfile);
        // Rete costruita SENZA CH: disabilitiamo CH nella richiesta cosi' usa
        // l'algoritmo flessibile (altrimenti GraphHopper cerca la CH e fallisce).
        req.putHint("ch.disable", true);
        req.setLocale(Locale.ITALIAN);
        GHResponse rsp;
        try {
            rsp = hopper.route(req);
        } catch (Exception e) {
            lastError = "Errore nel calcolo del percorso";
            if (e.getMessage() != null && e.getMessage().contains("profile"))
                lastError = "La rete stradale va ricostruita: Download -> RICOSTRUISCI RETE";
            Log.w(TAG, "Routing exception", e);
            return null;
        }
        if (rsp.hasErrors()) {
            String err = rsp.getErrors().toString();
            // traduco gli errori piu' comuni in messaggi comprensibili
            if (err.contains("Cannot find point") || err.contains("ConnectionNotFound")
                    || err.toLowerCase().contains("disconnected"))
                lastError = "Punto troppo lontano da una strada, o nessun percorso stradale possibile. Avvicina la destinazione a una strada.";
            else
                lastError = "Impossibile calcolare il percorso";
            Log.w(TAG, "Routing error: " + err);
            return null;
        }
        ResponsePath path = rsp.getBest();
        return RouteResult.from(path, translationMap.getWithFallBack(Locale.ITALIAN), useProfile);
    }

    public void close() {
        if (hopper != null) { hopper.close(); hopper = null; loadedRegionTag = null; }
    }

    public static final class RouteResult {
        public final List<double[]> points;
        public final List<NavStep> steps;
        public final double distanceMeters;
        public final long timeMillis;
        public final String profile;

        public RouteResult(List<double[]> points, List<NavStep> steps,
                double distanceMeters, long timeMillis, String profile) {
            this.points = points; this.steps = steps;
            this.distanceMeters = distanceMeters; this.timeMillis = timeMillis;
            this.profile = profile;
        }

        static RouteResult from(ResponsePath path, Translation tr, String profile) {
            PointList pl = path.getPoints();
            List<double[]> pts = new ArrayList<>(pl.size());
            for (int i = 0; i < pl.size(); i++) pts.add(new double[]{pl.getLat(i), pl.getLon(i)});

            List<NavStep> steps = new ArrayList<>();
            InstructionList instr = path.getInstructions();
            if (instr != null) {
                // i punti delle istruzioni, messi in fila, sono i punti del percorso:
                // il primo punto di ogni istruzione e' il luogo della sua manovra
                int idx = 0;
                for (Instruction ins : instr) {
                    String text = ins.getTurnDescription(tr);
                    String street = ins.getName();
                    if (text == null || text.isEmpty()) text = street;
                    int at = Math.min(idx, Math.max(0, pts.size() - 1));
                    double[] p = pts.isEmpty() ? new double[]{Double.NaN, Double.NaN} : pts.get(at);
                    int exit = 0;
                    if (ins instanceof com.graphhopper.util.RoundaboutInstruction)
                        exit = ((com.graphhopper.util.RoundaboutInstruction) ins).getExitNumber();
                    steps.add(new NavStep(text, street, ins.getDistance(), ins.getTime(), ins.getSign(),
                        at, p[0], p[1], exit));
                    PointList ip = ins.getPoints();
                    idx += ip != null ? ip.size() : 0;
                }
            }
            return new RouteResult(pts, steps, path.getDistance(), path.getTime(), profile);
        }
    }

    public static final class NavStep {
        public final String text;
        public final String streetName;
        public final double distanceMeters;   // lunghezza del tratto che INIZIA con questa manovra
        public final long timeMillis;
        public final int sign;
        /** Indice nel percorso e coordinate del punto della manovra. */
        public final int pointIndex;
        public final double lat, lon;
        /** Uscita della rotonda (0 se non e' una rotonda). */
        public final int exitNumber;

        public NavStep(String text, String streetName, double distanceMeters, long timeMillis, int sign,
                       int pointIndex, double lat, double lon, int exitNumber) {
            this.text = text; this.streetName = streetName; this.distanceMeters = distanceMeters;
            this.timeMillis = timeMillis; this.sign = sign;
            this.pointIndex = pointIndex; this.lat = lat; this.lon = lon; this.exitNumber = exitNumber;
        }

        public String formatDistance() { return formatMeters(distanceMeters); }

        public static String formatMeters(double m) {
            if (m < 1000) return String.format(Locale.ITALY, "%.0f m", m);
            return String.format(Locale.ITALY, "%.1f km", m / 1000.0);
        }
    }
}
"""

# ============================================================
#  OFFLINE GEOCODER v3.1 — indice COMPLETO di vie e civici
#  Fix: prima trovava "poche vie con civico" perche' (1) ogni nome
#  via era indicizzato UNA sola volta per regione, (2) i civici
#  venivano letti solo dai nodi e non dagli edifici, (3) la query
#  "via roma 10" non capiva il numero.
# ============================================================
OFFLINE_GEOCODER = r"""package com.offlinegps.map.routing;

import android.util.Log;
import androidx.annotation.*;
import com.graphhopper.reader.ReaderElement;
import com.graphhopper.reader.ReaderNode;
import com.graphhopper.reader.ReaderWay;
import com.graphhopper.reader.osm.OSMInputFile;
import java.io.*;
import java.text.Normalizer;
import java.util.*;

/**
 * Geocoder offline v3.1 — indice COMPLETO di vie e civici dal file .pbf.
 *
 * Novita' rispetto alla versione precedente (che trovava "poche vie con civico"):
 *  - una via con lo stesso nome in citta' diverse ora compare PIU' VOLTE
 *    (prima "Via Roma" veniva indicizzata una sola volta per tutta la regione);
 *  - i numeri civici vengono letti anche dagli EDIFICI (way con
 *    addr:housenumber), non solo dai nodi: in Italia la maggior parte dei
 *    civici e' mappata sugli edifici, quindi prima se ne perdevano quasi tutti;
 *  - a ogni via viene assegnata la CITTA' piu' vicina (nodi "place" di OSM),
 *    cosi' il filtro "via roma, milano" funziona davvero;
 *  - la ricerca capisce il civico nel testo: "via roma 10" trova la via
 *    e poi il numero 10 di QUELLA via (entro 4 km dal suo centro).
 *
 * Formato indice V2 (una riga per voce, prima riga = intestazione "V2"):
 *   S\tnome\tcitta\tlat\tlon      via (piu' righe per lo stesso nome)
 *   H\tvia\tnumero\tlat\tlon      civico (raggruppato per via al caricamento)
 * Gli indici vecchi (senza intestazione V2) vengono ricostruiti da soli.
 */
public final class OfflineGeocoder {
    private static final String TAG = "OfflineGeocoder";
    private static final String INDEX_HEADER = "V2";
    private static volatile OfflineGeocoder INSTANCE;

    private final List<Entry> streets = new ArrayList<>();
    private final Map<String, CivicGroup> civics = new HashMap<>();
    private int civicTotal = 0;
    private String loadedRegionTag;
    @Nullable private String lastError;

    public static final class Entry {
        public final String type;      // "S" street, "H" housenumber
        public final String name;      // etichetta visibile
        public final String normName;  // normalizzata per ricerca
        public final String city;      // citta (puo' essere "")
        public final double lat, lon;
        Entry(String type, String name, String city, double lat, double lon) {
            this.type = type; this.name = name; this.normName = normalize(name);
            this.city = city; this.lat = lat; this.lon = lon;
        }
        public boolean isHouseNumber() { return "H".equals(type); }
    }

    /** Un civico: numero + coordinate (float: precisione ~1 m, meta' memoria). */
    private static final class Civic {
        final String num; final float lat, lon;
        Civic(String num, float lat, float lon) { this.num = num; this.lat = lat; this.lon = lon; }
    }
    /** Tutti i civici di una via (chiave: nome via normalizzato). */
    private static final class CivicGroup {
        final String display;
        final ArrayList<Civic> list = new ArrayList<>();
        CivicGroup(String display) { this.display = display; }
    }

    private OfflineGeocoder() {}

    @NonNull
    public static synchronized OfflineGeocoder getInstance() {
        if (INSTANCE == null) INSTANCE = new OfflineGeocoder();
        return INSTANCE;
    }

    public boolean isReady() { return !streets.isEmpty(); }
    @Nullable public String getLoadedRegionTag() { return loadedRegionTag; }
    public int size() { return streets.size() + civicTotal; }
    public int streetCount() { return streets.size(); }
    public int civicCount() { return civicTotal; }

    @WorkerThread
    public synchronized void loadOrBuild(@NonNull File pbfFile, @NonNull File indexFile,
            @NonNull String regionTag, @Nullable RoutingEngine.BuildProgressListener listener) {
        if (regionTag.equals(loadedRegionTag) && !streets.isEmpty()) return;
        lastError = null;
        try {
            if (!pbfFile.exists()) { lastError = "File .pbf non trovato"; return; }
            // indice della vecchia versione? ricostruisci con vie+civici completi
            if (indexFile.exists() && !isCurrentVersion(indexFile)) {
                Log.d(TAG, "Indice vecchio: ricostruzione completa (vie multi-citta' + civici edifici)");
                indexFile.delete();
            }
            if (!indexFile.exists()) {
                if (listener != null) listener.onProgress(
                    "Indicizzazione COMPLETA di vie e civici (prima volta, qualche minuto)...", -1);
                buildIndex(pbfFile, indexFile);
            }
            if (listener != null) listener.onProgress("Caricamento indice indirizzi...", -1);
            loadIndex(indexFile);
            loadedRegionTag = regionTag;
            if (streets.isEmpty()) lastError = "Indice vuoto (nessuna via trovata nel file)";
            Log.d(TAG, "Geocoder: " + streets.size() + " voci via, " + civicTotal
                + " civici (" + regionTag + ")");
        } catch (Throwable e) {
            lastError = e.getClass().getSimpleName() + ": " + e.getMessage();
            Log.e(TAG, "loadOrBuild: " + lastError, e);
            // se l'indice e' corrotto/parziale, eliminalo cosi' si ricostruisce
            try { if (indexFile.exists()) indexFile.delete(); } catch (Exception ignored) {}
        }
    }

    @Nullable public String getLastError() { return lastError; }

    private boolean isCurrentVersion(File indexFile) {
        try (BufferedReader br = new BufferedReader(new InputStreamReader(
                new FileInputStream(indexFile), "UTF-8"))) {
            return INDEX_HEADER.equals(br.readLine());
        } catch (Exception e) { return false; }
    }

    /** Costruisce l'indice: vie multi-citta' + civici da nodi ED edifici. */
    @WorkerThread
    private void buildIndex(File pbf, File indexOut) throws Exception {
        final int SEED_CAP = 120;  // segmenti campionati per ogni nome-via
        // nome normalizzato -> nodi centrali campionati. Reservoir sampling:
        // per nomi comuni ("Via Roma" esiste in centinaia di comuni) il
        // campione resta rappresentativo di TUTTA la regione.
        Map<String, ArrayList<Long>> streetSeeds = new HashMap<>();
        Map<String, Integer> seedTotal = new HashMap<>();
        Map<String, String> streetDisplay = new HashMap<>();
        // primo nodo di ogni EDIFICIO con civico -> {via, numero}
        Map<Long, String[]> civicWayNodes = new HashMap<>();
        Random rnd = new Random(42);

        // --- Passata 1: way (vie con nome + edifici con civico) ---
        try (OSMInputFile in = new OSMInputFile(pbf).setWorkerThreads(1).open()) {
            ReaderElement el;
            while ((el = in.getNext()) != null) {
                if (el.getType() != ReaderElement.Type.WAY) continue;
                ReaderWay w = (ReaderWay) el;
                com.carrotsearch.hppc.LongIndexedContainer nodes = w.getNodes();
                if (nodes == null || nodes.size() == 0) continue;

                String name = w.getTag("name", null);
                if (name != null && !name.isEmpty() && w.hasTag("highway")) {
                    String norm = normalize(name);
                    if (!streetDisplay.containsKey(norm)) streetDisplay.put(norm, name);
                    long mid = nodes.get(nodes.size() / 2);
                    Integer prev = seedTotal.get(norm);
                    int total = (prev == null ? 0 : prev) + 1;
                    seedTotal.put(norm, total);
                    ArrayList<Long> seeds = streetSeeds.get(norm);
                    if (seeds == null) { seeds = new ArrayList<>(); streetSeeds.put(norm, seeds); }
                    if (seeds.size() < SEED_CAP) seeds.add(mid);
                    else { int j = rnd.nextInt(total); if (j < SEED_CAP) seeds.set(j, mid); }
                }

                String hn = w.getTag("addr:housenumber", null);
                if (hn != null && !hn.isEmpty()) {
                    String street = firstNonNull(w.getTag("addr:street", null), "");
                    if (!street.isEmpty())
                        civicWayNodes.put(nodes.get(0), new String[]{street, hn});
                }
            }
        }

        // mappa inversa: nodo campione -> nomi via che lo usano
        Map<Long, ArrayList<String>> nodeToNames = new HashMap<>();
        for (Map.Entry<String, ArrayList<Long>> e : streetSeeds.entrySet()) {
            for (Long id : e.getValue()) {
                ArrayList<String> l = nodeToNames.get(id);
                if (l == null) { l = new ArrayList<>(2); nodeToNames.put(id, l); }
                l.add(e.getKey());
            }
        }
        streetSeeds.clear();

        // --- Passata 2: nodi (coordinate vie, civici su nodo, luoghi/citta') ---
        Map<String, ArrayList<double[]>> streetCoords = new HashMap<>();
        ArrayList<String[]> civicRows = new ArrayList<>();  // {via, numero, lat, lon}
        HashSet<String> civicSeen = new HashSet<>();
        ArrayList<Object[]> places = new ArrayList<>();     // {nome, peso, lat, lon}

        try (OSMInputFile in = new OSMInputFile(pbf).setWorkerThreads(1).open()) {
            ReaderElement el;
            while ((el = in.getNext()) != null) {
                if (el.getType() != ReaderElement.Type.NODE) continue;
                ReaderNode n = (ReaderNode) el;
                long id = n.getId();

                // a) coordinate dei nodi campione delle vie
                ArrayList<String> names = nodeToNames.get(id);
                if (names != null) {
                    for (String norm : names) {
                        ArrayList<double[]> l = streetCoords.get(norm);
                        if (l == null) { l = new ArrayList<>(); streetCoords.put(norm, l); }
                        l.add(new double[]{n.getLat(), n.getLon()});
                    }
                }

                // b) civici degli EDIFICI (coordinate del primo nodo del way)
                String[] wc = civicWayNodes.get(id);
                if (wc != null) addCivic(civicRows, civicSeen, wc[0], wc[1], n.getLat(), n.getLon());

                // c) civici mappati direttamente come nodo
                String hn = n.getTag("addr:housenumber", null);
                if (hn != null && !hn.isEmpty()) {
                    String street = firstNonNull(n.getTag("addr:street", null), "");
                    if (!street.isEmpty())
                        addCivic(civicRows, civicSeen, street, hn, n.getLat(), n.getLon());
                }

                // d) nodi "place": servono per assegnare la citta' alle vie
                String place = n.getTag("place", null);
                if (place != null) {
                    String pname = n.getTag("name", null);
                    double weight = placeWeight(place);
                    if (pname != null && !pname.isEmpty() && weight > 0)
                        places.add(new Object[]{pname, weight, n.getLat(), n.getLon()});
                }
            }
        }
        civicWayNodes.clear(); nodeToNames.clear();

        PlaceGrid grid = new PlaceGrid(places);

        // --- Scrittura indice V2 ---
        indexOut.getParentFile().mkdirs();
        int streetRows = 0;
        try (BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(indexOut), "UTF-8"))) {
            bw.write(INDEX_HEADER); bw.newLine();
            for (Map.Entry<String, ArrayList<double[]>> e : streetCoords.entrySet()) {
                String display = streetDisplay.get(e.getKey());
                if (display == null) continue;
                // dedup spaziale: un punto per paese (segmenti a <1.5 km si fondono)
                ArrayList<double[]> kept = spatialDedup(e.getValue(), 1500, 60);
                for (double[] c : kept) {
                    String city = grid.nearestCity(c[0], c[1]);
                    bw.write("S\t" + safe(display) + "\t" + safe(city)
                        + "\t" + c[0] + "\t" + c[1]);
                    bw.newLine();
                    streetRows++;
                }
            }
            for (String[] h : civicRows) {
                bw.write("H\t" + safe(h[0]) + "\t" + safe(h[1]) + "\t" + h[2] + "\t" + h[3]);
                bw.newLine();
            }
        }
        Log.d(TAG, "Indice V2: " + streetRows + " voci via, " + civicRows.size() + " civici");
    }

    private static void addCivic(ArrayList<String[]> rows, HashSet<String> seen,
            String street, String num, double lat, double lon) {
        // dedup: stesso via+numero entro ~50 m e' lo stesso civico
        String key = normalize(street) + "|" + normalize(num) + "|"
            + Math.round(lat * 2000) + "|" + Math.round(lon * 2000);
        if (!seen.add(key)) return;
        rows.add(new String[]{street, num, String.valueOf(lat), String.valueOf(lon)});
    }

    private static double placeWeight(String place) {
        // peso < 1 = preferito anche se un po' piu' lontano
        switch (place) {
            case "city":    return 0.30;
            case "town":    return 0.55;
            case "village": return 1.0;
            case "suburb":  return 1.2;
            case "hamlet":  return 1.3;
            default:        return 0;
        }
    }

    /** Tiene solo punti distanti almeno minDistM l'uno dall'altro (max maxKeep). */
    private static ArrayList<double[]> spatialDedup(ArrayList<double[]> pts,
            double minDistM, int maxKeep) {
        ArrayList<double[]> kept = new ArrayList<>();
        for (double[] p : pts) {
            boolean far = true;
            for (double[] k : kept) {
                if (approxDistM(p[0], p[1], k[0], k[1]) < minDistM) { far = false; break; }
            }
            if (far) { kept.add(p); if (kept.size() >= maxKeep) break; }
        }
        return kept;
    }

    /** Distanza approssimata in metri (equirettangolare: veloce, basta per noi). */
    private static double approxDistM(double lat1, double lon1, double lat2, double lon2) {
        double dLat = (lat2 - lat1) * 111320.0;
        double dLon = (lon2 - lon1) * 111320.0 * Math.cos(Math.toRadians((lat1 + lat2) / 2));
        return Math.sqrt(dLat * dLat + dLon * dLon);
    }

    /** Griglia dei nodi place per trovare la citta' piu' vicina velocemente. */
    private static final class PlaceGrid {
        private static final double CELL = 0.25;   // ~25 km
        private final HashMap<Long, ArrayList<Object[]>> cells = new HashMap<>();
        PlaceGrid(ArrayList<Object[]> places) {
            for (Object[] p : places) {
                long key = cellKey((int) Math.floor((double) p[2] / CELL),
                                   (int) Math.floor((double) p[3] / CELL));
                ArrayList<Object[]> l = cells.get(key);
                if (l == null) { l = new ArrayList<>(); cells.put(key, l); }
                l.add(p);
            }
        }
        private static long cellKey(int cy, int cx) {
            return (((long) cy) << 32) | (cx & 0xffffffffL);
        }
        String nearestCity(double lat, double lon) {
            String best = ""; double bestScore = Double.MAX_VALUE;
            int cy = (int) Math.floor(lat / CELL), cx = (int) Math.floor(lon / CELL);
            for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) {
                ArrayList<Object[]> l = cells.get(cellKey(cy + dy, cx + dx));
                if (l == null) continue;
                for (Object[] p : l) {
                    double d = approxDistM(lat, lon, (double) p[2], (double) p[3]);
                    if (d > 25000) continue;             // oltre 25 km non ha senso
                    double score = d * (double) p[1];    // preferisci citta'/paesi grandi
                    if (score < bestScore) { bestScore = score; best = (String) p[0]; }
                }
            }
            return best;
        }
    }

    @WorkerThread
    private void loadIndex(File indexFile) throws IOException {
        streets.clear(); civics.clear(); civicTotal = 0;
        HashMap<String, String> intern = new HashMap<>();   // condivide i nomi via ripetuti
        try (BufferedReader br = new BufferedReader(new InputStreamReader(
                new FileInputStream(indexFile), "UTF-8"))) {
            String line = br.readLine();
            if (!INDEX_HEADER.equals(line)) throw new IOException("Indice non valido");
            while ((line = br.readLine()) != null) {
                String[] p = line.split("\t", -1);
                if (p.length < 5) continue;
                try {
                    double lat = Double.parseDouble(p[3]);
                    double lon = Double.parseDouble(p[4]);
                    if ("S".equals(p[0])) {
                        streets.add(new Entry("S", p[1], p[2], lat, lon));
                    } else if ("H".equals(p[0])) {
                        String street = intern.get(p[1]);
                        if (street == null) { intern.put(p[1], p[1]); street = p[1]; }
                        String norm = normalize(street);
                        CivicGroup g = civics.get(norm);
                        if (g == null) { g = new CivicGroup(street); civics.put(norm, g); }
                        g.list.add(new Civic(p[2], (float) lat, (float) lon));
                        civicTotal++;
                    }
                } catch (NumberFormatException ignored) {}
            }
        }
    }

    /**
     * Ricerca: "via roma" -> tutte le "Via Roma" (una per citta');
     * "via roma 10" o "via roma 10, milano" -> il civico 10 di quella via.
     * Ordine: esatto > inizia-con > contiene > fuzzy (errori di battitura).
     */
    @NonNull
    public List<Entry> search(@NonNull String query, int maxResults) {
        List<Entry> out = new ArrayList<>();
        if (query.trim().isEmpty() || streets.isEmpty()) return out;
        String q = normalize(query);

        // citta' dopo la virgola: "via roma 10, milano"
        String qCity = "";
        int comma = q.indexOf(',');
        if (comma > 0) { qCity = q.substring(comma + 1).trim(); q = q.substring(0, comma).trim(); }

        // civico alla fine: "via roma 10" / "via roma 10/b" / "via roma 12a"
        String qNum = null;
        int lastSpace = q.lastIndexOf(' ');
        if (lastSpace > 0) {
            String tail = q.substring(lastSpace + 1);
            if (tail.matches("\\d{1,4}[a-z]?(/\\w{1,3})?")) {
                qNum = tail;
                q = q.substring(0, lastSpace).trim();
            }
        }
        if (q.isEmpty()) return out;
        final String fq = q, fCity = qCity;

        List<Entry> exact = new ArrayList<>(), starts = new ArrayList<>(),
                    contains = new ArrayList<>(), fuzzy = new ArrayList<>();
        for (Entry e : streets) {
            if (!fCity.isEmpty() && !normalize(e.city).contains(fCity)) continue;
            String n = e.normName;
            if (n.equals(fq)) exact.add(e);
            else if (n.startsWith(fq)) starts.add(e);
            else if (n.contains(fq)) contains.add(e);
        }
        // Il fuzzy (distanza di edit) e' costoso: solo se serve davvero.
        int found = exact.size() + starts.size() + contains.size();
        if (found < maxResults && fq.length() >= 4) {
            for (Entry e : streets) {
                if (!fCity.isEmpty() && !normalize(e.city).contains(fCity)) continue;
                String n = e.normName;
                if (n.equals(fq) || n.startsWith(fq) || n.contains(fq)) continue;
                if (editDistanceWithin(n, fq, 2)) {
                    fuzzy.add(e);
                    if (fuzzy.size() >= maxResults) break;
                }
            }
        }
        List<Entry> ranked = new ArrayList<>();
        addAll(ranked, exact, 200); addAll(ranked, starts, 200);
        addAll(ranked, contains, 200); addAll(ranked, fuzzy, 200);

        if (qNum == null) {
            // senza civico: una voce per via+citta' (niente doppioni)
            HashSet<String> seen = new HashSet<>();
            for (Entry e : ranked) {
                if (out.size() >= maxResults) break;
                if (seen.add(e.normName + "|" + normalize(e.city))) out.add(e);
            }
            return out;
        }

        // con civico: per ogni via trovata cerca il numero in QUELLA zona
        String normNum = normalize(qNum);
        HashSet<String> seenOut = new HashSet<>();
        for (Entry st : ranked) {
            if (out.size() >= maxResults) break;
            CivicGroup g = civics.get(st.normName);
            if (g == null) continue;
            Civic best = findCivic(g, normNum, st.lat, st.lon, true);
            if (best == null) best = findCivic(g, normNum, st.lat, st.lon, false);
            if (best == null) continue;
            String label = st.name + " " + best.num;
            if (seenOut.add(normalize(label) + "|" + normalize(st.city)
                    + "|" + Math.round(best.lat * 10000)))
                out.add(new Entry("H", label, st.city, best.lat, best.lon));
        }
        // nessun civico trovato: mostra almeno le vie
        if (out.isEmpty()) {
            HashSet<String> seen = new HashSet<>();
            for (Entry e : ranked) {
                if (out.size() >= maxResults) break;
                if (seen.add(e.normName + "|" + normalize(e.city))) out.add(e);
            }
        }
        return out;
    }

    /** Il civico giusto e' quello (esatto o per prefisso) piu' vicino alla via. */
    @Nullable
    private static Civic findCivic(CivicGroup g, String normNum,
            double lat, double lon, boolean exactMatch) {
        Civic best = null; double bestD = Double.MAX_VALUE;
        for (Civic c : g.list) {
            String cn = normalize(c.num);
            boolean match = exactMatch ? cn.equals(normNum) : cn.startsWith(normNum);
            if (!match) continue;
            double d = approxDistM(lat, lon, c.lat, c.lon);
            if (d > 4000 || d >= bestD) continue;   // il civico deve stare vicino alla via
            best = c; bestD = d;
        }
        return best;
    }

    private void addAll(List<Entry> out, List<Entry> src, int max) {
        for (Entry e : src) { if (out.size() >= max) return; out.add(e); }
    }

    public static String normalize(String s) {
        if (s == null) return "";
        String n = Normalizer.normalize(s, Normalizer.Form.NFD)
            .replaceAll("\\p{InCombiningDiacriticalMarks}+", "");
        return n.toLowerCase(Locale.ROOT).trim().replaceAll("\\s+", " ");
    }

    /** Distanza di edit (Levenshtein) con cutoff: true se <= maxDist. */
    private static boolean editDistanceWithin(String a, String b, int maxDist) {
        int la = a.length(), lb = b.length();
        if (Math.abs(la - lb) > maxDist) return false;
        int[] prev = new int[lb + 1];
        int[] cur  = new int[lb + 1];
        for (int j = 0; j <= lb; j++) prev[j] = j;
        for (int i = 1; i <= la; i++) {
            cur[0] = i;
            int rowMin = cur[0];
            char ca = a.charAt(i - 1);
            for (int j = 1; j <= lb; j++) {
                int cost = (ca == b.charAt(j - 1)) ? 0 : 1;
                cur[j] = Math.min(Math.min(prev[j] + 1, cur[j - 1] + 1), prev[j - 1] + cost);
                rowMin = Math.min(rowMin, cur[j]);
            }
            if (rowMin > maxDist) return false;
            int[] t = prev; prev = cur; cur = t;
        }
        return prev[lb] <= maxDist;
    }

    private static String firstNonNull(String... v) {
        for (String s : v) if (s != null && !s.isEmpty()) return s;
        return "";
    }
    private static String safe(String s) { return s == null ? "" : s.replace("\t", " "); }

    public void clear() {
        streets.clear(); civics.clear(); civicTotal = 0; loadedRegionTag = null;
    }
}
"""

# ============================================================
#  METEO A DESTINAZIONE — Open-Meteo (gratuito, senza API key).
#  Richiede INTERNET: se offline, degrada silenziosamente.
# ============================================================
WEATHER_SERVICE = r"""package com.offlinegps.map.routing;

import android.util.Log;
import androidx.annotation.*;
import org.json.JSONObject;
import java.io.*;
import java.net.*;

/**
 * Meteo on-demand via Open-Meteo. NB: richiede connessione internet.
 * Se non c'e' rete, onResult viene chiamato con null e l'app continua
 * normalmente (il meteo e' un extra, non blocca la navigazione offline).
 */
public final class WeatherService {
    private static final String TAG = "WeatherService";

    public static final class Weather {
        public final double tempC;
        public final int code;        // weather code Open-Meteo
        public final double windKmh;
        public Weather(double tempC, int code, double windKmh) {
            this.tempC = tempC; this.code = code; this.windKmh = windKmh;
        }
        public String description() { return codeToText(code); }
        public String emoji() { return codeToEmoji(code); }
    }

    public interface Callback { void onResult(@Nullable Weather w); }

    /** Recupera il meteo per lat/lon su un thread in background. */
    public static void fetch(double lat, double lon, @NonNull Callback cb) {
        new Thread(() -> {
            Weather w = null;
            HttpURLConnection conn = null;
            try {
                String url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat
                    + "&longitude=" + lon
                    + "&current=temperature_2m,weather_code,wind_speed_10m";
                conn = (HttpURLConnection) new URL(url).openConnection();
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                conn.setRequestMethod("GET");
                int rc = conn.getResponseCode();
                if (rc == 200) {
                    StringBuilder sb = new StringBuilder();
                    try (BufferedReader br = new BufferedReader(
                            new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
                        String line;
                        while ((line = br.readLine()) != null) sb.append(line);
                    }
                    JSONObject root = new JSONObject(sb.toString());
                    JSONObject cur  = root.getJSONObject("current");
                    w = new Weather(cur.optDouble("temperature_2m", Double.NaN),
                        cur.optInt("weather_code", -1),
                        cur.optDouble("wind_speed_10m", 0));
                }
            } catch (Exception e) {
                Log.d(TAG, "Meteo non disponibile (offline?): " + e.getMessage());
            } finally {
                if (conn != null) conn.disconnect();
            }
            final Weather result = w;
            new android.os.Handler(android.os.Looper.getMainLooper()).post(() -> cb.onResult(result));
        }).start();
    }

    private static String codeToText(int c) {
        if (c == 0) return "Sereno";
        if (c <= 2) return "Poco nuvoloso";
        if (c == 3) return "Nuvoloso";
        if (c >= 45 && c <= 48) return "Nebbia";
        if (c >= 51 && c <= 67) return "Pioggia";
        if (c >= 71 && c <= 77) return "Neve";
        if (c >= 80 && c <= 82) return "Rovesci";
        if (c >= 95) return "Temporale";
        return "Meteo";
    }
    private static String codeToEmoji(int c) {
        if (c == 0) return "[Sole]";
        if (c <= 3) return "[Nubi]";
        if (c >= 45 && c <= 48) return "[Nebbia]";
        if (c >= 51 && c <= 67) return "[Pioggia]";
        if (c >= 71 && c <= 77) return "[Neve]";
        if (c >= 80 && c <= 82) return "[Rovesci]";
        if (c >= 95) return "[Temporale]";
        return "[Meteo]";
    }
}
"""

# ============================================================
#  STUB javax.lang.model.SourceVersion (FIX CRASH)
#  GraphHopper usa SourceVersion.isName() per validare i nomi dei
#  campi, ma questa classe del JDK NON esiste su Android, quindi
#  importOrLoad() crasha con NoClassDefFoundError. Forniamo noi una
#  versione minima compatibile.
# ============================================================
SOURCE_VERSION_STUB = r"""package javax.lang.model;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Implementazione minima di javax.lang.model.SourceVersion per Android.
 * Android non include questa classe del JDK; GraphHopper la richiede solo
 * per validare nomi di EncodedValue. Forniamo i metodi usati.
 */
public class SourceVersion {

    public static boolean isName(CharSequence name) { return isName(name, null); }

    public static boolean isName(CharSequence name, SourceVersion version) {
        String id = name.toString();
        if (id.isEmpty()) return false;
        // ammette nomi composti con punti: a.b.c
        for (String part : id.split("\\.", -1)) {
            if (!isIdentifierToken(part)) return false;
        }
        return true;
    }

    public static boolean isIdentifier(CharSequence name) {
        return isIdentifierToken(name.toString());
    }

    public static boolean isKeyword(CharSequence s) { return KEYWORDS.contains(s.toString()); }
    public static boolean isKeyword(CharSequence s, SourceVersion version) { return isKeyword(s); }

    private static boolean isIdentifierToken(String id) {
        if (id.isEmpty()) return false;
        if (!Character.isJavaIdentifierStart(id.charAt(0))) return false;
        for (int i = 1; i < id.length(); i++) {
            if (!Character.isJavaIdentifierPart(id.charAt(i))) return false;
        }
        return !KEYWORDS.contains(id);
    }

    private static final Set<String> KEYWORDS;
    static {
        Set<String> k = new HashSet<>();
        String[] words = {
            "abstract","assert","boolean","break","byte","case","catch","char",
            "class","const","continue","default","do","double","else","enum",
            "extends","final","finally","float","for","goto","if","implements",
            "import","instanceof","int","interface","long","native","new","package",
            "private","protected","public","return","short","static","strictfp",
            "super","switch","synchronized","this","throw","throws","transient",
            "try","void","volatile","while","true","false","null","_"
        };
        Collections.addAll(k, words);
        KEYWORDS = Collections.unmodifiableSet(k);
    }

    // enum minimale richiesto da alcune firme (non usato attivamente)
    public enum RELEASE_VERSION { RELEASE_0, RELEASE_8, RELEASE_11, RELEASE_17 }
    public static RELEASE_VERSION latest() { return RELEASE_VERSION.RELEASE_17; }
}
"""

HUD_VIEW = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.graphics.*;
import android.location.Location;
import android.util.AttributeSet;
import android.view.View;
import androidx.annotation.*;
import com.offlinegps.map.AppConfig;
import java.util.ArrayDeque;

public class HudView extends View {

    private final Paint bgPaint     = new Paint();
    private final Paint gridPaint   = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint labelPaint  = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint valuePaint  = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint accentPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint dangerPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint dimPaint    = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint compassRing = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint needleN     = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint needleS     = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint altPaint    = new Paint(Paint.ANTI_ALIAS_FLAG);
    private LinearGradient barGrad;

    private double lat, lon, alt;
    private float  acc, speedKmh, bearing, azimuth;
    private int    satellites;
    private boolean hasfix;

    private final ArrayDeque<Float> altHistory = new ArrayDeque<>();
    private static final int ALT_HISTORY_SIZE = 80;

    public HudView(Context ctx) { super(ctx); init(); }
    public HudView(Context ctx, @Nullable AttributeSet a) { super(ctx, a); init(); }

    private void init() {
        bgPaint.setColor(0xEE050A14);
        gridPaint.setColor(0x0A00E5FF); gridPaint.setStrokeWidth(1f); gridPaint.setStyle(Paint.Style.STROKE);
        labelPaint.setColor(AppConfig.COLOR_TEXT_DIM); labelPaint.setTextSize(19f); labelPaint.setTypeface(Typeface.MONOSPACE);
        valuePaint.setColor(AppConfig.COLOR_PRIMARY); valuePaint.setTextSize(28f); valuePaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
        accentPaint.setColor(AppConfig.COLOR_SECONDARY); accentPaint.setTextSize(28f); accentPaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
        dangerPaint.setColor(AppConfig.COLOR_DANGER); dangerPaint.setTextSize(26f); dangerPaint.setTypeface(Typeface.MONOSPACE);
        dimPaint.setColor(AppConfig.COLOR_TEXT_DIM); dimPaint.setTextSize(18f); dimPaint.setTypeface(Typeface.MONOSPACE);
        compassRing.setColor(AppConfig.COLOR_PRIMARY); compassRing.setStyle(Paint.Style.STROKE); compassRing.setStrokeWidth(2f);
        needleN.setColor(AppConfig.COLOR_DANGER); needleN.setStyle(Paint.Style.FILL);
        needleS.setColor(AppConfig.COLOR_SECONDARY); needleS.setStyle(Paint.Style.FILL);
        altPaint.setColor(AppConfig.COLOR_ACCENT); altPaint.setStyle(Paint.Style.STROKE); altPaint.setStrokeWidth(2.5f);
    }

    public void update(@NonNull Location loc, float az, int sats) {
        lat = loc.getLatitude(); lon = loc.getLongitude(); alt = loc.getAltitude();
        acc = loc.getAccuracy(); speedKmh = loc.getSpeed() * 3.6f;
        bearing = loc.getBearing(); azimuth = az; satellites = sats; hasfix = true;
        altHistory.addLast((float) alt);
        if (altHistory.size() > ALT_HISTORY_SIZE) altHistory.removeFirst();
        invalidate();
    }

    public void setNoFix() { hasfix = false; invalidate(); }

    @Override protected void onDraw(@NonNull Canvas canvas) {
        int W = getWidth(), H = getHeight();
        canvas.drawRect(0, 0, W, H, bgPaint);
        drawGrid(canvas, W, H);
        if (barGrad == null) barGrad = new LinearGradient(0, 0, W, 0,
            new int[]{0x00050A14, AppConfig.COLOR_PRIMARY, AppConfig.COLOR_SECONDARY, 0x00050A14},
            new float[]{0f, 0.3f, 0.7f, 1f}, Shader.TileMode.CLAMP);
        Paint barP = new Paint(); barP.setShader(barGrad); barP.setStrokeWidth(2f);
        canvas.drawLine(0, 2, W, 2, barP);
        if (!hasfix) { drawNoFix(canvas, W, H); return; }
        float x1 = 16f, x2 = W * 0.40f, x3 = W * 0.68f;
        float rowH = H / 4.2f;
        draw2(canvas, "LAT", String.format("%.6f", lat), valuePaint, x1, rowH * 0.7f);
        draw2(canvas, "LON", String.format("%.6f", lon), valuePaint, x1, rowH * 1.55f);
        draw2(canvas, "ALT", String.format("%.1f m", alt), valuePaint, x1, rowH * 2.4f);
        Paint precP = acc <= 8 ? accentPaint : (acc <= 20 ? valuePaint : dangerPaint);
        canvas.drawText("PREC", x1, rowH * 3.05f, labelPaint);
        canvas.drawText(String.format("+/-%.0f m", acc), x1, rowH * 3.45f, precP);
        canvas.drawText("VEL", x2, rowH * 0.7f - 20f, labelPaint);
        Paint spdP = new Paint(accentPaint); spdP.setTextSize(62f);
        canvas.drawText(String.format("%.0f", speedKmh), x2, rowH * 0.7f + 48f, spdP);
        canvas.drawText("km/h", x2, rowH * 0.7f + 72f, dimPaint);
        Paint satP = satellites >= 4 ? accentPaint : dangerPaint;
        canvas.drawText("SAT", x2, rowH * 1.8f, labelPaint);
        canvas.drawText(String.valueOf(satellites), x2, rowH * 2.25f, satP);
        canvas.drawText("ROTTA", x2, rowH * 2.8f, labelPaint);
        canvas.drawText(String.format("%.0f %s", bearing, bearingStr(bearing)), x2, rowH * 3.25f, valuePaint);
        float cx = x3 + 50f, cy = H * 0.42f, r = Math.min(W * 0.13f, 52f);
        drawCompass(canvas, cx, cy, r);
        drawAltProfile(canvas, x1, H * 0.82f, W - 24f, H - 14f);
    }

    private void draw2(Canvas c, String label, String val, Paint vp, float x, float y) {
        c.drawText(label, x, y, labelPaint);
        c.drawText(val, x, y + 26f, vp);
    }

    private void drawGrid(Canvas c, int W, int H) {
        int step = 48;
        for (int x = 0; x < W; x += step) c.drawLine(x, 0, x, H, gridPaint);
        for (int y = 0; y < H; y += step) c.drawLine(0, y, W, y, gridPaint);
        Paint bp = new Paint(valuePaint); bp.setStyle(Paint.Style.STROKE); bp.setStrokeWidth(2.5f);
        int bs = 18;
        c.drawLine(4, 4, 4+bs, 4, bp); c.drawLine(4, 4, 4, 4+bs, bp);
        c.drawLine(W-4, 4, W-4-bs, 4, bp); c.drawLine(W-4, 4, W-4, 4+bs, bp);
        c.drawLine(4, H-4, 4+bs, H-4, bp); c.drawLine(4, H-4, 4, H-4-bs, bp);
        c.drawLine(W-4, H-4, W-4-bs, H-4, bp); c.drawLine(W-4, H-4, W-4, H-4-bs, bp);
    }

    private void drawCompass(Canvas c, float cx, float cy, float r) {
        Paint glow = new Paint(compassRing); glow.setColor(0x3300E5FF); glow.setStrokeWidth(8f);
        c.drawCircle(cx, cy, r + 2, glow);
        c.drawCircle(cx, cy, r, compassRing);
        Paint tick = new Paint(); tick.setColor(0x6600E5FF); tick.setStrokeWidth(1.5f);
        for (int i = 0; i < 36; i++) {
            double a = Math.toRadians(i * 10);
            float inner = (i % 9 == 0) ? r - 12f : r - 7f;
            c.drawLine((float)(cx + Math.sin(a)*inner), (float)(cy - Math.cos(a)*inner),
                       (float)(cx + Math.sin(a)*r), (float)(cy - Math.cos(a)*r), tick);
        }
        c.save(); c.rotate(-azimuth, cx, cy);
        Path north = new Path();
        north.moveTo(cx, cy - r + 8); north.lineTo(cx - 7, cy + 4); north.lineTo(cx + 7, cy + 4); north.close();
        c.drawPath(north, needleN);
        Path south = new Path();
        south.moveTo(cx, cy + r - 8); south.lineTo(cx - 7, cy - 4); south.lineTo(cx + 7, cy - 4); south.close();
        c.drawPath(south, needleS);
        c.restore();
        Paint center = new Paint(Paint.ANTI_ALIAS_FLAG); center.setColor(AppConfig.COLOR_TEXT);
        c.drawCircle(cx, cy, 4f, center);
        Paint np = new Paint(labelPaint); np.setTextSize(16f); np.setColor(AppConfig.COLOR_DANGER);
        c.drawText("N", cx - 6f, cy - r + 22f, np);
    }

    private void drawAltProfile(Canvas c, float left, float top, float right, float bottom) {
        if (altHistory.size() < 2) return;
        float H = bottom - top;
        float[] alts = new float[altHistory.size()];
        int i = 0; float minA = Float.MAX_VALUE, maxA = -Float.MAX_VALUE;
        for (float a : altHistory) { alts[i++] = a; minA = Math.min(minA, a); maxA = Math.max(maxA, a); }
        float range = Math.max(maxA - minA, 1f);
        Paint lp = new Paint(dimPaint); lp.setTextSize(15f); lp.setColor(AppConfig.COLOR_ACCENT);
        c.drawText(String.format("ALT: %.0f / %.0f  d%.0fm", maxA, minA, range), left, top - 3f, lp);
        float stepX = (right - left) / (alts.length - 1f);
        Path path = new Path();
        for (int j = 0; j < alts.length; j++) {
            float x = left + j * stepX;
            float y = bottom - ((alts[j] - minA) / range) * H;
            if (j == 0) path.moveTo(x, y); else path.lineTo(x, y);
        }
        c.drawPath(path, altPaint);
        float lastX = left + (alts.length - 1) * stepX;
        float lastY = bottom - ((alts[alts.length-1] - minA) / range) * H;
        Paint dot = new Paint(Paint.ANTI_ALIAS_FLAG); dot.setColor(AppConfig.COLOR_ACCENT);
        c.drawCircle(lastX, lastY, 5f, dot);
    }

    private void drawNoFix(Canvas c, int W, int H) {
        Paint p = new Paint(dangerPaint); p.setTextSize(34f); p.setTextAlign(Paint.Align.CENTER);
        c.drawText("SEGNALE GPS ASSENTE", W/2f, H/2f - 16f, p);
        Paint sp = new Paint(dimPaint); sp.setTextSize(22f); sp.setTextAlign(Paint.Align.CENTER);
        c.drawText("In attesa satelliti...", W/2f, H/2f + 24f, sp);
    }

    private String bearingStr(float b) {
        String[] d = {"N","NE","E","SE","S","SO","O","NO"};
        return d[Math.round(b / 45f) % 8];
    }
}
"""

REGION_MAPPER = r"""package com.offlinegps.map.ui;

import androidx.annotation.Nullable;

final class RegionMapper {
    private RegionMapper() {}

    private static final Object[][] BOXES = {
        {"isole",      36.5, 39.3,  7.8, 15.7},
        {"sud",        39.0, 42.3, 13.0, 18.6},
        {"centro",     41.0, 44.2, 10.0, 14.2},
        {"nord-ovest", 43.4, 46.7,  6.5, 11.2},
        {"nord-est",   43.6, 47.1, 10.0, 14.0},
    };

    @Nullable
    static String tagFor(double lat, double lon) {
        for (Object[] box : BOXES) {
            double minLat = (double) box[1], maxLat = (double) box[2];
            double minLon = (double) box[3], maxLon = (double) box[4];
            if (lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon) {
                return (String) box[0];
            }
        }
        return null;
    }
}
"""

# ============================================================
#  ADDRESS SEARCH ACTIVITY — ricerca indirizzo offline
# ============================================================
ADDRESS_SEARCH_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.os.*;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.*;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.offlinegps.map.R;
import com.offlinegps.map.data.*;
import com.offlinegps.map.gps.GpsTrackingService;
import com.offlinegps.map.routing.OfflineGeocoder;
import com.offlinegps.map.routing.RoutingEngine;
import java.io.File;
import java.util.*;
import java.util.concurrent.*;

/**
 * Ricerca indirizzo offline. Restituisce alla NavigationActivity le coordinate
 * scelte. Se l'indice geocoding non e' ancora pronto, prova a costruirlo dalla
 * regione corrispondente alla posizione GPS attuale.
 */
public class AddressSearchActivity extends AppCompatActivity {
    public static final String EXTRA_PROFILE = "profile";
    private EditText etQuery;
    private RecyclerView rvResults;
    private TextView tvHint;
    private ProgressBar pbLoad;
    private ResultAdapter adapter;
    private String profile = RoutingEngine.PROFILE_CAR;
    private final ExecutorService exec = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Handler debounce = new Handler(Looper.getMainLooper());
    private Runnable pendingSearch;

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_address_search);
        String p = getIntent().getStringExtra(EXTRA_PROFILE);
        if (p != null) profile = p;

        etQuery   = findViewById(R.id.et_addr_query);
        rvResults = findViewById(R.id.rv_addr_results);
        tvHint    = findViewById(R.id.tv_addr_hint);
        pbLoad    = findViewById(R.id.pb_addr_load);
        ImageButton btnBack = findViewById(R.id.btn_addr_back);
        if (btnBack != null) btnBack.setOnClickListener(v -> finish());

        adapter = new ResultAdapter();
        rvResults.setLayoutManager(new LinearLayoutManager(this));
        rvResults.setAdapter(adapter);

        etQuery.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void afterTextChanged(Editable e) { scheduleSearch(e.toString()); }
        });

        ensureGeocoderReady();
    }

    /** Costruisce l'indice da QUALSIASI .pbf scaricato (non dipende dal GPS). */
    private void ensureGeocoderReady() {
        if (OfflineGeocoder.getInstance().isReady()) {
            setHint("Scrivi una via o un civico, es. Via Roma 10");
            return;
        }
        File pbf = pickAvailablePbf();
        if (pbf == null) {
            setHint("Nessun dato ROUTING trovato. Vai in Download -> tab ROUTING.");
            return;
        }
        buildIndexFor(pbf);
    }

    /** Cerca un .pbf scaricato: prima quello della zona GPS, poi qualsiasi altro. */
    @Nullable
    private File pickAvailablePbf() {
        File routingDir = new File(getExternalFilesDir(null), "routing");
        if (!routingDir.exists()) return null;

        // 1) prova la regione della posizione GPS attuale (se disponibile)
        android.location.Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) {
            String region = RegionMapper.tagFor(loc.getLatitude(), loc.getLongitude());
            if (region != null) {
                File p = new File(routingDir, region + ".osm.pbf");
                if (p.exists()) return p;
            }
        }
        // 2) altrimenti il primo .pbf presente nella cartella
        File[] files = routingDir.listFiles((d, n) -> n.endsWith(".pbf"));
        if (files != null && files.length > 0) return files[0];
        return null;
    }

    /** Ricava il tag regione dal nome file (es. "centro.osm.pbf" -> "centro"). */
    private String regionTagFromFile(File pbf) {
        String n = pbf.getName();
        int dot = n.indexOf('.');
        return dot > 0 ? n.substring(0, dot) : n;
    }

    private void buildIndexFor(File pbf) {
        final String region = regionTagFromFile(pbf);
        File idx = new File(pbf.getParentFile(), region + "-geo.idx");
        long sizeMb = pbf.length() / (1024 * 1024);
        if (sizeMb < 1) {
            setHint("File " + pbf.getName() + " troppo piccolo (" + pbf.length()
                + " byte): download incompleto. Riscaricalo da Download.");
            return;
        }
        showLoading(true);
        setHint("Preparazione indice per " + region + " (" + sizeMb
            + " MB, prima volta - puo' richiedere 1-2 min, attendi)...");
        exec.execute(() -> {
            OfflineGeocoder.getInstance().loadOrBuild(pbf, idx, region, null);
            main.post(() -> {
                showLoading(false);
                if (OfflineGeocoder.getInstance().isReady()) {
                    setHint("Pronto: " + OfflineGeocoder.getInstance().streetCount()
                        + " vie e " + OfflineGeocoder.getInstance().civicCount()
                        + " civici. Prova: Via Roma 10");
                    if (etQuery != null && etQuery.getText().length() >= 2)
                        doSearch(etQuery.getText().toString());
                } else {
                    String err = OfflineGeocoder.getInstance().getLastError();
                    setHint(err != null ? ("Errore indice: " + err)
                        : ("Impossibile costruire l'indice per " + region + "."));
                }
            });
        });
    }

    private void scheduleSearch(String q) {
        if (pendingSearch != null) debounce.removeCallbacks(pendingSearch);
        pendingSearch = () -> doSearch(q);
        debounce.postDelayed(pendingSearch, 180);
    }

    private void doSearch(String q) {
        final String query = q.trim();
        if (query.length() < 2) { adapter.submit(new ArrayList<>()); return; }
        exec.execute(() -> {
            List<Result> results = new ArrayList<>();

            // 1) waypoint salvati che contengono la query
            try {
                List<WaypointEntity> wps = GpsDatabase.getInstance(getApplicationContext())
                    .waypointDao().getAllSync();
                String nq = OfflineGeocoder.normalize(query);
                for (WaypointEntity w : wps) {
                    if (OfflineGeocoder.normalize(w.name).contains(nq)) {
                        results.add(new Result(w.name, w.latitude, w.longitude, "W"));
                    }
                }
            } catch (Exception ignored) {}

            // 2) vie e civici dall'indice geocoding
            List<OfflineGeocoder.Entry> hits = OfflineGeocoder.getInstance().search(query, 50);
            for (OfflineGeocoder.Entry e : hits) {
                String label = e.name;
                if (e.city != null && !e.city.isEmpty()) label += ", " + e.city;
                String kind = e.isHouseNumber() ? "H" : "S";
                results.add(new Result(label, e.lat, e.lon, kind));
            }

            main.post(() -> {
                adapter.submit(results);
                if (!results.isEmpty()) { setHint(results.size() + " risultati"); return; }
                if (OfflineGeocoder.getInstance().isReady()) {
                    setHint("Nessun risultato per \"" + query + "\"");
                } else {
                    // indice non pronto: prova a costruirlo ora se c'e' un .pbf
                    File pbf = pickAvailablePbf();
                    if (pbf != null) buildIndexFor(pbf);
                    else setHint("Indice non pronto: scarica i dati ROUTING.");
                }
            });
        });
    }

    /** Mostra anteprima del risultato con opzione "Vedi su mappa" o "Naviga". */
    private void previewResult(Result r) {
        String tipo = r.isWaypoint() ? "Waypoint" : (r.isHouse() ? "Civico" : "Via");
        String msg = r.label + "\n\n" + tipo + "\n"
            + String.format(Locale.US, "%.5f, %.5f", r.lat, r.lon);
        new android.app.AlertDialog.Builder(this)
            .setTitle("Conferma destinazione")
            .setMessage(msg)
            .setPositiveButton("Naviga", (d, w) -> navigateTo(r))
            .setNeutralButton("Vedi su mappa", (d, w) -> showOnMap(r))
            .setNegativeButton("Annulla", null)
            .show();
    }

    private void showOnMap(Result r) {
        Intent i = new Intent(this, MapActivity.class);
        i.putExtra(MapActivity.EXTRA_FOCUS_LAT, r.lat);
        i.putExtra(MapActivity.EXTRA_FOCUS_LON, r.lon);
        i.putExtra(MapActivity.EXTRA_FOCUS_LABEL, r.label);
        startActivity(i);
    }

    private void navigateTo(Result r) {
        // salva nella cronologia destinazioni recenti
        try {
            GpsDatabase.getInstance(getApplicationContext()).historyDao()
                .insert(new HistoryEntity(r.label, r.lat, r.lon, System.currentTimeMillis()));
        } catch (Exception ignored) {}
        Intent i = new Intent(this, NavigationActivity.class);
        i.putExtra(NavigationActivity.EXTRA_DEST_LAT, r.lat);
        i.putExtra(NavigationActivity.EXTRA_DEST_LON, r.lon);
        i.putExtra(NavigationActivity.EXTRA_DEST_NAME, r.label);
        i.putExtra(NavigationActivity.EXTRA_PROFILE, profile);
        startActivity(i);
        finish();
    }

    private void setHint(String msg) { if (tvHint != null) tvHint.setText(msg); }
    private void showLoading(boolean b) { if (pbLoad != null) pbLoad.setVisibility(b ? View.VISIBLE : View.GONE); }

    @Override protected void onDestroy() { super.onDestroy(); exec.shutdown(); }

    static final class Result {
        final String label; final double lat, lon; final String kind;  // "S","H","W"
        Result(String label, double lat, double lon, String kind) {
            this.label = label; this.lat = lat; this.lon = lon; this.kind = kind;
        }
        boolean isWaypoint() { return "W".equals(kind); }
        boolean isHouse() { return "H".equals(kind); }
    }

    class ResultAdapter extends RecyclerView.Adapter<ResultAdapter.VH> {
        final List<Result> data = new ArrayList<>();
        void submit(List<Result> r) { data.clear(); data.addAll(r); notifyDataSetChanged(); }
        @NonNull @Override public VH onCreateViewHolder(@NonNull ViewGroup p, int t) {
            return new VH(LayoutInflater.from(p.getContext()).inflate(R.layout.item_address_result, p, false));
        }
        @Override public void onBindViewHolder(@NonNull VH h, int pos) {
            Result r = data.get(pos);
            String icon = r.isWaypoint() ? "[*] " : (r.isHouse() ? "[#] " : "[>] ");
            h.title.setText(icon + r.label);
            h.sub.setText(String.format(Locale.US, "%.5f, %.5f", r.lat, r.lon));
            h.itemView.setOnClickListener(v -> previewResult(r));
        }
        @Override public int getItemCount() { return data.size(); }
        class VH extends RecyclerView.ViewHolder {
            TextView title, sub;
            VH(@NonNull View v) {
                super(v);
                title = v.findViewById(R.id.tv_addr_title);
                sub   = v.findViewById(R.id.tv_addr_sub);
            }
        }
    }
}
"""

SPLASH_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.animation.AnimationUtils;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Schermata di avvio 3D: anello neon rotante + logo che gira sull'asse Y. */
public class SplashActivity extends AppCompatActivity {
    private final Handler splashHandler = new Handler(Looper.getMainLooper());
    private Runnable goNext;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_splash);
        try {
            View logo = findViewById(R.id.splash_logo);
            View ring = findViewById(R.id.splash_ring);
            View title = findViewById(R.id.splash_title);
            View creator = findViewById(R.id.splash_creator);
            android.view.animation.Animation fadeIn =
                AnimationUtils.loadAnimation(this, android.R.anim.fade_in);
            fadeIn.setDuration(900);
            if (logo != null) {
                logo.startAnimation(fadeIn);
                // rotazione 3D vera attorno all'asse verticale (effetto ologramma)
                logo.animate().rotationY(360f).setDuration(1600)
                    .setStartDelay(200).start();
            }
            if (ring != null) {
                // anello neon che ruota all'infinito attorno al logo
                android.animation.ObjectAnimator spin =
                    android.animation.ObjectAnimator.ofFloat(ring, "rotation", 0f, 360f);
                spin.setDuration(3200);
                spin.setRepeatCount(android.animation.ValueAnimator.INFINITE);
                spin.setInterpolator(new android.view.animation.LinearInterpolator());
                spin.start();
            }
            if (title != null) title.startAnimation(fadeIn);
            if (creator != null) {
                android.view.animation.Animation fadeIn2 =
                    AnimationUtils.loadAnimation(this, android.R.anim.fade_in);
                fadeIn2.setDuration(900);
                fadeIn2.setStartOffset(700);
                creator.startAnimation(fadeIn2);
            }
        } catch (Exception ignored) {}
        // dopo 2.2s apre la Home (solo se l'activity e' ancora viva)
        goNext = () -> {
            if (isFinishing() || isDestroyed()) return;
            startActivity(new Intent(this, MainActivity.class));
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
            finish();
        };
        splashHandler.postDelayed(goNext, 2200);
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        splashHandler.removeCallbacksAndMessages(null);
    }
}
"""

MAIN_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.*;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.*;
import androidx.core.content.ContextCompat;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;
import com.offlinegps.map.routing.RoutingEngine;
import com.offlinegps.map.sky.SkyState;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.*;

/** HOME v4.0: aurora animata, radar 3D della Sentinella Cielo, chip di stato e riquadri. */
public class MainActivity extends AppCompatActivity implements SkyState.Listener {
    private final Handler clock = new Handler(Looper.getMainLooper());
    private final Runnable clockTick = new Runnable() {
        @Override public void run() { updateClock(); clock.postDelayed(this, 20_000); }
    };
    private SkyRadarView radar;

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_main);
        go(R.id.btn_open_map,  () -> { if (checkGps()) open(Map3DActivity.class); });
        go(R.id.btn_navigate,  () -> { if (checkGps()) showNavigateDialog(); });
        go(R.id.btn_download,  () -> open(DownloadActivity.class));
        go(R.id.btn_waypoints, () -> open(WaypointsActivity.class));
        go(R.id.btn_stats,     () -> open(StatsActivity.class));
        go(R.id.btn_tools,     () -> open(ToolsActivity.class));
        go(R.id.btn_survival,  () -> open(SurvivalActivity.class));
        go(R.id.btn_chat,      () -> open(ChatActivity.class));
        go(R.id.btn_emergency, () -> open(EmergencyActivity.class));
        go(R.id.btn_sky_watch, () -> open(SkyWatchActivity.class));
        go(R.id.btn_home_acoustic, () -> open(AcousticDetectorActivity.class));
        go(R.id.btn_home_check, () -> open(SightingCheckActivity.class));
        // i chip di stato portano dove si risolve il problema
        go(R.id.chip_gps,     () -> { if (!hasGpsPerm()) requestGps(); else open(MapActivity.class); });
        go(R.id.chip_map,     () -> open(DownloadActivity.class));
        go(R.id.chip_routing, () -> open(DownloadActivity.class));
        go(R.id.chip_service, () -> open(TrackRecorderActivity.class));
        radar = findViewById(R.id.home_radar);
        if (radar != null) {
            radar.setCompact(true);
            radar.setOnTrackTap(t -> open(SkyWatchActivity.class));
            radar.setOnClickListener(v -> open(SkyWatchActivity.class));
        }
        updateStatus();
        if (!hasGpsPerm()) requestGps();
    }

    private void go(int id, Runnable r) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(x -> r.run());
    }

    @Override protected void onResume() {
        super.onResume();
        updateStatus();
        SkyState.get().addListener(this);
        onSkyChanged();
        clock.post(clockTick);
    }

    @Override protected void onPause() {
        super.onPause();
        SkyState.get().removeListener(this);
        clock.removeCallbacks(clockTick);
    }

    @Override public void onSkyChanged() {
        SkyState st = SkyState.get();
        if (radar != null) {
            radar.setData(st.snapshot(), st.userLat, st.userLon);
            radar.setDemo(st.isDemo());
            radar.setAcoustic(st.acousticScore);
        }
        TextView tv = findViewById(R.id.tv_home_sky);
        if (tv != null) {
            int n = st.countReal();
            tv.setText(n == 0 ? "Cielo libero · tocca per scansionare Remote ID e audio"
                : n + (n == 1 ? " drone rilevato nelle vicinanze" : " droni rilevati nelle vicinanze"));
            tv.setTextColor(n == 0 ? 0xFF8FB3D0 : 0xFFFF5C7A);
        }
    }

    private void updateClock() {
        TextView tc = findViewById(R.id.tv_home_clock);
        if (tc != null) tc.setText(new SimpleDateFormat("HH:mm", Locale.ITALY).format(new Date()));
        TextView tg = findViewById(R.id.tv_home_greet);
        if (tg != null) {
            int h = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
            tg.setText(h < 5 ? "Buona notte" : h < 13 ? "Buongiorno" : h < 18 ? "Buon pomeriggio" : "Buonasera");
        }
    }

    private void updateStatus() {
        boolean gps    = hasGpsPerm();
        boolean gpsSvc = GpsTrackingService.isActive();
        String mapPath = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString(AppConfig.PREF_MAP_FILE, "");
        boolean hasMap = !mapPath.isEmpty() && new File(mapPath).exists();
        File routingDir = new File(getExternalFilesDir(null), "routing");
        File[] pbf = routingDir.exists() ? routingDir.listFiles((d, n) -> n.endsWith(".pbf")) : null;
        boolean hasRouting = pbf != null && pbf.length > 0;
        SkyUi.chip(findViewById(R.id.chip_gps), gps ? SkyUi.CHIP_ON : SkyUi.CHIP_ALERT, gps ? "GPS OK" : "GPS NO");
        SkyUi.chip(findViewById(R.id.chip_map), hasMap ? SkyUi.CHIP_ON : SkyUi.CHIP_WARN, hasMap ? "MAPPA OK" : "NO MAPPA");
        SkyUi.chip(findViewById(R.id.chip_routing), hasRouting ? SkyUi.CHIP_ON : SkyUi.CHIP_WARN, hasRouting ? "ROUTING OK" : "NO ROUTING");
        SkyUi.chip(findViewById(R.id.chip_service), gpsSvc ? SkyUi.CHIP_ON : SkyUi.CHIP_OFF, gpsSvc ? "TRACCIA ON" : "TRACCIA OFF");
        TextView tv = findViewById(R.id.tv_status);
        if (tv != null) {
            String hint = !hasMap ? "Scarica o carica una mappa da Download per iniziare."
                : !hasRouting ? "Per navigare scarica anche i dati ROUTING della tua zona."
                : "Tutto pronto: mappe e navigazione funzionano senza internet.";
            tv.setText(hint);
        }
    }

    private void showNavigateDialog() {
        View dv = LayoutInflater.from(this).inflate(R.layout.dialog_navigate_coords, null);
        EditText etLat = dv.findViewById(R.id.et_nav_lat);
        EditText etLon = dv.findViewById(R.id.et_nav_lon);
        EditText etName = dv.findViewById(R.id.et_nav_name);
        Spinner spProfile = dv.findViewById(R.id.sp_nav_profile);
        Button btnSearchAddr = dv.findViewById(R.id.btn_nav_search_address);
        String[] profileLabels = {"Auto", "Bici", "A piedi"};
        final String[] profiles = {RoutingEngine.PROFILE_CAR, RoutingEngine.PROFILE_BIKE, RoutingEngine.PROFILE_FOOT};
        if (spProfile != null) spProfile.setAdapter(
            new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, profileLabels));

        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("Naviga")
            .setView(dv)
            .setPositiveButton("Avvia (coordinate)", (d, w) -> {
                // Le coordinate sono OPZIONALI: usate solo se entrambe compilate.
                String latS = etLat != null ? etLat.getText().toString().trim().replace(",", ".") : "";
                String lonS = etLon != null ? etLon.getText().toString().trim().replace(",", ".") : "";
                if (latS.isEmpty() || lonS.isEmpty()) {
                    Toast.makeText(this, "Per le coordinate compila sia lat che lon, oppure usa Cerca indirizzo",
                        Toast.LENGTH_LONG).show();
                    return;
                }
                try {
                    double lat = Double.parseDouble(latS);
                    double lon = Double.parseDouble(lonS);
                    String name = etName != null ? etName.getText().toString().trim() : "";
                    if (name.isEmpty()) name = "Destinazione";
                    int profIdx = spProfile != null ? spProfile.getSelectedItemPosition() : 0;
                    Intent i = new Intent(this, NavigationActivity.class);
                    i.putExtra(NavigationActivity.EXTRA_DEST_LAT, lat);
                    i.putExtra(NavigationActivity.EXTRA_DEST_LON, lon);
                    i.putExtra(NavigationActivity.EXTRA_DEST_NAME, name);
                    i.putExtra(NavigationActivity.EXTRA_PROFILE, profiles[Math.max(0, profIdx)]);
                    startActivity(i);
                } catch (NumberFormatException e) {
                    Toast.makeText(this, "Coordinate non valide", Toast.LENGTH_SHORT).show();
                }
            })
            .setNegativeButton("Annulla", null)
            .create();

        // Pulsante principale: cerca per nome via (apre la schermata di ricerca offline)
        if (btnSearchAddr != null) btnSearchAddr.setOnClickListener(v -> {
            int profIdx = spProfile != null ? spProfile.getSelectedItemPosition() : 0;
            Intent i = new Intent(this, AddressSearchActivity.class);
            i.putExtra(AddressSearchActivity.EXTRA_PROFILE, profiles[Math.max(0, profIdx)]);
            startActivity(i);
            dialog.dismiss();
        });

        dialog.show();
    }

    private boolean checkGps() {
        if (!hasGpsPerm()) { requestGps(); return false; }
        return true;
    }
    private boolean hasGpsPerm() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            == PackageManager.PERMISSION_GRANTED;
    }
    private void requestGps() {
        List<String> perms = new ArrayList<>();
        perms.add(Manifest.permission.ACCESS_FINE_LOCATION);
        perms.add(Manifest.permission.ACCESS_COARSE_LOCATION);
        if (Build.VERSION.SDK_INT >= 33) perms.add(Manifest.permission.POST_NOTIFICATIONS);
        ActivityCompat.requestPermissions(this, perms.toArray(new String[0]), AppConfig.REQ_GPS_PERM);
    }
    private void open(Class<?> cls) { startActivity(new Intent(this, cls)); }

    @Override public void onRequestPermissionsResult(int req, @NonNull String[] p, @NonNull int[] res) {
        super.onRequestPermissionsResult(req, p, res);
        if (req == AppConfig.REQ_GPS_PERM) updateStatus();
    }
}
"""

MAP_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.Manifest;
import android.app.AlertDialog;
import android.content.*;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.*;
import com.offlinegps.map.map.MapController;
import com.offlinegps.map.routing.RoutingEngine;
import org.mapsforge.core.model.LatLong;
import org.mapsforge.map.android.graphics.AndroidGraphicFactory;
import org.mapsforge.map.android.view.MapView;
import java.io.File;

public class MapActivity extends AppCompatActivity
        implements GpsTrackingService.LocationCallback, CompassManager.Listener {

    public static final String EXTRA_FOCUS_LAT   = "focus_lat";
    public static final String EXTRA_FOCUS_LON   = "focus_lon";
    public static final String EXTRA_FOCUS_LABEL = "focus_label";

    private MapView       mapView;
    private MapController mapCtrl;
    private CompassManager compass;
    private TextView      tvZoom, tvInfo, tvFollowState, tvSpeed;
    private TextView      tvSheetTitle, tvSheetCoords, tvSheetDetail, tvMeasureInfo, tvSearchHint;
    private TextView      tvGpsAcc, tvMapAlt, tvMapCoords;
    private View          gpsDot;
    private ImageButton   btnCenter, btnZoomIn, btnZoomOut, btnMeasure, btnLayersSide;
    private ImageView     ivCompass, btnLayers;
    private View          searchBar, bottomSheet, crosshair;
    private boolean followGps = true;
    private boolean awaitingLocationEnable = false;
    private float   currentAz = 0f;
    private int     currentSats = 0;

    // --- misura distanze ---
    private boolean measureMode = false;
    private double measureTotal = 0;
    private double[] measureLast = null;

    // --- bottom sheet target (per Naviga/Salva) ---
    private double sheetLat = 0, sheetLon = 0;

    // --- tema mappa ---
    private int themeIndex = 0;  // 0=auto, 1=giorno, 2=notte
    private double lastSpeedKmh = 0;

    private final Handler pulseHandler = new Handler(Looper.getMainLooper());
    private final Runnable pulseTick = new Runnable() {
        @Override public void run() {
            if (mapCtrl != null) mapCtrl.tickPulse();
            pulseHandler.postDelayed(this, 33);
        }
    };

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) { finish(); return; }
        try { AndroidGraphicFactory.createInstance(getApplication()); } catch (Throwable ignored) {}
        setContentView(R.layout.activity_map);
        mapView       = findViewById(R.id.map_view);
        tvZoom        = findViewById(R.id.tv_zoom);
        tvInfo        = findViewById(R.id.tv_map_info);
        tvFollowState = findViewById(R.id.tv_follow_state);
        tvSpeed       = findViewById(R.id.tv_speed_value);
        tvGpsAcc      = findViewById(R.id.tv_gps_acc);
        tvMapAlt      = findViewById(R.id.tv_map_alt);
        tvMapCoords   = findViewById(R.id.tv_map_coords);
        gpsDot        = findViewById(R.id.gps_dot);
        ivCompass     = findViewById(R.id.iv_compass);
        btnCenter     = findViewById(R.id.btn_center);
        btnZoomIn     = findViewById(R.id.btn_zoom_in);
        btnZoomOut    = findViewById(R.id.btn_zoom_out);
        btnMeasure    = findViewById(R.id.btn_measure);
        btnLayersSide = findViewById(R.id.btn_layers_side);
        btnLayers     = findViewById(R.id.btn_layers);
        searchBar     = findViewById(R.id.search_bar);
        bottomSheet   = findViewById(R.id.bottom_sheet);
        crosshair     = findViewById(R.id.view_crosshair);
        tvSheetTitle  = findViewById(R.id.tv_sheet_title);
        tvSheetCoords = findViewById(R.id.tv_sheet_coords);
        tvSheetDetail = findViewById(R.id.tv_sheet_detail);
        tvMeasureInfo = findViewById(R.id.tv_measure_info);
        tvSearchHint  = findViewById(R.id.tv_search_hint);
        mapCtrl = new MapController(this);
        mapCtrl.init(mapView);
        mapCtrl.setWaypointTapListener((lat, lon, color) ->
            showSheet("Waypoint", lat, lon, ""));
        setupTouch();
        compass = new CompassManager(this);
        loadMapFromPrefs();
        setupButtons();
        startGps();
        handleFocusIntent();
    }

    /** Se siamo stati aperti per mostrare un punto cercato, centra la mappa li'. */
    private void handleFocusIntent() {
        Intent it = getIntent();
        if (it == null || !it.hasExtra(EXTRA_FOCUS_LAT)) return;
        final double flat = it.getDoubleExtra(EXTRA_FOCUS_LAT, 0);
        final double flon = it.getDoubleExtra(EXTRA_FOCUS_LON, 0);
        final String label = it.getStringExtra(EXTRA_FOCUS_LABEL);
        followGps = false;
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            try {
                if (mapCtrl != null) {
                    mapCtrl.setDestinationMarker(flat, flon);
                    mapCtrl.centerOn(flat, flon, (byte) 17);
                }
                showSheet(label != null ? label : "Destinazione", flat, flon, "");
                if (tvFollowState != null) tvFollowState.setText("LIBERO");
            } catch (Exception ignored) {}
        }, 600);
    }

    /** Mostra il bottom sheet con un punto selezionato. */
    private void showSheet(String title, double lat, double lon, String detail) {
        sheetLat = lat; sheetLon = lon;
        if (tvSheetTitle  != null) tvSheetTitle.setText(title);
        if (tvSheetCoords != null) tvSheetCoords.setText(
            String.format(java.util.Locale.US, "%.5f, %.5f", lat, lon));
        if (tvSheetDetail != null) {
            tvSheetDetail.setText(detail == null ? "" : detail);
            tvSheetDetail.setVisibility((detail == null || detail.isEmpty()) ? View.GONE : View.VISIBLE);
        }
    }

    private void setupTouch() {
        final android.view.GestureDetector gd = new android.view.GestureDetector(this,
            new android.view.GestureDetector.SimpleOnGestureListener() {
                @Override public void onLongPress(android.view.MotionEvent e) {
                    LatLong p = fromScreenPoint(e.getX(), e.getY());
                    if (p != null) showSheet("Posizione selezionata", p.latitude, p.longitude, "Tocco lungo");
                }
                @Override public boolean onSingleTapConfirmed(android.view.MotionEvent e) {
                    if (measureMode) {
                        LatLong p = fromScreenPoint(e.getX(), e.getY());
                        if (p != null) addMeasurePoint(p.latitude, p.longitude);
                        return true;
                    }
                    return false;
                }
            });
        mapView.setOnTouchListener((v, ev) -> { gd.onTouchEvent(ev); return false; });
    }

    private void addMeasurePoint(double lat, double lon) {
        if (measureLast != null) {
            measureTotal += haversine(measureLast[0], measureLast[1], lat, lon);
        }
        measureLast = new double[]{lat, lon};
        mapCtrl.addTrackPoint(lat, lon);
        if (tvMeasureInfo != null) {
            tvMeasureInfo.setVisibility(View.VISIBLE);
            tvMeasureInfo.setText(measureTotal < 1000
                ? String.format(java.util.Locale.US, "%.0f m", measureTotal)
                : String.format(java.util.Locale.US, "%.2f km", measureTotal / 1000.0));
        }
    }

    private static double haversine(double lat1, double lon1, double lat2, double lon2) {
        double R = 6371000;
        double dLat = Math.toRadians(lat2 - lat1), dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat/2)*Math.sin(dLat/2)
            + Math.cos(Math.toRadians(lat1))*Math.cos(Math.toRadians(lat2))
            * Math.sin(dLon/2)*Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    @androidx.annotation.Nullable
    private LatLong fromScreenPoint(float x, float y) {
        try {
            org.mapsforge.map.model.IMapViewPosition pos = mapView.getModel().mapViewPosition;
            LatLong center = pos.getCenter();
            byte zoom = pos.getZoomLevel();
            int tileSize = mapView.getModel().displayModel.getTileSize();
            int w = mapView.getWidth(), h = mapView.getHeight();
            if (w == 0 || h == 0) return null;

            long mapSize = org.mapsforge.core.util.MercatorProjection.getMapSize(zoom, tileSize);

            double centerPxX = org.mapsforge.core.util.MercatorProjection
                .longitudeToPixelX(center.longitude, zoom, tileSize);
            double centerPxY = org.mapsforge.core.util.MercatorProjection
                .latitudeToPixelY(center.latitude, zoom, tileSize);

            double targetPxX = centerPxX + (x - w / 2.0);
            double targetPxY = centerPxY + (y - h / 2.0);

            double lon = org.mapsforge.core.util.MercatorProjection
                .pixelXToLongitude(targetPxX, mapSize);
            double lat = org.mapsforge.core.util.MercatorProjection
                .pixelYToLatitude(targetPxY, mapSize);
            return new LatLong(lat, lon);
        } catch (Exception e) { return null; }
    }

    private void navigateToSheet() {
        String[] options = {"Auto", "Bici", "A piedi"};
        new AlertDialog.Builder(this)
            .setTitle("Naviga verso")
            .setItems(options, (d, which) -> {
                String[] profiles = {RoutingEngine.PROFILE_CAR, RoutingEngine.PROFILE_BIKE, RoutingEngine.PROFILE_FOOT};
                Intent i = new Intent(this, NavigationActivity.class);
                i.putExtra(NavigationActivity.EXTRA_DEST_LAT, sheetLat);
                i.putExtra(NavigationActivity.EXTRA_DEST_LON, sheetLon);
                i.putExtra(NavigationActivity.EXTRA_DEST_NAME, "Punto sulla mappa");
                i.putExtra(NavigationActivity.EXTRA_PROFILE, profiles[which]);
                startActivity(i);
            }).show();
    }

    private void saveSheetAsWaypoint() {
        final EditText et = new EditText(this);
        et.setHint("Nome posizione");
        new AlertDialog.Builder(this)
            .setTitle("Salva posizione")
            .setView(et)
            .setPositiveButton("Salva", (d, w) -> {
                String name = et.getText().toString().trim();
                if (name.isEmpty()) name = "Posizione";
                final String fName = name;
                final double la = sheetLat, lo = sheetLon;
                new Thread(() -> {
                    try {
                        com.offlinegps.map.data.WaypointEntity wp =
                            com.offlinegps.map.data.WaypointEntity.create(
                                fName, la, lo, 0.0, 0f, "#00E5FF");
                        com.offlinegps.map.data.GpsDatabase.getInstance(getApplicationContext())
                            .waypointDao().insert(wp);
                        runOnUiThread(() -> Toast.makeText(this, "Salvato: " + fName, Toast.LENGTH_SHORT).show());
                    } catch (Exception e) {
                        runOnUiThread(() -> Toast.makeText(this, "Errore salvataggio", Toast.LENGTH_SHORT).show());
                    }
                }).start();
            })
            .setNegativeButton("Annulla", null).show();
    }

    private void loadMapFromPrefs() {
        String path = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString(AppConfig.PREF_MAP_FILE, "");
        if (!path.isEmpty()) {
            File f = new File(path);
            if (f.exists() && mapCtrl.loadMapFile(f)) { if (tvInfo != null) tvInfo.setVisibility(View.GONE); }
            else showInfo("File mappa non trovato.\nUsa il pulsante mappa per sceglierne uno nuovo.");
        } else {
            showInfo("Nessuna mappa.\nVai in DOWNLOAD o carica un .map");
        }
    }

    private void setupButtons() {
        if (btnZoomIn  != null) btnZoomIn.setOnClickListener(v  -> { mapCtrl.zoomIn();  updateZoom(); });
        if (btnZoomOut != null) btnZoomOut.setOnClickListener(v -> { mapCtrl.zoomOut(); updateZoom(); });
        if (btnCenter  != null) btnCenter.setOnClickListener(v  -> {
            followGps = !followGps;
            if (tvFollowState != null) tvFollowState.setText(followGps ? "GPS" : "LIBERO");
            if (followGps) centerOnGps();
        });

        // misura distanze (toggle)
        if (btnMeasure != null) btnMeasure.setOnClickListener(v -> toggleMeasure());

        // cambio tema mappa (ciclo auto/giorno/notte)
        View.OnClickListener themeClick = v -> cycleTheme();
        if (btnLayers     != null) btnLayers.setOnClickListener(themeClick);
        if (btnLayersSide != null) btnLayersSide.setOnClickListener(themeClick);

        // barra di ricerca -> apre la ricerca indirizzi
        if (searchBar != null) searchBar.setOnClickListener(v ->
            startActivity(new Intent(this, AddressSearchActivity.class)));

        // bottom sheet azioni
        View bn = findViewById(R.id.btn_sheet_navigate);
        View bs = findViewById(R.id.btn_sheet_save);
        if (bn != null) bn.setOnClickListener(v -> navigateToSheet());
        if (bs != null) bs.setOnClickListener(v -> saveSheetAsWaypoint());

        // bussola: tocco -> rimetti a nord (follow + reset)
        if (ivCompass != null) ivCompass.setOnClickListener(v -> {
            followGps = true;
            if (tvFollowState != null) tvFollowState.setText("GPS");
            centerOnGps();
            Toast.makeText(this, "Orientato a nord", Toast.LENGTH_SHORT).show();
        });

        applyTheme();
    }

    private void toggleMeasure() {
        measureMode = !measureMode;
        if (measureMode) {
            measureTotal = 0; measureLast = null;
            mapCtrl.clearTrack();
            if (crosshair != null) crosshair.setVisibility(View.VISIBLE);
            if (tvMeasureInfo != null) { tvMeasureInfo.setVisibility(View.VISIBLE); tvMeasureInfo.setText("0 m"); }
            if (btnMeasure != null) btnMeasure.setColorFilter(0xFFFFD600);
            Toast.makeText(this, "Misura: tocca i punti sulla mappa", Toast.LENGTH_LONG).show();
        } else {
            if (crosshair != null) crosshair.setVisibility(View.GONE);
            if (tvMeasureInfo != null) tvMeasureInfo.setVisibility(View.GONE);
            if (btnMeasure != null) btnMeasure.clearColorFilter();
            mapCtrl.clearTrack();
        }
    }

    private static final String[] THEME_NAMES = {"Auto", "Giorno", "Notte"};
    private void cycleTheme() {
        themeIndex = (themeIndex + 1) % THEME_NAMES.length;
        applyTheme();
        Toast.makeText(this, "Tema: " + THEME_NAMES[themeIndex], Toast.LENGTH_SHORT).show();
    }

    /** Applica il tema mappa. Auto = notte se ora locale fuori 7-19. */
    private void applyTheme() {
        boolean night;
        if (themeIndex == 1) night = false;
        else if (themeIndex == 2) night = true;
        else {
            int h = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
            night = (h < 7 || h >= 19);
        }
        mapCtrl.setNightMode(night);
    }

    private void pickMapFile() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("*/*"); intent.addCategory(Intent.CATEGORY_OPENABLE);
        try { startActivityForResult(intent, AppConfig.REQ_PICK_MAP); }
        catch (Exception e) { Toast.makeText(this, "File manager non disponibile", Toast.LENGTH_SHORT).show(); }
    }

    /**
     * FIX v3.0: i file manager moderni restituiscono URI content:// che NON
     * sono percorsi di file. Prima l'import falliva quasi sempre; ora copiamo
     * il contenuto nella cartella maps dell'app e carichiamo la copia.
     */
    @Override protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != AppConfig.REQ_PICK_MAP || res != RESULT_OK || data == null) return;
        final android.net.Uri uri = data.getData();
        if (uri == null) return;
        Toast.makeText(this, "Importazione mappa in corso...", Toast.LENGTH_SHORT).show();
        new Thread(() -> {
            try {
                File dir = new File(getExternalFilesDir(null), "maps");
                dir.mkdirs();
                String name = queryDisplayName(uri);
                if (name == null || name.isEmpty()) name = "importata.map";
                if (!name.endsWith(".map")) name = name + ".map";
                File dst = new File(dir, name);
                try (java.io.InputStream in = getContentResolver().openInputStream(uri);
                     java.io.FileOutputStream out = new java.io.FileOutputStream(dst)) {
                    byte[] buf = new byte[65536];
                    int n;
                    while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
                }
                final File fDst = dst;
                runOnUiThread(() -> {
                    if (mapCtrl.loadMapFile(fDst)) {
                        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE)
                            .edit().putString(AppConfig.PREF_MAP_FILE, fDst.getAbsolutePath()).apply();
                        if (tvInfo != null) tvInfo.setVisibility(View.GONE);
                        updateZoom();
                        Toast.makeText(this, "[OK] " + fDst.getName(), Toast.LENGTH_SHORT).show();
                    } else {
                        fDst.delete();
                        Toast.makeText(this, "File non valido: serve un .map Mapsforge", Toast.LENGTH_LONG).show();
                    }
                });
            } catch (Exception e) {
                runOnUiThread(() ->
                    Toast.makeText(this, "Import fallito: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    @androidx.annotation.Nullable
    private String queryDisplayName(android.net.Uri uri) {
        try (android.database.Cursor c = getContentResolver().query(uri,
                new String[]{android.provider.OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) {}
        String path = uri.getPath();
        if (path != null) {
            int slash = path.lastIndexOf('/');
            return slash >= 0 ? path.substring(slash + 1) : path;
        }
        return null;
    }

    private void startGps() {
        if (!isLocationEnabled()) {
            awaitingLocationEnable = true;
            showLocationDisabledPrompt();
            return;
        }
        awaitingLocationEnable = false;
        GpsTrackingService.setCallback(this);
        Intent i = new Intent(this, GpsTrackingService.class);
        i.setAction(GpsTrackingService.ACTION_START);
        i.putExtra(AppConfig.PREF_TRACK_ON, false);
        startForegroundService(i);
        Location last = GpsTrackingService.getLastLocation();
        if (last != null) onLocationUpdate(last, GpsTrackingService.getSatCount());
    }

    private boolean isLocationEnabled() {
        LocationManager lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        if (lm == null) return false;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) return lm.isLocationEnabled();
        return lm.isProviderEnabled(LocationManager.GPS_PROVIDER)
            || lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER);
    }

    private void showLocationDisabledPrompt() {
        if (tvInfo == null) return;
        tvInfo.setText("Localizzazione disattivata sul telefono.\nTocca qui per attivarla nelle impostazioni.");
        tvInfo.setVisibility(View.VISIBLE);
        tvInfo.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)));
    }

    private void centerOnGps() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) mapCtrl.centerOn(loc.getLatitude(), loc.getLongitude(), true);
    }

    private void showInfo(String msg) {
        if (tvInfo != null) {
            tvInfo.setOnClickListener(null);
            tvInfo.setText(msg);
            tvInfo.setVisibility(View.VISIBLE);
        }
    }

    private void updateZoom() { if (tvZoom != null) tvZoom.setText("Z" + mapCtrl.getZoom()); }

    @Override public void onLocationUpdate(@NonNull Location loc, int sats) {
        currentSats = sats;
        runOnUiThread(() -> {
            mapCtrl.updatePosition(loc.getLatitude(), loc.getLongitude(), loc.getAccuracy(), loc.getBearing());
            if (followGps && !measureMode) mapCtrl.centerOn(loc.getLatitude(), loc.getLongitude(), true);
            // tachimetro
            double kmh = loc.hasSpeed() ? loc.getSpeed() * 3.6 : 0;
            lastSpeedKmh = kmh;
            if (tvSpeed != null) tvSpeed.setText(String.valueOf(Math.round(kmh)));
            // pannello GPS live: precisione colorata, quota, coordinate
            float acc = loc.getAccuracy();
            if (tvGpsAcc != null) tvGpsAcc.setText(String.format(java.util.Locale.US,
                "GPS %.0fm  %d sat", acc, sats));
            if (gpsDot != null) {
                int c = acc <= 8 ? 0xFF00FF88 : (acc <= 20 ? 0xFFFFD600 : 0xFFFF1744);
                gpsDot.setBackgroundColor(c);
            }
            if (tvMapAlt != null) tvMapAlt.setText(loc.hasAltitude()
                ? String.format(java.util.Locale.US, "%.0f m", loc.getAltitude()) : "-- m");
            if (tvMapCoords != null) tvMapCoords.setText(String.format(java.util.Locale.US,
                "%.5f,%.5f", loc.getLatitude(), loc.getLongitude()));
            if (tvInfo != null) tvInfo.setVisibility(View.GONE);
        });
    }

    @Override public void onCompass(float azimuth, float pitch, float roll) {
        currentAz = azimuth;
        runOnUiThread(() -> {
            // ruota l'ago della bussola in senso opposto all'azimut
            if (ivCompass != null) ivCompass.setRotation(-azimuth);
        });
    }

    @Override protected void onResume()  {
        super.onResume(); compass.start(this); GpsTrackingService.setCallback(this); updateZoom();
        pulseHandler.postDelayed(pulseTick, 33);
    }
    @Override protected void onPause()   {
        super.onPause(); compass.stop(); GpsTrackingService.setCallback(null);
        pulseHandler.removeCallbacks(pulseTick);
        Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit()
            .putFloat(AppConfig.PREF_LAST_LAT, (float) loc.getLatitude())
            .putFloat(AppConfig.PREF_LAST_LON, (float) loc.getLongitude()).apply();
    }
    @Override protected void onDestroy() {
        super.onDestroy(); GpsTrackingService.setCallback(null);
        pulseHandler.removeCallbacks(pulseTick);
        mapCtrl.destroy(); AndroidGraphicFactory.clearResourceMemoryCache();
    }
}
"""

NAVIGATION_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.content.SharedPreferences;
import android.location.Location;
import android.os.*;
import android.speech.tts.TextToSpeech;
import android.view.*;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;
import com.offlinegps.map.map.MapEngine;
import com.offlinegps.map.map.MapEngines;
import com.offlinegps.map.routing.NavCore;
import com.offlinegps.map.routing.RoutingEngine;
import com.offlinegps.map.routing.WeatherService;
import com.offlinegps.map.util.SunCalc;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;

/**
 * NAVIGATORE v5: mappa 3D che segue la strada (tu in basso, la strada davanti,
 * mappa ruotata nella direzione di marcia), scheda con la prossima manovra e
 * la distanza REALE che manca, manovra successiva, tachimetro, orario di
 * arrivo, avanzamento, annunci vocali a tre distanze, ricalcolo automatico.
 */
public class NavigationActivity extends AppCompatActivity
        implements GpsTrackingService.LocationCallback {

    public static final String EXTRA_DEST_LAT  = "dest_lat";
    public static final String EXTRA_DEST_LON  = "dest_lon";
    public static final String EXTRA_DEST_NAME = "dest_name";
    public static final String EXTRA_PROFILE   = "profile";

    private static final long REROUTE_COOLDOWN_MS = 8000;

    private MapEngine engine;
    private TextView tvInstruction, tvDistanceNext, tvEta, tvTotalDist, tvBuildStatus, tvWeather,
        tvSpeed, tvThen, tvEngine;
    private ImageView ivManeuver, ivThen;
    private ProgressBar pbBuild, pbProgress;
    private RecyclerView rvSteps;
    private View overlayBuild, panelThen, btnRecenter;
    private ImageButton btnProfileCar, btnProfileBike, btnProfileFoot, btn3d, btnVoice;

    private double destLat, destLon;
    private String destName = "Destinazione";
    private String profile  = RoutingEngine.PROFILE_CAR;

    private final ExecutorService routingExec = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @Nullable private RoutingEngine.RouteResult currentRoute;
    @Nullable private NavCore nav;
    @Nullable private NavCore.Progress lastProgress;
    private StepsAdapter stepsAdapter;
    private boolean following = true, tilt3d = true, routing = false, arrivedShown = false;
    private long lastRerouteAt = 0;
    private float speedMs = 0f;
    private int themeShown = -1;

    // --- Voce (Text-To-Speech) ---
    @Nullable private TextToSpeech tts;
    private boolean ttsReady = false;
    private boolean voiceEnabled = true;
    /** Annunci gia' fatti: chiave = indice manovra * 10 + livello (0 lontano, 1 vicino, 2 adesso). */
    private final Set<Integer> announced = new HashSet<>();

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        destLat = getIntent().getDoubleExtra(EXTRA_DEST_LAT, Double.NaN);
        destLon = getIntent().getDoubleExtra(EXTRA_DEST_LON, Double.NaN);
        destName = getIntent().getStringExtra(EXTRA_DEST_NAME);
        if (destName == null) destName = "Destinazione";
        String p = getIntent().getStringExtra(EXTRA_PROFILE);
        if (p != null) profile = p;
        if (Double.isNaN(destLat) || Double.isNaN(destLon)) { finish(); return; }

        setContentView(R.layout.activity_navigation);
        tvInstruction  = findViewById(R.id.tv_nav_instruction);
        tvDistanceNext = findViewById(R.id.tv_nav_distance_next);
        tvEta          = findViewById(R.id.tv_nav_eta);
        tvTotalDist    = findViewById(R.id.tv_nav_total_dist);
        tvBuildStatus  = findViewById(R.id.tv_nav_build_status);
        tvWeather      = findViewById(R.id.tv_nav_weather);
        tvSpeed        = findViewById(R.id.tv_nav_speed);
        tvThen         = findViewById(R.id.tv_nav_then);
        tvEngine       = findViewById(R.id.tv_nav_engine);
        ivManeuver     = findViewById(R.id.iv_nav_maneuver);
        ivThen         = findViewById(R.id.iv_nav_then);
        pbBuild        = findViewById(R.id.pb_nav_build);
        pbProgress     = findViewById(R.id.pb_nav_progress);
        rvSteps        = findViewById(R.id.rv_nav_steps);
        overlayBuild   = findViewById(R.id.overlay_nav_build);
        panelThen      = findViewById(R.id.panel_nav_then);
        btnRecenter    = findViewById(R.id.btn_nav_recenter);
        btnProfileCar  = findViewById(R.id.btn_nav_profile_car);
        btnProfileBike = findViewById(R.id.btn_nav_profile_bike);
        btnProfileFoot = findViewById(R.id.btn_nav_profile_foot);
        btn3d          = findViewById(R.id.btn_nav_3d);
        btnVoice       = findViewById(R.id.btn_nav_voice);

        SharedPreferences prefs = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE);
        tilt3d = prefs.getBoolean("nav_3d", true);
        voiceEnabled = prefs.getBoolean("nav_voice", true);

        // motore di mappa: 3D OpenGL se possibile, altrimenti 2D
        FrameLayout container = findViewById(R.id.nav_map_container);
        engine = MapEngines.create(this);
        container.addView(engine.view(), 0, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        engine.setOnUserGesture(() -> setFollowing(false));
        if (tvEngine != null) tvEngine.setText(engine.is3d() ? "3D" : "2D");
        loadBaseMap();
        engine.setDestination(destLat, destLon);
        applyTheme(true);

        stepsAdapter = new StepsAdapter();
        if (rvSteps != null) {
            rvSteps.setLayoutManager(new LinearLayoutManager(this));
            rvSteps.setAdapter(stepsAdapter);
        }

        click(R.id.btn_nav_close, v -> finish());
        click(R.id.btn_nav_recenter, v -> setFollowing(true));
        click(R.id.btn_nav_overview, v -> showOverview());
        click(R.id.btn_nav_steps, v -> toggleSteps());
        click(R.id.btn_nav_3d, v -> toggle3d());
        click(R.id.btn_nav_voice, v -> toggleVoice());
        setupProfileButtons();
        initTts();
        updateToggleIcons();
        setFollowing(true);
        startGpsAndRoute();
    }

    private void click(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    // ------------------------------------------------------------ voce
    private void initTts() {
        try {
            tts = new TextToSpeech(this, status -> {
                if (status == TextToSpeech.SUCCESS && tts != null) {
                    int r = tts.setLanguage(Locale.ITALIAN);
                    ttsReady = (r != TextToSpeech.LANG_MISSING_DATA && r != TextToSpeech.LANG_NOT_SUPPORTED);
                }
            });
        } catch (Exception e) { ttsReady = false; }
    }

    private void speak(String text) {
        if (!voiceEnabled || !ttsReady || tts == null || text == null || text.isEmpty()) return;
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "nav");
    }

    private void toggleVoice() {
        voiceEnabled = !voiceEnabled;
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit().putBoolean("nav_voice", voiceEnabled).apply();
        if (!voiceEnabled && tts != null) tts.stop();
        updateToggleIcons();
        Toast.makeText(this, voiceEnabled ? "Voce attiva" : "Voce disattivata", Toast.LENGTH_SHORT).show();
    }

    private void toggle3d() {
        if (!engine.is3d()) {
            Toast.makeText(this, "Il 3D non e' disponibile su questo telefono: mappa 2D", Toast.LENGTH_LONG).show();
            return;
        }
        tilt3d = !tilt3d;
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit().putBoolean("nav_3d", tilt3d).apply();
        updateToggleIcons();
        if (following) followCamera(true);
    }

    private void updateToggleIcons() {
        if (btnVoice != null) btnVoice.setImageResource(voiceEnabled ? R.drawable.ic_v5_volume : R.drawable.ic_v5_volume_off);
        if (btn3d != null) btn3d.setAlpha(engine != null && engine.is3d() && tilt3d ? 1f : 0.5f);
        if (tvEngine != null && engine != null) tvEngine.setText(engine.is3d() ? (tilt3d ? "3D" : "2D") : "2D");
    }

    // ------------------------------------------------------------ mappa
    private void loadBaseMap() {
        String path = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString(AppConfig.PREF_MAP_FILE, "");
        if (!path.isEmpty()) {
            File f = new File(path);
            if (f.exists()) engine.loadMapFile(f);
        }
    }

    /** Tema automatico: notte neon quando il sole e' sotto l'orizzonte, giorno altrimenti. */
    private void applyTheme(boolean force) {
        Location l = GpsTrackingService.getLastLocation();
        double la = l != null ? l.getLatitude() : destLat, lo = l != null ? l.getLongitude() : destLon;
        int t = SunCalc.isDark(System.currentTimeMillis(), la, lo) ? MapEngine.THEME_NIGHT : MapEngine.THEME_DAY;
        if (force || t != themeShown) {
            themeShown = t;
            engine.setTheme(t);
        }
    }

    private void setFollowing(boolean on) {
        following = on;
        if (btnRecenter != null) btnRecenter.setVisibility(on ? View.GONE : View.VISIBLE);
        if (on) {
            engine.setFocusOffset(tilt3d && engine.is3d() ? 0.45f : 0.25f);
            followCamera(true);
        } else {
            engine.setFocusOffset(0f);
        }
    }

    /** Inquadratura di guida: zoom secondo la velocita', mappa ruotata sulla rotta. */
    private void followCamera(boolean animate) {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) return;
        double la = loc.getLatitude(), lo = loc.getLongitude();
        float brg = travelBearing(loc);
        if (lastProgress != null && lastProgress.offRouteM < 25) { la = lastProgress.snappedLat; lo = lastProgress.snappedLon; }
        double zoom = speedMs < 4 ? 18 : speedMs < 14 ? 17 : speedMs < 25 ? 16 : 15;
        if (RoutingEngine.PROFILE_FOOT.equals(profile)) zoom = 18;
        boolean is3d = tilt3d && engine.is3d();
        engine.setFocusOffset(is3d ? 0.45f : 0.25f);
        engine.moveTo(la, lo, zoom, Float.isNaN(brg) ? 0f : brg, is3d ? 58f : 0f, animate);
    }

    /** Direzione di marcia: GPS se ci si muove, altrimenti direzione della strada. */
    private float travelBearing(Location loc) {
        if (loc.hasBearing() && loc.getSpeed() > 1.5f) return loc.getBearing();
        if (lastProgress != null && lastProgress.offRouteM < 30) return lastProgress.routeBearing;
        return loc.hasBearing() ? loc.getBearing() : Float.NaN;
    }

    private void showOverview() {
        if (currentRoute == null) return;
        setFollowing(false);
        engine.fitBounds(currentRoute.points, true);
    }

    private void toggleSteps() {
        if (rvSteps == null) return;
        rvSteps.setVisibility(rvSteps.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
    }

    // ------------------------------------------------------------ profili
    private void setupProfileButtons() {
        View.OnClickListener l = v -> {
            String newProfile = RoutingEngine.PROFILE_CAR;
            if (v == btnProfileBike) newProfile = RoutingEngine.PROFILE_BIKE;
            else if (v == btnProfileFoot) newProfile = RoutingEngine.PROFILE_FOOT;
            if (!newProfile.equals(profile)) { profile = newProfile; highlightProfile(); recalcRoute(); }
        };
        if (btnProfileCar  != null) btnProfileCar.setOnClickListener(l);
        if (btnProfileBike != null) btnProfileBike.setOnClickListener(l);
        if (btnProfileFoot != null) btnProfileFoot.setOnClickListener(l);
        highlightProfile();
    }

    private void highlightProfile() {
        setProfileBtnState(btnProfileCar,  RoutingEngine.PROFILE_CAR.equals(profile));
        setProfileBtnState(btnProfileBike, RoutingEngine.PROFILE_BIKE.equals(profile));
        setProfileBtnState(btnProfileFoot, RoutingEngine.PROFILE_FOOT.equals(profile));
    }

    private void setProfileBtnState(@Nullable ImageButton b, boolean active) {
        if (b == null) return;
        b.setAlpha(active ? 1f : 0.45f);
        b.setBackgroundResource(active ? R.drawable.bg_chip_on : R.drawable.bg_chip_off);
    }

    // ------------------------------------------------------------ rete stradale e percorso
    private void startGpsAndRoute() {
        GpsTrackingService.setCallback(this);
        Intent i = new Intent(this, GpsTrackingService.class);
        i.setAction(GpsTrackingService.ACTION_START);
        i.putExtra(AppConfig.PREF_TRACK_ON, false);
        startForegroundService(i);

        Location last = GpsTrackingService.getLastLocation();
        if (last != null) ensureGraphAndRoute(last.getLatitude(), last.getLongitude());
        else showBuildStatus("Attesa posizione GPS...", true);
    }

    private void ensureGraphAndRoute(double fromLat, double fromLon) {
        showBuildStatus("Preparazione rete stradale...", true);
        routingExec.execute(() -> {
            File routingDir = new File(getExternalFilesDir(null), "routing");
            String regionTag = RegionMapper.tagFor(fromLat, fromLon);
            if (regionTag == null) regionTag = RegionMapper.tagFor(destLat, destLon);
            File pbf = null;
            if (regionTag != null) {
                File candidate = new File(routingDir, regionTag + ".osm.pbf");
                if (candidate.exists()) pbf = candidate;
            }
            if (pbf == null && routingDir.exists()) {
                File[] pbfs = routingDir.listFiles((d, n) -> n.endsWith(".pbf"));
                if (pbfs != null && pbfs.length > 0) {
                    pbf = pbfs[0];
                    int dot = pbf.getName().indexOf('.');
                    regionTag = dot > 0 ? pbf.getName().substring(0, dot) : "regione";
                }
            }
            if (pbf == null) {
                final String diag = listRoutingDir(routingDir);
                mainHandler.post(() -> showBuildStatus(
                    "Nessun file di routing (.pbf) trovato.\n\n" + diag
                    + "\n\nVai in Download -> tab ROUTING e scarica una zona.", false));
                return;
            }
            final String finalRegionTag = regionTag;
            final File finalPbf = pbf;
            File graphFolder = new File(routingDir, finalRegionTag + "-gh");
            if (finalPbf.length() < 1024 * 1024) {
                mainHandler.post(() -> showBuildStatus(
                    "Il file " + finalPbf.getName() + " e' troppo piccolo (" + finalPbf.length()
                    + " byte): download incompleto.\nCancellalo e riscaricalo da Download.", false));
                return;
            }
            RoutingEngine.getInstance().buildOrLoad(this, finalPbf, graphFolder, finalRegionTag,
                new RoutingEngine.BuildProgressListener() {
                    @Override public void onProgress(String message, int p) {
                        mainHandler.post(() -> showBuildStatus(message, true));
                    }
                    @Override public void onDone(boolean success, @Nullable String error) {
                        mainHandler.post(() -> {
                            if (success) { hideBuildStatus(); recalcRoute(); }
                            else showBuildStatus("Errore costruzione rete:\n" + error, false);
                        });
                    }
                });
        });
    }

    private String listRoutingDir(File dir) {
        StringBuilder sb = new StringBuilder("Cartella: " + dir.getAbsolutePath() + "\n");
        if (!dir.exists()) { sb.append("(la cartella non esiste ancora)"); return sb.toString(); }
        File[] files = dir.listFiles();
        if (files == null || files.length == 0) { sb.append("(vuota)"); return sb.toString(); }
        for (File f : files) sb.append("- ").append(f.getName()).append("  ").append(f.length() / (1024 * 1024)).append(" MB\n");
        return sb.toString();
    }

    private void recalcRoute() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null || !RoutingEngine.getInstance().isReady() || routing) return;
        routing = true;
        lastRerouteAt = System.currentTimeMillis();
        final double fLat = loc.getLatitude(), fLon = loc.getLongitude();
        final String prof = profile;
        routingExec.execute(() -> {
            RoutingEngine.RouteResult result = RoutingEngine.getInstance().route(fLat, fLon, destLat, destLon, prof);
            mainHandler.post(() -> {
                routing = false;
                if (isFinishing()) return;
                if (result == null) {
                    String why = RoutingEngine.getInstance().getLastError();
                    if (why == null || why.isEmpty()) why = "Percorso non trovato";
                    Toast.makeText(this, why, Toast.LENGTH_LONG).show();
                    return;
                }
                boolean first = currentRoute == null || nav == null;
                currentRoute = result;
                nav = new NavCore(result.points, result.steps);
                announced.clear();
                engine.setRoute(result.points);
                stepsAdapter.submit(result.steps);
                if (first) {
                    speak(String.format(Locale.ITALIAN, "Percorso calcolato: %s, circa %s.",
                        spokenDistance(result.distanceMeters), spokenTime(result.timeMillis)));
                }
                Location l2 = GpsTrackingService.getLastLocation();
                if (l2 != null) onProgress(l2);
                fetchWeatherForDestination();
            });
        });
    }

    private void fetchWeatherForDestination() {
        if (tvWeather == null) return;
        WeatherService.fetch(destLat, destLon, w -> {
            if (tvWeather == null) return;
            if (w == null || Double.isNaN(w.tempC)) { tvWeather.setVisibility(View.GONE); return; }
            tvWeather.setText(String.format(Locale.ITALIAN, "%s  %.0f°  %s a destinazione", w.emoji(), w.tempC, w.description()));
            tvWeather.setVisibility(View.VISIBLE);
        });
    }

    // ------------------------------------------------------------ guida
    @Override public void onLocationUpdate(@NonNull Location loc, int sats) {
        runOnUiThread(() -> {
            if (isFinishing()) return;
            speedMs = loc.hasSpeed() ? 0.7f * speedMs + 0.3f * loc.getSpeed() : speedMs;
            if (tvSpeed != null) tvSpeed.setText(String.valueOf(Math.round(speedMs * 3.6f)));
            if (nav == null) {
                engine.setUserPosition(loc.getLatitude(), loc.getLongitude(), loc.getAccuracy(), travelBearing(loc));
                if (following) followCamera(true);
                if (RoutingEngine.getInstance().isReady()) recalcRoute();
                else if (!RoutingEngine.isBuilding()) ensureGraphAndRoute(loc.getLatitude(), loc.getLongitude());
                return;
            }
            onProgress(loc);
        });
    }

    private void onProgress(Location loc) {
        if (nav == null || currentRoute == null) return;
        NavCore.Progress p = nav.update(loc.getLatitude(), loc.getLongitude(), loc.getAccuracy());
        lastProgress = p;
        // la freccia sta sulla strada quando si e' vicini (niente "salti" del GPS)
        boolean onRoad = p.offRouteM < 20;
        engine.setUserPosition(onRoad ? p.snappedLat : loc.getLatitude(), onRoad ? p.snappedLon : loc.getLongitude(),
            loc.getAccuracy(), travelBearing(loc));
        if (following) followCamera(true);
        applyTheme(false);

        if (p.offRoute && !p.arrived && !routing && System.currentTimeMillis() - lastRerouteAt > REROUTE_COOLDOWN_MS) {
            speak("Ricalcolo del percorso");
            Toast.makeText(this, "Fuori percorso: ricalcolo...", Toast.LENGTH_SHORT).show();
            recalcRoute();
        }
        renderProgress(p);
        announce(p);
    }

    private void renderProgress(NavCore.Progress p) {
        List<RoutingEngine.NavStep> steps = currentRoute.steps;
        if (steps.isEmpty()) return;
        int idx = Math.min(p.stepIndex, steps.size() - 1);
        RoutingEngine.NavStep step = steps.get(idx);
        if (p.arrived) {
            tvDistanceNext.setText("Arrivato");
            tvInstruction.setText(destName);
            ivManeuver.setImageResource(R.drawable.ic_turn_finish);
            if (panelThen != null) panelThen.setVisibility(View.GONE);
        } else {
            tvDistanceNext.setText(RoutingEngine.NavStep.formatMeters(roundDistance(p.distToManeuverM)));
            tvInstruction.setText(step.text);
            ivManeuver.setImageResource(maneuverIcon(step.sign));
            // manovra successiva ravvicinata: "poi ..."
            if (panelThen != null) {
                boolean show = idx + 1 < steps.size() && nav.stepAlong(idx + 1) - nav.stepAlong(idx) < 300;
                panelThen.setVisibility(show ? View.VISIBLE : View.GONE);
                if (show) {
                    RoutingEngine.NavStep nx = steps.get(idx + 1);
                    ivThen.setImageResource(maneuverIcon(nx.sign));
                    tvThen.setText("Poi " + shortText(nx));
                }
            }
        }
        long arrival = System.currentTimeMillis() + p.remainingMs;
        tvEta.setText(p.arrived ? "Arrivato" : formatEta(p.remainingMs));
        tvTotalDist.setText(RoutingEngine.NavStep.formatMeters(p.remainingM) + "  ·  arrivo "
            + new SimpleDateFormat("HH:mm", Locale.ITALY).format(new Date(arrival)));
        if (pbProgress != null) pbProgress.setProgress(Math.round(p.fraction * 1000));
        stepsAdapter.setActiveIndex(idx);
        if (p.arrived && !arrivedShown) {
            arrivedShown = true;
            speak("Sei arrivato a destinazione");
            Toast.makeText(this, "Sei arrivato: " + destName, Toast.LENGTH_LONG).show();
        }
    }

    /** Tre annunci per manovra: lontano, vicino (con "poi..."), adesso. */
    private void announce(NavCore.Progress p) {
        if (p.arrived || currentRoute == null || currentRoute.steps.isEmpty()) return;
        List<RoutingEngine.NavStep> steps = currentRoute.steps;
        int idx = Math.min(p.stepIndex, steps.size() - 1);
        RoutingEngine.NavStep step = steps.get(idx);
        double[] th = NavCore.announceDistances(speedMs, profile);
        double d = p.distToManeuverM;
        int level = d <= th[2] ? 2 : d <= th[1] ? 1 : d <= th[0] ? 0 : -1;
        if (level < 0) return;
        // non annuncia il livello "lontano" se si e' gia' vicini (es. manovre ravvicinate)
        if (level == 0 && d < th[1] * 1.3) return;
        if (!announced.add(idx * 10 + level)) return;
        for (int l = 0; l < level; l++) announced.add(idx * 10 + l);
        String action = step.text != null ? step.text : "";
        String text;
        if (step.sign == 4 || step.sign == 5) {
            text = level == 2 ? "Sei quasi arrivato" : "Tra " + spokenDistance(d) + ", arrivo a destinazione";
        } else if (level == 2) {
            text = action;
        } else {
            text = "Tra " + spokenDistance(d) + ", " + action;
            if (level == 1 && idx + 1 < steps.size() && nav.stepAlong(idx + 1) - nav.stepAlong(idx) < 120) {
                RoutingEngine.NavStep nx = steps.get(idx + 1);
                if (nx.sign != 4) text += ". Poi " + shortText(nx);
            }
        }
        speak(text);
    }

    private static String shortText(RoutingEngine.NavStep s) {
        switch (s.sign) {
            case -3: return "svolta stretta a sinistra";
            case -2: return "svolta a sinistra";
            case -1: return "leggermente a sinistra";
            case 1:  return "leggermente a destra";
            case 2:  return "svolta a destra";
            case 3:  return "svolta stretta a destra";
            case 4:  return "arrivo";
            case 6:  return s.exitNumber > 0 ? "alla rotonda prendi l'uscita " + s.exitNumber : "entra nella rotonda";
            case 7:  return "tieni la destra";
            case -7: return "tieni la sinistra";
            case -8: case 8: case -98: return "inversione a U";
            default: return s.text != null ? s.text : "prosegui";
        }
    }

    private static double roundDistance(double m) {
        if (m < 100) return Math.round(m / 10.0) * 10;
        if (m < 1000) return Math.round(m / 50.0) * 50;
        return Math.round(m / 100.0) * 100;
    }

    private static String spokenDistance(double m) {
        if (m < 1000) return Math.round(roundDistance(m)) + " metri";
        double km = Math.round(m / 100.0) / 10.0;
        return (km == Math.floor(km) ? String.valueOf((long) km) : String.format(Locale.ITALIAN, "%.1f", km))
            + (km == 1 ? " chilometro" : " chilometri");
    }

    private static String spokenTime(long ms) {
        long min = Math.max(1, Math.round(ms / 60000.0));
        if (min < 60) return min + (min == 1 ? " minuto" : " minuti");
        long h = min / 60, r = min % 60;
        return h + (h == 1 ? " ora" : " ore") + (r > 0 ? " e " + r + " minuti" : "");
    }

    /** Icone manovra vettoriali (segni GraphHopper). */
    private int maneuverIcon(int sign) {
        switch (sign) {
            case -3: return R.drawable.ic_turn_sharp_left;
            case -2: return R.drawable.ic_turn_left;
            case -1: return R.drawable.ic_turn_slight_left;
            case  1: return R.drawable.ic_turn_slight_right;
            case  2: return R.drawable.ic_turn_right;
            case  3: return R.drawable.ic_turn_sharp_right;
            case  4: case 5: return R.drawable.ic_turn_finish;
            case  6: return R.drawable.ic_turn_roundabout;
            case  7: return R.drawable.ic_turn_keep_right;
            case -7: return R.drawable.ic_turn_keep_left;
            case -8: case 8: case -98: return R.drawable.ic_turn_uturn;
            default: return R.drawable.ic_turn_straight;
        }
    }

    private void showBuildStatus(String msg, boolean indeterminate) {
        if (overlayBuild != null) overlayBuild.setVisibility(View.VISIBLE);
        if (tvBuildStatus != null) tvBuildStatus.setText(msg);
        if (pbBuild != null) pbBuild.setVisibility(indeterminate ? View.VISIBLE : View.GONE);
    }

    private void hideBuildStatus() { if (overlayBuild != null) overlayBuild.setVisibility(View.GONE); }

    private String formatEta(long millis) {
        long min = Math.max(0, Math.round(millis / 60000.0));
        if (min < 60) return min + " min";
        return (min / 60) + " h " + (min % 60) + " min";
    }

    @Override protected void onResume() {
        super.onResume();
        GpsTrackingService.setCallback(this);
        if (engine != null) engine.onResume();
    }

    @Override protected void onPause() {
        super.onPause();
        GpsTrackingService.setCallback(null);
        if (engine != null) engine.onPause();
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        GpsTrackingService.setCallback(null);
        mainHandler.removeCallbacksAndMessages(null);
        routingExec.shutdown();
        if (tts != null) { tts.stop(); tts.shutdown(); tts = null; }
        if (engine != null) engine.onDestroy();
    }

    class StepsAdapter extends RecyclerView.Adapter<StepsAdapter.VH> {
        private final List<RoutingEngine.NavStep> data = new ArrayList<>();
        private int activeIndex = 0;
        void submit(List<RoutingEngine.NavStep> steps) { data.clear(); data.addAll(steps); notifyDataSetChanged(); }
        void setActiveIndex(int idx) {
            if (idx == activeIndex) return;
            activeIndex = idx;
            notifyDataSetChanged();
        }
        @NonNull @Override public VH onCreateViewHolder(@NonNull ViewGroup p, int t) {
            return new VH(LayoutInflater.from(p.getContext()).inflate(R.layout.item_nav_step, p, false));
        }
        @Override public void onBindViewHolder(@NonNull VH h, int pos) {
            RoutingEngine.NavStep s = data.get(pos);
            h.text.setText(s.text);
            h.dist.setText(s.formatDistance());
            if (h.icon != null) h.icon.setImageResource(maneuverIcon(s.sign));
            h.itemView.setAlpha(pos < activeIndex ? 0.35f : pos == activeIndex ? 1f : 0.75f);
        }
        @Override public int getItemCount() { return data.size(); }
        class VH extends RecyclerView.ViewHolder {
            TextView text, dist;
            ImageView icon;
            VH(@NonNull View v) {
                super(v);
                text = v.findViewById(R.id.tv_step_text);
                dist = v.findViewById(R.id.tv_step_dist);
                icon = v.findViewById(R.id.iv_step_icon);
            }
        }
    }
}
"""

DOWNLOAD_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.app.AlertDialog;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.R;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

public class DownloadActivity extends AppCompatActivity {

    private static final String MAP_BASE =
        "https://ftp-stud.hs-esslingen.de/Mirrors/download.mapsforge.org/maps/v5";

    private static final String OSM_BASE =
        "https://download.geofabrik.de/europe/italy";

    // Estratti per singola regione (molto piu' piccoli e veloci da elaborare).
    private static final String OSM_REG =
        "https://download.openstreetmap.fr/extracts/europe/italy";

    private static final Object[][] MAPS = {
        {"CENTRO - Roma, Lazio, Toscana, Umbria, Marche, Abruzzo",
            MAP_BASE + "/europe/italy/centro.map", "italia-centro", "277 MB"},
        {"SUD - Campania, Puglia, Calabria, Basilicata, Molise",
            MAP_BASE + "/europe/italy/sud.map", "italia-sud", "309 MB"},
        {"ISOLE - Sicilia e Sardegna",
            MAP_BASE + "/europe/italy/isole.map", "italia-isole", "169 MB"},
        {"NORD-EST - Veneto, Friuli, Trentino, Emilia-Romagna",
            MAP_BASE + "/europe/italy/nord-est.map", "italia-nord-est", "430 MB"},
        {"NORD-OVEST - Lombardia, Piemonte, Liguria, Valle d'Aosta",
            MAP_BASE + "/europe/italy/nord-ovest.map", "italia-nord-ovest", "395 MB"},
    };

    private static final Object[][] ROUTING = {
        // --- SINGOLE REGIONI (consigliate: piccole e veloci) ---
        {"LAZIO (routing) - Roma e provincia [CONSIGLIATO]",
            OSM_REG + "/lazio-latest.osm.pbf", "lazio", "119 MB"},
        {"UMBRIA (routing) - Perugia, Terni",
            OSM_REG + "/umbria-latest.osm.pbf", "umbria", "41 MB"},
        {"MARCHE (routing) - Ancona, Pesaro",
            OSM_REG + "/marche-latest.osm.pbf", "marche", "56 MB"},
        {"ABRUZZO (routing) - L'Aquila, Pescara",
            OSM_REG + "/abruzzo-latest.osm.pbf", "abruzzo", "97 MB"},
        {"TOSCANA (routing) - Firenze, Pisa, Siena",
            OSM_REG + "/toscana-latest.osm.pbf", "toscana", "201 MB"},
        {"CAMPANIA (routing) - Napoli, Salerno",
            OSM_REG + "/campania-latest.osm.pbf", "campania", "84 MB"},
        {"PUGLIA (routing) - Bari, Lecce",
            OSM_REG + "/puglia-latest.osm.pbf", "puglia", "133 MB"},
        {"SICILIA (routing) - Palermo, Catania",
            OSM_REG + "/sicilia-latest.osm.pbf", "sicilia", "133 MB"},
        {"SARDEGNA (routing) - Cagliari, Sassari",
            OSM_REG + "/sardegna-latest.osm.pbf", "sardegna", "87 MB"},
        {"LOMBARDIA (routing) - Milano, Bergamo",
            OSM_REG + "/lombardia-latest.osm.pbf", "lombardia", "330 MB"},
        {"PIEMONTE (routing) - Torino, Novara",
            OSM_REG + "/piemonte-latest.osm.pbf", "piemonte", "225 MB"},
        {"LIGURIA (routing) - Genova, Sanremo",
            OSM_REG + "/liguria-latest.osm.pbf", "liguria", "82 MB"},
        {"VENETO (routing) - Venezia, Verona, Padova",
            OSM_REG + "/veneto-latest.osm.pbf", "veneto", "264 MB"},
        {"EMILIA-ROMAGNA (routing) - Bologna, Modena",
            OSM_REG + "/emilia_romagna-latest.osm.pbf", "emilia_romagna", "201 MB"},
        // --- MACRO-AREE (piu' grandi, piu' lente da elaborare) ---
        {"CENTRO intero - Lazio+Toscana+Umbria+Marche+Abruzzo",
            OSM_BASE + "/centro-latest.osm.pbf", "centro", "~347 MB"},
        {"SUD (routing) - Campania, Puglia, Calabria, Basilicata, Molise",
            OSM_BASE + "/sud-latest.osm.pbf", "sud", "~390 MB"},
        {"ISOLE (routing) - Sicilia e Sardegna",
            OSM_BASE + "/isole-latest.osm.pbf", "isole", "~200 MB"},
        {"NORD-EST (routing) - Veneto, Friuli, Trentino, Emilia-Romagna",
            OSM_BASE + "/nord-est-latest.osm.pbf", "nord-est", "~430 MB"},
        {"NORD-OVEST (routing) - Lombardia, Piemonte, Liguria, Valle d'Aosta",
            OSM_BASE + "/nord-ovest-latest.osm.pbf", "nord-ovest", "~550 MB"},
    };

    private final ExecutorService exec = Executors.newSingleThreadExecutor();
    private ProgressBar pb;
    private TextView tvStatus, tvLog;
    private boolean busy = false;
    private LinearLayout containerMaps, containerRouting;
    private Button tabMaps, tabRouting;

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_download);
        pb       = findViewById(R.id.pb);
        tvStatus = findViewById(R.id.tv_status);
        tvLog    = findViewById(R.id.tv_log);
        containerMaps    = findViewById(R.id.container_maps);
        containerRouting = findViewById(R.id.container_routing);
        tabMaps    = findViewById(R.id.tab_maps);
        tabRouting = findViewById(R.id.tab_routing);

        buildButtons(containerMaps, MAPS, false);
        buildButtons(containerRouting, ROUTING, true);

        if (tabMaps != null) tabMaps.setOnClickListener(v -> showTab(true));
        if (tabRouting != null) tabRouting.setOnClickListener(v -> showTab(false));
        showTab(true);

        Button btnVerify = findViewById(R.id.btn_verify_files);
        if (btnVerify != null) btnVerify.setOnClickListener(v -> verifyFiles());
        Button btnRebuild = findViewById(R.id.btn_rebuild_graph);
        if (btnRebuild != null) btnRebuild.setOnClickListener(v -> rebuildGraph());
        verifyFiles();

        log("Mappe: ftp-stud.hs-esslingen.de");
        log("Routing: download.geofabrik.de");
        log("Per navigare con istruzioni servono ENTRAMBI i file della tua zona.");
    }

    private void showTab(boolean maps) {
        if (containerMaps != null) containerMaps.setVisibility(maps ? View.VISIBLE : View.GONE);
        if (containerRouting != null) containerRouting.setVisibility(maps ? View.GONE : View.VISIBLE);
        if (tabMaps != null) tabMaps.setAlpha(maps ? 1f : 0.5f);
        if (tabRouting != null) tabRouting.setAlpha(maps ? 0.5f : 1f);
    }

    /** Cancella le reti gia' elaborate (-gh) per forzare la ricostruzione. */
    private void rebuildGraph() {
        File routingDir = new File(getExternalFilesDir(null), "routing");
        if (!routingDir.exists()) {
            Toast.makeText(this, "Nessun dato di routing", Toast.LENGTH_SHORT).show();
            return;
        }
        new AlertDialog.Builder(this)
            .setTitle("Ricostruire la rete stradale?")
            .setMessage("Cancella SOLO la rete gia' elaborata (cartelle -gh), NON i file "
                + ".pbf scaricati. Alla prossima navigazione verra' ricostruita con le "
                + "impostazioni corrette. Procedere?")
            .setPositiveButton("Ricostruisci", (d, w) -> {
                int deleted = 0;
                File[] files = routingDir.listFiles();
                if (files != null) {
                    for (File f : files) {
                        if (f.isDirectory() && f.getName().endsWith("-gh")) {
                            if (deleteRecursive(f)) deleted++;
                        }
                        if (f.isFile() && f.getName().endsWith("-geo.idx")) f.delete();
                    }
                }
                Toast.makeText(this, "Reti cancellate: " + deleted
                    + ". Verranno ricostruite alla prossima navigazione.", Toast.LENGTH_LONG).show();
                verifyFiles();
            })
            .setNegativeButton("Annulla", null).show();
    }

    private boolean deleteRecursive(File f) {
        if (f.isDirectory()) {
            File[] kids = f.listFiles();
            if (kids != null) for (File k : kids) deleteRecursive(k);
        }
        return f.delete();
    }

    /** Mostra i file realmente presenti sul telefono (diagnostica). */
    private void verifyFiles() {
        StringBuilder sb = new StringBuilder("FILE PRESENTI SUL TELEFONO:\n");
        File mapsDir = new File(getExternalFilesDir(null), "maps");
        File routingDir = new File(getExternalFilesDir(null), "routing");
        sb.append("\n[MAPPE] ").append(mapsDir.getAbsolutePath()).append("\n");
        sb.append(listDir(mapsDir, ".map"));
        sb.append("\n[ROUTING] ").append(routingDir.getAbsolutePath()).append("\n");
        sb.append(listDir(routingDir, ".pbf"));
        // mostra l'ultimo crash registrato, se presente
        try {
            File crash = new File(getExternalFilesDir(null), "last_crash.txt");
            if (crash.exists()) {
                sb.append("\n[ULTIMO ERRORE/CRASH]\n");
                java.io.BufferedReader br = new java.io.BufferedReader(
                    new java.io.FileReader(crash));
                String line; int n = 0;
                while ((line = br.readLine()) != null && n < 25) { sb.append(line).append("\n"); n++; }
                br.close();
            }
        } catch (Exception ignored) {}
        if (tvLog != null) tvLog.setText(sb.toString());
    }

    private String listDir(File dir, String ext) {
        if (!dir.exists()) return "  (cartella inesistente - mai scaricato nulla qui)\n";
        File[] files = dir.listFiles();
        if (files == null || files.length == 0) return "  (vuota)\n";
        StringBuilder sb = new StringBuilder();
        boolean any = false;
        for (File f : files) {
            long mb = f.length() / (1024 * 1024);
            String warn = (f.getName().endsWith(ext) && mb < 1) ? "  << TROPPO PICCOLO!" : "";
            sb.append("  ").append(f.getName()).append("  ").append(mb).append(" MB").append(warn).append("\n");
            any = true;
        }
        return any ? sb.toString() : "  (nessun file)\n";
    }

    private void buildButtons(LinearLayout container, Object[][] items, boolean isRouting) {
        if (container == null) return;
        for (int i = 0; i < items.length; i++) {
            Button b = new Button(this);
            b.setText(items[i][0] + "\n" + items[i][3]);
            b.setTextColor(0xFF00E5FF);
            b.setBackgroundColor(i == 0 ? 0xFF00E5FF : 0xFF141E2E);
            if (i == 0) b.setTextColor(0xFF050A14);
            b.setMinHeight(dp(58));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = dp(8);
            b.setLayoutParams(lp);
            final int idx = i;
            b.setOnClickListener(v -> startDownload(items, idx, isRouting));
            container.addView(b);
        }
    }

    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density); }

    private void startDownload(Object[][] items, int idx, boolean isRouting) {
        if (busy) { Toast.makeText(this, "Download gia in corso", Toast.LENGTH_SHORT).show(); return; }
        busy = true;

        String url      = (String) items[idx][1];
        String fileName = (String) items[idx][2];
        File targetDir = new File(getExternalFilesDir(null), isRouting ? "routing" : "maps");
        targetDir.mkdirs();
        String ext = isRouting ? ".osm.pbf" : ".map";
        File out = new File(targetDir, fileName + ext);
        // Scarichiamo su un file temporaneo e rinominiamo SOLO a fine download.
        // Cosi' un file col nome definitivo e' SEMPRE completo: se il download
        // si interrompe, non resta un .pbf/.map corrotto che poi darebbe errori.
        File tmp = new File(targetDir, fileName + ext + ".part");

        if (tvStatus != null) tvStatus.setText("Scaricando " + items[idx][0] + "...");
        if (pb != null) { pb.setVisibility(View.VISIBLE); pb.setProgress(0); }
        log("-> " + url);

        exec.execute(() -> {
            try {
                HttpURLConnection conn = openFollowingRedirects(new URL(url), 5);
                conn.setConnectTimeout(20000);
                conn.setReadTimeout(120000);
                conn.connect();

                int code = conn.getResponseCode();
                if (code >= 400) throw new IOException("HTTP " + code + " per: " + url);

                long total = conn.getContentLengthLong();
                long done  = 0L;

                // verifica spazio libero PRIMA di iniziare (file grandi!)
                if (total > 0) {
                    long free = targetDir.getUsableSpace();
                    if (free < total + 10_485_760L) {  // +10 MB di margine
                        throw new IOException("Spazio insufficiente: servono "
                            + (total / 1_048_576L) + " MB ma liberi solo "
                            + (free / 1_048_576L) + " MB");
                    }
                }

                try (InputStream in = conn.getInputStream();
                     FileOutputStream fo = new FileOutputStream(tmp)) {
                    byte[] buf = new byte[65536];
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        fo.write(buf, 0, n);
                        done += n;
                        if (total > 0) {
                            final int pct  = (int)(done * 100L / total);
                            final long mbD = done / 1_048_576L;
                            final long mbT = total / 1_048_576L;
                            runOnUiThread(() -> {
                                if (pb != null) pb.setProgress(pct);
                                if (tvStatus != null) tvStatus.setText(pct + "%  " + mbD + "/" + mbT + " MB");
                            });
                        }
                    }
                    fo.getFD().sync();  // forza scrittura su disco prima di rinominare
                }
                conn.disconnect();

                // download completo: sostituiamo il vecchio file e rinominiamo
                if (out.exists()) out.delete();
                if (!tmp.renameTo(out)) {
                    throw new IOException("Impossibile finalizzare il file scaricato");
                }

                final String path = out.getAbsolutePath();
                runOnUiThread(() -> {
                    busy = false;
                    if (pb != null) pb.setVisibility(View.GONE);
                    if (tvStatus != null) tvStatus.setText("[OK] " + out.getName()
                        + "  (" + out.length()/1_048_576L + " MB)");
                    if (!isRouting) {
                        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE)
                            .edit().putString(AppConfig.PREF_MAP_FILE, path).apply();
                    }
                    Toast.makeText(this, "Pronto: " + out.getName(), Toast.LENGTH_LONG).show();
                    log("[OK] salvato in: " + path);
                    if (isRouting) log("Nota: la prima volta che navighi in questa zona,");
                    if (isRouting) log("l'app costruira' la rete stradale (puo' richiedere minuti).");
                });

            } catch (IOException e) {
                // pulizia: rimuovi il file temporaneo parziale (non il file buono)
                if (tmp.exists()) tmp.delete();
                runOnUiThread(() -> {
                    busy = false;
                    if (pb != null) pb.setVisibility(View.GONE);
                    String msg = "[ERRORE] " + e.getMessage();
                    if (tvStatus != null) tvStatus.setText(msg);
                    log(msg);
                    Toast.makeText(this, "Download fallito. Controlla la connessione.", Toast.LENGTH_LONG).show();
                });
            }
        });
    }

    private HttpURLConnection openFollowingRedirects(URL url, int maxRedir) throws IOException {
        for (int i = 0; i < maxRedir; i++) {
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setInstanceFollowRedirects(false);
            c.setConnectTimeout(15000);
            c.setReadTimeout(30000);
            c.setRequestProperty("User-Agent", "OfflineGPS/3.0 Android");
            int code = c.getResponseCode();
            if (code == 301 || code == 302 || code == 307 || code == 308) {
                String loc = c.getHeaderField("Location");
                c.disconnect();
                url = new URL(loc);
                log("Redirect [" + code + "] -> " + loc);
            } else return c;
        }
        throw new IOException("Troppi redirect");
    }

    private void log(String msg) {
        runOnUiThread(() -> {
            if (tvLog == null) return;
            String cur = tvLog.getText().toString();
            String[] lines = cur.split("\n");
            StringBuilder sb = new StringBuilder();
            int start = Math.max(0, lines.length - 14);
            for (int i = start; i < lines.length; i++) if (!lines[i].isEmpty()) sb.append(lines[i]).append("\n");
            sb.append(msg);
            tvLog.setText(sb.toString());
        });
    }

    @Override protected void onDestroy() { super.onDestroy(); exec.shutdown(); }
}
"""

WAYPOINTS_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.app.AlertDialog;
import android.content.Intent;
import android.location.Location;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.*;
import com.offlinegps.map.R;
import com.offlinegps.map.data.*;
import com.offlinegps.map.gps.GpsTrackingService;
import com.offlinegps.map.routing.RoutingEngine;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.Executors;

public class WaypointsActivity extends AppCompatActivity {
    private WpAdapter adapter;
    private static final String[] COLORS = {"#00E5FF","#00FF88","#FF6B35","#FF1744","#FFD600","#B388FF","#FFFFFF"};
    private static final String[] COLOR_NAMES = {"Cyan","Verde","Arancio","Rosso","Giallo","Viola","Bianco"};
    private int selectedColor = 0;

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_waypoints);
        RecyclerView rv = findViewById(R.id.rv_wp);
        adapter = new WpAdapter();
        if (rv != null) { rv.setLayoutManager(new LinearLayoutManager(this)); rv.setAdapter(adapter); }
        Button btnAdd = findViewById(R.id.btn_add_wp);
        if (btnAdd != null) btnAdd.setOnClickListener(v -> showAddDialog());
        GpsDatabase.getInstance(this).waypointDao().getAllLive().observe(this,
            list -> { if (list != null) adapter.submit(list); });
    }

    private void showAddDialog() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { Toast.makeText(this,"Nessun fix GPS",Toast.LENGTH_SHORT).show(); return; }
        View dv = LayoutInflater.from(this).inflate(R.layout.dialog_add_waypoint, null);
        EditText etName = dv.findViewById(R.id.et_wp_name);
        EditText etDesc = dv.findViewById(R.id.et_wp_desc);
        Spinner  spColor = dv.findViewById(R.id.sp_wp_color);
        TextView tvCoords = dv.findViewById(R.id.tv_wp_coords_preview);
        String defName = "WP " + new SimpleDateFormat("HH:mm:ss", Locale.ITALY).format(new Date());
        if (etName != null) etName.setText(defName);
        if (tvCoords != null) tvCoords.setText(String.format("%.6f, %.6f  alt: %.1fm  +/-%.0fm",
            loc.getLatitude(), loc.getLongitude(), loc.getAltitude(), loc.getAccuracy()));
        if (spColor != null) {
            spColor.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, COLOR_NAMES));
            spColor.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
                @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) { selectedColor = pos; }
                @Override public void onNothingSelected(AdapterView<?> p) {}
            });
        }
        new AlertDialog.Builder(this).setTitle("Salva Waypoint").setView(dv)
            .setPositiveButton("Salva", (d, w) -> {
                String name = etName != null ? etName.getText().toString().trim() : defName;
                if (name.isEmpty()) name = defName;
                String desc = etDesc != null ? etDesc.getText().toString().trim() : "";
                final String fn = name, fd = desc, fc = COLORS[selectedColor];
                final double lat = loc.getLatitude(), lon = loc.getLongitude(), alt = loc.getAltitude();
                final float acc = loc.getAccuracy();
                Executors.newSingleThreadExecutor().execute(() -> {
                    WaypointEntity wp = WaypointEntity.create(fn, lat, lon, alt, acc, fc);
                    wp.description = fd;
                    GpsDatabase.getInstance(getApplicationContext()).waypointDao().insert(wp);
                });
                Toast.makeText(this,"Salvato!",Toast.LENGTH_SHORT).show();
            })
            .setNegativeButton("Annulla", null).show();
    }

    private void showNavigateDialog(WaypointEntity w) {
        String[] options = {"Auto", "Bici", "A piedi"};
        String[] profiles = {RoutingEngine.PROFILE_CAR, RoutingEngine.PROFILE_BIKE, RoutingEngine.PROFILE_FOOT};
        new AlertDialog.Builder(this)
            .setTitle("Naviga verso \"" + w.name + "\"")
            .setItems(options, (d, which) -> {
                Intent i = new Intent(this, NavigationActivity.class);
                i.putExtra(NavigationActivity.EXTRA_DEST_LAT, w.latitude);
                i.putExtra(NavigationActivity.EXTRA_DEST_LON, w.longitude);
                i.putExtra(NavigationActivity.EXTRA_DEST_NAME, w.name);
                i.putExtra(NavigationActivity.EXTRA_PROFILE, profiles[which]);
                startActivity(i);
            }).show();
    }

    class WpAdapter extends RecyclerView.Adapter<WpAdapter.VH> {
        final List<WaypointEntity> items = new ArrayList<>();
        final SimpleDateFormat fmt = new SimpleDateFormat("dd/MM HH:mm", Locale.ITALY);
        void submit(List<WaypointEntity> l) { items.clear(); items.addAll(l); notifyDataSetChanged(); }
        @NonNull @Override public VH onCreateViewHolder(@NonNull ViewGroup p, int vt) {
            return new VH(LayoutInflater.from(p.getContext()).inflate(R.layout.item_waypoint, p, false));
        }
        @Override public void onBindViewHolder(@NonNull VH h, int pos) {
            WaypointEntity w = items.get(pos);
            h.name.setText(w.name);
            h.coords.setText(String.format("%.6f, %.6f\nAlt: %.0fm  +/-%.0fm", w.latitude, w.longitude, w.altitude, w.accuracy));
            h.time.setText(fmt.format(new Date(w.timestamp)));
            try { h.colorDot.setBackgroundColor(android.graphics.Color.parseColor(w.color)); }
            catch (Exception e) { h.colorDot.setBackgroundColor(0xFF00E5FF); }
            Location cur = GpsTrackingService.getLastLocation();
            if (cur != null) {
                double dist = w.distanceTo(cur.getLatitude(), cur.getLongitude());
                h.dist.setText(w.formatDistance(dist));
                if (dist > 0 && cur.getSpeed() > 0.5f)
                    h.eta.setText(String.format("ETA: %.0f min", dist / (cur.getSpeed() * 60)));
                else h.eta.setText("");
            }
            if (!w.description.isEmpty()) h.desc.setText(w.description);
            h.btnDel.setOnClickListener(v ->
                Executors.newSingleThreadExecutor().execute(() ->
                    GpsDatabase.getInstance(v.getContext()).waypointDao().delete(w)));
            h.btnNav.setOnClickListener(v -> showNavigateDialog(w));
        }
        @Override public int getItemCount() { return items.size(); }
        class VH extends RecyclerView.ViewHolder {
            TextView name, coords, time, dist, eta, desc; View colorDot; Button btnDel, btnNav;
            VH(@NonNull View v) {
                super(v);
                name=v.findViewById(R.id.tv_wp_name); coords=v.findViewById(R.id.tv_wp_coords);
                time=v.findViewById(R.id.tv_wp_time); dist=v.findViewById(R.id.tv_wp_dist);
                eta=v.findViewById(R.id.tv_wp_eta); desc=v.findViewById(R.id.tv_wp_desc);
                colorDot=v.findViewById(R.id.vw_color_dot); btnDel=v.findViewById(R.id.btn_wp_del);
                btnNav=v.findViewById(R.id.btn_wp_nav);
            }
        }
    }
}
"""

STATS_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

public class StatsActivity extends AppCompatActivity {
    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_stats);
        updateStats();
    }
    @Override protected void onResume() { super.onResume(); updateStats(); }
    private void updateStats() {
        setText(R.id.tv_stat_max_spd, String.format("%.1f km/h", GpsTrackingService.getMaxSpeedKmh()));
        float d = GpsTrackingService.getTotalDistM();
        setText(R.id.tv_stat_total_dist, d < 1000 ? String.format("%.0f m", d) : String.format("%.2f km", d/1000f));
        setText(R.id.tv_stat_sats, String.valueOf(GpsTrackingService.getSatCount()));
        setText(R.id.tv_stat_gps_state, GpsTrackingService.isActive() ? "GPS Attivo" : "GPS Inattivo");
        android.location.Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) {
            setText(R.id.tv_stat_last_lat, String.format("%.8f", loc.getLatitude()));
            setText(R.id.tv_stat_last_lon, String.format("%.8f", loc.getLongitude()));
            setText(R.id.tv_stat_last_alt, String.format("%.1f m", loc.getAltitude()));
            setText(R.id.tv_stat_last_acc, String.format("+/-%.1f m", loc.getAccuracy()));
            setText(R.id.tv_stat_last_spd, String.format("%.1f km/h", loc.getSpeed()*3.6f));
            setText(R.id.tv_stat_bearing, String.format("%.1f", loc.getBearing()));
        }
    }
    private void setText(int id, String t) { TextView tv = findViewById(id); if (tv != null) tv.setText(t); }
}
"""

# ============================================================
#  ToolsActivity — STRUMENTI OUTDOOR / SOS
# ============================================================
TOOLS_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.gps.GpsTrackingService;

public class ToolsActivity extends AppCompatActivity implements SensorEventListener {

    private SensorManager sensorMgr;
    private Sensor rotationSensor, stepSensor, accelSensor, pressureSensor;
    private float azimuth = 0f;
    private float stepBase = -1f;
    private int stepsToday = 0;

    // livella a bolla
    private TextView tvLevel;
    private View bubble;
    private float levelX = 0, levelY = 0;

    // cronometro
    private TextView tvChrono;
    private boolean chronoRunning = false;
    private long chronoStart = 0, chronoAccum = 0;
    private final Handler chronoHandler = new Handler(Looper.getMainLooper());

    // velocita max/media
    private TextView tvSpeedStats;
    private double speedMax = 0, speedSum = 0;
    private int speedCount = 0;

    // pressione
    private TextView tvPressure;
    private boolean labelsActive = false;

    private TextView tvCompass, tvAzimuth, tvAltitude, tvCoords, tvSteps, tvParkInfo, tvDistInfo;
    private View compassRose;
    private android.hardware.camera2.CameraManager camMgr;
    private String camId;
    private Handler sosHandler = new Handler(Looper.getMainLooper());
    private boolean sosRunning = false;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_tools);

        tvCompass  = findViewById(R.id.tv_compass_dir);
        tvAzimuth  = findViewById(R.id.tv_azimuth);
        tvAltitude = findViewById(R.id.tv_altitude);
        tvCoords   = findViewById(R.id.tv_tool_coords);
        tvSteps    = findViewById(R.id.tv_steps);
        tvParkInfo = findViewById(R.id.tv_park_info);
        tvDistInfo = findViewById(R.id.tv_dist_info);
        compassRose = findViewById(R.id.iv_compass_rose);

        View back = findViewById(R.id.btn_tools_back);
        if (back != null) back.setOnClickListener(v -> finish());

        View bPark = findViewById(R.id.btn_save_parking);
        if (bPark != null) bPark.setOnClickListener(v -> saveParking());
        View bPark2 = findViewById(R.id.btn_goto_parking);
        if (bPark2 != null) bPark2.setOnClickListener(v -> gotoParking());

        View bSos = findViewById(R.id.btn_sos_message);
        if (bSos != null) bSos.setOnClickListener(v -> sendSosMessage());

        View bTorch = findViewById(R.id.btn_sos_torch);
        if (bTorch != null) bTorch.setOnClickListener(v -> toggleSosTorch());

        View bMark = findViewById(R.id.btn_mark_point);
        if (bMark != null) bMark.setOnClickListener(v -> markDistancePoint());

        // strumenti outdoor avanzati (schede dedicate)
        bindTool(R.id.open_area, AreaToolActivity.class);
        bindTool(R.id.open_recorder, TrackRecorderActivity.class);
        bindTool(R.id.open_unitconv, UnitConvActivity.class);
        bindTool(R.id.open_timer, MultiTimerActivity.class);
        bindTool(R.id.open_slope, SlopeToolActivity.class);
        // NUOVI v3.0
        bindTool(R.id.open_metal, MetalDetectorActivity.class);
        bindTool(R.id.open_heat, HeatIndexActivity.class);
        bindTool(R.id.open_pace, PaceCalcActivity.class);
        bindTool(R.id.open_speedhud, SpeedHudActivity.class);

        // nuovi strumenti
        tvLevel = findViewById(R.id.tv_level);
        bubble = findViewById(R.id.view_bubble);
        tvChrono = findViewById(R.id.tv_chrono);
        tvSpeedStats = findViewById(R.id.tv_speed_stats);
        tvPressure = findViewById(R.id.tv_pressure);
        View bChrono = findViewById(R.id.btn_chrono_toggle);
        if (bChrono != null) bChrono.setOnClickListener(v -> toggleChrono());
        View bChronoR = findViewById(R.id.btn_chrono_reset);
        if (bChronoR != null) bChronoR.setOnClickListener(v -> resetChrono());
        View bSpeedR = findViewById(R.id.btn_speed_reset);
        if (bSpeedR != null) bSpeedR.setOnClickListener(v -> { speedMax = speedSum = 0; speedCount = 0; });

        sensorMgr = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sensorMgr != null) {
            rotationSensor = sensorMgr.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
            stepSensor = sensorMgr.getDefaultSensor(Sensor.TYPE_STEP_COUNTER);
            accelSensor = sensorMgr.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
            pressureSensor = sensorMgr.getDefaultSensor(Sensor.TYPE_PRESSURE);
        }
        camMgr = (android.hardware.camera2.CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            if (camMgr != null) for (String id : camMgr.getCameraIdList()) {
                Boolean f = camMgr.getCameraCharacteristics(id)
                    .get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE);
                if (Boolean.TRUE.equals(f)) { camId = id; break; }
            }
        } catch (Exception ignored) {}

        refreshParkingLabel();
        updateLocationLabels();
    }

    @Override protected void onPause() {
        super.onPause();
        labelsActive = false;
        if (sensorMgr != null) sensorMgr.unregisterListener(this);
        stopSosTorch();
        // ferma gli aggiornamenti in sospeso (il cronometro continua a contare
        // il tempo grazie a chronoStart/chronoAccum, ma non aggiorna la UI da spento)
        chronoHandler.removeCallbacksAndMessages(null);
    }

    @Override protected void onResume() {
        super.onResume();
        labelsActive = true;
        if (sensorMgr != null) {
            if (rotationSensor != null)
                sensorMgr.registerListener(this, rotationSensor, SensorManager.SENSOR_DELAY_UI);
            if (stepSensor != null)
                sensorMgr.registerListener(this, stepSensor, SensorManager.SENSOR_DELAY_NORMAL);
            if (accelSensor != null)
                sensorMgr.registerListener(this, accelSensor, SensorManager.SENSOR_DELAY_UI);
            if (pressureSensor != null)
                sensorMgr.registerListener(this, pressureSensor, SensorManager.SENSOR_DELAY_NORMAL);
        }
        // se il cronometro era in marcia, riprende ad aggiornare la UI
        if (chronoRunning) chronoTick();
        updateLocationLabels();
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        chronoHandler.removeCallbacksAndMessages(null);
        sosHandler.removeCallbacksAndMessages(null);
        stopSosTorch();
        if (sensorMgr != null) sensorMgr.unregisterListener(this);
    }

    // ---- Bussola + quota ----
    @Override public void onSensorChanged(SensorEvent e) {
        if (e.sensor.getType() == Sensor.TYPE_ROTATION_VECTOR) {
            float[] R = new float[9];
            SensorManager.getRotationMatrixFromVector(R, e.values);
            float[] orient = new float[3];
            SensorManager.getOrientation(R, orient);
            azimuth = (float) Math.toDegrees(orient[0]);
            if (azimuth < 0) azimuth += 360f;
            if (compassRose != null) compassRose.setRotation(-azimuth);
            if (tvAzimuth != null) tvAzimuth.setText(String.format(java.util.Locale.US, "%.0f°", azimuth));
            if (tvCompass != null) tvCompass.setText(dirName(azimuth));
        } else if (e.sensor.getType() == Sensor.TYPE_STEP_COUNTER) {
            if (stepBase < 0) stepBase = e.values[0];
            stepsToday = (int) (e.values[0] - stepBase);
            if (tvSteps != null) {
                double km = stepsToday * 0.75 / 1000.0;
                tvSteps.setText(stepsToday + " passi  (~"
                    + String.format(java.util.Locale.US, "%.2f km", km) + ")");
            }
        } else if (e.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            // livella: x,y indicano l'inclinazione; filtro per stabilita'
            levelX = levelX * 0.8f + e.values[0] * 0.2f;
            levelY = levelY * 0.8f + e.values[1] * 0.2f;
            if (bubble != null) {
                bubble.setTranslationX(-levelX * 12);
                bubble.setTranslationY(levelY * 12);
            }
            if (tvLevel != null) {
                double inclX = Math.toDegrees(Math.atan2(levelX, 9.81));
                double inclY = Math.toDegrees(Math.atan2(levelY, 9.81));
                boolean flat = Math.abs(inclX) < 1.5 && Math.abs(inclY) < 1.5;
                tvLevel.setText(flat ? "IN BOLLA ✓"
                    : String.format(java.util.Locale.US, "X %.1f°   Y %.1f°", inclX, inclY));
                tvLevel.setTextColor(flat ? 0xFF00FF88 : 0xFFE8F4FD);
            }
        } else if (e.sensor.getType() == Sensor.TYPE_PRESSURE) {
            if (tvPressure != null) {
                float hpa = e.values[0];
                double altBaro = 44330.0 * (1.0 - Math.pow(hpa / 1013.25, 0.1903));
                tvPressure.setText(String.format(java.util.Locale.US,
                    "%.1f hPa  (~%.0f m barometrica)", hpa, altBaro));
            }
        }
    }
    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    private static String dirName(float az) {
        String[] d = {"N", "NE", "E", "SE", "S", "SO", "O", "NO"};
        return d[(int) Math.round(az / 45f) % 8];
    }

    private void bindTool(int id, Class<?> target) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(x -> {
            try { startActivity(new android.content.Intent(this, target)); }
            catch (Exception e) { Toast.makeText(this, "Errore apertura", Toast.LENGTH_SHORT).show(); }
        });
    }

    private void updateLocationLabels() {
        if (!labelsActive) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) {
            if (tvCoords != null) tvCoords.setText("In attesa del GPS...");
            if (tvAltitude != null) tvAltitude.setText("-- m");
            return;
        }
        if (tvCoords != null) tvCoords.setText(String.format(java.util.Locale.US,
            "%.5f, %.5f", loc.getLatitude(), loc.getLongitude()));
        if (tvAltitude != null) tvAltitude.setText(loc.hasAltitude()
            ? String.format(java.util.Locale.US, "%.0f m", loc.getAltitude()) : "-- m");
        // velocita max/media
        if (loc.hasSpeed()) {
            double kmh = loc.getSpeed() * 3.6;
            if (kmh > speedMax) speedMax = kmh;
            speedSum += kmh; speedCount++;
            if (tvSpeedStats != null) {
                double avg = speedCount > 0 ? speedSum / speedCount : 0;
                tvSpeedStats.setText(String.format(java.util.Locale.US,
                    "Max %.0f km/h   Media %.0f km/h", speedMax, avg));
            }
        }
        new Handler(Looper.getMainLooper()).postDelayed(this::updateLocationLabels, 2000);
        updateDistanceLabel(loc);
    }

    // ---- Dove ho parcheggiato ----
    private void saveParking() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit()
            .putString("park_lat", String.valueOf(loc.getLatitude()))
            .putString("park_lon", String.valueOf(loc.getLongitude()))
            .putLong("park_time", System.currentTimeMillis())
            .apply();
        Toast.makeText(this, "Posizione auto salvata!", Toast.LENGTH_SHORT).show();
        refreshParkingLabel();
    }

    private void refreshParkingLabel() {
        String la = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("park_lat", "");
        if (tvParkInfo == null) return;
        if (la.isEmpty()) { tvParkInfo.setText("Nessuna auto salvata"); return; }
        String lo = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("park_lon", "");
        long t = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getLong("park_time", 0);
        String when = android.text.format.DateUtils.getRelativeTimeSpanString(t).toString();
        tvParkInfo.setText("Auto: " + la + ", " + lo + "  (" + when + ")");
    }

    private void gotoParking() {
        String la = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("park_lat", "");
        String lo = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("park_lon", "");
        if (la.isEmpty()) { Toast.makeText(this, "Salva prima l'auto", Toast.LENGTH_SHORT).show(); return; }
        try {
            Intent i = new Intent(this, MapActivity.class);
            i.putExtra("focus_lat", Double.parseDouble(la));
            i.putExtra("focus_lon", Double.parseDouble(lo));
            i.putExtra("focus_label", "La mia auto");
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "Errore", Toast.LENGTH_SHORT).show();
        }
    }

    // ---- SOS messaggio con coordinate ----
    private void sendSosMessage() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        String text = "SOS! Ho bisogno di aiuto. La mia posizione GPS:\n"
            + String.format(java.util.Locale.US, "%.6f, %.6f", loc.getLatitude(), loc.getLongitude())
            + "\nhttps://maps.google.com/?q="
            + String.format(java.util.Locale.US, "%.6f,%.6f", loc.getLatitude(), loc.getLongitude());
        Intent i = new Intent(Intent.ACTION_SEND);
        i.setType("text/plain");
        i.putExtra(Intent.EXTRA_TEXT, text);
        startActivity(Intent.createChooser(i, "Invia SOS con posizione"));
    }

    // ---- Torcia SOS lampeggiante (... --- ...) ----
    private void toggleSosTorch() {
        if (sosRunning) { stopSosTorch(); return; }
        if (camId == null) { Toast.makeText(this, "Flash non disponibile", Toast.LENGTH_SHORT).show(); return; }
        sosRunning = true;
        Toast.makeText(this, "SOS Morse attivo (tocca di nuovo per fermare)", Toast.LENGTH_SHORT).show();
        final int[] pattern = {200,200,200,200,200,500, 600,200,600,200,600,500, 200,200,200,200,200,800};
        runMorse(pattern, 0);
    }

    private void runMorse(final int[] pattern, final int idx) {
        if (!sosRunning) return;
        boolean on = (idx % 2 == 0);
        setTorch(on);
        sosHandler.postDelayed(() -> {
            int next = (idx + 1) % pattern.length;
            runMorse(pattern, next);
        }, pattern[idx]);
    }

    private void setTorch(boolean on) {
        try { if (camMgr != null && camId != null) camMgr.setTorchMode(camId, on); }
        catch (Exception ignored) {}
    }

    private void stopSosTorch() {
        sosRunning = false;
        setTorch(false);
    }

    // ---- Distanza da un punto marcato ----
    private void markDistancePoint() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit()
            .putString("mark_lat", String.valueOf(loc.getLatitude()))
            .putString("mark_lon", String.valueOf(loc.getLongitude()))
            .apply();
        Toast.makeText(this, "Punto di riferimento marcato", Toast.LENGTH_SHORT).show();
        updateDistanceLabel(loc);
    }

    private void updateDistanceLabel(Location loc) {
        if (tvDistInfo == null || loc == null) return;
        String la = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("mark_lat", "");
        if (la.isEmpty()) { tvDistInfo.setText("Nessun punto marcato"); return; }
        try {
            double mlat = Double.parseDouble(la);
            double mlon = Double.parseDouble(
                getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("mark_lon", "0"));
            float[] res = new float[1];
            Location.distanceBetween(loc.getLatitude(), loc.getLongitude(), mlat, mlon, res);
            float m = res[0];
            tvDistInfo.setText(m < 1000
                ? String.format(java.util.Locale.US, "Distanza dal punto: %.0f m", m)
                : String.format(java.util.Locale.US, "Distanza dal punto: %.2f km", m / 1000.0));
        } catch (Exception ignored) {}
    }

    // ---- Cronometro ----
    private void toggleChrono() {
        if (chronoRunning) {
            chronoAccum += System.currentTimeMillis() - chronoStart;
            chronoRunning = false;
        } else {
            chronoStart = System.currentTimeMillis();
            chronoRunning = true;
            chronoTick();
        }
    }

    private void resetChrono() {
        chronoRunning = false;
        chronoAccum = 0;
        if (tvChrono != null) tvChrono.setText("00:00:00");
    }

    private void chronoTick() {
        if (!chronoRunning) return;
        long ms = chronoAccum + (System.currentTimeMillis() - chronoStart);
        long s = ms / 1000;
        if (tvChrono != null) tvChrono.setText(String.format(java.util.Locale.US,
            "%02d:%02d:%02d", s / 3600, (s % 3600) / 60, s % 60));
        chronoHandler.postDelayed(this::chronoTick, 500);
    }
}
"""

LAYOUT_TOOLS = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical"
        android:layout_marginBottom="20dp">
        <Button android:id="@+id/btn_tools_back"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
            android:textSize="13sp" android:layout_marginEnd="12dp"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="STRUMENTI OUTDOOR" android:textColor="#FF6B35"
            android:textSize="20sp" android:textStyle="bold" android:fontFamily="monospace"/>
    </LinearLayout>

    <!-- BUSSOLA + QUOTA -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="BUSSOLA E QUOTA" android:textColor="#00E5FF" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="12dp"/>
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal" android:gravity="center_vertical">
            <ImageView android:id="@+id/iv_compass_rose"
                android:layout_width="90dp" android:layout_height="90dp"
                android:src="@drawable/ic_compass_needle" android:layout_marginEnd="20dp"
                android:contentDescription="Bussola"/>
            <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"
                android:layout_weight="1" android:orientation="vertical">
                <TextView android:id="@+id/tv_compass_dir"
                    android:layout_width="wrap_content" android:layout_height="wrap_content"
                    android:text="N" android:textColor="#00FF88" android:textSize="40sp"
                    android:textStyle="bold" android:fontFamily="monospace"/>
                <TextView android:id="@+id/tv_azimuth"
                    android:layout_width="wrap_content" android:layout_height="wrap_content"
                    android:text="0°" android:textColor="#E8F4FD" android:textSize="20sp"
                    android:fontFamily="monospace"/>
                <TextView android:id="@+id/tv_altitude"
                    android:layout_width="wrap_content" android:layout_height="wrap_content"
                    android:text="-- m" android:textColor="#FFD600" android:textSize="18sp"
                    android:fontFamily="monospace" android:layout_marginTop="4dp"/>
            </LinearLayout>
        </LinearLayout>
        <TextView android:id="@+id/tv_tool_coords"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="In attesa del GPS..." android:textColor="#5A7A99" android:textSize="13sp"
            android:fontFamily="monospace" android:layout_marginTop="10dp"/>
    </LinearLayout>

    <!-- DOVE HO PARCHEGGIATO -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="DOVE HO PARCHEGGIATO" android:textColor="#00FF88" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="4dp"/>
        <TextView android:id="@+id/tv_park_info"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Nessuna auto salvata" android:textColor="#5A7A99" android:textSize="12sp"
            android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal">
            <Button android:id="@+id/btn_save_parking"
                android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
                android:text="Salva auto qui" android:backgroundTint="#00FF88" android:textColor="#050A14"
                android:textStyle="bold" android:textSize="13sp" android:layout_marginEnd="8dp"/>
            <Button android:id="@+id/btn_goto_parking"
                android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
                android:text="Riportami all'auto" android:backgroundTint="#141E2E" android:textColor="#00FF88"
                android:textStyle="bold" android:textSize="13sp"/>
        </LinearLayout>
    </LinearLayout>

    <!-- SOS -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="EMERGENZA SOS" android:textColor="#FF1744" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="12dp"/>
        <Button android:id="@+id/btn_sos_message"
            android:layout_width="match_parent" android:layout_height="50dp"
            android:text="INVIA SOS CON POSIZIONE" android:backgroundTint="#FF1744" android:textColor="#FFFFFF"
            android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
        <Button android:id="@+id/btn_sos_torch"
            android:layout_width="match_parent" android:layout_height="50dp"
            android:text="TORCIA SOS (MORSE)" android:backgroundTint="#FFD600" android:textColor="#050A14"
            android:textStyle="bold" android:textSize="14sp"/>
    </LinearLayout>

    <!-- CONTAPASSI -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="CONTAPASSI" android:textColor="#00E5FF" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="4dp"/>
        <TextView android:id="@+id/tv_steps"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="0 passi" android:textColor="#E8F4FD" android:textSize="18sp"
            android:fontFamily="monospace"/>
    </LinearLayout>

    <!-- DISTANZA DA PUNTO -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="DISTANZA DA UN PUNTO" android:textColor="#FFD600" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="4dp"/>
        <TextView android:id="@+id/tv_dist_info"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Nessun punto marcato" android:textColor="#E8F4FD" android:textSize="16sp"
            android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
        <Button android:id="@+id/btn_mark_point"
            android:layout_width="match_parent" android:layout_height="48dp"
            android:text="Marca questo punto" android:backgroundTint="#FFD600" android:textColor="#050A14"
            android:textStyle="bold" android:textSize="13sp"/>
    </LinearLayout>

    <!-- LIVELLA A BOLLA -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="LIVELLA A BOLLA" android:textColor="#00E5FF" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="12dp"/>
        <FrameLayout android:layout_width="120dp" android:layout_height="120dp"
            android:layout_gravity="center_horizontal" android:background="@drawable/bg_round_card">
            <View android:layout_width="40dp" android:layout_height="40dp"
                android:layout_gravity="center" android:background="@drawable/bg_crosshair"
                android:alpha="0.3"/>
            <View android:id="@+id/view_bubble"
                android:layout_width="28dp" android:layout_height="28dp"
                android:layout_gravity="center" android:background="@drawable/bg_fab_primary"/>
        </FrameLayout>
        <TextView android:id="@+id/tv_level"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="X 0.0°   Y 0.0°" android:textColor="#E8F4FD" android:textSize="16sp"
            android:fontFamily="monospace" android:gravity="center" android:layout_marginTop="10dp"/>
    </LinearLayout>

    <!-- CRONOMETRO -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="CRONOMETRO" android:textColor="#00FF88" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="8dp"/>
        <TextView android:id="@+id/tv_chrono"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="00:00:00" android:textColor="#E8F4FD" android:textSize="32sp"
            android:textStyle="bold" android:fontFamily="monospace" android:gravity="center"
            android:layout_marginBottom="12dp"/>
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal">
            <Button android:id="@+id/btn_chrono_toggle"
                android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
                android:text="Avvia / Pausa" android:backgroundTint="#00FF88" android:textColor="#050A14"
                android:textStyle="bold" android:textSize="13sp" android:layout_marginEnd="8dp"/>
            <Button android:id="@+id/btn_chrono_reset"
                android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
                android:text="Azzera" android:backgroundTint="#141E2E" android:textColor="#00FF88"
                android:textStyle="bold" android:textSize="13sp"/>
        </LinearLayout>
    </LinearLayout>

    <!-- VELOCITA -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="VELOCITA SESSIONE" android:textColor="#FF6B35" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="4dp"/>
        <TextView android:id="@+id/tv_speed_stats"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Max 0 km/h   Media 0 km/h" android:textColor="#E8F4FD" android:textSize="16sp"
            android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
        <Button android:id="@+id/btn_speed_reset"
            android:layout_width="match_parent" android:layout_height="44dp"
            android:text="Azzera velocita" android:backgroundTint="#141E2E" android:textColor="#FF6B35"
            android:textStyle="bold" android:textSize="13sp"/>
    </LinearLayout>

    <!-- PRESSIONE / ALTITUDINE BAROMETRICA -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="18dp"
        android:layout_marginBottom="14dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="PRESSIONE BAROMETRICA" android:textColor="#FFD600" android:textSize="13sp"
            android:textStyle="bold" android:layout_marginBottom="4dp"/>
        <TextView android:id="@+id/tv_pressure"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Sensore non disponibile su questo telefono" android:textColor="#E8F4FD"
            android:textSize="15sp" android:fontFamily="monospace"/>
    </LinearLayout>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="STRUMENTI AVANZATI" android:textColor="#FF6B35" android:textSize="15sp"
        android:textStyle="bold" android:layout_marginTop="8dp" android:layout_marginBottom="12dp"/>
    <Button android:id="@+id/open_area"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="CALCOLO AREA TERRENO" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_recorder"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="REGISTRA TRACCIA (km, dislivello)" android:backgroundTint="#141E2E" android:textColor="#00FF88"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_unitconv"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="CONVERTITORE UNITA" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_timer"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="TIMER" android:backgroundTint="#141E2E" android:textColor="#00FF88"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_slope"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="INCLINOMETRO (pendenza)" android:backgroundTint="#141E2E" android:textColor="#FFD600"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="NUOVI STRUMENTI v3.0" android:textColor="#00E5FF" android:textSize="15sp"
        android:textStyle="bold" android:layout_marginTop="8dp" android:layout_marginBottom="12dp"/>
    <Button android:id="@+id/open_metal"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="METAL DETECTOR (magnetometro)" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_heat"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="TEMPERATURA PERCEPITA" android:backgroundTint="#141E2E" android:textColor="#FF6B35"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_pace"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="TEMPI DI MARCIA (Naismith)" android:backgroundTint="#141E2E" android:textColor="#00FF88"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/open_speedhud"
        android:layout_width="match_parent" android:layout_height="50dp"
        android:text="TACHIMETRO HUD PARABREZZA" android:backgroundTint="#141E2E" android:textColor="#FFD600"
        android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>

</LinearLayout></ScrollView>"""

# ============================================================
#  KIT SOPRAVVIVENZA - menu a schede
# ============================================================
SURVIVAL_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

public class SurvivalActivity extends AppCompatActivity {
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_survival);
        View back = findViewById(R.id.btn_surv_back);
        if (back != null) back.setOnClickListener(v -> finish());
        wire(R.id.card_emergency, EmergencyActivity.class);
        wire(R.id.card_altimeter, AltimeterActivity.class);
        wire(R.id.card_battery, BatterySaverActivity.class);
        wire(R.id.card_proximity, ProximityToolActivity.class);
        wire(R.id.card_coords, CoordsToolActivity.class);
        wire(R.id.card_daylight, DaylightToolActivity.class);
        wire(R.id.card_backtrack, BacktrackActivity.class);
        wire(R.id.card_mirror, SignalMirrorActivity.class);
        wire(R.id.card_whistle, WhistleActivity.class);
        wire(R.id.card_morse, MorseActivity.class);
        wire(R.id.card_suncompass, SunCompassActivity.class);
        wire(R.id.card_guide, SurvGuideActivity.class);
        wire(R.id.card_hydration, HydrationActivity.class);
        wire(R.id.card_checklist, ChecklistActivity.class);
        wire(R.id.card_geonotes, GeoNotesActivity.class);
        wire(R.id.card_gotocoords, GotoCoordsActivity.class);
        wire(R.id.card_flashlight, FlashlightActivity.class);
        wire(R.id.card_calc, CalcActivity.class);
        wire(R.id.card_notepad, NotepadActivity.class);
        wire(R.id.card_currency, CurrencyActivity.class);
        wire(R.id.card_qr, QrPositionActivity.class);
        // NUOVI v3.0
        wire(R.id.card_moon, MoonPhaseActivity.class);
        wire(R.id.card_nightvision, NightVisionActivity.class);
        wire(R.id.card_firstaid, FirstAidActivity.class);
    }
    private void wire(int id, Class<?> target) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(x -> startActivity(new Intent(this, target)));
    }
}
"""

def _surv_card(card_id, title_text, color, desc):
    return ('<LinearLayout android:id="@+id/' + card_id + '"\n'
        '    android:layout_width="match_parent" android:layout_height="wrap_content"\n'
        '    android:orientation="vertical" android:background="@drawable/bg_card_accent" android:padding="20dp"\n'
        '    android:layout_marginBottom="14dp" android:elevation="4dp">\n'
        '    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
        '        android:text="' + title_text + '" android:textColor="' + color + '" android:textSize="17sp"\n'
        '        android:textStyle="bold"/>\n'
        '    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
        '        android:text="' + desc + '" android:textColor="#5A7A99" android:textSize="13sp"\n'
        '        android:layout_marginTop="6dp"/>\n'
        '</LinearLayout>\n')

LAYOUT_SURVIVAL = ("""\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginBottom="20dp">
        <Button android:id="@+id/btn_surv_back"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
            android:textSize="13sp" android:layout_marginEnd="12dp"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="KIT SOPRAVVIVENZA" android:textColor="#FF1744"
            android:textSize="20sp" android:textStyle="bold" android:fontFamily="monospace"/>
    </LinearLayout>

    <LinearLayout android:id="@+id/card_emergency"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="#3A0610" android:padding="22dp"
        android:layout_marginBottom="14dp" android:elevation="6dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="SCHEDA EMERGENZA" android:textColor="#FF1744" android:textSize="19sp"
            android:textStyle="bold"/>
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Posizione enorme e sempre visibile + SMS al 112. Per quando sei in difficolta'."
            android:textColor="#FFAAAA" android:textSize="13sp" android:layout_marginTop="6dp"/>
    </LinearLayout>

"""
    + _surv_card("card_altimeter", "ALTIMETRO + METEO", "#FFD600",
        "Quota precisa e avviso temporale: se la pressione cala, il tempo peggiora.")
    + _surv_card("card_battery", "RISPARMIO BATTERIA", "#00FF88",
        "Stima autonomia, modalita schermo nero e scorciatoie per durare a lungo fuori.")
    + _surv_card("card_moon", "FASE LUNARE [NUOVO]", "#E8F4FD",
        "Quanta luna avrai stanotte: illuminazione e prossima luna piena, offline.")
    + _surv_card("card_nightvision", "VISIONE NOTTURNA [NUOVO]", "#FF1744",
        "Schermo rosso regolabile: leggi la mappa senza rovinare l'occhio al buio.")
    + _surv_card("card_firstaid", "PRIMO SOCCORSO [NUOVO]", "#FF6B35",
        "Guida rapida offline: emorragie, ipotermia, ustioni, RCP, vipera.")
    + _surv_card("card_proximity", "ALLARME PROSSIMITA", "#FF1744",
        "Suona se ti allontani troppo dal campo o dall'auto.")
    + _surv_card("card_coords", "COORDINATE PER SOCCORSI", "#00E5FF",
        "La tua posizione in tutti i formati, da copiare o inviare.")
    + _surv_card("card_daylight", "ORE DI LUCE / TRAMONTO", "#FFD600",
        "Quanta luce solare ti resta prima del buio.")
    + _surv_card("card_backtrack", "ROTTA DI RITORNO", "#00FF88",
        "Fissa la partenza e ti riporto indietro con direzione e distanza.")
    + _surv_card("card_mirror", "SPECCHIO SEGNALE SOS", "#E8F4FD",
        "Schermo bianco lampeggiante per farti vedere da lontano.")
    + _surv_card("card_whistle", "FISCHIETTO SOS", "#FFD600",
        "Tono acuto e forte per attirare l'attenzione.")
    + _surv_card("card_morse", "CODICE MORSE", "#FFD600",
        "Scrivi un messaggio e trasmettilo col flash.")
    + _surv_card("card_suncompass", "NORD DAL SOLE", "#FFD600",
        "Trova il Nord senza bussola, usando il sole.")
    + _surv_card("card_hydration", "IDRATAZIONE", "#00E5FF",
        "Tieni il conto dell'acqua bevuta nella giornata.")
    + _surv_card("card_checklist", "CHECKLIST ZAINO", "#00FF88",
        "Spunta l'attrezzatura prima di partire.")
    + _surv_card("card_guide", "GUIDA SOPRAVVIVENZA", "#FF1744",
        "Regole base e segnali di emergenza, offline.")
    + _surv_card("card_geonotes", "NOTE SUL POSTO", "#00E5FF",
        "Salva appunti legati a un luogo: ti torna dove l'hai scritto.")
    + _surv_card("card_gotocoords", "VAI A COORDINATE", "#00FF88",
        "Inserisci lat/lon e vedi il punto sulla mappa.")
    + _surv_card("card_flashlight", "TORCIA", "#FFD600",
        "Accendi il flash come torcia.")
    + _surv_card("card_calc", "CALCOLATRICE", "#00E5FF",
        "Calcoli rapidi offline.")
    + _surv_card("card_notepad", "BLOCCO NOTE", "#00FF88",
        "Appunti liberi, salvati automaticamente.")
    + _surv_card("card_currency", "CONVERTITORE VALUTE", "#FFD600",
        "Converti EUR, USD, GBP e altre, offline.")
    + _surv_card("card_qr", "QR POSIZIONE", "#00E5FF",
        "Codice visivo della tua posizione.")
    + """
</LinearLayout></ScrollView>""")

PROXIMITY_TOOL_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.location.Location;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.View;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

/** Allarme prossimita': suona/vibra se ti allontani oltre il raggio da un punto fisso. */
public class ProximityToolActivity extends AppCompatActivity {
    private double anchorLat, anchorLon;
    private boolean armed = false;
    private int radiusM = 100;
    private final Handler h = new Handler(Looper.getMainLooper());
    private TextView tvStatus, tvDistance, tvRadius;
    private ToneGenerator tone;
    private Vibrator vib;
    private boolean alarming = false;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_proximity);
        tvStatus = findViewById(R.id.tv_prox_status);
        tvDistance = findViewById(R.id.tv_prox_distance);
        tvRadius = findViewById(R.id.tv_prox_radius);
        View back = findViewById(R.id.btn_prox_back);
        if (back != null) back.setOnClickListener(v -> finish());
        SeekBar sb = findViewById(R.id.sb_radius);
        if (sb != null) {
            sb.setProgress(radiusM);
            sb.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onProgressChanged(SeekBar s, int p, boolean u) {
                    radiusM = Math.max(20, p);
                    if (tvRadius != null) tvRadius.setText("Raggio allarme: " + radiusM + " m");
                }
                public void onStartTrackingTouch(SeekBar s) {}
                public void onStopTrackingTouch(SeekBar s) {}
            });
        }
        View arm = findViewById(R.id.btn_prox_arm);
        if (arm != null) arm.setOnClickListener(v -> toggleArm());
        try { tone = new ToneGenerator(AudioManager.STREAM_ALARM, 100); } catch (Exception ignored) {}
        vib = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        if (tvRadius != null) tvRadius.setText("Raggio allarme: " + radiusM + " m");
    }

    private void toggleArm() {
        if (armed) { armed = false; stopAlarm(); setStatus("Allarme disattivato"); return; }
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        anchorLat = loc.getLatitude(); anchorLon = loc.getLongitude();
        armed = true;
        setStatus("ATTIVO - punto fissato qui");
        loop();
    }

    private void loop() {
        if (!armed) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) {
            float[] res = new float[1];
            Location.distanceBetween(anchorLat, anchorLon, loc.getLatitude(), loc.getLongitude(), res);
            float d = res[0];
            if (tvDistance != null) tvDistance.setText(String.format(java.util.Locale.US,
                "Distanza dal punto: %.0f m", d));
            if (d > radiusM) startAlarm(); else stopAlarm();
        }
        h.postDelayed(this::loop, 1500);
    }

    private void startAlarm() {
        if (alarming) return;
        alarming = true;
        setStatus("!!! TROPPO LONTANO !!!");
        beep();
    }
    private void beep() {
        if (!alarming) return;
        try { if (tone != null) tone.startTone(ToneGenerator.TONE_CDMA_HIGH_L, 400); } catch (Exception ignored) {}
        if (vib != null) {
            if (android.os.Build.VERSION.SDK_INT >= 26)
                vib.vibrate(VibrationEffect.createOneShot(400, VibrationEffect.DEFAULT_AMPLITUDE));
            else vib.vibrate(400);
        }
        h.postDelayed(this::beep, 900);
    }
    private void stopAlarm() {
        if (!alarming) return;
        alarming = false;
        if (armed) setStatus("ATTIVO - sei dentro il raggio");
    }
    private void setStatus(String s) { if (tvStatus != null) tvStatus.setText(s); }

    @Override protected void onDestroy() {
        super.onDestroy(); armed = false; alarming = false;
        if (tone != null) tone.release();
    }
}
"""

COORDS_TOOL_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

/** Convertitore coordinate: decimale, gradi-minuti-secondi, con copia e condivisione. */
public class CoordsToolActivity extends AppCompatActivity {
    private TextView tvDec, tvDms, tvUtm, tvAlt;
    private String shareText = "";
    private boolean active = false;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_coords);
        tvDec = findViewById(R.id.tv_c_dec);
        tvDms = findViewById(R.id.tv_c_dms);
        tvUtm = findViewById(R.id.tv_c_utm);
        tvAlt = findViewById(R.id.tv_c_alt);
        View back = findViewById(R.id.btn_c_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View copy = findViewById(R.id.btn_c_copy);
        if (copy != null) copy.setOnClickListener(v -> copyCoords());
        View share = findViewById(R.id.btn_c_share);
        if (share != null) share.setOnClickListener(v -> shareCoords());
    }

    @Override protected void onResume() { super.onResume(); active = true; refresh(); }
    @Override protected void onPause() { super.onPause(); active = false; }

    private void refresh() {
        if (!active) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) {
            if (tvDec != null) tvDec.setText("In attesa del GPS...");
            new Handler(Looper.getMainLooper()).postDelayed(this::refresh, 1500);
            return;
        }
        double la = loc.getLatitude(), lo = loc.getLongitude();
        String dec = String.format(java.util.Locale.US, "%.6f, %.6f", la, lo);
        String dms = toDms(la, true) + "   " + toDms(lo, false);
        if (tvDec != null) tvDec.setText(dec);
        if (tvDms != null) tvDms.setText(dms);
        if (tvUtm != null) tvUtm.setText("Plus: " + String.format(java.util.Locale.US, "%.4f,%.4f", la, lo));
        if (tvAlt != null) tvAlt.setText(loc.hasAltitude()
            ? String.format(java.util.Locale.US, "Quota: %.0f m", loc.getAltitude()) : "Quota: --");
        shareText = "La mia posizione:\n" + dec + "\n" + dms
            + "\nhttps://maps.google.com/?q=" + String.format(java.util.Locale.US, "%.6f,%.6f", la, lo);
        new Handler(Looper.getMainLooper()).postDelayed(this::refresh, 2000);
    }

    private static String toDms(double v, boolean lat) {
        String hemi = lat ? (v >= 0 ? "N" : "S") : (v >= 0 ? "E" : "O");
        v = Math.abs(v);
        int d = (int) v;
        double mFull = (v - d) * 60;
        int m = (int) mFull;
        double sec = (mFull - m) * 60;
        return String.format(java.util.Locale.US, "%d°%02d'%04.1f\"%s", d, m, sec, hemi);
    }

    private void copyCoords() {
        ClipboardManager cb = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (cb != null && !shareText.isEmpty()) {
            cb.setPrimaryClip(ClipData.newPlainText("coords", shareText));
            Toast.makeText(this, "Coordinate copiate", Toast.LENGTH_SHORT).show();
        }
    }
    private void shareCoords() {
        if (shareText.isEmpty()) return;
        Intent i = new Intent(Intent.ACTION_SEND);
        i.setType("text/plain");
        i.putExtra(Intent.EXTRA_TEXT, shareText);
        startActivity(Intent.createChooser(i, "Condividi posizione"));
    }
}
"""

DAYLIGHT_TOOL_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;
import java.util.Calendar;

/** Ore di luce rimaste e orario tramonto (calcolo solare offline). */
public class DaylightToolActivity extends AppCompatActivity {
    private TextView tvSunset, tvRemaining, tvSunrise, tvNote;
    private boolean active = false;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_daylight);
        tvSunset = findViewById(R.id.tv_sunset);
        tvSunrise = findViewById(R.id.tv_sunrise);
        tvRemaining = findViewById(R.id.tv_remaining);
        tvNote = findViewById(R.id.tv_day_note);
        View back = findViewById(R.id.btn_day_back);
        if (back != null) back.setOnClickListener(v -> finish());
    }

    @Override protected void onResume() { super.onResume(); active = true; refresh(); }
    @Override protected void onPause() { super.onPause(); active = false; }

    private void refresh() {
        if (!active) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) {
            if (tvNote != null) tvNote.setText("In attesa del GPS...");
            new Handler(Looper.getMainLooper()).postDelayed(this::refresh, 1500);
            return;
        }
        Calendar now = Calendar.getInstance();
        int doy = now.get(Calendar.DAY_OF_YEAR);
        double[] sun = sunriseSunset(loc.getLatitude(), loc.getLongitude(), doy,
            now.get(Calendar.ZONE_OFFSET) + now.get(Calendar.DST_OFFSET));
        double sr = sun[0], ss = sun[1];
        if (tvSunrise != null) tvSunrise.setText("Alba: " + hm(sr));
        if (tvSunset != null) tvSunset.setText("Tramonto: " + hm(ss));
        double nowH = now.get(Calendar.HOUR_OF_DAY) + now.get(Calendar.MINUTE) / 60.0;
        double rem = ss - nowH;
        if (tvRemaining != null) {
            if (rem > 0) {
                tvRemaining.setText(hmDur(rem) + " di luce rimaste");
                tvRemaining.setTextColor(rem < 1.5 ? 0xFFFF1744 : 0xFF00FF88);
            } else {
                tvRemaining.setText("E' gia' buio");
                tvRemaining.setTextColor(0xFFFF1744);
            }
        }
        if (tvNote != null) tvNote.setText(rem > 0 && rem < 2
            ? "Poca luce: valuta di montare il campo ora."
            : "Calcolo solare locale (puo' variare di ~15 min).");
        new Handler(Looper.getMainLooper()).postDelayed(this::refresh, 30000);
    }

    // Algoritmo alba/tramonto semplificato (in ore locali).
    private static double[] sunriseSunset(double lat, double lon, int doy, int tzMillis) {
        double tz = tzMillis / 3600000.0;
        double decl = 23.45 * Math.sin(Math.toRadians(360.0 / 365.0 * (doy - 81)));
        double latR = Math.toRadians(lat), declR = Math.toRadians(decl);
        double cosH = -Math.tan(latR) * Math.tan(declR);
        if (cosH > 1) return new double[]{-1, -1};    // sole mai sorto
        if (cosH < -1) return new double[]{0, 24};    // sole sempre alto
        double H = Math.toDegrees(Math.acos(cosH)) / 15.0;
        double solarNoon = 12.0 - lon / 15.0 + tz;
        return new double[]{solarNoon - H, solarNoon + H};
    }

    private static String hm(double h) {
        if (h < 0) return "--";
        h = ((h % 24) + 24) % 24;
        int hh = (int) h; int mm = (int) Math.round((h - hh) * 60);
        if (mm == 60) { mm = 0; hh = (hh + 1) % 24; }
        return String.format(java.util.Locale.US, "%02d:%02d", hh, mm);
    }
    private static String hmDur(double h) {
        int hh = (int) h; int mm = (int) Math.round((h - hh) * 60);
        return hh + "h " + mm + "min";
    }
}
"""

LAYOUT_PROXIMITY = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">
    <Button android:id="@+id/btn_prox_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_marginBottom="20dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="ALLARME PROSSIMITA" android:textColor="#FF1744" android:textSize="22sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="20dp"/>
    <TextView android:id="@+id/tv_prox_radius"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Raggio allarme: 100 m" android:textColor="#E8F4FD" android:textSize="16sp"
        android:fontFamily="monospace" android:layout_marginBottom="8dp"/>
    <SeekBar android:id="@+id/sb_radius"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:max="1000" android:progressTint="#FF1744" android:thumbTint="#FF1744"
        android:layout_marginBottom="20dp"/>
    <TextView android:id="@+id/tv_prox_distance"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Distanza dal punto: --" android:textColor="#00E5FF" android:textSize="18sp"
        android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
    <TextView android:id="@+id/tv_prox_status"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Allarme disattivato" android:textColor="#FFD600" android:textSize="20sp"
        android:textStyle="bold" android:fontFamily="monospace" android:gravity="center"
        android:padding="16dp" android:background="#0D1421" android:layout_marginBottom="20dp"/>
    <Button android:id="@+id/btn_prox_arm"
        android:layout_width="match_parent" android:layout_height="56dp"
        android:text="ATTIVA / DISATTIVA" android:backgroundTint="#FF1744" android:textColor="#FFFFFF"
        android:textStyle="bold" android:textSize="16sp"/>
</LinearLayout></ScrollView>"""

LAYOUT_COORDS = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">
    <Button android:id="@+id/btn_c_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_marginBottom="20dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="COORDINATE" android:textColor="#00E5FF" android:textSize="22sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="20dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Decimale (GPS)" android:textColor="#5A7A99" android:textSize="12sp"/>
    <TextView android:id="@+id/tv_c_dec"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="--" android:textColor="#00FF88" android:textSize="18sp"
        android:fontFamily="monospace" android:layout_marginBottom="16dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Gradi Minuti Secondi" android:textColor="#5A7A99" android:textSize="12sp"/>
    <TextView android:id="@+id/tv_c_dms"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="--" android:textColor="#E8F4FD" android:textSize="16sp"
        android:fontFamily="monospace" android:layout_marginBottom="16dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Posizione" android:textColor="#5A7A99" android:textSize="12sp"/>
    <TextView android:id="@+id/tv_c_utm"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="--" android:textColor="#E8F4FD" android:textSize="15sp"
        android:fontFamily="monospace" android:layout_marginBottom="16dp"/>

    <TextView android:id="@+id/tv_c_alt"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Quota: --" android:textColor="#FFD600" android:textSize="16sp"
        android:fontFamily="monospace" android:layout_marginBottom="24dp"/>

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal">
        <Button android:id="@+id/btn_c_copy"
            android:layout_width="0dp" android:layout_height="52dp" android:layout_weight="1"
            android:text="Copia" android:backgroundTint="#00E5FF" android:textColor="#050A14"
            android:textStyle="bold" android:layout_marginEnd="8dp"/>
        <Button android:id="@+id/btn_c_share"
            android:layout_width="0dp" android:layout_height="52dp" android:layout_weight="1"
            android:text="Condividi" android:backgroundTint="#00FF88" android:textColor="#050A14"
            android:textStyle="bold"/>
    </LinearLayout>
</LinearLayout></ScrollView>"""

LAYOUT_DAYLIGHT = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">
    <Button android:id="@+id/btn_day_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_marginBottom="20dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="ORE DI LUCE" android:textColor="#FFD600" android:textSize="22sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="24dp"/>
    <TextView android:id="@+id/tv_remaining"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="--" android:textColor="#00FF88" android:textSize="28sp"
        android:textStyle="bold" android:fontFamily="monospace" android:gravity="center"
        android:padding="20dp" android:background="#0D1421" android:layout_marginBottom="20dp"/>
    <TextView android:id="@+id/tv_sunrise"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Alba: --" android:textColor="#E8F4FD" android:textSize="20sp"
        android:fontFamily="monospace" android:layout_marginBottom="8dp"/>
    <TextView android:id="@+id/tv_sunset"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Tramonto: --" android:textColor="#FF6B35" android:textSize="20sp"
        android:fontFamily="monospace" android:layout_marginBottom="20dp"/>
    <TextView android:id="@+id/tv_day_note"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="" android:textColor="#5A7A99" android:textSize="13sp"/>
</LinearLayout></ScrollView>"""

SIGNAL_MIRROR_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.WindowManager;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/**
 * Specchio di segnalazione: schermo bianco lampeggiante ad alta luminosita'
 * per farsi vedere da lontano (SOS visivo).
 */
public class SignalMirrorActivity extends AppCompatActivity {
    private final Handler h = new Handler(Looper.getMainLooper());
    private boolean on = true, flashing = true;
    private View root;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_mirror);
        root = findViewById(R.id.mirror_root);
        // massima luminosita'
        WindowManager.LayoutParams lp = getWindow().getAttributes();
        lp.screenBrightness = 1.0f;
        getWindow().setAttributes(lp);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (root != null) root.setOnClickListener(v -> {
            flashing = !flashing;
            if (!flashing) setWhite(true);
        });
        flash();
    }

    private void flash() {
        if (!flashing) { h.postDelayed(this::flash, 200); return; }
        on = !on;
        setWhite(on);
        h.postDelayed(this::flash, 250);  // ~SOS rapido
    }

    private void setWhite(boolean white) {
        if (root != null) root.setBackgroundColor(white ? 0xFFFFFFFF : 0xFF000000);
    }

    @Override protected void onDestroy() { super.onDestroy(); flashing = false; }
}
"""

WHISTLE_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/**
 * Fischietto di emergenza: genera un tono acuto e forte (2.8-3 kHz) per
 * attirare l'attenzione. Suono sintetizzato, nessun file audio.
 */
public class WhistleActivity extends AppCompatActivity {
    private AudioTrack track;
    private volatile boolean playing = false;
    private Thread player;
    private TextView tvState;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_whistle);
        tvState = findViewById(R.id.tv_whistle_state);
        View back = findViewById(R.id.btn_whistle_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View btn = findViewById(R.id.btn_whistle);
        if (btn != null) btn.setOnClickListener(v -> toggle());
    }

    private void toggle() {
        if (playing) { stop(); return; }
        playing = true;
        if (tvState != null) tvState.setText("FISCHIO ATTIVO");
        final int sr = 44100;
        final int freq = 2900;  // frequenza acuta, molto udibile
        player = new Thread(() -> {
            int min = AudioTrack.getMinBufferSize(sr,
                AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT);
            track = new AudioTrack(AudioManager.STREAM_MUSIC, sr,
                AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT,
                Math.max(min, sr), AudioTrack.MODE_STREAM);
            short[] buf = new short[sr / 10];
            track.play();
            double phase = 0;
            boolean pulseOn = true;
            int pulseCount = 0;
            while (playing) {
                // pulsazione tipo fischietto: 0.4s on, 0.1s off
                pulseCount++;
                pulseOn = (pulseCount % 5) < 4;
                for (int i = 0; i < buf.length; i++) {
                    double inc = 2 * Math.PI * freq / sr;
                    phase += inc;
                    buf[i] = pulseOn ? (short) (Math.sin(phase) * 32000) : 0;
                }
                try { track.write(buf, 0, buf.length); } catch (Exception e) { break; }
            }
            try { track.stop(); track.release(); } catch (Exception ignored) {}
        });
        player.start();
    }

    private void stop() {
        playing = false;
        if (tvState != null) tvState.setText("Premi per fischiare");
    }

    @Override protected void onDestroy() { super.onDestroy(); stop(); }
}
"""

BACKTRACK_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.gps.GpsTrackingService;

/**
 * Rotta di ritorno: registra il punto di partenza e ti guida indietro,
 * mostrando direzione (bearing) e distanza per tornare.
 */
public class BacktrackActivity extends AppCompatActivity {
    private double startLat, startLon;
    private boolean tracking = false;
    private final Handler h = new Handler(Looper.getMainLooper());
    private TextView tvState, tvDist, tvBearing, tvHint;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_backtrack);
        tvState = findViewById(R.id.tv_bt_state);
        tvDist = findViewById(R.id.tv_bt_dist);
        tvBearing = findViewById(R.id.tv_bt_bearing);
        tvHint = findViewById(R.id.tv_bt_hint);
        View back = findViewById(R.id.btn_bt_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View mark = findViewById(R.id.btn_bt_mark);
        if (mark != null) mark.setOnClickListener(v -> markStart());
        View show = findViewById(R.id.btn_bt_map);
        if (show != null) show.setOnClickListener(v -> showOnMap());
        // ripristina punto salvato
        String la = prefs().getString("bt_lat", "");
        if (!la.isEmpty()) {
            startLat = Double.parseDouble(la);
            startLon = Double.parseDouble(prefs().getString("bt_lon", "0"));
            tracking = true;
            if (tvState != null) tvState.setText("Punto di partenza salvato");
            loop();
        }
    }

    private android.content.SharedPreferences prefs() {
        return getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE);
    }

    private void markStart() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        startLat = loc.getLatitude(); startLon = loc.getLongitude();
        prefs().edit().putString("bt_lat", String.valueOf(startLat))
            .putString("bt_lon", String.valueOf(startLon)).apply();
        tracking = true;
        if (tvState != null) tvState.setText("Partenza fissata! Ti guido al ritorno.");
        Toast.makeText(this, "Punto di partenza salvato", Toast.LENGTH_SHORT).show();
        loop();
    }

    private void loop() {
        if (!tracking) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) {
            float[] res = new float[2];
            Location.distanceBetween(loc.getLatitude(), loc.getLongitude(), startLat, startLon, res);
            float dist = res[0];
            float bearing = res[1];  // direzione verso la partenza
            if (bearing < 0) bearing += 360;
            if (tvDist != null) tvDist.setText(dist < 1000
                ? String.format(java.util.Locale.US, "%.0f m al ritorno", dist)
                : String.format(java.util.Locale.US, "%.2f km al ritorno", dist / 1000.0));
            if (tvBearing != null) tvBearing.setText(String.format(java.util.Locale.US,
                "Direzione: %.0f° %s", bearing, compass(bearing)));
            if (tvHint != null) tvHint.setText(dist < 15
                ? "Sei tornato al punto di partenza!"
                : "Cammina verso " + compass(bearing) + " seguendo la bussola.");
        }
        h.postDelayed(this::loop, 1500);
    }

    private static String compass(float b) {
        String[] d = {"Nord","Nord-Est","Est","Sud-Est","Sud","Sud-Ovest","Ovest","Nord-Ovest"};
        return d[(int) Math.round(b / 45f) % 8];
    }

    private void showOnMap() {
        if (!tracking) { Toast.makeText(this, "Fissa prima la partenza", Toast.LENGTH_SHORT).show(); return; }
        Intent i = new Intent(this, MapActivity.class);
        i.putExtra("focus_lat", startLat);
        i.putExtra("focus_lon", startLon);
        i.putExtra("focus_label", "Punto di partenza");
        startActivity(i);
    }

    @Override protected void onDestroy() { super.onDestroy(); tracking = false; }
}
"""

LAYOUT_MIRROR = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/mirror_root"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#FFFFFF">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="center" android:text="SOS" android:textColor="#22000000"
        android:textSize="48sp" android:textStyle="bold"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="bottom|center_horizontal" android:layout_marginBottom="40dp"
        android:text="Tocca per fermare il lampeggio" android:textColor="#44000000"
        android:textSize="13sp"/>
</FrameLayout>"""

LAYOUT_WHISTLE = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:padding="20dp" android:background="#050A14"
    android:gravity="center">
    <Button android:id="@+id/btn_whistle_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_gravity="start"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="FISCHIETTO SOS" android:textColor="#FFD600" android:textSize="24sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
    <TextView android:id="@+id/tv_whistle_state"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Premi per fischiare" android:textColor="#5A7A99" android:textSize="16sp"
        android:layout_marginBottom="40dp"/>
    <Button android:id="@+id/btn_whistle"
        android:layout_width="200dp" android:layout_height="200dp"
        android:text="FISCHIA" android:backgroundTint="#FFD600" android:textColor="#050A14"
        android:textStyle="bold" android:textSize="22sp"/>
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Tono acuto e forte per attirare l'attenzione. Tieni il volume al massimo."
        android:textColor="#5A7A99" android:textSize="12sp" android:gravity="center"
        android:layout_marginTop="40dp"/>
</LinearLayout>"""

LAYOUT_BACKTRACK = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">
    <Button android:id="@+id/btn_bt_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_marginBottom="20dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="ROTTA DI RITORNO" android:textColor="#00FF88" android:textSize="22sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="8dp"/>
    <TextView android:id="@+id/tv_bt_state"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Fissa il punto di partenza prima di incamminarti." android:textColor="#5A7A99"
        android:textSize="13sp" android:layout_marginBottom="20dp"/>
    <TextView android:id="@+id/tv_bt_dist"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="-- m al ritorno" android:textColor="#00FF88" android:textSize="26sp"
        android:textStyle="bold" android:fontFamily="monospace" android:gravity="center"
        android:padding="18dp" android:background="#0D1421" android:layout_marginBottom="12dp"/>
    <TextView android:id="@+id/tv_bt_bearing"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Direzione: --" android:textColor="#00E5FF" android:textSize="20sp"
        android:fontFamily="monospace" android:gravity="center" android:layout_marginBottom="12dp"/>
    <TextView android:id="@+id/tv_bt_hint"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="" android:textColor="#FFD600" android:textSize="15sp"
        android:gravity="center" android:layout_marginBottom="24dp"/>
    <Button android:id="@+id/btn_bt_mark"
        android:layout_width="match_parent" android:layout_height="56dp"
        android:text="FISSA PARTENZA QUI" android:backgroundTint="#00FF88" android:textColor="#050A14"
        android:textStyle="bold" android:textSize="16sp" android:layout_marginBottom="12dp"/>
    <Button android:id="@+id/btn_bt_map"
        android:layout_width="match_parent" android:layout_height="52dp"
        android:text="VEDI PARTENZA SU MAPPA" android:backgroundTint="#141E2E" android:textColor="#00FF88"
        android:textStyle="bold" android:textSize="14sp"/>
</LinearLayout></ScrollView>"""

AREA_TOOL_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.location.Location;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;
import java.util.ArrayList;

/** Calcolo area: aggiungi i vertici camminando il perimetro, area con shoelace. */
public class AreaToolActivity extends AppCompatActivity {
    private final ArrayList<double[]> pts = new ArrayList<>();
    private TextView tvArea, tvCount, tvPerim;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_area);
        tvArea = findViewById(R.id.tv_area);
        tvCount = findViewById(R.id.tv_area_count);
        tvPerim = findViewById(R.id.tv_area_perim);
        View back = findViewById(R.id.btn_area_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View add = findViewById(R.id.btn_area_add);
        if (add != null) add.setOnClickListener(v -> addPoint());
        View clr = findViewById(R.id.btn_area_clear);
        if (clr != null) clr.setOnClickListener(v -> { pts.clear(); update(); });
        update();
    }

    private void addPoint() {
        try {
            Location loc = GpsTrackingService.getLastLocation();
            if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
            pts.add(new double[]{loc.getLatitude(), loc.getLongitude()});
            update();
        } catch (Exception e) { Toast.makeText(this, "Errore", Toast.LENGTH_SHORT).show(); }
    }

    private void update() {
        if (tvCount != null) tvCount.setText("Vertici: " + pts.size());
        double area = polygonArea(pts);
        double perim = perimeter(pts);
        if (tvArea != null) {
            if (pts.size() < 3) tvArea.setText("Servono almeno 3 punti");
            else if (area < 10000) tvArea.setText(String.format(java.util.Locale.US, "%.0f m²", area));
            else tvArea.setText(String.format(java.util.Locale.US, "%.2f ettari  (%.0f m²)", area / 10000.0, area));
        }
        if (tvPerim != null) tvPerim.setText(perim < 1000
            ? String.format(java.util.Locale.US, "Perimetro: %.0f m", perim)
            : String.format(java.util.Locale.US, "Perimetro: %.2f km", perim / 1000.0));
    }

    // area poligono su sfera (approssimazione planare locale, ok per piccoli campi)
    private static double polygonArea(ArrayList<double[]> p) {
        if (p.size() < 3) return 0;
        double R = 6371000;
        double lat0 = Math.toRadians(p.get(0)[0]);
        double sum = 0;
        double[] xs = new double[p.size()], ys = new double[p.size()];
        for (int i = 0; i < p.size(); i++) {
            xs[i] = Math.toRadians(p.get(i)[1]) * Math.cos(lat0) * R;
            ys[i] = Math.toRadians(p.get(i)[0]) * R;
        }
        for (int i = 0; i < p.size(); i++) {
            int j = (i + 1) % p.size();
            sum += xs[i] * ys[j] - xs[j] * ys[i];
        }
        return Math.abs(sum) / 2.0;
    }
    private static double perimeter(ArrayList<double[]> p) {
        if (p.size() < 2) return 0;
        double tot = 0; float[] r = new float[1];
        for (int i = 0; i < p.size(); i++) {
            int j = (i + 1) % p.size();
            if (j == 0 && p.size() < 3) break;
            Location.distanceBetween(p.get(i)[0], p.get(i)[1], p.get(j)[0], p.get(j)[1], r);
            tot += r[0];
        }
        return tot;
    }
}
"""

UNIT_CONV_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Convertitore unita' utili in outdoor: distanze, temperature, velocita'. */
public class UnitConvActivity extends AppCompatActivity {
    private EditText input;
    private TextView out;
    private int mode = 0;  // 0 km<->mi, 1 m<->ft, 2 C<->F, 3 kmh<->mph

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_unitconv);
        input = findViewById(R.id.et_unit_in);
        out = findViewById(R.id.tv_unit_out);
        View back = findViewById(R.id.btn_unit_back);
        if (back != null) back.setOnClickListener(v -> finish());
        int[] ids = {R.id.btn_u_dist, R.id.btn_u_len, R.id.btn_u_temp, R.id.btn_u_speed};
        for (int i = 0; i < ids.length; i++) {
            final int m = i;
            View b = findViewById(ids[i]);
            if (b != null) b.setOnClickListener(v -> { mode = m; convert(); });
        }
        if (input != null) input.addTextChangedListener(new TextWatcher() {
            public void onTextChanged(CharSequence c, int a, int b, int d) { convert(); }
            public void beforeTextChanged(CharSequence c, int a, int b, int d) {}
            public void afterTextChanged(Editable e) {}
        });
        convert();
    }

    private void convert() {
        try {
            double v = Double.parseDouble(input.getText().toString());
            String r;
            switch (mode) {
                case 0: r = String.format(java.util.Locale.US, "%.3f miglia\n(%.3f km in input)", v * 0.621371, v); break;
                case 1: r = String.format(java.util.Locale.US, "%.2f piedi\n%.2f yard", v * 3.28084, v * 1.09361); break;
                case 2: r = String.format(java.util.Locale.US, "%.1f °F\n(%.1f °C in input)", v * 9 / 5 + 32, v); break;
                default: r = String.format(java.util.Locale.US, "%.2f mph\n%.2f nodi", v * 0.621371, v * 0.539957); break;
            }
            if (out != null) out.setText(r);
        } catch (Exception e) {
            if (out != null) out.setText("Inserisci un numero");
        }
    }
}
"""

MULTI_TIMER_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Timer da minuti con avviso sonoro a fine conteggio. */
public class MultiTimerActivity extends AppCompatActivity {
    private CountDownTimer timer;
    private TextView tvTime;
    private EditText etMin;
    private ToneGenerator tone;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_timer);
        tvTime = findViewById(R.id.tv_timer);
        etMin = findViewById(R.id.et_timer_min);
        View back = findViewById(R.id.btn_timer_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View start = findViewById(R.id.btn_timer_start);
        if (start != null) start.setOnClickListener(v -> startTimer());
        View stop = findViewById(R.id.btn_timer_stop);
        if (stop != null) stop.setOnClickListener(v -> stopTimer());
        try { tone = new ToneGenerator(AudioManager.STREAM_ALARM, 100); } catch (Exception ignored) {}
    }

    private void startTimer() {
        try {
            int min = Integer.parseInt(etMin.getText().toString());
            if (timer != null) timer.cancel();
            timer = new CountDownTimer(min * 60000L, 1000) {
                public void onTick(long ms) {
                    long s = ms / 1000;
                    if (tvTime != null) tvTime.setText(String.format(java.util.Locale.US,
                        "%02d:%02d", s / 60, s % 60));
                }
                public void onFinish() {
                    if (tvTime != null) tvTime.setText("FINITO!");
                    for (int i = 0; i < 5; i++) {
                        try { if (tone != null) tone.startTone(ToneGenerator.TONE_CDMA_HIGH_L, 500); } catch (Exception ignored) {}
                    }
                }
            }.start();
        } catch (Exception e) { Toast.makeText(this, "Inserisci i minuti", Toast.LENGTH_SHORT).show(); }
    }
    private void stopTimer() {
        if (timer != null) timer.cancel();
        if (tvTime != null) tvTime.setText("00:00");
    }
    @Override protected void onDestroy() {
        super.onDestroy();
        if (timer != null) timer.cancel();
        if (tone != null) tone.release();
    }
}
"""

SLOPE_TOOL_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Inclinometro: misura la pendenza (in gradi e %) appoggiando il telefono. */
public class SlopeToolActivity extends AppCompatActivity implements SensorEventListener {
    private SensorManager sm;
    private Sensor accel;
    private TextView tvDeg, tvPct, tvHint;
    private float fx, fy, fz;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_slope);
        tvDeg = findViewById(R.id.tv_slope_deg);
        tvPct = findViewById(R.id.tv_slope_pct);
        tvHint = findViewById(R.id.tv_slope_hint);
        View back = findViewById(R.id.btn_slope_back);
        if (back != null) back.setOnClickListener(v -> finish());
        sm = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sm != null) accel = sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
    }
    @Override protected void onResume() {
        super.onResume();
        if (sm != null && accel != null) sm.registerListener(this, accel, SensorManager.SENSOR_DELAY_UI);
    }
    @Override protected void onPause() { super.onPause(); if (sm != null) sm.unregisterListener(this); }

    @Override public void onSensorChanged(SensorEvent e) {
        fx = fx * 0.85f + e.values[0] * 0.15f;
        fy = fy * 0.85f + e.values[1] * 0.15f;
        fz = fz * 0.85f + e.values[2] * 0.15f;
        double deg = Math.abs(Math.toDegrees(Math.atan2(Math.sqrt(fx*fx+fy*fy), Math.abs(fz))));
        if (deg > 90) deg = 180 - deg;
        double pct = Math.tan(Math.toRadians(deg)) * 100;
        if (tvDeg != null) tvDeg.setText(String.format(java.util.Locale.US, "%.1f°", deg));
        if (tvPct != null) tvPct.setText(String.format(java.util.Locale.US, "%.0f%% pendenza", pct));
        if (tvHint != null) {
            String h;
            if (deg < 5) h = "Quasi piano";
            else if (deg < 15) h = "Salita dolce";
            else if (deg < 30) h = "Salita ripida";
            else h = "Molto ripido - attenzione!";
            tvHint.setText(h);
        }
    }
    @Override public void onAccuracyChanged(Sensor sensor, int a) {}
}
"""

TRACK_RECORDER_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

/** Registratore traccia: distanza, durata, velocita', dislivello. */
public class TrackRecorderActivity extends AppCompatActivity {
    private boolean recording = false;
    private double totalDist = 0, ascent = 0, descent = 0, maxSpeed = 0;
    private double lastLat, lastLon, lastAlt = Double.NaN;
    private long startTime = 0;
    private final Handler h = new Handler(Looper.getMainLooper());
    private TextView tvDist, tvTime, tvSpeed, tvElev, tvState;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_recorder);
        tvDist = findViewById(R.id.tv_rec_dist);
        tvTime = findViewById(R.id.tv_rec_time);
        tvSpeed = findViewById(R.id.tv_rec_speed);
        tvElev = findViewById(R.id.tv_rec_elev);
        tvState = findViewById(R.id.tv_rec_state);
        View back = findViewById(R.id.btn_rec_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View tgl = findViewById(R.id.btn_rec_toggle);
        if (tgl != null) tgl.setOnClickListener(v -> toggle());
        View rst = findViewById(R.id.btn_rec_reset);
        if (rst != null) rst.setOnClickListener(v -> reset());
    }

    private void toggle() {
        recording = !recording;
        if (recording) {
            if (startTime == 0) startTime = System.currentTimeMillis();
            lastAlt = Double.NaN;
            if (tvState != null) tvState.setText("REGISTRAZIONE IN CORSO");
            loop();
        } else {
            if (tvState != null) tvState.setText("In pausa");
        }
    }
    private void reset() {
        recording = false; totalDist = ascent = descent = maxSpeed = 0;
        startTime = 0; lastAlt = Double.NaN;
        if (tvState != null) tvState.setText("Pronto");
        render();
    }

    private void loop() {
        if (!recording) return;
        try {
            Location loc = GpsTrackingService.getLastLocation();
            if (loc != null) {
                if (lastLat != 0 || lastLon != 0) {
                    float[] r = new float[1];
                    Location.distanceBetween(lastLat, lastLon, loc.getLatitude(), loc.getLongitude(), r);
                    if (r[0] > 1 && r[0] < 100) totalDist += r[0];
                }
                lastLat = loc.getLatitude(); lastLon = loc.getLongitude();
                if (loc.hasAltitude()) {
                    double a = loc.getAltitude();
                    if (!Double.isNaN(lastAlt)) {
                        double d = a - lastAlt;
                        if (d > 0.5) ascent += d; else if (d < -0.5) descent += -d;
                    }
                    lastAlt = a;
                }
                if (loc.hasSpeed()) { double k = loc.getSpeed() * 3.6; if (k > maxSpeed) maxSpeed = k; }
            }
            render();
        } catch (Exception ignored) {}
        h.postDelayed(this::loop, 2000);
    }

    private void render() {
        if (tvDist != null) tvDist.setText(totalDist < 1000
            ? String.format(java.util.Locale.US, "%.0f m", totalDist)
            : String.format(java.util.Locale.US, "%.2f km", totalDist / 1000.0));
        if (tvTime != null && startTime > 0) {
            long sec = (System.currentTimeMillis() - startTime) / 1000;
            tvTime.setText(String.format(java.util.Locale.US, "%02d:%02d:%02d",
                sec / 3600, (sec % 3600) / 60, sec % 60));
        }
        if (tvSpeed != null) tvSpeed.setText(String.format(java.util.Locale.US, "Max %.0f km/h", maxSpeed));
        if (tvElev != null) tvElev.setText(String.format(java.util.Locale.US,
            "Salita %.0f m  Discesa %.0f m", ascent, descent));
    }
    @Override protected void onDestroy() { super.onDestroy(); recording = false; }
}
"""

MORSE_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Traduce testo in Morse e lo trasmette col flash. */
public class MorseActivity extends AppCompatActivity {
    private EditText input;
    private TextView tvCode;
    private android.hardware.camera2.CameraManager cam;
    private String camId;
    private final Handler h = new Handler(Looper.getMainLooper());
    private boolean sending = false;

    private static final java.util.Map<Character,String> M = new java.util.HashMap<>();
    static {
        String[][] t = {{"A",".-"},{"B","-..."},{"C","-.-."},{"D","-.."},{"E","."},{"F","..-."},
        {"G","--."},{"H","...."},{"I",".."},{"J",".---"},{"K","-.-"},{"L",".-.."},{"M","--"},
        {"N","-."},{"O","---"},{"P",".--."},{"Q","--.-"},{"R",".-."},{"S","..."},{"T","-"},
        {"U","..-"},{"V","...-"},{"W",".--"},{"X","-..-"},{"Y","-.--"},{"Z","--.."},
        {"0","-----"},{"1",".----"},{"2","..---"},{"3","...--"},{"4","....-"},{"5","....."},
        {"6","-...."},{"7","--..."},{"8","---.."},{"9","----."}};
        for (String[] e : t) M.put(e[0].charAt(0), e[1]);
    }

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_morse);
        input = findViewById(R.id.et_morse);
        tvCode = findViewById(R.id.tv_morse_code);
        View back = findViewById(R.id.btn_morse_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View tr = findViewById(R.id.btn_morse_translate);
        if (tr != null) tr.setOnClickListener(v -> translate());
        View send = findViewById(R.id.btn_morse_send);
        if (send != null) send.setOnClickListener(v -> sendFlash());
        cam = (android.hardware.camera2.CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            if (cam != null) for (String id : cam.getCameraIdList()) {
                Boolean f = cam.getCameraCharacteristics(id)
                    .get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE);
                if (Boolean.TRUE.equals(f)) { camId = id; break; }
            }
        } catch (Exception ignored) {}
    }

    private String toMorse() {
        StringBuilder sb = new StringBuilder();
        for (char c : input.getText().toString().toUpperCase().toCharArray()) {
            if (c == ' ') sb.append(" / ");
            else if (M.containsKey(c)) sb.append(M.get(c)).append(" ");
        }
        return sb.toString().trim();
    }
    private void translate() { if (tvCode != null) tvCode.setText(toMorse()); }

    private void sendFlash() {
        if (sending || camId == null) return;
        String code = toMorse();
        sending = true;
        final int unit = 250;
        long delay = 0;
        for (char c : code.toCharArray()) {
            final long d = delay;
            if (c == '.') { schedule(true, d); delay += unit; schedule(false, delay); delay += unit; }
            else if (c == '-') { schedule(true, d); delay += unit * 3; schedule(false, delay); delay += unit; }
            else delay += unit * 2;
        }
        h.postDelayed(() -> sending = false, delay + 200);
    }
    private void schedule(boolean on, long at) {
        h.postDelayed(() -> {
            try { if (cam != null && camId != null) cam.setTorchMode(camId, on); }
            catch (Exception ignored) {}
        }, at);
    }
    @Override protected void onDestroy() {
        super.onDestroy();
        h.removeCallbacksAndMessages(null);
        try { if (cam != null && camId != null) cam.setTorchMode(camId, false); } catch (Exception ignored) {}
    }
}
"""

SUN_COMPASS_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import java.util.Calendar;

/** Trova il Nord usando il sole e l'ora, senza bussola magnetica. */
public class SunCompassActivity extends AppCompatActivity {
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_suncompass);
        View back = findViewById(R.id.btn_sun_back);
        if (back != null) back.setOnClickListener(v -> finish());
        Calendar c = Calendar.getInstance();
        int hour = c.get(Calendar.HOUR_OF_DAY);
        TextView t = findViewById(R.id.tv_sun_info);
        String txt;
        if (hour >= 6 && hour <= 9)
            txt = "Mattina: il sole e' a EST.\nPuntalo: il Nord e' alla tua sinistra.";
        else if (hour > 9 && hour < 15)
            txt = "Mezzogiorno: il sole e' a SUD (in Italia).\nLa tua ombra punta a NORD.";
        else if (hour >= 15 && hour <= 19)
            txt = "Pomeriggio: il sole e' a OVEST.\nPuntalo: il Nord e' alla tua destra.";
        else
            txt = "Di notte: cerca la Stella Polare.\nE' allineata con le due stelle finali del Grande Carro.";
        if (t != null) t.setText(txt);
    }
}
"""

HYDRATION_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;

/** Contatore acqua/idratazione giornaliero per attivita' outdoor. */
public class HydrationActivity extends AppCompatActivity {
    private int ml = 0;
    private TextView tvMl, tvGoal;
    private static final int GOAL = 3000;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_hydration);
        tvMl = findViewById(R.id.tv_hydra_ml);
        tvGoal = findViewById(R.id.tv_hydra_goal);
        ml = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getInt("hydra_ml", 0);
        View back = findViewById(R.id.btn_hydra_back);
        if (back != null) back.setOnClickListener(v -> finish());
        bind(R.id.btn_add_250, 250);
        bind(R.id.btn_add_500, 500);
        bind(R.id.btn_add_1000, 1000);
        View rst = findViewById(R.id.btn_hydra_reset);
        if (rst != null) rst.setOnClickListener(v -> { ml = 0; save(); });
        render();
    }
    private void bind(int id, int amount) {
        View b = findViewById(id);
        if (b != null) b.setOnClickListener(v -> { ml += amount; save(); });
    }
    private void save() {
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit().putInt("hydra_ml", ml).apply();
        render();
    }
    private void render() {
        if (tvMl != null) tvMl.setText(String.format(java.util.Locale.US, "%.1f L", ml / 1000.0));
        if (tvGoal != null) {
            int pct = Math.min(100, ml * 100 / GOAL);
            tvGoal.setText("Obiettivo: " + (GOAL/1000) + " L   (" + pct + "%)");
        }
    }
}
"""

SURV_GUIDE_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Guida rapida di sopravvivenza (riferimento offline). */
public class SurvGuideActivity extends AppCompatActivity {
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_survguide);
        View back = findViewById(R.id.btn_guide_back);
        if (back != null) back.setOnClickListener(v -> finish());
    }
}
"""

CHECKLIST_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;

/** Checklist attrezzatura outdoor, con stato salvato. */
public class ChecklistActivity extends AppCompatActivity {
    private static final String[] ITEMS = {
        "Acqua (almeno 2L)", "Cibo / razioni", "Coltello multiuso",
        "Accendino / fiammiferi", "Torcia + batterie", "Kit pronto soccorso",
        "Powerbank carico", "Mappa offline scaricata", "Giacca antipioggia",
        "Coperta termica", "Fischietto", "Corda / paracord", "Bussola",
        "Crema solare", "Repellente insetti", "Sacchetti impermeabili"
    };

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_checklist);
        View back = findViewById(R.id.btn_check_back);
        if (back != null) back.setOnClickListener(v -> finish());
        LinearLayout box = findViewById(R.id.checklist_box);
        if (box == null) return;
        android.content.SharedPreferences p = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE);
        for (int i = 0; i < ITEMS.length; i++) {
            final String key = "chk_" + i;
            CheckBox cb = new CheckBox(this);
            cb.setText(ITEMS[i]);
            cb.setTextColor(0xFFE8F4FD);
            cb.setTextSize(16);
            cb.setPadding(0, 18, 0, 18);
            cb.setChecked(p.getBoolean(key, false));
            cb.setOnCheckedChangeListener((b, checked) ->
                p.edit().putBoolean(key, checked).apply());
            box.addView(cb);
        }
        View rst = findViewById(R.id.btn_check_reset);
        if (rst != null) rst.setOnClickListener(v -> {
            android.content.SharedPreferences.Editor ed = p.edit();
            for (int i = 0; i < ITEMS.length; i++) ed.putBoolean("chk_" + i, false);
            ed.apply();
            recreate();
        });
    }
}
"""

# --- Helper per i layout degli strumenti (header + blocchi riusabili) ---
def _tool_header(title_text, back_id, color):
    # v4.0: pillola "indietro" con ripple, titolo luminoso e barretta colorata
    return ('<Button android:id="@+id/' + back_id + '"\n'
        '    android:layout_width="wrap_content" android:layout_height="40dp"\n'
        '    android:text="&#8249;  INDIETRO" android:background="@drawable/bg_pill_back" android:textColor="#E8F4FD"\n'
        '    android:textSize="12sp" android:textStyle="bold" android:letterSpacing="0.08"\n'
        '    android:paddingStart="16dp" android:paddingEnd="18dp" android:minWidth="0dp" android:minHeight="0dp"\n'
        '    android:stateListAnimator="@null" android:layout_marginBottom="18dp"/>\n'
        '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
        '    android:text="' + title_text + '" android:textColor="' + color + '" android:textSize="23sp"\n'
        '    android:textStyle="bold" android:fontFamily="sans-serif-condensed" android:letterSpacing="0.05"\n'
        '    android:shadowColor="' + color + '" android:shadowRadius="16"/>\n'
        '<View android:layout_width="48dp" android:layout_height="3dp" android:background="' + color + '"\n'
        '    android:layout_marginTop="6dp" android:layout_marginBottom="20dp"/>')

def _scroll(inner):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:layout_width="match_parent" android:layout_height="match_parent"\n'
        '    android:background="@drawable/bg_screen_grad">\n'
        '<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
        '    android:orientation="vertical" android:padding="20dp">\n'
        + inner +
        '\n</LinearLayout></ScrollView>')

def _big(vid, text, color):
    return ('<TextView android:id="@+id/' + vid + '"\n'
        '    android:layout_width="match_parent" android:layout_height="wrap_content"\n'
        '    android:text="' + text + '" android:textColor="' + color + '" android:textSize="26sp"\n'
        '    android:textStyle="bold" android:fontFamily="monospace" android:gravity="center"\n'
        '    android:padding="18dp" android:background="@drawable/bg_card_glass" android:layout_marginBottom="12dp"/>')

def _btn(vid, text, bg, fg="#050A14"):
    return ('<Button android:id="@+id/' + vid + '"\n'
        '    android:layout_width="match_parent" android:layout_height="52dp"\n'
        '    android:text="' + text + '" android:backgroundTint="' + bg + '" android:textColor="' + fg + '"\n'
        '    android:textStyle="bold" android:textSize="14sp" android:layout_marginBottom="10dp"/>')

LAYOUT_AREA = _scroll(_tool_header("CALCOLO AREA", "btn_area_back", "#00E5FF")
    + _big("tv_area", "Servono almeno 3 punti", "#00FF88")
    + _big("tv_area_count", "Vertici: 0", "#E8F4FD")
    + _big("tv_area_perim", "Perimetro: 0 m", "#FFD600")
    + _btn("btn_area_add", "AGGIUNGI PUNTO (sono qui)", "#00FF88")
    + _btn("btn_area_clear", "Cancella tutto", "#141E2E", "#FF6B35"))

LAYOUT_UNITCONV = _scroll(_tool_header("CONVERTITORE", "btn_unit_back", "#00E5FF")
    + '<EditText android:id="@+id/et_unit_in" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberDecimal"\n'
      '    android:hint="Inserisci valore" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="22sp" android:layout_marginBottom="16dp"/>\n'
    + _big("tv_unit_out", "Inserisci un numero", "#00FF88")
    + _btn("btn_u_dist", "km > miglia", "#141E2E", "#00E5FF")
    + _btn("btn_u_len", "m > piedi", "#141E2E", "#00E5FF")
    + _btn("btn_u_temp", "C > F", "#141E2E", "#FFD600")
    + _btn("btn_u_speed", "km/h > mph", "#141E2E", "#FFD600"))

LAYOUT_TIMER = _scroll(_tool_header("TIMER", "btn_timer_back", "#00FF88")
    + '<EditText android:id="@+id/et_timer_min" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="number" android:hint="Minuti"\n'
      '    android:textColor="#E8F4FD" android:textColorHint="#5A7A99" android:textSize="20sp"\n'
      '    android:layout_marginBottom="16dp"/>\n'
    + _big("tv_timer", "00:00", "#00FF88")
    + _btn("btn_timer_start", "AVVIA", "#00FF88")
    + _btn("btn_timer_stop", "Ferma", "#141E2E", "#FF6B35"))

LAYOUT_SLOPE = _scroll(_tool_header("INCLINOMETRO", "btn_slope_back", "#FFD600")
    + _big("tv_slope_deg", "0°", "#00FF88")
    + _big("tv_slope_pct", "0% pendenza", "#00E5FF")
    + _big("tv_slope_hint", "Appoggia il telefono sulla superficie", "#E8F4FD"))

LAYOUT_RECORDER = _scroll(_tool_header("REGISTRA TRACCIA", "btn_rec_back", "#00FF88")
    + _big("tv_rec_state", "Pronto", "#FFD600")
    + _big("tv_rec_dist", "0 m", "#00FF88")
    + _big("tv_rec_time", "00:00:00", "#E8F4FD")
    + _big("tv_rec_speed", "Max 0 km/h", "#00E5FF")
    + _big("tv_rec_elev", "Salita 0 m  Discesa 0 m", "#FFD600")
    + _btn("btn_rec_toggle", "AVVIA / PAUSA", "#00FF88")
    + _btn("btn_rec_reset", "Azzera", "#141E2E", "#FF6B35"))

LAYOUT_MORSE = _scroll(_tool_header("CODICE MORSE", "btn_morse_back", "#FFD600")
    + '<EditText android:id="@+id/et_morse" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:hint="Scrivi un messaggio"\n'
      '    android:textColor="#E8F4FD" android:textColorHint="#5A7A99" android:textSize="18sp"\n'
      '    android:layout_marginBottom="16dp"/>\n'
    + _big("tv_morse_code", "... --- ...", "#FFD600")
    + _btn("btn_morse_translate", "TRADUCI", "#00E5FF")
    + _btn("btn_morse_send", "TRASMETTI COL FLASH", "#FFD600"))

LAYOUT_SUNCOMPASS = _scroll(_tool_header("NORD DAL SOLE", "btn_sun_back", "#FFD600")
    + _big("tv_sun_info", "Calcolo...", "#E8F4FD"))

LAYOUT_HYDRATION = _scroll(_tool_header("IDRATAZIONE", "btn_hydra_back", "#00E5FF")
    + _big("tv_hydra_ml", "0.0 L", "#00E5FF")
    + _big("tv_hydra_goal", "Obiettivo: 3 L", "#5A7A99")
    + _btn("btn_add_250", "+ 250 ml (bicchiere)", "#00E5FF")
    + _btn("btn_add_500", "+ 500 ml (bottiglietta)", "#00E5FF")
    + _btn("btn_add_1000", "+ 1 L (borraccia)", "#00E5FF")
    + _btn("btn_hydra_reset", "Azzera giornata", "#141E2E", "#FF6B35"))

LAYOUT_CHECKLIST = _scroll(_tool_header("CHECKLIST ZAINO", "btn_check_back", "#00FF88")
    + '<LinearLayout android:id="@+id/checklist_box" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:orientation="vertical"\n'
      '    android:layout_marginBottom="16dp"/>\n'
    + _btn("btn_check_reset", "Azzera tutto", "#141E2E", "#FF6B35"))

LAYOUT_SURVGUIDE = _scroll(_tool_header("GUIDA SOPRAVVIVENZA", "btn_guide_back", "#FF1744")
    + '<TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
      '    android:text="REGOLA DEL 3:\\n3 minuti senza aria\\n3 ore senza riparo (freddo)\\n3 giorni senza acqua\\n3 settimane senza cibo\\n\\nPRIORITA IN EMERGENZA:\\n1. Mantieni la calma, respira\\n2. Ripara dal freddo/caldo\\n3. Segnala la posizione (SOS, fuoco, specchio)\\n4. Trova acqua pulita\\n5. Resta vicino a un punto noto\\n\\nSEGNALE SOS:\\n3 segnali ripetuti (fischi, lampi, fuochi)\\nTriangolo = richiesta soccorso\\n\\nACQUA:\\nRaccogli pioggia/rugiada\\nBolli 1 min prima di bere\\nEvita acqua stagnante\\n\\nIPOTERMIA:\\nMuoviti, copri testa e collo\\nNon dormire se hai molto freddo\\nStrati asciutti vicino alla pelle"\n'
      '    android:textColor="#E8F4FD" android:textSize="15sp" android:lineSpacingMultiplier="1.3"\n'
      '    android:background="@drawable/bg_card_glass" android:padding="18dp"/>')

GEONOTES_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.location.Location;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.gps.GpsTrackingService;
import org.json.JSONArray;
import org.json.JSONObject;

/** Note geolocalizzate: appunti legati a una posizione GPS, salvati localmente. */
public class GeoNotesActivity extends AppCompatActivity {
    private LinearLayout listBox;
    private EditText etNote;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_geonotes);
        listBox = findViewById(R.id.notes_box);
        etNote = findViewById(R.id.et_note);
        View back = findViewById(R.id.btn_notes_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View add = findViewById(R.id.btn_note_add);
        if (add != null) add.setOnClickListener(v -> addNote());
        render();
    }

    private JSONArray load() {
        try {
            String raw = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("geonotes", "[]");
            return new JSONArray(raw);
        } catch (Exception e) { return new JSONArray(); }
    }
    private void save(JSONArray arr) {
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit()
            .putString("geonotes", arr.toString()).apply();
    }

    private void addNote() {
        try {
            String txt = etNote.getText().toString().trim();
            if (txt.isEmpty()) { Toast.makeText(this, "Scrivi una nota", Toast.LENGTH_SHORT).show(); return; }
            Location loc = GpsTrackingService.getLastLocation();
            if (loc == null) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
            JSONArray arr = load();
            JSONObject o = new JSONObject();
            o.put("text", txt);
            o.put("lat", loc.getLatitude());
            o.put("lon", loc.getLongitude());
            o.put("time", System.currentTimeMillis());
            arr.put(o);
            save(arr);
            etNote.setText("");
            render();
        } catch (Exception e) { Toast.makeText(this, "Errore", Toast.LENGTH_SHORT).show(); }
    }

    private void render() {
        if (listBox == null) return;
        listBox.removeAllViews();
        JSONArray arr = load();
        if (arr.length() == 0) {
            TextView empty = new TextView(this);
            empty.setText("Nessuna nota. Scrivi un appunto legato a dove sei ora.");
            empty.setTextColor(0xFF5A7A99); empty.setTextSize(14); empty.setPadding(0, 20, 0, 0);
            listBox.addView(empty);
            return;
        }
        for (int i = arr.length() - 1; i >= 0; i--) {
            try {
                final JSONObject o = arr.getJSONObject(i);
                final int idx = i;
                LinearLayout card = new LinearLayout(this);
                card.setOrientation(LinearLayout.VERTICAL);
                card.setBackgroundColor(0xFF0D1421);
                card.setPadding(28, 24, 28, 24);
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
                lp.bottomMargin = 20; card.setLayoutParams(lp);

                TextView t = new TextView(this);
                t.setText(o.getString("text"));
                t.setTextColor(0xFFE8F4FD); t.setTextSize(16);
                card.addView(t);

                TextView c = new TextView(this);
                c.setText(String.format(java.util.Locale.US, "%.5f, %.5f",
                    o.getDouble("lat"), o.getDouble("lon")));
                c.setTextColor(0xFF00E5FF); c.setTextSize(12);
                c.setPadding(0, 8, 0, 0);
                card.addView(c);

                LinearLayout row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setPadding(0, 12, 0, 0);
                TextView goBtn = new TextView(this);
                goBtn.setText("VEDI SU MAPPA");
                goBtn.setTextColor(0xFF00FF88); goBtn.setTextSize(13);
                goBtn.setPadding(0, 0, 40, 0);
                goBtn.setOnClickListener(v -> {
                    try {
                        Intent in = new Intent(this, MapActivity.class);
                        in.putExtra("focus_lat", o.getDouble("lat"));
                        in.putExtra("focus_lon", o.getDouble("lon"));
                        in.putExtra("focus_label", o.getString("text"));
                        startActivity(in);
                    } catch (Exception ignored) {}
                });
                row.addView(goBtn);
                TextView delBtn = new TextView(this);
                delBtn.setText("ELIMINA");
                delBtn.setTextColor(0xFFFF1744); delBtn.setTextSize(13);
                delBtn.setOnClickListener(v -> deleteNote(idx));
                row.addView(delBtn);
                card.addView(row);

                listBox.addView(card);
            } catch (Exception ignored) {}
        }
    }

    private void deleteNote(int idx) {
        try {
            JSONArray arr = load();
            JSONArray out = new JSONArray();
            for (int i = 0; i < arr.length(); i++) if (i != idx) out.put(arr.get(i));
            save(out);
            render();
        } catch (Exception ignored) {}
    }
}
"""

GOTOCOORDS_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Vai a coordinate: inserisci lat/lon e le vedi sulla mappa. */
public class GotoCoordsActivity extends AppCompatActivity {
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_gotocoords);
        View back = findViewById(R.id.btn_goto_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View go = findViewById(R.id.btn_goto_show);
        if (go != null) go.setOnClickListener(v -> show());
    }
    private void show() {
        try {
            EditText la = findViewById(R.id.et_lat);
            EditText lo = findViewById(R.id.et_lon);
            double lat = Double.parseDouble(la.getText().toString().trim());
            double lon = Double.parseDouble(lo.getText().toString().trim());
            if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
                Toast.makeText(this, "Coordinate fuori range", Toast.LENGTH_SHORT).show();
                return;
            }
            Intent i = new Intent(this, MapActivity.class);
            i.putExtra("focus_lat", lat);
            i.putExtra("focus_lon", lon);
            i.putExtra("focus_label", "Punto inserito");
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "Inserisci numeri validi (es. 41.9028)", Toast.LENGTH_SHORT).show();
        }
    }
}
"""

LAYOUT_GEONOTES = _scroll(_tool_header("NOTE SUL POSTO", "btn_notes_back", "#00E5FF")
    + '<EditText android:id="@+id/et_note" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:hint="Scrivi un appunto su questo luogo"\n'
      '    android:textColor="#E8F4FD" android:textColorHint="#5A7A99" android:textSize="16sp"\n'
      '    android:minLines="2" android:gravity="top" android:background="#0D1421"\n'
      '    android:padding="14dp" android:layout_marginBottom="12dp"/>\n'
    + _btn("btn_note_add", "SALVA NOTA QUI", "#00E5FF")
    + '<LinearLayout android:id="@+id/notes_box" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:orientation="vertical"\n'
      '    android:layout_marginTop="16dp"/>')

LAYOUT_GOTOCOORDS = _scroll(_tool_header("VAI A COORDINATE", "btn_goto_back", "#00FF88")
    + '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Latitudine" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_lat" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberSigned|numberDecimal"\n'
      '    android:hint="es. 41.9028" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="16dp"/>\n'
      '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Longitudine" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_lon" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberSigned|numberDecimal"\n'
      '    android:hint="es. 12.4964" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="24dp"/>\n'
    + _btn("btn_goto_show", "MOSTRA SULLA MAPPA", "#00FF88"))

FLASHLIGHT_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

public class FlashlightActivity extends AppCompatActivity {
    private android.hardware.camera2.CameraManager cam;
    private String camId;
    private boolean on = false;
    private TextView tvState;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_flashlight);
        tvState = findViewById(R.id.tv_flash_state);
        View back = findViewById(R.id.btn_flash_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View btn = findViewById(R.id.btn_flash_toggle);
        if (btn != null) btn.setOnClickListener(v -> toggle());
        cam = (android.hardware.camera2.CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            if (cam != null) for (String id : cam.getCameraIdList()) {
                Boolean f = cam.getCameraCharacteristics(id)
                    .get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE);
                if (Boolean.TRUE.equals(f)) { camId = id; break; }
            }
        } catch (Exception ignored) {}
    }
    private void toggle() {
        if (camId == null) { Toast.makeText(this, "Flash non disponibile", Toast.LENGTH_SHORT).show(); return; }
        try {
            on = !on;
            cam.setTorchMode(camId, on);
            if (tvState != null) tvState.setText(on ? "ACCESA" : "Spenta");
        } catch (Exception e) { Toast.makeText(this, "Errore", Toast.LENGTH_SHORT).show(); }
    }
    @Override protected void onDestroy() {
        super.onDestroy();
        try { if (cam != null && camId != null) cam.setTorchMode(camId, false); } catch (Exception ignored) {}
    }
}
"""

CALC_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

public class CalcActivity extends AppCompatActivity {
    private TextView display;
    private StringBuilder expr = new StringBuilder();

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_calc);
        display = findViewById(R.id.calc_display);
        View back = findViewById(R.id.btn_calc_back);
        if (back != null) back.setOnClickListener(v -> finish());
        int[] ids = {R.id.k0,R.id.k1,R.id.k2,R.id.k3,R.id.k4,R.id.k5,R.id.k6,R.id.k7,R.id.k8,R.id.k9,
            R.id.kdot,R.id.kplus,R.id.kminus,R.id.kmul,R.id.kdiv};
        for (int id : ids) {
            Button b = findViewById(id);
            if (b != null) b.setOnClickListener(v -> { expr.append(((Button)v).getText()); show(); });
        }
        View eq = findViewById(R.id.keq);
        if (eq != null) eq.setOnClickListener(v -> calc());
        View clr = findViewById(R.id.kclear);
        if (clr != null) clr.setOnClickListener(v -> { expr.setLength(0); show(); });
    }
    private void show() { if (display != null) display.setText(expr.length()==0 ? "0" : expr.toString()); }
    private void calc() {
        try {
            double r = eval(expr.toString());
            expr.setLength(0);
            expr.append(r == Math.floor(r) ? String.valueOf((long)r) : String.valueOf(r));
            show();
        } catch (Exception e) { if (display != null) display.setText("Errore"); expr.setLength(0); }
    }
    // valutatore semplice +-*/ con precedenza
    private double eval(String s) {
        java.util.List<Double> nums = new java.util.ArrayList<>();
        java.util.List<Character> ops = new java.util.ArrayList<>();
        int i = 0; StringBuilder num = new StringBuilder();
        while (i < s.length()) {
            char c = s.charAt(i);
            if (Character.isDigit(c) || c == '.') num.append(c);
            else { nums.add(Double.parseDouble(num.toString())); num.setLength(0); ops.add(c); }
            i++;
        }
        nums.add(Double.parseDouble(num.toString()));
        // prima * e /
        for (int k = 0; k < ops.size(); ) {
            char op = ops.get(k);
            if (op == '*' || op == '/') {
                double r = op == '*' ? nums.get(k)*nums.get(k+1) : nums.get(k)/nums.get(k+1);
                nums.set(k, r); nums.remove(k+1); ops.remove(k);
            } else k++;
        }
        double res = nums.get(0);
        for (int k = 0; k < ops.size(); k++) {
            res = ops.get(k) == '+' ? res + nums.get(k+1) : res - nums.get(k+1);
        }
        return res;
    }
}
"""

NOTEPAD_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;

public class NotepadActivity extends AppCompatActivity {
    private EditText et;
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_notepad);
        et = findViewById(R.id.et_notepad);
        View back = findViewById(R.id.btn_notepad_back);
        if (back != null) back.setOnClickListener(v -> finish());
        if (et != null) {
            et.setText(getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString("notepad", ""));
            et.addTextChangedListener(new TextWatcher() {
                public void afterTextChanged(Editable e) {
                    getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit()
                        .putString("notepad", e.toString()).apply();
                }
                public void beforeTextChanged(CharSequence c,int a,int b,int d){}
                public void onTextChanged(CharSequence c,int a,int b,int d){}
            });
        }
    }
}
"""

CURRENCY_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Convertitore valute con tassi approssimativi salvati (offline). */
public class CurrencyActivity extends AppCompatActivity {
    private EditText input;
    private TextView out;
    // tassi indicativi rispetto all'euro (modificabili)
    private final String[] names = {"USD Dollaro","GBP Sterlina","CHF Franco","JPY Yen","USD>EUR"};
    private final double[] rate = {1.08, 0.85, 0.95, 168.0, 0.926};
    private int mode = 0;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_currency);
        input = findViewById(R.id.et_cur);
        out = findViewById(R.id.tv_cur_out);
        View back = findViewById(R.id.btn_cur_back);
        if (back != null) back.setOnClickListener(v -> finish());
        int[] ids = {R.id.bc0,R.id.bc1,R.id.bc2,R.id.bc3,R.id.bc4};
        for (int i = 0; i < ids.length; i++) {
            final int m = i;
            View b = findViewById(ids[i]);
            if (b != null) b.setOnClickListener(v -> { mode = m; conv(); });
        }
        if (input != null) input.addTextChangedListener(new TextWatcher() {
            public void onTextChanged(CharSequence c,int a,int b,int d){ conv(); }
            public void beforeTextChanged(CharSequence c,int a,int b,int d){}
            public void afterTextChanged(Editable e){}
        });
    }
    private void conv() {
        try {
            double v = Double.parseDouble(input.getText().toString());
            double r = v * rate[mode];
            if (out != null) out.setText(String.format(java.util.Locale.US, "%.2f (%s)", r, names[mode]));
        } catch (Exception e) { if (out != null) out.setText("Inserisci un numero"); }
    }
}
"""

QR_POSITION_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.graphics.Bitmap;
import android.graphics.Color;
import android.location.Location;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

/** Genera un codice visivo (matrice) con le coordinate, per condivisione visiva. */
public class QrPositionActivity extends AppCompatActivity {
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_qr);
        View back = findViewById(R.id.btn_qr_back);
        if (back != null) back.setOnClickListener(v -> finish());
        TextView tv = findViewById(R.id.tv_qr_text);
        ImageView iv = findViewById(R.id.iv_qr);
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) { if (tv != null) tv.setText("GPS non pronto"); return; }
        String data = String.format(java.util.Locale.US, "geo:%.6f,%.6f",
            loc.getLatitude(), loc.getLongitude());
        if (tv != null) tv.setText(data);
        // QR vero richiede libreria; mostriamo una matrice pseudo-casuale dai dati
        // come "codice visivo" leggibile, piu' il testo sotto.
        try {
            int size = 25;
            Bitmap bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
            long seed = data.hashCode();
            java.util.Random rnd = new java.util.Random(seed);
            for (int y = 0; y < size; y++) for (int x = 0; x < size; x++) {
                boolean border = x<2||y<2||x>=size-2||y>=size-2;
                boolean corner = (x<7&&y<7)||(x>=size-7&&y<7)||(x<7&&y>=size-7);
                boolean fill = corner ? ((x+y)%2==0||x<2||y<2) : rnd.nextBoolean();
                bmp.setPixel(x, y, (fill||border)&&!(corner&&x>1&&x<6&&y>1&&y<6)
                    ? Color.BLACK : Color.WHITE);
            }
            if (iv != null) iv.setImageBitmap(bmp);
        } catch (Exception e) { Toast.makeText(this, "Errore QR", Toast.LENGTH_SHORT).show(); }
    }
}
"""

LAYOUT_FLASHLIGHT = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:padding="20dp" android:background="#050A14"
    android:gravity="center">
    <Button android:id="@+id/btn_flash_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_gravity="start"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="TORCIA" android:textColor="#FFD600" android:textSize="24sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
    <TextView android:id="@+id/tv_flash_state"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Spenta" android:textColor="#5A7A99" android:textSize="18sp"
        android:layout_marginBottom="40dp"/>
    <Button android:id="@+id/btn_flash_toggle"
        android:layout_width="200dp" android:layout_height="200dp"
        android:text="ON / OFF" android:backgroundTint="#FFD600" android:textColor="#050A14"
        android:textStyle="bold" android:textSize="22sp"/>
</LinearLayout>"""

def _calc_key(vid, label, bg, fg):
    return ('<Button android:id="@+id/' + vid + '" android:text="' + label + '"'
        + ' android:layout_columnWeight="1" android:layout_width="0dp" android:layout_height="64dp"'
        + ' android:backgroundTint="' + bg + '" android:textColor="' + fg + '"/>\n')

LAYOUT_CALC = ("""\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:padding="16dp" android:background="#050A14">
    <Button android:id="@+id/btn_calc_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_marginBottom="12dp"/>
    <TextView android:id="@+id/calc_display"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="0" android:textColor="#00FF88" android:textSize="40sp"
        android:gravity="end" android:fontFamily="monospace" android:background="#0D1421"
        android:padding="20dp" android:layout_marginBottom="12dp"/>
    <GridLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:columnCount="4" android:rowCount="5">
"""
    + _calc_key("kclear", "C", "#FF1744", "#FFFFFF")
    + _calc_key("kdiv", "/", "#141E2E", "#00E5FF")
    + _calc_key("kmul", "*", "#141E2E", "#00E5FF")
    + _calc_key("kminus", "-", "#141E2E", "#00E5FF")
    + _calc_key("k7", "7", "#0D1421", "#E8F4FD")
    + _calc_key("k8", "8", "#0D1421", "#E8F4FD")
    + _calc_key("k9", "9", "#0D1421", "#E8F4FD")
    + _calc_key("kplus", "+", "#141E2E", "#00E5FF")
    + _calc_key("k4", "4", "#0D1421", "#E8F4FD")
    + _calc_key("k5", "5", "#0D1421", "#E8F4FD")
    + _calc_key("k6", "6", "#0D1421", "#E8F4FD")
    + '<Button android:id="@+id/keq" android:text="=" android:layout_columnWeight="1"'
      ' android:layout_rowSpan="3" android:layout_width="0dp" android:layout_height="match_parent"'
      ' android:backgroundTint="#00FF88" android:textColor="#050A14" android:textStyle="bold"/>\n'
    + _calc_key("k1", "1", "#0D1421", "#E8F4FD")
    + _calc_key("k2", "2", "#0D1421", "#E8F4FD")
    + _calc_key("k3", "3", "#0D1421", "#E8F4FD")
    + '<Button android:id="@+id/k0" android:text="0" android:layout_columnWeight="2"'
      ' android:layout_columnSpan="2" android:layout_width="0dp" android:layout_height="64dp"'
      ' android:backgroundTint="#0D1421" android:textColor="#E8F4FD"/>\n'
    + _calc_key("kdot", ".", "#0D1421", "#E8F4FD")
    + """    </GridLayout>
</LinearLayout>""")

LAYOUT_NOTEPAD = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:padding="16dp" android:background="#050A14">
    <Button android:id="@+id/btn_notepad_back"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
        android:textSize="13sp" android:layout_marginBottom="12dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="BLOCCO NOTE" android:textColor="#00FF88" android:textSize="20sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="12dp"/>
    <EditText android:id="@+id/et_notepad"
        android:layout_width="match_parent" android:layout_height="match_parent"
        android:gravity="top" android:hint="Scrivi qui i tuoi appunti..."
        android:textColor="#E8F4FD" android:textColorHint="#5A7A99" android:textSize="16sp"
        android:background="#0D1421" android:padding="16dp"/>
</LinearLayout>"""

LAYOUT_CURRENCY = _scroll(_tool_header("VALUTE", "btn_cur_back", "#FFD600")
    + '<EditText android:id="@+id/et_cur" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberDecimal" android:hint="Importo in EUR"\n'
      '    android:textColor="#E8F4FD" android:textColorHint="#5A7A99" android:textSize="22sp"\n'
      '    android:layout_marginBottom="16dp"/>\n'
    + _big("tv_cur_out", "Inserisci un numero", "#00FF88")
    + _btn("bc0", "EUR > USD Dollaro", "#141E2E", "#00E5FF")
    + _btn("bc1", "EUR > GBP Sterlina", "#141E2E", "#00E5FF")
    + _btn("bc2", "EUR > CHF Franco", "#141E2E", "#00E5FF")
    + _btn("bc3", "EUR > JPY Yen", "#141E2E", "#00E5FF")
    + _btn("bc4", "USD > EUR", "#141E2E", "#FFD600")
    + '<TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
      '    android:text="Tassi indicativi salvati offline, possono non essere aggiornati."\n'
      '    android:textColor="#5A7A99" android:textSize="12sp" android:layout_marginTop="12dp"/>')

LAYOUT_QR = _scroll(_tool_header("QR POSIZIONE", "btn_qr_back", "#00E5FF")
    + '<ImageView android:id="@+id/iv_qr" android:layout_width="240dp" android:layout_height="240dp"\n'
      '    android:layout_gravity="center" android:background="#FFFFFF" android:padding="10dp"\n'
      '    android:scaleType="fitCenter" android:contentDescription="QR"/>\n'
      '<TextView android:id="@+id/tv_qr_text" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:text="--" android:textColor="#00E5FF"\n'
      '    android:textSize="14sp" android:fontFamily="monospace" android:gravity="center"\n'
      '    android:layout_marginTop="20dp"/>\n'
      '<TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
      '    android:text="Codice visivo della tua posizione. Mostralo o fotografalo come riferimento."\n'
      '    android:textColor="#5A7A99" android:textSize="12sp" android:gravity="center"\n'
      '    android:layout_marginTop="16dp"/>')

# ============================================================
#  CHAT OFFLINE via Bluetooth — un telefono OSPITA, l'altro ENTRA.
#  Scambio messaggi di testo senza internet, con rimbalzo mesh (TTL).
# ============================================================
CHAT_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.offlinegps.map.R;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

/** Chat di testo tra due telefoni via Bluetooth, senza internet. */
public class ChatActivity extends AppCompatActivity {
    private static final UUID APP_UUID = UUID.fromString("8ce255c0-200a-11e0-ac64-0800200c9a66");
    private static final String NAME = "OfflineGPSChat";

    private BluetoothAdapter adapter;
    private BluetoothSocket socket;
    private OutputStream outStream;
    private Thread serverThread, clientThread, readThread;
    private BluetoothServerSocket serverSocket;
    private final Handler ui = new Handler(Looper.getMainLooper());

    private LinearLayout msgBox;
    private ScrollView scroll;
    private EditText etMsg;
    private TextView tvStatus;
    private boolean connected = false;
    private String myName = "Io";

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_chat);
        msgBox = findViewById(R.id.chat_messages);
        scroll = findViewById(R.id.chat_scroll);
        etMsg = findViewById(R.id.chat_input);
        tvStatus = findViewById(R.id.chat_status);

        View back = findViewById(R.id.btn_chat_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View host = findViewById(R.id.btn_chat_host);
        if (host != null) host.setOnClickListener(v -> startHost());
        View join = findViewById(R.id.btn_chat_join);
        if (join != null) join.setOnClickListener(v -> startJoin());
        View send = findViewById(R.id.btn_chat_send);
        if (send != null) send.setOnClickListener(v -> sendMsg());

        adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter == null) { setStatus("Bluetooth non supportato"); return; }
        ensurePerms();
    }

    private void ensurePerms() {
        java.util.List<String> need = new java.util.ArrayList<>();
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED)
                need.add(Manifest.permission.BLUETOOTH_CONNECT);
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED)
                need.add(Manifest.permission.BLUETOOTH_SCAN);
        }
        if (!need.isEmpty())
            ActivityCompat.requestPermissions(this, need.toArray(new String[0]), 42);
    }

    private boolean hasConnectPerm() {
        return android.os.Build.VERSION.SDK_INT < 31 ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED;
    }

    // ----- HOST: mette il telefono in ascolto -----
    private void startHost() {
        if (!hasConnectPerm()) { ensurePerms(); return; }
        if (!adapter.isEnabled()) { Toast.makeText(this, "Attiva il Bluetooth", Toast.LENGTH_LONG).show(); return; }
        setStatus("In attesa di connessione... (l'altro deve premere ENTRA)");
        myName = "Host";
        serverThread = new Thread(() -> {
            try {
                serverSocket = adapter.listenUsingRfcommWithServiceRecord(NAME, APP_UUID);
                BluetoothSocket sock = serverSocket.accept();
                try { serverSocket.close(); } catch (Exception ignored) {}
                if (sock != null) { socket = sock; onConnected(); }
            } catch (SecurityException se) {
                ui.post(() -> setStatus("Permesso Bluetooth mancante"));
            } catch (Exception e) {
                ui.post(() -> setStatus("Errore host: " + e.getMessage()));
            }
        });
        serverThread.start();
    }

    // ----- JOIN: si connette a un host gia' accoppiato -----
    private void startJoin() {
        if (!hasConnectPerm()) { ensurePerms(); return; }
        if (!adapter.isEnabled()) { Toast.makeText(this, "Attiva il Bluetooth", Toast.LENGTH_LONG).show(); return; }
        try {
            java.util.Set<BluetoothDevice> paired = adapter.getBondedDevices();
            if (paired == null || paired.isEmpty()) {
                Toast.makeText(this, "Prima accoppia i due telefoni nelle impostazioni Bluetooth", Toast.LENGTH_LONG).show();
                return;
            }
            final java.util.List<BluetoothDevice> list = new java.util.ArrayList<>(paired);
            String[] labels = new String[list.size()];
            for (int i = 0; i < list.size(); i++) labels[i] = safeName(list.get(i));
            new android.app.AlertDialog.Builder(this)
                .setTitle("Scegli il telefono host")
                .setItems(labels, (d, w) -> connectTo(list.get(w)))
                .show();
        } catch (SecurityException se) { ensurePerms(); }
    }

    private String safeName(BluetoothDevice d) {
        try { return d.getName() + " (" + d.getAddress() + ")"; }
        catch (SecurityException e) { return d.getAddress(); }
    }

    private void connectTo(BluetoothDevice dev) {
        setStatus("Connessione in corso...");
        myName = "Guest";
        clientThread = new Thread(() -> {
            try {
                BluetoothSocket sock = dev.createRfcommSocketToServiceRecord(APP_UUID);
                adapter.cancelDiscovery();
                sock.connect();
                socket = sock;
                onConnected();
            } catch (SecurityException se) {
                ui.post(() -> setStatus("Permesso Bluetooth mancante"));
            } catch (Exception e) {
                ui.post(() -> setStatus("Connessione fallita: " + e.getMessage()));
            }
        });
        clientThread.start();
    }

    private void onConnected() {
        connected = true;
        try { outStream = socket.getOutputStream(); } catch (Exception ignored) {}
        ui.post(() -> { setStatus("CONNESSO! Potete scrivervi."); addMsg("Sistema", "Connessione stabilita."); });
        readThread = new Thread(() -> {
            try {
                InputStream in = socket.getInputStream();
                java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(in, "UTF-8"));
                String line;
                // ogni messaggio termina con \n: cosi' non si spezza ne' si unisce
                while ((line = reader.readLine()) != null) {
                    final String raw = line;
                    if (!raw.isEmpty()) handleIncoming(raw);
                }
            } catch (Exception e) {
                ui.post(() -> setStatus("Disconnesso"));
            }
        });
        readThread.start();
    }

    // formato pacchetto mesh: ID|TTL|mittente|testo
    private void handleIncoming(String raw) {
        try {
            String[] parts = raw.split("\\|", 4);
            if (parts.length < 4) { ui.post(() -> addMsg("Altro", raw)); return; }
            String id = parts[0];
            int ttl;
            try { ttl = Integer.parseInt(parts[1]); } catch (Exception e) { ttl = 0; }
            String sender = parts[2];
            String text = parts[3];
            // gia' visto? ignora (evita che il messaggio giri all'infinito)
            synchronized (seenIds) {
                if (seenIds.contains(id)) return;
                seenIds.add(id);
                if (seenIds.size() > 500) seenIds.clear();
            }
            ui.post(() -> addMsg(sender, text));
            // RIMBALZO: se il messaggio ha ancora "vita" (TTL>0), lo inoltro
            if (ttl > 0) {
                String relay = id + "|" + (ttl - 1) + "|" + sender + "|" + text;
                rawSend(relay);
            }
        } catch (Exception e) {
            ui.post(() -> addMsg("Altro", raw));
        }
    }

    private void sendMsg() {
        if (!connected || outStream == null) { Toast.makeText(this, "Non sei connesso", Toast.LENGTH_SHORT).show(); return; }
        String text = etMsg.getText().toString().trim();
        if (text.isEmpty()) return;
        // crea un pacchetto mesh con ID unico e TTL (numero di rimbalzi max)
        String id = Long.toHexString(System.currentTimeMillis())
            + Integer.toHexString((int)(Math.random()*65536));
        synchronized (seenIds) { seenIds.add(id); }
        final String packet = id + "|7|" + myName + "|" + text;
        final String shown = text;
        new Thread(() -> {
            rawSend(packet);
            ui.post(() -> { addMsg("Io", shown); etMsg.setText(""); });
        }).start();
    }

    private void rawSend(String packet) {
        try {
            if (outStream != null) {
                // \n delimita la fine del messaggio (vedi readLine in ricezione)
                outStream.write((packet + "\n").getBytes("UTF-8"));
                outStream.flush();
            }
        } catch (Exception e) { ui.post(() -> setStatus("Invio fallito")); }
    }

    private final java.util.Set<String> seenIds =
        java.util.Collections.synchronizedSet(new java.util.HashSet<>());

    private void addMsg(String who, String text) {
        if (msgBox == null) return;
        TextView tv = new TextView(this);
        boolean me = who.equals("Io");
        boolean sys = who.equals("Sistema");
        tv.setText(sys ? text : (who + ": " + text));
        tv.setTextColor(sys ? 0xFF5A7A99 : (me ? 0xFF00FF88 : 0xFF00E5FF));
        tv.setTextSize(16);
        tv.setPadding(16, 10, 16, 10);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.gravity = me ? android.view.Gravity.END : android.view.Gravity.START;
        lp.bottomMargin = 8;
        tv.setLayoutParams(lp);
        tv.setBackgroundColor(0xFF0D1421);
        msgBox.addView(tv);
        if (scroll != null) scroll.post(() -> scroll.fullScroll(View.FOCUS_DOWN));
    }

    private void setStatus(String s) { if (tvStatus != null) tvStatus.setText(s); }

    @Override protected void onDestroy() {
        super.onDestroy();
        connected = false;
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
        try { if (serverSocket != null) serverSocket.close(); } catch (Exception ignored) {}
        if (serverThread != null) serverThread.interrupt();
        if (clientThread != null) clientThread.interrupt();
        if (readThread != null) readThread.interrupt();
    }
}
"""

LAYOUT_CHAT = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:padding="12dp" android:background="#050A14">

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginBottom="10dp">
        <Button android:id="@+id/btn_chat_back" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="&lt; Indietro" android:backgroundTint="#141E2E"
            android:textColor="#00E5FF" android:textSize="13sp" android:layout_marginEnd="10dp"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="CHAT OFFLINE" android:textColor="#00FF88" android:textSize="18sp"
            android:textStyle="bold" android:fontFamily="monospace"/>
    </LinearLayout>

    <TextView android:id="@+id/chat_status" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="Non connesso. Un telefono fa OSPITA, l'altro ENTRA."
        android:textColor="#FFD600" android:textSize="13sp" android:background="#0D1421"
        android:padding="12dp" android:layout_marginBottom="10dp"/>

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginBottom="10dp">
        <Button android:id="@+id/btn_chat_host" android:layout_width="0dp" android:layout_height="48dp"
            android:layout_weight="1" android:text="OSPITA" android:backgroundTint="#00FF88"
            android:textColor="#050A14" android:textStyle="bold" android:layout_marginEnd="8dp"/>
        <Button android:id="@+id/btn_chat_join" android:layout_width="0dp" android:layout_height="48dp"
            android:layout_weight="1" android:text="ENTRA" android:backgroundTint="#00E5FF"
            android:textColor="#050A14" android:textStyle="bold"/>
    </LinearLayout>

    <ScrollView android:id="@+id/chat_scroll" android:layout_width="match_parent"
        android:layout_height="0dp" android:layout_weight="1" android:background="#0A0E1A"
        android:padding="8dp">
        <LinearLayout android:id="@+id/chat_messages" android:layout_width="match_parent"
            android:layout_height="wrap_content" android:orientation="vertical"/>
    </ScrollView>

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginTop="10dp">
        <EditText android:id="@+id/chat_input" android:layout_width="0dp" android:layout_height="wrap_content"
            android:layout_weight="1" android:hint="Scrivi un messaggio..." android:textColor="#E8F4FD"
            android:textColorHint="#5A7A99" android:background="#0D1421" android:padding="12dp"
            android:layout_marginEnd="8dp"/>
        <Button android:id="@+id/btn_chat_send" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="INVIA" android:backgroundTint="#00FF88"
            android:textColor="#050A14" android:textStyle="bold"/>
    </LinearLayout>

</LinearLayout>"""

EMERGENCY_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

/** Scheda emergenza: posizione grande e sempre visibile, schermo acceso. */
public class EmergencyActivity extends AppCompatActivity {
    private TextView tvLat, tvLon, tvDms, tvAlt, tvAcc, tvTime;
    private boolean active = false;
    private String shareText = "";

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_emergency);
        // schermo sempre acceso e luminosita' al massimo (mani fredde, sole forte)
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        try {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.screenBrightness = 1.0f;
            getWindow().setAttributes(lp);
        } catch (Exception ignored) {}

        tvLat = findViewById(R.id.em_lat);
        tvLon = findViewById(R.id.em_lon);
        tvDms = findViewById(R.id.em_dms);
        tvAlt = findViewById(R.id.em_alt);
        tvAcc = findViewById(R.id.em_acc);
        tvTime = findViewById(R.id.em_time);

        View back = findViewById(R.id.btn_em_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View share = findViewById(R.id.btn_em_share);
        if (share != null) share.setOnClickListener(v -> share());
        View sos = findViewById(R.id.btn_em_sos);
        if (sos != null) sos.setOnClickListener(v -> sosMessage());
    }

    @Override protected void onResume() { super.onResume(); active = true; refresh(); }
    @Override protected void onPause() { super.onPause(); active = false; }

    private void refresh() {
        if (!active) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null) {
            if (tvLat != null) tvLat.setText("Attendo GPS...");
            new Handler(Looper.getMainLooper()).postDelayed(this::refresh, 1500);
            return;
        }
        double la = loc.getLatitude(), lo = loc.getLongitude();
        if (tvLat != null) tvLat.setText(String.format(java.util.Locale.US, "%.5f", la));
        if (tvLon != null) tvLon.setText(String.format(java.util.Locale.US, "%.5f", lo));
        if (tvDms != null) tvDms.setText(toDms(la, true) + "   " + toDms(lo, false));
        if (tvAlt != null) tvAlt.setText(loc.hasAltitude()
            ? String.format(java.util.Locale.US, "%.0f m", loc.getAltitude()) : "-- m");
        if (tvAcc != null) {
            float acc = loc.getAccuracy();
            tvAcc.setText(String.format(java.util.Locale.US, "+/- %.0f m", acc));
            tvAcc.setTextColor(acc <= 10 ? 0xFF00FF88 : (acc <= 25 ? 0xFFFFD600 : 0xFFFF1744));
        }
        if (tvTime != null) tvTime.setText(android.text.format.DateFormat
            .format("HH:mm:ss", System.currentTimeMillis()).toString());
        shareText = "EMERGENZA - La mia posizione:\n"
            + String.format(java.util.Locale.US, "%.6f, %.6f", la, lo) + "\n"
            + toDms(la, true) + " " + toDms(lo, false)
            + (loc.hasAltitude() ? String.format(java.util.Locale.US, "\nQuota: %.0f m", loc.getAltitude()) : "")
            + "\nhttps://maps.google.com/?q=" + String.format(java.util.Locale.US, "%.6f,%.6f", la, lo);
        new Handler(Looper.getMainLooper()).postDelayed(this::refresh, 2000);
    }

    private static String toDms(double v, boolean lat) {
        String hemi = lat ? (v >= 0 ? "N" : "S") : (v >= 0 ? "E" : "O");
        v = Math.abs(v);
        int d = (int) v; double mF = (v - d) * 60; int m = (int) mF; double sec = (mF - m) * 60;
        return String.format(java.util.Locale.US, "%d°%02d'%04.1f\"%s", d, m, sec, hemi);
    }

    private void share() {
        if (shareText.isEmpty()) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        Intent i = new Intent(Intent.ACTION_SEND);
        i.setType("text/plain");
        i.putExtra(Intent.EXTRA_TEXT, shareText);
        startActivity(Intent.createChooser(i, "Condividi posizione di emergenza"));
    }
    private void sosMessage() {
        if (shareText.isEmpty()) { Toast.makeText(this, "GPS non pronto", Toast.LENGTH_SHORT).show(); return; }
        // prova ad aprire l'SMS verso il 112 (numero unico emergenze europeo)
        try {
            Intent i = new Intent(Intent.ACTION_SENDTO, android.net.Uri.parse("smsto:112"));
            i.putExtra("sms_body", shareText);
            startActivity(i);
        } catch (Exception e) { share(); }
    }
}
"""

LAYOUT_EMERGENCY = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#0A0000">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="16dp">

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginBottom="8dp">
        <Button android:id="@+id/btn_em_back" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="&lt; Indietro" android:backgroundTint="#2A1010"
            android:textColor="#FF8888" android:textSize="13sp" android:layout_marginEnd="10dp"/>
        <TextView android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
            android:text="EMERGENZA" android:textColor="#FF1744" android:textSize="22sp"
            android:textStyle="bold" android:fontFamily="monospace" android:gravity="center"/>
        <TextView android:id="@+id/em_time" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="--:--" android:textColor="#FF8888"
            android:textSize="14sp" android:fontFamily="monospace"/>
    </LinearLayout>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="LATITUDINE" android:textColor="#FF6666" android:textSize="14sp"
        android:layout_marginTop="8dp"/>
    <TextView android:id="@+id/em_lat" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="--" android:textColor="#FFFFFF"
        android:textSize="44sp" android:textStyle="bold" android:fontFamily="monospace"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="LONGITUDINE" android:textColor="#FF6666" android:textSize="14sp"
        android:layout_marginTop="8dp"/>
    <TextView android:id="@+id/em_lon" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="--" android:textColor="#FFFFFF"
        android:textSize="44sp" android:textStyle="bold" android:fontFamily="monospace"/>

    <TextView android:id="@+id/em_dms" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="--" android:textColor="#FFD600"
        android:textSize="18sp" android:fontFamily="monospace" android:layout_marginTop="12dp"/>

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginTop="16dp">
        <LinearLayout android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
            android:orientation="vertical">
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="QUOTA" android:textColor="#FF6666" android:textSize="13sp"/>
            <TextView android:id="@+id/em_alt" android:layout_width="wrap_content"
                android:layout_height="wrap_content" android:text="-- m" android:textColor="#FFFFFF"
                android:textSize="26sp" android:textStyle="bold" android:fontFamily="monospace"/>
        </LinearLayout>
        <LinearLayout android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
            android:orientation="vertical">
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="PRECISIONE" android:textColor="#FF6666" android:textSize="13sp"/>
            <TextView android:id="@+id/em_acc" android:layout_width="wrap_content"
                android:layout_height="wrap_content" android:text="--" android:textColor="#00FF88"
                android:textSize="26sp" android:textStyle="bold" android:fontFamily="monospace"/>
        </LinearLayout>
    </LinearLayout>

    <Button android:id="@+id/btn_em_share" android:layout_width="match_parent"
        android:layout_height="58dp" android:text="CONDIVIDI POSIZIONE" android:backgroundTint="#00AA55"
        android:textColor="#FFFFFF" android:textStyle="bold" android:textSize="16sp"
        android:layout_marginTop="24dp"/>
    <Button android:id="@+id/btn_em_sos" android:layout_width="match_parent"
        android:layout_height="58dp" android:text="SMS AL 112 CON POSIZIONE" android:backgroundTint="#FF1744"
        android:textColor="#FFFFFF" android:textStyle="bold" android:textSize="16sp"
        android:layout_marginTop="12dp"/>
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Il 112 e' il numero unico europeo per le emergenze. L'SMS puo' partire anche con segnale debole."
        android:textColor="#AA6666" android:textSize="12sp" android:layout_marginTop="12dp"/>

</LinearLayout></ScrollView>"""

ALTIMETER_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.AppConfig;
import java.util.ArrayDeque;

/** Altimetro barometrico + avviso temporale basato sulla tendenza pressione. */
public class AltimeterActivity extends AppCompatActivity implements SensorEventListener {
    private SensorManager sm;
    private Sensor pressure;
    private TextView tvAlt, tvPressure, tvTrend, tvWarning, tvNoSensor;
    private float seaLevel = 1013.25f;

    // storia pressione: coppie (tempo_ms, hPa) per calcolare la tendenza
    private final ArrayDeque<float[]> history = new ArrayDeque<>();
    private float lastHpa = 0;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_altimeter);
        tvAlt = findViewById(R.id.alt_value);
        tvPressure = findViewById(R.id.alt_pressure);
        tvTrend = findViewById(R.id.alt_trend);
        tvWarning = findViewById(R.id.alt_warning);
        tvNoSensor = findViewById(R.id.alt_nosensor);
        View back = findViewById(R.id.btn_alt_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View cal = findViewById(R.id.btn_alt_calibrate);
        if (cal != null) cal.setOnClickListener(v -> calibrate());

        // ripristina taratura livello mare salvata
        seaLevel = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE)
            .getFloat("sea_level", 1013.25f);

        sm = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sm != null) pressure = sm.getDefaultSensor(Sensor.TYPE_PRESSURE);
        if (pressure == null) {
            // niente barometro: mostro avviso, nascondo i dati
            if (tvNoSensor != null) tvNoSensor.setVisibility(View.VISIBLE);
        }
    }

    @Override protected void onResume() {
        super.onResume();
        if (sm != null && pressure != null)
            sm.registerListener(this, pressure, SensorManager.SENSOR_DELAY_NORMAL);
    }
    @Override protected void onPause() {
        super.onPause();
        if (sm != null) sm.unregisterListener(this);
    }

    @Override public void onSensorChanged(SensorEvent e) {
        float hpa = e.values[0];
        lastHpa = hpa;
        long now = System.currentTimeMillis();
        history.addLast(new float[]{now, hpa});
        // teniamo solo le ultime 3 ore
        while (!history.isEmpty() && now - history.peekFirst()[0] > 3 * 3600_000L)
            history.removeFirst();

        // quota dalla formula barometrica internazionale
        double alt = 44330.0 * (1.0 - Math.pow(hpa / seaLevel, 0.190284));
        if (tvAlt != null) tvAlt.setText(String.format(java.util.Locale.US, "%.0f m", alt));
        if (tvPressure != null) tvPressure.setText(String.format(java.util.Locale.US, "%.1f hPa", hpa));

        evaluateTrend(now, hpa);
    }
    @Override public void onAccuracyChanged(Sensor sensor, int a) {}

    private void evaluateTrend(long now, float hpa) {
        // cerco la pressione di circa 1 ora fa per calcolare la variazione
        float oldHpa = hpa; long oldTime = now;
        for (float[] p : history) {
            if (now - p[0] >= 3600_000L) { oldHpa = p[1]; oldTime = (long) p[0]; }
        }
        float deltaPerHour;
        long span = now - oldTime;
        if (span < 600_000L) {  // meno di 10 min di dati: non affidabile
            if (tvTrend != null) tvTrend.setText("Raccolgo dati... (servono ~1h per la tendenza)");
            if (tvWarning != null) tvWarning.setVisibility(View.GONE);
            return;
        }
        deltaPerHour = (hpa - oldHpa) / (span / 3600_000f);

        String trend; int color;
        if (deltaPerHour <= -2f) { trend = "Pressione in CALO RAPIDO"; color = 0xFFFF1744; }
        else if (deltaPerHour <= -1f) { trend = "Pressione in calo"; color = 0xFFFFD600; }
        else if (deltaPerHour >= 1.5f) { trend = "Pressione in aumento (bel tempo)"; color = 0xFF00FF88; }
        else { trend = "Pressione stabile"; color = 0xFF00E5FF; }
        if (tvTrend != null) {
            tvTrend.setText(String.format(java.util.Locale.US, "%s  (%+.1f hPa/h)", trend, deltaPerHour));
            tvTrend.setTextColor(color);
        }

        // avviso temporale: calo >= 2 hPa/h e' segnale classico di maltempo
        if (tvWarning != null) {
            if (deltaPerHour <= -2f) {
                tvWarning.setVisibility(View.VISIBLE);
                tvWarning.setText("ATTENZIONE: calo rapido di pressione.\nPossibile temporale o maltempo in arrivo. Valuta di scendere o cercare riparo.");
            } else if (deltaPerHour <= -1.3f) {
                tvWarning.setVisibility(View.VISIBLE);
                tvWarning.setText("Pressione in diminuzione: il tempo potrebbe peggiorare. Tieni d'occhio il cielo.");
            } else {
                tvWarning.setVisibility(View.GONE);
            }
        }
    }

    private void calibrate() {
        // taratura: l'utente inserisce la quota reale attuale e ricaviamo il
        // livello mare di riferimento, cosi' la quota diventa precisa.
        final android.widget.EditText et = new android.widget.EditText(this);
        et.setInputType(android.text.InputType.TYPE_CLASS_NUMBER
            | android.text.InputType.TYPE_NUMBER_FLAG_SIGNED);
        et.setHint("Quota reale in metri (es. 1200)");
        new android.app.AlertDialog.Builder(this)
            .setTitle("Calibra altimetro")
            .setMessage("Inserisci la quota reale del punto in cui sei (da una mappa o un cartello).")
            .setView(et)
            .setPositiveButton("OK", (d, w) -> {
                try {
                    double realAlt = Double.parseDouble(et.getText().toString());
                    // dalla quota reale e dalla pressione attuale ricavo seaLevel
                    seaLevel = (float) (lastHpa / Math.pow(1.0 - realAlt / 44330.0, 5.255));
                    getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit()
                        .putFloat("sea_level", seaLevel).apply();
                    android.widget.Toast.makeText(this, "Altimetro calibrato",
                        android.widget.Toast.LENGTH_SHORT).show();
                } catch (Exception ex) {
                    android.widget.Toast.makeText(this, "Valore non valido",
                        android.widget.Toast.LENGTH_SHORT).show();
                }
            })
            .setNegativeButton("Annulla", null)
            .show();
    }
}
"""

LAYOUT_ALTIMETER = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginBottom="20dp">
        <Button android:id="@+id/btn_alt_back" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="&lt; Indietro" android:backgroundTint="#141E2E"
            android:textColor="#00E5FF" android:textSize="13sp" android:layout_marginEnd="12dp"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="ALTIMETRO" android:textColor="#FFD600" android:textSize="20sp"
            android:textStyle="bold" android:fontFamily="monospace"/>
    </LinearLayout>

    <TextView android:id="@+id/alt_nosensor" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:visibility="gone"
        android:text="Questo telefono non ha il sensore barometro. L'altimetro e l'avviso temporale non sono disponibili. Puoi comunque usare la quota GPS negli altri strumenti."
        android:textColor="#FF8888" android:textSize="15sp" android:background="#2A1010"
        android:padding="18dp" android:layout_marginBottom="16dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="QUOTA (barometrica)" android:textColor="#5A7A99" android:textSize="13sp"/>
    <TextView android:id="@+id/alt_value" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="-- m" android:textColor="#FFFFFF"
        android:textSize="52sp" android:textStyle="bold" android:fontFamily="monospace"
        android:layout_marginBottom="16dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="PRESSIONE" android:textColor="#5A7A99" android:textSize="13sp"/>
    <TextView android:id="@+id/alt_pressure" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="-- hPa" android:textColor="#00E5FF"
        android:textSize="30sp" android:textStyle="bold" android:fontFamily="monospace"
        android:layout_marginBottom="16dp"/>

    <TextView android:id="@+id/alt_trend" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="Raccolgo dati..." android:textColor="#00E5FF"
        android:textSize="17sp" android:fontFamily="monospace" android:background="#0D1421"
        android:padding="16dp" android:layout_marginBottom="16dp"/>

    <TextView android:id="@+id/alt_warning" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:visibility="gone"
        android:text="" android:textColor="#FFFFFF" android:textSize="16sp" android:textStyle="bold"
        android:background="#5A0E1E" android:padding="18dp" android:layout_marginBottom="16dp"/>

    <Button android:id="@+id/btn_alt_calibrate" android:layout_width="match_parent"
        android:layout_height="52dp" android:text="CALIBRA CON QUOTA REALE" android:backgroundTint="#141E2E"
        android:textColor="#FFD600" android:textStyle="bold" android:textSize="14sp"/>
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="La quota barometrica e' piu' precisa di quella GPS, ma va calibrata: inserisci una volta la quota reale (da un cartello o una mappa). L'avviso temporale impara la tendenza nell'arco di circa un'ora."
        android:textColor="#5A7A99" android:textSize="12sp" android:layout_marginTop="12dp"/>

</LinearLayout></ScrollView>"""

BATTERY_SAVER_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Strumento risparmio batteria: stato, stima durata, modalita' schermo nero. */
public class BatterySaverActivity extends AppCompatActivity {
    private TextView tvLevel, tvStatus, tvEstimate, tvTemp, tvBlackLevel, tvBlackTime;
    private View normalPanel, blackPanel;
    private boolean blackMode = false;
    private BroadcastReceiver battReceiver;
    private float originalBrightness = -1;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_battery);
        tvLevel = findViewById(R.id.bat_level);
        tvStatus = findViewById(R.id.bat_status);
        tvEstimate = findViewById(R.id.bat_estimate);
        tvTemp = findViewById(R.id.bat_temp);
        normalPanel = findViewById(R.id.bat_normal_panel);
        blackPanel = findViewById(R.id.bat_black_panel);
        tvBlackLevel = findViewById(R.id.bat_black_level);
        tvBlackTime = findViewById(R.id.bat_black_time);

        View back = findViewById(R.id.btn_bat_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View black = findViewById(R.id.btn_bat_black);
        if (black != null) black.setOnClickListener(v -> enterBlackMode());
        View exitBlack = findViewById(R.id.btn_exit_black);
        if (exitBlack != null) exitBlack.setOnClickListener(v -> exitBlackMode());
        View sysSaver = findViewById(R.id.btn_sys_saver);
        if (sysSaver != null) sysSaver.setOnClickListener(v -> openSetting(Settings.ACTION_BATTERY_SAVER_SETTINGS));
        View airplane = findViewById(R.id.btn_airplane);
        if (airplane != null) airplane.setOnClickListener(v -> openSetting(Settings.ACTION_AIRPLANE_MODE_SETTINGS));
        View display = findViewById(R.id.btn_display);
        if (display != null) display.setOnClickListener(v -> openSetting(Settings.ACTION_DISPLAY_SETTINGS));
    }

    @Override protected void onResume() {
        super.onResume();
        battReceiver = new BroadcastReceiver() {
            @Override public void onReceive(Context c, Intent i) { updateBattery(i); }
        };
        registerReceiver(battReceiver, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
    }
    @Override protected void onPause() {
        super.onPause();
        try { if (battReceiver != null) unregisterReceiver(battReceiver); } catch (Exception ignored) {}
    }

    private void updateBattery(Intent i) {
        if (i == null) return;
        int level = i.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = i.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
        int status = i.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
        int temp = i.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1);
        int pct = (scale > 0) ? level * 100 / scale : level;

        boolean charging = status == BatteryManager.BATTERY_STATUS_CHARGING
            || status == BatteryManager.BATTERY_STATUS_FULL;

        String levelStr = pct + "%";
        if (tvLevel != null) {
            tvLevel.setText(levelStr);
            tvLevel.setTextColor(pct <= 15 ? 0xFFFF1744 : (pct <= 35 ? 0xFFFFD600 : 0xFF00FF88));
        }
        if (tvBlackLevel != null) {
            tvBlackLevel.setText(levelStr);
            tvBlackLevel.setTextColor(pct <= 15 ? 0xFFFF5555 : 0xFF66FF99);
        }
        if (tvStatus != null) tvStatus.setText(charging ? "In carica" : "A batteria");
        if (tvTemp != null && temp > 0)
            tvTemp.setText(String.format(java.util.Locale.US, "Temperatura: %.1f C", temp / 10.0));

        // stima durata (grossolana): a schermo spento un telefono medio dura
        // molte ore; qui diamo una stima prudente basata sul livello.
        if (tvEstimate != null) {
            if (charging) tvEstimate.setText("In carica");
            else {
                int hMin = pct / 6;   // uso attivo con GPS
                int hMax = pct / 2;   // uso leggero / schermo spento
                tvEstimate.setText(String.format(java.util.Locale.US,
                    "Autonomia stimata: %d-%d ore\n(dipende molto dall'uso)", hMin, hMax));
            }
        }
        if (blackMode && tvBlackTime != null) {
            tvBlackTime.setText(android.text.format.DateFormat
                .format("HH:mm", System.currentTimeMillis()).toString());
        }
    }

    private void enterBlackMode() {
        blackMode = true;
        if (normalPanel != null) normalPanel.setVisibility(View.GONE);
        if (blackPanel != null) blackPanel.setVisibility(View.VISIBLE);
        // abbassa la luminosita' al minimo (risparmio reale, specie OLED)
        try {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            originalBrightness = lp.screenBrightness;
            lp.screenBrightness = 0.02f;
            getWindow().setAttributes(lp);
        } catch (Exception ignored) {}
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        Toast.makeText(this, "Modalita' risparmio: tocca esci per uscire", Toast.LENGTH_LONG).show();
    }

    private void exitBlackMode() {
        blackMode = false;
        if (blackPanel != null) blackPanel.setVisibility(View.GONE);
        if (normalPanel != null) normalPanel.setVisibility(View.VISIBLE);
        try {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.screenBrightness = originalBrightness;
            getWindow().setAttributes(lp);
        } catch (Exception ignored) {}
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    private void openSetting(String action) {
        try { startActivity(new Intent(action)); }
        catch (Exception e) {
            try { startActivity(new Intent(Settings.ACTION_SETTINGS)); }
            catch (Exception ignored) {}
        }
    }

    @Override public void onBackPressed() {
        if (blackMode) { exitBlackMode(); return; }
        super.onBackPressed();
    }
}
"""

LAYOUT_BATTERY = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<ScrollView android:id="@+id/bat_normal_panel"
    android:layout_width="match_parent" android:layout_height="match_parent">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginBottom="20dp">
        <Button android:id="@+id/btn_bat_back" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="&lt; Indietro" android:backgroundTint="#141E2E"
            android:textColor="#00E5FF" android:textSize="13sp" android:layout_marginEnd="12dp"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="RISPARMIO BATTERIA" android:textColor="#00FF88" android:textSize="18sp"
            android:textStyle="bold" android:fontFamily="monospace"/>
    </LinearLayout>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="CARICA ATTUALE" android:textColor="#5A7A99" android:textSize="13sp"/>
    <TextView android:id="@+id/bat_level" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="--%" android:textColor="#00FF88"
        android:textSize="64sp" android:textStyle="bold" android:fontFamily="monospace"/>
    <TextView android:id="@+id/bat_status" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="--" android:textColor="#E8F4FD"
        android:textSize="16sp" android:layout_marginBottom="8dp"/>
    <TextView android:id="@+id/bat_temp" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="" android:textColor="#5A7A99"
        android:textSize="13sp" android:layout_marginBottom="16dp"/>

    <TextView android:id="@+id/bat_estimate" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:text="Autonomia stimata: --" android:textColor="#FFD600"
        android:textSize="17sp" android:fontFamily="monospace" android:background="#0D1421"
        android:padding="16dp" android:layout_marginBottom="20dp"/>

    <Button android:id="@+id/btn_bat_black" android:layout_width="match_parent"
        android:layout_height="58dp" android:text="MODALITA SCHERMO NERO" android:backgroundTint="#00AA55"
        android:textColor="#FFFFFF" android:textStyle="bold" android:textSize="16sp"
        android:layout_marginBottom="20dp"/>

    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="SCORCIATOIE RISPARMIO" android:textColor="#5A7A99" android:textSize="13sp"
        android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/btn_sys_saver" android:layout_width="match_parent"
        android:layout_height="50dp" android:text="Risparmio energetico di sistema" android:backgroundTint="#141E2E"
        android:textColor="#00FF88" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/btn_airplane" android:layout_width="match_parent"
        android:layout_height="50dp" android:text="Modalita aereo (spegne radio)" android:backgroundTint="#141E2E"
        android:textColor="#00E5FF" android:textSize="14sp" android:layout_marginBottom="10dp"/>
    <Button android:id="@+id/btn_display" android:layout_width="match_parent"
        android:layout_height="50dp" android:text="Luminosita e schermo" android:backgroundTint="#141E2E"
        android:textColor="#FFD600" android:textSize="14sp"/>
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="Consiglio: in montagna senza segnale, la modalita aereo fa durare molto di piu' la batteria perche' il telefono smette di cercare rete. Il GPS funziona lo stesso anche in modalita aereo."
        android:textColor="#5A7A99" android:textSize="12sp" android:layout_marginTop="16dp"/>

</LinearLayout>
</ScrollView>
<LinearLayout android:id="@+id/bat_black_panel"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:gravity="center" android:background="#000000"
    android:visibility="gone" android:clickable="true" android:focusable="true">
    <TextView android:id="@+id/bat_black_level" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="--%" android:textColor="#66FF99"
        android:textSize="72sp" android:textStyle="bold" android:fontFamily="monospace"/>
    <TextView android:id="@+id/bat_black_time" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="--:--" android:textColor="#335544"
        android:textSize="28sp" android:fontFamily="monospace" android:layout_marginTop="20dp"/>
    <Button android:id="@+id/btn_exit_black" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="esci" android:backgroundTint="#111111"
        android:textColor="#445555" android:textSize="13sp" android:layout_marginTop="60dp"/>
</LinearLayout>
</FrameLayout>"""

# ============================================================
#  NUOVI STRUMENTI v3.0 — 7 tool aggiuntivi
# ============================================================
MOON_PHASE_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import java.util.Calendar;
import java.util.TimeZone;

/** Fase lunare offline: illuminazione, eta' della luna, prossime fasi. */
public class MoonPhaseActivity extends AppCompatActivity {
    private static final double SYNODIC = 29.530588853;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_moon);
        View back = findViewById(R.id.btn_moon_back);
        if (back != null) back.setOnClickListener(v -> finish());
        render();
    }

    private void render() {
        long now = System.currentTimeMillis();
        double age = moonAge(now);
        double illum = (1 - Math.cos(2 * Math.PI * age / SYNODIC)) / 2 * 100;
        TextView tvPhase = findViewById(R.id.tv_moon_phase);
        TextView tvIllum = findViewById(R.id.tv_moon_illum);
        TextView tvNext  = findViewById(R.id.tv_moon_next);
        TextView tvHint  = findViewById(R.id.tv_moon_hint);
        if (tvPhase != null) tvPhase.setText(phaseName(age));
        if (tvIllum != null) tvIllum.setText(String.format(java.util.Locale.US,
            "Illuminazione: %.0f%%   Eta': %.1f giorni", illum, age));
        double toFull = (SYNODIC / 2 - age + SYNODIC) % SYNODIC;
        double toNew  = (SYNODIC - age) % SYNODIC;
        if (tvNext != null) tvNext.setText(String.format(java.util.Locale.US,
            "Luna piena tra %.0f giorni\nLuna nuova tra %.0f giorni", toFull, toNew));
        if (tvHint != null) tvHint.setText(illum >= 60
            ? "Molta luce lunare stanotte: buona visibilita' per camminare al buio."
            : "Poca luce lunare stanotte: porta una torcia carica.");
    }

    // giorni trascorsi dall'ultima luna nuova (riferimento: 6 gen 2000 18:14 UTC)
    private static double moonAge(long millis) {
        Calendar ref = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        ref.clear();
        ref.set(2000, Calendar.JANUARY, 6, 18, 14, 0);
        double days = (millis - ref.getTimeInMillis()) / 86400000.0;
        double age = days % SYNODIC;
        if (age < 0) age += SYNODIC;
        return age;
    }

    private static String phaseName(double a) {
        if (a < 1.85)  return "LUNA NUOVA";
        if (a < 5.54)  return "FALCE CRESCENTE";
        if (a < 9.23)  return "PRIMO QUARTO";
        if (a < 12.92) return "GIBBOSA CRESCENTE";
        if (a < 16.61) return "LUNA PIENA";
        if (a < 20.30) return "GIBBOSA CALANTE";
        if (a < 23.99) return "ULTIMO QUARTO";
        if (a < 27.68) return "FALCE CALANTE";
        return "LUNA NUOVA";
    }
}
"""

METAL_DETECTOR_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/**
 * Metal detector: usa il magnetometro. Il metallo vicino al telefono
 * altera il campo magnetico (misurato in microtesla). Taratura con un
 * tasto, beep quando la variazione supera la soglia.
 */
public class MetalDetectorActivity extends AppCompatActivity implements SensorEventListener {
    private SensorManager sm;
    private Sensor mag;
    private TextView tvVal, tvHint, tvNoSensor;
    private ProgressBar bar;
    private float baseline = -1;
    private float smooth = 0;
    private ToneGenerator tone;
    private long lastBeep = 0;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_metal);
        tvVal = findViewById(R.id.tv_metal_val);
        tvHint = findViewById(R.id.tv_metal_hint);
        tvNoSensor = findViewById(R.id.tv_metal_nosensor);
        bar = findViewById(R.id.pb_metal);
        View back = findViewById(R.id.btn_metal_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View cal = findViewById(R.id.btn_metal_cal);
        if (cal != null) cal.setOnClickListener(v -> { baseline = smooth; });
        sm = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sm != null) mag = sm.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        if (mag == null && tvNoSensor != null) tvNoSensor.setVisibility(View.VISIBLE);
        try { tone = new ToneGenerator(AudioManager.STREAM_MUSIC, 90); } catch (Exception ignored) {}
    }

    @Override protected void onResume() {
        super.onResume();
        if (sm != null && mag != null)
            sm.registerListener(this, mag, SensorManager.SENSOR_DELAY_UI);
    }
    @Override protected void onPause() {
        super.onPause();
        if (sm != null) sm.unregisterListener(this);
    }
    @Override protected void onDestroy() {
        super.onDestroy();
        if (tone != null) tone.release();
    }

    @Override public void onSensorChanged(SensorEvent e) {
        float m = (float) Math.sqrt(e.values[0]*e.values[0]
            + e.values[1]*e.values[1] + e.values[2]*e.values[2]);
        smooth = smooth == 0 ? m : smooth * 0.7f + m * 0.3f;
        if (baseline < 0) baseline = smooth;
        float delta = Math.abs(smooth - baseline);
        if (bar != null) bar.setProgress((int) Math.min(100, delta * 2));
        if (tvVal != null) tvVal.setText(String.format(java.util.Locale.US,
            "%.0f uT   (variazione %.0f)", smooth, delta));
        if (tvHint != null) {
            if (delta < 8) tvHint.setText("Nessun metallo rilevato");
            else if (delta < 25) tvHint.setText("Segnale debole: qualcosa nelle vicinanze");
            else {
                tvHint.setText("SEGNALE FORTE: metallo vicino!");
                long now = System.currentTimeMillis();
                if (now - lastBeep > 400) {
                    lastBeep = now;
                    try { if (tone != null) tone.startTone(ToneGenerator.TONE_PROP_BEEP, 150); }
                    catch (Exception ignored) {}
                }
            }
        }
    }
    @Override public void onAccuracyChanged(Sensor sensor, int a) {}
}
"""

NIGHT_VISION_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.SeekBar;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/**
 * Visione notturna: schermo rosso a bassa luminosita'. La luce rossa non
 * distrugge l'adattamento dell'occhio al buio (usata da astronomi e militari).
 * Tocca lo schermo per nascondere/mostrare i controlli.
 */
public class NightVisionActivity extends AppCompatActivity {
    private View controls;

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_nightvision);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        controls = findViewById(R.id.nv_controls);
        View root = findViewById(R.id.nv_root);
        if (root != null) root.setOnClickListener(v -> {
            if (controls != null) controls.setVisibility(
                controls.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
        });
        View back = findViewById(R.id.btn_nv_back);
        if (back != null) back.setOnClickListener(v -> finish());
        SeekBar sb = findViewById(R.id.sb_nv_brightness);
        if (sb != null) {
            sb.setProgress(15);
            setBrightness(0.15f);
            sb.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onProgressChanged(SeekBar seek, int p, boolean u) {
                    setBrightness(Math.max(0.02f, p / 100f));
                }
                public void onStartTrackingTouch(SeekBar seek) {}
                public void onStopTrackingTouch(SeekBar seek) {}
            });
        }
    }

    private void setBrightness(float b) {
        try {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.screenBrightness = b;
            getWindow().setAttributes(lp);
        } catch (Exception ignored) {}
    }
}
"""

HEAT_INDEX_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/**
 * Temperatura percepita: wind chill (freddo+vento) e heat index (caldo+umidita').
 * Formule standard: Environment Canada e Rothfusz (versione in gradi Celsius).
 */
public class HeatIndexActivity extends AppCompatActivity {

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_heatindex);
        View back = findViewById(R.id.btn_heat_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View calc = findViewById(R.id.btn_heat_calc);
        if (calc != null) calc.setOnClickListener(v -> calc());
    }

    private void calc() {
        try {
            EditText etT = findViewById(R.id.et_heat_temp);
            EditText etH = findViewById(R.id.et_heat_hum);
            EditText etW = findViewById(R.id.et_heat_wind);
            double t = Double.parseDouble(etT.getText().toString().trim().replace(",", "."));
            double rh = parseOrDefault(etH, 50);
            double w = parseOrDefault(etW, 0);

            double felt = t;
            String note;
            if (t <= 10 && w > 4.8) {
                // wind chill (Environment Canada)
                double v = Math.pow(w, 0.16);
                felt = 13.12 + 0.6215 * t - 11.37 * v + 0.3965 * t * v;
                note = "Wind chill: il vento fa percepire piu' freddo.";
            } else if (t >= 27 && rh >= 40) {
                // heat index (Rothfusz, versione Celsius)
                felt = -8.784695 + 1.61139411*t + 2.338549*rh - 0.14611605*t*rh
                    - 0.012308094*t*t - 0.016424828*rh*rh
                    + 0.002211732*t*t*rh + 0.00072546*t*rh*rh
                    - 0.000003582*t*t*rh*rh;
                note = "Heat index: l'umidita' fa percepire piu' caldo.";
            } else {
                note = "Condizioni neutre: percepita simile alla reale.";
            }

            String advice;
            if (felt <= -25) advice = "PERICOLO CONGELAMENTO: pelle esposta a rischio in pochi minuti.";
            else if (felt <= -10) advice = "Molto freddo: copri mani, testa e collo.";
            else if (felt >= 40) advice = "PERICOLO COLPO DI CALORE: fermati all'ombra e bevi.";
            else if (felt >= 32) advice = "Molto caldo: bevi spesso, evita sforzi nelle ore centrali.";
            else advice = "Condizioni gestibili con equipaggiamento normale.";

            TextView out = findViewById(R.id.tv_heat_out);
            TextView tvNote = findViewById(R.id.tv_heat_note);
            if (out != null) out.setText(String.format(java.util.Locale.US,
                "Percepita: %.1f °C", felt));
            if (tvNote != null) tvNote.setText(note + "\n" + advice);
        } catch (Exception e) {
            Toast.makeText(this, "Inserisci almeno la temperatura", Toast.LENGTH_SHORT).show();
        }
    }

    private double parseOrDefault(EditText et, double def) {
        try { return Double.parseDouble(et.getText().toString().trim().replace(",", ".")); }
        catch (Exception e) { return def; }
    }
}
"""

FIRST_AID_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/** Guida rapida di primo soccorso (riferimento offline, non sostituisce il 112). */
public class FirstAidActivity extends AppCompatActivity {
    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_firstaid);
        View back = findViewById(R.id.btn_aid_back);
        if (back != null) back.setOnClickListener(v -> finish());
    }
}
"""

PACE_CALC_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;

/**
 * Tempi di marcia con la regola di Naismith: 1 ora ogni ~4-5 km in piano
 * + 1 ora ogni 600 m di dislivello in salita. Aggiunge pause consigliate.
 */
public class PaceCalcActivity extends AppCompatActivity {

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_pace);
        View back = findViewById(R.id.btn_pace_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View calc = findViewById(R.id.btn_pace_calc);
        if (calc != null) calc.setOnClickListener(v -> calc());
    }

    private void calc() {
        try {
            EditText etD = findViewById(R.id.et_pace_dist);
            EditText etA = findViewById(R.id.et_pace_ascent);
            EditText etV = findViewById(R.id.et_pace_speed);
            double dist = Double.parseDouble(etD.getText().toString().trim().replace(",", "."));
            double asc = parseOrDefault(etA, 0);
            double vel = parseOrDefault(etV, 4);
            if (vel <= 0) vel = 4;

            double hours = dist / vel + asc / 600.0;
            double pauses = Math.floor(hours) * 10.0 / 60.0;  // ~10 min di pausa ogni ora
            double total = hours + pauses;

            TextView out = findViewById(R.id.tv_pace_out);
            TextView tvNote = findViewById(R.id.tv_pace_note);
            if (out != null) out.setText(fmtDur(hours) + " di cammino");
            if (tvNote != null) tvNote.setText(
                "Con le pause consigliate (~10 min/ora): " + fmtDur(total)
                + "\nRegola di Naismith: " + String.format(java.util.Locale.US,
                    "%.1f km a %.1f km/h + %.0f m di salita.", dist, vel, asc)
                + "\nParti presto: controlla le ore di luce nel Kit Sopravvivenza.");
        } catch (Exception e) {
            Toast.makeText(this, "Inserisci almeno la distanza in km", Toast.LENGTH_SHORT).show();
        }
    }

    private double parseOrDefault(EditText et, double def) {
        try { return Double.parseDouble(et.getText().toString().trim().replace(",", ".")); }
        catch (Exception e) { return def; }
    }

    private static String fmtDur(double h) {
        int hh = (int) h;
        int mm = (int) Math.round((h - hh) * 60);
        if (mm == 60) { mm = 0; hh++; }
        return hh + "h " + String.format(java.util.Locale.US, "%02d", mm) + "min";
    }
}
"""

SPEED_HUD_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.gps.GpsTrackingService;

/**
 * Tachimetro HUD: cifre giganti su sfondo nero. Con la modalita' SPECCHIO
 * appoggi il telefono sul cruscotto di notte e la velocita' si riflette
 * sul parabrezza (testo capovolto orizzontalmente).
 */
public class SpeedHudActivity extends AppCompatActivity {
    private TextView tvSpeed, tvMax;
    private View hudBox;
    private boolean mirrored = false;
    private double maxKmh = 0;
    private boolean active = false;
    private final Handler h = new Handler(Looper.getMainLooper());

    @Override protected void onCreate(@Nullable Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_speedhud);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        tvSpeed = findViewById(R.id.tv_hud_speed);
        tvMax = findViewById(R.id.tv_hud_max);
        hudBox = findViewById(R.id.hud_box);
        View back = findViewById(R.id.btn_hud_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View mirror = findViewById(R.id.btn_hud_mirror);
        if (mirror != null) mirror.setOnClickListener(v -> {
            mirrored = !mirrored;
            if (hudBox != null) hudBox.setScaleX(mirrored ? -1f : 1f);
        });
    }

    @Override protected void onResume() { super.onResume(); active = true; tick(); }
    @Override protected void onPause() { super.onPause(); active = false; }

    private void tick() {
        if (!active) return;
        Location loc = GpsTrackingService.getLastLocation();
        if (loc != null && loc.hasSpeed()) {
            double kmh = loc.getSpeed() * 3.6;
            if (kmh > maxKmh) maxKmh = kmh;
            if (tvSpeed != null) tvSpeed.setText(String.valueOf(Math.round(kmh)));
            if (tvMax != null) tvMax.setText(String.format(java.util.Locale.US,
                "max %.0f km/h", maxKmh));
        } else if (tvSpeed != null) {
            tvSpeed.setText("--");
        }
        h.postDelayed(this::tick, 800);
    }
}
"""

LAYOUT_MOON = _scroll(_tool_header("FASE LUNARE", "btn_moon_back", "#E8F4FD")
    + _big("tv_moon_phase", "Calcolo...", "#E8F4FD")
    + _big("tv_moon_illum", "Illuminazione: --", "#00E5FF")
    + _big("tv_moon_next", "--", "#FFD600")
    + '<TextView android:id="@+id/tv_moon_hint" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:text="" android:textColor="#5A7A99"\n'
      '    android:textSize="13sp" android:gravity="center" android:layout_marginTop="8dp"/>')

LAYOUT_METAL = _scroll(_tool_header("METAL DETECTOR", "btn_metal_back", "#00E5FF")
    + '<TextView android:id="@+id/tv_metal_nosensor" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:visibility="gone"\n'
      '    android:text="Questo telefono non ha il magnetometro: il metal detector non e\' disponibile."\n'
      '    android:textColor="#FF8888" android:textSize="15sp" android:background="#2A1010"\n'
      '    android:padding="18dp" android:layout_marginBottom="16dp"/>\n'
    + _big("tv_metal_val", "-- uT", "#00FF88")
    + '<ProgressBar android:id="@+id/pb_metal" style="?android:attr/progressBarStyleHorizontal"\n'
      '    android:layout_width="match_parent" android:layout_height="24dp" android:max="100"\n'
      '    android:progressTint="#00E5FF" android:layout_marginBottom="12dp"/>\n'
    + _big("tv_metal_hint", "Muovi il telefono vicino al metallo", "#E8F4FD")
    + _btn("btn_metal_cal", "TARA QUI (azzera il fondo)", "#00E5FF")
    + '<TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
      '    android:text="Tara il sensore lontano da metalli, poi avvicina il telefono al terreno o alla parete. Il campo magnetico terrestre e\' ~50 uT: metallo vicino lo altera."\n'
      '    android:textColor="#5A7A99" android:textSize="12sp" android:layout_marginTop="12dp"/>')

LAYOUT_NIGHTVISION = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/nv_root"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#7A0000" android:clickable="true" android:focusable="true">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="center" android:text="VISIONE NOTTURNA"
        android:textColor="#33000000" android:textSize="26sp" android:textStyle="bold"
        android:fontFamily="monospace"/>
    <LinearLayout android:id="@+id/nv_controls"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="bottom" android:orientation="vertical"
        android:background="#66000000" android:padding="16dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="Luminosita (bassa = occhio adattato al buio)" android:textColor="#FF8888"
            android:textSize="13sp" android:layout_marginBottom="8dp"/>
        <SeekBar android:id="@+id/sb_nv_brightness"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:max="100" android:progressTint="#FF4444" android:thumbTint="#FF4444"
            android:layout_marginBottom="12dp"/>
        <Button android:id="@+id/btn_nv_back"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="&lt; Esci" android:backgroundTint="#2A0000" android:textColor="#FF8888"
            android:textSize="13sp"/>
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Tocca lo schermo per nascondere i controlli. La luce rossa preserva la visione notturna."
            android:textColor="#AA5555" android:textSize="11sp" android:layout_marginTop="8dp"/>
    </LinearLayout>
</FrameLayout>"""

LAYOUT_HEATINDEX = _scroll(_tool_header("TEMPERATURA PERCEPITA", "btn_heat_back", "#FF6B35")
    + '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Temperatura reale (C)" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_heat_temp" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberSigned|numberDecimal"\n'
      '    android:hint="es. 30" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="12dp"/>\n'
      '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Umidita (%) - opzionale" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_heat_hum" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="number"\n'
      '    android:hint="es. 70" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="12dp"/>\n'
      '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Vento (km/h) - opzionale" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_heat_wind" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberDecimal"\n'
      '    android:hint="es. 20" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="16dp"/>\n'
    + _btn("btn_heat_calc", "CALCOLA PERCEPITA", "#FF6B35")
    + _big("tv_heat_out", "--", "#FF6B35")
    + '<TextView android:id="@+id/tv_heat_note" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:text="" android:textColor="#E8F4FD"\n'
      '    android:textSize="14sp" android:lineSpacingMultiplier="1.3" android:layout_marginTop="8dp"/>')

LAYOUT_FIRSTAID = _scroll(_tool_header("PRIMO SOCCORSO", "btn_aid_back", "#FF6B35")
    + '<TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
      '    android:text="Guida rapida. In emergenza chiama SEMPRE il 112.\\n\\nEMORRAGIA:\\nPremi forte sulla ferita con un panno pulito\\nNon togliere il panno: aggiungine sopra\\nSolleva l\'arto se possibile\\n\\nIPOTERMIA:\\nPorta al riparo, togli i vestiti bagnati\\nCopri con coperte (anche la testa)\\nBevande calde e zuccherate SE cosciente\\nNON strofinare la pelle\\n\\nCOLPO DI CALORE:\\nSposta all\'ombra, sdraia\\nRaffredda con acqua su collo, ascelle, inguine\\nFai bere a piccoli sorsi SE cosciente\\n\\nDISTORSIONE:\\nRiposo, ghiaccio (o acqua fredda) 20 min\\nFascia stretta ma non troppo\\nArto sollevato, non camminarci sopra\\n\\nUSTIONE:\\nAcqua corrente fresca per 10-20 minuti\\nNON ghiaccio, NON creme, NON bucare le bolle\\nCopri con garza pulita non aderente\\n\\nMORSO DI VIPERA:\\nMantieni la calma, immobilizza l\'arto\\nNON incidere, NON succhiare, NO laccio\\nVai in ospedale il prima possibile\\n\\nPOSIZIONE LATERALE DI SICUREZZA:\\nPer chi e\' incosciente MA respira:\\nsu un fianco, testa indietro, bocca verso il basso\\n\\nRCP (se NON respira):\\n30 compressioni al centro del torace\\n(100-120 al minuto, profonde 5-6 cm)\\n2 ventilazioni, poi ripeti senza fermarti"\n'
      '    android:textColor="#E8F4FD" android:textSize="15sp" android:lineSpacingMultiplier="1.3"\n'
      '    android:background="@drawable/bg_card_glass" android:padding="18dp"/>')

LAYOUT_PACE = _scroll(_tool_header("TEMPI DI MARCIA", "btn_pace_back", "#00FF88")
    + '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Distanza (km)" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_pace_dist" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberDecimal"\n'
      '    android:hint="es. 12" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="12dp"/>\n'
      '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Dislivello in salita (m) - opzionale" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_pace_ascent" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="number"\n'
      '    android:hint="es. 800" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="12dp"/>\n'
      '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
      '    android:text="Velocita in piano (km/h, default 4)" android:textColor="#5A7A99" android:textSize="13sp"/>\n'
      '<EditText android:id="@+id/et_pace_speed" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:inputType="numberDecimal"\n'
      '    android:hint="es. 4" android:textColor="#E8F4FD" android:textColorHint="#5A7A99"\n'
      '    android:textSize="20sp" android:layout_marginBottom="16dp"/>\n'
    + _btn("btn_pace_calc", "CALCOLA TEMPO", "#00FF88")
    + _big("tv_pace_out", "--", "#00FF88")
    + '<TextView android:id="@+id/tv_pace_note" android:layout_width="match_parent"\n'
      '    android:layout_height="wrap_content" android:text="" android:textColor="#E8F4FD"\n'
      '    android:textSize="14sp" android:lineSpacingMultiplier="1.3" android:layout_marginTop="8dp"/>')

LAYOUT_SPEEDHUD = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#000000">
    <LinearLayout android:id="@+id/hud_box"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="center" android:orientation="vertical" android:gravity="center">
        <TextView android:id="@+id/tv_hud_speed"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="--" android:textColor="#00FF88" android:textSize="140sp"
            android:textStyle="bold" android:fontFamily="monospace"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="km/h" android:textColor="#1E5C3A" android:textSize="24sp"
            android:fontFamily="monospace"/>
        <TextView android:id="@+id/tv_hud_max"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="max 0 km/h" android:textColor="#1E5C3A" android:textSize="16sp"
            android:fontFamily="monospace" android:layout_marginTop="10dp"/>
    </LinearLayout>
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="bottom" android:orientation="horizontal" android:padding="14dp">
        <Button android:id="@+id/btn_hud_back"
            android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
            android:text="&lt; Esci" android:backgroundTint="#101810" android:textColor="#4D8A66"
            android:textSize="13sp" android:layout_marginEnd="8dp"/>
        <Button android:id="@+id/btn_hud_mirror"
            android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
            android:text="SPECCHIA (parabrezza)" android:backgroundTint="#101810" android:textColor="#4D8A66"
            android:textSize="13sp"/>
    </LinearLayout>
</FrameLayout>"""

STRINGS_XML = '<resources><string name="app_name">OfflineGPS 3D</string></resources>'

THEMES_XML = """<resources>
    <!-- v4.0: sempre scuro (prima DayNight: col tema chiaro del telefono i
         dialoghi diventavano bianchi attorno a contenuti scuri) -->
    <style name="Theme.OfflineGPS" parent="Theme.AppCompat.NoActionBar">
        <item name="colorPrimary">#00E5FF</item>
        <item name="colorPrimaryDark">#050A14</item>
        <item name="colorAccent">#00FF88</item>
        <item name="android:windowBackground">#050A14</item>
        <item name="android:statusBarColor">#050A14</item>
        <item name="android:navigationBarColor">#050A14</item>
        <item name="android:windowAnimationStyle">@style/OfflineGPS.WindowAnim</item>
        <item name="android:alertDialogTheme">@style/OfflineGPS.Dialog</item>
    </style>
    <style name="OfflineGPS.WindowAnim" parent="@android:style/Animation.Activity">
        <item name="android:activityOpenEnterAnimation">@anim/fx_open_enter</item>
        <item name="android:activityOpenExitAnimation">@anim/fx_open_exit</item>
        <item name="android:activityCloseEnterAnimation">@anim/fx_close_enter</item>
        <item name="android:activityCloseExitAnimation">@anim/fx_close_exit</item>
    </style>
    <style name="OfflineGPS.Dialog" parent="@android:style/Theme.Material.Dialog.Alert">
        <item name="android:colorBackground">#101A2B</item>
        <item name="android:colorAccent">#00E5FF</item>
        <item name="android:textColorPrimary">#E8F4FD</item>
        <item name="android:textColorSecondary">#8FB3D0</item>
    </style>
    <style name="Theme.OfflineGPS.Fullscreen" parent="Theme.OfflineGPS">
        <item name="android:windowFullscreen">true</item>
    </style>
</resources>"""

IC_GPS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#050A14" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#00E5FF"
        android:pathData="M54,10 C34,10 18,26 18,46 C18,66 54,98 54,98 C54,98 90,66 90,46 C90,26 74,10 54,10z"/>
    <path android:fillColor="#050A14" android:pathData="M38,46 A16,16 0 1,0 70,46 A16,16 0 1,0 38,46 Z"/>
    <path android:fillColor="#00E5FF" android:pathData="M46,46 A8,8 0 1,0 62,46 A8,8 0 1,0 46,46 Z"/>
    <path android:fillColor="#00FF88" android:pathData="M51,46 A3,3 0 1,0 57,46 A3,3 0 1,0 51,46 Z"/>
</vector>"""

# Frecce di manovra vettoriali grandi e chiare (viewport 24x24, freccia ciano).
def _arrow(path):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="48dp" android:height="48dp"\n'
        '    android:viewportWidth="24" android:viewportHeight="24">\n'
        '    <path android:fillColor="#00E5FF" android:pathData="' + path + '"/>\n'
        '</vector>')

# pathData per ogni manovra (stile material directions)
MANEUVER_ICONS = {
    "ic_turn_straight":     _arrow("M12,2 L17,9 L13,9 L13,22 L11,22 L11,9 L7,9 Z"),
    "ic_turn_left":         _arrow("M2,12 L9,7 L9,11 L20,11 L20,20 L18,20 L18,13 L9,13 L9,17 Z"),
    "ic_turn_right":        _arrow("M22,12 L15,7 L15,11 L4,11 L4,20 L6,20 L6,13 L15,13 L15,17 Z"),
    "ic_turn_slight_left":  _arrow("M5,5 L13,5 L10,8 L17,15 L17,21 L15,21 L15,16 L9,10 L6,13 Z"),
    "ic_turn_slight_right": _arrow("M19,5 L11,5 L14,8 L7,15 L7,21 L9,21 L9,16 L15,10 L18,13 Z"),
    "ic_turn_sharp_left":   _arrow("M3,11 L10,6 L10,10 L16,10 L16,20 L14,20 L14,12 L10,12 L10,16 Z"),
    "ic_turn_sharp_right":  _arrow("M21,11 L14,6 L14,10 L8,10 L8,20 L10,20 L10,12 L14,12 L14,16 Z"),
    "ic_turn_roundabout":   _arrow("M12,2 C8,2 5,5 5,9 C5,12 7,15 10,15 L10,22 L12,22 L12,13 C9,13 7,11 7,9 C7,6 9,4 12,4 L12,7 L17,3 L12,-1 Z"),
}

def _neon_btn(shadow, grad_start, grad_center, grad_end, stroke):
    # v4.0: avvolto in un <ripple> -> onda luminosa al tocco su tutti i pulsanti neon
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<ripple xmlns:android="http://schemas.android.com/apk/res/android" android:color="#40FFFFFF">\n'
        '<item>\n'
        '<layer-list>\n'
        '    <item android:bottom="3dp">\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="' + shadow + '"/>\n'
        '            <corners android:radius="16dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:bottom="3dp">\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="90"\n'
        '                android:startColor="' + grad_start + '" android:centerColor="' + grad_center + '" android:endColor="' + grad_end + '"/>\n'
        '            <corners android:radius="16dp"/>\n'
        '            <stroke android:width="2dp" android:color="' + stroke + '"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:bottom="3dp" android:left="2dp" android:right="2dp" android:top="1dp">\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="90"\n'
        '                android:startColor="#44FFFFFF" android:endColor="#00FFFFFF"/>\n'
        '            <corners android:radius="14dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</layer-list>\n'
        '</item>\n'
        '</ripple>')

# ============================================================
#  DRAWABLE del tema futuristico (glass, neon, FAB, splash 3D)
# ============================================================
UI_DRAWABLES = {
    # FAB tondo scuro semi-trasparente
    "bg_fab":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">\n'
        '    <solid android:color="#E6141E2E"/>\n'
        '    <stroke android:width="1dp" android:color="#22FFFFFF"/>\n'
        '</shape>',
    # FAB primario (accento)
    "bg_fab_primary":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">\n'
        '    <solid android:color="#1565C0"/>\n'
        '    <stroke android:width="2dp" android:color="#4FC3F7"/>\n'
        '</shape>',
    # card tonda (bussola, info)
    "bg_round_card":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">\n'
        '    <solid android:color="#E6141E2E"/>\n'
        '</shape>',
    # card tachimetro (angoli molto arrotondati)
    "bg_speed_card":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <solid android:color="#E6141E2E"/>\n'
        '    <corners android:radius="20dp"/>\n'
        '    <stroke android:width="1dp" android:color="#2200FF88"/>\n'
        '</shape>',
    # barra di ricerca pill
    "bg_searchbar":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <solid android:color="#F0182338"/>\n'
        '    <corners android:radius="28dp"/>\n'
        '    <stroke android:width="1dp" android:color="#22FFFFFF"/>\n'
        '</shape>',
    # bottom sheet (angoli alti arrotondati)
    "bg_bottomsheet":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <solid android:color="#F2101826"/>\n'
        '    <corners android:topLeftRadius="24dp" android:topRightRadius="24dp"/>\n'
        '</shape>',
    # handle del bottom sheet
    "bg_handle":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <solid android:color="#44FFFFFF"/>\n'
        '    <corners android:radius="2dp"/>\n'
        '</shape>',
    # chip piccolo (zoom, stato)
    "bg_chip":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <solid android:color="#CC141E2E"/>\n'
        '    <corners android:radius="12dp"/>\n'
        '</shape>',
    # ripple per icone (fallback: trasparente)
    "bg_icon_ripple":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">\n'
        '    <solid android:color="#00000000"/>\n'
        '</shape>',
    # crosshair centrale per misura
    "bg_crosshair":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="oval">\n'
        '    <solid android:color="#FFD600"/>\n'
        '    <stroke android:width="2dp" android:color="#050A14"/>\n'
        '</shape>',
    # ago bussola (vettoriale: rosso nord / grigio sud)
    "ic_compass_needle":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="40dp" android:height="40dp"\n'
        '    android:viewportWidth="40" android:viewportHeight="40">\n'
        '    <path android:fillColor="#FF1744" android:pathData="M20,4 L26,20 L20,17 L14,20 Z"/>\n'
        '    <path android:fillColor="#5A7A99" android:pathData="M20,36 L14,20 L20,23 L26,20 Z"/>\n'
        '    <path android:fillColor="#E8F4FD" android:pathData="M20,18 m-2,0 a2,2 0 1,0 4,0 a2,2 0 1,0 -4,0"/>\n'
        '</vector>',
    # bagliore radiale per lo splash
    "bg_splash_glow":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <gradient android:type="radial" android:gradientRadius="500"\n'
        '        android:centerColor="#141E2E" android:endColor="#050A14"\n'
        '        android:centerX="0.5" android:centerY="0.42"/>\n'
        '</shape>',
    # logo splash: bussola stilizzata in vettoriale
    "ic_splash_logo":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="120dp" android:height="120dp"\n'
        '    android:viewportWidth="120" android:viewportHeight="120">\n'
        '    <path android:fillColor="#0D2840" android:pathData="M60,8 a52,52 0 1,0 0.1,0 Z"/>\n'
        '    <path android:strokeColor="#00E5FF" android:strokeWidth="3" android:fillColor="#00000000"\n'
        '        android:pathData="M60,12 a48,48 0 1,0 0.1,0 Z"/>\n'
        '    <path android:fillColor="#FF1744" android:pathData="M60,24 L72,60 L60,52 L48,60 Z"/>\n'
        '    <path android:fillColor="#5A7A99" android:pathData="M60,96 L48,60 L60,68 L72,60 Z"/>\n'
        '    <path android:fillColor="#00FF88" android:pathData="M60,56 m-6,0 a6,6 0 1,0 12,0 a6,6 0 1,0 -12,0"/>\n'
        '    <path android:fillColor="#E8F4FD" android:pathData="M60,2 l3,7 l-6,0 Z"/>\n'
        '</vector>',
    # NUOVO v3.0: anello neon rotante attorno al logo (effetto ologramma)
    "ic_splash_ring":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="150dp" android:height="150dp"\n'
        '    android:viewportWidth="150" android:viewportHeight="150">\n'
        '    <path android:strokeColor="#2200E5FF" android:strokeWidth="2" android:fillColor="#00000000"\n'
        '        android:pathData="M75,6 a69,69 0 1,0 0.1,0 Z"/>\n'
        '    <path android:strokeColor="#00E5FF" android:strokeWidth="4" android:fillColor="#00000000"\n'
        '        android:strokeLineCap="round" android:pathData="M75,3 A72,72 0 0,1 147,75"/>\n'
        '    <path android:strokeColor="#00FF88" android:strokeWidth="3" android:fillColor="#00000000"\n'
        '        android:strokeLineCap="round" android:pathData="M75,147 A72,72 0 0,1 3,75"/>\n'
        '</vector>',
    # sfondo schermata con gradiente profondo (effetto profondita')
    "bg_screen_grad":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="135"\n'
        '                android:startColor="#0A1428" android:centerColor="#050A14" android:endColor="#0A1020"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="radial" android:gradientRadius="900"\n'
        '                android:centerX="0.1" android:centerY="0.0"\n'
        '                android:startColor="#2200E5FF" android:endColor="#0000E5FF"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="radial" android:gradientRadius="1000"\n'
        '                android:centerX="1.0" android:centerY="1.0"\n'
        '                android:startColor="#1A7C4DFF" android:endColor="#007C4DFF"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</layer-list>',
    # pulsanti neon 3D (bombati con ombra, luce in alto e bordo luminoso)
    "bg_btn_neon":         _neon_btn("#05080F", "#0B1424", "#16243A", "#1C2E48", "#3300E5FF"),
    "bg_btn_neon_primary": _neon_btn("#021926", "#06324D", "#0E4A6E", "#12608F", "#6600E5FF"),
    "bg_btn_neon_green":   _neon_btn("#021A10", "#063220", "#0E4A32", "#125F40", "#6600FF88"),
    "bg_btn_neon_red":     _neon_btn("#1F0309", "#3A0614", "#5A0E1E", "#78142A", "#66FF1744"),
    # NUOVO v3.0: variante gialla (strumenti outdoor)
    "bg_btn_neon_yellow":  _neon_btn("#1A1403", "#33290A", "#4A3B10", "#5E4C16", "#66FFD600"),
    # scheda "vetro" con effetto profondita' e bordo sottile luminoso
    "bg_card_glass":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <gradient android:type="linear" android:angle="135"\n'
        '        android:startColor="#16223A" android:endColor="#0D1626"/>\n'
        '    <corners android:radius="18dp"/>\n'
        '    <stroke android:width="1dp" android:color="#22FFFFFF"/>\n'
        '</shape>',
    # scheda con accento laterale luminoso (effetto "barra al neon")
    "bg_card_accent":
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="135"\n'
        '                android:startColor="#16223A" android:endColor="#0D1626"/>\n'
        '            <corners android:radius="18dp"/>\n'
        '            <stroke android:width="1dp" android:color="#1AFFFFFF"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:width="5dp" android:gravity="start">\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#00E5FF"/>\n'
        '            <corners android:radius="18dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</layer-list>',
}

LAYOUT_SPLASH = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#050A14">

    <!-- bagliore radiale centrale -->
    <View android:layout_width="match_parent" android:layout_height="match_parent"
        android:background="@drawable/bg_splash_glow"/>

    <LinearLayout android:layout_width="match_parent" android:layout_height="match_parent"
        android:orientation="vertical" android:gravity="center">

        <!-- logo con anello neon rotante (effetto ologramma 3D) -->
        <FrameLayout android:layout_width="150dp" android:layout_height="150dp"
            android:layout_marginBottom="28dp">
            <ImageView android:id="@+id/splash_ring"
                android:layout_width="150dp" android:layout_height="150dp"
                android:src="@drawable/ic_splash_ring"
                android:contentDescription="Anello"/>
            <ImageView android:id="@+id/splash_logo"
                android:layout_width="116dp" android:layout_height="116dp"
                android:layout_gravity="center" android:src="@drawable/ic_splash_logo"
                android:contentDescription="Logo"/>
        </FrameLayout>

        <TextView android:id="@+id/splash_title"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="OfflineGPS 3D" android:textColor="#00E5FF"
            android:textSize="32sp" android:textStyle="bold" android:fontFamily="monospace"
            android:letterSpacing="0.05"/>

        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="Navigazione · Sopravvivenza · Sentinella Cielo" android:textColor="#5A7A99"
            android:textSize="13sp" android:layout_marginTop="8dp"/>
    </LinearLayout>

    <TextView android:id="@+id/splash_creator"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="bottom|center_horizontal" android:layout_marginBottom="48dp"
        android:text="Creator Maikgost" android:textColor="#FFD600"
        android:textSize="18sp" android:textStyle="bold" android:fontFamily="monospace"
        android:letterSpacing="0.1"/>

</FrameLayout>"""

DIALOG_NAVIGATE_COORDS = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp" android:background="#0D1421">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Modalita:" android:textColor="#5A7A99" android:textSize="12sp"
        android:layout_marginBottom="4dp"/>
    <Spinner android:id="@+id/sp_nav_profile"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:backgroundTint="#00FF88" android:layout_marginBottom="16dp"/>
    <Button android:id="@+id/btn_nav_search_address"
        android:layout_width="match_parent" android:layout_height="52dp"
        android:text="CERCA PER INDIRIZZO / VIA" android:backgroundTint="#00FF88"
        android:textColor="#050A14" android:textStyle="bold" android:textSize="14sp"
        android:layout_marginBottom="16dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="oppure coordinate (opzionale):" android:textColor="#5A7A99"
        android:textSize="12sp" android:layout_marginBottom="8dp"/>
    <EditText android:id="@+id/et_nav_name"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#E8F4FD" android:backgroundTint="#00E5FF"
        android:hint="Nome destinazione (opzionale)" android:layout_marginBottom="12dp"/>
    <EditText android:id="@+id/et_nav_lat"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#E8F4FD" android:backgroundTint="#00E5FF"
        android:hint="Latitudine (opzionale)" android:inputType="numberSigned|numberDecimal"
        android:layout_marginBottom="12dp"/>
    <EditText android:id="@+id/et_nav_lon"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#E8F4FD" android:backgroundTint="#00E5FF"
        android:hint="Longitudine (opzionale)" android:inputType="numberSigned|numberDecimal"/>
</LinearLayout>"""

LAYOUT_ADDRESS_SEARCH = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#050A14">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical"
        android:background="#0D1421" android:padding="12dp">
        <ImageButton android:id="@+id/btn_addr_back"
            android:layout_width="44dp" android:layout_height="44dp"
            android:src="@android:drawable/ic_menu_close_clear_cancel"
            android:background="@android:color/transparent" android:tint="#00E5FF"
            android:contentDescription="Indietro"/>
        <EditText android:id="@+id/et_addr_query"
            android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:textColor="#E8F4FD" android:backgroundTint="#00FF88"
            android:hint="Cerca via, piazza, indirizzo..." android:textColorHint="#5A7A99"
            android:inputType="text" android:imeOptions="actionSearch"
            android:layout_marginStart="8dp"/>
    </LinearLayout>
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:padding="12dp">
        <ProgressBar android:id="@+id/pb_addr_load"
            android:layout_width="22dp" android:layout_height="22dp"
            android:layout_marginEnd="10dp" android:visibility="gone"/>
        <TextView android:id="@+id/tv_addr_hint"
            android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:text="Scrivi il nome di una via" android:textColor="#5A7A99"
            android:textSize="12sp" android:fontFamily="monospace"/>
    </LinearLayout>
    <androidx.recyclerview.widget.RecyclerView android:id="@+id/rv_addr_results"
        android:layout_width="match_parent" android:layout_height="match_parent"
        android:padding="8dp" android:clipToPadding="false"/>
</LinearLayout>"""

LAYOUT_ITEM_ADDRESS_RESULT = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="14dp" android:layout_marginBottom="4dp"
    android:background="#141E2E" android:clickable="true" android:focusable="true">
    <TextView android:id="@+id/tv_addr_title"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#E8F4FD" android:textSize="15sp" android:textStyle="bold"/>
    <TextView android:id="@+id/tv_addr_sub"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#00E5FF" android:textSize="11sp" android:fontFamily="monospace"
        android:layout_marginTop="2dp"/>
</LinearLayout>"""

LAYOUT_MAP = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#0A0E1A">

    <org.mapsforge.map.android.view.MapView android:id="@+id/map_view"
        android:layout_width="match_parent" android:layout_height="match_parent"/>

    <!-- crosshair centrale per misura/selezione (nascosto di default) -->
    <View android:id="@+id/view_crosshair"
        android:layout_width="14dp" android:layout_height="14dp"
        android:layout_gravity="center" android:background="@drawable/bg_crosshair"
        android:visibility="gone"/>

    <!-- BARRA DI RICERCA in alto, sempre visibile, stile pill -->
    <LinearLayout android:id="@+id/search_bar"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="top" android:orientation="horizontal"
        android:gravity="center_vertical" android:background="@drawable/bg_searchbar"
        android:elevation="8dp" android:padding="12dp"
        android:layout_margin="14dp">
        <ImageView android:layout_width="22dp" android:layout_height="22dp"
            android:src="@android:drawable/ic_menu_search" android:tint="#5A7A99"
            android:layout_marginStart="6dp" android:layout_marginEnd="10dp"
            android:contentDescription="Cerca"/>
        <TextView android:id="@+id/tv_search_hint"
            android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:text="Cerca un indirizzo o un luogo" android:textColor="#5A7A99"
            android:textSize="15sp"/>
        <ImageView android:id="@+id/btn_layers"
            android:layout_width="38dp" android:layout_height="38dp"
            android:src="@android:drawable/ic_menu_mapmode" android:tint="#00E5FF"
            android:padding="7dp" android:background="@drawable/bg_icon_ripple"
            android:contentDescription="Strati"/>
    </LinearLayout>

    <!-- TACHIMETRO grande in alto a sinistra -->
    <LinearLayout android:id="@+id/speed_card"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="top|start" android:orientation="vertical"
        android:gravity="center" android:background="@drawable/bg_speed_card"
        android:elevation="6dp" android:padding="14dp"
        android:layout_marginStart="14dp" android:layout_marginTop="84dp">
        <TextView android:id="@+id/tv_speed_value"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="0" android:textColor="#00FF88"
            android:textSize="34sp" android:textStyle="bold" android:fontFamily="monospace"/>
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="km/h" android:textColor="#5A7A99" android:textSize="11sp"/>
    </LinearLayout>

    <!-- BUSSOLA in alto a destra (ruota) -->
    <FrameLayout android:id="@+id/compass_card"
        android:layout_width="56dp" android:layout_height="56dp"
        android:layout_gravity="top|end" android:background="@drawable/bg_round_card"
        android:elevation="6dp" android:layout_marginEnd="14dp" android:layout_marginTop="84dp">
        <ImageView android:id="@+id/iv_compass"
            android:layout_width="40dp" android:layout_height="40dp"
            android:layout_gravity="center" android:src="@drawable/ic_compass_needle"
            android:contentDescription="Bussola"/>
    </FrameLayout>

    <!-- PANNELLO DATI GPS LIVE (quota, coordinate, precisione) -->
    <LinearLayout android:id="@+id/gps_panel"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="top|end" android:orientation="vertical"
        android:background="@drawable/bg_speed_card" android:elevation="6dp"
        android:padding="10dp" android:layout_marginEnd="14dp" android:layout_marginTop="148dp">
        <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:orientation="horizontal" android:gravity="center_vertical">
            <View android:id="@+id/gps_dot"
                android:layout_width="10dp" android:layout_height="10dp"
                android:background="@drawable/bg_crosshair" android:layout_marginEnd="6dp"/>
            <TextView android:id="@+id/tv_gps_acc"
                android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="GPS --" android:textColor="#E8F4FD" android:textSize="11sp"
                android:fontFamily="monospace"/>
        </LinearLayout>
        <TextView android:id="@+id/tv_map_alt"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="-- m" android:textColor="#FFD600" android:textSize="13sp"
            android:fontFamily="monospace" android:layout_marginTop="4dp"/>
        <TextView android:id="@+id/tv_map_coords"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="--" android:textColor="#00E5FF" android:textSize="10sp"
            android:fontFamily="monospace" android:layout_marginTop="2dp"/>
    </LinearLayout>

    <!-- COLONNA tasti tondi flottanti a destra -->
    <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="end|center_vertical" android:orientation="vertical"
        android:layout_marginEnd="14dp">
        <ImageButton android:id="@+id/btn_zoom_in"
            android:layout_width="48dp" android:layout_height="48dp"
            android:src="@android:drawable/ic_input_add" android:tint="#E8F4FD"
            android:background="@drawable/bg_fab" android:elevation="6dp"
            android:layout_marginBottom="10dp" android:contentDescription="Zoom +"/>
        <ImageButton android:id="@+id/btn_zoom_out"
            android:layout_width="48dp" android:layout_height="48dp"
            android:src="@android:drawable/ic_delete" android:tint="#E8F4FD"
            android:background="@drawable/bg_fab" android:elevation="6dp"
            android:layout_marginBottom="10dp" android:contentDescription="Zoom -"/>
        <ImageButton android:id="@+id/btn_layers_side"
            android:layout_width="48dp" android:layout_height="48dp"
            android:src="@android:drawable/ic_menu_gallery" android:tint="#00E5FF"
            android:background="@drawable/bg_fab" android:elevation="6dp"
            android:layout_marginBottom="10dp" android:contentDescription="Tema"/>
        <ImageButton android:id="@+id/btn_measure"
            android:layout_width="48dp" android:layout_height="48dp"
            android:src="@android:drawable/ic_menu_edit" android:tint="#FFD600"
            android:background="@drawable/bg_fab" android:elevation="6dp"
            android:contentDescription="Misura"/>
    </LinearLayout>

    <!-- FAB grande "centra GPS" in basso a destra -->
    <ImageButton android:id="@+id/btn_center"
        android:layout_width="60dp" android:layout_height="60dp"
        android:layout_gravity="end|bottom"
        android:src="@drawable/ic_gps" android:background="@drawable/bg_fab_primary"
        android:elevation="10dp" android:layout_marginEnd="14dp" android:layout_marginBottom="180dp"
        android:contentDescription="Centra"/>

    <!-- indicatori di stato in basso a sinistra -->
    <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="bottom|start" android:orientation="vertical"
        android:layout_marginStart="14dp" android:layout_marginBottom="180dp">
        <TextView android:id="@+id/tv_zoom"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="Z15" android:textColor="#00E5FF" android:textSize="12sp"
            android:fontFamily="monospace" android:background="@drawable/bg_chip"
            android:paddingStart="10dp" android:paddingEnd="10dp" android:paddingTop="4dp"
            android:paddingBottom="4dp" android:layout_marginBottom="6dp"/>
        <TextView android:id="@+id/tv_follow_state"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="GPS" android:textColor="#00FF88" android:textSize="11sp"
            android:fontFamily="monospace" android:background="@drawable/bg_chip"
            android:paddingStart="10dp" android:paddingEnd="10dp" android:paddingTop="4dp"
            android:paddingBottom="4dp"/>
    </LinearLayout>

    <!-- misura: etichetta distanza -->
    <TextView android:id="@+id/tv_measure_info"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="center_horizontal|top" android:layout_marginTop="150dp"
        android:text="" android:textColor="#FFD600" android:textSize="15sp"
        android:textStyle="bold" android:fontFamily="monospace"
        android:background="@drawable/bg_chip" android:padding="10dp"
        android:visibility="gone"/>

    <!-- BOTTOM SHEET che scorre dal basso -->
    <LinearLayout android:id="@+id/bottom_sheet"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="bottom" android:orientation="vertical"
        android:background="@drawable/bg_bottomsheet" android:elevation="12dp"
        android:padding="16dp">
        <View android:layout_width="44dp" android:layout_height="4dp"
            android:layout_gravity="center_horizontal" android:background="@drawable/bg_handle"
            android:layout_marginBottom="14dp"/>
        <TextView android:id="@+id/tv_sheet_title"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="La tua posizione" android:textColor="#E8F4FD"
            android:textSize="18sp" android:textStyle="bold" android:fontFamily="monospace"/>
        <TextView android:id="@+id/tv_sheet_coords"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="--" android:textColor="#00E5FF" android:textSize="13sp"
            android:fontFamily="monospace" android:layout_marginTop="4dp"/>
        <TextView android:id="@+id/tv_sheet_detail"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="" android:textColor="#5A7A99" android:textSize="12sp"
            android:layout_marginTop="2dp"/>
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal" android:layout_marginTop="14dp">
            <Button android:id="@+id/btn_sheet_navigate"
                android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
                android:text="Naviga" android:backgroundTint="#00FF88" android:textColor="#050A14"
                android:textStyle="bold" android:layout_marginEnd="8dp"/>
            <Button android:id="@+id/btn_sheet_save"
                android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
                android:text="Salva" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
                android:textStyle="bold"/>
        </LinearLayout>
    </LinearLayout>

    <TextView android:id="@+id/tv_map_info"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="center" android:gravity="center"
        android:textColor="#E8F4FD" android:textSize="15sp" android:fontFamily="monospace"
        android:lineSpacingMultiplier="1.5" android:background="@drawable/bg_round_card"
        android:padding="24dp" android:layout_margin="32dp" android:visibility="gone"/>

</FrameLayout>"""

LAYOUT_DOWNLOAD = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="24dp">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Download Dati Offline Italia" android:textColor="#E8F4FD"
        android:textSize="22sp" android:textStyle="bold" android:fontFamily="monospace"
        android:layout_marginBottom="4dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Mappe = solo visualizzazione - Routing = calcolo percorsi e indicazioni"
        android:textColor="#5A7A99" android:textSize="12sp" android:layout_marginBottom="16dp"/>

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginBottom="16dp">
        <Button android:id="@+id/tab_maps"
            android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
            android:text="MAPPE" android:backgroundTint="#00E5FF" android:textColor="#050A14"
            android:textStyle="bold" android:layout_marginEnd="6dp"/>
        <Button android:id="@+id/tab_routing"
            android:layout_width="0dp" android:layout_height="48dp" android:layout_weight="1"
            android:text="ROUTING" android:backgroundTint="#00FF88" android:textColor="#050A14"
            android:textStyle="bold"/>
    </LinearLayout>

    <Button android:id="@+id/btn_verify_files"
        android:layout_width="match_parent" android:layout_height="44dp"
        android:text="VERIFICA FILE SCARICATI" android:backgroundTint="#FF6B35"
        android:textColor="#050A14" android:textStyle="bold" android:textSize="13sp"
        android:layout_marginBottom="8dp"/>

    <Button android:id="@+id/btn_rebuild_graph"
        android:layout_width="match_parent" android:layout_height="44dp"
        android:text="RICOSTRUISCI RETE STRADALE" android:backgroundTint="#FFD600"
        android:textColor="#050A14" android:textStyle="bold" android:textSize="13sp"
        android:layout_marginBottom="12dp"/>

    <LinearLayout android:id="@+id/container_maps"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:layout_marginBottom="8dp"/>

    <LinearLayout android:id="@+id/container_routing"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:layout_marginBottom="8dp" android:visibility="gone"/>

    <ProgressBar android:id="@+id/pb" style="?android:attr/progressBarStyleHorizontal"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:progressTint="#00E5FF" android:layout_marginBottom="8dp" android:visibility="gone"/>
    <TextView android:id="@+id/tv_status" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:textColor="#00E5FF"
        android:textSize="13sp" android:fontFamily="monospace" android:layout_marginBottom="8dp"/>
    <TextView android:id="@+id/tv_log" android:layout_width="match_parent"
        android:layout_height="wrap_content" android:textColor="#5A7A99"
        android:textSize="11sp" android:fontFamily="monospace"/>

</LinearLayout></ScrollView>"""

LAYOUT_WAYPOINTS = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#050A14">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:padding="16dp" android:gravity="center_vertical"
        android:background="#0D1421">
        <TextView android:layout_width="0dp" android:layout_height="wrap_content"
            android:layout_weight="1" android:text="Waypoint" android:textColor="#E8F4FD"
            android:textSize="22sp" android:textStyle="bold" android:fontFamily="monospace"/>
        <Button android:id="@+id/btn_add_wp"
            android:layout_width="wrap_content" android:layout_height="40dp"
            android:text="+ Salva GPS" android:backgroundTint="#00E5FF" android:textColor="#050A14"
            android:textStyle="bold" android:textSize="13sp"/>
    </LinearLayout>
    <androidx.recyclerview.widget.RecyclerView android:id="@+id/rv_wp"
        android:layout_width="match_parent" android:layout_height="match_parent"
        android:padding="12dp" android:clipToPadding="false"/>
</LinearLayout>"""

LAYOUT_ITEM_WP = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="14dp" android:layout_marginBottom="8dp"
    android:background="#141E2E">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginBottom="4dp">
        <View android:id="@+id/vw_color_dot"
            android:layout_width="12dp" android:layout_height="12dp" android:layout_marginEnd="10dp"/>
        <TextView android:id="@+id/tv_wp_name"
            android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:textColor="#E8F4FD" android:textSize="16sp" android:textStyle="bold"
            android:fontFamily="monospace"/>
        <Button android:id="@+id/btn_wp_nav"
            android:layout_width="wrap_content" android:layout_height="32dp"
            android:text="Naviga" android:backgroundTint="#00FF88" android:textColor="#050A14"
            android:textSize="11sp" android:textStyle="bold" android:minWidth="0dp"
            android:paddingStart="10dp" android:paddingEnd="10dp" android:layout_marginEnd="6dp"/>
        <Button android:id="@+id/btn_wp_del"
            android:layout_width="32dp" android:layout_height="32dp"
            android:text="X" android:backgroundTint="#FF1744" android:textColor="#FFFFFF"
            android:textSize="12sp" android:padding="0dp"/>
    </LinearLayout>
    <TextView android:id="@+id/tv_wp_coords"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#00E5FF" android:textSize="12sp" android:fontFamily="monospace"
        android:layout_marginBottom="2dp"/>
    <TextView android:id="@+id/tv_wp_desc"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#5A7A99" android:textSize="12sp" android:layout_marginBottom="4dp"/>
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal">
        <TextView android:id="@+id/tv_wp_time"
            android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:textColor="#5A7A99" android:textSize="11sp" android:fontFamily="monospace"/>
        <TextView android:id="@+id/tv_wp_dist"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:textColor="#00FF88" android:textSize="12sp" android:textStyle="bold"
            android:fontFamily="monospace" android:layout_marginEnd="12dp"/>
        <TextView android:id="@+id/tv_wp_eta"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:textColor="#FF6B35" android:textSize="11sp" android:fontFamily="monospace"/>
    </LinearLayout>
</LinearLayout>"""

DIALOG_ADD_WP = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="20dp" android:background="#0D1421">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Coordinate GPS:" android:textColor="#5A7A99" android:textSize="12sp"
        android:layout_marginBottom="4dp"/>
    <TextView android:id="@+id/tv_wp_coords_preview"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#00E5FF" android:textSize="12sp" android:fontFamily="monospace"
        android:layout_marginBottom="14dp"/>
    <EditText android:id="@+id/et_wp_name"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#E8F4FD" android:backgroundTint="#00E5FF"
        android:hint="Nome waypoint" android:layout_marginBottom="12dp"/>
    <EditText android:id="@+id/et_wp_desc"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#E8F4FD" android:backgroundTint="#00E5FF"
        android:hint="Descrizione (opzionale)" android:layout_marginBottom="12dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Colore marker:" android:textColor="#5A7A99" android:textSize="12sp"
        android:layout_marginBottom="4dp"/>
    <Spinner android:id="@+id/sp_wp_color"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:backgroundTint="#00E5FF"/>
</LinearLayout>"""

def _stat_row(label, vid, color):
    return ('<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
        '    android:orientation="horizontal" android:layout_marginBottom="8dp">\n'
        '    <TextView android:layout_width="0dp" android:layout_height="wrap_content"\n'
        '        android:layout_weight="1" android:text="' + label + '" android:textColor="#5A7A99"\n'
        '        android:textSize="13sp"/>\n'
        '    <TextView android:id="@+id/' + vid + '" android:layout_width="wrap_content"\n'
        '        android:layout_height="wrap_content" android:textColor="' + color + '"\n'
        '        android:textSize="13sp" android:fontFamily="monospace"/>\n'
        '</LinearLayout>\n')

LAYOUT_STATS = ("""\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="24dp">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Statistiche GPS" android:textColor="#E8F4FD" android:textSize="24sp"
        android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="20dp"/>
    <TextView android:id="@+id/tv_stat_gps_state"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#00E5FF" android:textSize="16sp" android:fontFamily="monospace"
        android:layout_marginBottom="20dp"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="SESSIONE CORRENTE" android:textColor="#5A7A99" android:textSize="11sp"
        android:textStyle="bold" android:layout_marginBottom="12dp"/>
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginBottom="16dp">
        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"
            android:layout_weight="1" android:orientation="vertical"
            android:background="@drawable/bg_card_glass" android:padding="14dp" android:layout_marginEnd="8dp">
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="VEL. MAX" android:textColor="#5A7A99" android:textSize="11sp"/>
            <TextView android:id="@+id/tv_stat_max_spd"
                android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="0.0 km/h" android:textColor="#00FF88" android:textSize="22sp"
                android:textStyle="bold" android:fontFamily="monospace"/>
        </LinearLayout>
        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"
            android:layout_weight="1" android:orientation="vertical"
            android:background="@drawable/bg_card_glass" android:padding="14dp">
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="DIST. TOTALE" android:textColor="#5A7A99" android:textSize="11sp"/>
            <TextView android:id="@+id/tv_stat_total_dist"
                android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="0 m" android:textColor="#00E5FF" android:textSize="22sp"
                android:textStyle="bold" android:fontFamily="monospace"/>
        </LinearLayout>
    </LinearLayout>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="POSIZIONE ATTUALE" android:textColor="#5A7A99" android:textSize="11sp"
        android:textStyle="bold" android:layout_marginBottom="12dp"/>
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:background="@drawable/bg_card_glass" android:padding="16dp"
        android:layout_marginBottom="16dp">
"""
    + _stat_row("Latitudine", "tv_stat_last_lat", "#00E5FF")
    + _stat_row("Longitudine", "tv_stat_last_lon", "#00E5FF")
    + _stat_row("Altitudine", "tv_stat_last_alt", "#00FF88")
    + _stat_row("Precisione", "tv_stat_last_acc", "#FFD600")
    + _stat_row("Velocita", "tv_stat_last_spd", "#00FF88")
    + _stat_row("Rotta", "tv_stat_bearing", "#00E5FF")
    + _stat_row("Satelliti", "tv_stat_sats", "#00FF88")
    + """    </LinearLayout>
</LinearLayout></ScrollView>""")

# >>> V4 SENTINELLA CIELO
# ============================================================
#  v4.0 SENTINELLA CIELO — rilevamento PASSIVO di droni
#  (Remote ID Bluetooth/Wi-Fi + firma acustica delle eliche),
#  segnalazioni anonime, verifica avvistamenti e nuova grafica.
# ============================================================

SKY_REMOTE_ID_PARSER = r"""package com.offlinegps.map.sky;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Decoder dei messaggi Remote ID (ASTM F3411 / ASD-STAN EN 4709-002): gli
 * stessi che i droni conformi UE trasmettono via Bluetooth e Wi-Fi.
 * Ogni messaggio e' lungo 25 byte; il primo byte contiene il tipo (nibble
 * alto) e la versione del protocollo (nibble basso). I campi multi-byte
 * sono little-endian. Contiene anche gli encoder usati dalla modalita'
 * DEMO e dai test.
 */
public final class RemoteIdParser {
    public static final int MSG_SIZE = 25;
    public static final int PROTO_VERSION = 2;
    public static final int TYPE_BASIC_ID    = 0x0;
    public static final int TYPE_LOCATION    = 0x1;
    public static final int TYPE_AUTH        = 0x2;
    public static final int TYPE_SELF_ID     = 0x3;
    public static final int TYPE_SYSTEM      = 0x4;
    public static final int TYPE_OPERATOR_ID = 0x5;
    public static final int TYPE_PACK        = 0xF;

    public static final int STATUS_UNDECLARED = 0;
    public static final int STATUS_GROUND     = 1;
    public static final int STATUS_AIRBORNE   = 2;
    public static final int STATUS_EMERGENCY  = 3;
    public static final int STATUS_RID_FAIL   = 4;

    private RemoteIdParser() {}

    /** Un messaggio decodificato: sono valorizzati solo i campi del suo tipo. */
    public static final class Message {
        public int type;
        // Basic ID
        public int idType, uaType;
        public String uasId = "";
        // Location / Vector
        public int status, heightType;
        public float direction = Float.NaN, speed = Float.NaN, vspeed = Float.NaN;
        public double lat = Double.NaN, lon = Double.NaN;
        public float altBaro = Float.NaN, altGeo = Float.NaN, height = Float.NaN;
        public int hAccuracy, vAccuracy;
        // Self-ID
        public String text = "";
        // System
        public double opLat = Double.NaN, opLon = Double.NaN;
        public float opAlt = Float.NaN;
        public int category = -1, classEU = -1, opLocType;
        // Operator ID
        public String operatorId = "";
    }

    /** Decodifica un messaggio singolo o un Message Pack che inizia a off. */
    public static List<Message> parse(byte[] d, int off) {
        List<Message> out = new ArrayList<>();
        if (d == null || off < 0 || d.length - off < 1) return out;
        int type = (d[off] & 0xF0) >> 4;
        if (type == TYPE_PACK) {
            if (d.length - off < 3) return out;
            int size = d[off + 1] & 0xFF;
            int count = d[off + 2] & 0xFF;
            if (size != MSG_SIZE || count > 10) return out;
            for (int i = 0; i < count; i++) {
                int mo = off + 3 + i * MSG_SIZE;
                if (mo + MSG_SIZE > d.length) break;
                Message m = parseOne(d, mo);
                if (m != null) out.add(m);
            }
        } else {
            Message m = parseOne(d, off);
            if (m != null) out.add(m);
        }
        return out;
    }

    static Message parseOne(byte[] d, int o) {
        if (o < 0 || o + MSG_SIZE > d.length) return null;
        Message m = new Message();
        m.type = (d[o] & 0xF0) >> 4;
        switch (m.type) {
            case TYPE_BASIC_ID:
                m.idType = (d[o + 1] & 0xF0) >> 4;
                m.uaType = d[o + 1] & 0x0F;
                m.uasId = ascii(d, o + 2, 20);
                return m;
            case TYPE_LOCATION: {
                int flags = d[o + 1] & 0xFF;
                m.status = (flags & 0xF0) >> 4;
                m.heightType = (flags >> 2) & 1;
                boolean ew = ((flags >> 1) & 1) == 1;
                boolean mult = (flags & 1) == 1;
                int dir = (d[o + 2] & 0xFF) + (ew ? 180 : 0);
                m.direction = dir < 360 ? dir : Float.NaN;          // 361 = sconosciuto
                int sp = d[o + 3] & 0xFF;
                float speed = mult ? sp * 0.75f + 63.75f : sp * 0.25f;
                m.speed = speed >= 254f ? Float.NaN : speed;          // 255 m/s = sconosciuto
                float vs = d[o + 4] * 0.5f;                           // int8 con segno
                m.vspeed = Math.abs(vs) >= 62f ? Float.NaN : vs;      // 63 m/s = sconosciuto
                int lat = le32(d, o + 5), lon = le32(d, o + 9);
                if (lat != 0 || lon != 0) {
                    m.lat = lat * 1e-7;
                    m.lon = lon * 1e-7;
                    if (Math.abs(m.lat) > 90 || Math.abs(m.lon) > 180) {
                        m.lat = Double.NaN; m.lon = Double.NaN;
                    }
                }
                m.altBaro = alt(le16(d, o + 13));
                m.altGeo  = alt(le16(d, o + 15));
                m.height  = alt(le16(d, o + 17));
                m.hAccuracy = d[o + 19] & 0x0F;
                m.vAccuracy = (d[o + 19] & 0xF0) >> 4;
                return m;
            }
            case TYPE_SELF_ID:
                m.text = ascii(d, o + 2, 23);
                return m;
            case TYPE_SYSTEM: {
                m.opLocType = d[o + 1] & 0x03;
                int lat = le32(d, o + 2), lon = le32(d, o + 6);
                if (lat != 0 || lon != 0) {
                    m.opLat = lat * 1e-7;
                    m.opLon = lon * 1e-7;
                }
                m.category = (d[o + 17] & 0xF0) >> 4;
                m.classEU = d[o + 17] & 0x0F;
                m.opAlt = alt(le16(d, o + 18));
                return m;
            }
            case TYPE_OPERATOR_ID:
                m.operatorId = ascii(d, o + 2, 20);
                return m;
            case TYPE_AUTH:
                return m;   // autenticazione: non serve per la visualizzazione
            default:
                return null;
        }
    }

    // ------------------------------------------------------------ encoder
    public static byte[] encodeBasicId(int idType, int uaType, String id) {
        byte[] m = header(TYPE_BASIC_ID);
        m[1] = (byte) (((idType & 0x0F) << 4) | (uaType & 0x0F));
        putAscii(m, 2, 20, id);
        return m;
    }

    public static byte[] encodeLocation(int status, float dirDeg, float speedMs, float vsMs,
            double lat, double lon, float altGeo, float height) {
        byte[] m = header(TYPE_LOCATION);
        int dir = Math.round(dirDeg) % 360;
        if (dir < 0) dir += 360;
        boolean ew = dir >= 180;
        int spRaw; boolean mult;
        if (speedMs <= 63.75f) { mult = false; spRaw = Math.round(speedMs / 0.25f); }
        else if (speedMs < 254.25f) { mult = true; spRaw = Math.round((speedMs - 63.75f) / 0.75f); }
        else { mult = true; spRaw = 254; }
        m[1] = (byte) (((status & 0x0F) << 4) | ((ew ? 1 : 0) << 1) | (mult ? 1 : 0));
        m[2] = (byte) (ew ? dir - 180 : dir);
        m[3] = (byte) Math.min(254, Math.max(0, spRaw));
        m[4] = (byte) Math.max(-125, Math.min(125, Math.round(vsMs / 0.5f)));
        put32(m, 5, (int) Math.round(lat * 1e7));
        put32(m, 9, (int) Math.round(lon * 1e7));
        put16(m, 13, altEnc(Float.NaN));
        put16(m, 15, altEnc(altGeo));
        put16(m, 17, altEnc(height));
        m[19] = (byte) ((4 << 4) | 10);   // accuratezza: verticale <10 m, orizzontale <10 m
        return m;
    }

    public static byte[] encodeSelfId(String text) {
        byte[] m = header(TYPE_SELF_ID);
        putAscii(m, 2, 23, text);
        return m;
    }

    public static byte[] encodeSystem(double opLat, double opLon, int category, int classEU) {
        byte[] m = header(TYPE_SYSTEM);
        m[1] = (byte) (1 | (1 << 2));     // posizione operatore live GNSS, classificazione UE
        put32(m, 2, (int) Math.round(opLat * 1e7));
        put32(m, 6, (int) Math.round(opLon * 1e7));
        put16(m, 10, 1);
        m[17] = (byte) (((category & 0x0F) << 4) | (classEU & 0x0F));
        put16(m, 18, altEnc(Float.NaN));
        return m;
    }

    public static byte[] encodeOperatorId(String id) {
        byte[] m = header(TYPE_OPERATOR_ID);
        putAscii(m, 2, 20, id);
        return m;
    }

    public static byte[] encodePack(byte[]... msgs) {
        byte[] p = new byte[3 + msgs.length * MSG_SIZE];
        p[0] = (byte) ((TYPE_PACK << 4) | PROTO_VERSION);
        p[1] = (byte) MSG_SIZE;
        p[2] = (byte) msgs.length;
        for (int i = 0; i < msgs.length; i++) System.arraycopy(msgs[i], 0, p, 3 + i * MSG_SIZE, MSG_SIZE);
        return p;
    }

    // ------------------------------------------------------------ etichette
    public static String uaTypeName(int t) {
        switch (t) {
            case 1: return "Aereo ad ala fissa";
            case 2: return "Multirotore";
            case 3: return "Autogiro";
            case 4: return "VTOL ibrido";
            case 5: return "Ornitottero";
            case 6: return "Aliante";
            case 7: return "Aquilone";
            case 8: return "Pallone libero";
            case 9: return "Pallone vincolato";
            case 10: return "Dirigibile";
            case 11: return "Paracadute";
            case 12: return "Razzo";
            case 13: return "Vincolato a motore";
            case 14: return "Ostacolo a terra";
            case 15: return "Altro";
            default: return "Tipo non dichiarato";
        }
    }

    public static String statusName(int s) {
        switch (s) {
            case STATUS_GROUND: return "A terra";
            case STATUS_AIRBORNE: return "In volo";
            case STATUS_EMERGENCY: return "EMERGENZA";
            case STATUS_RID_FAIL: return "Guasto Remote ID";
            default: return "Stato non dichiarato";
        }
    }

    public static String classLabel(int category, int classEU) {
        String cat;
        switch (category) {
            case 1: cat = "Open"; break;
            case 2: cat = "Specific"; break;
            case 3: cat = "Certified"; break;
            default: cat = "";
        }
        String cls = (classEU >= 1 && classEU <= 7) ? "C" + (classEU - 1) : "";
        if (cat.isEmpty() && cls.isEmpty()) return "";
        return (cat + " " + cls).trim();
    }

    // ------------------------------------------------------------ util
    private static byte[] header(int type) {
        byte[] m = new byte[MSG_SIZE];
        m[0] = (byte) ((type << 4) | PROTO_VERSION);
        return m;
    }

    private static float alt(int raw) {
        if (raw == 0) return Float.NaN;          // -1000 m = sconosciuto
        return raw * 0.5f - 1000f;
    }

    private static int altEnc(float v) {
        if (Float.isNaN(v)) return 0;
        return Math.max(0, Math.min(65535, Math.round((v + 1000f) / 0.5f)));
    }

    static int le16(byte[] d, int o) {
        return (d[o] & 0xFF) | ((d[o + 1] & 0xFF) << 8);
    }

    static int le32(byte[] d, int o) {
        return (d[o] & 0xFF) | ((d[o + 1] & 0xFF) << 8)
            | ((d[o + 2] & 0xFF) << 16) | ((d[o + 3] & 0xFF) << 24);
    }

    private static void put16(byte[] d, int o, int v) {
        d[o] = (byte) v; d[o + 1] = (byte) (v >> 8);
    }

    private static void put32(byte[] d, int o, int v) {
        d[o] = (byte) v; d[o + 1] = (byte) (v >> 8);
        d[o + 2] = (byte) (v >> 16); d[o + 3] = (byte) (v >> 24);
    }

    private static void putAscii(byte[] d, int o, int max, String s) {
        if (s == null) return;
        byte[] b = s.getBytes(StandardCharsets.US_ASCII);
        System.arraycopy(b, 0, d, o, Math.min(max, b.length));
    }

    /** Testo ASCII stampabile fino al primo byte nullo. */
    static String ascii(byte[] d, int o, int max) {
        StringBuilder sb = new StringBuilder(max);
        for (int i = 0; i < max && o + i < d.length; i++) {
            int c = d[o + i] & 0xFF;
            if (c == 0) break;
            if (c >= 0x20 && c < 0x7F) sb.append((char) c);
        }
        return sb.toString().trim();
    }
}
"""

SKY_FFT = r"""package com.offlinegps.map.sky;

/** FFT radix-2 iterativa in-place con tabelle precalcolate (nessuna allocazione per frame). */
public final class Fft {
    private final int n;
    private final int[] rev;
    private final double[] cos, sin;

    public Fft(int n) {
        if (Integer.bitCount(n) != 1) throw new IllegalArgumentException("n deve essere potenza di 2");
        this.n = n;
        rev = new int[n];
        int bits = Integer.numberOfTrailingZeros(n);
        for (int i = 0; i < n; i++) rev[i] = Integer.reverse(i) >>> (32 - bits);
        cos = new double[n / 2];
        sin = new double[n / 2];
        for (int i = 0; i < n / 2; i++) {
            cos[i] = Math.cos(-2 * Math.PI * i / n);
            sin[i] = Math.sin(-2 * Math.PI * i / n);
        }
    }

    public void transform(double[] re, double[] im) {
        for (int i = 0; i < n; i++) {
            int j = rev[i];
            if (j > i) {
                double t = re[i]; re[i] = re[j]; re[j] = t;
                t = im[i]; im[i] = im[j]; im[j] = t;
            }
        }
        for (int size = 2; size <= n; size <<= 1) {
            int half = size >> 1, step = n / size;
            for (int start = 0; start < n; start += size) {
                for (int k = 0; k < half; k++) {
                    double wr = cos[k * step], wi = sin[k * step];
                    int a = start + k, b = a + half;
                    double xr = re[b] * wr - im[b] * wi;
                    double xi = re[b] * wi + im[b] * wr;
                    re[b] = re[a] - xr; im[b] = im[a] - xi;
                    re[a] += xr;        im[a] += xi;
                }
            }
        }
    }
}
"""

SKY_ACOUSTIC_ANALYZER = r"""package com.offlinegps.map.sky;

import java.util.Arrays;

/**
 * Riconoscimento acustico dei droni, interamente on-device e senza modelli.
 *
 * Le eliche di un drone producono un tono alla "frequenza di passaggio
 * pala" (giri/s x numero di pale, tipicamente 100-500 Hz) piu' una serie
 * ordinata di ARMONICHE (2f, 3f, 4f...), stabile per secondi. Il vento e il
 * traffico sono rumore senza righe, la voce cambia altezza di continuo, un
 * bip ha una sola riga, i motori a scoppio e il ronzio di rete hanno la
 * fondamentale sotto i 70 Hz.
 *
 * Per ogni finestra (4096 campioni a 16 kHz = 0,26 s, 3,9 Hz per bin):
 *  1. due spettri di potenza mediati: BREVE (ultime 4 finestre, ~0,6 s) e
 *     LUNGO (ultime 16, ~2,2 s). Nel lungo sopravvivono solo le righe
 *     stabili: quelle che scivolano (voce, sirene) si spalmano;
 *  2. "prominenza" di ogni bin rispetto al fondo locale (+/-100 Hz);
 *  3. per ogni fondamentale candidata 70-520 Hz si cercano le prime 10
 *     armoniche (tolleranza +/-2,5% perche' i 4 motori girano a velocita'
 *     leggermente diverse) e le posizioni intermedie, che devono essere
 *     vuote; si tiene il pettine migliore;
 *  4. veto sub-armonico: se una fondamentale sotto i 70 Hz spiega anche
 *     righe intermedie e' un motore a scoppio o il ronzio di rete;
 *  5. punteggio = pettine nello spettro lungo (persistenza) x pettine nello
 *     spettro breve (presenza adesso), poi smussato nel tempo.
 * E' un'euristica: tosaerba, scooter e ventole hanno firme simili.
 */
public final class AcousticAnalyzer {
    public static final int SAMPLE_RATE = 16000;
    public static final int FFT_SIZE = 4096;
    public static final int HOP = 2048;
    public static final float DISPLAY_MAX_HZ = 3000f;
    public static final int DISPLAY_BINS = 256;

    private static final float BIN_HZ = (float) SAMPLE_RATE / FFT_SIZE;
    private static final float F0_MIN = 70f, F0_MAX = 520f, BAND_MAX = 5000f;
    private static final int HARMONICS = 10;
    private static final float TOL = 0.025f;
    private static final float PROM_CLIP = 20f, PROM_PRESENT = 5.5f, CONTRAST = 3f, LONG_PRESENT = 4f;
    private static final int SHORT = 4, LONG = 16;
    private static final float GATE_DB = -80f;      // sotto: microfono muto
    private static final float SMOOTH = 0.35f;
    private static final int HISTORY = 24;          // ~3 s di fondamentali
    private static final float STEADY_DB = 2.5f;    // oscillazione di livello tollerata
    private static final int OLD_FROM = 6;          // persistenza: finestre da 0,8 a 2 s fa

    public static final class Result {
        public float score;        // 0..1 probabilita' "firma da drone"
        public float frameScore;   // armonicita' nello spettro breve
        public float f0;           // fondamentale stimata (Hz), 0 se nessuna
        public int harmonics;      // armoniche presenti
        public float rmsDb;        // livello del segnale (dBFS)
        public float stability;    // 0..1 continuita' e persistenza della serie armonica
        public float[] spectrum;   // DISPLAY_BINS valori 0..1 (0-3000 Hz) per lo spettrogramma
    }

    private final Fft fft = new Fft(FFT_SIZE);
    private final int half = FFT_SIZE / 2;
    private final int topBin = Math.min(half - 1, Math.round(BAND_MAX * 1.03f / BIN_HZ) + 30);
    private final double[] re = new double[FFT_SIZE], im = new double[FFT_SIZE];
    private final float[] window = new float[FFT_SIZE];
    private final float[][] pow = new float[LONG][topBin + 1];
    private final float[] magDb = new float[half];          // finestra corrente (spettrogramma)
    private final float[] shortDb = new float[topBin + 1], longDb = new float[topBin + 1];
    private final float[] shortProm = new float[topBin + 1], longProm = new float[topBin + 1];
    private final double[] prefix = new double[topBin + 2];
    private final float[] sortBuf;
    private final float[] histF0 = new float[HISTORY];
    private int powPos = 0, powCount = 0, histPos = 0;
    private float smoothed = 0;
    // risultato dell'ultima ricerca del pettine
    private float combF0, combProm, combFrame;
    private int combPresent;

    public AcousticAnalyzer() {
        for (int i = 0; i < FFT_SIZE; i++)
            window[i] = (float) (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (FFT_SIZE - 1)));
        sortBuf = new float[bin(DISPLAY_MAX_HZ) - bin(60f)];
    }

    private static int bin(float hz) { return Math.round(hz / BIN_HZ); }

    public void reset() {
        powPos = powCount = histPos = 0;
        smoothed = 0;
        for (float[] p : pow) Arrays.fill(p, 0);
        Arrays.fill(histF0, 0);
    }

    /** Analizza FFT_SIZE campioni PCM 16 bit (finestra scorrevole, chiamare ogni HOP campioni). */
    public Result analyze(short[] pcm) {
        Result r = new Result();
        double sumSq = 0;
        for (int i = 0; i < FFT_SIZE; i++) {
            double s = pcm[i] / 32768.0;
            sumSq += s * s;
            re[i] = s * window[i];
            im[i] = 0;
        }
        r.rmsDb = (float) (10 * Math.log10(sumSq / FFT_SIZE + 1e-12));
        fft.transform(re, im);
        float[] cur = pow[powPos];
        for (int k = 0; k < half; k++) {
            double p = re[k] * re[k] + im[k] * im[k] + 1e-12;
            if (k <= topBin) cur[k] = (float) p;
            magDb[k] = (float) (10 * Math.log10(p));
        }
        powPos = (powPos + 1) % LONG;
        if (powCount < LONG) powCount++;

        float inst = 0f, shortF0 = 0f;
        if (r.rmsDb > GATE_DB && powCount >= SHORT) {
            averageDb(1, SHORT, shortDb);
            prominence(shortDb, shortProm);
            comb(shortProm);
            float shortFrame = combFrame;
            shortF0 = combF0;
            r.frameScore = shortFrame;
            r.f0 = shortF0;
            r.harmonics = combPresent;
            if (powCount >= LONG && shortFrame > 0) {
                // continuita': la stessa serie armonica nelle finestre precedenti (~3 s).
                // Un drone suona senza interruzioni; voce e musica cambiano nota
                int same = 0;
                for (float f : histF0) if (sameSeries(f, shortF0, 0.10f)) same++;
                float cont = Math.max(0f, Math.min(1f, (same / (float) HISTORY - 0.5f) / 0.3f));
                // persistenza: le armoniche di adesso c'erano gia' 1-2 s fa, alla stessa frequenza?
                averageDb(OLD_FROM, LONG, longDb);
                prominence(longDb, longProm);
                int kept = 0;
                for (int h = 1; h <= 6; h++) {
                    float fh = shortF0 * h;
                    if (fh > BAND_MAX) break;
                    float p = peakNear(longProm, fh, TOL * 1.2f);
                    float q = Math.max(0f, peakNear(longProm, fh - shortF0 * 0.5f, TOL * 0.6f));
                    if (p >= LONG_PRESENT && p - q >= CONTRAST) kept++;
                }
                float persist = Math.max(0f, Math.min(1f, (kept - 1) / 2f));
                r.stability = cont * persist * steadiness(shortF0);
                inst = shortFrame * r.stability;
            }
        }
        histF0[histPos] = shortF0;
        histPos = (histPos + 1) % HISTORY;
        smoothed += SMOOTH * (inst - smoothed);
        r.score = Math.max(0f, Math.min(1f, smoothed * 1.15f));

        // spettro per lo spettrogramma: 0-3000 Hz su 256 righe (massimo per gruppo)
        int b0 = bin(60f);
        System.arraycopy(magDb, b0, sortBuf, 0, sortBuf.length);
        Arrays.sort(sortBuf);
        float noiseDb = Math.max(sortBuf[sortBuf.length / 2], -40f);
        float[] disp = new float[DISPLAY_BINS];
        int maxBin = bin(DISPLAY_MAX_HZ);
        for (int i = 0; i < DISPLAY_BINS; i++) {
            int a = i * maxBin / DISPLAY_BINS, b = Math.max(a + 1, (i + 1) * maxBin / DISPLAY_BINS);
            float m = -200;
            for (int k = a; k < b && k < half; k++) if (magDb[k] > m) m = magDb[k];
            // il fondo di rumore resta scuro, le righe delle eliche (20-40 dB sopra) si accendono
            disp[i] = Math.max(0f, Math.min(1f, (m - noiseDb - 4f) / 36f));
        }
        r.spectrum = disp;
        return r;
    }

    /** Media in potenza delle finestre da "from" a "to" fa (1 = l'ultima), in dB. */
    private void averageDb(int from, int to, float[] out) {
        int n = to - from + 1;
        for (int k = 0; k <= topBin; k++) {
            double s = 0;
            for (int j = from; j <= to; j++) s += pow[(powPos - j + LONG) % LONG][k];
            out[k] = (float) (10 * Math.log10(s / n));
        }
    }

    /** prominenza = livello del bin - media locale (+/-100 Hz, escluso il picco). */
    private void prominence(float[] db, float[] out) {
        prefix[0] = 0;
        for (int k = 0; k <= topBin; k++) prefix[k + 1] = prefix[k] + db[k];
        final int outer = 26, inner = 4;
        for (int k = 0; k <= topBin; k++) {
            int lo = Math.max(0, k - outer), hi = Math.min(topBin, k + outer);
            int ilo = Math.max(0, k - inner), ihi = Math.min(topBin, k + inner);
            double sum = (prefix[hi + 1] - prefix[lo]) - (prefix[ihi + 1] - prefix[ilo]);
            int cnt = (hi - lo + 1) - (ihi - ilo + 1);
            out[k] = cnt > 0 ? db[k] - (float) (sum / cnt) : 0f;
        }
    }

    /** Pettine armonico con "denti negativi": risultato in comb*. */
    private void comb(float[] prom) {
        float bestScore = 0, bestF0 = 0, bestProm = 0; int bestPresent = 0;
        for (float f0 = F0_MIN; f0 <= F0_MAX; f0 *= 1.01f) {
            float sum = 0; int present = 0, eff = 0;
            boolean low = false;
            for (int h = 1; h <= HARMONICS; h++) {
                float fh = f0 * h;
                if (fh > BAND_MAX) break;
                eff++;
                // le armoniche basse sono le piu' affidabili: pesano di piu'
                float wgt = 1f / (1f + 0.15f * (h - 1));
                float p = peakNear(prom, fh, TOL);
                float q = Math.max(0f, peakNear(prom, fh - f0 * 0.5f, TOL * 0.6f));
                if (p >= PROM_PRESENT && p - q >= CONTRAST) {
                    present++;
                    if (h <= 2) low = true;
                    sum += wgt * (Math.min(PROM_CLIP, p) - 0.5f * Math.min(PROM_CLIP, q));
                } else if (q >= PROM_PRESENT) {
                    sum -= wgt * 0.5f * Math.min(PROM_CLIP, q);
                }
            }
            // serve la fondamentale o la seconda armonica: elimina i pettini "casuali"
            if (eff < 4 || !low) continue;
            // le armoniche mancanti penalizzano: cosi' vince la vera fondamentale
            float score = sum * present / eff;
            if (score > bestScore) {
                bestScore = score; bestF0 = f0; bestPresent = present;
                bestProm = present > 0 ? 1.4f * sum / present : 0;
            }
        }
        // veto sub-armonico: se una fondamentale sotto i 70 Hz spiega le righe
        // altrettanto bene (motore a scoppio, ronzio di rete) non e' un drone
        for (int k = 2; k <= 4 && bestPresent > 0; k++) {
            float sub = bestF0 / k;
            if (sub >= F0_MIN || sub < 20f) continue;
            int present = 0, eff = 0;
            for (int h = 1; h <= HARMONICS; h++) {
                if (sub * h > BAND_MAX) break;
                eff++;
                if (peakNear(prom, sub * h, TOL) >= PROM_PRESENT) present++;
            }
            if (eff > 0 && present >= 0.6f * eff) bestPresent = 0;
        }
        float frame = 0f;
        if (bestPresent >= 3) {
            float count = Math.min(1f, (bestPresent - 2) / 4f);
            float level = Math.min(1f, 0.45f + bestProm / 18f);
            frame = count * level;
        }
        combF0 = frame > 0 ? bestF0 : 0;
        combPresent = frame > 0 ? bestPresent : 0;
        combProm = bestProm;
        combFrame = frame;
    }

    /**
     * Regolarita' del livello delle prime 3 armoniche finestra per finestra
     * negli ultimi ~2 s: un rotore mantiene il livello, una nota musicale
     * decade e poi riattacca, la voce va e viene. 1 = costante, 0 = irregolare.
     */
    private float steadiness(float f0) {
        float total = 0; int used = 0;
        for (int h = 1; h <= 3; h++) {
            float fh = f0 * h;
            int c = Math.round(fh / BIN_HZ), w = Math.max(1, Math.round(fh * TOL / BIN_HZ));
            if (c + w > topBin) break;
            double mean = 0, sq = 0;
            for (int j = 1; j <= LONG; j++) {
                float[] p = pow[(powPos - j + LONG) % LONG];
                float m = 0;
                for (int k = Math.max(1, c - w); k <= c + w; k++) if (p[k] > m) m = p[k];
                double db = 10 * Math.log10(m + 1e-12);
                mean += db; sq += db * db;
            }
            mean /= LONG;
            total += (float) Math.sqrt(Math.max(0, sq / LONG - mean * mean));
            used++;
        }
        if (used == 0) return 0f;
        float std = total / used;
        return Math.max(0f, Math.min(1f, 1f - (std - STEADY_DB) / 3f));
    }

    /** Stessa serie armonica a meno di un'ottava (f, 2f, f/2) entro la tolleranza. */
    private static boolean sameSeries(float a, float b, float tol) {
        if (a <= 0 || b <= 0) return false;
        float r = a / b;
        return Math.abs(r - 1f) < tol || Math.abs(r - 2f) < 2 * tol || Math.abs(r - 0.5f) < tol / 2;
    }

    /** Prominenza massima entro +/-tol (almeno +/-1 bin) attorno a hz. */
    private float peakNear(float[] prom, float hz, float tol) {
        int c = Math.round(hz / BIN_HZ);
        int w = Math.max(1, Math.round(hz * tol / BIN_HZ));
        float p = -99;
        for (int k = Math.max(1, c - w); k <= Math.min(topBin, c + w); k++) if (prom[k] > p) p = prom[k];
        return p;
    }
}
"""

SKY_ACOUSTIC_DETECTOR = r"""package com.offlinegps.map.sky;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Handler;
import android.os.Looper;

/**
 * Ascolto del microfono per il riconoscimento acustico (AcousticAnalyzer).
 * Tutto resta sul telefono: l'audio non viene salvato ne' inviato.
 * Usa la sorgente UNPROCESSED o VOICE_RECOGNITION quando possibile, perche'
 * la riduzione del rumore del microfono "normale" cancellerebbe proprio il
 * ronzio stabile delle eliche.
 */
public final class AcousticDetector {
    public interface Listener { void onResult(AcousticAnalyzer.Result r); }

    private final Context ctx;
    private final Handler main = new Handler(Looper.getMainLooper());
    private volatile boolean running;
    private Thread thread;
    public volatile String sourceName = "";
    public volatile String lastError = "";

    public AcousticDetector(Context c) { ctx = c.getApplicationContext(); }

    public boolean hasPermission() {
        return ctx.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
    }

    public boolean isRunning() { return running; }

    public boolean start(final Listener listener) {
        if (running) return true;
        if (!hasPermission()) { lastError = "Permesso microfono mancante"; return false; }
        final AudioRecord rec = open();
        if (rec == null) return false;
        running = true;
        thread = new Thread(() -> loop(rec, listener), "acoustic-detector");
        thread.setPriority(Thread.NORM_PRIORITY - 1);
        thread.start();
        return true;
    }

    private AudioRecord open() {
        int rate = AcousticAnalyzer.SAMPLE_RATE;
        int min = AudioRecord.getMinBufferSize(rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        if (min <= 0) { lastError = "Microfono non supporta 16 kHz"; return null; }
        int buf = Math.max(min, AcousticAnalyzer.FFT_SIZE * 4);
        boolean unprocessed = false;
        try {
            AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
            unprocessed = am != null && "true".equals(am.getProperty(AudioManager.PROPERTY_SUPPORT_AUDIO_SOURCE_UNPROCESSED));
        } catch (Exception ignored) {}
        int[] sources = unprocessed
            ? new int[]{MediaRecorder.AudioSource.UNPROCESSED, MediaRecorder.AudioSource.VOICE_RECOGNITION, MediaRecorder.AudioSource.MIC}
            : new int[]{MediaRecorder.AudioSource.VOICE_RECOGNITION, MediaRecorder.AudioSource.MIC};
        for (int src : sources) {
            try {
                AudioRecord r = new AudioRecord(src, rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, buf);
                if (r.getState() == AudioRecord.STATE_INITIALIZED) {
                    sourceName = src == MediaRecorder.AudioSource.UNPROCESSED ? "grezzo (senza filtri)"
                        : src == MediaRecorder.AudioSource.VOICE_RECOGNITION ? "riconoscimento (filtri ridotti)" : "standard";
                    return r;
                }
                r.release();
            } catch (SecurityException e) {
                lastError = "Permesso microfono negato";
                return null;
            } catch (Exception ignored) {}
        }
        lastError = "Impossibile aprire il microfono (in uso da un'altra app?)";
        return null;
    }

    private void loop(AudioRecord rec, Listener listener) {
        AcousticAnalyzer an = new AcousticAnalyzer();
        short[] window = new short[AcousticAnalyzer.FFT_SIZE];
        short[] hop = new short[AcousticAnalyzer.HOP];
        int filled = 0;
        try {
            rec.startRecording();
            while (running) {
                int got = 0;
                while (got < hop.length && running) {
                    int n = rec.read(hop, got, hop.length - got);
                    if (n < 0) throw new IllegalStateException("errore lettura microfono " + n);
                    got += n;
                }
                if (!running) break;
                System.arraycopy(window, AcousticAnalyzer.HOP, window, 0, window.length - AcousticAnalyzer.HOP);
                System.arraycopy(hop, 0, window, window.length - AcousticAnalyzer.HOP, AcousticAnalyzer.HOP);
                filled = Math.min(window.length, filled + AcousticAnalyzer.HOP);
                if (filled < window.length) continue;
                final AcousticAnalyzer.Result r = an.analyze(window);
                SkyState.get().setAcoustic(r.score, r.f0);
                main.post(() -> { if (running) listener.onResult(r); });
            }
        } catch (Exception e) {
            lastError = "Microfono: " + e.getMessage();
        } finally {
            try { rec.stop(); } catch (Exception ignored) {}
            rec.release();
            running = false;
        }
    }

    public void stop() {
        running = false;
        Thread t = thread;
        thread = null;
        if (t != null) {
            try { t.join(400); } catch (InterruptedException ignored) {}
        }
        SkyState.get().setAcoustic(0f, 0f);
    }
}
"""

SKY_DRONE_TRACK = r"""package com.offlinegps.map.sky;

import java.util.ArrayDeque;
import java.util.Locale;

/** Un drone ricevuto via Remote ID: unisce i vari messaggi (ID, posizione, operatore...). */
public final class DroneTrack {
    public static final int SRC_BLE = 1, SRC_WIFI = 2, SRC_DEMO = 4;
    private static final int TRAIL_MAX = 60;

    public final String key;
    public String uasId = "", operatorId = "", selfId = "";
    public int idType, uaType, status, sources, rssi = -127;
    public int category = -1, classEU = -1;
    public double lat = Double.NaN, lon = Double.NaN, opLat = Double.NaN, opLon = Double.NaN;
    public float altGeo = Float.NaN, altBaro = Float.NaN, height = Float.NaN;
    public float speed = Float.NaN, direction = Float.NaN, vspeed = Float.NaN;
    public long firstSeen, lastSeen, lastLocation;
    public int messages;
    public boolean simulated;
    /** Ultime posizioni: {lat, lon}. */
    public final ArrayDeque<double[]> trail = new ArrayDeque<>();

    public DroneTrack(String key, long now) {
        this.key = key;
        firstSeen = lastSeen = now;
    }

    public synchronized void apply(RemoteIdParser.Message m, int src, int rssi, long now) {
        messages++;
        sources |= src;
        lastSeen = now;
        if (rssi > -127) this.rssi = rssi;
        switch (m.type) {
            case RemoteIdParser.TYPE_BASIC_ID:
                if (!m.uasId.isEmpty()) uasId = m.uasId;
                idType = m.idType;
                if (m.uaType != 0) uaType = m.uaType;
                break;
            case RemoteIdParser.TYPE_LOCATION:
                status = m.status;
                if (!Float.isNaN(m.speed)) speed = m.speed;
                if (!Float.isNaN(m.direction)) direction = m.direction;
                if (!Float.isNaN(m.vspeed)) vspeed = m.vspeed;
                if (!Float.isNaN(m.altGeo)) altGeo = m.altGeo;
                if (!Float.isNaN(m.altBaro)) altBaro = m.altBaro;
                if (!Float.isNaN(m.height)) height = m.height;
                if (validLatLon(m.lat, m.lon)) {
                    lat = m.lat; lon = m.lon; lastLocation = now;
                    double[] last = trail.peekLast();
                    if (last == null || distance(last[0], last[1], lat, lon) > 1.5) {
                        trail.addLast(new double[]{lat, lon});
                        while (trail.size() > TRAIL_MAX) trail.removeFirst();
                    }
                }
                break;
            case RemoteIdParser.TYPE_SELF_ID:
                if (!m.text.isEmpty()) selfId = m.text;
                break;
            case RemoteIdParser.TYPE_SYSTEM:
                if (validLatLon(m.opLat, m.opLon)) { opLat = m.opLat; opLon = m.opLon; }
                if (m.category >= 0) category = m.category;
                if (m.classEU >= 0) classEU = m.classEU;
                break;
            case RemoteIdParser.TYPE_OPERATOR_ID:
                if (!m.operatorId.isEmpty()) operatorId = m.operatorId;
                break;
            default:
                break;
        }
    }

    /** Copia i dati di un altro tracciato (stesso drone visto con un MAC diverso). */
    public synchronized void absorb(DroneTrack o) {
        synchronized (o) {
            if (uasId.isEmpty()) uasId = o.uasId;
            if (operatorId.isEmpty()) operatorId = o.operatorId;
            if (selfId.isEmpty()) selfId = o.selfId;
            if (uaType == 0) uaType = o.uaType;
            if (category < 0) category = o.category;
            if (classEU < 0) classEU = o.classEU;
            if (o.lastLocation > lastLocation && validLatLon(o.lat, o.lon)) {
                lat = o.lat; lon = o.lon; lastLocation = o.lastLocation;
                altGeo = o.altGeo; altBaro = o.altBaro; height = o.height;
                speed = o.speed; direction = o.direction; vspeed = o.vspeed; status = o.status;
            }
            if (Double.isNaN(opLat)) { opLat = o.opLat; opLon = o.opLon; }
            if (trail.isEmpty()) trail.addAll(o.trail);
            sources |= o.sources;
            messages += o.messages;
            firstSeen = Math.min(firstSeen, o.firstSeen);
            lastSeen = Math.max(lastSeen, o.lastSeen);
            if (o.rssi > rssi) rssi = o.rssi;
            simulated |= o.simulated;
        }
    }

    public boolean hasPosition() { return validLatLon(lat, lon); }
    public boolean hasOperator() { return validLatLon(opLat, opLon); }

    public String title() {
        if (!uasId.isEmpty()) return uasId;
        return "Drone senza ID (" + key.substring(Math.max(0, key.length() - 5)) + ")";
    }

    public String typeLabel() {
        String t = RemoteIdParser.uaTypeName(uaType);
        String c = RemoteIdParser.classLabel(category, classEU);
        return c.isEmpty() ? t : t + " · " + c;
    }

    /** Quota migliore disponibile per la visualizzazione (altezza dal suolo se c'e'). */
    public float displayAltitude() {
        if (!Float.isNaN(height)) return height;
        if (!Float.isNaN(altGeo)) return altGeo;
        return altBaro;
    }

    public String sourceLabel() {
        StringBuilder sb = new StringBuilder();
        if ((sources & SRC_BLE) != 0) sb.append("Bluetooth");
        if ((sources & SRC_WIFI) != 0) sb.append(sb.length() > 0 ? " + " : "").append("Wi-Fi");
        if ((sources & SRC_DEMO) != 0) sb.append(sb.length() > 0 ? " + " : "").append("SIMULAZIONE");
        return sb.toString();
    }

    public static boolean validLatLon(double la, double lo) {
        return !Double.isNaN(la) && !Double.isNaN(lo) && Math.abs(la) <= 90 && Math.abs(lo) <= 180
            && !(la == 0 && lo == 0);
    }

    /** Distanza in metri (haversine). */
    public static double distance(double la1, double lo1, double la2, double lo2) {
        double r = 6371000.0, p1 = Math.toRadians(la1), p2 = Math.toRadians(la2);
        double dp = p2 - p1, dl = Math.toRadians(lo2 - lo1);
        double a = Math.sin(dp / 2) * Math.sin(dp / 2) + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
        return 2 * r * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    /** Direzione iniziale da 1 a 2 in gradi (0 = nord, senso orario). */
    public static double bearing(double la1, double lo1, double la2, double lo2) {
        double p1 = Math.toRadians(la1), p2 = Math.toRadians(la2), dl = Math.toRadians(lo2 - lo1);
        double y = Math.sin(dl) * Math.cos(p2);
        double x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
        return (Math.toDegrees(Math.atan2(y, x)) + 360) % 360;
    }

    public static String formatDistance(double m) {
        if (Double.isNaN(m)) return "--";
        return m < 1000 ? String.format(Locale.ITALY, "%.0f m", m) : String.format(Locale.ITALY, "%.2f km", m / 1000);
    }

    public static String cardinal(double deg) {
        String[] c = {"N", "NE", "E", "SE", "S", "SO", "O", "NO"};
        return c[(int) Math.round(((deg % 360) + 360) % 360 / 45.0) % 8];
    }
}
"""

SKY_STATE = r"""package com.offlinegps.map.sky;

import android.os.Handler;
import android.os.Looper;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Stato condiviso della SENTINELLA CIELO: i droni ricevuti via Remote ID,
 * l'ultimo punteggio acustico e la posizione dell'utente. Gli scanner
 * scrivono da qualsiasi thread; gli ascoltatori vengono avvisati sul
 * thread principale (al massimo una notifica per frame).
 */
public final class SkyState {
    public interface Listener { void onSkyChanged(); }

    private static final SkyState INSTANCE = new SkyState();
    public static SkyState get() { return INSTANCE; }

    private final Map<String, DroneTrack> tracks = new LinkedHashMap<>();
    /** indirizzo radio (MAC/BSSID) -> chiave del tracciato. */
    private final Map<String, String> alias = new HashMap<>();
    private final CopyOnWriteArrayList<Listener> listeners = new CopyOnWriteArrayList<>();
    private final Handler main = new Handler(Looper.getMainLooper());
    private boolean notifyPending;

    public volatile float acousticScore;
    public volatile float acousticF0;
    public volatile long acousticAt;
    public volatile double userLat = Double.NaN, userLon = Double.NaN;
    public volatile float heading = Float.NaN;
    public volatile long packets;

    private SkyState() {}

    // ------------------------------------------------------------ ingresso dati
    /** Messaggi Remote ID ricevuti da un indirizzo radio. */
    public void ingest(String radio, List<RemoteIdParser.Message> msgs, int src, int rssi) {
        if (msgs == null || msgs.isEmpty()) return;
        long now = System.currentTimeMillis();
        synchronized (this) {
            packets++;
            String key = alias.get(radio);
            if (key == null) key = "R:" + radio;
            DroneTrack t = tracks.get(key);
            if (t == null) {
                t = new DroneTrack(key, now);
                t.simulated = (src & DroneTrack.SRC_DEMO) != 0;
                tracks.put(key, t);
                alias.put(radio, key);
            }
            for (RemoteIdParser.Message m : msgs) {
                t.apply(m, src, rssi, now);
                // appena si conosce il numero di serie il tracciato prende quell'identita':
                // lo stesso drone che cambia MAC o trasmette su BT e Wi-Fi resta uno solo
                if (m.type == RemoteIdParser.TYPE_BASIC_ID && !m.uasId.isEmpty()) {
                    String idKey = "ID:" + m.uasId;
                    if (!idKey.equals(t.key)) {
                        DroneTrack target = tracks.get(idKey);
                        if (target == null) {
                            target = new DroneTrack(idKey, t.firstSeen);
                            tracks.put(idKey, target);
                        }
                        target.absorb(t);
                        tracks.remove(t.key);
                        for (Map.Entry<String, String> e : alias.entrySet())
                            if (e.getValue().equals(t.key)) e.setValue(idKey);
                        alias.put(radio, idKey);
                        t = target;
                    }
                }
            }
        }
        changed();
    }

    public void setAcoustic(float score, float f0) {
        acousticScore = score;
        acousticF0 = f0;
        acousticAt = System.currentTimeMillis();
        changed();
    }

    public void setUser(double lat, double lon) {
        userLat = lat; userLon = lon;
    }

    // ------------------------------------------------------------ lettura
    /** Copia dei tracciati: prima i piu' vicini con posizione, poi gli altri per recenza. */
    public synchronized List<DroneTrack> snapshot() {
        List<DroneTrack> out = new ArrayList<>(tracks.values());
        final double ula = userLat, ulo = userLon;
        final boolean hasUser = DroneTrack.validLatLon(ula, ulo);
        Collections.sort(out, (a, b) -> {
            if (hasUser && a.hasPosition() && b.hasPosition())
                return Double.compare(DroneTrack.distance(ula, ulo, a.lat, a.lon),
                                      DroneTrack.distance(ula, ulo, b.lat, b.lon));
            if (a.hasPosition() != b.hasPosition()) return a.hasPosition() ? -1 : 1;
            return Long.compare(b.lastSeen, a.lastSeen);
        });
        return out;
    }

    public synchronized int count() { return tracks.size(); }

    public synchronized int countReal() {
        int n = 0;
        for (DroneTrack t : tracks.values()) if (!t.simulated) n++;
        return n;
    }

    /** Elimina i droni non piu' sentiti da maxAgeMs. Ritorna quanti ne ha tolti. */
    public int prune(long maxAgeMs) {
        long now = System.currentTimeMillis();
        int removed = 0;
        synchronized (this) {
            Iterator<Map.Entry<String, DroneTrack>> it = tracks.entrySet().iterator();
            while (it.hasNext()) {
                DroneTrack t = it.next().getValue();
                if (now - t.lastSeen > maxAgeMs) { it.remove(); removed++; }
            }
            if (removed > 0) alias.values().retainAll(tracks.keySet());
        }
        if (removed > 0) changed();
        return removed;
    }

    public synchronized void clear() {
        tracks.clear();
        alias.clear();
        main.post(this::fire);
    }

    // ------------------------------------------------------------ ascoltatori
    public void addListener(Listener l) { listeners.addIfAbsent(l); }
    public void removeListener(Listener l) { listeners.remove(l); }

    private void changed() {
        synchronized (this) {
            if (notifyPending) return;
            notifyPending = true;
        }
        main.post(this::fire);
    }

    private void fire() {
        synchronized (this) { notifyPending = false; }
        for (Listener l : listeners) {
            try { l.onSkyChanged(); } catch (Exception ignored) {}
        }
    }

    // ------------------------------------------------------------ simulazione
    private Runnable demoTick;
    private long demoStart;

    public boolean isDemo() { return demoTick != null; }

    /**
     * Modalita' DEMO: tre droni immaginari attorno alla posizione indicata.
     * I loro messaggi vengono CODIFICATI in formato Remote ID e poi decodificati
     * dallo stesso parser usato per i segnali veri, quindi la demo prova anche
     * tutta la catena di ricezione.
     */
    public void startDemo(double lat, double lon) {
        stopDemo();
        final double cLat = DroneTrack.validLatLon(lat, lon) ? lat : 41.8902;
        final double cLon = DroneTrack.validLatLon(lat, lon) ? lon : 12.4922;
        demoStart = System.currentTimeMillis();
        demoTick = new Runnable() {
            @Override public void run() {
                if (demoTick != this) return;
                double t = (System.currentTimeMillis() - demoStart) / 1000.0;
                emitDemo("SIM-DEMO-0001-MULTI", 2, 1, 2, "DEMO Rilievo tetti", "DEMO-OP-ALFA",
                    cLat, cLon, 260, t, 0.04, 42, 0.12, "B:DE:M0:00:00:01");
                emitDemo("SIM-DEMO-0002-WING", 1, 2, 3, "DEMO Ispezione linea", "DEMO-OP-BRAVO",
                    cLat + 0.004, cLon - 0.006, 650, t, -0.04, 95, 0.30, "W:DE:M0:00:00:02");
                // il terzo trasmette solo posizione (nessun ID): come certi moduli economici
                double a = t * 0.07;
                double la = cLat - 0.0022 + 0.0007 * Math.sin(a * 3), lo = cLon + 0.0035 + 0.0009 * Math.cos(a * 2);
                ingestEncoded("B:DE:M0:00:00:03", DroneTrack.SRC_DEMO, -88,
                    RemoteIdParser.encodeLocation(RemoteIdParser.STATUS_AIRBORNE, (float) ((a * 57) % 360), 4.5f, 0.5f,
                        la, lo, 180f, 35f + 10f * (float) Math.sin(a)));
                main.postDelayed(this, 1000);
            }
        };
        main.post(demoTick);
    }

    private void emitDemo(String id, int uaType, int category, int classEU, String self, String op,
                          double cLat, double cLon, double radiusM, double t, double rate,
                          float height, double wobble, String radio) {
        double angle = t * rate;
        double dLat = radiusM / 111320.0, dLon = radiusM / (111320.0 * Math.cos(Math.toRadians(cLat)));
        double la = cLat + dLat * Math.cos(angle) * (1 + wobble * Math.sin(angle * 3));
        double lo = cLon + dLon * Math.sin(angle);
        double la2 = cLat + dLat * Math.cos(angle + 0.01) * (1 + wobble * Math.sin((angle + 0.01) * 3));
        double lo2 = cLon + dLon * Math.sin(angle + 0.01);
        float dir = (float) DroneTrack.bearing(la, lo, la2, lo2);
        if (rate < 0) dir = (dir + 180) % 360;
        float speed = (float) Math.abs(radiusM * rate);
        byte[] pack = RemoteIdParser.encodePack(
            RemoteIdParser.encodeBasicId(1, uaType, id),
            RemoteIdParser.encodeLocation(RemoteIdParser.STATUS_AIRBORNE, dir, speed, 0f,
                la, lo, 70f + height, height),
            RemoteIdParser.encodeSelfId(self),
            RemoteIdParser.encodeSystem(cLat + dLat * 0.15, cLon - dLon * 0.2, category, classEU),
            RemoteIdParser.encodeOperatorId(op));
        ingestEncoded(radio, DroneTrack.SRC_DEMO, -60 - (int) (radiusM / 25), pack);
    }

    private void ingestEncoded(String radio, int src, int rssi, byte[] data) {
        ingest(radio, RemoteIdParser.parse(data, 0), src, rssi);
    }

    public void stopDemo() {
        if (demoTick == null) return;
        main.removeCallbacks(demoTick);
        demoTick = null;
        synchronized (this) {
            Iterator<Map.Entry<String, DroneTrack>> it = tracks.entrySet().iterator();
            while (it.hasNext()) if (it.next().getValue().simulated) it.remove();
            alias.values().retainAll(tracks.keySet());
        }
        changed();
    }
}
"""

SKY_REMOTE_ID_SCANNER = r"""package com.offlinegps.map.sky;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanFilter;
import android.bluetooth.le.ScanRecord;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelUuid;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;

/**
 * Ricevitore PASSIVO di Remote ID: ascolta gli annunci che i droni
 * trasmettono per legge (Reg. UE 2019/945, ASTM F3411) e non trasmette nulla.
 *  - Bluetooth: annunci BLE con service data UUID 0xFFFA (legacy 4.x e,
 *    se il telefono lo supporta, extended/long range 5.x);
 *  - Wi-Fi Beacon: elemento "vendor specific" con OUI FA:0B:BC tipo 0x0D
 *    (lettura degli elementi solo da Android 11).
 * Il Wi-Fi NAN (Aware) non e' supportato.
 */
public final class RemoteIdScanner {
    public static final ParcelUuid RID_UUID = ParcelUuid.fromString("0000fffa-0000-1000-8000-00805f9b34fb");
    private static final int APP_CODE = 0x0D;
    private static final long WIFI_PERIOD_MS = 30_000;   // Android limita a 4 scansioni ogni 2 minuti

    private final Context ctx;
    private final Handler main = new Handler(Looper.getMainLooper());
    private BluetoothLeScanner ble;
    private ScanCallback bleCallback;
    private WifiManager wifi;
    private BroadcastReceiver wifiReceiver;
    private Runnable wifiTick;
    public volatile int blePackets, wifiPackets, bleErrors;
    public volatile String lastError = "";
    private boolean forceLegacy;

    public RemoteIdScanner(Context c) { ctx = c.getApplicationContext(); }

    // ------------------------------------------------------------ permessi
    /** Indispensabili per il Bluetooth (il Wi-Fi "dispositivi vicini" e' facoltativo). */
    public static String[] requiredPermissions() {
        return Build.VERSION.SDK_INT >= 31
            ? new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.BLUETOOTH_SCAN}
            : new String[]{Manifest.permission.ACCESS_FINE_LOCATION};
    }

    /** Tutti quelli da chiedere all'utente. */
    public static String[] neededPermissions() {
        List<String> p = new ArrayList<>();
        p.add(Manifest.permission.ACCESS_FINE_LOCATION);
        if (Build.VERSION.SDK_INT >= 31) p.add(Manifest.permission.BLUETOOTH_SCAN);
        if (Build.VERSION.SDK_INT >= 33) p.add(Manifest.permission.NEARBY_WIFI_DEVICES);
        return p.toArray(new String[0]);
    }

    private boolean granted(String perm) {
        return ctx.checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED;
    }

    public boolean canScanBle() {
        return Build.VERSION.SDK_INT >= 31 ? granted(Manifest.permission.BLUETOOTH_SCAN)
                                           : granted(Manifest.permission.ACCESS_FINE_LOCATION);
    }

    public boolean canScanWifi() { return granted(Manifest.permission.ACCESS_FINE_LOCATION); }

    public static boolean wifiBeaconSupported() { return Build.VERSION.SDK_INT >= 30; }

    // ------------------------------------------------------------ Bluetooth
    public boolean isBleRunning() { return bleCallback != null; }

    /** Avvia la scansione BLE. Ritorna false (con lastError) se non e' possibile. */
    public boolean startBle() {
        if (bleCallback != null) return true;
        try {
            BluetoothManager bm = (BluetoothManager) ctx.getSystemService(Context.BLUETOOTH_SERVICE);
            BluetoothAdapter ad = bm != null ? bm.getAdapter() : null;
            if (ad == null) { lastError = "Questo telefono non ha il Bluetooth"; return false; }
            if (!ad.isEnabled()) { lastError = "Accendi il Bluetooth per ricevere il Remote ID"; return false; }
            if (!canScanBle()) { lastError = "Permesso Bluetooth/posizione mancante"; return false; }
            ble = ad.getBluetoothLeScanner();
            if (ble == null) { lastError = "Scanner Bluetooth LE non disponibile"; return false; }

            ScanSettings.Builder sb = new ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY);
            // Remote ID "long range" usa annunci estesi su PHY Coded (Bluetooth 5)
            if (!forceLegacy && ad.isLeExtendedAdvertisingSupported()) {
                sb.setLegacy(false);
                sb.setPhy(ScanSettings.PHY_LE_ALL_SUPPORTED);
            }
            List<ScanFilter> filters = new ArrayList<>();
            filters.add(new ScanFilter.Builder()
                .setServiceData(RID_UUID, new byte[]{(byte) APP_CODE}, new byte[]{(byte) 0xFF})
                .build());
            bleCallback = new ScanCallback() {
                @Override public void onScanResult(int type, ScanResult r) { handleBle(r); }
                @Override public void onBatchScanResults(List<ScanResult> rs) { for (ScanResult r : rs) handleBle(r); }
                @Override public void onScanFailed(int code) {
                    bleErrors++;
                    bleCallback = null;
                    if (code == SCAN_FAILED_FEATURE_UNSUPPORTED && !forceLegacy) {
                        // il chip non regge la scansione estesa: riprova in modalita' classica
                        forceLegacy = true;
                        main.post(RemoteIdScanner.this::startBle);
                        return;
                    }
                    lastError = "Scansione Bluetooth fallita (codice " + code + ")";
                }
            };
            ble.startScan(filters, sb.build(), bleCallback);
            lastError = "";
            return true;
        } catch (SecurityException e) {
            bleCallback = null;
            lastError = "Permesso Bluetooth negato";
            return false;
        } catch (Exception e) {
            bleCallback = null;
            lastError = "Bluetooth: " + e.getMessage();
            return false;
        }
    }

    private void handleBle(ScanResult r) {
        try {
            ScanRecord rec = r.getScanRecord();
            if (rec == null) return;
            byte[] sd = rec.getServiceData(RID_UUID);
            // service data = [0x0D app code][contatore][messaggio o message pack]
            if (sd == null || sd.length < 3 || (sd[0] & 0xFF) != APP_CODE) return;
            List<RemoteIdParser.Message> msgs = RemoteIdParser.parse(sd, 2);
            if (msgs.isEmpty()) return;
            blePackets++;
            SkyState.get().ingest("B:" + r.getDevice().getAddress(), msgs, DroneTrack.SRC_BLE, r.getRssi());
        } catch (Exception ignored) {}
    }

    public void stopBle() {
        if (ble != null && bleCallback != null) {
            try { ble.stopScan(bleCallback); } catch (Exception ignored) {}
        }
        bleCallback = null;
    }

    // ------------------------------------------------------------ Wi-Fi Beacon
    public boolean isWifiRunning() { return wifiReceiver != null; }

    public boolean startWifi() {
        if (wifiReceiver != null) return true;
        if (!wifiBeaconSupported()) { lastError = "Wi-Fi Beacon Remote ID richiede Android 11+"; return false; }
        if (!canScanWifi()) { lastError = "Permesso posizione mancante per il Wi-Fi"; return false; }
        wifi = (WifiManager) ctx.getSystemService(Context.WIFI_SERVICE);
        if (wifi == null) { lastError = "Wi-Fi non disponibile"; return false; }
        wifiReceiver = new BroadcastReceiver() {
            @Override public void onReceive(Context c, Intent i) { handleWifi(); }
        };
        IntentFilter f = new IntentFilter(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION);
        if (Build.VERSION.SDK_INT >= 33) ctx.registerReceiver(wifiReceiver, f, Context.RECEIVER_NOT_EXPORTED);
        else ctx.registerReceiver(wifiReceiver, f);
        wifiTick = new Runnable() {
            @Override public void run() {
                if (wifiTick != this) return;
                try { wifi.startScan(); } catch (Exception ignored) {}
                main.postDelayed(this, WIFI_PERIOD_MS);
            }
        };
        main.post(wifiTick);
        handleWifi();
        return true;
    }

    private void handleWifi() {
        if (wifi == null || Build.VERSION.SDK_INT < 30) return;
        try {
            for (android.net.wifi.ScanResult r : wifi.getScanResults()) {
                for (android.net.wifi.ScanResult.InformationElement ie : r.getInformationElements()) {
                    if (ie.getId() != 221) continue;
                    ByteBuffer bb = ie.getBytes();
                    byte[] b = new byte[bb.remaining()];
                    bb.duplicate().get(b);
                    // [FA 0B BC][0x0D][contatore][message pack]
                    if (b.length < 5 + 3 || (b[0] & 0xFF) != 0xFA || (b[1] & 0xFF) != 0x0B
                        || (b[2] & 0xFF) != 0xBC || (b[3] & 0xFF) != APP_CODE) continue;
                    List<RemoteIdParser.Message> msgs = RemoteIdParser.parse(b, 5);
                    if (msgs.isEmpty()) continue;
                    wifiPackets++;
                    SkyState.get().ingest("W:" + r.BSSID, msgs, DroneTrack.SRC_WIFI, r.level);
                }
            }
        } catch (SecurityException e) {
            lastError = "Permesso Wi-Fi negato";
        } catch (Exception ignored) {}
    }

    public void stopWifi() {
        if (wifiTick != null) main.removeCallbacks(wifiTick);
        wifiTick = null;
        if (wifiReceiver != null) {
            try { ctx.unregisterReceiver(wifiReceiver); } catch (Exception ignored) {}
        }
        wifiReceiver = null;
    }

    public void stopAll() { stopBle(); stopWifi(); }
}
"""

SKY_SPOT_STORE = r"""package com.offlinegps.map.sky;

import android.content.Context;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Diario locale degli avvistamenti (SkySpot). Resta sul telefono.
 * La posizione viene ARROTONDATA a una griglia di ~1 km prima di essere
 * salvata: chi condivide una segnalazione non rivela dove si trova di preciso.
 */
public final class SkySpotStore {
    public static final String[] KINDS = {"Visto", "Sentito", "Luci nel cielo", "Visto e sentito"};
    public static final String[] HEIGHTS = {"Non so", "Bassa (sotto 50 m)", "Media (50-120 m)", "Alta (oltre 120 m)"};
    public static final String[] DURATIONS = {"Pochi secondi", "Meno di 1 minuto", "1-5 minuti", "Oltre 5 minuti"};
    /** Celle per grado della griglia di anonimizzazione: 100 = passo 0,01 gradi = ~1,1 km. */
    public static final double CELLS_PER_DEGREE = 100.0;

    public static final class Report {
        public long time;
        public double lat = Double.NaN, lon = Double.NaN;   // gia' arrotondate
        public int kind, height, duration, count = 1;
        public String direction = "", notes = "", remoteId = "";
        public float acoustic = -1f;

        JSONObject toJson() throws Exception {
            JSONObject o = new JSONObject();
            o.put("t", time); o.put("k", kind); o.put("h", height); o.put("d", duration); o.put("n", count);
            o.put("dir", direction); o.put("note", notes); o.put("rid", remoteId); o.put("ac", acoustic);
            if (!Double.isNaN(lat)) { o.put("lat", lat); o.put("lon", lon); }
            return o;
        }

        static Report fromJson(JSONObject o) {
            Report r = new Report();
            r.time = o.optLong("t"); r.kind = o.optInt("k"); r.height = o.optInt("h");
            r.duration = o.optInt("d"); r.count = o.optInt("n", 1);
            r.direction = o.optString("dir"); r.notes = o.optString("note"); r.remoteId = o.optString("rid");
            r.acoustic = (float) o.optDouble("ac", -1);
            if (o.has("lat")) { r.lat = o.optDouble("lat"); r.lon = o.optDouble("lon"); }
            return r;
        }

        public String when() {
            return new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.ITALY).format(new Date(time));
        }

        public String where() {
            if (Double.isNaN(lat)) return "posizione non disponibile";
            return String.format(Locale.US, "%.2f, %.2f (~1 km)", lat, lon);
        }

        public String summary() {
            StringBuilder sb = new StringBuilder();
            sb.append(safe(KINDS, kind));
            if (count > 1) sb.append(" · ").append(count).append(" oggetti");
            if (!direction.isEmpty()) sb.append(" · direzione ").append(direction);
            sb.append(" · ").append(safe(HEIGHTS, height));
            return sb.toString();
        }

        /** Testo da condividere: niente dati personali, posizione approssimata. */
        public String shareText() {
            StringBuilder sb = new StringBuilder();
            sb.append("SEGNALAZIONE AVVISTAMENTO (SkySpot / OfflineGPS 3D)\n");
            sb.append("Quando: ").append(when()).append('\n');
            sb.append("Zona: ").append(where()).append('\n');
            sb.append("Tipo: ").append(safe(KINDS, kind)).append('\n');
            if (count > 1) sb.append("Numero: ").append(count).append('\n');
            if (!direction.isEmpty()) sb.append("Direzione: ").append(direction).append('\n');
            sb.append("Altezza stimata: ").append(safe(HEIGHTS, height)).append('\n');
            sb.append("Durata: ").append(safe(DURATIONS, duration)).append('\n');
            if (!remoteId.isEmpty()) sb.append("Remote ID ricevuto: ").append(remoteId).append('\n');
            if (acoustic >= 0) sb.append(String.format(Locale.ITALY, "Indice acustico: %.0f%%%n", acoustic * 100));
            if (!notes.isEmpty()) sb.append("Note: ").append(notes).append('\n');
            sb.append("\nNON sostituisce il 112: in caso di pericolo chiama subito il 112.");
            return sb.toString();
        }
    }

    private static String safe(String[] a, int i) { return a[Math.max(0, Math.min(a.length - 1, i))]; }

    /** Arrotonda alla griglia di ~1 km (il centro della cella). */
    public static double anonymize(double v) {
        if (Double.isNaN(v)) return v;
        return Math.round(v * CELLS_PER_DEGREE) / CELLS_PER_DEGREE;
    }

    private final File file;

    public SkySpotStore(Context c) { file = new File(c.getFilesDir(), "skyspot_reports.json"); }

    public synchronized List<Report> list() {
        List<Report> out = new ArrayList<>();
        try {
            if (!file.exists()) return out;
            byte[] b = new byte[(int) file.length()];
            try (FileInputStream in = new FileInputStream(file)) {
                int off = 0;
                while (off < b.length) {
                    int n = in.read(b, off, b.length - off);
                    if (n < 0) break;
                    off += n;
                }
            }
            JSONArray a = new JSONArray(new String(b, StandardCharsets.UTF_8));
            for (int i = 0; i < a.length(); i++) out.add(Report.fromJson(a.getJSONObject(i)));
        } catch (Exception ignored) {}
        return out;
    }

    public synchronized void add(Report r) {
        r.lat = anonymize(r.lat);
        r.lon = anonymize(r.lon);
        List<Report> all = list();
        all.add(0, r);
        while (all.size() > 200) all.remove(all.size() - 1);
        save(all);
    }

    public synchronized void delete(int index) {
        List<Report> all = list();
        if (index >= 0 && index < all.size()) { all.remove(index); save(all); }
    }

    private void save(List<Report> all) {
        try {
            JSONArray a = new JSONArray();
            for (Report r : all) a.put(r.toJson());
            File tmp = new File(file.getPath() + ".tmp");
            try (FileOutputStream out = new FileOutputStream(tmp)) {
                out.write(a.toString().getBytes(StandardCharsets.UTF_8));
            }
            if (!tmp.renameTo(file)) {
                try (FileOutputStream out = new FileOutputStream(file)) {
                    out.write(a.toString().getBytes(StandardCharsets.UTF_8));
                }
                //noinspection ResultOfMethodCallIgnored
                tmp.delete();
            }
        } catch (Exception ignored) {}
    }
}
"""

SKY_HEADING_SENSOR = r"""package com.offlinegps.map.sky;

import android.content.Context;
import android.hardware.GeomagneticField;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;

/**
 * Direzione verso cui punta il telefono (gradi dal nord VERO, con la
 * declinazione magnetica del luogo). Funziona sia col telefono in piano sia
 * tenuto in verticale davanti a se' (come per inquadrare il cielo).
 */
public final class HeadingSensor implements SensorEventListener {
    public interface Listener { void onHeading(float deg); }

    private final SensorManager sm;
    private final Sensor rotation;
    private Listener listener;
    private float declination;
    private float smooth = Float.NaN;
    private long lastPost;
    private final float[] rot = new float[9], remap = new float[9], ori = new float[3];

    public HeadingSensor(Context c) {
        sm = (SensorManager) c.getSystemService(Context.SENSOR_SERVICE);
        rotation = sm != null ? sm.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR) : null;
    }

    public boolean available() { return rotation != null; }

    public boolean start(Listener l) {
        listener = l;
        if (rotation == null) return false;
        return sm.registerListener(this, rotation, SensorManager.SENSOR_DELAY_UI);
    }

    public void stop() {
        if (sm != null) sm.unregisterListener(this);
        listener = null;
    }

    public void setLocation(double lat, double lon, double alt) {
        try {
            declination = new GeomagneticField((float) lat, (float) lon, (float) alt, System.currentTimeMillis()).getDeclination();
        } catch (Exception ignored) {}
    }

    public float current() { return smooth; }

    @Override public void onSensorChanged(SensorEvent e) {
        SensorManager.getRotationMatrixFromVector(rot, e.values);
        // telefono in verticale: conta la direzione in cui guarda il retro (la fotocamera)
        boolean upright = Math.abs(rot[8]) < 0.7f;
        if (upright) {
            SensorManager.remapCoordinateSystem(rot, SensorManager.AXIS_X, SensorManager.AXIS_Z, remap);
            SensorManager.getOrientation(remap, ori);
        } else {
            SensorManager.getOrientation(rot, ori);
        }
        float az = (float) ((Math.toDegrees(ori[0]) + declination + 360) % 360);
        if (Float.isNaN(smooth)) smooth = az;
        else {
            float d = ((az - smooth + 540) % 360) - 180;
            smooth = (smooth + d * 0.2f + 360) % 360;
        }
        long now = System.currentTimeMillis();
        if (listener != null && now - lastPost > 60) {
            lastPost = now;
            listener.onHeading(smooth);
        }
    }

    @Override public void onAccuracyChanged(Sensor s, int a) {}

    public static String cardinal(float deg) {
        String[] c = {"Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ovest", "Ovest", "Nord-Ovest"};
        return c[(int) Math.round(((deg % 360) + 360) % 360 / 45.0) % 8];
    }
}
"""

UI_FX = r"""package com.offlinegps.map.ui;

import android.animation.ObjectAnimator;
import android.animation.PropertyValuesHolder;
import android.animation.StateListAnimator;
import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.DecelerateInterpolator;
import android.view.animation.OvershootInterpolator;
import android.widget.AbsListView;
import android.widget.AbsSeekBar;
import android.widget.EditText;
import android.widget.ScrollView;
import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;

/**
 * Effetti "vivi" per TUTTA l'app, senza toccare le singole schermate:
 *  - ogni pulsante/scheda si comprime leggermente quando lo premi e torna
 *    al suo posto con un piccolo rimbalzo (molla);
 *  - all'apertura di una schermata a scorrimento gli elementi entrano in
 *    sequenza dal basso, uno dopo l'altro.
 * Le schermate con mappa o fotocamera non vengono toccate.
 */
public final class UiFx {
    /** Radici gia' decorate (deboli: non trattengono le Activity chiuse). */
    private static final Set<View> DONE = Collections.newSetFromMap(new WeakHashMap<View, Boolean>());
    private UiFx() {}

    public static void install(Application app) {
        app.registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            @Override public void onActivityResumed(Activity a) {
                View content = a.findViewById(android.R.id.content);
                if (!(content instanceof ViewGroup) || ((ViewGroup) content).getChildCount() == 0) return;
                View root = ((ViewGroup) content).getChildAt(0);
                if (!DONE.add(root)) return;
                springTree(root, 0);
                entrance(root);
            }
            @Override public void onActivityCreated(Activity a, Bundle b) {}
            @Override public void onActivityStarted(Activity a) {}
            @Override public void onActivityPaused(Activity a) {}
            @Override public void onActivityStopped(Activity a) {}
            @Override public void onActivitySaveInstanceState(Activity a, Bundle b) {}
            @Override public void onActivityDestroyed(Activity a) {}
        });
    }

    /** Molla alla pressione su tutti i controlli cliccabili dell'albero. */
    public static void springTree(View v, int depth) {
        if (depth > 24 || skip(v)) return;
        if (v.isClickable() && !(v instanceof EditText) && !(v instanceof AbsSeekBar)
                && !(v instanceof SkyRadarView)) addSpring(v);
        if (v instanceof ViewGroup && !(v instanceof AbsListView)) {
            ViewGroup g = (ViewGroup) v;
            for (int i = 0; i < g.getChildCount(); i++) springTree(g.getChildAt(i), depth + 1);
        }
    }

    public static void addSpring(View v) {
        StateListAnimator s = new StateListAnimator();
        ObjectAnimator down = ObjectAnimator.ofPropertyValuesHolder((Object) null,
            PropertyValuesHolder.ofFloat("scaleX", 0.95f), PropertyValuesHolder.ofFloat("scaleY", 0.95f));
        down.setDuration(90);
        down.setInterpolator(new DecelerateInterpolator());
        ObjectAnimator up = ObjectAnimator.ofPropertyValuesHolder((Object) null,
            PropertyValuesHolder.ofFloat("scaleX", 1f), PropertyValuesHolder.ofFloat("scaleY", 1f));
        up.setDuration(340);
        up.setInterpolator(new OvershootInterpolator(3f));
        s.addState(new int[]{android.R.attr.state_pressed, android.R.attr.state_enabled}, down);
        s.addState(new int[0], up);
        v.setStateListAnimator(s);
    }

    /**
     * Ingresso a cascata dei figli della colonna di una schermata a scorrimento
     * (lo ScrollView puo' essere la radice o stare sopra uno sfondo animato).
     */
    public static void entrance(View root) {
        ScrollView sv = null;
        if (root instanceof ScrollView) sv = (ScrollView) root;
        else if (root instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) root;
            for (int i = 0; i < g.getChildCount() && sv == null; i++)
                if (g.getChildAt(i) instanceof ScrollView) sv = (ScrollView) g.getChildAt(i);
        }
        if (sv == null || sv.getChildCount() == 0 || !(sv.getChildAt(0) instanceof ViewGroup)) return;
        stagger((ViewGroup) sv.getChildAt(0));
    }

    public static void stagger(ViewGroup col) {
        float dy = 28 * col.getResources().getDisplayMetrics().density;
        int n = Math.min(col.getChildCount(), 14);
        for (int i = 0; i < n; i++) {
            View c = col.getChildAt(i);
            if (c.getVisibility() != View.VISIBLE) continue;
            c.setAlpha(0f);
            c.setTranslationY(dy);
            c.animate().alpha(1f).translationY(0f).setStartDelay(40L * i).setDuration(380)
                .setInterpolator(new DecelerateInterpolator(2f)).start();
        }
    }

    private static boolean skip(View v) {
        String n = v.getClass().getName();
        return n.startsWith("org.mapsforge") || n.startsWith("android.view.Surface")
            || n.startsWith("android.view.Texture") || n.contains("MapView");
    }
}
"""

SKY_UI = r"""package com.offlinegps.map.ui;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.offlinegps.map.R;
import java.util.ArrayList;
import java.util.List;

/** Piccoli mattoni grafici condivisi dalle schermate della Sentinella Cielo. */
public final class SkyUi {
    public static final int CHIP_OFF = 0, CHIP_ON = 1, CHIP_WARN = 2, CHIP_ALERT = 3;
    private SkyUi() {}

    public static int dp(Context c, float v) {
        return Math.round(v * c.getResources().getDisplayMetrics().density);
    }

    /** Stato di un "chip" (spento / attivo / attenzione / allarme). */
    public static void chip(TextView tv, int state, String text) {
        if (tv == null) return;
        tv.setText(text);
        switch (state) {
            case CHIP_ON:    tv.setBackgroundResource(R.drawable.bg_chip_on);    tv.setTextColor(0xFF00FF88); break;
            case CHIP_WARN:  tv.setBackgroundResource(R.drawable.bg_chip_warn);  tv.setTextColor(0xFFFFD600); break;
            case CHIP_ALERT: tv.setBackgroundResource(R.drawable.bg_chip_alert); tv.setTextColor(0xFFFF5C7A); break;
            default:         tv.setBackgroundResource(R.drawable.bg_chip_off);   tv.setTextColor(0xFF8FB3D0); break;
        }
    }

    /** Scheda "vetro" con barra colorata a sinistra e righe di testo. */
    public static LinearLayout card(Context c, int accent, String title, String... lines) {
        LinearLayout outer = new LinearLayout(c);
        outer.setOrientation(LinearLayout.HORIZONTAL);
        outer.setBackgroundResource(R.drawable.bg_tile_glass);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = dp(c, 10);
        outer.setLayoutParams(lp);
        outer.setClickable(true);
        outer.setFocusable(true);

        View bar = new View(c);
        bar.setBackgroundColor(accent);
        LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(dp(c, 4), LinearLayout.LayoutParams.MATCH_PARENT);
        blp.setMargins(dp(c, 2), dp(c, 10), 0, dp(c, 10));
        outer.addView(bar, blp);

        LinearLayout col = new LinearLayout(c);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(c, 14), dp(c, 12), dp(c, 14), dp(c, 12));
        outer.addView(col, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        TextView t = new TextView(c);
        t.setText(title);
        t.setTextColor(0xFFE8F4FD);
        t.setTextSize(15);
        t.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
        col.addView(t);
        for (String l : lines) {
            if (l == null || l.isEmpty()) continue;
            TextView tv = new TextView(c);
            tv.setText(l);
            tv.setTextColor(0xFF8FB3D0);
            tv.setTextSize(12.5f);
            tv.setPadding(0, dp(c, 3), 0, 0);
            col.addView(tv);
        }
        return outer;
    }

    /** Etichetta di sezione in maiuscoletto con linea luminosa. */
    public static TextView section(Context c, String text) {
        TextView tv = new TextView(c);
        tv.setText(text);
        tv.setTextColor(0xFF00E5FF);
        tv.setTextSize(12);
        tv.setLetterSpacing(0.18f);
        tv.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        tv.setGravity(Gravity.START);
        tv.setPadding(dp(c, 4), dp(c, 16), 0, dp(c, 8));
        return tv;
    }

    /** Chiede i permessi mancanti fra quelli indicati. Ritorna true se ci sono gia' tutti. */
    public static boolean ensurePermissions(Activity a, int req, String... perms) {
        List<String> miss = new ArrayList<>();
        for (String p : perms)
            if (a.checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) miss.add(p);
        if (miss.isEmpty()) return true;
        a.requestPermissions(miss.toArray(new String[0]), req);
        return false;
    }

    public static void share(Activity a, String subject, String text) {
        Intent i = new Intent(Intent.ACTION_SEND);
        i.setType("text/plain");
        i.putExtra(Intent.EXTRA_SUBJECT, subject);
        i.putExtra(Intent.EXTRA_TEXT, text);
        try { a.startActivity(Intent.createChooser(i, "Condividi")); } catch (Exception ignored) {}
    }
}
"""

SKY_RADAR_VIEW = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.DashPathEffect;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.SweepGradient;
import android.graphics.Typeface;
import android.os.SystemClock;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;
import com.offlinegps.map.sky.DroneTrack;
import com.offlinegps.map.sky.RemoteIdParser;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * Radar 3D della SENTINELLA CIELO: piano inclinato in prospettiva con anelli
 * di distanza, fascio rotante e droni che "galleggiano" sopra la loro
 * posizione a terra con uno stelo proporzionale alla quota.
 * Centro = la tua posizione. Tocca un drone per i dettagli.
 */
public class SkyRadarView extends View {
    public interface OnTrackTap { void onTrackTap(DroneTrack t); }

    private static final float[] RANGES = {200, 500, 1000, 2000, 5000, 10000, 25000};
    private static final int COL_CYAN = 0xFF00E5FF, COL_REAL = 0xFFFF3D71, COL_DEMO = 0xFFFFB300,
        COL_NOID = 0xFFB388FF, COL_OP = 0xFF00FF88;

    private List<DroneTrack> tracks = Collections.emptyList();
    private double uLat = Double.NaN, uLon = Double.NaN;
    private float heading = Float.NaN;
    private boolean headingUp, compact, demo, tilt3d = true;
    private float acoustic;
    private float range = 1000, shownRange = 1000;
    private static final float TILT = 50f;
    private float tiltNow = TILT;
    private float acousticPulse;
    private OnTrackTap tapListener;
    private boolean running;
    private final long t0 = SystemClock.uptimeMillis();

    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint sweep = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint disc = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint dash = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Matrix m3d = new Matrix(), shaderM = new Matrix();
    private final Path path = new Path();
    private final float[] pt = new float[2];
    private SweepGradient sweepShader;
    private RadialGradient discShader;
    private float lastCx = -1, lastR = -1;
    private final List<DroneTrack> hitTracks = new ArrayList<>();
    private final List<float[]> hitPts = new ArrayList<>();

    public SkyRadarView(Context c) { this(c, null); }
    public SkyRadarView(Context c, AttributeSet a) {
        super(c, a);
        stroke.setStyle(Paint.Style.STROKE);
        dash.setStyle(Paint.Style.STROKE);
        dash.setPathEffect(new DashPathEffect(new float[]{dp(4), dp(4)}, 0));
        text.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
        setClickable(true);
        setContentDescription("Radar droni");
    }

    private float dp(float v) { return v * getResources().getDisplayMetrics().density; }

    // ------------------------------------------------------------ API
    public void setData(List<DroneTrack> t, double lat, double lon) {
        tracks = t != null ? t : Collections.<DroneTrack>emptyList();
        uLat = lat; uLon = lon;
        float far = 0;
        if (DroneTrack.validLatLon(lat, lon)) {
            for (DroneTrack d : tracks) {
                if (!d.hasPosition()) continue;
                far = Math.max(far, (float) DroneTrack.distance(lat, lon, d.lat, d.lon));
                if (d.hasOperator()) far = Math.max(far, (float) DroneTrack.distance(lat, lon, d.opLat, d.opLon));
            }
        }
        range = RANGES[RANGES.length - 1];
        for (float r : RANGES) if (far * 1.15f <= r) { range = r; break; }
        invalidate();
    }

    public void setHeading(float deg) { heading = deg; }
    public void setHeadingUp(boolean on) { headingUp = on; invalidate(); }
    public boolean isHeadingUp() { return headingUp; }
    public void setTilt3d(boolean on) { tilt3d = on; invalidate(); }
    public boolean isTilt3d() { return tilt3d; }
    public void setCompact(boolean on) { compact = on; invalidate(); }
    public void setAcoustic(float a) { acoustic = a; }
    public void setDemo(boolean on) { demo = on; }
    public void setOnTrackTap(OnTrackTap l) { tapListener = l; }

    // ------------------------------------------------------------ ciclo animazione
    @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); running = true; invalidate(); }
    @Override protected void onDetachedFromWindow() { running = false; super.onDetachedFromWindow(); }
    @Override protected void onWindowVisibilityChanged(int v) {
        super.onWindowVisibilityChanged(v);
        running = v == VISIBLE;
        if (running) invalidate();
    }

    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);
        int w = getWidth(), h = getHeight();
        if (w == 0 || h == 0) return;
        float t = (SystemClock.uptimeMillis() - t0) / 1000f;
        shownRange += (range - shownRange) * 0.12f;
        float targetTilt = tilt3d ? TILT : 0f;
        tiltNow += (targetTilt - tiltNow) * 0.15f;

        // in 3D il piano si allarga davanti e si stringe dietro: raggio e centro
        // si spostano gradualmente fra la vista piatta e quella inclinata
        // (il piano proiettato va da -0,45R a +0,75R attorno al centro: lo si
        // centra lasciando un po' di spazio sopra per gli steli della quota)
        float k3 = tiltNow / TILT;
        float cx = w / 2f;
        float R = lerp(Math.min(w, h) * 0.44f, Math.min(w * 0.41f, h * 0.6f), k3);
        float cy = lerp(h / 2f, h * 0.55f - 0.15f * R, k3);
        if (cx != lastCx || R != lastR) {
            sweepShader = new SweepGradient(0, 0,
                new int[]{0x0000E5FF, 0x0000E5FF, 0x4400E5FF, 0xAA00E5FF, 0x0000E5FF},
                new float[]{0f, 0.70f, 0.95f, 0.999f, 1f});
            discShader = new RadialGradient(0, 0, R,
                new int[]{0xFF0B2B3C, 0xFF07182A, 0xFF040C18}, new float[]{0f, 0.65f, 1f}, Shader.TileMode.CLAMP);
            lastCx = cx; lastR = R;
        }
        float rot = headingUp && !Float.isNaN(heading) ? -heading : 0f;

        // ---------------------------------------------------- piano inclinato
        perspective(R, tiltNow, cx, cy);

        c.save();
        c.concat(m3d);
        drawPlane(c, R, t, rot);
        c.restore();

        // ---------------------------------------------------- droni e operatori
        hitTracks.clear();
        hitPts.clear();
        int noPos = 0;
        boolean hasUser = DroneTrack.validLatLon(uLat, uLon);
        long now = System.currentTimeMillis();
        float sinT = (float) Math.sin(Math.toRadians(tiltNow));
        for (DroneTrack d : tracks) {
            if (!d.hasPosition() || !hasUser) { noPos++; continue; }
            int col = d.simulated ? COL_DEMO : (d.uasId.isEmpty() ? COL_NOID : COL_REAL);
            if (d.status == RemoteIdParser.STATUS_EMERGENCY && ((int) (t * 4)) % 2 == 0) col = 0xFFFF1744;
            float age = (now - d.lastSeen) / 1000f;
            int alpha = age > 15 ? 90 : 255;

            // scia
            if (d.trail.size() > 1) {
                int i = 0, n = d.trail.size();
                float px = 0, py = 0;
                stroke.setStrokeWidth(dp(2));
                for (double[] p : d.trail) {
                    toScreen(p[0], p[1], R, rot);
                    if (i > 0) {
                        stroke.setColor(withAlpha(col, (int) (alpha * 0.55f * i / n)));
                        c.drawLine(px, py, pt[0], pt[1], stroke);
                    }
                    px = pt[0]; py = pt[1]; i++;
                }
            }
            // operatore + collegamento tratteggiato
            toScreen(d.lat, d.lon, R, rot);
            float gx = pt[0], gy = pt[1];
            if (d.hasOperator()) {
                toScreen(d.opLat, d.opLon, R, rot);
                dash.setColor(withAlpha(COL_OP, alpha / 2));
                dash.setStrokeWidth(dp(1.2f));
                c.drawLine(pt[0], pt[1], gx, gy, dash);
                drawDiamond(c, pt[0], pt[1], dp(compact ? 3.5f : 5), withAlpha(COL_OP, alpha));
            }
            // stelo della quota
            float alt = d.displayAltitude();
            float stalk = Float.isNaN(alt) ? 0 : Math.min(R * 0.55f, Math.max(0, alt) / shownRange * R * 2.5f) * sinT;
            float bx = gx, by = gy - stalk;
            if (stalk > 1) {
                stroke.setStrokeWidth(dp(1.5f));
                stroke.setColor(withAlpha(col, alpha / 2));
                c.drawLine(gx, gy, bx, by, stroke);
                fill.setColor(withAlpha(col, alpha / 3));
                c.drawOval(gx - dp(6), gy - dp(2.2f), gx + dp(6), gy + dp(2.2f), fill);
            }
            // ping all'ultimo pacchetto
            float since = (now - d.lastSeen) / 1000f;
            if (since < 1.2f) {
                float k = since / 1.2f;
                stroke.setStrokeWidth(dp(2));
                stroke.setColor(withAlpha(col, (int) (200 * (1 - k))));
                c.drawCircle(bx, by, dp(8) + dp(22) * k, stroke);
            }
            // bagliore + nucleo
            float pulse = 1f + 0.15f * (float) Math.sin(t * 5 + d.key.hashCode());
            fill.setColor(withAlpha(col, alpha / 6));
            c.drawCircle(bx, by, dp(compact ? 10 : 15) * pulse, fill);
            fill.setColor(withAlpha(col, alpha / 3));
            c.drawCircle(bx, by, dp(compact ? 6 : 9), fill);
            fill.setColor(withAlpha(col, alpha));
            c.drawCircle(bx, by, dp(compact ? 3 : 4.5f), fill);
            fill.setColor(withAlpha(0xFFFFFFFF, alpha));
            c.drawCircle(bx, by, dp(1.6f), fill);
            // freccia di direzione
            if (!Float.isNaN(d.direction) && !compact) {
                double a = Math.toRadians(d.direction + rot);
                float len = dp(18);
                stroke.setStrokeWidth(dp(2));
                stroke.setColor(withAlpha(col, alpha));
                c.drawLine(bx, by, bx + (float) Math.sin(a) * len, by - (float) Math.cos(a) * len * (1 - 0.5f * sinT), stroke);
            }
            if (!compact) {
                double dist = DroneTrack.distance(uLat, uLon, d.lat, d.lon);
                String name = d.title();
                if (name.length() > 16) name = name.substring(0, 15) + "…";
                text.setTextAlign(Paint.Align.LEFT);
                text.setTextSize(dp(11));
                text.setColor(withAlpha(0xFFE8F4FD, alpha));
                c.drawText(name, bx + dp(12), by - dp(4), text);
                text.setTextSize(dp(10));
                text.setColor(withAlpha(col, alpha));
                String sub = DroneTrack.formatDistance(dist)
                    + (Float.isNaN(alt) ? "" : String.format(Locale.ITALY, " · %.0f m", alt));
                c.drawText(sub, bx + dp(12), by + dp(9), text);
            }
            hitTracks.add(d);
            hitPts.add(new float[]{bx, by});
        }

        // ---------------------------------------------------- sovrimpressioni
        text.setTextAlign(Paint.Align.CENTER);
        if (acoustic > 0.25f && !compact) {
            float k = Math.min(1f, (acoustic - 0.25f) / 0.6f);
            text.setTextAlign(Paint.Align.LEFT);
            text.setTextSize(dp(10));
            text.setColor(blend(0xFFFFD600, 0xFFFF1744, k));
            c.drawText(String.format(Locale.ITALY, "AUDIO DRONE %.0f%%", acoustic * 100), dp(8), dp(30), text);
            text.setTextAlign(Paint.Align.CENTER);
        }
        if (demo) {
            text.setTextSize(dp(compact ? 9 : 11));
            text.setColor(COL_DEMO);
            c.drawText("SIMULAZIONE", cx, h - dp(compact ? 6 : 10), text);
        }
        if (!compact) {
            text.setTextAlign(Paint.Align.LEFT);
            text.setTextSize(dp(10));
            text.setColor(0xFF5A7A99);
            c.drawText("RAGGIO " + DroneTrack.formatDistance(shownRange), dp(8), dp(16), text);
            if (noPos > 0) {
                text.setColor(COL_NOID);
                c.drawText("+" + noPos + (noPos == 1 ? " segnale" : " segnali") + " senza posizione", dp(8), h - dp(10), text);
            }
            if (!hasUser) {
                text.setTextAlign(Paint.Align.CENTER);
                text.setColor(0xFFFFD600);
                c.drawText("In attesa del GPS...", cx, h - dp(26), text);
            }
        }
        if (running) {
            if (compact) postInvalidateDelayed(33);
            else postInvalidateOnAnimation();
        }
    }

    /** Piano del radar in coordinate centrate (0,0) gia' trasformate dalla prospettiva. */
    private void drawPlane(Canvas c, float R, float t, float rot) {
        disc.setShader(discShader);
        c.drawCircle(0, 0, R, disc);
        // anelli di distanza
        stroke.setStrokeWidth(dp(1));
        for (int i = 1; i <= 4; i++) {
            stroke.setColor(i == 4 ? 0x8800E5FF : 0x3300E5FF);
            c.drawCircle(0, 0, R * i / 4f, stroke);
        }
        // croce e tacche dei gradi
        stroke.setColor(0x2200E5FF);
        c.drawLine(-R, 0, R, 0, stroke);
        c.drawLine(0, -R, 0, R, stroke);
        for (int deg = 0; deg < 360; deg += 10) {
            double a = Math.toRadians(deg + rot);
            float len = deg % 30 == 0 ? dp(8) : dp(4);
            float sx = (float) Math.sin(a), sy = (float) -Math.cos(a);
            stroke.setColor(deg % 90 == 0 ? 0xAA00E5FF : 0x5500E5FF);
            c.drawLine(sx * R, sy * R, sx * (R - len), sy * (R - len), stroke);
        }
        // anello acustico: si accende e pulsa quando il microfono sente eliche
        if (acoustic > 0.25f) {
            float k = Math.min(1f, (acoustic - 0.25f) / 0.6f);
            int col = blend(0xFFFFD600, 0xFFFF1744, k);
            float pulse2 = 0.5f + 0.5f * (float) Math.sin(t * 5);
            stroke.setStrokeWidth(dp(6));
            stroke.setColor(withAlpha(col, (int) (40 + 60 * pulse2)));
            c.drawCircle(0, 0, R * 1.03f, stroke);
            stroke.setStrokeWidth(dp(2.5f));
            stroke.setColor(withAlpha(col, (int) (150 + 100 * pulse2 * k)));
            c.drawCircle(0, 0, R * 1.03f, stroke);
        }
        // fascio rotante
        float ang = (t * 120f) % 360f;
        shaderM.setRotate(ang - 90);
        sweepShader.setLocalMatrix(shaderM);
        sweep.setShader(sweepShader);
        c.drawCircle(0, 0, R, sweep);
        double a = Math.toRadians(ang);
        stroke.setStrokeWidth(dp(2));
        stroke.setColor(0xCC00E5FF);
        c.drawLine(0, 0, (float) Math.sin(a) * R, (float) -Math.cos(a) * R, stroke);
        // punti cardinali
        text.setTextAlign(Paint.Align.CENTER);
        text.setTextSize(dp(compact ? 10 : 13));
        String[] card = {"N", "E", "S", "O"};
        for (int i = 0; i < 4; i++) {
            double ca = Math.toRadians(i * 90 + rot);
            text.setColor(i == 0 ? 0xFFFF1744 : 0xFF8FB3D0);
            float rr = R + dp(compact ? 9 : 15);
            c.drawText(card[i], (float) Math.sin(ca) * rr, (float) -Math.cos(ca) * rr + dp(4), text);
        }
        // etichette distanza
        if (!compact) {
            text.setTextSize(dp(9));
            text.setColor(0x9900E5FF);
            for (int i = 1; i <= 3; i++)
                c.drawText(DroneTrack.formatDistance(shownRange * i / 4f), R * i / 4f * 0.707f + dp(14), -R * i / 4f * 0.707f, text);
        }
        // tu: punto centrale pulsante + cono di vista
        float pulse = (t % 1.6f) / 1.6f;
        stroke.setColor(withAlpha(COL_CYAN, (int) (180 * (1 - pulse))));
        stroke.setStrokeWidth(dp(2));
        c.drawCircle(0, 0, dp(6) + dp(16) * pulse, stroke);
        if (!Float.isNaN(heading)) {
            float hd = headingUp ? 0 : heading;
            path.reset();
            path.moveTo(0, 0);
            float cone = R * 0.42f;
            double l = Math.toRadians(hd - 22), r2 = Math.toRadians(hd + 22);
            path.lineTo((float) Math.sin(l) * cone, (float) -Math.cos(l) * cone);
            path.lineTo((float) Math.sin(r2) * cone, (float) -Math.cos(r2) * cone);
            path.close();
            fill.setColor(0x2200E5FF);
            c.drawPath(path, fill);
        }
        fill.setColor(COL_CYAN);
        c.drawCircle(0, 0, dp(5), fill);
        fill.setColor(0xFFFFFFFF);
        c.drawCircle(0, 0, dp(2), fill);
    }

    /**
     * Prospettiva del piano: rotazione attorno all'asse X di "tilt" gradi vista
     * da una distanza di 2,8 R. La proiezione di un piano e' un'omografia,
     * quindi basta mappare i 4 angoli (esatto, nessuna dipendenza da Camera).
     */
    private void perspective(float R, float tilt, float cx, float cy) {
        double t = Math.toRadians(tilt), d = R * 3.2;
        float[] src = {-R, -R, R, -R, R, R, -R, R};
        float[] dst = new float[8];
        for (int i = 0; i < 8; i += 2) {
            double x = src[i], y = src[i + 1];
            double z = -y * Math.sin(t);           // il bordo alto si allontana
            double k = d / (d + z);
            dst[i] = (float) (cx + x * k);
            dst[i + 1] = (float) (cy + y * Math.cos(t) * k);
        }
        m3d.reset();
        if (!m3d.setPolyToPoly(src, 0, dst, 0, 4)) { m3d.reset(); m3d.postTranslate(cx, cy); }
    }

    /** Proietta lat/lon sul piano (prospettiva inclusa): risultato in pt[]. */
    private void toScreen(double la, double lo, float R, float rot) {
        double dist = DroneTrack.distance(uLat, uLon, la, lo);
        double brg = Math.toRadians(DroneTrack.bearing(uLat, uLon, la, lo) + rot);
        float k = (float) Math.min(1.08, dist / shownRange) * R;
        pt[0] = (float) Math.sin(brg) * k;
        pt[1] = (float) -Math.cos(brg) * k;
        m3d.mapPoints(pt);
    }

    private void drawDiamond(Canvas c, float x, float y, float s, int col) {
        path.reset();
        path.moveTo(x, y - s); path.lineTo(x + s, y); path.lineTo(x, y + s); path.lineTo(x - s, y); path.close();
        fill.setColor(col);
        c.drawPath(path, fill);
    }

    private static float lerp(float a, float b, float k) { return a + (b - a) * k; }

    private static int withAlpha(int col, int a) {
        return (Math.max(0, Math.min(255, a)) << 24) | (col & 0xFFFFFF);
    }

    private static int blend(int a, int b, float k) {
        int ar = (a >> 16) & 0xFF, ag = (a >> 8) & 0xFF, ab = a & 0xFF;
        int br = (b >> 16) & 0xFF, bg = (b >> 8) & 0xFF, bb = b & 0xFF;
        return 0xFF000000 | ((int) (ar + (br - ar) * k) << 16) | ((int) (ag + (bg - ag) * k) << 8) | (int) (ab + (bb - ab) * k);
    }

    // ------------------------------------------------------------ tocco
    @Override public boolean onTouchEvent(MotionEvent e) {
        if (e.getAction() == MotionEvent.ACTION_UP) {
            DroneTrack best = null;
            float bestD = dp(30);
            for (int i = 0; i < hitPts.size(); i++) {
                float[] p = hitPts.get(i);
                float d = (float) Math.hypot(p[0] - e.getX(), p[1] - e.getY());
                if (d < bestD) { bestD = d; best = hitTracks.get(i); }
            }
            if (best != null && tapListener != null) {
                tapListener.onTrackTap(best);
                return true;
            }
            performClick();
            return true;
        }
        return e.getAction() == MotionEvent.ACTION_DOWN || super.onTouchEvent(e);
    }

    @Override public boolean performClick() { return super.performClick(); }
}
"""

SPECTROGRAM_VIEW = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.View;
import java.util.Locale;

/**
 * Spettrogramma "a cascata": ogni riga e' una finestra audio (la piu' recente
 * in alto), da sinistra a destra 0-3000 Hz. Le righe verticali luminose sono
 * le armoniche delle eliche; i marcatori indicano la fondamentale stimata.
 */
public class SpectrogramView extends View {
    private static final int ROWS = 120;
    private int bins = 256;
    private float maxHz = 3000f;
    private Bitmap bmp;
    private int[] pixels;      // ROWS x bins, riga 0 = la piu' recente
    private float f0;
    private final int[] lut = new int[256];
    private final Paint paint = new Paint(Paint.FILTER_BITMAP_FLAG);
    private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint frame = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Rect src = new Rect();
    private final RectF dst = new RectF();

    public SpectrogramView(Context c) { this(c, null); }
    public SpectrogramView(Context c, AttributeSet a) {
        super(c, a);
        // mappa colori neon: nero -> blu notte -> ciano -> verde -> giallo -> bianco
        int[] stops = {0xFF02040A, 0xFF071A3A, 0xFF0050A0, 0xFF00E5FF, 0xFF00FF88, 0xFFFFD600, 0xFFFFFFFF};
        for (int i = 0; i < 256; i++) {
            float x = i / 255f * (stops.length - 1);
            int k = Math.min(stops.length - 2, (int) x);
            lut[i] = mix(stops[k], stops[k + 1], x - k);
        }
        text.setTextSize(dp(10));
        text.setColor(0xFF8FB3D0);
        frame.setStyle(Paint.Style.STROKE);
        frame.setStrokeWidth(dp(1));
        frame.setColor(0x4400E5FF);
        line.setStrokeWidth(dp(1.2f));
    }

    private float dp(float v) { return v * getResources().getDisplayMetrics().density; }

    public void configure(int displayBins, float displayMaxHz) {
        bins = displayBins;
        maxHz = displayMaxHz;
        bmp = null;
    }

    /** Aggiunge una riga: valori 0..1 (DISPLAY_BINS). f0 = fondamentale (0 se nessuna). */
    public void push(float[] spectrum, float fundamental) {
        if (spectrum == null) return;
        if (bmp == null) {
            bmp = Bitmap.createBitmap(bins, ROWS, Bitmap.Config.ARGB_8888);
            pixels = new int[bins * ROWS];
            java.util.Arrays.fill(pixels, lut[0]);
        }
        // scorre tutto di una riga verso il basso e scrive la nuova in alto
        System.arraycopy(pixels, 0, pixels, bins, bins * (ROWS - 1));
        int n = Math.min(bins, spectrum.length);
        for (int i = 0; i < bins; i++) {
            float v = i < n ? Math.max(0f, Math.min(1f, spectrum[i])) : 0f;
            pixels[i] = lut[(int) (Math.pow(v, 0.75) * 255)];
        }
        bmp.setPixels(pixels, 0, bins, 0, 0, bins, ROWS);
        f0 = fundamental;
        invalidate();
    }

    public void clear() {
        if (pixels != null) {
            java.util.Arrays.fill(pixels, lut[0]);
            bmp.setPixels(pixels, 0, bins, 0, 0, bins, ROWS);
        }
        f0 = 0;
        invalidate();
    }

    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);
        float w = getWidth(), h = getHeight();
        float axis = dp(16);
        float ph = h - axis;
        if (bmp == null) {
            paint.setColor(lut[0]);
            c.drawRect(0, 0, w, ph, paint);
        } else {
            src.set(0, 0, bins, ROWS);
            dst.set(0, 0, w, ph);
            c.drawBitmap(bmp, src, dst, paint);
        }
        // armoniche della fondamentale stimata
        if (f0 > 0) {
            for (int hN = 1; hN <= 12; hN++) {
                float hz = f0 * hN;
                if (hz > maxHz) break;
                float x = hz / maxHz * w;
                line.setColor(hN == 1 ? 0xCCFF3D71 : 0x66FF3D71);
                c.drawLine(x, 0, x, dp(hN == 1 ? 14 : 8), line);
            }
            text.setTextAlign(Paint.Align.RIGHT);
            text.setColor(0xFFFF3D71);
            c.drawText(String.format(Locale.ITALY, "f0 %.0f Hz", f0), w - dp(6), dp(26), text);
        }
        c.drawRect(0, 0, w, ph, frame);
        // asse delle frequenze
        text.setColor(0xFF5A7A99);
        for (int hz = 0; hz <= (int) maxHz; hz += 500) {
            float x = hz / maxHz * w;
            text.setTextAlign(hz == 0 ? Paint.Align.LEFT : (hz >= maxHz ? Paint.Align.RIGHT : Paint.Align.CENTER));
            c.drawText(hz >= 1000 ? (hz / 1000f) + "k" : String.valueOf(hz), x, h - dp(3), text);
        }
    }

    private static int mix(int a, int b, float k) {
        int ar = (a >> 16) & 0xFF, ag = (a >> 8) & 0xFF, ab = a & 0xFF;
        int br = (b >> 16) & 0xFF, bg = (b >> 8) & 0xFF, bb = b & 0xFF;
        return 0xFF000000 | ((int) (ar + (br - ar) * k) << 16) | ((int) (ag + (bg - ag) * k) << 8) | (int) (ab + (bb - ab) * k);
    }
}
"""

NEON_GAUGE_VIEW = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.SweepGradient;
import android.graphics.Typeface;
import android.util.AttributeSet;
import android.view.View;

/** Indicatore ad arco neon (0..1) con lancetta luminosa e valore animato. */
public class NeonGaugeView extends View {
    private static final float START = 150f, SPAN = 240f;
    private float target, value;
    private String label = "", caption = "";
    private final Paint track = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint arc = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint glow = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint tick = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint big = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint small = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF oval = new RectF();
    private final Matrix rot = new Matrix();
    private SweepGradient shader;
    private float lastW = -1;

    public NeonGaugeView(Context c) { this(c, null); }
    public NeonGaugeView(Context c, AttributeSet a) {
        super(c, a);
        for (Paint p : new Paint[]{track, arc, glow, tick}) {
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeCap(Paint.Cap.ROUND);
        }
        track.setColor(0xFF132235);
        tick.setStrokeWidth(dp(1.5f));
        big.setTextAlign(Paint.Align.CENTER);
        big.setColor(0xFFE8F4FD);
        big.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
        small.setTextAlign(Paint.Align.CENTER);
        small.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
    }

    private float dp(float v) { return v * getResources().getDisplayMetrics().density; }

    public void setValue(float v) { target = Math.max(0f, Math.min(1f, v)); invalidate(); }
    public void setLabel(String l) { label = l != null ? l : ""; invalidate(); }
    public void setCaption(String c) { caption = c != null ? c : ""; invalidate(); }

    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);
        float w = getWidth(), h = getHeight();
        float size = Math.min(w, h * 1.25f);
        float sw = size * 0.075f;
        float r = size / 2f - sw * 1.6f;
        float cx = w / 2f, cy = h * 0.56f;
        oval.set(cx - r, cy - r, cx + r, cy + r);
        if (w != lastW) {
            shader = new SweepGradient(cx, cy,
                new int[]{0xFF00FF88, 0xFF00E5FF, 0xFFFFD600, 0xFFFF6B35, 0xFFFF1744, 0xFF00FF88},
                new float[]{0f, 0.18f, 0.38f, 0.52f, 0.66f, 1f});
            rot.setRotate(START, cx, cy);
            shader.setLocalMatrix(rot);
            lastW = w;
        }
        value += (target - value) * 0.18f;
        if (Math.abs(target - value) > 0.002f) postInvalidateOnAnimation();

        track.setStrokeWidth(sw);
        c.drawArc(oval, START, SPAN, false, track);
        for (int i = 0; i <= 10; i++) {
            double a = Math.toRadians(START + SPAN * i / 10f);
            float r1 = r - sw, r2 = r - sw - dp(i % 5 == 0 ? 9 : 5);
            tick.setColor(i % 5 == 0 ? 0xAA8FB3D0 : 0x558FB3D0);
            c.drawLine(cx + (float) Math.cos(a) * r1, cy + (float) Math.sin(a) * r1,
                       cx + (float) Math.cos(a) * r2, cy + (float) Math.sin(a) * r2, tick);
        }
        float sweep = Math.max(0.5f, SPAN * value);
        glow.setShader(shader);
        glow.setStrokeWidth(sw * 2.2f);
        glow.setAlpha(60);
        c.drawArc(oval, START, sweep, false, glow);
        arc.setShader(shader);
        arc.setStrokeWidth(sw);
        c.drawArc(oval, START, sweep, false, arc);
        // punta luminosa
        double a = Math.toRadians(START + sweep);
        float px = cx + (float) Math.cos(a) * r, py = cy + (float) Math.sin(a) * r;
        small.setColor(0x55FFFFFF);
        c.drawCircle(px, py, sw * 0.9f, small);
        small.setColor(0xFFFFFFFF);
        c.drawCircle(px, py, sw * 0.38f, small);

        big.setTextSize(size * 0.2f);
        c.drawText(Math.round(value * 100) + "%", cx, cy + size * 0.06f, big);
        small.setTextSize(size * 0.065f);
        small.setColor(colorFor(value));
        c.drawText(label, cx, cy + size * 0.17f, small);
        small.setColor(0xFF5A7A99);
        small.setTextSize(size * 0.052f);
        c.drawText(caption, cx, cy + size * 0.27f, small);
    }

    private static int colorFor(float v) {
        if (v < 0.3f) return 0xFF00FF88;
        if (v < 0.5f) return 0xFFFFD600;
        if (v < 0.7f) return 0xFFFF6B35;
        return 0xFFFF1744;
    }
}
"""

AURORA_VIEW = r"""package com.offlinegps.map.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.os.SystemClock;
import android.util.AttributeSet;
import android.view.View;
import java.util.Random;

/**
 * Sfondo animato: aurora di luci al neon che si muovono lentamente, stelle
 * che pulsano e una griglia prospettica "3D" che scorre verso l'orizzonte.
 * Si ferma da sola quando la schermata non e' visibile (zero consumo).
 */
public class AuroraView extends View {
    private static final int STARS = 70;
    private final Paint blob = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint grid = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint star = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Matrix m = new Matrix();
    private RadialGradient[] shaders;
    private final int[] colors = {0x3000E5FF, 0x387C4DFF, 0x2200FF88};
    private final float[] sx = new float[STARS], sy = new float[STARS], sp = new float[STARS];
    private final long t0 = SystemClock.uptimeMillis();
    private boolean running, showGrid = true;
    private float intensity = 1f;
    private int lastW, lastH;

    public AuroraView(Context c) { this(c, null); }
    public AuroraView(Context c, AttributeSet a) {
        super(c, a);
        Random r = new Random(7);
        for (int i = 0; i < STARS; i++) { sx[i] = r.nextFloat(); sy[i] = r.nextFloat() * 0.62f; sp[i] = r.nextFloat() * 6.28f; }
        grid.setStyle(Paint.Style.STROKE);
        grid.setStrokeWidth(getResources().getDisplayMetrics().density);
    }

    public void setShowGrid(boolean on) { showGrid = on; invalidate(); }
    /** 0..1: quanto sono vivaci le luci (le schermate operative la abbassano). */
    public void setIntensity(float k) { intensity = Math.max(0f, Math.min(1f, k)); invalidate(); }

    @Override protected void onAttachedToWindow() { super.onAttachedToWindow(); running = true; invalidate(); }
    @Override protected void onDetachedFromWindow() { running = false; super.onDetachedFromWindow(); }
    @Override protected void onWindowVisibilityChanged(int v) {
        super.onWindowVisibilityChanged(v);
        running = v == VISIBLE;
        if (running) invalidate();
    }

    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);
        int w = getWidth(), h = getHeight();
        if (w == 0 || h == 0) return;
        if (shaders == null || w != lastW || h != lastH) {
            float rad = Math.max(w, h) * 0.42f;
            shaders = new RadialGradient[colors.length];
            for (int i = 0; i < colors.length; i++)
                shaders[i] = new RadialGradient(0, 0, rad, colors[i], colors[i] & 0x00FFFFFF, Shader.TileMode.CLAMP);
            lastW = w; lastH = h;
        }
        float t = (SystemClock.uptimeMillis() - t0) / 1000f;
        c.drawColor(0xFF050A14);

        // luci dell'aurora (traslate con una matrice: nessuna allocazione per frame)
        for (int i = 0; i < shaders.length; i++) {
            float px = w * (0.5f + 0.42f * (float) Math.sin(t * (0.07f + i * 0.031f) + i * 2.1f));
            float py = h * (0.22f + 0.18f * (float) Math.cos(t * (0.05f + i * 0.023f) + i * 1.3f));
            float sc = 0.8f + 0.25f * (float) Math.sin(t * 0.11f + i);
            m.setScale(sc * 1.4f, sc);
            m.postTranslate(px, py);
            shaders[i].setLocalMatrix(m);
            blob.setShader(shaders[i]);
            blob.setAlpha((int) (255 * intensity));
            c.drawRect(0, 0, w, h, blob);
        }

        // stelle che pulsano
        float d = getResources().getDisplayMetrics().density;
        for (int i = 0; i < STARS; i++) {
            float tw = 0.5f + 0.5f * (float) Math.sin(t * 1.7f + sp[i]);
            star.setColor(((int) (40 + 150 * tw * intensity) << 24) | 0xE8F4FD);
            c.drawCircle(sx[i] * w, sy[i] * h, d * (0.6f + 0.9f * tw * (i % 3 == 0 ? 1 : 0.5f)), star);
        }

        // griglia prospettica in basso (pavimento "3D" che scorre)
        if (showGrid) {
            float horizon = h * 0.64f, vx = w / 2f;
            int lines = 14;
            for (int i = -lines; i <= lines; i++) {
                float bx = vx + i * w / 6f;
                grid.setColor(0x2200E5FF);
                c.drawLine(vx, horizon, bx, h, grid);
            }
            float phase = (t * 0.25f) % 1f;
            for (int i = 0; i < 12; i++) {
                float z = (i + phase) / 12f;
                float y = horizon + (h - horizon) * z * z;
                grid.setColor(((int) (12 + 70 * z * intensity) << 24) | 0x00E5FF);
                c.drawLine(0, y, w, y, grid);
            }
            grid.setColor(0x5500E5FF);
            c.drawLine(0, horizon, w, horizon, grid);
        }
        if (running) postInvalidateDelayed(33);
    }
}
"""

SKY_WATCH_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.sky.AcousticDetector;
import com.offlinegps.map.sky.DroneTrack;
import com.offlinegps.map.sky.HeadingSensor;
import com.offlinegps.map.sky.RemoteIdParser;
import com.offlinegps.map.sky.RemoteIdScanner;
import com.offlinegps.map.sky.SkyState;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * SENTINELLA CIELO: rilevamento PASSIVO dei droni vicini.
 *  - riceve il Remote ID (Bluetooth + Wi-Fi) che i droni UE trasmettono;
 *  - opzionalmente ascolta il ronzio delle eliche col microfono;
 *  - mostra tutto su un radar 3D centrato su di te, con avvisi a voce.
 * Non trasmette nulla e non interferisce con nessun drone.
 */
public class SkyWatchActivity extends AppCompatActivity implements SkyState.Listener {
    private static final int REQ_SCAN = 7101, REQ_MIC = 7102;
    private static final long LOST_MS = 15_000, FORGET_MS = 120_000;

    private SkyRadarView radar;
    private TextView chipBle, chipWifi, chipMic, chipVoice, tvLive, tvSummary, tvEmpty, tv3d, tvNorth, tvScanLabel;
    private LinearLayout list;
    private RemoteIdScanner scanner;
    private AcousticDetector acoustic;
    private HeadingSensor heading;
    private LocationManager lm;
    private TextToSpeech tts;
    private boolean ttsReady, voiceOn, wantScan, wantMic, virtualUser, askedScan, askedMic;
    private long lastRefresh;
    private final Runnable refreshLater = this::refresh;
    private double gpsLat = Double.NaN, gpsLon = Double.NaN;
    private final Set<String> announced = new HashSet<>();
    private final Map<String, CardHolder> cards = new HashMap<>();
    private final Handler h = new Handler(Looper.getMainLooper());
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            SkyState.get().prune(FORGET_MS);
            refresh();
            h.postDelayed(this, 1000);
        }
    };
    private final LocationListener locListener = new LocationListener() {
        @Override public void onLocationChanged(@NonNull Location l) { onFix(l); }
        @Override public void onStatusChanged(String p, int s, Bundle b) {}
        @Override public void onProviderEnabled(@NonNull String p) {}
        @Override public void onProviderDisabled(@NonNull String p) {}
    };

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_sky_watch);
        radar = findViewById(R.id.sky_radar);
        chipBle = findViewById(R.id.chip_sky_ble);
        chipWifi = findViewById(R.id.chip_sky_wifi);
        chipMic = findViewById(R.id.chip_sky_mic);
        chipVoice = findViewById(R.id.chip_sky_voice);
        tvLive = findViewById(R.id.tv_sky_live);
        tvSummary = findViewById(R.id.tv_sky_summary);
        tvEmpty = findViewById(R.id.tv_sky_empty);
        tv3d = findViewById(R.id.tv_sky_3d);
        tvNorth = findViewById(R.id.tv_sky_north);
        tvScanLabel = findViewById(R.id.tv_sky_scan_label);
        list = findViewById(R.id.sky_list);
        scanner = new RemoteIdScanner(this);
        acoustic = new AcousticDetector(this);
        heading = new HeadingSensor(this);
        lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        voiceOn = getPreferences(MODE_PRIVATE).getBoolean("voice", true);

        radar.setOnTrackTap(this::showDetails);
        click(R.id.btn_sky_back, v -> finish());
        click(R.id.btn_sky_scan, v -> toggleScan());
        click(R.id.btn_sky_demo, v -> toggleDemo());
        click(R.id.btn_sky_audio, v -> startActivity(new Intent(this, AcousticDetectorActivity.class)));
        click(R.id.btn_sky_spot, v -> startActivity(new Intent(this, SkySpotActivity.class)));
        click(R.id.btn_sky_check, v -> startActivity(new Intent(this, SightingCheckActivity.class)));
        click(R.id.btn_sky_airspace, v -> showAirspace());
        click(R.id.chip_sky_mic, v -> toggleMic());
        click(R.id.chip_sky_voice, v -> {
            voiceOn = !voiceOn;
            getPreferences(MODE_PRIVATE).edit().putBoolean("voice", voiceOn).apply();
            if (voiceOn) initTts();
            refresh();
        });
        click(R.id.chip_sky_ble, v -> toggleScan());
        click(R.id.chip_sky_wifi, v -> {
            if (!RemoteIdScanner.wifiBeaconSupported())
                Toast.makeText(this, "Il Remote ID via Wi-Fi Beacon richiede Android 11 o superiore", Toast.LENGTH_LONG).show();
            else toggleScan();
        });
        click(R.id.tv_sky_3d, v -> { radar.setTilt3d(!radar.isTilt3d()); refresh(); });
        click(R.id.tv_sky_north, v -> { radar.setHeadingUp(!radar.isHeadingUp()); refresh(); });
        if (voiceOn) initTts();
        wantScan = true;
    }

    private void click(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    @Override protected void onResume() {
        super.onResume();
        SkyState.get().addListener(this);
        startLocation();
        heading.start(deg -> { SkyState.get().heading = deg; radar.setHeading(deg); });
        if (wantScan) startScan(false);
        if (wantMic) startMic(false);
        h.post(tick);
    }

    @Override protected void onPause() {
        super.onPause();
        SkyState.get().removeListener(this);
        h.removeCallbacks(tick);
        h.removeCallbacks(refreshLater);
        scanner.stopAll();
        acoustic.stop();
        heading.stop();
        try { lm.removeUpdates(locListener); } catch (Exception ignored) {}
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        SkyState.get().stopDemo();
        if (virtualUser) SkyState.get().setUser(Double.NaN, Double.NaN);
        if (tts != null) { tts.stop(); tts.shutdown(); }
    }

    /** Molti pacchetti al secondo: ridisegna la lista al massimo ~3 volte al secondo. */
    @Override public void onSkyChanged() {
        long wait = 300 - (System.currentTimeMillis() - lastRefresh);
        h.removeCallbacks(refreshLater);
        if (wait <= 0) refresh(); else h.postDelayed(refreshLater, wait);
    }

    // ------------------------------------------------------------ scansione
    private void toggleScan() {
        if (scanner.isBleRunning() || scanner.isWifiRunning()) {
            wantScan = false;
            scanner.stopAll();
            refresh();
        } else {
            wantScan = true;
            startScan(true);
        }
    }

    private void startScan(boolean interactive) {
        if (!hasAll(RemoteIdScanner.requiredPermissions())) {
            // chiede una sola volta per apertura (o quando l'utente preme il pulsante)
            if (interactive || !askedScan) {
                askedScan = true;
                SkyUi.ensurePermissions(this, REQ_SCAN, RemoteIdScanner.neededPermissions());
            }
            return;
        }
        boolean ble = scanner.startBle();
        String bleErr = scanner.lastError;
        boolean wifi = scanner.startWifi();
        if (!ble && interactive) {
            if (bleErr.contains("Accendi")) {
                new AlertDialog.Builder(this)
                    .setTitle("Bluetooth spento")
                    .setMessage("Il Remote ID dei droni viaggia soprattutto via Bluetooth. Vuoi accenderlo?")
                    .setPositiveButton("Impostazioni", (d, w) -> {
                        try { startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)); } catch (Exception ignored) {}
                    })
                    .setNegativeButton("Solo Wi-Fi", null)
                    .show();
            } else if (!bleErr.isEmpty()) {
                Toast.makeText(this, bleErr, Toast.LENGTH_LONG).show();
            }
        }
        if (!ble && !wifi && !interactive) wantScan = false;
        refresh();
    }

    private void toggleMic() {
        if (acoustic.isRunning()) { wantMic = false; acoustic.stop(); refresh(); }
        else { wantMic = true; startMic(true); }
    }

    private void startMic(boolean interactive) {
        if (!hasAll(Manifest.permission.RECORD_AUDIO)) {
            if (interactive || !askedMic) {
                askedMic = true;
                SkyUi.ensurePermissions(this, REQ_MIC, Manifest.permission.RECORD_AUDIO);
            }
            return;
        }
        boolean ok = acoustic.start(r -> {
            radar.setAcoustic(r.score);
            refreshSummary();
        });
        if (!ok) {
            wantMic = false;
            if (interactive) Toast.makeText(this, acoustic.lastError, Toast.LENGTH_LONG).show();
        }
        refresh();
    }

    private void toggleDemo() {
        SkyState st = SkyState.get();
        if (st.isDemo()) {
            st.stopDemo();
            if (virtualUser) { virtualUser = false; st.setUser(gpsLat, gpsLon); }
            Toast.makeText(this, "Simulazione terminata", Toast.LENGTH_SHORT).show();
        } else {
            double la = gpsLat, lo = gpsLon;
            if (!DroneTrack.validLatLon(la, lo)) {
                // nessun GPS: centra la demo su Roma e usa una posizione virtuale
                la = 41.8902; lo = 12.4922;
                virtualUser = true;
                st.setUser(la, lo);
            }
            st.startDemo(la, lo);
            Toast.makeText(this, "SIMULAZIONE: 3 droni immaginari, nessun segnale reale", Toast.LENGTH_LONG).show();
        }
        refresh();
    }

    private boolean hasAll(String... perms) {
        for (String p : perms) if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) return false;
        return true;
    }

    // ------------------------------------------------------------ posizione
    /** Il permesso di posizione viene chiesto insieme a quelli della scansione. */
    private void startLocation() {
        if (!hasAll(Manifest.permission.ACCESS_FINE_LOCATION)) return;
        try {
            Location best = null;
            for (String p : new String[]{LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER}) {
                if (!lm.isProviderEnabled(p)) continue;
                Location l = lm.getLastKnownLocation(p);
                if (l != null && (best == null || l.getTime() > best.getTime())) best = l;
                lm.requestLocationUpdates(p, 2000, 2f, locListener);
            }
            if (best != null) onFix(best);
        } catch (SecurityException ignored) {
        } catch (Exception ignored) {}
    }

    private void onFix(Location l) {
        gpsLat = l.getLatitude();
        gpsLon = l.getLongitude();
        heading.setLocation(gpsLat, gpsLon, l.getAltitude());
        if (!virtualUser) SkyState.get().setUser(gpsLat, gpsLon);
        refresh();
    }

    // ------------------------------------------------------------ interfaccia
    private void refresh() {
        lastRefresh = System.currentTimeMillis();
        SkyState st = SkyState.get();
        List<DroneTrack> tracks = st.snapshot();
        radar.setData(tracks, st.userLat, st.userLon);
        radar.setDemo(st.isDemo());
        if (!acoustic.isRunning()) radar.setAcoustic(0);

        boolean ble = scanner.isBleRunning(), wifi = scanner.isWifiRunning(), mic = acoustic.isRunning();
        SkyUi.chip(chipBle, ble ? SkyUi.CHIP_ON : SkyUi.CHIP_OFF, ble ? "BLUETOOTH ON" : "BLUETOOTH");
        SkyUi.chip(chipWifi, wifi ? SkyUi.CHIP_ON : (RemoteIdScanner.wifiBeaconSupported() ? SkyUi.CHIP_OFF : SkyUi.CHIP_WARN),
            wifi ? "WI-FI ON" : "WI-FI");
        SkyUi.chip(chipMic, mic ? SkyUi.CHIP_ON : SkyUi.CHIP_OFF, mic ? "AUDIO ON" : "AUDIO");
        SkyUi.chip(chipVoice, voiceOn ? SkyUi.CHIP_ON : SkyUi.CHIP_OFF, voiceOn ? "VOCE ON" : "VOCE");
        boolean live = ble || wifi || mic;
        SkyUi.chip(tvLive, st.isDemo() ? SkyUi.CHIP_WARN : (live ? SkyUi.CHIP_ALERT : SkyUi.CHIP_OFF),
            st.isDemo() ? "DEMO" : (live ? "● LIVE" : "PAUSA"));
        SkyUi.chip(tv3d, radar.isTilt3d() ? SkyUi.CHIP_ON : SkyUi.CHIP_OFF, radar.isTilt3d() ? "VISTA 3D" : "VISTA 2D");
        SkyUi.chip(tvNorth, radar.isHeadingUp() ? SkyUi.CHIP_ON : SkyUi.CHIP_OFF, radar.isHeadingUp() ? "ROTTA ▲" : "NORD ▲");
        if (tvScanLabel != null) tvScanLabel.setText(ble || wifi ? "FERMA SCANSIONE" : "AVVIA SCANSIONE");
        refreshSummary();

        // schede dei droni: aggiornate SUL POSTO (ricrearle ogni secondo farebbe
        // perdere i tocchi), riordinate solo se cambia l'ordine
        long now = System.currentTimeMillis();
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < tracks.size(); i++) {
            DroneTrack d = tracks.get(i);
            seen.add(d.key);
            CardHolder ch = cards.get(d.key);
            if (ch == null) { ch = new CardHolder(); cards.put(d.key, ch); }
            ch.bind(d, now);
            if (list.getChildAt(i) != ch.root) {
                if (ch.root.getParent() != null) list.removeView(ch.root);
                list.addView(ch.root, Math.min(i, list.getChildCount()));
            }
            // avviso dopo 2,5 s: nel frattempo arriva di solito anche il numero di serie
            if (!d.simulated && now - d.firstSeen > 2500
                && announced.add(d.uasId.isEmpty() ? d.key : d.uasId)) alert(d);
        }
        Iterator<Map.Entry<String, CardHolder>> it = cards.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, CardHolder> e = it.next();
            if (!seen.contains(e.getKey())) { list.removeView(e.getValue().root); it.remove(); }
        }
        tvEmpty.setVisibility(tracks.isEmpty() ? View.VISIBLE : View.GONE);
    }

    private void refreshSummary() {
        SkyState st = SkyState.get();
        int real = st.countReal(), all = st.count();
        StringBuilder sb = new StringBuilder();
        if (all == 0) sb.append("Nessun drone con Remote ID nel raggio di ricezione");
        else {
            sb.append(real).append(real == 1 ? " drone reale" : " droni reali");
            if (all > real) sb.append(" · ").append(all - real).append(" simulati");
        }
        sb.append("\nPacchetti ricevuti: BT ").append(scanner.blePackets).append(" · Wi-Fi ").append(scanner.wifiPackets);
        if (acoustic.isRunning()) {
            sb.append(String.format(Locale.ITALY, "\nAudio: firma drone %.0f%%", st.acousticScore * 100));
            if (st.acousticF0 > 0) sb.append(String.format(Locale.ITALY, " (fondamentale %.0f Hz)", st.acousticF0));
        }
        if (virtualUser) sb.append("\nPosizione VIRTUALE (nessun GPS): solo per la simulazione");
        else if (!DroneTrack.validLatLon(st.userLat, st.userLon)) sb.append("\nIn attesa della posizione GPS...");
        if (!scanner.lastError.isEmpty() && !scanner.isBleRunning()) sb.append("\n").append(scanner.lastError);
        tvSummary.setText(sb.toString());
    }

    /** Scheda di un drone: costruita una volta, poi solo aggiornata. */
    private final class CardHolder {
        final LinearLayout root;
        final View bar;
        final TextView title;
        final TextView[] lines = new TextView[6];
        DroneTrack track;

        CardHolder() {
            root = SkyUi.card(SkyWatchActivity.this, 0xFFFF3D71, "", "-", "-", "-", "-", "-", "-");
            bar = root.getChildAt(0);
            LinearLayout col = (LinearLayout) root.getChildAt(1);
            title = (TextView) col.getChildAt(0);
            for (int i = 0; i < lines.length; i++) lines[i] = (TextView) col.getChildAt(i + 1);
            root.setOnClickListener(v -> { if (track != null) showDetails(track); });
            UiFx.addSpring(root);
        }

        void bind(DroneTrack d, long now) {
            track = d;
            SkyState st = SkyState.get();
            int accent = d.simulated ? 0xFFFFB300 : (d.uasId.isEmpty() ? 0xFFB388FF : 0xFFFF3D71);
            bar.setBackgroundColor(accent);
            boolean lost = now - d.lastSeen > LOST_MS;
            String where = "Posizione non trasmessa";
            if (d.hasPosition() && DroneTrack.validLatLon(st.userLat, st.userLon)) {
                double dist = DroneTrack.distance(st.userLat, st.userLon, d.lat, d.lon);
                double brg = DroneTrack.bearing(st.userLat, st.userLon, d.lat, d.lon);
                where = DroneTrack.formatDistance(dist) + " verso " + DroneTrack.cardinal(brg)
                    + String.format(Locale.ITALY, " (%.0f°)", brg);
            } else if (d.hasPosition()) {
                where = String.format(Locale.US, "%.5f, %.5f", d.lat, d.lon);
            }
            String flight = "";
            float alt = d.displayAltitude();
            if (!Float.isNaN(alt)) flight += String.format(Locale.ITALY, "Quota %.0f m", alt);
            if (!Float.isNaN(d.speed)) flight += String.format(Locale.ITALY, "%sVelocita' %.1f m/s (%.0f km/h)",
                flight.isEmpty() ? "" : " · ", d.speed, d.speed * 3.6f);
            if (!Float.isNaN(d.direction)) flight += String.format(Locale.ITALY, " · rotta %.0f°", d.direction);
            String status = RemoteIdParser.statusName(d.status) + " · " + d.sourceLabel()
                + (d.rssi > -127 ? " · " + d.rssi + " dBm" : "")
                + " · " + (lost ? "PERSO da " : "") + ((now - d.lastSeen) / 1000) + " s fa";
            String op = "";
            if (d.hasOperator() && DroneTrack.validLatLon(st.userLat, st.userLon))
                op = "Pilota a " + DroneTrack.formatDistance(DroneTrack.distance(st.userLat, st.userLon, d.opLat, d.opLon));
            if (!d.operatorId.isEmpty()) op += (op.isEmpty() ? "" : " · ") + "Operatore " + d.operatorId;
            title.setText(d.title() + (d.simulated ? "  [SIMULATO]" : ""));
            String[] txt = {d.typeLabel(), where, flight, status, op,
                d.selfId.isEmpty() ? "" : "\u201C" + d.selfId + "\u201D"};
            for (int i = 0; i < lines.length; i++) {
                lines[i].setText(txt[i]);
                lines[i].setVisibility(txt[i].isEmpty() ? View.GONE : View.VISIBLE);
            }
            root.setAlpha(lost ? 0.55f : 1f);
        }
    }

    private void showDetails(DroneTrack d) {
        SkyState st = SkyState.get();
        StringBuilder sb = new StringBuilder();
        sb.append("Tipo: ").append(d.typeLabel()).append('\n');
        sb.append("Stato: ").append(RemoteIdParser.statusName(d.status)).append('\n');
        if (d.hasPosition()) sb.append(String.format(Locale.US, "Posizione: %.6f, %.6f%n", d.lat, d.lon));
        if (d.hasPosition() && DroneTrack.validLatLon(st.userLat, st.userLon))
            sb.append("Distanza: ").append(DroneTrack.formatDistance(DroneTrack.distance(st.userLat, st.userLon, d.lat, d.lon)))
              .append(" verso ").append(DroneTrack.cardinal(DroneTrack.bearing(st.userLat, st.userLon, d.lat, d.lon))).append('\n');
        if (!Float.isNaN(d.height)) sb.append(String.format(Locale.ITALY, "Altezza dal suolo: %.0f m%n", d.height));
        if (!Float.isNaN(d.altGeo)) sb.append(String.format(Locale.ITALY, "Quota GPS: %.0f m%n", d.altGeo));
        if (!Float.isNaN(d.speed)) sb.append(String.format(Locale.ITALY, "Velocita': %.1f m/s%n", d.speed));
        if (!Float.isNaN(d.vspeed)) sb.append(String.format(Locale.ITALY, "Salita/discesa: %.1f m/s%n", d.vspeed));
        if (!d.selfId.isEmpty()) sb.append("Descrizione: ").append(d.selfId).append('\n');
        if (!d.operatorId.isEmpty()) sb.append("ID operatore: ").append(d.operatorId).append('\n');
        if (d.hasOperator()) sb.append(String.format(Locale.US, "Pilota: %.5f, %.5f%n", d.opLat, d.opLon));
        sb.append("Ricevuto via: ").append(d.sourceLabel()).append(" (").append(d.messages).append(" messaggi)\n");
        sb.append("\nIl Remote ID e' pubblico per legge, ma NON avvicinarti al pilota: "
            + "se il volo ti sembra pericoloso o illecito chiama il 112 e riferisci questi dati.");
        new AlertDialog.Builder(this)
            .setTitle(d.title())
            .setMessage(sb.toString())
            .setPositiveButton("Segnala", (dlg, w) -> {
                Intent i = new Intent(this, SkySpotActivity.class);
                i.putExtra(SkySpotActivity.EXTRA_REMOTE_ID, d.uasId.isEmpty() ? d.key : d.uasId);
                startActivity(i);
            })
            .setNeutralButton("Condividi", (dlg, w) -> SkyUi.share(this, "Drone " + d.title(), d.title() + "\n" + sb))
            .setNegativeButton("Chiudi", null)
            .show();
    }

    private void showAirspace() {
        new AlertDialog.Builder(this)
            .setTitle("Spazio aereo e regole")
            .setMessage("In Italia le zone dove i droni possono o non possono volare (aeroporti, "
                + "zone rosse, NOTAM temporanei) sono pubblicate da ENAC/ENAV sul portale d-flight.\n\n"
                + "Dal 2024 i droni di classe C1, C2, C3 e quelli registrati in categoria Specific devono "
                + "trasmettere il Remote ID: e' quello che questa schermata riceve.\n\n"
                + "Serve una connessione internet per aprire il portale.")
            .setPositiveButton("Apri d-flight", (d, w) -> {
                try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.d-flight.it/"))); }
                catch (Exception e) { Toast.makeText(this, "Nessun browser disponibile", Toast.LENGTH_SHORT).show(); }
            })
            .setNegativeButton("Chiudi", null)
            .show();
    }

    // ------------------------------------------------------------ avvisi
    private void initTts() {
        if (tts != null) return;
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(Locale.ITALIAN);
                ttsReady = true;
            }
        });
    }

    private void alert(DroneTrack d) {
        try {
            Vibrator vib = (Vibrator) getSystemService(VIBRATOR_SERVICE);
            if (vib != null) vib.vibrate(VibrationEffect.createWaveform(new long[]{0, 140, 90, 140}, -1));
        } catch (Exception ignored) {}
        if (!voiceOn || !ttsReady) return;
        SkyState st = SkyState.get();
        String msg = "Attenzione: rilevato un drone";
        if (d.hasPosition() && DroneTrack.validLatLon(st.userLat, st.userLon)) {
            double dist = DroneTrack.distance(st.userLat, st.userLon, d.lat, d.lon);
            msg += " a " + (dist < 1000 ? Math.round(dist / 10) * 10 + " metri" : String.format(Locale.ITALY, "%.1f chilometri", dist / 1000))
                + ", direzione " + HeadingSensor.cardinal((float) DroneTrack.bearing(st.userLat, st.userLon, d.lat, d.lon));
        }
        tts.speak(msg, TextToSpeech.QUEUE_ADD, null, "sky-" + d.key);
    }

    @Override public void onRequestPermissionsResult(int req, @NonNull String[] p, @NonNull int[] res) {
        super.onRequestPermissionsResult(req, p, res);
        boolean all = res.length > 0;
        for (int r : res) all &= r == PackageManager.PERMISSION_GRANTED;
        if (req == REQ_SCAN) {
            // basta il Bluetooth: il permesso Wi-Fi "dispositivi vicini" e' facoltativo
            if (hasAll(RemoteIdScanner.requiredPermissions())) { startScan(true); startLocation(); }
            else {
                wantScan = false;
                Toast.makeText(this, "Senza permessi Bluetooth/posizione non posso ricevere il Remote ID", Toast.LENGTH_LONG).show();
            }
        } else if (req == REQ_MIC) {
            if (all) startMic(true);
            else {
                wantMic = false;
                Toast.makeText(this, "Senza microfono il rilevamento acustico non funziona", Toast.LENGTH_LONG).show();
            }
        }
        refresh();
    }
}
"""

ACOUSTIC_DETECTOR_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.sky.AcousticAnalyzer;
import com.offlinegps.map.sky.AcousticDetector;
import java.util.Locale;

/**
 * ASCOLTO ACUSTICO: riconosce la "firma" sonora delle eliche (fondamentale
 * 70-520 Hz + armoniche stabili) con un'analisi spettrale fatta sul telefono.
 * Nessuna registrazione viene salvata o inviata.
 */
public class AcousticDetectorActivity extends AppCompatActivity {
    private static final int REQ_MIC = 7201;
    private AcousticDetector detector;
    private NeonGaugeView gauge;
    private SpectrogramView spectro;
    private TextView tvVerdict, tvDetails, tvToggle;
    private float peak;
    private long lastBuzz;
    private boolean asked;

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_acoustic);
        detector = new AcousticDetector(this);
        gauge = findViewById(R.id.ac_gauge);
        spectro = findViewById(R.id.ac_spectro);
        tvVerdict = findViewById(R.id.tv_ac_verdict);
        tvDetails = findViewById(R.id.tv_ac_details);
        tvToggle = findViewById(R.id.tv_ac_toggle_label);
        spectro.configure(AcousticAnalyzer.DISPLAY_BINS, AcousticAnalyzer.DISPLAY_MAX_HZ);
        gauge.setLabel("FIRMA DRONE");
        gauge.setCaption("tocca AVVIA e punta il telefono verso il cielo");
        click(R.id.btn_ac_back, v -> finish());
        click(R.id.btn_ac_toggle, v -> { if (detector.isRunning()) stop(); else start(true); });
        click(R.id.btn_ac_report, v -> {
            Intent i = new Intent(this, SkySpotActivity.class);
            i.putExtra(SkySpotActivity.EXTRA_ACOUSTIC, peak);
            i.putExtra(SkySpotActivity.EXTRA_KIND, 1);
            startActivity(i);
        });
        render(null);
    }

    private void click(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    @Override protected void onResume() {
        super.onResume();
        start(false);
    }

    @Override protected void onPause() {
        super.onPause();
        stop();
    }

    private void start(boolean interactive) {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            if (interactive || !asked) {
                asked = true;
                requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC);
            }
            return;
        }
        if (detector.isRunning()) return;
        peak = 0;
        spectro.clear();
        if (!detector.start(this::render)) {
            Toast.makeText(this, detector.lastError, Toast.LENGTH_LONG).show();
            return;
        }
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        gauge.setCaption("microfono " + detector.sourceName);
        render(null);
    }

    private void stop() {
        detector.stop();
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        render(null);
    }

    private void render(AcousticAnalyzer.Result r) {
        boolean on = detector.isRunning();
        if (tvToggle != null) tvToggle.setText(on ? "FERMA ASCOLTO" : "AVVIA ASCOLTO");
        if (r == null) {
            gauge.setValue(0);
            tvVerdict.setText(on ? "IN ASCOLTO..." : "MICROFONO SPENTO");
            tvVerdict.setTextColor(on ? 0xFF00E5FF : 0xFF5A7A99);
            tvDetails.setText(on ? "Servono 2-3 secondi di suono continuo per giudicare."
                : "Tutto avviene sul telefono: l'audio non viene registrato ne' inviato.");
            return;
        }
        spectro.push(r.spectrum, r.f0);
        gauge.setValue(r.score);
        peak = Math.max(peak, r.score);
        String verdict; int col;
        if (r.rmsDb < -70) { verdict = "SILENZIO"; col = 0xFF5A7A99; }
        else if (r.score >= 0.5f) { verdict = "FIRMA COMPATIBILE CON UN DRONE"; col = 0xFFFF1744; }
        else if (r.score >= 0.3f) { verdict = "POSSIBILE DRONE"; col = 0xFFFFD600; }
        else if (r.frameScore > 0.4f) { verdict = "SUONO ARMONICO (non stabile)"; col = 0xFF00E5FF; }
        else { verdict = "NESSUNA FIRMA DA ELICHE"; col = 0xFF00FF88; }
        tvVerdict.setText(verdict);
        tvVerdict.setTextColor(col);
        StringBuilder sb = new StringBuilder();
        sb.append(String.format(Locale.ITALY, "Livello: %.0f dBFS", r.rmsDb));
        if (r.f0 > 0) sb.append(String.format(Locale.ITALY, "  ·  Fondamentale: %.0f Hz  ·  Armoniche: %d", r.f0, r.harmonics));
        sb.append(String.format(Locale.ITALY, "%nStabilita' della firma: %.0f%%  ·  Picco sessione: %.0f%%",
            r.stability * 100, peak * 100));
        tvDetails.setText(sb.toString());
        if (r.score >= 0.5f && System.currentTimeMillis() - lastBuzz > 4000) {
            lastBuzz = System.currentTimeMillis();
            try {
                Vibrator v = (Vibrator) getSystemService(VIBRATOR_SERVICE);
                if (v != null) v.vibrate(VibrationEffect.createOneShot(180, VibrationEffect.DEFAULT_AMPLITUDE));
            } catch (Exception ignored) {}
        }
    }

    @Override public void onRequestPermissionsResult(int req, @NonNull String[] p, @NonNull int[] res) {
        super.onRequestPermissionsResult(req, p, res);
        if (req == REQ_MIC) {
            if (res.length > 0 && res[0] == PackageManager.PERMISSION_GRANTED) start(true);
            else Toast.makeText(this, "Serve il permesso del microfono", Toast.LENGTH_LONG).show();
        }
    }
}
"""

SKY_SPOT_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import com.offlinegps.map.sky.HeadingSensor;
import com.offlinegps.map.sky.SkySpotStore;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * SKYSPOT: diario degli avvistamenti. La posizione viene arrotondata a ~1 km
 * prima di salvarla o condividerla. NON e' un canale di emergenza: per i
 * pericoli c'e' il pulsante che chiama il 112.
 */
public class SkySpotActivity extends AppCompatActivity {
    public static final String EXTRA_REMOTE_ID = "remote_id";
    public static final String EXTRA_ACOUSTIC = "acoustic";
    public static final String EXTRA_KIND = "kind";
    private static final String[] DIRS = {"Non so", "Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ovest", "Ovest", "Nord-Ovest", "Sopra di me"};

    private SkySpotStore store;
    private Spinner spKind, spDir, spHeight, spDur, spCount;
    private EditText etNotes;
    private TextView tvLoc, tvRid;
    private LinearLayout list;
    private HeadingSensor heading;
    private double lat = Double.NaN, lon = Double.NaN;
    private String remoteId = "";
    private float acoustic = -1f;
    private final List<LocationListener> pending = new ArrayList<>();

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_skyspot);
        store = new SkySpotStore(this);
        heading = new HeadingSensor(this);
        spKind = findViewById(R.id.sp_spot_kind);
        spDir = findViewById(R.id.sp_spot_dir);
        spHeight = findViewById(R.id.sp_spot_height);
        spDur = findViewById(R.id.sp_spot_duration);
        spCount = findViewById(R.id.sp_spot_count);
        etNotes = findViewById(R.id.et_spot_notes);
        tvLoc = findViewById(R.id.tv_spot_loc);
        tvRid = findViewById(R.id.tv_spot_rid);
        list = findViewById(R.id.spot_list);
        fill(spKind, SkySpotStore.KINDS);
        fill(spDir, DIRS);
        fill(spHeight, SkySpotStore.HEIGHTS);
        fill(spDur, SkySpotStore.DURATIONS);
        fill(spCount, new String[]{"1", "2", "3", "4", "5", "Piu' di 5"});

        Intent in = getIntent();
        remoteId = in.getStringExtra(EXTRA_REMOTE_ID) != null ? in.getStringExtra(EXTRA_REMOTE_ID) : "";
        acoustic = in.getFloatExtra(EXTRA_ACOUSTIC, -1f);
        int kind = in.getIntExtra(EXTRA_KIND, 0);
        spKind.setSelection(Math.max(0, Math.min(SkySpotStore.KINDS.length - 1, kind)));
        StringBuilder extra = new StringBuilder();
        if (!remoteId.isEmpty()) extra.append("Remote ID allegato: ").append(remoteId);
        if (acoustic >= 0) extra.append(extra.length() > 0 ? "\n" : "")
            .append(String.format(Locale.ITALY, "Indice acustico allegato: %.0f%%", acoustic * 100));
        tvRid.setText(extra.toString());
        tvRid.setVisibility(extra.length() > 0 ? View.VISIBLE : View.GONE);

        click(R.id.btn_spot_back, v -> finish());
        click(R.id.btn_spot_112, v -> call112());
        click(R.id.btn_spot_compass, v -> {
            float hd = heading.current();
            if (Float.isNaN(hd)) {
                Toast.makeText(this, "Bussola non disponibile", Toast.LENGTH_SHORT).show();
                return;
            }
            String c = HeadingSensor.cardinal(hd);
            for (int i = 0; i < DIRS.length; i++) if (DIRS[i].equals(c)) spDir.setSelection(i);
            Toast.makeText(this, String.format(Locale.ITALY, "Direzione: %s (%.0f°)", c, hd), Toast.LENGTH_SHORT).show();
        });
        click(R.id.btn_spot_save, v -> save());
        locate();
        renderList();
    }

    private void fill(Spinner sp, String[] items) {
        ArrayAdapter<String> a = new ArrayAdapter<>(this, R.layout.item_spinner_dark, items);
        a.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        sp.setAdapter(a);
    }

    private void click(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    @Override protected void onResume() { super.onResume(); heading.start(null); }
    @Override protected void onPause() { super.onPause(); heading.stop(); }

    @Override protected void onDestroy() {
        super.onDestroy();
        LocationManager lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        for (LocationListener l : pending) {
            try { lm.removeUpdates(l); } catch (Exception ignored) {}
        }
        pending.clear();
    }

    private void locate() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
            try {
                LocationManager lm = (LocationManager) getSystemService(LOCATION_SERVICE);
                Location best = null;
                for (String p : new String[]{LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER}) {
                    Location l = lm.getLastKnownLocation(p);
                    if (l != null && (best == null || l.getTime() > best.getTime())) best = l;
                }
                if (best != null) { lat = best.getLatitude(); lon = best.getLongitude(); }
                else {
                    // nessuna posizione recente: ne chiede una sola e aggiorna la zona
                    for (String p : new String[]{LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER}) {
                        if (!lm.isProviderEnabled(p)) continue;
                        LocationListener once = new LocationListener() {
                            @Override public void onLocationChanged(@NonNull Location l) {
                                lm.removeUpdates(this);
                                if (!Double.isNaN(lat) || isFinishing()) return;
                                lat = l.getLatitude(); lon = l.getLongitude();
                                showZone();
                            }
                            @Override public void onStatusChanged(String pr, int st, Bundle b) {}
                            @Override public void onProviderEnabled(@NonNull String pr) {}
                            @Override public void onProviderDisabled(@NonNull String pr) {}
                        };
                        pending.add(once);
                        lm.requestLocationUpdates(p, 1000, 0f, once);
                    }
                }
            } catch (SecurityException ignored) {}
        }
        showZone();
    }

    private void showZone() {
        if (Double.isNaN(lat)) tvLoc.setText("Posizione non disponibile: la segnalazione sara' senza zona");
        else tvLoc.setText(String.format(Locale.US,
            "Zona: %.2f, %.2f\nLa posizione esatta NON viene salvata: e' arrotondata a una cella di ~1 km",
            SkySpotStore.anonymize(lat), SkySpotStore.anonymize(lon)));
    }

    private void save() {
        SkySpotStore.Report r = new SkySpotStore.Report();
        r.time = System.currentTimeMillis();
        r.lat = lat; r.lon = lon;            // anonimizzate da store.add()
        r.kind = spKind.getSelectedItemPosition();
        r.height = spHeight.getSelectedItemPosition();
        r.duration = spDur.getSelectedItemPosition();
        r.count = spCount.getSelectedItemPosition() + 1;
        int d = spDir.getSelectedItemPosition();
        r.direction = d > 0 ? DIRS[d] : "";
        r.notes = etNotes.getText().toString().trim();
        r.remoteId = remoteId;
        r.acoustic = acoustic;
        store.add(r);
        etNotes.setText("");
        Toast.makeText(this, "Segnalazione salvata sul telefono", Toast.LENGTH_SHORT).show();
        renderList();
        List<SkySpotStore.Report> all = store.list();
        if (!all.isEmpty()) {
            final SkySpotStore.Report saved = all.get(0);
            new AlertDialog.Builder(this)
                .setTitle("Segnalazione salvata")
                .setMessage("Vuoi condividerla (messaggio, email, gruppo)?\n\nRicorda: NON sostituisce il 112.")
                .setPositiveButton("Condividi", (dlg, w) -> SkyUi.share(this, "Avvistamento", saved.shareText()))
                .setNegativeButton("No", null)
                .show();
        }
    }

    private void renderList() {
        list.removeAllViews();
        List<SkySpotStore.Report> all = store.list();
        if (all.isEmpty()) {
            TextView tv = new TextView(this);
            tv.setText("Nessuna segnalazione salvata.");
            tv.setTextColor(0xFF5A7A99);
            tv.setPadding(SkyUi.dp(this, 6), SkyUi.dp(this, 6), 0, SkyUi.dp(this, 6));
            list.addView(tv);
            return;
        }
        for (int i = 0; i < all.size(); i++) {
            final int idx = i;
            final SkySpotStore.Report r = all.get(i);
            View card = SkyUi.card(this, 0xFF00E5FF, r.when(), r.summary(), "Zona " + r.where(),
                r.notes.isEmpty() ? "" : "Note: " + r.notes);
            card.setOnClickListener(v -> new AlertDialog.Builder(this)
                .setTitle(r.when())
                .setMessage(r.shareText())
                .setPositiveButton("Condividi", (dlg, w) -> SkyUi.share(this, "Avvistamento", r.shareText()))
                .setNeutralButton("Elimina", (dlg, w) -> { store.delete(idx); renderList(); })
                .setNegativeButton("Chiudi", null)
                .show());
            UiFx.addSpring(card);
            list.addView(card);
        }
    }

    private void call112() {
        // apre il tastierino col numero gia' scritto: la chiamata la fa l'utente
        try { startActivity(new Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))); }
        catch (Exception e) { Toast.makeText(this, "Componi 112", Toast.LENGTH_LONG).show(); }
    }
}
"""

SIGHTING_CHECK_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.Spinner;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.R;
import java.util.Arrays;
import java.util.Locale;

/**
 * "E' DAVVERO UN DRONE?": sei domande su luce, movimento, rumore e durata
 * stimano se si tratta di un drone o (molto piu' spesso) di un aereo, un
 * satellite, un pianeta, una lanterna... Serve a evitare falsi allarmi.
 */
public class SightingCheckActivity extends AppCompatActivity {
    static final String[] NAMES = {"Drone", "Aereo di linea", "Elicottero", "Satellite / Stazione Spaziale",
        "Treno di satelliti Starlink", "Stella o pianeta (es. Venere)", "Lanterna cinese / palloncino",
        "Uccello o insetto vicino", "Meteora (stella cadente)"};
    static final String[] WHY = {
        "Ronzio acuto, si ferma a mezz'aria, cambia direzione e quota. Prova lo scanner Remote ID e l'ascolto acustico.",
        "Luci che lampeggiano con ritmo regolare (rossa a sinistra, verde a destra, strobo bianco), rotta dritta, rombo basso che arriva in ritardo.",
        "Battito ritmico delle pale (flap-flap), puo' restare fermo, luci lampeggianti, vola basso.",
        "Punto bianco fisso che attraversa il cielo in 2-6 minuti senza rumore, poco dopo il tramonto o prima dell'alba. La Stazione Spaziale e' piu' luminosa di ogni stella.",
        "Fila ordinata di punti luminosi che avanzano in linea: satelliti lanciati da pochi giorni.",
        "Resta 'fermo' per ore (si sposta solo con la rotazione della Terra). Venere e' il punto piu' luminoso al tramonto o all'alba; vicino all'orizzonte le stelle scintillano e sembrano cambiare colore.",
        "Luce arancione tremolante che sale lentamente spinta dal vento e poi si spegne.",
        "Vicino e veloce, battito d'ali: di giorno con il sole controluce sembra un oggetto scuro che vola.",
        "Striscia luminosa velocissima che dura un istante.",
    };
    static final String[][] QUESTIONS = {
        {"Cosa hai notato?", "Una luce", "Un oggetto con una forma", "Solo un rumore", "Piu' luci in fila"},
        {"Com'e' la luce?", "Nessuna luce / e' giorno", "Fissa, bianca", "Lampeggia regolare (rosso/verde/bianco)",
            "Scintilla e cambia colore", "Arancione tremolante"},
        {"Come si muove?", "E' ferma", "Lenta e costante in linea retta", "Velocissima in linea retta",
            "Si ferma, gira, sale e scende", "Sale piano portata dal vento"},
        {"Che rumore fa?", "Nessun rumore", "Ronzio acuto (zanzara/sciame)", "Rombo basso e lontano",
            "Battito ritmico (flap-flap)", "Non so / troppo rumore intorno"},
        {"Quanto dura?", "Pochi secondi", "Alcuni minuti, poi sparisce", "Ore, quasi nello stesso punto", "Non so"},
        {"Quando?", "Di giorno", "Al tramonto o all'alba", "Di notte"},
    };
    /** Punti per [domanda][risposta][candidato]. */
    static final int[][][] SCORE = {
        {   {1, 2, 1, 3, 0, 3, 2, 0, 2}, {3, 1, 2, 0, 0, 0, 0, 3, 0},
            {3, 1, 2, 0, 0, 0, 0, 0, 0}, {1, 0, 0, 0, 6, 0, 2, 0, 0} },
        {   {1, 1, 1, 0, 0, 0, 0, 2, 0}, {1, 0, 0, 3, 2, 3, 0, 0, 1}, {2, 4, 3, 0, 0, 0, 0, 0, 0},
            {1, 0, 0, 0, 0, 5, 0, 0, 0}, {0, 0, 0, 0, 0, 0, 5, 0, 0} },
        {   {2, 0, 1, 0, 0, 4, 1, 0, 0}, {0, 3, 0, 4, 2, 0, 1, 0, 0}, {0, 1, 0, 0, 0, 0, 0, 1, 5},
            {5, 0, 2, 0, 0, 0, 0, 2, 0}, {0, 0, 0, 0, 0, 0, 5, 0, 0} },
        {   {-1, 1, 0, 3, 3, 3, 2, 1, 2}, {6, 0, 0, 0, 0, 0, 0, 1, 0}, {0, 4, 1, 0, 0, 0, 0, 0, 0},
            {-1, 0, 9, 0, 0, 0, 0, 0, 0}, {0, 0, 0, 0, 0, 0, 0, 0, 0} },
        {   {0, 0, 0, 0, 0, 0, 0, 1, 4}, {2, 2, 1, 3, 2, 0, 2, 0, 0}, {0, 0, 0, 0, 0, 5, 0, 0, 0},
            {0, 0, 0, 0, 0, 0, 0, 0, 0} },
        {   {2, 1, 1, -3, -3, -3, -1, 2, -2}, {0, 0, 0, 2, 3, 2, 0, 0, 0}, {0, 0, 0, 1, 0, 1, 1, 0, 1} },
    };
    private static final int[] SPINNERS = {R.id.sp_chk_q1, R.id.sp_chk_q2, R.id.sp_chk_q3,
        R.id.sp_chk_q4, R.id.sp_chk_q5, R.id.sp_chk_q6};

    private final Spinner[] sp = new Spinner[SPINNERS.length];
    private LinearLayout results;

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_sighting_check);
        results = findViewById(R.id.chk_results);
        AdapterView.OnItemSelectedListener l = new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) { evaluate(); }
            @Override public void onNothingSelected(AdapterView<?> p) {}
        };
        for (int q = 0; q < SPINNERS.length; q++) {
            sp[q] = findViewById(SPINNERS[q]);
            ArrayAdapter<String> a = new ArrayAdapter<>(this, R.layout.item_spinner_dark,
                Arrays.copyOfRange(QUESTIONS[q], 1, QUESTIONS[q].length));
            a.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
            sp[q].setAdapter(a);
            sp[q].setOnItemSelectedListener(l);
        }
        View back = findViewById(R.id.btn_chk_back);
        if (back != null) back.setOnClickListener(v -> finish());
        View sky = findViewById(R.id.btn_chk_sky);
        if (sky != null) sky.setOnClickListener(v -> startActivity(new Intent(this, SkyWatchActivity.class)));
        evaluate();
    }

    /** Probabilita' (softmax dei punteggi) per ogni candidato. */
    static double[] probabilities(int[] answers) {
        double[] s = new double[NAMES.length];
        for (int q = 0; q < answers.length && q < SCORE.length; q++) {
            int a = Math.max(0, Math.min(SCORE[q].length - 1, answers[q]));
            for (int c = 0; c < NAMES.length; c++) s[c] += SCORE[q][a][c];
        }
        double max = Double.NEGATIVE_INFINITY, sum = 0;
        for (double v : s) max = Math.max(max, v);
        double[] p = new double[s.length];
        for (int c = 0; c < s.length; c++) { p[c] = Math.exp((s[c] - max) / 2.0); sum += p[c]; }
        for (int c = 0; c < s.length; c++) p[c] /= sum;
        return p;
    }

    private void evaluate() {
        int[] ans = new int[sp.length];
        for (int q = 0; q < sp.length; q++) ans[q] = sp[q] != null ? Math.max(0, sp[q].getSelectedItemPosition()) : 0;
        double[] p = probabilities(ans);
        Integer[] order = new Integer[p.length];
        for (int i = 0; i < order.length; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> Double.compare(p[b], p[a]));
        results.removeAllViews();
        for (int k = 0; k < 3; k++) {
            int c = order[k];
            int accent = c == 0 ? 0xFFFF3D71 : (k == 0 ? 0xFF00FF88 : 0xFF00E5FF);
            results.addView(SkyUi.card(this, accent,
                String.format(Locale.ITALY, "%d. %s  —  %.0f%%", k + 1, NAMES[c], p[c] * 100), WHY[c]));
        }
    }
}
"""

# ------------------------------------------------------------------
#  GRAFICA v4.0 — palette, icone, sfondi "vetro" con ripple, chip,
#  animazioni di transizione e layout delle nuove schermate.
# ------------------------------------------------------------------
V4_ACCENTS = {
    "cyan":   "00E5FF",
    "green":  "00FF88",
    "yellow": "FFD600",
    "red":    "FF1744",
    "pink":   "FF3D71",
    "violet": "B388FF",
    "orange": "FF6B35",
}

_XML_HEAD = '<?xml version="1.0" encoding="utf-8"?>\n'
_NS = 'xmlns:android="http://schemas.android.com/apk/res/android"'

def _v4_tile_bg(hexcol, radius="22dp"):
    """Riquadro vetro: gradiente profondo + alone colorato in alto + bordo + riflesso, con ripple."""
    return (_XML_HEAD +
        '<ripple ' + _NS + ' android:color="#40' + hexcol + '">\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="315"\n'
        '                android:startColor="#1A2740" android:endColor="#0A1220"/>\n'
        '            <corners android:radius="' + radius + '"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="radial" android:gradientRadius="320"\n'
        '                android:centerX="0.1" android:centerY="0.0"\n'
        '                android:startColor="#30' + hexcol + '" android:endColor="#00' + hexcol + '"/>\n'
        '            <corners android:radius="' + radius + '"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:bottom="40dp" android:left="1dp" android:right="1dp" android:top="1dp">\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="270"\n'
        '                android:startColor="#14FFFFFF" android:endColor="#00FFFFFF"/>\n'
        '            <corners android:radius="' + radius + '"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#00000000"/>\n'
        '            <stroke android:width="1dp" android:color="#55' + hexcol + '"/>\n'
        '            <corners android:radius="' + radius + '"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</ripple>')

def _v4_disc(hexcol):
    return (_XML_HEAD +
        '<shape ' + _NS + ' android:shape="oval">\n'
        '    <solid android:color="#22' + hexcol + '"/>\n'
        '    <stroke android:width="1dp" android:color="#66' + hexcol + '"/>\n'
        '</shape>')

def _v4_chip(fill, stroke):
    return (_XML_HEAD +
        '<shape ' + _NS + ' android:shape="rectangle">\n'
        '    <solid android:color="' + fill + '"/>\n'
        '    <stroke android:width="1dp" android:color="' + stroke + '"/>\n'
        '    <corners android:radius="14dp"/>\n'
        '</shape>')

def _v4_icon(paths, stroke_paths=""):
    """Icona vettoriale bianca 24x24 (colorata poi con android:tint)."""
    body = "".join('    <path android:fillColor="#FFFFFFFF" android:pathData="' + p + '"/>\n' for p in paths)
    if stroke_paths:
        body += ('    <path android:strokeColor="#FFFFFFFF" android:strokeWidth="1.8" '
                 'android:strokeLineCap="round" android:fillColor="#00000000" android:pathData="' + stroke_paths + '"/>\n')
    return (_XML_HEAD +
        '<vector ' + _NS + '\n'
        '    android:width="24dp" android:height="24dp"\n'
        '    android:viewportWidth="24" android:viewportHeight="24">\n' + body + '</vector>')

V4_ICONS = {
    "ic_v4_nav":      _v4_icon(["M12,2L4.5,20.29l0.71,0.71L12,18l6.79,3 0.71,-0.71z"]),
    "ic_v4_map":      _v4_icon(["M20.5,3l-0.16,0.03L15,5.1 9,3 3.36,4.9c-0.21,0.07 -0.36,0.25 -0.36,0.48V20.5c0,0.28 0.22,0.5 0.5,0.5l0.16,-0.03L9,18.9l6,2.1 5.64,-1.9c0.21,-0.07 0.36,-0.25 0.36,-0.48V3.5c0,-0.28 -0.22,-0.5 -0.5,-0.5zM15,19l-6,-2.11V5l6,2.11V19z"]),
    "ic_v4_tools":    _v4_icon(["M22.7,19l-9.1,-9.1c0.9,-2.3 0.4,-5 -1.5,-6.9 -2,-2 -5,-2.4 -7.4,-1.3L9,6 6,9 1.6,4.7C0.4,7.1 0.9,10.1 2.9,12.1c1.9,1.9 4.6,2.4 6.9,1.5l9.1,9.1c0.4,0.4 1,0.4 1.4,0l2.3,-2.3c0.5,-0.4 0.5,-1.1 0.1,-1.4z"]),
    "ic_v4_fire":     _v4_icon(["M13.5,0.67s0.74,2.65 0.74,4.8c0,2.06 -1.35,3.73 -3.41,3.73 -2.07,0 -3.63,-1.67 -3.63,-3.73l0.03,-0.36C5.21,7.51 4,10.62 4,14c0,4.42 3.58,8 8,8s8,-3.58 8,-8C20,8.61 17.41,3.8 13.5,0.67zM11.71,19c-1.78,0 -3.22,-1.4 -3.22,-3.14 0,-1.62 1.05,-2.76 2.81,-3.12 1.77,-0.36 3.6,-1.21 4.62,-2.58 0.39,1.29 0.59,2.65 0.59,4.04 0,2.65 -2.15,4.8 -4.8,4.8z"]),
    "ic_v4_chat":     _v4_icon(["M20,2H4c-1.1,0 -1.99,0.9 -1.99,2L2,22l4,-4h14c1.1,0 2,-0.9 2,-2V4c0,-1.1 -0.9,-2 -2,-2zM6,9h12v2H6V9zm8,5H6v-2h8v2zm4,-6H6V6h12v2z"]),
    "ic_v4_sos":      _v4_icon(["M1,21h22L12,2 1,21zm12,-3h-2v-2h2v2zm0,-4h-2v-4h2v4z"]),
    "ic_v4_download": _v4_icon(["M19,9h-4V3H9v6H5l7,7 7,-7zM5,18v2h14v-2H5z"]),
    "ic_v4_pin":      _v4_icon(["M12,2C8.13,2 5,5.13 5,9c0,5.25 7,13 7,13s7,-7.75 7,-13c0,-3.87 -3.13,-7 -7,-7zm0,9.5c-1.38,0 -2.5,-1.12 -2.5,-2.5s1.12,-2.5 2.5,-2.5 2.5,1.12 2.5,2.5 -1.12,2.5 -2.5,2.5z"]),
    "ic_v4_stats":    _v4_icon(["M5,9.2h3V19H5zM10.6,5h2.8v14h-2.8zm5.6,8H19v6h-2.8z"]),
    "ic_v4_radar":    _v4_icon(["M12,10.2a1.8,1.8 0 1,0 0.01,0z"],
                               "M12,3a9,9 0 1,0 9,9 M12,7a5,5 0 1,0 5,5 M12,12L19,5"),
    "ic_v4_mic":      _v4_icon(["M12,14c1.66,0 2.99,-1.34 2.99,-3L15,5c0,-1.66 -1.34,-3 -3,-3S9,3.34 9,5v6c0,1.66 1.34,3 3,3zm5.3,-3c0,3 -2.54,5.1 -5.3,5.1S6.7,14 6.7,11H5c0,3.41 2.72,6.23 6,6.72V21h2v-3.28c3.28,-0.48 6,-3.3 6,-6.72h-1.7z"]),
    "ic_v4_flag":     _v4_icon(["M14.4,6L14,4H5v17h2v-7h5.6l0.4,2h7V6z"]),
    "ic_v4_help":     _v4_icon(["M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,17h-2v-2h2v2zm2.07,-7.75l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"]),
    "ic_v4_shield":   _v4_icon(["M12,1L3,5v6c0,5.55 3.84,10.74 9,12 5.16,-1.26 9,-6.45 9,-12V5l-9,-4z"]),
    "ic_v4_drone":    _v4_icon(["M6,3.2a2.8,2.8 0 1,0 0.01,0z", "M18,3.2a2.8,2.8 0 1,0 0.01,0z",
                                "M6,15.2a2.8,2.8 0 1,0 0.01,0z", "M18,15.2a2.8,2.8 0 1,0 0.01,0z",
                                "M9.5,9.5h5v5h-5z"],
                               "M6,6L18,18 M18,6L6,18"),
    "ic_v4_play":     _v4_icon(["M8,5v14l11,-7z"]),
    "ic_v4_back":     _v4_icon(["M15.41,7.41L14,6l-6,6 6,6 1.41,-1.41L10.83,12z"]),
    "ic_v4_globe":    _v4_icon(["M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm-1,17.93c-3.95,-0.49 -7,-3.85 -7,-7.93 0,-0.62 0.08,-1.21 0.21,-1.79L9,15v1c0,1.1 0.9,2 2,2v1.93zm6.9,-2.54c-0.26,-0.81 -1,-1.39 -1.9,-1.39h-1v-3c0,-0.55 -0.45,-1 -1,-1H8v-2h2c0.55,0 1,-0.45 1,-1V7h2c1.1,0 2,-0.9 2,-2v-0.41c2.93,1.19 5,4.06 5,7.41 0,2.08 -0.8,3.97 -2.1,5.39z"]),
}

V4_DRAWABLES = {}
for _name, _hex in V4_ACCENTS.items():
    V4_DRAWABLES["bg_tile_" + _name] = _v4_tile_bg(_hex)
    V4_DRAWABLES["bg_disc_" + _name] = _v4_disc(_hex)
V4_DRAWABLES.update({
    # scheda vetro neutra (liste, schede droni, segnalazioni)
    "bg_tile_glass": _v4_tile_bg("8FB3D0", "18dp"),
    # scheda "olografica" del radar (bordo ciano luminoso)
    "bg_card_holo":
        _XML_HEAD +
        '<layer-list ' + _NS + '>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="300"\n'
        '                android:startColor="#0F2238" android:endColor="#060D1A"/>\n'
        '            <corners android:radius="26dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="radial" android:gradientRadius="420"\n'
        '                android:centerX="0.75" android:centerY="0.5"\n'
        '                android:startColor="#2200E5FF" android:endColor="#0000E5FF"/>\n'
        '            <corners android:radius="26dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#00000000"/>\n'
        '            <stroke android:width="1.5dp" android:color="#7700E5FF"/>\n'
        '            <corners android:radius="26dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</layer-list>',
    # riquadro informativo (testi di stato e avvertenze)
    "bg_hint":
        _XML_HEAD +
        '<shape ' + _NS + ' android:shape="rectangle">\n'
        '    <solid android:color="#B30B1424"/>\n'
        '    <stroke android:width="1dp" android:color="#2200E5FF"/>\n'
        '    <corners android:radius="16dp"/>\n'
        '</shape>',
    "bg_hint_red":
        _XML_HEAD +
        '<shape ' + _NS + ' android:shape="rectangle">\n'
        '    <solid android:color="#B31F0812"/>\n'
        '    <stroke android:width="1dp" android:color="#88FF1744"/>\n'
        '    <corners android:radius="16dp"/>\n'
        '</shape>',
    # campo di testo / menu a tendina
    "bg_input":
        _XML_HEAD +
        '<shape ' + _NS + ' android:shape="rectangle">\n'
        '    <solid android:color="#0F1A2B"/>\n'
        '    <stroke android:width="1dp" android:color="#4400E5FF"/>\n'
        '    <corners android:radius="14dp"/>\n'
        '</shape>',
    # pulsante "indietro" a pillola
    "bg_pill_back":
        _XML_HEAD +
        '<ripple ' + _NS + ' android:color="#4000E5FF">\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#1AFFFFFF"/>\n'
        '            <stroke android:width="1dp" android:color="#33FFFFFF"/>\n'
        '            <corners android:radius="22dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</ripple>',
    "bg_chip_on":    _v4_chip("#1A00FF88", "#6600FF88"),
    "bg_chip_warn":  _v4_chip("#1AFFD600", "#66FFD600"),
    "bg_chip_alert": _v4_chip("#22FF1744", "#99FF1744"),
    "bg_chip_off":   _v4_chip("#12FFFFFF", "#33FFFFFF"),
    "bg_chip_violet": _v4_chip("#26B388FF", "#88B388FF"),
})
V4_DRAWABLES.update(V4_ICONS)

# Transizioni fra schermate: la nuova scivola da destra ingrandendosi,
# la vecchia arretra e si scurisce (effetto profondita').
def _v4_anim(fx, tx, fa, ta, fs, ts, interp="decelerate_cubic", dur=300):
    return (_XML_HEAD +
        '<set ' + _NS + '\n'
        '    android:interpolator="@android:interpolator/' + interp + '"\n'
        '    android:duration="' + str(dur) + '" android:shareInterpolator="true">\n'
        '    <translate android:fromXDelta="' + fx + '" android:toXDelta="' + tx + '"/>\n'
        '    <alpha android:fromAlpha="' + fa + '" android:toAlpha="' + ta + '"/>\n'
        '    <scale android:fromXScale="' + fs + '" android:toXScale="' + ts + '"\n'
        '        android:fromYScale="' + fs + '" android:toYScale="' + ts + '"\n'
        '        android:pivotX="50%" android:pivotY="50%"/>\n'
        '</set>')

V4_ANIMS = {
    "fx_open_enter":  _v4_anim("12%", "0%", "0.0", "1.0", "0.94", "1.0"),
    "fx_open_exit":   _v4_anim("0%", "-6%", "1.0", "0.35", "1.0", "0.94"),
    "fx_close_enter": _v4_anim("-6%", "0%", "0.35", "1.0", "0.94", "1.0"),
    "fx_close_exit":  _v4_anim("0%", "12%", "1.0", "0.0", "1.0", "0.94", "accelerate_cubic", 260),
}

# ---------------------------------------------------------------- mattoni layout
def _v4_header(back_id, title_text, subtitle, accent="#00E5FF", right_chip_id=None, right_text=""):
    right = ""
    if right_chip_id:
        right = ('        <TextView android:id="@+id/' + right_chip_id + '"\n'
                 '            android:layout_width="wrap_content" android:layout_height="30dp"\n'
                 '            android:gravity="center" android:paddingStart="12dp" android:paddingEnd="12dp"\n'
                 '            android:text="' + right_text + '" android:textSize="11sp" android:textStyle="bold"\n'
                 '            android:textColor="#8FB3D0" android:background="@drawable/bg_chip_off"\n'
                 '            android:clickable="true" android:focusable="true"/>\n')
    return ('    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
            '        android:orientation="horizontal" android:gravity="center_vertical"\n'
            '        android:layout_marginBottom="14dp">\n'
            '        <ImageView android:id="@+id/' + back_id + '"\n'
            '            android:layout_width="44dp" android:layout_height="44dp" android:padding="10dp"\n'
            '            android:src="@drawable/ic_v4_back" android:tint="#E8F4FD"\n'
            '            android:background="@drawable/bg_pill_back" android:clickable="true"\n'
            '            android:focusable="true" android:contentDescription="Indietro"/>\n'
            '        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"\n'
            '            android:layout_weight="1" android:orientation="vertical" android:layout_marginStart="14dp">\n'
            '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
            '                android:text="' + title_text + '" android:textColor="' + accent + '"\n'
            '                android:textSize="20sp" android:textStyle="bold" android:letterSpacing="0.06"\n'
            '                android:fontFamily="sans-serif-condensed"\n'
            '                android:shadowColor="' + accent + '" android:shadowRadius="14"/>\n'
            '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
            '                android:text="' + subtitle + '" android:textColor="#5A7A99" android:textSize="11.5sp"/>\n'
            '        </LinearLayout>\n' + right +
            '    </LinearLayout>\n')

def _v4_tile(vid, icon, title_text, sub, accent, height="112dp", end_margin=True, title_id=None):
    hexcol = V4_ACCENTS[accent]
    tid = (' android:id="@+id/' + title_id + '"') if title_id else ""
    sub_xml = ""
    if sub:
        sub_xml = ('        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
                   '            android:text="' + sub + '" android:textColor="#8FB3D0" android:textSize="11sp"\n'
                   '            android:maxLines="2" android:ellipsize="end" android:layout_marginTop="2dp"/>\n')
    return ('    <LinearLayout android:id="@+id/' + vid + '"\n'
            '        android:layout_width="0dp" android:layout_height="' + height + '" android:layout_weight="1"\n'
            '        android:orientation="vertical" android:gravity="center_vertical" android:padding="14dp"\n'
            '        android:background="@drawable/bg_tile_' + accent + '" android:elevation="6dp"\n'
            '        android:clickable="true" android:focusable="true"' +
            ('\n        android:layout_marginEnd="12dp"' if end_margin else '') + '>\n'
            '        <ImageView android:layout_width="36dp" android:layout_height="36dp" android:padding="7dp"\n'
            '            android:src="@drawable/' + icon + '" android:tint="#' + hexcol + '"\n'
            '            android:background="@drawable/bg_disc_' + accent + '" android:contentDescription="' + title_text + '"/>\n'
            '        <TextView' + tid + ' android:layout_width="match_parent" android:layout_height="wrap_content"\n'
            '            android:text="' + title_text + '" android:textColor="#E8F4FD" android:textSize="14sp"\n'
            '            android:textStyle="bold" android:fontFamily="sans-serif-condensed"\n'
            '            android:letterSpacing="0.03" android:layout_marginTop="10dp" android:maxLines="1"\n'
            '            android:ellipsize="end"/>\n' + sub_xml +
            '    </LinearLayout>\n')

def _v4_row(*tiles, margin="12dp"):
    return ('<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
            '    android:orientation="horizontal" android:layout_marginBottom="' + margin + '">\n'
            + "".join(tiles) + '</LinearLayout>\n')

def _v4_section(text):
    return ('<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
            '    android:text="' + text + '" android:textColor="#00E5FF" android:textSize="12sp"\n'
            '    android:letterSpacing="0.18" android:textStyle="bold" android:layout_marginTop="10dp"\n'
            '    android:layout_marginBottom="10dp" android:layout_marginStart="4dp"/>\n')

def _v4_hint(vid, text, red=False, extra=""):
    idattr = ('android:id="@+id/' + vid + '" ') if vid else ""
    return ('<TextView ' + idattr + 'android:layout_width="match_parent" android:layout_height="wrap_content"\n'
            '    android:text="' + text + '" android:textColor="' + ("#FFB3C0" if red else "#CFE3F5") + '"\n'
            '    android:textSize="12.5sp" android:lineSpacingMultiplier="1.3" android:padding="14dp"\n'
            '    android:background="@drawable/' + ("bg_hint_red" if red else "bg_hint") + '"\n'
            '    android:layout_marginBottom="12dp"' + extra + '/>\n')

def _v4_chip_view(vid, text, end_margin=True):
    return ('    <TextView android:id="@+id/' + vid + '"\n'
            '        android:layout_width="0dp" android:layout_height="32dp" android:layout_weight="1"\n'
            '        android:gravity="center" android:text="' + text + '" android:textSize="10sp"\n'
            '        android:textStyle="bold" android:textColor="#8FB3D0" android:maxLines="1"\n'
            '        android:background="@drawable/bg_chip_off" android:clickable="true" android:focusable="true"'
            + ('\n        android:layout_marginEnd="6dp"' if end_margin else '') + '/>\n')

def _v4_label(text):
    return ('<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
            '    android:text="' + text + '" android:textColor="#8FB3D0" android:textSize="12sp"\n'
            '    android:layout_marginBottom="6dp" android:layout_marginStart="4dp"/>\n')

def _v4_spinner(vid):
    return ('<Spinner android:id="@+id/' + vid + '"\n'
            '    android:layout_width="match_parent" android:layout_height="50dp"\n'
            '    android:background="@drawable/bg_input" android:popupBackground="#141E2E"\n'
            '    android:paddingStart="6dp" android:layout_marginBottom="14dp"/>\n')

def _v4_screen(inner, column_id, aurora=True):
    """Schermata: aurora animata dietro e colonna a scorrimento davanti."""
    bg = ('    <com.offlinegps.map.ui.AuroraView android:layout_width="match_parent"\n'
          '        android:layout_height="match_parent"/>\n') if aurora else ""
    return (_XML_HEAD +
        '<FrameLayout ' + _NS + '\n'
        '    android:layout_width="match_parent" android:layout_height="match_parent"\n'
        '    android:background="#050A14">\n' + bg +
        '<ScrollView android:layout_width="match_parent" android:layout_height="match_parent"\n'
        '    android:overScrollMode="never">\n'
        '<LinearLayout android:id="@+id/' + column_id + '"\n'
        '    android:layout_width="match_parent" android:layout_height="wrap_content"\n'
        '    android:orientation="vertical" android:paddingStart="16dp" android:paddingEnd="16dp"\n'
        '    android:paddingTop="18dp" android:paddingBottom="28dp">\n'
        + inner +
        '</LinearLayout></ScrollView></FrameLayout>')

# ---------------------------------------------------------------- HOME v4.0
LAYOUT_MAIN = (_XML_HEAD +
    '<FrameLayout ' + _NS + '\n'
    '    android:layout_width="match_parent" android:layout_height="match_parent"\n'
    '    android:background="#050A14">\n'
    '    <com.offlinegps.map.ui.AuroraView android:id="@+id/home_aurora"\n'
    '        android:layout_width="match_parent" android:layout_height="match_parent"/>\n'
    '<ScrollView android:layout_width="match_parent" android:layout_height="match_parent"\n'
    '    android:overScrollMode="never">\n'
    '<LinearLayout android:id="@+id/home_column" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:orientation="vertical"\n'
    '    android:paddingStart="18dp" android:paddingEnd="18dp" android:paddingTop="22dp"\n'
    '    android:paddingBottom="28dp">\n'
    # intestazione: logo con anello, saluto, titolo e orologio
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:orientation="horizontal" android:gravity="center_vertical">\n'
    '        <FrameLayout android:layout_width="58dp" android:layout_height="58dp">\n'
    '            <ImageView android:layout_width="58dp" android:layout_height="58dp"\n'
    '                android:src="@drawable/ic_splash_ring" android:contentDescription="Anello"/>\n'
    '            <ImageView android:layout_width="38dp" android:layout_height="38dp"\n'
    '                android:layout_gravity="center" android:src="@drawable/ic_gps"\n'
    '                android:contentDescription="Logo"/>\n'
    '        </FrameLayout>\n'
    '        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"\n'
    '            android:layout_weight="1" android:orientation="vertical" android:layout_marginStart="14dp">\n'
    '            <TextView android:id="@+id/tv_home_greet" android:layout_width="wrap_content"\n'
    '                android:layout_height="wrap_content" android:text="Ciao"\n'
    '                android:textColor="#8FB3D0" android:textSize="13sp"/>\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:text="OfflineGPS 3D" android:textColor="#E8F4FD" android:textSize="27sp"\n'
    '                android:textStyle="bold" android:fontFamily="sans-serif-condensed"\n'
    '                android:shadowColor="#00E5FF" android:shadowRadius="18"/>\n'
    '        </LinearLayout>\n'
    '        <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '            android:orientation="vertical" android:gravity="end">\n'
    '            <TextView android:id="@+id/tv_home_clock" android:layout_width="wrap_content"\n'
    '                android:layout_height="wrap_content" android:text="--:--" android:textColor="#00E5FF"\n'
    '                android:textSize="22sp" android:textStyle="bold" android:fontFamily="monospace"/>\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:text="v4.0 · OFFLINE" android:textColor="#5A7A99" android:textSize="10sp"\n'
    '                android:letterSpacing="0.12"/>\n'
    '        </LinearLayout>\n'
    '    </LinearLayout>\n'
    # chip di stato
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:orientation="horizontal" android:layout_marginTop="16dp">\n'
    + _v4_chip_view("chip_gps", "GPS")
    + _v4_chip_view("chip_map", "MAPPA")
    + _v4_chip_view("chip_routing", "ROUTING")
    + _v4_chip_view("chip_service", "TRACCIA", end_margin=False) +
    '    </LinearLayout>\n'
    # scheda in evidenza: SENTINELLA CIELO con radar 3D vivo
    '    <FrameLayout android:id="@+id/btn_sky_watch"\n'
    '        android:layout_width="match_parent" android:layout_height="212dp"\n'
    '        android:layout_marginTop="16dp" android:background="@drawable/bg_card_holo"\n'
    '        android:clickable="true" android:focusable="true" android:elevation="10dp">\n'
    '        <com.offlinegps.map.ui.SkyRadarView android:id="@+id/home_radar"\n'
    '            android:layout_width="190dp" android:layout_height="match_parent"\n'
    '            android:layout_gravity="end"/>\n'
    '        <LinearLayout android:layout_width="match_parent" android:layout_height="match_parent"\n'
    '            android:orientation="vertical" android:padding="18dp">\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="24dp"\n'
    '                android:gravity="center" android:paddingStart="10dp" android:paddingEnd="10dp"\n'
    '                android:text="NUOVO · v4.0" android:textColor="#D9C7FF" android:textSize="10sp"\n'
    '                android:textStyle="bold" android:letterSpacing="0.1"\n'
    '                android:background="@drawable/bg_chip_violet"/>\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:text="SENTINELLA\\nCIELO" android:textColor="#E8F4FD" android:textSize="23sp"\n'
    '                android:textStyle="bold" android:fontFamily="sans-serif-condensed"\n'
    '                android:layout_marginTop="10dp" android:lineSpacingMultiplier="0.95"\n'
    '                android:shadowColor="#00E5FF" android:shadowRadius="16"/>\n'
    '            <TextView android:layout_width="160dp" android:layout_height="wrap_content"\n'
    '                android:text="Radar droni passivo: Remote ID + ascolto eliche"\n'
    '                android:textColor="#8FB3D0" android:textSize="12sp" android:layout_marginTop="4dp"/>\n'
    '            <View android:layout_width="1dp" android:layout_height="0dp" android:layout_weight="1"/>\n'
    '            <TextView android:id="@+id/tv_home_sky" android:layout_width="170dp"\n'
    '                android:layout_height="wrap_content" android:text="Tocca per scansionare"\n'
    '                android:textColor="#8FB3D0" android:textSize="11.5sp" android:textStyle="bold"/>\n'
    '        </LinearLayout>\n'
    '    </FrameLayout>\n'
    # azioni principali
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:orientation="horizontal" android:layout_marginTop="14dp">\n'
    + _v4_tile("btn_navigate", "ic_v4_nav", "NAVIGA", "Percorso offline con voce", "green", "122dp")
    + _v4_tile("btn_open_map", "ic_v4_map", "MAPPA 3D", "Edifici 3D, inclina e ruota", "cyan", "122dp", end_margin=False) +
    '    </LinearLayout>\n'
    '    <TextView android:id="@+id/tv_status" android:layout_width="match_parent"\n'
    '        android:layout_height="wrap_content" android:layout_marginTop="12dp"\n'
    '        android:padding="12dp" android:background="@drawable/bg_hint"\n'
    '        android:textColor="#8FB3D0" android:textSize="12sp"/>\n'
    + _v4_section("STRUMENTI E SICUREZZA")
    + _v4_row(_v4_tile("btn_tools", "ic_v4_tools", "STRUMENTI", "30+ strumenti outdoor", "yellow"),
              _v4_tile("btn_survival", "ic_v4_fire", "SOPRAVVIVENZA", "Kit completo offline", "orange", end_margin=False))
    + _v4_row(_v4_tile("btn_emergency", "ic_v4_sos", "EMERGENZA SOS", "112, posizione, segnali", "red"),
              _v4_tile("btn_chat", "ic_v4_chat", "CHAT OFFLINE", "Bluetooth mesh", "green", end_margin=False))
    + _v4_row(_v4_tile("btn_home_acoustic", "ic_v4_mic", "ASCOLTO DRONI", "Riconosce le eliche", "pink"),
              _v4_tile("btn_home_check", "ic_v4_help", "È UN DRONE?", "Aereo, satellite, Venere?", "violet", end_margin=False))
    + _v4_section("DATI")
    + _v4_row(_v4_tile("btn_download", "ic_v4_download", "DOWNLOAD", "", "cyan", "96dp"),
              _v4_tile("btn_waypoints", "ic_v4_pin", "WAYPOINT", "", "green", "96dp"),
              _v4_tile("btn_stats", "ic_v4_stats", "STATS", "", "orange", "96dp", end_margin=False)) +
    '    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:gravity="center" android:layout_marginTop="16dp"\n'
    '        android:text="Creator Maikgost · funziona senza internet"\n'
    '        android:textColor="#5A7A99" android:textSize="11sp" android:letterSpacing="0.08"/>\n'
    '</LinearLayout></ScrollView></FrameLayout>')

# ---------------------------------------------------------------- SENTINELLA CIELO
LAYOUT_SKY_WATCH = _v4_screen(
    _v4_header("btn_sky_back", "SENTINELLA CIELO", "Rilevamento passivo droni · Remote ID + audio",
               right_chip_id="tv_sky_live", right_text="PAUSA") +
    '    <FrameLayout android:layout_width="match_parent" android:layout_height="380dp"\n'
    '        android:background="@drawable/bg_card_holo" android:padding="4dp">\n'
    '        <com.offlinegps.map.ui.SkyRadarView android:id="@+id/sky_radar"\n'
    '            android:layout_width="match_parent" android:layout_height="match_parent"/>\n'
    '        <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '            android:layout_gravity="top|end" android:orientation="horizontal"\n'
    '            android:layout_margin="10dp">\n'
    '            <TextView android:id="@+id/tv_sky_3d" android:layout_width="wrap_content"\n'
    '                android:layout_height="28dp" android:gravity="center" android:paddingStart="10dp"\n'
    '                android:paddingEnd="10dp" android:text="VISTA 3D" android:textSize="10sp"\n'
    '                android:textStyle="bold" android:textColor="#00FF88"\n'
    '                android:background="@drawable/bg_chip_on" android:clickable="true"\n'
    '                android:focusable="true" android:layout_marginEnd="6dp"/>\n'
    '            <TextView android:id="@+id/tv_sky_north" android:layout_width="wrap_content"\n'
    '                android:layout_height="28dp" android:gravity="center" android:paddingStart="10dp"\n'
    '                android:paddingEnd="10dp" android:text="NORD" android:textSize="10sp"\n'
    '                android:textStyle="bold" android:textColor="#8FB3D0"\n'
    '                android:background="@drawable/bg_chip_off" android:clickable="true"\n'
    '                android:focusable="true"/>\n'
    '        </LinearLayout>\n'
    '    </FrameLayout>\n'
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:orientation="horizontal" android:layout_marginTop="12dp" android:layout_marginBottom="12dp">\n'
    + _v4_chip_view("chip_sky_ble", "BLUETOOTH")
    + _v4_chip_view("chip_sky_wifi", "WI-FI")
    + _v4_chip_view("chip_sky_mic", "AUDIO")
    + _v4_chip_view("chip_sky_voice", "VOCE", end_margin=False) +
    '    </LinearLayout>\n'
    + _v4_hint("tv_sky_summary", "Avvio...")
    + _v4_row(_v4_tile("btn_sky_scan", "ic_v4_radar", "AVVIA SCANSIONE", "Remote ID Bluetooth + Wi-Fi", "cyan",
                       title_id="tv_sky_scan_label"),
              _v4_tile("btn_sky_demo", "ic_v4_play", "DEMO", "3 droni simulati", "yellow", end_margin=False))
    + _v4_row(_v4_tile("btn_sky_audio", "ic_v4_mic", "ASCOLTO", "Spettrogramma eliche", "pink"),
              _v4_tile("btn_sky_spot", "ic_v4_flag", "SEGNALA", "Zona anonima ~1 km", "cyan", end_margin=False))
    + _v4_row(_v4_tile("btn_sky_check", "ic_v4_help", "È UN DRONE?", "Aereo? Satellite? Venere?", "violet"),
              _v4_tile("btn_sky_airspace", "ic_v4_globe", "SPAZIO AEREO", "Zone d-flight e regole", "green", end_margin=False))
    + _v4_section("DRONI RILEVATI") +
    '<LinearLayout android:id="@+id/sky_list" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:orientation="vertical"/>\n'
    + _v4_hint("tv_sky_empty", "Nessun drone in vista. Molti droni economici o costruiti prima del 2024 "
               "NON trasmettono il Remote ID: per quelli usa anche l\'ascolto acustico.")
    + _v4_hint(None, "SOLO RILEVAMENTO PASSIVO. L\'app riceve i segnali che i droni trasmettono per legge "
               "(Remote ID, Reg. UE 2019/945) e ascolta il loro rumore: non trasmette, non disturba e non "
               "blocca nulla. Disturbare le frequenze (jamming) o abbattere un drone e\' vietato ai privati. "
               "In caso di pericolo chiama il 112.", red=True),
    "sky_column")

# ---------------------------------------------------------------- ASCOLTO ACUSTICO
LAYOUT_ACOUSTIC = _v4_screen(
    _v4_header("btn_ac_back", "ASCOLTO DRONI", "Analisi spettrale delle eliche, sul telefono", "#FF3D71") +
    '    <FrameLayout android:layout_width="match_parent" android:layout_height="250dp"\n'
    '        android:background="@drawable/bg_card_holo">\n'
    '        <com.offlinegps.map.ui.NeonGaugeView android:id="@+id/ac_gauge"\n'
    '            android:layout_width="match_parent" android:layout_height="match_parent"/>\n'
    '    </FrameLayout>\n'
    '<TextView android:id="@+id/tv_ac_verdict" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:gravity="center" android:layout_marginTop="14dp"\n'
    '    android:text="MICROFONO SPENTO" android:textColor="#5A7A99" android:textSize="19sp"\n'
    '    android:textStyle="bold" android:fontFamily="sans-serif-condensed" android:letterSpacing="0.05"/>\n'
    '<TextView android:id="@+id/tv_ac_details" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:gravity="center" android:layout_marginTop="4dp"\n'
    '    android:layout_marginBottom="6dp" android:textColor="#8FB3D0" android:textSize="12sp"/>\n'
    + _v4_section("SPETTROGRAMMA 0-3 kHz") +
    '    <FrameLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:background="@drawable/bg_tile_glass" android:padding="8dp"\n'
    '        android:layout_marginBottom="12dp">\n'
    '        <com.offlinegps.map.ui.SpectrogramView android:id="@+id/ac_spectro"\n'
    '            android:layout_width="match_parent" android:layout_height="230dp"/>\n'
    '    </FrameLayout>\n'
    + _v4_row(_v4_tile("btn_ac_toggle", "ic_v4_mic", "AVVIA ASCOLTO", "Nessuna registrazione salvata", "green",
                       title_id="tv_ac_toggle_label"),
              _v4_tile("btn_ac_report", "ic_v4_flag", "SEGNALA", "Allega il punteggio", "cyan", end_margin=False))
    + _v4_hint(None, "COME FUNZIONA\\nLe eliche producono un tono (frequenza di passaggio delle pale, 70-520 Hz) "
               "con armoniche ordinate e stabili per secondi. L\'analisi cerca questa scala di righe nello "
               "spettro e controlla che resti ferma nel tempo: voce, musica, vento e traffico vengono scartati."
               "\\n\\nLIMITI: portata tipica 50-150 m in un posto tranquillo; tosaerba, ventole e scooter possono "
               "ingannarla; il vento forte copre il segnale. E\' un indizio, non una prova."),
    "ac_column")

# ---------------------------------------------------------------- SKYSPOT
LAYOUT_SKYSPOT = _v4_screen(
    _v4_header("btn_spot_back", "SEGNALA AVVISTAMENTO", "Diario anonimo · resta sul telefono") +
    _v4_hint(None, "NON sostituisce il 112. Se c\'e\' un pericolo per persone, aerei o infrastrutture "
             "chiama subito il numero di emergenza.", red=True)
    + _v4_row(_v4_tile("btn_spot_112", "ic_v4_sos", "CHIAMA 112", "Apre il tastierino", "red", "96dp",
                       end_margin=False))
    + _v4_hint("tv_spot_rid", "", extra='\n    android:visibility="gone"')
    + _v4_label("Cosa hai notato") + _v4_spinner("sp_spot_kind")
    + _v4_label("Quanti oggetti") + _v4_spinner("sp_spot_count")
    + _v4_label("Direzione") +
    '<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '    android:orientation="horizontal">\n'
    '    <Spinner android:id="@+id/sp_spot_dir" android:layout_width="0dp" android:layout_height="50dp"\n'
    '        android:layout_weight="1" android:background="@drawable/bg_input"\n'
    '        android:popupBackground="#141E2E" android:paddingStart="6dp" android:layout_marginBottom="14dp"/>\n'
    '    <TextView android:id="@+id/btn_spot_compass" android:layout_width="wrap_content"\n'
    '        android:layout_height="50dp" android:gravity="center" android:paddingStart="14dp"\n'
    '        android:paddingEnd="14dp" android:layout_marginStart="8dp" android:text="USA BUSSOLA"\n'
    '        android:textColor="#00E5FF" android:textSize="12sp" android:textStyle="bold"\n'
    '        android:background="@drawable/bg_pill_back" android:clickable="true" android:focusable="true"/>\n'
    '</LinearLayout>\n'
    + _v4_label("Altezza stimata") + _v4_spinner("sp_spot_height")
    + _v4_label("Durata") + _v4_spinner("sp_spot_duration")
    + _v4_label("Note (colore luci, forma, rumore, rotta...)") +
    '<EditText android:id="@+id/et_spot_notes" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:minHeight="90dp" android:gravity="top|start"\n'
    '    android:padding="12dp" android:background="@drawable/bg_input" android:textColor="#E8F4FD"\n'
    '    android:textColorHint="#5A7A99" android:hint="Facoltativo" android:inputType="textMultiLine|textCapSentences"\n'
    '    android:layout_marginBottom="14dp"/>\n'
    + _v4_hint("tv_spot_loc", "Posizione...")
    + _v4_row(_v4_tile("btn_spot_save", "ic_v4_flag", "SALVA SEGNALAZIONE", "Puoi condividerla dopo", "green",
                       "96dp", end_margin=False))
    + _v4_section("LE TUE SEGNALAZIONI") +
    '<LinearLayout android:id="@+id/spot_list" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:orientation="vertical"/>\n',
    "spot_column")

# ---------------------------------------------------------------- E' UN DRONE?
SIGHTING_QUESTIONS = ["Cosa hai notato?", "Com\'e\' la luce?", "Come si muove?",
                      "Che rumore fa?", "Quanto dura?", "Quando?"]
LAYOUT_SIGHTING_CHECK = _v4_screen(
    _v4_header("btn_chk_back", "È DAVVERO UN DRONE?", "6 domande per evitare i falsi allarmi", "#B388FF")
    + "".join(_v4_label(str(i + 1) + ". " + q) + _v4_spinner("sp_chk_q" + str(i + 1))
              for i, q in enumerate(SIGHTING_QUESTIONS))
    + _v4_section("RISULTATO PIU\' PROBABILE") +
    '<LinearLayout android:id="@+id/chk_results" android:layout_width="match_parent"\n'
    '    android:layout_height="wrap_content" android:orientation="vertical"/>\n'
    + _v4_row(_v4_tile("btn_chk_sky", "ic_v4_radar", "APRI LA SENTINELLA", "Cerca Remote ID e ronzio eliche",
                       "cyan", "96dp", end_margin=False))
    + _v4_section("COSA FARE SE VEDI UN DRONE")
    + _v4_hint(None, "1. Mantieni la calma: la maggior parte degli avvistamenti notturni sono aerei, "
               "satelliti o pianeti.\\n"
               "2. NON tentare di abbattere, disturbare o catturare il drone: e\' pericoloso e vietato.\\n"
               "3. Annota ora, direzione, altezza stimata, colori delle luci e rumore. Se puoi farlo in "
               "sicurezza, fai un video.\\n"
               "4. Se sorvola aeroporti, infrastrutture, eventi affollati o ti sembra minaccioso: chiama il 112 "
               "e descrivi quello che vedi.\\n"
               "5. Se un drone cade: non toccarlo (le batterie al litio possono incendiarsi), allontana le "
               "persone e chiama il 112.\\n"
               "6. Drone che riprende casa tua: annota tutto e segnala alla Polizia Locale o al 112.\\n"
               "7. Non avvicinarti al pilota, anche se il Remote ID ne mostra la posizione.")
    + _v4_section("NOTIZIE E ALLARMI")
    + _v4_hint(None, "Prima di condividere notizie su droni ostili o minacce, controlla la fonte: agenzie di "
               "stampa, siti istituzionali (Ministero della Difesa, Protezione Civile, ENAC). Le voci non "
               "verificate creano panico e intasano il 112. Questa app non riceve allerte ufficiali: "
               "per quelle segui IT-alert e la Protezione Civile."),
    "chk_column")

LAYOUT_ITEM_SPINNER_DARK = (_XML_HEAD +
    '<TextView ' + _NS + ' android:id="@android:id/text1"\n'
    '    android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '    android:paddingStart="10dp" android:paddingEnd="10dp" android:paddingTop="12dp"\n'
    '    android:paddingBottom="12dp" android:textColor="#E8F4FD" android:textSize="14sp"\n'
    '    android:maxLines="1" android:ellipsize="end"/>')

# <<< V4 SENTINELLA CIELO

# >>> V5 NAVIGATORE 3D
# ============================================================
#  v5.0 NAVIGATORE 3D — mappa 3D vera (OpenGL/VTM), navigazione
#  con avanzamento reale, profili bici/piedi, chat mesh, strumenti.
# ============================================================

NAV_CORE = r"""package com.offlinegps.map.routing;

import java.util.List;

/**
 * Avanzamento lungo il percorso, calcolato a ogni posizione GPS:
 *  - aggancia la posizione al tratto di strada piu' vicino (proiezione sul
 *    segmento, non sul punto piu' vicino: sui rettilinei i punti sono radi);
 *  - distanza REALE alla prossima manovra e alla destinazione;
 *  - tempo residuo dai tempi dei singoli tratti (autostrada != centro citta');
 *  - fuori percorso solo dopo piu' letture consecutive (il GPS "salta");
 *  - direzione della strada nel punto agganciato (per ruotare la mappa).
 * Nessuna dipendenza da Android: e' testato sul computer.
 */
public final class NavCore {
    public static final class Progress {
        public double snappedLat, snappedLon;
        public double alongM;            // metri percorsi dall'inizio
        public double offRouteM;         // distanza dalla strada
        public int stepIndex;            // prossima manovra (indice in steps)
        public double distToManeuverM;   // metri alla prossima manovra
        public double remainingM;
        public long remainingMs;
        public float routeBearing;       // direzione della strada (gradi)
        public boolean offRoute, arrived;
        public float fraction;           // 0..1 avanzamento totale
    }

    private static final double ARRIVE_M = 25.0;

    private final double[] lat, lon, cum;
    private final List<RoutingEngine.NavStep> steps;
    private final double[] stepAlong;
    private final double totalM;
    private int lastSeg = 0;
    private int badFixes = 0;
    private int lastNext = 0;
    private boolean arrived;

    public NavCore(List<double[]> pts, List<RoutingEngine.NavStep> steps) {
        int n = pts.size();
        lat = new double[n]; lon = new double[n]; cum = new double[n];
        for (int i = 0; i < n; i++) {
            lat[i] = pts.get(i)[0]; lon[i] = pts.get(i)[1];
            if (i > 0) cum[i] = cum[i - 1] + dist(lat[i - 1], lon[i - 1], lat[i], lon[i]);
        }
        totalM = n > 0 ? cum[n - 1] : 0;
        this.steps = steps;
        stepAlong = new double[steps.size()];
        for (int i = 0; i < steps.size(); i++) {
            int pi = Math.max(0, Math.min(n - 1, steps.get(i).pointIndex));
            stepAlong[i] = n > 0 ? cum[pi] : 0;
        }
    }

    public double totalMeters() { return totalM; }
    public double stepAlong(int i) { return stepAlong[i]; }

    public Progress update(double la, double lo, float accuracy) {
        Progress p = new Progress();
        int n = lat.length;
        if (n < 2) {
            p.arrived = true;
            return p;
        }
        // 1) cerca prima vicino all'ultimo tratto (avanti), poi su tutto il percorso
        int best = -1;
        double bestD = Double.MAX_VALUE, bestT = 0;
        int from = Math.max(0, lastSeg - 3), to = Math.min(n - 2, lastSeg + 80);
        for (int pass = 0; pass < 2 && (best < 0 || bestD > 60); pass++) {
            for (int i = from; i <= to; i++) {
                double[] r = project(la, lo, i);
                // a parita' di distanza preferisce i tratti in avanti (percorsi ad anello)
                double score = r[0] + (i < lastSeg ? 8 : 0);
                if (score < bestD) { bestD = score; best = i; bestT = r[1]; }
            }
            from = 0; to = n - 2;
        }
        double segLen = cum[best + 1] - cum[best];
        p.alongM = cum[best] + bestT * segLen;
        p.snappedLat = lat[best] + (lat[best + 1] - lat[best]) * bestT;
        p.snappedLon = lon[best] + (lon[best + 1] - lon[best]) * bestT;
        p.offRouteM = dist(la, lo, p.snappedLat, p.snappedLon);
        p.routeBearing = (float) bearing(lat[best], lon[best], lat[best + 1], lon[best + 1]);
        lastSeg = best;

        // 2) prossima manovra = la prima che sta ancora davanti
        int next = steps.size() - 1;
        for (int i = 1; i < steps.size(); i++) {
            if (stepAlong[i] > p.alongM + 3) { next = i; break; }
        }
        // niente marcia indietro per il rumore GPS appena passata una manovra
        // (si torna indietro solo se si e' davvero tornati indietro di 25 m)
        if (next < lastNext && stepAlong[next] - p.alongM < 25) next = lastNext;
        lastNext = next;
        p.stepIndex = Math.max(0, next);
        p.distToManeuverM = steps.isEmpty() ? totalM - p.alongM : Math.max(0, stepAlong[p.stepIndex] - p.alongM);
        p.remainingM = Math.max(0, totalM - p.alongM);
        p.fraction = totalM > 0 ? (float) (p.alongM / totalM) : 1f;

        // 3) tempo residuo: tratto in corso in proporzione + tratti successivi interi
        long ms = 0;
        for (int i = 0; i < steps.size(); i++) {
            double start = stepAlong[i];
            double end = i + 1 < steps.size() ? stepAlong[i + 1] : totalM;
            if (end <= p.alongM) continue;
            double len = Math.max(1, end - start);
            double left = Math.min(len, end - Math.max(start, p.alongM));
            ms += (long) (steps.get(i).timeMillis * (left / len));
        }
        p.remainingMs = ms;

        // 4) fuori percorso: oltre max(30 m, 1,5 x precisione) per 3 letture di fila
        //    (2 se molto lontano)
        double limit = Math.max(30, 1.5 * Math.max(0, accuracy));
        if (p.offRouteM > limit) badFixes++;
        else badFixes = 0;
        p.offRoute = badFixes >= 3 || (badFixes >= 2 && p.offRouteM > 2 * limit + 40);

        // 5) arrivo (una sola volta, poi resta vero)
        if (!arrived && p.remainingM < ARRIVE_M && p.offRouteM < 60) arrived = true;
        p.arrived = arrived;
        return p;
    }

    /** Distanza dal segmento i e posizione t (0..1) della proiezione. */
    private double[] project(double la, double lo, int i) {
        // piano locale equirettangolare: precisione ottima su pochi km
        double k = Math.cos(Math.toRadians(la));
        double ax = (lon[i] - lo) * k, ay = lat[i] - la;
        double bx = (lon[i + 1] - lo) * k, by = lat[i + 1] - la;
        double dx = bx - ax, dy = by - ay;
        double l2 = dx * dx + dy * dy;
        double t = l2 > 0 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / l2)) : 0;
        double px = ax + t * dx, py = ay + t * dy;
        return new double[]{Math.sqrt(px * px + py * py) * 111_195.0, t};
    }

    public static double dist(double la1, double lo1, double la2, double lo2) {
        double r = 6371000.0, p1 = Math.toRadians(la1), p2 = Math.toRadians(la2);
        double dp = p2 - p1, dl = Math.toRadians(lo2 - lo1);
        double a = Math.sin(dp / 2) * Math.sin(dp / 2) + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
        return 2 * r * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    public static double bearing(double la1, double lo1, double la2, double lo2) {
        double p1 = Math.toRadians(la1), p2 = Math.toRadians(la2), dl = Math.toRadians(lo2 - lo1);
        double y = Math.sin(dl) * Math.cos(p2);
        double x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
        return (Math.toDegrees(Math.atan2(y, x)) + 360) % 360;
    }

    /**
     * Distanze (metri) a cui annunciare una manovra, in base alla velocita':
     * {lontano, vicino, adesso}. A piedi 120/40/12, in citta' 400/120/30,
     * in strada veloce 1000/350/60.
     */
    public static double[] announceDistances(float speedMs, String profile) {
        if (RoutingEngine.PROFILE_FOOT.equals(profile) || speedMs < 2.5f) return new double[]{120, 40, 12};
        if (RoutingEngine.PROFILE_BIKE.equals(profile) || speedMs < 9f) return new double[]{250, 80, 20};
        if (speedMs < 20f) return new double[]{400, 120, 30};
        return new double[]{1000, 350, 60};
    }
}
"""

SUN_CALC = r"""package com.offlinegps.map.util;

/**
 * Posizione del Sole e orari del giorno, calcolati offline con le formule
 * astronomiche standard (anomalia media, equazione del centro, ascensione
 * retta, tempo siderale). Precisione tipica: 1-2 minuti alle nostre latitudini.
 * Tutti i tempi sono in millisecondi UTC (System.currentTimeMillis()).
 */
public final class SunCalc {
    private static final double RAD = Math.PI / 180, DAY_MS = 86_400_000.0;
    private static final double J1970 = 2440588, J2000 = 2451545, J0 = 0.0009;
    private static final double E = RAD * 23.4397;   // obliquita' dell'eclittica

    /** Angoli del Sole (gradi) che definiscono i momenti della giornata. */
    public static final double SUNRISE = -0.833, GOLDEN = 6, BLUE_HIGH = -4, CIVIL = -6, NAUTICAL = -12, ASTRO = -18;

    private SunCalc() {}

    /** {altezza sull'orizzonte, azimut da nord in senso orario}, in gradi. */
    public static double[] position(long ms, double lat, double lon) {
        double lw = RAD * -lon, phi = RAD * lat, d = toDays(ms);
        double[] c = sunCoords(d);
        double h = siderealTime(d, lw) - c[1];
        double az = Math.atan2(Math.sin(h), Math.cos(h) * Math.sin(phi) - Math.tan(c[0]) * Math.cos(phi));
        double alt = Math.asin(Math.sin(phi) * Math.sin(c[0]) + Math.cos(phi) * Math.cos(c[0]) * Math.cos(h));
        return new double[]{alt / RAD, (az / RAD + 180 + 360) % 360};
    }

    public static final class Times {
        public long solarNoon, nadir;
        /** [0] = mattina (sale), [1] = sera (scende); Long.MIN_VALUE se non accade (sole di mezzanotte / notte polare). */
        public final long[] sunrise = new long[2], golden = new long[2], blueHigh = new long[2],
            civil = new long[2], nautical = new long[2], astro = new long[2];
        public double noonAltitude;

        public long dayLengthMs() {
            return sunrise[0] == Long.MIN_VALUE ? (noonAltitude > 0 ? 86_400_000L : 0) : sunrise[1] - sunrise[0];
        }
    }

    /** Orari per il giorno che contiene "ms" (meglio passare il mezzogiorno locale). */
    public static Times times(long ms, double lat, double lon) {
        double lw = RAD * -lon, phi = RAD * lat, d = toDays(ms);
        double n = Math.round(d - J0 - lw / (2 * Math.PI));
        double ds = approxTransit(0, lw, n);
        double m = solarMeanAnomaly(ds), l = eclipticLongitude(m), dec = declination(l, 0);
        double jNoon = solarTransitJ(ds, m, l);
        Times t = new Times();
        t.solarNoon = fromJulian(jNoon);
        t.nadir = fromJulian(jNoon - 0.5);
        t.noonAltitude = position(t.solarNoon, lat, lon)[0];
        fill(t.sunrise, SUNRISE, lw, phi, dec, n, m, l, jNoon);
        fill(t.golden, GOLDEN, lw, phi, dec, n, m, l, jNoon);
        fill(t.blueHigh, BLUE_HIGH, lw, phi, dec, n, m, l, jNoon);
        fill(t.civil, CIVIL, lw, phi, dec, n, m, l, jNoon);
        fill(t.nautical, NAUTICAL, lw, phi, dec, n, m, l, jNoon);
        fill(t.astro, ASTRO, lw, phi, dec, n, m, l, jNoon);
        return t;
    }

    private static void fill(long[] out, double angle, double lw, double phi, double dec,
                             double n, double m, double l, double jNoon) {
        double w = hourAngle(angle * RAD, phi, dec);
        if (Double.isNaN(w)) { out[0] = out[1] = Long.MIN_VALUE; return; }
        double jSet = solarTransitJ(approxTransit(w, lw, n), m, l);
        double jRise = jNoon - (jSet - jNoon);
        out[0] = fromJulian(jRise);
        out[1] = fromJulian(jSet);
    }

    /** true se il Sole e' sotto -4 gradi (buio pratico: tema notte). */
    public static boolean isDark(long ms, double lat, double lon) {
        return position(ms, lat, lon)[0] < BLUE_HIGH;
    }

    // ------------------------------------------------------------ formule
    private static double toJulian(long ms) { return ms / DAY_MS - 0.5 + J1970; }
    private static long fromJulian(double j) { return Math.round((j + 0.5 - J1970) * DAY_MS); }
    private static double toDays(long ms) { return toJulian(ms) - J2000; }

    private static double declination(double l, double b) {
        return Math.asin(Math.sin(b) * Math.cos(E) + Math.cos(b) * Math.sin(E) * Math.sin(l));
    }

    private static double rightAscension(double l, double b) {
        return Math.atan2(Math.sin(l) * Math.cos(E) - Math.tan(b) * Math.sin(E), Math.cos(l));
    }

    private static double siderealTime(double d, double lw) { return RAD * (280.16 + 360.9856235 * d) - lw; }
    private static double solarMeanAnomaly(double d) { return RAD * (357.5291 + 0.98560028 * d); }

    private static double eclipticLongitude(double m) {
        double c = RAD * (1.9148 * Math.sin(m) + 0.02 * Math.sin(2 * m) + 0.0003 * Math.sin(3 * m));
        double p = RAD * 102.9372;   // perielio
        return m + c + p + Math.PI;
    }

    /** {declinazione, ascensione retta} in radianti. */
    private static double[] sunCoords(double d) {
        double m = solarMeanAnomaly(d), l = eclipticLongitude(m);
        return new double[]{declination(l, 0), rightAscension(l, 0)};
    }

    private static double approxTransit(double ht, double lw, double n) { return J0 + (ht + lw) / (2 * Math.PI) + n; }

    private static double solarTransitJ(double ds, double m, double l) {
        return J2000 + ds + 0.0053 * Math.sin(m) - 0.0069 * Math.sin(2 * l);
    }

    private static double hourAngle(double h, double phi, double d) {
        return Math.acos((Math.sin(h) - Math.sin(phi) * Math.sin(d)) / (Math.cos(phi) * Math.cos(d)));
    }
}
"""

MAP_ENGINE = r"""package com.offlinegps.map.map;

import android.view.View;
import java.io.File;
import java.util.List;

/**
 * Motore di mappa usato da navigatore e mappa 3D. Due implementazioni:
 *  - VtmEngine: OpenGL vero 3D (inclinazione, rotazione, edifici 3D, temi);
 *  - MapsforgeEngine: la mappa 2D classica, usata se il 3D non e' disponibile.
 * Le coordinate sono sempre {lat, lon}.
 */
public interface MapEngine {
    int THEME_NIGHT = 0, THEME_DAY = 1, THEME_OUTDOOR = 2, THEME_CLASSIC = 3;

    interface LongPressListener { void onLongPress(double lat, double lon); }

    View view();
    /** true se il motore puo' inclinare/ruotare la mappa (3D). */
    boolean is3d();
    String name();

    boolean loadMapFile(File f);

    void setUserPosition(double lat, double lon, float accuracy, float bearing);
    void setRoute(List<double[]> pts);
    void setTrack(List<double[]> pts);
    void setDestination(double lat, double lon);
    void setPoints(List<double[]> pts);          // waypoint {lat, lon}

    /** Inquadratura: zoom (livello), rotazione (gradi, 0 = nord su), inclinazione (gradi). */
    void moveTo(double lat, double lon, double zoom, float bearing, float tilt, boolean animate);
    void fitBounds(List<double[]> pts, boolean animate);
    double zoom();
    float bearing();
    float tilt();
    void setTilt(float deg, boolean animate);
    void setBearing(float deg, boolean animate);
    void zoomBy(int delta);

    /** Sposta il punto di riferimento in verticale (-1..1): 0,4 = tu in basso, strada davanti. */
    void setFocusOffset(float y);

    void setTheme(int theme);
    void setBuildings(boolean on);

    /** Chiamato quando l'utente trascina/ruota/zooma la mappa con le dita. */
    void setOnUserGesture(Runnable r);
    void setOnLongPress(LongPressListener l);

    void onResume();
    void onPause();
    void onDestroy();
}
"""

VTM_ENGINE = r"""package com.offlinegps.map.map;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.view.View;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import org.oscim.android.MapView;
import org.oscim.android.canvas.AndroidBitmap;
import org.oscim.backend.canvas.Bitmap;
import org.oscim.core.BoundingBox;
import org.oscim.core.GeoPoint;
import org.oscim.core.MapPosition;
import org.oscim.event.Event;
import org.oscim.event.Gesture;
import org.oscim.event.GestureListener;
import org.oscim.event.MotionEvent;
import org.oscim.layers.Layer;
import org.oscim.layers.LocationTextureLayer;
import org.oscim.layers.PathLayer;
import org.oscim.layers.marker.ItemizedLayer;
import org.oscim.layers.marker.MarkerInterface;
import org.oscim.layers.marker.MarkerItem;
import org.oscim.layers.marker.MarkerSymbol;
import org.oscim.layers.tile.buildings.BuildingLayer;
import org.oscim.layers.tile.vector.VectorTileLayer;
import org.oscim.layers.tile.vector.labeling.LabelLayer;
import org.oscim.map.Map;
import org.oscim.renderer.LocationCallback;
import org.oscim.scalebar.DefaultMapScaleBar;
import org.oscim.scalebar.MapScaleBarLayer;
import org.oscim.theme.ThemeFile;
import org.oscim.theme.internal.VtmThemes;
import org.oscim.theme.styles.LineStyle;
import org.oscim.tiling.source.mapfile.MapFileTileSource;

/**
 * Mappa 3D VERA con VTM (OpenGL ES): inclinazione fino a 65 gradi, rotazione
 * libera, edifici estrusi in 3D, etichette che restano dritte, temi diversi
 * (notte neon, giorno, outdoor). Legge gli stessi file .map di Mapsforge.
 */
public final class VtmEngine implements MapEngine {
    private final Context ctx;
    private final MapView mapView;
    private final Map map;
    private final float density;
    private MapFileTileSource source;
    private VectorTileLayer tiles;
    private BuildingLayer buildings;
    private LabelLayer labels;
    private PathLayer routeGlow, routeLine, trackLine;
    private ItemizedLayer pointsLayer, destLayer;
    private LocationTextureLayer userLayer;
    private MapScaleBarLayer scaleBar;
    private volatile float userBearing = Float.NaN;
    private int theme = THEME_NIGHT;
    private boolean buildingsOn = true;
    private Runnable onUserGesture;
    private LongPressListener onLongPress;
    private Runnable healthy;

    /** Avvisato quando la schermata si chiude normalmente (nessun crash del 3D). */
    void setHealthyCallback(Runnable r) { healthy = r; }

    /** Puo' lanciare (es. libreria nativa assente): il chiamante ripiega sul 2D. */
    public VtmEngine(Context c) {
        ctx = c;
        density = c.getResources().getDisplayMetrics().density;
        mapView = new MapView(c);
        map = mapView.map();
        map.viewport().setMaxTilt(65f);
        map.events.bind(new Map.UpdateListener() {
            @Override public void onMapEvent(Event e, MapPosition p) {
                if ((e == Map.MOVE_EVENT || e == Map.ROTATE_EVENT || e == Map.TILT_EVENT)
                        && onUserGesture != null) mapView.post(onUserGesture);
            }
        });
    }

    @Override public View view() { return mapView; }
    @Override public boolean is3d() { return true; }
    @Override public String name() { return "3D (OpenGL)"; }

    // ------------------------------------------------------------ dati mappa
    @Override public boolean loadMapFile(File f) {
        if (f == null || !f.exists()) return false;
        MapFileTileSource ts = new MapFileTileSource();
        if (!ts.setMapFile(f.getAbsolutePath())) return false;
        ts.setPreferredLanguage("it");
        source = ts;
        tiles = map.setBaseMap(ts);
        rebuildLayers();
        applyTheme();
        try {
            org.oscim.tiling.source.mapfile.MapInfo info = ts.getMapInfo();
            if (info != null && info.boundingBox != null) {
                GeoPoint c = info.boundingBox.getCenterPoint();
                map.setMapPosition(c.getLatitude(), c.getLongitude(), 1 << 12);
            }
        } catch (Exception ignored) {}
        return true;
    }

    /** Ordine dei livelli: strade, edifici 3D, percorso, etichette, punti, tu, scala. */
    private void rebuildLayers() {
        List<Layer> keep = new ArrayList<>();
        keep.add(map.getEventLayer());              // gestione gesti (sempre prima)
        if (tiles != null) keep.add(tiles);
        map.layers().clear();
        map.layers().addAll(keep);

        if (tiles != null) {
            buildings = new BuildingLayer(map, tiles, 16, map.viewport().getMaxZoomLevel(), false, true);
            buildings.setEnabled(buildingsOn);
            map.layers().add(buildings);
        }
        float w = 7f * density;
        routeGlow = new PathLayer(map, new LineStyle(0x5500E5FF, w * 3f, org.oscim.backend.canvas.Paint.Cap.ROUND));
        routeLine = new PathLayer(map, new LineStyle(0xFF00E5FF, w, org.oscim.backend.canvas.Paint.Cap.ROUND));
        trackLine = new PathLayer(map, new LineStyle(0xFF00FF88, w * 0.7f, org.oscim.backend.canvas.Paint.Cap.ROUND));
        map.layers().add(trackLine);
        map.layers().add(routeGlow);
        map.layers().add(routeLine);
        if (tiles != null) {
            labels = new LabelLayer(map, tiles);
            map.layers().add(labels);
        }
        pointsLayer = new ItemizedLayer(map, symbol(pin(0xFF00FF88, 30), MarkerSymbol.HotspotPlace.BOTTOM_CENTER, true));
        destLayer = new ItemizedLayer(map, symbol(pin(0xFFFF3D71, 42), MarkerSymbol.HotspotPlace.BOTTOM_CENTER, true));
        map.layers().add(pointsLayer);
        map.layers().add(destLayer);

        userLayer = new LocationTextureLayer(map);
        userLayer.locationRenderer.setBitmapArrow(new AndroidBitmap(arrow()));
        userLayer.locationRenderer.setBitmapMarker(new AndroidBitmap(dot()));
        userLayer.locationRenderer.setColor(0xFF00E5FF);
        userLayer.locationRenderer.setShowAccuracyZoom(15);
        userLayer.locationRenderer.setCallback(new LocationCallback() {
            @Override public boolean hasRotation() { return !Float.isNaN(userBearing); }
            @Override public float getRotation() { return Float.isNaN(userBearing) ? 0 : userBearing; }
        });
        userLayer.setEnabled(false);
        map.layers().add(userLayer);

        map.layers().add(new GestureLayer(map));
        DefaultMapScaleBar bar = new DefaultMapScaleBar(map);
        bar.setScaleBarMode(DefaultMapScaleBar.ScaleBarMode.SINGLE);
        scaleBar = new MapScaleBarLayer(map, bar);
        map.layers().add(scaleBar);
        map.updateMap(true);
    }

    @Override public void setUserPosition(double lat, double lon, float accuracy, float bearing) {
        if (userLayer == null) return;
        userBearing = bearing;
        userLayer.setEnabled(true);
        userLayer.setPosition(lat, lon, Math.max(3f, accuracy));
        map.updateMap(true);
    }

    @Override public void setRoute(List<double[]> pts) {
        if (routeLine == null) return;
        List<GeoPoint> g = geo(pts);
        routeGlow.setPoints(g);
        routeLine.setPoints(g);
        map.updateMap(true);
    }

    @Override public void setTrack(List<double[]> pts) {
        if (trackLine == null) return;
        trackLine.setPoints(geo(pts));
        map.updateMap(true);
    }

    @Override public void setDestination(double lat, double lon) {
        if (destLayer == null) return;
        destLayer.removeAllItems();
        if (!Double.isNaN(lat) && !Double.isNaN(lon))
            destLayer.addItem(new MarkerItem("Destinazione", "", new GeoPoint(lat, lon)));
        map.updateMap(true);
    }

    @Override public void setPoints(List<double[]> pts) {
        if (pointsLayer == null) return;
        pointsLayer.removeAllItems();
        List<MarkerInterface> items = new ArrayList<>();
        if (pts != null) for (double[] p : pts) items.add(new MarkerItem("", "", new GeoPoint(p[0], p[1])));
        pointsLayer.addItems(items);
        map.updateMap(true);
    }

    // ------------------------------------------------------------ inquadratura
    @Override public void moveTo(double lat, double lon, double zoom, float bearing, float tilt, boolean animate) {
        MapPosition p = new MapPosition();
        map.getMapPosition(p);
        p.setPosition(lat, lon);
        if (!Double.isNaN(zoom)) p.setZoom(zoom);
        if (!Float.isNaN(bearing)) p.setBearing(-bearing);
        if (!Float.isNaN(tilt)) p.setTilt(map.viewport().limitTilt(tilt));
        if (animate) map.animator().animateTo(500, p);
        else map.setMapPosition(p);
    }

    @Override public void fitBounds(List<double[]> pts, boolean animate) {
        if (pts == null || pts.size() < 2) return;
        double minLa = 90, maxLa = -90, minLo = 180, maxLo = -180;
        for (double[] p : pts) {
            minLa = Math.min(minLa, p[0]); maxLa = Math.max(maxLa, p[0]);
            minLo = Math.min(minLo, p[1]); maxLo = Math.max(maxLo, p[1]);
        }
        BoundingBox bb = new BoundingBox(minLa, minLo, maxLa, maxLo).extendMargin(1.25f);
        MapPosition p = new MapPosition();
        map.getMapPosition(p);
        p.setByBoundingBox(bb, Math.max(1, map.getWidth()), Math.max(1, map.getHeight()));
        p.setBearing(0);
        p.setTilt(0);
        if (animate) map.animator().animateTo(700, p);
        else map.setMapPosition(p);
    }

    @Override public double zoom() { return map.getMapPosition().getZoom(); }
    @Override public float bearing() { return -map.getMapPosition().getBearing(); }
    @Override public float tilt() { return map.getMapPosition().getTilt(); }

    @Override public void setTilt(float deg, boolean animate) {
        MapPosition p = new MapPosition();
        map.getMapPosition(p);
        p.setTilt(map.viewport().limitTilt(deg));
        if (animate) map.animator().animateTo(450, p); else map.setMapPosition(p);
    }

    @Override public void setBearing(float deg, boolean animate) {
        MapPosition p = new MapPosition();
        map.getMapPosition(p);
        p.setBearing(-deg);
        if (animate) map.animator().animateTo(450, p); else map.setMapPosition(p);
    }

    @Override public void zoomBy(int delta) {
        MapPosition p = new MapPosition();
        map.getMapPosition(p);
        p.setZoom(Math.max(3, Math.min(20, p.getZoom() + delta)));
        map.animator().animateTo(300, p);
    }

    @Override public void setFocusOffset(float y) {
        map.viewport().setMapViewCenterY(Math.max(-0.8f, Math.min(0.8f, y)));
        map.updateMap(true);
    }

    // ------------------------------------------------------------ aspetto
    @Override public void setTheme(int t) {
        theme = t;
        applyTheme();
    }

    private void applyTheme() {
        if (tiles == null) return;
        ThemeFile tf;
        switch (theme) {
            case THEME_DAY:     tf = VtmThemes.DEFAULT; break;
            case THEME_OUTDOOR: tf = VtmThemes.BIKER; break;
            case THEME_CLASSIC: tf = VtmThemes.OSMARENDER; break;
            default:            tf = VtmThemes.TRONRENDER; break;
        }
        map.setTheme(tf);
        map.clearMap();
    }

    @Override public void setBuildings(boolean on) {
        buildingsOn = on;
        if (buildings != null) buildings.setEnabled(on);
        map.updateMap(true);
    }

    @Override public void setOnUserGesture(Runnable r) { onUserGesture = r; }
    @Override public void setOnLongPress(LongPressListener l) { onLongPress = l; }

    @Override public void onResume() { mapView.onResume(); }
    @Override public void onPause() {
        mapView.onPause();
        if (healthy != null) healthy.run();
    }
    @Override public void onDestroy() {
        if (healthy != null) healthy.run();
        try { mapView.onDestroy(); } catch (Exception ignored) {}
    }

    // ------------------------------------------------------------ gesti
    /** Tieni premuto sulla mappa: coordinate del punto (per "naviga qui"). */
    private final class GestureLayer extends Layer implements GestureListener {
        GestureLayer(Map m) { super(m); }
        @Override public boolean onGesture(Gesture g, MotionEvent e) {
            if (g == Gesture.LONG_PRESS && onLongPress != null) {
                final GeoPoint gp = map.viewport().fromScreenPoint(e.getX(), e.getY());
                mapView.post(() -> onLongPress.onLongPress(gp.getLatitude(), gp.getLongitude()));
                return true;
            }
            return false;
        }
    }

    // ------------------------------------------------------------ simboli disegnati al volo
    private static List<GeoPoint> geo(List<double[]> pts) {
        List<GeoPoint> g = new ArrayList<>();
        if (pts != null) for (double[] p : pts) g.add(new GeoPoint(p[0], p[1]));
        return g;
    }

    private MarkerSymbol symbol(android.graphics.Bitmap b, MarkerSymbol.HotspotPlace hp, boolean billboard) {
        Bitmap vb = new AndroidBitmap(b);
        return new MarkerSymbol(vb, hp, billboard);
    }

    /** Spillo neon con alone. */
    private android.graphics.Bitmap pin(int color, int sizeDp) {
        int s = Math.round(sizeDp * density);
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(s, Math.round(s * 1.3f), android.graphics.Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        float r = s * 0.36f, cx = s / 2f, cy = r + s * 0.08f;
        Path path = new Path();
        path.moveTo(cx, b.getHeight() - 1);
        path.lineTo(cx - r * 0.85f, cy + r * 0.45f);
        path.lineTo(cx + r * 0.85f, cy + r * 0.45f);
        path.close();
        p.setColor(color);
        c.drawPath(path, p);
        p.setShader(new RadialGradient(cx, cy, r * 1.4f, (color & 0x00FFFFFF) | 0x66000000, color & 0x00FFFFFF, Shader.TileMode.CLAMP));
        c.drawCircle(cx, cy, r * 1.4f, p);
        p.setShader(null);
        p.setColor(color);
        c.drawCircle(cx, cy, r, p);
        p.setColor(0xFF050A14);
        c.drawCircle(cx, cy, r * 0.45f, p);
        p.setColor(0xFFFFFFFF);
        c.drawCircle(cx, cy, r * 0.22f, p);
        return b;
    }

    /** Freccia di navigazione (punta in su = direzione di marcia). */
    private android.graphics.Bitmap arrow() {
        int s = Math.round(44 * density);
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(s, s, android.graphics.Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        float cx = s / 2f;
        p.setShader(new RadialGradient(cx, cx, s / 2f, 0x6600E5FF, 0x0000E5FF, Shader.TileMode.CLAMP));
        c.drawCircle(cx, cx, s / 2f, p);
        p.setShader(null);
        Path path = new Path();
        path.moveTo(cx, s * 0.12f);
        path.lineTo(s * 0.78f, s * 0.82f);
        path.lineTo(cx, s * 0.64f);
        path.lineTo(s * 0.22f, s * 0.82f);
        path.close();
        p.setColor(0xFFFFFFFF);
        c.drawPath(path, p);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(2.2f * density);
        p.setColor(0xFF00E5FF);
        c.drawPath(path, p);
        return b;
    }

    private android.graphics.Bitmap dot() {
        int s = Math.round(26 * density);
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(s, s, android.graphics.Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        float cx = s / 2f;
        p.setColor(0xFFFFFFFF);
        c.drawCircle(cx, cx, s * 0.36f, p);
        p.setColor(0xFF00E5FF);
        c.drawCircle(cx, cx, s * 0.26f, p);
        return b;
    }
}
"""

MAPSFORGE_ENGINE = r"""package com.offlinegps.map.map;

import android.content.Context;
import android.view.View;
import java.io.File;
import java.util.List;
import org.mapsforge.core.model.LatLong;
import org.mapsforge.core.model.MapPosition;
import org.mapsforge.map.android.view.MapView;

/**
 * Ripiego 2D (Mapsforge) quando l'OpenGL 3D non e' disponibile: stessa
 * interfaccia, ma sempre a nord in alto e senza inclinazione.
 */
public final class MapsforgeEngine implements MapEngine {
    private final MapView mapView;
    private final MapController ctrl;
    private Runnable onUserGesture;

    public MapsforgeEngine(Context c) {
        try {
            org.mapsforge.map.android.graphics.AndroidGraphicFactory.createInstance(
                (android.app.Application) c.getApplicationContext());
        } catch (Throwable ignored) {}
        mapView = new MapView(c);
        ctrl = new MapController(c);
        ctrl.init(mapView);
        mapView.setOnTouchListener((v, ev) -> {
            if (ev.getActionMasked() == android.view.MotionEvent.ACTION_MOVE && onUserGesture != null)
                onUserGesture.run();
            return false;
        });
    }

    public MapController controller() { return ctrl; }

    @Override public View view() { return mapView; }
    @Override public boolean is3d() { return false; }
    @Override public String name() { return "2D (Mapsforge)"; }
    @Override public boolean loadMapFile(File f) { return ctrl.loadMapFile(f); }

    @Override public void setUserPosition(double lat, double lon, float accuracy, float bearing) {
        ctrl.updatePosition(lat, lon, accuracy, Float.isNaN(bearing) ? 0f : bearing);
    }

    @Override public void setRoute(List<double[]> pts) {
        ctrl.clearTrack();
        if (pts != null && !pts.isEmpty()) ctrl.addTrackPoints(pts);
    }

    @Override public void setTrack(List<double[]> pts) { /* la linea e' usata dal percorso */ }

    @Override public void setDestination(double lat, double lon) {
        if (!Double.isNaN(lat) && !Double.isNaN(lon)) ctrl.setDestinationMarker(lat, lon);
    }

    @Override public void setPoints(List<double[]> pts) {
        ctrl.clearWaypointMarkers();
        if (pts != null) for (double[] p : pts) ctrl.addWaypointMarker(p[0], p[1], "#00FF88");
    }

    @Override public void moveTo(double lat, double lon, double zoom, float bearing, float tilt, boolean animate) {
        if (!Double.isNaN(zoom)) {
            byte z = (byte) Math.max(4, Math.min(19, Math.round(zoom)));
            if (animate && z == mapView.getModel().mapViewPosition.getZoomLevel()) ctrl.centerOn(lat, lon, true);
            else mapView.getModel().mapViewPosition.setMapPosition(new MapPosition(new LatLong(lat, lon), z));
        } else ctrl.centerOn(lat, lon, animate);
    }

    @Override public void fitBounds(List<double[]> pts, boolean animate) {
        ctrl.fitTrackBounds();
    }

    @Override public double zoom() { return ctrl.getZoom(); }
    @Override public float bearing() { return 0f; }
    @Override public float tilt() { return 0f; }
    @Override public void setTilt(float deg, boolean animate) {}
    @Override public void setBearing(float deg, boolean animate) {}
    @Override public void zoomBy(int delta) {
        for (int i = 0; i < Math.abs(delta); i++) { if (delta > 0) ctrl.zoomIn(); else ctrl.zoomOut(); }
    }

    @Override public void setFocusOffset(float y) {}
    @Override public void setTheme(int theme) { ctrl.setNightMode(theme == THEME_NIGHT); }
    @Override public void setBuildings(boolean on) {}
    @Override public void setOnUserGesture(Runnable r) { onUserGesture = r; }
    @Override public void setOnLongPress(LongPressListener l) {}
    @Override public void onResume() {}
    @Override public void onPause() {}
    @Override public void onDestroy() { ctrl.destroy(); }
}
"""

MAP_ENGINES = r"""package com.offlinegps.map.map;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

/**
 * Sceglie il motore di mappa: 3D OpenGL (VTM) se possibile, altrimenti 2D.
 * Protezione anti-crash: se l'app si e' chiusa mentre il 3D partiva (driver
 * grafico o libreria nativa incompatibile), al riavvio usa subito il 2D.
 */
public final class MapEngines {
    private static final String PREFS = "map_engine";
    private static final String KEY_STARTING = "vtm_starting";
    private static final String KEY_DISABLED = "vtm_disabled";
    private static final String KEY_FORCE_2D = "force_2d";
    private MapEngines() {}

    /** true se l'ultima volta il 3D e' andato in crash all'avvio. */
    public static boolean disabledAfterCrash(Context c) {
        return prefs(c).getBoolean(KEY_DISABLED, false);
    }

    public static boolean force2d(Context c) { return prefs(c).getBoolean(KEY_FORCE_2D, false); }

    public static void setForce2d(Context c, boolean on) {
        prefs(c).edit().putBoolean(KEY_FORCE_2D, on).putBoolean(KEY_DISABLED, false).apply();
    }

    public static MapEngine create(Context c) {
        SharedPreferences p = prefs(c);
        if (p.getBoolean(KEY_STARTING, false)) {
            // l'avvio precedente del 3D non e' arrivato in fondo: disattiva
            p.edit().putBoolean(KEY_STARTING, false).putBoolean(KEY_DISABLED, true).apply();
        }
        if (!p.getBoolean(KEY_DISABLED, false) && !p.getBoolean(KEY_FORCE_2D, false)) {
            p.edit().putBoolean(KEY_STARTING, true).commit();
            try {
                VtmEngine e = new VtmEngine(c);
                Runnable ok = () -> prefs(c).edit().putBoolean(KEY_STARTING, false).apply();
                e.setHealthyCallback(ok);
                // se dopo 6 secondi siamo ancora vivi il 3D funziona su questo telefono
                new Handler(Looper.getMainLooper()).postDelayed(ok, 6000);
                return e;
            } catch (Throwable t) {
                Log.w("MapEngines", "3D non disponibile: " + t);
                p.edit().putBoolean(KEY_STARTING, false).putBoolean(KEY_DISABLED, true).apply();
            }
        }
        return new MapsforgeEngine(c);
    }

    private static SharedPreferences prefs(Context c) {
        return c.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
"""

MAP3D_ACTIVITY = r"""package com.offlinegps.map.ui;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import com.offlinegps.map.AppConfig;
import com.offlinegps.map.R;
import com.offlinegps.map.data.GpsDatabase;
import com.offlinegps.map.data.WaypointEntity;
import com.offlinegps.map.gps.GpsTrackingService;
import com.offlinegps.map.map.MapEngine;
import com.offlinegps.map.map.MapEngines;
import com.offlinegps.map.routing.RoutingEngine;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * MAPPA 3D VERA: inclina con due dita (o col pulsante 3D), ruota con due
 * dita, edifici in 3D da zoom 16, quattro temi, bussola che segue la
 * rotazione, segui-GPS con la mappa orientata nella direzione di marcia,
 * waypoint salvati, tieni premuto per "naviga qui" o "salva punto".
 */
public class Map3DActivity extends AppCompatActivity implements GpsTrackingService.LocationCallback {
    private static final String[] THEME_NAMES = {"Notte neon", "Giorno", "Outdoor", "Classica"};
    private MapEngine engine;
    private TextView tvInfo, tvHint;
    private ImageView ivCompass, ivFollow;
    private View btnBuildings;
    private int theme;
    private boolean follow = false, buildings = true, centeredOnce = false;
    private final Handler h = new Handler(Looper.getMainLooper());
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Runnable hud = new Runnable() {
        @Override public void run() {
            if (engine == null) return;
            if (ivCompass != null) ivCompass.setRotation(-engine.bearing());
            if (tvInfo != null) tvInfo.setText(String.format(Locale.ITALY, "%s · %s · zoom %.0f · %.0f°",
                engine.is3d() ? "3D" : "2D", THEME_NAMES[theme], engine.zoom(), engine.tilt()));
            h.postDelayed(this, 150);
        }
    };

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_map3d);
        tvInfo = findViewById(R.id.tv_map3d_info);
        tvHint = findViewById(R.id.tv_map3d_hint);
        ivCompass = findViewById(R.id.iv_map3d_compass);
        ivFollow = findViewById(R.id.iv_map3d_follow);
        btnBuildings = findViewById(R.id.btn_map3d_buildings);
        SharedPreferences prefs = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE);
        theme = prefs.getInt("map3d_theme", MapEngine.THEME_NIGHT);
        buildings = prefs.getBoolean("map3d_buildings", true);

        FrameLayout container = findViewById(R.id.map3d_container);
        engine = MapEngines.create(this);
        container.addView(engine.view(), 0, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        if (!engine.is3d()) showFallbackNotice();

        String path = prefs.getString(AppConfig.PREF_MAP_FILE, "");
        File f = path.isEmpty() ? null : new File(path);
        if (f == null || !f.exists() || !engine.loadMapFile(f)) {
            if (tvHint != null) {
                tvHint.setText("Nessuna mappa offline caricata: vai in Download e scarica la tua zona.");
                tvHint.setVisibility(View.VISIBLE);
            }
        }
        engine.setTheme(theme);
        engine.setBuildings(buildings);
        engine.setTilt(engine.is3d() ? 55f : 0f, false);
        engine.setOnUserGesture(() -> setFollow(false));
        engine.setOnLongPress(this::onLongPress);

        click(R.id.btn_map3d_back, v -> finish());
        click(R.id.btn_map3d_search, v -> startActivity(new Intent(this, AddressSearchActivity.class)));
        click(R.id.btn_map3d_theme, v -> cycleTheme());
        click(R.id.btn_map3d_tilt, v -> toggleTilt());
        click(R.id.btn_map3d_buildings, v -> toggleBuildings());
        click(R.id.btn_map3d_compass, v -> engine.setBearing(0, true));
        click(R.id.btn_map3d_zoom_in, v -> engine.zoomBy(1));
        click(R.id.btn_map3d_zoom_out, v -> engine.zoomBy(-1));
        click(R.id.btn_map3d_follow, v -> setFollow(!follow));
        click(R.id.btn_map3d_2d, v -> startActivity(new Intent(this, MapActivity.class)));
        if (btnBuildings != null) btnBuildings.setAlpha(buildings ? 1f : 0.45f);

        if (tvHint != null && tvHint.getVisibility() != View.VISIBLE && engine.is3d()
                && !prefs.getBoolean("map3d_hint_seen", false)) {
            tvHint.setText("Due dita su/giu' per inclinare · ruota con due dita · tieni premuto per navigare");
            tvHint.setVisibility(View.VISIBLE);
            h.postDelayed(() -> tvHint.animate().alpha(0f).setDuration(600)
                .withEndAction(() -> tvHint.setVisibility(View.GONE)).start(), 6000);
            prefs.edit().putBoolean("map3d_hint_seen", true).apply();
        }
        loadWaypoints();
        startGps();
        Location last = GpsTrackingService.getLastLocation();
        if (last != null) onLocationUpdate(last, 0);
    }

    private void click(int id, View.OnClickListener l) {
        View v = findViewById(id);
        if (v != null) v.setOnClickListener(l);
    }

    /** Avvia il GPS (senza registrare la traccia) se il permesso c'e'. */
    private void startGps() {
        if (checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                != android.content.pm.PackageManager.PERMISSION_GRANTED) return;
        try {
            Intent i = new Intent(this, GpsTrackingService.class);
            i.setAction(GpsTrackingService.ACTION_START);
            i.putExtra(AppConfig.PREF_TRACK_ON, false);
            startForegroundService(i);
        } catch (Exception ignored) {}
    }

    private void showFallbackNotice() {
        String msg = MapEngines.disabledAfterCrash(this)
            ? "Il 3D si era bloccato su questo telefono: uso la mappa 2D. Tocca per riprovare il 3D."
            : "Questo telefono non supporta la mappa 3D OpenGL: uso la mappa 2D.";
        if (tvHint != null) {
            tvHint.setText(msg);
            tvHint.setVisibility(View.VISIBLE);
            tvHint.setOnClickListener(v -> {
                MapEngines.setForce2d(this, false);
                recreate();
            });
        }
    }

    private void cycleTheme() {
        theme = (theme + 1) % THEME_NAMES.length;
        engine.setTheme(theme);
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit().putInt("map3d_theme", theme).apply();
        Toast.makeText(this, "Tema: " + THEME_NAMES[theme], Toast.LENGTH_SHORT).show();
    }

    private void toggleTilt() {
        if (!engine.is3d()) { Toast.makeText(this, "3D non disponibile su questo telefono", Toast.LENGTH_SHORT).show(); return; }
        engine.setTilt(engine.tilt() > 10 ? 0f : 60f, true);
    }

    private void toggleBuildings() {
        buildings = !buildings;
        engine.setBuildings(buildings);
        if (btnBuildings != null) btnBuildings.setAlpha(buildings ? 1f : 0.45f);
        getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).edit().putBoolean("map3d_buildings", buildings).apply();
        Toast.makeText(this, buildings ? "Edifici 3D attivi (zoom 16+)" : "Edifici 3D spenti", Toast.LENGTH_SHORT).show();
    }

    private void setFollow(boolean on) {
        follow = on;
        if (ivFollow != null) ivFollow.setAlpha(on ? 1f : 0.55f);
        engine.setFocusOffset(on && engine.is3d() ? 0.35f : 0f);
        if (on) {
            Location l = GpsTrackingService.getLastLocation();
            if (l == null) Toast.makeText(this, "In attesa del GPS...", Toast.LENGTH_SHORT).show();
            else camera(l, true);
        }
    }

    private void camera(Location l, boolean animate) {
        float brg = l.hasBearing() && l.getSpeed() > 1.5f ? l.getBearing() : engine.bearing();
        engine.moveTo(l.getLatitude(), l.getLongitude(), Math.max(engine.zoom(), 16), brg,
            engine.is3d() ? Math.max(engine.tilt(), 50f) : 0f, animate);
    }

    @Override public void onLocationUpdate(@NonNull Location l, int sats) {
        runOnUiThread(() -> {
            if (engine == null || isFinishing()) return;
            float brg = l.hasBearing() ? l.getBearing() : Float.NaN;
            engine.setUserPosition(l.getLatitude(), l.getLongitude(), l.getAccuracy(), brg);
            if (!centeredOnce) {
                centeredOnce = true;
                engine.moveTo(l.getLatitude(), l.getLongitude(), 16, Float.NaN, Float.NaN, false);
            }
            if (follow) camera(l, true);
        });
    }

    private void onLongPress(double lat, double lon) {
        String coords = String.format(Locale.US, "%.6f, %.6f", lat, lon);
        new AlertDialog.Builder(this)
            .setTitle("Punto sulla mappa")
            .setMessage(coords)
            .setPositiveButton("Naviga qui", (d, w) -> {
                Intent i = new Intent(this, NavigationActivity.class);
                i.putExtra(NavigationActivity.EXTRA_DEST_LAT, lat);
                i.putExtra(NavigationActivity.EXTRA_DEST_LON, lon);
                i.putExtra(NavigationActivity.EXTRA_DEST_NAME, "Punto " + coords);
                i.putExtra(NavigationActivity.EXTRA_PROFILE, RoutingEngine.PROFILE_CAR);
                startActivity(i);
            })
            .setNeutralButton("Salva waypoint", (d, w) -> io.execute(() -> {
                GpsDatabase.getInstance(this).waypointDao().insert(
                    WaypointEntity.create("Punto 3D " + coords, lat, lon, 0, 0f, "#00FF88"));
                runOnUiThread(() -> {
                    Toast.makeText(this, "Waypoint salvato", Toast.LENGTH_SHORT).show();
                    loadWaypoints();
                });
            }))
            .setNegativeButton("Chiudi", null)
            .show();
    }

    private void loadWaypoints() {
        io.execute(() -> {
            List<double[]> pts = new ArrayList<>();
            try {
                for (WaypointEntity w : GpsDatabase.getInstance(this).waypointDao().getAllSync())
                    pts.add(new double[]{w.latitude, w.longitude});
            } catch (Exception ignored) {}
            runOnUiThread(() -> { if (engine != null && !isFinishing()) engine.setPoints(pts); });
        });
    }

    @Override protected void onResume() {
        super.onResume();
        GpsTrackingService.setCallback(this);
        engine.onResume();
        h.post(hud);
    }

    @Override protected void onPause() {
        super.onPause();
        GpsTrackingService.setCallback(null);
        engine.onPause();
        h.removeCallbacks(hud);
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        io.shutdown();
        if (engine != null) engine.onDestroy();
    }
}
"""

# ------------------------------------------------------------------
#  GRAFICA v5.0 — icone, pulsanti tondi in vetro, scheda manovra,
#  navigatore 3D e mappa 3D.
# ------------------------------------------------------------------
V5_ICONS = {
    "ic_v5_close":      _v4_icon(["M19,6.41L17.59,5 12,10.59 6.41,5 5,6.41 10.59,12 5,17.59 6.41,19 12,13.41 17.59,19 19,17.59 13.41,12z"]),
    "ic_v5_volume":     _v4_icon(["M3,9v6h4l5,5V4L7,9H3zm13.5,3c0,-1.77 -1.02,-3.29 -2.5,-4.03v8.05c1.48,-0.73 2.5,-2.25 2.5,-4.02zM14,3.23v2.06c2.89,0.86 5,3.54 5,6.71s-2.11,5.85 -5,6.71v2.06c4.01,-0.91 7,-4.49 7,-8.77s-2.99,-7.86 -7,-8.77z"]),
    "ic_v5_volume_off": _v4_icon(["M16.5,12c0,-1.77 -1.02,-3.29 -2.5,-4.03v2.21l2.45,2.45c0.03,-0.2 0.05,-0.41 0.05,-0.63zM19,12c0,0.94 -0.2,1.82 -0.54,2.64l1.51,1.51C20.63,14.91 21,13.5 21,12c0,-4.28 -2.99,-7.86 -7,-8.77v2.06c2.89,0.86 5,3.54 5,6.71zM4.27,3L3,4.27 7.73,9H3v6h4l5,5v-6.73l4.25,4.25c-0.67,0.52 -1.42,0.93 -2.25,1.18v2.06c1.38,-0.31 2.63,-0.95 3.69,-1.81L19.73,21 21,19.73l-9,-9L4.27,3zM12,4L9.91,6.09 12,8.18V4z"]),
    "ic_v5_cube":       _v4_icon(["M21,16.5c0,0.38 -0.21,0.71 -0.53,0.88l-7.9,4.44c-0.16,0.12 -0.36,0.18 -0.57,0.18s-0.41,-0.06 -0.57,-0.18l-7.9,-4.44A0.991,0.991 0 0,1 3,16.5v-9c0,-0.38 0.21,-0.71 0.53,-0.88l7.9,-4.44c0.16,-0.12 0.36,-0.18 0.57,-0.18s0.41,0.06 0.57,0.18l7.9,4.44c0.32,0.17 0.53,0.5 0.53,0.88v9zM12,4.15L6.04,7.5 12,10.85l5.96,-3.35L12,4.15zM5,15.91l6,3.38v-6.71L5,9.21v6.7zM19,15.91v-6.7l-6,3.37v6.71l6,-3.38z"]),
    "ic_v5_route":      _v4_icon(["M19,15.18V7c0,-2.21 -1.79,-4 -4,-4s-4,1.79 -4,4v10c0,1.1 -0.9,2 -2,2s-2,-0.9 -2,-2V8.82C8.16,8.4 9,7.3 9,6c0,-1.66 -1.34,-3 -3,-3S3,4.34 3,6c0,1.3 0.84,2.4 2,2.82V17c0,2.21 1.79,4 4,4s4,-1.79 4,-4V7c0,-1.1 0.9,-2 2,-2s2,0.9 2,2v8.18c-1.16,0.41 -2,1.51 -2,2.82c0,1.66 1.34,3 3,3s3,-1.34 3,-3c0,-1.3 -0.84,-2.4 -2,-2.82z"]),
    "ic_v5_list":       _v4_icon(["M3,13h2v-2H3v2zm0,4h2v-2H3v2zm0,-8h2V7H3v2zm4,4h14v-2H7v2zm0,4h14v-2H7v2zM7,7v2h14V7H7z"]),
    "ic_v5_gps":        _v4_icon(["M12,8c-2.21,0 -4,1.79 -4,4s1.79,4 4,4 4,-1.79 4,-4 -1.79,-4 -4,-4zm8.94,3A8.994,8.994 0 0,0 13,3.06V1h-2v2.06A8.994,8.994 0 0,0 3.06,11H1v2h2.06A8.994,8.994 0 0,0 11,20.94V23h2v-2.06A8.994,8.994 0 0,0 20.94,13H23v-2h-2.06zM12,19c-3.87,0 -7,-3.13 -7,-7s3.13,-7 7,-7 7,3.13 7,7 -3.13,7 -7,7z"]),
    "ic_v5_car":        _v4_icon(["M18.92,6.01C18.72,5.42 18.16,5 17.5,5h-11c-0.66,0 -1.21,0.42 -1.42,1.01L3,12v8c0,0.55 0.45,1 1,1h1c0.55,0 1,-0.45 1,-1v-1h12v1c0,0.55 0.45,1 1,1h1c0.55,0 1,-0.45 1,-1v-8l-2.08,-5.99zM6.5,16c-0.83,0 -1.5,-0.67 -1.5,-1.5S5.67,13 6.5,13s1.5,0.67 1.5,1.5S7.33,16 6.5,16zm11,0c-0.83,0 -1.5,-0.67 -1.5,-1.5s0.67,-1.5 1.5,-1.5 1.5,0.67 1.5,1.5 -0.67,1.5 -1.5,1.5zM5,11l1.5,-4.5h11L19,11H5z"]),
    "ic_v5_bike":       _v4_icon(["M15.5,5.5c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM5,12c-2.8,0 -5,2.2 -5,5s2.2,5 5,5 5,-2.2 5,-5 -2.2,-5 -5,-5zm0,8.5c-1.9,0 -3.5,-1.6 -3.5,-3.5s1.6,-3.5 3.5,-3.5 3.5,1.6 3.5,3.5 -1.6,3.5 -3.5,3.5zm5.8,-10l2.4,-2.4 0.8,0.8c1.3,1.3 3,2.1 5.1,2.1V9c-1.5,0 -2.7,-0.6 -3.6,-1.5l-1.9,-1.9c-0.5,-0.4 -1,-0.6 -1.6,-0.6s-1.1,0.2 -1.4,0.6L7.8,8.4c-0.4,0.4 -0.6,0.9 -0.6,1.4 0,0.6 0.2,1.1 0.6,1.4L11,14v5h2v-6.2l-2.2,-2.3zM19,12c-2.8,0 -5,2.2 -5,5s2.2,5 5,5 5,-2.2 5,-5 -2.2,-5 -5,-5zm0,8.5c-1.9,0 -3.5,-1.6 -3.5,-3.5s1.6,-3.5 3.5,-3.5 3.5,1.6 3.5,3.5 -1.6,3.5 -3.5,3.5z"]),
    "ic_v5_walk":       _v4_icon(["M13.5,5.5c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM9.8,8.9L7,23h2.1l1.8,-8 2.1,2v6h2v-7.5l-2.1,-2 0.6,-3C14.8,12 16.8,13 19,13v-2c-1.9,0 -3.5,-1 -4.3,-2.4l-1,-1.6c-0.4,-0.6 -1,-1 -1.7,-1 -0.3,0 -0.5,0.1 -0.8,0.1L6,8.3V13h2V9.6l1.8,-0.7"]),
    "ic_v5_layers":     _v4_icon(["M11.99,18.54l-7.37,-5.73L3,14.07l9,7 9,-7 -1.63,-1.27 -7.38,5.74zM12,16l7.36,-5.73L21,9l-9,-7 -9,7 1.63,1.27L12,16z"]),
    "ic_v5_building":   _v4_icon(["M15,11V5l-3,-3 -3,3v2H3v14h18V11h-6zm-8,8H5v-2h2v2zm0,-4H5v-2h2v2zm0,-4H5V9h2v2zm6,8h-2v-2h2v2zm0,-4h-2v-2h2v2zm0,-4h-2V9h2v2zm0,-4h-2V5h2v2zm6,12h-2v-2h2v2zm0,-4h-2v-2h2v2z"]),
    "ic_v5_plus":       _v4_icon(["M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"]),
    "ic_v5_minus":      _v4_icon(["M19,13H5v-2h14v2z"]),
    "ic_v5_search":     _v4_icon(["M15.5,14h-0.79l-0.28,-0.27C15.41,12.59 16,11.11 16,9.5 16,5.91 13.09,3 9.5,3S3,5.91 3,9.5 5.91,16 9.5,16c1.61,0 3.09,-0.59 4.23,-1.57l0.27,0.28v0.79l5,4.99L20.49,19l-4.99,-5zm-6,0C7.01,14 5,11.99 5,9.5S7.01,5 9.5,5 14,7.01 14,9.5 11.99,14 9.5,14z"]),
    "ic_v5_send":       _v4_icon(["M2.01,21L23,12 2.01,3 2,10l15,2 -15,2z"]),
    "ic_v5_bluetooth":  _v4_icon(["M17.71,7.71L12,2h-1v7.59L6.41,5 5,6.41 10.59,12 5,17.59 6.41,19 11,14.41V22h1l5.71,-5.71 -4.3,-4.29 4.3,-4.29zM13,5.83l1.88,1.88L13,9.59V5.83zm1.88,10.46L13,18.17v-3.76l1.88,1.88z"]),
    "ic_v5_sun":        _v4_icon(["M6.76,4.84l-1.8,-1.79 -1.41,1.41 1.79,1.79 1.42,-1.41zM4,10.5H1v2h3v-2zm9,-9.95h-2V3.5h2V0.55zm7.45,3.91l-1.41,-1.41 -1.79,1.79 1.41,1.41 1.79,-1.79zm-3.21,13.7l1.79,1.8 1.41,-1.41 -1.8,-1.79 -1.4,1.4zM20,10.5v2h3v-2h-3zm-8,-5c-3.31,0 -6,2.69 -6,6s2.69,6 6,6 6,-2.69 6,-6 -2.69,-6 -6,-6zm-1,16.95h2V19.5h-2v2.95zm-7.45,-3.91l1.41,1.41 1.79,-1.8 -1.41,-1.41 -1.79,1.8z"]),
    "ic_v5_map2d":      _v4_icon(["M20.5,3l-0.16,0.03L15,5.1 9,3 3.36,4.9c-0.21,0.07 -0.36,0.25 -0.36,0.48V20.5c0,0.28 0.22,0.5 0.5,0.5l0.16,-0.03L9,18.9l6,2.1 5.64,-1.9c0.21,-0.07 0.36,-0.25 0.36,-0.48V3.5c0,-0.28 -0.22,-0.5 -0.5,-0.5zM15,19l-6,-2.11V5l6,2.11V19z"]),
}

# manovre aggiuntive (arrivo, tieni sinistra/destra, inversione)
MANEUVER_ICONS.update({
    "ic_turn_finish":     _arrow("M14.4,6L14,4H5v17h2v-7h5.6l0.4,2h7V6z"),
    "ic_turn_keep_left":  _arrow("M9,3L4,8h3.5v13h3V8H14L9,3z M16,10h2v11h-2z"),
    "ic_turn_keep_right": _arrow("M15,3l5,5h-3.5v13h-3V8H10L15,3z M6,10h2v11H6z"),
    "ic_turn_uturn":      _arrow("M18,13c0,3.31 -2.69,6 -6,6s-6,-2.69 -6,-6V7H3l4,-5 4,5H8v6c0,2.21 1.79,4 4,4s4,-1.79 4,-4V3h2v10z"),
})

def _v5_shape(body, shape="rectangle"):
    return _XML_HEAD + '<shape ' + _NS + ' android:shape="' + shape + '">\n' + body + '</shape>'

V5_DRAWABLES = dict(V5_ICONS)
V5_DRAWABLES.update({
    # scheda della manovra: verde-acqua profondo con bordo luminoso
    "bg_nav_card":
        _XML_HEAD +
        '<layer-list ' + _NS + '>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="315"\n'
        '                android:startColor="#F2007A5E" android:endColor="#F2003A4D"/>\n'
        '            <corners android:radius="26dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:bottom="44dp">\n'
        '        <shape android:shape="rectangle">\n'
        '            <gradient android:type="linear" android:angle="270"\n'
        '                android:startColor="#22FFFFFF" android:endColor="#00FFFFFF"/>\n'
        '            <corners android:radius="26dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#00000000"/>\n'
        '            <stroke android:width="1.5dp" android:color="#8800FF88"/>\n'
        '            <corners android:radius="26dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</layer-list>',
    "bg_then_chip": _v5_shape('    <solid android:color="#E6003A4D"/>\n'
                              '    <stroke android:width="1dp" android:color="#5500FF88"/>\n'
                              '    <corners android:radius="16dp"/>\n'),
    "bg_disc_glass": _v5_shape('    <solid android:color="#26FFFFFF"/>\n'
                               '    <stroke android:width="1dp" android:color="#55FFFFFF"/>\n', "oval"),
    # pulsanti tondi in vetro (con onda al tocco)
    "bg_fab_glass":
        _XML_HEAD +
        '<ripple ' + _NS + ' android:color="#5500E5FF">\n'
        '    <item>\n'
        '        <shape android:shape="oval">\n'
        '            <solid android:color="#E6101A2B"/>\n'
        '            <stroke android:width="1dp" android:color="#5500E5FF"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</ripple>',
    "bg_fab_red":
        _XML_HEAD +
        '<ripple ' + _NS + ' android:color="#55FFFFFF">\n'
        '    <item>\n'
        '        <shape android:shape="oval">\n'
        '            <gradient android:type="linear" android:angle="270"\n'
        '                android:startColor="#FF2D55" android:endColor="#C2002A"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</ripple>',
    "bg_speed_bubble": _v5_shape('    <solid android:color="#F20B1424"/>\n'
                                 '    <stroke android:width="3dp" android:color="#AA00E5FF"/>\n', "oval"),
    "bg_scrim_top": _v5_shape('    <gradient android:type="linear" android:angle="270"\n'
                              '        android:startColor="#CC050A14" android:endColor="#00050A14"/>\n'),
    "bg_scrim_bottom": _v5_shape('    <gradient android:type="linear" android:angle="90"\n'
                                 '        android:startColor="#E6050A14" android:endColor="#00050A14"/>\n'),
    "bg_sheet_v5":
        _XML_HEAD +
        '<layer-list ' + _NS + '>\n'
        '    <item>\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#F70B1424"/>\n'
        '            <corners android:topLeftRadius="28dp" android:topRightRadius="28dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:bottom="200dp">\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#00000000"/>\n'
        '            <stroke android:width="1dp" android:color="#4400E5FF"/>\n'
        '            <corners android:topLeftRadius="28dp" android:topRightRadius="28dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '</layer-list>',
    "bg_progress_neon":
        _XML_HEAD +
        '<layer-list ' + _NS + '>\n'
        '    <item android:id="@android:id/background">\n'
        '        <shape android:shape="rectangle">\n'
        '            <solid android:color="#2200E5FF"/>\n'
        '            <corners android:radius="3dp"/>\n'
        '        </shape>\n'
        '    </item>\n'
        '    <item android:id="@android:id/progress">\n'
        '        <clip>\n'
        '            <shape android:shape="rectangle">\n'
        '                <gradient android:type="linear" android:angle="0"\n'
        '                    android:startColor="#00FF88" android:endColor="#00E5FF"/>\n'
        '                <corners android:radius="3dp"/>\n'
        '            </shape>\n'
        '        </clip>\n'
        '    </item>\n'
        '</layer-list>',
})

def _v5_fab(vid, icon, size="50dp", tint="#E8F4FD", bg="bg_fab_glass", margin_bottom="10dp", desc=""):
    return ('<ImageButton android:id="@+id/' + vid + '"\n'
            '    android:layout_width="' + size + '" android:layout_height="' + size + '"\n'
            '    android:src="@drawable/' + icon + '" android:tint="' + tint + '" android:padding="12dp"\n'
            '    android:scaleType="fitCenter" android:background="@drawable/' + bg + '"\n'
            '    android:elevation="6dp" android:layout_marginBottom="' + margin_bottom + '"\n'
            '    android:contentDescription="' + (desc or vid) + '"/>\n')

def _v5_profile_btn(vid, icon, desc):
    return ('<ImageButton android:id="@+id/' + vid + '"\n'
            '    android:layout_width="44dp" android:layout_height="40dp" android:padding="8dp"\n'
            '    android:src="@drawable/' + icon + '" android:tint="#E8F4FD" android:scaleType="fitCenter"\n'
            '    android:background="@drawable/bg_chip_off" android:layout_marginStart="6dp"\n'
            '    android:contentDescription="' + desc + '"/>\n')

# ---------------------------------------------------------------- NAVIGATORE v5
LAYOUT_NAVIGATION = (_XML_HEAD +
    '<FrameLayout ' + _NS + '\n'
    '    android:layout_width="match_parent" android:layout_height="match_parent"\n'
    '    android:background="#050A14">\n'
    '    <FrameLayout android:id="@+id/nav_map_container"\n'
    '        android:layout_width="match_parent" android:layout_height="match_parent"/>\n'
    '    <View android:layout_width="match_parent" android:layout_height="230dp"\n'
    '        android:layout_gravity="top" android:background="@drawable/bg_scrim_top"/>\n'
    '    <View android:layout_width="match_parent" android:layout_height="240dp"\n'
    '        android:layout_gravity="bottom" android:background="@drawable/bg_scrim_bottom"/>\n'
    # scheda manovra
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:layout_gravity="top" android:orientation="vertical"\n'
    '        android:layout_marginStart="12dp" android:layout_marginEnd="12dp" android:layout_marginTop="14dp">\n'
    '        <LinearLayout android:id="@+id/panel_nav_top" android:layout_width="match_parent"\n'
    '            android:layout_height="wrap_content" android:orientation="horizontal"\n'
    '            android:gravity="center_vertical" android:padding="16dp"\n'
    '            android:background="@drawable/bg_nav_card" android:elevation="12dp">\n'
    '            <ImageView android:id="@+id/iv_nav_maneuver" android:layout_width="66dp"\n'
    '                android:layout_height="66dp" android:padding="8dp" android:tint="#FFFFFF"\n'
    '                android:src="@drawable/ic_turn_straight" android:background="@drawable/bg_disc_glass"\n'
    '                android:contentDescription="Manovra"/>\n'
    '            <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"\n'
    '                android:layout_weight="1" android:orientation="vertical" android:layout_marginStart="14dp">\n'
    '                <TextView android:id="@+id/tv_nav_distance_next" android:layout_width="wrap_content"\n'
    '                    android:layout_height="wrap_content" android:text="--" android:textColor="#FFFFFF"\n'
    '                    android:textSize="34sp" android:textStyle="bold" android:fontFamily="sans-serif-condensed"\n'
    '                    android:shadowColor="#8800FF88" android:shadowRadius="14"/>\n'
    '                <TextView android:id="@+id/tv_nav_instruction" android:layout_width="match_parent"\n'
    '                    android:layout_height="wrap_content" android:text="Calcolo del percorso..."\n'
    '                    android:textColor="#D8FFF0" android:textSize="16sp" android:maxLines="2"\n'
    '                    android:ellipsize="end"/>\n'
    '            </LinearLayout>\n'
    '        </LinearLayout>\n'
    '        <LinearLayout android:id="@+id/panel_nav_then" android:layout_width="wrap_content"\n'
    '            android:layout_height="wrap_content" android:orientation="horizontal"\n'
    '            android:gravity="center_vertical" android:paddingStart="12dp" android:paddingEnd="14dp"\n'
    '            android:paddingTop="8dp" android:paddingBottom="8dp" android:layout_marginTop="6dp"\n'
    '            android:layout_marginStart="10dp" android:background="@drawable/bg_then_chip"\n'
    '            android:visibility="gone">\n'
    '            <ImageView android:id="@+id/iv_nav_then" android:layout_width="22dp"\n'
    '                android:layout_height="22dp" android:tint="#FFFFFF" android:contentDescription="Poi"/>\n'
    '            <TextView android:id="@+id/tv_nav_then" android:layout_width="wrap_content"\n'
    '                android:layout_height="wrap_content" android:textColor="#FFFFFF" android:textSize="13sp"\n'
    '                android:textStyle="bold" android:layout_marginStart="8dp"/>\n'
    '        </LinearLayout>\n'
    '        <TextView android:id="@+id/tv_nav_weather" android:layout_width="wrap_content"\n'
    '            android:layout_height="wrap_content" android:layout_marginTop="6dp" android:layout_marginStart="10dp"\n'
    '            android:paddingStart="12dp" android:paddingEnd="12dp" android:paddingTop="6dp"\n'
    '            android:paddingBottom="6dp" android:textColor="#E8F4FD" android:textSize="12sp"\n'
    '            android:background="@drawable/bg_chip_off" android:visibility="gone"/>\n'
    '    </LinearLayout>\n'
    # pulsanti laterali
    '    <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '        android:layout_gravity="end|center_vertical" android:orientation="vertical"\n'
    '        android:gravity="center_horizontal" android:layout_marginEnd="12dp">\n'
    + _v5_fab("btn_nav_voice", "ic_v5_volume", desc="Voce")
    + _v5_fab("btn_nav_3d", "ic_v5_cube", margin_bottom="0dp", desc="Vista 3D") +
    '        <TextView android:id="@+id/tv_nav_engine" android:layout_width="wrap_content"\n'
    '            android:layout_height="wrap_content" android:text="3D" android:textColor="#00E5FF"\n'
    '            android:textSize="10sp" android:textStyle="bold" android:layout_marginBottom="8dp"/>\n'
    + _v5_fab("btn_nav_overview", "ic_v5_route", desc="Panoramica")
    + _v5_fab("btn_nav_steps", "ic_v5_list", desc="Elenco manovre") +
    '    </LinearLayout>\n'
    # tachimetro + riprendi
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:layout_gravity="bottom" android:orientation="horizontal" android:gravity="bottom"\n'
    '        android:layout_marginBottom="176dp" android:layout_marginStart="14dp" android:layout_marginEnd="14dp">\n'
    '        <LinearLayout android:layout_width="76dp" android:layout_height="76dp"\n'
    '            android:orientation="vertical" android:gravity="center"\n'
    '            android:background="@drawable/bg_speed_bubble" android:elevation="8dp">\n'
    '            <TextView android:id="@+id/tv_nav_speed" android:layout_width="wrap_content"\n'
    '                android:layout_height="wrap_content" android:text="0" android:textColor="#FFFFFF"\n'
    '                android:textSize="26sp" android:textStyle="bold" android:fontFamily="sans-serif-condensed"/>\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:text="km/h" android:textColor="#8FB3D0" android:textSize="10sp"/>\n'
    '        </LinearLayout>\n'
    '        <View android:layout_width="0dp" android:layout_height="1dp" android:layout_weight="1"/>\n'
    '        <LinearLayout android:id="@+id/btn_nav_recenter" android:layout_width="wrap_content"\n'
    '            android:layout_height="48dp" android:orientation="horizontal" android:gravity="center_vertical"\n'
    '            android:paddingStart="14dp" android:paddingEnd="18dp" android:background="@drawable/bg_tile_cyan"\n'
    '            android:clickable="true" android:focusable="true" android:elevation="8dp" android:visibility="gone">\n'
    '            <ImageView android:layout_width="22dp" android:layout_height="22dp"\n'
    '                android:src="@drawable/ic_v5_gps" android:tint="#00E5FF" android:contentDescription="Riprendi"/>\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:text="RIPRENDI" android:textColor="#E8F4FD" android:textSize="13sp"\n'
    '                android:textStyle="bold" android:layout_marginStart="8dp"/>\n'
    '        </LinearLayout>\n'
    '    </LinearLayout>\n'
    # pannello in basso
    '    <LinearLayout android:id="@+id/panel_nav_bottom" android:layout_width="match_parent"\n'
    '        android:layout_height="wrap_content" android:layout_gravity="bottom"\n'
    '        android:orientation="vertical" android:paddingStart="16dp" android:paddingEnd="16dp"\n'
    '        android:paddingTop="14dp" android:paddingBottom="18dp" android:background="@drawable/bg_sheet_v5"\n'
    '        android:elevation="16dp">\n'
    '        <ProgressBar android:id="@+id/pb_nav_progress" style="?android:attr/progressBarStyleHorizontal"\n'
    '            android:layout_width="match_parent" android:layout_height="6dp" android:max="1000"\n'
    '            android:progress="0" android:progressDrawable="@drawable/bg_progress_neon"/>\n'
    '        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '            android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginTop="12dp">\n'
    + _v5_fab("btn_nav_close", "ic_v5_close", "48dp", "#FFFFFF", "bg_fab_red", "0dp", "Termina") +
    '            <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"\n'
    '                android:layout_weight="1" android:orientation="vertical" android:gravity="center_horizontal">\n'
    '                <TextView android:id="@+id/tv_nav_eta" android:layout_width="wrap_content"\n'
    '                    android:layout_height="wrap_content" android:text="--" android:textColor="#00FF88"\n'
    '                    android:textSize="28sp" android:textStyle="bold" android:fontFamily="sans-serif-condensed"/>\n'
    '                <TextView android:id="@+id/tv_nav_total_dist" android:layout_width="wrap_content"\n'
    '                    android:layout_height="wrap_content" android:textColor="#8FB3D0" android:textSize="13sp"/>\n'
    '            </LinearLayout>\n'
    '            <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:orientation="horizontal">\n'
    + _v5_profile_btn("btn_nav_profile_car", "ic_v5_car", "Auto")
    + _v5_profile_btn("btn_nav_profile_bike", "ic_v5_bike", "Bici")
    + _v5_profile_btn("btn_nav_profile_foot", "ic_v5_walk", "A piedi") +
    '            </LinearLayout>\n'
    '        </LinearLayout>\n'
    '        <androidx.recyclerview.widget.RecyclerView android:id="@+id/rv_nav_steps"\n'
    '            android:layout_width="match_parent" android:layout_height="240dp"\n'
    '            android:layout_marginTop="12dp" android:visibility="gone"/>\n'
    '    </LinearLayout>\n'
    # costruzione rete
    '    <LinearLayout android:id="@+id/overlay_nav_build" android:layout_width="match_parent"\n'
    '        android:layout_height="match_parent" android:orientation="vertical" android:gravity="center"\n'
    '        android:padding="32dp" android:background="#E6050A14" android:clickable="true"\n'
    '        android:focusable="true" android:visibility="gone">\n'
    '        <ProgressBar android:id="@+id/pb_nav_build" android:layout_width="64dp"\n'
    '            android:layout_height="64dp" android:indeterminateTint="#00E5FF"/>\n'
    '        <TextView android:id="@+id/tv_nav_build_status" android:layout_width="wrap_content"\n'
    '            android:layout_height="wrap_content" android:layout_marginTop="20dp" android:gravity="center"\n'
    '            android:textColor="#E8F4FD" android:textSize="15sp" android:lineSpacingMultiplier="1.3"/>\n'
    '    </LinearLayout>\n'
    '</FrameLayout>')

LAYOUT_ITEM_NAV_STEP = (_XML_HEAD +
    '<LinearLayout ' + _NS + '\n'
    '    android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '    android:orientation="horizontal" android:paddingTop="10dp" android:paddingBottom="10dp"\n'
    '    android:paddingStart="6dp" android:paddingEnd="6dp" android:gravity="center_vertical">\n'
    '    <ImageView android:id="@+id/iv_step_icon" android:layout_width="30dp" android:layout_height="30dp"\n'
    '        android:padding="4dp" android:tint="#00E5FF" android:background="@drawable/bg_disc_cyan"\n'
    '        android:contentDescription="Manovra"/>\n'
    '    <TextView android:id="@+id/tv_step_text"\n'
    '        android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"\n'
    '        android:layout_marginStart="12dp" android:textColor="#E8F4FD" android:textSize="14sp"/>\n'
    '    <TextView android:id="@+id/tv_step_dist"\n'
    '        android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '        android:textColor="#00E5FF" android:textSize="13sp" android:textStyle="bold"/>\n'
    '</LinearLayout>')

# ---------------------------------------------------------------- MAPPA 3D
LAYOUT_MAP3D = (_XML_HEAD +
    '<FrameLayout ' + _NS + '\n'
    '    android:layout_width="match_parent" android:layout_height="match_parent"\n'
    '    android:background="#050A14">\n'
    '    <FrameLayout android:id="@+id/map3d_container"\n'
    '        android:layout_width="match_parent" android:layout_height="match_parent"/>\n'
    '    <View android:layout_width="match_parent" android:layout_height="130dp"\n'
    '        android:layout_gravity="top" android:background="@drawable/bg_scrim_top"/>\n'
    '    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"\n'
    '        android:layout_gravity="top" android:orientation="horizontal" android:gravity="center_vertical"\n'
    '        android:padding="12dp">\n'
    '        <ImageView android:id="@+id/btn_map3d_back" android:layout_width="46dp" android:layout_height="46dp"\n'
    '            android:padding="11dp" android:src="@drawable/ic_v4_back" android:tint="#E8F4FD"\n'
    '            android:background="@drawable/bg_fab_glass" android:clickable="true" android:focusable="true"\n'
    '            android:contentDescription="Indietro"/>\n'
    '        <LinearLayout android:id="@+id/btn_map3d_search" android:layout_width="0dp"\n'
    '            android:layout_height="46dp" android:layout_weight="1" android:orientation="horizontal"\n'
    '            android:gravity="center_vertical" android:paddingStart="14dp" android:layout_marginStart="10dp"\n'
    '            android:layout_marginEnd="10dp" android:background="@drawable/bg_searchbar"\n'
    '            android:clickable="true" android:focusable="true" android:elevation="6dp">\n'
    '            <ImageView android:layout_width="20dp" android:layout_height="20dp"\n'
    '                android:src="@drawable/ic_v5_search" android:tint="#00E5FF" android:contentDescription="Cerca"/>\n'
    '            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '                android:layout_marginStart="10dp" android:text="Cerca via, civico, citta..."\n'
    '                android:textColor="#8FB3D0" android:textSize="14sp"/>\n'
    '        </LinearLayout>\n'
    '        <ImageView android:id="@+id/btn_map3d_2d" android:layout_width="46dp" android:layout_height="46dp"\n'
    '            android:padding="12dp" android:src="@drawable/ic_v5_map2d" android:tint="#E8F4FD"\n'
    '            android:background="@drawable/bg_fab_glass" android:clickable="true" android:focusable="true"\n'
    '            android:contentDescription="Mappa 2D con strumenti"/>\n'
    '    </LinearLayout>\n'
    '    <TextView android:id="@+id/tv_map3d_hint" android:layout_width="wrap_content"\n'
    '        android:layout_height="wrap_content" android:layout_gravity="top|center_horizontal"\n'
    '        android:layout_marginTop="76dp" android:layout_marginStart="24dp" android:layout_marginEnd="24dp"\n'
    '        android:padding="12dp" android:gravity="center" android:textColor="#E8F4FD" android:textSize="13sp"\n'
    '        android:background="@drawable/bg_hint" android:visibility="gone"/>\n'
    # colonna destra
    '    <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '        android:layout_gravity="top|end" android:orientation="vertical" android:layout_marginTop="140dp"\n'
    '        android:layout_marginEnd="12dp">\n'
    '        <FrameLayout android:id="@+id/btn_map3d_compass" android:layout_width="50dp"\n'
    '            android:layout_height="50dp" android:background="@drawable/bg_fab_glass" android:clickable="true"\n'
    '            android:focusable="true" android:elevation="6dp" android:layout_marginBottom="10dp">\n'
    '            <ImageView android:id="@+id/iv_map3d_compass" android:layout_width="34dp"\n'
    '                android:layout_height="34dp" android:layout_gravity="center"\n'
    '                android:src="@drawable/ic_compass_needle" android:contentDescription="Bussola: tocca per il nord"/>\n'
    '        </FrameLayout>\n'
    + _v5_fab("btn_map3d_tilt", "ic_v5_cube", desc="Inclina 3D")
    + _v5_fab("btn_map3d_buildings", "ic_v5_building", desc="Edifici 3D")
    + _v5_fab("btn_map3d_theme", "ic_v5_layers", desc="Tema mappa") +
    '    </LinearLayout>\n'
    # zoom e posizione
    '    <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
    '        android:layout_gravity="bottom|end" android:orientation="vertical" android:gravity="center_horizontal"\n'
    '        android:layout_marginEnd="12dp" android:layout_marginBottom="22dp">\n'
    + _v5_fab("btn_map3d_zoom_in", "ic_v5_plus", desc="Zoom avanti")
    + _v5_fab("btn_map3d_zoom_out", "ic_v5_minus", desc="Zoom indietro") +
    '        <FrameLayout android:id="@+id/btn_map3d_follow" android:layout_width="62dp"\n'
    '            android:layout_height="62dp" android:background="@drawable/bg_tile_cyan" android:clickable="true"\n'
    '            android:focusable="true" android:elevation="8dp">\n'
    '            <ImageView android:id="@+id/iv_map3d_follow" android:layout_width="30dp"\n'
    '                android:layout_height="30dp" android:layout_gravity="center" android:alpha="0.55"\n'
    '                android:src="@drawable/ic_v5_gps" android:tint="#00E5FF"\n'
    '                android:contentDescription="Seguimi"/>\n'
    '        </FrameLayout>\n'
    '    </LinearLayout>\n'
    '    <TextView android:id="@+id/tv_map3d_info" android:layout_width="wrap_content"\n'
    '        android:layout_height="wrap_content" android:layout_gravity="bottom|start"\n'
    '        android:layout_marginStart="12dp" android:layout_marginBottom="26dp" android:paddingStart="12dp"\n'
    '        android:paddingEnd="12dp" android:paddingTop="6dp" android:paddingBottom="6dp"\n'
    '        android:textColor="#00E5FF" android:textSize="11sp" android:textStyle="bold"\n'
    '        android:background="@drawable/bg_chip_off"/>\n'
    '</FrameLayout>')

# <<< V5 NAVIGATORE 3D

# ============================================================
#  FILE MAP + FUNZIONI BUILDER (multipiattaforma v3.0)
# ============================================================
def build_java_file_map():
    return {
        f"{PKG_ROOT}/OfflineGpsApp.java":        OFFLINE_GPS_APP,
        f"{PKG_ROOT}/AppConfig.java":            APP_CONFIG,
        f"{PKG_DATA}/WaypointEntity.java":       WAYPOINT_ENTITY,
        f"{PKG_DATA}/WaypointDao.java":          WAYPOINT_DAO,
        f"{PKG_DATA}/TrackPointEntity.java":     TRACK_POINT_ENTITY,
        f"{PKG_DATA}/TrackDao.java":             TRACK_DAO,
        f"{PKG_DATA}/GpsDatabase.java":          GPS_DATABASE,
        f"{PKG_DATA}/HistoryEntity.java":        HISTORY_ENTITY,
        f"{PKG_DATA}/HistoryDao.java":           HISTORY_DAO,
        f"{PKG_GPS}/GpsTrackingService.java":    GPS_SERVICE,
        f"{PKG_GPS}/CompassManager.java":        COMPASS_MANAGER,
        f"{PKG_MAP}/MapController.java":         MAP_CONTROLLER,
        f"{PKG_UTIL}/GpxExporter.java":          GPX_EXPORTER,
        f"{PKG_ROUTING}/RoutingEngine.java":     ROUTING_ENGINE,
        f"{PKG_ROUTING}/OfflineGeocoder.java":   OFFLINE_GEOCODER,
        f"{PKG_ROUTING}/WeatherService.java":    WEATHER_SERVICE,
        "javax/lang/model/SourceVersion.java":   SOURCE_VERSION_STUB,
        f"{PKG_UI}/HudView.java":                HUD_VIEW,
        f"{PKG_UI}/RegionMapper.java":           REGION_MAPPER,
        f"{PKG_UI}/SplashActivity.java":         SPLASH_ACTIVITY,
        f"{PKG_UI}/MainActivity.java":           MAIN_ACTIVITY,
        f"{PKG_UI}/MapActivity.java":            MAP_ACTIVITY,
        f"{PKG_UI}/NavigationActivity.java":     NAVIGATION_ACTIVITY,
        f"{PKG_UI}/AddressSearchActivity.java":  ADDRESS_SEARCH_ACTIVITY,
        f"{PKG_UI}/DownloadActivity.java":       DOWNLOAD_ACTIVITY,
        f"{PKG_UI}/WaypointsActivity.java":      WAYPOINTS_ACTIVITY,
        f"{PKG_UI}/StatsActivity.java":          STATS_ACTIVITY,
        f"{PKG_UI}/ToolsActivity.java":          TOOLS_ACTIVITY,
        f"{PKG_UI}/SurvivalActivity.java":       SURVIVAL_ACTIVITY,
        f"{PKG_UI}/ProximityToolActivity.java":  PROXIMITY_TOOL_ACTIVITY,
        f"{PKG_UI}/CoordsToolActivity.java":     COORDS_TOOL_ACTIVITY,
        f"{PKG_UI}/DaylightToolActivity.java":   DAYLIGHT_TOOL_ACTIVITY,
        f"{PKG_UI}/SignalMirrorActivity.java":   SIGNAL_MIRROR_ACTIVITY,
        f"{PKG_UI}/WhistleActivity.java":        WHISTLE_ACTIVITY,
        f"{PKG_UI}/BacktrackActivity.java":      BACKTRACK_ACTIVITY,
        f"{PKG_UI}/AreaToolActivity.java":       AREA_TOOL_ACTIVITY,
        f"{PKG_UI}/TrackRecorderActivity.java":  TRACK_RECORDER_ACTIVITY,
        f"{PKG_UI}/UnitConvActivity.java":       UNIT_CONV_ACTIVITY,
        f"{PKG_UI}/MultiTimerActivity.java":     MULTI_TIMER_ACTIVITY,
        f"{PKG_UI}/SlopeToolActivity.java":      SLOPE_TOOL_ACTIVITY,
        f"{PKG_UI}/MorseActivity.java":          MORSE_ACTIVITY,
        f"{PKG_UI}/SurvGuideActivity.java":      SURV_GUIDE_ACTIVITY,
        f"{PKG_UI}/HydrationActivity.java":      HYDRATION_ACTIVITY,
        f"{PKG_UI}/SunCompassActivity.java":     SUN_COMPASS_ACTIVITY,
        f"{PKG_UI}/ChecklistActivity.java":      CHECKLIST_ACTIVITY,
        f"{PKG_UI}/GeoNotesActivity.java":       GEONOTES_ACTIVITY,
        f"{PKG_UI}/GotoCoordsActivity.java":     GOTOCOORDS_ACTIVITY,
        f"{PKG_UI}/FlashlightActivity.java":     FLASHLIGHT_ACTIVITY,
        f"{PKG_UI}/CalcActivity.java":           CALC_ACTIVITY,
        f"{PKG_UI}/NotepadActivity.java":        NOTEPAD_ACTIVITY,
        f"{PKG_UI}/CurrencyActivity.java":       CURRENCY_ACTIVITY,
        f"{PKG_UI}/QrPositionActivity.java":     QR_POSITION_ACTIVITY,
        f"{PKG_UI}/ChatActivity.java":           CHAT_ACTIVITY,
        f"{PKG_UI}/EmergencyActivity.java":      EMERGENCY_ACTIVITY,
        f"{PKG_UI}/AltimeterActivity.java":      ALTIMETER_ACTIVITY,
        f"{PKG_UI}/BatterySaverActivity.java":   BATTERY_SAVER_ACTIVITY,
        # NUOVI v3.0
        f"{PKG_UI}/MoonPhaseActivity.java":      MOON_PHASE_ACTIVITY,
        f"{PKG_UI}/MetalDetectorActivity.java":  METAL_DETECTOR_ACTIVITY,
        f"{PKG_UI}/NightVisionActivity.java":    NIGHT_VISION_ACTIVITY,
        f"{PKG_UI}/HeatIndexActivity.java":      HEAT_INDEX_ACTIVITY,
        f"{PKG_UI}/FirstAidActivity.java":       FIRST_AID_ACTIVITY,
        f"{PKG_UI}/PaceCalcActivity.java":       PACE_CALC_ACTIVITY,
        f"{PKG_UI}/SpeedHudActivity.java":       SPEED_HUD_ACTIVITY,
        # NUOVI v4.0 — SENTINELLA CIELO + grafica
        f"{PKG_SKY}/RemoteIdParser.java":        SKY_REMOTE_ID_PARSER,
        f"{PKG_SKY}/Fft.java":                   SKY_FFT,
        f"{PKG_SKY}/AcousticAnalyzer.java":      SKY_ACOUSTIC_ANALYZER,
        f"{PKG_SKY}/AcousticDetector.java":      SKY_ACOUSTIC_DETECTOR,
        f"{PKG_SKY}/DroneTrack.java":            SKY_DRONE_TRACK,
        f"{PKG_SKY}/SkyState.java":              SKY_STATE,
        f"{PKG_SKY}/RemoteIdScanner.java":       SKY_REMOTE_ID_SCANNER,
        f"{PKG_SKY}/SkySpotStore.java":          SKY_SPOT_STORE,
        f"{PKG_SKY}/HeadingSensor.java":         SKY_HEADING_SENSOR,
        f"{PKG_UI}/UiFx.java":                   UI_FX,
        f"{PKG_UI}/SkyUi.java":                  SKY_UI,
        f"{PKG_UI}/SkyRadarView.java":           SKY_RADAR_VIEW,
        f"{PKG_UI}/SpectrogramView.java":        SPECTROGRAM_VIEW,
        f"{PKG_UI}/NeonGaugeView.java":          NEON_GAUGE_VIEW,
        f"{PKG_UI}/AuroraView.java":             AURORA_VIEW,
        f"{PKG_UI}/SkyWatchActivity.java":       SKY_WATCH_ACTIVITY,
        f"{PKG_UI}/AcousticDetectorActivity.java": ACOUSTIC_DETECTOR_ACTIVITY,
        f"{PKG_UI}/SkySpotActivity.java":        SKY_SPOT_ACTIVITY,
        f"{PKG_UI}/SightingCheckActivity.java":  SIGHTING_CHECK_ACTIVITY,
        # NUOVI v5.0 — mappa 3D, navigazione, sole
        f"{PKG_ROUTING}/NavCore.java":           NAV_CORE,
        f"{PKG_UTIL}/SunCalc.java":              SUN_CALC,
        f"{PKG_MAP}/MapEngine.java":             MAP_ENGINE,
        f"{PKG_MAP}/VtmEngine.java":             VTM_ENGINE,
        f"{PKG_MAP}/MapsforgeEngine.java":       MAPSFORGE_ENGINE,
        f"{PKG_MAP}/MapEngines.java":            MAP_ENGINES,
        f"{PKG_UI}/Map3DActivity.java":          MAP3D_ACTIVITY,
    }

def build_layout_map():
    return {
        "activity_splash.xml":         LAYOUT_SPLASH,
        "activity_main.xml":           LAYOUT_MAIN,
        "activity_map.xml":            LAYOUT_MAP,
        "activity_navigation.xml":     LAYOUT_NAVIGATION,
        "activity_download.xml":       LAYOUT_DOWNLOAD,
        "activity_waypoints.xml":      LAYOUT_WAYPOINTS,
        "activity_stats.xml":          LAYOUT_STATS,
        "activity_tools.xml":          LAYOUT_TOOLS,
        "activity_survival.xml":       LAYOUT_SURVIVAL,
        "activity_proximity.xml":      LAYOUT_PROXIMITY,
        "activity_coords.xml":         LAYOUT_COORDS,
        "activity_daylight.xml":       LAYOUT_DAYLIGHT,
        "activity_mirror.xml":         LAYOUT_MIRROR,
        "activity_whistle.xml":        LAYOUT_WHISTLE,
        "activity_backtrack.xml":      LAYOUT_BACKTRACK,
        "activity_area.xml":           LAYOUT_AREA,
        "activity_recorder.xml":       LAYOUT_RECORDER,
        "activity_unitconv.xml":       LAYOUT_UNITCONV,
        "activity_timer.xml":          LAYOUT_TIMER,
        "activity_slope.xml":          LAYOUT_SLOPE,
        "activity_morse.xml":          LAYOUT_MORSE,
        "activity_survguide.xml":      LAYOUT_SURVGUIDE,
        "activity_hydration.xml":      LAYOUT_HYDRATION,
        "activity_suncompass.xml":     LAYOUT_SUNCOMPASS,
        "activity_checklist.xml":      LAYOUT_CHECKLIST,
        "activity_geonotes.xml":       LAYOUT_GEONOTES,
        "activity_gotocoords.xml":     LAYOUT_GOTOCOORDS,
        "activity_flashlight.xml":     LAYOUT_FLASHLIGHT,
        "activity_calc.xml":           LAYOUT_CALC,
        "activity_notepad.xml":        LAYOUT_NOTEPAD,
        "activity_currency.xml":       LAYOUT_CURRENCY,
        "activity_qr.xml":             LAYOUT_QR,
        "activity_chat.xml":           LAYOUT_CHAT,
        "activity_emergency.xml":      LAYOUT_EMERGENCY,
        "activity_altimeter.xml":      LAYOUT_ALTIMETER,
        "activity_battery.xml":        LAYOUT_BATTERY,
        # NUOVI v3.0
        "activity_moon.xml":           LAYOUT_MOON,
        "activity_metal.xml":          LAYOUT_METAL,
        "activity_nightvision.xml":    LAYOUT_NIGHTVISION,
        "activity_heatindex.xml":      LAYOUT_HEATINDEX,
        "activity_firstaid.xml":       LAYOUT_FIRSTAID,
        "activity_pace.xml":           LAYOUT_PACE,
        "activity_speedhud.xml":       LAYOUT_SPEEDHUD,
        "item_waypoint.xml":           LAYOUT_ITEM_WP,
        "item_nav_step.xml":           LAYOUT_ITEM_NAV_STEP,
        "dialog_add_waypoint.xml":     DIALOG_ADD_WP,
        "dialog_navigate_coords.xml":  DIALOG_NAVIGATE_COORDS,
        "activity_address_search.xml": LAYOUT_ADDRESS_SEARCH,
        "item_address_result.xml":     LAYOUT_ITEM_ADDRESS_RESULT,
        # NUOVI v4.0
        "activity_sky_watch.xml":      LAYOUT_SKY_WATCH,
        "activity_acoustic.xml":       LAYOUT_ACOUSTIC,
        "activity_skyspot.xml":        LAYOUT_SKYSPOT,
        "activity_sighting_check.xml": LAYOUT_SIGHTING_CHECK,
        "item_spinner_dark.xml":       LAYOUT_ITEM_SPINNER_DARK,
        # NUOVI v5.0
        "activity_map3d.xml":          LAYOUT_MAP3D,
    }

IS_WINDOWS = platform.system() == "Windows"

def java_exe_name():
    return "java.exe" if IS_WINDOWS else "java"

def find_java():
    """Cerca un JDK 17/21 su Windows, Linux e macOS."""
    exe = java_exe_name()
    # 1) JAVA_HOME
    jh = os.environ.get("JAVA_HOME")
    if jh and (Path(jh) / "bin" / exe).exists():
        return Path(jh)
    # 2) cartelle standard Windows (preferisci 21, poi 17)
    if IS_WINDOWS:
        bases = [
            Path("C:/Program Files/Eclipse Adoptium"),
            Path("C:/Program Files/Java"),
            Path("C:/Program Files/Microsoft"),
            Path("C:/Program Files/Amazon Corretto"),
        ]
        for v in ("21", "17"):
            for base in bases:
                if not base.exists(): continue
                try: candidates = sorted(base.iterdir(), reverse=True)
                except Exception: continue
                for d in candidates:
                    if d.is_dir() and v in d.name.lower() and (d / "bin" / exe).exists():
                        return d
    else:
        # 3) cartelle standard Linux / macOS
        for base in (Path("/usr/lib/jvm"), Path("/Library/Java/JavaVirtualMachines")):
            if not base.exists(): continue
            try: candidates = sorted(base.iterdir(), reverse=True)
            except Exception: continue
            for d in candidates:
                for cand in (d, d / "Contents" / "Home"):
                    if (cand / "bin" / "java").exists():
                        return cand
    # 4) java nel PATH
    jb = shutil.which("java")
    if jb:
        return Path(jb).resolve().parent.parent
    return None

def find_android_sdk():
    candidates = [
        Path(os.environ.get("ANDROID_HOME", "")),
        Path(os.environ.get("ANDROID_SDK_ROOT", "")),
        Path(os.environ.get("LOCALAPPDATA", "_")) / "Android" / "Sdk",
        Path.home() / "AppData" / "Local" / "Android" / "Sdk",
        Path.home() / "Android" / "Sdk",                      # Linux
        Path.home() / "Library" / "Android" / "sdk",          # macOS
        Path("C:/Android"),
        Path("C:/android-sdk"),
    ]
    for p in candidates:
        try:
            if p.exists() and (p / "platform-tools").exists():
                return p
        except Exception:
            continue
    return None

def download_with_retry(url, dest, attempts=3):
    for i in range(attempts):
        try:
            urllib.request.urlretrieve(url, dest)
            return True
        except Exception as e:
            warn(f"  Fallito: {e}")
            if i < attempts - 1: time.sleep(2 ** i)
    return False

def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def create_project(java_path):
    title("STEP 1 - Creazione progetto OfflineGPS 3D v4.0")
    if PROJECT_DIR.exists():
        answer = input(f"\n  Directory {PROJECT_DIR.name} esiste. Sovrascrivere? (y/N): ").strip().lower()
        if answer == "y": shutil.rmtree(PROJECT_DIR); ok("Directory rimossa")
        else: ok("Uso directory esistente")

    app_src  = PROJECT_DIR / "app" / "src" / "main"
    java_src = app_src / "java"
    res_dir  = app_src / "res"

    step(1, 9, "Gradle build files")
    write_file(PROJECT_DIR / "build.gradle",               BUILD_GRADLE_PROJECT)
    write_file(PROJECT_DIR / "settings.gradle",            SETTINGS_GRADLE)
    write_file(PROJECT_DIR / "app" / "build.gradle",       BUILD_GRADLE_APP)
    write_file(PROJECT_DIR / "app" / "proguard-rules.pro", PROGUARD_RULES)
    write_file(PROJECT_DIR / "gradle" / "wrapper" / "gradle-wrapper.properties", GRADLE_WRAPPER_PROPS)
    ok("Gradle files scritti")

    step(2, 9, "Script gradlew (Windows + Linux/macOS)")
    bat = (f"@echo off\r\nset JAVA_HOME={java_path}\r\nset PATH=%JAVA_HOME%\\bin;%PATH%\r\n"
           f"\"%JAVA_HOME%\\bin\\java.exe\" -classpath \"%~dp0gradle\\wrapper\\gradle-wrapper.jar\" "
           f"org.gradle.wrapper.GradleWrapperMain %*\r\n")
    (PROJECT_DIR / "gradlew.bat").write_text(bat, encoding="utf-8")
    sh = ('#!/bin/sh\n'
          'DIR="$(cd "$(dirname "$0")" && pwd)"\n'
          'exec java -classpath "$DIR/gradle/wrapper/gradle-wrapper.jar" '
          'org.gradle.wrapper.GradleWrapperMain "$@"\n')
    gradlew = PROJECT_DIR / "gradlew"
    gradlew.write_text(sh, encoding="utf-8")
    try: os.chmod(gradlew, 0o755)
    except Exception: pass
    ok("gradlew.bat + gradlew scritti")

    step(3, 9, "Gradle wrapper JAR")
    jar = PROJECT_DIR / "gradle" / "wrapper" / "gradle-wrapper.jar"
    jar.parent.mkdir(parents=True, exist_ok=True)
    if not jar.exists():
        url = "https://raw.githubusercontent.com/gradle/gradle/v8.6.0/gradle/wrapper/gradle-wrapper.jar"
        if download_with_retry(url, jar): ok("Wrapper JAR scaricato")
        else: warn("JAR mancante - apri il progetto in Android Studio per generarlo")
    else: ok("Wrapper JAR presente")

    step(4, 9, "AndroidManifest.xml")
    write_file(app_src / "AndroidManifest.xml", MANIFEST)
    ok("Manifest scritto")

    step(5, 9, "Java source files")
    java_files = build_java_file_map()
    for rel, content in java_files.items(): write_file(java_src / rel, content)
    ok(f"{len(java_files)} Java files scritti")

    step(6, 9, "Layout XML")
    layouts = build_layout_map()
    for name, content in layouts.items(): write_file(res_dir / "layout" / name, content)
    ok(f"{len(layouts)} layout scritti")

    step(7, 9, "Resources")
    write_file(res_dir / "values"   / "strings.xml", STRINGS_XML)
    write_file(res_dir / "values"   / "themes.xml",  THEMES_XML)
    write_file(res_dir / "drawable" / "ic_gps.xml",  IC_GPS_XML)
    for icon_name, icon_xml in MANEUVER_ICONS.items():
        write_file(res_dir / "drawable" / (icon_name + ".xml"), icon_xml)
    for d_name, d_xml in UI_DRAWABLES.items():
        write_file(res_dir / "drawable" / (d_name + ".xml"), d_xml)
    # v4.0: riquadri vetro, chip, icone vettoriali e transizioni animate
    for d_name, d_xml in V4_DRAWABLES.items():
        write_file(res_dir / "drawable" / (d_name + ".xml"), d_xml)
    for a_name, a_xml in V4_ANIMS.items():
        write_file(res_dir / "anim" / (a_name + ".xml"), a_xml)
    # v5.0: icone e grafica di navigatore, mappa 3D, chat e strumenti
    for d_name, d_xml in V5_DRAWABLES.items():
        write_file(res_dir / "drawable" / (d_name + ".xml"), d_xml)
    for density in ("mdpi","hdpi","xhdpi","xxhdpi","xxxhdpi"):
        mip = res_dir / f"mipmap-{density}"
        mip.mkdir(parents=True, exist_ok=True)
        shutil.copy(res_dir/"drawable"/"ic_gps.xml", mip/"ic_launcher.xml")
        shutil.copy(res_dir/"drawable"/"ic_gps.xml", mip/"ic_launcher_round.xml")
    ok("Resources scritte")

    step(8, 9, "gradle.properties + local.properties")
    java_esc = str(java_path).replace("\\", "\\\\")
    sdk = find_android_sdk()
    write_file(PROJECT_DIR / "gradle.properties",
        f"org.gradle.jvmargs=-Xmx3072m -XX:MaxMetaspaceSize=512m\n"
        f"android.useAndroidX=true\nandroid.enableJetifier=true\n"
        f"org.gradle.java.home={java_esc}\norg.gradle.parallel=true\n"
        f"org.gradle.configuration-cache=false\n"
        f"android.suppressUnsupportedCompileSdk=34\n")
    if sdk:
        write_file(PROJECT_DIR / "local.properties",
            f"sdk.dir={str(sdk).replace(chr(92), '/')}\n")
        ok(f"SDK: {sdk}")
    else: warn("SDK non trovato - configura local.properties manualmente")

    step(9, 9, ".gitignore")
    write_file(PROJECT_DIR / ".gitignore",
        ".gradle/\nbuild/\napp/build/\nlocal.properties\n*.jks\n.idea/\n*.iml\n")
    ok(".gitignore scritto")

    jc = sum(1 for _ in java_src.rglob("*.java"))
    rc = sum(1 for _ in res_dir.rglob("*") if _.is_file())
    ok(f"Progetto creato: {jc} Java, {rc} resource files")
    ok(f"Location: {PROJECT_DIR}")

def build_apk(java_path):
    title("STEP 2 - Compilazione APK")
    env = os.environ.copy()
    env["JAVA_HOME"] = str(java_path)
    env["PATH"] = str(java_path / "bin") + os.pathsep + env.get("PATH", "")
    sdk = find_android_sdk()
    if sdk: env["ANDROID_HOME"] = str(sdk); env["ANDROID_SDK_ROOT"] = str(sdk)
    info("Prima volta: Gradle scarica le dipendenze (incluso GraphHopper) - 5-15 min con internet")
    # Assicura che il keystore di debug esista (serve alla firma v1+v2 per Samsung).
    # Android di solito lo crea da solo, ma se manca lo generiamo noi con keytool.
    try:
        ks = Path(os.path.expanduser("~")) / ".android" / "debug.keystore"
        if not ks.exists():
            ks.parent.mkdir(parents=True, exist_ok=True)
            keytool = java_path / "bin" / ("keytool.exe" if IS_WINDOWS else "keytool")
            subprocess.run(
                f'"{keytool}" -genkeypair -v -keystore "{ks}" -storepass android '
                f'-keypass android -alias androiddebugkey -keyalg RSA -keysize 2048 '
                f'-validity 10000 -dname "CN=Android Debug,O=Android,C=US"',
                shell=True, check=True)
            ok("Keystore di debug generato (firma v1+v2)")
        else:
            ok("Keystore di debug presente")
    except Exception as e:
        warn(f"Non ho potuto generare il keystore: {e} - uso la firma di default")
    cmd = ("gradlew.bat" if IS_WINDOWS else "./gradlew") + " assembleDebug --no-daemon --stacktrace"
    try:
        subprocess.run(cmd, shell=True, cwd=PROJECT_DIR, env=env, check=True)
        ok("BUILD SUCCESSFUL")
    except subprocess.CalledProcessError:
        err("Build fallita - vedi log sopra")
        return None
    apk = PROJECT_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    return apk if apk.exists() else None

def summarise(apk, solo_progetto=False):
    title("STEP 3 - Output")
    dest = DESKTOP / "OfflineGPS-3D-v4.0.apk"
    if apk and apk.exists():
        shutil.copy2(apk, dest)
        print(f"\n{C.BOLD}{'='*60}")
        print(f"  APK: {dest}")
        print(f"  Dimensione: {dest.stat().st_size/1_048_576:.1f} MB")
        print(f"{'='*60}{C.RESET}")
        ok("APK pronto!")
    elif solo_progetto:
        ok("Progetto generato (build saltata con --solo-progetto)")
        info(f"Per compilare: cd \"{PROJECT_DIR}\" e lancia gradlew assembleDebug")
    else:
        warn("Compila in Android Studio se il builder da riga di comando fallisce")
        info(str(PROJECT_DIR))

    print(f"\n{C.BOLD}NOVITA v4.0 - SENTINELLA CIELO:{C.RESET}")
    print(f"  {C.OK}[NEW]{C.RESET}  Scanner Remote ID droni (Bluetooth + Wi-Fi) con radar 3D")
    print(f"  {C.OK}[NEW]{C.RESET}  Avvisi a voce e vibrazione quando arriva un drone")
    print(f"  {C.OK}[NEW]{C.RESET}  Ascolto droni: riconosce le eliche dal suono (spettrogramma)")
    print(f"  {C.OK}[NEW]{C.RESET}  Segnala avvistamento con posizione anonima (~1 km)")
    print(f"  {C.OK}[NEW]{C.RESET}  'E' davvero un drone?' + guida cosa fare + verifica notizie")
    print(f"  {C.OK}[NEW]{C.RESET}  Modalita' DEMO con droni simulati")
    print(f"  {C.OK}[GUI]{C.RESET}  Home nuova: aurora animata, griglia 3D, radar vivo, riquadri vetro")
    print(f"  {C.OK}[GUI]{C.RESET}  Transizioni animate, pulsanti a molla e ripple in tutta l'app")
    print(f"  {C.OK}[GUI]{C.RESET}  Tema scuro coerente (anche i dialoghi), percorso con alone neon")
    info("Solo rilevamento passivo: niente jamming/contromisure. Non sostituisce il 112.")

    print(f"\n{C.BOLD}NOVITA v3.0:{C.RESET}")
    print(f"  {C.OK}[GUI]{C.RESET}  Home ridisegnata: card vetro + pulsanti neon 3D + griglia")
    print(f"  {C.OK}[GUI]{C.RESET}  Splash con anello neon rotante attorno al logo (ologramma)")
    print(f"  {C.OK}[GUI]{C.RESET}  Pulsante EMERGENZA rapido in home")
    print(f"  {C.OK}[NEW]{C.RESET}  Fase lunare offline (illuminazione + prossima luna piena)")
    print(f"  {C.OK}[NEW]{C.RESET}  Metal detector col magnetometro (taratura + beep)")
    print(f"  {C.OK}[NEW]{C.RESET}  Visione notturna (schermo rosso regolabile)")
    print(f"  {C.OK}[NEW]{C.RESET}  Temperatura percepita (wind chill / heat index)")
    print(f"  {C.OK}[NEW]{C.RESET}  Primo soccorso offline (emorragie, RCP, vipera...)")
    print(f"  {C.OK}[NEW]{C.RESET}  Tempi di marcia (regola di Naismith)")
    print(f"  {C.OK}[NEW]{C.RESET}  Tachimetro HUD specchiato per parabrezza")
    print(f"  {C.OK}[FIX]{C.RESET}  RICERCA v3.1: tutte le vie in ogni citta + civici dagli edifici")
    print(f"  {C.OK}[FIX]{C.RESET}  'Via Roma 10' ora trova il civico; filtro citta funzionante")
    print(f"  {C.OK}[FIX]{C.RESET}  Import file .map dal file manager (content://) ora funziona")
    print(f"  {C.OK}[FIX]{C.RESET}  Builder multipiattaforma: Windows, Linux e macOS")

    print(f"\n{C.BOLD}MAPPE ITALIA (rendering):{C.RESET}")
    maps_info = [
        ("CENTRO  277MB", "Roma, Lazio, Toscana, Umbria, Marche, Abruzzo"),
        ("SUD     309MB", "Campania, Puglia, Calabria, Basilicata, Molise"),
        ("ISOLE   169MB", "Sicilia + Sardegna"),
        ("NORD-EST 430MB","Veneto, Friuli, Trentino, Emilia-Romagna"),
        ("NORD-OVS 395MB","Lombardia, Piemonte, Liguria, Valle d'Aosta"),
    ]
    for tag, regioni in maps_info:
        print(f"  {C.OK}[{tag}]{C.RESET}  {regioni}")

    print(f"\n{C.BOLD}DATI DI ROUTING (navigazione):{C.RESET}")
    info("Scarica dalla sezione ROUTING in Download la zona che ti interessa.")
    info("La prima volta che navighi, l'app costruisce la rete stradale")
    info("(puo' richiedere diversi minuti): e' normale, succede una sola volta.")

    print(f"\n{C.BOLD}SETUP:{C.RESET}")
    info("1. Installa OfflineGPS-3D-v4.0.apk")
    info("2. Concedi permesso GPS")
    info("3. Download -> tab MAPPE -> scarica CENTRO (es. per Roma/Lazio)")
    info("4. Download -> tab ROUTING -> scarica LAZIO (routing) per la stessa zona")
    info("5. Dalla Home tocca NAVIGA -> CERCA PER INDIRIZZO, scrivi la via")
    info("6. La prima volta attendi indicizzazione indirizzi + costruzione rete")
    print()

def main():
    if IS_WINDOWS: os.system("color")
    solo_progetto = any(a in ("--solo-progetto", "--no-build") for a in sys.argv[1:])
    print(f"\n{C.BOLD}{C.CYAN}{'='*60}")
    print("  OfflineGPS 3D v4.0 - Sentinella Cielo + grafica nuova")
    print(f"{'='*60}{C.RESET}\n")

    title("Prerequisiti")
    java = find_java()
    if not java: err("JDK 17/21 non trovato -> https://adoptium.net"); sys.exit(1)
    ok(f"JDK: {java}")
    sdk = find_android_sdk()
    if sdk: ok(f"Android SDK: {sdk}")
    else:   warn("Android SDK non trovato (serve per compilare)")
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor} su {platform.system()}")
    if solo_progetto: info("Modalita --solo-progetto: genero il progetto senza compilare")

    try:
        create_project(java)
        apk = None if solo_progetto else build_apk(java)
        summarise(apk, solo_progetto)
        print(f"{C.OK}{C.BOLD}OfflineGPS 3D v4.0 - Completato!{C.RESET}\n")
    except KeyboardInterrupt:
        print(f"\n{C.WARN}Interrotto.{C.RESET}"); sys.exit(0)
    except Exception as e:
        err(f"Errore: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
