from flask import Blueprint, render_template, request, redirect, url_for, make_response
from helper.db_utils import get_db_dict_connection
from helper.utils import get_navbar_status
import os,json

data_model_bp = Blueprint('data_model', __name__)

@data_model_bp.route('/lihat_data_model', methods=['GET', 'POST'])
def lihat_data_model():
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    conn = get_db_dict_connection()
    data_filtered = []

    selected_model_name = None
    selected_model_id = None
    training_type = None
    data_count = 0

    # Ambil parameter halaman
    page = int(request.args.get('page', 1))
    per_page = 10  # Atur jumlah data per halaman

    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM models")
        models = cursor.fetchall()

        # POST: Submit form model + training_type
        if request.method == 'POST':
            selected_model_id = request.form.get('model_id')
            training_type = request.form.get('training_type')
            page = 1  # Reset halaman ke awal saat submit

            # Tambahkan cookie untuk reset local storage
            response = make_response(redirect(url_for('data_model.lihat_data_model', model_id=selected_model_id, training_type=training_type)))
            response.set_cookie('clear_local_storage', 'true')
            return response

        # GET: Navigasi antar halaman
        elif request.method == 'GET':
            selected_model_id = request.args.get('model_id')
            training_type = request.args.get('training_type')

            # Validasi model_id
            if selected_model_id and not any(str(m['id']) == str(selected_model_id) for m in models):
                # Model tidak ditemukan, hapus localStorage lewat JS
                response = make_response(redirect(url_for('data_model.lihat_data_model')))
                response.set_cookie('clear_local_storage', 'true')
                return response

        # Ambil nama model
        for m in models:
            if str(m['id']) == str(selected_model_id):
                selected_model_name = m['name']
                break

        if selected_model_id and training_type:
            if training_type == 'jaro':
                file_path = f"model_jaro_winkler/{selected_model_name}_combinations.txt"
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_lines = [line.strip() for line in f if line.strip()]
                        data_count = len(all_lines)
                        start = (page - 1) * per_page
                        end = start + per_page
                        data_filtered = [{"id": idx + start + 1, "location": line}
                                         for idx, line in enumerate(all_lines[start:end])]
            else:
                # Hitung total data terlebih dahulu
                count_query = ""
                data_query = ""
                if training_type == 'bert':
                    count_query = "SELECT COUNT(*) AS total FROM data_create_model WHERE model_id = %s AND bert_train_used = 1"
                    data_query = """
                        SELECT id, text, annotations, bio_bert, model_id, timestamp 
                        FROM data_create_model
                        WHERE model_id = %s AND bert_train_used = 1
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """
                elif training_type == 'spacy':
                    count_query = "SELECT COUNT(*) AS total FROM data_create_model WHERE model_id = %s AND spacy_train_used = 1"
                    data_query = """
                        SELECT id, text, annotations, model_id, timestamp 
                        FROM data_create_model
                        WHERE model_id = %s AND spacy_train_used = 1
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """

                if count_query and data_query:
                    cursor.execute(count_query, (selected_model_id,))
                    result = cursor.fetchone()
                    if result:
                        data_count = result['total']  # Gunakan alias 'total'
                    else:
                        data_count = 0  # Jika tidak ada data, set jumlah data ke 0

                    offset = (page - 1) * per_page
                    cursor.execute(data_query, (selected_model_id, per_page, offset))
                    rows = cursor.fetchall()

                    if training_type == 'bert':
                        # Proses data untuk parsing JSON
                        for row in rows:
                            bio_bert_raw = row['bio_bert']
                            try:
                                bio_bert_parsed = json.loads(bio_bert_raw) if bio_bert_raw else {}
                            except json.JSONDecodeError:
                                bio_bert_parsed = {}

                            # Siapkan data untuk ditampilkan di template
                            if bio_bert_parsed:
                                tokens = bio_bert_parsed.get("tokens", [])
                                offsets = bio_bert_parsed.get("offsets", [])
                                labels = bio_bert_parsed.get("labels", [])
                                label_map = ['O', 'B-LOCATION', 'I-LOCATION', 'B-DISASTER', 'I-DISASTER']

                                # Gabungkan data menggunakan zip di backend
                                bio_bert_parsed["zipped_data"] = [
                                    {"token": token, "offset": offset, "label": label_map[label]}
                                    for token, offset, label in zip(tokens, offsets, labels)
                                ]
                            else:
                                bio_bert_parsed["zipped_data"] = []

                            row['bio_bert_raw'] = bio_bert_raw  # Data mentah
                            row['bio_bert_parsed'] = bio_bert_parsed  # Data hasil parsing
                            data_filtered.append(row)
                    elif training_type == 'spacy':
                        # Proses data untuk spaCy
                        for row in rows:
                            annotations_raw = row['annotations']
                            try:
                                annotations_parsed = json.loads(annotations_raw) if annotations_raw else {}
                            except json.JSONDecodeError:
                                annotations_parsed = {}
                                
                            # Tambahkan data parsing ke row
                            row['annotations_raw'] = annotations_raw
                            row['annotations_parsed'] = annotations_parsed
                            
                            # Tambahkan row ke data_filtered
                            data_filtered.append(row)

    conn.close()

    total_pages = (data_count + per_page - 1) // per_page

    return render_template(
        'lihat_data_model.html',
        active_page='data model',
        models=models,
        data_filtered=data_filtered,
        data_count=data_count,
        selected_model_id=selected_model_id,
        selected_training_type=training_type,
        selected_model_name=selected_model_name,
        page=page,
        total_pages=total_pages,
        per_page=per_page
    )