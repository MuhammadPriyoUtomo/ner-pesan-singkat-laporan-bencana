from helper.db_utils import get_db_connection

def get_navbar_status():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Periksa apakah tabel olah_data_asli memiliki data
    cursor.execute("SELECT COUNT(*) FROM data_olah_asli LIMIT 1")
    olah_data_asli_count = cursor.fetchone()[0]

    # Periksa apakah tabel hasil_ekstraksi memiliki data
    cursor.execute("SELECT COUNT(*) FROM hasil_ekstraksi LIMIT 1")
    hasil_ekstraksi_count = cursor.fetchone()[0]

    # Periksa mode input
    cursor.execute("SELECT input_mode FROM input_mode_status LIMIT 1")
    result_mode = cursor.fetchone()
    result_mode = result_mode[0] if result_mode else None

    # Periksa apakah tabel evaluation_per_report memiliki data
    cursor.execute("SELECT COUNT(*) FROM evaluation_per_report LIMIT 1")
    hasil_evaluasi_count = cursor.fetchone()[0]
    
    # Periksa apakah tabel hasil_ekstraksi memiliki data
    cursor.execute("SELECT COUNT(*) FROM models WHERE complete_status = 'Complete' LIMIT 1")
    models_count = cursor.fetchone()[0]

    # Tentukan apakah menu Evaluasi harus dinonaktifkan
    disable_evaluasi = hasil_evaluasi_count == 0

    # scraping condition
    cursor.execute("SELECT active FROM scraping_condition WHERE id = 1")
    scraping_result = cursor.fetchone()
    # Ambil nilai dari tuple, jika ada hasil
    scraping_condition = scraping_result[0] if scraping_result else 0

    # Cek apakah ada data dengan selected = 1 di tabel results
    cursor.execute("SELECT filename FROM results WHERE selected = 1")
    selected_result = cursor.fetchone()
    has_selected_result = selected_result is not None  # True jika ada data, False jika tidak

    cursor.close()
    connection.close()

    return {
        'disable_hasil_asli': olah_data_asli_count == 0,
        'disable_hasil_deteksi': hasil_ekstraksi_count == 0,
        'disable_evaluasi': disable_evaluasi,
        'result_mode': result_mode,
        'disable_models': models_count == 0,
        'scraping_condition': scraping_condition,
        'has_selected_result': has_selected_result 
    }