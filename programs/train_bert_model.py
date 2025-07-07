from datasets import Dataset, DatasetDict
from transformers import (AutoTokenizer, AutoModelForTokenClassification,
                          DataCollatorForTokenClassification, Trainer, TrainingArguments, TrainerCallback, EarlyStoppingCallback)
from helper.db_utils import get_db_connection
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from tabulate import tabulate
import numpy as np, os, random

# Project menggunakan Hugging Face Transformers indolem/indobert-base-uncased

# Path constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Folder root proyek
BASE_MODEL_DIR = os.path.join(BASE_DIR, "model_bert")  # Path ke folder model_bert

class LoggingCallback(TrainerCallback):
    def __init__(self, results_list):
        self.results_list = results_list
        self.current_epoch_metrics = {}
        self.last_step = 0
        self.pending_eval_metrics = False  # Flag to track if we're waiting for eval metrics

    def on_epoch_begin(self, args, state, control, **kwargs):
        print(f"\n[INFO] Memulai Epoch {state.epoch:.1f}/{args.num_train_epochs}\n")
        self.current_epoch_metrics = {"epoch": state.epoch}

    def on_step_end(self, args, state, control, **kwargs):
        if state.log_history and 'loss' in state.log_history[-1]:
            log = state.log_history[-1]
            if 'loss' in log and 'eval_loss' not in log:  # Hanya log training loss
                self.current_epoch_metrics["train_loss"] = log['loss']
                self.last_step = state.global_step  # Store the step number
                print(f"[INFO] Langkah {state.global_step}: Loss = {log['loss']:.4f}")

    def on_evaluate(self, args, state, control, metrics, **kwargs):
        # Store metrics directly when evaluation happens
        if metrics:
            eval_metrics = {
                "step": self.last_step,
                "eval_loss": metrics.get("eval_loss", None),
                "precision": metrics.get("eval_precision", None),
                "recall": metrics.get("eval_recall", None),
                "f1": metrics.get("eval_f1", None),
                "accuracy": metrics.get("eval_accuracy", None)
            }
            
            # Update current epoch metrics with evaluation results
            self.current_epoch_metrics.update(eval_metrics)
            
            # If this is from an epoch end evaluation, print results
            if self.pending_eval_metrics:
                self.pending_eval_metrics = False
                self._print_epoch_results()
                
                # Now add to results list after we have all metrics
                self.results_list.append(self.current_epoch_metrics.copy())

    # Rest of the class remains the same...

    def on_epoch_end(self, args, state, control, **kwargs):
        # Set the epoch in metrics
        self.current_epoch_metrics["epoch"] = state.epoch
        
        # Flag that we're waiting for eval metrics (which come after epoch end)
        self.pending_eval_metrics = True
        
        # We'll print results after evaluation metrics come in

    def _format_metric(self, value):
        """Helper untuk memformat nilai metrik (handle None/string)"""
        if value is None or isinstance(value, str):
            return "-"
        # return f"{value:.4f}"
        return f"{value}"
    
    def _print_epoch_results(self):
        """Helper to print epoch results with actual metrics"""
        if self.current_epoch_metrics:
            print(f"\n[EPOCH {self.current_epoch_metrics['epoch']:.0f} RESULT]")
            
            train_loss = self._format_metric(self.current_epoch_metrics.get('train_loss'))
            eval_loss = self._format_metric(self.current_epoch_metrics.get('eval_loss'))
            precision = self._format_metric(self.current_epoch_metrics.get('precision'))
            recall = self._format_metric(self.current_epoch_metrics.get('recall'))
            f1 = self._format_metric(self.current_epoch_metrics.get('f1'))
            accuracy = self._format_metric(self.current_epoch_metrics.get('accuracy'))
            
            print(f"Train Loss: {train_loss}")
            print(f"Eval Loss: {eval_loss}")
            print(f"Precision: {precision}")
            print(f"Recall: {recall}")
            print(f"F1: {f1}")
            print(f"Accuracy: {accuracy}\n")

