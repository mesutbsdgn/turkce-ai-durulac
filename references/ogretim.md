# `+ogretim` — öğretim materyali ölçeği

Öğrenciye giden belgeleri (ders notu, konu anlatımı, rehber, ezber kitapçığı, kelime listesi, pano) **8 boyutlu**,
kanıta dayalı bir ölçekle denetler, puanlar (0–2 × 8 = **16**), güvenli düzeltmeleri yapar ve **yayınlanabilir mi**
kararı verir. Tek kiptir ama **alanı tanır**: belgenin alanını (32 alan; liste aşağıda) ve biçimini (sözel / görsel)
tespit eder, her alanda aynı kalan **ortak çekirdeğe** o alanın **profilini** ekler. Fransızca ölçeği tıp notuna ya da
görsel atlas çalışmasına uygulanmaz. Fransızca/DELF satırları yalnız **örnek**tir.

Kaynak çalışmalar (hepsi 22.11.2026, quoteproof): öğretim ölçeği (5 başlık, 168 bulgu, 113 doğrulandı), alan
profilleri (6 başlık, 249 bulgu, 151 doğrulandı) ve bilim dalları genişletmesi (12 başlık, 5'i sağlık; 455 bulgu, 303
doğrulandı). Kurala giren kanıt ve Claude'un kaynağında açtıkları: `docs/ogretim-alan-kanitlari.md`.

## Ne zaman açık, ne zaman kapalı

- **Açık:** öğretim amaçlı belge: ders notu, rehber, çalışma kâğıdı, ezber/kelime listesi, sınav hazırlık notu.
  Tetikleyiciler: "ders notunu denetle", "öğretim materyali ölçeği", "bu PDF öğretir mi", "+ogretim".
- **Kapalı:** sözleşme ve dilekçe gibi hukuk belgeleri, edebî eserin kendisi (şiir, öykü), sohbet/mesaj, resmî yazı.
  Akademik makale öğretim materyali değildir (tez modu kullanılır). Hukuk fakültesi ders notu ve edebiyat ders notu
  öğretim materyalidir; `+ogretim` bunlarda açıktır.
- `+ogretim` Temizle'nin yerine geçmez: önce düzyazı Temizle kurallarıyla sadeleşir (yabancı dildeki örnek cümlelere,
  okunuşlara ve tablolara dokunulmaz), sonra ölçek çalışır.

## Alan tespiti ve profiller

Ortak çekirdek (her alanda): yabancı alfabe karışması, yer tutucu, başlık numarası, sayfa göndermesi, kendini sınama,
alt metni olmayan görsel, okunaklılık (PDF), verimlilik (PDF). Dayanağı Sweller, Mayer ve Dunlosky; alan değiştirmez.

**Tespit sırası:** `--alan` → frontmatter `alan:` → sözcük puanı. Her alanın anahtar sözcükleri
`references/ogretim-alanlari.json`'da; bir sözcük en çok 3 kez sayılır, 4 harf ve kısası yalnız tam sözcük (+kısa ek)
olarak eşleşir ("gen" ≠ "genel"). Yabancı dil alanı Türkçe harfli okunuş (`/…/`) sayısıyla tanınır; İngilizce yazılmış
tıp notu bu yüzden "dil" sayılmaz. En yüksek puan 4'ün altındaysa **genel** profil seçilir. Çıktı alanı, güveni
(kesin / yüksek / orta / düşük), ipucu sözcükleri ve ikinci adayı yazar; güven yüksek değilse `alan:` yazmasını önerir.

**Biçim:** frontmatter `bicim: gorsel|sozel` ya da tespit: md'de görsel başına 120 kelimeden az metin, ya da PDF
sayfalarının yarısı görselli ve az metinli (<120 kelime) → **görsel**. Görsel biçimde her alanın elle listesine
`_gorsel` maddeleri eklenir ve 3+ görselde şekil başlığı ("Şekil N") aranır.

