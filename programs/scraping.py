# Tambahkan di awal file sebelum import lainnya
import logging
# Konfigurasi logging - matikan log debug dari selenium dan urllib3
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from helper.db_utils import get_db_dict_connection, get_db_connection
from datetime import datetime
import time, pickle, mysql.connector, re, os, helper.App_config as App_config

# Path constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Folder root proyek
cookies_path = os.path.join(BASE_DIR, 'cookies.pkl')  # Path ke file cookies.pkl
driver_path = os.path.join(BASE_DIR, 'chromedriver', 'chromedriver.exe')  # Path ke chromedriver.exe
profile_path = os.path.join(App_config.PROFILE_PATH)  # Path ke folder profil Chrome

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={profile_path}")
    
    # Mematikan debug logs - tambahan baru
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")  # Hanya tampilkan error fatal
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Tambahkan ini untuk mematikan logging konsol browser
    prefs = {
        'devtools.silent': True,
        'logging.browser.level': 'OFF',
        'logging.profiler.enabled': False
    }
    options.add_experimental_option('prefs', prefs)
    
    # Konfigurasi service
    service = Service(
        executable_path=driver_path,
        log_path="NUL" if os.name == "nt" else "/dev/null"  # Gunakan NUL di Windows
    )
    
    # Inisialisasi driver
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def load_cookies(driver):
    try:
        print(f"Loading cookies from: {cookies_path}")
        if os.path.getsize(cookies_path) == 0:
            print("Cookies file kosong, abaikan loading.")
            return

        with open(cookies_path, "rb") as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
    except (FileNotFoundError, EOFError) as e:
        print(f"Tidak bisa memuat cookies: {e}. Silakan login manual.")

def save_cookies(driver):
    print(f"Saving cookies to: {cookies_path}")
    with open(cookies_path, "wb") as cookiesfile:
        pickle.dump(driver.get_cookies(), cookiesfile)
    print(f"Cookies saved to {cookies_path}.")

