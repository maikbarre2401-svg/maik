#!/usr/bin/env python3
"""
OfflineGPS 3D v3.0 — Builder COMPLETO con NAVIGAZIONE OFFLINE (routing GraphHopper)

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

NOVITA' v3.0 (questa versione) — GUI 3D AVANZATA + NUOVI STRUMENTI:
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
        versionCode 46
        versionName "3.1.0"
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

    def vtm_version = "0.28.0"
    implementation "com.github.mapsforge.vtm:vtm:${vtm_version}"
    implementation "com.github.mapsforge.vtm:vtm-themes:${vtm_version}"
    implementation "com.github.mapsforge.vtm:vtm-android:${vtm_version}"
    runtimeOnly    "com.github.mapsforge.vtm:vtm-android:${vtm_version}:natives-armeabi-v7a"
    runtimeOnly    "com.github.mapsforge.vtm:vtm-android:${vtm_version}:natives-arm64-v8a"
    runtimeOnly    "com.github.mapsforge.vtm:vtm-android:${vtm_version}:natives-x86"
    runtimeOnly    "com.github.mapsforge.vtm:vtm-android:${vtm_version}:natives-x86_64"
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
        maven { url 'https://jitpack.io' }
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
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29"/>

    <uses-feature android:name="android.hardware.sensor.accelerometer" android:required="true"/>
    <uses-feature android:name="android.hardware.sensor.compass" android:required="false"/>
    <uses-feature android:name="android.hardware.location.gps" android:required="true"/>

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
    private Polyline trackLine;
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
        if (trackLine == null) {
            Paint paint = AndroidGraphicFactory.INSTANCE.createPaint();
            paint.setColor(0xFF00FF88); paint.setStrokeWidth(7f); paint.setStyle(Style.STROKE);
            trackLine = new Polyline(paint, AndroidGraphicFactory.INSTANCE);
            mapView.getLayerManager().getLayers().add(trackLine);
        }
        trackLine.getLatLongs().clear();
        trackLine.getLatLongs().addAll(trackPoints);
        mapView.getLayerManager().redrawLayers();
    }

    public void clearTrack() {
        trackPoints.clear();
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
            boolean alreadyBuilt = graphFolder.exists()
                && new File(graphFolder, "properties").exists();

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
            // OTTIMIZZAZIONE VELOCITA': costruiamo solo il profilo AUTO e SENZA
            // Contraction Hierarchies (CH). La CH e' la fase piu' pesante in
            // assoluto e su telefono richiede molti minuti; costruirla per 3
            // profili la triplica. Senza CH la rete si costruisce in 1-2 min e
            // il calcolo del singolo percorso resta veloce su distanze normali.
            gh.setProfiles(
                new Profile(PROFILE_CAR).setVehicle("car").setWeighting("fastest").setTurnCosts(false)
            );
            // NIENTE setCHProfiles -> usa l'algoritmo "flessibile" (nessuna
            // preparazione pesante).
            gh.setMinNetworkSize(200);
            gh.setElevationProvider(com.graphhopper.reader.dem.ElevationProvider.NOOP);

            gh.importOrLoad();
            ticking.set(false);

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

    /** Ultimo messaggio d'errore leggibile (es. punto lontano da strade). */
    private volatile String lastError = "";
    public String getLastError() { return lastError; }

    @WorkerThread
    @Nullable
    public RouteResult route(double fromLat, double fromLon, double toLat, double toLon,
            @NonNull String profile) {
        lastError = "";
        if (hopper == null) { lastError = "Rete stradale non caricata"; return null; }
        // Costruiamo solo il profilo AUTO: se arriva bici/piedi, usiamo car.
        String useProfile = PROFILE_CAR;
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
        return RouteResult.from(path, translationMap.getWithFallBack(Locale.ITALIAN));
    }

    public void close() {
        if (hopper != null) { hopper.close(); hopper = null; loadedRegionTag = null; }
    }

    public static final class RouteResult {
        public final List<double[]> points;
        public final List<NavStep> steps;
        public final double distanceMeters;
        public final long timeMillis;

        private RouteResult(List<double[]> points, List<NavStep> steps,
                double distanceMeters, long timeMillis) {
            this.points = points; this.steps = steps;
            this.distanceMeters = distanceMeters; this.timeMillis = timeMillis;
        }

        static RouteResult from(ResponsePath path, Translation tr) {
            PointList pl = path.getPoints();
            List<double[]> pts = new ArrayList<>(pl.size());
            for (int i = 0; i < pl.size(); i++) pts.add(new double[]{pl.getLat(i), pl.getLon(i)});

            List<NavStep> steps = new ArrayList<>();
            InstructionList instr = path.getInstructions();
            if (instr != null) {
                for (Instruction ins : instr) {
                    String text = ins.getTurnDescription(tr);
                    String street = ins.getName();
                    if (text == null || text.isEmpty()) text = street;
                    steps.add(new NavStep(text, street, ins.getDistance(), ins.getTime(), ins.getSign()));
                }
            }
            return new RouteResult(pts, steps, path.getDistance(), path.getTime());
        }
    }

    public static final class NavStep {
        public final String text;
        public final String streetName;
        public final double distanceMeters;
        public final long timeMillis;
        public final int sign;

        public NavStep(String text, String streetName, double distanceMeters, long timeMillis, int sign) {
            this.text = text; this.streetName = streetName; this.distanceMeters = distanceMeters;
            this.timeMillis = timeMillis; this.sign = sign;
        }

        public String formatDistance() {
            if (distanceMeters < 1000) return String.format("%.0f m", distanceMeters);
            return String.format("%.1f km", distanceMeters / 1000.0);
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
import java.io.File;
import java.util.*;

public class MainActivity extends AppCompatActivity {

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_main);
        Button btnMap   = findViewById(R.id.btn_open_map);
        Button btnDl    = findViewById(R.id.btn_download);
        Button btnWp    = findViewById(R.id.btn_waypoints);
        Button btnStat  = findViewById(R.id.btn_stats);
        Button btnNav   = findViewById(R.id.btn_navigate);
        Button btnTools = findViewById(R.id.btn_tools);
        if (btnMap  != null) btnMap.setOnClickListener(v  -> { if (checkGps()) go(MapActivity.class); });
        if (btnDl   != null) btnDl.setOnClickListener(v   -> go(DownloadActivity.class));
        if (btnWp   != null) btnWp.setOnClickListener(v   -> go(WaypointsActivity.class));
        if (btnStat != null) btnStat.setOnClickListener(v -> go(StatsActivity.class));
        if (btnTools != null) btnTools.setOnClickListener(v -> go(ToolsActivity.class));
        Button btnSurv = findViewById(R.id.btn_survival);
        if (btnSurv != null) btnSurv.setOnClickListener(v -> go(SurvivalActivity.class));
        Button btnChat = findViewById(R.id.btn_chat);
        if (btnChat != null) btnChat.setOnClickListener(v -> go(ChatActivity.class));
        Button btnEmerg = findViewById(R.id.btn_emergency);
        if (btnEmerg != null) btnEmerg.setOnClickListener(v -> go(EmergencyActivity.class));
        if (btnNav  != null) btnNav.setOnClickListener(v  -> { if (checkGps()) showNavigateDialog(); });
        updateStatus();
        if (!hasGpsPerm()) requestGps();
    }

    @Override protected void onResume() { super.onResume(); updateStatus(); }

    private void updateStatus() {
        TextView tv = findViewById(R.id.tv_status);
        if (tv == null) return;
        boolean gps    = hasGpsPerm();
        boolean gpsSvc = GpsTrackingService.isActive();
        String mapPath = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE).getString(AppConfig.PREF_MAP_FILE, "");
        boolean hasMap = !mapPath.isEmpty() && new File(mapPath).exists();
        File routingDir = new File(getExternalFilesDir(null), "routing");
        boolean hasRouting = routingDir.exists() && routingDir.listFiles() != null
            && routingDir.listFiles((d, n) -> n.endsWith(".pbf")).length > 0;
        tv.setText(
            (gps    ? "[OK] " : "[X] ") + "Permesso GPS\n" +
            (hasMap ? "[OK] " : "[!] ") + (hasMap ? "Mappa offline pronta" : "Nessuna mappa - scarica o carica") + "\n" +
            (hasRouting ? "[OK] " : "[!] ") + (hasRouting ? "Dati routing presenti" : "Nessun dato routing - scarica per navigare") + "\n" +
            (gpsSvc ? "[OK] " : "[ ] ") + "Servizio GPS");
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
    private void go(Class<?> cls) { startActivity(new Intent(this, cls)); }

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
import com.offlinegps.map.map.MapController;
import com.offlinegps.map.routing.RoutingEngine;
import com.offlinegps.map.routing.WeatherService;
import org.mapsforge.map.android.graphics.AndroidGraphicFactory;
import org.mapsforge.map.android.view.MapView;
import java.io.File;
import java.util.*;
import java.util.concurrent.*;

public class NavigationActivity extends AppCompatActivity
        implements GpsTrackingService.LocationCallback {

    public static final String EXTRA_DEST_LAT  = "dest_lat";
    public static final String EXTRA_DEST_LON  = "dest_lon";
    public static final String EXTRA_DEST_NAME = "dest_name";
    public static final String EXTRA_PROFILE   = "profile";

    private static final double REROUTE_THRESHOLD_M = 40.0;
    private static final double STEP_ADVANCE_M      = 25.0;

    private MapView       mapView;
    private MapController mapCtrl;
    private TextView      tvInstruction, tvDistanceNext, tvEta, tvTotalDist, tvBuildStatus, tvNextStreet, tvWeather;
    private ImageView     ivManeuver;
    private ProgressBar   pbBuild;
    private RecyclerView  rvSteps;
    private View          overlayBuild, panelTop, panelBottom;
    private ImageButton   btnClose, btnRecenter, btnProfileCar, btnProfileBike, btnProfileFoot;

    private double destLat, destLon;
    private String destName = "Destinazione";
    private String profile  = RoutingEngine.PROFILE_CAR;

    private final ExecutorService routingExec = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @Nullable private RoutingEngine.RouteResult currentRoute;
    private int currentStepIdx = 0;
    private double[] lastReroutePoint = null;
    private StepsAdapter stepsAdapter;
    private boolean panelExpanded = false;

    // --- Voce (Text-To-Speech) ---
    @Nullable private TextToSpeech tts;
    private boolean ttsReady = false;
    private boolean voiceEnabled = true;
    private int lastAnnouncedStep = -1;
    private boolean announcedClose = false;   // annuncio "tra X metri"
    private boolean announcedArrival = false;
    // distanze a cui annunciare l'avvicinamento alla manovra (in metri)
    private static final double ANNOUNCE_FAR_M  = 250.0;
    private static final double ANNOUNCE_NEAR_M = 60.0;

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

        try { AndroidGraphicFactory.createInstance(getApplication()); } catch (Throwable ignored) {}
        setContentView(R.layout.activity_navigation);

        mapView        = findViewById(R.id.nav_map_view);
        tvInstruction  = findViewById(R.id.tv_nav_instruction);
        tvDistanceNext = findViewById(R.id.tv_nav_distance_next);
        tvEta          = findViewById(R.id.tv_nav_eta);
        tvTotalDist    = findViewById(R.id.tv_nav_total_dist);
        tvBuildStatus  = findViewById(R.id.tv_nav_build_status);
        tvNextStreet   = findViewById(R.id.tv_nav_next_street);
        tvWeather      = findViewById(R.id.tv_nav_weather);
        ivManeuver     = findViewById(R.id.iv_nav_maneuver);
        pbBuild        = findViewById(R.id.pb_nav_build);
        rvSteps        = findViewById(R.id.rv_nav_steps);
        overlayBuild   = findViewById(R.id.overlay_nav_build);
        panelTop       = findViewById(R.id.panel_nav_top);
        panelBottom    = findViewById(R.id.panel_nav_bottom);
        btnClose       = findViewById(R.id.btn_nav_close);
        btnRecenter    = findViewById(R.id.btn_nav_recenter);
        btnProfileCar  = findViewById(R.id.btn_nav_profile_car);
        btnProfileBike = findViewById(R.id.btn_nav_profile_bike);
        btnProfileFoot = findViewById(R.id.btn_nav_profile_foot);

        mapCtrl = new MapController(this);
        mapCtrl.init(mapView);
        loadBaseMap();

        stepsAdapter = new StepsAdapter();
        if (rvSteps != null) {
            rvSteps.setLayoutManager(new LinearLayoutManager(this));
            rvSteps.setAdapter(stepsAdapter);
        }

        if (btnClose != null) btnClose.setOnClickListener(v -> finish());
        if (btnRecenter != null) btnRecenter.setOnClickListener(v -> centerOnGps());
        if (panelBottom != null) panelBottom.setOnClickListener(v -> togglePanel());
        setupProfileButtons();
        initTts();
        setupVoiceToggle();

        startGpsAndRoute();
    }

    private void initTts() {
        try {
            tts = new TextToSpeech(this, status -> {
                if (status == TextToSpeech.SUCCESS && tts != null) {
                    int r = tts.setLanguage(Locale.ITALIAN);
                    ttsReady = (r != TextToSpeech.LANG_MISSING_DATA
                                && r != TextToSpeech.LANG_NOT_SUPPORTED);
                }
            });
        } catch (Exception e) { ttsReady = false; }
    }

    private void setupVoiceToggle() {
        ImageButton btnVoice = findViewById(R.id.btn_nav_voice);
        if (btnVoice == null) return;
        btnVoice.setOnClickListener(v -> {
            voiceEnabled = !voiceEnabled;
            btnVoice.setAlpha(voiceEnabled ? 1f : 0.35f);
            if (!voiceEnabled && tts != null) tts.stop();
            Toast.makeText(this, voiceEnabled ? "Voce attiva" : "Voce disattivata",
                Toast.LENGTH_SHORT).show();
        });
    }

    private void speak(String text) {
        if (!voiceEnabled || !ttsReady || tts == null || text == null || text.isEmpty()) return;
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "nav");
    }

    private void loadBaseMap() {
        String path = getSharedPreferences(AppConfig.PREFS, MODE_PRIVATE)
            .getString(AppConfig.PREF_MAP_FILE, "");
        if (!path.isEmpty()) {
            File f = new File(path);
            if (f.exists()) mapCtrl.loadMapFile(f);
        }
    }

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
        if (b != null) b.setAlpha(active ? 1f : 0.4f);
    }

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

    /**
     * NB: regionTag viene copiata in finalRegionTag prima dell'uso nelle
     * lambda (deve essere final o effectively final).
     */
    private void ensureGraphAndRoute(double fromLat, double fromLon) {
        showBuildStatus("Preparazione rete stradale...", true);
        routingExec.execute(() -> {
            File routingDir = new File(getExternalFilesDir(null), "routing");

            // 1) prova a dedurre la regione dalla posizione (o dalla destinazione)
            String regionTag = RegionMapper.tagFor(fromLat, fromLon);
            if (regionTag == null) regionTag = RegionMapper.tagFor(destLat, destLon);

            // 2) individua il file .pbf da usare
            File pbf = null;
            if (regionTag != null) {
                File candidate = new File(routingDir, regionTag + ".osm.pbf");
                if (candidate.exists()) pbf = candidate;
            }
            // 3) se non trovato per regione, usa QUALSIASI .pbf scaricato
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

            // controllo dimensione minima: un .pbf valido pesa molti MB
            long sizeMb = finalPbf.length() / (1024 * 1024);
            if (sizeMb < 1) {
                mainHandler.post(() -> showBuildStatus(
                    "Il file " + finalPbf.getName() + " e' troppo piccolo ("
                    + finalPbf.length() + " byte): download incompleto.\n"
                    + "Cancellalo e riscaricalo da Download.", false));
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

    /** Diagnostica: elenca i file presenti nella cartella routing. */
    private String listRoutingDir(File dir) {
        StringBuilder sb = new StringBuilder("Cartella: " + dir.getAbsolutePath() + "\n");
        if (!dir.exists()) { sb.append("(la cartella non esiste ancora)"); return sb.toString(); }
        File[] files = dir.listFiles();
        if (files == null || files.length == 0) { sb.append("(vuota)"); return sb.toString(); }
        for (File f : files) {
            sb.append("- ").append(f.getName()).append("  ")
              .append(f.length() / (1024 * 1024)).append(" MB\n");
        }
        return sb.toString();
    }

    private void recalcRoute() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc == null || !RoutingEngine.getInstance().isReady()) return;
        final double fLat = loc.getLatitude(), fLon = loc.getLongitude();
        routingExec.execute(() -> {
            RoutingEngine.RouteResult result = RoutingEngine.getInstance()
                .route(fLat, fLon, destLat, destLon, profile);
            mainHandler.post(() -> {
                if (result == null) {
                    String why = RoutingEngine.getInstance().getLastError();
                    if (why == null || why.isEmpty()) why = "Percorso non trovato";
                    Toast.makeText(this, why, Toast.LENGTH_LONG).show();
                    return;
                }
                currentRoute = result;
                currentStepIdx = 0;
                lastReroutePoint = new double[]{fLat, fLon};
                drawRoute(result);
                updateInstructionPanel();
                stepsAdapter.submit(result.steps);
                if (tvTotalDist != null) tvTotalDist.setText(formatDistance(result.distanceMeters));
                if (tvEta != null) tvEta.setText(formatEta(result.timeMillis));
                fetchWeatherForDestination();
            });
        });
    }

    private void drawRoute(RoutingEngine.RouteResult result) {
        mapCtrl.clearTrack();
        for (double[] p : result.points) mapCtrl.addTrackPoint(p[0], p[1]);
        if (!result.points.isEmpty()) {
            double[] first = result.points.get(0);
            mapCtrl.centerOn(first[0], first[1], true);
        }
    }

    /** Meteo a destinazione (richiede internet; se offline non mostra nulla). */
    private void fetchWeatherForDestination() {
        if (tvWeather == null) return;
        WeatherService.fetch(destLat, destLon, w -> {
            if (tvWeather == null) return;
            if (w == null || Double.isNaN(w.tempC)) {
                tvWeather.setVisibility(View.GONE);
                return;
            }
            tvWeather.setText(String.format(Locale.ITALIAN, "%s  %.0f gradi  %s",
                w.emoji(), w.tempC, w.description()));
            tvWeather.setVisibility(View.VISIBLE);
        });
    }

    private void updateInstructionPanel() {
        if (currentRoute == null || currentRoute.steps.isEmpty()) return;
        int idx = Math.min(currentStepIdx, currentRoute.steps.size() - 1);
        RoutingEngine.NavStep step = currentRoute.steps.get(idx);
        if (tvInstruction != null) tvInstruction.setText(step.text);
        if (tvDistanceNext != null) tvDistanceNext.setText(step.formatDistance());
        if (ivManeuver != null) ivManeuver.setImageResource(maneuverIcon(step.sign));

        // nome della strada successiva, se disponibile
        if (tvNextStreet != null) {
            String street = (step.streetName != null && !step.streetName.isEmpty())
                ? step.streetName : "";
            tvNextStreet.setText(street);
            tvNextStreet.setVisibility(street.isEmpty() ? View.GONE : View.VISIBLE);
        }

        stepsAdapter.setActiveIndex(idx);

        // annuncio vocale all'ingresso in un nuovo step
        if (idx != lastAnnouncedStep) {
            lastAnnouncedStep = idx;
            announcedClose = false;
            speak(buildVoiceText(step, -1));
        }
    }

    /** Costruisce la frase vocale. Se distMeters>0 antepone "tra X metri". */
    private String buildVoiceText(RoutingEngine.NavStep step, double distMeters) {
        String action = step.text != null ? step.text : "";
        if (distMeters > 0) {
            long rounded = Math.round(distMeters / 10.0) * 10;
            return "Tra " + rounded + " metri, " + action;
        }
        return action;
    }

    /** Icone manovra vettoriali grandi. */
    private int maneuverIcon(int sign) {
        switch (sign) {
            case -3: return R.drawable.ic_turn_sharp_left;
            case -2: return R.drawable.ic_turn_left;
            case -1: return R.drawable.ic_turn_slight_left;
            case  0: return R.drawable.ic_turn_straight;
            case  1: return R.drawable.ic_turn_slight_right;
            case  2: return R.drawable.ic_turn_right;
            case  3: return R.drawable.ic_turn_sharp_right;
            case  4: return R.drawable.ic_turn_straight;    // finish
            case  6: return R.drawable.ic_turn_roundabout;  // roundabout
            default: return R.drawable.ic_turn_straight;
        }
    }

    private void centerOnGps() {
        Location loc = GpsTrackingService.getLastLocation();
        if (loc != null) mapCtrl.centerOn(loc.getLatitude(), loc.getLongitude(), true);
    }

    private void togglePanel() {
        panelExpanded = !panelExpanded;
        if (rvSteps != null) rvSteps.setVisibility(panelExpanded ? View.VISIBLE : View.GONE);
    }

    private void showBuildStatus(String msg, boolean indeterminate) {
        if (overlayBuild != null) overlayBuild.setVisibility(View.VISIBLE);
        if (tvBuildStatus != null) tvBuildStatus.setText(msg);
        if (pbBuild != null) pbBuild.setVisibility(indeterminate ? View.VISIBLE : View.GONE);
    }
    private void hideBuildStatus() { if (overlayBuild != null) overlayBuild.setVisibility(View.GONE); }

    private String formatDistance(double m) {
        return m < 1000 ? String.format("%.0f m", m) : String.format("%.1f km", m / 1000.0);
    }
    private String formatEta(long millis) {
        long min = millis / 60000;
        if (min < 60) return min + " min";
        return (min / 60) + " h " + (min % 60) + " min";
    }

    @Override public void onLocationUpdate(@NonNull Location loc, int sats) {
        runOnUiThread(() -> {
            mapCtrl.updatePosition(loc.getLatitude(), loc.getLongitude(), loc.getAccuracy(), loc.getBearing());
            if (currentRoute == null) {
                if (RoutingEngine.getInstance().isReady()) recalcRoute();
                else if (!RoutingEngine.isBuilding()) ensureGraphAndRoute(loc.getLatitude(), loc.getLongitude());
                return;
            }
            checkProgressAndReroute(loc);
        });
    }

    private void checkProgressAndReroute(@NonNull Location loc) {
        if (currentRoute == null || currentRoute.points.isEmpty()) return;

        double minDist = Double.MAX_VALUE;
        for (double[] p : currentRoute.points) {
            double d = haversine(loc.getLatitude(), loc.getLongitude(), p[0], p[1]);
            if (d < minDist) minDist = d;
        }

        if (minDist > REROUTE_THRESHOLD_M && !RoutingEngine.isBuilding()) {
            Toast.makeText(this, "Fuori percorso, ricalcolo...", Toast.LENGTH_SHORT).show();
            currentRoute = null;
            recalcRoute();
            return;
        }

        if (currentRoute.steps.isEmpty()) return;
        RoutingEngine.NavStep step = currentRoute.steps.get(
            Math.min(currentStepIdx, currentRoute.steps.size() - 1));

        // annuncio vocale di avvicinamento: "tra 200 metri, gira a destra"
        if (step.distanceMeters > 0 && step.distanceMeters <= ANNOUNCE_FAR_M && !announcedClose) {
            announcedClose = true;
            speak(buildVoiceText(step, step.distanceMeters));
        }

        if (step.distanceMeters > 0 && step.distanceMeters < STEP_ADVANCE_M
                && currentStepIdx < currentRoute.steps.size() - 1) {
            currentStepIdx++;
            updateInstructionPanel();
        }

        double destDist = haversine(loc.getLatitude(), loc.getLongitude(), destLat, destLon);
        if (destDist < 20) {
            if (!announcedArrival) {
                announcedArrival = true;
                speak("Sei arrivato a destinazione");
            }
            Toast.makeText(this, "Sei arrivato a destinazione", Toast.LENGTH_LONG).show();
        }
    }

    private double haversine(double lat1, double lon1, double lat2, double lon2) {
        final double R = 6371000.0;
        double dLat = Math.toRadians(lat2 - lat1), dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat/2)*Math.sin(dLat/2)
            + Math.cos(Math.toRadians(lat1))*Math.cos(Math.toRadians(lat2))*Math.sin(dLon/2)*Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    @Override protected void onResume() { super.onResume(); GpsTrackingService.setCallback(this); }
    @Override protected void onPause()  { super.onPause();  GpsTrackingService.setCallback(null); }
    @Override protected void onDestroy() {
        super.onDestroy();
        GpsTrackingService.setCallback(null);
        mainHandler.removeCallbacksAndMessages(null);
        routingExec.shutdown();
        if (tts != null) { tts.stop(); tts.shutdown(); tts = null; }
        mapCtrl.destroy();
        AndroidGraphicFactory.clearResourceMemoryCache();
    }

    class StepsAdapter extends RecyclerView.Adapter<StepsAdapter.VH> {
        private final List<RoutingEngine.NavStep> data = new ArrayList<>();
        private int activeIndex = 0;
        void submit(List<RoutingEngine.NavStep> steps) { data.clear(); data.addAll(steps); notifyDataSetChanged(); }
        void setActiveIndex(int idx) { activeIndex = idx; notifyDataSetChanged(); }
        @NonNull @Override public VH onCreateViewHolder(@NonNull ViewGroup p, int t) {
            return new VH(LayoutInflater.from(p.getContext()).inflate(R.layout.item_nav_step, p, false));
        }
        @Override public void onBindViewHolder(@NonNull VH h, int pos) {
            RoutingEngine.NavStep s = data.get(pos);
            h.text.setText(s.text);
            h.dist.setText(s.formatDistance());
            h.itemView.setAlpha(pos == activeIndex ? 1f : 0.55f);
        }
        @Override public int getItemCount() { return data.size(); }
        class VH extends RecyclerView.ViewHolder {
            TextView text, dist;
            VH(@NonNull View v) {
                super(v);
                text = v.findViewById(R.id.tv_step_text);
                dist = v.findViewById(R.id.tv_step_dist);
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
    return ('<Button android:id="@+id/' + back_id + '"\n'
        '    android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
        '    android:text="&lt; Indietro" android:backgroundTint="#141E2E" android:textColor="#00E5FF"\n'
        '    android:textSize="13sp" android:layout_marginBottom="16dp"/>\n'
        '<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n'
        '    android:text="' + title_text + '" android:textColor="' + color + '" android:textSize="22sp"\n'
        '    android:textStyle="bold" android:fontFamily="monospace" android:layout_marginBottom="20dp"/>')

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
    <style name="Theme.OfflineGPS" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="colorPrimary">#00E5FF</item>
        <item name="colorPrimaryDark">#050A14</item>
        <item name="colorAccent">#00FF88</item>
        <item name="android:windowBackground">#050A14</item>
        <item name="android:statusBarColor">#050A14</item>
        <item name="android:navigationBarColor">#0D1421</item>
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
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
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
        '</layer-list>')

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
        '<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n'
        '    <gradient android:type="linear" android:angle="135"\n'
        '        android:startColor="#0A1428" android:centerColor="#050A14" android:endColor="#0A1020"/>\n'
        '</shape>',
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
            android:text="Navigazione e sopravvivenza offline" android:textColor="#5A7A99"
            android:textSize="13sp" android:layout_marginTop="8dp"/>
    </LinearLayout>

    <TextView android:id="@+id/splash_creator"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="bottom|center_horizontal" android:layout_marginBottom="48dp"
        android:text="Creator Maikgost" android:textColor="#FFD600"
        android:textSize="18sp" android:textStyle="bold" android:fontFamily="monospace"
        android:letterSpacing="0.1"/>

</FrameLayout>"""

