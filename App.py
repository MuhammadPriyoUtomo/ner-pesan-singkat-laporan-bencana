from flask import Flask, render_template, jsonify
from waitress import serve
from routes import blueprints
from dotenv import load_dotenv
from helper.utils import get_navbar_status
from helper.db_utils import get_db_connection
from helper.chromedriver_update import chromedriver_update
import logging, json, helper.App_config as App_config, os, socket

app = Flask(__name__)

load_dotenv()

# ========================
# Non-caching untuk semua response
# ========================
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# ========================
# Secret key untuk session
# ========================
app.secret_key = os.getenv('SECRET_KEY')

# ========================
# Register Blueprints
# ========================
for blueprint in blueprints:
    app.register_blueprint(blueprint)

# ========================
# Route tambahan jika JS nonaktif
# ========================
@app.route('/javascript-disabled')
def javascript_disabled():
    print("Route /javascript-disabled hit!")
    return render_template('javascript_disabled.html')

# ========================
# Tambahkan filter custom ke Jinja
# ========================
@app.template_filter('fromjson')
def fromjson(value):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}

# ========================
# Load konfigurasi proyek
# ========================
app.config.from_object(App_config)

# ========================
# Logging Setup - suppress werkzeug & static log
# ========================
# class StaticFilter(logging.Filter):
#     def filter(self, record):
#         return 'GET /static/' not in record.getMessage()

# Atur logger Werkzeug
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)  # Atur ke INFO atau ERROR sesuai kebutuhan

# Tambahkan filter untuk menghilangkan static files
# werkzeug_logger.addFilter(StaticFilter())

# Logging custom Anda
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ========================
# Inject status navbar (jika ada)
# ========================
@app.context_processor
def inject_navbar_status():
    return get_navbar_status()

# ========================
# Route: requirements reader
# ========================
@app.route('/get_requirements', methods=['GET'])
def get_requirements():
    try:
        # # Baca file dengan encoding UTF-16 LE
        # with open('requirements.txt', 'r', encoding='utf-16') as file:
        #     requirements = file.readlines()
        with open('requirements.txt', 'r', encoding='utf-8') as file:
            requirements = file.readlines()
        requirements = [f"{i + 1}. {req.strip()}" for i, req in enumerate(requirements) if req.strip()]
        return jsonify({'requirements': requirements})
    except FileNotFoundError:
        return jsonify({'error': 'File requirements.txt tidak ditemukan'}), 404
    except UnicodeDecodeError as e:
        return jsonify({'error': f'Error decoding file: {str(e)}'}), 500

connection = get_db_connection()
cursor = connection.cursor()

# Update atau insert mode dengan id = 1
cursor.execute("""
    INSERT INTO scraping_condition (id, active)
    VALUES (1, 0)
    ON DUPLICATE KEY UPDATE active = 0
""")
connection.commit()

cursor.close()
connection.close()

@app.errorhandler(Exception)
def handle_exception(e):
    # Untuk error HTTP (404, 500, dll)
    code = getattr(e, 'code', 500)
    return render_template("error.html", error_message=str(e)), code

def check_internet(host="8.8.8.8", port=53, timeout=3):
    """Cek koneksi internet dengan mencoba konek ke DNS Google."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

# Setup fugnsional bert dan chromedriver
if check_internet():
    chromedriver_update()
else:
    print("[WARNING] Tidak ada koneksi internet, skip update chromedriver.")
    # Jika ingin program benar-benar wajib internet, bisa exit:
    # import sys; sys.exit(1)

# ========================
# Main entry point
# ========================
if __name__ == '__main__':

    app.run(debug=True, use_reloader=True, threaded=True) # Untuk development
    # serve(app, host='127.0.0.1', port=5000) # Untuk production