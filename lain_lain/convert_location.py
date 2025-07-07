from helper.db_utils import get_db_connection
import csv, re, mysql.connector, os

# jika error buat ulang tabel dan kolomnya tanpa tambahan index dll (hanya primary id)

# Fungsi bantu
def clean_name(name):
    match = re.match(r'^(.*?)\s*\(.*?\)', name)
    return match.group(1).strip().upper() if match else name.strip().upper()

def remove_dots(id_str):
    return int(id_str.replace('.', ''))

# Path input
BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
DATA_DIR = os.path.join(BASE_DIR, "arsip", "alifbint_indonesia-38-provinsi")
# Definisikan path file CSV
desa_file = os.path.join(DATA_DIR, "kelurahan.csv")
kecamatan_file = os.path.join(DATA_DIR, "kecamatan.csv")
kabupaten_file = os.path.join(DATA_DIR, "kabupaten_kota.csv")
provinsi_file = os.path.join(DATA_DIR, "provinsi.csv")

# Connect to DB
conn = get_db_connection()
cursor = conn.cursor()

# Kosongkan tabel
print("Menghapus isi tabel...")
for table in ['list_desa', 'list_kecamatan', 'list_kabupaten', 'list_provinsi']:
    cursor.execute(f"DELETE FROM {table}")
    cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")  # Reset Auto Increment
conn.commit()

# Memasukkan data Provinsi
print("Memasukkan provinsi...")
try:
    with open(provinsi_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        count = 0
        for row in reader:
            id_str, name = row
            id_clean = int(id_str)
            name_clean = clean_name(name)
            cursor.execute("INSERT INTO list_provinsi (id, nama_provinsi) VALUES (%s, %s)", (id_clean, name_clean))
            print(f"Provinsi - ID: {id_clean}, Name: {name_clean}")
            # count += 1
            # if count == 3:  # Limit 3 data
            #     break
except mysql.connector.Error as err:
    print(f"Error: {err}")
    conn.rollback()
    conn.commit()
    cursor.close()
    conn.close()

# Memasukkan data Kabupaten
print("Memasukkan kabupaten...")
try:
    with open(kabupaten_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        count = 0
        for row in reader:
            id_str, name = row
            id_clean = remove_dots(id_str)
            id_prov = int(str(id_clean)[:2])  # Ambil 2 digit pertama sebagai id_provinsi
            name_clean = clean_name(name)
            cursor.execute("INSERT INTO list_kabupaten (id, id_provinsi, nama_kabupaten) VALUES (%s, %s, %s)", (id_clean, id_prov, name_clean))
            print(f"Kabupaten - ID: {id_clean}, ID Provinsi: {id_prov}, Name: {name_clean}")
            # count += 1
            # if count == 3:  # Limit 3 data
            #     break
except mysql.connector.Error as err:
    print(f"Error: {err}")
    conn.rollback()
    conn.commit()
    cursor.close()
    conn.close()

# Memasukkan data Kecamatan
print("Memasukkan kecamatan...")
try:
    with open(kecamatan_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        count = 0
        for row in reader:
            id_str, name = row
            id_clean = remove_dots(id_str)
            id_kab = int(str(id_clean)[:4])  # Ambil 4 digit pertama sebagai id_kabupaten
            name_clean = clean_name(name)
            cursor.execute("INSERT INTO list_kecamatan (id, id_kabupaten, nama_kecamatan) VALUES (%s, %s, %s)", (id_clean, id_kab, name_clean))
            print(f"Kecamatan - ID: {id_clean}, ID Kabupaten: {id_kab}, Name: {name_clean}")
            # count += 1
            # if count == 3:  # Limit 3 data
            #     break
except mysql.connector.Error as err:
    print(f"Error: {err}")
    conn.rollback()
    conn.commit()
    cursor.close()
    conn.close()

# Memasukkan data Desa
print("Memasukkan desa...")
try:
    with open(desa_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        count = 0
        for row in reader:
            id_str, name = row
            id_clean = remove_dots(id_str)
            id_kec = int(str(id_clean)[:6])  # Ambil 6 digit pertama sebagai id_kecamatan
            name_clean = clean_name(name)
            cursor.execute("INSERT INTO list_desa (id, id_kecamatan, nama_desa) VALUES (%s, %s, %s)", (id_clean, id_kec, name_clean))
            print(f"Desa - ID: {id_clean}, ID Kecamatan: {id_kec}, Name: {name_clean}")
            # count += 1
            # if count == 3:  # Limit 3 data
            #     break
except mysql.connector.Error as err:
    print(f"Error: {err}")
    conn.rollback()
    conn.commit()
    cursor.close()
    conn.close()

conn.commit()
cursor.close()
conn.close()
print("✅ Semua data berhasil dimasukkan.")
