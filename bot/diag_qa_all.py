"""Tylko odczyt: ta sama kontrola jakości co bramka, ale na CAŁEJ bazie (bez ukrywania – sam raport)."""
import os, runpy
os.environ["SINCE"] = "2020-01-01T00:00:00Z"
os.environ.pop("QA_FIX", None)
runpy.run_path(os.path.join(os.path.dirname(__file__), "qa_after_add.py"), run_name="__main__")
