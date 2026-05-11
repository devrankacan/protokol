/* Genexa CRO — Frontend Logic */

// ── Drag & Drop ──────────────────────────────────────────────────────────────

document.querySelectorAll('.upload-zone').forEach(zone => {
  if (zone.classList.contains('upload-zone-disabled')) return;

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.style.borderColor = 'var(--navy-mid)';
    zone.style.background  = '#F0F4FF';
  });

  zone.addEventListener('dragleave', () => {
    zone.style.borderColor = '';
    zone.style.background  = '';
  });

  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.style.borderColor = '';
    zone.style.background  = '';

    const file = e.dataTransfer.files[0];
    if (!file) return;

    const input = zone.querySelector('.file-input');
    if (!input || input.disabled) return;

    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event('change'));
  });
});


// ── Protocol Upload ───────────────────────────────────────────────────────────

async function uploadProtocol(input) {
  const file = input.files[0];
  if (!file) return;

  const progress = document.getElementById('protocol-progress');
  const fill     = document.getElementById('protocol-progress-fill');
  const text     = document.getElementById('protocol-progress-text');
  const result   = document.getElementById('protocol-result');

  showProgress(progress, fill, text, 'Protokol yükleniyor...', false);
  hideEl(result);

  const formData = new FormData();
  formData.append('file', file);

  try {
    // Animate progress during upload
    animateProgress(fill, 0, 85, 1200);

    const res = await fetch('/api/upload-protocol', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();

    fill.style.width = '100%';

    if (res.ok && data.success) {
      showResult(result, `✅ ${data.message} (${(data.char_count / 1000).toFixed(0)}K karakter)`, true);
      setTimeout(() => location.reload(), 1500);
    } else {
      showResult(result, `❌ Hata: ${data.detail || 'Yükleme başarısız'}`, false);
    }
  } catch (err) {
    showResult(result, `❌ Bağlantı hatası: ${err.message}`, false);
  } finally {
    hideProgress(progress);
    input.value = '';
  }
}


// ── Language Toggle ───────────────────────────────────────────────────────────

function setLang(lang) {
  document.getElementById('report-language').value = lang;
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('lang-btn-active', btn.dataset.lang === lang);
  });
}


// ── Patient Analysis ──────────────────────────────────────────────────────────

async function analyzePatient(input) {
  const file = input.files[0];
  if (!file) return;

  const patientId   = document.getElementById('patient-id')?.value?.trim() || '';
  const language    = document.getElementById('report-language')?.value || 'tr';
  const includeLogo = document.getElementById('include-logo')?.value || '0';
  const progress  = document.getElementById('patient-progress');
  const fill      = document.getElementById('patient-progress-fill');
  const text      = document.getElementById('patient-progress-text');
  const result    = document.getElementById('patient-result');

  const isTR = language === 'tr';
  const waitMsg = isTR
    ? 'Claude AI analiz yapıyor — lütfen bekleyin (~30-60 sn)...'
    : 'Claude AI is analyzing — please wait (~30-60 sec)...';

  showProgress(progress, fill, text, waitMsg, true);
  hideEl(result);

  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);
  formData.append('include_logo', includeLogo);
  if (patientId) formData.append('patient_id', patientId);

  // Cycle status messages during long analysis
  const messages = isTR ? [
    'Protokol kriterleri karşılaştırılıyor...',
    'Biyomarker değerleri analiz ediliyor...',
    'Klinik bulgular değerlendiriliyor...',
    'Kohort önerisi hesaplanıyor...',
    'Risk değerlendirmesi yapılıyor...',
    'Rapor oluşturuluyor...',
  ] : [
    'Comparing protocol criteria...',
    'Analyzing biomarker values...',
    'Evaluating clinical findings...',
    'Calculating cohort recommendation...',
    'Performing risk assessment...',
    'Generating report...',
  ];
  let msgIdx = 0;
  const msgTimer = setInterval(() => {
    msgIdx = (msgIdx + 1) % messages.length;
    text.textContent = messages[msgIdx];
  }, 7000);

  try {
    const res = await fetch('/api/analyze-patient', {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();

    if (res.ok && data.success) {
      const icon = data.karar === 'UYGUN' ? '✅' : data.karar === 'UYGUN_DEGIL' ? '❌' : '⚠️';
      showResult(
        result,
        `${icon} Analiz tamamlandı — <strong>${data.patient_id}</strong>: ${data.karar_text}
         <br><a href="/report/${data.report_id}" target="_blank" style="color:var(--navy-mid);font-weight:700">Raporu Görüntüle →</a>
         &nbsp; <a href="/report/${data.report_id}/pdf" style="color:var(--navy-mid);font-weight:700">PDF İndir ↓</a>`,
        true
      );
      showToast(data);
      setTimeout(() => location.reload(), 5000);
    } else {
      showResult(result, `❌ Hata: ${data.detail || 'Analiz başarısız'}`, false);
    }
  } catch (err) {
    showResult(result, `❌ Bağlantı hatası: ${err.message}`, false);
  } finally {
    clearInterval(msgTimer);
    hideProgress(progress);
    input.value = '';
  }
}


// ── Logo Toggle ───────────────────────────────────────────────────────────────

function toggleLogo() {
  const btn = document.getElementById('logo-toggle-btn');
  const input = document.getElementById('include-logo');
  const label = document.getElementById('logo-toggle-label');
  const isActive = btn.classList.toggle('active');
  input.value = isActive ? '1' : '0';
  label.textContent = isActive ? 'Logo Aktif' : 'Logo Ekle';
}


// ── Logo Upload ───────────────────────────────────────────────────────────────

async function uploadLogo(input) {
  const file = input.files[0];
  if (!file) return;

  const msg = document.getElementById('logo-upload-msg');
  msg.textContent = 'Yükleniyor...';
  msg.style.color = 'var(--text-light)';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload-logo', { method: 'POST', body: formData });
    const data = await res.json();

    if (res.ok && data.success) {
      msg.textContent = '✅ Logo güncellendi';
      msg.style.color = 'var(--success)';
      const preview = document.getElementById('logo-preview-img');
      const placeholder = document.getElementById('logo-placeholder');
      preview.src = '/static/images/logo.png?t=' + Date.now();
      preview.style.display = 'block';
      if (placeholder) placeholder.style.display = 'none';
      setTimeout(() => location.reload(), 1200);
    } else {
      msg.textContent = '❌ ' + (data.detail || 'Hata');
      msg.style.color = 'var(--danger)';
    }
  } catch (err) {
    msg.textContent = '❌ Bağlantı hatası';
    msg.style.color = 'var(--danger)';
  } finally {
    input.value = '';
  }
}


