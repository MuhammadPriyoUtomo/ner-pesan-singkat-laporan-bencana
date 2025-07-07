from flask import Blueprint, render_template, request, redirect, url_for, flash
from helper.db_utils import get_db_dict_connection
from helper.utils import get_navbar_status

template_bp = Blueprint('template', __name__)

@template_bp.route('/kelola_template', methods=['GET'])
def kelola_template():
    
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
    page_template = int(request.args.get('page_template', 1))
    page_bencana = int(request.args.get('page_bencana', 1))
    page_urgensi = int(request.args.get('page_urgensi', 1))
    per_page = 10  # Jumlah data per halaman

    with conn.cursor() as cursor:
        # Pagination untuk Template Chat
        cursor.execute("SELECT COUNT(*) AS total FROM list_template_chat")
        total_templates = cursor.fetchone()['total']
        offset_template = (page_template - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM list_template_chat
            LIMIT {per_page} OFFSET {offset_template}
        """)
        templates = cursor.fetchall()

        # Pagination untuk Bencana
        cursor.execute("SELECT COUNT(*) AS total FROM list_bencana")
        total_bencana = cursor.fetchone()['total']
        offset_bencana = (page_bencana - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM list_bencana
            LIMIT {per_page} OFFSET {offset_bencana}
        """)
        bencana = cursor.fetchall()

        # Pagination untuk Urgensi
        cursor.execute("SELECT COUNT(*) AS total FROM list_urgensi")
        total_urgensi = cursor.fetchone()['total']
        offset_urgensi = (page_urgensi - 1) * per_page
        cursor.execute(f"""
            SELECT * FROM list_urgensi
            LIMIT {per_page} OFFSET {offset_urgensi}
        """)
        urgensis = cursor.fetchall()

    conn.close()

    # Hitung total halaman
    total_pages_template = (total_templates + per_page - 1) // per_page
    total_pages_bencana = (total_bencana + per_page - 1) // per_page
    total_pages_urgensi = (total_urgensi + per_page - 1) // per_page

    return render_template(
        'kelola_template.html',
        active_page='edit template',
        templates=templates,
        bencana=bencana,
        urgensis=urgensis,
        page_template=page_template,
        total_pages_template=total_pages_template,
        page_bencana=page_bencana,
        total_pages_bencana=total_pages_bencana,
        page_urgensi=page_urgensi,
        total_pages_urgensi=total_pages_urgensi,
        per_page=per_page
    )

# ========================== TEMPLATE ==========================
# Tambah Template
@template_bp.route('/template/add', methods=['POST'])
def add_template():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    chat_template = request.form['chat_template']
    report_status = request.form['report_status']
    conn = get_db_dict_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO list_template_chat (chat_template, report_status) VALUES (%s, %s)", (chat_template, report_status))
        new_id = cursor.lastrowid  # Gunakan lastrowid untuk mendapatkan ID terakhir
    conn.commit()
    conn.close()
    return {'status': 'success', 'id': new_id}


@template_bp.route('/template/toggle_active/<int:id>', methods=['POST'])
def toggle_active_template(id):
    
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
    with conn.cursor() as cursor:
        cursor.execute("SELECT is_active FROM list_template_chat WHERE id=%s", (id,))
        current_status = cursor.fetchone()['is_active']
        new_status = not current_status
        cursor.execute("UPDATE list_template_chat SET is_active=%s WHERE id=%s", (new_status, id))
    conn.commit()
    conn.close()
    return {'status': 'success', 'new_status': new_status}


# Edit Template
@template_bp.route('/template/edit/<int:id>', methods=['POST'])
def edit_template(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    chat_template = request.form['chat_template']
    report_status = request.form['report_status']
    is_active = request.form.get('is_active') == 'true'
    conn = get_db_dict_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE list_template_chat SET chat_template=%s, report_status=%s, is_active=%s WHERE id=%s",
            (chat_template, report_status, is_active, id)
        )
    conn.commit()
    conn.close()
    return {'status': 'success'}


# Delete Template
@template_bp.route('/template/delete/<int:id>', methods=['POST'])
def delete_template(id):
    
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
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM list_template_chat WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return {'status': 'success'}

# ========================== BENCANA ==========================
@template_bp.route('/bencana/add', methods=['POST'])
def add_bencana():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    bencana = request.form['bencana']
    conn = get_db_dict_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO list_bencana (bencana) VALUES (%s)", (bencana,))
        new_id = cursor.lastrowid  # Gunakan lastrowid untuk mendapatkan ID terakhir
    conn.commit()
    conn.close()
    return {'status': 'success', 'id': new_id}

@template_bp.route('/bencana/edit/<int:id>', methods=['POST'])
def edit_bencana(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    bencana = request.form['bencana']
    is_active = request.form.get('is_active') == 'true'
    conn = get_db_dict_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE list_bencana SET bencana=%s, is_active=%s WHERE id=%s",
            (bencana, is_active, id)
        )
    conn.commit()
    conn.close()
    return {'status': 'success'}

@template_bp.route('/bencana/delete/<int:id>', methods=['POST'])
def delete_bencana(id):
    
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
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM list_bencana WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return {'status': 'success'}

@template_bp.route('/bencana/toggle_active/<int:id>', methods=['POST'])
def toggle_active_bencana(id):
    
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
    with conn.cursor() as cursor:
        cursor.execute("SELECT is_active FROM list_bencana WHERE id=%s", (id,))
        current_status = cursor.fetchone()['is_active']
        new_status = not current_status
        cursor.execute("UPDATE list_bencana SET is_active=%s WHERE id=%s", (new_status, id))
    conn.commit()
    conn.close()
    return {'status': 'success', 'new_status': new_status}

# ========================== URGENSI ==========================
@template_bp.route('/urgensi/add', methods=['POST'])
def add_urgensi():
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    urgensi = request.form['urgensi']
    conn = get_db_dict_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO list_urgensi (urgensi) VALUES (%s)", (urgensi,))
        new_id = cursor.lastrowid  # Gunakan lastrowid untuk mendapatkan ID terakhir
    conn.commit()
    conn.close()
    return {'status': 'success', 'id': new_id}

@template_bp.route('/urgensi/edit/<int:id>', methods=['POST'])
def edit_urgensi(id):
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # Redirect ke halaman scraping jika result_mode adalah 'auto'
    if result_mode == 'manual':
        return redirect(url_for('main.index'))
    elif result_mode == 'results':
        return redirect(url_for('results.results'))
    elif result_mode == 'auto':
        return redirect(url_for('scraping.scraping_detection_page'))  # Gunakan nama endpoint default

    urgensi = request.form['urgensi']
    is_active = request.form.get('is_active') == 'true'
    conn = get_db_dict_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE list_urgensi SET urgensi=%s, is_active=%s WHERE id=%s",
            (urgensi, is_active, id)
        )
    conn.commit()
    conn.close()
    return {'status': 'success'}

@template_bp.route('/urgensi/delete/<int:id>', methods=['POST'])
def delete_urgensi(id):
    
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
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM list_urgensi WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return {'status': 'success'}

@template_bp.route('/urgensi/toggle_active/<int:id>', methods=['POST'])
def toggle_active_urgensi(id):
    
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
    with conn.cursor() as cursor:
        cursor.execute("SELECT is_active FROM list_urgensi WHERE id=%s", (id,))
        current_status = cursor.fetchone()['is_active']
        new_status = not current_status
        cursor.execute("UPDATE list_urgensi SET is_active=%s WHERE id=%s", (new_status, id))
    conn.commit()
    conn.close()
    return {'status': 'success', 'new_status': new_status}