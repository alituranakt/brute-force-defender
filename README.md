# Brute-Force Defender

[![CI](https://img.shields.io/github/actions/workflow/status/alituranakt/brute-force-defender/ci.yml?branch=main&label=tests&logo=githubactions&logoColor=white)](https://github.com/alituranakt/brute-force-defender/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](./pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](./docker-compose.yml)
[![Docs](https://img.shields.io/badge/docs-available-22c55e)](./docs)

<p align="right">
  <img width="28" height="28" alt="Istinye University logo" src="https://github.com/user-attachments/assets/f1433eee-5c4d-458d-b7cd-b1a26e1c9d3b" />
</p>

## BLAKE3 Salting and Brute-Force Defense Demonstration

**Tersine Muhendislik Dersi - Vize Projesi**

Bu proje, BLAKE3 kullanarak salt'siz ve salt'li sifre saklama yaklasimlarini karsilastirir. Amac, rainbow table, dictionary attack ve brute-force senaryolarinda salting kullaniminin neden kritik oldugunu kod, test, CLI demo, Flask API, Docker ve CI/CD ile birlikte gostermektir.

## 🎬 Demo

![Project Demo Video](./demo/project-demo.webp)

## Ozet

- `main.py`: CLI tabanli demo ve benchmark akisi
- `app.py`: JWT korumali Flask API
- `src/`: hashing, salting, saldiri simulasyonu, benchmark ve gorsellestirme modulleri
- `tests/`: unit testler
- `docs/RAPOR.md`: ders icin detayli analiz raporu
- `install.sh` / `uninstall.sh`: kurulum ve temiz kaldirma scriptleri
- `Dockerfile` / `docker-compose.yml`: container tabanli calistirma
- `.github/workflows/ci.yml`: otomatik test ve kalite kontrolu

## Proje Yapisi

```text
brute-force-defender/
|-- app.py
|-- main.py
|-- requirements.txt
|-- setup.py
|-- pyproject.toml
|-- .env.example
|-- Dockerfile
|-- docker-compose.yml
|-- install.sh
|-- uninstall.sh
|-- src/
|   |-- hasher.py
|   |-- database.py
|   |-- attacker.py
|   |-- benchmark.py
|   `-- visualizer.py
|-- tests/
|   |-- test_hasher.py
|   |-- test_attacker.py
|   `-- test_database.py
|-- docs/
|   `-- RAPOR.md
`-- results/
```

## Hangi Problemi Cozuyor?

Salt kullanilmadiginda:

- ayni sifre her zaman ayni hash'i uretir
- ayni sifreyi kullanan hesaplar tespit edilebilir
- rainbow table ile toplu saldiri kolaylasir
- bir hedefte bulunan sifre baska kullanicilara da uygulanabilir

Salt kullanildiginda:

- her kullanici icin hash benzersizlesir
- rainbow table tekrar kullanimi anlamsizlasir
- saldirgan her hedef icin ayri hesaplama yapmak zorunda kalir

## Kurulum

### Gereksinimler

- Python 3.8+
- pip

### Hizli Baslangic

```bash
git clone https://github.com/alituranakt/brute-force-defender.git
cd brute-force-defender
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Windows icin sanal ortam aktivasyonu:

```powershell
venv\Scripts\activate
```

## Ortam Degiskenleri

Repo artik `.env.example` ile gelir. Yerelde `.env` olusturup asagidaki degerleri kullanabilirsin:

```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=0
FLASK_PORT=5000
JWT_SECRET_KEY=change-this-secret-in-production
JWT_EXPIRATION_HOURS=24
DATABASE_PATH=data/users.json
SALT_LENGTH=16
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

Not: `app.py` ortam degiskenlerini `.env` icinden de yukler.

## Kullanim

### CLI demolari

```bash
python main.py
python main.py --demo 1
python main.py --demo 3
python main.py --benchmark
python main.py --interactive
```

### Flask API

```bash
python app.py
```

Temel endpointler:

- `POST /api/register`
- `POST /api/login`
- `GET /api/profile`
- `POST /api/hash`
- `POST /api/demo/attack`
- `GET /api/benchmark`
- `GET /health`

## Docker

```bash
docker compose up --build
```

Ek compose profilleri:

```bash
docker compose --profile demo run --rm demo
docker compose --profile test run --rm test
```

## Testler

```bash
python -m pytest tests/ -v
python -m unittest discover tests/ -v
```

## Uretilen Ciktilar

Calisma sonunda `results/` altinda su artefaktlar uretilir:

- `attack_comparison.png`
- `rainbow_table_effect.png`
- `blake3_vs_sha256.png`
- `salt_length_impact.png`
- `crack_time_estimation.png`
- `same_password_hashes.png`
- `all_results.json`

## Dokumantasyon

- [Analiz raporu](./docs/RAPOR.md)
- [Kurulum scripti](./install.sh)
- [Temizlik scripti](./uninstall.sh)

## Repo Profesyonelligi

- `.gitignore` mevcut
- `.gitattributes` mevcut
- `.env.example` mevcut
- `.editorconfig` mevcut
- `pyproject.toml` mevcut
- Docker dosyalari mevcut
- CI workflow mevcut
- Docs klasoru mevcut
- License mevcut

## Lisans

Bu proje [MIT License](./LICENSE) altinda yayinlanmistir.

## Etik Not

Bu repository egitsel ve akademik amaclidir. Buradaki brute-force ve saldiri simulasyonlari yalnizca yerel, kontrollu ve izinli ortamlarda kullanilmalidir.
