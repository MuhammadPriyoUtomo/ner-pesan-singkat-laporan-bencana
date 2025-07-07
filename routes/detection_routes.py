from flask import Blueprint, render_template, redirect, url_for, request
from programs.deteksi import deteksi_main
from programs.evaluation_per_report import evaluate_report_main
from programs.evaluation_per_entities import evaluate_entity_main
from markupsafe import Markup
from helper.utils import get_navbar_status
from helper.db_utils import get_db_dict_connection
from datetime import datetime
from decimal import Decimal
import json, os, re

detection_bp = Blueprint('detection', __name__)

@detection_bp.route('/deteksi_data', methods=['POST'])
def deteksi_data():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Menghapus isi tabel hasil_ekstraksi
    cursor.execute("DELETE FROM hasil_ekstraksi")
    cursor.execute("ALTER TABLE hasil_ekstraksi AUTO_INCREMENT = 1")
    
    # Menghapus isi tabel evaluation_per_report
    cursor.execute("DELETE FROM evaluation_per_report")
    cursor.execute("ALTER TABLE evaluation_per_report AUTO_INCREMENT = 1")

    # Menghapus isi tabel evaluation_per_entity
    cursor.execute("DELETE FROM evaluation_per_entity")
    cursor.execute("ALTER TABLE evaluation_per_entity AUTO_INCREMENT = 1")

    deteksi_main()

    cursor.execute("SELECT source FROM detection_mode")
    source_mode_db = cursor.fetchone()['source']

    if source_mode_db == "generate_data":
        evaluate_report_main()
        evaluate_entity_main()

    cursor.close()
    conn.close()
    
    return redirect(url_for('detection.hasil_deteksi'))

