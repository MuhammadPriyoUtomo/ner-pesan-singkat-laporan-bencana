from flask import Blueprint, redirect, url_for, jsonify, render_template, request, Response
from helper.utils import get_navbar_status
from helper.db_utils import get_db_connection, get_db_dict_connection
from programs.scraping import scraping_main
from programs.scraping_detection_worker import detection_worker
import logging, threading, json, time

scraping_bp = Blueprint('scraping', __name__)

# Variabel global untuk menghentikan scraping dan menyimpan status
scraping_thread = None
detection_thread = None

stop_scraping_flag = threading.Event()
stop_detection_flag = threading.Event()

scraping_status = {'is_running': False}  # Status scraping

@scraping_bp.route('/get_scraping_status', methods=['GET'])
def get_scraping_status():
    """
    Endpoint untuk mendapatkan status scraping dari database.
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        # Jika bukan AJAX request, lakukan redirect normal
        navbar_status = get_navbar_status()
        result_mode = navbar_status.get('result_mode')
        
        if result_mode == 'model':
            return redirect(url_for('training.training_page'))
        elif result_mode == 'manual':
            return redirect(url_for('main.index'))
        elif result_mode == 'results':
            return redirect(url_for('results.results'))
    
    # Dapatkan status dari database (bukan dari variabel global)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT active FROM scraping_condition WHERE id = 1")
    result = cursor.fetchone()
    is_active = result[0] == 1 if result else False
    cursor.close()
    connection.close()
    
    # Perbarui variabel global sesuai dengan database
    global scraping_status
    scraping_status['is_running'] = is_active
    
    return jsonify({'is_running': is_active})

@scraping_bp.route('/scraping', methods=['GET'])
def scraping_detection_page():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))

    """
    Render the Scraping Detection page.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ambil region_model dari tabel detection_mode
    cursor.execute("SELECT region_model FROM detection_mode LIMIT 1")
    detection_mode = cursor.fetchone()
    selected_model_name = detection_mode[0] if detection_mode else None

    print(f"Detection Mode: {detection_mode}")
    print(f"Selected Model Name: {selected_model_name}")

    # Ambil semua model untuk dropdown
    cursor.execute("SELECT id, name FROM models WHERE complete_status = 'Complete'")
    models = cursor.fetchall()
    print(f"Models: {models}")

    cursor.close()
    conn.close()

    return render_template('scraping.html', active_page='scraping', selected_model_name=selected_model_name, models=models)

@scraping_bp.route('/start_scraping', methods=['POST'])
def start_scraping():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    
    connection = get_db_connection()
    cursor = connection.cursor()

    # Update atau insert mode dengan id = 1
    cursor.execute("""
        INSERT INTO scraping_condition (id, active)
        VALUES (1, 1)
        ON DUPLICATE KEY UPDATE active = 1
    """)
    connection.commit()
    
    # Update semua baris pada kolom has_unread_messages menjadi 0
    cursor.execute("""
        UPDATE chat_status
        SET has_unread_messages = 0
    """)
    connection.commit()

    cursor.close()
    connection.close()

    global scraping_thread, detection_thread, stop_scraping_flag, stop_detection_flag, scraping_status

    logging.debug("Received request to start scraping")

    # Reset flag stop_scraping_flag
    stop_scraping_flag.clear()
    stop_detection_flag.clear()

    # Perbarui status scraping
    scraping_status['is_running'] = True

    # Jalankan scraping di thread terpisah
    scraping_thread = threading.Thread(target=scraping_main, args=(stop_scraping_flag,))
    detection_thread = threading.Thread(target=detection_worker, args=(stop_detection_flag,))
    scraping_thread.start()
    detection_thread.start()

    logging.debug("Scraping process started.")
    return jsonify({'status': 'started'})

@scraping_bp.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    
    connection = get_db_connection()
    cursor = connection.cursor()

    # Update atau insert mode dengan id = 1
    cursor.execute("""
        INSERT INTO scraping_condition (id, active)
        VALUES (1, 0)
        ON DUPLICATE KEY UPDATE active = 0
    """)
    connection.commit()

    # Update semua baris pada kolom has_unread_messages menjadi 0
    cursor.execute("""
        UPDATE chat_status
        SET has_unread_messages = 0
    """)
    connection.commit()

    cursor.close()
    connection.close()

    global stop_scraping_flag, stop_detection_flag, scraping_thread, detection_thread, scraping_status

    # Set flag untuk menghentikan scraping
    stop_scraping_flag.set()
    stop_detection_flag.set()

    # Tunggu thread scraping selesai
    if scraping_thread and scraping_thread.is_alive():
        scraping_thread.join()
    if detection_thread and detection_thread.is_alive():
        detection_thread.join()

    # Perbarui status scraping
    scraping_status['is_running'] = False

    logging.debug("Scraping process stopped.")
    return jsonify({'status': 'stopped'})

