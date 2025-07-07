from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from helper.db_utils import get_db_dict_connection, get_db_connection
from datetime import datetime
import json, tabulate

def ambil_data():
    # koneksi ke MySQL (ganti dengan punyamu)
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    # 1. Ambil data asli dari database
    cursor.execute("SELECT * FROM hasil_ekstraksi")
    data_deteksi = cursor.fetchall()

    cursor.execute("SELECT * FROM data_olah_asli")  # atau table lain tempat data aslimu
    data_asli = cursor.fetchall()

    cursor.close()
    conn.close()

    return data_asli, data_deteksi

def clean_data_deteksi(data_deteksi):
    hasil_bersih = []
    for item in data_deteksi:
        # Pertama parse hasil_ekstraksi luar (berisi string JSON dalam bentuk string)
        outer = json.loads(item['hasil_ekstraksi'])

        # Parse hasil_ekstraksi dalam (yang sebelumnya di-escape dengan banyak \)
        inner = json.loads(outer['hasil_ekstraksi'])

        # Ganti hasil_ekstraksi menjadi dict, bukan string
        outer['hasil_ekstraksi'] = inner

        hasil_bersih.append(outer)
    return hasil_bersih

def simpan_hasil_evaluasi(model_name, evaluation_result):
    # Koneksi ke database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Konversi confusion_matrix dan mismatched_ids menjadi JSON
    confusion_matrix_list = evaluation_result['confusion_matrix'].tolist()
    mismatched_ids_json = json.dumps(evaluation_result['mismatched_ids'])

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # Simpan hasil evaluasi ke tabel evaluasi_report
    cursor.execute("""
        INSERT INTO evaluation_per_report (model_name, confusion_matrix, classification_report, accuracy, mismatched_ids, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        model_name,
        json.dumps(confusion_matrix_list),  # Simpan confusion matrix sebagai JSON
        json.dumps(evaluation_result['classification_report']),  # Simpan classification report sebagai JSON
        evaluation_result['accuracy'],  # Simpan akurasi
        mismatched_ids_json,  # Simpan mismatched_ids sebagai JSON
        timestamp  # Simpan timestamp
    ))
    conn.commit()
    cursor.close()
    conn.close()

def evaluate_status(data_asli, dict_data_deteksi, selected_model=None):
    y_true = []
    y_pred = []
    mismatched_ids = {
        "pred_bukan_actual_report": [],
        "pred_report_actual_bukan": []
    }

    # Buat dict lookup berdasarkan id untuk efisiensi
    deteksi_lookup = {item['id']: item for item in dict_data_deteksi}

    for item in data_asli:
        id_ = item['id']
        status_db = item.get("report_status", "bukan report")
        y_true_label = 1 if status_db == "report" else 0
        y_true.append(y_true_label)

        # Cek apakah hasil deteksi tersedia
        deteksi = deteksi_lookup.get(id_)
        if not deteksi:
            y_pred.append(0)  # fallback ke "bukan report" kalau tidak ditemukan
            if y_true_label == 1:  # Jika actual adalah "report"
                mismatched_ids["pred_bukan_actual_report"].append(id_)
            continue
        
        status_pred = deteksi.get("report_status", "bukan report")

        y_pred_label = 1 if status_pred == "report" else 0
        y_pred.append(y_pred_label)

        # Catat ID jika ada mismatch
        if y_pred_label == 0 and y_true_label == 1:
            mismatched_ids["pred_bukan_actual_report"].append(id_)
        elif y_pred_label == 1 and y_true_label == 0:
            mismatched_ids["pred_report_actual_bukan"].append(id_)

    # Evaluasi metrik
    cm = confusion_matrix(y_true, y_pred)
    cr = classification_report(y_true, y_pred, target_names=["bukan report", "report"], output_dict=True, zero_division=0)
    acc = accuracy_score(y_true, y_pred)

    # Return hasil evaluasi dan mismatched IDs
    return {
        "confusion_matrix": cm,
        "classification_report": cr,
        "accuracy": acc,
        "mismatched_ids": mismatched_ids
    }

def print_evaluation_human_friendly(title, evaluation_result):
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")

    # Confusion Matrix
    cm = evaluation_result['confusion_matrix']
    print("📊 Confusion Matrix (Actual vs Predicted):")
    headers = ["", "Pred: Bukan Report", "Pred: Report"]
    rows = [
        ["Actual: Bukan Report", cm[0][0], cm[0][1]],
        ["Actual: Report", cm[1][0], cm[1][1]],
    ]
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
    print()

    # Classification Report (Per Label)
    print("📋 Classification Report (Per Class):")
    cr = evaluation_result['classification_report']
    rows = [
        ["Label", "Precision", "Recall", "F1-Score", "Support"],
        ["Bukan Report", f"{cr['bukan report']['precision']:.2f}", f"{cr['bukan report']['recall']:.2f}",
         f"{cr['bukan report']['f1-score']:.2f}", f"{cr['bukan report']['support']}"],
        ["Report", f"{cr['report']['precision']:.2f}", f"{cr['report']['recall']:.2f}",
         f"{cr['report']['f1-score']:.2f}", f"{cr['report']['support']}"],
    ]
    print(tabulate(rows, headers="firstrow", tablefmt="fancy_grid"))
    print()

    # Tambahkan macro avg dan weighted avg
    print("📈 Overall Performance (Averages):")
    rows = [
        ["Averaging", "Precision", "Recall", "F1-Score", "Support"],
        ["Macro Avg", f"{cr['macro avg']['precision']:.2f}", f"{cr['macro avg']['recall']:.2f}",
         f"{cr['macro avg']['f1-score']:.2f}", f"{cr['macro avg']['support']}"],
        ["Weighted Avg", f"{cr['weighted avg']['precision']:.2f}", f"{cr['weighted avg']['recall']:.2f}",
         f"{cr['weighted avg']['f1-score']:.2f}", f"{cr['weighted avg']['support']}"]
    ]
    print(tabulate(rows, headers="firstrow", tablefmt="fancy_grid"))

    print(f"\n✅ Total Accuracy: {evaluation_result['accuracy']:.2f}")
    print("\n")

def evaluate_report_main():
    # Ambil detection mode dari database
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mode FROM detection_mode ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result["mode"] or result["mode"] == "disabled":
        print("Mode deteksi tidak ditemukan atau dinonaktifkan.")
        model_name = "Unknown"
    else:
        model_name = result["mode"]

    data_asli, data_deteksi = ambil_data()
    dict_data_deteksi = clean_data_deteksi(data_deteksi)

    result_eval = evaluate_status(data_asli, dict_data_deteksi)
    # print_evaluation_human_friendly(f"Evaluasi - {model_name}", result_eval)

    simpan_hasil_evaluasi(model_name=model_name, evaluation_result=result_eval)

    # Cetak ID pesan yang mismatch
    print("\n🔍 ID pesan dengan prediksi salah:")
    print(f"(Pred: Bukan Report, Actual: Report): {result_eval['mismatched_ids']['pred_bukan_actual_report']}")
    print(f"(Pred: Report, Actual: Bukan Report): {result_eval['mismatched_ids']['pred_report_actual_bukan']}")