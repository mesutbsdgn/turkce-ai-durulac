# Türkçe Humanizer öz denetimi

Düzenleme sonrasında her soruya **Evet/Hayır** de. Bir yanıt Hayır ise metni düzeltmeden sunma. Tespit modunda yeniden yazmama kuralını ayrıca denetle.

> Bu liste her kalıba dokunmanı DEĞİL, dokunduğun her yerin gerekçeli olmasını denetler. Bir maddeyi “Evet”e çevirmek için metne yeni değişiklik ekleme baskısı yapma — çoğu “Evet” zaten dokunmadığın içindir.

## Kontrol listesi

- Metnin ana anlamını ve yazarın sesini korudum mu?
- Güçlü ve doğal cümlelere dokunmadan bıraktım mı?
- Kaynak, sayı, tarih, örnek, fail veya görüş uydurmadım mı?
- Belirsiz iddiayı kanıtsız kesinleştirmek yerine işaretledim mi?
- Gereksiz isimleştirme ve yardımcı fiilleri doğrudan fiile çevirdim mi?
- Fail biliniyorsa etken çatıda görünür kıldım mı; bilinmiyorsa uydurmadım mı?
- Bürokrasiyi, dolgu geçişleri ve jenerik açılışları yalnızca gereksiz olduklarında kestim mi?
- Plaza sözcüklerini ve reklam sıfatlarını bağlama göre ele aldım mı?
- Sohbet biçim süsünü belge yapısından ayırdım mı?
- Metnin registerını (dil düzeyini) korudum mu; sohbeti rapor ağzına çevirmedim mi (devrik cümle, kişisel ses, kısa cümle korundu; `-DIr/-maktadır`, edilgen çatı, isimleştirme, olmayan tarih/sayı EKLENMEDİ)?
- Kod blokları, tablolar ve komut içeren teknik içeriğe dokunmadım mı?
- Tekrarı azalttım ama yazarın ritmini ve yapısını korudum mu?
- Dolgu/bağlaç silince akışı yeniden bağladım mı; art arda kopuk kısa cümle (telgraf tonu) bırakmadım mı?
- Gramer şahsını metin boyunca tutarlı tuttum mu (3. tekil ↔ 1. çoğul arası kaymadım mı)?
- Bilgi taşıyan bir cümleyi/birimini tümüyle atmadım mı (sadeleştirme yaptım, özetleme değil)?
- Niteliksel kısalma satırını ekledim mi; kelime sayısı verdiysem “yaklaşık” dedim mi (sayıyı uydurup kesin gibi sunmadım)?
- Korumalı türde (resmî/akademik/hukuk) devre dışı kalıpları uygulamadım mı; bürokratik edatı başka edatla değiştirmedim mi?
- Temizle modunda tam metni ve “Ne değiştirdim” listesini verdim mi?
- Tespit modunda kalıp adını ve alıntıyı verdim; yazarlık tahmini yapmadım mı?

## Önce/sonra denetim örnekleri

Her örnekte düzeltme yönü beklenir; çevresindeki metin anlamı değiştiriyorsa otomatik uygulama.

1. **-mekte/-makta → doğal zaman:** “Ekip çalışmalarını sürdürmektedir.” → “Ekip çalışıyor.”
2. **İsimleştirme → doğrudan fiil:** “Destek talebinde bulunuyoruz.” → “Destek istiyoruz.”
3. **Reklam sıfatı → kanıt veya daraltma:** “Kusursuz hizmet sunuyoruz.” → “Hizmetin hangi ölçütle iyi olduğu belirtilmeli; veri yoksa ‘kusursuz’ çıkarılmalı.”
4. **Dolgu geçiş → doğrudan nokta:** “Bu bağlamda, sonuç olarak ekip işi bitirdi.” → “Ekip işi bitirdi.”
5. **Plaza terimi → Türkçe karşılık:** “Notları forward edeceğim.” → “Notları ileteceğim.”
6. **Edilgen fail → faili göster / uydurma:** “Karar verildi.” → “Kurul kararı verdi.” (Kurul olduğu kaynakta biliniyorsa; değilse fail sorulur.)
7. **Kaynaksız iddia → kaynak iste veya çıkar:** “Uzmanlara göre bu yöntem en iyisi.” → “Hangi uzman ve hangi kaynak? Kaynak yoksa iddiayı çıkar.”
8. **Biçim süsü → sohbet dilinde sadeleştir, belgede koru:** “**Özet** — ✅ hazır!” → Sohbet: “Özet: hazır.” Teknik README başlığı, tablo veya görev işareti işlevliyse korunur.

