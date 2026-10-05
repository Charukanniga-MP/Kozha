const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('public/dellar-lab.html', 'utf8');
const func1 = html.match(/function analyzeHandShape[\s\S]*?\n    }/)[0];
const func2 = html.match(/function classifyGestureFeatures[\s\S]*?\n    }/)[0];

const context = { console, Math, Date, setTimeout, clearTimeout };
vm.createContext(context);
vm.runInContext(func1 + '\n' + func2 + '\nthis.analyzeHandShape = analyzeHandShape;\nthis.classifyGestureFeatures = classifyGestureFeatures;', context);

// Test numbers mode
const testSignClassifier = require('./test_sign_classifier.cjs');

console.log('--- TESTING NUMBERS SPECIFIC MODE ---');
// Let's create an inline helper for landmarks
function createHand(config) {
  const pts = [];
  pts[0] = { x: 300, y: 350 };
  pts[5] = { x: 260, y: 250 };
  pts[9] = { x: 300, y: 250 };
  pts[13] = { x: 340, y: 255 };
  pts[17] = { x: 375, y: 265 };

  function setF(mcpIdx, tipIdx, ext) {
    const mcp = pts[mcpIdx];
    if (ext) {
      pts[mcpIdx + 1] = { x: mcp.x, y: mcp.y - 30 };
      pts[mcpIdx + 2] = { x: mcp.x, y: mcp.y - 60 };
      pts[tipIdx] = { x: mcp.x, y: mcp.y - 95 };
    } else {
      pts[mcpIdx + 1] = { x: mcp.x, y: mcp.y - 25 };
      pts[mcpIdx + 2] = { x: mcp.x, y: mcp.y - 10 };
      pts[tipIdx] = { x: mcp.x, y: mcp.y + 15 };
    }
  }

  setF(5, 8, config.index);
  setF(9, 12, config.middle);
  setF(13, 16, config.ring);
  setF(17, 20, config.pinky);

  pts[1] = { x: 270, y: 320 };
  pts[2] = { x: 240, y: 295 };
  if (config.thumb === 'out') {
    pts[3] = { x: 200, y: 285 };
    pts[4] = { x: 160, y: 280 };
  } else if (config.thumb === 'up') {
    pts[3] = { x: 230, y: 260 };
    pts[4] = { x: 225, y: 215 };
  } else {
    pts[3] = { x: 260, y: 275 };
    pts[4] = { x: 285, y: 265 };
  }
  return pts;
}

// 1. Numbers mode:
const f1 = createHand({ index: true, middle: false, ring: false, pinky: false, thumb: 'folded' });
const r1 = context.classifyGestureFeatures(context.analyzeHandShape(f1), 'numbers');
console.log('Numbers mode 1 finger:', r1?.text, '(expected: "1 (One)")');

const f2 = createHand({ index: true, middle: true, ring: false, pinky: false, thumb: 'folded' });
const r2 = context.classifyGestureFeatures(context.analyzeHandShape(f2), 'numbers');
console.log('Numbers mode 2 fingers:', r2?.text, '(expected: "2 (Two)")');

const f5 = createHand({ index: true, middle: true, ring: true, pinky: true, thumb: 'out' });
const r5 = context.classifyGestureFeatures(context.analyzeHandShape(f5), 'numbers');
console.log('Numbers mode 5 fingers:', r5?.text, '(expected: "5 (Five)")');

const f10 = createHand({ index: false, middle: false, ring: false, pinky: false, thumb: 'up' });
const r10 = context.classifyGestureFeatures(context.analyzeHandShape(f10), 'numbers');
console.log('Numbers mode thumb up:', r10?.text, '(expected: "10 (Ten)")');

// 2. Alphabets mode:
console.log('\n--- TESTING ALPHABETS SPECIFIC MODE ---');
const fa = createHand({ index: false, middle: false, ring: false, pinky: false, thumb: 'up' });
const ra = context.classifyGestureFeatures(context.analyzeHandShape(fa), 'alphabets');
console.log('Alphabets mode A:', ra?.text, '(expected: "Letter A")');

const fb = createHand({ index: true, middle: true, ring: true, pinky: true, thumb: 'folded' });
const rb = context.classifyGestureFeatures(context.analyzeHandShape(fb), 'alphabets');
console.log('Alphabets mode B:', rb?.text, '(expected: "Letter B")');

const fl = createHand({ index: true, middle: false, ring: false, pinky: false, thumb: 'out' });
const rl = context.classifyGestureFeatures(context.analyzeHandShape(fl), 'alphabets');
console.log('Alphabets mode L:', rl?.text, '(expected: "Letter L")');

const fy = createHand({ index: false, middle: false, ring: false, pinky: true, thumb: 'out' });
const ry = context.classifyGestureFeatures(context.analyzeHandShape(fy), 'alphabets');
console.log('Alphabets mode Y:', ry?.text, '(expected: "Letter Y")');
