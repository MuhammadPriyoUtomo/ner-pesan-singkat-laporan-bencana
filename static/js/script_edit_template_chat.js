// ========== TEMPLATE CHAT ==========

document.addEventListener('submit', function (e) {
    if (e.target.matches('#formAddTemplate')) {
        e.preventDefault();

        const form = e.target;

        // Tutup modal konfirmasi
        var addTemplateModal = bootstrap.Modal.getInstance(document.getElementById('addTemplateModal'));
        if (addTemplateModal) {
            addTemplateModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch('/template/add', {
            method: 'POST',
            body: new FormData(form)
        })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal menambahkan template. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formEditTemplate')) {
        e.preventDefault();

        // Ambil ID modal dari elemen form
        const form = e.target;
        const id = form.dataset.id; // Ambil ID dari atribut data-id
        const modalId = `editTemplateModal${id}`; // Buat ID modal dinamis

        // Tutup modal konfirmasi
        var editTemplateModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (editTemplateModal) {
            editTemplateModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/template/edit/${id}`, {
            method: 'POST',
            body: new FormData(form)
        })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload(); // Reload halaman setelah berhasil
                } else {
                    alert('Terjadi kesalahan saat memperbarui template.');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Terjadi kesalahan saat memperbarui template.');
            })
            .finally(() => {
                loadingModal.hide(); // Tutup modal loading setelah selesai
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('click', function (e) {
    if (e.target.matches('.btn-toggle-template')) {
        e.preventDefault();

        const id = e.target.dataset.id;

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/template/toggle_active/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload();
                } else {
                    alert('Gagal mengubah status template. Silakan coba lagi.');
                }
            });
        isProcessing = true;
        xhr.send()
    }
});

document.addEventListener('submit', function (e) {
    if (e.target.matches('.formDeleteTemplate')) {
        e.preventDefault();

        const id = e.target.dataset.id;
        const modalId = `deleteTemplateModal${id}`; // Buat ID modal dinamis
        // Tutup modal konfirmasi
        var deleteTemplateModal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (deleteTemplateModal) {
            deleteTemplateModal.hide();
        }

        // Tampilkan modal loading
        var loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        fetch(`/template/delete/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success') {
                    window.location.reload();
                } else {
                    alert('Gagal menghapus template. Silakan coba lagi.');
                }
            });
        isProcessing = true;
        xhr.send()
    }
});