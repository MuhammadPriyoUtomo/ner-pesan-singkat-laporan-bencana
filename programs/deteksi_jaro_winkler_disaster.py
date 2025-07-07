from rapidfuzz.distance import JaroWinkler
from helper.utils import get_navbar_status
from datetime import datetime
import re, os, time

# =========================
# Fungsi Utilitas dan Logging
# =========================

def ensure_log_folder_exists(LOG_FOLDER_PATH):
    """Pastikan folder log ada."""
    if not os.path.exists(LOG_FOLDER_PATH):
        os.makedirs(LOG_FOLDER_PATH)

def log_jaro_winkler_disaster_per_input(data_index, original_text, detected_disasters, best_disaster, timestamp,min_similarity=0.9, execution_time=0.0):
    """
    Menyimpan log pencocokan untuk data input ke-{data_index} ke file log.
    """
    BASE_DIR = os.getcwd()
    LOG_JARO_WINKLER_DISASTER_PATH = "LogDetect/Jaro_Winkler/Disaster"
    LOG_FOLDER_PATH = os.path.join(BASE_DIR, LOG_JARO_WINKLER_DISASTER_PATH)    
    ensure_log_folder_exists(LOG_FOLDER_PATH)
    log_file = os.path.join(LOG_FOLDER_PATH, f"log_Jaro_Disaster_{data_index}.txt")
    
    with open(log_file, "w", encoding="utf-8") as file:
        file.write(f"Timestamp: {timestamp}\n\n")
        file.write(f"Log Pencocokan Bencana untuk Data Input ke-{data_index}:\n")
        file.write(f"Jumlah hasil ditemukan: {len(detected_disasters)}\n")
        file.write(f"Jumlah hasil relevan (>= {min_similarity}): {len([d for d in detected_disasters if d['similarity'] >= min_similarity])}\n")
        file.write(f"Waktu eksekusi: {execution_time:.2f} detik\n")
        
        file.write("\nTeks Asli:\n")
        file.write(f"{original_text}\n")
        
        file.write("\nHasil Pencocokan Terbaik:\n")
        if best_disaster:
            file.write(f"Disaster: {best_disaster['disaster']}, Window: {best_disaster['window_phrase']}, Similarity: {best_disaster['similarity']:.4f}\n")
        else:
            file.write("Tidak ditemukan bencana yang cocok untuk hasil terbaik.\n")
        
        # Log semua kandidat dengan skor >= min_similarity
        file.write("\nKandidat dengan skor >=" + str(min_similarity) + ":\n")
        for disaster in detected_disasters:
            if disaster['similarity'] >= min_similarity:
                file.write(f"- Disaster: {disaster['disaster']}, Window: {disaster['window_phrase']}, Similarity: {disaster['similarity']:.4f}\n")

# =========================
# Fungsi Pencocokan Bencana dengan Jaro-Winkler
# =========================

def clean_text(text):
    """
    Membersihkan teks:
      - Mengubah semua ke lowercase
      - Menghapus karakter non-alfanumerik kecuali koma, titik, dan tanda hubung
    """
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s,.-]', '', text)
    return text

def match_with_jaro_winkler_disaster(text, disaster_database, threshold=0.9):
    """
    Mencocokkan teks input dengan daftar bencana menggunakan Jaro-Winkler.
    """
    cleaned_text = clean_text(text)
    words = cleaned_text.split()
    detected_disasters = []

    for disaster in disaster_database:
        disaster_words = disaster.split()
        disaster_len = len(disaster_words)

        for i in range(len(words) - disaster_len + 1):
            window = words[i:i + disaster_len]
            window_phrase = re.sub(r'[^\w\s]+$', '', " ".join(window))
            similarity = JaroWinkler.similarity(disaster, window_phrase)
            if similarity >= threshold:
                detected_disasters.append({
                    "disaster": disaster,
                    "window_phrase": window_phrase,
                    "similarity": similarity
                })

    detected_disasters = sorted(detected_disasters, key=lambda x: x['similarity'], reverse=True)
    return detected_disasters

def find_best_disaster_match(detected_disasters, text):
    """
    Mengembalikan hasil pencocokan terbaik berdasarkan similarity tertinggi,
    panjang frasa, dan posisi dalam teks asli.
    """
    if not detected_disasters:
        return None

    # Filter kandidat dengan minimal 2 kata
    filtered = [disaster for disaster in detected_disasters if len(disaster['disaster'].split()) >= 2]
    if not filtered:
        filtered = detected_disasters

    # Pilih hasil terbaik berdasarkan similarity, panjang frasa, dan posisi dalam teks
    best_match = max(
        filtered,
        key=lambda x: (x['similarity'], len(x['disaster'].split()), -text.find(x['window_phrase']))
    )
    # return best_match
    return {
        "disaster": best_match['disaster'],
        "window_phrase": best_match['window_phrase'],
        "similarity": best_match['similarity']
    }

# =========================
# Fungsi Utama Proses Pencocokan Bencana
# =========================

def process_with_jaro_winkler_disaster(text, disaster_database, threshold=0.9, data_index=1):
    """
    Memproses satu data input:
      - Melakukan pencocokan bencana menggunakan Jaro-Winkler.
      - Mengambil hasil terbaik dan kemudian hasil paling lengkap.
      - Menyimpan log ke file dengan nama berdasarkan data_index.
      - Mengembalikan hasil ekstraksi bencana.
    """
    start_time = time.time()  # Mulai hitung waktu eksekusi
    detected_disasters = match_with_jaro_winkler_disaster(text, disaster_database, threshold)
    best_disaster = find_best_disaster_match(detected_disasters, text)  # Tambahkan argumen `text`
    # most_complete_disaster = find_most_complete_disaster(best_disaster, disaster_database, text)
    execution_time = time.time() - start_time  # Akhir hitung waktu eksekusi

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # jangan logging jika mode adalah 'auto'
    if result_mode == 'manual':
        # Log hasil pencocokan beserta teks asli
        log_jaro_winkler_disaster_per_input(
            data_index=data_index, 
            original_text=text, 
            detected_disasters=detected_disasters, 
            best_disaster=best_disaster, 
            timestamp=timestamp,
            min_similarity=threshold, 
            execution_time=execution_time
        )
    
    if best_disaster:
        return {
            "disaster": best_disaster['disaster'],
            "source": "jaro_winkler",
            "similarity": best_disaster['similarity'],
            "execution_time": execution_time
        }
    else:
        return {
            "disaster": None,
            "source": None,
            "similarity": None,
            "execution_time": execution_time
        }