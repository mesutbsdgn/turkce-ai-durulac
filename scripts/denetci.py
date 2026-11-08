#!/usr/bin/env python3
"""denetci.py — ajanın yaptığı izli değişiklikleri BAĞIMSIZ olarak denetler (tez_onar.py'yi kullanmaz).

Girdi: özgün docx ve ajanın ürettiği docx. Çıktı: her izli değişiklik için "önce → sonra" (yalnız değişen
parça ve bitişik sözcük), kural sınıfı ve uygun/şüpheli kararı. Cümle yazmaz.

Denetimler:
  1. Hepsini reddedince metin özgünle aynı mı?
  2. Her değişiklik bilinen bir kalıba uyuyor mu (atıf sayfa, ünsüz benzeşmesi, başlık, onaylı ad/yıl)?
  3. Değişikliklerin dışında hiçbir paragrafın metni farklı mı?
Kullanım: python3 denetci.py OZGUN.docx AJAN.docx [--onayli ayar.json]
"""
import json
import re
import sys
import zipfile
from xml.sax.saxutils import unescape

sys.dont_write_bytecode = True

YAZAR = "Durulaç-Ajan"
TOKEN_RE = re.compile(
    r'<w:(?P<tur>ins|del)\b[^>]*w:author="(?P<yazar>[^"]*)"[^>]*>(?P<ic>.*?)</w:(?P=tur)>'
    r'|<w:t(?:\s[^>]*)?>(?P<t>[^<]*)</w:t>', re.S)
PAR_RE = re.compile(r"<w:p(?=[\s>])[^>]*>(?:(?!<w:p[\s>]).)*?</w:p>", re.S)


