
const accordionItems = document.querySelectorAll('.accordion .card');

accordionItems.forEach(card => {
    const collapseEl = card.querySelector('.collapse');
    const icon = card.querySelector('.rotate-icon');

    collapseEl.addEventListener('show.bs.collapse', () => {
        icon.classList.add('rotate-180');
    });

    collapseEl.addEventListener('hide.bs.collapse', () => {
        icon.classList.remove('rotate-180');
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.querySelector('table tbody');
    const tableRows = document.querySelectorAll('table tbody tr');
    const noDataFound = !tableBody || tableRows.length === 0;

    const currentUrl = window.location.pathname;
    const currentPage = new URLSearchParams(window.location.search).get('page') || "1";

    const lastPage = localStorage.getItem('lastPageTrainDataModel');
    const hasRedirected = localStorage.getItem('hasRedirectedTrainDataModel');

    // 1. Jika tidak ada data dan bukan halaman default: kembali ke halaman default
    if (noDataFound && currentUrl === '/training' && currentPage !== "1") {
        localStorage.removeItem('lastPageTrainDataModel');
        window.location.href = '/training';
        return;
    }

    // 2. Jika tidak ada data dan sudah di halaman default: jangan apa-apa
    if (noDataFound && currentUrl === '/training') {
        return;
    }

    // 3. Jika ada data tapi belum di halaman terakhir, redirect
    if (lastPage && !hasRedirected && parseInt(currentPage) !== parseInt(lastPage)) {
        localStorage.setItem('hasRedirectedTrainDataModel', 'true');
        const url = new URL(window.location.href);
        url.searchParams.set('page', lastPage);
        window.location.href = url.toString();
        return;
    } else {
        // Reset flag redirect jika sudah di halaman benar
        localStorage.removeItem('hasRedirectedTrainDataModel');
    }

    // 5. Tangani form input manual pada pagination
    document.querySelectorAll('.page-item form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault(); // Mencegah reload halaman default
            const page = form.querySelector('input[name="page"]')?.value;
            if (page) {
                localStorage.setItem('lastPageTrainDataModel', page);
                const url = new URL(window.location.href);
                url.searchParams.set('page', page);
                window.location.href = url.toString();
            }
        });
    });

    // 6. Simpan halaman saat klik pagination
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function () {
            const page = this.dataset.page || new URL(this.href).searchParams.get('page');
            if (page) {
                localStorage.setItem('lastPageTrainDataModel', page);
            }
        });
    });
});

//Delete Model
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("button[data-bs-target^='#deleteModelModal_']").forEach(button => {
        button.addEventListener("click", () => {
            const modelId = button.getAttribute("data-model-id");
            const modelName = button.getAttribute("data-model-name");
            const modalId = `deleteModelModal_${modelId}`;
            const modal = document.getElementById(modalId);

            // Perbarui teks di modal
            modal.querySelector(".deleteModalBody").textContent =
                `Apakah Anda yakin ingin menghapus model "${modelName}" ini? Semua data terkait akan dihapus secara permanen.`;

            // Reset password input dan hapus pesan error
            const passwordInput = modal.querySelector(".deletePasswordConfirm");
            passwordInput.value = "";
            passwordInput.classList.remove("is-invalid");

            // Tombol konfirmasi hapus
            const confirmDeleteButton = modal.querySelector(".confirmDeleteButton");
            confirmDeleteButton.onclick = function () {
                if (passwordInput.value === "1234") {
                    // Tampilkan modal loading
                    const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"), {
                        backdrop: "static",
                        keyboard: false
                    });
                    loadingModal.show();

                    // Tutup modal konfirmasi
                    const deleteModelModalInstance = bootstrap.Modal.getInstance(modal);
                    deleteModelModalInstance.hide();

                    // Kirim permintaan POST untuk menghapus model
                    fetch("/delete_model", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body: `model_id=${modelId}`,
                    })
                        .then(response => {
                            if (response.ok) {
                                window.location.reload();
                            } else {
                                throw new Error("Gagal menghapus model.");
                            }
                        })
                        .catch(error => {
                            console.error("Error:", error);
                            alert("Terjadi kesalahan saat menghapus model.");
                            loadingModal.hide();
                        });
                } else {
                    passwordInput.classList.add("is-invalid");
                }
            };
        });
    });
});

