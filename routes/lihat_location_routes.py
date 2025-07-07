from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from helper.utils import get_navbar_status
from helper.db_utils import get_db_dict_connection

lihat_location_bp = Blueprint('lihat_lokasi', __name__)

@lihat_location_bp.route('/lihat_lokasi', methods=['GET'])
def lihat_lokasi():
    """
    Route to display the locations page.
    """
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    """
    Menampilkan halaman manajemen nomor dengan pagination.
    """
    page = int(request.args.get('page', 1))  # Halaman saat ini (default: 1)
    if page < 1:  # Validasi nilai page
        page = 1

    per_page = 10  # Jumlah data per halaman

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Hitung total data nomor
    cursor.execute("SELECT COUNT(*) AS total FROM list_desa")
    total_data = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total_kecamatan FROM list_kecamatan")
    total_data_kecamatan = cursor.fetchone()['total_kecamatan']

    cursor.execute("SELECT COUNT(*) AS total_kabupaten FROM list_kabupaten")
    total_data_kabupaten = cursor.fetchone()['total_kabupaten']

    cursor.execute("SELECT COUNT(*) AS total_provinsi FROM list_provinsi")
    total_data_provinsi = cursor.fetchone()['total_provinsi']

    # Hitung offset untuk pagination
    offset = (page - 1) * per_page

    # Ambil data nomor dengan pagination
    cursor.execute("""
        SELECT 
            desa.id AS id_desa,
            desa.nama_desa,
            kecamatan.id AS id_kecamatan,
            kecamatan.nama_kecamatan,
            kabupaten.id AS id_kabupaten,
            kabupaten.nama_kabupaten,
            provinsi.id AS id_provinsi,
            provinsi.nama_provinsi
        FROM 
            list_desa desa
        JOIN 
            list_kecamatan kecamatan ON desa.id_kecamatan = kecamatan.id
        JOIN 
            list_kabupaten kabupaten ON kecamatan.id_kabupaten = kabupaten.id
        JOIN 
            list_provinsi provinsi ON kabupaten.id_provinsi = provinsi.id
        ORDER BY desa.id ASC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    numbers = cursor.fetchall()

    cursor.close()
    conn.close()

    # Hitung total halaman
    total_pages = (total_data + per_page - 1) // per_page

    return render_template(
        'lihat_data_lokasi.html',
        numbers=numbers,  # Data hasil query
        locations=numbers,  # Tambahkan alias untuk kejelasan
        page=page,
        total_pages=total_pages,
        total_data_desa=total_data,
        total_data_kecamatan=total_data_kecamatan,
        total_data_kabupaten=total_data_kabupaten,
        total_data_provinsi=total_data_provinsi,
        active_page='lihat lokasi',
    )