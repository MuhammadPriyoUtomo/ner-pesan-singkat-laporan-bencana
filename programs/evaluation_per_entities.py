from sklearn.metrics import confusion_matrix, classification_report
from rapidfuzz import fuzz
from helper.db_utils import get_db_dict_connection, get_db_connection
from datetime import datetime
import mysql.connector, json, pandas as pd

def fetch_data_from_db():
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, text, annotations FROM data_olah_asli")
        data_olah_asli = cursor.fetchall()

        cursor.execute("SELECT id, chat_asli, hasil_ekstraksi FROM hasil_ekstraksi")
        hasil_ekstraksi = cursor.fetchall()

        cursor.close()
        conn.close()

        return data_olah_asli, hasil_ekstraksi
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return [], []

def parse_annotations(annotation_str):
    try:
        annotations = json.loads(annotation_str)
        entities = annotations.get("entities", [])
        parsed_entities = [(start, end, label) for start, end, label in entities]
        return parsed_entities
    except json.JSONDecodeError as e:
        print(f"Error parsing annotations: {e}")
        return []

def save_evaluation_to_db(model_name, cm, report, accuracy, mismatched_ids):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        query = """
            INSERT INTO evaluation_per_entity (model_name, confusion_matrix, classification_report, accuracy, mismatched_ids, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            model_name,
            json.dumps(cm.tolist()),
            json.dumps(report),
            accuracy,
            json.dumps(mismatched_ids),
            timestamp
        ))
        conn.commit()
        print("Hasil evaluasi berhasil disimpan ke database.")
    except mysql.connector.Error as e:
        print(f"Error menyimpan hasil evaluasi ke database: {e}")
    finally:
        cursor.close()
        conn.close()

def normalize_entity_text(text):
    if not text:
        return ""
    # Hilangkan spasi di sekitar tanda hubung, ubah ke lower, dan strip spasi ganda
    import re
    text = text.lower()
    text = re.sub(r'\s*([^\w\s,])\s*', r'\1', text)  # Gabungkan karakter khusus selain koma misal "awu - awu" jadi "awu-awu"
    text = re.sub(r'\s+', ' ', text)      # spasi ganda jadi satu
    return text.strip()

def is_fuzzy_match(true_entity, pred_entity):
    true_text, true_label = true_entity
    pred_text, pred_label = pred_entity

    if true_label != pred_label:
        return False

    true_text = normalize_entity_text(true_text)
    pred_text = normalize_entity_text(pred_text)

    # Hanya substring match dari pred ke true
    return pred_text and pred_text in true_text

def extract_entities(hasil_ekstraksi_str):
    try:
        parsed = json.loads(hasil_ekstraksi_str)
        if isinstance(parsed, dict) and "hasil_ekstraksi" in parsed:
            parsed = json.loads(parsed["hasil_ekstraksi"])

        entities = []
        # Format first_detected_match
        if "disaster" in parsed and "location" in parsed:
            if parsed["disaster"] and parsed["disaster"].get("text"):
                entities.append((parsed["disaster"]["text"].strip().lower(), "DISASTER"))
            if parsed["location"] and parsed["location"].get("text"):
                entities.append((parsed["location"]["text"].strip().lower(), "LOCATION"))
        else:
            # Format all_detected_matches
            for method, result in parsed.items():
                if result.get("location"):
                    loc = result["location"]
                    if loc:
                        entities.append((loc.strip().lower(), "LOCATION"))
                if result.get("disaster"):
                    dis = result["disaster"]
                    if dis:
                        entities.append((dis.strip().lower(), "DISASTER"))
        return entities
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return []

def evaluate_entity_main():
    print(f"\n\n============ EVALUASI PER ENTITAS OTOMATIS (GABUNGAN SEMUA MODEL) ============\n\n")

    data_olah_asli, hasil_ekstraksi = fetch_data_from_db()
    if not data_olah_asli or not hasil_ekstraksi:
        print("Data dari database kosong. Pastikan database terisi dengan data yang valid.")
        return

    y_true = []
    y_pred = []
    mismatched_ids = {
        "pred_false_actual_true": [],
        "pred_true_actual_false": []
    }

    for index, asli in enumerate(data_olah_asli, start=1):
        ekstraksi = next((h for h in hasil_ekstraksi if h["id"] == asli["id"]), None)
        true_entities = parse_annotations(asli["annotations"])

        true_disaster = next((asli["text"][start:end].strip() for start, end, label in true_entities if label == "DISASTER"), None)
        true_location = next((asli["text"][start:end].strip() for start, end, label in true_entities if label == "LOCATION"), None)

        pred_disaster = None
        pred_location = None

        if ekstraksi:
            pred_entities = extract_entities(ekstraksi["hasil_ekstraksi"])
            pred_disaster = next((text for text, label in pred_entities if label == "DISASTER"), None)
            pred_location = next((text for text, label in pred_entities if label == "LOCATION"), None)

        # Evaluasi disaster
        if true_disaster and pred_disaster:
            if is_fuzzy_match((true_disaster, "DISASTER"), (pred_disaster, "DISASTER")):
                y_true.append(1)
                y_pred.append(1)
            else:
                y_true.append(1)
                y_pred.append(0)
                mismatched_ids["pred_false_actual_true"].append(asli["id"])
        elif true_disaster and not pred_disaster:
            y_true.append(1)
            y_pred.append(0)
            mismatched_ids["pred_false_actual_true"].append(asli["id"])
        elif not true_disaster and pred_disaster:
            y_true.append(0)
            y_pred.append(1)
            mismatched_ids["pred_true_actual_false"].append(asli["id"])
        else:
            y_true.append(0)
            y_pred.append(0)

        # Evaluasi location
        if true_location and pred_location:
            if is_fuzzy_match((true_location, "LOCATION"), (pred_location, "LOCATION")):
                y_true.append(1)
                y_pred.append(1)
            else:
                y_true.append(1)
                y_pred.append(0)
                mismatched_ids["pred_false_actual_true"].append(asli["id"])
        elif true_location and not pred_location:
            y_true.append(1)
            y_pred.append(0)
            mismatched_ids["pred_false_actual_true"].append(asli["id"])
        elif not true_location and pred_location:
            y_true.append(0)
            y_pred.append(1)
            mismatched_ids["pred_true_actual_false"].append(asli["id"])
        else:
            y_true.append(0)
            y_pred.append(0)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    report = classification_report(
        y_true,
        y_pred,
        target_names=["False", "True"],
        labels=[0, 1],
        output_dict=True,
        zero_division=0
    )
    accuracy = (cm[0][0] + cm[1][1]) / cm.sum() if cm.sum() > 0 else 0

    report["accuracy"] = accuracy

    print("\n============ Hasil Evaluasi Gabungan ============\n")
    print("Confusion Matrix:")
    print(pd.DataFrame(cm, index=["Actual False", "Actual True"], columns=["Predicted False", "Predicted True"]))
    print("\nClassification Report:")
    print(classification_report(
        y_true,
        y_pred,
        target_names=["False", "True"],
        labels=[0, 1],
        zero_division=0
    ))
    print(f"\nAccuracy: {accuracy:.2f}")
    print(f"Pred False, Actual True: {mismatched_ids['pred_false_actual_true']}")
    print(f"Pred True, Actual False: {mismatched_ids['pred_true_actual_false']}")

    # Ambil mode deteksi dari database
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mode FROM detection_mode ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result["mode"] or result["mode"] == "disabled":
        model_name = "Unknown"
    else:
        model_name = result["mode"]

    save_evaluation_to_db(
        model_name=model_name,
        cm=cm,
        report=report,
        accuracy=accuracy,
        mismatched_ids=mismatched_ids
    )

    print("\n============ Evaluasi Selesai ============\n")