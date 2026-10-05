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
  
  page.on('console', msg => console.log('[PAGE]', msg.text()));
  page.on('pageerror', err => console.error('[ERR]', err));

  await page.goto('http://127.0.0.1:8000/dellar-lab.html', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 4000));

  const result = await page.evaluate(async () => {
    return new Promise((resolve) => {
      let callCount = 0;
      let landmarksFound = 0;

      // Intercept onHandResults
      const origOnHandResults = window.onHandResults;
      window.onHandResults = function(res) {
        callCount++;
        if (res.multiHandLandmarks && res.multiHandLandmarks.length > 0) {
          landmarksFound++;
        }
        origOnHandResults(res);
      };

      setTimeout(() => {
        resolve({
          callCount,
          landmarksFound,
          activeConfirmedSign: window.activeConfirmedSign,
          currentRecognizedWord: window.currentRecognizedWord,
          speechQuoteText: document.getElementById('speechQuoteText')?.innerText
        });
      }, 5000);
    });
  });

  console.log('HAND DETECTION TEST RESULT:', JSON.stringify(result, null, 2));

  await browser.close();
})();
