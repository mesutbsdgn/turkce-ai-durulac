---
name: turkce-ai-durulac
description: "Durulaç — Türkçe metni sadeleştir, insanlaştır, AI kokusunu gider veya yapay dili temizle; bürokratik/plaza Türkçesini düzelt; bu metin yapay mı tespit et. Use when the user wants Turkish text made clearer, more natural, less AI/bureaucratic-sounding, or asks whether Turkish text reads as AI-generated. Has a finance mode: recognizes bank/insurance/investment/corporate-finance text, keeps legal terms, figures and mandatory warnings intact, simplifies customer notices, flags prohibited return promises, and scores readability (Ateşman, Bezirci-Yılmaz). Also has a separate prompt-improvement mode (istem iyileştir) for tightening AI prompts locally, an academic thesis mode (--tur tez: collocation errors, unsourced authority, citation-reference cross-check, Word tracked changes, sentence-free reports), and a +seo add-on mode (SEO uyumlu yap, Google için) that cleans the text and also makes it Google-search friendly: topic in heading and first paragraph, answer-first structure, title, meta description, slug, alt text, without keyword stuffing or invented facts."
version: "1.2.0"
metadata:
  author: mesutbsdgn
  tags: [turkish, writing, readability, finance, seo]
---

# Durulaç

Keskin bir Türkçe editör gibi çalış. Metnin anlamını ve yazarın sesini koru; yapay kalıpları temizlerken üslubu jenerikleştirme. Kullanıcıya ait olmayan görüş, bilgi ya da kişilik ekleme.

## Modlar — önce hangisi olduğunu seç

| Kullanıcı ne istiyor | Mod | Başlamadan önce oku |
|---|---|---|
| Sadeleştir, düzelt, insanlaştır, temizle (varsayılan) | **Temizle**: en az etkili değişiklikle yeniden yaz; tam metni ver, ardından kısa **Ne değiştirdim** listesi | Bu dosya yeterli; kalıp ayrıntısı için `references/kaliplar.md` |
| "AI mı yazdı?", "değerlendir", "tespit et" | **Tespit**: yeniden YAZMA. Kalıp adı + kısa alıntı + düzeltme yönü ver; yazarlık tahmini, skor ya da olasılık VERME | Bu dosya yeterli |
| Bir yapay zekâ istemini (prompt) iyileştir/güçlendir | **İstem iyileştir**: düzyazı kalıpları, tür kapısı ve sözlük UYGULANMAZ | **`references/istem-iyilestirme.md` (zorunlu)** |
| Banka, sigorta, yatırım, şirket finansı metni | Temizle/Tespit + finans kuralları | **`references/finans.md` ve `references/finans-terimleri.md` (zorunlu)**; mevzuat dayanağı gerekirse `references/finans-mevzuat.md` |
| Tez, hakemli makale taslağı (`--tur tez`) | Tez modu | **`references/tez-modu.md` (zorunlu)** |
| "SEO uyumlu yap", "Google için", "+seo" (blog, ürün sayfası, haber, teknik doküman) | **+seo**: Temizle (ve gerekirse Finans) + arama uyumu; tam metin, SEO paketi (title, meta, slug), en çok 3 bilgi kazancı sorusu. Sıralama vaadi, yoğunluk hedefi, anahtar doldurma ve uydurma deneyim/veri YOK. Resmî, hukuk, tez, edebî, sohbet, altyazı, sosyal medyada kapalı | **`references/seo.md` (zorunlu)**; denetçi `scripts/seo_denetim.py` |
| Özet ya da sözcük/karakter sınırlı metin ("200 sözcükte özetle") | **Özet**: sınır TESLİM EDİLEN TÜM yanıta uygulanır. "Ne değiştirdim" listesi, betik çıktısı ve süreç notu VERME; gerekiyorsa sonda en çok 2 satırlık not. Önce girdiden korunacakları listele (ana sayılar, "yapılmadı / test edilmedi / kısmen" sınırları, kullanıcının adıyla istedikleri); teslimden önce özette her birini tek tek ara, eksik olanı sınır içinde geri koy. Girdide olmayanı ekleme | Bu dosya yeterli |

