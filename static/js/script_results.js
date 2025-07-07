document.addEventListener('click', function (e) {
    // Tangani tombol "Tampilkan"
    if (e.target.matches('.btn-toggle-result-selected')) {
        const id = e.target.dataset.id;

        // Hapus localStorage terkait simulasi dan deteksi
        localStorage.removeItem('lastPageResultsSimulasi');
        localStorage.removeItem('lastPageResultsDeteksi');
        localStorage.removeItem('scrollResultsEvaluasiY');

        // Tampilkan modal loading
        const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        loadingModal.show();

        // Kirim permintaan ke server untuk mengubah status selected
        fetch(`/results/toggle_selected/${id}`, { method: 'POST' })
            .then(response => response.json())
            .then(res => {
                if (res.status === 'success') {
                    location.reload(); // Reload halaman jika berhasil
                } else {
                    alert('Gagal mengubah status. Silakan coba lagi.');
                    loadingModal.hide(); // Sembunyikan modal loading jika gagal
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Terjadi kesalahan. Silakan coba lagi.');
                loadingModal.hide();
            });
        isProcessing = true;
        xhr.send()
    }
});

//Delete Model
document.addEventListener("DOMContentLoaded", () => {
    const deleteResultsModal = document.getElementById("deleteResultsModal");
    const deleteModalBody = document.getElementById("deleteModalBody");
    const confirmDeleteButton = document.getElementById("confirmDeleteButton");
    const passwordInput = document.getElementById("deletePasswordConfirm");

    let selectedResultsId = null; // Untuk menyimpan ID Results yang dipilih

    // Event listener untuk tombol "Hapus"
    document.querySelectorAll("button[data-bs-target='#deleteResultsModal']").forEach(button => {
        button.addEventListener("click", () => {
            const resultsId = button.getAttribute("data-results-id");
            const resultsName = button.getAttribute("data-results-name");

            // Simpan ID results yang dipilih
            selectedResultsId = resultsId;

            // Perbarui teks di modal
            deleteModalBody.textContent = `Apakah Anda yakin ingin menghapus results "${resultsName}" ini? Semua data terkait akan dihapus secara permanen.`;

            // Reset password input dan hapus pesan error
            passwordInput.value = "";
            passwordInput.classList.remove("is-invalid");
        });
    });

    // Event listener untuk tombol "Hapus" di modal
    confirmDeleteButton.addEventListener("click", () => {
        if (selectedResultsId) {
            // Periksa password
            if (passwordInput.value === "1234") {
                // Password benar, lanjutkan dengan penghapusan

                // Tampilkan modal loading
                const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"), {
                    backdrop: "static",
                    keyboard: false
                });
                loadingModal.show();

                // Tutup modal konfirmasi
                const deleteResultsModalInstance = bootstrap.Modal.getInstance(deleteResultsModal);
                deleteResultsModalInstance.hide();

                // Kirim permintaan POST untuk menghapus results
                fetch(`/results/delete/${selectedResultsId}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: `result_id=${selectedResultsId}`,
                })
                    .then(response => {
                        if (response.ok) {
                            // Reload halaman setelah berhasil menghapus
                            // Hapus localStorage terkait simulasi dan deteksi
                            localStorage.removeItem('lastPageResultsSimulasi');
                            localStorage.removeItem('lastPageResultsDeteksi');
                            localStorage.removeItem('scrollResultsEvaluasiY');

                            window.location.reload();
                        } else {
                            throw new Error("Gagal menghapus results.");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        alert("Terjadi kesalahan saat menghapus results.");
                        // Sembunyikan modal loading jika terjadi error
                        loadingModal.hide();
                    });
            } else {
                // Password salah, tampilkan pesan error
                passwordInput.classList.add("is-invalid");
            }
        }
    });
});