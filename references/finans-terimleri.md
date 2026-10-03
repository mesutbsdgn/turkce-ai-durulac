# Finans terimleri — sade karşılık ve dokunma listesi

Durulaç finans metninde bu tabloya bakar. Üç durum var:

- **AYNEN**: Yasal ya da sözleşmesel terimdir. Sözcüğü değiştirme. Müşteri metninde gerekiyorsa
  ilk geçtiği yerde parantez içinde kısa açıklama ekle: "yıllık maliyet oranı (kredinin faiz,
  vergi ve masraflar dâhil yıllık toplam maliyeti)". Açıklama terimin yerine geçmez.
- **SADE**: Müşteriye giden metinde sade karşılığı kullan. Sözleşme, KAP açıklaması ve yasal
  bildirimde ise aynen bırak (tür kapısı: yasal ibare).
- **TR**: İç yazışmadaki plaza İngilizcesi; Türkçe karşılığı kullan.

Kaynak notu: Karşılıklar Claude tarafından TCMB, SPK ve TBB'nin herkese açık sözlük ve mevzuat
metinlerindeki kullanımdan derlenmiştir (TCMB: https://www.tcmb.gov.tr ; SPK: https://spk.gov.tr ; TBB: https://www.tbb.org.tr). Satır satır kaynak eşlemesi yoktur; bir karşılığı
resmî belgede kullanmadan önce kurum sözlüğüyle karşılaştır; GitHub'da olgun bir Türkçe finans sözlüğü yoktur. Yapı fikri
[`sal-keskin/okunabilir`](https://github.com/sal-keskin/okunabilir) (MIT) deposundaki sağlık terimleri
listesinden alınmıştır; içerik kopyalanmamıştır.
Bir terimden emin değilsen AYNEN say ve kullanıcıya sor.

## Kredi, kart, mevduat

| Terim | Sade karşılık / açıklama | Durum |
|---|---|---|
| yıllık maliyet oranı (YMO) | faiz, vergi ve masraflar dâhil yıllık toplam maliyet | AYNEN |
| akdi faiz | sözleşme faizi (gecikme faizinden ayrı tutulmalı; ikisini "faiz" diye birleştirme) | SADE |
| gecikme faizi | gecikme faizi (zaten sade) | AYNEN |
| KKDF (Kaynak Kullanımını Destekleme Fonu) | kredi faizinden alınan fon kesintisi | AYNEN |
| BSMV (Banka ve Sigorta Muameleleri Vergisi) | banka işlemlerinden alınan vergi | AYNEN |
| asgari ödeme tutarı | en az ödemeniz gereken tutar | SADE |
| hesap kesim tarihi | hesap özetinin hazırlandığı gün | SADE |
| son ödeme tarihi | son ödeme günü (zaten sade) | AYNEN |
| hesap özeti / ekstre | hesap özeti ("ekstre" yerine) | SADE |
| tahakkuk etmek / tahakkuk ettirilmek | işlemek, hesaba eklenmek | SADE |
| yansıtılmak (hesaba) | eklenmek | SADE |
| dönem borcu | bu ayki borcunuz | SADE |
| nakit avans | karttan çekilen nakit (terim kalabilir, ilk geçişte açıkla) | AYNEN |
| erken ödeme tazminatı / erken kapama ücreti | krediyi erken kapatırsanız ödediğiniz ücret | AYNEN |
| kredi tahsis ücreti / dosya masrafı | kredi açılış ücreti | AYNEN |
| temerrüt | ödemenin gecikmesi, borcun ödenmemesi | SADE (sözleşmede AYNEN) |
| muacceliyet / muaccel hâle gelmek | kalan borcun tamamının hemen ödenmesi gerekmesi | SADE (sözleşmede AYNEN) |
| kefil / müteselsil kefil | kefil · borçla birlikte sorumlu kefil | AYNEN |
| rehin / ipotek | rehin · ipotek (açıklama eklenebilir) | AYNEN |
| vadesiz / vadeli mevduat | istediğiniz an çekebileceğiniz / belli süre bağlı kalan hesap | AYNEN |
| mevduat sigortası (TMSF kapsamı) | TMSF'nin mevzuattaki kapsam ve tutar sınırı içinde güvence altına aldığı mevduat; "devlet tüm paranızı korur" deme | AYNEN |
| kâr payı (katılım bankacılığı) | kâr payı; "faiz" diye ÇEVİRME | AYNEN |
| stopaj | kaynakta kesilen vergi | SADE (vergi belgesinde AYNEN) |
| ödenmemiş bakiye | kalan borç | SADE |
| limit tahsisi | limit tanımlanması | SADE |
| ibraz etmek | göstermek, vermek | SADE |
| keşide etmek (çek) | çek yazmak | SADE (çek mevzuatında AYNEN) |

## Yatırım ve sermaye piyasası

| Terim | Sade karşılık / açıklama | Durum |
|---|---|---|
| yatırım danışmanlığı kapsamında değildir (uyarı) | zorunlu uyarı metni | AYNEN, asla silinmez |
| risk bildirim formu | risk bildirim formu | AYNEN |
| yatırım fonu / borsa yatırım fonu (BYF) | yatırım fonu · borsada işlem gören fon | AYNEN |
| getiri | kazanç (yalnız müşteri pazarlama metninde; rakamla birlikte "getiri" kalabilir) | SADE |
| geçmiş getiri | önceki dönem kazancı; yanında "gelecek getirinin göstergesi değildir" uyarısı kalır | AYNEN |
| volatilite / oynaklık | fiyatın ne kadar sert inip çıktığı | SADE |
| likidite | nakde çevirme kolaylığı | SADE |
| kaldıraç | borçla işlem; kazancı da zararı da büyütür | SADE (açıklama zorunlu) |
| teminat tamamlama çağrısı (margin call) | hesaba ek teminat yatırma çağrısı | SADE |
| temettü | kâr payı (hisse için) | AYNEN |
| bedelli / bedelsiz sermaye artırımı | para karşılığı / ücretsiz yeni pay | AYNEN (KAP'ta) |
| içsel bilgi, piyasa dolandırıcılığı | — | AYNEN |
| özel durum açıklaması | şirketin KAP'a bildirdiği önemli gelişme | AYNEN |

## Sigorta

| Terim | Sade karşılık / açıklama | Durum |
|---|---|---|
| poliçe | sigorta sözleşmesi (poliçe kalabilir) | AYNEN |
| prim | sigorta ücreti | SADE (poliçede AYNEN) |
| muafiyet | hasarın sizin ödediğiniz kısmı | SADE (poliçede AYNEN) |
| teminat | sigortanın karşıladığı durum ve tutar | AYNEN |
| rücu | sigortacının ödediği tutarı sorumludan geri istemesi | SADE (poliçede AYNEN) |
| hasar ihbarı | hasarı bildirmek | SADE |
| sigortalı / sigorta ettiren | — | AYNEN (ikisi farklı kişi olabilir) |

## Muhasebe ve iç rapor

| Terim | Karşılık | Durum |
|---|---|---|
| EBITDA / FAVÖK | yerleşik kısaltma; metinde hangisi geçiyorsa o kalır, birini ötekine çevirme | AYNEN |
| KDV, ÖTV, SGK, e-Fatura | yerleşik kısaltma | AYNEN |
| bilanço, gelir tablosu, nakit akış tablosu | — | AYNEN |
| cash flow | nakit akışı | TR |
| forecast(lemek) | tahmin (etmek) | TR |
| budget(lamak) | bütçe (ayırmak) | TR |
| revenue | gelir, ciro | TR |
| margin | kâr marjı | TR |
| run-rate | bugünkü hızla yıllık tutar | TR |
| burn rate | aylık nakit harcaması | TR |
| P&L | gelir tablosu, kâr-zarar | TR |
| YoY / MoM | geçen yıla göre / geçen aya göre | TR |
| closing yapmak | dönem kapanışı yapmak | TR |
| reconcile etmek | mutabakat yapmak, hesapları eşleştirmek | TR |
| approve almak | onay almak | TR |
| reflect etmek | yansıtmak | TR |
| Q1–Q4 | 1.–4. çeyrek | TR |
| accrual | tahakkuk (iç raporda muhasebe terimi olarak kalır) | TR |
| write-off | kayıttan düşme, silme | TR |
| capex / opex | yatırım harcaması / işletme gideri | TR |

## Asla değiştirilmeyenler (her finans türünde)

- **Rakamlar:** tutar, oran, yüzde, tarih, vade, adet. Biçim de korunur: binlik nokta, ondalık
  virgül, `₺`/`TL` yeri, `%` yeri ("1.250,00 TL" → "1.250 TL" bile değişikliktir).
- **Kurum ve ürün adları**, sözleşme ve ürün kodları, IBAN/hesap no'nun gösterilen kısmı.
- **Zorunlu uyarılar ve bildirim cümleleri** (risk uyarısı, "geçmiş getiri gelecek getirinin
  göstergesi değildir", "yatırım danışmanlığı kapsamında değildir", cayma hakkı bildirimi).
- **Şart cümleleri:** "… hâlinde", "… kadar", "… şartıyla" gibi koşul bildiren yapı sadeleşebilir
  ama koşul düşmez. "Ödenmemesi hâlinde %4,25 gecikme faizi uygulanır" → "Ödemezseniz %4,25
  gecikme faizi işler" doğru; koşulu silmek yanlış.

Denetim için: `python3 scripts/okunabilirlik.py once.txt sonra.txt` sayıların aynen kaldığını
kontrol eder; sorun varsa çıkış kodu 1 olur.
