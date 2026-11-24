"""Paczka pełnego przeglądu: even (patrz audit/state.json -> next_even)."""
import os, runpy
os.environ["PARITY"] = "even"
runpy.run_path(os.path.join(os.path.dirname(__file__), "diag_audit_batch.py"), run_name="__main__")
