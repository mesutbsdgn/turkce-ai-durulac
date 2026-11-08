#!/usr/bin/env python3
"""Bilgi koruma denetimi: sadeleştirme ya da kısaltma bilgi düşürdü mü?

Sadeleştirme sözcük yükünü azaltır, bilgiyi değil (SKILL.md "Sadeleştirme ≠ özetleme").
Bu betik önce/sonra metinlerini karşılaştırır ve kaybolan bilgi birimlerini listeler:

  * sayı      — sayı, tutar, yüzde, tarih (okunabilirlik.py ile aynı desen)
  * alıntı    — tırnak içindeki söz ("…", “…”)
  * ad        — cümle ortasında büyük harfle başlayan özel ad (kişi, kurum, yer)
  * atıf      — kaynak atfı ve denge işaretleri: "…'ya göre", iddia, yalanlama, ret,
                "teyit edilmedi", "yorum yapmadı"; düşerse iddia olgu gibi görünür ya da
                karşı taraf susturulmuş olur

Kullanım:
  python3 bilgi_koruma.py once.txt sonra.txt
  python3 bilgi_koruma.py --json once.json sonra.json [--alan ozet] [--anahtar id]
      JSON: öğe listesi ya da {"olaylar": [...]}; öğeler anahtar alanıyla eşlenir.

Çıkış: 0 kayıp yok, 1 en az bir bilgi birimi kayboldu, 2 kullanım hatası.
Bulgu bir kontrol listesidir: kaybolan birim gerçekten gereksizse (ör. aynı sayının
tekrarı) gerekçesini "Ne değiştirdim" listesine yaz; değilse metne geri koy.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from okunabilirlik import SAYI, normal  # noqa: E402

ALINTI = re.compile(r"[\"“”«]([^\"“”«»]{2,})[\"“”»]")
# Büyük harfle başlayan sözcük; kesme işaretinden sonraki ek atılır (Sarıgül'ün → Sarıgül).
AD = re.compile(r"\b([A-ZÇĞİÖŞÜ][\wçğıöşüâîû.-]*)(?:['’][\wçğıöşüâîû]+)?")
CUMLE_BASI = re.compile(r"(?:^|[.!?…]\s+|\n\s*)([A-ZÇĞİÖŞÜ][\wçğıöşüâîû.-]*)")
ATIF = {
    "göre": r"\w+['’]?[ae] göre\b",
    "iddia": r"\biddia",
    "yalanlama": r"\byalanla",
    "ret": r"\bredde[dt]|\breddi\b",  # reddetti, reddedip, reddi
    "teyit yok": r"teyit edil(?:me|em)|doğrulan(?:ma|ama)",
    "yorum yok": r"yorum yap(?:ma|ma)",
    "öne sürme": r"öne sür",
}


# Ay adları tarih olarak sayı denetimine girer; ad sayılmaz.
AYLAR = {"Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"}


def _adlar(metin: str) -> set[str]:
    metin = ALINTI.sub(" ", metin)  # alıntı içindeki sözcükler alıntı denetimine girer
    basta = {m.group(1) for m in CUMLE_BASI.finditer(metin)}
    tum = Counter(m.group(1).rstrip(".-") for m in AD.finditer(metin))
    # Cümle başındaki sözcük yalnız başka bir yerde de büyük harfle geçiyorsa ad sayılır.
    return {a for a, n in tum.items()
            if len(a) > 1 and a not in AYLAR and (a not in basta or n > 1)}


def birimler(metin: str) -> dict[str, Counter]:
    return {
        "sayı": Counter(normal(x) for x in SAYI.findall(metin)),
        "alıntı": Counter(" ".join(x.split()).lower() for x in ALINTI.findall(metin)),
        "ad": Counter(_adlar(metin)),
        "atıf": Counter(
            {ad: len(re.findall(desen, metin, re.I)) for ad, desen in ATIF.items()
             if re.search(desen, metin, re.I)}
        ),
    }


def kayiplar(once: str, sonra: str) -> dict[str, list[str]]:
    """Önce metninde olup sonra metninde kalmayan birimler (tür → liste)."""
    b1, b2 = birimler(once), birimler(sonra)
    sonuc: dict[str, list[str]] = {}
    for tur in b1:
        if tur == "ad":
            # Ad, sonra metninde herhangi bir biçimde geçiyorsa korunmuş sayılır.
            eksik = [a for a in b1["ad"] if a not in sonra]
        elif tur == "atıf":
            eksik = [a for a in b1["atıf"] if a not in b2["atıf"]]
        else:
            eksik = sorted((b1[tur] - b2[tur]).elements())
        if eksik:
            sonuc[tur] = sorted(set(eksik))
    return sonuc


def _yaz(baslik: str, k: dict[str, list[str]]) -> None:
    print(baslik)
    for tur, liste in k.items():
        print(f"  {tur:7} kayboldu: {', '.join(liste)}")


def _ogeler(yol: str, alan: str, anahtar: str) -> dict[str, str]:
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    if isinstance(veri, dict):
        veri = veri.get("olaylar") or []
    return {o[anahtar]: o.get(alan) or "" for o in veri if anahtar in o}


def main(arg: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sadeleştirmede kaybolan bilgi birimlerini listeler.")
    ap.add_argument("once")
    ap.add_argument("sonra")
    ap.add_argument("--json", action="store_true", help="öğe listesi karşılaştır")
    ap.add_argument("--alan", default="ozet")
    ap.add_argument("--anahtar", default="id")
    a = ap.parse_args(arg)
    for yol in (a.once, a.sonra):
        if not os.path.isfile(yol):
            print(f"bilgi_koruma: dosya bulunamadı: {yol}", file=sys.stderr)
            return 2

    if not a.json:
        with open(a.once, encoding="utf-8") as f1, open(a.sonra, encoding="utf-8") as f2:
            k = kayiplar(f1.read(), f2.read())
        if not k:
            print("Bilgi koruma: tamam")
            return 0
        _yaz("Bilgi koruma: SORUN", k)
        return 1

    once, sonra = _ogeler(a.once, a.alan, a.anahtar), _ogeler(a.sonra, a.alan, a.anahtar)
    sorunlu = 0
    for anahtar, metin in once.items():
        if anahtar not in sonra:
            print(f"{anahtar}: sonra dosyasında yok (öğe düştü)")
            sorunlu += 1
            continue
        k = kayiplar(metin, sonra[anahtar])
        if k:
            sorunlu += 1
            _yaz(f"{anahtar}:", k)
    print(f"Bilgi koruma: {len(once)} öğe, {sorunlu} öğede kayıp"
          + (" — tamam" if not sorunlu else ""))
    return 1 if sorunlu else 0


if __name__ == "__main__":
    sys.exit(main())
