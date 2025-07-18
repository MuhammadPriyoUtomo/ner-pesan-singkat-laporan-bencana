# 🧠 Informasi

Program ini dikembangkan sebagai bagian dari tugas akhir (skripsi) dengan judul:

**“PERBANDINGAN ALGORITMA JARO-WINKLER, BERT DAN SPACY PADA EKSTRAKSI PESAN SINGKAT WHATSAPP UNTUK MITIGASI BENCANA”**  
Program Studi Informatika, Fakultas Teknologi Informasi dan Sains Data,  
Universitas Sebelas Maret – Tahun 2025

Penulis: **Muhammad Priyo Utomo** (NIM: M0518036)

Link Skripsi: https://digilib.uns.ac.id/dokumen/detail/125086/PERBANDINGAN-ALGORITMA-JARO-WINKLER-BERT-DAN-SPACY-PADA-EKSTRAKSI-PESAN-SINGKAT-WHATSAPP-UNTUK-MITIGASI-BENCANA

# 🧠 Data Model, File Hasil Penelitian, File SQL

- https://huggingface.co/utomomuhammadpriyo/ner-pesan-singkat-laporan-bencana/
- https://huggingface.co/datasets/utomomuhammadpriyo/dataset-ner-pesan-singkat-laporan-bencana/

# Petunjuk Installasi

- Petunjuk installasi dapat dilihat pada file "petunjuk.txt"
- Untuk melakukan scraping web, pastikan nomor default yang digunakan di WhatsApp sudah dipin.

## Konfigurasi Environment

Buat file `.env` di root project dengan isi seperti berikut:

```env
# Secret key Flask
SECRET_KEY=a_random_and_secure_secret_key_12345

# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=8111
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=skripsi_m0518036_muhammad-priyo-utomo

# WhatsApp
# misal +62 812-3456-7890
DEFAULT_NUMBER=+62 8XX-XXXX-XXXX
