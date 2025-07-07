from flask import Blueprint, render_template, redirect, url_for
from helper.db_utils import get_db_connection
from helper.utils import get_navbar_status

data_bp = Blueprint('data', __name__)

@data_bp.route('/data')
def data():
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    connection = get_db_connection()
    cursor = connection.cursor()

    # Ambil daftar tabel dari database
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    data_preview = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        # Ambil nama kolom dari tabel
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in cursor.description]
        
        if total_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            remaining_count = total_count - len(rows)  # Hitung jumlah data yang tersisa
            data_preview[table_name] = {
                'rows': [dict(zip(columns, row)) for row in rows],
                'columns': columns,
                'total_count': total_count,
                'remaining_count': remaining_count
            }
        else:
            # Jika tabel kosong, hanya tampilkan nama kolom
            data_preview[table_name] = {
                'rows': [],
                'columns': columns,
                'total_count': 0,
                'remaining_count': 0
            }

    cursor.close()
    connection.close()
    
    # Hitung jumlah tabel
    total_tables = len(tables)
    
    return render_template('data.html', data_preview=data_preview, total_tables=total_tables, active_page='data')