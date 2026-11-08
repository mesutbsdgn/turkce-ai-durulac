#!/usr/bin/env python3
"""yerlestir.py — onaylı yeni metinleri, tezde anlamca en yakın gövde paragrafının ARDINA izli ekleme olarak koyar.

Her yeni paragraf Word'de izli eklemedir (w:ins, yazar "Durulaç-Ajan"; paragraf işareti dahil): reddedince paragraf tamamen kalkar.
Yer seçimi: yerel bge-m3 gömme modeli (Ollama, 127.0.0.1). Aday: tablo, başlık, liste, alan, bölüm sonu içermeyen, en az 40 kelimelik
gövde paragrafları; ilk bölüm başlığından kaynakçaya kadar. Benzerlik eşiğin altındaysa yerleştirilmez.
Rapor cümlesizdir (kimlik, paragraf sıra numarası, skor, durum).
"""
import json
import math
import re
import sys
import urllib.request
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
import tez_onar as to  # noqa: E402

OLLAMA_EMBED = "http://127.0.0.1:11434/api/embed"
BASLIK_ADI_RE = re.compile(r"Heading|Balk|Başlık|Baslik|Caption|Altyaz|TOC|ndekiler|Kaynak|Footnote|Dipnot|Header|Footer|List", re.I)
ILK_BOLUM_RE = re.compile(r"^I\.\s*G[İI]R[İI]Ş\b")
BITIS_RE = re.compile(r"^(?:KAYNAKÇA|KAYNAKCA|EKLER|EK\s*\d|ÖZGEÇMİŞ|ÖZGEÇMIŞ)\s*$")


def par_metni(par):
    return "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", par))


