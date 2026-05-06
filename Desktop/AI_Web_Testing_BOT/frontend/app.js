// API Base URL - Explicitly use the backend server port
const API_BASE_URL = 'http://127.0.0.1:5000';

// DOM Elements
const urlInput = document.getElementById('urlInput');
const testBtn = document.getElementById('testBtn');
const loadingDiv = document.getElementById('loading');
const resultsDiv = document.getElementById('results');
const errorDiv = document.getElementById('error');
const errorText = document.getElementById('errorText');

// Stats Elements
const totalLinksEl = document.getElementById('totalLinks');
const workingLinksEl = document.getElementById('workingLinks');
const brokenLinksEl = document.getElementById('brokenLinks');
const successRateEl = document.getElementById('successRate');
const linksTableBody = document.getElementById('linksTableBody');

// Store all links for filtering
let allLinksData = [];
let currentFilter = 'all';

// Start Test Function
async function startTest() {
    const url = urlInput.value.trim();

    // Validate URL
    if (!url) {
        showError('Please enter a valid URL');
        return;
    }

    if (!isValidUrl(url)) {
        showError('Please enter a valid URL (e.g., https://example.com)');
        return;
    }

    // Reset UI
    hideError();
    hideResults();
    showLoading();

    // Disable button during test
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';

    try {
        // Call the API
        const response = await fetch(`${API_BASE_URL}/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // Display results
        displayResults(data);

    } catch (error) {
        showError(`Error: ${error.message}. Make sure the backend server is running.`);
    } finally {
        hideLoading();
        testBtn.disabled = false;
        testBtn.textContent = 'Start Test';
    }
}

// Display Results
function displayResults(data) {
    console.log('displayResults called with data:', data);
    const links = data.results || [];
    const total = links.length;
    const working = links.filter(link => link.status >= 200 && link.status < 400).length;
    const broken = total - working;
    const rate = total > 0 ? Math.round((working / total) * 100) : 0;
    
    console.log('Total:', total, 'Working:', working, 'Broken:', broken);

    // Store links for filtering
    allLinksData = links;
    currentFilter = 'all';

    // Update stats
    totalLinksEl.textContent = total;
    workingLinksEl.textContent = working;
    brokenLinksEl.textContent = broken;
    successRateEl.textContent = rate + '%';

    // Display AI Summary
    const aiSummaryEl = document.getElementById('aiSummary');
    const summaryTextEl = document.getElementById('summaryText');
    if (data.ai_summary) {
        summaryTextEl.textContent = data.ai_summary;
        aiSummaryEl.classList.remove('hidden');
    } else {
        aiSummaryEl.classList.add('hidden');
    }

    // Populate table with all links
    populateTable(links);

    // Show results
    console.log('Showing results...');
    showResults();
}

// Populate table with filtered links
function populateTable(links) {
    linksTableBody.innerHTML = '';

    links.forEach(link => {
        const row = document.createElement('tr');
        const statusClass = getStatusClass(link.status);
        const statusText = getStatusText(link.status);
        
        // Add details button for all links
        const detailBtn = `<button class="detail-btn" onclick="showDetail('${encodeURIComponent(link.url)}', '${encodeURIComponent(link.error_detail || '')}', ${link.status})">Details</button>`;

        row.innerHTML = `
            <td class="url-cell"><a href="${link.url}" target="_blank" title="${link.url}">${truncateUrl(link.url)}</a></td>
            <td>${link.status}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${detailBtn}</td>
        `;

        linksTableBody.appendChild(row);
    });
}

// Show detail modal
function showDetail(url, errorDetail, status) {
    const modal = document.getElementById('errorModal');
    const modalUrl = document.getElementById('modalUrl');
    const modalDetail = document.getElementById('modalDetail');
    
    modalUrl.textContent = decodeURIComponent(url);
    modalDetail.textContent = decodeURIComponent(errorDetail) || getStatusText(status);
    modalDetail.className = 'modal-detail ' + getStatusClass(status);
    
    modal.classList.remove('hidden');
}

// Close modal
function closeModal() {
    document.getElementById('errorModal').classList.add('hidden');
}

// Filter links function
function filterLinks(filter) {
    currentFilter = filter;
    
    // Update button states
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });

    // Filter data
    let filteredLinks;
    if (filter === 'all') {
        filteredLinks = allLinksData;
    } else if (filter === 'ok') {
        filteredLinks = allLinksData.filter(link => link.status >= 200 && link.status < 400);
    } else if (filter === 'error') {
        filteredLinks = allLinksData.filter(link => link.status === 0 || link.status >= 400);
    }

    populateTable(filteredLinks);
}

// Download PDF function
function downloadPDF() {
    if (allLinksData.length === 0) {
        showError('No results to download');
        return;
    }

    const url = urlInput.value;
    const total = allLinksData.length;
    const working = allLinksData.filter(link => link.status >= 200 && link.status < 400).length;
    const broken = total - working;
    const rate = Math.round((working / total) * 100);
    const date = new Date().toLocaleString();

    // Build PDF content
    let content = `
AI WEB TESTING BOT REPORT
=========================

Test URL: ${url}
Test Date: ${date}

SUMMARY
=======

Total Links Tested: ${total}
Working Links: ${working}
Broken Links: ${broken}
Success Rate: ${rate}%

LINK DETAILS
============

`;

    allLinksData.forEach((link, index) => {
        const status = link.status === 0 ? 'ERROR' : link.status;
        const result = link.status >= 200 && link.status < 400 ? 'OK' : 
                     link.status >= 300 && link.status < 400 ? 'REDIRECT' : 'ERROR';
        content += `${index + 1}. ${link.url}
   Status: ${status} - ${result}
`;
    });

    content += `
Generated by AI Web Testing Bot
`;

    // Create and download file
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `web-test-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
}

// Helper Functions
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

function getStatusClass(status) {
    if (status === 0) return 'error';
    if (status >= 200 && status < 300) return 'success';
    if (status >= 300 && status < 400) return 'warning';
    return 'error';
}

function getStatusText(status) {
    if (status === 0) return 'Error';
    if (status >= 200 && status < 300) return 'OK';
    if (status >= 300 && status < 400) return 'Redirect';
    if (status >= 400 && status < 500) return 'Client Error';
    if (status >= 500) return 'Server Error';
    return 'Unknown';
}

function truncateUrl(url, maxLength = 60) {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength) + '...';
}

// UI Control Functions
function showLoading() {
    loadingDiv.classList.remove('hidden');
}

function hideLoading() {
    loadingDiv.classList.add('hidden');
}

function showResults() {
    resultsDiv.classList.remove('hidden');
}

function hideResults() {
    resultsDiv.classList.add('hidden');
}

function showError(message) {
    errorText.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    errorDiv.classList.add('hidden');
}

// Enter key support
urlInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        startTest();
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Web Testing Bot initialized');
});
