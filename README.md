<div align="center">

<img src="assets/durulac-logo.svg" width="120" alt="Durulaç logosu">

# Durulaç

### Yapay ve bürokratik Türkçeyi duru bir dile çevirir; ne anlamını bozar ne bir şey uydurur.

![Lisans](https://img.shields.io/badge/lisans-AGPL--3.0-blue) ![Biçim](https://img.shields.io/badge/bi%C3%A7im-Claude%20skill-8A63D2) ![Model](https://img.shields.io/badge/model-ba%C4%9F%C4%B1ms%C4%B1z-brightgreen) ![Dil](https://img.shields.io/badge/dil-T%C3%BCrk%C3%A7e-e30a17) ![TDK](https://img.shields.io/badge/kurallar-TDK-informational)

</div>

Durulaç bir metni alır, içindeki yapay ve bürokratik kalıpları ayıklar, geriye yazarın kendi sesini bırakır. Cümleleri cilalayıp birbirine benzetmez; sayı, tarih ya da iddia uydurmaz. İstersen tek kelimeye dokunmadan sadece bakar: "Bu metin yapay mı?" diye sorarsan, bulduğu kalıpları tek tek, alıntısıyla gösterir.

Kuralları düz Markdown olduğu için tek bir modele bağlı değil. Claude Code, Claude Desktop ve web'de hazır beceri (skill) olarak çalışır; ChatGPT, OpenCode, OpenClaw ve Ollama gibi model ve araçlarda ise sistem yönergesi (system prompt) olarak kullanılır. Nitekim aşağıdaki testler DeepSeek, Qwen, GPT ve Claude ile yapıldı; hepsinde çalışıyor.

## İçindekiler

- [Sorun: yapay dil Türkçede başka türlü görünür](#sorun-yapay-dil-türkçede-başka-türlü-görünür)
- [Bir örnek](#bir-örnek)
- [Üç çalışma biçimi](#üç-çalışma-biçimi)
- [Finans metinleri](#finans-metinleri)
- [Akademik tez modu](#akademik-tez-modu)
- [Word izli değişiklik hattı](#word-izli-değişiklik-hattı)
- [Bilgi koruma denetimi](#bilgi-koruma-denetimi)
- [Ne yapar, ne yapmaz](#ne-yapar-ne-yapmaz)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Nasıl sınandı](#nasıl-sınandı)
- [Sınırları](#sınırları)
- [Katkı](#katkı)
- [Lisans](#lisans)

## Sorun: yapay dil Türkçede başka türlü görünür

Yapaylık Türkçenin kendinde değil; yapay zekânın ve bürokrasinin ürettiği metinde. Üstelik bu metinlerin bıraktığı izler İngilizcedekinden farklıdır. Hazır "humanizer" araçları İngilizceye göre yazılmıştır; onların avladığı şeyler bizde pek işe yaramaz: aşırı uzun çizgi, "X is the Y of Z" kalıbı, birtakım İngilizce dolgu sözcükleri.

Yapay zekâ ve bürokrasi, Türkçede kendini başka yerlerden belli eder:

- İsimleştirme ve şişkin fiiller: "iyileştirilmesi amacıyla optimizasyonlar gerçekleştirilmiştir"
- Bürokratik edatlar: "hususunda", "nezdinde", "bu bağlamda"
- Kanıtsız övgü sıfatları: "yenilikçi, güçlü ve katma değerli çözümler"
- Her konuya uyan klişe girişler: "Günümüzün hızlı tempolu dünyasında..."
- Failini gizleyen edilgen cümleler ve boş vaatler: "hedeflenmektedir", "sağlanmış olup"

Durulaç bu izleri hazır bir listeyi çevirerek değil, Türkçeye göre ve TDK kurallarına dayanarak temizler.

## Bir örnek

Girdi (yapay, kurumsal bir paragraf):

> Günümüzün hızlı tempolu dünyasında, dijital dönüşüm süreçleri işletmeler açısından büyük önem arz etmektedir. Şirketimiz, müşteri memnuniyetini en üst düzeye çıkarmak amacıyla yenilikçi, güçlü ve katma değerli çözümler sunmaktadır. Bu bağlamda, geçtiğimiz dönemde birçok proje hayata geçirilmiş ve olumlu geri dönüşler alınmıştır.

Durulaç'tan sonra:

> Müşteri memnuniyeti bizim için öncelikli, çünkü işimizin sürekliliği ona bağlı. Geçtiğimiz dönemde birçok projeyi tamamladık ve kullanıcılardan olumlu dönüşler aldık.

Klişe giriş, "önem arz etmektedir", boş sıfat dizisi ve "bu bağlamda" çıkarıldı. Edilgen cümleler tek ve tutarlı bir "biz" sesine döndü; kopuk kalanlar bağlaçla birbirine bağlandı.

## Üç çalışma biçimi

**Temizle (varsayılan).** Metni en az müdahaleyle yeniden yazar. Tam metni verir, altına neyi neden değiştirdiğini kısaca sıralar.

**Tespit et.** Hiçbir şeyi yeniden yazmaz. Bulduğu her kalıbı adıyla ve kısa bir alıntıyla gösterir, düzeltme yönünü söyler. "Bunu yapay zekâ mı yazdı?" sorusuna kimin yazdığını tahmin ederek değil, yalnızca metinde görünen kalıpları sayarak yanıt verir. Yüzde ya da olasılık vermez; tespit kesin değildir, hafif bir yeniden yazma kalıpları silebilir. Bu yüzden çıktısı "şu kalıplar görülüyor" der, "bu metin yapaydır" demez.

**İstem iyileştir.** Düzyazıyı değil, yapay zekâ istemini (prompt) düzenler. Amacı değiştirmez; eksik rol, bağlam, kısıt, çıktı biçimi ve doğrulama cümlesini ekler, boşlukları `${değişken}` ile işaretler, sahte örnek uydurmaz. Metin dışarıya gönderilmez; yöntem yerelde uygulanır.

## Finans metinleri

Banka, sigorta, yatırım ve şirket finansı metinlerinde hata iki yönlü olabilir. Yasal olarak aynen kalması gereken bir cümle değişebilir; ya da müşteriye giden karışık bir metin yeterince sadeleşmeyebilir. Durulaç bu yüzden önce metnin hangi finans türü olduğuna bakar:

| Tür | Örnek | Ne yapar |
|---|---|---|
| Yasal ibare ve bildirim | KAP açıklaması, sözleşme hükmü, risk uyarısı | Dokunmaz; yalnız açık yazım hatasını düzeltir. |
| Müşteri bilgilendirmesi | Banka SMS'i, kart mektubu, sigorta bildirimi | Cesurca sadeleştirir; rakamlara, yasal terimlere ve koşullara dokunmaz. |
| Yatırım içeriği ve pazarlama | Fon tanıtımı, kampanya | "Garantili getiri", "risksiz kazanç" gibi vaatleri ve dayanaksız performans iddialarını ayrı bir uyum notunda işaretler; risk uyarısını aynen bırakır. |
| İç yazışma ve rapor | Ekip e-postası, bütçe notu | Plaza İngilizcesini Türkçeleştirir; EBITDA, KDV gibi yerleşik kısaltmaları korur. |

Örnek, müşteri bilgilendirmesi:

> **Önce:** Asgari ödeme tutarı olan 1.250,00 TL'nin son ödeme tarihi olan 13.10.2026 tarihine kadar ödenmemesi halinde aylık %4,25 oranında gecikme faizi uygulanacaktır.
>
> **Sonra:** En az 1.250,00 TL'yi 13.10.2026'ya kadar ödeyin. Ödemezseniz aylık %4,25 gecikme faizi işler.

Tutar, tarih, oran ve "ödemezseniz" koşulu aynen kaldı; uzun cümle ikiye bölündü.

Bu türler için üç yardımcı dosya var:

- [`references/finans-terimleri.md`](references/finans-terimleri.md): 67 terim. Her birinin sade karşılığı ve aynen kalıp kalmayacağı yazılı ("yıllık maliyet oranı" aynen kalır, "ekstre" "hesap özeti" olur, "cash flow" "nakit akışı" olur).
- [`references/finans-mevzuat.md`](references/finans-mevzuat.md): Davranışın dayanağı (TCMB'nin sade dil hükmü, SPK'nın getiri garantisi yasağı, KAP'ın Türkçe kuralı) ve kaynak bağlantıları. Hukuk görüşü değildir.
- [`scripts/okunabilirlik.py`](scripts/okunabilirlik.py): Önceki ve sonraki metin için Ateşman ve Bezirci–Yılmaz okunabilirlik puanı verir. Ayrıca sayıları denetler: "1.250,00 TL" metinde "1.250 TL" ya da "1,5 milyon TL" "1,5 TL" olursa uyarır. Yalnız Python'un standart kütüphanesini kullanır.

- [`scripts/tarama.py`](scripts/tarama.py): Dosya hâlindeki düzyazıda kalıpları satır satır listeler; kod blokları, URL'ler ve tablo ayraçları taranmaz. `--onceki` ile eski sürümle kalıp başına önce → sonra sayısını karşılaştırır. Karar vermez, kontrol listesi üretir; resmî, akademik ve hukuk türünde (`--tur`) devre dışıdır. Okuyarak düzenlemenin kaçırdığı kalıpları yakalamak için eklendi ([Deney 8](docs/deneyler.md)).

```bash
python3 scripts/okunabilirlik.py once.txt sonra.txt
python3 scripts/tarama.py README.tr.md --onceki README.tr.eski.md
```

Testler: `scripts/` içindeki her `test_*.py` dosyası tek başına çalışır (`python3 -B scripts/test_tarama.py` gibi); ek kenar durum testleri için `python3 -m pytest scripts/tests`. v1.4'te toplam 284 test vardır (193 unittest + 91 pytest) ve hepsi geçer.

## Akademik tez modu

Yüksek lisans ve doktora tezlerinde (`--tur tez`) kural tersine döner: edilgen çatı (`-ılmıştır`, `tarafından`), `kapsamında`, `söz konusu` gibi akademik kalıplar bilinçlidir, bu yüzden muaf tutulur. Bunun yerine tezlere özgü sorunlar aranır:

- **Çeviri kokusu ve eş dizim hataları:** "tehdit sergilemek" yerine "tehdit oluşturmak", "politika inşa etmek" yerine "politika geliştirmek", "boşluğu doldurmak" yerine "eksikliği gidermek". 105 kurallı [`references/akademik-esdizim.json`](references/akademik-esdizim.json) çekim eklerini soyarak çalışır (`scripts/esdizim.py`).
- **Kaynaksız otorite:** "Araştırmacılara göre" der ama cümlede `(Yazar, Yıl)` ya da `[1]` yoksa işaretlenir.
- **Ad tamlaması zinciri** (4 ve üzeri) ve **birinci şahıs sızıntısı** ("tezimizde", "ele aldık").
- **Atıf ↔ kaynakça çapraz denetimi** (`scripts/atif_tani.py`): metinde olup kaynakçada olmayan, kaynakçada olup metinde anılmayan, yılı birbirini tutmayan künyeler.
- **Kurum kılavuzu uygunluğu:** [`references/iau-tez-kilavuzu.json`](references/iau-tez-kilavuzu.json) İstanbul Aydın Üniversitesi Tez Yazım Kılavuzu'ndaki sayfa düzeni, başlık hiyerarşisi, atıf biçimi ve terim birliği kurallarını makine okunur biçimde tutar. Başka bir üniversiteye uyarlamak için aynı şemada yeni bir JSON yazmak yeterlidir.

Hepsini tek raporda toplayan araç:

```bash
python3 scripts/tez_analiz.py Tez.docx                 # jüri/üslup raporu (varsayılan: cümlesiz)
python3 scripts/tez_analiz.py Tez.docx --cikti rapor.md
python3 scripts/tez_analiz.py yeni.md --onceki eski.md  # iki sürümü karşılaştırır
python3 scripts/tez_analiz.py Tez.docx --tam            # ifadeleri aynen yazar (yalnız kendi kullanımın için)
```

Varsayılan rapor **cümlesizdir**: tezin tek cümlesi bulunmaz, yalnız konum, kural kimliği, sayı ve geri döndürülemez kısa bir özet kalır. Raporu okuyan kişi ya da model metni görmez; bir bulut modeline tez yüklemek istemeyenler için tasarlandı. Alan beyaz listesi vardır, bir de sızıntı bekçisi: rapor yazılmadan önce tez gövdesinden ardışık beş sözcük arar, bulursa raporu yazmaz ve 3 koduyla çıkar. Testler bekçiyi kasten kapatıp testin kırıldığını da doğrular.

İstersen kendi Ollama sunucundaki bir modelden cümle önerisi de alınabilir: `DURULAC_UZAK_SSH` (ssh takma adı) ve `DURULAC_UZAK_MODEL` ortam değişkenlerini tanımlayıp `--uzak` ver. Bu bayrak, eş dizim bulunan cümlelerden birini (en çok 500 karakter) senin verdiğin ssh takma adına gönderir; bayrak ya da değişken yoksa hiçbir şey gönderilmez. [`references/Modelfile.durulac-tez.sablon`](references/Modelfile.durulac-tez.sablon) kendi temel modeline bağlayacağın bir şablondur; hazır bir model dağıtılmaz.

## Word izli değişiklik hattı

Tez metnine dokunacak her şey Word'ün **izli değişikliği** olarak yazılır (yazar etiketi `Durulaç-Ajan`); reddedersen orijinal geri gelir. Orijinal dosya hiç değişmez, yeni `.docx` yazılır. Bu betikler yalnız Python standart kütüphanesiyle çalışır:

| Betik | İş |
|---|---|
| `tez_onar.py` | Kural tabanlı onarım: yazım ve biçim düzeltmeleri, izli değişiklik olarak |
| `denetci.py` | Özgün ve ajan çıktısını karşılaştırır; sayı, atıf, özel ad ve cümle sayısı kaybını yakalar |
| `benzerlik.py` | Quetext raporundaki atıfsız ve yüksek benzerlikli eşleşmeleri yerel Ollama modeliyle yeniden kurar (izli değişiklik); kaynak künyesi uydurmaz, atıf yerini işaretler. Rapor cümlesizdir |
| `yerlestir.py` | Onaylanmış yeni paragrafı gömme (embedding) benzerliğiyle en yakın gövde paragrafının ardına koyar; eşik altındaysa yerleştirmez |
| `intihal.py` | Tez ile verdiğin korpus arasında yerel benzerlik ön kontrolü (Python 3.12+). Turnitin gibi geniş veri tabanlarının yerini tutmaz; korpus eksikse tespit de eksiktir |
| `icerik.py`, `rapor_ozet.py` | Konu listesi kapsama kontrolü ve Quetext PDF raporundan cümlesiz özet (`pdftotext` gerekir) |
| `tez_ajan.py` | Yukarıdakileri tek kök dizinde, `ayar.json` ile yöneten görev koşturucu (`TEZ_AJAN_KOK`); adında “orijinal” geçen dosyayla çalışmayı reddeder |

`yerlestir.py` gömme için yerel Ollama'da `bge-m3` kullanır. Betikler 127.0.0.1 dışına çıkmaz; tek istisna yukarıdaki açık `--uzak` bayrağıdır.

## Bilgi koruma denetimi

`scripts/bilgi_koruma.py` yalnız finansta değil her Temizle işinde çalışır. Önce ve sonra metnini karşılaştırır, kaybolan sayıyı, alıntıyı, özel adı ve atfı listeler. Uzunluk sınırı geldiğinde (“en çok 30 sözcük”) karşı açıklamanın, kaynak atfının, toplam sayının ve hedef bilgisinin düşmesini önlemek için eklendi: 23 Ekim 2026'da 42 maddelik bir bültende kısaltma 17 maddede bu bilgileri düşürmüştü ve betik hepsini yakaladı.

```bash
python3 scripts/bilgi_koruma.py once.txt sonra.txt
```

## Ne yapar, ne yapmaz

Yapar:

- Metnin türünü önce belirler ve her türe kendi kuralıyla yaklaşır. Resmî yazı, dilekçe, akademik makale ve sözleşmede o türe özgü kalıplar (edilgen çatı, "arz ederim", "işbu") bilinçlidir; onlara dokunmaz. Haberde kaynak atfını, altyazıda kısa satırları, sosyal medyada hashtag ve emojiyi, edebî metinde devrik cümleyi korur.
- Sohbeti sohbet bırakır. Devrik cümleyi, günlük dolguyu, "bence" gibi yumuşatıcıları ve kişisel sesi rapor diline çevirmez.
- Onlarca yapay/bürokratik kalıbı tanır (61–66 numaralı kalıplar yalnız tez modunda): klişe giriş, boş sıfat dizisi, plaza İngilizcesi, sahte-derin kapanış ve daha fazlası. Yerleşik olmayan eş dizimleri de düzeltir ("etki üretmek" yerine "etki yaratmak").
- Bir şey silerken yerine akış bırakır. Dolgu attığında cümleleri kopuk kopuk bırakmaz, bağlaçla toparlar.
- Sadeleştirir, özetlemez. Kelime yükünü azaltır ama bilgi taşıyan cümleyi atmaz.
- Finans metninde rakamları, yasal terimleri ve zorunlu uyarıları korur; yatırım reklamındaki yasak vaatleri işaretler.

Yapmaz:

- Kod bloklarına, komutlara, tablolara ve teknik adlara karışmaz.
- "commit", "pull request" gibi kavram adlarını çevirmez; yalnız "merge etmek" gibi plaza fiillerini Türkçeleştirir ("birleştirmek").
- Metinde olmayan sayıyı, tarihi ya da iddiayı asla uydurmaz. Kanıtsız iddiayı ya işaretler ya da çıkarır.
- Zaten doğal olan cümleyi güya iyileştirmek için ellemez.
- Uyum kararı vermez. Finans metninde riskli ifadeyi işaretler, kararı uyum birimine bırakır.

## Kurulum

Beceri klasörüne klonlamak yeterli:

```bash
git clone https://github.com/mesutbsdgn/turkce-ai-durulac.git ~/.claude/skills/turkce-ai-durulac
```

Beceri dizinin farklıysa (örneğin `~/.agents/skills/`) oraya klonla. Claude bir sonraki oturumda beceriyi kendiliğinden tanır.

**Başka bir modelde ya da araçta (ChatGPT, OpenCode, OpenClaw, Ollama…):** kurulum gerekmez. `SKILL.md` dosyasının içeriğini sistem yönergesi (system prompt / özel talimat) olarak yapıştır; ince ayar istiyorsan `references/degistirme-sozlugu.md` sözlüğünü, finans metni için `references/finans-terimleri.md` dosyasını da ekle. Okunabilirlik betiği Python 3 ister; betiği çalıştıramayan ortamda puan istenmez. Model bunları okuyup aynı kurallarla çalışır. Zayıf modeller kuralları daha eksik uygular; kurumsal/resmî metinde güçlü bir model tercih et.

## Kullanım

Doğal dille istemen yeterli; dilersen adıyla da çağırabilirsin:

```
/turkce-ai-durulac
Şu metni sadeleştir: <metin>
```

Birkaç örnek istek:

- "Bu duyurunun kurumsal kokusunu al." Temizle biçiminde çalışır.
- "Bu paragraf yapay mı, kalıpları göster." Tespit biçiminde çalışır, metne dokunmaz.
- "Şu mesajı sadeleştir." Sohbet tonunu korur, resmîleştirmez.
- "Bu teknik yazıyı düzelt." Kodu ve terimleri bırakır, yalnız düzyazıyı toparlar.
- "Bu banka SMS'ini sadeleştir." Rakamları ve yasal terimleri koruyarak sadeleştirir, okunabilirlik puanını verir.
- "Bu fon tanıtımında sorun var mı?" Yasak vaatleri ve dayanaksız iddiaları uyum notunda gösterir.

## Nasıl sınandı

Durulaç körü körüne "iyidir" denmedi; birkaç turluk kontrollü deneyle ölçüldü. Farklı modeller (DeepSeek, Qwen, GPT-6 Luna) aynı metinleri hem beceriyle hem becerisiz temizledi, bağımsız bir model (Claude Sonnet) sonuçları kör puanladı. Ardından Claude Opus 4.8 kırmızı takım gözüyle yedi sistematik eksik buldu; hepsi kapatıldı. Sonraki turda dört yeni tür kapısı (altyazı, sosyal medya, haber, edebî) ve yeni kalıplar eklendi, aynı koşullarda yinelenen testte gerileme çıkmadı (güçlü uygulayıcıda ortalama 9,9/10). Ardından sözlük derinleştirmesi A/B testiyle seçildi. v1.3'teki finans eklentisi GPT-6 Luna ile kör denendi (15 metin) ve ayrıca koda ve kurallara yönelik bir incelemeden geçti; bulunan hatalar düzeltildikten sonra yinelenen denemede hepsi kapandı.

Öğrendiklerimiz:

- Farklı modellerle çalışması, becerinin tek bir modele bağlı olmadığını da gösterdi.
- Becerinin asıl katkısı yalnızca kalıp silmek değil, güçlü bir modelin fazla düzeltmesini frenlemek. Modelin teknik terimi ya da sohbet tonunu bozmasını engelliyor.
- Zayıf bir modelin gözünden kaçan boş sıfatları ve klişeleri yakalatıyor.
- Uydurma yasağı hem uygulayan hem puanlayan modelce doğrulandı: üslup düzeliyor ama metne olgu eklenmiyor.

Bütün deney kayıtları [`docs/deneyler.md`](docs/deneyler.md) dosyasında. Örneklem küçük ve puanlar bir modelin yargısı olduğundan sonuçlar kesin ölçü değil, yön gösterir.

## Sınırları

- Sonuç uygulayan modele bağlı. Güçlü bir model beceri olmadan da iyi yazabilir; kurumsal metin temizliğinde güçlü bir model önerilir.
- Beceri bir korkuluktur, sihirli değnek değil. Aradığın hatayı temizler, ama güzel üslubu garanti etmez.
- Son söz sende. Altındaki değişiklik listesini oku, onaylamadığını geri al.
- Finans eklentisi hukuk ya da uyum danışmanlığı değildir. Mevzuat notundaki bazı madde numaraları ikincil kaynakla doğrulandı ve dosyada öyle işaretli; resmî kullanımda aslından kontrol et.
- Tarama betiği bağlamı bilmez: doğru kullanımı da işaretleyebilir ve bulmadığı kalıbı (anlam, ritim, fail) bulmaz. Bulguları gerekçeyle karara bağla.
- Tez modu bir danışman ya da jüri yerine geçmez. Bulduğu şey kural ihlali ve olası çeviri kokusudur, bilimsel değerlendirme değil. Eş dizim kuralları derlenmiş bir listedir (`korpus_pmi.py` onu bir korpusla genişletmek içindir, listedeki kurallar yayımlanmış bir korpusa dayanmaz); her kuralın örneği var ama kapsam dar, bulmadığı hatayı yok sayma.
- Yerel küçük bir modelin (7-8 milyar parametre) akademik cümleyi yeniden yazması denendi; bu sürümde modelin kalitesi ölçülmedi, bu yüzden model önerisi **isteğe bağlı bir ek** olarak bırakıldı. Asıl denetim 0-token betiklerdedir; bir modeli tezde kullanmadan önce kendi örneklerinle ölç.
- Okunabilirlik formülleri sözcük ve hece uzunluğuna bakar, anlamı ölçmez. Kısa metinde puan oynaktır; puanı tek başına başarı ölçüsü sayma.

## Katkı

Yeni bir kalıp, sözlük eşlemesi ya da "şuna dokunmamalı" örneği önereceksen issue veya pull request aç. Her kalıp için sorunu, kötü bir örneği ve düzeltilmiş halini ver; dayanağını TDK'ye bağla. Metinde olmayan bir olguyu uyduran örnek kabul edilmez.

## Lisans

GNU Affero Genel Kamu Lisansı, sürüm 3 (AGPL-3.0-only). Tam metin: [LICENSE](LICENSE). Telif © 2026 mesutbsdgn.

`fe24416` dahil önceki commit'ler (son etiket `v1.3`) MIT Lisansı ile yayımlanmıştı; o sürümleri edinenlerin MIT'in verdiği haklar sürer. AGPL, bu değişiklikten sonraki sürümler için geçerlidir. Değiştirme sözlüğünün seçildiği MIT lisanslı kaynağın bildirimi [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) dosyasındadır.

Finans terim listesinin yapısı [sal-keskin/okunabilir](https://github.com/sal-keskin/okunabilir) (MIT) projesinden esinlendi; içerik kopyalanmadı. Okunabilirlik formülleri (Ateşman 1997, Bezirci–Yılmaz 2010) yayımlanmış hâllerinden sıfırdan yazıldı.

Yapısı [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) (MIT) projesinden esinlendi; İngilizce içerik kopyalanmadı, her şey Türkçeye özgün yazıldı. Değiştirme sözlüğü [Denomas/Turkce-yazim-denetimi](https://github.com/Denomas/Turkce-yazim-denetimi) (MIT) kurallarından seçilerek uyarlandı. Dil bilgisi ve noktalama [TDK Yazım Kılavuzu](https://tdk.gov.tr/) temel alındı. Ayrıntılı notlar: [LICENSE-NOTES.md](LICENSE-NOTES.md).
