import './style.css'
import { openHowTo } from './howto.js'

const root = document.getElementById('app')
root.className = 'menu'
root.innerHTML = `
  <h1>Squad Tactics</h1>
  <p class="tagline">Lead 3 heroes against a team of monsters that plan together.</p>
  <p class="legend"><span class="dot hero"></span>Your heroes <span class="dot monster"></span>Monsters</p>
  <p>Kill all monsters before your heroes die. You have 30 rounds.</p>
  <label class="label" for="brain">Monster brain</label>
  <select id="brain" class="select">
    <option value="scripted">Scripted (hand-made rules)</option>
    <option value="random">Random (easy)</option>
    <option value="laya">Laya (needs a GPU server)</option>
  </select>
  <p class="label">Choose a level</p>
  <div id="levels"></div>
`

const levels = [
  { title: 'Level 1: Open room', desc: '5 monsters' },
  { title: 'Level 2: Split room', desc: '8 monsters' },
  { title: 'Level 3: Two doors', desc: '10 monsters, hard' },
]

function levelButton(title, desc, cls, onClick) {
  const b = document.createElement('button')
  b.className = 'level-btn' + (cls ? ' ' + cls : '')
  const t = document.createElement('span')
  t.className = 'level-title'
  t.textContent = title
  const d = document.createElement('span')
  d.className = 'level-desc'
  d.textContent = desc
  b.appendChild(t)
  b.appendChild(d)
  b.onclick = onClick
  document.getElementById('levels').appendChild(b)
}

levelButton('Tutorial', 'Learn the game step by step. Best for new players.', 'tutorial', () => {
  location.href = '/?level=0&tutorial=1&brain=scripted'
})
levels.forEach((lv, i) => {
  levelButton(lv.title, lv.desc, '', () => {
    const brain = document.getElementById('brain').value
    location.href = '/?level=' + (i + 1) + '&brain=' + brain
  })
})

const hb = document.createElement('button')
hb.className = 'btn gold'
hb.textContent = 'How to play'
hb.style.marginTop = '16px'
hb.onclick = () => openHowTo()
root.appendChild(hb)