def update_chat_status(sender_number, has_unread_messages):
    try:
        default_number = App_config.DEFAULT_NUMBER
        if sender_number == default_number:
            has_unread_messages = False

        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM chat_status WHERE sender_number = %s"
        cursor.execute(query, (sender_number,))
        result = cursor.fetchone()
        
        if result:
            if result[1] != has_unread_messages:
                query = "UPDATE chat_status SET has_unread_messages = %s WHERE sender_number = %s"
                cursor.execute(query, (has_unread_messages, sender_number))
        else:
            query = "INSERT INTO chat_status (sender_number, has_unread_messages) VALUES (%s, %s)"
            cursor.execute(query, (sender_number, has_unread_messages))
        
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def get_unread_chats():
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()
        
        query = "SELECT sender_number FROM chat_status WHERE has_unread_messages = TRUE"
        cursor.execute(query)
        unread_chats = cursor.fetchall()
        print(f"Unread chats dari database: {unread_chats}")
        
        cursor.close()
        conn.close()
        return unread_chats
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    
def scrape_messages(driver, stop_flag, scan_count):
    
    hasil_scraping = {}
    
    default_number = App_config.DEFAULT_NUMBER

    try:
        print(f"\nScanning iteration {scan_count}")
        print("\nStarting scraping process...")

        # Tahap ke-1: Mencari chat dengan nomor default
        try:
            print("\nTahap ke-1: Mencari chat dengan nomor default")
            default_chat = driver.find_element(By.XPATH, f'//span[@title="{App_config.DEFAULT_NUMBER}"]')
            default_chat.click()
            print("Default chat ditemukan dan diklik.")
        except NoSuchElementException:
            print("Default chat tidak ditemukan.")

        # Tahap ke-2: Menlist nomor di sidebar dan update database
        try:
            print("\nTahap ke-2: Menlist nomor di sidebar dan update database")
            chat_list = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]//div[@role="grid"]'))
            )
            chats = chat_list.find_elements(By.XPATH, './/div[@role="listitem"]')
            print(f"\nJumlah chat yang ditemukan di sidebar: {len(chats)}")

            if chats:
                for chat in chats:
                    try:
                        sender_number = chat.find_element(By.XPATH, './/span[@dir="auto"]').get_attribute("title")

                        # ✅ Lewati nomor default
                        if sender_number == App_config.DEFAULT_NUMBER:
                            print(f"\nMelewati nomor default: {sender_number}")
                            continue

                        print(f"\nProcessing chat with sender number: {sender_number}")

                        try:
                            chat.find_element(By.XPATH, './/div[contains(@class, "_ahlk")]')
                            has_unread_messages = True
                            print("\nMenemukan chat belum dibaca.")
                        except NoSuchElementException:
                            has_unread_messages = False
                            print("\nTidak ada chat belum dibaca.")

                        update_chat_status(sender_number, has_unread_messages)
                    except Exception as e:
                        print(f"Error processing chat: {e}")

        except TimeoutException:
            print("Gagal menemukan daftar chat. Memuat ulang halaman...")
            driver.refresh()
            return scan_count  # Tetap kembalikan scan_count agar tidak menyebabkan None di caller

        # Tahap ke-3: Memanggil nomor dengan pesan belum dibaca
        print("\nTahap ke-3: Memanggil nomor dengan pesan belum dibaca")
        unread_chats = get_unread_chats()
        print(f"\nJumlah chat dengan pesan belum dibaca: {len(unread_chats)}")

        # Tahap ke-4: Looping untuk memproses chat
        if unread_chats:

            print("\nTahap ke-4: Looping untuk memproses chat")

            for unread_chat in unread_chats:

                sender_number = unread_chat['sender_number']
                if sender_number == default_number:
                    print(f"\nNomor default {default_number} dilewati.")
                    continue

                try:
                    print(f"\nMembuka chat dengan nomor: {sender_number}")
                    chat = driver.find_element(By.XPATH, f'//span[@title="{sender_number}"]')
                    chat.click()
                    # Tunggu chat benar-benar terbuka (tunggu pesan muncul)
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "copyable-text") and @data-pre-plain-text]'))
                    )

                    # Cari elemen penanda "pesan belum dibaca"
                    unread_divs = driver.find_elements(By.XPATH, '//span[contains(text(), "pesan belum dibaca")]')
                    messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text") and @data-pre-plain-text]')
                    print(f"\nJumlah pesan yang ditemukan: {len(messages)}\n")

                    if unread_divs:
                        print("Menemukan chat belum dibaca.")
                        last_unread = unread_divs[-1]
                        driver.execute_script("arguments[0].scrollIntoView();", last_unread)
                        # Tunggu pesan baru muncul setelah scroll
                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "copyable-text") and @data-pre-plain-text]'))
                        )
                        messages = driver.find_elements(By.XPATH, '//div[contains(@class, "copyable-text") and @data-pre-plain-text]')
                        unread_index = None
                        for idx, msg in enumerate(messages):
                            if last_unread.location['y'] < msg.location['y']:
                                unread_index = idx
                                break
                        if unread_index is not None:
                            messages = messages[unread_index:]
                            print(f"\nMemproses mulai dari pesan ke-{unread_index}")
                        else:
                            print("\nTidak bisa menentukan pesan setelah 'pesan belum dibaca', lewati chat ini.")
                            continue
                    else:
                        print("\nTidak ada indikator pesan belum dibaca, lewati.")
                        continue

                    for message in messages:
                        print(f"\nHTML elemen pesan: {message.get_attribute('outerHTML')}\n")
                        sender_info = message.get_attribute("data-pre-plain-text")
                        print(f"\nData pre-plain-text: {sender_info}\n")
                        message_text_element = message.find_element(By.XPATH, './/span[@dir="ltr"]//span')
                        message_text = message_text_element.text if message_text_element else ""
                        print(f"\nTeks pesan: {message_text}\n")
                        message_text = message_text.lower()
                        print(f"\nTeks pesan setelah diubah menjadi huruf kecil: {message_text}\n")

                        match = re.match(r'\[(.*?)\] (.*?):', sender_info.strip())
                        date = match.group(1)
                        sender = match.group(2)
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

                        print(f"Match: {match}\n")
                        print(f"\nSender: {sender}\n")
                        print(f"\nTanggal: {date}\n")
                        print(f"\nPesan dari {sender}: {message_text}\n")
                        print(f"\nTimestamp: {timestamp}\n")
                        
                        if match:
                            if sender not in hasil_scraping:
                                hasil_scraping[sender] = []
                            hasil_scraping[sender].append({
                                "date": date,
                                "text": message_text,
                                "timestamp": timestamp
                            })
                            print(f"\nPesan ditambahkan ke hasil_scraping: {hasil_scraping[sender][-1]}")

                    # === OPTIMASI: Setelah semua pesan diambil, langsung kembali ke chat default ===
                    try:
                        print(f"\nKembali ke chat default: {default_number}")
                        default_chat = driver.find_element(By.XPATH, f'//span[@title="{default_number}"]')
                        default_chat.click()
                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "copyable-text") and @data-pre-plain-text]'))
                        )
                    except Exception as e:
                        print(f"Error kembali ke chat default: {e}")

                except Exception as e:
                    print(f"Error membuka chat dengan nomor {sender_number}: {e}")
        else:
            print("\nMelewati tahap 4.")

        # Tahap ke-5: Deteksi pesan + simpan ke database
        if hasil_scraping:
            conn = get_db_connection()
            cursor = conn.cursor()
            for sender, messages in hasil_scraping.items():
                for message in messages:
                    try:
                        query = """
                            INSERT INTO pending_detection (
                                nomor_pengirim, tanggal, chat, timestamp
                            ) VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(query, (
                            sender,
                            message['date'],
                            message['text'],
                            message['timestamp']
                        ))
                        conn.commit()
                    except Exception as e:
                        print(f"Gagal menyimpan ke pending_detection: {e}")
            cursor.close()
            conn.close()
        else:
            print("\nMelewati tahap 5.")

        # Bersihkan hasil setelah diproses
        hasil_scraping.clear()

        print("\nTahap ke-6: Cooldown sebelum mengulang")

        cooldown_time = 1
        for remaining in range(cooldown_time, 0, -1):
            if stop_flag.is_set():
                print("\nStop flag terdeteksi saat cooldown. Keluar dari loop.")
                break
            print(f"\nMenunggu sebelum memindai ulang: {remaining} detik")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Program dihentikan oleh pengguna.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        print("Scraping selesai.")
        return scan_count  # ✅ WAJIB: Kembalikan scan_count agar tidak menjadi None

def wait_until_logged_in(driver, stop_flag, timeout=20, check_interval=5):
    """
    Tunggu hingga user login (element #pane-side muncul),
    atau keluar jika stop_flag diaktifkan.
    """
    print("Menunggu login... Silakan scan QR code jika belum.")

    while not stop_flag.is_set():
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "pane-side"))
            )
            print("Login berhasil!")
            return True
        except TimeoutException:
            print(f"Belum login. Akan dicek lagi dalam {check_interval} detik...")
            time.sleep(check_interval)

    print("Stop flag terdeteksi saat menunggu login. Proses dibatalkan.")
    return False  # login belum terjadi dan diminta berhenti

def scraping_main(stop_flag):
    print("Log Start\nInitializing driver and loading cookies...\n")

    driver = initialize_driver()
    driver.get('https://web.whatsapp.com')

    load_cookies(driver)
    driver.refresh()

    print("Please scan the QR code to log in if not already logged in.")

    # ✅ Tunggu login, tapi bisa dibatalkan oleh stop_flag
    if not wait_until_logged_in(driver, stop_flag):
        driver.quit()
        return  # keluar sebelum masuk scraping loop

    save_cookies(driver)
    print("Cookies saved, starting to check for unread messages.")

    scan_count = 1  # Inisialisasi scan_count di luar loop

    try:
        while not stop_flag.is_set():
            print("Scraping in progress...")
            scan_count = scrape_messages(driver, stop_flag, scan_count)  # Perbarui scan_count
            if stop_flag.is_set():
                print("Scraping stopped by flag.")
                break
        print("Exiting scraping_main.")
    finally:
        print("Scraping stopped by user.")
        driver.quit()