// Set mode default ke "Generate Data" saat halaman dimuat
document.addEventListener('DOMContentLoaded', function () {
    toggleManualMode('generate');
});

function clearHasilLocalStorage() {
    localStorage.removeItem('lastPageHasilAsli');
    localStorage.removeItem('hasRedirectedHasilAsli');
    localStorage.removeItem('lastPageHasilDeteksi');
    localStorage.removeItem('hasRedirectedHasilDeteksi');
}

function toggleManualMode(mode) {
    const generateDataForm = document.getElementById('generateDataForm');
    const inputDataForm = document.getElementById('inputDataForm');
    const generateDataBtn = document.getElementById('generateDataBtn');
    const inputDataBtn = document.getElementById('inputDataBtn');

    if (mode === 'generate') {
        // Tampilkan form Generate Data dan sembunyikan form Text Input
        generateDataForm.style.display = 'block';
        inputDataForm.style.display = 'none';

        // Ubah tombol Generate Data menjadi btn-success
        generateDataBtn.classList.remove('btn-outline-primary');
        generateDataBtn.classList.add('btn-primary');

        // Ubah tombol Text Input menjadi btn-outline-secondary
        inputDataBtn.classList.remove('btn-secondary');
        inputDataBtn.classList.add('btn-outline-secondary');

    } else if (mode === 'input') {
        // Tampilkan form Text Input dan sembunyikan form Generate Data
        generateDataForm.style.display = 'none';
        inputDataForm.style.display = 'block';

        // Ubah tombol Text Input menjadi btn-secondary
        inputDataBtn.classList.remove('btn-outline-secondary');
        inputDataBtn.classList.add('btn-secondary');

        // Ubah tombol Generate Data menjadi btn-outline-primary
        generateDataBtn.classList.remove('btn-primary');
        generateDataBtn.classList.add('btn-outline-primary');
    }
}

function validateGenerateDataForm() {
    const modelDropdown = document.getElementById('model_id');
    const numEntriesInput = document.getElementById('num_entries');
    const numStatusReportsInput = document.getElementById('num_status_reports'); // Tambahan
    const numNonReportsInput = document.getElementById('num_non_reports'); // Tambahan
    const warning = document.getElementById('generateDataWarning');

    const numEntries = parseInt(numEntriesInput.value, 10);
    const numStatusReports = parseInt(numStatusReportsInput.value, 10);
    const numNonReports = parseInt(numNonReportsInput.value, 10);

    // Validasi jumlah total
    if (numStatusReports + numNonReports !== numEntries) {
        warning.textContent = 'Jumlah Status Report dan Bukan Report harus sama dengan Jumlah Data.';
        warning.style.display = 'block';
        return false;
    }

    // Validasi jumlah tidak boleh negatif atau nol
    if (numEntries <= 0 || numStatusReports < 0 || numNonReports < 0) {
        warning.textContent = 'Jumlah data tidak valid. Pastikan semua nilai lebih dari 0.';
        warning.style.display = 'block';
        return false;
    }

    if (!modelDropdown.value) {
        alert('Pilih model terlebih dahulu.');
        return false;
    }

    if (!numEntriesInput.value || numEntriesInput.value <= 0) {
        warning.style.display = 'block';
        return false;
    }

    if (!numStatusReportsInput.value || numStatusReportsInput.value <= 0) { // Validasi tambahan
        alert('Jumlah Status Report harus diisi dan lebih dari 0.');
        return false;
    }

    if (!numNonReportsInput.value || numNonReportsInput.value <= 0) { // Validasi tambahan
        alert('Jumlah Bukan Report harus diisi dan lebih dari 0.');
        return false;
    }

    warning.style.display = 'none';
    return true;
}

function submitGenerateDataForm() {
    if (validateGenerateDataForm()) {
        document.getElementById('generate-data-form').submit();
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const modelDropdownItems = document.querySelectorAll('#modelDropdown + .dropdown-menu .dropdown-item');
    const modelInput = document.getElementById('model_id');
    const modelDropdownButton = document.getElementById('modelDropdown');

    modelDropdownItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const modelName = this.textContent;
            const modelId = this.getAttribute('data-value');

            modelDropdownButton.textContent = modelName;
            modelInput.value = modelId;
        });
    });
});

function submitGenerateDataForm() {
    if (validateGenerateDataForm()) {
        clearHasilLocalStorage(); // Hapus localStorage sebelum submit

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        // Tutup modal konfirmasi
        var generateDataModal = bootstrap.Modal.getInstance(document.getElementById('generateDataModal'));
        generateDataModal.hide();

        // Nonaktifkan tombol untuk mencegah pengiriman berulang
        var submitButton = document.querySelector('#generate-data-form button[type="button"]');
        submitButton.disabled = true;

        // Mengirim permintaan AJAX untuk memulai generate data
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/generate_data', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                console.log('Status:', xhr.status);
                console.log('Response:', xhr.responseText);

                if (xhr.status === 200) {
                    // Mengganti state riwayat untuk mencegah tombol back
                    history.replaceState(null, null, window.location.href);
                    allowForward = true;
                    isProcessing = false;
                    window.location.replace('/hasil_asli');
                } else {
                    // Tampilkan pesan error jika server mengembalikan status selain 200
                    alert('Terjadi kesalahan saat memproses data. Silakan coba lagi.');
                    isProcessing = false;
                    submitButton.disabled = false; // Aktifkan kembali tombol jika terjadi error
                }
            }
        };
        isProcessing = true;
        xhr.send(new URLSearchParams(new FormData(document.getElementById('generate-data-form'))).toString());
    }
}

// mencegah inputan data kosong
function validateInputDataForm() {
    var isiChatPengaduan = document.getElementById('isi_chat_pengaduan').value.trim();
    var warning = document.getElementById('inputDataWarning');
    if (isiChatPengaduan === '') {
        warning.style.display = 'block';
        return false;
    }
    warning.style.display = 'none';
    return true;
}

// Mencegah enter di input text
document.getElementById('isi_chat_pengaduan').addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        event.preventDefault();
    }
});

// input data
function submitInputDataForm() {
    if (validateInputDataForm()) {
        clearHasilLocalStorage(); // Hapus localStorage sebelum submit

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        // Tutup modal konfirmasi
        var inputDataModal = bootstrap.Modal.getInstance(document.getElementById('inputDataModal'));
        inputDataModal.hide();

        // Mengirim permintaan AJAX untuk memulai input data
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/input_data', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                // Mengganti state riwayat untuk mencegah tombol back
                history.replaceState(null, null, window.location.href);
                allowForward = true;
                isProcessing = false;
                window.location.replace('/hasil_asli');
            }
        };
        isProcessing = true;
        xhr.send(new URLSearchParams(new FormData(document.getElementById('input-data-form'))).toString());
    }
}