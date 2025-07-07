from programs.deteksi_bert import process_text_with_bert
from programs.deteksi_spacy import load_and_test_model
from programs.deteksi_jaro_winkler_disaster import process_with_jaro_winkler_disaster
from programs.deteksi_jaro_winkler_location import read_location_groups, process_with_jaro_winkler_location
from helper.db_utils import get_db_dict_connection
from helper.utils import get_navbar_status
from datetime import datetime
import os, time, json, shutil

def get_detection_mode_from_db():
    conn = get_db_dict_connection()
    cursor = conn.cursor()  # Gunakan DictCursor untuk hasil berbentuk dictionary
    cursor.execute("SELECT * FROM detection_mode")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result  # Mengembalikan dictionary dengan semua mode

def fetch_data_from_db(table_name):
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def fetch_list_from_db(table_name):
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def clear_log_folder(folder="LogDetect"):
    """
    Menghapus semua isi folder log sebelum memulai proses.
    """
    if os.path.exists(folder):
        shutil.rmtree(folder)  # Hapus folder beserta isinya
    os.makedirs(folder)  # Buat ulang folder kosong

def process_row(row, valid_disasters, region_model, location_groups, index, detection_mode, bert_pipeline=None, spacy_nlp=None, aggregation_strategy="simple", device=-1):
    print(f"\n\n[PROCESS ROW] Memproses baris ke-{index + 1}: {row}")
    text = row['text']    

    # Inisialisasi variabel untuk menyimpan hasil
    disaster = None
    location = None
    source_disaster = None
    source_location = None

    execution_times = {
        "global": 0
    }

    # ===================== #
    # Ekstraksi dengan BERT #
    # ===================== #
    if region_model and any(m in detection_mode for m in ['bert+spacy', 'bert']):
        bert_model_path = f"model_bert/{region_model}"
        if os.path.exists(bert_model_path):
            start_time = time.time()  # Mulai hitung waktu eksekusi

            if bert_pipeline is not None:
                hasil_bert = process_text_with_bert(
                    bert_model_path, text, data_index=index + 1, pipeline=bert_pipeline,
                    aggregation_strategy=aggregation_strategy, device=device
                )
            else:
                hasil_bert = process_text_with_bert(
                    bert_model_path, text, data_index=index + 1,
                    aggregation_strategy=aggregation_strategy, device=device
                )

            end_time = time.time()  # Akhiri hitung waktu eksekusi
            execution_times["global"] += end_time - start_time  # Tambahkan waktu eksekusi ke variabel
            print(f"\n[PROCESS ROW] Hasil ekstraksi BERT: {hasil_bert}\n")
            for ent in hasil_bert:
                if ent['label'] == 'DISASTER' and not disaster:
                    disaster = ent['text']
                    source_disaster = "bert"
                elif ent['label'] == 'LOCATION' and not location:
                    location = ent['text']
                    source_location = "bert"

    # ======================= #
    # Ekstraksi dengan SpaCy #
    # ======================= #
    if not disaster or not location:  # Hanya lanjutkan jika entitas belum ditemukan
        if region_model and any(m in detection_mode for m in ['bert+spacy', 'spacy']):
            spacy_model_path = f"model_spacy/{region_model}"
            start_time = time.time()  # Mulai hitung waktu eksekusi
            
            if spacy_nlp is not None:
                hasil_spacy = load_and_test_model(spacy_model_path, text, data_index=index + 1, nlp=spacy_nlp)
            else:
                hasil_spacy = load_and_test_model(spacy_model_path, text, data_index=index + 1)

            end_time = time.time()  # Akhiri hitung waktu eksekusi
            execution_times["global"] += end_time - start_time  # Tambahkan waktu eksekusi ke variabel
            print(f"\n[PROCESS ROW] Hasil ekstraksi SpaCy: {hasil_spacy}\n")
            if hasil_spacy and 'entities' in hasil_spacy:
                for ent in hasil_spacy['entities']:
                    if ent['label'] == 'DISASTER' and not disaster:
                        disaster = ent['text']
                        source_disaster = "spacy"
                    elif ent['label'] == 'LOCATION' and not location:
                        location = ent['text']
                        source_location = "spacy"

    # ============================== #
    # Ekstraksi dengan Jaro-Winkler #
    # ============================== #
    if not disaster or not location:  # Hanya lanjutkan jika entitas belum ditemukan
        if any(m in detection_mode for m in ['jaro']):
            if not disaster:
                print(f"\n[PROCESS ROW] Memproses dengan Jaro-Winkler untuk 'disaster'...")
                start_time = time.time()  # Mulai hitung waktu eksekusi
                hasil_jaro_disaster = process_with_jaro_winkler_disaster(
                    text,
                    valid_disasters,
                    threshold=0.9,
                    data_index=index + 1
                )
                end_time = time.time()  # Akhiri hitung waktu eksekusi
                execution_times["global"] += end_time - start_time  # Tambahkan waktu eksekusi ke variabel
                print(f"\n[PROCESS ROW] Hasil Jaro-Winkler untuk 'disaster': {hasil_jaro_disaster}\n")
                disaster = hasil_jaro_disaster.get("disaster")
                if disaster:  # Hanya isi source jika disaster terdeteksi
                    source_disaster = "jaro"

            if not location:
                print(f"\n[PROCESS ROW] Memproses dengan Jaro-Winkler untuk 'location'...")
                start_time = time.time()  # Mulai hitung waktu eksekusi
                hasil_jaro_location = process_with_jaro_winkler_location(
                    text,
                    location_groups,
                    threshold=0.9,
                    data_index=index + 1
                )
                end_time = time.time()  # Akhiri hitung waktu eksekusi
                execution_times["global"] += end_time - start_time  # Tambahkan waktu eksekusi ke variabel
                print(f"\n[PROCESS ROW] Hasil Jaro-Winkler untuk 'location': {hasil_jaro_location}\n")
                location = hasil_jaro_location.get("location")
                if location:  # Hanya isi source jika location terdeteksi
                    source_location = "jaro"

    # Gabungkan hasil deteksi
    hasil_ekstraksi = {
        "disaster": {
            "text": disaster,
            "source": source_disaster if disaster else None
        },
        "location": {
            "text": location,
            "source": source_location if location else None
        }
    }

    print(f"\n[PROCESS ROW] Hasil ekstraksi: {hasil_ekstraksi}\n")

    # Jika hasil tetap tidak ditemukan, tambahkan log
    if not disaster and not location:
        print(f"[PROCESS ROW] Tidak ditemukan entitas pada data ke-{index + 1}: {text}")
        hasil_ekstraksi["log"] = "Tidak ditemukan entitas."

    # Tentukan report_status
    report_status = "report" if disaster and location else "bukan report"

    # Format hasil akhir
    result = {
        "id": index + 1,
        "chat_asli": text,
        "hasil_ekstraksi": json.dumps(hasil_ekstraksi),
        "report_status": report_status,  # Tambahkan report_status
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')  # Tambahkan timestamp
    }
    print(f"\n[PROCESS ROW] Hasil akhir:", result)

    return {
        "result": result,
        "execution_times": execution_times
    }

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

