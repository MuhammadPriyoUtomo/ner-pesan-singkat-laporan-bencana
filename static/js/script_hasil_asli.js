document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.querySelector('table tbody');
    const tableRows = document.querySelectorAll('table tbody tr');
    const noDataFound = !tableBody || tableRows.length === 0;

    const currentUrl = window.location.pathname;
    const currentPage = new URLSearchParams(window.location.search).get('page') || "1";

    const lastPage = localStorage.getItem('lastPageHasilAsli');
    const hasRedirected = localStorage.getItem('hasRedirectedHasilAsli');

    // 1. Jika tidak ada data dan bukan halaman default: kembali ke halaman default
    if (noDataFound && currentUrl === '/hasil_asli' && currentPage !== "1") {
        localStorage.removeItem('lastPageHasilAsli');
        window.location.href = '/hasil_asli';
        return;
    }

    // 2. Jika tidak ada data dan sudah di halaman default: jangan apa-apa
    if (noDataFound && currentUrl === '/hasil_asli') {
        return;
    }

    // 3. Jika ada data tapi belum di halaman terakhir, redirect
    if (lastPage && !hasRedirected && parseInt(currentPage) !== parseInt(lastPage)) {
        localStorage.setItem('hasRedirectedHasilAsli', 'true');
        const url = new URL(window.location.href);
        url.searchParams.set('page', lastPage);
        window.location.href = url.toString();
        return;
    } else {
        // Reset flag redirect jika sudah di halaman benar
        localStorage.removeItem('hasRedirectedHasilAsli');
    }

    // 4. Tangani form input manual pada pagination
    document.querySelectorAll('.page-item form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault(); // Mencegah reload halaman default
            const page = form.querySelector('input[name="page"]')?.value;
            if (page) {
                localStorage.setItem('lastPageHasilAsli', page);
                const url = new URL(window.location.href);
                url.searchParams.set('page', page);
                window.location.href = url.toString();
            }
        });
    });

    // 5. Simpan halaman saat klik pagination
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function () {
            const page = this.dataset.page || new URL(this.href).searchParams.get('page');
            if (page) {
                localStorage.setItem('lastPageHasilAsli', page);
            }
        });
    });
});

// submit deteksi generate data
function submitDeteksiGenerateDataForm() {
    // Tampilkan modal loading
    var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        backdrop: 'static',
        keyboard: false
    });
    loadingModal.show();

    // Tutup modal konfirmasi
    var deteksiGenerateDataModal = bootstrap.Modal.getInstance(document.getElementById('deteksiGenerateDataModal'));
    deteksiGenerateDataModal.hide();

    // Mengirim permintaan AJAX untuk memulai deteksi data
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/deteksi_data', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Mengganti state riwayat untuk mencegah tombol back
            history.replaceState(null, null, window.location.href);
            allowForward = true;
            isProcessing = false;
            window.location.replace('/hasil_deteksi');
        }
    };
    isProcessing = true;
    xhr.send('deteksi_generate=true');
}

// Detection Mode
document.addEventListener('DOMContentLoaded', function () {
    const detectionModeButton = document.getElementById('detectionModeDropdown');

    // Fungsi untuk memperbarui warna tombol berdasarkan mode
    function updateButtonStyle(button, mode) {
        switch (mode) {
            case 'bert+spacy':
                button.style.backgroundColor = '#28a745'; // Hijau Tua
                button.style.color = '#ffffff'; // Teks putih
                break;
            case 'bert':
                button.style.backgroundColor = '#007bff'; // Biru
                button.style.color = '#ffffff'; // Teks putih
                break;
            case 'spacy':
                button.style.backgroundColor = '#007bff'; // Biru
                button.style.color = '#ffffff'; // Teks putih
                break;
            case 'jaro':
                button.style.backgroundColor = '#fd7e14'; // Oranye
                button.style.color = '#ffffff'; // Teks putih
                break;
            default:
                button.style.backgroundColor = ''; // Reset ke default
                button.style.color = ''; // Reset ke default
        }
    }

    // Fungsi untuk mengatur mode
    function setDetectionMode(mode) {
        fetch('/set_detection_mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ detection_mode: mode })
        }).then(response => {
            if (response.ok) {
                detectionModeButton.textContent = `Mode Deteksi: ${mode}`;
                updateButtonStyle(detectionModeButton, mode);
            } else {
                alert('Gagal memperbarui mode Detection.');
            }
        });
    }

    // Fetch mode awal dari server
    fetch('/get_detection_mode')
        .then(response => response.json())
        .then(data => {
            detectionModeButton.textContent = `Mode Deteksi: ${data.detection_mode}`;
            updateButtonStyle(detectionModeButton, data.detection_mode);
        })
        .catch(error => {
            console.error('Error fetching detection modes:', error);
        });

    // Ekspor fungsi ke global scope
    window.setDetectionMode = setDetectionMode;
});

