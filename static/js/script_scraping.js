const detectionResultsContainer = document.getElementById('detection-results');
const scrapingDetectionToggleButton = document.getElementById('toggle-scraping-detection');
let isScrapingDetectionRunning = false;

// Ambil state dari localStorage saat halaman dimuat
document.addEventListener('DOMContentLoaded', function () {
    const storedScrapingState = localStorage.getItem('isScrapingDetectionRunning');
    if (storedScrapingState !== null) {
        isScrapingDetectionRunning = JSON.parse(storedScrapingState);
        updateFooterButtons();
        updateScrapingDetectionButton();
        updateDetectionAndRegionButtons();
    }
});

function showAlert(message, type) {
    const detectionAlert = document.getElementById('detection-alert');
    detectionAlert.textContent = message;
    detectionAlert.classList.remove('d-none', 'alert-info', 'alert-success', 'alert-danger');
    detectionAlert.classList.add(`alert-${type}`);
}

// SSE: Terima data live dari backend
if (!!window.EventSource) {
    const source = new EventSource('/live_stream');
    source.onmessage = function (event) {
        const results = JSON.parse(event.data);
        // Simpan ke localStorage
        localStorage.setItem('detectionResults', JSON.stringify(results));
        renderDetectionResults(results);
    };
}

let lastResultIds = [];

function renderDetectionResults(results) {
    detectionResultsContainer.innerHTML = '';
    const currentIds = results.map(r => r.id);
    results.forEach(result => {
        let disasterData = {};
        let locationData = {};
        try {
            const parsedData = typeof result.hasil_ekstraksi === 'string'
                ? JSON.parse(result.hasil_ekstraksi)
                : result.hasil_ekstraksi;
            disasterData = parsedData.disaster || {};
            locationData = parsedData.location || {};
        } catch (parseError) {
            disasterData = {};
            locationData = {};
        }
        const resultRow = document.createElement('tr');
        // Tambahkan animasi jika id belum ada di lastResultIds (data baru)
        if (!lastResultIds.includes(result.id)) {
            resultRow.classList.add('tr-fade-in');
        }
        resultRow.innerHTML = `
            <td>${result.id}</td>
            <td>${result.nomor_pengirim}</td>
            <td>${result.tanggal}</td>
            <td>${result.chat}</td>
            <td>
                <div class="d-flex flex-column gap-2">
                    <div class="border rounded p-2 bg-white shadow-sm">
                        <strong class="text-primary mb-1 d-block">Hasil Ekstraksi</strong>
                        <div class="mb-1" style="padding-bottom: 10px;">
                            <i class="bi bi-caret-right-fill">
                                <strong class="text-dark">Disaster:</strong>
                                ${disasterData.text ?
                `<span class="badge-label" style="font-size: 1rem; background-color: #b86cff;">
                    ${disasterData.text}
                </span>
                <small class="text-muted">(${disasterData.source || 'N/A'})</small>`
                :
                `<span class="text-muted">Tidak ditemukan</span>`
            }
                            </i>
                        </div>
                        <div class="mb-1" style="padding-bottom: 10px;">
                            <i class="bi bi-caret-right-fill">
                                <strong class="text-dark">Location:</strong>
                                ${locationData.text ?
                `<span class="badge-label" style="font-size: 1rem; background-color: #17a2b8;">
                    ${locationData.text}
                </span>
                <small class="text-muted">(${locationData.source || 'N/A'})</small>
                <a href="https://www.google.com/maps/search/${encodeURIComponent(locationData.text)}"
                target="_blank" title="Cari di Google Maps"
                style="margin-left: 8px; color: #0d6efd;">
                <i class="bi bi-search"></i> Cari
                </a>`
                :
                `<span class="text-muted">Tidak ditemukan</span>`
            }
                            </i>
                        </div>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge ${result.report_status === 'report' ? 'bg-success' : 'bg-secondary'}" style="font-size: 1rem; padding:10px;">
                    ${result.report_status === 'report' ? 'Report' : 'Bukan Report'}
                </span>
            </td>
            <td>${result.timestamp}</td>
        `;
        detectionResultsContainer.appendChild(resultRow);
    });
    // Simpan id terakhir untuk deteksi data baru berikutnya
    lastResultIds = currentIds;
}