# Fungsi untuk mengonversi data ke format BIO (dengan deteksi jeda entity)
def convert_to_bio(text, entities, tokenizer, label2id):
    # Tokenisasi teks dan dapatkan mapping offset
    tokens = tokenizer(text, return_offsets_mapping=True, truncation=True, max_length=512)
    print(f"\n[INFO] Tokenisasi: {tokens}\n")
    input_tokens = tokenizer.convert_ids_to_tokens(tokens['input_ids'])
    print(f"\n[INFO] Input tokens: {input_tokens}\n")
    offsets = tokens['offset_mapping']
    print(f"\n[INFO] Offset mapping: {offsets}\n")
    
    # Inisialisasi label dengan 'O' (Outside)
    labels = ['O'] * len(offsets)
    print(f"\n[INFO] Inisialisasi labels: {labels}\n")

    # Urutkan entitas berdasarkan start position untuk penanganan yang berurutan
    entities = sorted(entities, key=lambda x: x[0])
    print(f"\n[INFO] Entitas yang diurutkan: {entities}\n")

    # Iterasi melalui semua entitas
    for start, end, label in entities:
        print(f"\n[INFO] Memproses entitas: {start}, {end}, {label}\n")
        for i, (token_start, token_end) in enumerate(offsets):
            print(f"\n[INFO] Memeriksa token: {token_start}, {token_end}\n")
            # Skip special tokens like [CLS], [SEP]
            if token_start == token_end == 0:
                continue

            # Cek apakah token bertumpang tindih dengan entitas
            if token_end <= start or token_start >= end:
                print(f"\n[INFO] Token di luar entitas: {token_start}, {token_end}\n")
                continue  # Token di luar entitas

            # Token bertumpang tindih dengan entitas
            if token_start >= start and token_end <= end:
                print(f"\n[INFO] Token di dalam entitas: {token_start}, {token_end}\n")
                if token_start == start:
                    print(f"\n[INFO] Token pertama dari entitas: {token_start}, {token_end}\n")
                    labels[i] = f"B-{label}"  # Token pertama dari entitas
                    print(f"\n[INFO] Label ditetapkan: {labels[i]}\n")
                else:
                    labels[i] = f"I-{label}"  # Token lanjutan dari entitas
                    print(f"\n[INFO] Label ditetapkan: {labels[i]}\n")

    # Konversi label teks ke ID
    label_ids = [label2id.get(lab, label2id['O']) for lab in labels]
    print(f"\n[INFO] Label IDs: {label_ids}\n")

    return {
        "tokens": input_tokens,
        "input_ids": tokens['input_ids'],
        "attention_mask": tokens['attention_mask'],
        "labels": label_ids,
        "offsets": offsets  # opsional untuk debugging
    }

def update_database_with_used_ids(used_data_ids):
    # Koneksi ke database MySQL
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query untuk memperbarui kolom bert_train_used menjadi 1
        query = "UPDATE data_create_model SET bert_train_used = 1 WHERE id = %s"
        cursor.executemany(query, [(data_id,) for data_id in used_data_ids])
        conn.commit()
        print(f"\n[SUCCESS] Kolom bert_train_used berhasil diperbarui untuk ID: {used_data_ids}")
    except Exception as e:
        print(f"\n[ERROR] Gagal memperbarui database: {e}")
    finally:
        cursor.close()
        conn.close()

def save_training_results_to_db(model_id, training_results, bert_training_settings):
    """
    Menyimpan hasil pelatihan ke tabel model_bert_detail.
    Sekaligus menyimpan konfigurasi bert_training_settings ke kolom settings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Format data untuk disimpan
        detail = []
        for result in training_results:
            detail.append({
                "Training Loss": result.get('train_loss'),
                "Epoch": result.get('epoch'),
                "Step": result.get('step'),
                "Validation Loss": result.get('eval_loss'),
                "Precision": result.get('precision'),
                "Recall": result.get('recall'),
                "F1": result.get('f1'),
                "Accuracy": result.get('accuracy')
            })

        import json
        detail_json = json.dumps(detail)
        settings_json = json.dumps(bert_training_settings)  # Konversi settings ke JSON

        # Sesuaikan query sesuai skema kolom baru (settings)
        query = """
            INSERT INTO model_bert_detail (model_id, detail, settings)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (model_id, detail_json, settings_json))
        conn.commit()
        print(f"\n[SUCCESS] Hasil pelatihan dan bert_training_settings berhasil disimpan. model_id: {model_id}")
    except Exception as e:
        print(f"\n[ERROR] Gagal menyimpan data ke database: {e}")
    finally:
        cursor.close()
        conn.close()

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    
    # Flatten predictions dan labels (abaikan padding tokens -100)
    mask = labels != -100
    flat_predictions = predictions[mask].flatten()
    flat_labels = labels[mask].flatten()
    
    # Hitung semua metrik
    precision = precision_score(flat_labels, flat_predictions, average='weighted', zero_division=0)
    recall = recall_score(flat_labels, flat_predictions, average='weighted', zero_division=0)
    f1 = f1_score(flat_labels, flat_predictions, average='weighted', zero_division=0)
    accuracy = accuracy_score(flat_labels, flat_predictions)
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy
    }

