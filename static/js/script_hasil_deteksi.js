document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.querySelector('table tbody');
    const tableRows = document.querySelectorAll('table tbody tr');
    const noDataFound = !tableBody || tableRows.length === 0;

    const currentUrl = window.location.pathname;
    const currentPage = new URLSearchParams(window.location.search).get('page') || "1";

    const lastPage = localStorage.getItem('lastPageHasilDeteksi');
    const hasRedirected = localStorage.getItem('hasRedirectedHasilDeteksi');

    // 1. Jika tidak ada data dan bukan halaman default: kembali ke halaman default
    if (noDataFound && currentUrl === '/hasil_deteksi' && currentPage !== "1") {
        localStorage.removeItem('lastPageHasilDeteksi');
        window.location.href = '/hasil_deteksi';
        return;
    }

    // 2. Jika tidak ada data dan sudah di halaman default: jangan apa-apa
    if (noDataFound && currentUrl === '/hasil_deteksi') {
        return;
    }

    // 3. Jika ada data tapi belum di halaman terakhir, redirect
    if (lastPage && !hasRedirected && parseInt(currentPage) !== parseInt(lastPage)) {
        localStorage.setItem('hasRedirectedHasilDeteksi', 'true');
        const url = new URL(window.location.href);
        url.searchParams.set('page', lastPage);
        window.location.href = url.toString();
        return;
    } else {
        // Reset flag redirect jika sudah di halaman benar
        localStorage.removeItem('hasRedirectedHasilDeteksi');
    }

    // 4. Tangani form input manual pada pagination
    document.querySelectorAll('.page-item form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault(); // Mencegah reload halaman default
            const page = form.querySelector('input[name="page"]')?.value;
            if (page) {
                localStorage.setItem('lastPageHasilDeteksi', page);
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
                localStorage.setItem('lastPageHasilDeteksi', page);
            }
        });
    });
});

// submit save results
function submitSaveResultsForm() {
    // Tampilkan modal loading
    var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        backdrop: 'static',
        keyboard: false
    });
    loadingModal.show();

    // Tutup modal konfirmasi
    var resultsSaveModal = bootstrap.Modal.getInstance(document.getElementById('resultsSaveModal'));
    resultsSaveModal.hide();

    // Ambil nilai dari input teks
    var resultTitle = document.getElementById('resultTitle').value;

    // Validasi input (opsional)
    if (!resultTitle) {
        alert('Judul tidak boleh kosong!');
        loadingModal.hide(); // Tutup modal loading jika validasi gagal
        return;
    }

    // Mengirim permintaan AJAX untuk memulai save results
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/save_results', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Mengganti state riwayat untuk mencegah tombol back
            history.replaceState(null, null, window.location.href);
            allowForward = true;
            isProcessing = false;
            window.location.replace('/hasil_deteksi');
        } else if (xhr.readyState === 4) {
            alert('Terjadi kesalahan saat menyimpan data.');
            loadingModal.hide(); // Tutup modal loading jika terjadi kesalahan
        }
    };

    // Kirim data judul ke backend
    isProcessing = true;
    xhr.send('resultTitle=' + encodeURIComponent(resultTitle));
}