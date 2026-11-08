#!/usr/bin/env python3
"""tez_onar.py — kural tabanlı tez onarımı; her METİN değişikliği izli değişikliktir (w:ins / w:del).

Yalnız standart kütüphane. Orijinal dosyaya dokunmaz; yeni .docx yazar.

Kurallar (hepsi belirleyici, model yok):
  ATIF_SAYFA     (Soyad, 2014, s.102) -> (Soyad, 2014: 102)         İAÜ Madde V.A
  BENZESME       Kitap'da -> Kitap'ta, 1960'da -> 1960'ta            ünsüz benzeşmesi
  BASLIK_BOSLUK  IX.SONUÇ -> IX. SONUÇ                               İAÜ Madde III.C
  BASLIK_BUYUK   1. düzey başlık tamamı BÜYÜK HARF                   İAÜ Madde III.C
Biçim (izsiz, günlüğe yazılır): üst/alt kenar boşluğu 2,5 cm (--kenar).

Kullanım:
  python3 tez_onar.py GIRDI.docx                       # kuru: yalnız sayar
  python3 tez_onar.py GIRDI.docx CIKTI.docx [--kenar]  # yazar ve doğrular
Özet çıktısı cümlesizdir (yalnız sayılar).
"""
import datetime
import hashlib
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, unescape

sys.dont_write_bytecode = True

YAZAR = "Durulaç-Ajan"
KENAR_TWIPS = 1417  # 2,5 cm
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS

TAG_RE = re.compile(r"<(/?)([A-Za-z0-9_:]+)((?:\s[^>]*?)?)(/?)>", re.S)
P_TAG_RE = re.compile(r"<w:p(?=[\s/>])[^>]*?(/?)>|</w:p>")
RUN_RE = re.compile(
    r"^<w:r(?P<ra>(?:\s[^>]*)?)>(?P<rpr><w:rPr>.*?</w:rPr>|<w:rPr/>)?"
    r"<w:t(?P<ta>(?:\s[^>]*)?)>(?P<t>[^<]*)</w:t></w:r>$", re.S)
SEFFAF = ("w:proofErr", "w:bookmarkStart", "w:bookmarkEnd")
BASLIK1_STILLERI = {"Balk1", "Heading1", "Heading 1", "Balk 1"}

EK_DUZELT = {"da": "ta", "de": "te", "dan": "tan", "den": "ten"}
SAYI_BENZESME_RE = re.compile(r"\b(\d*(?:[345]|[467]0))\s*['’]\s*(da|de|dan|den)\b")
KELIME_BENZESME_RE = re.compile(
    r"\b([A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]{2,}[fstkçşhpFSTKÇŞHP])\s*['’]\s*(da|de|dan|den)\b")
ATIF_SAYFA_RE = re.compile(r",\s*(?:s|p|pp|ss)\.\s*(?=\d)")
YIL_SONU_RE = re.compile(r"(?:19|20)\d\d[a-z]?$")


