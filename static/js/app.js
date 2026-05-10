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


// ── Patient Analysis ──────────────────────────────────────────────────────────

async function analyzePatient(input) {
  const file = input.files[0];
  if (!file) return;

  const patientId = document.getElementById('patient-id')?.value?.trim() || '';
  const progress  = document.getElementById('patient-progress');
  const fill      = document.getElementById('patient-progress-fill');
  const text      = document.getElementById('patient-progress-text');
  const result    = document.getElementById('patient-result');

  showProgress(progress, fill, text, 'Claude AI analiz yapıyor — lütfen bekleyin (~30-60 sn)...', true);
  hideEl(result);

  const formData = new FormData();
  formData.append('file', file);
  if (patientId) formData.append('patient_id', patientId);

  // Cycle status messages during long analysis
  const messages = [
    'Protokol kriterleri karşılaştırılıyor...',
    'Biyomarker değerleri analiz ediliyor...',
    'Klinik bulgular değerlendiriliyor...',
    'Kohort önerisi hesaplanıyor...',
    'Risk değerlendirmesi yapılıyor...',
    'Rapor oluşturuluyor...',
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
      setTimeout(() => location.reload(), 4000);
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