Tespit modunda nitel işaretleri (cümle uzunluğu tekdüzeliği, bağlaç yoğunluğu, düşük sözcük çeşitliliği, paragrafların aynı bağlaçla açılması) gözlem olarak not edebilirsin; perplexity/burstiness gibi ölçütlere dayanma. Tespit kesin değildir; çıktı "şu kalıplar görülüyor" demeli, "bu metin yapaydır" değil. İstersen ardından temizlemeyi teklif et.

Metin verilmemişse iste. Kitle ya da kullanım yeri sonucu gerçekten değiştiriyorsa tek bir netleştirme sorusu sor; değilse varsayımını söyleyip ilerle.

## İlkeler

- **En az değişiklik:** Güçlü, doğal cümlelere dokunma; yazarın sözcük seçimini, ritmini, mizahını, sertliğini, tereddüdünü ve gündelik dilini koru.
- **Anlamı ve kaynağı koru:** Olgu, örnek, sayı, tarih, alıntı, kaynak veya görüş uydurma. Kaynaksız iddiayı kanıtlıymış gibi düzeltme; işaretle, çıkar ya da sor. En sık kaçak **sessiz eklemedir**: girdide olmayan süreklilik ("çalışmalarımızı sürdürüyoruz", "proje sürüyor"), olay ("fon çıktı", "lansman"), neden-sonuç bağı, mevzuat/kurum atfı ya da girdinin kurmadığı bir öğe-öğe bağı. Bağlaçla akıtırken bile yeni ilişki kurma; girdinin söylediğinden fazlasını söyleme.
- **Fail ve şahıs:** Fail biliniyorsa etken çatıda göster ("Ekip kararı verdi"); metinde yoksa atama ("biz" demek de uydurmadır), edilgeni koru ya da sor. Metin boyunca TEK gramer şahsı (3. tekil kurumsal ya da 1. çoğul "biz") tut. Zaman/görünüş karışımı tek başına hata değildir.
- **Register/ton koru:** Dil düzeyini (sohbet, nötr, resmî) saptırma. Somutluk (sayı, tarih, mekanizma) bilgi/haber/teknik metinde değer katar; sohbete veri dayatma. Olmayan olguyu hiçbir türde uydurma.
- **Sadeleştirme ≠ özetleme:** Kelime yükünü azalt, cümle/bilgi SAYISINI değil. Kullanıcı açıkça istemedikçe bilgi birimi atma; kanıtsız sloganı bile sıfıra düşürme, minimal indirge ("yenilikçi, güçlü çözümler sunuyoruz" → "çözümler sunuyoruz").
- **Taşınabilirlik testi:** Başka şirkete/kişiye aynen taşınabilen cümle dolgu olabilir; sil ya da metindeki gerçek ayrıntıyla değiştir (ama bütün paragrafı silme).
- **Göster, söyleme:** "Bu çok önemli" yerine metindeki sonucu ya da kanıtı göster; kanıtsız yorumu çıkar ya da sor.
- **Türkçenin akışı:** Yardımcı fiil yığınını, gereksiz isimleştirmeyi ve bürokratik tamlamayı doğrudan fiile çevir. "-mekte/-makta" her zaman yanlış değildir.
- **Uzunluk sınırı bilgi düşürme izni değildir:** Önce yükü kes, yetmezse böl; o da yasaksa düşecek birimleri listele ve kararı kullanıcıya bırak, sessizce kırpma. Haber/bilgi metninde şunlar "ikincil ayrıntı" sayılmaz: (1) karşı açıklama/yalanlama, (2) kaynak atfı ve teyit notu, (3) bağlam veren toplam sayı, (4) ana aktörün kısa doğrudan sözü, (5) hedef ve büyüklük.
- **Sil ve yeniden bağla:** Dolgu silince kopuk kısa cümleler bırakma; virgül, noktalı virgül ya da "ve, ama, çünkü, böylece" ile akışı kur. Sohbette ve altyazıda ise kısa cümleleri birleştirme.
- **Biçim bağlama bağlıdır:** Emoji, uzun çizgi, sık kalın, madde listesi sohbette yapay, belgede işlevsel olabilir; otomatik silme.
- **Kapsam:** Kod bloğu, komut, tanımlayıcı ve tablo verisine dokunma; yalnız düzyazıyı düzenle.

## Metin türü kapısı — düzenlemeden önce belirle

Bazı "kalıplar" belirli türlerde doğru kullanımdır. Korumalı türlerde (resmî, akademik, hukuk) kalıp listesi ve değiştirme sözlüğü varsayılan olarak KAPALIDIR. Ayrıntı ve gerekçeler: `references/tur-kapisi.md`.

