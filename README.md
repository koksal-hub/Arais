# YouTube Otomasyon Platformu

Bu proje, YouTube kanal operasyonlarını uçtan uca yöneten modüler bir otomasyon iskeletidir. OAuth 2.0 kimlik doğrulamasından video yüklemeye, zamanlama, yorum yönetimi, analiz, bildirim ve çoklu platform paylaşımına kadar tüm bileşenler test odaklı şekilde tasarlanmıştır.

## Dizim

```
/app
  api/            # FastAPI router'ları
  core/           # yapılandırma, logging, retry yardımcıları
  jobs/           # zamanlama ve iş akışları
  models/         # SQLModel veri şemaları
  repo/           # veri erişim katmanı
  services/       # domain servisleri
  tests/          # pytest senaryoları
  ui/             # FastAPI templates
```

## Başlangıç

1. Sanal ortam oluşturup bağımlılıkları kurun (ağ erişimi gerektirir):
   ```bash
   make init
   ```
2. Testleri çalıştırın:
   ```bash
   make test
   ```
3. Uygulamayı başlatın:
   ```bash
   make run
   ```

> Not: Ağ kısıtlamaları olan ortamlarda `make init` başarısız olabilir. Bu durumda gerekli paketleri manuel olarak sağlamanız gerekir.

## Öne Çıkan Modüller

- **M000 – Altyapı**: FastAPI, yapılandırma yönetimi, sağlık uç noktası ve SQLModel tabanlı veritabanı.
- **M010 – OAuth & Kimlik Doğrulama**: Cihaz akışı, token yenileme ve kota yönetimi.
- **M020 – Video Yükleme**: Meta doğrulama, dry-run, yükleme kuyruğu ve hata/geri alınma mekanizması.
- **M030 – Takvim & Zamanlama**: Apscheduler tabanlı video yayın tetikleyici.
- **M040 – Yorum Yönetimi**: Spam tespiti, filtreleme ve otomatik yanıt kuyruğu.
- **M050 – Analitik & Dashboard**: Mock YouTube Analytics istemcisi, snapshot depolama, FastAPI + Jinja2 arayüzü.
- **M060 – Bildirimler**: E-posta/Slack kanalına eşik bazlı uyarılar, hata bildirimi.
- **M070+ – Genişletmeler**: A/B testleri, altyazı yönetimi, içerik üretim asistanı, sponsorluk takibi, çoklu kanal desteği ve platformlar arası paylaşım.

## Test Stratejisi

Tüm servisler pytest ile kapsanmıştır. `app/tests/conftest.py` her test için veritabanını temizler. Modüller arası uçtan uca akışlar için `Mock` YouTube istemcileri kullanılır.

## Çevresel Değişkenler

`.env.example` dosyası örnek değerleri içerir. En azından `DATABASE_URL`, `APP_NAME`, `SLACK_WEBHOOK_URL` değişkenlerini özelleştirin.

## Hızlı Demo

1. `ContentAssistantService` ile anahtar kelime bazlı başlık/etiket önerisi alın.
2. `VideoUploadService` ile plan oluşturup dry-run çalıştırın.
3. `PlanScheduler.process_due_plans()` ile zamanlanmış videoyu yayınlayın.
4. `AnalyticsService.collect_snapshot()` çağrısıyla performans verisini kaydedin.
5. `NotificationService.evaluate_metric()` ile eşik aşımlarında uyarı gönderin.

Bu iskelet, gerçek YouTube API anahtarlarıyla genişletilmeye hazırdır ve modüler yapısı sayesinde yeni özellikler kolayca entegre edilebilir.
