// Unit test for sign gesture classifier geometries
const fs = require('fs');

// Extract the classify functions from public/dellar-lab.html
const html = fs.readFileSync('public/dellar-lab.html', 'utf8');

// Helper to construct synthetic 21 MediaPipe hand points
function createHandLandmarks({
  thumb = 'folded', // 'up', 'down', 'out', 'folded', 'touchIndex', 'touchPinky'
  index = 'curled', // 'ext', 'curled', 'hooked'
  middle = 'curled', // 'ext', 'curled'
  ring = 'curled', // 'ext', 'curled'
  pinky = 'curled', // 'ext', 'curled'
  spreadV = false,
  spreadTogether = false
}) {
  const pts = [];
  const wrist = { x: 300, y: 350 };
  pts[0] = wrist;

  const palmSize = 100; // wrist to middle MCP = 100px

  // MCPs (5, 9, 13, 17)
  pts[5] = { x: 260, y: 250 }; // index MCP
  pts[9] = { x: 300, y: 250 }; // middle MCP
  pts[13] = { x: 340, y: 255 }; // ring MCP
  pts[17] = { x: 375, y: 265 }; // pinky MCP

  // Finger maker
  function setFinger(mcpIdx, tipIdx, state, xOffset = 0) {
    const mcp = pts[mcpIdx];
    if (state === 'ext') {
      pts[mcpIdx + 1] = { x: mcp.x + xOffset * 0.3, y: mcp.y - 30 }; // PIP
      pts[mcpIdx + 2] = { x: mcp.x + xOffset * 0.6, y: mcp.y - 60 }; // DIP
      pts[tipIdx] = { x: mcp.x + xOffset, y: mcp.y - 95 }; // TIP far up
    } else if (state === 'hooked') {
      pts[mcpIdx + 1] = { x: mcp.x, y: mcp.y - 35 }; // PIP up
      pts[mcpIdx + 2] = { x: mcp.x + 15, y: mcp.y - 20 }; // DIP bent
      pts[tipIdx] = { x: mcp.x + 20, y: mcp.y }; // TIP curled down
    } else { // curled
      pts[mcpIdx + 1] = { x: mcp.x, y: mcp.y - 25 }; // PIP
      pts[mcpIdx + 2] = { x: mcp.x, y: mcp.y - 10 }; // DIP
      pts[tipIdx] = { x: mcp.x, y: mcp.y + 15 }; // TIP folded into palm
    }
  }

  // Index
  setFinger(5, 8, index, spreadV ? -20 : 0);

  // Middle
  setFinger(9, 12, middle, spreadV ? 20 : 0);

  // Ring
  setFinger(13, 16, ring);

  // Pinky
  setFinger(17, 20, pinky, 15);

  // Thumb (1, 2, 3, 4)
  pts[1] = { x: 270, y: 320 }; // CMC
  pts[2] = { x: 240, y: 295 }; // MCP

  if (thumb === 'up') {
    pts[3] = { x: 230, y: 260 }; // IP
    pts[4] = { x: 225, y: 215 }; // TIP pointing straight up!
  } else if (thumb === 'down') {
    pts[3] = { x: 230, y: 340 }; // IP
    pts[4] = { x: 225, y: 385 }; // TIP pointing straight down!
  } else if (thumb === 'out') {
    pts[3] = { x: 200, y: 285 }; // IP
    pts[4] = { x: 160, y: 280 }; // TIP pointing way out left
  } else if (thumb === 'touchIndex') {
    pts[3] = { x: 245, y: 230 };
    pts[4] = { x: pts[8].x - 5, y: pts[8].y + 5 }; // touches index tip
  } else if (thumb === 'touchPinky') {
    pts[3] = { x: 300, y: 260 };
    pts[4] = { x: pts[20].x - 5, y: pts[20].y + 5 }; // touches pinky tip
  } else { // folded across palm
    pts[3] = { x: 260, y: 275 };
    pts[4] = { x: 285, y: 265 };
  }

  return pts;
}

