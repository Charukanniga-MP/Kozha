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

  console.log('Connecting call...');
  await page.evaluate(() => {
    activeCallRemote = { id: 'c2', name: 'Keerthi', phone: '9834567290' };
    connectActiveCallSession();
  });

  console.log('Waiting 8s for Luna and Anna meshes to bind...');
  await new Promise(r => setTimeout(r, 8000));

  console.log('Testing Person A (Luna av0) signing "hello"...');
  await page.evaluate(() => {
    handleLocalSpokenText('hello');
  });

  await new Promise(r => setTimeout(r, 2000));

  console.log('Testing Person B (Anna av1) signing "where are you"...');
  await page.evaluate(() => {
    handleRemoteSpokenText('Keerthi', 'where are you');
  });

  await new Promise(r => setTimeout(r, 3000));

  const testReport = await page.evaluate(() => {
    const avs = window.SignAvatarEngine ? window.SignAvatarEngine.avatars : null;
    const box1Cap = document.getElementById('box1CaptionText')?.textContent;
    const box2Cap = document.getElementById('box2CaptionText')?.textContent;
    const box1Badge = document.getElementById('box1StatusBadge')?.textContent;
    const box2Badge = document.getElementById('box2StatusBadge')?.textContent;

    return {
      av0Id: avs ? avs[0].id : null,
      av0State: avs ? avs[0].state : null,
      av0LastText: avs ? avs[0].lastText : null,
      box1Cap,
      box1Badge,

      av1Id: avs ? avs[1].id : null,
      av1State: avs ? avs[1].state : null,
      av1LastText: avs ? avs[1].lastText : null,
      box2Cap,
      box2Badge
    };
  });

  console.log('Test Report:', JSON.stringify(testReport, null, 2));

  await page.screenshot({ path: 'scratch/test_sign_both_sides.png', fullPage: true });
  console.log('Screenshot saved to scratch/test_sign_both_sides.png');

  await browser.close();
})();
