#!/usr/bin/env python3
"""benzerlik.py — Quetext raporundaki atıfsız ve yüksek benzerlikli eşleşmeleri yerel modelle yeniden kurar.

Her yeniden kurulan cümle Word'de izli değişikliktir (w:del + w:ins, yazar "Durulaç-Ajan"); reddetmek orijinali geri getirir.
Model yalnız sunucudaki Ollama'ya (127.0.0.1) gider. Çıktı raporu cümlesizdir (eşleşme no, yüzde, alan adı, durum).

ÖNEMLİ: Yeniden kurmak benzerlik oranını düşürür ama atıf eksikliğini gidermez. Raporda "atıf eklenecek" listesi çıkar;
kaynak künyesi uydurulmaz, yazar ekler.

Doğrulama (her cümle için; biri tutmazsa değişiklik YAPILMAZ):
  - sayılar aynı, parantez içi (Soyad, Yıl) atıfları aynı, büyük harfle başlayan özel adlar yeni sözcük içermez
  - uzunluk eski cümlenin %60-%140'ı, aynı bitiş noktalaması
  - eşleşen metinden ardışık 5 sözcük yeni cümlede kalmaz; 4'lü diziler en çok %30 ortak
"""
import json
import re
import sys
import urllib.request

sys.dont_write_bytecode = True

KATLA = str.maketrans({"ı": "i", "â": "a", "î": "i", "û": "u", "ş": "s", "ç": "c", "ğ": "g", "ö": "o", "ü": "u"})
KISALTMA = {"al", "vb", "vs", "bkz", "örn", "orn", "md", "s", "ss", "no", "dr", "prof", "doç", "doc", "yrd", "sn", "mad", "ör"}
ATIF_RE = re.compile(r"\([^()]{0,160}\b(?:1[89]|20)\d{2}[a-z]?\b[^()]{0,60}\)")
SAYI_RE = re.compile(r"\d+(?:[.,]\d+)?")
BUYUK_RE = re.compile(r"\b[A-ZÇĞİÖŞÜ][\w'’-]{2,}")
OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"

PROMPT = ("Aşağıdaki cümleyi yeniden yaz. Anlamı, sayıları, özel adları, kısaltmaları ve parantez içindeki atıfları AYNEN koru. "
          "Sözcük seçimini ve cümle yapısını değiştir; akademik, sade, doğal Türkçe kullan. "
          "Yalnız yeni cümleyi yaz; açıklama, tırnak ya da başlık ekleme.\n\nCümle: {cumle}\n\nYeni cümle:")


def katla(s):
    s = re.sub(r"[^\w\s]", " ", s.replace("İ", "i").replace("I", "ı").lower())
    return s.translate(KATLA)


def sozcukler(s):
    return katla(s).split()


def ngramlar(w, n):
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def cumle_baslangiclari(metin):
    bas = [0]
    for m in re.finditer(r"[.!?]+(?=\s+\S)", metin):
        once = re.findall(r"\w+", metin[:m.start()])
        if once and katla(once[-1]).strip() in KISALTMA:
            continue
        sonra = metin[m.end():]
        k = len(sonra) - len(sonra.lstrip())
        ilk = sonra.lstrip()[:1]
        if ilk.isupper() or ilk in "\"“‘'(":
            bas.append(m.end() + k)
    return bas


def cumle_siniri(metin, bas, son):
    """(cumle_bas, cumle_son) ya da None (cümle bütün değil)."""
    bs = cumle_baslangiclari(metin)
    cb = max(b for b in bs if b <= bas)
    sonraki = [b for b in bs if b > son]
    ce = sonraki[0] if sonraki else len(metin)
    cumle = metin[cb:ce].rstrip()
    if not cumle or cumle[-1] not in ".!?" and not cumle.endswith((".)", "!)", "?)")):
        return None
    if cb != 0 and not metin[cb:cb + 1].isupper():
        return None
    return cb, cb + len(cumle)


TERIM_CIFTLERI = [("kanun", "yasa"), ("teori", "kuram"), ("tabiat", "doğa"), ("yöntem", "metot"), ("olanak", "imkân"),
                  ("koşul", "şart"), ("siber uzay", "siber alan")]
BIRINCI_SAHIS_RE = re.compile(r"\b(?:tezimiz\w*|inceledik|yaptık|ettik|ulaştık|gördük|kanaatimce|çalışmamız\w*)\b", re.I)
TABLO_RE = re.compile(r"\bTablo\s+\d", re.I)


