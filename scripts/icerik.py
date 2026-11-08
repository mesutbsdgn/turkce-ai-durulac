#!/usr/bin/env python3
"""icerik.py — brif tabanlı konu kapsamı denetimi (model YOK, yalnız sözcük eşleşmesi).

Girdi : ana metin + brif (konu başlığı, anahtar sözcükler).
Çıktı : her konu için sözcük bazında geçiş sayısı ve geçtiği bölüm numaraları.
Rapor yalnız brifteki ifadeleri, sayıları ve bölüm sıra numaralarını içerir; tez cümlesi ya da başlık metni içermez.

Brif biçimi (calisma/brif.json):
  {"konular": [{"id": "C1", "ad": "7545 ve 177 sayılı CBK", "terimler": ["7545", "siber güvenlik kanunu"], "en_az": 1}]}
Eşleşme: Türkçe harf katlanmış, küçük harfli, sözcük başı eşleşmesi (ekler kabul).
"""
import json
import re
import sys

sys.dont_write_bytecode = True

KATLA = str.maketrans({"ı": "i", "â": "a", "î": "i", "û": "u", "ş": "s", "ç": "c", "ğ": "g", "ö": "o", "ü": "u"})


def katla(s):
    return s.replace("İ", "i").replace("I", "ı").lower().translate(KATLA)


def terim_re(t):
    kat = re.escape(katla(t.strip()))
    kat = kat.replace(r"\ ", r"\s+")
    son = r"(?![0-9])" if kat[-1:].isdigit() else ""
    return re.compile(r"(?<![0-9a-z])" + kat + son)


def bolum_sirasi(metin, bolumlere_ayir):
    """[(sıra_no, katlanmış_içerik)]; başlık metni raporlanmaz."""
    return [(i + 1, katla(icerik)) for i, (_, icerik) in enumerate(bolumlere_ayir(metin))]


def brif_dogrula(brif):
    hatalar = []
    konular = brif.get("konular") if isinstance(brif, dict) else None
    if not konular:
        return ["brif.json: 'konular' boş ya da yok"]
    gorulen = set()
    for k in konular:
        if not isinstance(k, dict) or not k.get("id") or not k.get("terimler"):
            hatalar.append(f"konu eksik alan: {k!r}"[:80])
            continue
        if k["id"] in gorulen:
            hatalar.append(f"yinelenen id: {k['id']}")
        gorulen.add(k["id"])
        if not all(isinstance(t, str) and t.strip() for t in k["terimler"]):
            hatalar.append(f"geçersiz terim: {k['id']}")
    return hatalar


def tara(metin, brif, bolumlere_ayir):
    bolumler = bolum_sirasi(metin, bolumlere_ayir)
    sonuc = []
    for k in brif["konular"]:
        en_az = int(k.get("en_az", 1))
        terimler = []
        toplam = 0
        yerler = set()
        gorulen_terim = set()
        for t in k["terimler"]:
            if katla(t.strip()) in gorulen_terim:
                continue
            gorulen_terim.add(katla(t.strip()))
            rx = terim_re(t)
            sayi = 0
            for no, icerik in bolumler:
                n = len(rx.findall(icerik))
                if n:
                    sayi += n
                    yerler.add(no)
            terimler.append({"terim": t, "gecis": sayi})
            toplam += sayi
        kapsanan = sum(1 for x in terimler if x["gecis"] > 0)
        durum = "yok" if toplam == 0 else ("zayif" if toplam < en_az else "var")
        sonuc.append({"id": k["id"], "oncelik": k.get("oncelik", "destek"), "ad": k.get("ad", ""), "durum": durum, "toplam_gecis": toplam,
                      "terim_kapsami": f"{kapsanan}/{len(terimler)}", "bolumler": sorted(yerler),
                      "terimler": terimler})
    return {"bolum_sayisi": len(bolumler), "konular": sonuc,
            "ozet": {d: sum(1 for s in sonuc if s["durum"] == d) for d in ("var", "zayif", "yok")}}


def markdown(s):
    out = ["# İçerik kapsamı (brif tabanlı, cümlesiz)", "",
           f"Bölüm sayısı: {s['bolum_sayisi']} · var: {s['ozet']['var']} · zayıf: {s['ozet']['zayif']} · yok: {s['ozet']['yok']}", "",
           "| Konu | Öncelik | Durum | Geçiş | Terim kapsamı | Bölüm no |", "|---|---|---|---|---|---|"]
    for k in s["konular"]:
        out.append(f"| {k['id']} {k['ad']} | {k['oncelik']} | {k['durum']} | {k['toplam_gecis']} | {k['terim_kapsami']} | "
                   f"{', '.join(map(str, k['bolumler'])) or '-'} |")
    out += ["", "## Terim ayrıntısı", ""]
    for k in s["konular"]:
        out.append(f"- {k['id']}: " + "; ".join(f"{t['terim']}={t['gecis']}" for t in k["terimler"]))
    return "\n".join(out) + "\n"
