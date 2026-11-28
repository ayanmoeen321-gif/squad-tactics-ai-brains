import Phaser from 'phaser'
import './style.css'

const CELL = 48
const FLOOR = { '.': 0x1f2533, '#': 0x4b556d, 'C': 0x2f6a4c, 'L': 0xc4552b }
const FLOOR_B = 0x232a3a
const HERO = 0x4aa3df
const MON = 0xe4604f
const GOLD = 0xf2c14e
const FONT = 'Segoe UI, system-ui, -apple-system, Arial, sans-serif'
const level = Number(new URLSearchParams(location.search).get('level') || 1)
const seed = Number(new URLSearchParams(location.search).get('seed') || 0)
const brain = new URLSearchParams(location.search).get('brain') || 'scripted'

let S = null
let selected = null
let mode = null
let scene = null

const msg = document.createElement('div')
msg.className = 'msg'
const bar = document.createElement('div')
bar.className = 'bar'

async function api(path, body) {
  const r = await fetch('/api' + path, {
    method: path === '/state' ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : '{}',
  })
  const j = await r.json()
  if (!r.ok) throw new Error(j.detail || 'error')
  return j
}

async function act(path, body) {
  try {
    const before = S ? S.round : 1; const j = await api(path, body)
    S = j.state || j; if (path === '/new') { logLines.length = 0; logDiv.innerHTML = ''; for (const k in tutDone) delete tutDone[k] } else { tutDone[path] = true }; if (j.events) logEvents(j.events, path, before)
    msg.textContent = ''
  } catch (e) {
    msg.textContent = e.message
  }
  mode = null
  redraw()
}

const brainDiv = document.createElement('div')
brainDiv.className = 'brain'
brainDiv.style.display = 'none'
let hoverId = null
let showArrows = false
let resultHidden = false
const resultDiv = document.createElement('div')
resultDiv.style.cssText = 'position:absolute;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,0.6);z-index:10'
document.body.appendChild(resultDiv)

function showResult() {
  if (resultHidden || resultDiv.style.display === 'flex') return
  const cv = document.querySelector('canvas')
  if (!cv) return
  const r = cv.getBoundingClientRect()
  resultDiv.style.left = (r.left + window.scrollX) + 'px'
  resultDiv.style.top = (r.top + window.scrollY) + 'px'
  resultDiv.style.width = r.width + 'px'
  resultDiv.style.height = r.height + 'px'
  const win = S.result === 'win'
  const alive = S.units.filter((u) => u.side === 'hero' && u.alive)
  const left = S.units.filter((u) => u.side === 'monster' && u.alive)
  const why = win ? 'All monsters are dead.' : (alive.length === 0 ? 'All your heroes are dead.' : 'The 30 rounds ran out with monsters still alive.')
  const box = document.createElement('div')
  box.className = 'result-box ' + (win ? 'win' : 'lose')
  box.innerHTML = '<div class="result-title">' + (win ? 'Victory!' : 'Defeat') + '</div>' +
    why + '<br>Ended in round ' + Math.min(S.round, 30) + '<br>Heroes alive: ' +
    (alive.map((h) => h.label + ' ' + h.hp + '/' + h.max_hp).join(', ') || 'none') +
    '<br>Monsters left: ' + left.length + '<br>'
  const mk = (label, fn) => {
    const b = document.createElement('button')
    b.textContent = label
    b.className = 'btn'
    b.style.margin = '12px 6px 0 6px'
    b.onclick = fn
    box.appendChild(b)
  }
  mk('Play again', () => { selected = null; act('/new', { level, seed, brain }) })
  if (win && level < 3) mk('Next level', () => { location.href = '/?level=' + (level + 1) + '&brain=' + brain })
  mk('View board', () => { resultHidden = true; resultDiv.style.display = 'none' })
  mk('Menu', () => { location.href = '/' })
  resultDiv.innerHTML = ''
  resultDiv.appendChild(box)
  resultDiv.style.display = 'flex'
}

