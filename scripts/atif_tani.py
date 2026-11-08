#!/usr/bin/env python3
"""atif_tani.py — atıf ↔ kaynakça uyuşmazlıklarını sınıflandırır (yalnız Soyad (Yıl); cümle yok).

Kategoriler (metinde atıf var, kaynakçada yok):
  yazim_farki        aynı yıl, soyadı ≤2 harf farklı  (Bernan ↔ BERMAN)
  yil_farki          aynı soyad, başka yıl            (Kaya 2008 ↔ KAYA 2009)
  ikinci_yazar_olasi soyad aynı yıllı bir kaynakça satırında geçiyor (ilk yazar atıfta başka yazılmış)
  gercek_eksik       hiçbiri
Kaynakçada var, metinde yok:
  yazim_farki / yil_farki (metindeki atıflarla eşleşen) ve gercek_atifsiz
"""
import re
import sys

sys.dont_write_bytecode = True

AD_YIL_RE = re.compile(r"^(?P<ad>.+?)\s*\((?P<yil>(?:19|20)\d\d)[a-z]?\)$")
KAYNAKCA_BASI_RE = re.compile(r"^([A-ZÇĞİÖŞÜa-zçğıöşüÂÎÛâîû'-]{2,25})\s*,")
YIL_RE = re.compile(r"\b((?:19|20)\d\d)\b")


def katla(s):
    s = s.replace("İ", "i").replace("I", "ı").lower()
    for k, h in (("ı", "i"), ("â", "a"), ("î", "i"), ("û", "u"), ("ş", "s"), ("ç", "c"), ("ğ", "g"), ("ö", "o"), ("ü", "u")):
        s = s.replace(k, h)
    return s


def uzaklik(a, b):
    """Levenshtein uzaklığı."""
    onceki = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        simdiki = [i]
        for j, cb in enumerate(b, 1):
            simdiki.append(min(onceki[j] + 1, simdiki[j - 1] + 1, onceki[j - 1] + (ca != cb)))
        onceki = simdiki
    return onceki[-1]


def yakin(a, b):
    """Yazım farkı sayılacak kadar yakın mı: kısa adlarda sıkı eşik (UN ≠ LIN)."""
    en_kisa = min(len(a), len(b))
    esik = 2 if en_kisa >= 6 else (1 if en_kisa >= 4 else 0)
    return 0 < uzaklik(a, b) <= esik


def ayristir(etiket):
    m = AD_YIL_RE.match(etiket.strip())
    return (katla(m.group("ad").split()[0]), m.group("yil"), m.group("ad")) if m else None


def kaynakca_girdileri(satirlar):
    cikti = []
    for s in satirlar:
        m, y = KAYNAKCA_BASI_RE.match(s.strip()), YIL_RE.search(s)
        if m and y:
            cikti.append({"ad": m.group(1), "soyad": katla(m.group(1)), "yil": y.group(1), "norm": katla(s)})
    return cikti


def tani(eksik_atiflar, eksik_kaynaklar, kaynakca_satirlari, metin_atiflari):
    girdiler = kaynakca_girdileri(kaynakca_satirlari)
    atiflar = [a for a in (ayristir(x) for x in metin_atiflari) if a]
    sonuc = {"atif_kaynakcada_yok": {}, "kaynakca_atifsiz": {}}

    for etiket in eksik_atiflar:
        a = ayristir(etiket)
        if not a:
            continue
        soyad, yil, _ = a
        kat, eslesen = "gercek_eksik", None
        for g in girdiler:
            if g["yil"] == yil and yakin(soyad, g["soyad"]):
                kat, eslesen = "yazim_farki", g["ad"]
                break
        else:
            for g in girdiler:
                if g["soyad"] == soyad and g["yil"] != yil:
                    kat, eslesen = "yil_farki", f"{g['ad']} ({g['yil']})"
                    break
            else:
                for g in girdiler:
                    if g["yil"] == yil and re.search(rf"\b{re.escape(soyad)}\b", g["norm"]):
                        kat, eslesen = "ikinci_yazar_olasi", g["ad"]
                        break
        sonuc["atif_kaynakcada_yok"].setdefault(kat, []).append(
            {"atif": etiket, "kaynakca": eslesen} if eslesen else {"atif": etiket})

    for etiket in eksik_kaynaklar:
        a = ayristir(etiket)
        if not a:
            continue
        soyad, yil, _ = a
        kat, eslesen = "gercek_atifsiz", None
        for (s2, y2, h2) in atiflar:
            if y2 == yil and yakin(soyad, s2):
                kat, eslesen = "yazim_farki", h2
                break
        else:
            for (s2, y2, h2) in atiflar:
                if s2 == soyad and y2 != yil:
                    kat, eslesen = "yil_farki", f"{h2} ({y2})"
                    break
            else:
                satir = next((g["norm"] for g in girdiler if g["soyad"] == soyad and g["yil"] == yil), "")
                for (s2, y2, h2) in atiflar:
                    if y2 == yil and s2 != soyad and re.search(rf"\b{re.escape(s2)}\b", satir):
                        kat, eslesen = "ikinci_yazar_olasi", h2
                        break
        sonuc["kaynakca_atifsiz"].setdefault(kat, []).append(
            {"kaynakca": etiket, "atif": eslesen} if eslesen else {"kaynakca": etiket})

    sonuc["ozet"] = {
        "atif_kaynakcada_yok": {k: len(v) for k, v in sonuc["atif_kaynakcada_yok"].items()},
        "kaynakca_atifsiz": {k: len(v) for k, v in sonuc["kaynakca_atifsiz"].items()},
    }
    return sonuc


if __name__ == "__main__":
    print(__doc__)
