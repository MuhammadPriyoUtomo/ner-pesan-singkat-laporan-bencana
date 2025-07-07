// Create Model
document.addEventListener("DOMContentLoaded", () => {
    // const trainingForm = document.getElementById("trainingForm");
    const createModelForm = document.getElementById("createModelForm");

    const provinsiCheckboxes = document.querySelectorAll("input[name='provinsi[]']");
    const kabupatenContainer = document.getElementById("kabupaten-container");
    const kecamatanContainer = document.getElementById("kecamatan-container");
    const desaContainer = document.getElementById("desa-container");


    // Fungsi untuk menampilkan modal loading
    function showLoadingModal() {
        const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"), {
            backdrop: "static",
            keyboard: false
        });
        loadingModal.show();
    }

    // Fungsi untuk submit form create model
    function submitCreateModelForm() {
        console.log("submitCreateModelForm called"); // Log untuk debugging

        // Validasi checkbox provinsi
        const checkboxes = document.querySelectorAll("input[name='provinsi[]']:checked");
        if (checkboxes.length === 0) {
            alert("Pilih setidaknya satu provinsi untuk model ini.");
            return; // Hentikan proses submit jika tidak ada checkbox yang dipilih
        }

        // Tutup modal konfirmasi
        const confirmModal = bootstrap.Modal.getInstance(document.getElementById("confirmCreateModelModal"));
        if (confirmModal) {
            confirmModal.hide();
        }

        showLoadingModal(); // Tampilkan modal loading

        // Mengirim permintaan POST menggunakan fetch
        fetch(createModelForm.action, {
            method: "POST",
            body: new FormData(createModelForm),
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(response => {
                console.log("Response received:", response); // Log respons
                if (response.ok) {
                    // Reload halaman setelah model berhasil dibuat
                    window.location.reload();
                } else {
                    throw new Error('Network response was not ok');
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Error: " + error.message);
            });
    }

    // Tampilkan modal konfirmasi saat tombol "Create Model" diklik
    createModelSubmitBtn.addEventListener("click", () => {
        const confirmModal = new bootstrap.Modal(document.getElementById("confirmCreateModelModal"));
        confirmModal.show();
    });

    // Submit form saat tombol "Ya, Lanjutkan" di modal diklik
    confirmCreateModelSubmitBtn.addEventListener("click", () => {
        submitCreateModelForm();
    });

    // Fungsi untuk memuat checkbox lokasi
    function loadCheckboxes(level, parentIds, container) {
        // Simpan status checkbox yang dipilih
        const selectedValues = Array.from(container.querySelectorAll("input[type='checkbox']:checked"))
            .map(checkbox => checkbox.value);

        container.innerHTML = `<p>Loading...</p>`; // Tampilkan pesan loading

        fetch(`/get_locations?level=${level}&parent_id=${parentIds}`)
            .then(response => response.json())
            .then(data => {
                container.innerHTML = ""; // Kosongkan container
                if (data.locations) {
                    const row = document.createElement("div");
                    row.classList.add("row"); // Tambahkan kelas row untuk grid

                    data.locations.forEach(location => {
                        const col = document.createElement("div");
                        col.classList.add("col-md-3"); // Set ukuran kolom, misalnya 4 kolom per baris
                        col.classList.add("mt-2");

                        const checkbox = document.createElement("input");
                        checkbox.type = "checkbox";
                        checkbox.name = `${level}[]`;
                        checkbox.value = location.id;
                        checkbox.id = `${level}_${location.id}`;
                        checkbox.classList.add("form-check-input");

                        // Pulihkan status checkbox jika sebelumnya dipilih
                        if (selectedValues.includes(location.id.toString())) {
                            checkbox.checked = true;
                        }

                        const label = document.createElement("label");
                        label.htmlFor = `${level}_${location.id}`;
                        label.textContent = location.name;
                        label.classList.add("form-check-label");

                        const formCheck = document.createElement("div");
                        formCheck.classList.add("form-check");
                        formCheck.style.marginBottom = "10px"; // Tambahkan jarak antar checkbox
                        formCheck.appendChild(checkbox);
                        formCheck.appendChild(label);

                        col.appendChild(formCheck);
                        row.appendChild(col);
                    });

                    container.appendChild(row); // Tambahkan row ke container
                } else {
                    container.innerHTML = `<p>Tidak ada data ${level} tersedia.</p>`;
                }
            })
            .catch(error => {
                console.error(`Error loading ${level}:`, error);
                container.innerHTML = `<p>Error loading data.</p>`;
            });
    }

    // Event listener untuk checkbox provinsi
    provinsiCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", () => {
            const selectedProvinsiIds = Array.from(provinsiCheckboxes)
                .filter(checkbox => checkbox.checked)
                .map(checkbox => checkbox.value)
                .join(',');

            if (selectedProvinsiIds) {
                loadCheckboxes("kabupaten", selectedProvinsiIds, kabupatenContainer);
                kecamatanContainer.innerHTML = ""; // Reset kecamatan
                desaContainer.innerHTML = ""; // Reset desa
            } else {
                kabupatenContainer.innerHTML = `<p>Pilih provinsi terlebih dahulu.</p>`;
                kecamatanContainer.innerHTML = "";
                desaContainer.innerHTML = "";
            }
        });
    });

    // Event listener untuk checkbox kabupaten
    kabupatenContainer.addEventListener("change", () => {
        const kabupatenCheckboxes = kabupatenContainer.querySelectorAll("input[name='kabupaten[]']:checked");
        const selectedKabupatenIds = Array.from(kabupatenCheckboxes)
            .map(checkbox => checkbox.value)
            .join(',');

        if (selectedKabupatenIds) {
            loadCheckboxes("kecamatan", selectedKabupatenIds, kecamatanContainer);
            desaContainer.innerHTML = ""; // Reset desa
        } else {
            kecamatanContainer.innerHTML = `<p>Pilih kabupaten terlebih dahulu.</p>`;
            desaContainer.innerHTML = "";
        }
    });

    // Event listener untuk checkbox kecamatan
    kecamatanContainer.addEventListener("change", () => {
        const kecamatanCheckboxes = kecamatanContainer.querySelectorAll("input[name='kecamatan[]']:checked");
        const selectedKecamatanIds = Array.from(kecamatanCheckboxes)
            .map(checkbox => checkbox.value)
            .join(',');

        if (selectedKecamatanIds) {
            loadCheckboxes("desa", selectedKecamatanIds, desaContainer);
        } else {
            desaContainer.innerHTML = `<p>Pilih kecamatan terlebih dahulu.</p>`;
        }
    });

    createModelForm.addEventListener("submit", (e) => {
        const checkboxes = document.querySelectorAll("input[name='provinsi[]']:checked");
        if (checkboxes.length === 0) {
            e.preventDefault();
            alert("Pilih setidaknya satu provinsi untuk model ini.");
        }
    });

});