const logLines = []
const logDiv = document.createElement('div')
logDiv.className = 'panel log'

function logEvents(events, path, round) {
  const R = 'R' + round + ' '
  const side = (id) => id === 'tank' || id === 'archer' || id === 'healer' ? '[HERO] ' : '[MONSTER] '
  const n = (id) => { const u = S.units.find((v) => v.id === id); return u ? u.label : id }
  if (path === '/end_turn') logLines.push(R + '--- Monsters act ---')
  events.forEach((e) => {
    const tag = e.taunted ? ' (taunted)' : ''
    if (e.type === 'attack' || e.type === 'piercing_shot') {
      const what = e.type === 'attack' ? 'hit' : 'pierced'
      logLines.push(R + side(e.attacker) + n(e.attacker) + ' ' + what + ' ' + n(e.target) + ' for ' + e.damage + (e.killed ? ' - dead' : '') + tag)
    } else if (e.type === 'heal') {
      logLines.push(R + side(e.healer) + n(e.healer) + ' healed ' + n(e.target) + ' +' + e.restored)
    } else if (e.type === 'lava') {
      logLines.push(R + n(e.target) + ' burned by lava for ' + e.damage + (e.killed ? ' - dead' : ''))
    } else if (e.type === 'taunt') {
      logLines.push(R + side(e.unit) + n(e.unit) + ' used Taunt on ' + (e.affected ? e.affected.length : 0) + ' monster(s)')
    }
  })
  if (logLines.length > 40) logLines.splice(0, logLines.length - 40)
  logDiv.innerHTML = '<b>Log (newest first):</b><br>' + logLines.slice(-14).reverse().join('<br>')
}

function button(label, fn, cls) {
  const b = document.createElement('button')
  b.textContent = label
  b.className = 'btn' + (cls ? ' ' + cls : '')
  b.onclick = fn
  bar.appendChild(b)
}

button('Wait', () => selected && act('/wait', { hero: selected }))
button('Undo move', () => selected && act('/undo', { hero: selected }))
button('Skill', () => {
  if (!selected) return
  if (selected === 'tank') act('/taunt', { hero: 'tank' })
  else if (selected === 'archer') { mode = 'shot'; msg.textContent = 'Piercing Shot: click a direction' }
  else if (selected === 'healer' && S.heroes.healer.can_heal.length === 0) { msg.textContent = 'No hurt hero in range to heal.' }
  else if (selected === 'healer') { mode = 'heal'; msg.textContent = 'Heal: click a hurt hero' }
})
button('End turn', () => { selected = null; act('/end_turn') }, 'primary')
button('Menu', () => { location.href = '/' })
button('Restart', () => { selected = null; act('/new', { level, seed, brain }) })
button('Arrows', () => { showArrows = !showArrows; redraw() })
button('Help', () => {
  if (tipsDiv.style.display === 'block') { tipsDiv.style.display = 'none'; return }
  const tips = {
    tank: '<b>Tank:</b> tough, hits adjacent only. Skill = Taunt: monsters within 3 steps must attack the Tank this turn. Use it when the Tank stands where you want the fight.',
    archer: '<b>Archer:</b> hits from 4 tiles away, needs a clear line. Skill = Piercing Shot: hits every monster in a straight line. Weak (10 HP), so keep it behind the Tank.',
    healer: '<b>Healer:</b> weak attack. Skill = Heal: +5 HP to another hero within 3 tiles. Cannot heal herself.',
  }
  const basics = '<b>Tips:</b> Each hero moves once, then acts once. A red number on a hero is the damage planned against it. Red-outlined monsters will attack. A faint square is where a monster will walk. Hover a monster, or press Arrows, to see its arrow. All act after End turn, so block, kill or dodge them. Green = cover (ranged hits do 1 less). Orange = lava (3 damage if you end there). Click a hero to get tips for it.'
  window.refreshTips = () => { tipsDiv.innerHTML = (selected && tips[selected]) ? tips[selected] : basics }; window.refreshTips()
  tipsDiv.style.display = 'block'
})

