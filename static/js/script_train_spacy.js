document.addEventListener("DOMContentLoaded", () => {
    const createSpacyForm = document.getElementById("createSpacyForm");
    const spacy_dropdownItems = document.querySelectorAll(".dropdown-item-spacy");
    const spacy_hiddenInput = document.getElementById("spacy_model");
    const spacy_dropdownButton = document.getElementById("spacy_modelDropdown");
    const confirmSpacySubmitBtn = document.getElementById("confirmSpacySubmitBtn");

    let isFormValid = false; // Flag untuk validasi

    spacy_dropdownItems.forEach(item => {
        item.addEventListener("click", () => {
            const selectedValue = item.getAttribute("data-value");
            const selectedText = item.textContent;
            spacy_hiddenInput.value = selectedValue;
            spacy_dropdownButton.textContent = selectedText;
        });
    });

    createSpacyForm.addEventListener("submit", (e) => {
        e.preventDefault(); // Selalu dicegah dulu

        const modelInput = document.getElementById("spacy_model").value;
        const dataUsedInput = parseInt(document.getElementById("spacy_data_used").value, 10);

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
        const confirmModal = new bootstrap.Modal(document.getElementById("confirmSpacyModal"));
        confirmModal.show();
    });

    confirmSpacySubmitBtn.addEventListener("click", () => {
        if (isFormValid) {
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById("confirmSpacyModal"));
            confirmModal.hide(); // Tutup modal
            submitSpacyModelForm();
        }
    });

    function showLoadingModal() {
        const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"), {
            backdrop: "static",
            keyboard: false
        });
        loadingModal.show();
    }

    function submitSpacyModelForm() {
        showLoadingModal();
        fetch(createSpacyForm.action, {
            method: "POST",
            body: new FormData(createSpacyForm),
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
