"""Podpisywanie iOS bez Maca: tworzy (raz) certyfikat dystrybucyjny i (za każdym razem) profil App Store
przez App Store Connect API, a potem zapisuje credentials.json dla EAS (credentialsSource: local).

Certyfikat (.p12) trzymamy w repo ZASZYFROWANY (AES-256, hasło = sekret IOS_CERT_PASS albo klucz API),
bo Apple pozwala mieć tylko kilka certyfikatów, a klucza prywatnego nie da się pobrać drugi raz.
"""
import base64, hashlib, json, os, subprocess, sys, time
import jwt, requests

APP = os.path.join(os.environ["GITHUB_WORKSPACE"], "app")
CRED = os.path.join(APP, "credentials")
ENC = os.path.join(CRED, "ios-dist.p12.enc")
CERT_ID = os.path.join(CRED, "ios-dist.id")
BUNDLE = "ae.outtoday.app"
KEY = open(os.environ["EXPO_ASC_API_KEY_PATH"]).read()
# hasło do zaszyfrowania .p12 w repo – pochodna klucza API (sekret), nigdy nie trafia do logów
PASS = hashlib.sha256(("outtoday-ios|" + KEY).encode()).hexdigest()
TMP = os.environ.get("RUNNER_TEMP", "/tmp")


def tok():
    return jwt.encode({"iss": os.environ["EXPO_ASC_ISSUER_ID"], "iat": int(time.time()), "exp": int(time.time()) + 900,
                       "aud": "appstoreconnect-v1"}, KEY, algorithm="ES256", headers={"kid": os.environ["EXPO_ASC_KEY_ID"]})


def api(method, path, **kw):
    r = requests.request(method, "https://api.appstoreconnect.apple.com/v1/" + path,
                         headers={"Authorization": f"Bearer {tok()}", "Content-Type": "application/json"}, timeout=60, **kw)
    if r.status_code >= 400:
        sys.exit(f"ASC {method} {path}: {r.status_code} {r.text[:500]}")
    return r.json() if r.text else {}


def sh(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL)


os.makedirs(CRED, exist_ok=True)
p12 = os.path.join(TMP, "dist.p12")
created = False
if os.path.exists(ENC) and os.path.exists(CERT_ID):
    sh("openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-in", ENC, "-out", p12, "-pass", f"pass:{PASS}")
    cert_id = open(CERT_ID).read().strip()
    print("certyfikat z repo:", cert_id)
else:
    keyf, csr = os.path.join(TMP, "dist.key"), os.path.join(TMP, "dist.csr")
    sh("openssl", "genrsa", "-out", keyf, "2048")
    sh("openssl", "req", "-new", "-key", keyf, "-out", csr, "-subj", "/CN=OutToday Distribution/C=AE")
    csr_txt = open(csr).read()
    d = api("POST", "certificates", json={"data": {"type": "certificates", "attributes": {
        "certificateType": "DISTRIBUTION", "csrContent": csr_txt}}})["data"]
    cert_id = d["id"]
    der = os.path.join(TMP, "dist.cer")
    open(der, "wb").write(base64.b64decode(d["attributes"]["certificateContent"]))
    pem = os.path.join(TMP, "dist.pem")
    sh("openssl", "x509", "-inform", "DER", "-in", der, "-out", pem)
    sh("openssl", "pkcs12", "-export", "-legacy", "-inkey", keyf, "-in", pem, "-out", p12, "-passout", f"pass:{PASS}")
    sh("openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-in", p12, "-out", ENC, "-pass", f"pass:{PASS}")
    open(CERT_ID, "w").write(cert_id + "\n")
    created = True
    print("nowy certyfikat:", cert_id)

bid = api("GET", "bundleIds", params={"filter[identifier]": BUNDLE})["data"]
bid = [b for b in bid if b["attributes"]["identifier"] == BUNDLE][0]["id"]
name = "OutToday AppStore"
for p in api("GET", "profiles", params={"filter[name]": name, "limit": 50})["data"]:
    api("DELETE", f"profiles/{p['id']}")
prof = api("POST", "profiles", json={"data": {"type": "profiles", "attributes": {"name": name, "profileType": "IOS_APP_STORE"},
        "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": bid}},
                          "certificates": {"data": [{"type": "certificates", "id": cert_id}]}}}})["data"]
mp = os.path.join(TMP, "profile.mobileprovision")
open(mp, "wb").write(base64.b64decode(prof["attributes"]["profileContent"]))
json.dump({"ios": {"provisioningProfilePath": mp, "distributionCertificate": {"path": p12, "password": PASS}}},
          open(os.path.join(APP, "credentials.json"), "w"))
print("profil:", prof["id"], "| credentials.json gotowe")
if created and os.environ.get("GITHUB_OUTPUT"):
    open(os.environ["GITHUB_OUTPUT"], "a").write("new_cert=true\n")
