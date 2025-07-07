from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from helper.utils import get_navbar_status
from datetime import datetime
import os, time

# Tambahkan cache global di atas
BERT_MODELS = {}

def get_bert_pipeline(model_path, aggregation_strategy="simple", device=-1):
    key = (model_path, aggregation_strategy, device)
    if key not in BERT_MODELS:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForTokenClassification.from_pretrained(model_path)
        BERT_MODELS[key] = pipeline(
            "ner",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy=aggregation_strategy,
            device=device
        )
    return BERT_MODELS[key]

def ensure_log_folder_exists(LOG_FOLDER_PATH):
    if not os.path.exists(LOG_FOLDER_PATH):
        os.makedirs(LOG_FOLDER_PATH)

def log_bert_per_input(data_index, model_path, aggregation_strategy, original_text, extracted_entities, timestamp, execution_time=0.0, threshold=0.9):
    """
    Menyimpan log pencocokan untuk data input ke-{data_index} ke file log.
    """
    BASE_DIR = os.getcwd()
    LOG_BERT_PATH = "LogDetect/Bert"
    LOG_FOLDER_PATH = os.path.join(BASE_DIR, LOG_BERT_PATH)
    ensure_log_folder_exists(LOG_FOLDER_PATH)
    log_file = os.path.join(LOG_FOLDER_PATH, f"log_Bert_{data_index}.txt")

    with open(log_file, "w", encoding="utf-8") as file:
        file.write(f"Timestamp: {timestamp}\n\n")
        file.write(f"Model Path: {model_path}\n")
        file.write(f"Aggregation Strategy: {aggregation_strategy}\n")
        file.write(f"Threshold: {threshold}\n\n")
        file.write(f"Log Ekstraksi untuk Data Input ke-{data_index}:\n")
        file.write(f"Waktu eksekusi: {execution_time:.2f} detik\n")
        
        # 1. Teks Asli
        file.write("\nTeks Asli:\n")
        file.write(f"{original_text}\n")
        
        # 2. Hasil Terbaik (per kategori)
        file.write("\nHasil Terbaik:\n")
        if extracted_entities:
            # Kelompokkan entitas berdasarkan label
            disaster_entities = [e for e in extracted_entities if e['label'] == 'DISASTER']
            location_entities = [e for e in extracted_entities if e['label'] == 'LOCATION']
            
            # Tampilkan entitas terbaik untuk DISASTER jika ada
            if disaster_entities:
                best_disaster = max(disaster_entities, key=lambda x: x['score'])
                file.write(f"DISASTER: \"{best_disaster['text']}\", Score: {best_disaster['score']:.4f}\n")
            else:
                file.write("DISASTER: Tidak ditemukan\n")
                
            # Tampilkan entitas terbaik untuk LOCATION jika ada
            if location_entities:
                best_location = max(location_entities, key=lambda x: x['score'])
                file.write(f"LOCATION: \"{best_location['text']}\", Score: {best_location['score']:.4f}\n")
            else:
                file.write("LOCATION: Tidak ditemukan\n")
        else:
            file.write("Tidak ditemukan entitas yang cocok.\n")
        
        # 3. Hasil dengan skor >= threshold
        high_score_entities = [e for e in extracted_entities if e['score'] >= threshold]
        file.write(f"\nHasil dengan skor >={threshold}:\n")
        if high_score_entities:
            for i, entity in enumerate(high_score_entities, start=1):
                file.write(f"{i}. Text: \"{entity['text']}\"\n")
                file.write(f"   Label: {entity['label']}, Score: {entity['score']:.4f}\n")
        else:
            file.write(f"Tidak ada entitas dengan skor >={threshold}.\n")
            
        # 4. Semua hasil ekstraksi entitas
        file.write("\nHasil Ekstraksi Entitas:\n")
        if extracted_entities:
            for i, entity in enumerate(extracted_entities, start=1):
                file.write(f"{i}. Text: \"{entity['text']}\"\n")
                file.write(f"   Label: {entity['label']}, Score: {entity['score']:.4f}\n")
        else:
            file.write("Tidak ditemukan entitas yang cocok.\n")

def process_text_with_bert(model_path, text, data_index=1, threshold=0.9, pipeline=None,
    aggregation_strategy="simple", device=-1):
    """
    Memuat model BERT dari path yang diberikan dan memproses teks untuk ekstraksi entitas.
    Menerapkan threshold untuk memfilter hasil dengan skor rendah.
    """

    start_time = time.time()

    aggregation_strategy = "simple"
    nlp_ner = pipeline if pipeline is not None else get_bert_pipeline(model_path, aggregation_strategy, device)
    
    # Memproses teks
    results = nlp_ner(text)
    entities = []
    for entity in results:
        entities.append({
            "text": entity['word'],
            "label": entity['entity_group'],
            "score": entity['score']
        })
    
    # Filter entitas dengan skor >= threshold    
    filtered_entities = [entity for entity in entities if entity['score'] >= threshold]
        
    execution_time = time.time() - start_time
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    navbar_status = get_navbar_status()
    result_mode = navbar_status.get('result_mode')

    # jangan logging jika mode adalah 'auto'
    if result_mode == 'manual':
        # Log hasil ekstraksi entitas
        log_bert_per_input(
            data_index=data_index,
            model_path=model_path,
            aggregation_strategy=aggregation_strategy,
            original_text=text,
            extracted_entities=entities,  # Kirim semua entitas ke log
            timestamp=timestamp,
            execution_time=execution_time,
            threshold=threshold
        )

    # Kembalikan hanya entitas dengan skor di atas threshold
    return filtered_entities