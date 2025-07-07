// ========== URGENSI ==========

document.addEventListener('submit', function (e) {
    if (e.target.matches('#formAddUrgensi')) {
        e.preventDefault();

        const form = e.target;

        // Tutup modal konfirmasi
        var addUrgensiModal = bootstrap.Modal.getInstance(document.getElementById('addUrgensiModal'));
        if (addUrgensiModal) {
            addUrgensiModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch('/urgensi/add', {
            method: 'POST',
            body: new FormData(form)
        })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal menambahkan urgensi. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formEditUrgensi')) {
        e.preventDefault();

        const form = e.target;
        const id = form.dataset.id;
        const modalId = `editUrgensiModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var editUrgensiModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (editUrgensiModal) {
            editUrgensiModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/urgensi/edit/${id}`, {
            method: 'POST',
            body: new FormData(form)
        })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal mengedit urgensi. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('click', function (e) {
    if (e.target.matches('.btn-toggle-urgensi')) {

        const id = e.target.dataset.id;
        const modalId = `editUrgensiModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var editUrgensiModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (editUrgensiModal) {
            editUrgensiModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/urgensi/toggle_active/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal mengubah status urgensi. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formDeleteUrgensi')) {
        e.preventDefault();

        const id = e.target.dataset.id;
        const modalId = `deleteUrgensiModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var deleteUrgensiModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (deleteUrgensiModal) {
            deleteUrgensiModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/urgensi/delete/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal menghapus urgensi. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});