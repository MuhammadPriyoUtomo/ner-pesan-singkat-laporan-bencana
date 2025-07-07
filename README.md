# ner-pesan-singkat-laporan-bencana

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
