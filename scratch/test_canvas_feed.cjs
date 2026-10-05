const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  page.on('console', msg => console.log('[PAGE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('[PAGE ERROR]', err.message));

  console.log('Navigating to http://127.0.0.1:8000/dellar-lab.html ...');
  await page.goto('http://127.0.0.1:8000/dellar-lab.html', { waitUntil: 'networkidle2' });

  const testRes = await page.evaluate(async () => {
    const iframe = document.getElementById('handTrackerFrame');
    if (!iframe || !iframe.contentWindow || !iframe.contentWindow.processVideoFrame) {
      return { error: 'iframe processVideoFrame not ready' };
    }

    // Wait until MediaPipe is initialized in iframe
    let attempts = 0;
    while (!iframe.contentWindow.isHandsReady && attempts < 30) {
      await new Promise(r => setTimeout(r, 100));
      attempts++;
    }

    // Create an offscreen canvas with explicit 640x480 dimensions
    const feedCanvas = document.createElement('canvas');
    feedCanvas.width = 640;
    feedCanvas.height = 480;
    const fctx = feedCanvas.getContext('2d');
    fctx.fillStyle = '#1e293b';
    fctx.fillRect(0, 0, 640, 480);
    // Draw palm circle
    fctx.fillStyle = '#ffdbac';
    fctx.beginPath();
    fctx.arc(320, 260, 55, 0, Math.PI * 2);
    fctx.fill();
    // Draw 5 fingers
    for (let i = 0; i < 5; i++) {
      fctx.fillRect(260 + i * 26, 120, 18, 90);
    }

    let gotCallback = false;
    let landmarkCount = 0;
    let firstResult = null;
    window.onHandResults = function(res) {
      gotCallback = true;
      landmarkCount = (res.multiHandLandmarks && res.multiHandLandmarks.length) || 0;
      firstResult = res;
    };

    let sendErr = null;
    try {
      await iframe.contentWindow.processVideoFrame(feedCanvas);
    } catch (e) {
      sendErr = e.message;
    }

    // wait 500ms for callback
    await new Promise(r => setTimeout(r, 600));

    return {
      gotCallback,
      landmarkCount,
      sendErr
    };
  });

  console.log('Test Canvas Feed Result:', JSON.stringify(testRes, null, 2));
  await browser.close();
})();