def kucult_tr(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def buyut_tr(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def ozet(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------- kurallar
def kural_oner(metin, stil, ilk_segment=True, baslik_roman=None, once_ek="", duzeltmeler=None):
    """Segment metni için [(bas, son, yeni, kural_id)] önerir (örtüşenler ayıklanır).

    ilk_segment: paragrafın ilk metin parçası mı; baslik_roman: paragraf Romen rakamıyla başlayan kısa metin mi
    (None ise bu segmentten çıkarılır); once_ek: aynı paragrafta bu segmentten önceki metin (yalnız bağlam).
    """
    if baslik_roman is None:
        baslik_roman = bool(re.match(r"^[IVX]{1,5}\.", metin)) and len(metin) < 200
    oneriler = []
    for m in ATIF_SAYFA_RE.finditer(metin):
        once = once_ek + metin[:m.start()]
        if YIL_SONU_RE.search(once) and once.rfind("(") > once.rfind(")"):
            oneriler.append((m.start(), m.end(), ": ", "ATIF_SAYFA"))
    for rx in (SAYI_BENZESME_RE, KELIME_BENZESME_RE):
        for m in rx.finditer(metin):
            govde = m.group(1)
            if rx is KELIME_BENZESME_RE and govde.isupper():
                continue  # kısaltmalar harf adıyla okunur (TSK'da); karar insanındır
            oneriler.append((m.start(2), m.end(2), EK_DUZELT[m.group(2)], "BENZESME"))
    if baslik_roman:
        duzeltilmis = (re.sub(r"^([IVX]{1,5}\.)(?=[A-Za-zÇĞİÖŞÜçğıöşü])", r"\1 ", metin)
                       if ilk_segment else metin)
        if stil in BASLIK1_STILLERI and any(c.islower() for c in duzeltilmis):
            oneriler.append((0, len(metin), buyut_tr(duzeltilmis), "BASLIK_BUYUK"))
        elif (ilk_segment and duzeltilmis != metin and re.match(r"^[IVX]{1,5}\.[A-ZÇĞİÖŞÜ]", metin)
              and stil.startswith(("Balk", "Heading"))):
            oneriler.append((len(re.match(r"^[IVX]{1,5}\.", metin).group(0)),) * 2 + (" ", "BASLIK_BOSLUK"))
    for d in (duzeltmeler or {}).get("ad", []):
        eski, yeni = d["eski"], d["yeni"]
        for m in re.finditer(rf"(?<![\wÇĞİÖŞÜçğıöşüÂÎÛâîû]){re.escape(eski)}(?![\wÇĞİÖŞÜçğıöşüÂÎÛâîû])", metin):
            if d.get("kapsam") == "kaynakca_basi" and not (ilk_segment and m.start() == 0):
                continue
            oneriler.append((m.start(), m.end(), yeni, "AD_DUZELT"))
    for d in (duzeltmeler or {}).get("yil", []):
        sy = re.escape(d["soyad"])
        rx = re.compile(rf"(?<![\wÇĞİÖŞÜçğıöşüÂÎÛâîû]){sy}(?![\wÇĞİÖŞÜçğıöşüÂÎÛâîû])(?:[^;()]{{0,60}}?,|\s*\()\s*(?P<y>{re.escape(d['eski'])})(?!\d)")
        for m in rx.finditer(metin):
            oneriler.append((m.start("y"), m.end("y"), d["yeni"], "YIL_DUZELT"))
    oneriler.sort(key=lambda o: (o[0], o[1]))
    secilen, son = [], -1
    for o in oneriler:
        if o[0] >= son:
            secilen.append(o)
            son = max(o[1], o[0] + 1) if o[1] == o[0] else o[1]
    return secilen


IZINLI_AD = set()   # (eski, yeni) çiftleri: yalnız kullanıcının onayladığı düzeltmeler
IZINLI_YIL = set()


def degisiklik_gecerli(kural, eski, yeni):
    """Kural başına değişmez: izin verilmeyen bir fark varsa değişiklik reddedilir."""
    if kural == "YENIDEN_KUR":
        return yeni != eski and bool(yeni.strip() or eski.strip())  # asıl doğrulama benzerlik.py içinde yapılır; saf silme/ekleme serbest
    if kural == "AD_DUZELT":
        return (eski, yeni) in IZINLI_AD and eski != yeni
    if kural == "YIL_DUZELT":
        return (eski, yeni) in IZINLI_YIL and re.fullmatch(r"(?:19|20)\d\d", yeni) is not None
    if kural == "ATIF_SAYFA":
        return yeni == ": " and bool(re.fullmatch(r",\s*(?:s|p|pp|ss)\.\s*", eski))
    if kural == "BENZESME":
        return EK_DUZELT.get(eski) == yeni
    if kural == "BASLIK_BOSLUK":
        return eski == "" and yeni == " "
    if kural == "BASLIK_BUYUK":
        return kucult_tr(re.sub(r"\s+", "", yeni)) == kucult_tr(re.sub(r"\s+", "", eski))
    return False


# ------------------------------------------------------------- XML yardımcıları
def paragraflar(xml):
    """İçinde iç içe w:p olmayan (yaprak) paragrafların (bas, son) aralıkları."""
    yigin, sonuc = [], []
    for m in P_TAG_RE.finditer(xml):
        if m.group(0).startswith("</"):
            if yigin:
                bas, ic_var = yigin.pop()
                if not ic_var:
                    sonuc.append((bas, m.end()))
        elif not m.group(1):
            if yigin:
                yigin[-1] = (yigin[-1][0], True)
            yigin.append((m.start(), False))
    return sonuc


def cocuklar(ic):
    """Paragraf içeriğinin üst düzey çocuklarını sırayla döner; birleşimleri ic'e eşit değilse None."""
    cikti, derinlik, bas = [], 0, 0
    for m in TAG_RE.finditer(ic):
        kapat, _, _, ozkapat = m.groups()
        if ozkapat:
            if derinlik == 0:
                cikti.append(ic[m.start():m.end()])
        elif kapat:
            derinlik -= 1
            if derinlik == 0:
                cikti.append(ic[bas:m.end()])
        else:
            if derinlik == 0:
                bas = m.start()
            derinlik += 1
    return cikti if "".join(cikti) == ic else None


def ac_kapat(par):
    ac = re.match(r"<w:p(?:\s[^>]*)?>", par).group(0)
    return ac, par[len(ac):-len("</w:p>")]


def sonraki_id(xml):
    ids = [int(x) for x in re.findall(r'w:id="(\d+)"', xml)]
    return max(ids + [0]) + 1000


def calisma_xml(ra, rpr, metin, silinen):
    etiket = "w:delText" if silinen else "w:t"
    return f'<w:r{ra}>{rpr or ""}<{etiket} xml:space="preserve">{escape(metin)}</{etiket}></w:r>'


def duzenlemeleri_uygula(cocuk_listesi, segment, duzenlemeler, kimlik, tarih):
    """segment: [(cocuk_indeksi, ra, rpr, metin)], duzenlemeler: [(bas, son, yeni, kural)] -> cocuk_listesi güncellenir."""
    kes = []
    for bas, son, yeni, kural in duzenlemeler:
        # ortak ön ek/son ek atılır: izli fark en küçük olsun (YENIDEN_KUR sözcük bazlı hesaplandı; sözcük ortasından kesilmez)
        eski = "".join(s[3] for s in segment)[bas:son]
        a = b = 0
        if kural != "YENIDEN_KUR":
            while a < min(len(eski), len(yeni)) and eski[a] == yeni[a]:
                a += 1
            while b < min(len(eski), len(yeni)) - a and eski[len(eski) - 1 - b] == yeni[len(yeni) - 1 - b]:
                b += 1
        kes.append((bas + a, son - b, yeni[a:len(yeni) - b]))
    kes = [k for k in kes if not (k[0] == k[1] and k[2] == "")]
    kes.sort()
    konum, sayac = 0, kimlik
    for ci, ra, rpr, metin in segment:
        r_bas, r_son = konum, konum + len(metin)
        konum = r_son
        sinirlar = {r_bas, r_son}
        for kb, ks, _ in kes:
            for p in (kb, ks):
                if r_bas < p < r_son:
                    sinirlar.add(p)
        sinirlar = sorted(sinirlar)
        if len(sinirlar) == 2 and not any(
                (kb < r_son and ks > r_bas) or (kb == ks and r_bas <= kb <= r_son) for kb, ks, _ in kes):
            continue  # bu çalışmaya dokunulmaz, özgün XML korunur
        parcalar = []
        yerlestirilen = set()
        for x, y in zip(sinirlar, sinirlar[1:]):
            for j, (kb, ks, yeni) in enumerate(kes):
                if kb == ks and kb == x and j not in yerlestirilen:
                    parcalar.append(f'<w:ins w:id="{sayac}" w:author="{YAZAR}" w:date="{tarih}">{calisma_xml(ra, rpr, yeni, False)}</w:ins>')
                    sayac += 1
                    yerlestirilen.add(j)
            silinen = next((j for j, (kb, ks, _) in enumerate(kes) if kb != ks and kb <= x and y <= ks), None)
            parca_metin = metin[x - r_bas:y - r_bas]
            if silinen is None:
                parcalar.append(calisma_xml(ra, rpr, parca_metin, False))
            else:
                parcalar.append(f'<w:del w:id="{sayac}" w:author="{YAZAR}" w:date="{tarih}">{calisma_xml(ra, rpr, parca_metin, True)}</w:del>')
                sayac += 1
                if y == kes[silinen][1] and silinen not in yerlestirilen:
                    if kes[silinen][2]:
                        parcalar.append(f'<w:ins w:id="{sayac}" w:author="{YAZAR}" w:date="{tarih}">{calisma_xml(ra, rpr, kes[silinen][2], False)}</w:ins>')
                        sayac += 1
                    yerlestirilen.add(silinen)
        # çalışmanın sonunda biten saf eklemeler (segment sonu)
        for j, (kb, ks, yeni) in enumerate(kes):
            if kb == ks and kb == r_son and j not in yerlestirilen and ci == segment[-1][0]:
                parcalar.append(f'<w:ins w:id="{sayac}" w:author="{YAZAR}" w:date="{tarih}">{calisma_xml(ra, rpr, yeni, False)}</w:ins>')
                sayac += 1
                yerlestirilen.add(j)
        cocuk_listesi[ci] = "".join(parcalar)
    return sayac


def paragraf_onar(par, kimlik, tarih, gunluk, par_no, sayac_kural, atlanan, duzeltmeler=None):
    if "<w:ins " in par or "<w:del " in par or "<w:moveFrom" in par or "<w:moveTo" in par:
        atlanan["izli_degisiklik_var"] = atlanan.get("izli_degisiklik_var", 0) + 1
        return par, kimlik
    ac, ic = ac_kapat(par)
    cl = cocuklar(ic)
    if cl is None:
        atlanan["ayristirilamadi"] = atlanan.get("ayristirilamadi", 0) + 1
        return par, kimlik
    stil_m = re.search(r'<w:pStyle w:val="([^"]+)"', ac + ic)
    stil = stil_m.group(1) if stil_m else ""
    segmentler, aktif = [], []
    for i, c in enumerate(cl):
        m = RUN_RE.match(c.replace("<w:lastRenderedPageBreak/>", ""))  # yalnız Word önbellek ipucu
        if m and "&#" not in m.group("t"):
            aktif.append((i, m.group("ra") or "", m.group("rpr") or "",
                          unescape(m.group("t"), {"&quot;": '"', "&apos;": "'"})))
        elif any(c.startswith("<" + s) for s in SEFFAF):
            continue
        else:
            if aktif:
                segmentler.append(aktif)
            aktif = []
    if aktif:
        segmentler.append(aktif)
    degisti = False
    tum_metin = "".join(s[3] for seg in segmentler for s in seg)
    baslik_roman = bool(re.match(r"^[IVX]{1,5}\.", tum_metin)) and len(tum_metin) < 200
    once_ek = ""
    for sira, seg in enumerate(segmentler):
        metin = "".join(s[3] for s in seg)
        gecerli = []
        oneriler = kural_oner(metin, stil, ilk_segment=(sira == 0), baslik_roman=baslik_roman, once_ek=once_ek, duzeltmeler=duzeltmeler)
        once_ek += metin
        if EK_ONERI is not None:
            oneriler = oneriler + [o for o in EK_ONERI(metin) if not any(o[0] < b and a < o[1] for a, b, _, _ in oneriler)]
        for bas, son, yeni, kural in oneriler:
            if degisiklik_gecerli(kural, metin[bas:son], yeni):
                gecerli.append((bas, son, yeni, kural))
            else:
                sayac_kural["reddedildi_degisken"] = sayac_kural.get("reddedildi_degisken", 0) + 1
        if not gecerli:
            continue
        kimlik = duzenlemeleri_uygula(cl, seg, gecerli, kimlik, tarih)
        degisti = True
        for bas, son, yeni, kural in gecerli:
            sayac_kural[kural] = sayac_kural.get(kural, 0) + 1
            if kural in ("AD_DUZELT", "YIL_DUZELT"):  # onaylı eşleme adı: kullanıcının kendi verdiği ad/yıl
                anahtar = f"{kural}[{metin[bas:son]}→{yeni}]"
                sayac_kural[anahtar] = sayac_kural.get(anahtar, 0) + 1
            gunluk.append({"kural": kural, "paragraf": par_no,
                           "eski": ozet(metin[bas:son]), "yeni": ozet(yeni)})
    return (ac + "".join(cl) + "</w:p>", kimlik) if degisti else (par, kimlik)


def kenar_duzelt(xml, gunluk):
    def degistir(m):
        govde, sayi = m.group(0), 0
        for ad in ("top", "bottom"):
            mm = re.search(rf'w:{ad}="(-?\d+)"', govde)
            if mm and abs(int(mm.group(1)) - KENAR_TWIPS) > 85:
                govde = govde.replace(mm.group(0), f'w:{ad}="{KENAR_TWIPS}"')
                gunluk.append({"kural": "KENAR", "eski": mm.group(1), "yeni": str(KENAR_TWIPS)})
        return govde
    return re.sub(r"<w:pgMar\b[^>]*?/>", degistir, xml)


SON_TESHIS = {}
EK_ONERI = None  # benzerlik.py: metin -> [(bas, son, yeni, 'YENIDEN_KUR')]; yalnız belge_onar(ek_oneri=...) içinde atanır


def _artir(sozluk, anahtar, n=1):
    sozluk[anahtar] = sozluk.get(anahtar, 0) + n


def yapi_imzasi(par):
    """Yalnız XML etiket adlarından oluşan imza (metin yok): ör. 'r(t) bookmarkStart r(tab,t)'."""
    try:
        _, ic = ac_kapat(par)
    except AttributeError:
        return "ac_kapat_basarisiz"
    cl = cocuklar(ic)
    if cl is None:
        return "cocuklar_ayristirilamadi"
    cikti = []
    for c in cl[:14]:
        etiket = re.match(r"<w:(\w+)", c)
        ad = etiket.group(1) if etiket else "?"
        if ad == "r":
            govde = re.sub(r"<w:rPr>.*?</w:rPr>", "", c, flags=re.S)
            ic_etiket = [e for e in re.findall(r"<w:(\w+)", govde)[1:]]
            ad = "r(" + ",".join(dict.fromkeys(ic_etiket)) + ")" + ("&#" if "&#" in c else "")
        cikti.append(ad)
    return " ".join(cikti) + (" ..." if len(cl) > 14 else "")


def paragraf_teshisi(par, sayac_once, sayac_sonra, atlanan_once, atlanan_sonra, t):
    """Cümlesiz teşhis: yalnız stil adları ve sayılar toplanır, metin saklanmaz."""
    tam = unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", par)))
    stil_m = re.search(r'<w:pStyle w:val="([^"]+)"', par)
    stil = stil_m.group(1) if stil_m else "(yok)"
    _artir(t["stil_dagilimi"], stil)
    atlandi = [k for k in atlanan_sonra if atlanan_sonra[k] > atlanan_once.get(k, 0)]
    uygulanan = lambda *k: sum(sayac_sonra.get(x, 0) - sayac_once.get(x, 0) for x in k)  # noqa: E731
    if re.match(r"^\s*[IVX]{1,5}\.\s*[A-ZÇĞİÖŞÜa-zçğıöşü]", tam) and len(tam) < 200:
        _artir(t["baslik_benzeri_stiller"], stil)
        buyuk_gerekli = any(c.islower() for c in tam)
        if buyuk_gerekli or re.match(r"^\s*[IVX]{1,5}\.[A-ZÇĞİÖŞÜ]", tam):
            if uygulanan("BASLIK_BUYUK", "BASLIK_BOSLUK"):
                _artir(t, "baslik_duzeltilen")
            else:
                neden = (atlandi[0] if atlandi else
                         ("stil_baslik1_degil:" + stil if stil not in BASLIK1_STILLERI else "kural_uygulanmadi"))
                _artir(t["baslik_atlanma_nedenleri"], neden)
                if neden == "kural_uygulanmadi":
                    _artir(t["baslik_imzalari"], yapi_imzasi(par))
    adaylar = 0
    for m in ATIF_SAYFA_RE.finditer(tam):
        once = tam[:m.start()]
        if YIL_SONU_RE.search(once) and once.rfind("(") > once.rfind(")"):
            adaylar += 1
    if adaylar:
        _artir(t, "atif_adayi", adaylar)
        uyg = uygulanan("ATIF_SAYFA")
        _artir(t, "atif_duzeltilen", uyg)
        if adaylar > uyg:
            _artir(t["atif_atlanma_nedenleri"], atlandi[0] if atlandi else "parcali_ya_da_opak_calisma", adaylar - uyg)
            _artir(t["atif_imzalari"], yapi_imzasi(par))
    _artir(t, "paragraf_toplam")


def belge_onar(xml, kenar=False, duzeltmeler=None, ek_oneri=None):
    global EK_ONERI
    EK_ONERI = ek_oneri
    try:
        return _belge_onar(xml, kenar, duzeltmeler)
    finally:
        EK_ONERI = None


def _belge_onar(xml, kenar=False, duzeltmeler=None):
    gunluk, sayac, atlanan = [], {}, {}
    IZINLI_AD.clear(); IZINLI_YIL.clear()
    for d in (duzeltmeler or {}).get("ad", []):
        IZINLI_AD.add((d["eski"], d["yeni"]))
    for d in (duzeltmeler or {}).get("yil", []):
        IZINLI_YIL.add((d["eski"], d["yeni"]))
    tarih = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    kimlik = sonraki_id(xml)
    parcalar, onceki = [], 0
    teshis = {"stil_dagilimi": {}, "baslik_benzeri_stiller": {}, "baslik_atlanma_nedenleri": {},
              "atif_atlanma_nedenleri": {}, "baslik_imzalari": {}, "atif_imzalari": {}}
    for no, (bas, son) in enumerate(paragraflar(xml)):
        sayac_once, atlanan_once = dict(sayac), dict(atlanan)
        yeni, kimlik = paragraf_onar(xml[bas:son], kimlik, tarih, gunluk, no, sayac, atlanan, duzeltmeler)
        paragraf_teshisi(xml[bas:son], sayac_once, sayac, atlanan_once, atlanan, teshis)
        parcalar.append(xml[onceki:bas])
        parcalar.append(yeni)
        onceki = son
    parcalar.append(xml[onceki:])
    yeni_xml = "".join(parcalar)
    if kenar:
        yeni_xml = kenar_duzelt(yeni_xml, gunluk)
    teshis["stil_dagilimi"] = dict(sorted(teshis["stil_dagilimi"].items(), key=lambda kv: -kv[1])[:12])
    SON_TESHIS.clear()
    SON_TESHIS.update(teshis)
    return yeni_xml, gunluk, sayac, atlanan


# ------------------------------------------------------------------ doğrulama
def _metin(xml):
    kok = ET.fromstring(xml)
    return ["".join(t.text or "" for t in p.iter(W + "t")) for p in kok.iter(W + "p")]


def hepsini_reddet(xml):
    # paragraf işareti izli eklenmiş (yerlestir.py) paragraflar tamamen kalkar
    xml = re.sub(r"<w:p>(?:(?!</w:p>).)*?<w:rPr><w:ins\b[^>]*/>(?:(?!</w:p>).)*</w:p>", "", xml, flags=re.S)
    xml = re.sub(r"<w:ins\b[^>]*/>", "", xml)
    xml = re.sub(r"<w:ins\b[^>]*>.*?</w:ins>", "", xml, flags=re.S)
    xml = re.sub(r"<w:del\b[^>]*>(.*?)</w:del>", r"\1", xml, flags=re.S)
    return xml.replace("<w:delText", "<w:t").replace("</w:delText>", "</w:t>")


def hepsini_kabul(xml):
    xml = re.sub(r"<w:ins\b[^>]*/>", "", xml)
    xml = re.sub(r"<w:del\b[^>]*>.*?</w:del>", "", xml, flags=re.S)
    return re.sub(r"<w:ins\b[^>]*>(.*?)</w:ins>", r"\1", xml, flags=re.S)


def dogrula(eski_xml, yeni_xml):
    """Hata listesi döner (boş = temiz): iyi biçimlilik, 'hepsini reddet' = orijinal metin."""
    hatalar = []
    try:
        yeni_metin_reddedilmis = _metin(hepsini_reddet(yeni_xml))
    except ET.ParseError as e:
        return [f"XML bozuk: {e}"]
    if yeni_metin_reddedilmis != _metin(hepsini_reddet(eski_xml)):
        hatalar.append("hepsini reddedince metin orijinalden farklı")
    return hatalar


def onar_dosya(girdi, cikti=None, kenar=False, duzeltmeler=None, ek_oneri=None):
    with zipfile.ZipFile(girdi) as z:
        eski_xml = z.read("word/document.xml").decode("utf-8")
    yeni_xml, gunluk, sayac, atlanan = belge_onar(eski_xml, kenar=kenar, duzeltmeler=duzeltmeler, ek_oneri=ek_oneri)
    hatalar = dogrula(eski_xml, yeni_xml)
    sonuc = {"sayac": sayac, "atlanan": atlanan, "izli_degisiklik": sum(1 for g in gunluk if g["kural"] != "KENAR"),
             "izsiz_kenar": sum(1 for g in gunluk if g["kural"] == "KENAR"), "hatalar": hatalar,
             "teshis": dict(SON_TESHIS), "gunluk": gunluk}
    if cikti and not hatalar:
        with zipfile.ZipFile(girdi) as zi, zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as zo:
            for bilgi in zi.infolist():
                veri = zi.read(bilgi.filename)
                if bilgi.filename == "word/document.xml":
                    veri = yeni_xml.encode("utf-8")
                zo.writestr(bilgi, veri)
        with zipfile.ZipFile(cikti) as z:
            if z.testzip() is not None:
                sonuc["hatalar"].append("çıktı zip bozuk")
    return sonuc


def main(arg):
    if not arg or any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0 if arg else 2
    kenar = "--kenar" in arg
    yollar = [a for a in arg if not a.startswith("--")]
    girdi = yollar[0]
    cikti = yollar[1] if len(yollar) > 1 else None
    if not os.path.isfile(girdi):
        print(f"tez_onar: dosya yok: {girdi}", file=sys.stderr)
        return 2
    s = onar_dosya(girdi, cikti, kenar=kenar)
    print(json.dumps({k: v for k, v in s.items() if k != "gunluk"}, ensure_ascii=False, indent=2))
    return 4 if s["hatalar"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
