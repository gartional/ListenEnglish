const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const out = path.join(__dirname, 'app');

const toCopy = [
  'index.html',
  'mock17-practice.html',
  'mock30-practice.html',
  'voa-practice.html',
  'content'
];

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    fs.readdirSync(src).forEach(name => {
      if (name === '.git' || name === '.mamba' || name === 'node_modules') return;
      copyRecursive(path.join(src, name), path.join(dest, name));
    });
  } else {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
  }
}

if (fs.existsSync(out)) fs.rmSync(out, { recursive: true });
fs.mkdirSync(out, { recursive: true });

toCopy.forEach(name => {
  const src = path.join(root, name);
  const dest = path.join(out, name);
  if (fs.existsSync(src)) copyRecursive(src, dest);
});

console.log('已复制到 desktop/app/');
