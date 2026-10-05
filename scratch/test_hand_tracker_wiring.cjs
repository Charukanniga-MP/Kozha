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

  const result = await page.evaluate(async () => {
    const iframe = document.getElementById('handTrackerFrame');
    if (!iframe) return { error: 'iframe not found' };
    
    // Check if iframe is ready
    const hasProcess = typeof iframe.contentWindow.processVideoFrame === 'function';
    
    // Create an offscreen canvas with a simulated hand drawn on it
    const testCanvas = document.createElement('canvas');
    testCanvas.width = 640;
    testCanvas.height = 480;
    const ctx = testCanvas.getContext('2d');
    ctx.fillStyle = '#111827';
    ctx.fillRect(0, 0, 640, 480);
    // Draw a hand-like flesh shape
    ctx.fillStyle = '#ffdbac';
    ctx.beginPath();
    ctx.arc(320, 240, 60, 0, Math.PI * 2);
    ctx.fill();

    let receivedResults = null;
    window.onHandResults = function(res) {
      receivedResults = res;
    };

    let sendError = null;
    try {
      await iframe.contentWindow.processVideoFrame(testCanvas);
    } catch (e) {
      sendError = e.message;
    }

    return {
      hasProcess,
      sendError,
      receivedResults: receivedResults ? {
        hasMultiHand: !!receivedResults.multiHandLandmarks,
        count: receivedResults.multiHandLandmarks ? receivedResults.multiHandLandmarks.length : 0
      } : null
    };
  });

  console.log('Test result:', JSON.stringify(result, null, 2));

  await browser.close();
})();
