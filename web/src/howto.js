// Shared helpers: sprite icons (Kenney Tiny Dungeon, CC0) and the "How to play" pop-up.
// frame numbers in tilemap_packed.png, 12 sprites per row, 16x16 each
export const SPRITE = { 'hero:T': 97, 'hero:A': 112, 'hero:H': 99, 'monster:G': 110, 'monster:A': 111, 'monster:H': 108, 'monster:B': 109 }
export const SWORD = 103

// one short role line per unit (from data/heroes.json and data/monsters.json)
export const ROLE = {
  'hero:T': 'Tough front-liner. Taunt pulls nearby monsters onto it.',
  'hero:A': 'Long range. Piercing Shot hits a whole line.',
  'hero:H': 'Heals another hero for 5 HP.',
  'monster:G': 'Fast, weak melee attacker.',
  'monster:B': 'Slow, very tough melee attacker.',
  'monster:A': 'Ranged attacker.',
  'monster:H': 'Heals other monsters.',
}

// a sprite from the sheet, drawn with CSS at k times its size (crisp pixels)
export function sprite(frame, k) {
  const s = 16 * k
  const x = (frame % 12) * s
  const y = Math.floor(frame / 12) * s
  return '<span class="spr" style="width:' + s + 'px;height:' + s + 'px;background-size:' + (192 * k) + 'px auto;background-position:-' + x + 'px -' + y + 'px"></span>'
}

// sprite on a team plate: blue circle = hero, coral rounded square = monster
export function unitIcon(side, label, k) {
  const frame = SPRITE[side + ':' + String(label)[0]]
  const inner = frame === undefined ? '<b>' + String(label)[0] + '</b>' : sprite(frame, k || 1.5)
  return '<span class="ico ' + side + '">' + inner + '</span>'
}

const TABS = [
  ['turn', 'Your turn'],
  ['danger', 'Danger'],
  ['skills', 'Skills'],
  ['terrain', 'Terrain'],
]

function arrowSvg() {
  return '<svg class="pic-arrow" viewBox="0 0 48 24" width="48" height="24"><line x1="3" y1="12" x2="36" y2="12" stroke="#f2c14e" stroke-width="3"/><polygon points="45,12 33,5 33,19" fill="#f2c14e"/></svg>'
}