// Evaluate in sandboxed context
const vm = require('vm');
const context = { console, Math, Date, setTimeout, clearTimeout };
vm.createContext(context);

// Extract analyzeHandShape and classifyGestureFeatures from html
const func1 = html.match(/function analyzeHandShape[\s\S]*?\n    }/)[0];
const func2 = html.match(/function classifyGestureFeatures[\s\S]*?\n    }/)[0];
vm.runInContext(func1 + '\n' + func2 + '\nthis.analyzeHandShape = analyzeHandShape;\nthis.classifyGestureFeatures = classifyGestureFeatures;', context);

const tests = [
  { name: '1 Finger (Number 1 / Point)', config: { index: 'ext', thumb: 'folded', middle: 'curled', ring: 'curled', pinky: 'curled' }, expected: '1 (One)' },
  { name: '2 Fingers (Peace / 2)', config: { index: 'ext', middle: 'ext', spreadV: true, thumb: 'folded', ring: 'curled', pinky: 'curled' }, expected: 'Peace (✌️)' },
  { name: '3 Fingers (Number 3)', config: { index: 'ext', middle: 'ext', ring: 'ext', thumb: 'folded', pinky: 'curled' }, expected: '3 (Three)' },
  { name: '4 Fingers (Number 4)', config: { index: 'ext', middle: 'ext', ring: 'ext', pinky: 'ext', thumb: 'folded' }, expected: '4 (Four)' },
  { name: '5 Fingers Open (Hello)', config: { index: 'ext', middle: 'ext', ring: 'ext', pinky: 'ext', thumb: 'out' }, expected: 'Hello' },
  { name: 'Thumbs Up (Good)', config: { index: 'curled', middle: 'curled', ring: 'curled', pinky: 'curled', thumb: 'up' }, expected: 'Good (👍)' },
  { name: 'Thumbs Down (Bad)', config: { index: 'curled', middle: 'curled', ring: 'curled', pinky: 'curled', thumb: 'down' }, expected: 'Bad (👎)' },
  { name: 'Welcome Gesture', config: { index: 'ext', pinky: 'ext', thumb: 'out', middle: 'curled', ring: 'curled' }, expected: 'Welcome' },
  { name: 'Call Me (🤙)', config: { index: 'curled', pinky: 'ext', thumb: 'out', middle: 'curled', ring: 'curled' }, expected: 'Call Me (🤙)' },
  { name: 'Letter L', config: { index: 'ext', thumb: 'out', middle: 'curled', ring: 'curled', pinky: 'curled' }, expected: 'Letter L' },
  { name: 'Letter I', config: { pinky: 'ext', thumb: 'folded', index: 'curled', middle: 'curled', ring: 'curled' }, expected: 'Letter I' },
  { name: 'OK Sign (👌)', config: { thumb: 'touchIndex', index: 'curled', middle: 'ext', ring: 'ext', pinky: 'ext' }, expected: 'OK (👌)' },
  { name: 'Fist (Power)', config: { index: 'curled', middle: 'curled', ring: 'curled', pinky: 'curled', thumb: 'folded' }, expected: 'Fist (Power)' }
];

console.log('--- RUNNING SIGN CLASSIFIER GEOMETRIC TESTS ---');
let passed = 0;
tests.forEach(t => {
  const pts = createHandLandmarks(t.config);
  const feat = context.analyzeHandShape(pts);
  const res = context.classifyGestureFeatures(feat, 'all');
  const matched = res && res.text === t.expected;
  if (matched) {
    console.log(`[PASS] ${t.name} -> "${res.text}" (Speech: "${res.speech}", Category: "${res.category}")`);
    passed++;
  } else {
    console.error(`[FAIL] ${t.name} -> Expected "${t.expected}", got:`, res ? `"${res.text}"` : 'null');
  }
});

console.log(`\nResults: ${passed} / ${tests.length} tests passed!`);
module.exports = { createHandLandmarks };
