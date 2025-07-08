let allowForward = false;
let isProcessing = false;
let searchTimeout = null;

// Tambahkan state awal ke riwayat browser
history.replaceState(null, null, window.location.href);

// // Mengizinkan navigasi dari navbar
// document.querySelectorAll('.navbar a').forEach(function (navLink) {
//     navLink.addEventListener('click', function () {
//         allowForward = true;
//         setTimeout(() => {
//             allowForward = false; // Reset setelah navigasi selesai
//         }, 1000); // Sesuaikan waktu dengan durasi navigasi
//     });
// });

// Event listener untuk mencegah tombol backward dan forward
// window.addEventListener('popstate', function(event) {
//     // Dorong kembali state baru untuk mencegah navigasi
//     history.pushState(null, null, window.location.href);
//     alert('Navigasi back dan forward dinonaktifkan!');
// });

// window.addEventListener('keydown', function (event) {
//     if ((event.ctrlKey && event.key === 'r') || (event.ctrlKey && event.key === 'R') || (event.ctrlKey && event.shiftKey && event.key === 'r') || (event.ctrlKey && event.shiftKey && event.key === 'R') || event.key === 'F5') {
//         event.preventDefault();
//     }
// });

// window.addEventListener('beforeunload', function (event) {
//     if (isProcessing) {
//         event.preventDefault();
//         event.returnValue = ''; // Tampilkan dialog konfirmasi
//     }
// });

function highlightText(text, query) {
    if (!query) return text; // Jika query kosong, kembalikan teks asli

    // Escape karakter khusus regex agar tidak error
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    const regex = new RegExp(`(${escapedQuery})`, 'gi'); // Buat regex case-insensitive
    return text.replace(regex, '<span class="search-highlight">$1</span>');
}

// Di luar performSearch, sebelum DOMContentLoaded
let lastSearchHTML = '';
let lastSearchInfo = '';
let lastSearchQuery = '';
let lastSearchMode = '';