# HOME v3.0: header con logo, card stato "vetro", pulsanti neon 3D e griglia 2 colonne
LAYOUT_MAIN = """\
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="@drawable/bg_screen_grad">
<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:padding="22dp">

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical"
        android:layout_marginBottom="20dp">
        <ImageView android:layout_width="54dp" android:layout_height="54dp"
            android:src="@drawable/ic_gps" android:layout_marginEnd="16dp"
            android:contentDescription="Logo"/>
        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"
            android:layout_weight="1" android:orientation="vertical">
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="OfflineGPS 3D" android:textColor="#E8F4FD"
                android:textSize="28sp" android:textStyle="bold" android:fontFamily="monospace"/>
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="v3.0 · Navigazione · Sopravvivenza · Offline"
                android:textColor="#00E5FF" android:textSize="12sp"/>
        </LinearLayout>
    </LinearLayout>

    <TextView android:id="@+id/tv_status"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textColor="#5A7A99" android:textSize="13sp" android:fontFamily="monospace"
        android:lineSpacingMultiplier="1.6" android:background="@drawable/bg_card_glass"
        android:padding="16dp" android:layout_marginBottom="20dp"/>

    <Button android:id="@+id/btn_navigate"
        android:layout_width="match_parent" android:layout_height="62dp"
        android:text="NAVIGA - Calcola Percorso" android:background="@drawable/bg_btn_neon_green"
        android:textColor="#00FF88" android:textSize="16sp" android:textStyle="bold"
        android:elevation="14dp" android:layout_marginBottom="14dp"/>

    <Button android:id="@+id/btn_open_map"
        android:layout_width="match_parent" android:layout_height="58dp"
        android:text="APRI MAPPA 3D OFFLINE" android:background="@drawable/bg_btn_neon_primary"
        android:textColor="#4FE8FF" android:textSize="15sp" android:textStyle="bold"
        android:elevation="14dp" android:layout_marginBottom="14dp"/>

    <!-- griglia 2 colonne: strumenti / sopravvivenza -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginBottom="14dp">
        <Button android:id="@+id/btn_tools"
            android:layout_width="0dp" android:layout_height="72dp" android:layout_weight="1"
            android:text="STRUMENTI\\nOUTDOOR" android:background="@drawable/bg_btn_neon_yellow"
            android:textColor="#FFDF4D" android:textSize="13sp" android:textStyle="bold"
            android:elevation="12dp" android:layout_marginEnd="12dp"/>
        <Button android:id="@+id/btn_survival"
            android:layout_width="0dp" android:layout_height="72dp" android:layout_weight="1"
            android:text="KIT\\nSOPRAVVIVENZA" android:background="@drawable/bg_btn_neon_red"
            android:textColor="#FF5C7A" android:textSize="13sp" android:textStyle="bold"
            android:elevation="12dp"/>
    </LinearLayout>

    <!-- griglia 2 colonne: chat / emergenza -->
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginBottom="14dp">
        <Button android:id="@+id/btn_chat"
            android:layout_width="0dp" android:layout_height="72dp" android:layout_weight="1"
            android:text="CHAT OFFLINE\\n(Bluetooth)" android:background="@drawable/bg_btn_neon"
            android:textColor="#4DFFA0" android:textSize="13sp" android:textStyle="bold"
            android:elevation="12dp" android:layout_marginEnd="12dp"/>
        <Button android:id="@+id/btn_emergency"
            android:layout_width="0dp" android:layout_height="72dp" android:layout_weight="1"
            android:text="EMERGENZA\\nSOS" android:background="@drawable/bg_btn_neon_red"
            android:textColor="#FF8888" android:textSize="13sp" android:textStyle="bold"
            android:elevation="12dp"/>
    </LinearLayout>

    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginBottom="10dp">
        <Button android:id="@+id/btn_download"
            android:layout_width="0dp" android:layout_height="52dp" android:layout_weight="1"
            android:text="Download" android:backgroundTint="#141E2E" android:textColor="#00E5FF"
            android:textSize="13sp" android:layout_marginEnd="8dp"/>
        <Button android:id="@+id/btn_waypoints"
            android:layout_width="0dp" android:layout_height="52dp" android:layout_weight="1"
            android:text="Waypoint" android:backgroundTint="#141E2E" android:textColor="#00FF88"
            android:textSize="13sp" android:layout_marginEnd="8dp"/>
        <Button android:id="@+id/btn_stats"
            android:layout_width="0dp" android:layout_height="52dp" android:layout_weight="1"
            android:text="Stats" android:backgroundTint="#141E2E" android:textColor="#FF6B35"
            android:textSize="13sp"/>
    </LinearLayout>

</LinearLayout></ScrollView>"""

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

