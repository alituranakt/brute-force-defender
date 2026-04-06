# Brute-Force Defender

## BLAKE3 Tuzlama (Salting) Mekanizması Demonstrasyonu

**Tersine Mühendislik Dersi - Vize Projesi**

Bu proje, BLAKE3 hash algoritması kullanarak tuzlama (salting) mekanizmasının brute-force saldırılara karşı etkisini gösterir. Şifreleri salt eklemeden açık hash olarak tutarsanız, birisi hızlıca milyon kere deneyerek (brute) bulabilir. Her kullanıcının hash'ine eşsiz tuz (salt) serp ve saldırganın nasıl yavaşladığını izle.

---

## Proje Yapısı

```
brute-force-defender/
├── main.py                  # Ana çalıştırılabilir dosya
├── requirements.txt         # Python bağımlılıkları
├── setup.py                 # Paket kurulum dosyası
├── .gitignore              # Git ignore kuralları
├── README.md               # Bu dosya
├── src/
│   ├── __init__.py
│   ├── hasher.py           # BLAKE3 hash işlemleri (salt'lı/salt'sız)
│   ├── database.py         # Simüle edilmiş kullanıcı veritabanı
│   ├── attacker.py         # Brute-force & sözlük saldırı simülatörü
│   ├── benchmark.py        # Performans ölçüm modülü
│   └── visualizer.py       # Grafik oluşturma modülü (matplotlib)
├── tests/
│   ├── __init__.py
│   ├── test_hasher.py      # Hasher birim testleri
│   ├── test_attacker.py    # Attacker birim testleri
│   └── test_database.py    # Database birim testleri
├── results/                # Çıktı grafikleri ve JSON raporları
└── docs/                   # Ek dokümantasyon
```

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- pip paket yöneticisi

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/KULLANICI_ADINIZ/brute-force-defender.git
cd brute-force-defender

# 2. Sanal ortam oluştur (önerilir)
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Bağımlılıkları kur
pip install -r requirements.txt