def aday_paragraflar(xml, en_az_kelime=40):
    """[(no, (bas, son), metin)]; no = belgedeki yaprak paragraf sırası (0 tabanlı)."""
    par = to.paragraflar(xml)
    tablolar = [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", xml, re.S)]
    metinler = [par_metni(xml[b:s]) for b, s in par]
    ilk = None
    for i, t in enumerate(metinler):
        if ILK_BOLUM_RE.match(t.strip().upper()):
            ilk = i  # sonuncusu: içindekiler satırından sonraki gerçek başlık
    if ilk is None:
        return []
    bitis = len(par)
    for i in range(ilk + 1, len(par)):
        if BITIS_RE.match(metinler[i].strip().upper()):
            bitis = i
            break
    out = []
    for i in range(ilk + 1, bitis):
        b, s = par[i]
        p = xml[b:s]
        if any(tb <= b and s <= te for tb, te in tablolar):
            continue
        if re.search(r"<w:pStyle w:val=\"([^\"]+)\"", p) and BASLIK_ADI_RE.search(re.search(r"<w:pStyle w:val=\"([^\"]+)\"", p).group(1)):
            continue
        if any(x in p for x in ("<w:numPr", "<w:sectPr", "<w:drawing", "<w:fldChar", "<w:pict", "<w:object")):
            continue
        if len(metinler[i].split()) < en_az_kelime:
            continue
        out.append((i, (b, s), metinler[i]))
    return out


def kosinus(a, b):
    pay = sum(x * y for x, y in zip(a, b))
    d = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return pay / d if d else 0.0


def ollama_gomme(model="bge-m3", toplu=16, zaman_asimi=300):
    def gom(metinler):
        out = []
        for i in range(0, len(metinler), toplu):
            veri = json.dumps({"model": model, "input": [m[:1500] for m in metinler[i:i + toplu]]}).encode()
            istek = urllib.request.Request(OLLAMA_EMBED, data=veri, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as r:
                out.extend(json.loads(r.read())["embeddings"])
        return out
    return gom


def yer_sec(adaylar, metinler, gom_fn, esik=0.5):
    """Her yeni metin için {id, durum, par_no, skor, ilk3}; adaylar aday_paragraflar() çıktısı."""
    if not adaylar:
        return [{"id": m["id"], "durum": "atlandi:aday_yok", "par_no": None, "skor": None, "ilk3": []} for m in metinler]
    avek = gom_fn([a[2] for a in adaylar])
    qvek = gom_fn([(" ".join(m["paragraflar"]))[:1500] for m in metinler])
    sonuc = []
    for m, q in zip(metinler, qvek):
        skorlar = sorted(((kosinus(q, v), a) for v, a in zip(avek, adaylar)), key=lambda x: -x[0])
        ilk3 = [(round(s, 3), a[0]) for s, a in skorlar[:3]]
        s0, a0 = skorlar[0]
        if s0 < esik:
            sonuc.append({"id": m["id"], "durum": "atlandi:dusuk_benzerlik", "par_no": a0[0], "skor": round(s0, 3), "ilk3": ilk3})
        else:
            sonuc.append({"id": m["id"], "durum": "yerlestirildi", "par_no": a0[0], "skor": round(s0, 3), "ilk3": ilk3,
                          "aralik": a0[1]})
    return sonuc


def _calisma_rpr(ic):
    en, secilen = -1, ""
    for m in re.finditer(r"<w:r(?:\s[^>]*)?>(<w:rPr>.*?</w:rPr>)?<w:t(?:\s[^>]*)?>([^<]*)</w:t></w:r>", ic, re.S):
        if len(m.group(2)) > en:
            en, secilen = len(m.group(2)), m.group(1) or ""
    return secilen


def yeni_paragraf(anchor, metin, kimlik, tarih):
    _, ic = to.ac_kapat(anchor)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", ic, re.S)
    ppr_x = ppr.group(0) if ppr else "<w:pPr></w:pPr>"
    ppr_x = re.sub(r"<w:pPrChange\b.*?</w:pPrChange>", "", ppr_x, flags=re.S)
    isaret = f'<w:ins w:id="{kimlik}" w:author="{to.YAZAR}" w:date="{tarih}"/>'
    if "<w:rPr>" in ppr_x:
        ppr_x = ppr_x.replace("<w:rPr>", "<w:rPr>" + isaret, 1)
    elif "<w:rPr/>" in ppr_x:
        ppr_x = ppr_x.replace("<w:rPr/>", f"<w:rPr>{isaret}</w:rPr>", 1)
    else:
        ppr_x = ppr_x.replace("</w:pPr>", f"<w:rPr>{isaret}</w:rPr></w:pPr>", 1)
    run = (f'<w:ins w:id="{kimlik + 1}" w:author="{to.YAZAR}" w:date="{tarih}"><w:r>{_calisma_rpr(ic)}'
           f'<w:t xml:space="preserve">{escape(metin)}</w:t></w:r></w:ins>')
    return f"<w:p>{ppr_x}{run}</w:p>"


def ekle(xml, yerlesimler, metinler, tarih):
    """yerlesimler: yer_sec çıktısından 'yerlestirildi' olanlar; paragraflar sondan başa eklenir."""
    sozluk = {m["id"]: m["paragraflar"] for m in metinler}
    kimlik = to.sonraki_id(xml)
    ekler = []
    for y in yerlesimler:
        if y["durum"] != "yerlestirildi":
            continue
        b, s = y["aralik"]
        anchor = xml[b:s]
        yeni = ""
        for metin in sozluk[y["id"]]:
            yeni += yeni_paragraf(anchor, metin, kimlik, tarih)
            kimlik += 2
        ekler.append((s, yeni))
    for s, yeni in sorted(ekler, reverse=True):
        xml = xml[:s] + yeni + xml[s:]
    return xml


def rapor(sonuclar, aday_sayisi):
    md = ["# Yeni metin yerleştirme (cümlesiz)", "", f"Aday gövde paragrafı: {aday_sayisi}", "",
          "| Metin | Durum | Paragraf no | Skor | İlk 3 (skor, paragraf no) |", "|---|---|---|---|---|"]
    for s in sonuclar:
        md.append(f"| {s['id']} | {s['durum']} | {s['par_no']} | {s['skor']} | {s['ilk3']} |")
    return "\n".join(md) + "\n"
