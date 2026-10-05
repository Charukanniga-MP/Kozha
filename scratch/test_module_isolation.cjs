const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  page.on('console', msg => console.log('[PAGE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('[PAGE ERROR]', err.message));

  await page.setContent(`
    <!DOCTYPE html>
    <html>
    <head>
      <script>
        // Simulate CWASA Emscripten module
        window.Module = {
          arguments: [],
          preRun: [],
          postRun: []
        };
      </script>
      <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
    </head>
    <body>
      <canvas id="c" width="320" height="240"></canvas>
      <script>
        async function test() {
          console.log('Testing MediaPipe with window.Module collision...');
          
          // Test with isolation: temporarily stash window.Module
          const cwasaModule = window.Module;
          window.Module = undefined; // isolate

          try {
            const hands = new window.Hands({
              locateFile: (file) => 'https://cdn.jsdelivr.net/npm/@mediapipe/hands/' + file
            });
            hands.setOptions({
              maxNumHands: 1,
              modelComplexity: 0,
              minDetectionConfidence: 0.5,
              minTrackingConfidence: 0.5
            });
            hands.onResults((res) => {
              console.log('SUCCESS! onResults received hands:', res.multiHandLandmarks ? res.multiHandLandmarks.length : 0);
            });

            // Restore CWASA module
            window.Module = cwasaModule;

            const c = document.getElementById('c');
            await hands.send({ image: c });
            console.log('SUCCESS! hands.send finished without aborting!');
          } catch(e) {
            console.error('FAILED WITH ERROR:', e);
          }
        }
        test();
      </script>
    </body>
    </html>
  `);

  await new Promise(r => setTimeout(r, 6000));
  await browser.close();
})();
