from helper.db_utils import get_db_connection
import os, requests, sys, time, zipfile, shutil

# ================================= Helper Functions =================================

def format_size(num):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"

def show_file_list_with_size(repo_id, file_list, base_url):
    print("\nDaftar file yang akan di-download dari HuggingFace:")
    for filename in file_list:
        url = base_url + filename
        try:
            resp_head = requests.head(url, allow_redirects=True)
            size = int(resp_head.headers.get('content-length', 0))
            print(f"  - {filename} ({format_size(size)})")
        except Exception:
            print(f"  - {filename} (ukuran tidak diketahui)")

# ================================= Model Downloading Functions =================================

def get_hf_file_list(repo_id):
    """Ambil daftar file dari HuggingFace repo secara dinamis. Jika gagal (misal repo private), return []."""
    api_url = f"https://huggingface.co/api/models/{repo_id}"
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        return [f['rfilename'] for f in data.get('siblings', [])]
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Tidak bisa mengakses repo HuggingFace '{repo_id}': {e}")
        return []

def is_model_complete(local_dir, repo_id):
    """Cek apakah semua file dari repo sudah ada di lokal."""
    if not os.path.isdir(local_dir):
        return False
    file_list = get_hf_file_list(repo_id)
    if not file_list:
        print(f"[WARNING] Repo HuggingFace '{repo_id}' tidak bisa diakses atau kosong. Skip proses download.")
        return True  # Anggap sudah "lengkap" agar proses download dilewati
    for filename in file_list:
        local_path = os.path.join(local_dir, filename)
        if not os.path.isfile(local_path):
            return False
    return True

def download_bert_model(local_dir, repo_id):
    base_url = f"https://huggingface.co/{repo_id}/resolve/main/"
    os.makedirs(local_dir, exist_ok=True)
    file_list = get_hf_file_list(repo_id)

    # Tampilkan daftar file dan ukuran sebelum download
    show_file_list_with_size(repo_id, file_list, base_url)
    print("\n[INFO] Mulai proses download...\n")

    for filename in file_list:
        local_path = os.path.join(local_dir, filename)
        url = base_url + filename

        # Pastikan subfolder dibuat
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Ambil ukuran file online (HEAD, fallback GET jika perlu)
        try:
            resp_head = requests.head(url, allow_redirects=True)
            online_size = int(resp_head.headers.get('content-length', 0))
            if online_size == 0:
                resp_head = requests.get(url, stream=True)
                online_size = int(resp_head.headers.get('content-length', 0))
                resp_head.close()
        except Exception:
            online_size = 0

        # Cek file lokal
        local_size = os.path.getsize(local_path) if os.path.isfile(local_path) else 0

        # Toleransi 1% untuk file > 50MB (50*1024*1024 = 52428800 bytes)
        toleransi = 0.01 if online_size > 52428800 else 0.0

        if local_size > 0 and online_size > 0:
            print(f"\n[INFO] {filename} | Lokal: {format_size(local_size)} | Online: {format_size(online_size)}")
            if abs(local_size - online_size) <= toleransi * online_size:
                print(f"[SKIP] {filename} sudah ada dan ukuran hampir sama (toleransi {toleransi*100:.0f}%), lewati download.\n")
                continue
            elif local_size < online_size:
                print(f"[RESUME] {filename} akan dilanjutkan dari {format_size(local_size)}.\n")
            else:
                print(f"[WARNING] {filename} lokal lebih besar dari online, akan diulang dari awal.\n")
                os.remove(local_path)
                local_size = 0
        else:
            if local_size == 0:
                print(f"[INFO] {filename} | Lokal: (tidak ada) | Online: {format_size(online_size)}\n")

        # Resume download jika perlu
        headers = {}
        mode = "wb"
        if local_size > 0 and online_size > 0 and local_size < online_size:
            headers['Range'] = f'bytes={local_size}-'
            mode = "ab"

        print(f"Downloading {filename} ...")
        resp = requests.get(url, stream=True, headers=headers)
        # Untuk resume, content-length hanya sisa byte, total = local_size + content-length
        if 'Range' in headers:
            total = online_size
        else:
            total = int(resp.headers.get('content-length', 0))

        if resp.status_code in [200, 206]:
            with open(local_path, mode) as f:
                downloaded = local_size
                start_time = time.time()
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = time.time() - start_time
                        speed = (downloaded - local_size) / elapsed if elapsed > 0 else 0
                        if online_size > 0:
                            percent = int(downloaded * 100 / online_size)
                            sys.stdout.write(
                                f"\r  Progress: {percent}% ({format_size(downloaded)}/{format_size(online_size)}) | {format_size(speed)}/s"
                            )
                            sys.stdout.flush()
                print()
            # Validasi akhir untuk file besar
            if online_size > 52428800:
                final_size = os.path.getsize(local_path)
                if abs(final_size - online_size) > 0.01 * online_size:
                    print(f"[WARNING] Ukuran file {filename} setelah download ({format_size(final_size)}) berbeda >1% dari server ({format_size(online_size)}).\n")
        else:
            print(f"Failed to download {filename} (status {resp.status_code})")
    print("Download selesai.")