// Delete Bert Model
document.addEventListener("DOMContentLoaded", () => {
    const deleteModelModal = document.getElementById("deleteBertModelModal");
    const deleteModalBody = document.getElementById("deleteBertModalBody");
    const confirmDeleteButton = document.getElementById("confirmBertDeleteButton");
    const passwordInput = document.getElementById("deleteBertPasswordConfirm");

    let selectedModelId = null; // Untuk menyimpan ID model yang dipilih

    // Event listener untuk tombol "Hapus"
    document.querySelectorAll("button[data-bs-target='#deleteBertModelModal']").forEach(button => {
        button.addEventListener("click", () => {
            const modelId = button.getAttribute("data-model-id");
            const modelName = button.getAttribute("data-model-name");

            // Simpan ID model yang dipilih
            selectedModelId = modelId;

            // Perbarui teks di modal
            deleteModalBody.textContent = `Apakah Anda yakin ingin menghapus model Bert dari model "${modelName}" ini? Semua data terkait akan dihapus secara permanen.`;

            // Reset password input dan hapus pesan error
            passwordInput.value = "";
            passwordInput.classList.remove("is-invalid");
        });
    });

    // Event listener untuk tombol "Hapus" di modal
    confirmDeleteButton.addEventListener("click", () => {
        if (selectedModelId) {
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
                const deleteModelModalInstance = bootstrap.Modal.getInstance(deleteModelModal);
                deleteModelModalInstance.hide();

                // Kirim permintaan POST untuk menghapus model
                fetch("/delete_bert_model", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: `model_id=${selectedModelId}`,
                })
                    .then(response => {
                        if (response.ok) {
                            // Reload halaman setelah berhasil menghapus
                            window.location.reload();
                        } else {
                            throw new Error("Gagal menghapus model.");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        alert("Terjadi kesalahan saat menghapus model.");
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

// Delete Spacy Model
document.addEventListener("DOMContentLoaded", () => {
    const deleteModelModal = document.getElementById("deleteSpacyModelModal");
    const deleteModalBody = document.getElementById("deleteSpacyModalBody");
    const confirmDeleteButton = document.getElementById("confirmSpacyDeleteButton");
    const passwordInput = document.getElementById("deleteSpacyPasswordConfirm");

    let selectedModelId = null; // Untuk menyimpan ID model yang dipilih

    // Event listener untuk tombol "Hapus"
    document.querySelectorAll("button[data-bs-target='#deleteSpacyModelModal']").forEach(button => {
        button.addEventListener("click", () => {
            const modelId = button.getAttribute("data-model-id");
            const modelName = button.getAttribute("data-model-name");

            // Simpan ID model yang dipilih
            selectedModelId = modelId;

            // Perbarui teks di modal
            deleteModalBody.textContent = `Apakah Anda yakin ingin menghapus model Spacy dari model "${modelName}" ini? Semua data terkait akan dihapus secara permanen.`;

            // Reset password input dan hapus pesan error
            passwordInput.value = "";
            passwordInput.classList.remove("is-invalid");
        });
    });

    // Event listener untuk tombol "Hapus" di modal
    confirmDeleteButton.addEventListener("click", () => {
        if (selectedModelId) {
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
                const deleteModelModalInstance = bootstrap.Modal.getInstance(deleteModelModal);
                deleteModelModalInstance.hide();

                // Kirim permintaan POST untuk menghapus model
                fetch("/delete_spacy_model", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: `model_id=${selectedModelId}`,
                })
                    .then(response => {
                        if (response.ok) {
                            // Reload halaman setelah berhasil menghapus
                            window.location.reload();
                        } else {
                            throw new Error("Gagal menghapus model.");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        alert("Terjadi kesalahan saat menghapus model.");
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