@detection_bp.route('/hasil_deteksi')
def hasil_deteksi():
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')
    disable_hasil_asli = navbar_status.get('disable_hasil_asli')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default
    elif disable_hasil_asli:
        return redirect(url_for('main.index')) 

    def highlight_text(text, entities):
        spans = sorted(entities, key=lambda x: x[0])
        highlighted = ""
        last_idx = 0
        for start, end, label in spans:
            highlighted += text[last_idx:start]
            highlighted += f'<span class="{label.lower()} fw-bold" style="font-size: 1rem; padding: 0.4em 0.6em; border-radius: 0.5rem;">{text[start:end]}</span>'
            last_idx = end
        highlighted += text[last_idx:]
        return Markup(highlighted)

    connection = get_db_dict_connection()
    cursor = connection.cursor()

    # Hitung total data
    cursor.execute("SELECT COUNT(*) as total FROM hasil_ekstraksi")
    total_data = cursor.fetchone()['total']

    # Ambil parameter halaman
    page = int(request.args.get('page', 1))  # Halaman saat ini (default: 1)
    per_page = 10  # Jumlah data per halaman
    offset = (page - 1) * per_page

    # Ambil data dengan limit dan offset
    cursor.execute("""
        SELECT * FROM hasil_ekstraksi
        ORDER BY id ASC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    list_ekstraksi = cursor.fetchall()

    list_ekstraksi_parsed = []
    for row in list_ekstraksi:
        try:
            raw_data = json.loads(row['hasil_ekstraksi'])
            parsed_ekstraksi = json.loads(raw_data['hasil_ekstraksi'])

            row['hasil_ekstraksi'] = parsed_ekstraksi
            row['report_status'] = parsed_ekstraksi.get('disaster', {}).get('report_status') or \
                                    parsed_ekstraksi.get('location', {}).get('report_status') or \
                                    raw_data.get('report_status') or ''
            try:
                cursor.execute("SELECT annotations FROM data_olah_asli WHERE id = %s", (row['id'],))
                annot_res = cursor.fetchone()
                if annot_res:
                    annotations = json.loads(annot_res['annotations'])
                    entities = annotations.get('entities', [])
                else:
                    entities = []

                row['highlighted'] = highlight_text(row['chat_asli'], entities)
            except Exception as e:
                print("Error highlighting text:", e)
                row['highlighted'] = row['chat_asli']

        except Exception as e:
            row['hasil_ekstraksi'] = {}
            row['report_status'] = 'error'
            row['highlighted'] = row['chat_asli']

        list_ekstraksi_parsed.append(row)

    cursor.execute("SELECT * FROM variabel_global")
    waktu_eksekusi = cursor.fetchall()

    # Ambil nilai status dari tabel results_status
    cursor.execute("SELECT status FROM results_status WHERE id = 1")
    results_status = cursor.fetchone()
    save_status = results_status['status'] if results_status else 0  # Default ke 0 jika tidak ada data

    print(f"\nResults Status: {results_status}\n")

    if results_status['status'] == 1:
        cursor.execute("SELECT filename FROM results ORDER BY id DESC LIMIT 1")
        filename = cursor.fetchone()
    elif results_status['status'] == 0:
        filename = None

    cursor.close()
    connection.close()

    # Hitung total halaman
    total_pages = (total_data + per_page - 1) // per_page
    
    return render_template(
        'hasil_deteksi.html',
        list_ekstraksi=list_ekstraksi_parsed,
        waktu_eksekusi=waktu_eksekusi,
        page=page,
        total_data=total_data,
        total_pages=total_pages,
        per_page=per_page,
        save_status=save_status,
        filename=filename,
        active_page='hasil_deteksi'
    )

@detection_bp.route('/save_results', methods=['POST'])
def save_results():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default
    
    connection = get_db_dict_connection()
    cursor = connection.cursor()

    # Ambil data judul dari request
    result_title = request.form.get('resultTitle')
    # Proses judul: hapus spasi depan/belakang, ganti spasi dengan _, dan hapus karakter khusus
    if result_title:
        result_title = result_title.strip()  # Hapus spasi depan dan belakang
        result_title = re.sub(r'[^\w\s]', '', result_title)  # Hapus karakter khusus
        result_title = result_title.replace(" ", "_")  # Ganti spasi dengan _

    print(f"Result Title: {result_title}")

    # Ambil baris pertama data_olah_asli kolom model id
    cursor.execute("SELECT source FROM data_olah_asli LIMIT 1")
    source = cursor.fetchone()

    if source != "text_input":
        # Ambil data Evaluasi Per Report
        cursor.execute("SELECT * FROM evaluation_per_report")
        evaluation_per_report = cursor.fetchall()

        # Ambil data Evaluasi Per Entity
        cursor.execute("SELECT * FROM evaluation_per_entity")
        evaluation_per_entity = cursor.fetchall()

    # Ambil data Hasil Ekstraksi
    cursor.execute("SELECT * FROM hasil_ekstraksi")
    hasil_ekstraksi = cursor.fetchall()

    # Ambil data Olah Asli
    cursor.execute("SELECT * FROM data_olah_asli")
    data_olah_asli = cursor.fetchall()

    # Ambil baris pertama data_olah_asli kolom model id
    cursor.execute("SELECT model_id FROM hasil_ekstraksi LIMIT 1")
    model_id = cursor.fetchone()

    # Ambil nama model dari models
    cursor.execute("SELECT name FROM models WHERE id = %s", (model_id['model_id'],))
    model_name = cursor.fetchone()

    # Ambil Jumlah Data
    cursor.execute("SELECT COUNT(*) as count FROM data_olah_asli")
    count_data_olah_asli = cursor.fetchone()

    # Ambil data variabel_global
    cursor.execute("SELECT * FROM variabel_global")
    variabel_global = cursor.fetchall()

    print(f"Data Count: {count_data_olah_asli['count']}")

    # Gabungkan semua data ke dalam satu dictionary
    combined_data = {
        "result_title": result_title,
        "model_name": model_name['name'],
        "data_count": count_data_olah_asli['count'],
        "variabel_global": variabel_global,
        "data_olah_asli": data_olah_asli,
        "hasil_ekstraksi": hasil_ekstraksi
    }

    # Tambahkan evaluation_per_report dan evaluation_per_entity jika source != "text_input"
    if source != "text_input":
        combined_data["evaluation_per_report"] = evaluation_per_report
        combined_data["evaluation_per_entity"] = evaluation_per_entity
    
    # Tambahkan data dari folder LogDetect
    logdetect_path = os.path.join(os.getcwd(), "LogDetect")
    log_data = {}

    # Baca log dari folder Bert
    bert_path = os.path.join(logdetect_path, "Bert")
    if os.path.exists(bert_path):
        bert_logs = {}
        for f in os.listdir(bert_path):
            if f.endswith('.txt'):
                with open(os.path.join(bert_path, f), 'r') as file:
                    bert_logs[f] = file.read()  # Simpan isi file
        if bert_logs:  # Hanya tambahkan jika ada file log
            log_data["Bert"] = bert_logs

    # Baca log dari folder Spacy
    spacy_path = os.path.join(logdetect_path, "Spacy")
    if os.path.exists(spacy_path):
        spacy_logs = {}
        for f in os.listdir(spacy_path):
            if f.endswith('.txt'):
                with open(os.path.join(spacy_path, f), 'r') as file:
                    spacy_logs[f] = file.read()  # Simpan isi file
        if spacy_logs:  # Hanya tambahkan jika ada file log
            log_data["Spacy"] = spacy_logs

    # Baca log dari folder Jaro_Winkler
    jaro_winkler_path = os.path.join(logdetect_path, "Jaro_Winkler")
    if os.path.exists(jaro_winkler_path):
        jaro_winkler_logs = {}

        # Baca log dari folder Jaro_Winkler/Disaster
        jaro_disaster_path = os.path.join(jaro_winkler_path, "Disaster")
        if os.path.exists(jaro_disaster_path):
            disaster_logs = {}
            for f in os.listdir(jaro_disaster_path):
                if f.endswith('.txt'):
                    with open(os.path.join(jaro_disaster_path, f), 'r') as file:
                        disaster_logs[f] = file.read()  # Simpan isi file
            if disaster_logs:  # Hanya tambahkan jika ada file log
                jaro_winkler_logs["Disaster"] = disaster_logs

        # Baca log dari folder Jaro_Winkler/Location
        jaro_location_path = os.path.join(jaro_winkler_path, "Location")
        if os.path.exists(jaro_location_path):
            location_logs = {}
            for f in os.listdir(jaro_location_path):
                if f.endswith('.txt'):
                    with open(os.path.join(jaro_location_path, f), 'r') as file:
                        location_logs[f] = file.read()  # Simpan isi file
            if location_logs:  # Hanya tambahkan jika ada file log
                jaro_winkler_logs["Location"] = location_logs

        # Tambahkan Jaro_Winkler ke log_data jika ada data
        if jaro_winkler_logs:
            log_data["Jaro_Winkler"] = jaro_winkler_logs

    # Tambahkan log_data ke combined_data
    combined_data["log_detect"] = log_data

    BASE_DIR = os.getcwd()
    RESULT_PATH = os.path.join(BASE_DIR, "results")
    if not os.path.exists(RESULT_PATH):
        os.makedirs(RESULT_PATH)

    timestamp = datetime.now().astimezone().strftime('%Y-%m-%d_%H-%M-%S.%f_%z')

    # Simpan data ke file JSON
    json_filename = f"results_{timestamp}_{result_title}.json"
    json_filepath = os.path.join(RESULT_PATH, json_filename)

    # Fungsi untuk mengonversi Decimal ke float
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Konversi Decimal ke float
        elif isinstance(obj, datetime):
            return obj.isoformat()  # Konversi datetime ke string ISO 8601
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    with open(json_filepath, 'w') as json_file:
        json.dump(combined_data, json_file, indent=4, default=convert_decimal)

    # Masukkan judul dan timestamp ke tabel results
    cursor.execute("INSERT INTO results (title, filename, timestamp) VALUES (%s, %s, %s)", (result_title, json_filename, timestamp))
    connection.commit()

    # Update results_status
    cursor.execute("UPDATE results_status SET status = 1 WHERE id = 1")
    connection.commit()

    cursor.close()
    connection.close()

    print(f"Results saved to {json_filepath}")

    # Redirect ke /hasil_deteksi
    return redirect(url_for('detection.hasil_deteksi'))