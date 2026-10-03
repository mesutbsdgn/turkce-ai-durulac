#!/usr/bin/env python3
"""Türkçe okunabilirlik puanı ve sayı koruma denetimi (yalnız standart kütüphane).

Kullanım:
  python3 okunabilirlik.py metin.txt                 # tek metnin puanı
  python3 okunabilirlik.py once.txt sonra.txt        # önce/sonra + sayı koruma denetimi
  echo "metin" | python3 okunabilirlik.py -          # standart girdiden

Formüller (kamuya açık yayınlardan):
  Ateşman (1997):  198,825 - 40,175 * (hece/sözcük) - 2,610 * (sözcük/cümle)
                   90-100 çok kolay · 70-89 kolay · 50-69 orta · 30-49 zor · 1-29 çok zor
  Bezirci-Yılmaz (2010): sqrt(OKS * (H3*0,84 + H4*1,5 + H5*3,5 + H6*26,25))
                   OKS = cümle başına ortalama sözcük; Hn = cümle başına n heceli
                   (H6 için 6 ve üstü) ortalama sözcük. Sonuç yaklaşık eğitim yılıdır.

Hece = ünlü sayısı (Türkçede her hecede bir ünlü). Yalnız rakamdan oluşan
belirteçler sözcük sayılmaz. Puan yol göstericidir; kısa metinde (3 cümleden az)
oynaktır. Sayı koruma denetimi: sayı, tutar, yüzde ve tarihler önce ile sonrada
aynı mı (işaret, para birimi, yüzde ve bin/milyon ölçeği dâhil)?
Biçim de karşılaştırılır: "1.250,00" ile "1.250" farklı sayılır. Bir değer kaybolduysa ya da değiştiyse çıkış kodu 1 olur.
"""
import math
import re
import sys
from collections import Counter

