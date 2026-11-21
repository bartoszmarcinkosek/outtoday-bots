"""Tylko odczyt: podgląd geo_clean (DRY)."""
import os
os.environ["DRY"] = "1"
import runpy
runpy.run_path(os.path.join(os.path.dirname(__file__), "geo_clean.py"), run_name="__main__")