def terim_ihlali(eski, yeni):
    e, y = katla(eski), katla(yeni)
    for a, b in TERIM_CIFTLERI:
        ka, kb = katla(a), katla(b)
        for x, z in ((ka, kb), (kb, ka)):
            if re.search(r"(?<![0-9a-z])" + re.escape(x), e) and not re.search(r"(?<![0-9a-z])" + re.escape(z), e) \
                    and re.search(r"(?<![0-9a-z])" + re.escape(z), y) and not re.search(r"(?<![0-9a-z])" + re.escape(x), y):
                return True
    return False


def dogrula_cumle(eski, yeni, eslesen, n=5):
    """None = geçerli; aksi hâlde kısa neden kodu."""
    if not yeni or "\n" in yeni:
        return "bicim"
    if yeni.strip() == eski.strip():
        return "ayni"
    ew, yw = len(eski.split()), len(yeni.split())
    if not (0.6 * ew <= yw <= 1.4 * ew):
        return "uzunluk"
    if SAYI_RE.findall(eski) != SAYI_RE.findall(yeni):
        return "sayi"
    if sorted(ATIF_RE.findall(eski)) != sorted(ATIF_RE.findall(yeni)):
        return "atif"
    if terim_ihlali(eski, yeni):
        return "terim_birligi"
    if BIRINCI_SAHIS_RE.search(yeni) and not BIRINCI_SAHIS_RE.search(eski):
        return "birinci_sahis"
    if TABLO_RE.search(yeni) and not TABLO_RE.search(eski):
        return "tablo_cizelge"
    ilk_eski = {katla(x).strip() for x in BUYUK_RE.findall(eski)}
    yeni_buyuk = {katla(x).strip() for x in BUYUK_RE.findall(yeni)}
    ilk_kelime = katla(yeni.split()[0]).strip() if yeni.split() else ""
    if (yeni_buyuk - ilk_eski) - {ilk_kelime}:
        return "ozel_ad"
    if eski.rstrip()[-1] != yeni.rstrip()[-1]:
        return "noktalama"
    yw_n = sozcukler(yeni)
    if ngramlar(sozcukler(" ".join(eslesen)), n) & ngramlar(yw_n, n):
        return "eslesme_kaldi"
    e4, y4 = ngramlar(sozcukler(eski), 4), ngramlar(yw_n, 4)
    if e4 and len(e4 & y4) / len(e4) > 0.3:
        return "cok_benzer"
    return None


def temizle(cikti):
    t = (cikti or "").strip().split("\n")[0].strip()
    t = re.sub(r"^(Yeni cümle|Cümle)\s*:\s*", "", t, flags=re.I).strip()
    return t.strip("\"“”«»'‘’ ").strip()


SICAKLIK = (0.7, 0.9, 1.0, 1.0)


def cakisan_ifadeler(eslesen_ham, yeni, en_cok=4, n=5):
    """Yeni cümlede kalan, eşleşen metinden 5'li söz dizileri (özgün yazımla)."""
    ham = re.findall(r"\w+", " ".join(eslesen_ham))
    yeni_n = ngramlar(sozcukler(yeni), n)
    out = []
    for i in range(len(ham) - n + 1):
        if tuple(sozcukler(" ".join(ham[i:i + n]))) in yeni_n:
            out.append(" ".join(ham[i:i + n]))
        if len(out) >= en_cok:
            break
    return out


def geri_bildirim(neden, eslesen_ham, yeni, n=5):
    if neden == "eslesme_kaldi":
        ifs = cakisan_ifadeler(eslesen_ham, yeni, n=n)
        return ("Önceki denemede şu ifadeler aynen kaldı; bunları KULLANMA, eş anlamlılarla ya da farklı bir yapıyla ifade et: "
                + "; ".join(f"«{x}»" for x in ifs) + ".") if ifs else ""
    if neden in ("ayni", "cok_benzer"):
        return "Önceki deneme özgün cümleye çok benziyordu. Özneyi, sözcük sırasını ve bağlaçları belirgin biçimde değiştir."
    return ""


