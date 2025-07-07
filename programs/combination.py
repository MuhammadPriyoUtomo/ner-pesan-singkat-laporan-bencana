from helper.db_utils import get_db_dict_connection
import json, os

def fetch_location_details(provinsi_ids=None, kabupaten_ids=None, kecamatan_ids=None, desa_ids=None):
    """Mengambil detail lokasi berdasarkan ID dari tabel lokasi."""
    
    conn = get_db_dict_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        list_desa.nama_desa,
        list_kecamatan.nama_kecamatan,
        list_kabupaten.nama_kabupaten,
        list_provinsi.nama_provinsi
    FROM 
        list_desa
    LEFT JOIN list_kecamatan ON list_desa.id_kecamatan = list_kecamatan.id
    LEFT JOIN list_kabupaten ON list_kecamatan.id_kabupaten = list_kabupaten.id
    LEFT JOIN list_provinsi ON list_kabupaten.id_provinsi = list_provinsi.id
    WHERE 1=1
    """

    params = []
    if provinsi_ids:
        query += f" AND list_provinsi.id IN ({','.join(['%s'] * len(provinsi_ids))})"
        params.extend(provinsi_ids)
    if kabupaten_ids:
        query += f" AND list_kabupaten.id IN ({','.join(['%s'] * len(kabupaten_ids))})"
        params.extend(kabupaten_ids)
    if kecamatan_ids:
        query += f" AND list_kecamatan.id IN ({','.join(['%s'] * len(kecamatan_ids))})"
        params.extend(kecamatan_ids)
    if desa_ids:
        query += f" AND list_desa.id IN ({','.join(['%s'] * len(desa_ids))})"
        params.extend(desa_ids)

    cursor.execute(query, params)
    locations = cursor.fetchall()

    cursor.close()
    conn.close()
    return locations

def generate_combinations(location):
    """Membuat berbagai kombinasi tingkatan lokasi."""
    combinations = [
        location['nama_desa'],
        location['nama_kecamatan'],
        location['nama_kabupaten'],
        location['nama_provinsi'],
        f"{location['nama_desa']}, {location['nama_kecamatan']}",
        f"{location['nama_kecamatan']}, {location['nama_kabupaten']}",
        f"{location['nama_kabupaten']}, {location['nama_provinsi']}",
        f"{location['nama_desa']}, {location['nama_kecamatan']}, {location['nama_kabupaten']}",
        f"{location['nama_kecamatan']}, {location['nama_kabupaten']}, {location['nama_provinsi']}",
        f"{location['nama_desa']}, {location['nama_kecamatan']}, {location['nama_kabupaten']}, {location['nama_provinsi']}"
    ]
    return combinations

def write_combinations_to_file(combinations, folder, filename):
    """Menulis kombinasi lokasi ke file dengan pemisah antar blok."""
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)

        filepath = os.path.join(folder, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"File lama '{filepath}' telah dihapus.")

        with open(filepath, "w", encoding="utf-8") as file:
            for i, combination in enumerate(combinations):
                file.write(combination + "\n")
                if (i + 1) % 10 == 0:
                    file.write("\n")
        print(f"File '{filepath}' berhasil dibuat dengan {len(combinations)} kombinasi.")
    except Exception as e:
        print(f"Error saat menulis file: {e}")

def generate_combinations_for_model(model_id):
    """Menghasilkan kombinasi lokasi untuk model tertentu."""
    try:
        conn = get_db_dict_connection()
        cursor = conn.cursor()

        # Ambil data lokasi dari model_locations
        cursor.execute("SELECT locations FROM model_locations WHERE model_id = %s", (model_id,))
        result = cursor.fetchone()

        if not result:
            print(f"Tidak ada lokasi yang ditemukan untuk model ID {model_id}.")
            return "Model ID tidak valid."

        # Parse lokasi dari kolom JSON
        locations_data = json.loads(result['locations'])
        provinsi_ids = locations_data.get('provinsi_ids', [])
        kabupaten_ids = locations_data.get('kabupaten_ids', [])
        kecamatan_ids = locations_data.get('kecamatan_ids', [])
        desa_ids = locations_data.get('desa_ids', [])

        # Ambil lokasi berdasarkan filter
        locations = fetch_location_details(provinsi_ids, kabupaten_ids, kecamatan_ids, desa_ids)
        if not locations:
            print(f"Tidak ada lokasi yang ditemukan untuk filter yang diberikan.")
            return "Lokasi tidak ditemukan."

        # Buat kombinasi untuk setiap lokasi
        model_combinations = []
        for location in locations:
            combinations = generate_combinations(location)
            model_combinations.extend(combinations)

        # Ambil nama model
        cursor.execute("SELECT name FROM models WHERE id = %s", (model_id,))
        model = cursor.fetchone()
        model_name = model['name'] if model else f"model_{model_id}"

        # Tulis kombinasi ke file
        output_folder = "model_jaro_winkler"
        model_filename = f"{model_name}_combinations.txt"
        write_combinations_to_file(model_combinations, output_folder, model_filename)

        return f"Kombinasi lokasi untuk model '{model_name}' berhasil dibuat."
    except Exception as e:
        print(f"Error: {e}")
        return str(e)
    finally:
        cursor.close()
        conn.close()