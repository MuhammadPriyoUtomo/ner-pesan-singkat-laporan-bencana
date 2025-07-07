function toggleKelolaMode(mode) {
    const templateSection = document.getElementById('templateSection');
    const urgensiSection = document.getElementById('urgensiSection');
    const bencanaSection = document.getElementById('bencanaSection');
    const templateBtn = document.getElementById('templateBtn');
    const urgensiBtn = document.getElementById('urgensiBtn');
    const bencanaBtn = document.getElementById('bencanaBtn');

    // Simpan mode ke localStorage
    localStorage.setItem('activeTab', mode);

    // Sembunyikan semua
    templateSection.style.display = 'none';
    urgensiSection.style.display = 'none';
    bencanaSection.style.display = 'none';

    // Reset semua tombol
    templateBtn.className = 'btn btn-outline-primary';
    urgensiBtn.className = 'btn btn-outline-secondary';
    bencanaBtn.className = 'btn btn-outline-success';

    // Tampilkan dan aktifkan sesuai mode
    if (mode === 'template') {
        templateSection.style.display = 'block';
        templateBtn.className = 'btn btn-primary';
        document.getElementById('addButton').setAttribute('data-bs-target', '#addTemplateModal');

    } else if (mode === 'urgensi') {
        urgensiSection.style.display = 'block';
        urgensiBtn.className = 'btn btn-secondary';
        document.getElementById('addButton').setAttribute('data-bs-target', '#addUrgensiModal');

    } else if (mode === 'bencana') {
        bencanaSection.style.display = 'block';
        bencanaBtn.className = 'btn btn-success';
        document.getElementById('addButton').setAttribute('data-bs-target', '#addBencanaModal');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Tangkap semua tombol yang membuka modal
    const modalButtons = document.querySelectorAll('[data-bs-toggle="modal"]');

    modalButtons.forEach(button => {
        button.addEventListener('click', function () {
            const targetModalId = button.getAttribute('data-bs-target'); // Ambil ID modal dari data-bs-target
            const targetModal = document.querySelector(targetModalId); // Cari elemen modal berdasarkan ID

            if (targetModal) {
                targetModal.addEventListener('shown.bs.modal', function () {
                    // Cari input pertama di dalam modal
                    const firstInput = targetModal.querySelector('input, textarea, select');
                    if (firstInput) {
                        firstInput.focus(); // Pindahkan fokus ke input pertama
                    }
                }, { once: true }); // Pastikan event listener hanya dipanggil sekali per pembukaan modal
            }
        });
    });
});

// Saat halaman selesai dimuat
document.addEventListener('DOMContentLoaded', function () {
    const activeTab = localStorage.getItem('activeTab') || 'template'; // default ke template
    toggleKelolaMode(activeTab);

    // Delegasi event delete
    document.body.addEventListener('submit', function (e) {
        if (
            e.target.matches('.formDeleteBencana') ||
            e.target.matches('.formDeleteTemplate') ||
            e.target.matches('.formDeleteUrgensi')
        ) {
            e.preventDefault();
            const id = e.target.dataset.id;

            fetch(e.target.action, {
                method: 'POST'
            })
                .then(r => r.json())
                .then(res => {
                    if (res.status === 'success') {
                        window.location.reload();
                    }
                });
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const params = new URLSearchParams(window.location.search);
    const currentTemplate = params.get('page_template') || "1";
    const currentBencana = params.get('page_bencana') || "1";
    const currentUrgensi = params.get('page_urgensi') || "1";

    const storedTemplate = localStorage.getItem('page_template');
    const storedBencana = localStorage.getItem('page_bencana');
    const storedUrgensi = localStorage.getItem('page_urgensi');
    const hasRedirected = localStorage.getItem('hasRedirectedKelolaTemplate');

    // Simpan jika berbeda
    if (currentTemplate !== storedTemplate) localStorage.setItem('page_template', currentTemplate);
    if (currentBencana !== storedBencana) localStorage.setItem('page_bencana', currentBencana);
    if (currentUrgensi !== storedUrgensi) localStorage.setItem('page_urgensi', currentUrgensi);

    // Redirect hanya jika belum redirect dan halaman template tidak sesuai
    if (!hasRedirected && storedTemplate && storedBencana && storedUrgensi) {
        const needsRedirect = (
            currentTemplate !== storedTemplate ||
            currentBencana !== storedBencana ||
            currentUrgensi !== storedUrgensi
        );
        if (needsRedirect) {
            localStorage.setItem('hasRedirectedKelolaTemplate', 'true');
            const url = new URL(window.location.href);
            url.searchParams.set('page_template', storedTemplate);
            url.searchParams.set('page_bencana', storedBencana);
            url.searchParams.set('page_urgensi', storedUrgensi);
            window.location.href = url.toString();
            return;
        }
    } else {
        localStorage.removeItem('hasRedirectedKelolaTemplate');
    }

    // Klik baris: simpan ID dan halaman
    document.querySelectorAll('tbody tr').forEach(row => {
        row.addEventListener('click', function () {
            const id = this.id.replace('row-', '');
            localStorage.setItem('page_template', currentTemplate);
            localStorage.setItem('page_bencana', currentBencana);
            localStorage.setItem('page_urgensi', currentUrgensi);
        });
    });

    // Klik link pagination
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function () {
            const url = new URL(this.href);
            const pageTemplate = url.searchParams.get('page_template');
            const pageBencana = url.searchParams.get('page_bencana');
            const pageUrgensi = url.searchParams.get('page_urgensi');

            if (pageTemplate) localStorage.setItem('page_template', pageTemplate);
            if (pageBencana) localStorage.setItem('page_bencana', pageBencana);
            if (pageUrgensi) localStorage.setItem('page_urgensi', pageUrgensi);
        });
    });

    // Klik tombol "Go" form input manual
    document.querySelectorAll('.page-item form').forEach(form => {
        form.addEventListener('submit', function (e) {
            const template = form.querySelector('input[name="page_template"]')?.value;
            const bencana = form.querySelector('input[name="page_bencana"]')?.value;
            const urgensi = form.querySelector('input[name="page_urgensi"]')?.value;
            if (template) localStorage.setItem('page_template', template);
            if (bencana) localStorage.setItem('page_bencana', bencana);
            if (urgensi) localStorage.setItem('page_urgensi', urgensi);
        });
    });
});

// ================= Utility =================
function formToObj(form) {
    return Object.fromEntries(new FormData(form).entries());
}