def ollama_yaz(model, zaman_asimi=300):
    """/api/chat + think=false: gemma4 sohbet biçimlendiricisiyle (RENDERER gemma4) tanımlı bir model gerekir (tez-yaz)."""
    def yaz(cumle, ek="", sicaklik=0.9):
        istem = PROMPT.format(cumle=cumle)
        if ek:
            istem = istem.replace("\n\nCümle:", " " + ek + "\n\nCümle:")
        veri = json.dumps({"model": model, "messages": [{"role": "user", "content": istem}], "stream": False, "think": False,
                           "options": {"temperature": sicaklik, "num_ctx": 2048}}).encode()
        istek = urllib.request.Request(OLLAMA_CHAT, data=veri, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as r:
            return json.loads(r.read())["message"]["content"]
    return yaz


def sozcuk_farki(eski, yeni):
    """Cümle içinde yalnız değişen sözcük aralıkları: [(eski_bas, eski_son, yeni_metin)] (eski cümleye göre göreli)."""
    import difflib
    et = [(m.start(), m.end()) for m in re.finditer(r"\S+", eski)]
    yt = [(m.start(), m.end()) for m in re.finditer(r"\S+", yeni)]
    sm = difflib.SequenceMatcher(None, [eski[a:b] for a, b in et], [yeni[a:b] for a, b in yt], autojunk=False)
    out = []
    for etiket, i1, i2, j1, j2 in sm.get_opcodes():
        if etiket == "equal":
            continue
        if i1 < i2:
            bas, son = et[i1][0], et[i2 - 1][1]
        else:  # saf ekleme: komşu sözcük sınırında
            bas = son = et[i1][0] if i1 < len(et) else len(eski)
        if j1 < j2:
            yeni_metin = yeni[yt[j1][0]:yt[j2 - 1][1]]
            if i1 == i2:
                yeni_metin = yeni_metin + " " if i1 < len(et) else " " + yeni_metin
        else:
            yeni_metin = ""
            if i1 < i2 and i2 < len(et):
                son = et[i2][0]  # silinen sözcükten sonraki boşluğu da al
        out.append((bas, son, yeni_metin))
    return out


class Kanca:
    """tez_onar.belge_onar(ek_oneri=Kanca(...)) olarak verilir; durum: {eşleşme_no: {"durum": ..., ...}}."""

    def __init__(self, hedefler, yaz_fn, azami=40, ngram=5):
        self.hedefler, self.yaz, self.azami, self.ngram = hedefler, yaz_fn, azami, ngram
        self.durum, self.uygulanan = {}, 0

    def __call__(self, metin):
        tok = [(m.start(), m.end(), katla(m.group()).strip()) for m in re.finditer(r"\w+", metin)]
        normler = [t[2] for t in tok]
        sonuc, kullanilan = [], []
        for h in self.hedefler:
            no = h["no"]
            if no in self.durum:
                continue
            w, k = h["kelimeler"], min(8, len(h["kelimeler"]))
            idx = next((i for i in range(len(normler) - k + 1) if normler[i:i + k] == w[:k]), None)
            if idx is None:
                continue
            bas, son = tok[idx][0], tok[min(idx + len(w), len(tok)) - 1][1]
            kayit = {"durum": "", "yuzde": h["yuzde"], "alan": h["alan"], "bolum": h.get("bolum")}
            self.durum[no] = kayit
            sin = cumle_siniri(metin, bas, son)
            if not sin:
                kayit["durum"] = "atlandi:cumle_tam_degil"
                continue
            if any(sin[0] < b and a < sin[1] for a, b in kullanilan):
                kayit["durum"] = "atlandi:ayni_cumle"
                continue
            cumle = metin[sin[0]:sin[1]]
            n = len(cumle.split())
            if n < 6 or n > 70:
                kayit["durum"] = "atlandi:cumle_uzunlugu"
                continue
            if self.uygulanan >= self.azami:
                kayit["durum"] = "atlandi:azami_sinir"
                continue
            ek, neden, yeni = "", "ilk", ""
            for deneme, sic in enumerate(SICAKLIK, 1):
                try:
                    yeni = temizle(self.yaz(cumle, ek, sic))
                except TypeError:
                    yeni = temizle(self.yaz(cumle))
                except Exception as e:  # noqa: BLE001
                    neden = f"model_hatasi({type(e).__name__})"
                    break
                neden = dogrula_cumle(cumle, yeni, h["kelimeler_ham"], self.ngram)
                kayit["deneme"] = deneme
                if not neden:
                    break
                ek = geri_bildirim(neden, h["kelimeler_ham"], yeni, self.ngram)
            if neden:
                kayit["durum"] = ("atlandi:" if neden.startswith("model_hatasi") else "reddedildi:") + neden
                continue
            kayit["durum"] = "uygulandi"
            self.uygulanan += 1
            kullanilan.append((sin[0], sin[1]))
            parcalar = sozcuk_farki(cumle, yeni)
            # güvenlik: parçalar uygulanınca tam olarak 'yeni' cümlesi çıkmalı
            kur, son_k = "", 0
            for b, e, y_ in sorted(parcalar):
                kur += cumle[son_k:b] + y_
                son_k = e
            kur += cumle[son_k:]
            if kur != yeni:
                parcalar = [(0, len(cumle), yeni)]
            sonuc.extend((sin[0] + b, sin[0] + e, y_, "YENIDEN_KUR") for b, e, y_ in parcalar)
        return sonuc


def hedefleri_sec(eslesmeler, esik=60):
    """konumla() sonrası: atıfsız ve eşik üstü benzerlikli, ana metinde konumlanmış eşleşmeler."""
    hedef = []
    for e in eslesmeler:
        if e.get("atifli") is False and e["yuzde"] >= esik and e.get("bolum") is not None:
            w = sozcukler(e["metin"])
            if len(w) >= 6:
                hedef.append({"no": e["no"], "yuzde": e["yuzde"], "alan": e["alan"], "bolum": e["bolum"],
                              "kelimeler": w, "kelimeler_ham": e["metin"].split()})
    return hedef


def rapor(durumlar):
    sayim = {}
    for d in durumlar.values():
        sayim[d["durum"]] = sayim.get(d["durum"], 0) + 1
    md = ["# Benzerlik onarımı (cümlesiz)", "", f"Hedef eşleşme: {len(durumlar)}", ""]
    md += [f"- {k}: {v}" for k, v in sorted(sayim.items())]
    md += ["", "## Eşleşme durumları", "", "| # | Benzerlik % | Bölüm | Alan adı | Durum |", "|---|---|---|---|---|"]
    for no in sorted(durumlar):
        d = durumlar[no]
        md.append(f"| {no} | {d['yuzde']} | {d['bolum']} | {d['alan']} | {d['durum']} |")
    atif = [(no, d) for no, d in sorted(durumlar.items()) if d["durum"] == "uygulandi"]
    md += ["", "## Atıf eklenecek (yeniden kurulan cümleler; kaynak künyesini yazar ekler)", "",
           "| # | Bölüm | Olası kaynak alanı |", "|---|---|---|"]
    md += [f"| {no} | {d['bolum']} | {d['alan']} |" for no, d in atif]
    return "\n".join(md) + "\n", {"sayim": sayim, "durumlar": {str(k): v for k, v in durumlar.items()}}


# ------------------------------------------------------------ sürüm denetimi (v12 -> v13)
def paragraf_ihlalleri(eski, yeni):
    ih = []
    if SAYI_RE.findall(eski) != SAYI_RE.findall(yeni):
        ih.append("sayi")
    if sorted(ATIF_RE.findall(eski)) != sorted(ATIF_RE.findall(yeni)):
        ih.append("atif")
    bas = {katla(c.split()[0]).strip() for c in re.split(r"(?<=[.!?])\s+", yeni) if c.split()}
    eski_b = {katla(x).strip() for x in BUYUK_RE.findall(eski)}
    yeni_b = {katla(x).strip() for x in BUYUK_RE.findall(yeni)}
    if (yeni_b - eski_b) - bas:
        ih.append("ozel_ad")
    if terim_ihlali(eski, yeni):
        ih.append("terim_birligi")
    if BIRINCI_SAHIS_RE.search(yeni) and not BIRINCI_SAHIS_RE.search(eski):
        ih.append("birinci_sahis")
    if TABLO_RE.search(yeni) and not TABLO_RE.search(eski):
        ih.append("tablo_cizelge")
    return ih


def surum_denetle(eski_par, yeni_par):
    """İki sürümün paragraf listelerini hizalar; değişen paragrafları ve ihlal türlerini (metinsiz) döner."""
    import difflib
    sm = difflib.SequenceMatcher(None, eski_par, yeni_par, autojunk=False)
    degisen, ihlaller, eklenen, silinen = [], {}, 0, 0
    kelime_eski = sum(len(p.split()) for p in eski_par)
    kelime_yeni = sum(len(p.split()) for p in yeni_par)
    for etiket, i1, i2, j1, j2 in sm.get_opcodes():
        if etiket == "equal":
            continue
        if etiket == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                ih = paragraf_ihlalleri(eski_par[i1 + k], yeni_par[j1 + k])
                degisen.append({"paragraf_no": j1 + k + 1, "eski_kelime": len(eski_par[i1 + k].split()),
                                "yeni_kelime": len(yeni_par[j1 + k].split()), "ihlal": ih})
                for x in ih:
                    ihlaller[x] = ihlaller.get(x, 0) + 1
        else:
            silinen += i2 - i1
            eklenen += j2 - j1
    return {"eski_paragraf": len(eski_par), "yeni_paragraf": len(yeni_par), "degisen_paragraf": len(degisen),
            "yapisal_fark": {"silinen_paragraf": silinen, "eklenen_paragraf": eklenen},
            "kelime": {"eski": kelime_eski, "yeni": kelime_yeni}, "ihlal_sayim": ihlaller, "degisenler": degisen}


def surum_rapor(s):
    md = ["# Sürüm denetimi (cümlesiz)", "",
          f"Paragraf: {s['eski_paragraf']} -> {s['yeni_paragraf']} · değişen: {s['degisen_paragraf']} · "
          f"silinen/eklenen (yapısal): {s['yapisal_fark']['silinen_paragraf']}/{s['yapisal_fark']['eklenen_paragraf']}",
          f"Kelime: {s['kelime']['eski']} -> {s['kelime']['yeni']}", "",
          f"İhlal sayımı: {s['ihlal_sayim'] or 'yok'}", "", "## Değişen paragraflar", "",
          "| Paragraf no | Eski kelime | Yeni kelime | İhlal |", "|---|---|---|---|"]
    md += [f"| {d['paragraf_no']} | {d['eski_kelime']} | {d['yeni_kelime']} | {', '.join(d['ihlal']) or '-'} |" for d in s["degisenler"]]
    return "\n".join(md) + "\n"


# ---------------------------------------------------- eklenen metin denetimi (v13 -> v14)
UZUN_CUMLE = 40
BASLANGIC_SUPHELI_RE = re.compile(r"^\s*(?:[a-zçğıöşü]\s*[)/.]|[A-Za-z]\s*/|[/\\|•·▪■□\-–—*#_~^]+)")


def cumleler(par):
    return [c for c in re.split(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ\"“‘(])", par.strip()) if c.strip()]


def baslangic_sinifi(par):
    s = par.lstrip()
    if not s:
        return "bos"
    if BASLANGIC_SUPHELI_RE.match(s):
        return "supheli"
    if s[0].isalpha() and s[0].islower():
        return "kucuk_harf"
    if s[0].isalnum() or s[0] in "\"“‘'(":
        return "normal"
    return "diger"


def metin_denetimi(eski, yeni, metinler):
    """eski/yeni: [{'metin','numpr','stil'}] listeleri; metinler: yeni-metin.json 'metinler'. Çıktıda tez cümlesi yoktur
    (yalnız bozuk görünen paragraf başlarının ilk 3 karakteri ve eklediğimiz metnin kendisi)."""
    import difflib
    sm = difflib.SequenceMatcher(None, [p["metin"] for p in eski], [p["metin"] for p in yeni], autojunk=False)
    niyet = [(m["id"], k, t) for m in metinler for k, t in enumerate(m["paragraflar"], 1)]
    eklenen, kullanilan = [], set()
    for etiket, i1, i2, j1, j2 in sm.get_opcodes():
        if etiket in ("insert", "replace"):
            for j in range(j1, j2):
                p = yeni[j]
                en, ad = 0.0, None
                for n, (mid, k, t) in enumerate(niyet):
                    if n in kullanilan:
                        continue
                    r = difflib.SequenceMatcher(None, p["metin"], t, autojunk=False).ratio()
                    if r > en:
                        en, ad = r, (n, mid, k)
                if ad and en >= 0.6:
                    kullanilan.add(ad[0])
                cs = [len(c.split()) for c in cumleler(p["metin"])]
                kayit = {"paragraf_no": j + 1, "metin_kodu": f"{ad[1]}.{ad[2]}" if ad and en >= 0.6 else None,
                         "benzerlik": round(en, 3), "kullanici_duzenledi": bool(ad and 0.6 <= en < 0.995),
                         "baslangic": baslangic_sinifi(p["metin"]), "numpr": p["numpr"], "stil": p["stil"],
                         "kelime": len(p["metin"].split()), "cumle_sayisi": len(cs), "en_uzun_cumle": max(cs) if cs else 0,
                         "uzun_cumle_sayisi": sum(1 for c in cs if c > UZUN_CUMLE)}
                if kayit["baslangic"] in ("supheli", "diger", "kucuk_harf", "bos"):
                    kayit["ilk3"] = p["metin"].lstrip()[:3]
                eklenen.append(kayit)
    bulunamayan = [f"{mid}.{k}" for n, (mid, k, t) in enumerate(niyet) if n not in kullanilan]
    belge_geneli = []
    for j, p in enumerate(yeni):
        s = baslangic_sinifi(p["metin"])
        if s == "supheli":
            belge_geneli.append({"paragraf_no": j + 1, "ilk3": p["metin"].lstrip()[:3]})
    return {"eski_paragraf": len(eski), "yeni_paragraf": len(yeni), "eklenen_paragraf": len(eklenen),
            "beklenen_metin_paragrafi": len(niyet), "bulunamayan_metin": bulunamayan, "eklenenler": eklenen,
            "belge_geneli_supheli_baslangic": belge_geneli}


def metin_denetim_rapor(s):
    md = ["# Eklenen metin denetimi", "",
          f"Paragraf: {s['eski_paragraf']} -> {s['yeni_paragraf']} · eklenen: {s['eklenen_paragraf']} (beklenen {s['beklenen_metin_paragrafi']})",
          f"Bulunamayan metin: {s['bulunamayan_metin'] or 'yok'}", "",
          "| Paragraf | Kod | Benz. | Düzenlendi | Başlangıç | numPr | Kelime | Cümle | En uzun | >40 kelimelik |", "|---|---|---|---|---|---|---|---|---|---|"]
    for e in s["eklenenler"]:
        md.append(f"| {e['paragraf_no']} | {e['metin_kodu']} | {e['benzerlik']} | {e['kullanici_duzenledi']} | {e['baslangic']}"
                  f"{' ' + repr(e['ilk3']) if 'ilk3' in e else ''} | {e['numpr']} | {e['kelime']} | {e['cumle_sayisi']} | {e['en_uzun_cumle']} | {e['uzun_cumle_sayisi']} |")
    md += ["", f"## Belge genelinde şüpheli paragraf başlangıcı: {len(s['belge_geneli_supheli_baslangic'])}", ""]
    md += [f"- paragraf {x['paragraf_no']}: ilk 3 karakter {x['ilk3']!r}" for x in s["belge_geneli_supheli_baslangic"][:60]]
    return "\n".join(md) + "\n"


# ------------------------------------------------ eklenen metni güncelleme (kısaltma/düzeltme) — izli
class MetinGuncelle:
    """tez_onar.belge_onar(ek_oneri=MetinGuncelle(eski, yeni)): metni tam eşleşen paragrafları sözcük bazlı izli değişiklikle günceller.
    eski/yeni: yeni-metin.json 'metinler' listeleri (aynı id ve sıra). Sayı, atıf, özel ad, terim ihlali olan güncelleme yapılmaz."""

    def __init__(self, eski, yeni):
        yd = {m["id"]: m["paragraflar"] for m in yeni}
        self.esler = {}
        for m in eski:
            for k, t in enumerate(m["paragraflar"], 1):
                y = yd.get(m["id"], [])
                if k <= len(y) and y[k - 1] != t:
                    self.esler[t.strip()] = (f"{m['id']}.{k}", y[k - 1])
        self.durum = {kod: {"durum": "bulunamadi"} for kod, _ in self.esler.values()}

    def __call__(self, metin):
        t = metin.strip()
        if t not in self.esler:
            return []
        kod, yeni = self.esler[t]
        ih = paragraf_ihlalleri(t, yeni)
        cs = [len(c.split()) for c in cumleler(yeni)]
        if ih:
            self.durum[kod] = {"durum": "reddedildi:" + ",".join(ih)}
            return []
        bas = metin.index(t)
        parcalar = sozcuk_farki(t, yeni)
        self.durum[kod] = {"durum": "uygulandi", "en_uzun_cumle_yeni": max(cs) if cs else 0,
                           "en_uzun_cumle_eski": max([len(c.split()) for c in cumleler(t)] or [0])}
        return [(bas + b, bas + e, y, "YENIDEN_KUR") for b, e, y in parcalar]
