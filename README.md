# ULTRA Finans Ajanı

Windows masaüstünde çalışan; kripto ve ileride borsa verilerini aynı çatı altında izleyen, dar görevli uzman ajanlar, bağımsız risk motoru, çoklu zaman analizi, sanal işlem ve yeniden üretilebilir araştırma laboratuvarı kullanan uygulama.

> **v0.3 yalnızca analiz, backtest, walk-forward araştırması ve sanal işlem içindir.** Gerçek emir, kaldıraç, vadeli işlem ve para çekme yetkisi yoktur.

## v0.3 ile gelenler

- 1 saatlik ana karar + 4 saatlik rejim doğrulaması
- Zaman dilimleri çelişirse otomatik `BEKLE`
- Dengeli, Muhafazakâr, Momentum ve Tepki adlı dört denetlenebilir strateji adayı
- Her strateji için ayrı gösterge periyotları, eşikler, risk ve işlem maliyetleri
- Yuvarlanan eğitim/test pencereleriyle walk-forward laboratuvarı
- Stratejinin yalnızca geçmiş eğitim penceresinde seçilip sonraki görülmemiş pencerede sınanması
- Araştırma şampiyonu ve meydan okuyan strateji tablosu
- Ortalama/medyan test getirisi, düşüş, pozitif katman, işlem ve sağlamlık puanı
- Eski v0.2 SQLite veritabanını otomatik yükselten şema göçü
- Walk-forward deneylerinin ve lider tablolarının SQLite kaydı
- 10 otomatik çekirdek test

## Önceki çekirdek özellikler

- Binance halka açık API üzerinden OHLCV mumları
- İnternet yoksa açıkça işaretlenen deterministik demo veri
- SMA, EMA, RSI, MACD, ATR, Bollinger, hacim, destek/direnç ve mum formasyonları
- Teknik, rejim, hacim ve risk ajanlarından oluşan kurul
- Komisyon ve kayma içeren, sonraki mum açılışında işlem yapan backtest
- 1.250 TL kripto ve 10.000 TL Borsa İstanbul sanal hesapları
- Acil durdurma, %20 pozisyon sınırı, %25 rezerv ve %65 güven eşiği

## Çalıştırma

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py app.py
```

Bu sürüm yalnızca Python standart kütüphanesini kullanır.

## Testler

```powershell
py -m unittest discover -s tests -v
```

Beklenen sonuç: `Ran 10 tests ... OK`

## Güvenlik anayasası

1. Gerçek emir kapalıdır.
2. API anahtarı istenmez ve kodda tutulmaz.
3. Yapay zekâ veya haber ajanı doğrudan emir gönderemez.
4. 1 saatlik ve 4 saatlik görüşler çelişirse işlem açılmaz.
5. Her yeni pozisyon bağımsız risk motorundan geçer.
6. Komisyon, spread ve kayma sonuçlardan saklanmaz.
7. Backtest aynı mumun kapanış sinyalini aynı mumda işleme sokmaz.
8. Walk-forward stratejiyi eğitim penceresinde seçer, sonraki test penceresinde sınar.
9. “Şampiyon” etiketi gerçek işlem izni değildir; yeni canlı sanal dönemde tekrar doğrulanmalıdır.
10. İlk hedef yüksek kâr değil; tekrar üretilebilir, denetlenebilir ve sermayeyi koruyan sistemdir.

## Sonraki kapı: v0.4

- Günlük sanal otomatik çalışma ve performans günlüğü
- Şampiyon–aday terfi kuralları ve minimum gözlem süresi
- Haber/KAP veri kaynağı güven puanı
- BIST veri adaptörü
- Bilimsel makale deney kartları
- Monte Carlo ve stres testi
