import{r as e}from"./howto-p0KY5NlT.js";var t=document.getElementById(`app`);t.className=`menu`,t.innerHTML=`
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
`;var n=[{title:`Level 1: Open room`,desc:`5 monsters`},{title:`Level 2: Split room`,desc:`8 monsters`},{title:`Level 3: Two doors`,desc:`10 monsters, hard`}];function r(e,t,n,r){let i=document.createElement(`button`);i.className=`level-btn`+(n?` `+n:``);let a=document.createElement(`span`);a.className=`level-title`,a.textContent=e;let o=document.createElement(`span`);o.className=`level-desc`,o.textContent=t,i.appendChild(a),i.appendChild(o),i.onclick=r,document.getElementById(`levels`).appendChild(i)}r(`Tutorial`,`Learn the game step by step. Best for new players.`,`tutorial`,()=>{location.href=`/?level=0&tutorial=1&brain=scripted`}),n.forEach((e,t)=>{r(e.title,e.desc,``,()=>{let e=document.getElementById(`brain`).value;location.href=`/?level=`+(t+1)+`&brain=`+e})});var i=document.createElement(`button`);i.className=`btn gold`,i.textContent=`How to play`,i.style.marginTop=`16px`,i.onclick=()=>e(),t.appendChild(i);