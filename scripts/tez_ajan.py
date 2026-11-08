#!/usr/bin/env python3
"""tez_ajan.py GOREV — systemd birimi (tez-ajan@GOREV.service) tarafından çağrılır.

Görevler:
  denetle     rapor-tam.md (yalnız sunucuda kalır) + rapor-cumlesiz.md (Claude'a verilebilir)
  onar-kural  kural tabanlı izli değişiklik (varsayılan KURU; ayar.json "uygula": true ile yazar)
  onar-model  henüz yok
  icerik-oner brif.json'daki konuların tezde geçip geçmediği (model yok; cikti/icerik-cumlesiz.md, .json)
  benzerlik   Quetext raporundaki atıfsız yüksek eşleşmeleri yerel modelle yeniden kurar (izli değişiklik; kuru varsayılan)
  yerlestir   onaylı yeni metinleri en ilgili paragrafın ardına izli ekleme olarak koyar (kuru varsayılan)
  intihal     tez ↔ korpus benzerlik ön kontrolü (cikti/intihal-cumlesiz.md, -tam.md)
  denetci     ajan çıktısını özgün kopyayla bağımsız karşılaştırır (cikti/denetci.json)

Ayar: <KOK>/calisma/ayar.json  örn. {"girdi": "Tez.docx", "uygula": false, "kenar": true}
Kök: ortam değişkeni TEZ_AJAN_KOK (varsayılan ./tez-ajan). Yalnız standart kütüphane.
Çıkış kodları: 0 tamam · 2 kullanım/girdi · 3 sızıntı bekçisi · 4 doğrulama hatası · 5 orijinal koruması · 6 henüz yok
"""
import datetime
import hashlib
import json
import os
import re
import sys
import zipfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for ek in (os.environ.get("TEZ_AJAN_DURULAC"),):
    if ek:
        sys.path.insert(0, ek)

import atif_tani as at  # noqa: E402
import benzerlik as bz  # noqa: E402
import denetci as dn  # noqa: E402
import icerik as ic  # noqa: E402
import intihal as ih  # noqa: E402
import rapor_ozet as ro  # noqa: E402
import yerlestir as yz  # noqa: E402
import tez_analiz as ta  # noqa: E402
import tez_onar as to  # noqa: E402

KOK = os.environ.get("TEZ_AJAN_KOK", "./tez-ajan")
VARSAYILAN_AYAR = {"girdi": "Tez.docx", "uygula": False, "kenar": True}


def yol(*parca):
    return os.path.join(KOK, *parca)


