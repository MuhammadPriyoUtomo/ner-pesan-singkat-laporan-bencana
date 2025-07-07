// ========== BENCANA ==========

document.addEventListener('submit', function (e) {
    if (e.target.matches('#formAddBencana')) {
        e.preventDefault();

        const form = e.target;

        // Tutup modal konfirmasi
        var addBencanaModal = bootstrap.Modal.getInstance(document.getElementById('addBencanaModal'));
        if (addBencanaModal) {
            addBencanaModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch('/bencana/add', {
            method: 'POST',
            body: new FormData(form)
        })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal menambahkan bencana. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formEditBencana')) {
        e.preventDefault();

        // Ambil ID modal dari elemen form
        const form = e.target;
        const id = form.dataset.id;
        const modalId = `editBencanaModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var editBencanaModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (editBencanaModal) {
            editBencanaModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/bencana/edit/${id}`, {
            method: 'POST',
            body: new FormData(form)
        })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal mengedit bencana. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('click', function (e) {
    if (e.target.matches('.btn-toggle-bencana')) {

        const id = e.target.dataset.id;
        const modalId = `toggleBencanaModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var toggleBencanaModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (toggleBencanaModal) {
            toggleBencanaModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/bencana/toggle_active/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal mengubah status bencana. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formDeleteBencana')) {
        e.preventDefault();

        const id = e.target.dataset.id;
        const modalId = `deleteBencanaModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var deleteBencanaModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (deleteBencanaModal) {
            deleteBencanaModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/bencana/delete/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal menghapus bencana. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});