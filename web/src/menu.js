import './style.css'

const root = document.getElementById('app')
root.style.cssText = 'color:#eee;font-family:sans-serif;max-width:560px;margin:40px auto;padding:0 16px;line-height:1.5'
root.innerHTML = `
  <h1 style="margin:0 0 4px">Squad Tactics</h1>
  <p style="color:#aaa;margin:0 0 20px">Lead 3 heroes against a team of monsters that plan together.</p>
  <p><b>Goal:</b> kill all monsters before your heroes die. You have 30 rounds.</p>
  <p style="margin:20px 0 6px"><b>Monster brain:</b></p>
  <select id="brain" style="font-size:16px;padding:6px">
    <option value="scripted">Scripted (hand-made rules)</option>
    <option value="random">Random (easy)</option>
  </select>
  <p style="margin:20px 0 6px"><b>Choose a level:</b></p>
  <div id="levels"></div>
`
const names = ['1 - Open room (5 monsters)', '2 - Split room (8 monsters)', '3 - Two doors (10 monsters, hard)']
names.forEach((label, i) => {
  const b = document.createElement('button')
  b.textContent = 'Level ' + label
  b.style.cssText = 'display:block;width:100%;margin:8px 0;padding:12px;font-size:16px;cursor:pointer'
  b.onclick = () => {
    const brain = document.getElementById('brain').value
    location.href = '/?level=' + (i + 1) + '&brain=' + brain
  }
  document.getElementById('levels').appendChild(b)
})