// ── Toast Notification ────────────────────────────────────────────────────────

function showToast(data) {
  const icon = data.karar === 'UYGUN' ? '✅' : data.karar === 'UYGUN_DEGIL' ? '❌' : '⚠️';
  const isTR = (data.language || 'tr') === 'tr';
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-body">
      <div class="toast-title">${isTR ? 'Raporunuz Hazır!' : 'Report Ready!'}</div>
      <div class="toast-sub">${data.patient_id} — ${data.karar_text}</div>
      <div class="toast-actions">
        <a href="/report/${data.report_id}" target="_blank">${isTR ? 'Görüntüle' : 'View'}</a>
        <a href="/report/${data.report_id}/pdf">${isTR ? 'PDF İndir' : 'Download PDF'}</a>
      </div>
    </div>
    <button class="toast-close" onclick="dismissToast(this.closest('.toast'))">×</button>
  `;
  document.body.appendChild(toast);
  setTimeout(() => dismissToast(toast), 8000);
}

function dismissToast(toast) {
  if (!toast || toast.classList.contains('toast-hiding')) return;
  toast.classList.add('toast-hiding');
  setTimeout(() => toast.remove(), 300);
}


// ── Accordion ─────────────────────────────────────────────────────────────────

function toggleAcc(btn) {
  const parent = btn.parentElement;
  const body   = btn.nextElementSibling;
  const isOpen = parent.classList.toggle('acc-open');
  body.classList.toggle('acc-body-open', isOpen);
}


// ── Report Search ─────────────────────────────────────────────────────────────

function searchReports(query) {
  const accordion    = document.getElementById('report-accordion');
  const searchResult = document.getElementById('search-results');
  const clearBtn     = document.getElementById('search-clear');
  const tbody        = document.getElementById('search-tbody');

  query = query.trim().toLowerCase();

  if (!query) {
    searchResult.classList.add('hidden');
    accordion.classList.remove('hidden');
    clearBtn.classList.add('hidden');
    return;
  }

  clearBtn.classList.remove('hidden');
  accordion.classList.add('hidden');
  searchResult.classList.remove('hidden');

  // Collect all report rows from accordion
  const allRows = document.querySelectorAll('#report-accordion tr[data-search]');
  tbody.innerHTML = '';
  let count = 0;
  allRows.forEach(row => {
    if (row.dataset.search.includes(query)) {
      tbody.appendChild(row.cloneNode(true));
      count++;
    }
  });

  if (count === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="padding:24px;text-align:center;color:var(--text-light)">Sonuç bulunamadı.</td></tr>';
  }
}

function clearSearch() {
  const input = document.getElementById('report-search');
  input.value = '';
  searchReports('');
  input.focus();
}


// ── Helpers ───────────────────────────────────────────────────────────────────

function showProgress(container, fill, text, message, animated) {
  container.classList.remove('hidden');
  text.textContent = message;
  if (animated) {
    fill.classList.add('progress-animated');
    fill.style.width = '100%';
  } else {
    fill.classList.remove('progress-animated');
    fill.style.width = '0%';
  }
}

function hideProgress(container) {
  container.classList.add('hidden');
}

function showResult(el, html, success) {
  el.innerHTML = html;
  el.className = 'result-msg ' + (success ? 'result-success' : 'result-error');
  el.classList.remove('hidden');
}

function hideEl(el) {
  el.classList.add('hidden');
}

function animateProgress(fill, from, to, duration) {
  const start = performance.now();
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    fill.style.width = (from + (to - from) * eased) + '%';
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
