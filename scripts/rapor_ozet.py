#!/usr/bin/env python3
"""rapor_ozet.py — Quetext PDF raporundan CÜMLESİZ özet çıkarır (yerelde çalışır, hiçbir yere göndermez).

Kullanım:
  python3 -I rapor_ozet.py RAPOR.pdf [ANA_METIN.txt] [--cikti ozet.md] [--kontrol liste.md]

Çıktı yalnız sayı, yüzde, alan adı ve bölüm sıra numarası içerir; tez ya da kaynak cümlesi içermez.
ANA_METIN verilirse her eşleşmenin hangi bölümde olduğu ve çevresinde (Soyad, Yıl) biçiminde atıf bulunup bulunmadığı da yazılır.
Gereken araç: pdftotext (poppler).
"""
import re
import subprocess
import sys
import urllib.parse

sys.dont_write_bytecode = True
TR = str.maketrans({"İ": "i", "I": "ı"})
KATLA = str.maketrans({"ı": "i", "â": "a", "î": "i", "û": "u", "ş": "s", "ç": "c", "ğ": "g", "ö": "o", "ü": "u"})
ATIF_RE = re.compile(r"\([^()]{0,160}\b(?:1[89]|20)\d{2}[a-z]?\b[^()]{0,60}\)")
BASLIK_RE = re.compile(r"^[IVX]+\.\s*[A-ZÇĞİÖŞÜ]{3,}")
MATCH_RE = re.compile(r"^\s*Match\s+#(\d+)\s+(\d+)%\s+similar")


def katla(s):
    return re.sub(r"[^\w\s]", " ", s.translate(TR).lower().translate(KATLA))


def pdf_metni(yol):
    return subprocess.run(["pdftotext", "-layout", yol, "-"], capture_output=True, text=True, check=True).stdout


def toplam_yuzde(satirlar):
    for s in satirlar[:6]:
        m = re.match(r"\s*(\d+)%\s+overall", s)
        if m:
            return int(m.group(1))
    return None


def eslesmeleri_ayir(metin):
    satirlar = metin.split("\n")
    sonuc, aktif, kol = [], None, None
    for s in satirlar:
        m = MATCH_RE.match(s)
        if m:
            if aktif:
                sonuc.append(aktif)
            aktif, kol = {"no": int(m.group(1)), "yuzde": int(m.group(2)), "sol": [], "url": None}, None
            continue
        if aktif is None:
            continue
        if "YOUR TEXT" in s and "SOURCE" in s:
            kol = s.index("SOURCE")
            continue
        if kol is None or not s.strip():
            continue
        sol, sag = s[:kol].strip(), s[kol:].strip()
        if sol:
            aktif["sol"].append(sol)
        if aktif["url"] is None and sag.startswith("http"):
            aktif["url"] = sag.split()[0]
    if aktif:
        sonuc.append(aktif)
    for e in sonuc:
        e["metin"] = " ".join(e.pop("sol"))
        e["alan"] = urllib.parse.urlparse(e["url"]).netloc.removeprefix("www.") if e["url"] else "?"
        e.pop("url", None)
    return sonuc


def bolum_haritasi(ana):
    """Kelime indeksine göre bölüm sıra numarası: [(kelime_baslangici, no)]."""
    harita, kelime, no = [], 0, 0
    for satir in ana.split("\n"):
        if BASLIK_RE.match(satir.strip()):
            no += 1
            harita.append((kelime, no))
        kelime += len(satir.split())
    return harita or [(0, 1)]


def konumla(eslesmeler, ana):
    ham = ana.split()
    norm = [katla(w).strip() for w in ham]
    bol = bolum_haritasi(ana)
    indeks = {}
    for i in range(len(norm) - 5):
        indeks.setdefault(tuple(norm[i:i + 6]), i)
    for e in eslesmeler:
        w = [x for x in katla(e["metin"]).split()]
        e["kelime"] = len(w)
        e["bolum"] = e["atifli"] = None
        if len(w) < 6:
            continue
        i = indeks.get(tuple(w[:6]))
        if i is None:
            continue
        e["bolum"] = max(no for (bas, no) in bol if bas <= i)
        cevre = " ".join(ham[max(0, i - 25): i + len(w) + 25])
        e["atifli"] = bool(ATIF_RE.search(cevre))
    return eslesmeler


