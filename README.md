# ULTRA Finans Ajanı

Windows masaüstünde çalışan; kripto ve ileride borsa verilerini aynı çatı altında izleyen, dar görevli uzman ajanlar, bağımsız risk motoru, teknik laboratuvar ve sanal işlem sistemi kullanan araştırma uygulaması.

> **v0.2 yalnızca analiz, backtest ve sanal işlem içindir.** Gerçek emir, kaldıraç, vadeli işlem ve para çekme yetkisi yoktur.

## v0.2 ile gelenler

- Binance halka açık API üzerinden 1 saatlik OHLCV mumları
- İnternet yoksa açıkça işaretlenen deterministik demo veri
- SMA20/50, EMA12/26, RSI14, MACD, ATR14 ve Bollinger Bantları
- Hacim oranı, destek/direnç ve matematiksel mum formasyonları
- Teknik, rejim, hacim ve risk ajanlarından oluşan Ajanlar Kurulu
- Yüksek ATR oynaklığında bağımsız işlem engeli
- SQLite mum, karar, sanal emir ve backtest kayıtları
- 1.250 TL kripto ve 10.000 TL Borsa İstanbul sanal hesapları
- Komisyon ve kayma içeren, sonraki mum açılışında işlem yapan backtest
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

## Güvenlik anayasası

1. Gerçek emir kapalıdır.
2. API anahtarı istenmez ve kodda tutulmaz.
3. Yapay zekâ veya haber ajanı doğrudan emir gönderemez.
4. Her yeni pozisyon bağımsız risk motorundan geçer.
5. Ağ/veri hatasında sistem demo modunu açıkça gösterir.
6. Komisyon, spread ve kayma sonuçlardan saklanmaz.
7. Backtest, aynı mumun kapanış sinyalini aynı mumda işleme sokmaz.
8. İlk hedef yüksek kâr değil; tekrar üretilebilir, denetlenebilir ve sermayeyi koruyan sistemdir.

## Sonraki kapı: v0.3

- Çoklu zaman dilimi
- Walk-forward deney yöneticisi
- Strateji şampiyon/adayı karşılaştırması
- Günlük zarar ve ardışık kayıp kayıtlarının otomatik hesaplanması
- KAP ve BIST veri katmanı
- Bilimsel makale kütüphanesi ve deney kartları