const card = document.createElement('div')
card.className = 'panel card'
card.textContent = 'Hover a unit to see its stats.'

function onHover(x, y) {
  if (!S) return
  const u = unitAt(Math.floor(y / CELL), Math.floor(x / CELL))
  const hid = u && u.side === 'monster' ? u.id : null
  if (hid !== hoverId) { hoverId = hid; redraw() }
  if (!u) { card.textContent = 'Hover a unit to see its stats.'; return }
  const lines = ['<b>' + u.label + '</b> (' + u.side + ')',
    'HP ' + u.hp + '/' + u.max_hp + ' | Move ' + u.move + ' | Range ' + u.range + ' | Damage ' + u.damage]
  if (u.skill) lines.push('Skill: ' + u.skill + (u.cooldown > 0 ? ' (ready in ' + u.cooldown + ' rounds)' : ' (ready)'))
  const p = S.plans.find((q) => q.monster === u.id)
  if (p) {
    const tg = p.target ? S.units.find((v) => v.id === p.target) : null
    const stay = p.dest[0] === u.pos[0] && p.dest[1] === u.pos[1]
    lines.push('Plan: ' + p.kind + (tg ? ' ' + tg.label : '') + (stay ? ' (stays where it is)' : ' (moves to the marked square)'))
  }
  card.innerHTML = lines.join('<br>')
}

function unitAt(r, c) {
  return S.units.find((u) => u.alive && u.pos[0] === r && u.pos[1] === c)
}

function onClick(x, y) {
  if (!S || S.result) return
  const r = Math.floor(y / CELL)
  const c = Math.floor(x / CELL)
  if (r < 0 || c < 0 || r > 11 || c > 11) return
  const info = selected ? S.heroes[selected] : null
  const u = unitAt(r, c)
  if (mode === 'shot' && selected) {
    const a = S.units.find((v) => v.id === selected).pos
    const dr = r - a[0], dc = c - a[1]
    const dir = Math.abs(dr) >= Math.abs(dc) ? (dr < 0 ? 'up' : 'down') : (dc < 0 ? 'left' : 'right')
    return act('/piercing_shot', { hero: selected, direction: dir })
  }
  if (mode === 'heal' && selected) {
    if (u && u.side === 'hero') return act('/heal', { hero: selected, target: u.id })
    mode = null; msg.textContent = ''
    return redraw()
  }
  if (u && u.side === 'hero') { selected = u.id; msg.textContent = ''; return redraw() }
  if (u && u.side === 'monster' && info && info.can_attack.includes(u.id)) {
    return act('/attack', { hero: selected, target: u.id })
  }
  if (info && info.reachable.some((t) => t[0] === r && t[1] === c)) {
    return act('/move', { hero: selected, to: [r, c] })
  }
  selected = null
  redraw()
}

function mid(p) { return [p[1] * CELL + CELL / 2, p[0] * CELL + CELL / 2] }

const tutorial = new URLSearchParams(location.search).get('tutorial') === '1'
const tutDiv = document.createElement('div')
tutDiv.className = 'tut'
tutDiv.style.display = tutorial ? 'block' : 'none'

const tipsDiv = document.createElement('div')
tipsDiv.className = 'tips'
tipsDiv.style.display = 'none'

const tutDone = {}