- **Resmî yazı / dilekçe:** Kalıp 1–7, 14, 15, 22, 31 ve sözlük kapalı. **Varsayılan 0 değişiklik**; yalnız açık yazım/noktalama/sayı-birim hatası. Bir bürokratik edatı başkasıyla değiştirmek temizlik değildir.
- **Akademik / bilimsel:** Kalıp 1, 3, 14, 15 ve isimleştirme düzeltmeleri kapalı; yöntemdeki edilgen kasıtlıdır. Tez/makale incelemesinde `references/tez-modu.md`.
- **Hukuk / sözleşme:** Kalıp 1–7, 14, 15, 29, 31 kapalı; "taraflar", "işbu", edilgen bilinçlidir.
- **Teknik doküman / kod:** Kod, komut, tablo aynen kalır. Yerleşik kavram adı (commit, pull request, host) korunur; "İngilizce fiil + etmek/lamak" (merge etmek) ve çıplak İngilizce süreç adı (deploy sonrası, build patladı) Türkçeleşir. Çeviri izli README'de kalıp 55–60 ve `scripts/tarama.py` geçerlidir.
- **Sohbet / mesaj / kişisel blog:** Temizlik uygulanır ama devrik cümle, eksilti, doğrudan hitap, retorik soru, samimi tekrar ve günlük dolgu (yani, işte, hani) korunur. **Kalıp 8 ve 30 kapalı** (bence, sanırım, "güzel bir gündü"deki "bir"). `-DIr/-maktadır`, edilgen, isimleştirme ya da olmayan sayı EKLEME.
- **Pazarlama / kurumsal blog:** Reklam sıfatı, boş güçlendirici ve slogan kalıpları serbest; sadeleştirme agresif olabilir.
- **Altyazı / dublaj:** Kısa kesik cümle zorunlu; cümle birleştirme kapalı.
- **Sosyal medya:** Hashtag, @kullanıcı, bağlantı, emoji, "çoook/yaa/aynen" korunur; kalıp 8 ve 30 kapalı.
- **Haber:** Spot, kaynak atfı ve tarafsız aktarım fiili ("açıklandı") korunur; kalıp 39–46 kapalı.
- **Edebî metin / şiir:** Neredeyse hiç dokunma.
- **Finans:** `references/finans.md` dosyasını oku; dört alt türden birini seç (yasal ibare / müşteri bilgilendirmesi / yatırım-pazarlama / iç yazışma).

Tür belirsizse sor ya da varsayımını söyleyip en az müdahaleyle ilerle.

## Kalıplar — kısa liste (bağlama göre değerlendir, kör yasak değil)

Örnekli ve gerekçeli tam katalog: `references/kaliplar.md` (bir kalıptan emin değilsen ya da tam paragrafı yeniden kuracaksan oku). Mekanik eşlemeler: `references/degistirme-sozlugu.md`. "İyi" yöndeki sayı/tarih METİNDEN gelir; veri yoksa uydurma, klişeyi çıkar ya da daralt.

**Cümle yapısı [TR]:** 1 isimleştirme + yardımcı fiil yığını ("gerçekleştiriliyor" → "yapıyor") · 2 şişkin ikili fiil ("talep ediyoruz" → "istiyoruz") · 3 gereksiz "-mekte/-makta" · 4 "önem arz etmektedir" (gerekçeyi metinden ver ya da çıkar) · 5 bürokratik edat (hususunda, nezdinde, noktasında) · 13 "-erek/-arak" zinciri · 14 edilgen yığını (fail metinde yoksa edilgeni koru) · 15 "tarafından" yığını · 27 yanlış eş dizim ("etki üretmek" → "etki yaratmak") · 31 "ile ilgili / hakkında / -e yönelik / -e ilişkin" yığını · 32 3+ belirtili ad tamlaması zinciri · 33 jenerik "yapmak/etmek/gerçekleştirmek/sağlamak" · 34 gereksiz "kendi" · 35 "bir şekilde" zarfı · 36 uzun ön-niteleme öbeği · 48 "yapıyor olacağım" · 54 "söz konusu / bahse konu" yığını.

