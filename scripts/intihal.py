#!/usr/bin/env python3
"""intihal.py — tez ↔ korpus benzerlik motoru (yalnız standart kütüphane, Python ≥3.12).

Bu bir ÖN KONTROLDÜR: yalnız verdiğiniz korpusla karşılaştırır. Turnitin/iThenticate gibi geniş
veri tabanlarının yerini tutmaz; eksik korpus = eksik tespit.

Aşama 1 (birebir): n sözcüklük (varsayılan 8) dizilerin birebir örtüşmesi, en uzun ortak dizi, kapsama oranı.
Aşama 2 (anlamsal, isteğe bağlı): bge-m3 gömmeleriyle yeniden ifade / çeviri adayları (yerel Ollama).
Her işaretli paragraf için: atıf var mı? (atıfsız yüksek benzerlik asıl risktir).

Çıktılar:
  cumlesiz (Claude'a verilebilir): kaynak kimliği/başlığı, paragraf konumu, skorlar. Tez metni yok.
  tam (yalnız sunucuda): işaretli paragrafın başı ve eşleşen korpus parçası.
"""
import hashlib
import json
import math
import os
import re
import sys
import urllib.request
from array import array

sys.dont_write_bytecode = True

KELIME_RE = re.compile(r"[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ]+")
ATIF_RE = re.compile(r"\(\s*[^)]*(?:19|20)\d\d[^)]*\)|\[\d+(?:\s*[-,]\s*\d+)*\]")

VARSAYILAN = {
    "n": 8,                 # birebir dizi uzunluğu (sözcük)
    "kapsama_esigi": 0.15,  # paragrafın bu oranı bir kaynakla örtüşüyorsa işaretle
    "dizi_esigi": 12,       # ya da en uzun ortak dizi bu kadar sözcük ise
    "min_paragraf_sozcuk": 25,
    "anlamsal_esik": 0.85,  # bge-m3 kosinüs eşiği (yeniden ifade adayı)
    "pencere": 100, "adim": 50,   # korpus parçası (sözcük)
    "tez_pencere": 3,       # tez parçası (cümle)
}