# Fungsi utama untuk melatih model BERT
def train_bert_model(model_name, train_data, bert_training_settings):

    print(f"\n[Def train_bert_model()]\n")
    print(f"bert_training_settings: {bert_training_settings}")

    model_path = os.path.join(BASE_MODEL_DIR, model_name)
    os.makedirs(model_path, exist_ok=True)

    max_data = bert_training_settings.get("data_used")

    print(f"\nTrain data (sample): {train_data[:3]}")

    # Randomisasi dan pembatasan data
    if max_data:
        random.shuffle(train_data)
        used_data_ids = [data["id"] for data in train_data[:max_data]]
        print(f"\n[INFO] ID data yang digunakan setelah shuffle: {used_data_ids}")
        update_database_with_used_ids(used_data_ids)
        train_data = train_data[:max_data]

    print(f"\n[INFO] Jumlah data yang digunakan untuk pelatihan: {len(train_data)}")

    # Default label jika tidak diberikan
    if "label_list" not in bert_training_settings:
        label_list = ['O', 'B-LOCATION', 'I-LOCATION', 'B-DISASTER', 'I-DISASTER']
        bert_training_settings["label_list"] = label_list
        bert_training_settings["label2id"] = {label: i for i, label in enumerate(label_list)}
        bert_training_settings["id2label"] = {i: label for label, i in bert_training_settings["label2id"].items()}

    print(f"\n[INFO] data diterima di train_bert_model(): {bert_training_settings}\n")

    BASE_DIR = os.getcwd()  # Direktori kerja aplikasi Flask
    BERT_MODEL_INDOLEM = os.path.join(BASE_DIR, "indolem_indobert-base-uncased")  # Path ke model indolem/indobert-base-uncased

    tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_INDOLEM)
    model = AutoModelForTokenClassification.from_pretrained(
        BERT_MODEL_INDOLEM,
        num_labels=len(bert_training_settings["label_list"]),
        id2label=bert_training_settings["id2label"],
        label2id=bert_training_settings["label2id"]
    )

    # Proses data
    dataset_entries = []
    for data in train_data:
        bio_bert = data["bio_bert"]
        dataset_entries.append({
            "input_ids": bio_bert["input_ids"],
            "attention_mask": bio_bert["attention_mask"],
            "labels": bio_bert["labels"]
        })

    full_dataset = Dataset.from_list(dataset_entries)
    train_test = full_dataset.train_test_split(test_size=bert_training_settings["test_size"])
    dataset = DatasetDict({"train": train_test["train"], "test": train_test["test"]})

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    training_results = []

    training_args = TrainingArguments(
        output_dir=model_path,
        learning_rate=bert_training_settings["learning_rate"],
        per_device_train_batch_size=bert_training_settings["train_batch_size"],
        per_device_eval_batch_size=bert_training_settings["eval_batch_size"],
        num_train_epochs=bert_training_settings["epochs"],
        weight_decay=bert_training_settings["weight_decay"],
        logging_dir="./logs",
        logging_steps=1,
        save_strategy="epoch",
        eval_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_f1",  # Tetap gunakan ini karena return kita menggunakan prefix eval_
        greater_is_better=True,
        save_total_limit=1,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=[
            LoggingCallback(training_results),  # Callback untuk logging standar
            EarlyStoppingCallback(
                early_stopping_patience=bert_training_settings["early_stopping_patience"],  # Berhenti setelah 3 epoch tanpa perbaikan
                early_stopping_threshold=bert_training_settings["early_stopping_threshold"],  # Perbaikan minimal 0.001
            ),
        ],
        compute_metrics=compute_metrics  # <-- TAMBAHKAN INI
    )

    print("\n[INFO] Memulai proses training...\n")
    trainer.train()

    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)
    print(f"\n[SUCCESS] Model {model_name} berhasil disimpan di: {model_path}\n")

    # Di bagian tampilan hasil akhir, gunakan fungsi yang sama:
    # Alternative printing using tabulate:
    print("\n[INFO] Training selesai. Berikut hasil akhir:\n")
    logging_callback = LoggingCallback(training_results)

    # Prepare data for tabulate
    headers = ["Training Loss", "Epoch", "Step", "Validation Loss", "Precision", "Recall", "F1", "Accuracy"]
    data = []
    for result in training_results:
        data.append([
            logging_callback._format_metric(result.get('train_loss')),
            f"{result['epoch']:.1f}",
            result.get('step', '-'),
            logging_callback._format_metric(result.get('eval_loss')),
            logging_callback._format_metric(result.get('precision')),
            logging_callback._format_metric(result.get('recall')),
            logging_callback._format_metric(result.get('f1')),
            logging_callback._format_metric(result.get('accuracy'))
        ])

    print(tabulate(data, headers=headers, tablefmt="simple"))

    # Simpan hasil pelatihan ke database
    model_id = bert_training_settings.get("model_id")  # Pastikan model_id tersedia di pengaturan
    if model_id:
        save_training_results_to_db(model_id, training_results, bert_training_settings)
    else:
        print("\n[WARNING] model_id tidak ditemukan di pengaturan, hasil pelatihan tidak disimpan ke database.")