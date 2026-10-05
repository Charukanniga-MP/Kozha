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
  
  page.on('console', msg => console.log('[PAGE ' + msg.type() + ']:', msg.text()));
  page.on('pageerror', err => console.error('[ERR]', err));

  await page.goto('http://127.0.0.1:8000/dellar-lab.html', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 4000));

  const sendResult = await page.evaluate(async () => {
    const video = document.getElementById('webcamVideo');
    if (!window.mediaPipeHands) {
      return { error: 'mediaPipeHands is null or not initialized' };
    }
    try {
      console.log('Explicitly calling mediaPipeHands.send({ image: video })...');
      const promise = window.mediaPipeHands.send({ image: video });
      
      // race with 4 second timeout
      const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('mediaPipeHands.send TIMEOUT after 4s')), 4000));
      await Promise.race([promise, timeoutPromise]);
      return { success: true };
    } catch(e) {
      return { error: e.message, stack: e.stack };
    }
  });

  console.log('SEND RESULT:', JSON.stringify(sendResult, null, 2));

  await browser.close();
})();