**Üst/alt alan:** hemşirelik, eczacılık, veteriner, beslenme, fizyoterapi, acil ve diş hekimliği tıbbın; fizik,
kimya ve biyoloji fenin; istatistik matematiğin alt alanıdır. Alt alanın puanı üst alanın yarısına ulaşırsa daha özel
olan seçilir (hemşirelik notu tıp sözcüğü de taşır). Alt alanlar üst alanın ortak kontrol grubunu (`@saglik`, `@fen`)
ve sağlıkta ortak elle listesini miras alır.

**Ortak çekirdeğe eklenen kişisel veri kuralı:** sağlama algoritmasından geçen 11 haneli TC kimlik numarası her alanda
**HATA**dır (rastgele 11 haneli sayı yakalanmaz).

### Sağlık grubu (`@saglik`) — en ayrıntılı bölüm

Tıp ve yedi sağlık alt alanında birlikte çalışır. HATA olanlar yayını durdurur.

| Kontrol | Düzey | Ne yakalar | Dayanak |
|---|---|---|---|
| Doz yazımı | **HATA** | sondaki sıfır (5,0 mg) ve baştaki sıfırsız ondalık (,5 mg); g/dL gibi derişim sayılmaz | ISMP 2024: "Mistaken as 10 mg if the decimal point is not seen" ✓ |
| Hasta kimliği | **HATA** | "Hasta: Ad Soyad", protokol/dosya no | HIPAA Safe Harbor; BMJ ve ICMJE onam kuralları; kimliksizleştirme yönetmeliği (mevzuat.gov.tr) |
| Tehlikeli kısaltma | UYARI | U, IU, cc, q.d., q.o.d., MSO4, MgSO4, μg; SC/SQ, TIW, D/C, AD/AS/AU, OD/OS/OU, doz önünde > < | ISMP 2024 listesi ✓ ("Use SUBQ", "Mistaken as 3 times a day or twice in a week", "<10 misread as 40") |
| Kiloya göre doz | UYARI | "mg/kg" ya da "mg/kg/d" zaman birimi olmadan | ISMP Kanada "Provide the weight and dose per unit weight" ✓; bpac NZ en yüksek erişkin dozu ✓; PSNet "mg/kg/d" vakası (açılamadı) → Durulaç açıklık kuralı |
| Gebelik kategorisi | UYARI | "gebelik kategorisi X" | FDA: "The PLLR removes pregnancy letter categories – A, B, C, D and X" ✓ (30 Haziran 2015) |
| Lab birim karışması | UYARI | aynı analit mg/dL ve mmol/L (ya da µmol/L) ile, dönüşüm yazılmadan | glukoz ÷ 18 (Sacks, Clin Chem); kreatinin ÷ 88,4 ✓ |
| Referans aralığı | UYARI | 2+ "normal değer" kaynaksız ve koşulsuz | Lab raporlama kılavuzları: birim ve aralık birlikte (oto) |
| Kılavuz yılı / yaşı | UYARI | yılsız kılavuz; 5 yıldan eski kılavuz yılı | NHMRC "date of last review is clearly marked" ✓, 5 yıllık gözden geçirme; ERC beş yılda bir (oto) |
| Eski tanı sürümü | UYARI | DSM-IV/III (DSM-5 anılmıyorsa) | DSM-5-TR 2022 (psychiatry.org, oto); ICD-10 bilerek yok: ülkeler kullanmayı sürdürebiliyor (WHO) |
| Tür adı | UYARI | "Escherichia Coli", küçük harfli cins, "E.coli" | ICZN: cins büyük, tür küçük, italik (oto) |
| Tanımsız kısaltma | UYARI | ≥2 kez kullanılan 3+ tanımsız kısaltma | ISMP "avoid abbreviating drug names"; kısaltma belirsizliği çalışmaları |

