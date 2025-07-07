from datetime import datetime
from helper.db_utils import get_db_dict_connection, get_db_connection
from programs.train_bert_model import convert_to_bio
from transformers import AutoTokenizer
import random, mysql.connector, json, time, os

TOKENIZER_CACHE = {}

def get_tokenizer(model_path):
    if model_path not in TOKENIZER_CACHE:
        TOKENIZER_CACHE[model_path] = AutoTokenizer.from_pretrained(model_path)
    return TOKENIZER_CACHE[model_path]

def fetch_list_from_db(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

# Mengambil data dari tabel MySQL
bencana_list = fetch_list_from_db('list_bencana')
# print(f"bencana_list: {bencana_list}")

def fetch_active_list_from_db(table_name):
    """
    Mengambil data dari tabel yang hanya memiliki status is_active = TRUE.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Query hanya untuk data yang aktif
        cursor.execute(f"SELECT * FROM {table_name} WHERE is_active = TRUE")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

urgensi_list = fetch_active_list_from_db('list_urgensi')
templates_chat = fetch_active_list_from_db('list_template_chat')

def fetch_locations_by_model(model_id, provinsi_ids=None, kabupaten_ids=None, kecamatan_ids=None, desa_ids=None):
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Query dasar
    query = """
    SELECT 
        list_desa.id AS id_desa,
        list_desa.nama_desa,
        list_kecamatan.id AS id_kecamatan,
        list_kecamatan.nama_kecamatan,
        list_kabupaten.id AS id_kabupaten,
        list_kabupaten.nama_kabupaten,
        list_provinsi.id AS id_provinsi,
        list_provinsi.nama_provinsi
    FROM 
        list_desa
    LEFT JOIN list_kecamatan ON list_desa.id_kecamatan = list_kecamatan.id
    LEFT JOIN list_kabupaten ON list_kecamatan.id_kabupaten = list_kabupaten.id
    LEFT JOIN list_provinsi ON list_kabupaten.id_provinsi = list_provinsi.id
    WHERE 1=1
    """

    # Tambahkan filter berdasarkan tingkatan lokasi yang dipilih
    if provinsi_ids:
        query += f" AND list_provinsi.id IN ({','.join(['%s'] * len(provinsi_ids))})"
    if kabupaten_ids:
        query += f" AND list_kabupaten.id IN ({','.join(['%s'] * len(kabupaten_ids))})"
    if kecamatan_ids:
        query += f" AND list_kecamatan.id IN ({','.join(['%s'] * len(kecamatan_ids))})"
    if desa_ids:
        query += f" AND list_desa.id IN ({','.join(['%s'] * len(desa_ids))})"

    # Gabungkan semua parameter
    params = []
    if provinsi_ids:
        params.extend(provinsi_ids)
    if kabupaten_ids:
        params.extend(kabupaten_ids)
    if kecamatan_ids:
        params.extend(kecamatan_ids)
    if desa_ids:
        params.extend(desa_ids)

    cursor.execute(query, params)
    locations = cursor.fetchall()
    cursor.close()
    conn.close()
    return locations

def generate_location_combinations(locations):
    """
    Membuat semua kombinasi lokasi dari tingkatan lokasi yang diberikan.
    """
    combinations = []
    for location in locations:
        desa = location.get('nama_desa', '')
        kecamatan = location.get('nama_kecamatan', '')
        kabupaten = location.get('nama_kabupaten', '')
        provinsi = location.get('nama_provinsi', '')

        # Kombinasi lokasi dalam berbagai urutan
        if desa:
            combinations.append(desa)
        if desa and kecamatan:
            combinations.append(f"{desa}, {kecamatan}")
        if desa and kecamatan and kabupaten:
            combinations.append(f"{desa}, {kecamatan}, {kabupaten}")
        if desa and kecamatan and kabupaten and provinsi:
            combinations.append(f"{desa}, {kecamatan}, {kabupaten}, {provinsi}")
        if kecamatan:
            combinations.append(kecamatan)
        if kecamatan and kabupaten:
            combinations.append(f"{kecamatan}, {kabupaten}")
        if kecamatan and kabupaten and provinsi:
            combinations.append(f"{kecamatan}, {kabupaten}, {provinsi}")
        if kabupaten:
            combinations.append(kabupaten)
        if kabupaten and provinsi:
            combinations.append(f"{kabupaten}, {provinsi}")
        if provinsi:
            combinations.append(provinsi)

    # Hapus duplikasi sambil mempertahankan urutan
    seen = set()
    unique_combinations = []
    for combination in combinations:
        if combination not in seen:
            unique_combinations.append(combination)
            seen.add(combination)

    return unique_combinations

# Fungsi Random lokasi
def generate_random_location(locations):
    if not locations:
        raise ValueError("Locations list is empty or None")
    
    # Pilih lokasi secara acak
    location = random.choice(locations)
    # print(f"Selected location: {location}")
    
    # Tentukan berapa banyak tingkatan lokasi yang akan dihasilkan (1 hingga 4)
    num_levels = random.choice([1, 2, 3, 4])
    
    # Buat list untuk menyimpan tingkatan lokasi yang dipilih
    selected_levels = []
    
    # Tambahkan tingkatan lokasi secara acak berdasarkan num_levels
    if num_levels >= 1:
        selected_levels.append(location.get('nama_desa', '') or '')
    if num_levels >= 2:
        selected_levels.append(location.get('nama_kecamatan', '') or '')
    if num_levels >= 3:
        selected_levels.append(location.get('nama_kabupaten', '') or '')
    if num_levels == 4:
        selected_levels.append(location.get('nama_provinsi', '') or '')
    
    # Gabungkan tingkatan lokasi yang dipilih menjadi satu string
    return ', '.join(filter(None, selected_levels)), location

def process_row(index, locations, templates, is_report, isi_chat_pengaduan=None, training_data=None):
    # Menyimpan hasil random lokasi
    lokasi_tuple = generate_random_location(locations)
    # print(f"\nlokasi_tuple: {lokasi_tuple}\n")
    
    # Mengambil hanya bagian pertama dari tuple lokasi
    lokasi = lokasi_tuple[0]
    annotations = lokasi_tuple[1]
    
    # Pilih bencana, urgensi, dan template secara acak
    bencana = random.choice(bencana_list)[1]  # Akses elemen kedua dari tuple
    # print(f"\nbencana: {bencana}\n")
    urgensi = random.choice(urgensi_list)[1]  # Akses elemen kedua dari tuple
    # print(f"\nurgensi: {urgensi}\n")
    template = random.choice(templates)[1]  # Pilih template dari daftar yang diberikan
    # print(f"\ntemplate: {template}\n")

    # Menghasilkan isi chat atau menggunakan input teks
    if isi_chat_pengaduan:
        isi_chat = isi_chat_pengaduan
    else:
        isi_chat = template.format(bencana=bencana, lokasi=lokasi, urgensi=urgensi)
        # print(f"\nIsi Chat Pengaduan: {isi_chat}\n")
        
    # Anotasi entitas untuk model 1
    entities_model_1 = []
    disaster_start = isi_chat.find(bencana)
    # print(f"\ndisaster_start: {disaster_start}\n")
    if disaster_start != -1:
        disaster_end = disaster_start + len(bencana)
        # print(f"\ndisaster_end: {disaster_end}\n")
        entities_model_1.append((disaster_start, disaster_end, 'DISASTER'))
        # print(f"\nentities_model_1: {entities_model_1}\n")

    # Cocokkan lokasi yang terpilih berdasarkan annotations untuk model 1
    for key, value in annotations.items():
        # print(f"\nkey: {key}, value: {value}\n")
        if "nama_" in key:  # Mengambil key yang berhubungan dengan lokasi
            # print(f"\nkey: {key}\n")
            location_name = value or ""  # Ganti None dengan string kosong
            # print(f"\nlocation_name: {location_name}\n")
            location_entity = annotations.get(f"{key.split('_')[1]}_entities", '')
            # print(f"\nlocation_entity: {location_entity}\n")
            if location_name:  # Pastikan location_name tidak kosong
                location_start = isi_chat.find(location_name)
                # print(f"\nlocation_start: {location_start}\n")
                if location_start != -1:
                    location_end = location_start + len(location_name)
                    # print(f"\nlocation_end: {location_end}\n")
                    entities_model_1.append((location_start, location_end, location_entity))
                    # print(f"\nentities_model_1: {entities_model_1}\n")

    # Anotasi entitas untuk model 2 (gabungkan semua lokasi menjadi satu entitas LOCATION)
    entities_model_2 = []
    location_starts = []
    location_ends = []
    for key, value in annotations.items():
        # print(f"\nkey: {key}, value: {value}\n")
        if "nama_" in key:  # Mengambil key yang berhubungan dengan lokasi
            # print(f"\nkey: {key}\n")
            location_name = value or ""  # Ganti None dengan string kosong
            # print(f"\nlocation_name: {location_name}\n")
            location_start = isi_chat.find(location_name)
            # print(f"\nlocation_start: {location_start}\n")
            
            if location_start != -1:
                location_end = location_start + len(location_name)
                # print(f"\nlocation_end: {location_end}\n")
                location_starts.append(location_start)
                # print(f"\nlocation_starts: {location_starts}\n")
                location_ends.append(location_end)
                # print(f"\nlocation_ends: {location_ends}\n")

    # Gabungkan semua lokasi menjadi satu entitas LOCATION
    if location_starts and location_ends:
        combined_start = min(location_starts)
        # print(f"\ncombined_start: {combined_start}\n")
        combined_end = max(location_ends)
        # print(f"\ncombined_end: {combined_end}\n")
        entities_model_2.append((combined_start, combined_end, 'LOCATION'))
        # print(f"\nentities_model_2: {entities_model_2}\n")

    # Tambahkan data ke format spaCy untuk model 1 dan model 2
    if training_data is not None:
        training_data.append((isi_chat, {"entities": entities_model_1}))
        # print(f"\ntraining_data: {training_data}\n")
        training_data.append((isi_chat, {"entities": entities_model_2}))
        # print(f"\ntraining_data: {training_data}\n")
    
    # Anotasi entitas untuk hasil akhir
    entities = []
    disaster_start = isi_chat.find(bencana)
    # print(f"\ndisaster_start: {disaster_start}\n")
    if disaster_start != -1:
        disaster_end = disaster_start + len(bencana)
        # print(f"\ndisaster_end: {disaster_end}\n")
        entities.append((disaster_start, disaster_end, 'DISASTER'))
        # print(f"\nentities: {entities}\n")
    
    location_start = isi_chat.find(lokasi)
    # print(f"\nlocation_start: {location_start}\n")
    if location_start != -1:
        location_end = location_start + len(lokasi)
        # print(f"\nlocation_end: {location_end}\n")
        entities.append((location_start, location_end, 'LOCATION'))
        # print(f"\nentities: {entities}\n")
    
    # Tentukan report_status
    report_status = "report" if is_report else "bukan report"
    
    # Siapkan data untuk hasil akhir
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')  # Ambil timestamp saat data dihasilkan
    data = {
        "Isi Chat Pengaduan": isi_chat.lower(),
        "annotations": entities,
        "report_status": report_status,  # Tambahkan report_status
        "timestamp": timestamp  # Tambahkan timestamp ke data
    }

    print(f"\nMembuat data: {data}\n")
    
    return data

# Fungsi untuk mengonversi waktu eksekusi menjadi format yang lebih mudah dibaca
def format_execution_time(seconds):
    if seconds < 60:
        return f"{seconds:.2f} detik"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes} menit {remaining_seconds:.2f} detik"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours} jam {remaining_minutes} menit {remaining_seconds:.2f} detik"

def generate_data(source, num_entries=None, model_id=None, text_inputan=None, num_status_reports=None, num_non_reports=None,format_execution_time=format_execution_time):

    if source != "create_model":
        # Mulai Hitung Waktu Eksekusi
        start_time = time.time()

    print(f"generate_data.py")
    print(f"Source: {source}")
    print(f"Jumlah entri: {num_entries}")
    print(f"Model ID: {model_id}")
    print(f"Isi Chat Pengaduan: {text_inputan}")
    print(f"Jumlah status report: {num_status_reports}")
    print(f"Jumlah bukan report: {num_non_reports}")
    
    # Menyimpan DataFrame ke tabel MySQL
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if source == "text_input" or source == "generate_data":
            # Menghapus isi tabel data_olah_asli
            cursor.execute("DELETE FROM data_olah_asli")
            cursor.execute("ALTER TABLE data_olah_asli AUTO_INCREMENT = 1")

            # Menghapus isi tabel hasil_ekstraksi
            cursor.execute("DELETE FROM hasil_ekstraksi")
            cursor.execute("ALTER TABLE hasil_ekstraksi AUTO_INCREMENT = 1")

            # Menghapus isi tabel variabel_global
            cursor.execute("DELETE FROM variabel_global")
            cursor.execute("ALTER TABLE variabel_global AUTO_INCREMENT = 1")
            
            # Menghapus isi tabel evaluation_per_report
            cursor.execute("DELETE FROM evaluation_per_report")
            cursor.execute("ALTER TABLE evaluation_per_report AUTO_INCREMENT = 1")
            
            # Menghapus isi tabel evaluation_per_entity
            cursor.execute("DELETE FROM evaluation_per_entity")
            cursor.execute("ALTER TABLE evaluation_per_entity AUTO_INCREMENT = 1")

            # Update results_status
            cursor.execute("UPDATE results_status SET status = 0 WHERE id = 1")

            cursor.execute("UPDATE detection_mode SET model_id = NULL, region_model = NULL")
            conn.commit()
            
        # Jika source adalah "text_input", tidak perlu mengambil lokasi dari model
        if source == "text_input":
            if not text_inputan:
                print("Error: Isi chat pengaduan tidak boleh kosong untuk source 'text_input'.")
                return "Isi chat pengaduan tidak boleh kosong."

            # Buat data olah asli langsung dari input teks
            data_olah_asli = []
            for index in range(num_entries):
                result = {
                    "Isi Chat Pengaduan": text_inputan.lower(),
                    "annotations": [],  # Tidak ada anotasi untuk input langsung
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                }
                data_olah_asli.append(result)

            for entry in data_olah_asli:
                annotations = {"entities": entry['annotations']}
                annotations_str = json.dumps(annotations)
                timestamp = entry.get('timestamp')
                model_id_value = entry.get("model_id", None)  # Ambil ID model dari data
                cursor.execute(
                    "INSERT INTO data_olah_asli (text, annotations, source, model_id, timestamp) VALUES (%s, %s, %s, %s, %s)",
                    (entry['Isi Chat Pengaduan'], annotations_str, source, model_id_value, timestamp)
                )
                    
                # Akhir Hitung Waktu Eksekusi
                end_time = time.time()
                execution_time = end_time - start_time
                formatted_execution_time = format_execution_time(execution_time)

                # Insert waktu eksekusi ke tabel variabel_global
                cursor.execute("""
                    INSERT INTO variabel_global (id, generate_execution_time)
                    VALUES (1, %s)
                    ON DUPLICATE KEY UPDATE generate_execution_time = VALUES(generate_execution_time)
                """, (formatted_execution_time,))
                conn.commit()

            print(f"Waktu eksekusi: {formatted_execution_time}")

        # Jika source adalah "generate_data", ambil lokasi berdasarkan model
        elif source == "generate_data":
            # Ambil lokasi berdasarkan model
            conn = get_db_dict_connection()
            cursor = conn.cursor()

            # Ambil data lokasi dari model_locations
            cursor.execute("SELECT locations FROM model_locations WHERE model_id = %s", (model_id,))
            result = cursor.fetchone()

            if not result:
                print(f"Tidak ada lokasi yang ditemukan untuk model ID {model_id}.")
                return "Model ID tidak valid."

            # Parse lokasi dari kolom JSON
            locations_data = json.loads(result['locations'])
            provinsi_ids = locations_data.get('provinsi_ids', [])
            kabupaten_ids = locations_data.get('kabupaten_ids', [])
            kecamatan_ids = locations_data.get('kecamatan_ids', [])
            desa_ids = locations_data.get('desa_ids', [])

            # Ambil lokasi berdasarkan filter
            locations = fetch_locations_by_model(model_id, provinsi_ids, kabupaten_ids, kecamatan_ids, desa_ids)
            if not locations:
                print(f"Tidak ada lokasi yang ditemukan untuk filter yang diberikan.")
                return "Lokasi tidak ditemukan."

            # Pisahkan template berdasarkan report_status
            report_templates = [template for template in templates_chat if template[2] == 'report']
            non_report_templates = [template for template in templates_chat if template[2] == 'bukan report']

            # Proses data
            data_olah_asli = []
            for index in range(num_status_reports):
                result = process_row(index, locations, report_templates, is_report=True)
                result["model_id"] = model_id  # Tambahkan ID model ke data
                data_olah_asli.append(result)

            for index in range(num_non_reports):
                result = process_row(index, locations, non_report_templates, is_report=False)
                result["model_id"] = model_id  # Tambahkan ID model ke data
                data_olah_asli.append(result)

            # Siapkan data untuk bulk insert
            data_to_insert = []
            for entry in data_olah_asli:
                annotations = {"entities": entry['annotations']}
                annotations_str = json.dumps(annotations)
                timestamp = entry.get('timestamp')
                model_id_value = entry.get("model_id", None)  # Ambil ID model dari data
                report_status = entry.get("report_status", "bukan report")  # Ambil report_status dari data
                data_to_insert.append((
                    entry['Isi Chat Pengaduan'], annotations_str, source, model_id_value, report_status, timestamp
                ))

            # Bulk insert ke database
            cursor.executemany(
                "INSERT INTO data_olah_asli (text, annotations, source, model_id, report_status, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
                data_to_insert
            )

            # Akhir Hitung Waktu Eksekusi
            end_time = time.time()
            execution_time = end_time - start_time
            formatted_execution_time = format_execution_time(execution_time)

            # Insert waktu eksekusi ke tabel variabel_global (hanya sekali)
            cursor.execute("""
                INSERT INTO variabel_global (id, generate_execution_time)
                VALUES (1, %s)
                ON DUPLICATE KEY UPDATE generate_execution_time = VALUES(generate_execution_time)
            """, (formatted_execution_time,))

            # Commit semua perubahan sekaligus
            conn.commit()

            print(f"Waktu eksekusi: {formatted_execution_time}")

        # Jika source adalah "create_model", ambil lokasi berdasarkan model
        elif source == "create_model":

            print(f"\n[Generate Data] Data create_model\n")
            # Ambil lokasi berdasarkan model
            conn = get_db_dict_connection()
            cursor = conn.cursor()

            # Ambil data lokasi dari model_locations
            cursor.execute("SELECT locations FROM model_locations WHERE model_id = %s", (model_id,))
            result = cursor.fetchone()

            if not result:
                print(f"Tidak ada lokasi yang ditemukan untuk model ID {model_id}.")
                return "Model ID tidak valid."

            # Parse lokasi dari kolom JSON
            locations_data = json.loads(result['locations'])
            provinsi_ids = locations_data.get('provinsi_ids', [])
            kabupaten_ids = locations_data.get('kabupaten_ids', [])
            kecamatan_ids = locations_data.get('kecamatan_ids', [])
            desa_ids = locations_data.get('desa_ids', [])
            
            # Ambil lokasi berdasarkan filter
            locations = fetch_locations_by_model(model_id, provinsi_ids, kabupaten_ids, kecamatan_ids, desa_ids)
            if not locations:
                print(f"Tidak ada lokasi yang ditemukan untuk filter yang diberikan.")
                return "Lokasi tidak ditemukan."

            # print(f"Locations Data: {locations}")  # Debugging: cetak data lokasi

            # Buat kombinasi lokasi
            location_combinations = generate_location_combinations(locations)
            # print(f"Kombinasi lokasi yang dihasilkan: {location_combinations}")

            # Jumlah entri adalah jumlah kombinasi lokasi
            num_entries = len(location_combinations)

            # Bagi jumlah entri menjadi dua bagian
            num_reports = num_entries // 2  # Separuh untuk laporan
            num_non_reports = num_entries - num_reports  # Sisanya untuk bukan laporan

            BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
            BERT_MODEL_INDOLEM = os.path.join(BASE_DIR, "indolem_indobert-base-uncased")  # Path ke model indolem/indobert-base-uncased

            # Inisialisasi tokenizer
            # tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_INDOLEM)
            tokenizer = get_tokenizer(BERT_MODEL_INDOLEM)

            # Definisi label untuk BIO tagging
            label_list = ['O', 'B-LOCATION', 'I-LOCATION', 'B-DISASTER', 'I-DISASTER']
            label2id = {label: i for i, label in enumerate(label_list)}
            id2label = {i: label for label, i in label2id.items()}

            # Proses data untuk laporan
            data_create_model = []
            for index in range(num_reports):
                combination = location_combinations[index]
                result = process_row(index, [{"nama_desa": combination}], templates_chat, is_report=True)
                result["model_id"] = model_id  # Tambahkan ID model ke data
                
                # Konversi ke format BIO
                bio_data = convert_to_bio(
                    text=result["Isi Chat Pengaduan"],
                    entities=result["annotations"],
                    tokenizer=tokenizer,
                    label2id=label2id
                )
                result["bio_bert"] = json.dumps(bio_data)  # Simpan hasil BIO sebagai JSON
                data_create_model.append(result)

            # Proses data untuk bukan laporan
            for index in range(num_non_reports):
                combination = location_combinations[num_reports + index]
                result = process_row(index, [{"nama_desa": combination}], templates_chat, is_report=False)
                result["model_id"] = model_id  # Tambahkan ID model ke data
                
                # Konversi ke format BIO
                bio_data = convert_to_bio(
                    text=result["Isi Chat Pengaduan"],
                    entities=result["annotations"],
                    tokenizer=tokenizer,
                    label2id=label2id
                )
                result["bio_bert"] = json.dumps(bio_data)  # Simpan hasil BIO sebagai JSON
                data_create_model.append(result)

            # ==== PERUBAHAN DIMULAI DI SINI ====
            # Siapkan data untuk bulk insert
            data_to_insert = []
            for entry in data_create_model:
                annotations = {"entities": entry['annotations']}
                annotations_str = json.dumps(annotations)
                timestamp = entry.get('timestamp')
                model_id_value = entry.get("model_id", None)
                bio_bert_value = entry.get("bio_bert", None)  # Ambil kolom bio_bert
                data_to_insert.append((
                    entry['Isi Chat Pengaduan'], annotations_str, bio_bert_value, source, model_id_value, timestamp
                ))

            # Bulk insert ke database
            cursor.executemany(
                "INSERT INTO data_create_model (text, annotations, bio_bert, source, model_id, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
                data_to_insert
            )

            # ✅ Commit semua perubahan
            conn.commit()

        else:
            print(f"Error: Source '{source}' tidak valid.")
            return "Source tidak valid."
    
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()  # Rollback jika terjadi error
    finally:
        # Pastikan koneksi ditutup hanya sekali
        if cursor:
            cursor.close()
        if conn:
            conn.close()