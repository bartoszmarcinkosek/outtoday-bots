import os, runpy
os.environ["SHARD"] = "1/4"
runpy.run_path(os.path.join(os.path.dirname(__file__), "diag_verify_all.py"), run_name="__main__")
