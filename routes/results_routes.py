from flask import Blueprint, render_template, redirect, url_for, request
from markupsafe import Markup
from helper.utils import get_navbar_status
from helper.db_utils import get_db_dict_connection
import os, json

results_bp = Blueprint('results', __name__)

@results_bp.route('/results')
def results():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))
    
    # Ambil parameter halaman
    page = int(request.args.get('page', 1))  # Halaman saat ini (default: 1)
    per_page = 10  # Jumlah data per halaman

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Hitung total data
    cursor.execute("SELECT COUNT(*) as total FROM results")
    total_data = cursor.fetchone()['total']

    # Hitung offset untuk pagination
    offset = (page - 1) * per_page

    # Ambil data dengan limit dan offset
    cursor.execute("""
        SELECT *
        FROM results
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    # Hitung total halaman
    total_pages = (total_data + per_page - 1) // per_page

    return render_template(
        'results.html',
        results=results,
        page=page,
        total_data=total_data,
        total_pages=total_pages,
        per_page=per_page,
        active_page='results'
    )

@results_bp.route('/results_hasil_simulasi')
def results_hasil_simulasi():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))
    elif not navbar_status['has_selected_result']:
        return redirect(url_for('results.results'))
    
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Ambil filename dari tabel results
    cursor.execute("SELECT filename FROM results WHERE selected = 1")
    selected_result = cursor.fetchone()  # Gunakan fetchone() untuk mengambil satu baris

    cursor.close()
    conn.close()

    # Periksa apakah hasil query valid
    if not selected_result:
        return "File JSON tidak ditemukan di database.", 404

    # Ambil nama file dari key 'filename' dalam dictionary
    json_filename = selected_result['filename']  # Ambil nilai dari key 'filename'

    print("Selected Result:", json_filename)

    RESULT_PATH = os.path.join(os.getcwd(), "results")
    JSON_FILE_PATH = os.path.join(RESULT_PATH, json_filename)  # Gabungkan path dengan nama file
    print("JSON File Path:", JSON_FILE_PATH)

    # Periksa apakah file JSON ada
    if not os.path.exists(JSON_FILE_PATH):
        return "File JSON tidak ditemukan.", 404

    # Baca file JSON
    with open(JSON_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)

    result_title=data.get('result_title')
    model_name=data.get('model_name')
    data_count=data.get('data_count')
    data_olah_asli=data.get('data_olah_asli', [])
    variabel_global=data.get('variabel_global', [])

    # Ganti model_id dengan model_name
    for row in data_olah_asli:
        if 'model_id' in row:
            # Ganti model_id dengan model_name
            row['model_name'] = model_name
            del row['model_id']  # Hapus key model_id jika tidak diperlukan

    # Pagination logic
    page = request.args.get('page', 1, type=int)  # Ambil parameter 'page' dari query string
    per_page = 10  # Jumlah item per halaman
    total_pages = (len(data_olah_asli) + per_page - 1) // per_page  # Hitung total halaman
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = data_olah_asli[start:end]  # Ambil data untuk halaman saat ini

    return render_template(
        'results_hasil_simulasi.html', 
        result_title=result_title, 
        data_count=data_count, 
        data_olah_asli=paginated_data,
        variabel_global=variabel_global,
        active_page='results_hasil_simulasi',
        page=page,
        total_pages=total_pages
    )

@results_bp.route('/results_hasil_deteksi')
def results_hasil_deteksi():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))
    elif not navbar_status['has_selected_result']:
        return redirect(url_for('results.results'))
    
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
    
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Ambil filename dari tabel results
    cursor.execute("SELECT filename FROM results WHERE selected = 1")
    selected_result = cursor.fetchone()  # Gunakan fetchone() untuk mengambil satu baris

    cursor.close()
    conn.close()

    # Periksa apakah hasil query valid
    if not selected_result:
        return "File JSON tidak ditemukan di database.", 404

    # Ambil nama file dari key 'filename' dalam dictionary
    json_filename = selected_result['filename']  # Ambil nilai dari key 'filename'

    print("Selected Result:", json_filename)

    RESULT_PATH = os.path.join(os.getcwd(), "results")
    JSON_FILE_PATH = os.path.join(RESULT_PATH, json_filename)  # Gabungkan path dengan nama file
    print("JSON File Path:", JSON_FILE_PATH)

    # Periksa apakah file JSON ada
    if not os.path.exists(JSON_FILE_PATH):
        return "File JSON tidak ditemukan.", 404

    # Baca file JSON
    with open(JSON_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)

    result_title=data.get('result_title')
    data_count=data.get('data_count')

    variabel_global = data.get('variabel_global', [])

    list_ekstraksi_parsed = []
    for row in data.get('hasil_ekstraksi', []):
        try:
            # Parse level pertama
            raw_data = json.loads(row['hasil_ekstraksi'])
            # print(f"\nRaw Data:{raw_data}\n")

            # Parse level kedua
            parsed_ekstraksi = json.loads(raw_data['hasil_ekstraksi'])
            # print(f"\nParsed Ekstraksi:{parsed_ekstraksi}\n")

            row['hasil_ekstraksi'] = parsed_ekstraksi
            row['report_status'] = parsed_ekstraksi.get('disaster', {}).get('report_status') or \
                                parsed_ekstraksi.get('location', {}).get('report_status') or \
                                raw_data.get('report_status') or ''

            # Ambil annotations dari data_olah_asli berdasarkan ID
            matching_data = next((item for item in data.get('data_olah_asli', []) if item['id'] == row['id']), None)
            if matching_data and 'annotations' in matching_data:
                annotations = json.loads(matching_data['annotations'])
                entities = annotations.get('entities', [])
            else:
                entities = []

            # Gunakan highlight_text untuk menyoroti teks
            row['highlighted'] = highlight_text(row['chat_asli'], entities)

            # Tambahkan row yang sudah diproses ke list_ekstraksi_parsed
            list_ekstraksi_parsed.append(row)

        except Exception as e:
            print(f"Error parsing row: {e}")

    # Pagination logic
    page = request.args.get('page', 1, type=int)  # Ambil parameter 'page' dari query string
    per_page = 10  # Jumlah item per halaman
    total_pages = (len(list_ekstraksi_parsed) + per_page - 1) // per_page  # Hitung total halaman
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = list_ekstraksi_parsed[start:end]  # Ambil data untuk halaman saat ini

    return render_template(
        'results_hasil_deteksi.html',
        result_title=result_title,
        data_count=data_count,
        list_ekstraksi_parsed=paginated_data,  # Kirim data yang sudah dipaginasi
        variabel_global=variabel_global,
        active_page='results_hasil_deteksi',
        page=page,
        total_pages=total_pages
    )

@results_bp.route('/results_evaluasi')
def results_evaluasi():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))
    elif not navbar_status['has_selected_result']:
        return redirect(url_for('results.results'))

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Ambil filename dari tabel results
    cursor.execute("SELECT filename FROM results WHERE selected = 1")
    selected_result = cursor.fetchone()  # Gunakan fetchone() untuk mengambil satu baris

    cursor.close()
    conn.close()

    # Periksa apakah hasil query valid
    if not selected_result:
        return "File JSON tidak ditemukan di database.", 404

    # Ambil nama file dari key 'filename' dalam dictionary
    json_filename = selected_result['filename']  # Ambil nilai dari key 'filename'

    print("Selected Result:", json_filename)

    RESULT_PATH = os.path.join(os.getcwd(), "results")
    JSON_FILE_PATH = os.path.join(RESULT_PATH, json_filename)  # Gabungkan path dengan nama file
    print("JSON File Path:", JSON_FILE_PATH)

    # Periksa apakah file JSON ada
    if not os.path.exists(JSON_FILE_PATH):
        return "File JSON tidak ditemukan.", 404

    # Baca file JSON
    with open(JSON_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)

    result_title=data.get('result_title')

    # Ambil nilai source dari data_olah_asli
    data_olah_asli = data.get('data_olah_asli', [])
    source = data_olah_asli[0].get('source') if data_olah_asli else None
    print(f"Source: {source}")

    if source == 'text_input':
        # Kirim data ke template
        return render_template(
            'results_evaluasi.html',
            active_page='results_evaluasi',
            result_title=result_title,
            source=source
        )

    elif source == 'generate_data':
        # Ambil data evaluasi dari evaluation_per_report
        hasil_evaluasi_per_report = data.get('evaluation_per_report')

        mismatched_ids_report = set()
        # Iterasi setiap elemen di evaluation_per_report
        for row in data.get('evaluation_per_report', []):
            if row['mismatched_ids']:
                # Parse mismatched_ids dari string JSON ke dictionary
                row['mismatched_ids'] = json.loads(row['mismatched_ids'])

                # Update mismatched_ids_report dengan ID dari pred_bukan_actual_report dan pred_report_actual_bukan
                mismatched_ids_report.update(row['mismatched_ids'].get('pred_bukan_actual_report', []))
                mismatched_ids_report.update(row['mismatched_ids'].get('pred_report_actual_bukan', []))

        # Ambil data dari tabel hasil_deteksi berdasarkan mismatched IDs untuk Per Report
        if mismatched_ids_report:
            hasil_deteksi_report = [
                {
                    "id": item["id"],
                    "hasil_ekstraksi": item["hasil_ekstraksi"],
                    "report_status": item["report_status"]
                }
                for item in data.get("hasil_ekstraksi", [])
                if item["id"] in mismatched_ids_report
            ]
        else:
            hasil_deteksi_report = []

        # Ambil data evaluasi dari evaluation_per_report
        hasil_evaluasi_per_entity = data.get('evaluation_per_entity')

        mismatched_ids_entity = set()
        # Iterasi setiap elemen di evaluation_per_entity
        for row in data.get('evaluation_per_entity', []):
            if row['mismatched_ids']:
                # Parse mismatched_ids dari string JSON ke dictionary
                row['mismatched_ids'] = json.loads(row['mismatched_ids'])

                # Update mismatched_ids_report dengan ID dari pred_bukan_actual_report dan pred_report_actual_bukan
                mismatched_ids_report.update(row['mismatched_ids'].get('pred_false_actual_true', []))
                mismatched_ids_report.update(row['mismatched_ids'].get('pred_true_actual_false', []))

        # Ambil data dari tabel hasil_deteksi berdasarkan mismatched IDs untuk Per Entity
        if mismatched_ids_entity:
            hasil_deteksi_entity = [
                {
                    "id": item["id"],
                    "hasil_ekstraksi": item["hasil_ekstraksi"],
                    "report_status": item["report_status"]
                }
                for item in data.get("hasil_ekstraksi", [])
                if item["id"] in mismatched_ids_report
            ]
        else:
            hasil_deteksi_entity = []

        # Kirim data ke template
        return render_template(
            'results_evaluasi.html',
            active_page='results_evaluasi',
            result_title=result_title,
            source=source,
            hasil_evaluasi_per_report=hasil_evaluasi_per_report,
            hasil_evaluasi_per_entity=hasil_evaluasi_per_entity,
            hasil_deteksi_report=hasil_deteksi_report,
            hasil_deteksi_entity=hasil_deteksi_entity
        )

@results_bp.route('/results/toggle_selected/<int:id>', methods=['POST'])
def toggle_selected(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    try:
        # Ambil status saat ini dari baris dengan ID tertentu
        cursor.execute("SELECT selected FROM results WHERE id=%s", (id,))
        result = cursor.fetchone()

        if not result:
            return {"status": "error", "message": "Data tidak ditemukan."}

        current_status = result['selected']

        if current_status == 1:
            # Jika data sudah aktif, nonaktifkan hanya baris tersebut
            cursor.execute("UPDATE results SET selected = 0 WHERE id = %s", (id,))
        else:
            # Jika data tidak aktif, nonaktifkan semua baris dan aktifkan baris yang dipilih
            cursor.execute("UPDATE results SET selected = 0")
            cursor.execute("UPDATE results SET selected = 1 WHERE id = %s", (id,))

        conn.commit()
        return {"status": "success", "new_status": not current_status}

    except Exception as e:
        print(f"Error toggling selected: {e}")
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

@results_bp.route('/results/delete/<int:id>', methods=['POST'])
def delete_result(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM results WHERE id = %s", (id,))
    selected_result = cursor.fetchone()

    BASE_DIR = os.getcwd()
    RESULT_PATH = os.path.join(BASE_DIR, "results")
    JSON_FILE_PATH = os.path.join(RESULT_PATH, selected_result['filename'])
    print("JSON File Path:", JSON_FILE_PATH)

    # Periksa apakah file JSON ada
    if os.path.exists(JSON_FILE_PATH):
        try:
            # Hapus file JSON
            os.remove(JSON_FILE_PATH)
        except Exception as e:
            print(f"Error deleting file: {e}")
            return {"status": "error", "message": str(e)}

    try:
        # Hapus data berdasarkan ID
        cursor.execute("DELETE FROM results WHERE id = %s", (id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"Error deleting result: {e}")
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@results_bp.route('/results/view_log/<int:id>', methods=['GET'])
def view_log(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))
    
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Ambil filename dari tabel results
    cursor.execute("SELECT filename FROM results WHERE selected = 1")
    selected_result = cursor.fetchone()  # Gunakan fetchone() untuk mengambil satu baris
    # Ambil nama file dari key 'filename' dalam dictionary
    json_filename = selected_result['filename']  # Ambil nilai dari key 'filename'

    RESULT_PATH = os.path.join(os.getcwd(), "results")
    JSON_FILE_PATH = os.path.join(RESULT_PATH, json_filename)  # Gabungkan path dengan nama file
    print("JSON File Path:", JSON_FILE_PATH)

    # Periksa apakah file JSON ada
    if not os.path.exists(JSON_FILE_PATH):
        return "File JSON tidak ditemukan.", 404

    # Baca file JSON
    with open(JSON_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)

    result_title=data.get('result_title')

    # Ambil log_detect dari JSON
    log_detect = data.get('log_detect', {})

    # Iterasi untuk mencetak judul log
    for log_title, log_content in log_detect.items():
        print(f"Log Title: {log_title}")

    # Cari log berdasarkan ID
    log_detail = {}

    # Proses log dari semua model, termasuk Jaro_Winkler jika ada
    for model, logs in log_detect.items():
        if model == 'Jaro_Winkler':
            # Jika model adalah Jaro_Winkler, iterasi subkategori
            for sub_category, sub_logs in logs.items():
                for log_name, log_content in sub_logs.items():
                    # Cocokkan ID berdasarkan angka di akhir nama file log
                    if log_name.endswith(f"_{id}.txt"):
                        log_detail[f"{model} - {sub_category} - {log_name}"] = log_content
        else:
            # Proses log dari model lain (Bert, Spacy, dll.)
            for log_name, log_content in logs.items():
                # Cocokkan ID berdasarkan angka di akhir nama file log
                if log_name.endswith(f"_{id}.txt"):
                    log_detail[f"{model} - {log_name}"] = log_content

    # Render halaman log, meskipun log_detail kosong
    return render_template(
        'view_log.html',
        id=id,
        result_title=result_title,
        log_detail=log_detail
    )