def yaz_gizli(hedef, icerik):
    fd = os.open(hedef, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(icerik)


def gunluk_yaz(olay):
    olay = dict(olay, zaman=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
    fd = os.open(yol("gunluk", "ajan.jsonl"), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(json.dumps(olay, ensure_ascii=False) + "\n")


def ayar_oku():
    ayar = dict(VARSAYILAN_AYAR)
    yolu = yol("calisma", "ayar.json")
    if os.path.isfile(yolu):
        with open(yolu, encoding="utf-8") as f:
            ayar.update(json.load(f))
    return ayar


def girdi_bul(ayar):
    """Yalnız gelen/ içindeki dosya adı; yol gezintisi ve adında “orijinal” geçen dosya reddedilir."""
    ad = os.path.basename(str(ayar["girdi"]))
    if ad != ayar["girdi"]:
        return None, "girdi yalnız dosya adı olabilir"
    if "orijinal" in ad.lower():
        return None, "adında “orijinal” geçen dosyayla çalışılmaz; kopyasıyla çalışın"
    p = yol("gelen", ad)
    if not os.path.isfile(p):
        return None, f"girdi bulunamadı: gelen/{ad}"
    return p, ""


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def gorev_denetle(girdi):
    y = ta.docx_ayristir(girdi)
    analiz = ta.metin_analiz_et(
        y["ana_metin"], kaynakca_satirlari=y["kaynakca_satirlari"], yorumlar=y["yorumlar"],
        on_sayfalar=y.get("on_sayfalar"), kaynakca_ham_satirlar=y.get("kaynakca_ham_satirlar"),
        ozgecmis_satirlari=y.get("ozgecmis_satirlari"), kenar_bosluklari=y.get("kenar_bosluklari"))
    tam = ta.rapor_uret(analiz)
    cumlesiz = ta.rapor_uret(ta.cumlesizlestir(analiz))
    sizan = ta.sizinti_denetle(cumlesiz, y["ana_metin"])
    if sizan:
        yerler = ta.sizinti_bolumleri(cumlesiz, y["ana_metin"])
        gunluk_yaz({"gorev": "denetle", "durum": "sizinti_bekcisi", "parca": sizan, "bolumler": yerler})
        print(f"SIZINTI BEKÇİSİ: {sizan} parça; cümlesiz rapor yazılmadı; bölümler: {json.dumps(yerler, ensure_ascii=False)}", file=sys.stderr)
        return 3
    ak = analiz["atif_kaynakca_denetimi"]
    tani = at.tani(ak.get("kaynakcada_eksik_atiflar", []), ak.get("metinde_eksik_kaynaklar", []),
                   y["kaynakca_satirlari"], ak.get("metin_atiflari", []))
    yaz_gizli(yol("cikti", "atif-tani.json"), json.dumps(tani, ensure_ascii=False, indent=1))
    yaz_gizli(yol("cikti", "rapor-tam.md"), tam)
    yaz_gizli(yol("cikti", "rapor-cumlesiz.md"), cumlesiz)
    gunluk_yaz({"gorev": "denetle", "durum": "tamam"})
    print("denetle: rapor-tam.md (sunucuda kalır) ve rapor-cumlesiz.md yazıldı")
    return 0


def gorev_onar_kural(girdi, ayar):
    ad = os.path.splitext(os.path.basename(girdi))[0]
    cikti = yol("cikti", ad + ".ajan.docx") if ayar.get("uygula") else None
    s = to.onar_dosya(girdi, cikti, kenar=bool(ayar.get("kenar")), duzeltmeler=ayar.get("duzeltmeler"))
    ozet = {k: v for k, v in s.items() if k != "gunluk"}
    ozet["kip"] = "uygula" if cikti else "kuru"
    for g in s["gunluk"]:
        gunluk_yaz(dict(g, gorev="onar-kural"))
    gunluk_yaz({"gorev": "onar-kural", "durum": "hata" if s["hatalar"] else "tamam", "kip": ozet["kip"]})
    yaz_gizli(yol("cikti", "onar-ozet.json"), json.dumps(ozet, ensure_ascii=False, indent=2))
    print(json.dumps(ozet, ensure_ascii=False, indent=2))
    if s["hatalar"]:
        if cikti and os.path.exists(cikti):
            os.unlink(cikti)
        return 4
    return 0


def gorev_denetci(girdi, ayar):
    """Ajanın ürettiği docx'i özgün kopyayla BAĞIMSIZ karşılaştırır (denetci.py, tez_onar.py'yi kullanmaz)."""
    ad = os.path.splitext(os.path.basename(girdi))[0]
    ajan = yol("cikti", ad + ".ajan.docx")
    if not os.path.isfile(ajan):
        print(f"denetçi: ajan çıktısı yok: cikti/{ad}.ajan.docx (önce onar-kural uygula)", file=sys.stderr)
        return 2
    s = dn.denetle(girdi, ajan, ayar.get("duzeltmeler"))
    yaz_gizli(yol("cikti", "denetci.json"), json.dumps(s, ensure_ascii=False, indent=1))
    gunluk_yaz({"gorev": "denetci", "durum": "sorun" if s["sorunlar"] else "tamam", "sayilar": s["sayilar"]})
    print(json.dumps({"sayilar": s["sayilar"], "sorunlar": s["sorunlar"],
                      "yabanci_degisiklik_sayisi": s["yabanci_degisiklik_sayisi"]}, ensure_ascii=False, indent=1))
    return 4 if s["sorunlar"] else 0


def gorev_intihal(girdi, ayar):
    """Tez ↔ korpus benzerlik ön kontrolü. Korpus: <KOK>/korpus (kaynaklar.json ya da *.txt)."""
    y = ta.docx_ayristir(girdi)
    korpus = ih.korpus_yukle(yol("korpus"))
    ia = ayar.get("intihal", {})
    s = ih.calistir(y["ana_metin"], korpus, ia.get("esikler"), anlamsal_ac=bool(ia.get("anlamsal")))
    md = ih.markdown(s)
    js = json.dumps(s, ensure_ascii=False, indent=1)
    sizan = ta.sizinti_denetle(md + "\n" + js, y["ana_metin"])
    if sizan:
        gunluk_yaz({"gorev": "intihal", "durum": "sizinti_bekcisi", "parca": sizan})
        print(f"SIZINTI BEKÇİSİ: {sizan} parça; cümlesiz intihal raporu yazılmadı", file=sys.stderr)
        return 3
    yaz_gizli(yol("cikti", "intihal-cumlesiz.md"), md)
    yaz_gizli(yol("cikti", "intihal-cumlesiz.json"), js)
    yaz_gizli(yol("cikti", "intihal-tam.md"),
              ih.tam_rapor(s, ih.tez_paragraflari(y["ana_metin"], s["ayar"]), korpus))
    gunluk_yaz({"gorev": "intihal", "durum": "tamam", "ozet": s["ozet"]})
    print(json.dumps(s["ozet"], ensure_ascii=False, indent=1))
    return 0


def gorev_icerik_oner(girdi):
    """calisma/brif.json konularının tezde kapsanıp kapsanmadığı. Model yok; rapor cümle içermez."""
    bp = yol("calisma", "brif.json")
    if not os.path.isfile(bp):
        print("brif yok: calisma/brif.json", file=sys.stderr)
        return 2
    with open(bp, encoding="utf-8") as f:
        brif = json.load(f)
    hatalar = ic.brif_dogrula(brif)
    if hatalar:
        print("brif geçersiz: " + "; ".join(hatalar), file=sys.stderr)
        return 2
    y = ta.docx_ayristir(girdi)
    s = ic.tara(y["ana_metin"], brif, ta.bolumlere_ayir)
    md = ic.markdown(s)
    js = json.dumps(s, ensure_ascii=False, indent=1)
    sizan = ta.sizinti_denetle(md + "\n" + js, y["ana_metin"])
    if sizan:
        gunluk_yaz({"gorev": "icerik-oner", "durum": "sizinti_bekcisi", "parca": sizan})
        print(f"SIZINTI BEKÇİSİ: {sizan} parça; içerik raporu yazılmadı", file=sys.stderr)
        return 3
    yaz_gizli(yol("cikti", "icerik-cumlesiz.md"), md)
    yaz_gizli(yol("cikti", "icerik-cumlesiz.json"), js)
    gunluk_yaz({"gorev": "icerik-oner", "durum": "tamam", "ozet": s["ozet"]})
    print(json.dumps(s["ozet"], ensure_ascii=False))
    return 0


def gorev_benzerlik(girdi, ayar):
    """calisma/ayar.json: "benzerlik": {"rapor": "rapor-web.pdf", "uygula": false, "esik": 60, "model": "durulac-tez", "azami": 40}."""
    b = ayar.get("benzerlik", {})
    rp = yol("gelen", os.path.basename(str(b.get("rapor", "rapor-web.pdf"))))
    if not os.path.isfile(rp):
        print(f"rapor yok: gelen/{os.path.basename(rp)}", file=sys.stderr)
        return 2
    y = ta.docx_ayristir(girdi)
    es = ro.konumla(ro.eslesmeleri_ayir(ro.pdf_metni(rp)), y["ana_metin"])
    hedef = bz.hedefleri_sec(es, int(b.get("esik", 60)))
    kanca = bz.Kanca(hedef, bz.ollama_yaz(b.get("model", "durulac-tez")), int(b.get("azami", 40)), int(b.get("ngram", 5)))
    ad = os.path.splitext(os.path.basename(girdi))[0]
    cikti = yol("cikti", ad + ".benzerlik.docx") if b.get("uygula") else None
    s = to.onar_dosya(girdi, cikti, kenar=False, ek_oneri=kanca)
    for h in hedef:
        kanca.durum.setdefault(h["no"], {"durum": "atlandi:bulunamadi", "yuzde": h["yuzde"], "alan": h["alan"], "bolum": h["bolum"]})
    md, js = bz.rapor(kanca.durum)
    js = json.dumps(dict(js, kip="uygula" if cikti else "kuru", hatalar=s["hatalar"]), ensure_ascii=False, indent=1)
    sizan = ta.sizinti_denetle(md + "\n" + js, y["ana_metin"])
    if sizan:
        gunluk_yaz({"gorev": "benzerlik", "durum": "sizinti_bekcisi", "parca": sizan})
        if cikti and os.path.exists(cikti):
            os.unlink(cikti)
        print(f"SIZINTI BEKÇİSİ: {sizan} parça; rapor yazılmadı", file=sys.stderr)
        return 3
    yaz_gizli(yol("cikti", "benzerlik-cumlesiz.md"), md)
    yaz_gizli(yol("cikti", "benzerlik-cumlesiz.json"), js)
    for g in s["gunluk"]:
        gunluk_yaz(dict(g, gorev="benzerlik"))
    gunluk_yaz({"gorev": "benzerlik", "durum": "hata" if s["hatalar"] else "tamam", "kip": "uygula" if cikti else "kuru"})
    print(json.dumps(json.loads(js)["sayim"], ensure_ascii=False))
    if s["hatalar"]:
        if cikti and os.path.exists(cikti):
            os.unlink(cikti)
        return 4
    return 0


def gorev_benzerlik_denetle(girdi, ayar):
    """calisma/ayar.json: "benzerlik_denetim": {"eski": "Tez.docx", "yeni": "Tez.docx"}; yalnız sayı ve paragraf no yazar."""
    d = ayar.get("benzerlik_denetim", {})
    yollar = []
    for k, varsayilan in (("eski", os.path.basename(girdi)), ("yeni", "Tez.docx")):
        ad = os.path.basename(str(d.get(k, varsayilan)))
        if "orijinal" in ad.lower():
            print("adında “orijinal” geçen dosyayla çalışılmaz", file=sys.stderr)
            return 5
        p = yol("gelen", ad)
        if not os.path.isfile(p):
            print(f"yok: gelen/{ad}", file=sys.stderr)
            return 2
        yollar.append(p)
    def paragraflar_oku(p):
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        return [t for t in to._metin(to.hepsini_kabul(xml)) if t.strip()]
    s = bz.surum_denetle(paragraflar_oku(yollar[0]), paragraflar_oku(yollar[1]))
    md, js = bz.surum_rapor(s), json.dumps(s, ensure_ascii=False, indent=1)
    y = ta.docx_ayristir(yollar[1])
    sizan = ta.sizinti_denetle(md + "\n" + js, y["ana_metin"])
    if sizan:
        gunluk_yaz({"gorev": "benzerlik-denetle", "durum": "sizinti_bekcisi", "parca": sizan})
        print(f"SIZINTI BEKÇİSİ: {sizan} parça; rapor yazılmadı", file=sys.stderr)
        return 3
    yaz_gizli(yol("cikti", "benzerlik-denetim-cumlesiz.md"), md)
    yaz_gizli(yol("cikti", "benzerlik-denetim-cumlesiz.json"), js)
    gunluk_yaz({"gorev": "benzerlik-denetle", "durum": "tamam", "degisen": s["degisen_paragraf"], "ihlal": s["ihlal_sayim"]})
    print(json.dumps({"degisen_paragraf": s["degisen_paragraf"], "yapisal_fark": s["yapisal_fark"], "ihlal": s["ihlal_sayim"]}, ensure_ascii=False))
    return 0


def gorev_yerlestir(girdi, ayar):
    """calisma/ayar.json: "yerlestir": {"girdi": "Tez.docx", "metin": "yeni-metin.json", "uygula": false, "esik": 0.5, "gomme": "bge-m3"}."""
    b = ayar.get("yerlestir", {})
    ad_g = os.path.basename(str(b.get("girdi", os.path.basename(girdi))))
    if "orijinal" in ad_g.lower():
        print("adında “orijinal” geçen dosyayla çalışılmaz", file=sys.stderr)
        return 5
    gp, mp = yol("gelen", ad_g), yol("calisma", os.path.basename(str(b.get("metin", "yeni-metin.json"))))
    for p_ in (gp, mp):
        if not os.path.isfile(p_):
            print(f"yok: {os.path.relpath(p_, KOK)}", file=sys.stderr)
            return 2
    with zipfile.ZipFile(gp) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    with open(mp, encoding="utf-8") as f:
        metinler = json.load(f)["metinler"]
    adaylar = yz.aday_paragraflar(xml)
    sonuc = yz.yer_sec(adaylar, metinler, yz.ollama_gomme(b.get("gomme", "bge-m3")), float(b.get("esik", 0.5)))
    hatalar, cikti = [], None
    if b.get("uygula"):
        tarih = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        yeni = yz.ekle(xml, sonuc, metinler, tarih)
        hatalar = to.dogrula(xml, yeni)
        if not hatalar:
            cikti = yol("cikti", os.path.splitext(ad_g)[0] + ".yeni-metin.docx")
            with zipfile.ZipFile(gp) as zi, zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as zo:
                for bilgi in zi.infolist():
                    veri = zi.read(bilgi.filename)
                    if bilgi.filename == "word/document.xml":
                        veri = yeni.encode("utf-8")
                    zo.writestr(bilgi, veri)
    for s in sonuc:
        s.pop("aralik", None)
    md = yz.rapor(sonuc, len(adaylar))
    js = json.dumps({"kip": "uygula" if b.get("uygula") else "kuru", "aday": len(adaylar), "sonuc": sonuc, "hatalar": hatalar,
                     "cikti": os.path.basename(cikti) if cikti else None}, ensure_ascii=False, indent=1)
    yaz_gizli(yol("cikti", "yerlestir-cumlesiz.md"), md)
    yaz_gizli(yol("cikti", "yerlestir-cumlesiz.json"), js)
    gunluk_yaz({"gorev": "yerlestir", "durum": "hata" if hatalar else "tamam", "kip": "uygula" if b.get("uygula") else "kuru",
                "yerlestirilen": sum(1 for s in sonuc if s["durum"] == "yerlestirildi")})
    print(md)
    return 4 if hatalar else 0


def gorev_metin_denetle(girdi, ayar):
    """calisma/ayar.json: "metin_denetim": {"eski": "Tez.docx", "yeni": "Tez.docx", "metin": "yeni-metin.json"}; cümlesiz rapor."""
    d = ayar.get("metin_denetim", {})
    yol_ = []
    for k, v in (("eski", "Tez.docx"), ("yeni", "Tez.docx")):
        ad = os.path.basename(str(d.get(k, v)))
        if "orijinal" in ad.lower():
            print("adında “orijinal” geçen dosyayla çalışılmaz", file=sys.stderr)
            return 5
        p = yol("gelen", ad)
        if not os.path.isfile(p):
            print(f"yok: gelen/{ad}", file=sys.stderr)
            return 2
        yol_.append(p)
    mp = yol("calisma", os.path.basename(str(d.get("metin", "yeni-metin.json"))))
    with open(mp, encoding="utf-8") as f:
        metinler = json.load(f)["metinler"]

    def oku(p):
        with zipfile.ZipFile(p) as z:
            xml = to.hepsini_kabul(z.read("word/document.xml").decode("utf-8"))
        cikti = []
        for b, s in to.paragraflar(xml):
            par = xml[b:s]
            st = re.search(r'<w:pStyle w:val="([^"]+)"', par)
            cikti.append({"metin": yz.par_metni(par), "numpr": "<w:numPr" in par, "stil": st.group(1) if st else ""})
        return cikti
    s = bz.metin_denetimi(oku(yol_[0]), oku(yol_[1]), metinler)
    md, js = bz.metin_denetim_rapor(s), json.dumps(s, ensure_ascii=False, indent=1)
    yaz_gizli(yol("cikti", "metin-denetim-cumlesiz.md"), md)
    yaz_gizli(yol("cikti", "metin-denetim-cumlesiz.json"), js)
    gunluk_yaz({"gorev": "metin-denetle", "durum": "tamam", "eklenen": s["eklenen_paragraf"], "supheli": len(s["belge_geneli_supheli_baslangic"])})
    print(md)
    return 0


def gorev_metin_guncelle(girdi, ayar):
    """calisma/ayar.json: "metin_guncelle": {"girdi": "Tez.docx", "eski": "yeni-metin.json", "yeni": "yeni-metin-v2.json", "uygula": false}."""
    b = ayar.get("metin_guncelle", {})
    ad_g = os.path.basename(str(b.get("girdi", "Tez.docx")))
    if "orijinal" in ad_g.lower():
        print("adında “orijinal” geçen dosyayla çalışılmaz", file=sys.stderr)
        return 5
    gp = yol("gelen", ad_g)
    mp = [yol("calisma", os.path.basename(str(b.get(k, v)))) for k, v in (("eski", "yeni-metin.json"), ("yeni", "yeni-metin-v2.json"))]
    for p_ in [gp] + mp:
        if not os.path.isfile(p_):
            print(f"yok: {os.path.relpath(p_, KOK)}", file=sys.stderr)
            return 2
    with open(mp[0], encoding="utf-8") as f:
        eski = json.load(f)["metinler"]
    with open(mp[1], encoding="utf-8") as f:
        yeni = json.load(f)["metinler"]
    g = bz.MetinGuncelle(eski, yeni)
    cikti = yol("cikti", os.path.splitext(ad_g)[0] + ".guncel.docx") if b.get("uygula") else None
    s = to.onar_dosya(gp, cikti, kenar=False, ek_oneri=g)
    md = ["# Metin güncelleme (cümlesiz)", "", f"Hatalar: {s['hatalar'] or 'yok'}", "", "| Kod | Durum | En uzun cümle (eski -> yeni) |", "|---|---|---|"]
    for kod in sorted(g.durum):
        d = g.durum[kod]
        md.append(f"| {kod} | {d['durum']} | {d.get('en_uzun_cumle_eski', '-')} -> {d.get('en_uzun_cumle_yeni', '-')} |")
    md = "\n".join(md) + "\n"
    yaz_gizli(yol("cikti", "metin-guncelle-cumlesiz.md"), md)
    gunluk_yaz({"gorev": "metin-guncelle", "durum": "hata" if s["hatalar"] else "tamam", "kip": "uygula" if cikti else "kuru"})
    print(md)
    return 4 if s["hatalar"] else 0


def main(arg):
    if len(arg) != 1 or arg[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if arg else 2
    gorev = arg[0]
    if gorev not in ("denetle", "onar-kural", "onar-model", "denetci", "intihal", "icerik-oner", "benzerlik", "benzerlik-denetle", "yerlestir", "metin-denetle", "metin-guncelle"):
        print(f"bilinmeyen görev: {gorev}", file=sys.stderr)
        return 2
    if gorev == "onar-model":
        print("onar-model henüz yok (model ölçümü geçilmeden açılmaz)", file=sys.stderr)
        return 6
    ayar = ayar_oku()
    girdi, hata = girdi_bul(ayar)
    if not girdi:
        gunluk_yaz({"gorev": gorev, "durum": "girdi_reddedildi", "neden": hata})
        print(hata, file=sys.stderr)
        return 5 if "orijinal" in hata else 2
    gunluk_yaz({"gorev": gorev, "durum": "basladi", "girdi_sha256": sha256(girdi)})
    if gorev == "denetci":
        return gorev_denetci(girdi, ayar)
    if gorev == "intihal":
        return gorev_intihal(girdi, ayar)
    if gorev == "icerik-oner":
        return gorev_icerik_oner(girdi)
    if gorev == "benzerlik":
        return gorev_benzerlik(girdi, ayar)
    if gorev == "benzerlik-denetle":
        return gorev_benzerlik_denetle(girdi, ayar)
    if gorev == "yerlestir":
        return gorev_yerlestir(girdi, ayar)
    if gorev == "metin-denetle":
        return gorev_metin_denetle(girdi, ayar)
    if gorev == "metin-guncelle":
        return gorev_metin_guncelle(girdi, ayar)
    return gorev_denetle(girdi) if gorev == "denetle" else gorev_onar_kural(girdi, ayar)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
