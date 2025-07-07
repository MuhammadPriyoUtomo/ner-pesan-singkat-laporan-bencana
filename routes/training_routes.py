from flask import Blueprint, render_template, request, redirect, url_for, flash
from programs.train_spacy_model import train_spacy_model
from programs.train_bert_model import train_bert_model
from programs.combination import generate_combinations_for_model  # Impor fungsi kombinasi
from programs.generate_data import generate_data  # Impor fungsi generate_data
from helper.db_utils import get_db_dict_connection, get_db_connection
from helper.utils import get_navbar_status
import json, re, os, shutil

training_bp = Blueprint('training', __name__)

def get_folder_size(folder_path):
    """Menghitung ukuran folder dalam byte."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def format_size(size_in_bytes):
    """Mengonversi ukuran dari byte ke KB, MB, atau GB."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024

def count_non_empty_lines(file_path):
    """Menghitung jumlah baris yang tidak kosong dalam file dan menambahkan teks '... baris'."""
    if not os.path.exists(file_path):
        return "0 baris"
    with open(file_path, 'r', encoding='utf-8') as file:
        non_empty_line_count = sum(1 for line in file if line.strip())
    return f"{non_empty_line_count} baris"

# Fungsi untuk mengambil data dari database MySQL
def fetch_spacy_train_data(model_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ambil kolom `id`, `text`, dan `annotations`
    query = "SELECT id, text, annotations FROM data_create_model WHERE model_id = %s"
    cursor.execute(query, (model_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    # Konversi annotations dari string JSON ke dictionary jika diperlukan
    processed_data = []
    for row in data:
        data_id, text, annotations = row  # Ambil ID, teks, dan anotasi
        if isinstance(annotations, str):
            try:
                annotations = json.loads(annotations)  # Konversi string JSON ke dictionary
            except json.JSONDecodeError:
                print(f"[ERROR] Gagal mengonversi annotations menjadi JSON: {annotations}")
                continue
        # Jangan tambahkan ID ke dalam anotasi, simpan ID secara terpisah
        processed_data.append((data_id, text, annotations))
    return processed_data

def fetch_bert_train_data(model_id):
    """
    Fungsi untuk mengambil data khusus untuk pelatihan BERT dari tabel data_create_model.
    Data yang diambil mencakup kolom id, text, dan bio_bert.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ambil kolom `id`, `text`, dan `bio_bert` dari tabel data_create_model
        query = """
        SELECT id, text, bio_bert 
        FROM data_create_model 
        WHERE model_id = %s
        """
        cursor.execute(query, (model_id,))
        data = cursor.fetchall()

        # Proses data untuk memastikan bio_bert dalam format JSON
        processed_data = []
        for row in data:
            data_id, text, bio_bert = row
            if isinstance(bio_bert, str):
                try:
                    bio_bert = json.loads(bio_bert)  # Konversi string JSON ke dictionary
                except json.JSONDecodeError:
                    print(f"[ERROR] Gagal mengonversi bio_bert menjadi JSON: {bio_bert}")
                    continue
            processed_data.append({
                "id": data_id,
                "text": text,
                "bio_bert": bio_bert
            })

        return processed_data

    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan saat mengambil data BERT: {e}")
        return []

    finally:
        cursor.close()
        conn.close()

def get_models():
    """Fetch available models from the database."""
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models")
    models = cursor.fetchall()
    cursor.close()
    conn.close()
    return models

def get_provinsi_list():
    """Fetch all provinces from the database."""
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama_provinsi AS name FROM list_provinsi ORDER BY nama_provinsi ASC")
    provinsi_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return provinsi_list

def get_default_spacy_settings():
    """Fetch default training settings from the database."""
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM spacy_training_settings")
    settings = cursor.fetchone()
    cursor.close()
    conn.close()
    return settings

def get_default_bert_settings():
    """Fetch default training settings from the database."""
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bert_training_settings")
    settings = cursor.fetchone()
    cursor.close()
    conn.close()
    return settings

def get_model_name(model_id):
    """Get model name by ID"""
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
    model = cursor.fetchone()
    cursor.close()
    conn.close()
    return model['name'] if model else None

def fetch_locations_by_model(model_id):
    """
    Mengambil data lokasi berdasarkan ID yang ada di kolom `locations` dari tabel `model_locations`.
    Hanya mengambil data untuk level yang memiliki ID (provinsi, kabupaten, kecamatan, desa).
    """
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Ambil data lokasi dari tabel model_locations
    cursor.execute("SELECT locations FROM model_locations WHERE model_id = %s", (model_id,))
    location_data = cursor.fetchone()

    if not location_data:
        cursor.close()
        conn.close()
        return []  # Jika tidak ada data lokasi, kembalikan list kosong

    # Parse JSON lokasi
    locations = json.loads(location_data['locations'])

    # Siapkan hasil akhir
    result = []

    # Query untuk provinsi
    provinsi_ids = locations.get('provinsi_ids', [])
    if provinsi_ids:
        query = f"SELECT id, nama_provinsi FROM list_provinsi WHERE id IN ({','.join(['%s'] * len(provinsi_ids))}) ORDER BY nama_provinsi ASC"
        cursor.execute(query, provinsi_ids)
        result.extend(cursor.fetchall())

    # Query untuk kabupaten
    kabupaten_ids = locations.get('kabupaten_ids', [])
    if kabupaten_ids:
        query = f"SELECT id, nama_kabupaten FROM list_kabupaten WHERE id IN ({','.join(['%s'] * len(kabupaten_ids))}) ORDER BY nama_kabupaten ASC"
        cursor.execute(query, kabupaten_ids)
        result.extend(cursor.fetchall())

    # Query untuk kecamatan
    kecamatan_ids = locations.get('kecamatan_ids', [])
    if kecamatan_ids:
        query = f"SELECT id, nama_kecamatan FROM list_kecamatan WHERE id IN ({','.join(['%s'] * len(kecamatan_ids))}) ORDER BY nama_kecamatan ASC"
        cursor.execute(query, kecamatan_ids)
        result.extend(cursor.fetchall())

    # Query untuk desa
    desa_ids = locations.get('desa_ids', [])
    if desa_ids:
        query = f"SELECT id, nama_desa FROM list_desa WHERE id IN ({','.join(['%s'] * len(desa_ids))})  ORDER BY nama_desa ASC"
        cursor.execute(query, desa_ids)
        result.extend(cursor.fetchall())

    cursor.close()
    conn.close()
    return result

@training_bp.route('/training', methods=['GET'])
def training_page():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    conn = get_db_dict_connection()

    # Ambil parameter halaman
    page = int(request.args.get('page', 1))  # Halaman saat ini (default: 1)
    per_page = 5  # Jumlah data per halaman

    with conn.cursor() as cursor:
        # Hitung total data
        cursor.execute("SELECT COUNT(*) AS total FROM models")
        total_models = cursor.fetchone()['total']

        # Hitung offset untuk pagination
        offset = (page - 1) * per_page

        # Ambil data model dengan limit dan offset
        cursor.execute(f"""
            SELECT * FROM models
            ORDER BY created_at DESC
            LIMIT {per_page} OFFSET {offset}
        """)
        models = cursor.fetchall()

        cursor.execute("SELECT id, name FROM models WHERE spacy_model IS NULL")
        spacy_models = cursor.fetchall()

        cursor.execute("SELECT id, name FROM models WHERE bert_model IS NULL")
        bert_models = cursor.fetchall()

        # Ambil data training bert untuk setiap model
        for model in models:
            # Ambil 'detail' dan 'settings' dari tabel model_bert_detail
            cursor.execute("SELECT detail, settings FROM model_bert_detail WHERE model_id = %s", (model['id'],))
            bert_detail = cursor.fetchone()

            # Parsing detail
            if bert_detail and bert_detail['detail']:
                try:
                    model['bert_training_detail'] = json.loads(bert_detail['detail'])
                except Exception:
                    model['bert_training_detail'] = []
            else:
                model['bert_training_detail'] = []

            # Parsing settings
            if bert_detail and bert_detail['settings']:
                try:
                    model['bert_training_settings'] = json.loads(bert_detail['settings'])
                except Exception:
                    model['bert_training_settings'] = {}
            else:
                model['bert_training_settings'] = {}

            # Ambil data training spacy untuk setiap model
            cursor.execute("SELECT detail, settings FROM model_spacy_detail WHERE model_id = %s", (model['id'],))
            spacy_detail = cursor.fetchone()

            # Parsing detail spacy
            if spacy_detail and spacy_detail['detail']:
                try:
                    model['spacy_training_detail'] = json.loads(spacy_detail['detail'])
                except Exception:
                    model['spacy_training_detail'] = []
            else:
                model['spacy_training_detail'] = []

            # Parsing settings spacy
            if spacy_detail and spacy_detail['settings']:
                try:
                    model['spacy_training_settings'] = json.loads(spacy_detail['settings'])
                except Exception:
                    model['spacy_training_settings'] = {}
            else:
                model['spacy_training_settings'] = {}
            
            # Ambil data lokasi dari tabel model_locations
            cursor.execute("SELECT locations FROM model_locations WHERE model_id = %s", (model['id'],))
            location_data = cursor.fetchone()

            if location_data:
                # Gunakan fungsi fetch_locations_by_model untuk mendapatkan detail lokasi
                location_details = fetch_locations_by_model(model['id'])

                # Pisahkan data lokasi berdasarkan tingkatan
                provinsi_list = []
                kabupaten_list = []
                kecamatan_list = []
                desa_list = []

                for location in location_details:
                    if 'nama_provinsi' in location:
                        provinsi_list.append(location['nama_provinsi'])
                    elif 'nama_kabupaten' in location:
                        kabupaten_list.append(location['nama_kabupaten'])
                    elif 'nama_kecamatan' in location:
                        kecamatan_list.append(location['nama_kecamatan'])
                    elif 'nama_desa' in location:
                        desa_list.append(location['nama_desa'])

                # Tambahkan data lokasi ke model
                model['locations'] = {
                    'provinsi': provinsi_list,
                    'kabupaten': kabupaten_list,
                    'kecamatan': kecamatan_list,
                    'desa': desa_list
                }

                print(f"Model ID: {model['id']} - Locations: {model['locations']}")
            else:
                model['locations'] = {
                    'provinsi': [],
                    'kabupaten': [],
                    'kecamatan': [],
                    'desa': []
                }
    
    conn.close()

    # Hitung total halaman
    total_pages = (total_models + per_page - 1) // per_page

    # Ambil daftar provinsi
    provinsi_list = get_provinsi_list()

    # Ambil pengaturan default dari database
    default_spacy_settings = get_default_spacy_settings()
    default_bert_settings = get_default_bert_settings()

    return render_template(
        'training.html',
        active_page='training',
        models=models,
        spacy_models=spacy_models,
        bert_models=bert_models,
        provinsi_list=provinsi_list,
        default_spacy_settings=default_spacy_settings,
        default_bert_settings=default_bert_settings,
        page=page,
        total_pages=total_pages,
        per_page=per_page
    )

@training_bp.route('/create_model', methods=['POST'])
def create_model():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    # Cetak semua data yang dikirimkan untuk debugging
    print("Form Data Received:", request.form)
    
    name = request.form.get('name')  # Nama model
    provinsi_ids = request.form.getlist('provinsi[]')  # Ambil semua provinsi yang dipilih
    kabupaten_ids = request.form.getlist('kabupaten[]')  # Ambil semua kabupaten yang dipilih
    kecamatan_ids = request.form.getlist('kecamatan[]')  # Ambil semua kecamatan yang dipilih
    desa_ids = request.form.getlist('desa[]')  # Ambil semua desa yang dipilih

    if not name:
        flash('Model name is required', 'error')
        return redirect(url_for('training.training_page'))

    # Ganti spasi dengan underscore
    name = name.replace(" ", "_")
    # Hanya izinkan huruf dan underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Periksa apakah nama model sudah ada
    cursor.execute("SELECT COUNT(*) FROM models WHERE name = %s", (name,))
    model_exists = cursor.fetchone()[0]

    if model_exists > 0:
        flash('Model name already exists. Please choose a different name.', 'error')
        return redirect(url_for('training.training_page'))

    try:
        # Simpan model baru
        cursor.execute("INSERT INTO models (name) VALUES (%s)", (name,))
        model_id = cursor.lastrowid

        # Buat data lokasi dalam format JSON
        locations = {
            "provinsi_ids": provinsi_ids,
            "kabupaten_ids": kabupaten_ids,
            "kecamatan_ids": kecamatan_ids,
            "desa_ids": desa_ids
        }

        # Simpan lokasi terkait model dalam format JSON
        cursor.execute(
            """
            INSERT INTO model_locations (model_id, locations)
            VALUES (%s, %s)
            """,
            (model_id, json.dumps(locations))
        )
        conn.commit()
        
        print(f"\n[Route Create Model] Generate data for model_id: {model_id}\n")
        source = "create_model"
        generate_data(source=source, num_entries=None, model_id=model_id, text_inputan=None)
        
        print(f"\n[Route Create Model] Generate Combination location for model_id: {model_id}\n")
        # Panggil fungsi generate_combinations_for_model untuk membuat kombinasi lokasi
        generate_combinations_for_model(model_id)

        cursor.execute("SELECT COUNT(*) FROM data_create_model WHERE model_id = %s", (model_id,))
        count = cursor.fetchone()[0]
        # Tambahkan "data" ke hasil count
        count_with_label = f"{count} data"
        print(f"Jumlah data_create_model untuk model_id {model_id}: {count_with_label}")

        cursor.execute(
            "UPDATE models SET bert_model = NULL, spacy_model = NULL, jaro_winkler_model = %s, database_count = %s WHERE id = %s",
            ("READY", count_with_label, model_id)
        )
        conn.commit()

        print(f"Model ID: {model_id}")

        BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
        BASE_MODEL_JARO_WINKLER = os.path.join(BASE_DIR, "model_jaro_winkler") 

        # Ambil nama model berdasarkan ID
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model_name = cursor.fetchone()
        if not model_name:
            raise ValueError(f"Model with ID {model_id} not found.")
        model_name = model_name[0]

        # Path file kombinasi
        combination_file = os.path.join(BASE_MODEL_JARO_WINKLER, f"{model_name}_combinations.txt")
        print(f"Combination File Path: {combination_file}")

        # Periksa keberadaan file
        if not os.path.exists(combination_file):
            print(f"[ERROR] File not found: {combination_file}")
            raise FileNotFoundError(f"Combination file not found: {combination_file}")

        # Hitung jumlah baris tidak kosong
        non_empty_lines = count_non_empty_lines(combination_file)
        print(f"Non-empty lines: {non_empty_lines}")

        # Update database
        cursor.execute(
            "UPDATE models SET jaro_location_combination = %s WHERE id = %s",
            (non_empty_lines, model_id)
        )
        conn.commit()

    except Exception as e:
        # Rollback jika terjadi error
        if conn:
            conn.rollback()
        print(f"Error: {e}")
        flash("Terjadi kesalahan saat membuat model.", "danger")
        return redirect(url_for('training.training_page'))

    finally:
        # Pastikan koneksi ditutup hanya sekali
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('training.training_page'))

@training_bp.route('/training_bert_model', methods=['POST'])
def training_bert_model():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    # Cetak isi dari request.form untuk debugging
    print("Form Data Received:", request.form)

    # Ambil data dari form dan konversi ke tipe data yang sesuai
    model_id = request.form.get('model')
    data_used = int(request.form.get('data_used'))  # Konversi ke integer
    
    if not model_id:
        flash('Please select a model.', 'error')
        return redirect(url_for('training.training_page'))
    if data_used < 10:
        flash('Number of data used must be at least 10.', 'error')
        return redirect(url_for('training.training_page'))

    epochs = int(request.form.get('epochs'))
    test_size = float(request.form.get('test_size'))
    train_batch_size = int(request.form.get('train_batch_size'))
    eval_batch_size = int(request.form.get('eval_batch_size'))  
    weight_decay = float(request.form.get('weight_decay'))
    learning_rate = float(request.form.get('learning_rate'))
    early_stopping_patience = int(request.form.get('early_stopping_patience'))
    early_stopping_threshold = float(request.form.get('early_stopping_threshold'))

    # Get model name from ID
    model_name = get_model_name(model_id)
    if not model_name:
        flash('Model not found', 'error')
        return redirect(url_for('training.training_page'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        train_data = fetch_bert_train_data(model_id)

        train_bert_model(
            model_name, train_data, bert_training_settings={
                "model_id": model_id,
                "data_used": data_used,
                "epochs": epochs,
                "test_size": test_size,
                "train_batch_size": train_batch_size,
                "eval_batch_size": eval_batch_size,
                "weight_decay": weight_decay,
                "learning_rate": learning_rate,
                "early_stopping_patience": early_stopping_patience,
                "early_stopping_threshold": early_stopping_threshold
            }
        )
        
        # Update kolom bert_model menjadi READY
        cursor.execute("UPDATE models SET bert_model = %s WHERE id = %s", ("READY", model_id))
        conn.commit()

        try:
            # Ambil semua model yang sudah lengkap
            cursor.execute("""
                SELECT id 
                FROM models 
                WHERE bert_model = 'READY' AND spacy_model = 'READY' AND jaro_winkler_model = 'READY' AND complete_status = 'Incomplete'
            """)
            completed_models = cursor.fetchall()

            # Hapus data di tabel data_create_model untuk setiap model yang sudah lengkap
            for model in completed_models:
                model_id = model[0]
                
                cursor.execute("UPDATE models SET complete_status = 'Complete' WHERE id = %s", (model_id,))
                conn.commit()  # Commit perubahan

        except Exception as e:
            print(f"Error saat memeriksa dan menghapus data_create_model: {e}")

        print(f"Model ID: {model_id}")

        BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
        BASE_MODEL_DIR_BERT = os.path.join(BASE_DIR, "model_bert") 

        # Ambil nama model berdasarkan ID
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model_name = cursor.fetchone()
        if not model_name:
            raise ValueError(f"Model with ID {model_id} not found.")
        model_name = model_name[0]

        # Path file kombinasi
        bert_file = os.path.join(BASE_MODEL_DIR_BERT, f"{model_name}")
        print(f"Combination File Path: {bert_file}")

        # Periksa keberadaan file
        if not os.path.exists(bert_file):
            print(f"[ERROR] File not found: {bert_file}")
            raise FileNotFoundError(f"Bert file not found: {bert_file}")

        # Hitung jumlah baris tidak kosong
        bert_size = get_folder_size(bert_file)
        formatted_size = format_size(bert_size)
        print(f"Folder size: {formatted_size}")

        # Update database
        cursor.execute(
            "UPDATE models SET bert_size = %s WHERE id = %s",
            (formatted_size, model_id)
        )
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Training error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('training.training_page'))

@training_bp.route('/training_spacy_model', methods=['POST'])
def training_spacy_model():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    # Cetak isi dari request.form untuk debugging
    print("\nForm Data Received:", request.form)

    # Ambil data dari form dan konversi ke tipe data yang sesuai
    model_id = request.form.get('model')
    data_used = int(request.form.get('data_used'))  # Konversi ke integer

    print(f"\nmodel_id: {model_id}")
    print(f"data_used: {data_used}\n")
    
    if not model_id:
        flash('Please select a model.', 'error')
        return redirect(url_for('training.training_page'))
    if data_used < 10:
        flash('Number of data used must be at least 10.', 'error')
        return redirect(url_for('training.training_page'))

    epochs = int(request.form.get('epochs'))
    test_size = float(request.form.get('test_size'))
    dropout = float(request.form.get('dropout'))
    batch_size_start = int(request.form.get('batch_size_start'))
    batch_size_end = int(request.form.get('batch_size_end'))
    batch_rate = float(request.form.get('batch_rate'))
    learning_rate = float(request.form.get('learning_rate'))

    # Get model name from ID
    model_name = get_model_name(model_id)
    if not model_name:
        flash('Model not found', 'error')
        return redirect(url_for('training.training_page'))
    
    print(f"Train Spacy Routes. Try train spacy model():")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        train_data = fetch_spacy_train_data(model_id)

        train_spacy_model(
            model_name, train_data, spacy_training_settings={
                "model_id": model_id,
                "data_used": data_used,
                "epochs": epochs,
                "test_size": test_size,
                "dropout": dropout,
                "batch_size_start": batch_size_start,
                "batch_size_end": batch_size_end,
                "batch_rate": batch_rate,
                "learning_rate": learning_rate
            }
        )

        # Update kolom spacy_model menjadi READY
        cursor.execute("UPDATE models SET spacy_model = %s WHERE id = %s", ("READY", model_id))
        conn.commit()

        try:
            # Ambil semua model yang sudah lengkap
            cursor.execute("""
                SELECT id 
                FROM models 
                WHERE bert_model = 'READY' AND spacy_model = 'READY' AND jaro_winkler_model = 'READY' AND complete_status = 'Incomplete'
            """)
            completed_models = cursor.fetchall()

            # Hapus data di tabel data_create_model untuk setiap model yang sudah lengkap
            for model in completed_models:
                model_id = model[0]
                
                cursor.execute("UPDATE models SET complete_status = 'Complete' WHERE id = %s", (model_id,))

        except Exception as e:
            print(f"Error saat memeriksa dan menghapus data_create_model: {e}")

        print(f"Model ID: {model_id}")

        # Hitung jumlah baris tidak kosong untuk kombinasi
        BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
        BASE_MODEL_DIR_SPACY = os.path.join(BASE_DIR, "model_spacy") 

        # Ambil nama model berdasarkan ID
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model_name = cursor.fetchone()
        if not model_name:
            raise ValueError(f"Model with ID {model_id} not found.")
        model_name = model_name[0]

        # Path file kombinasi
        spacy_file = os.path.join(BASE_MODEL_DIR_SPACY, f"{model_name}")
        print(f"Combination File Path: {spacy_file}")

        # Periksa keberadaan file
        if not os.path.exists(spacy_file):
            print(f"[ERROR] File not found: {spacy_file}")
            raise FileNotFoundError(f"Spacy file not found: {spacy_file}")

        # Hitung jumlah baris tidak kosong
        spacy_size = get_folder_size(spacy_file)
        formatted_size = format_size(spacy_size)
        print(f"Folder size: {formatted_size}")

        # Update database
        cursor.execute(
            "UPDATE models SET spacy_size = %s WHERE id = %s",
            (formatted_size, model_id)
        )
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Training error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('training.training_page'))

@training_bp.route('/get_locations', methods=['GET'])
def get_locations():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    level = request.args.get('level')  # Level: provinsi, kabupaten, kecamatan, desa
    parent_ids = request.args.get('parent_id')  # ID parent (id_provinsi, id_kabupaten, id_kecamatan)

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    try:
        if level == 'kabupaten':
            query = f"SELECT id, nama_kabupaten AS name FROM list_kabupaten WHERE id_provinsi IN ({parent_ids}) ORDER BY nama_kabupaten ASC"
            cursor.execute(query)
        elif level == 'kecamatan':
            query = f"SELECT id, nama_kecamatan AS name FROM list_kecamatan WHERE id_kabupaten IN ({parent_ids}) ORDER BY nama_kecamatan ASC"
            cursor.execute(query)
        elif level == 'desa':
            query = f"SELECT id, nama_desa AS name FROM list_desa WHERE id_kecamatan IN ({parent_ids}) ORDER BY nama_desa ASC"
            cursor.execute(query)
        else:
            return {"error": "Invalid level"}, 400

        locations = cursor.fetchall()
        return {"locations": locations}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        cursor.close()
        conn.close()

@training_bp.route('/delete_bert_model', methods=['POST'])
def delete_bert_model():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    # Cetak semua data yang dikirimkan untuk debugging
    print("Form Data Received:", request.form)
    
    model_id = request.form.get('model_id')  # ID model yang akan dihapus

    BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
    # Path constants
    BASE_MODEL_DIR_BERT = os.path.join(BASE_DIR, "model_bert")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ambil nama model berdasarkan ID
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model = cursor.fetchone()
        if not model:
            flash("Model not found", "error")
            return redirect(url_for('training.training_page'))

        model_name = model[0]  # Nama model, misalnya "Jawa_Tengah"
        print(f"Deleting bert model from model: {model_name}")

        # Hapus folder model Bert
        bert_folder = os.path.join(BASE_MODEL_DIR_BERT, model_name)
        if os.path.exists(bert_folder):
            shutil.rmtree(bert_folder)
            print(f"Deleted folder: {bert_folder}")
        else:
            print(f"Folder not found: {bert_folder}")

        # Hapus data di tabel model_bert_detail
        cursor.execute("DELETE FROM model_bert_detail WHERE model_id = %s", (model_id,))
        print(f"Deleted Table model_bert_detail With ID: {model_id,}")

        # Update kolom bert_model, bert_size, dan complete_status di tabel models
        cursor.execute("""
            UPDATE models
            SET bert_model = NULL, 
                bert_size = NULL, 
                complete_status = 'Incomplete'
            WHERE id = %s
        """, (model_id,))
        conn.commit()

        # hapus data di tabel data_create_model yang digunakan untuk training bert
        cursor.execute("""
            UPDATE data_create_model
            SET bert_train_used = NULL
            WHERE model_id = %s
        """, (model_id,))
        conn.commit()

        print("Model Bert deleted successfully and database updated.")
        flash("Model Bert deleted successfully", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error deleting Bert model from model: {e}")
        flash(f"Error deleting Bert model from model: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('training.training_page'))

@training_bp.route('/delete_spacy_model', methods=['POST'])
def delete_spacy_model():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    # Cetak semua data yang dikirimkan untuk debugging
    print("Form Data Received:", request.form)
    
    model_id = request.form.get('model_id')  # ID model yang akan dihapus

    BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
    # Path constants
    BASE_MODEL_DIR_SPACY = os.path.join(BASE_DIR, "model_spacy")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ambil nama model berdasarkan ID
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model = cursor.fetchone()
        if not model:
            flash("Model not found", "error")
            return redirect(url_for('training.training_page'))

        model_name = model[0]  # Nama model, misalnya "Jawa_Tengah"
        print(f"Deleting spacy model from model: {model_name}")

        # Hapus folder model Spacy
        spacy_folder = os.path.join(BASE_MODEL_DIR_SPACY, model_name)
        if os.path.exists(spacy_folder):
            shutil.rmtree(spacy_folder)
            print(f"Deleted folder: {spacy_folder}")
        else:
            print(f"Folder not found: {spacy_folder}")

        # Hapus data di tabel model_spacy_detail
        cursor.execute("DELETE FROM model_spacy_detail WHERE model_id = %s", (model_id,))
        print(f"Deleted Table model_spacy_detail With ID: {model_id,}")

        # Update kolom spacy_model, spacy_size, dan complete_status di tabel models
        cursor.execute("""
            UPDATE models
            SET spacy_model = NULL, 
                spacy_size = NULL, 
                complete_status = 'Incomplete'
            WHERE id = %s
        """, (model_id,))
        conn.commit()

        # hapus data di tabel data_create_model yang digunakan untuk training spacy
        cursor.execute("""
            UPDATE data_create_model
            SET spacy_train_used = NULL
            WHERE model_id = %s
        """, (model_id,))
        conn.commit()

        print("Model Spacy deleted successfully and database updated.")
        flash("Model Spacy deleted successfully", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error deleting Spacy model from model: {e}")
        flash(f"Error deleting Spacy model from model: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('training.training_page'))

@training_bp.route('/delete_model', methods=['POST'])
def delete_model():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    # Cetak semua data yang dikirimkan untuk debugging
    print("Form Data Received:", request.form)
    
    model_id = request.form.get('model_id')  # ID model yang akan dihapus

    BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
    # Path constants
    BASE_MODEL_DIR_SPACY = os.path.join(BASE_DIR, "model_spacy")
    BASE_MODEL_DIR_BERT = os.path.join(BASE_DIR, "model_bert")
    BASE_MODEL_JARO_WINKLER = os.path.join(BASE_DIR, "model_jaro_winkler")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ambil nama model berdasarkan ID
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model = cursor.fetchone()
        if not model:
            flash("Model not found", "error")
            return redirect(url_for('training.training_page'))

        model_name = model[0]  # Nama model, misalnya "Jawa_Tengah"
        print(f"Deleting model: {model_name}")

        # Hapus file model Jaro Winkler
        jaro_winkler_file = os.path.join(BASE_MODEL_JARO_WINKLER, f"{model_name}_combinations.txt")
        if os.path.exists(jaro_winkler_file):
            os.remove(jaro_winkler_file)
            print(f"Deleted file: {jaro_winkler_file}")
        else:
            print(f"File not found: {jaro_winkler_file}")

        # Hapus folder model Spacy
        spacy_folder = os.path.join(BASE_MODEL_DIR_SPACY, model_name)
        if os.path.exists(spacy_folder):
            shutil.rmtree(spacy_folder)
            print(f"Deleted folder: {spacy_folder}")
        else:
            print(f"Folder not found: {spacy_folder}")

        # Hapus folder model Bert
        bert_folder = os.path.join(BASE_MODEL_DIR_BERT, model_name)
        if os.path.exists(bert_folder):
            shutil.rmtree(bert_folder)
            print(f"Deleted folder: {bert_folder}")
        else:
            print(f"Folder not found: {bert_folder}")
            
        # Cek apakah region_model di tabel detection_mode sama dengan nama model
        cursor.execute("SELECT region_model FROM detection_mode WHERE region_model = %s", (model_name,))
        detection_mode_entry = cursor.fetchone()

        if detection_mode_entry:
            # Jika region_model cocok dengan nama model, hapus nilai region_model (set NULL)
            cursor.execute("""
                UPDATE detection_mode
                SET model_id = NULL, region_model = NULL
                WHERE region_model = %s
            """, (model_name,))
            conn.commit()
            print(f"Region model '{model_name}' di tabel detection_mode telah dihapus (set NULL).")
        
        # Hapus data di tabel data_create_model
        cursor.execute("DELETE FROM data_create_model WHERE model_id = %s", (model_id,))
        print(f"Deleted Table Data Create Model WIth ID: {model_id,}")

        # Hapus data di tabel model_bert_detail
        cursor.execute("DELETE FROM model_bert_detail WHERE model_id = %s", (model_id,))
        print(f"Deleted Table model_bert_detail With ID: {model_id,}")

        # Hapus data di tabel model_spacy_detail
        cursor.execute("DELETE FROM model_spacy_detail WHERE model_id = %s", (model_id,))
        print(f"Deleted Table model_spacy_detail With ID: {model_id,}")

        # Hapus data di tabel model_locations terlebih dahulu
        cursor.execute("DELETE FROM model_locations WHERE model_id = %s", (model_id,))
        print(f"Deleted Table model_location With ID: {model_id,}")

        # Hapus data di tabel models
        cursor.execute("DELETE FROM models WHERE id = %s", (model_id,))
        print(f"Deleted Table models With ID: {model_id,}")
        
        conn.commit()
        print("Model and related locations deleted successfully.")
        flash("Model deleted successfully", "success")
    except Exception as e:
        conn.rollback()
        print(f"Error deleting model: {e}")
        flash(f"Error deleting model: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('training.training_page'))