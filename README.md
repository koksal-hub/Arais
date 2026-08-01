# ULTRA Finans Ajanı

Windows masaüstünde çalışan, kripto ve borsa verilerini aynı çatı altında izleyen; uzman ajanlar, bağımsız risk motoru ve sanal işlem sistemi kullanan araştırma uygulaması.

> Bu sürüm yalnızca analiz ve **sanal işlem** içindir. Gerçek emir, kaldıraç ve para çekme yetkisi yoktur.

## v0.1 hedefi

- Binance ve BtcTurk halka açık piyasa verilerini okuma
- Verileri SQLite'a kaydetme
- Teknik, rejim ve risk ajanlarının ilk çalışan sürümü
- Sanal portföy ve işlem günlüğü
- Windows masaüstü paneli
- Ağ bağlantısı yoksa güvenli biçimde çevrimdışı kalma

## Çalıştırma

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py app.py
```

Bu ilk sürüm yalnızca Python standart kütüphanesini kullanır.

## Güvenlik anayasası

1. Gerçek emir kapalıdır.
2. API anahtarı istenmez ve kodda tutulmaz.
3. LLM veya haber ajanı doğrudan emir gönderemez.
4. Her öneri bağımsız risk motorundan geçer.
5. Ağ/veri hatasında sistem yeni işlem açmaz.
6. Komisyon, spread ve kayma raporlarda ayrıca izlenir.
7. İlk hedef yüksek kâr değil; tekrarlanabilir ve denetlenebilir bir sistemdir.