UNLU = set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")
SOZCUK = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+(?:['’][A-Za-zÇĞİÖŞÜçğıöşüâîû]+)?")
# Cümle sonu: . ! ? … ardından boşluk ya da metin sonu ("12.500" bölünmez)
CUMLE_SONU = re.compile(r"(?<=[.!?…])\s+|\n\s*\n")
# Ardından gelen parça yeni cümle sayılmaz: kısaltma ("Dr.", "md.", "A.Ş.") ya da
# sıra sayısı ardından küçük harf ("3. çeyrek")
KISALTMA = {
    "dr", "prof", "doç", "av", "md", "mad", "vb", "vs", "bkz", "örn", "ör", "no",
    "sn", "ltd", "şti", "a.ş", "t.c", "mah", "cad", "sok", "tel", "yy", "s", "c", "bşk",
}
# Sayı benzeri değerler; işaret, para birimi, yüzde ve ölçek (bin/milyon/milyar)
# değerin parçasıdır: "1,5 milyon TL" → "1,5 TL" ya da "USD" → "TL" yakalanır.
TARIH = r"\d{1,2}[./]\d{1,2}[./]\d{2,4}"
SAYI = re.compile(
    r"(?<![\w.,])(?:" + TARIH + r"|"
    r"(?:(?:[₺$€]|%|(?:TL|USD|EUR)\s)\s?)?"             # önde birim: ₺1.250, %4,25
    r"(?:(?<![\d\w])[-−+])?"                              # işaret (10-20 aralığı hariç)
    r"\d+(?:[.,]\d+)*"
    r"(?:\s?%)?"                                          # 4,25%
    r"(?:\s?(?:bin|milyon|milyar|trilyon)(?![a-zçğıöşü]))?"
    r"(?:\s?(?:TL|USD|EUR|₺|\$|€)|\s?(?:lira|dolar|avro|euro)(?![a-zçğıöşü]))?"
    r")",
    re.IGNORECASE,
)


def hece(sozcuk: str) -> int:
    return max(1, sum(1 for h in sozcuk if h in UNLU))


def _kisaltmayla_biter(parca: str) -> bool:
    son = parca.rstrip().rsplit(maxsplit=1)[-1] if parca.strip() else ""
    son = son.rstrip(".").lower()
    return son in KISALTMA or bool(re.fullmatch(r"(?:\w\.)+\w", son))


def cumleler(metin: str) -> list[str]:
    birlesik: list[str] = []
    for parca in (c.strip() for c in CUMLE_SONU.split(metin.strip())):
        if not parca:
            continue
        if birlesik and (_kisaltmayla_biter(birlesik[-1])
                         or (parca[0].islower() and re.search(r"\d\.$", birlesik[-1]))):
            birlesik[-1] += " " + parca
        else:
            birlesik.append(parca)
    return [c for c in birlesik if SOZCUK.search(c)]


def olc(metin: str) -> dict:
    cumle = cumleler(metin)
    sozcukler = SOZCUK.findall(metin)
    n_c, n_s = len(cumle), len(sozcukler)
    if not n_c or not n_s:
        return {"cumle": n_c, "sozcuk": n_s, "atesman": None, "by": None}
    heceler = [hece(s) for s in sozcukler]
    atesman = 198.825 - 40.175 * (sum(heceler) / n_s) - 2.610 * (n_s / n_c)
    oks = n_s / n_c
    h = Counter(min(x, 6) for x in heceler)
    by = math.sqrt(oks * (h[3] / n_c * 0.84 + h[4] / n_c * 1.5
                          + h[5] / n_c * 3.5 + h[6] / n_c * 26.25))
    return {"cumle": n_c, "sozcuk": n_s, "ort_sozcuk": oks,
            "ort_hece": sum(heceler) / n_s, "atesman": atesman, "by": by}


def atesman_duzey(p: float) -> str:
    if p > 100 or p < 0: return "ölçek dışı; bu metinde puan karşılaştırılamaz"
    if p >= 90: return "çok kolay"
    if p >= 70: return "kolay"
    if p >= 50: return "orta"
    if p >= 30: return "zor"
    return "çok zor"


def by_duzey(p: float) -> str:
    if p <= 8: return "ilköğretim"
    if p <= 12: return "lise"
    if p <= 16: return "lisans"
    return "akademik"


def yaz(ad: str, o: dict) -> None:
    if o["atesman"] is None:
        print(f"{ad}: ölçülecek cümle yok")
        return
    uyari = "  (3 cümleden az: puan oynak)" if o["cumle"] < 3 else ""
    print(f"{ad}: {o['cumle']} cümle, {o['sozcuk']} sözcük, "
          f"cümle başına {o['ort_sozcuk']:.1f} sözcük, sözcük başına {o['ort_hece']:.2f} hece{uyari}")
    print(f"  Ateşman        {o['atesman']:6.1f}  ({atesman_duzey(o['atesman'])}; yüksek = kolay)")
    print(f"  Bezirci-Yılmaz {o['by']:6.1f}  ({by_duzey(o['by'])}; düşük = kolay)")


def normal(deger: str) -> str:
    return re.sub(r"\s+", "", deger).replace("−", "-").lower()


def oku(yol: str) -> str:
    if yol == "-":
        return sys.stdin.read()
    with open(yol, encoding="utf-8") as f:
        return f.read()


def main(arg: list[str]) -> int:
    if len(arg) not in (1, 2):
        print(__doc__)
        return 2
    once = oku(arg[0])
    o1 = olc(once)
    yaz("Önce" if len(arg) == 2 else "Metin", o1)
    if len(arg) == 1:
        return 0
    sonra = oku(arg[1])
    o2 = olc(sonra)
    yaz("Sonra", o2)
    if o1["atesman"] is not None and o2["atesman"] is not None:
        print(f"Fark: Ateşman {o2['atesman'] - o1['atesman']:+.1f}, "
              f"Bezirci-Yılmaz {o2['by'] - o1['by']:+.1f}")
    s1 = Counter(normal(x) for x in SAYI.findall(once))
    s2 = Counter(normal(x) for x in SAYI.findall(sonra))
    eksik, yeni = s1 - s2, s2 - s1
    if not eksik and not yeni:
        print(f"Sayı koruma: tamam ({sum(s1.values())} değer aynen korundu)")
        return 0
    print("Sayı koruma: SORUN")
    for d in sorted(eksik):
        print(f"  kayboldu/değişti: {d}")
    for d in sorted(yeni):
        print(f"  yeni çıktı:       {d}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
