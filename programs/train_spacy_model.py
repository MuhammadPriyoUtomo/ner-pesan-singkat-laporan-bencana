from spacy.training import Example
from spacy.util import minibatch, compounding
from spacy.scorer import Scorer  # Tambahkan import Scorer
from helper.db_utils import get_db_connection
from tabulate import tabulate  # Tambahkan import tabulate untuk menampilkan hasil
import os, spacy, random, numpy as np

# Path constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_DIR = os.path.join(BASE_DIR, "model_spacy")

def update_database_with_used_ids(used_data_ids):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE data_create_model SET spacy_train_used = 1 WHERE id = %s"
        cursor.executemany(query, [(data_id,) for data_id in used_data_ids])
        conn.commit()
        print(f"\n[SUCCESS] Kolom spacy_train_used berhasil diperbarui untuk ID: {used_data_ids}")
    except Exception as e:
        print(f"\n[ERROR] Gagal memperbarui database: {e}")
    finally:
        cursor.close()
        conn.close()

def convert_np_types(obj):
    """Rekursif ubah np.float32 dan np.int32 ke float dan int Python native"""
    if isinstance(obj, dict):
        return {k: convert_np_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np_types(i) for i in obj]
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    else:
        return obj

def save_spacy_training_results_to_db(model_id, training_results, spacy_training_settings):
    """
    Menyimpan hasil pelatihan ke tabel model_spacy_detail.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Format data untuk disimpan
        detail = []
        for result in training_results:
            detail.append({
                "Epoch": int(result.get('epoch')),
                "Loss": float(result.get('loss', 0)),
                "Precision": float(result.get('ents_p', 0)),
                "Recall": float(result.get('ents_r', 0)),
                "F1": float(result.get('ents_f', 0)),
            })

        # Konversi ke format JSON-safe
        import json
        detail_json = json.dumps(convert_np_types(detail))
        settings_json = json.dumps(convert_np_types(spacy_training_settings))

        # Simpan ke tabel model_spacy_detail
        query = """
            INSERT INTO model_spacy_detail (model_id, detail, settings)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (model_id, detail_json, settings_json))
        conn.commit()
        print(f"\n[SUCCESS] Hasil pelatihan dan settings berhasil disimpan. model_id: {model_id}")
    except Exception as e:
        print(f"\n[ERROR] Gagal menyimpan data ke database: {e}")
    finally:
        cursor.close()
        conn.close()