// Search
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const searchMode = document.getElementById('search-mode');
    const searchResults = document.getElementById('search-results');
    const searchInfo = document.getElementById('search-info');
    const searchWrapper = document.getElementById('search-wrapper');
    const searchBtn = document.getElementById('search-btn');

    function syncTableHeadScrollbar() {
        // Ambil elemen head dan body tabel hasil search model
        const tableHead = document.querySelector('#search-results > table');
        const tableBody = document.querySelector('#search-results > div > table');
        const scrollDiv = document.querySelector('#search-results > div');
        if (!tableHead || !tableBody || !scrollDiv) return;

        const bodyThs = tableBody.querySelectorAll('thead th');
        const scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth;
        let extraTh = '';
        if (scrollbarWidth > 0) {
            extraTh = `<th style="width:${scrollbarWidth}px;min-width:${scrollbarWidth}px;max-width:${scrollbarWidth}px;padding:0;border:none;background:transparent"></th>`;
        }
        // Update ulang tableHead agar th ekstra muncul
        tableHead.innerHTML = `
        <thead>
            <tr>
                <th>ID</th>
                <th>Text</th>
                <th>Model ID</th>
                <th>BERT Used</th>
                <th>Spacy Used</th>
                ${extraTh}
            </tr>
        </thead>
    `;
        // Sinkronisasi ulang lebar kolom
        const headThs = tableHead.querySelectorAll('th');
        for (let i = 0; i < Math.min(headThs.length, bodyThs.length); i++) {
            const width = bodyThs[i].getBoundingClientRect().width;
            headThs[i].style.width = width + 'px';
        }
        // th ekstra sudah diatur width-nya di atas
    }

    searchInput.addEventListener('focus', function () {
        // Jika ada hasil pencarian terakhir dan query belum berubah, tampilkan kembali
        if (lastSearchHTML && searchInput.value === lastSearchQuery && searchMode.value === lastSearchMode) {
            searchResults.innerHTML = lastSearchHTML;
            searchInfo.textContent = lastSearchInfo;
            searchInfo.style.display = 'block';
            searchWrapper.classList.add('border', 'border-success', 'border-5');
            // Tambahan: sinkronisasi ulang header jika mode model
            if (lastSearchMode === 'model') {
                setTimeout(syncTableHeadScrollbar, 0);
            }
        }
    });

    function performSearch(query) {
        if (query.length > 2) {
            // Tambahkan kelas berkedip ke tombol search
            const searchForm = searchInput.closest('form');
            if (searchForm) searchForm.classList.add('form-blink');

            const mode = searchMode.value;
            let url = '/search?query=' + encodeURIComponent(query);
            if (mode === 'model_bert') {
                url = '/search_model?query=' + encodeURIComponent(query) + '&type=bert';
            } else if (mode === 'model_spacy') {
                url = '/search_model?query=' + encodeURIComponent(query) + '&type=spacy';
            } else if (mode === 'bencana') {
                url = '/search_bencana?query=' + encodeURIComponent(query);
            }
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';
                    if (mode === 'lokasi') {
                        const listGroup = document.createElement('div');
                        listGroup.className = 'list-group';
                        data.forEach(item => {
                            const resultItem = document.createElement('div');
                            resultItem.className = 'list-group-item d-flex justify-content-between align-items-center flex-wrap';
                            resultItem.innerHTML = `
                                <span>
                                    <i class="bi bi-clipboard-data-fill" style="cursor:pointer" onclick="copyToClipboard('${item[1]}, ${item[3]}, ${item[5]}, ${item[7]}')"></i>
                                    ${highlightText(`${item[1]}, ${item[3]}, ${item[5]}, ${item[7]}`, query)}
                                </span>
                                <a href="https://www.google.com/maps/search/${encodeURIComponent(item[1] + ', ' + item[3] + ', ' + item[5] + ', ' + item[7])}" 
                                    target="_blank" title="Cari di Google Maps" style="margin-left: 8px; color: #0d6efd; white-space:nowrap;">
                                    <i class="bi bi-search"></i> Cari
                                </a>
                            `;
                            listGroup.appendChild(resultItem);
                        });
                        searchResults.appendChild(listGroup);
                        searchInfo.textContent = `Menemukan ${data.length} data lokasi yang relevan`;
                    }  else if (mode === 'model_bert' || mode === 'model_spacy') {
                        // 1. Head luar (selalu terlihat)
                        let tableHead = document.createElement('table');
                        tableHead.className = 'table table-bordered table-hover table-striped shadow mb-0 w-100';
                        tableHead.style.border = '2px solid #28a745';
                        tableHead.style.tableLayout = 'fixed';

                        // 2. Tabel isi (tbody) + head dalam (hidden)
                        let tableBody = document.createElement('table');
                        tableBody.className = 'table table-bordered table-hover table-striped shadow mb-0 w-100 table-inner-hide';
                        tableBody.style.border = '2px solid #28a745';
                        // Tidak perlu tableLayout fixed di body, biarkan natural
                        tableBody.innerHTML = `
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Text</th>
                                    <th>Model ID</th>
                                    <th>BERT Used</th>
                                    <th>Spacy Used</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.map(item => `
                                    <tr>
                                        <td>${item[0]}</td>
                                        <td>${highlightText(item[1], query)}</td>
                                        <td>${item[2]}</td>
                                        <td>${item[3]}</td>
                                        <td>${item[4]}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        `;

                        // Render ke DOM
                        searchResults.innerHTML = '';
                        searchResults.appendChild(tableHead);

                        // Bungkus tbody dengan div scrollable
                        let scrollDiv = document.createElement('div');
                        scrollDiv.style.maxHeight = '300px';
                        scrollDiv.style.overflowY = 'auto';
                        scrollDiv.appendChild(tableBody);
                        searchResults.appendChild(scrollDiv);

                        // Sinkronisasi lebar kolom head luar dan isi, serta th kosong untuk scrollbar
                        setTimeout(() => {
                            const bodyThs = tableBody.querySelectorAll('thead th');
                            const scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth;
                            let extraTh = '';
                            if (scrollbarWidth > 0) {
                                extraTh = `<th style="width:${scrollbarWidth}px;min-width:${scrollbarWidth}px;max-width:${scrollbarWidth}px;padding:0;border:none;background:transparent"></th>`;
                            }
                            tableHead.innerHTML = `
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Text</th>
                                        <th>Model ID</th>
                                        <th>BERT Used</th>
                                        <th>Spacy Used</th>
                                        ${extraTh}
                                    </tr>
                                </thead>
                            `;
                            const headThs = tableHead.querySelectorAll('th');
                            for (let i = 0; i < Math.min(headThs.length, bodyThs.length); i++) {
                                const width = bodyThs[i].getBoundingClientRect().width;
                                headThs[i].style.width = width + 'px';
                            }
                        }, 0);

                        // Info label sesuai mode
                        if (mode === 'model_bert') {
                            searchInfo.textContent = `Menemukan ${data.length} data model BERT yang relevan`;
                        } else {
                            searchInfo.textContent = `Menemukan ${data.length} data model Spacy yang relevan`;
                        }
                    } else if (mode === 'bencana') {
                        const listGroup = document.createElement('div');
                        listGroup.className = 'list-group';
                        data.forEach(item => {
                            const resultItem = document.createElement('div');
                            resultItem.className = 'list-group-item d-flex justify-content-between align-items-center flex-wrap';
                            resultItem.innerHTML = `
                            <span>
                                <i class="bi bi-clipboard-data-fill" style="cursor:pointer" onclick="copyToClipboard('${item[1]}')"></i>
                                ${highlightText(item[1], query)}
                            </span>
                        `;
                            listGroup.appendChild(resultItem);
                        });
                        searchResults.appendChild(listGroup);
                        searchInfo.textContent = `Menemukan ${data.length} data bencana yang relevan`;
                    }
                    searchInfo.style.display = 'block';
                    searchInfo.style.top = `${searchResults.offsetHeight}px`;
                    searchWrapper.classList.add('border', 'border-success', 'border-5');

                    lastSearchHTML = searchResults.innerHTML;
                    lastSearchInfo = searchInfo.textContent;
                    lastSearchQuery = query;
                    lastSearchMode = mode;
                })
                .catch(error => {
                    console.error("Error fetching search results:", error);
                })
                .finally(() => {
                    // Hapus kelas berkedip setelah selesai
                    if (searchForm) searchForm.classList.remove('form-blink');
                });
        } else {
            searchResults.innerHTML = '';
            searchInfo.textContent = '';
            searchInfo.style.display = 'none';
            searchWrapper.classList.remove('border', 'border-success', 'border-5');
            searchWrapper.classList.remove('border', 'border-success', 'border-5');
        }
    }

    if (searchInput && searchResults && searchInfo && searchWrapper && searchMode && searchBtn) {
        searchBtn.addEventListener('click', function () {
            performSearch(searchInput.value);
        });
        // Optional: Enter key triggers search
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(searchInput.value);
            }
        });
        searchMode.addEventListener('change', function () {
            // Optional: clear results when mode changed
            searchResults.innerHTML = '';
            searchInfo.textContent = '';
            searchInfo.style.display = 'none';
            searchWrapper.classList.remove('border', 'border-success', 'border-5');
        });
        document.addEventListener('click', function (event) {
            if (!searchInput.contains(event.target) && !searchWrapper.contains(event.target)) {
                searchResults.innerHTML = '';
                searchInfo.textContent = '';
                searchInfo.style.display = 'none';
                searchWrapper.classList.remove('border', 'border-success', 'border-5');
            }
        });
    }
});

// clipboard search
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function () {
        console.log('Copied to clipboard successfully!');
        // Tampilkan data yang disalin di modal body
        document.getElementById('copyModalBody').textContent = text;
        // Tampilkan modal
        var copyModal = new bootstrap.Modal(document.getElementById('copyModal'));
        copyModal.show();
    }, function (err) {
        console.error('Could not copy text: ', err);
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const requirementsList = document.getElementById('requirements-list');

    // Fetch daftar requirements dari server
    fetch('/get_requirements')
        .then(response => response.json())
        .then(data => {
            if (data.requirements) {
                // Tambahkan setiap item ke dalam <ul>
                data.requirements.forEach(req => {
                    const li = document.createElement('li');
                    li.textContent = req;
                    requirementsList.appendChild(li);
                });
            } else {
                // Tampilkan pesan error jika tidak ada data
                const li = document.createElement('li');
                li.textContent = 'Tidak ada data requirements.';
                requirementsList.appendChild(li);
            }
        })
        .catch(error => {
            console.error('Error fetching requirements:', error);
            const li = document.createElement('li');
            li.textContent = 'Gagal memuat daftar requirements.';
            requirementsList.appendChild(li);
        });
});

function toggleInfo(section) {
    const requirementsSection = document.getElementById('requirementsSection');
    const profileSection = document.getElementById('profileSection');
    const requirementsBtn = document.getElementById('requirementsBtn');
    const profileBtn = document.getElementById('profileBtn');

    // Reset semua tampilan
    requirementsSection.style.display = 'none';
    profileSection.style.display = 'none';
    requirementsBtn.classList.remove('active');
    profileBtn.classList.remove('active');

    // Tampilkan bagian yang dipilih
    if (section === 'requirements') {
        requirementsSection.style.display = 'block';
        requirementsBtn.classList.add('active');
    } else if (section === 'profile') {
        profileSection.style.display = 'block';
        profileBtn.classList.add('active');
    }
}