def deteksi_main():
    
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    detection_mode_data = get_detection_mode_from_db()
    detection_mode = detection_mode_data['mode']
    model_id = detection_mode_data['model_id']
    region_model = detection_mode_data['region_model']

    print("[MAIN] Detection Mode:", detection_mode)
    print("[MAIN] Region Model:", region_model)

    # Bersihkan folder LogDetect sebelum memulai proses
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # jangan clear log jika mode adalah 'auto'
    if result_mode == 'manual':
        clear_log_folder("LogDetect")

    cursor.execute("SELECT text FROM data_olah_asli")
    data = cursor.fetchall()

    # Ambil daftar bencana dari tabel list_bencana
    bencana_list = fetch_list_from_db('list_bencana')
    valid_disasters = [disaster['bencana'].lower() for disaster in bencana_list]

    # Baca file kombinasi lokasi untuk Jaro-Winkler
    if region_model:
        combination_file = f"model_jaro_winkler/{region_model}_combinations.txt"
        if not os.path.exists(combination_file):
            print(f"[MAIN] Error: File kombinasi lokasi '{combination_file}' tidak ditemukan.")
            location_groups = []
        else:
            location_groups = read_location_groups(combination_file)
    else:
        location_groups = []

    print("[MAIN] Proses Deteksi untuk Setiap Baris Data")

    hasil_deteksi = []

    total_global_execution_time = {
        "global":0
    }

    for index, row in enumerate(data):
        # Proses setiap baris data menggunakan fungsi `process_row`
        row_result = process_row(row, valid_disasters, region_model, location_groups, index, detection_mode)

        result = row_result["result"]
        execution_times = row_result["execution_times"]

        # Akumulasi waktu eksekusi
        for method, time_spent in execution_times.items():
            total_global_execution_time[method] += time_spent

        hasil_deteksi.append(result)

        report_status = result['report_status']  # Simpan report_status secara terpisah
        # Simpan hasil ke database
        cursor.execute("""
            INSERT INTO hasil_ekstraksi (id, chat_asli, hasil_ekstraksi, model_id, region_model, report_status, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (index + 1, row['text'], json.dumps(result), model_id, region_model, report_status, result['timestamp']))
        conn.commit()

    data_count = len(data)  # data adalah hasil fetchall dari data_olah_asli
    average_execution_time = format_execution_time(total_global_execution_time["global"] / data_count if data_count else 0)
    print(f"Rata-rata waktu eksekusi untuk {data_count} data: {average_execution_time}")

    global_execution_time = format_execution_time(total_global_execution_time["global"])
    print(f"\n[MAIN] Waktu eksekusi Global: {global_execution_time}\n")

    # Simpan waktu eksekusi ke database
    cursor.execute("""
        INSERT INTO variabel_global (id, deteksi_execution_time, deteksi_average_execution_time)
        VALUES (1, %s, %s)
        ON DUPLICATE KEY UPDATE deteksi_execution_time = VALUES(deteksi_execution_time), deteksi_average_execution_time = VALUES(deteksi_average_execution_time)
    """, (global_execution_time, average_execution_time,))
    conn.commit()
    
    cursor.close()
    conn.close()