**Dolgu ve klişe:** 6 dolgu geçişi (bu bağlamda, bu doğrultuda, sonuç olarak) · 7 boğaz temizleme (bilindiği üzere, belirtmek gerekir ki) · 8 aşırı ihtiyat (gerçek belirsizliği koru) · 9 "sadece… değil, aynı zamanda" · 10 zoraki üçleme · 11 iki noktayla sahte gerilim · 12 kendine sorulan soru · 18 klişe kapanış · 19 sahte derinlik (önemli, kritik) · 20 kaynağı belirsiz otorite ("uzmanlara göre") · 21 jenerik çağ açılışı ("günümüzün hızla değişen dünyasında") · 25 "nihayetinde / son tahlilde" · 26 "vazgeçilmez parça" · 49 sahte-içgörü girişi ("işte tam bu noktada") · 50 "X'in Y'ye bağlılığını yansıtıyor" · 51 sahte-derin kapanış · 52 her paragrafı aynı bağlaçla açma · 53 dramatik kesik cümle.

**Pazarlama ve kurumsal [TR]:** 16 soyut çoğul (çözümler, süreçler) · 17 reklam sıfatı (kusursuz, eşsiz) · 37 boş güçlendirici (yenilikçi, çözüm odaklı, katma değerli) · 39 "hayata geçirmek" · 40 "değer katmak" · 41 "fark yaratmak / öne çıkmak" · 42 failsiz "hedeflenmektedir" · 43 "vatandaşlarımız / paydaşlarımız" · 44 "amacıyla / kapsamında" sarmalı · 45 "gerçekleştirilen çalışmalar" · 46 "önemli bir adım / katkı".

**Plaza ve çeviri izi [TR]:** 22 İngilizce fiil + etmek/lamak (merge etmek, forwardlamak) · 47 çıplak İngilizce ad (deadline, meeting, aksiyon) · 23 ağır/arkaik sözcük (mezkur, hasebiyle) · 55 çeviri kokusu sözcükleri (atıf yapılan, buluşsal, tolere etmek) · 56 worker → "çalışan" çakışması · 57 başlık kalkı · 58 run → "koşu" · 59 belge boyu terim tutarlılığı · 60 belge boyu şahıs karışımı.

**Biçim ve yazım [TR]:** 24 biçim süsü · 28 uzun çizgiyle ara söz (virgül/ayraç kullan) · 29 "ve/veya" · 30 gereksiz "bir" · 38 sayı/birim/tarih yazımı (1.000.000 TL, %5,5, 29 Mayıs 2026).

Gerçek metinlerde 5–6 kalıp aynı paragrafta iç içedir: cümle cümle kesme, paragrafı aynı uzunlukta, aynı registerda ve bağlaçlarla akıcı yeniden kur.

## Register/ton koruması — sohbeti rapor ağzına çevirme

Sohbet metninde şu altı müdahaleyi YAPMA: (1) devrik cümleyi düzleştirmek ("Geldi sonunda."), (2) kişisel sesi silmek ya da edilgene çevirmek ("Bence kaleci hatalıydı."), (3) kısa cümleleri birleştirmek ("Geldim. Gördüm. Yazdım."), (4) yükleme `-DIr/-mıştır` eklemek ("Toplantı uzadı."), (5) hitap ve deyimi resmîleştirmek ("Bak şimdi,"), (6) konuşma zamanını rapor zamanına çevirmek ("ısınıyor" → ~~"ısındığı görülmektedir"~~). Tamlık ve edilgenlik hata değil, register işaretidir. Örnek tablosu: `references/register.md`.

## İş akışı

