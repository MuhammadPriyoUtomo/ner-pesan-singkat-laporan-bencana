from helper.utils import get_navbar_status
from datetime import datetime
import spacy, os, time

NLP_MODELS = {}

def get_nlp(model_dir):
    if model_dir not in NLP_MODELS:
        NLP_MODELS[model_dir] = spacy.load(model_dir, disable=["parser", "lemmatizer", "tagger"]) #Tambahkan disable=["parser", "lemmatizer", "tagger"] jika hanya butuh NER.
    return NLP_MODELS[model_dir]

def ensure_log_folder_exists(LOG_FOLDER_PATH):
    """Pastikan folder log ada."""
    if not os.path.exists(LOG_FOLDER_PATH):
        os.makedirs(LOG_FOLDER_PATH)

def log_spacy_per_input(data_index, model_path, original_text, extracted_entities, timestamp, execution_time=0.0):
    """
    Menyimpan log ekstraksi entitas untuk data input ke-{data_index} ke file log.
    """
    BASE_DIR = os.getcwd()
    LOG_SPACY_PATH = "LogDetect/Spacy"
    LOG_FOLDER_PATH = os.path.join(BASE_DIR, LOG_SPACY_PATH)
    ensure_log_folder_exists(LOG_FOLDER_PATH)
    log_file = os.path.join(LOG_FOLDER_PATH, f"log_Spacy_{data_index}.txt")

    with open(log_file, "w", encoding="utf-8") as file:
        file.write(f"Timestamp: {timestamp}\n\n")
        file.write(f"Model Path: {model_path}\n\n")
        file.write(f"Log Ekstraksi untuk Data Input ke-{data_index}:\n")
        file.write(f"Waktu eksekusi: {execution_time:.2f} detik\n")
        file.write("\nTeks Asli:\n")
        file.write(f"{original_text}\n")

        file.write("\nHasil Ekstraksi Entitas:\n")
        if extracted_entities:
            for i, entity in enumerate(extracted_entities, start=1):
                file.write(f"{i}. Text: \"{entity['text']}\"\n")
                file.write(f"   Label: {entity['label']}\n")
        else:
            file.write("Tidak ditemukan entitas yang cocok.\n")

def load_and_test_model(model_dir, text, data_index=1, nlp=None):
    """
    Memuat model spaCy dari path yang diberikan dan memproses teks untuk ekstraksi entitas.
    """

    start_time = time.time()

    nlp_model = nlp if nlp is not None else get_nlp(model_dir)
    doc = nlp_model(text)
    entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    
    # Hasil ekstraksi
    hasil_ekstraksi = {
        "entities": entities
    }
  
    execution_time = time.time() - start_time
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # jangan logging jika mode adalah 'auto'
    if result_mode == 'manual':
        # Log hasil ekstraksi entitas
        log_spacy_per_input(
            data_index=data_index,  # Ganti dengan index yang sesuai
            model_path=model_dir,
            original_text=text,
            extracted_entities=entities,
            timestamp=timestamp,
            execution_time=execution_time
        )

    return hasil_ekstraksi