Alt alana özgü: **diş** (FDI/Universal karışması; Al-Johany 2016 ✓), **hemşirelik** (bakım planında tanı/amaç/girişim/
değerlendirme eksikliği; NANDA-I 2024–2026), **veteriner** (türü yazılmamış doz; gıda hayvanında arınma süresi yok;
Merck: kedide parasetamol 40–50 mg/kg ✓; AB 2019/6), **beslenme** ("kalori" yerine kcal; besine hastalık tedavi/önleme
özelliği), **fizyoterapi** (FITT öğesi eksik egzersiz reçetesi; ACSM FITT-VP), **acil** (kılavuz yaşı; ERC 2025),
**psikoloji** (DSM-IV, p = 0,000, hasta kimliği).

### Öteki alanlar

| Alan | OTO kontroller | Dayanak |
|---|---|---|
| Yabancı dil | dil bilgisi terimi > 12, hedef dışı dil > 8, uzun okunuş > %15, okunuşsuz yabancı metin | Nation, Sweller, DELF ızgarası |
| Matematik · İstatistik | çözülmüş örnek yok; cevapsız alıştırma; istatistikte p = 0,000 | Barbieri 2023 g = 0,48 ✓; IES; APA "p value is … not zero" (oto), baştaki sıfırsız p (APA) |
| Fen · Fizik · Kimya · Biyoloji | SI sembolü yanlış (Kg, Km, gr, lt, KW); sayı-birim bitişik (5kg); deneyde güvenlik notu yok; çözülmüş örnek; tür adı (biyoloji) | BIPM SI Broşürü: küçük harf, "always" boşluk (oto); GHS H/P ifadeleri; ICZN |
| Mühendislik | SI kuralları, cevapsız problem, yılsız veri | BIPM; NIST SP 811 (oto) |
| Yer bilimleri · Ziraat | yılsız veri; harita öğeleri; SI; ziraatte deney/ilaçlama güvenliği, tür adı | ICS çizelgesi 2026/06 (oto); EPA etiket kılavuzu "Percentage application rates should never be used alone" (oto) |
| Bilgisayar | dil etiketi olmayan kod bloğu; Python 2; sürümsüz kod örneği; 99 karakteri aşan Python satırı | python.org "Python 2 is no longer supported" ✓; PEP 8 "79 characters" ✓ |
| Hukuk | yürürlükten kalkmış kanun: 818, 1086, 6762 → **HATA**; 765, 743, 1412 → UYARI; numarasız kanun adı; künyesiz mahkeme kararı; kaynaksız alıntı | 6098 m. 647, 6100 m. 450, 6102 m. 1533 (mevzuat.gov.tr, Claude açtı); Yargıtay karar arama: Esas/Karar/Tarih (oto) |
| İktisat · İşletme | yılsız veri; çözülmüş örnek; kaynak | TÜİK baz yılı; KGK TFRS (oto) |
| Tarih · Coğrafya · Sosyal | kaynağı belirsiz otorite; kaynak yok; yüzyıl yazımı; yılsız veri; harita öğeleri | Wineburg; BBC Bitesize ✓; Time & Spatial |
| İlahiyat | kaynaksız hadis; sure/âyet numarasız meal; kaynaksız alıntı | Türkçe yayınlarda "Bakara, 2/211" düzeni (oto) |
| Edebiyat · Felsefe | kaynaksız doğrudan alıntı (2+); kaynak yok | Chicago, MLA künye ögeleri (oto) |
| Sanat · Mimarlık | künyesiz eser görseli; ölçeksiz teknik çizim | Getty CDWA çekirdek künye; ISO 128 / ISO 5455 (oto); FSEK 70 yıl (mevzuat.gov.tr, oto) |
| Eğitim bilimleri | kaynağı belirsiz otorite; kaynak yok | — (yalnız genel kurallar) |
| Genel | yalnız ortak çekirdek | — |

✓ = Claude kaynağında ayrıca açtı; (oto) = quoteproof otomatik doğrulaması alıntıyı sayfada buldu.

