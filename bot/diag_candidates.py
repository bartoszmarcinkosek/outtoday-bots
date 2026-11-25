"""Tylko odczyt: sprawdza kandydatów na źródła (sources/candidates.txt): czy strona odpowiada i czy wygląda na listę wydarzeń."""
import concurrent.futures as cf, os, re, requests
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"}
rows = [[p.strip() for p in l.split("|")] for l in open(os.path.join(os.path.dirname(__file__), "..", "sources", "candidates.txt")) if l.strip() and not l.startswith("#")]
MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
def check(r):
    try:
        x = requests.get(r[3], headers=UA, timeout=25)
        t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", x.text[:500000], flags=re.S | re.I)
        title = (re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I) or [None, ""])[1].strip()[:60]
        body = re.sub(r"<[^>]+>", " ", t).lower()
        dates = len(re.findall(rf"\b\d{{1,2}}\s+{MON}|{MON}\s+\d{{1,2}}\b|\b20(26|27)\b", body))
        return f"CN|{r[0]}|{r[1]}|{x.status_code}|{len(body)}|dates={dates}|ev={body.count('event')}|{x.url[:70]}|{title}"
    except requests.RequestException as e:
        return f"CN|{r[0]}|{r[1]}|ERR|0|{type(e).__name__}|||"
with cf.ThreadPoolExecutor(10) as ex:
    for line in ex.map(check, rows):
        print(line)
