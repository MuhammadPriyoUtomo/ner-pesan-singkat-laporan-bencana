document.addEventListener("DOMContentLoaded", function () {
    // Ambil posisi scroll terakhir dari localStorage
    const scrollY = localStorage.getItem('scrollResultsEvaluasiY');
    if (scrollY && document.referrer && !document.referrer.includes(window.location.origin + window.location.pathname)) {
        window.scrollTo({ top: parseInt(scrollY), behavior: 'smooth' });
    }

    // Simpan posisi scroll saat user meninggalkan halaman
    window.addEventListener('beforeunload', function () {
        localStorage.setItem('scrollResultsEvaluasiY', window.scrollY);
    });
});