# ================================= HuggingFace Dataset Functions =================================

def get_hf_dataset_file_list(repo_id):
    """Ambil daftar file dari HuggingFace dataset repo. Jika gagal, return []."""
    api_url = f"https://huggingface.co/api/datasets/{repo_id}"
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        return [f['rfilename'] for f in data.get('siblings', [])]
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Tidak bisa mengakses repo dataset HuggingFace '{repo_id}': {e}")
        return []
    
def download_file_with_progress(url, local_path):
    try:
        # Cek apakah file sudah ada dan ukurannya
        local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

        # Ambil ukuran file online
        resp_head = requests.head(url, allow_redirects=True)
        online_size = int(resp_head.headers.get('content-length', 0))
        if online_size == 0:
            resp_head = requests.get(url, stream=True)
            online_size = int(resp_head.headers.get('content-length', 0))
            resp_head.close()

        # Jika file sudah ada dan ukurannya sama, skip
        if local_size > 0 and online_size > 0 and abs(local_size - online_size) < 2:
            print(f"[SKIP] {os.path.basename(local_path)} sudah ada dan ukuran sama, lewati download.")
            return

        # Resume jika file lokal sudah ada dan lebih kecil dari online
        headers = {}
        mode = "wb"
        if local_size > 0 and online_size > 0 and local_size < online_size:
            headers['Range'] = f'bytes={local_size}-'
            mode = "ab"
            print(f"[RESUME] Melanjutkan download {os.path.basename(local_path)} dari {format_size(local_size)}.")

        resp = requests.get(url, stream=True, headers=headers)
        if 'Range' in headers:
            total = online_size
        else:
            total = int(resp.headers.get('content-length', 0))

        downloaded = local_size
        start_time = time.time()
        with open(local_path, mode) as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    elapsed = time.time() - start_time
                    speed = (downloaded - local_size) / elapsed if elapsed > 0 else 0
                    if online_size > 0:
                        percent = int(downloaded * 100 / online_size)
                        sys.stdout.write(
                            f"\r  Progress: {percent}% ({format_size(downloaded)}/{format_size(online_size)}) | {format_size(speed)}/s"
                        )
                        sys.stdout.flush()
        if online_size > 0:
            print()
        print(f"[INFO] Berhasil download {os.path.basename(local_path)} ke {local_path}")
    except Exception as e:
        print(f"[WARNING] Gagal download {os.path.basename(local_path)}: {e}")

