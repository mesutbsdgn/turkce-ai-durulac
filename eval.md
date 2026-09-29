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
- Uzunluk anlamsız çökmedi mi; “Ne değiştirdim” listesine uzunluk (X→Y kelime) satırını ekledim mi?
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

## Tespit modu çıktı şablonu

Her bulgu: **[kalıp adı]** · “<alıntı>” · düzeltme yönü. Sonda: kaç kalıp / metin uzunluğu ve “tek kalıp kanıt değildir; yoğunluk anlamlıdır” notu. Yazarlık tahmini yapma.

## Son okuma — Evet/Hayır kapısı

Bu da bir kapıdır: Hayır ise sunma. Şüphedeysen daha az değiştir.

- Düzenlenmiş metin yazarın ağzından, tek ve tutarlı bir sesle doğal duyuluyor mu?
- Her değişiklik anlamı, kanıtı veya okunabilirliği iyileştiriyor mu; hiçbiri akışı ya da registerı bozmuyor mu?
