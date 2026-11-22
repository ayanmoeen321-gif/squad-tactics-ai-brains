import Phaser from 'phaser'
import './style.css'

const CELL = 48
const FLOOR = { '.': 0x2b2f3a, '#': 0x777777, 'C': 0x3d6b3d, 'L': 0xb5481f }
const level = Number(new URLSearchParams(location.search).get('level') || 1)
const seed = Number(new URLSearchParams(location.search).get('seed') || 0)

let S = null
let selected = null
let mode = null
let scene = null

const msg = document.createElement('div')
msg.style.cssText = 'color:#ddd;font:16px sans-serif;padding:8px;min-height:24px'
const bar = document.createElement('div')
bar.style.cssText = 'padding:0 8px'

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
    const j = await api(path, body)
    S = j.state || j; if (path === '/new') { logLines.length = 0; logDiv.innerHTML = '' }; if (j.events) logEvents(j.events, path)
    msg.textContent = ''
  } catch (e) {
    msg.textContent = e.message
  }
  mode = null
  redraw()
}

const logLines = []
const logDiv = document.createElement('div')
logDiv.style.cssText = 'color:#ccc;font:14px sans-serif;padding:8px;max-width:560px;line-height:1.5'

function logEvents(events, path) {
  const n = (id) => { const u = S.units.find((v) => v.id === id); return u ? u.label : id }
  if (path === '/end_turn') logLines.push('--- Monsters act ---')
  events.forEach((e) => {
    const tag = e.taunted ? ' (taunted)' : ''
    if (e.type === 'attack' || e.type === 'piercing_shot') {
      const what = e.type === 'attack' ? 'hit' : 'pierced'
      logLines.push(n(e.attacker) + ' ' + what + ' ' + n(e.target) + ' for ' + e.damage + (e.killed ? ' - dead' : '') + tag)
    } else if (e.type === 'heal') {
      logLines.push(n(e.healer) + ' healed ' + n(e.target) + ' +' + e.restored)
    } else if (e.type === 'lava') {
      logLines.push(n(e.target) + ' burned by lava for ' + e.damage + (e.killed ? ' - dead' : ''))
    } else if (e.type === 'taunt') {
      logLines.push(n(e.unit) + ' used Taunt on ' + (e.affected ? e.affected.length : 0) + ' monster(s)')
    }
  })
  if (logLines.length > 40) logLines.splice(0, logLines.length - 40)
  logDiv.innerHTML = '<b>Log (newest first):</b><br>' + logLines.slice(-14).reverse().join('<br>')
}

function button(label, fn) {
  const b = document.createElement('button')
  b.textContent = label
  b.style.cssText = 'margin-right:8px;padding:6px 12px;font-size:15px'
  b.onclick = fn
  bar.appendChild(b)
}

button('Wait', () => selected && act('/wait', { hero: selected }))
button('Undo move', () => selected && act('/undo', { hero: selected }))
button('Skill', () => {
  if (!selected) return
  if (selected === 'tank') act('/taunt', { hero: 'tank' })
  else if (selected === 'archer') { mode = 'shot'; msg.textContent = 'Piercing Shot: click a direction' }
  else if (selected === 'healer') { mode = 'heal'; msg.textContent = 'Heal: click a hurt hero' }
})
button('End turn', () => { selected = null; act('/end_turn') })
button('Restart', () => { selected = null; act('/new', { level, seed, brain: 'scripted' }) })

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

