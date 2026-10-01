import urllib.request
U = "http://web.archive.org/web/20230127231322id_/https://www.hesa.ac.uk/data-and-analysis/sb265/figure-7.csv"
b = urllib.request.urlopen(urllib.request.Request(U, headers={"User-Agent": "Mozilla/5.0 (research)"}), timeout=120).read()
open("uk_hesa.csv", "wb").write(b)
print("saved", len(b), "bytes")
# inspect: find the data header row + domicile categories + provider column
import csv
with open("uk_hesa.csv", encoding="utf-8-sig") as f:
    lines = [next(f) for _ in range(60)]
for i, ln in enumerate(lines[:30]):
    print(i, ln.rstrip()[:150])
