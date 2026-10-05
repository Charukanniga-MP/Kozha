const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: [
      '--use-fake-ui-for-media-stream',
      '--use-fake-device-for-media-stream',
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  });

  const page = await browser.newPage();
  const logs = [];
  const errors = [];
  const networkFails = [];

  page.on('console', msg => {
    logs.push(`[${msg.type()}] ${msg.text()}`);
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  page.on('pageerror', err => {
    errors.push(`PageError: ${err.message}`);
  });

  page.on('requestfailed', req => {
    networkFails.push(`FAILED: ${req.url()} (${req.failure()?.errorText})`);
  });

  console.log('Navigating to http://127.0.0.1:8000/dellar-lab.html...');
  await page.goto('http://127.0.0.1:8000/dellar-lab.html', { waitUntil: 'networkidle2', timeout: 30000 });

  await new Promise(r => setTimeout(r, 3000));

  const pageState = await page.evaluate(() => {
    const video = document.getElementById('webcamVideo');
    const canvas = document.getElementById('trackingCanvas');
    return {
      windowHandsDefined: typeof window.Hands !== 'undefined',
      mediaPipeHandsInitialized: typeof window.mediaPipeHands !== 'undefined' && window.mediaPipeHands !== null,
      isWebcamRunning: typeof isWebcamRunning !== 'undefined' ? isWebcamRunning : null,
      videoReadyState: video ? video.readyState : null,
      videoWidth: video ? video.videoWidth : null,
      videoHeight: video ? video.videoHeight : null,
      canvasWidth: canvas ? canvas.width : null,
      canvasHeight: canvas ? canvas.height : null,
      currentRecognizedWord: typeof currentRecognizedWord !== 'undefined' ? currentRecognizedWord : null,
      activeConfirmedSign: typeof activeConfirmedSign !== 'undefined' ? activeConfirmedSign : null,
      fallbackTrackerInterval: typeof fallbackTrackerInterval !== 'undefined' && fallbackTrackerInterval !== null
    };
  });

  console.log('Page State:', JSON.stringify(pageState, null, 2));
  console.log('Console Errors:', errors);
  console.log('Network Fails:', networkFails);
  console.log('Total Logs:', logs.length);
  console.log('Recent Logs:', logs.slice(-15));

  await browser.close();
})();
