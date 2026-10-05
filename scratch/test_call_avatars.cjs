const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  page.on('console', msg => console.log('[PAGE]', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('[PAGE ERROR]', err.message));

  console.log('Opening http://127.0.0.1:8000/call.html ...');
  await page.goto('http://127.0.0.1:8000/call.html', { waitUntil: 'networkidle2' });

  console.log('Triggering call connect...');
  await page.evaluate(() => {
    // Simulate answering or connecting call
    activeCallRemote = { id: 'c2', name: 'Keerthi', phone: '9834567290' };
    connectActiveCallSession();
  });

  console.log('Waiting 10s for CWASA avatars (Luna & Anna) to load...');
  await new Promise(r => setTimeout(r, 10000));

  const status = await page.evaluate(() => {
    const av0 = document.querySelector('.CWASAAvatar.av0');
    const av1 = document.querySelector('.CWASAAvatar.av1');
    const canvas0 = av0 ? av0.querySelector('canvas') : null;
    const canvas1 = av1 ? av1.querySelector('canvas') : null;

    let cur0 = 'n/a', cur1 = 'n/a';
    try {
      if (window.CWASA && typeof window.CWASA.getCurAv === 'function') {
        cur0 = window.CWASA.getCurAv(0);
        cur1 = window.CWASA.getCurAv(1);
      }
    } catch (e) {
      cur0 = e.message;
    }

    const engineAvs = window.SignAvatarEngine ? window.SignAvatarEngine.avatars : null;

    return {
      canvas0Exists: !!canvas0,
      canvas1Exists: !!canvas1,
      canvas0Width: canvas0 ? canvas0.width : 0,
      canvas1Width: canvas1 ? canvas1.width : 0,
      cwasaCurAv0: cur0,
      cwasaCurAv1: cur1,
      engineAv0: engineAvs ? engineAvs[0] : null,
      engineAv1: engineAvs ? engineAvs[1] : null
    };
  });

  console.log('Call page avatar test result:', JSON.stringify(status, null, 2));

  // Take a screenshot of the call page to verify Luna and Anna visually
  await page.screenshot({ path: 'scratch/call_luna_anna_verify.png' });
  console.log('Screenshot saved to scratch/call_luna_anna_verify.png');

  await browser.close();
})();