Tıpta doz yazımı HATA'dır, çünkü ISMP bu iki biçimi 10–100 kat doz hatasının kaynağı sayar ve hiç kullanılmamasını
ister. ISMP kuralı reçete içindir; öğrenci notuna uygulandığını ölçen çalışma bulunamadı. Gerekçe: not, öğrencinin yazma
alışkanlığını kurar. Bölü işaretli derişim (g/dL, mg/L) sayılmaz; laboratuvar değerinde sondaki sıfır kesinlik bildirir.

Yeni alan eklemek: `ogretim-alanlari.json`'a anahtar sözcük, kontrol adları (betikteki `KONTROLLER`), elle listesi ve
sınama önerisi yaz; gerekçesini bu tabloya ekle. Kaynağı olmayan alan kuralı yalnız UYARI ya da ELLE olabilir.

## İş akışı

1. Belgeyi oku; hedef dili, seviyeyi ve hedefi (sınav görevi ya da öğrenme hedefi) belirle.
2. Türkçe açıklama metnine Temizle uygula (tür kapısı: "öğretim materyali").
3. `python3 scripts/ogretim_denetim.py BELGE.md [--pdf BELGE.pdf] [--alan AD]` → alan ve biçim, 8 boyut puanı,
   bulgular, alanın elle listesi, çıkış kodu. Alanı ve güveni kullanıcıya söyle; güven düşükse alanı sor.
   İstenirse önce `--duzelt` (yalnız anlamı değiştirmeyen düzeltmeler), sonra yeniden çalıştır.
4. Kullanıcıya kısa tablo: alan, 8 boyut + puan, ilk 5 bulgu, alanın ELLE maddeleri, karar.
5. **Betik çalışmazsa puan uydurma:** çalışmadığını söyle, elle kontrol listesini uygula, puan verme.

**Karar:** otomatik denetimde **HATA** varsa → **yayınlanamaz** (çıkış 1). **UYARI** yayını durdurmaz ama düzeltme
listesine girer (çıkış 0). Dosya okunamadı → çıkış 2. Puan yalnız otomatik ölçülebilen kusuru gösterir; doğruluk ve
hedef uyumu her zaman ELLE maddedir, onlar boşsa karar "otomatik denetimden geçti, elle maddeler bekliyor" olur.

## Ölçek — 8 boyut

Puan: **2** temiz · **1** uyarı · **0** hata. **OTO** = betik ölçer; **ELLE** = üreten ajan kontrol eder ve frontmatter'a yazar.

