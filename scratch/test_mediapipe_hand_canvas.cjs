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
  page.on('pageerror', err => console.error('[PAGE ERROR]:', err));

  await page.goto('http://127.0.0.1:8000/dellar-lab.html', { waitUntil: 'networkidle2' });

  const testInfo = await page.evaluate(async () => {
    const video = document.getElementById('webcamVideo');
    const logs = [];

    logs.push(`video exists: ${!!video}, readyState: ${video?.readyState}, videoWidth: ${video?.videoWidth}`);
    logs.push(`window.Hands exists: ${typeof window.Hands}`);

    if (window.Hands) {
      try {
        const testHands = new window.Hands({
          locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}`
        });
        testHands.setOptions({
          maxNumHands: 1,
          modelComplexity: 0,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });

        let resultsFired = false;
        testHands.onResults((res) => {
          resultsFired = true;
          logs.push(`testHands onResults received! Hands count: ${res.multiHandLandmarks ? res.multiHandLandmarks.length : 0}`);
        });

        logs.push('Calling testHands.initialize()...');
        if (typeof testHands.initialize === 'function') {
          await testHands.initialize();
          logs.push('testHands.initialize completed!');
        }

        // Draw a simulated hand onto a test canvas and send it
        const c = document.createElement('canvas');
        c.width = 320;
        c.height = 240;
        const ctx = c.getContext('2d');
        ctx.fillStyle = '#ffccaa'; // skin tone
        ctx.fillRect(100, 50, 120, 140); // palm
        ctx.fillRect(110, 10, 20, 50); // index
        ctx.fillRect(140, 5, 20, 55); // middle
        ctx.fillRect(170, 10, 20, 50); // ring
        ctx.fillRect(200, 25, 18, 40); // pinky
        ctx.fillRect(75, 90, 30, 25); // thumb

        logs.push('Sending simulated hand canvas to testHands.send()...');
        await testHands.send({ image: c });
        logs.push(`testHands.send succeeded! resultsFired = ${resultsFired}`);
      } catch(err) {
        logs.push(`testHands ERROR: ${err.message}\n${err.stack}`);
      }
    }

    return logs;
  });

  console.log('TEST RESULTS:\n' + testInfo.join('\n'));

  await browser.close();
})();