9. **Yanlış eş dizim → doğal fiil:** “291.900 TL’lik etkiyi üretti.” → “291.900 TL’lik etki yarattı.” (“etki üretmek” yerleşik değil; “-lik” miktar eki doğrudur, olgu ekleme.)
10. **Kurum/birim eki kesmesi → kesmesiz:** “Finans’ın imzaladığı” (birim kastediliyorsa) → “Finans biriminin imzaladığı” ya da “şirketin finans birimi”. (TDK: kurum/birim adına gelen ek kesmeyle ayrılmaz.)
11. **Özne–yüklem virgülü → uzun nitelemede virgül:** “OptivoPlex stok … düşüren bir yazılımdır.” → “OptivoPlex, stok … düşüren bir yazılımdır.” (Uzun niteleme özneyi yüklemden uzaklaştırır.)

## DOKUNMA örnekleri (aşırı düzeltme freni)

Bu örneklerde kalıp GÖRÜNÜR ama tür/bağlam nedeniyle DOĞRUDUR; değiştirirsen hata yaparsın.

1. **Resmî dilekçe:** “Gereğini arz ederim.” → dokunma (Resmî Yazışma Kılavuzu zorunlu kalıbı).
2. **Akademik yöntem:** “Veriler SPSS ile analiz edildi.” → edilgen kasıtlı, dokunma.
3. **Teknik düzyazı — kavram korunur:** “Pull request’teki commit’leri inceledim.” → dokunma. (“pull request”, “commit” kavram adıdır, korunur; “incelemek” zaten Türkçe. NOT: “merge ettim” gibi İngilizce FİİL kalıbı olsaydı “birleştirdim”e çevrilirdi — kavram korunur, fiil Türkçeleşir.)
4. **Yerleşik retorik üçleme:** “Hızlı, ucuz ve güvenli.” → tek seferlikse dokunma.
5. **Gerçek belirsizlik:** “Sunucu aşırı yükte çökebilir.” → olay kesin değilse “-ebilir” kalır.
6. **Hukuk:** “İşbu sözleşme taraflarca imzalanmıştır.” → tür kalıbı, dokunma.
7. **Sohbet — devrik cümle:** “Geldi sonunda.” → dokunma. (“Sonunda geldi.” yapmak vurguyu ve konuşma ritmini bozar.)
8. **Sohbet — eksilti + doğrudan hitap:** “Bak şimdi, bana da bir tane.” → dokunma. (Bağlam yüklemi veriyor; hitap işlevsel.)
9. **Sohbet — retorik soru + kişisel ses:** “Son dakika golü yedik ya, of. Bence kalecinin hatasıydı.” → dokunma. (Edilgene/rapor tonuna çevirme.)
10. **Sohbet — konuşma yumuşatıcısı + doğal “bir”:** “Çok etkileyici bir yapımdı diyebilirim.” → dokunma. (“diyebilirim” ihtiyat değil yumuşatıcı; “bir” doğal — kalıp 8/30 sohbette devre dışı.)
11. **Resmî dilekçe — edat swap yok:** “…çerçevesinde gereğini arz ederim.” → dokunma. (“çerçevesinde → doğrultusunda” aynı derece resmî; temizlik değil, gereksiz müdahale.)

## Tespit modu çıktı şablonu

Her bulgu: **[kalıp adı]** · “<alıntı>” · düzeltme yönü. **Her alıntıya EN uygun TEK kalıp adı ver; aynı ifadeye kalıp yığma — bulgu SAYISI kanıt gücü değildir, yapay yoğunluk oluşturma.** Sonda: kaç kalıp / metin uzunluğu (yaklaşık) ve “tek kalıp kanıt değildir; yoğunluk anlamlıdır” notu. Yazarlık tahmini yapma.

## Son okuma — Evet/Hayır kapısı

Bu da bir kapıdır: Hayır ise sunma. Şüphedeysen daha az değiştir.

- Düzenlenmiş metin yazarın ağzından, tek ve tutarlı bir sesle doğal duyuluyor mu?
- Her değişiklik anlamı, kanıtı veya okunabilirliği iyileştiriyor mu; hiçbiri akışı ya da registerı bozmuyor mu?

## Finans deneme vakaları

Her vakada **beklenen davranış** tutmalı. “Asla” satırı ihlal edilirse düzenleme reddedilir. Müşteri bilgilendirmesi vakalarında `python3 scripts/okunabilirlik.py once.txt sonra.txt` çalıştırılır: Ateşman artmalı, “Sayı koruma: tamam” çıkmalı.

