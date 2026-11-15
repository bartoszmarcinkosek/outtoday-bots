"""Wysyła plik HTML z folderu notes/ na adresy z MAIL_TO (np. instrukcje dla zespołu)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import digest  # noqa: E402

path, subject = sys.argv[1], sys.argv[2]
if not os.path.abspath(path).startswith(os.path.abspath("notes") + os.sep):
    sys.exit("Tylko pliki z folderu notes/")
with open(path, encoding="utf-8") as f:
    body = f.read()
digest.send(subject, body, "Otwórz ten e-mail w widoku HTML.")