LAYOUT_NAVIGATION = """\
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#050A14">

    <org.mapsforge.map.android.view.MapView android:id="@+id/nav_map_view"
        android:layout_width="match_parent" android:layout_height="match_parent"/>

    <LinearLayout android:id="@+id/panel_nav_top"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="top" android:orientation="horizontal"
        android:gravity="center_vertical" android:background="#EE0D1421"
        android:padding="18dp">
        <ImageView android:id="@+id/iv_nav_maneuver"
            android:layout_width="64dp" android:layout_height="64dp"
            android:layout_marginEnd="16dp" android:tint="#00E5FF"
            android:src="@drawable/ic_turn_straight"
            android:contentDescription="Direzione"/>
        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"
            android:layout_weight="1" android:orientation="vertical">
            <TextView android:id="@+id/tv_nav_distance_next"
                android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="-- m" android:textColor="#00FF88"
                android:textSize="24sp" android:textStyle="bold" android:fontFamily="monospace"/>
            <TextView android:id="@+id/tv_nav_instruction"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Calcolo percorso..." android:textColor="#E8F4FD"
                android:textSize="17sp" android:textStyle="bold" android:maxLines="2"/>
            <TextView android:id="@+id/tv_nav_next_street"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:textColor="#00E5FF" android:textSize="14sp"
                android:visibility="gone" android:maxLines="1"
                android:ellipsize="end"/>
        </LinearLayout>
        <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:orientation="vertical" android:gravity="center">
            <ImageButton android:id="@+id/btn_nav_voice"
                android:layout_width="40dp" android:layout_height="40dp"
                android:src="@android:drawable/ic_lock_silent_mode_off"
                android:background="@android:color/transparent" android:tint="#00FF88"
                android:contentDescription="Voce"/>
            <ImageButton android:id="@+id/btn_nav_close"
                android:layout_width="40dp" android:layout_height="40dp"
                android:src="@android:drawable/ic_menu_close_clear_cancel"
                android:background="@android:color/transparent" android:tint="#FF1744"
                android:contentDescription="Chiudi"/>
        </LinearLayout>
    </LinearLayout>

    <ImageButton android:id="@+id/btn_nav_recenter"
        android:layout_width="48dp" android:layout_height="48dp"
        android:layout_gravity="end|center_vertical"
        android:layout_marginEnd="12dp" android:layout_marginBottom="160dp"
        android:src="@drawable/ic_gps" android:background="#CC141E2E"
        android:contentDescription="Centra"/>

    <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_gravity="end|top" android:layout_marginTop="100dp" android:layout_marginEnd="12dp"
        android:orientation="vertical" android:background="#CC141E2E" android:padding="6dp">
        <ImageButton android:id="@+id/btn_nav_profile_car"
            android:layout_width="44dp" android:layout_height="44dp"
            android:src="@android:drawable/ic_menu_directions"
            android:background="@android:color/transparent" android:tint="#00E5FF"
            android:contentDescription="Auto"/>
        <ImageButton android:id="@+id/btn_nav_profile_bike"
            android:layout_width="44dp" android:layout_height="44dp"
            android:src="@android:drawable/ic_menu_compass"
            android:background="@android:color/transparent" android:tint="#00FF88"
            android:contentDescription="Bici"/>
        <ImageButton android:id="@+id/btn_nav_profile_foot"
            android:layout_width="44dp" android:layout_height="44dp"
            android:src="@android:drawable/ic_menu_mylocation"
            android:background="@android:color/transparent" android:tint="#FF6B35"
            android:contentDescription="A piedi"/>
    </LinearLayout>

    <LinearLayout android:id="@+id/panel_nav_bottom"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_gravity="bottom" android:orientation="vertical"
        android:background="#EE0D1421" android:padding="16dp">
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal" android:gravity="center_vertical">
            <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content"
                android:layout_weight="1" android:orientation="vertical">
                <TextView android:id="@+id/tv_nav_eta"
                    android:layout_width="wrap_content" android:layout_height="wrap_content"
                    android:text="-- min" android:textColor="#00E5FF"
                    android:textSize="22sp" android:textStyle="bold" android:fontFamily="monospace"/>
                <TextView android:id="@+id/tv_nav_total_dist"
                    android:layout_width="wrap_content" android:layout_height="wrap_content"
                    android:text="-- km" android:textColor="#5A7A99" android:textSize="13sp"/>
            </LinearLayout>
            <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="Tocca per i dettagli" android:textColor="#5A7A99" android:textSize="11sp"/>
        </LinearLayout>
        <TextView android:id="@+id/tv_nav_weather"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:textColor="#00E5FF" android:textSize="13sp" android:fontFamily="monospace"
            android:layout_marginTop="6dp" android:visibility="gone"/>
        <androidx.recyclerview.widget.RecyclerView android:id="@+id/rv_nav_steps"
            android:layout_width="match_parent" android:layout_height="260dp"
            android:layout_marginTop="12dp" android:visibility="gone"/>
    </LinearLayout>

    <LinearLayout android:id="@+id/overlay_nav_build"
        android:layout_width="match_parent" android:layout_height="match_parent"
        android:orientation="vertical" android:gravity="center"
        android:background="#DD050A14" android:padding="32dp">
        <ProgressBar android:id="@+id/pb_nav_build"
            android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:layout_marginBottom="20dp"/>
        <TextView android:id="@+id/tv_nav_build_status"
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Preparazione rete stradale..." android:textColor="#E8F4FD"
            android:textSize="15sp" android:gravity="center" android:fontFamily="monospace"
            android:lineSpacingMultiplier="1.4"/>
    </LinearLayout>

</FrameLayout>"""

LAYOUT_ITEM_NAV_STEP = """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="horizontal" android:padding="12dp" android:gravity="center_vertical"
    android:background="#141E2E" android:layout_marginBottom="2dp">
    <TextView android:id="@+id/tv_step_text"
        android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
        android:textColor="#E8F4FD" android:textSize="14sp"/>
    <TextView android:id="@+id/tv_step_dist"
        android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:textColor="#00E5FF" android:textSize="13sp" android:fontFamily="monospace"/>
</LinearLayout>"""

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
    title("STEP 1 - Creazione progetto OfflineGPS 3D v3.1")
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
    dest = DESKTOP / "OfflineGPS-3D-v3.1.apk"
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
    info("1. Installa OfflineGPS-3D-v3.1.apk")
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
    print("  OfflineGPS 3D v3.1 - ricerca vie+civici completa")
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
        print(f"{C.OK}{C.BOLD}OfflineGPS 3D v3.1 - Completato!{C.RESET}\n")
    except KeyboardInterrupt:
        print(f"\n{C.WARN}Interrotto.{C.RESET}"); sys.exit(0)
    except Exception as e:
        err(f"Errore: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
