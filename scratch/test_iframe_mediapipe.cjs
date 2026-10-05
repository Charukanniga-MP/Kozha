const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  page.on('console', msg => console.log('[PAGE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('[PAGE ERROR]', err.message));

  console.log('Testing MediaPipe inside an isolated iframe...');

  await page.setContent(`
    <!DOCTYPE html>
    <html>
    <head>
      <script>
        // Main page has CWASA Module
        window.Module = { name: "CWASA", arguments: [] };
      </script>
    </head>
    <body>
      <h3>Main Page with CWASA Module</h3>
      <iframe id="trackerFrame" srcdoc="
        <!DOCTYPE html>
        <html>
        <head>
          <script src='https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js' crossorigin='anonymous'></script>
        </head>
        <body>
          <canvas id='c' width='320' height='240'></canvas>
          <script>
            let hands = null;
            function init() {
              console.log('Inside iframe: window.Module is', typeof window.Module);
              hands = new window.Hands({
                locateFile: (f) => 'https://cdn.jsdelivr.net/npm/@mediapipe/hands/' + f
              });
              hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 0,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
              });
              hands.onResults((res) => {
                console.log('IFRAME ONRESULTS! Hands detected:', res.multiHandLandmarks ? res.multiHandLandmarks.length : 0);
                if (window.parent && window.parent.onIframeResults) {
                  window.parent.onIframeResults(res);
                }
              });
              console.log('Iframe hands tracker initialized successfully!');
            }
            window.onload = init;

            window.processImage = async function(img) {
              if (hands) {
                await hands.send({ image: img });
              }
            };
          </script>
        </body>
        </html>
      " style="width:1px;height:1px;border:none;"></iframe>

      <script>
        window.onIframeResults = function(res) {
          console.log('MAIN PAGE RECEIVED RESULTS! Hands:', res.multiHandLandmarks ? res.multiHandLandmarks.length : 0);
        };

        async function runTest() {
          await new Promise(r => setTimeout(r, 4000));
          const frame = document.getElementById('trackerFrame');
          const canvas = document.createElement('canvas');
          canvas.width = 320;
          canvas.height = 240;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#ffccaa';
          ctx.fillRect(100, 50, 100, 120);

          console.log('Sending canvas to iframe...');
          await frame.contentWindow.processImage(canvas);
          console.log('Iframe processImage finished successfully!');
        }
        runTest();
      </script>
    </body>
    </html>
  `);

  await new Promise(r => setTimeout(r, 10000));
  await browser.close();
})();