function updateTut() {
  if (!tutorial || !S) return
  const left = S.units.filter((u) => u.alive && u.side === 'monster').length
  const hurt = S.units.some((u) => u.alive && u.side === 'hero' && u.hp < u.max_hp)
  let t
  if (S.result === 'win') t = "You won! You know the basics. Press Next level to try Level 1."
  else if (S.result) t = "You lost, and that is fine. Press Restart and try again."
  else if (!tutDone['/move'] && !selected) t = "Step 1: click your Tank (the blue T)."
  else if (!tutDone['/move']) t = "Step 2: light-blue squares show where the Tank can move. Click one toward the red goblins."
  else if (!tutDone['/end_turn']) t = "Step 3: a red number on a hero is the damage the goblins plan to do to it. A red outline marks a goblin that will attack. Faint squares show where goblins will walk; hover a goblin or press Arrows to see its arrow. They act AFTER you press End turn. Click End turn now."
  else if (!tutDone['/attack']) t = "Step 4: the goblins came to you. Click a hero, then click a goblin with a yellow outline to attack it."
  else if (!tutDone['/taunt'] && left >= 1) t = "Step 5: Taunt. Click the Tank, press Skill. Goblins near the Tank must attack it this turn. Then click End turn or use other heroes."
  else if (!tutDone['/piercing_shot'] && left >= 1) t = "Step 6: Piercing Shot. Click the Archer, press Skill, then click in the direction of the goblins. It hits every monster in that line. Works best when goblins line up."
  else if (!tutDone['/heal'] && left >= 1 && hurt) t = "Step 7: a hero is hurt. Click the Healer, press Skill, then click the hurt hero to heal 5 HP."
  else if (left >= 1) t = "Tips: orange squares are lava (3 damage if you end your turn on one). Green squares are cover (ranged hits do 1 less). Now defeat the goblins."
  else t = "Almost done. Finish the last goblin."
  tutDiv.textContent = t
}
function redraw() {
  if (S && S.brain_stats) { const b = S.brain_stats; brainDiv.style.display = 'block'; brainDiv.style.color = b.fallbacks > 0 ? '#ff8080' : '#9fd'; brainDiv.textContent = 'Laya: ' + b.decisions + ' decisions, ' + b.fallbacks + ' fell back to scripted, ' + b.avg_seconds + ' s average, ' + b.worst_seconds + ' s slowest' } else { brainDiv.style.display = 'none' }
  if (window.refreshTips) window.refreshTips()
  if (S && !S.result) { resultDiv.style.display = 'none'; resultHidden = false }
  if (!scene || !S) return
  updateTut()
  scene.children.removeAll(true)
  const gt = scene.add.graphics()
  S.grid.forEach((row, r) => {
    [...row].forEach((ch, c) => {
      const base = ch === '.' ? ((r + c) % 2 ? FLOOR_B : FLOOR['.']) : (FLOOR[ch] || FLOOR['.'])
      const tx = c * CELL + 1, ty = r * CELL + 1
      gt.fillStyle(base, 1)
      gt.fillRoundedRect(tx, ty, CELL - 2, CELL - 2, 5)
      if (ch === '#') { gt.fillStyle(0xffffff, 0.14); gt.fillRoundedRect(tx + 2, ty + 2, CELL - 6, 9, 4) }
      if (ch === 'C') { gt.fillStyle(0xffffff, 0.10); gt.fillRoundedRect(tx + 9, ty + 9, CELL - 20, CELL - 20, 6) }
      if (ch === 'L') { gt.fillStyle(0xffd27a, 0.30); gt.fillRoundedRect(tx + 8, ty + 8, CELL - 18, CELL - 18, 8) }
    })
  })
  const g = scene.add.graphics()
  const byId = Object.fromEntries(S.units.map((u) => [u.id, u]))
  const attackerIds = new Set()
  Object.values(S.heroes).forEach((hh) => (hh.attackers || []).forEach((id) => attackerIds.add(id)))
  S.plans.forEach((p, i) => {
    if (!byId[p.monster].alive) return
    const a = mid(byId[p.monster].pos)
    const b = mid(p.dest)
    const color = Phaser.Display.Color.HSVToRGB(0.1 + ((i * 0.17) % 0.75), 0.8, 1).color
    if (a[0] !== b[0] || a[1] !== b[1]) { g.fillStyle(color, 0.35); g.fillRect(p.dest[1] * CELL + 5, p.dest[0] * CELL + 5, CELL - 10, CELL - 10); g.lineStyle(3, color, 1); g.strokeRect(p.dest[1] * CELL + 5, p.dest[0] * CELL + 5, CELL - 10, CELL - 10); g.strokeRect(byId[p.monster].pos[1] * CELL + 3, byId[p.monster].pos[0] * CELL + 3, CELL - 6, CELL - 6) }
    if (attackerIds.has(p.monster)) { const mp = byId[p.monster].pos; g.lineStyle(3, 0xff3b3b, 1); g.strokeRoundedRect(mp[1] * CELL + 2, mp[0] * CELL + 2, CELL - 4, CELL - 4, 9) }
    if (!showArrows && hoverId !== p.monster) return
    g.lineStyle(3, color, 0.7)
    if (a[0] !== b[0] || a[1] !== b[1]) {
      g.lineBetween(a[0], a[1], b[0], b[1])
      const ang = Math.atan2(b[1] - a[1], b[0] - a[0])
      const hx = (k) => b[0] - 12 * Math.cos(ang + k)
      const hy = (k) => b[1] - 12 * Math.sin(ang + k)
      g.fillStyle(color, 0.9)
      g.fillTriangle(b[0], b[1], hx(0.5), hy(0.5), hx(-0.5), hy(-0.5))
    }
    if (p.kind === 'attack' && p.target && byId[p.target] && byId[p.target].alive) {
      const t2 = mid(byId[p.target].pos)
      g.lineStyle(5, 0xff0000, 1)
      g.lineBetween(b[0], b[1], t2[0], t2[1])
      g.lineBetween(t2[0] - 8, t2[1] - 8, t2[0] + 8, t2[1] + 8)
      g.lineBetween(t2[0] - 8, t2[1] + 8, t2[0] + 8, t2[1] - 8)
    }
  })
  const info = selected ? S.heroes[selected] : null
  if (info) {
    g.fillStyle(0x7cc4ff, 0.34)
    info.reachable.forEach((t) => g.fillRoundedRect(t[1] * CELL + 3, t[0] * CELL + 3, CELL - 6, CELL - 6, 6))
  }
  S.units.filter((u) => u.alive).forEach((u) => {
    const [x, y] = mid(u.pos)
    const acted = u.side === 'hero' && S.heroes[u.id] && S.heroes[u.id].acted
    const hero = u.side === 'hero'
    const cy = y - 2
    const ug = scene.add.graphics()
    ug.setAlpha(acted ? 0.45 : 1)
    ug.fillStyle(0x000000, 0.35)
    if (hero) ug.fillCircle(x, cy + 2, 17); else ug.fillRoundedRect(x - 17, cy - 15, 34, 34, 8)
    ug.fillStyle(hero ? HERO : MON, 1)
    if (hero) ug.fillCircle(x, cy, 17); else ug.fillRoundedRect(x - 17, cy - 17, 34, 34, 8)
    const ratio = Math.max(0, Math.min(1, u.hp / u.max_hp))
    ug.fillStyle(0x0b0e14, 0.9)
    ug.fillRoundedRect(x - 17, cy + 20, 34, 5, 2)
    ug.fillStyle(ratio > 0.5 ? 0x5fd38d : (ratio > 0.25 ? GOLD : 0xe4604f), 1)
    ug.fillRoundedRect(x - 17, cy + 20, Math.max(2, 34 * ratio), 5, 2)
    scene.add.text(x, cy, u.label[0], { fontFamily: FONT, fontSize: '20px', fontStyle: 'bold', color: '#fff' }).setOrigin(0.5)
    const inc = u.side === 'hero' && S.heroes[u.id] ? S.heroes[u.id].incoming : 0
    if (inc > 0) {
      const dies = inc >= u.hp; const bx = dies ? x - 6 : x - 13; scene.add.rectangle(bx, y - 14, dies ? 32 : 18, dies ? 17 : 13, dies ? 0xff0000 : 0xaa0000).setStrokeStyle(dies ? 2 : 0, 0xffffff)
      scene.add.text(bx, y - 14, '-' + inc + (dies ? ' !' : ''), { fontSize: dies ? '13px' : '11px', color: '#fff', fontStyle: 'bold' }).setOrigin(0.5)
    }
    scene.add.text(x + 15, y - 16, String(u.hp), { fontFamily: FONT, fontSize: '11px', fontStyle: 'bold', color: '#fff', stroke: '#000', strokeThickness: 3 }).setOrigin(0.5)
    if (info && u.side === 'monster' && info.can_attack.includes(u.id)) {
      g.lineStyle(3, GOLD, 1)
      g.strokeRoundedRect(x - CELL / 2 + 3, y - CELL / 2 + 3, CELL - 6, CELL - 6, 9)
    }
    if (u.id === selected) {
      g.lineStyle(3, 0xffffff, 1)
      g.strokeRoundedRect(x - CELL / 2 + 3, y - CELL / 2 + 3, CELL - 6, CELL - 6, 9)
    }
  })
  if (S.result) {
    msg.textContent = S.result === 'win' ? 'YOU WIN!' : 'You lost.'; showResult()
  } else if (!msg.textContent) {
    msg.textContent = 'Round ' + S.round + (selected ? ' - ' + selected : ' - click a hero')
  }
}

