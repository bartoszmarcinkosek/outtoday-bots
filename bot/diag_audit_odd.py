"""Paczka pełnego przeglądu: odd (patrz audit/state.json -> next_odd)."""
import os, runpy
os.environ["PARITY"] = "odd"
runpy.run_path(os.path.join(os.path.dirname(__file__), "diag_audit_batch.py"), run_name="__main__")
