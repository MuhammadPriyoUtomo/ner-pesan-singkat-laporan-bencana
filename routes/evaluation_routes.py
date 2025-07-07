import pymysql, json
from flask import Blueprint, render_template, redirect, url_for
from helper.utils import get_navbar_status
from helper.db_utils import get_db_connection

evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route('/evaluate_matrix')
def evaluate_matrix():
    
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

    # Koneksi ke database
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # Ambil data evaluasi dari tabel evaluation_per_report
    cursor.execute("SELECT * FROM evaluation_per_report")
    hasil_evaluasi = cursor.fetchall()

    mismatched_ids_report = set()
    # Konversi kolom mismatched_ids dari JSON string ke dictionary
    for row in hasil_evaluasi:
        if row['mismatched_ids']:
            row['mismatched_ids'] = json.loads(row['mismatched_ids'])
            mismatched_ids_report.update(row['mismatched_ids']['pred_report_actual_bukan'])
            mismatched_ids_report.update(row['mismatched_ids']['pred_bukan_actual_report'])

    # Ambil data dari tabel hasil_deteksi berdasarkan mismatched IDs untuk Per Report
    if mismatched_ids_report:
        cursor.execute(
            "SELECT id, hasil_ekstraksi, report_status FROM hasil_ekstraksi WHERE id IN %s",
            (tuple(mismatched_ids_report),)
        )
        hasil_deteksi_report = cursor.fetchall()
    else:
        hasil_deteksi_report = []

    # Ambil data evaluasi per entity dari tabel evaluation_per_entity
    cursor.execute("SELECT * FROM evaluation_per_entity")
    hasil_evaluasi_per_entity = cursor.fetchall()

    mismatched_ids_entity = set()
    # Konversi kolom mismatched_ids dari JSON string ke dictionary
    for row in hasil_evaluasi_per_entity:
        if row['mismatched_ids']:
            row['mismatched_ids'] = json.loads(row['mismatched_ids'])
            mismatched_ids_entity.update(row['mismatched_ids']['pred_false_actual_true'])
            mismatched_ids_entity.update(row['mismatched_ids']['pred_true_actual_false'])

    # Ambil data dari tabel hasil_deteksi berdasarkan mismatched IDs untuk Per Entity
    if mismatched_ids_entity:
        cursor.execute(
            "SELECT id, hasil_ekstraksi, report_status FROM hasil_ekstraksi WHERE id IN %s",
            (tuple(mismatched_ids_entity),)
        )
        hasil_deteksi_entity = cursor.fetchall()
    else:
        hasil_deteksi_entity = []

    # Tutup koneksi
    cursor.close()
    connection.close()

    # Kirim data ke template
    return render_template(
        'evaluasi.html',
        active_page='evaluasi',
        hasil_evaluasi=hasil_evaluasi,
        hasil_evaluasi_per_entity=hasil_evaluasi_per_entity,
        hasil_deteksi_report=hasil_deteksi_report,
        hasil_deteksi_entity=hasil_deteksi_entity,
    )