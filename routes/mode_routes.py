from flask import Blueprint, request, jsonify, redirect, url_for
from helper.utils import get_navbar_status
from helper.db_utils import get_db_connection
from helper.utils import get_navbar_status

mode_bp = Blueprint('mode', __name__)

@mode_bp.route('/set_input_mode', methods=['POST'])
def set_mode():

    data = request.get_json()
    mode = data.get('mode')

    print(f"Mode: {mode}")

    if mode not in ['model','manual', 'auto', 'results']:
        return jsonify({'error': 'Invalid mode'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Update atau insert mode dengan id = 1
    cursor.execute("""
        INSERT INTO input_mode_status (id, input_mode)
        VALUES (1, %s)
        ON DUPLICATE KEY UPDATE input_mode = VALUES(input_mode)
    """, (mode,))
    connection.commit()

    # Ambil mode terbaru dari database
    cursor.execute("SELECT input_mode FROM input_mode_status WHERE id = 1")
    result_mode = cursor.fetchone()
    result_mode = result_mode[0] if result_mode else None

    cursor.close()
    connection.close()

    return jsonify({'message': 'Input mode updated successfully', 'result_mode': result_mode})
    
@mode_bp.route('/set_detection_mode', methods=['POST'])
def set_detection_mode():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'results':
        return redirect(url_for('results.results'))  # Gunakan nama endpoint default
    
    data = request.get_json()
    detection_mode = data.get('detection_mode')

    print(f"Detection Mode: {detection_mode}")

    # Validasi input mode
    if detection_mode not in ['bert+spacy','bert','spacy','jaro','disabled'] and detection_mode is not None:
        return jsonify({'error': 'Invalid detection mode'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO detection_mode (id, mode)
        VALUES (1, %s)
        ON DUPLICATE KEY UPDATE mode = VALUES(mode)
    """, (detection_mode))
    print(f"Mengirimkan mode deteksi: {detection_mode}")

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'Detection mode updated successfully'})

@mode_bp.route('/set_region_detection_model', methods=['POST'])
def set_spacy_model():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'results':
        return redirect(url_for('results.results'))  # Gunakan nama endpoint default
    
    data = request.get_json()
    region_detection_model_id = data.get('region_detection_model_id')  # Ambil ID region
    region_detection_model_name = data.get('region_detection_model_name')  # Ambil nama model

    print(f"Region Detection Model ID: {region_detection_model_id}, Name: {region_detection_model_name}")

    if not region_detection_model_id or not region_detection_model_name:
        return jsonify({'error': 'Model Region tidak valid'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Update atau insert model Region ke tabel detection_mode
    cursor.execute("""
        UPDATE detection_mode 
        SET model_id = %s, region_model = %s 
        WHERE id = 1
    """, (region_detection_model_id, region_detection_model_name))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'Model Region updated successfully'})

@mode_bp.route('/get_detection_mode', methods=['GET'])
def get_detection_mode():

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'results':
        return redirect(url_for('results.results'))  # Gunakan nama endpoint default
    
    connection = get_db_connection()
    cursor = connection.cursor()

    # Ambil mode deteksi dari database
    cursor.execute("SELECT mode FROM detection_mode WHERE id = 1")
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    if result:
        # Konversi hasil tuple menjadi dictionary error????? undefined
        return jsonify({'detection_mode': result[0]}), 200
    else:
        # Default mode jika tidak ada data
        return jsonify({'message': 'Tidak ada mode deteksi yang disimpan di database'}), 404