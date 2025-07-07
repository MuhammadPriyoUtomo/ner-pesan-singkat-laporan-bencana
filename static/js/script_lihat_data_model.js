document.addEventListener('DOMContentLoaded', function () {

    // Jika backend mengirim perintah untuk reset localStorage
    if (document.cookie.includes("clear_local_storage=true")) {
        localStorage.removeItem('lastModelIdLihatDataModel');
        localStorage.removeItem('lastTrainingTypeLihatDataModel');
        localStorage.removeItem('lastPageLihatDataModel');
        document.cookie = "clear_local_storage=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    }

    const tableBody = document.querySelector('table tbody');
    const noDataFound = !tableBody || tableBody.children.length === 0;

    const urlParams = new URLSearchParams(window.location.search);
    const currentPage = urlParams.get('page') || "1";
    const modelId = urlParams.get('model_id');
    const trainingType = urlParams.get('training_type');

    const currentPath = window.location.pathname;

    const lastPage = localStorage.getItem('lastPageLihatDataModel');
    const lastModelId = localStorage.getItem('lastModelIdLihatDataModel');
    const lastTrainingType = localStorage.getItem('lastTrainingTypeLihatDataModel');
    const hasRedirected = localStorage.getItem('hasRedirectedLihatDataModel');

    // Fungsi untuk bangun URL lengkap
    function buildFullUrl(page, modelId, trainingType) {
        const newParams = new URLSearchParams();
        if (modelId) newParams.set('model_id', modelId);
        if (trainingType) newParams.set('training_type', trainingType);
        if (page) newParams.set('page', page);
        return `${currentPath}?${newParams.toString()}`;
    }

    // Simpan data baru ke localStorage
    if (modelId) localStorage.setItem('lastModelIdLihatDataModel', modelId);
    if (trainingType) localStorage.setItem('lastTrainingTypeLihatDataModel', trainingType);
    if (currentPage) localStorage.setItem('lastPageLihatDataModel', currentPage);

    // 2. Tidak ada data dan ?page → redirect ke model_id & training_type saja
    if (noDataFound && urlParams.has('page')) {
        localStorage.removeItem('lastPageLihatDataModel');
        window.location.href = buildFullUrl(null, modelId, trainingType);
        return;
    }

    // 3. Tidak ada data tanpa ?page → diam saja
    if (noDataFound && !urlParams.has('page')) return;

    // 4. Redirect jika belum dihalaman terakhir
    if (!hasRedirected &&
        lastPage &&
        (lastPage !== currentPage ||
            modelId !== lastModelId ||
            trainingType !== lastTrainingType)) {

        // Gunakan fallback dari localStorage jika URL tidak punya
        const redirectModelId = modelId || localStorage.getItem('lastModelIdLihatDataModel');
        const redirectTrainingType = trainingType || localStorage.getItem('lastTrainingTypeLihatDataModel');

        localStorage.setItem('hasRedirectedLihatDataModel', 'true');
        window.location.href = buildFullUrl(lastPage, redirectModelId, redirectTrainingType);
        return;
    } else {
        localStorage.removeItem('hasRedirectedLihatDataModel');
    }

    // 5. Simpan page saat klik pagination
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function () {
            const url = new URL(this.href);
            const page = url.searchParams.get('page');
            const modelId = url.searchParams.get('model_id');
            const trainingType = url.searchParams.get('training_type');

            if (page) localStorage.setItem('lastPageLihatDataModel', page);
            if (modelId) localStorage.setItem('lastModelIdLihatDataModel', modelId);
            if (trainingType) localStorage.setItem('lastTrainingTypeLihatDataModel', trainingType);
        });
    });

    // 6. Simpan page saat form Go disubmit (GET method)
    const goToPageForm = document.querySelector('form[action=""]');
    if (goToPageForm) {
        goToPageForm.addEventListener('submit', function () {
            const formData = new FormData(goToPageForm);
            const page = formData.get('page');
            const modelId = formData.get('model_id');
            const trainingType = formData.get('training_type');

            if (page) localStorage.setItem('lastPageLihatDataModel', page);
            if (modelId) localStorage.setItem('lastModelIdLihatDataModel', modelId);
            if (trainingType) localStorage.setItem('lastTrainingTypeLihatDataModel', trainingType);
        });
    }
});