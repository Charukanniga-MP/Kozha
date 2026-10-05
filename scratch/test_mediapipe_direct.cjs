const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('PAGE ERROR:', err.message));

  console.log('Testing MediaPipe Hands standalone...');
  await page.setContent(`
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
    </head>
    <body>
      <canvas id="c" width="300" height="300"></canvas>
      <script>
        async function test() {
          console.log('window.Hands exists?', typeof window.Hands);
          try {
            const hands = new window.Hands({
              locateFile: (file) => 'https://cdn.jsdelivr.net/npm/@mediapipe/hands/' + file
            });
            hands.setOptions({
              maxNumHands: 2,
              modelComplexity: 1,
              minDetectionConfidence: 0.5,
              minTrackingConfidence: 0.5
            });
            hands.onResults((res) => {
              console.log('onResults fired! multiHandLandmarks:', res.multiHandLandmarks ? res.multiHandLandmarks.length : 0);
            });
            console.log('Sending blank canvas...');
            const canvas = document.getElementById('c');
            await hands.send({ image: canvas });
            console.log('hands.send succeeded!');
          } catch(e) {
            console.error('Hands initialization error:', e);
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
