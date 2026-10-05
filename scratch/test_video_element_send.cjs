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

    // Wait until MediaPipe is ready
    let attempts = 0;
    while (!iframe.contentWindow.isHandsReady && attempts < 40) {
      await new Promise(r => setTimeout(r, 100));
      attempts++;
    }

    // Create a video element with a canvas stream
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#222';
    ctx.fillRect(0, 0, 640, 480);
    // Draw a hand shape
    ctx.fillStyle = '#ffccaa';
    ctx.beginPath();
    ctx.arc(320, 240, 50, 0, Math.PI * 2);
    ctx.fill();

    const stream = canvas.captureStream(30);
    const video = document.createElement('video');
    video.srcObject = stream;
    video.autoplay = true;
    video.muted = true;
    video.playsInline = true;
    document.body.appendChild(video);
    await video.play();

    let gotCallback = false;
    let landmarkCount = 0;
    window.onHandResults = function(res) {
      gotCallback = true;
      landmarkCount = (res.multiHandLandmarks && res.multiHandLandmarks.length) || 0;
    };

    let sendErr = null;
    try {
      await iframe.contentWindow.processVideoFrame(video);
    } catch (e) {
      sendErr = e.message;
    }

    return {
      gotCallback,
      landmarkCount,
      sendErr,
      videoReadyState: video.readyState,
      videoWidth: video.videoWidth
    };
  });

  console.log('Test Video Element Send Result:', JSON.stringify(testRes, null, 2));
  await browser.close();
})();