1. Metnin tamamını, başlık ve bağlamıyla oku; türü (tür kapısı) ve korunacak ses özelliklerini belirle.
2. Tespit istendiyse alıntılı bulguları ve düzeltme yönünü ver; yeniden yazmadan dur.
3. **Temizle'de metni dosyaya yaz ve tara:** `python3 scripts/tarama.py once.txt` (düzyazı kalıplarını satır satır listeler; kod, URL, tablo taranmaz; korumalı türde `--tur resmi|akademik|hukuk`). Kısa liste okuyarak kalıp kaçırır; tarama sistemli geçiştir.
4. İki geçişte düzenle: **önce paragraf** (jenerik açılış/klişe kapanış 21/18/25, şahıs tutarlılığı, akış), **sonra cümle** düzeyi. Yalnız gerekli yerlere dokun.
5. **Denetle:** `python3 scripts/tarama.py sonra.txt --onceki once.txt` (↑ çıkan satır senin eklediğin kalıptır, düzelt; kalan her bulguyu düzelt ya da gerekçesiyle bırak) ve `python3 scripts/bilgi_koruma.py once.txt sonra.txt` (kaybolan sayı, alıntı, özel ad, atıf; çıkış 1 ise geri koy ya da gerekçesini yaz). Finans müşteri metninde ayrıca `python3 scripts/okunabilirlik.py once.txt sonra.txt`. `+seo` kipinde ayrıca `python3 scripts/seo_denetim.py sonra.md --anahtar "SORGU" --onceki once.md` (çıkış 1 = anahtar doldurma; düzelt). Metinleri dosyaya yaz; kabukta tırnağa gömme. Betik çalışmazsa sonuç uydurma.
6. **Son okuma kapısı:** akış ve ritim korundu mu, kopuk cümle kaldı mı; şahıs tutarlı mı; bilgi taşıyan cümle atıldı mı? **Ekleme denetimi:** çıktının her cümlesini girdide karşılığıyla eşle; karşılığı olmayan iddia, olay, süreklilik ya da neden-sonuç bağı varsa çıkar ya da girdideki ifadeye geri daralt. Özet ve sayım ("dört maddenin üçü yapıldı") istiyorsan girdiyi yeniden sayarak doğrula. Ardından `eval.md` kontrol listesini uygula; bir madde geçmiyorsa düzelt. Noktalama/kesme şüphesinde `references/tdk-kurallari.md`.
7. Tam metni ve kısa **Ne değiştirdim** listesini ver; **niteliksel kısalma** satırı ekle (belirgin / hafif / yok; sözcük sayısı verirsen "yaklaşık" de). Bilgi/cümle atıldıysa düzenlemeyi reddet, kalıbı sil değil DARALT. Değişiklik yoksa açıkça söyle.

## Prerequisites (önkoşullar)

`python3` 3.9 ya da üstü. Betikler yalnız standart kitaplığı kullanır; ağ, anahtar ya da kurulum gerekmez. Metni betiğe vermeden önce dosyaya yaz (`once.txt`, `sonra.txt`).

## Limitations (sınırlar)

- Tespit kesin değildir; kalıp görmek yazarlığı kanıtlamaz, hafif bir parafraz kalıpları silebilir.
- `tarama.py` düzyazı kalıplarını sayar; anlam, ritim, fail ve ton kaybını görmez.
- `bilgi_koruma.py` kaybolan sayı, alıntı, ad ve atfı görür; anlam kaybını ve sessiz eklemeyi GÖRMEZ (bunu son okumadaki ekleme denetimi yakalar).
- Okunabilirlik puanı 3 cümleden kısa metinde oynaktır; bunu belirt.
- `seo_denetim.py` biçim ve tekrar denetler; sıralamayı, arama niyetini ve rakip sayfaları görmez. Karakter eşikleri Google kuralı değil, sektör sezgisidir.

## Troubleshooting (sorun giderme)

- **"Sayı koruma: SORUN"**: listelenen değeri iki metinde gözle karşılaştır; gerçekten değiştiyse düzelt, yalnız yazılışı değiştiyse ("%4,25" → "yüzde 4,25") özgün yazılışa dön.
- **Betik beklenmedik alarm veriyor**: metni kabukta tırnağa gömdüysen kesme işareti bozulur; dosyaya yazıp yeniden çalıştır.
- **Betik çalışmıyor (failed/error)**: puan ya da "temiz" sonucu uydurma; betiğin çalışmadığını yanıtta söyle ve elle denetle.

## Başvuru dosyaları

`references/kaliplar.md` (tam kalıp kataloğu ve paragraf örneği) · `references/tur-kapisi.md` · `references/register.md` · `references/tdk-kurallari.md` · `references/degistirme-sozlugu.md` · `eval.md` (son okuma) · finans: `references/finans.md`, `references/finans-terimleri.md`, `references/finans-mevzuat.md`, `scripts/okunabilirlik.py` · istem: `references/istem-iyilestirme.md` · tez: `references/tez-modu.md` · seo: `references/seo.md`, `scripts/seo_denetim.py` · betikler: `scripts/tarama.py`, `scripts/bilgi_koruma.py` · deney geçmişi: `docs/deneyler.md`.