function tabHtml(id) {
  if (id === 'turn') {
    return '<ol class="steps">' +
      '<li><b>Click a hero.</b> Its light-blue squares show where it can move.</li>' +
      '<li><b>Click a light-blue square</b> to move there.</li>' +
      '<li><b>Click a monster with a gold outline</b> to attack it. Or press Skill.</li>' +
      '<li><b>Press End turn.</b> Then the monsters act.</li>' +
      '</ol><p class="note">Each hero moves once, then acts once. You win when all monsters are dead. You have 30 rounds.</p>'
  }
  if (id === 'danger') {
    const row = (pic, text) => '<div class="hrow"><div class="hpic">' + pic + '</div><div>' + text + '</div></div>'
    return row('<span class="pic">' + unitIcon('hero', 'Tank', 2) + '<span class="pic-badge">-3</span></span>',
        '<b>Red number</b> on a hero: damage the monsters plan to do to it.') +
      row('<span class="ico monster red-out">' + sprite(SPRITE['monster:G'], 2) + '</span>',
        '<b>Red outline</b> on a monster: it will attack this turn.') +
      row('<span class="faint"></span>',
        '<b>Faint square</b>: where a monster will walk. It has the same color as that monster\'s outline.') +
      row(arrowSvg(),
        '<b>Arrow</b>: hover a monster, or press Arrows, to see where it goes. A thick red line shows its target.') +
      '<p class="note">Monsters act AFTER you press End turn. Use your turn to block, kill or dodge them.</p>'
  }
  if (id === 'skills') {
    const card = (side, name, skill, text) => '<div class="scard">' + unitIcon(side, name, 3) +
      '<div class="sname">' + name + '</div><div class="sskill">' + skill + '</div><div class="stext">' + text + '</div></div>'
    return '<div class="cards">' +
      card('hero', 'Tank', 'Taunt', 'Monsters within 3 steps must attack the Tank this turn.') +
      card('hero', 'Archer', 'Piercing Shot', 'Hits every monster in a straight line. Only 10 HP, so stay behind the Tank.') +
      card('hero', 'Healer', 'Heal', 'Gives another hero +5 HP, up to 3 tiles away. Cannot heal herself.') +
      '</div><p class="note">Select a hero, then press Skill. Skills cannot be undone.</p>'
  }
  // same shapes and colors as the tiles drawn on the board (main.js redraw)
  const tile = (inner) => '<svg width="48" height="48" viewBox="0 0 48 48" style="border-radius:6px;display:block">' + inner + '</svg>'
  const R = (x, y, w, h, rx, fill, op) => '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + rx + '" fill="' + fill + '"' + (op ? ' fill-opacity="' + op + '"' : '') + '/>'
  const C = (x, y, r, fill, op) => '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + fill + '"' + (op ? ' fill-opacity="' + op + '"' : '') + '/>'
  const cover = tile(R(1, 1, 46, 46, 5, '#24432f') +
    '<ellipse cx="24" cy="36" rx="17" ry="4.5" fill="#000" fill-opacity="0.25"/>' +
    C(15, 27, 10, '#2f7a4d') + C(33, 27, 10, '#2f7a4d') + C(24, 20, 12, '#3d9460') +
    C(21, 16, 5, '#bfeccf', 0.22) + C(33, 24, 3, '#bfeccf', 0.22))
  const lava = tile(R(1, 1, 46, 46, 5, '#7d2a10') + R(4, 4, 40, 40, 8, '#c4401a') + R(9, 9, 30, 30, 8, '#ff7a2f', 0.9) +
    R(15, 15, 18, 18, 6, '#ffd27a', 0.55) + C(21, 21, 3, '#fff0b0', 0.85))
  const wall = tile(R(1, 1, 46, 46, 5, '#2a3042') + R(1, 1, 46, 42, 5, '#58627c') +
    R(2, 15, 44, 2, 0, '#3b4359') + R(2, 29, 44, 2, 0, '#3b4359') + R(24, 3, 2, 12, 0, '#3b4359') + R(13, 17, 2, 12, 0, '#3b4359') +
    R(35, 17, 2, 12, 0, '#3b4359') + R(24, 31, 2, 12, 0, '#3b4359') + R(3, 3, 42, 4, 2, '#fff', 0.16))
  const sw = (pic, name, text) => '<div class="hrow"><div class="hpic">' + pic + '</div><div><b>' + name + '</b>: ' + text + '</div></div>'
  return sw(cover, 'Cover', 'a unit standing here takes 1 less damage from ranged attacks.') +
    sw(lava, 'Lava', 'a unit that ends its turn here takes 3 damage. Walking through is safe.') +
    sw(wall, 'Wall', 'blocks walking and line of sight.')
}

let openModal = null

function closeHowTo() {
  if (!openModal) return
  const m = openModal
  openModal = null
  document.removeEventListener('keydown', m.onKey)
  m.el.classList.remove('show')
  setTimeout(() => m.el.remove(), 160)
}

export function openHowTo(tab) {
  if (openModal) { closeHowTo() }
  const el = document.createElement('div')
  el.className = 'modal'
  el.innerHTML = '<div class="modal-box" role="dialog" aria-label="How to play">' +
    '<button class="modal-x" aria-label="Close">&times;</button>' +
    '<div class="modal-title">How to play</div>' +
    '<div class="tabs">' + TABS.map((t) => '<button class="tab" data-tab="' + t[0] + '">' + t[1] + '</button>').join('') + '</div>' +
    '<div class="tab-body"></div></div>'
  const body = el.querySelector('.tab-body')
  const show = (id) => {
    el.querySelectorAll('.tab').forEach((b) => b.classList.toggle('on', b.dataset.tab === id))
    body.innerHTML = tabHtml(id)
  }
  el.querySelectorAll('.tab').forEach((b) => { b.onclick = () => show(b.dataset.tab) })
  el.querySelector('.modal-x').onclick = closeHowTo
  el.addEventListener('mousedown', (e) => { if (e.target === el) closeHowTo() })
  const onKey = (e) => { if (e.key === 'Escape') closeHowTo() }
  document.addEventListener('keydown', onKey)
  document.body.appendChild(el)
  openModal = { el, onKey }
  show(tab || 'turn')
  requestAnimationFrame(() => el.classList.add('show'))
}