class Board extends Phaser.Scene {
  async create() {
    scene = this
    this.input.on('pointerdown', (p) => onClick(p.x, p.y))
    this.input.on('pointermove', (p) => onHover(p.x, p.y))
    await act('/new', { level, seed, brain })
  }
}

new Phaser.Game({
  type: Phaser.AUTO,
  width: 12 * CELL,
  height: 12 * CELL,
  backgroundColor: '#12161f',
  parent: 'app',
  scene: Board,
})
const title = document.createElement('div')
title.className = 'title'
title.textContent = 'Squad Tactics'
const goal = document.createElement('div')
goal.className = 'goal'
goal.textContent = 'Goal: kill all monsters (red squares) before your heroes (blue circles) die. You have 30 rounds.'

const help = document.createElement('div')
help.className = 'help'
help.innerHTML =
  '<b>How to play:</b> 1) Click a hero. 2) Click a light-blue tile to move. ' +
  '3) Click a monster with a yellow outline to attack it (or use Skill). ' +
  '4) Press End turn.<br>' +
  '<b>Danger:</b> a red number on a hero is the damage planned against it. Red-outlined monsters will attack. ' +
  'A faint square is where a monster will walk (same color as its outline). Hover a monster, or press Arrows, to see its arrow. The monsters act AFTER you press End turn, so use your ' +
  'turn to block, kill or avoid them.<br>' +
  '<b>Skills:</b> Tank = Taunt (nearby monsters attack the Tank). Archer = Piercing Shot ' +
  '(hits a whole line). Healer = Heal (+5 HP to another hero).'

const layout = document.createElement('div')
layout.className = 'layout'
const boardCol = document.createElement('div')
boardCol.className = 'board-col'
const sideCol = document.createElement('div')
sideCol.className = 'side'
document.body.insertBefore(layout, document.body.firstChild)
boardCol.appendChild(title)
boardCol.appendChild(goal)
boardCol.appendChild(document.getElementById('app'))
boardCol.appendChild(msg)
boardCol.appendChild(bar)
sideCol.appendChild(brainDiv)
sideCol.appendChild(tutDiv)
sideCol.appendChild(tipsDiv)
sideCol.appendChild(card)
sideCol.appendChild(logDiv)
sideCol.appendChild(help)
layout.appendChild(boardCol)
layout.appendChild(sideCol)
