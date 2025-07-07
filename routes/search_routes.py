from flask import Blueprint, request, jsonify
from helper.db_utils import get_db_connection

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search():
    query = request.args.get('query', '')
    connection = get_db_connection()
    cursor = connection.cursor()

    parts = [p.strip() for p in query.split(',') if p.strip()]
    num_parts = len(parts)

    if num_parts == 0:
        return jsonify([])

    search_conditions = []
    values = []

    # Jika hanya ada 1 komponen, cocokkan ke semua level
    if num_parts == 1:
        part = parts[0]
        search_conditions.append("""
            (list_desa.nama_desa LIKE %s OR
             list_kecamatan.nama_kecamatan LIKE %s OR
             list_kabupaten.nama_kabupaten LIKE %s OR
             list_provinsi.nama_provinsi LIKE %s)
        """)
        values.extend([f"%{part}%"] * 4)

    # Jika ada lebih dari 1 komponen, cocokkan sesuai level bertingkat
    else:
        search_pairs = [
            ['list_desa.nama_desa', 'list_kecamatan.nama_kecamatan'],
            ['list_kecamatan.nama_kecamatan', 'list_kabupaten.nama_kabupaten'],
            ['list_kabupaten.nama_kabupaten', 'list_provinsi.nama_provinsi'],
        ]
        
        for i, part in enumerate(parts):
            if i < len(search_pairs):
                col1, col2 = search_pairs[i]
                search_conditions.append(f"({col1} LIKE %s OR {col2} LIKE %s)")
                values.extend([f"%{part}%"] * 2)
            else:
                # Jika lebih banyak komponen, cocokkan ke level provinsi
                search_conditions.append("list_provinsi.nama_provinsi LIKE %s")
                values.append(f"%{part}%")

    # Gabungkan kondisi pencarian
    search_query = f"""
    SELECT    
        list_desa.id AS desa_id,
        list_desa.nama_desa,
        list_kecamatan.id AS kecamatan_id,
        list_kecamatan.nama_kecamatan,
        list_kabupaten.id AS kabupaten_id,
        list_kabupaten.nama_kabupaten,
        list_provinsi.id AS provinsi_id,
        list_provinsi.nama_provinsi
    FROM 
        list_desa
    JOIN 
        list_kecamatan ON list_desa.id_kecamatan = list_kecamatan.id
    JOIN 
        list_kabupaten ON list_kecamatan.id_kabupaten = list_kabupaten.id
    JOIN 
        list_provinsi ON list_kabupaten.id_provinsi = list_provinsi.id
    WHERE 
        {" AND ".join(search_conditions)}
    ORDER BY 
        list_desa.nama_desa ASC
    """

    cursor.execute(search_query, values)
    results = cursor.fetchall()

    cursor.close()
    connection.close()
    return jsonify(results)
    
@search_bp.route('/search_model')
def search_model():
    query = request.args.get('query', '')
    if not query.strip():
        return jsonify([])
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, text, model_id, bert_train_used, spacy_train_used
        FROM data_create_model
        WHERE text LIKE %s
        AND (bert_train_used = 1 OR spacy_train_used = 1)
        ORDER BY id ASC
    """, (f"%{query}%",))
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(results)