@scraping_bp.route('/live_stream')
def live_stream():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))

    def event_stream():
        last_ids = set()
        while True:
            conn = get_db_dict_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nomor_pengirim, tanggal, chat, hasil_ekstraksi, report_status, timestamp
                FROM live_scraping
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            # Kirim data hanya jika ada perubahan (id baru)
            current_ids = set(row['id'] for row in rows)
            if current_ids != last_ids:
                data = json.dumps([dict(row) for row in rows])
                yield f"data: {data}\n\n"
                last_ids = current_ids
            time.sleep(1)  # interval update

    return Response(event_stream(), mimetype="text/event-stream")

@scraping_bp.route('/hasil_scraping', methods=['GET'])
def hasil_scraping():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))

    """
    Menampilkan hasil scraping yang sudah diproses dengan pagination.
    """
    page = int(request.args.get('page', 1))  # Halaman saat ini (default: 1)
    if page < 1:  # Validasi nilai page
        page = 1

    per_page = 10  # Jumlah data per halaman

    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # Hitung total data yang sudah diproses
    cursor.execute("SELECT COUNT(*) AS total FROM hasil_scraping")
    total_data = cursor.fetchone()['total']

    # Hitung offset untuk pagination
    offset = (page - 1) * per_page

    # Ambil data yang sudah diproses, diurutkan secara descending berdasarkan tanggal
    cursor.execute("""
        SELECT id, nomor_pengirim, tanggal, chat, hasil_ekstraksi, report_status, timestamp
        FROM hasil_scraping
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    results = cursor.fetchall()

    # print(f"\nResult Raws: {results}\n")

    # Parse hasil_ekstraksi dari JSON string ke Python object
    for row in results:
        first_parse = json.loads(row['hasil_ekstraksi'])
        
        # Periksa apakah ada properti hasil_ekstraksi di dalam objek yang sudah di-parse
        if 'hasil_ekstraksi' in first_parse and first_parse['hasil_ekstraksi']:
            # Double parsing untuk mengakses disaster dan location
            actual_data = json.loads(first_parse['hasil_ekstraksi'])
            row['hasil_ekstraksi'] = {
                'disaster': actual_data.get('disaster', {}),
                'location': actual_data.get('location', {})
            }
        else:
            # Jika tidak perlu double parsing (struktur data berbeda)
            # atau first_parse sudah memiliki properti disaster dan location langsung
            if 'disaster' in first_parse or 'location' in first_parse:
                row['hasil_ekstraksi'] = first_parse
            else:
                # Fallback jika struktur tidak dikenali
                row['hasil_ekstraksi'] = {
                    'disaster': {'text': 'Tidak ditemukan', 'source': 'N/A'},
                    'location': {'text': 'Tidak ditemukan', 'source': 'N/A'}
                }

    cursor.close()
    conn.close()

    # print(f"\nResults fetched for page {page}: {results}\n")

    # Hitung total halaman
    total_pages = (total_data + per_page - 1) // per_page

    return render_template(
        'hasil_scraping.html',
        results=results,
        page=page,
        active_page='hasil scraping',
        total_pages=total_pages
    )

@scraping_bp.route('/delete/<int:id>', methods=['POST'])
def delete_result(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM hasil_scraping WHERE id = %s", (id,))
        connection.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        cursor.close()
        connection.close()

@scraping_bp.route('/manage_numbers', methods=['GET'])
def manage_numbers():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    
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
    cursor.execute("SELECT COUNT(*) AS total FROM chat_status")
    total_data = cursor.fetchone()['total']

    # Hitung offset untuk pagination
    offset = (page - 1) * per_page

    # Ambil data nomor dengan pagination
    cursor.execute("""
        SELECT id, sender_number, has_unread_messages, timestamp
        FROM chat_status
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    numbers = cursor.fetchall()

    cursor.close()
    conn.close()

    # Hitung total halaman
    total_pages = (total_data + per_page - 1) // per_page

    return render_template(
        'manage_numbers.html',
        numbers=numbers,
        page=page,
        total_pages=total_pages,
        active_page='manage_numbers'
    )

@scraping_bp.route('/delete_number/<int:id>', methods=['POST'])
def delete_number(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman utama jika mode manual
    if result_mode == 'model':
        return redirect(url_for('training.training_page'))
    elif result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    
    """
    Menghapus nomor dari database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chat_status WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        cursor.close()
        conn.close()