def kucult_tr(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def metin_ic(ic):
    return unescape("".join(re.findall(r"<w:(?:t|delText)(?:\s[^>]*)?>([^<]*)</w:(?:t|delText)>", ic)),
                    {"&quot;": '"', "&apos;": "'"})


def belge_oku(yol):
    with zipfile.ZipFile(yol) as z:
        return z.read("word/document.xml").decode("utf-8")


def paragraf_parcalari(par):
    """[('keep'|'del'|'ins', metin)] sırasıyla; yalnız YAZAR'ın değişiklikleri."""
    parcalar = []
    for m in TOKEN_RE.finditer(par):
        if m.group("tur"):
            if m.group("yazar") == YAZAR:
                parcalar.append((m.group("tur"), metin_ic(m.group("ic"))))
            else:
                parcalar.append(("yabanci", metin_ic(m.group("ic"))))
        else:
            parcalar.append(("keep", unescape(m.group("t"), {"&quot;": '"', "&apos;": "'"})))
    return parcalar


def bitisik_sozcuk(parcalar, bas, son):
    """Değişimin solundaki ve sağındaki 'keep' metinlerden bitişik sözcük parçalarını alır (boşluğa kadar)."""
    sol = ""
    for t, m in reversed(parcalar[:bas]):
        if t in ("del", "ins"):
            continue
        sol = m + sol
        if re.search(r"\s", m):
            break
    sag = ""
    for t, m in parcalar[son:]:
        if t in ("del", "ins"):
            continue
        sag += m
        if re.search(r"\s", m):
            break
    sol = re.split(r"\s", sol)[-1] if sol else ""
    sag = re.split(r"\s", sag)[0] if sag else ""
    return sol, sag


def paragraf_degisiklikleri(par):
    """[(eski_sozcuk, yeni_sozcuk, eski_parca, yeni_parca)] — bitişik sözcükle birlikte."""
    parcalar = paragraf_parcalari(par)
    sonuc, i = [], 0
    while i < len(parcalar):
        if parcalar[i][0] in ("del", "ins"):
            bas = i
            eski = yeni = ""
            while i < len(parcalar) and parcalar[i][0] in ("del", "ins"):
                if parcalar[i][0] == "del":
                    eski += parcalar[i][1]
                else:
                    yeni += parcalar[i][1]
                i += 1
            sol, sag = bitisik_sozcuk(parcalar, bas, i)
            sonuc.append((sol + eski + sag, sol + yeni + sag, eski, yeni))
        else:
            i += 1
    return sonuc


def sinifla(eski_parca, yeni_parca, eski_s, yeni_s, onayli_ad, onayli_yil):
    """Bilinen kalıba uyuyorsa (sınıf, True); uymuyorsa ('bilinmeyen', False)."""
    if re.fullmatch(r",\s*(?:s|p|pp|ss)\.\s*", eski_parca) and yeni_parca.strip() == ":":
        return "ATIF_SAYFA", True
    if eski_parca == "d" and yeni_parca == "t":
        return "BENZESME", True
    if eski_parca == "" and yeni_parca == " ":
        return "BASLIK_BOSLUK", True
    if eski_parca and kucult_tr(eski_parca) == kucult_tr(yeni_parca) and eski_parca != yeni_parca:
        return "BASLIK_BUYUK", True
    for e, y in onayli_ad:
        if (eski_s.strip("()'’,.;:") == e and yeni_s.strip("()'’,.;:") == y) or (e in eski_s and eski_s.replace(e, y) == yeni_s):
            return "AD_DUZELT", True
    for e, y in onayli_yil:
        if eski_s.strip("()'’,.;:") == e and yeni_s.strip("()'’,.;:") == y:
            return "YIL_DUZELT", True
    return "bilinmeyen", False


def hepsini_reddet_metinleri(xml):
    xml = re.sub(r"<w:ins\b[^>]*>.*?</w:ins>", "", xml, flags=re.S)
    xml = re.sub(r"<w:del\b[^>]*>(.*?)</w:del>", r"\1", xml, flags=re.S).replace("w:delText", "w:t")
    return [metin_ic(p) for p in PAR_RE.findall(xml)]


def denetle(ozgun_yol, ajan_yol, onayli=None):
    ozgun, ajan = belge_oku(ozgun_yol), belge_oku(ajan_yol)
    onayli = onayli or {}
    onayli_ad = [(d["eski"], d["yeni"]) for d in onayli.get("ad", [])]
    onayli_yil = [(d["eski"], d["yeni"]) for d in onayli.get("yil", [])]
    sonuc = {"degisiklikler": [], "sayilar": {}, "sorunlar": []}

    # 1) hepsini reddet = özgün
    ozgun_metin = hepsini_reddet_metinleri(ozgun)
    ajan_reddedilmis = hepsini_reddet_metinleri(ajan)
    if ozgun_metin != ajan_reddedilmis:
        farkli = sum(1 for a, b in zip(ozgun_metin, ajan_reddedilmis) if a != b) + abs(len(ozgun_metin) - len(ajan_reddedilmis))
        sonuc["sorunlar"].append(f"hepsini reddedince {farkli} paragraf özgünden farklı")

    # 2) her değişiklik bilinen bir kalıba uyuyor mu
    for no, par in enumerate(PAR_RE.findall(ajan)):
        for eski_s, yeni_s, eski_p, yeni_p in paragraf_degisiklikleri(par):
            sinif, uygun = sinifla(eski_p, yeni_p, eski_s, yeni_s, onayli_ad, onayli_yil)
            sonuc["degisiklikler"].append({"paragraf": no, "sinif": sinif, "uygun": uygun,
                                           "once": eski_s, "sonra": yeni_s,
                                           "parca": [eski_p, yeni_p]})
            sonuc["sayilar"][sinif] = sonuc["sayilar"].get(sinif, 0) + 1
            if not uygun:
                sonuc["sorunlar"].append(f"paragraf {no}: bilinmeyen değişiklik")

    # 3) yabancı yazarın izli değişikliği (ajan dışında) var mı
    yabanci = len(re.findall(r'<w:(?:ins|del)\b[^>]*w:author="(?!%s")' % re.escape(YAZAR), ajan))
    sonuc["yabanci_degisiklik_sayisi"] = yabanci
    return sonuc


def main(arg):
    if len(arg) < 2:
        print(__doc__)
        return 2
    onayli = None
    if "--onayli" in arg:
        with open(arg[arg.index("--onayli") + 1], encoding="utf-8") as f:
            onayli = json.load(f).get("duzeltmeler")
    s = denetle(arg[0], arg[1], onayli)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    return 4 if s["sorunlar"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
