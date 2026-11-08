# Lisans ve kaynak notları

- **Lisans (8 Kasım 2026):** GNU AGPL-3.0'dan kullanım hakkı lisansına geçildi (kullan, kopyalama/dağıtma/değiştirme/eğitim yok). Gerekçe: Durulaç artık bir uygulamaya yerleşik beceri olarak gömülüyor; AGPL, kopyalanıp yeniden dağıtılmasını engellemiyordu ve tescilli uygulamayla ilişkisinde belirsizlik yaratıyordu. Telif hakkı tek sahiptedir (tüm commit'ler mesutbsdgn). Önceki lisanslarla edinilen kopyaların hakları sürer (v1.3'e kadar MIT; 9 Ekim - 8 Kasım 2026 arası AGPL). Üçüncü taraf MIT parçaların bildirimi korunur.

- **Lisans (9 Ekim 2026):** MIT'ten GNU AGPL-3.0'a geçildi. `fe24416` dahil önceki commit'ler (son etiket `v1.3`) MIT ile yayımlanmıştı. MIT lisanslı kaynaklardan uyarlanan parçaların (aşağıda) kendi bildirimi [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) dosyasında korunur.

- Yapı (iki mod, sesi koru/uydurma ilkeleri, "kesilecek kalıplar") petergyang/no-ai-slop (MIT) esinli; İngilizce içerik kopyalanmadı, Türkçeye özgün yazıldı.
- Mekanik eşleme sözlüğü Denomas/Turkce-yazim-denetimi (MIT) Vale kurallarından SEÇİLİP uyarlandı; toptan alınmadı.
- 29 Eyl 2026 Fable 5.1 incelemesinden sonra: TDK'ye aykırı "Deyim yazımı" bölümü tümüyle çıkarıldı; anlam kaydıran ve teknik düzyazıyı bozan ~150 eşleme budandı (görülmektedir→görülüyor, tespit etmek→saptamak, branch/host/commit gibi terim çevirileri kaldırıldı); özdeş eşlemeler silindi; Plaza bölümü "Plaza kalıpları" + "İngilizce terim (isteğe bağlı)" olarak ayrıldı.
- Dil bilgisi/noktalama kuralları TDK yazım kılavuzuna dayanır (tdk.gov.tr). Deyim doğrulaması için sozluk.gov.tr GTS.

Finans eklentisi (3 Ekim 2026): `references/finans-terimleri.md` yapısı sal-keskin/okunabilir (MIT)
deposundaki terim listesinden esinlenmiştir; içerik kopyalanmamış, kamuya açık kurum sözlüklerinden
derlenmiştir. `scripts/okunabilirlik.py` Ateşman (1997) ve Bezirci–Yılmaz (2010) formüllerinin
yayımlanmış hâlinden sıfırdan yazılmıştır (GPL'li atesman-readability kodu kullanılmadı).
