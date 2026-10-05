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
  
  page.on('console', msg => {
    console.log('[BROWSER ' + msg.type() + ']:', msg.text());
  });

  page.on('pageerror', err => {
    console.error('[BROWSER ERROR]:', err);
  });

  console.log('Navigating to http://127.0.0.1:8000/dellar-lab.html...');
  await page.goto('http://127.0.0.1:8000/dellar-lab.html', { waitUntil: 'domcontentloaded' });

  // Wait 10 seconds to observe logs
  await new Promise(r => setTimeout(r, 10000));

  const debugInfo = await page.evaluate(() => {
    return {
      windowHands: typeof window.Hands,
      mediaPipeHands: typeof mediaPipeHands !== 'undefined' ? (mediaPipeHands !== null) : 'undefined',
      isWebcamRunning: typeof isWebcamRunning !== 'undefined' ? isWebcamRunning : 'undefined',
      webcamStream: typeof webcamStream !== 'undefined' ? (webcamStream !== null) : 'undefined',
      video: {
        srcObject: document.getElementById('webcamVideo')?.srcObject !== null,
        readyState: document.getElementById('webcamVideo')?.readyState,
        videoWidth: document.getElementById('webcamVideo')?.videoWidth,
        videoHeight: document.getElementById('webcamVideo')?.videoHeight
      },
      fallbackTrackerInterval: typeof fallbackTrackerInterval !== 'undefined' ? (fallbackTrackerInterval !== null) : 'undefined',
      activeConfirmedSign: typeof activeConfirmedSign !== 'undefined' ? activeConfirmedSign : 'undefined'
    };
  });

  console.log('DEBUG INFO:', JSON.stringify(debugInfo, null, 2));

  await browser.close();
})();
