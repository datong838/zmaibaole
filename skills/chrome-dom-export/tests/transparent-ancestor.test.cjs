// Regression: invisible date-picker descendants must not obstruct a review crop.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../extension/region-proof.js'), 'utf8');

function fixture(count = 1) {
  const make = (tag, text, box) => ({
    tagName: tag, innerText: text, children: [], parentElement: null,
    style: {display: 'block', visibility: 'visible', opacity: '1', transform: 'none', backgroundColor: 'rgb(255, 255, 255)', backgroundImage: 'none', pointerEvents: 'auto', position: 'static'},
    getBoundingClientRect() {return {...box, width: box.right-box.left, height: box.bottom-box.top};},
    getAttribute() {return null;}, getAnimations() {return [];}, matches() {return false;},
    contains(node) {return node === this || this.children.some(child => child.contains(node));},
    querySelectorAll() {return this.children;}
  });
  const card = make('DIV', 'review', {left: 200, top: 300, right: 1200, bottom: 500});
  const action = make('BUTTON', '投诉', {left: 1050, top: 350, right: 1150, bottom: 390});
  action.getAttribute = name => name === 'class' ? 'button-vhqEd7' : null;
  card.children = [action]; action.parentElement = card;
  const parent = make('DIV', 'date picker', {left: 500, top: 250, right: 700, bottom: 450});
  parent.style.opacity = '0';
  for (let i = 0; i < count; i++) {
    const child = make('DIV', 'date option', {left: 520, top: 350, right: 600, bottom: 400});
    child.parentElement = parent; parent.children.push(child);
  }
  const base = {scope: {tabId: 1, windowId: 2, groupid: '123'}, url: 'https://life.douyin.com/p/life_comment/management?groupid=123', reviews: [{card: '#card', card_visible: true}]};
  let reads = 0, after = () => {};
  const context = {
    document: {documentElement: {clientWidth: 1400, clientHeight: 800}, querySelectorAll: q => q === '.commentItem-jrXo5p' ? [card] : [card, action, parent, ...parent.children]},
    devicePixelRatio: 2, visualViewport: {scale: 1}, getComputedStyle: node => node.style,
    __localReviewProof: {proof: async () => {if (++reads === 2) after(); return structuredClone(base);}}
  };
  vm.createContext(context); vm.runInContext(source, context);
  const command = {op: 'dom-region-proof', purpose: 'evidence-crop-only', tabId: 1, windowId: 2, groupid: '123', selectors: ['#card'], channel: 'local-dom-export-v1', base: {op: 'review-viewport-proof', tabId: 1, windowId: 2, groupid: '123'}};
  return {parent, card, after(fn) {after = fn;}, run: () => context.__localRegionProof.proof(command, () => card, () => ({}))};
}

test('151 invisible descendants do not block crop; every descendant remains checked', async () => {
  assert.equal((await fixture(151).run()).external_painted_overlap, false);
  const changed = fixture(151); changed.after(() => {changed.parent.children[120].parentElement = null;});
  await assert.rejects(changed.run(), /region-transparent-ancestor-changed/);
});
test('visible and animating overlays still block; selected hidden review remains rejected', async () => {
  for (const opacity of ['1', '.001']) {
    const f = fixture(); f.parent.style.opacity = opacity;
    await assert.rejects(f.run(), /region-painted-external-overlap/);
  }
  const moving = fixture(); moving.parent.getAnimations = () => [{playState: 'running'}];
  await assert.rejects(moving.run(), /region-painted-external-overlap/);
  const selected = fixture(); selected.card.parentElement = selected.parent;
  await assert.rejects(selected.run(), /region-element-hidden/);
});
