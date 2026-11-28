import './style.css'
import { SPRITE, sprite, openHowTo } from './howto.js'

// Set to false if the sprites face the wrong way on the title screen.
const FLIP_MONSTERS = true
const FLIP_HEROES = false

const root = document.getElementById('app')
root.className = 'scene'
root.innerHTML = `
  <div class="sc-floor"></div>
  <div class="sc-glow"></div>
  <div class="sc-embers" id="embers"></div>
  <div class="sc-main">
    <h1 class="sc-title">SQUAD TACTICS</h1>
    <p class="sc-tag">Lead 3 heroes against a team of monsters that plan together.</p>
    <p class="sc-legend"><span class="dot hero"></span>Your heroes <span class="dot monster"></span>Monsters</p>
    <div class="sc-views">
      <div class="sc-view" id="v-title">
        <button class="btn big primary" id="b-play">Play</button>
        <button class="btn big" id="b-tut">Tutorial</button>
        <button class="btn big gold" id="b-how">How to play</button>
      </div>
      <div class="sc-view off-right" id="v-play">
        <label class="sc-label" for="brain">Monster brain</label>
        <select id="brain" class="select">
          <option value="scripted">Scripted (hand-made rules)</option>
          <option value="random">Random (easy)</option>
          <option value="laya">Laya (needs a GPU server)</option>
        </select>
        <div id="levels" class="sc-levels"></div>
        <button class="btn quiet" id="b-back">Back</button>
      </div>
    </div>
  </div>
  <div class="sc-stage" id="stage"></div>
  <div class="sc-credit">Unit sprites: Tiny Dungeon by Kenney (CC0), kenney.nl</div>
`

// ---- embers ----
const embers = document.getElementById('embers')
for (let i = 0; i < 26; i++) {
  const e = document.createElement('span')
  e.className = 'ember'
  e.style.setProperty('--x', (Math.random() * 100).toFixed(1) + '%')
  e.style.setProperty('--dx', (Math.random() * 120 - 60).toFixed(0) + 'px')
  e.style.setProperty('--d', (9 + Math.random() * 10).toFixed(1) + 's')
  e.style.setProperty('--delay', (-Math.random() * 18).toFixed(1) + 's')
  e.style.opacity = '0'
  embers.appendChild(e)
}

// ---- idle sprites: heroes left, monsters right, facing each other ----
const HEROES = [['Tank', 'hero:T'], ['Archer', 'hero:A'], ['Healer', 'hero:H']]
const MONSTERS = [['Goblin', 'monster:G'], ['Brute', 'monster:B'], ['Archer', 'monster:A'], ['Healer', 'monster:H']]
const stage = document.getElementById('stage')
function side(list, cls, flip) {
  const wrap = document.createElement('div')
  wrap.className = 'sc-side ' + cls
  list.forEach(([name, key], i) => {
    const u = document.createElement('div')
    u.className = 'sc-unit'
    u.style.setProperty('--bd', (-i * 0.37).toFixed(2) + 's')
    u.innerHTML = '<div class="sc-sprite' + (flip ? ' flip' : '') + '">' + sprite(SPRITE[key], 5) + '</div>' +
      '<div class="sc-shadow"></div><div class="nm ' + cls + '">' + name + '</div>'
    wrap.appendChild(u)
  })
  stage.appendChild(wrap)
}
side(HEROES, 'hero', FLIP_HEROES)
side(MONSTERS, 'monster', FLIP_MONSTERS)

// ---- views ----
const vTitle = document.getElementById('v-title')
const vPlay = document.getElementById('v-play')
function showPlay(on) {
  vTitle.classList.toggle('off-left', on)
  vPlay.classList.toggle('off-right', !on)
}
document.getElementById('b-play').onclick = () => showPlay(true)
document.getElementById('b-back').onclick = () => showPlay(false)
document.getElementById('b-how').onclick = () => openHowTo()
document.getElementById('b-tut').onclick = () => { location.href = '/?level=0&tutorial=1&brain=scripted' }

const levels = [
  { title: 'Level 1: Open room', desc: '5 monsters' },
  { title: 'Level 2: Split room', desc: '8 monsters' },
  { title: 'Level 3: Two doors', desc: '10 monsters, hard' },
]

function levelButton(title, desc, onClick) {
  const b = document.createElement('button')
  b.className = 'level-btn'
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

levels.forEach((lv, i) => {
  levelButton(lv.title, lv.desc, () => {
    const brain = document.getElementById('brain').value
    location.href = '/?level=' + (i + 1) + '&brain=' + brain
  })
})