# 4. Projeyi çalıştır
python main.py
```

## Kullanım

### Tüm Demoları Çalıştır

```bash
python main.py
```

### Belirli Bir Demo

```bash
python main.py --demo 1    # Hash Temelleri ve Salt Mekanizması
python main.py --demo 2    # Kullanıcı Veritabanı Simülasyonu
python main.py --demo 3    # Saldırı Simülasyonu
python main.py --demo 4    # Brute-Force Saldırı (Kısa Şifreler)
python main.py --demo 5    # Benchmark ve Görselleştirme
```

### Sadece Benchmark

```bash
python main.py --benchmark
```

### İnteraktif Mod

```bash
python main.py --interactive
```

### Testleri Çalıştır

```bash
python -m pytest tests/ -v
# veya
python -m unittest discover tests/ -v
```

## Demo İçerikleri

### Demo 1: BLAKE3 Hash Temelleri

- Temel BLAKE3 hash oluşturma
- Salt'sız hash'lerin deterministic (belirleyici) doğası
- Salt'lı hash'lerin her seferinde farklı çıktı üretmesi
- BLAKE3 keyed hash (HMAC alternatifi)

### Demo 2: Veritabanı Simülasyonu

- 8 demo kullanıcı ile gerçekçi veritabanı simülasyonu
- Salt'sız tabloda aynı şifre = aynı hash problemi
- Salt'lı tabloda her hash'in benzersiz olması
- Duplicate hash tespiti ve güvenlik analizi

### Demo 3: Saldırı Simülasyonu

- **Sözlük Saldırısı**: 40 yaygın şifre ile salt'lı vs salt'sız karşılaştırma
- **Rainbow Table Saldırısı**: Önceden hesaplanmış hash tablosu ile anlık eşleşme
- **Çoklu Kullanıcı Saldırısı**: Rainbow table'ın salt'sız hash'ler için yıkıcı etkisi
- Salt'ın çoklu kullanıcı senaryolarında saldırganı nasıl yavaşlattığı

### Demo 4: Brute-Force Saldırı

- Kısa şifreler (3 karakter) üzerinde kaba kuvvet saldırısı
- Tüm olası kombinasyonların denenmesi
- Salt'lı ve salt'sız hash kırma süresi karşılaştırması

### Demo 5: Benchmark ve Görselleştirme

- Hash hızı ölçümü (100,000 iterasyon)
- BLAKE3 vs SHA-256 performans karşılaştırması
- Salt uzunluğunun güvenlik ve performansa etkisi
- Şifre kırma süresi projeksiyonları (3-8 karakter)
- Otomatik grafik oluşturma (`results/` dizinine)

## Temel Kavramlar

### BLAKE3 Nedir?

BLAKE3, 2020 yılında yayınlanan modern bir kriptografik hash fonksiyonudur. SHA-256'ya göre çok daha hızlıdır ve paralel işleme desteği sunar. 256-bit çıktı üretir ve Merkle tree yapısında çalışır.

### Salt (Tuz) Nedir?

Salt, her kullanıcı için oluşturulan rastgele bir byte dizisidir. Şifre hash'lenmeden önce şifreye eklenir, böylece aynı şifre farklı hash değerleri üretir.

### Neden Salt Kullanılmalı?

1. **Rainbow Table Koruması**: Önceden hesaplanmış hash tabloları etkisiz hale gelir
2. **Aynı Şifre Gizleme**: Aynı şifreyi kullanan kullanıcılar tespit edilemez
3. **Çoklu Hedef Koruması**: Saldırgan her kullanıcı için ayrı saldırı yapmak zorundadır

### Salt'sız Hash Riskleri

- Rainbow table ile anlık kırılma (O(1) arama)
- Bir şifreyi bulunca aynı şifreyi kullanan TÜM kullanıcılar ele geçirilir
- Aynı hash'e bakarak hangi kullanıcıların aynı şifreyi kullandığı tespit edilir

## Çıktı Grafikleri

Proje çalıştırıldığında `results/` dizinine aşağıdaki grafikler oluşturulur:

| Dosya | Açıklama |
|-------|----------|
| `attack_comparison.png` | Salt'lı vs Salt'sız saldırı süresi |
| `rainbow_table_effect.png` | Rainbow table'ın çoklu kullanıcılardaki etkisi |
| `blake3_vs_sha256.png` | BLAKE3 ve SHA-256 performans karşılaştırması |
| `salt_length_impact.png` | Salt uzunluğunun güvenlik etkisi |
| `crack_time_estimation.png` | Şifre kırılma süresi projeksiyonu |
| `same_password_hashes.png` | Aynı şifrenin farklı hash üretmesi |
| `all_results.json` | Tüm sonuçların JSON formatında kaydı |

## Teknik Detaylar

### Kullanılan Kütüphaneler

| Kütüphane | Versiyon | Kullanım |
|-----------|----------|----------|
| blake3 | >=1.0.0 | BLAKE3 hash hesaplama |
| matplotlib | >=3.5.0 | Grafik oluşturma |
| colorama | >=0.4.6 | Renkli terminal çıktısı |
| tabulate | >=0.9.0 | Tablo formatlama |

### Hash Algoritma Detayları

- **BLAKE3**: 256-bit çıktı, Merkle tree tabanlı, paralel işleme destekli
- **Salt Uzunluğu**: Varsayılan 16 byte (128-bit), konfigüre edilebilir
- **Salt Üretimi**: `os.urandom()` - CSPRNG (Kriptografik olarak güvenli rastgele sayı üreteci)

## Lisans

Bu proje eğitim amaçlıdır. Tersine Mühendislik dersi vize projesi kapsamında hazırlanmıştır.

## Etik Uyarı

Bu proje yalnızca eğitim ve akademik amaçlarla geliştirilmiştir. Brute-force saldırıları izinsiz sistemlere karşı kullanmak yasadışıdır. Tüm simülasyonlar yerel ortamda ve sahte verilerle gerçekleştirilmiştir.
<img width="28" height="28" alt="download" src="https://github.com/user-attachments/assets/f1433eee-5c4d-458d-b7cd-b1a26e1c9d3b" />