1. **Müşteri SMS'i — sadeleştir.** “Kredi kartınıza tahakkuk ettirilen akdi faiz tutarı hesap özetinize yansıtılmıştır.” → “Kartınıza işleyen sözleşme faizi hesap özetinize eklendi.” Asla: “akdi faiz”i yalnız “faiz” yapmak (gecikme faiziyle karışır).
2. **Müşteri mektubu — koşul ve rakam.** “Asgari ödeme tutarı olan 1.250,00 TL'nin son ödeme tarihi olan 13.10.2026 tarihine kadar ödenmemesi halinde aylık %4,25 oranında gecikme faizi uygulanacaktır.” → “En az 1.250,00 TL'yi 13.10.2026'ya kadar ödeyin. Ödemezseniz aylık %4,25 gecikme faizi işler.” Asla: tutarı yuvarlamak, tarihi “ay ortası” yapmak, koşulu silmek.
3. **Yasal terim — açıkla, değiştirme.** “Kredinizin yıllık maliyet oranı %52,80'dir.” → terim kalır; isteğe bağlı: “Kredinizin yıllık maliyet oranı (faiz, vergi ve masraflar dâhil yıllık toplam maliyet) %52,80.” Asla: “yıllık maliyet oranı” yerine “yıllık faiz” yazmak.
4. **KAP açıklaması — dokunma.** “Şirketimiz Yönetim Kurulu, 02.10.2026 tarihli toplantısında, çıkarılmış sermayenin %100 oranında bedelsiz olarak artırılmasına karar vermiştir.” → 0 değişiklik. Sadeleştirme istenirse yeniden yazma; yasal ibare olduğunu söyle, gerekirse tespit modunda “bedelsiz” teriminin müşteri için açıklanabileceğini not et.
5. **Risk uyarısı — asla silinmez.** Fon tanıtımının sonundaki “Burada yer alan yatırım bilgi, yorum ve tavsiyeleri yatırım danışmanlığı kapsamında değildir.” cümlesi metin ne kadar sadeleşirse sadeleşsin aynen kalır.
6. **Yatırım reklamı — yasak vaat.** “Garantili getiri sunan yeni fonumuzla risksiz kazanç sizi bekliyor! Bu fırsatı kaçırmayın!” → Tespit: “garantili getiri”, “risksiz kazanç”, “fırsatı kaçırmayın” — SPK III-37.1 açısından riskli olabilir, uyum birimine sorun. Temizle modunda vaat çıkar, kalan öz korunur: “Yeni fonumuz.” ya da metin kullanıcıya geri verilir. Asla: yerine yeni vaat (“yüksek getiri”) ya da metinde olmayan çağrı (“Yeni fonumuzu inceleyin”) koymak.
7. **Geçmiş getiri — uyarı kalır.** “Fonumuz son 12 ayda %38 getiri sağladı. Geçmiş getiri gelecek getirinin göstergesi değildir.” → ilk cümle sadeleşebilir, rakam ve dönem kalır; ikinci cümle aynen kalır.
8. **İç yazışma — plaza dili.** “Q4 cash flow'u forecast'leyip P&L'e reflect edelim; EBITDA marjını da approve almadan paylaşmayalım.” → “4. çeyreğin nakit akışını tahmin edip gelir tablosuna yansıtalım; EBITDA marjını da onay almadan paylaşmayalım.” Asla: EBITDA'yı FAVÖK'e (ya da tersine) çevirmek.
9. **Katılım bankası — terim karışmaz.** “Katılma hesabınıza 4.512,30 TL kâr payı tahakkuk etmiştir.” → “Katılma hesabınıza 4.512,30 TL kâr payı işledi.” Asla: “kâr payı”nı “faiz” yapmak.
10. **Sigorta bildirimi — bilgi düşmez.** “Poliçenizde 5.000 TL muafiyet bulunmakta olup bu tutarın altındaki hasarlar tarafınızca karşılanacaktır.” → “Poliçenizde 5.000 TL muafiyet var; bu tutarın altındaki hasarları siz ödersiniz.” (Tutarı ikinci kez yazmak sayı denetimini bozar.) Asla: muafiyet tutarını ya da koşulu atmak.
11. **Kanıtsız performans iddiası — işaretle.** “Fonumuz, uzman portföy yöneticilerimizin özenli çalışmalarıyla istikrarlı bir performans sergilemektedir.” → övgü daralır (“Fonumuz … performans gösteriyor” gibi) ve “istikrarlı performans” ayrıca işaretlenir: dayanak (dönem, oran) yoksa TBB ilkesi açısından abartılı/yanıltıcı olabilir. Asla: iddiayı olduğu gibi işaretsiz bırakmak ya da rakam uydurmak.
12. **Bilgisiz kapanış — atılır.** “Kredinizin yıllık maliyet oranı %52,80 olarak hesaplanmış olup tarafınıza bilgi verilmektedir.” → “Kredinizin yıllık maliyet oranı %52,80.” “Bilgi verilmektedir / Bilgilerinize sunarız” bilgi birimi değildir; yerine “Sizi bilgilendiriyoruz” gibi yeni bir dolgu konmaz.
