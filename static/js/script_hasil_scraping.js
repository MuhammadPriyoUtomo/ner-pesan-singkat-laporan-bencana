document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.querySelector('table tbody');
    const tableRows = document.querySelectorAll('table tbody tr');
    const noDataFound = !tableBody || tableRows.length === 0;

    const currentUrl = window.location.pathname;
    const currentPage = new URLSearchParams(window.location.search).get('page') || "1";

    const lastPage = localStorage.getItem('lastPageHasilScraping');
    const hasRedirected = localStorage.getItem('hasRedirectedHasilScraping');

    // 1. Jika tidak ada data dan bukan halaman default: kembali ke halaman default
    if (noDataFound && currentUrl === '/hasil_scraping' && currentPage !== "1") {
        localStorage.removeItem('lastPageHasilScraping');
        window.location.href = '/hasil_scraping';
        return;
    }

    // 2. Jika tidak ada data dan sudah di halaman default: jangan apa-apa
    if (noDataFound && currentUrl === '/hasil_scraping') {
        return;
    }

    // 3. Jika ada data tapi belum di halaman terakhir, redirect
    if (lastPage && !hasRedirected && parseInt(currentPage) !== parseInt(lastPage)) {
        localStorage.setItem('hasRedirectedHasilScraping', 'true');
        const url = new URL(window.location.href);
        url.searchParams.set('page', lastPage);
        window.location.href = url.toString();
        return;
    } else {
        // Reset flag redirect jika sudah di halaman benar
        localStorage.removeItem('hasRedirectedHasilScraping');
    }

    // 4. Tangani form input manual pada pagination
    document.querySelectorAll('.page-item form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault(); // Mencegah reload halaman default
            const page = form.querySelector('input[name="page"]')?.value;
            if (page) {
                localStorage.setItem('lastPageHasilScraping', page);
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
                localStorage.setItem('lastPageHasilScraping', page);
            }
        });
    });
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formDeleteResult')) {
        e.preventDefault();
        const id = e.target.dataset.id;

        fetch(e.target.action, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {

                    // Tutup modal secara manual
                    const modal = document.querySelector(`#deleteResultModal${id}`);
                    if (modal) {
                        const bootstrapModal = bootstrap.Modal.getInstance(modal);
                        bootstrapModal.hide(); // Tutup modal
                    }

                    window.location.reload();
                } else {
                    alert('Gagal menghapus data.');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Terjadi kesalahan saat menghapus data.');
            });
    }
});