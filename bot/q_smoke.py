import os, sys, subprocess
os.environ["BATCH"] = "force"
os.environ["BATCH_WAIT_MIN"] = "30"
r = subprocess.run([sys.executable, "bot/run.py", "--dry-run", "--only", "etihad_arena,coca_cola_arena", "--max-items", "15", "--max-details", "2"],
                   capture_output=True, text=True)
out = r.stdout + r.stderr
print("\n".join(l for l in out.splitlines() if any(k in l for k in ("Paczka", "gotowe", "HTTP", "Traceback", "Error", "błąd", "BŁĄD", "[cache]", "Zapis", "wpis", "koszt", "nowe")))[-4000:])
print("EXIT", r.returncode)
