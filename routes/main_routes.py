from flask import Blueprint, render_template, request, redirect, url_for
from programs.generate_data import generate_data
from helper.utils import get_navbar_status
from helper.db_utils import get_db_connection
import os, shutil

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')
    models_count = navbar_status.get('disable_models')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default
    
    connection = get_db_connection()
    cursor = connection.cursor()

    # Ambil daftar model
    cursor.execute("SELECT id, name FROM models WHERE complete_status = 'Complete'")
    models = cursor.fetchall()
    models = [{"id": model[0], "name": model[1]} for model in models]

    print(f"Models fetched: {models}")

    cursor.close()
    connection.close()

    return render_template('index.html', models=models, active_page='home')
    
@main_bp.route('/generate_data', methods=['POST'])
def main_generate_data():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    source = "generate_data"
    num_entries = int(request.form.get('num_entries'))
    model_id = int(request.form.get('model_id'))
    num_status_reports = int(request.form.get('num_status_reports'))  # Ambil jumlah status report
    num_non_reports = int(request.form.get('num_non_reports'))  # Ambil jumlah bukan report

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
    model_name = cursor.fetchall()

    print(f"Model name fetched: {model_name}")

    # Update atau insert model Region ke tabel detection_mode
    cursor.execute("""
        UPDATE detection_mode SET region_model = %s WHERE id = 1
    """, (model_name,))
    connection.commit()

    if num_entries == 0 or model_id == 0 or num_status_reports == 0 or num_non_reports == 0:
        return redirect(url_for('main.index'))

    # Validasi jumlah total
    if num_status_reports + num_non_reports != num_entries:
        return "Jumlah Status Report dan Bukan Report harus sama dengan Jumlah Data.", 400

    # Validasi jumlah tidak boleh negatif atau nol
    if num_entries <= 0 or num_status_reports < 0 or num_non_reports < 0:
        return "Jumlah data tidak valid. Pastikan semua nilai lebih dari 0.", 400

    print(f"@main_bp.route('/generate_data'")
    print(f"Model ID: {model_id}")
    print(f"Source: {source}")
    print(f"Number of entries: {num_entries}")
    print(f"Number of status reports: {num_status_reports}")
    print(f"Number of non-reports: {num_non_reports}")

    # Pastikan fungsi generate_data mendukung parameter tambahan
    generate_data(
        source,
        num_entries=num_entries,
        model_id=model_id,
        num_status_reports=num_status_reports,
        num_non_reports=num_non_reports
    )


    # Perbaikan pada sintaks SQL dan parameter
    cursor.execute("INSERT INTO detection_mode (id, source) VALUES (1, %s) ON DUPLICATE KEY UPDATE source = VALUES(source)", (source,))

    connection.commit()
    cursor.close()
    connection.close()

    # Menghapus folder LogDetect dan membuat ulang folder kosong
    folder = "LogDetect"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

    return redirect(url_for('hasil.hasil_asli'))

@main_bp.route('/input_data', methods=['POST'])
def input_data():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    source = "text_input"  # Identitas sumber
    num_entries = int(1)
    text_inputan = request.form.get('isi_chat_pengaduan')

    if text_inputan == "":
        return redirect(url_for('main.index'))  

    print(f"Text inputan: {text_inputan}")
    print(f"Source: {source}")
    print(f"Number of entries: {num_entries}")

    generate_data(source, num_entries, text_inputan=text_inputan)

    connection = get_db_connection()
    cursor = connection.cursor()

    # Perbaikan pada sintaks SQL dan parameter
    cursor.execute("INSERT INTO detection_mode (id, source) VALUES (1, %s) ON DUPLICATE KEY UPDATE source = VALUES(source)", (source,))

    # print(cursor.mogrify("INSERT INTO mode_detection (source) VALUES (%s) ON DUPLICATE KEY UPDATE source = VALUES(source)", (source,)))

    connection.commit()
    cursor.close()
    connection.close()

    # Menghapus folder LogDetect dan membuat ulang folder kosong
    folder = "LogDetect"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

    return redirect(url_for('hasil.hasil_asli'))