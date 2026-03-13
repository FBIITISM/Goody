// Goody QR Scanner – uses html5-qrcode library via CDN
// Scans order QR codes and marks them as delivered

(function () {
  const SCANNER_ELEMENT_ID = 'qr-reader';
  const RESULT_ELEMENT_ID = 'qr-result';
  const DELIVER_ENDPOINT = '/kitchen/scan-deliver';

  let scanner = null;
  let scanning = false;

  function loadScript(src, cb) {
    const s = document.createElement('script');
    s.src = src;
    s.onload = cb;
    document.head.appendChild(s);
  }

  function initScanner() {
    const el = document.getElementById(SCANNER_ELEMENT_ID);
    if (!el) return;

    loadScript('https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js', () => {
      if (typeof Html5Qrcode === 'undefined') {
        document.getElementById(RESULT_ELEMENT_ID).innerHTML =
          '<div class="alert alert-warning small">QR scanner library failed to load.</div>';
        return;
      }

      scanner = new Html5Qrcode(SCANNER_ELEMENT_ID);
      const config = { fps: 10, qrbox: { width: 220, height: 220 } };

      scanner.start(
        { facingMode: 'environment' },
        config,
        onScanSuccess,
        onScanError
      ).then(() => {
        scanning = true;
      }).catch(err => {
        document.getElementById(RESULT_ELEMENT_ID).innerHTML =
          `<div class="alert alert-info small">Camera not available: ${err}. <br/>You can still use manual delivery buttons.</div>`;
      });
    });
  }

  async function onScanSuccess(decodedText) {
    if (!scanning) return;
    scanning = false; // prevent double-scan

    const resultEl = document.getElementById(RESULT_ELEMENT_ID);
    resultEl.innerHTML = '<div class="spinner-border spinner-border-sm text-success"></div> Processing...';

    try {
      const res = await fetch(DELIVER_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qr_data: decodedText }),
      });
      const data = await res.json();

      if (data.success) {
        resultEl.innerHTML = `
          <div class="alert alert-success">
            <i class="bi bi-check-circle-fill"></i>
            Order <strong>#${data.order_number}</strong> marked as Delivered! ✅
          </div>`;
        // Pause and reload
        if (scanner) scanner.pause();
        setTimeout(() => window.location.reload(), 2000);
      } else {
        resultEl.innerHTML = `<div class="alert alert-danger">Error: ${data.error || 'Order not found'}</div>`;
        setTimeout(() => { scanning = true; resultEl.innerHTML = ''; }, 3000);
      }
    } catch (e) {
      resultEl.innerHTML = `<div class="alert alert-danger">Network error. Try again.</div>`;
      setTimeout(() => { scanning = true; resultEl.innerHTML = ''; }, 3000);
    }
  }

  function onScanError(err) {
    // Silently ignore scan failures (normal during scanning)
  }

  // Start scanner when QR scan area is expanded
  const qrCollapseEl = document.getElementById('qrScanArea');
  if (qrCollapseEl) {
    qrCollapseEl.addEventListener('shown.bs.collapse', () => {
      if (!scanner) initScanner();
      else if (!scanning) { scanning = true; if (scanner.isPaused()) scanner.resume(); }
    });
    qrCollapseEl.addEventListener('hidden.bs.collapse', () => {
      if (scanner && typeof scanner.getState !== 'function') return; // safety
      scanning = false;
    });
  }
})();