def train_spacy_model(model_name, train_data, spacy_training_settings):
    print(f"\n[Def train_spacy_model()]\n")

    model_path = os.path.join(BASE_MODEL_DIR, model_name)
    os.makedirs(BASE_MODEL_DIR, exist_ok=True)

    print(f"\nspacy_training_settings: {spacy_training_settings}\n")

    max_data = spacy_training_settings["data_used"]
    print(f"\nTrain data (sample): {train_data[:3]}\n")

    if max_data:
        random.shuffle(train_data)
        used_data_ids = [data[0] for data in train_data[:max_data]]
        print(f"\n[INFO] ID data yang digunakan setelah shuffle: {used_data_ids}\n")
        update_database_with_used_ids(used_data_ids)
        train_data = train_data[:max_data]

    # Hapus ID sebelum pelatihan
    train_data = [(text, annotations) for _, text, annotations in train_data]
    print(f"\n[INFO] Jumlah data yang digunakan untuk pelatihan: {len(train_data)}\n")

    # Bagi data menjadi training dan validation
    random.shuffle(train_data)
    split_point = int(len(train_data) * (1 - spacy_training_settings["test_size"]))
    train_examples = train_data[:split_point]
    eval_examples = train_data[split_point:]
    
    print(f"\n[INFO] Data training: {len(train_examples)}, Data validasi: {len(eval_examples)}\n")

    if os.path.exists(model_path):
        try:
            print(f"\n[INFO] Memuat model yang sudah ada: {model_name}\n")
            nlp = spacy.load(model_path)
        except Exception:
            print("\n[INFO] Membuat model baru...\n")
            nlp = spacy.blank("id")
    else:
        print(f"\n[INFO] Membuat model baru: {model_name}\n")
        nlp = spacy.blank("id")

    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Tambahkan label dari semua data (train dan eval)
    for text, annotations in train_data:
        for ent in annotations["entities"]:
            ner.add_label(ent[2])

    # Fungsi untuk evaluasi model
    def evaluate_model(nlp, examples):
        scorer = Scorer()
        all_examples = []
        for text, annotations in examples:
            doc_gold = nlp.make_doc(text)
            gold = Example.from_dict(doc_gold, annotations)
            pred = nlp(text)
            example = Example(pred, gold.reference)
            all_examples.append(example)

        # Score all examples at once
        if all_examples:
            scores = scorer.score(all_examples)
            return scores
        else:
            return {}

    def get_examples():
        for text, annotations in train_examples:  # Gunakan hanya train_examples
            doc = nlp.make_doc(text)
            yield Example.from_dict(doc, annotations)

    nlp.initialize(get_examples=get_examples)
    optimizer = nlp.begin_training()
    optimizer.learn_rate = spacy_training_settings["learning_rate"]

    # Simpan hasil training untuk laporan
    training_results = []

    print("\n[INFO] Memulai proses training...\n")
    for itn in range(spacy_training_settings["epochs"]):
        print(f"\n[EPOCH] {itn+1}/{spacy_training_settings['epochs']}\n")
        random.shuffle(train_examples)  # Shuffle hanya train_examples
        losses = {}
        batches = minibatch(train_examples, size=compounding(
            spacy_training_settings["batch_size_start"],
            spacy_training_settings["batch_size_end"],
            spacy_training_settings["batch_rate"]
        ))
        for batch in batches:
            examples = []
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)
            nlp.update(examples, drop=spacy_training_settings["dropout"], losses=losses, sgd=optimizer)
        
        # Evaluasi setelah setiap epoch
        metrics = evaluate_model(nlp, eval_examples)
        
        # Simpan hasil untuk laporan
        epoch_result = {
            "epoch": itn + 1,
            "loss": losses.get("ner", 0.0),
            "ents_p": metrics.get("ents_p", 0.0),  # Precision
            "ents_r": metrics.get("ents_r", 0.0),  # Recall
            "ents_f": metrics.get("ents_f", 0.0),  # F1 score
            "ents_per_type": metrics.get("ents_per_type", {})  # Metrik per entity type
        }
        training_results.append(epoch_result)
        
        # Tampilkan hasil
        print(f"\n[EPOCH {itn+1} RESULT]")
        print(f"Loss: {losses}")
        print(f"Precision: {metrics.get('ents_p', 0.0):.4f}")
        print(f"Recall: {metrics.get('ents_r', 0.0):.4f}")
        print(f"F1 Score: {metrics.get('ents_f', 0.0):.4f}")
        print(f"Per entity: {metrics.get('ents_per_type', {})}\n")

    # Simpan model
    nlp.to_disk(model_path)
    print(f"\n[SUCCESS] Model {model_name} berhasil disimpan di: {model_path}\n")
    
    # Tampilkan ringkasan hasil training
    print("\n[INFO] Training selesai. Berikut hasil akhir:")
    headers = ["Epoch", "Loss", "Precision", "Recall", "F1 Score"]
    rows = [(res["epoch"], f"{res['loss']:.4f}", f"{res['ents_p']:.4f}", 
            f"{res['ents_r']:.4f}", f"{res['ents_f']:.4f}") for res in training_results]
    print("\n" + tabulate(rows, headers=headers) + "\n")
    
    # Simpan hasil training ke database jika ada model_id
    if "model_id" in spacy_training_settings:
        save_spacy_training_results_to_db(spacy_training_settings["model_id"], training_results, spacy_training_settings)
    else:
        print("\n[WARNING] model_id tidak ditemukan di pengaturan, hasil pelatihan tidak disimpan ke database.")
    
    return model_path, training_results