document.addEventListener("DOMContentLoaded", () => {
    const createBertForm = document.getElementById("createBertForm");
    const bert_dropdownItems = document.querySelectorAll(".dropdown-item-bert");
    const bert_hiddenInput = document.getElementById("bert_model");
    const bert_dropdownButton = document.getElementById("bert_modelDropdown");
    const confirmBertSubmitBtn = document.getElementById("confirmBertSubmitBtn");

    let isFormValid = false; // Flag untuk validasi

    bert_dropdownItems.forEach(item => {
        item.addEventListener("click", () => {
            const selectedValue = item.getAttribute("data-value");
            const selectedText = item.textContent;
            bert_hiddenInput.value = selectedValue;
            bert_dropdownButton.textContent = selectedText;
        });
    });

    createBertForm.addEventListener("submit", (e) => {
        e.preventDefault(); // Selalu dicegah dulu

        const modelInput = document.getElementById("bert_model").value;
        const dataUsedInput = parseInt(document.getElementById("bert_data_used").value, 10);

        if (!modelInput) {
            alert("Please select a model.");
            return;
        }
        if (isNaN(dataUsedInput) || dataUsedInput < 10) {
            alert("Number of data used must be at least 10.");
            return;
        }

        // Tampilkan modal konfirmasi
        isFormValid = true;
        const confirmModal = new bootstrap.Modal(document.getElementById("confirmBertModal"));
        confirmModal.show();
    });

    confirmBertSubmitBtn.addEventListener("click", () => {
        if (isFormValid) {
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById("confirmBertModal"));
            confirmModal.hide(); // Tutup modal
            submitBertModelForm();
        }
    });

    function showLoadingModal() {
        const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"), {
            backdrop: "static",
            keyboard: false
        });
        loadingModal.show();
    }

    function submitBertModelForm() {
        showLoadingModal();
        fetch(createBertForm.action, {
            method: "POST",
            body: new FormData(createBertForm),
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    throw new Error('Network response was not ok');
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Error: " + error.message);
            });
    }
});