// Saat halaman dimuat, render dari localStorage (jika ada)
document.addEventListener('DOMContentLoaded', function () {
    const storedResults = JSON.parse(localStorage.getItem('detectionResults')) || [];
    renderDetectionResults(storedResults);
});

// Toggle tombol scraping
document.addEventListener('DOMContentLoaded', function () {
    const scrapingDetectionToggleButton = document.getElementById('toggle-scraping-detection');
    if (scrapingDetectionToggleButton) {
        scrapingDetectionToggleButton.addEventListener('click', () => {
            if (isScrapingDetectionRunning) {
                stopScrapingAndDetection();
            } else {
                startScrapingAndDetection();
            }
        });
    }
});

async function startScrapingAndDetection() {
    const startModalEl = document.getElementById('startScrapingModal');
    const startModal = bootstrap.Modal.getOrCreateInstance(startModalEl);
    startModal.show();
    try {
        const response = await fetch('/start_scraping', { method: 'POST' });
        if (response.ok) {
            showAlert('Scraping and Detection started. Waiting for detection results...', 'info');
            isScrapingDetectionRunning = true;
            localStorage.setItem('isScrapingDetectionRunning', JSON.stringify(isScrapingDetectionRunning));
            updateScrapingDetectionButton();
            updateDetectionAndRegionButtons();
            updateFooterButtons();
        } else {
            showAlert('Failed to start scraping and detection.', 'danger');
        }
    } catch (error) {
        showAlert('Error starting scraping and detection.', 'danger');
    }
    setTimeout(() => {
        startModal.hide();
        updateFooterButtons();
    }, 5000);
}

async function stopScrapingAndDetection() {
    const stopModalEl = document.getElementById('stopScrapingModal');
    const stopModal = bootstrap.Modal.getOrCreateInstance(stopModalEl);
    stopModal.show();
    try {
        const response = await fetch('/stop_scraping', { method: 'POST' });
        if (response.ok) {
            showAlert('Scraping and Detection stopped.', 'danger');
            isScrapingDetectionRunning = false;
            localStorage.setItem('isScrapingDetectionRunning', JSON.stringify(isScrapingDetectionRunning));
            updateScrapingDetectionButton();
            updateDetectionAndRegionButtons();
            updateFooterButtons();
        } else {
            showAlert('Failed to stop scraping and detection.', 'danger');
        }
    } catch (error) {
        showAlert('Error stopping scraping and detection.', 'danger');
    }
    setTimeout(() => {
        stopModal.hide();
        updateFooterButtons();
    }, 5000);
}

function updateScrapingDetectionButton() {
    if (isScrapingDetectionRunning) {
        scrapingDetectionToggleButton.textContent = 'Stop Scraping & Detection';
        scrapingDetectionToggleButton.classList.remove('btn-primary');
        scrapingDetectionToggleButton.classList.add('btn-danger');
        scrapingDetectionToggleButton.disabled = false;
    } else {
        scrapingDetectionToggleButton.textContent = 'Start Scraping & Detection';
        scrapingDetectionToggleButton.classList.remove('btn-danger');
        scrapingDetectionToggleButton.classList.add('btn-primary');
        scrapingDetectionToggleButton.disabled = false;
    }
}

function updateDetectionAndRegionButtons() {
    const detectionModeDropdown = document.getElementById('detectionModeDropdown');
    const modelRegionDetectionDropdown = document.getElementById('modelRegionDetectionDropdown');
    const scrapingButton = document.getElementById('toggle-scraping-detection');
    if (isScrapingDetectionRunning) {
        detectionModeDropdown.disabled = true;
        detectionModeDropdown.style.opacity = '0.5';
        modelRegionDetectionDropdown.disabled = true;
        modelRegionDetectionDropdown.style.opacity = '0.5';
        if (scrapingButton) scrapingButton.disabled = false;
    } else {
        detectionModeDropdown.disabled = false;
        detectionModeDropdown.style.opacity = '1';
        modelRegionDetectionDropdown.disabled = false;
        modelRegionDetectionDropdown.style.opacity = '1';
        const selectedRegion = document.querySelector('#modelRegionDetectionDropdown + .dropdown-menu .dropdown-item[data-selected="true"]');
        if (scrapingButton) scrapingButton.disabled = !selectedRegion;
        if (!selectedRegion && modelRegionDetectionDropdown) {
            modelRegionDetectionDropdown.textContent = 'Pilih Model Region Detection';
        }
    }
}