def ozet_md(toplam, es, konumlu):
    out = ["# Quetext raporu özeti (cümlesiz)", "", f"Toplam benzerlik: %{toplam}" if toplam is not None else "Toplam benzerlik: okunamadı",
           f"Eşleşme sayısı: {len(es)}", ""]
    alan = {}
    for e in es:
        a = alan.setdefault(e["alan"], {"n": 0, "kelime": 0, "toplam_yuzde": 0})
        a["n"] += 1
        a["kelime"] += len(katla(e["metin"]).split())
        a["toplam_yuzde"] += e["yuzde"]
    out += ["## Alan adlarına göre", "", "| Alan adı | Eşleşme | Eşleşen kelime | Ort. benzerlik % |", "|---|---|---|---|"]
    for k, v in sorted(alan.items(), key=lambda x: -x[1]["kelime"]):
        out.append(f"| {k} | {v['n']} | {v['kelime']} | {v['toplam_yuzde'] // v['n']} |")
    if konumlu:
        bol = {}
        for e in es:
            b = bol.setdefault(e["bolum"], {"n": 0, "kelime": 0, "atifsiz": 0})
            b["n"] += 1
            b["kelime"] += e["kelime"]
            if e["atifli"] is False:
                b["atifsiz"] += 1
        out += ["", "## Bölümlere göre (bölüm sıra numarası; '-' = ana metinde konumlanamadı)", "",
                "| Bölüm | Eşleşme | Eşleşen kelime | Çevresinde atıf bulunmayan |", "|---|---|---|---|"]
        for k in sorted(bol, key=lambda x: (x is None, x)):
            v = bol[k]
            out.append(f"| {k if k is not None else '-'} | {v['n']} | {v['kelime']} | {v['atifsiz']} |")
        out += ["", "## Yüksek benzerlikli ve atıfsız eşleşmeler (>= %60)", "", "| # | Benzerlik % | Kelime | Bölüm | Alan adı |", "|---|---|---|---|---|"]
        for e in es:
            if e["yuzde"] >= 60 and e["atifli"] is False:
                out.append(f"| {e['no']} | {e['yuzde']} | {e['kelime']} | {e['bolum']} | {e['alan']} |")
    return "\n".join(out) + "\n"


def kontrol_listesi(es):
    """Raporda tek tek bakılacak eşleşmeler; öncelik: atıfsız ve yüksek benzerlik, sonra konumlanamayanlar, sonra kalan."""
    def oncelik(e):
        if e.get("atifli") is False and e["yuzde"] >= 60:
            return 0
        if e.get("bolum") is None:
            return 1
        return 2 if e.get("atifli") is False else 3
    ad = {0: "A. Önce bak: atıf görünmüyor, benzerlik %60+", 1: "B. Konumlanamadı (ana metinde yeri bulunamadı)",
          2: "C. Atıf görünmüyor, benzerlik %60 altı", 3: "D. Çevresinde atıf görünüyor"}
    out = ["# Eşleşme kontrol listesi (cümlesiz)", "",
           "Numaralar Quetext raporundaki 'Match #' numaralarıdır. Her satırı raporda aç, aşağıdaki kodlardan birini yaz:",
           "T = ortak terim/kalıp, dokunma · A = atıf ekle · Y = cümleyi yeniden kur · O = atıf zaten var · ? = emin değilim", ""]
    for g in (0, 1, 2, 3):
        grup = sorted([e for e in es if oncelik(e) == g], key=lambda e: (-e["yuzde"], e["no"]))
        if not grup:
            continue
        out += [f"## {ad[g]} ({len(grup)})", "", "| # | Benzerlik % | Kelime | Bölüm | Alan adı | Karar |", "|---|---|---|---|---|---|"]
        for e in grup:
            out.append(f"| {e['no']} | {e['yuzde']} | {e.get('kelime') or len(katla(e['metin']).split())} | {e.get('bolum') or '-'} | {e['alan']} | |")
        out.append("")
    return "\n".join(out) + "\n"


def main(arg):
    if not arg or arg[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if arg else 2
    cikti = kontrol = None
    if "--kontrol" in arg:
        i = arg.index("--kontrol")
        kontrol = arg[i + 1]
        arg = arg[:i] + arg[i + 2:]
    if "--cikti" in arg:
        i = arg.index("--cikti")
        cikti = arg[i + 1]
        arg = arg[:i] + arg[i + 2:]
    metin = pdf_metni(arg[0])
    es = eslesmeleri_ayir(metin)
    toplam = toplam_yuzde(metin.split("\n"))
    konumlu = False
    if len(arg) > 1:
        with open(arg[1], encoding="utf-8") as f:
            es = konumla(es, f.read())
        konumlu = True
    if kontrol:
        with open(kontrol, "w", encoding="utf-8") as f:
            f.write(kontrol_listesi(es))
        print(f"yazıldı: {kontrol}")
    md = ozet_md(toplam, es, konumlu)
    if cikti:
        with open(cikti, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"yazıldı: {cikti}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
