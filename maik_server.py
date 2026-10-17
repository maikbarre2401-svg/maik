"""MAIK è diventato MAIK PRIME: il programma adesso è maikprime.py (nella stessa cartella).
Questo file resta solo per chi lo avvia ancora con «python maik_server.py»: fa partire maikprime.py.
I tuoi dati (dati_maik/) sono gli stessi."""
import os
import runpy

if __name__ == "__main__":
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "maikprime.py"), run_name="__main__")
