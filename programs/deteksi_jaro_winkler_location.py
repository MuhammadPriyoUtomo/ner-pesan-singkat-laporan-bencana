from rapidfuzz.distance import JaroWinkler
from helper.utils import get_navbar_status
from datetime import datetime
import re, os, time

# =========================
# Fungsi Utilitas dan Logging
# =========================

def ensure_log_folder_exists(LOG_FOLDER_PATH):
    if not os.path.exists(LOG_FOLDER_PATH):
        os.makedirs(LOG_FOLDER_PATH)

def log_jaro_winkler_location_per_input(data_index, original_text, detected_locations, most_complete_location, timestamp, min_similarity=0.9, execution_time=0.0):
    """
    Menyimpan log pencocokan untuk data input ke-{data_index} ke file log.
    """
    BASE_DIR = os.getcwd()
    LOG_JARO_WINKLER_LOCATION_PATH = "LogDetect/Jaro_Winkler/Location"
    LOG_FOLDER_PATH = os.path.join(BASE_DIR, LOG_JARO_WINKLER_LOCATION_PATH)
    ensure_log_folder_exists(LOG_FOLDER_PATH)
    log_file = os.path.join(LOG_FOLDER_PATH, f"log_Jaro_Location_{data_index}.txt")
    
    # Deduplicate kandidat berdasarkan kombinasi
    dedup_candidates = deduplicate_candidates([loc['combination'] for loc in detected_locations if loc['similarity'] >= min_similarity])
    
    with open(log_file, "w", encoding="utf-8") as file:
        file.write(f"Timestamp: {timestamp}\n\n")
        file.write(f"Log Pencocokan untuk Data Input ke-{data_index}:\n")
        file.write(f"Jumlah hasil ditemukan: {len(detected_locations)}\n")
        file.write(f"Jumlah hasil relevan (>= {min_similarity}): {len([loc for loc in detected_locations if loc['similarity'] >= min_similarity])}\n")
        file.write(f"Waktu eksekusi: {execution_time:.2f} detik\n")
        file.write("\nTeks Asli:\n")
        file.write(f"{original_text}\n")
        
        file.write("\nHasil Pencocokan Terbaik:\n")
        if most_complete_location:
            file.write(f"Combination: {most_complete_location['combination']}, ")
            file.write(f"Window: {most_complete_location['window_phrase']}, ")
            file.write(f"Similarity: {most_complete_location['similarity']:.4f}\n")
        else:
            file.write("Tidak ditemukan lokasi yang cocok untuk hasil terbaik.\n")
        
        file.write("\nDeduplicated Kandidat:\n")
        if dedup_candidates:
            for cand, count in dedup_candidates.items():
                file.write(f"- {cand} (x{count})\n")
        else:
            file.write("Tidak ditemukan lokasi yang cocok.\n")

        # Log semua kandidat dengan skor >= min_similarity
        file.write("\nKandidat dengan skor >=" + str(min_similarity) + ":\n")
        for loc in detected_locations:
            if loc['similarity'] >= min_similarity:
                file.write(f"- Combination: {loc['combination']}, Window: {loc['window_phrase']}, Similarity: {loc['similarity']:.4f}\n")

# =========================
# Fungsi Deduplication Kandidat
# =========================

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s,.\-']", '', text)
    return text.strip()

def read_location_groups(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
        groups = [group.strip().split("\n") for group in content.strip().split("\n\n") if group.strip()]
        return [[clean_text(line) for line in group] for group in groups]
    except Exception as e:
        print(f"Error saat membaca file {filename}: {e}")
        return []

def deduplicate_candidates(candidates):
    dedup = {}
    for cand in candidates:
        cand_clean = cand.strip()
        if cand_clean in dedup:
            dedup[cand_clean] += 1
        else:
            dedup[cand_clean] = 1
    return dedup

def clean_window_phrase(window_phrase):
    """
    Membersihkan karakter tidak diinginkan di awal dan akhir window_phrase.
    """
    # Hilangkan karakter non-alphanumeric di awal dan akhir
    return re.sub(r'^[^\w]+|[^\w]+$', '', window_phrase)

# =========================
# Fungsi Pencocokan Lokasi dengan Jaro-Winkler (Revisi)
# =========================

def match_with_jaro_winkler(text, groups, threshold=0.9, max_window_size=10):
    cleaned_text = clean_text(text)
    words = cleaned_text.split()
    detected_locations = []
    
    for group in groups:
        seen_combinations = set()
        for combination in group:
            # Skip kombinasi yang kurang dari 2 kata
            # if len(combination.split()) < 2:
            #     continue
            if combination in seen_combinations:
                continue
            seen_combinations.add(combination)
            
            combination_words = combination.split()
            combination_len = len(combination_words)
            if combination_len > max_window_size:
                continue
            
            for i in range(len(words) - combination_len + 1):
                window = words[i:i + combination_len]
                window_phrase = " ".join(window)
                # Bersihkan window_phrase
                cleaned_window_phrase = clean_window_phrase(window_phrase)
                
                similarity = JaroWinkler.similarity(combination, cleaned_window_phrase)
                if similarity >= threshold:
                    detected_locations.append({
                        "combination": combination,
                        "window_phrase": cleaned_window_phrase,  # Gunakan window_phrase yang sudah dibersihkan
                        "similarity": similarity,
                        "group": group
                    })
    detected_locations = sorted(detected_locations, key=lambda x: x['similarity'], reverse=True)
    return detected_locations

def find_best_match(detected_locations, original_text):
    if not detected_locations:
        return None
    # Filter kandidat dengan minimal 2 kata
    # filtered = [loc for loc in detected_locations if len(loc['combination'].split()) >= 2]

    # Filter kandidat dengan minimal 1 kata
    filtered = [loc for loc in detected_locations if len(loc['combination'].split()) >= 1]
    if not filtered:
        filtered = detected_locations
    best_match = max(
        filtered,
        key=lambda x: (x['similarity'], len(x['combination'].split()), -original_text.find(x['window_phrase']))
    )
    return best_match

# =========================
# Fungsi Utama untuk Proses Pencocokan Lokasi
# =========================

def process_with_jaro_winkler_location(text, location_groups, threshold=0.9, data_index=1):
    start_time = time.time()
    detected_locations = match_with_jaro_winkler(text, location_groups, threshold)
    best_match = find_best_match(detected_locations, text)
    # most_complete_location = find_most_complete_location(best_match, text)
    execution_time = time.time() - start_time

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # jangan logging jika mode adalah 'auto'
    if result_mode == 'manual':
        log_jaro_winkler_location_per_input(
            data_index=data_index,
            original_text=text,
            detected_locations=detected_locations,
            most_complete_location=best_match,  # Pastikan ini sesuai dengan yang diharapkan
            timestamp=timestamp,
            min_similarity=threshold,
            execution_time=execution_time
        )
    
    if best_match:
        return {
            "location": best_match['combination'],
            "source": "jaro_winkler",
            "similarity": best_match['similarity'],
            "execution_time": execution_time
        }
    else:
        return {
            "location": None,
            "source": None,
            "similarity": None,
            "execution_time": execution_time
        }