| # | Boyut | Ölçüt | OTO ölçüm ve eşik | ELLE |
|---|---|---|---|---|
| 1 | **Doğruluk** | Dil, çeviri, okunuş doğru; kaynaksız örnek işaretli | Yabancı alfabe harfi karışması (Kiril, Yunan) → HATA; `TODO`/`FIXME`/`???` → HATA | Bağımsız bir modele denetlet; `denetim: 2026-11-22 sonnet` |
| 2 | **Hedefle uyum** | Belge hangi sınav görevine / öğrenme hedefine hizmet ediyor; gerçek görev tipleri var; kelime sınırı güvenli | — | `hedef:` (ya da `sinav:`) alanı; görev tipleriyle karşılaştır |
| 3 | **Seviye** | Acemide terim yerine sade açıklama; hedef dışı dil yok; sayfada tek yeni kavram | Dil: dil bilgisi terimi > 12, hedef dışı açıklama dili (ör. Fransızca belgede İngilizce) > 8 → UYARI; tıp/diş/fen: 3+ tanımsız kısaltma → UYARI | Sayfada tek yeni kavram |
| 4 | **Ezber ve kavrama** | Kısa cümle, tekrar eden iskelet, tutarlı yazım; dilde okunuş/karşılık yanında | Dil: uzun okunuş > %15, okunuşsuz yabancı metin → UYARI; tarih: yüzyıl yazımı karışık → UYARI | Belgeler arası aynı ifade aynı mı |
| 5 | **Okunaklılık** | Gövde ≥ 11 pt, tablo ≥ 9 pt; boş sayfa yok | PDF'te kelime kutusu yüksekliği ortancası (≈ punto, alt bilgi hariç): < 8 pt → HATA, < 9 pt → UYARI; boş sayfa → HATA | — |
| 6 | **Sıra ve akış** | Harita → seç → kur → uygula → sına; düz başlık numarası; sayfa numarasına gönderme yok | Ek numara (3.5+), aynı numara iki kez, geriye giden numara → UYARI; "s. 6'daki" türü gönderme → UYARI | Mantıksal sıra |
| 7 | **Kendini sınama** | Her konu kapalı kitap sınamayla biter; cevap ayrı; boşluk sayısı cevapla uyumlu | Test / prova / alıştırma / "kendini dene" bölümü yok → UYARI | Cevap anahtarı ayrı, boşluklar uyumlu |
| 8 | **Verimlilik** | Sayfa içerikle orantılı; yarım sayfa az; aynı kural tekrar anlatılmıyor | `sayfa_tavan` aşıldı → HATA; tavan yoksa 16+ sayfa → UYARI; %40'tan az dolu sayfa oranı > %20 → UYARI (son sayfa sayılmaz) | Aynı kural iki kez anlatılmış mı |

Eşikler `scripts/ogretim_denetim.py` başında sabittir; değişiklik bu tabloyla birlikte yapılır.

### Eşiklerin gerekçesi ve sınırı

- Yazı boyu PDF'teki **kelime kutusu yüksekliğinin ortancası**yla ölçülür (≈ punto). Tablo ağırlıklı belgede ortanca
  tablo yazısıdır; bu yüzden HATA eşiği tablo için mutlak alt sınır olan **8 pt**, UYARI **9 pt**'dir. 11 pt gövde
  hedefi ELLE kontrol edilir.
- Yarım sayfa tek başına hata değildir: ünite sonu bilerek boş bırakılabilir. Oran %20'yi aşarsa düzen sorunudur.
- Otomatik denetim **doğruluğu kanıtlamaz**; yalnız ölçülebilen kusurları yakalar.

## Dayanak ilkeleri