// Region Detection Model
document.addEventListener('DOMContentLoaded', function () {
    const dropdownButton = document.getElementById('modelRegionDetectionDropdown');
    const modelIdInput = document.getElementById('model_id');
    const dropdownItems = document.querySelectorAll('#modelRegionDetectionDropdown + .dropdown-menu .dropdown-item');
    const deteksiButton = document.getElementById('deteksiDataButton');

    // Selalu nonaktifkan tombol deteksi saat halaman dimuat
    if (deteksiButton) {
        deteksiButton.disabled = true;

        // Tambahkan event listener untuk tombol deteksi data
        deteksiButton.addEventListener('click', function () {
            if (!this.disabled) {
                // Tampilkan modal konfirmasi
                var deteksiGenerateDataModal = new bootstrap.Modal(document.getElementById('deteksiGenerateDataModal'));
                deteksiGenerateDataModal.show();
            }
        });
    }

    // Hapus atribut data-selected dari semua item dropdown (memaksa user memilih secara manual)
    dropdownItems.forEach(item => {
        item.removeAttribute('data-selected');
    });

    // Selalu set default teks dropdown ke "Pilih Model Region Detection"
    dropdownButton.textContent = 'Pilih Model Region Detection';

    // Tambahkan event listener ke item dropdown
    dropdownItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const modelId = this.getAttribute('data-id');
            const modelName = this.getAttribute('data-name');

            // Perbarui tombol dropdown
            dropdownButton.textContent = 'Model Region Detection: ' + modelName;

            // Hapus atribut data-selected dari semua item dan tambahkan ke item yang dipilih
            dropdownItems.forEach(i => i.removeAttribute('data-selected'));
            this.setAttribute('data-selected', 'true');

            // Aktifkan tombol deteksi
            if (deteksiButton) {
                deteksiButton.disabled = false;
            }

            // Kirim model yang dipilih ke server
            setRegionDetectionModel(modelId, modelName);
        });
    });

    const deteksiModal = document.getElementById('deteksiGenerateDataModal');
    const batalButton = deteksiModal?.querySelector('.btn-secondary'); // Tombol Batal
    const closeButton = deteksiModal?.querySelector('.btn-close'); // Tombol Close (silang)

    if (deteksiModal) {
        // Hanya hapus backdrop jika tombol Batal atau Close ditekan
        [batalButton, closeButton].forEach(button => {
            if (button) {
                button.addEventListener('click', function () {
                    // Hapus backdrop secara manual
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    // Hapus class modal-open dari body
                    document.body.classList.remove('modal-open');
                    // Reset style padding-right
                    document.body.style.paddingRight = '';
                });
            }
        });
    }
});

// Fungsi untuk mengirim model region detection ke server
function setRegionDetectionModel(modelId, modelName) {
    fetch('/set_region_detection_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ region_detection_model_id: modelId, region_detection_model_name: modelName })
    }).then(response => {
        if (response.ok) {
            console.log('Model Region Detection berhasil diperbarui:', modelName, 'ID:', modelId);
        } else {
            alert('Gagal memperbarui model Region Detection.');
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

function clearHasilDeteksiLocalStorage() {
    localStorage.removeItem('lastPageHasilDeteksi');
    localStorage.removeItem('hasRedirectedHasilDeteksi');
}

function clearHasilAsliLocalStorage() {
    localStorage.removeItem('lastPageHasilAsli');
    localStorage.removeItem('hasRedirectedHasilAsli');
}

// Fungsi untuk submit form hapus data deteksi
function submitHapusDataDeteksiForm() {
    clearHasilDeteksiLocalStorage(); // Hapus localStorage hasil deteksi

    // Tampilkan modal loading
    var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        backdrop: 'static',
        keyboard: false
    });
    loadingModal.show();

    // Tutup modal konfirmasi
    var hapusDataDeteksiModal = bootstrap.Modal.getInstance(document.getElementById('hapusDataDeteksiModal'));
    hapusDataDeteksiModal.hide();

    // Mengirim permintaan AJAX untuk memulai save results
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/hapus_data_deteksi', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Mengganti state riwayat untuk mencegah tombol back
            history.replaceState(null, null, window.location.href);
            allowForward = true;
            isProcessing = false;
            window.location.replace('/hasil_asli');
        } else if (xhr.readyState === 4) {
            alert('Terjadi kesalahan saat menghapus data.');
            loadingModal.hide(); // Tutup modal loading jika terjadi kesalahan
        }
    };

    isProcessing = true;
    xhr.send();
}

// reset data
function submitResetGenerateDataForm() {
    clearHasilDeteksiLocalStorage(); // Hapus localStorage hasil deteksi
    clearHasilAsliLocalStorage();    // Hapus localStorage hasil asli

    // Tampilkan modal loading
    var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        backdrop: 'static',
        keyboard: false
    });
    loadingModal.show();

    // Tutup modal konfirmasi
    var resetDataModal = bootstrap.Modal.getInstance(document.getElementById('resetGenerateDataModal'));
    resetDataModal.hide();

    // Mengirim permintaan AJAX untuk memulai reset data
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/reset_data', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Mengganti state riwayat untuk mencegah tombol back
            history.replaceState(null, null, window.location.href);
            allowForward = true;
            isProcessing = false;
            window.location.replace('/');
        } else if (xhr.readyState === 4) {
            alert('Terjadi kesalahan saat menghapus data.');
            loadingModal.hide(); // Tutup modal loading jika terjadi kesalahan
        }
    };

    isProcessing = true;
    xhr.send();
}