def download_hf_dataset_files(repo_id, root_dir):
    """Download file JSON ke folder 'results', file SQL ke root project."""
    base_url = f"https://huggingface.co/datasets/{repo_id}/resolve/main/"
    file_list = get_hf_dataset_file_list(repo_id)
    if not file_list:
        print(f"[WARNING] Repo dataset HuggingFace '{repo_id}' tidak bisa diakses atau kosong. Skip download.")
        return

    results_dir = os.path.join(root_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Filter file JSON dan SQL
    json_files = [f for f in file_list if f.lower().endswith(".json")]
    sql_files = [f for f in file_list if f.lower().endswith(".sql")]

    # Tampilkan daftar file yang akan di-download beserta ukuran
    print("\n[INFO] File JSON yang akan di-download ke folder 'results':")
    show_file_list_with_size(repo_id, json_files, base_url)
    print("\n[INFO] File SQL yang akan di-download ke root project:")
    show_file_list_with_size(repo_id, sql_files, base_url)
    print("\n[INFO] Mulai proses download...\n")

    # Download file JSON ke folder results
    for filename in json_files:
        url = base_url + filename
        local_path = os.path.join(results_dir, os.path.basename(filename))
        print(f"\n[INFO] Downloading {filename} ke {local_path} ...")
        download_file_with_progress(url, local_path)

    # Download file SQL ke root project
    for filename in sql_files:
        url = base_url + filename
        local_path = os.path.join(root_dir, os.path.basename(filename))
        print(f"\n[INFO] Downloading {filename} ke {local_path} ...")
        download_file_with_progress(url, local_path)

# ================================= Bootstrap Icons Functions =================================

def ensure_bootstrap_icons_ready():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ICONS_VERSION = "1.11.3"
    ICONS_FOLDER = os.path.join(BASE_DIR, "static", "css", f"bootstrap-icons-{ICONS_VERSION}")
    ICONS_ZIP_URL = f"https://github.com/twbs/icons/releases/download/v{ICONS_VERSION}/bootstrap-icons-{ICONS_VERSION}.zip"
    ICONS_ZIP_PATH = os.path.join(BASE_DIR, "static", "css", f"bootstrap-icons-{ICONS_VERSION}.zip")

    # Cek apakah folder sudah ada dan berisi file icons.min.css
    if os.path.isdir(ICONS_FOLDER) and os.path.isfile(os.path.join(ICONS_FOLDER, "bootstrap-icons.css")):
        print(f"[INFO] Bootstrap Icons v{ICONS_VERSION} sudah lengkap di {ICONS_FOLDER}")
        return

    os.makedirs(os.path.dirname(ICONS_ZIP_PATH), exist_ok=True)

    # Download ZIP jika belum ada
    if not os.path.isfile(ICONS_ZIP_PATH):
        print(f"[INFO] Downloading Bootstrap Icons v{ICONS_VERSION} ...")
        try:
            resp = requests.get(ICONS_ZIP_URL, stream=True)
            resp.raise_for_status()
            total = int(resp.headers.get('content-length', 0))
            with open(ICONS_ZIP_PATH, "wb") as f:
                downloaded = 0
                start_time = time.time()
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        elapsed = time.time() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        if total > 0:
                            percent = int(downloaded * 100 / total)
                            sys.stdout.write(
                                f"\r  Progress: {percent}% ({format_size(downloaded)}/{format_size(total)}) | {format_size(speed)}/s"
                            )
                            sys.stdout.flush()
                print()
            print(f"[INFO] Berhasil download Bootstrap Icons ZIP ke {ICONS_ZIP_PATH}")
        except Exception as e:
            print(f"[WARNING] Gagal download Bootstrap Icons: {e}")
            return
    else:
        print(f"[INFO] File ZIP Bootstrap Icons sudah ada di {ICONS_ZIP_PATH}")

    # Ekstrak ZIP ke folder sementara, lalu pindahkan isinya ke ICONS_FOLDER
    try:
        temp_extract = os.path.join(os.path.dirname(ICONS_FOLDER), "__temp_icons_extract__")
        if os.path.exists(temp_extract):
            shutil.rmtree(temp_extract)
        with zipfile.ZipFile(ICONS_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(temp_extract)
        # Pindahkan isi temp_extract/bootstrap-icons-1.11.3/* ke ICONS_FOLDER
        inner_folder = os.path.join(temp_extract, f"bootstrap-icons-{ICONS_VERSION}")
        if os.path.isdir(inner_folder):
            if not os.path.exists(ICONS_FOLDER):
                os.makedirs(ICONS_FOLDER)
            for item in os.listdir(inner_folder):
                s = os.path.join(inner_folder, item)
                d = os.path.join(ICONS_FOLDER, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            print(f"[INFO] Berhasil ekstrak Bootstrap Icons ke {ICONS_FOLDER}")
        else:
            print(f"[WARNING] Struktur ZIP tidak sesuai ekspektasi.")
        shutil.rmtree(temp_extract)
    except Exception as e:
        print(f"[WARNING] Gagal ekstrak Bootstrap Icons: {e}")
        return

    # (Opsional) Hapus ZIP setelah ekstrak
    os.remove(ICONS_ZIP_PATH)

# ================================= Indobert Model Functions =================================

def ensure_indobert_ready():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INDOBERT_LOCAL_ROOT = os.path.join(BASE_DIR, "indolem_indobert-base-uncased")
    INDOBERT_ONLINE_REPO = "indolem/indobert-base-uncased"

    if not is_model_complete(INDOBERT_LOCAL_ROOT, INDOBERT_ONLINE_REPO):
        print(f"[INFO] Model indobert belum lengkap di {INDOBERT_LOCAL_ROOT}, download dari HuggingFace...")
        download_bert_model(INDOBERT_LOCAL_ROOT, INDOBERT_ONLINE_REPO)
    else:
        print(f"[INFO] Model indobert sudah lengkap di {INDOBERT_LOCAL_ROOT}")

# ================================= Regional Jawa Model Functions =================================

def ensure_regional_jawa_ready():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    REGIONAL_JAWA_LOCAL_ROOT = os.path.join(BASE_DIR, "model_bert", "Regional_Jawa")
    REGIONAL_JAWA_REPO = "utomomuhammadpriyo/ner-pesan-singkat-laporan-bencana"

    if not is_model_complete(REGIONAL_JAWA_LOCAL_ROOT, REGIONAL_JAWA_REPO):
        print(f"[INFO] Model Regional_Jawa belum lengkap di {REGIONAL_JAWA_LOCAL_ROOT}, download dari HuggingFace...")
        download_bert_model(REGIONAL_JAWA_LOCAL_ROOT, REGIONAL_JAWA_REPO)
    else:
        print(f"[INFO] Model Regional_Jawa sudah lengkap di {REGIONAL_JAWA_LOCAL_ROOT}")

# ================================= Dataset Preparation Functions =================================

def ensure_dataset_and_sql_file_ready():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATASET_REPO = "utomomuhammadpriyo/dataset-ner-pesan-singkat-laporan-bencana"
    download_hf_dataset_files(DATASET_REPO, BASE_DIR)

# ================================= Main Execution =================================

if __name__ == "__main__":
    ensure_indobert_ready()
    ensure_regional_jawa_ready()
    ensure_dataset_and_sql_file_ready()
    ensure_bootstrap_icons_ready()
    print("[INFO] Semua model, dataset, sql, dan Bootstrap Icons sudah siap digunakan.")