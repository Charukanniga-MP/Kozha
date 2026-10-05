const https = require('https');

const files = [
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js',
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands_solution_packed_assets_loader.js',
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands_solution_simd_wasm_bin.js',
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands_solution_simd_wasm_bin.wasm',
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.binarypb'
];

files.forEach(url => {
  https.get(url, (res) => {
    console.log(res.statusCode, url, 'size:', res.headers['content-length']);
  }).on('error', (e) => {
    console.error('ERROR for', url, e.message);
  });
});