def kucult_tr(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def kelimeler(s):
    return KELIME_RE.findall(kucult_tr(s))


def kar(g):
    return int.from_bytes(hashlib.blake2b(" ".join(g).encode("utf-8"), digest_size=8).digest(), "big")


# ------------------------------------------------------------------ korpus
def korpus_yukle(dizin):
    """{id: {"baslik","tur","yil","url","kelimeler":[...], "metin": str}}. kaynaklar.json yoksa tüm .txt dosyaları."""
    belgeler, manifest = {}, os.path.join(dizin, "kaynaklar.json")
    liste = []
    if os.path.isfile(manifest):
        with open(manifest, encoding="utf-8") as f:
            liste = json.load(f).get("belgeler", [])
    else:
        for ad in sorted(os.listdir(dizin)) if os.path.isdir(dizin) else []:
            if ad.endswith(".txt"):
                kimlik = ad[:-4]
                liste.append({"id": kimlik, "dosya": ad, "baslik": kimlik,
                              "tur": "kendi" if kimlik.startswith("kendi-") else "dis"})
    for b in liste:
        yol = os.path.join(dizin, os.path.basename(b["dosya"]))
        if os.path.isfile(yol):
            with open(yol, encoding="utf-8", errors="replace") as f:
                metin = f.read()
            belgeler[b["id"]] = {"baslik": b.get("baslik", b["id"]), "tur": b.get("tur", "dis"),
                                 "yil": b.get("yil"), "url": b.get("url"), "metin": metin,
                                 "kelimeler": kelimeler(metin)}
    return belgeler


# ------------------------------------------------------------------ tez
def tez_paragraflari(ana_metin, ayar):
    """[(satir_no, bolum_basligi, metin)] — başlıklar ve kısa satırlar hariç."""
    cikti, bolum = [], "Giriş / Genel Metin"
    for no, satir in enumerate(ana_metin.splitlines(), 1):
        st = satir.strip()
        if st.startswith("# "):
            bolum = st[2:].strip()
            continue
        if st.startswith("#") or not st:
            continue
        if len(kelimeler(st)) >= ayar["min_paragraf_sozcuk"]:
            cikti.append((no, bolum, st))
    return cikti


# ------------------------------------------------------------------ aşama 1
def dizin_olustur(belgeler, n):
    indeks = {}
    for kimlik, b in belgeler.items():
        w = b["kelimeler"]
        for i in range(len(w) - n + 1):
            indeks.setdefault(kar(w[i:i + n]), set()).add(kimlik)
    return indeks


def birebir(paragraflar, belgeler, indeks, ayar):
    n = ayar["n"]
    sonuc = []
    for no, bolum, metin in paragraflar:
        w = kelimeler(metin_atifsiz(metin))
        if len(w) < n:
            continue
        kapsanan, ilk = {}, {}   # belge -> kapsanan sözcük konumları; belge -> ilk eşleşen dizinin tez konumu
        for i in range(len(w) - n + 1):
            for kimlik in indeks.get(kar(w[i:i + n]), ()):
                kapsanan.setdefault(kimlik, set()).update(range(i, i + n))
                ilk.setdefault(kimlik, i)
        en_iyi = None
        for kimlik, konumlar in kapsanan.items():
            oran = len(konumlar) / len(w)
            dizi, mevcut, onceki = 0, 0, -2
            for p in sorted(konumlar):
                mevcut = mevcut + 1 if p == onceki + 1 else 1
                dizi, onceki = max(dizi, mevcut), p
            if en_iyi is None or oran > en_iyi["kapsama"]:
                en_iyi = {"kaynak": kimlik, "kapsama": round(oran, 3), "en_uzun_dizi": dizi, "ortak_sozcuk": len(konumlar),
                          "konum": _konum_bul(belgeler[kimlik]["kelimeler"], w[ilk[kimlik]:ilk[kimlik] + n])}
        if en_iyi and (en_iyi["kapsama"] >= ayar["kapsama_esigi"] or en_iyi["en_uzun_dizi"] >= ayar["dizi_esigi"]):
            en_iyi.update({"satir": no, "bolum": bolum, "tur": "birebir", "atifli": bool(ATIF_RE.search(metin)),
                           "sozcuk": len(w)})
            sonuc.append(en_iyi)
    return sonuc


def _konum_bul(belge_kelimeleri, gram):
    n = len(gram)
    for i in range(len(belge_kelimeleri) - n + 1):
        if belge_kelimeleri[i:i + n] == gram:
            return i
    return 0


def metin_atifsiz(metin):
    return ATIF_RE.sub(" ", metin)


def bolum_ozeti(paragraflar, eslesmeler):
    toplam, isaretli = {}, {}
    for no, bolum, metin in paragraflar:
        toplam[bolum] = toplam.get(bolum, 0) + len(kelimeler(metin))
    for e in eslesmeler:
        kapsanan = e.get("ortak_sozcuk", 0)
        isaretli[e["bolum"]] = isaretli.get(e["bolum"], 0) + kapsanan
    return [{"baslik": b, "sozcuk": toplam[b], "birebir_ortak_sozcuk": isaretli.get(b, 0),
             "birebir_yuzde": round(100 * isaretli.get(b, 0) / toplam[b], 2) if toplam[b] else 0.0}
            for b in toplam]


# ------------------------------------------------------------------ aşama 2
def ollama_gomme(metinler, model="bge-m3", url="http://127.0.0.1:11434/api/embed", parti=16, zaman_asimi=120):
    vektorler = []
    for i in range(0, len(metinler), parti):
        istek = json.dumps({"model": model, "input": metinler[i:i + parti], "keep_alive": "10m"}).encode()
        with urllib.request.urlopen(urllib.request.Request(url, istek, {"Content-Type": "application/json"}),
                                    timeout=zaman_asimi) as r:
            vektorler.extend(json.loads(r.read())["embeddings"])
    return [normalle(v) for v in vektorler]


def normalle(v):
    b = math.sqrt(math.sumprod(v, v)) or 1.0
    return array("f", (x / b for x in v))


def parcala_korpus(belgeler, ayar):
    cikti = []
    for kimlik, b in belgeler.items():
        w = b["kelimeler"]
        for i in range(0, max(1, len(w) - ayar["pencere"] + 1), ayar["adim"]):
            parca = w[i:i + ayar["pencere"]]
            if len(parca) >= 20:
                cikti.append((kimlik, i, " ".join(parca)))
    return cikti


def parcala_tez(paragraflar, ayar):
    cikti = []
    for no, bolum, metin in paragraflar:
        cumleler = [c.strip() for c in re.split(r"(?<=[.!?])\s+", metin) if c.strip()]
        for i in range(0, max(1, len(cumleler) - ayar["tez_pencere"] + 1), 2):
            parca = " ".join(cumleler[i:i + ayar["tez_pencere"]])
            if len(kelimeler(parca)) >= 15:
                cikti.append((no, bolum, metin_atifsiz(parca), bool(ATIF_RE.search(parca)) or bool(ATIF_RE.search(metin))))
    return cikti


def anlamsal(paragraflar, belgeler, ayar, gomme=ollama_gomme, dislanan_satirlar=()):
    kparca, tparca = parcala_korpus(belgeler, ayar), parcala_tez(paragraflar, ayar)
    if not kparca or not tparca:
        return [], {"esik_alti_en_yuksek": None}
    kv = gomme([p[2] for p in kparca])
    tv = gomme([p[2] for p in tparca])
    sonuc, en_iyi_paragraf = {}, {}
    for (no, bolum, _, atifli), v in zip(tparca, tv):
        enk, enskor = None, -1.0
        for (kimlik, konum, _), kvv in zip(kparca, kv):
            s = math.sumprod(v, kvv)
            if s > enskor:
                enk, enskor = (kimlik, konum), s
        if enskor >= ayar["anlamsal_esik"] and no not in dislanan_satirlar:
            onceki = sonuc.get(no)
            if onceki is None or enskor > onceki["skor"]:
                sonuc[no] = {"satir": no, "bolum": bolum, "kaynak": enk[0], "tur": "anlamsal",
                             "skor": round(enskor, 3), "atifli": atifli, "konum": enk[1]}
        en_iyi_paragraf[no] = max(en_iyi_paragraf.get(no, -1.0), enskor)
    dagilim = {}
    for s in en_iyi_paragraf.values():
        kova = f"{math.floor(s * 20) / 20:.2f}"
        dagilim[kova] = dagilim.get(kova, 0) + 1
    return list(sonuc.values()), {"skor_dagilimi": dict(sorted(dagilim.items()))}


# ------------------------------------------------------------------ rapor
def calistir(ana_metin, belgeler, ayar=None, anlamsal_ac=False, gomme=ollama_gomme):
    ayar = dict(VARSAYILAN, **(ayar or {}))
    paragraflar = tez_paragraflari(ana_metin, ayar)
    indeks = dizin_olustur(belgeler, ayar["n"])
    eslesmeler = birebir(paragraflar, belgeler, indeks, ayar)
    ek = {}
    if anlamsal_ac:
        a, ek = anlamsal(paragraflar, belgeler, ayar, gomme=gomme, dislanan_satirlar={e["satir"] for e in eslesmeler})
        eslesmeler += a
    for e in eslesmeler:
        b = belgeler[e["kaynak"]]
        e["kaynak_baslik"], e["kaynak_tur"] = b["baslik"], b["tur"]
    eslesmeler.sort(key=lambda e: (e["satir"], e["tur"]))
    toplam_sozcuk = sum(len(kelimeler(m)) for _, _, m in paragraflar)
    ortak = sum(e.get("ortak_sozcuk", 0) for e in eslesmeler if e["tur"] == "birebir")
    kaynak_ozeti = {}
    for e in eslesmeler:
        k = kaynak_ozeti.setdefault(e["kaynak"], {"id": e["kaynak"], "baslik": e["kaynak_baslik"], "tur": e["kaynak_tur"],
                                                  "isaretli_paragraf": 0, "birebir_ortak_sozcuk": 0})
        k["isaretli_paragraf"] += 1
        k["birebir_ortak_sozcuk"] += e.get("ortak_sozcuk", 0)
    ozet = {
        "taranan_paragraf": len(paragraflar), "taranan_sozcuk": toplam_sozcuk,
        "korpus_belge": len(belgeler), "korpus_sozcuk": sum(len(b["kelimeler"]) for b in belgeler.values()),
        "birebir_paragraf": sum(1 for e in eslesmeler if e["tur"] == "birebir"),
        "anlamsal_paragraf": sum(1 for e in eslesmeler if e["tur"] == "anlamsal"),
        "birebir_benzerlik_yuzde": round(100 * ortak / toplam_sozcuk, 2) if toplam_sozcuk else 0.0,
        "atifsiz_isaretli": sum(1 for e in eslesmeler if not e["atifli"]),
        "kendi_eserle_isaretli": sum(1 for e in eslesmeler if e["kaynak_tur"] == "kendi"),
    }
    return {"sema": "intihal-cumlesiz-v1", "cumle_icerir": False, "ayar": ayar, "ozet": ozet,
            "bolumler": bolum_ozeti(paragraflar, [e for e in eslesmeler if e["tur"] == "birebir"]),
            "kaynaklar": sorted(kaynak_ozeti.values(), key=lambda k: -k["birebir_ortak_sozcuk"]),
            "eslesmeler": eslesmeler, "anlamsal_ek": ek}


def markdown(s):
    o, ay = s["ozet"], s["ayar"]
    satir = [
        "# İntihal Ön Kontrol Raporu (cümlesiz)", "",
        f"> Şema `{s['sema']}`: tez cümlesi içermez. Yalnız verilen korpusla karşılaştırır "
        f"({o['korpus_belge']} belge, {o['korpus_sozcuk']} sözcük); Turnitin/iThenticate'in yerini tutmaz.", "",
        "## 1. Özet",
        f"- Taranan: {o['taranan_paragraf']} paragraf · {o['taranan_sozcuk']} sözcük",
        f"- Birebir benzerlik (≥{ay['n']} sözcüklük diziler): **%{o['birebir_benzerlik_yuzde']}**",
        f"- İşaretli paragraf: {o['birebir_paragraf']} birebir · {o['anlamsal_paragraf']} anlamsal",
        f"- Atıfsız işaretli paragraf: **{o['atifsiz_isaretli']}** (asıl risk)",
        f"- Kendi eserleriyle örtüşen: {o['kendi_eserle_isaretli']}", "",
        "## 2. Kaynaklara göre"]
    if not s["kaynaklar"]:
        satir.append("- Hiçbir kaynakla eşik üstü örtüşme bulunmadı.")
    for k in s["kaynaklar"][:30]:
        satir.append(f"- `{k['id']}` ({k['tur']}) {k['baslik']}: {k['isaretli_paragraf']} paragraf · {k['birebir_ortak_sozcuk']} ortak sözcük")
    satir += ["", "## 3. Bölümlere göre", "| Bölüm | Sözcük | Birebir ortak | % |", "|---|---:|---:|---:|"]
    for b in s["bolumler"]:
        satir.append(f"| {b['baslik']} | {b['sozcuk']} | {b['birebir_ortak_sozcuk']} | {b['birebir_yuzde']} |")
    satir += ["", "## 4. İşaretli paragraflar (konum + kaynak; metin yok)",
              "| Satır | Bölüm | Tür | Kaynak | Skor | Atıf |", "|---:|---|---|---|---|---|"]
    for e in s["eslesmeler"]:
        skor = f"kapsama {e['kapsama']}, dizi {e['en_uzun_dizi']}" if e["tur"] == "birebir" else f"kosinüs {e['skor']}"
        satir.append(f"| {e['satir']} | {e['bolum']} | {e['tur']} | `{e['kaynak']}` | {skor} | {'var' if e['atifli'] else '**YOK**'} |")
    if s["anlamsal_ek"].get("skor_dagilimi"):
        satir += ["", "## 5. Anlamsal skor dağılımı (paragraf başına en yüksek kosinüs; eşik ayarı için)",
                  ", ".join(f"{k}: {v}" for k, v in s["anlamsal_ek"]["skor_dagilimi"].items())]
    return "\n".join(satir) + "\n"


def tam_rapor(s, paragraflar, belgeler):
    """Yalnız sunucuda kalır: işaretli paragrafın başı + eşleşen korpus parçası."""
    harita = {no: m for no, _, m in paragraflar}
    satir = ["# İntihal TAM rapor (tez metni içerir; sunucudan çıkarmayın)", ""]
    for e in s["eslesmeler"]:
        satir.append(f"## Satır {e['satir']} · {e['tur']} · `{e['kaynak']}` · atıf {'var' if e['atifli'] else 'YOK'}")
        satir.append(f"Tez: {harita.get(e['satir'], '')[:300]}")
        b = belgeler[e["kaynak"]]
        konum = e.get("konum", 0)
        satir.append(f"Korpus: {' '.join(b['kelimeler'][konum:konum + 60])}")
        satir.append("")
    return "\n".join(satir)


if __name__ == "__main__":
    print(__doc__)
