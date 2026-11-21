import Phaser from 'phaser'
import './style.css'

const CELL = 48
const FLOOR = { '.': 0x2b2f3a, '#': 0x777777, 'C': 0x3d6b3d, 'L': 0xb5481f }

async function api(path, body) {
  const r = await fetch('/api' + path, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  return r.json()
}

class Board extends Phaser.Scene {
  async create() {
    const level = Number(new URLSearchParams(location.search).get('level') || 1)
    const s = await api('/new', { level, seed: 0, brain: 'scripted' })
    this.draw(s)
  }

  draw(s) {
    s.grid.forEach((row, r) => {
      [...row].forEach((ch, c) => {
        this.add.rectangle(c * CELL + CELL / 2, r * CELL + CELL / 2, CELL - 2, CELL - 2, FLOOR[ch])
      })
    })
    const g = this.add.graphics()
    const mid = (p) => [p[1] * CELL + CELL / 2, p[0] * CELL + CELL / 2]
    const byId = Object.fromEntries(s.units.map((u) => [u.id, u]))
    s.plans.forEach((p, i) => {
      const a = mid(byId[p.monster].pos)
      const b = mid(p.dest)
      const color = Phaser.Display.Color.HSVToRGB((i * 0.17) % 1, 0.8, 1).color
      g.lineStyle(3, color, 0.6)
      g.lineBetween(a[0], a[1], b[0], b[1])
    })
    s.units.filter((u) => u.alive).forEach((u) => {
      const [x, y] = mid(u.pos)
      const color = u.side === 'hero' ? 0x3a7bd5 : 0xd5483a
      this.add.rectangle(x, y, CELL - 10, CELL - 10, color)
      this.add.text(x, y - 4, u.label[0], { fontSize: '20px', color: '#fff' }).setOrigin(0.5)
      this.add.rectangle(x, y + 16, (CELL - 12) * (u.hp / u.max_hp), 4, 0x55ff55)
    })
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