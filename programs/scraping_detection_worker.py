from helper.db_utils import get_db_dict_connection
from programs.deteksi import process_row, get_detection_mode_from_db, fetch_list_from_db
from programs.deteksi_jaro_winkler_location import read_location_groups
from programs.deteksi_bert import get_bert_pipeline
from programs.deteksi_spacy import get_nlp
import time

def detection_worker(stop_flag):

    # --- Ambil parameter model dari DB ---
    detection_mode_data = get_detection_mode_from_db()
    detection_mode = detection_mode_data['mode']
    region_model = detection_mode_data['region_model']

    # --- Preload model di awal worker ---
    aggregation_strategy = "simple"
    device = -1
    bert_pipeline = None
    spacy_nlp = None
    if region_model:
        bert_model_path = f"model_bert/{region_model}"
        spacy_model_path = f"model_spacy/{region_model}"
        if 'bert' in detection_mode:
            bert_pipeline = get_bert_pipeline(bert_model_path, aggregation_strategy, device)
        if 'spacy' in detection_mode:
            spacy_nlp = get_nlp(spacy_model_path)

    while not stop_flag.is_set():
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pending_detection LIMIT 1")
        row = cursor.fetchone()
        if row:
            # Ambil parameter deteksi dari DB
            detection_mode_data = get_detection_mode_from_db()
            detection_mode = detection_mode_data['mode']
            region_model = detection_mode_data['region_model']
            bencana_list = fetch_list_from_db('list_bencana')
            valid_disasters = [disaster['bencana'].lower() for disaster in bencana_list]
            location_groups = []
            if region_model:
                combination_file = f"model_jaro_winkler/{region_model}_combinations.txt"
                try:
                    location_groups = read_location_groups(combination_file)
                except FileNotFoundError:
                    print(f"File kombinasi tidak ditemukan: {combination_file}")

            # Proses deteksi
            row_data = {
                'id': row['id'],
                'sender': row['nomor_pengirim'],
                'text': row['chat'],
                'date': row['tanggal'],
                'timestamp': row['timestamp']
            }

            result = process_row(
                row_data,
                valid_disasters,
                region_model,
                location_groups,
                0,
                detection_mode,
                bert_pipeline=bert_pipeline,
                spacy_nlp=spacy_nlp,
                aggregation_strategy=aggregation_strategy,
                device=device
            )

            hasil_ekstraksi = result['result']['hasil_ekstraksi']
            report_status = result['result']['report_status']

            # Simpan ke live_scraping
            try:
                insert_query = """
                    INSERT INTO live_scraping (
                        nomor_pengirim, tanggal, chat, hasil_ekstraksi, report_status, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    row['nomor_pengirim'],
                    row['tanggal'],
                    row['chat'],
                    hasil_ekstraksi,
                    report_status,
                    row['timestamp']
                ))
                conn.commit()

                # Langsung copy ke hasil_scraping setelah masuk ke live_scraping
                cursor.execute("""
                    INSERT INTO hasil_scraping (nomor_pengirim, tanggal, chat, hasil_ekstraksi, report_status, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    row['nomor_pengirim'],
                    row['tanggal'],
                    row['chat'],
                    hasil_ekstraksi,
                    report_status,
                    row['timestamp']
                ))
                conn.commit()

                # Cek jumlah data, hapus yang ke-6 (paling lama) dari live_scraping saja
                cursor.execute("SELECT id FROM live_scraping ORDER BY timestamp DESC")
                all_ids = [r['id'] for r in cursor.fetchall()]
                if len(all_ids) > 5:
                    ids_to_remove = all_ids[5:]
                    for remove_id in ids_to_remove:
                        cursor.execute("DELETE FROM live_scraping WHERE id = %s", (remove_id,))
                    conn.commit()

                # Hapus dari pending_detection
                cursor.execute("DELETE FROM pending_detection WHERE id = %s", (row['id'],))
                conn.commit()
            except Exception as e:
                print(f"Gagal simpan hasil deteksi: {e}")
        else:
            # Tidak ada data, tunggu sebentar
            time.sleep(1)
        cursor.close()
        conn.close()