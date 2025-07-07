function setMode(mode) {
    const button = document.querySelector('button');
    if (button.disabled) return;

    // Mapping mode ke judul dan pesan
    const modeMap = {
        'model': {
            title: 'Konfirmasi Peralihan ke Mode Model',
            body: 'Anda akan beralih ke mode <span class="text-purple fw-bold">Model</span>. Lanjutkan?'
        },
        'manual': {
            title: 'Konfirmasi Peralihan ke Manual Input',
            body: 'Anda akan beralih ke mode <span class="text-primary fw-bold">Manual Input</span>. Lanjutkan?'
        },
        'results': {
            title: 'Konfirmasi Peralihan ke Mode Result',
            body: 'Anda akan beralih ke mode <span class="text-info fw-bold">Result</span>. Lanjutkan?'
        },
        'auto': {
            title: 'Konfirmasi Peralihan ke Scraping',
            body: 'Anda akan beralih ke mode <span class="text-warning fw-bold">Scraping</span>. Lanjutkan?'
        }
    };

    // Set isi modal dinamis
    document.getElementById('modeSwitchModalLabel').innerHTML = modeMap[mode].title;
    document.getElementById('modeSwitchModalBody').innerHTML = modeMap[mode].body;

    // Tampilkan modal
    const modeSwitchModal = new bootstrap.Modal(document.getElementById('modeSwitchModal'), {
        backdrop: 'static',
        keyboard: false
    });
    modeSwitchModal.show();

    // Set event listener tombol lanjutkan
    document.getElementById('confirmModeSwitchBtn').onclick = function () {
        switchMode(mode);
        modeSwitchModal.hide();
    };
}

// Fungsi untuk mengirim permintaan POST ke server untuk mengubah mode
function switchMode(mode) {
    // Tampilkan modal loading
    var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        backdrop: 'static',
        keyboard: false
    });
    loadingModal.show();

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/set_input_mode', false); // Synchronous request
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({ mode: mode }));

    if (xhr.status === 200) {
        // Jika berhasil, reload halaman
        location.reload();
    } else {
        // Jika gagal, tampilkan pesan kesalahan
        alert('Gagal mengatur mode. Silakan coba lagi.');
        loadingModal.hide(); // Tutup modal loading jika gagal
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const input = document.querySelector('.form_input_pagination');

    function resizeInput() {
        const span = document.createElement('span');
        span.style.visibility = 'hidden';
        span.style.position = 'absolute';
        span.style.whiteSpace = 'pre';
        span.style.font = window.getComputedStyle(input).font;
        span.textContent = input.value || '1';
        document.body.appendChild(span);

        input.style.width = span.offsetWidth + 20 + 'px'; // 20px padding ekstra
        span.remove();
    }

    // Resize saat load dan saat user mengetik
    resizeInput();
    input.addEventListener('input', resizeInput);
});