function redraw() {
  if (!scene || !S) return
  scene.children.removeAll(true)
  S.grid.forEach((row, r) => {
    [...row].forEach((ch, c) => {
      scene.add.rectangle(c * CELL + CELL / 2, r * CELL + CELL / 2, CELL - 2, CELL - 2, FLOOR[ch])
    })
  })
  const g = scene.add.graphics()
  const byId = Object.fromEntries(S.units.map((u) => [u.id, u]))
  S.plans.forEach((p, i) => {
    if (!byId[p.monster].alive) return
    const a = mid(byId[p.monster].pos)
    const b = mid(p.dest)
    const color = Phaser.Display.Color.HSVToRGB((i * 0.17) % 1, 0.8, 1).color
    g.lineStyle(3, color, 0.6)
    g.lineBetween(a[0], a[1], b[0], b[1])
  })
  const info = selected ? S.heroes[selected] : null
  if (info) {
    g.fillStyle(0xffffff, 0.25)
    info.reachable.forEach((t) => g.fillRect(t[1] * CELL + 2, t[0] * CELL + 2, CELL - 4, CELL - 4))
  }
  S.units.filter((u) => u.alive).forEach((u) => {
    const [x, y] = mid(u.pos)
    const acted = u.side === 'hero' && S.heroes[u.id] && S.heroes[u.id].acted
    const color = u.side === 'hero' ? 0x3a7bd5 : 0xd5483a
    scene.add.rectangle(x, y, CELL - 10, CELL - 10, color).setAlpha(acted ? 0.45 : 1)
    scene.add.text(x, y - 4, u.label[0], { fontSize: '20px', color: '#fff' }).setOrigin(0.5)
    scene.add.rectangle(x, y + 16, Math.max(1, (CELL - 12) * (u.hp / u.max_hp)), 4, 0x55ff55)
    if (info && u.side === 'monster' && info.can_attack.includes(u.id)) {
      g.lineStyle(3, 0xffff00, 1)
      g.strokeRect(x - CELL / 2 + 3, y - CELL / 2 + 3, CELL - 6, CELL - 6)
    }
    if (u.id === selected) {
      g.lineStyle(3, 0xffffff, 1)
      g.strokeRect(x - CELL / 2 + 3, y - CELL / 2 + 3, CELL - 6, CELL - 6)
    }
  })
  if (S.result) {
    msg.textContent = S.result === 'win' ? 'YOU WIN! Press Restart.' : 'You lost. Press Restart.'
  } else if (!msg.textContent) {
    msg.textContent = 'Round ' + S.round + (selected ? ' - ' + selected : ' - click a hero')
  }
}

class Board extends Phaser.Scene {
  async create() {
    scene = this
    this.input.on('pointerdown', (p) => onClick(p.x, p.y))
    await act('/new', { level, seed, brain: 'scripted' })
  }
}

new Phaser.Game({
  type: Phaser.AUTO,
  width: 12 * CELL,
  height: 12 * CELL,
  backgroundColor: '#111',
  parent: 'app',
  scene: Board,
})
const goal = document.createElement('div')
goal.style.cssText = 'color:#fff;font:bold 17px sans-serif;padding:8px'
goal.textContent = 'Goal: kill all monsters (red) before your heroes (blue) die. You have 30 rounds.'
document.body.insertBefore(goal, document.body.firstChild)

const help = document.createElement('div')
help.style.cssText = 'color:#aaa;font:14px sans-serif;padding:8px;max-width:560px;line-height:1.5'
help.innerHTML =
  '<b>How to play:</b> 1) Click a hero. 2) Click a white tile to move. ' +
  '3) Click a monster with a yellow outline to attack it (or use Skill). ' +
  '4) Press End turn.<br>' +
  '<b>Colored lines:</b> each one is a monster\'s plan for this round, from where it ' +
  'stands to where it will go. The monsters act AFTER you press End turn, so use your ' +
  'turn to block, kill or avoid them.<br>' +
  '<b>Skills:</b> Tank = Taunt (nearby monsters attack the Tank). Archer = Piercing Shot ' +
  '(hits a whole line). Healer = Heal (+5 HP to another hero).'

document.body.appendChild(msg)
document.body.appendChild(bar)

const side = document.createElement('div')
side.style.cssText = 'position:absolute;left:600px;top:50px;width:520px'
side.appendChild(logDiv)
side.appendChild(help)
document.body.appendChild(side)