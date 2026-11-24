"""Paczka ciągłego przeglądu jakości (audit/roll_next.txt)."""
import os, runpy
os.environ["ROLL"] = "1"
runpy.run_path(os.path.join(os.path.dirname(__file__), "diag_audit_batch.py"), run_name="__main__")