| İlke | Ne söylüyor | Belgeye etkisi | Kaynak |
|---|---|---|---|
| **Bilişsel yük** (Sweller) | Bölünmüş dikkat ve gereksizlik öğrenmeyi düşürür; acemiye önce çözülmüş örnek; **uzman ters etkisi**: acemiye yarayan tam destek ileri öğrencide yük olur | Örnek kuralın yanında; aynı kural iki kez anlatılmaz; "çözülmüş → yarım çözümlü → çözümsüz"; acemiye tam destek, seviye yükseldikçe azalt | Chandler & Sweller 1992; Sweller, van Merriënboer & Paas 2019 (Educ. Psychol. Rev. 31) |
| **Mayer çoklu ortam** | Tutarlılık, işaretleme, mekânsal bitişiklik, bölümleme. Etkiler Mayer derlemelerinde orta-büyük, bağımsız meta-analizlerde daha küçük: **yönü tutarlı, büyüklüğü koşullu** | Süs yok; vurgu az ve anlamlı; açıklama ilgili yerin yanında; bölümler kısa | Mayer 2021 (Multimedia Learning); Rey ve ark. 2019 (bölümleme meta-analizi) |
| **Etkili teknikler** (Dunlosky 2013) | On teknikten yalnız **kendini sınama** ve **aralıklı tekrar** yüksek fayda; yeniden okuma ve vurgulama düşük *(elle doğrulandı)* | Her konu kapalı kitap sınamayla biter; tekrar günlere yayılır; "tekrar oku" çalışma sayılmaz | Dunlosky ve ark. 2013 (Psychol. Sci. Public Interest 14/1) |
| **Kelime** (Nation) | Kelimeyi bilmek = biçim–anlam–kullanım; seçim sıklığa göre; başlangıçta ana dil karşılığı en etkili anlam yolu | Kelime cümle/kalıp içinde; her yabancı ögenin yanında ana dil karşılığı ve okunuşu | Nation 2001/2013 (Learning Vocabulary in Another Language) |
| **Kalıp** (Lewis; Boers) | Kalıplar tek parça öğrenilir ve üretim turunda pekişir | Selamlaşma/tanıtma gibi kalıplar bütün verilir; her kalıba en az bir üretim turu | Lewis 1993; Boers & Lindstromberg 2012 |
| **İkili kodlama** (Paivio) | Görsel somut kelimede ek bellek katmanı verir; çevirinin yerini tutmaz | Görsel yalnız somut kelimede; süs görsel yok | Clark & Paivio 1991 |
| **Sınav ızgarası** *(örnek: DELF A1 / CEFR A1)* | Yazma: form (10 puan) + en az **40 kelimelik** mesaj (15 puan; 5 ölçüt). **19 kelime ve altı = 0 puan** *(elle doğrulandı)* | Sınav belgesinde görev tipleri, kelime sayısı ve hitap/veda kuralı açık; metin sınırın güvenle üstünde | FEI DELF A1 Grille PE; CEFR Companion Volume 2020 |
| **Okunabilirlik** | Kılavuzlar en küçük okunur gövde boyunda 12 pt basılıda birleşiyor; tabloda 8 pt altı "çok küçük" | Tablet PDF'inde gövde ≥ 11 pt, tablo ≥ 9 pt; 8 pt altı yayın yok; tablo sade | Australian Government Style Manual — Tables; RNIB/WCAG özetleri |

### Doğrulanamadı — kurala ALINMADI

- Alan araştırması (22.11.2026; quoteproof, 6 başlık, 67 bağımsız kaynak, 249 bulgu, 151 otomatik doğrulandı; kanıt
  özeti `docs/ogretim-alan-kanitlari.md`): ICA harita tasarımı belgesi (başlıkta yıl, lejant eksiksizliği), Rohrer 2020
  karışık alıştırma denemesi (%61 / %38), Shekelle 2001 kılavuz eskime süresi (5,8 yıl) ve Joint Commission yasaklı
  kısaltma sayfası kaynağında açılamadı. Bunlara dayanan kural yok; harita ve kılavuz kuralları doğrulanan başka
  kaynaklara (BBC, Time & Spatial, NHMRC, ISMP) dayanır. Karışık alıştırma yalnız ELLE maddedir.
- Bilim dalları genişletmesinde açılamayan ya da doğrulanamayanlar: PSNet "mg/kg/d" vakası (403), JNC 7'nin yerini
  alan kılavuz (kural çıkarıldı), KVKK karar sayfaları (kural HIPAA/BMJ/ICMJE ve yönetmeliğe dayandı), 765, 743 ve
  1412 sayılı kanunların kaldırılma hükmü (yürürlük kanunlarının metni açılamadı → yalnız UYARI), Madrid Kodu sayfası
  (yalnız ELLE madde), ISMP 2024'te artık bulunmayan HS, BT, x3d (kuraldan çıkarıldı).
- Tall Man harf yazımı (benzer ilaç adları) için kanıt çelişkili (ISMP); kural yapılmadı. Tıp öğrencisinin Anki
  kullanımı için kanıt kesinliği "çok düşük"; ölçek yalnız genel kendini sınama ilkesini kullanır.
- Satır uzunluğu 45–90 karakter ve satır aralığı puntonun 1,2–1,45 katı önerileri kaynağında doğrulanamadı.
- Satır aralığının okuma başarısını değil yalnız tercihi etkilediği bulgusu tek kaynaklı.

