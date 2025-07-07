from flask import Blueprint, render_template, redirect, url_for, request
from helper.utils import get_navbar_status
from helper.db_utils import get_db_connection
import os, shutil

hasil_bp = Blueprint('hasil', __name__)

@hasil_bp.route('/hasil_asli')
def hasil_asli():
    
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

    # Ambil parameter halaman
    page = int(request.args.get('page', 1))  # Halaman saat ini (default: 1)
    per_page = 10  # Jumlah data per halaman

    connection = get_db_connection()
    cursor = connection.cursor()

    # Hitung total data
    cursor.execute("SELECT COUNT(*) as total FROM data_olah_asli")
    total_data = cursor.fetchone()[0]

    # Hitung offset untuk pagination
    offset = (page - 1) * per_page

    # Ambil data dengan limit dan offset
    cursor.execute("""
        SELECT data_olah_asli.id, data_olah_asli.text, data_olah_asli.annotations, 
               data_olah_asli.source, data_olah_asli.timestamp, data_olah_asli.model_id, 
               data_olah_asli.report_status, models.name AS model_name
        FROM data_olah_asli
        LEFT JOIN models ON data_olah_asli.model_id = models.id
        ORDER BY data_olah_asli.id ASC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    list_generate = cursor.fetchall()

    # Ubah hasil query menjadi list of dictionaries agar mudah diakses di template
    list_generate = [
        {
            "id": row[0],
            "text": row[1],
            "annotations": row[2],
            "source": row[3],
            "timestamp": row[4],
            "model_name": row[7] if row[7] else "",  # Gunakan "N/A" jika nama model tidak ditemukan
            "report_status": row[6]  # Tambahkan report_status ke dictionary
        }
        for row in list_generate
    ]

    # Periksa apakah tabel hasil_ekstraksi memiliki data
    cursor.execute("SELECT COUNT(*) as count FROM hasil_ekstraksi limit 1")
    list_ekstraksi = cursor.fetchone()[0]

    # Mengambil data dari tabel variabel_global
    cursor.execute("SELECT * FROM variabel_global")
    waktu_eksekusi = cursor.fetchall()

    # Ambil region_model dari tabel detection_mode
    cursor.execute("SELECT region_model FROM detection_mode LIMIT 1")
    detection_mode = cursor.fetchone()
    selected_model_name = detection_mode[0] if detection_mode else None

    # Ambil semua model untuk dropdown
    cursor.execute("SELECT id, name FROM models WHERE complete_status = 'Complete'")
    models = cursor.fetchall()

    cursor.close()
    connection.close()

    # Hitung total halaman
    total_pages = (total_data + per_page - 1) // per_page

    return render_template(
        'hasil_asli.html',
        models=models,
        selected_model_name=selected_model_name,
        list_generate=list_generate,
        list_ekstraksi=list_ekstraksi,
        waktu_eksekusi=waktu_eksekusi,
        page=page,
        total_data=total_data,
        total_pages=total_pages,
        per_page=per_page,
        active_page='hasil_asli'
    )

@hasil_bp.route('/hapus_data_deteksi', methods=['POST'])
def hapus_data_deteksi():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    connection = get_db_connection()
    cursor = connection.cursor()

    # Menghapus isi tabel hasil_ekstraksi_data
    cursor.execute("DELETE FROM hasil_ekstraksi")
    cursor.execute("ALTER TABLE hasil_ekstraksi AUTO_INCREMENT = 1")

    # Menghapus isi tabel evaluation_per_report
    cursor.execute("DELETE FROM evaluation_per_report")
    cursor.execute("ALTER TABLE evaluation_per_report AUTO_INCREMENT = 1")
    
    # Menghapus isi tabel evaluation_per_entity
    cursor.execute("DELETE FROM evaluation_per_entity")
    cursor.execute("ALTER TABLE evaluation_per_entity AUTO_INCREMENT = 1")

    # Menghapus nilai di kolom deteksi_execution_time pada tabel variabel_global
    cursor.execute("UPDATE variabel_global SET deteksi_execution_time = NULL, deteksi_average_execution_time = NULL")

    # Update results_status
    cursor.execute("UPDATE results_status SET status = 0 WHERE id = 1")

    cursor.execute("UPDATE detection_mode SET model_id = NULL, region_model = NULL")
    connection.commit()

    # Menghapus folder LogDetect dan membuat ulang folder kosong
    folder = "LogDetect"
    if os.path.exists(folder):
        shutil.rmtree(folder)  # Hapus folder beserta isinya
    os.makedirs(folder)  # Buat ulang folder kosong

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('hasil.hasil_asli'))

@hasil_bp.route('/reset_data', methods=['POST'])
def reset_data():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    connection = get_db_connection()
    cursor = connection.cursor()

    # Menghapus isi tabel data_olah_asli_data
    cursor.execute("DELETE FROM data_olah_asli")
    cursor.execute("ALTER TABLE data_olah_asli AUTO_INCREMENT = 1")

    # Menghapus isi tabel hasil_ekstraksi_data
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

    # Mengosongkan kolom region_model pada tabel detection_mode
    cursor.execute("UPDATE detection_mode SET region_model = ''")  # Atur ke string kosong

    # Update results_status
    cursor.execute("UPDATE results_status SET status = 0 WHERE id = 1")

    cursor.execute("UPDATE detection_mode SET model_id = NULL, region_model = NULL")
    connection.commit()

    # Menghapus folder LogDetect dan membuat ulang folder kosong
    folder = "LogDetect"
    if os.path.exists(folder):
        shutil.rmtree(folder)  # Hapus folder beserta isinya
    os.makedirs(folder)  # Buat ulang folder kosong

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('main.index'))
    