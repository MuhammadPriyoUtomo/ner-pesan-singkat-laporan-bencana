import os, re, requests, zipfile, shutil, subprocess

CHROMEDRIVER_DIR = os.path.join(os.path.dirname(__file__), '..', 'chromedriver')
CHROMEDRIVER_EXE = os.path.join(CHROMEDRIVER_DIR, 'chromedriver.exe')

def get_chrome_version():
    # Cek versi Chrome di Windows
    import winreg
    reg_path = r"SOFTWARE\Google\Chrome\BLBeacon"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        version, _ = winreg.QueryValueEx(key, "version")
        return version
    except Exception:
        # Coba di HKEY_LOCAL_MACHINE
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            version, _ = winreg.QueryValueEx(key, "version")
            return version
        except Exception:
            pass
    # Fallback: coba via command line
    try:
        output = subprocess.check_output(
            r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --version',
            shell=True
        )
        version = re.search(r'(\d+\.\d+\.\d+\.\d+)', output.decode())
        if version:
            return version.group(1)
    except Exception:
        pass
    return None

def get_chromedriver_version():
    if not os.path.exists(CHROMEDRIVER_EXE):
        return None
    try:
        output = subprocess.check_output([CHROMEDRIVER_EXE, '--version'])
        version = re.search(r'(\d+\.\d+\.\d+\.\d+)', output.decode())
        if version:
            return version.group(1)
    except Exception:
        pass
    return None

def get_latest_chromedriver_url(chrome_version):
    major = chrome_version.split('.')[0]
    url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Tidak bisa mengakses API chromedriver: {e}")
        return None, None
    # Cari versi yang cocok di semua versi
    for v in data['versions']:
        if v['version'].split('.')[0] == major and v.get('channel', '').lower() == 'stable':
            for d in v['downloads']['chromedriver']:
                if d['platform'] == 'win64':
                    return d['url'], v['version']
    for v in data['versions']:
        if v['version'].split('.')[0] == major:
            for d in v['downloads']['chromedriver']:
                if d['platform'] == 'win64':
                    return d['url'], v['version']
    return None, None

def download_and_extract(url, extract_to):
    zip_path = os.path.join(extract_to, 'chromedriver.zip')
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('chromedriver.exe'):
                    zip_ref.extract(member, extract_to)
                    src = os.path.join(extract_to, member)
                    dst = os.path.join(extract_to, 'chromedriver.exe')
                    shutil.move(src, dst)
        os.remove(zip_path)
        folder = os.path.join(extract_to, 'chromedriver-win64')
        if os.path.isdir(folder):
            shutil.rmtree(folder)
    except Exception as e:
        print(f"[WARNING] Gagal download atau extract chromedriver: {e}")

def chromedriver_update():
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("[WARNING] Google Chrome tidak ditemukan.")
        return
    chromedriver_version = get_chromedriver_version()
    print(f"Chrome version: {chrome_version}")
    print(f"Chromedriver version: {chromedriver_version}")
    if chromedriver_version and chromedriver_version.split('.')[0] == chrome_version.split('.')[0]:
        print("Chromedriver sudah sesuai dengan versi Chrome.")
        return
    print("Mencari chromedriver terbaru...")
    url, latest_version = get_latest_chromedriver_url(chrome_version)
    if not url:
        print("[WARNING] Tidak menemukan chromedriver yang cocok atau gagal akses API.")
        return
    print(f"Mendownload chromedriver versi {latest_version} ...")
    if not os.path.exists(CHROMEDRIVER_DIR):
        os.makedirs(CHROMEDRIVER_DIR)
    download_and_extract(url, CHROMEDRIVER_DIR)
    print("Chromedriver berhasil diupdate.")