Bu değerler öneri olarak anılabilir ama betik eşiği ya da HATA/UYARI gerekçesi yapılmaz.

## Elle kontrol listesi — yayından önce

- [ ] **Doğruluk:** yabancı dil, okunuş ve çeviri bağımsız bir modele okutuldu; frontmatter `denetim: TARİH MODEL`
- [ ] **Hedef:** hangi sınav görevine / öğrenme hedefine hizmet ettiği frontmatter'da: `hedef:` (ya da `sinav:`);
      gerçek görev tipleri ve kelime sınırı var (örnek: DELF A1 mesajı ≥ 40 kelime, güvenli hedef 60+)
- [ ] **Çözülmüş örnek önce:** kural → çözülmüş örnek → yarım çözümlü → kendin yap
- [ ] **Kendini sınama:** konu sonunda kapalı kitap bölümü; cevaplar ayrı yerde; boşluk sayısı cevapla uyumlu
- [ ] **Aralıklı tekrar:** belge ya da program konuya günler sonra dönüşü söylüyor
- [ ] **Tekrar yok:** aynı kural iki yerde anlatılmıyor
- [ ] **Ortak dil:** aşağıdaki şablon kullanıldı

## Ortak dil şablonu — bütün belgelerde aynı

| Öğe | Standart |
|---|---|
| Cümle şeması | **KİM** (mavi) · **FİİL** (kırmızı) · **GERİSİ** (yeşil); renk her belgede aynı anlama gelir |
| Üç sütun | **Yabancı · Okunuş · Türkçe** (ezber tablosu); Türkçe sütunu kapatılıp kendini sınamaya uygun |
| Okunuş | Türkçe harfle, eğik çizgi arasında: `/jö mapel/` *(örnek, Fransızca)*; IPA yalnız Türkçede olmayan ses için |
| Kutular | 🪤 tuzak · 💡 püf nokta · ✍️ yazma / kaynağı yazara ait · 🎤 konuşma · ❓ soru · ✅ kendini dene |
| Başlık numarası | Düz: 1, 1.1, 1.2, 2 …; ek numara (3.5+) yok; araya bölüm girerse yeniden numarala |
| Gönderme | Sayfa numarası değil bölüm numarası/adı ("3.2'deki tablo") |
| Dosya adı | `NN-Ad.pdf`; `-v2`, `-eski`, tarih eki yok; yeni sürüm aynı adın üzerine |
| Frontmatter | `tur:` · `baslik:` · isteğe bağlı `sayfa_tavan:` · `not_sayfasi:` · `denetim:` · `hedef:`/`sinav:` |

`alan:` (genel, dil, tip, dis, hemsirelik, eczacilik, veteriner, beslenme, fizyoterapi, acil, psikoloji, matematik,
istatistik, fen, fizik, kimya, biyoloji, yer_bilimleri, ziraat, bilgisayar, muhendislik, mimarlik, hukuk, iktisat, tarih,
cografya, sosyal, ilahiyat, edebiyat, felsefe, sanat, egitim) ve `bicim:` (gorsel, sozel) tespiti geçer;
`dil:` yabancı dil alanında öğretilen dili verir.

`tur:` değerleri betikte kullanılır: `konu-anlatimi`, `rehber`, `pano` (ya da boş) kendini sınama bölümü ister;
`indeks`, `yonetim` okunuş aramaz; `kilavuz` sayfa göndermesine izinlidir.

## `--duzelt` neyi yapar, neyi yapmaz

Yalnız anlamı değiştirmeyen iki düzeltme, yalnız verilen `.md` dosyasına:
1. Latin harfe benzeyen yabancı alfabe harfi (Kiril `е а о р с …`, Yunan `ο α ε …`) → Latin karşılığı.
2. `html { font-size: X pt }` X < 8,5 ise → 9 pt.

Ötekiler bulgu satırındaki öneriyle ELLE düzeltilir. PDF yeniden üretilmelidir; betik PDF üretmez.