// Update footer buttons based on scraping state
function updateFooterButtons() {
    const modelBtn = document.getElementById('footer-model-btn');
    const manualBtn = document.getElementById('footer-manual-btn');
    const resultsBtn = document.getElementById('footer-results-btn');
    const scrapingBtn = document.getElementById('footer-scraping-btn');

    if (isScrapingDetectionRunning) {
        if (modelBtn) { modelBtn.disabled = true; modelBtn.style.opacity = "0.5"; }
        if (manualBtn) { manualBtn.disabled = true; manualBtn.style.opacity = "0.5"; }
        if (resultsBtn) { resultsBtn.disabled = true; resultsBtn.style.opacity = "0.5"; }
        if (scrapingBtn) { scrapingBtn.disabled = true; scrapingBtn.style.opacity = "1"; }
    } else {
        if (modelBtn) { modelBtn.disabled = false; modelBtn.style.opacity = "1"; }
        if (manualBtn) { manualBtn.disabled = false; manualBtn.style.opacity = "1"; }
        if (resultsBtn) { resultsBtn.disabled = false; resultsBtn.style.opacity = "1"; }
        if (scrapingBtn) { scrapingBtn.disabled = false; scrapingBtn.style.opacity = "1"; }
    }
    // Tambahkan baris berikut:
    attachFooterModeButtonListeners();
}

function attachFooterModeButtonListeners() {
    const modelBtn = document.getElementById('footer-model-btn');
    const manualBtn = document.getElementById('footer-manual-btn');
    const resultsBtn = document.getElementById('footer-results-btn');
    const scrapingBtn = document.getElementById('footer-scraping-btn');

    if (modelBtn) {
        modelBtn.onclick = function () {
            if (!modelBtn.disabled) setMode('model');
        };
    }
    if (manualBtn) {
        manualBtn.onclick = function () {
            if (!manualBtn.disabled) setMode('manual');
        };
    }
    if (resultsBtn) {
        resultsBtn.onclick = function () {
            if (!resultsBtn.disabled) setMode('results');
        };
    }
    if (scrapingBtn) {
        scrapingBtn.onclick = function () {
            if (!scrapingBtn.disabled) setMode('auto');
        };
    }
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
    const scrapingButton = document.getElementById('toggle-scraping-detection');

    // Hapus atribut data-selected dari semua item dropdown (memaksa user memilih secara manual)
    dropdownItems.forEach(item => {
        item.removeAttribute('data-selected');
    });

    // Selalu set default teks dropdown ke "Pilih Model Region Detection"
    dropdownButton.textContent = 'Pilih Model Region Detection';

    // Selalu nonaktifkan tombol scraping saat halaman dimuat kecuali jika scraping sedang berjalan
    if (scrapingButton) {
        if (!isScrapingDetectionRunning) {
            scrapingButton.disabled = true;  // Nonaktifkan jika scraping tidak berjalan
        }
    }

    // Tambahkan event listener ke item dropdown
    dropdownItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const modelId = this.getAttribute('data-id');
            const modelName = this.getAttribute('data-name');

            // Perbarui tombol dropdown
            dropdownButton.textContent = 'Model Region Detection: ' + modelName;
            modelIdInput.value = modelId;

            // Hapus atribut data-selected dari semua item dan tambahkan ke item yang dipilih
            dropdownItems.forEach(i => i.removeAttribute('data-selected'));
            this.setAttribute('data-selected', 'true');

            // Aktifkan tombol scraping hanya jika scraping tidak sedang berjalan
            if (scrapingButton && !isScrapingDetectionRunning) {
                scrapingButton.disabled = false;
            }

            // Kirim model yang dipilih ke server
            setRegionDetectionModel(modelId, modelName);
        });
    });
});

// Fungsi fetch untuk mengatur model region detection
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