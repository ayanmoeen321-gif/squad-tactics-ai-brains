import{i as e,n as t,r as n}from"./howto-B1vLqXm_.js";var r=!0,i=!1,a=document.getElementById(`app`);a.className=`scene`,a.innerHTML=`
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
`;var o=document.getElementById(`embers`);for(let e=0;e<26;e++){let e=document.createElement(`span`);e.className=`ember`,e.style.setProperty(`--x`,(Math.random()*100).toFixed(1)+`%`),e.style.setProperty(`--dx`,(Math.random()*120-60).toFixed(0)+`px`),e.style.setProperty(`--d`,(9+Math.random()*10).toFixed(1)+`s`),e.style.setProperty(`--delay`,(-Math.random()*18).toFixed(1)+`s`),e.style.opacity=`0`,o.appendChild(e)}var s=[[`Tank`,`hero:T`],[`Archer`,`hero:A`],[`Healer`,`hero:H`]],c=[[`Goblin`,`monster:G`],[`Brute`,`monster:B`],[`Archer`,`monster:A`],[`Healer`,`monster:H`]],l=document.getElementById(`stage`);function u(n,r,i){let a=document.createElement(`div`);a.className=`sc-side `+r,n.forEach(([n,o],s)=>{let c=document.createElement(`div`);c.className=`sc-unit`,c.style.setProperty(`--bd`,(-s*.37).toFixed(2)+`s`),c.innerHTML=`<div class="sc-sprite`+(i?` flip`:``)+`">`+e(t[o],5)+`</div><div class="sc-shadow"></div><div class="nm `+r+`">`+n+`</div>`,a.appendChild(c)}),l.appendChild(a)}u(s,`hero`,i),u(c,`monster`,r);var d=document.getElementById(`v-title`),f=document.getElementById(`v-play`);function p(e){d.classList.toggle(`off-left`,e),f.classList.toggle(`off-right`,!e)}document.getElementById(`b-play`).onclick=()=>p(!0),document.getElementById(`b-back`).onclick=()=>p(!1),document.getElementById(`b-how`).onclick=()=>n(),document.getElementById(`b-tut`).onclick=()=>{location.href=`/?level=0&tutorial=1&brain=scripted`};var m=[{title:`Level 1: Open room`,desc:`5 monsters`},{title:`Level 2: Split room`,desc:`8 monsters`},{title:`Level 3: Two doors`,desc:`10 monsters, hard`}];function h(e,t,n){let r=document.createElement(`button`);r.className=`level-btn`;let i=document.createElement(`span`);i.className=`level-title`,i.textContent=e;let a=document.createElement(`span`);a.className=`level-desc`,a.textContent=t,r.appendChild(i),r.appendChild(a),r.onclick=n,document.getElementById(`levels`).appendChild(r)}m.forEach((e,t)=>{h(e.title,e.desc,()=>{let e=document.getElementById(`brain`).value;location.href=`/?level=`+(t+1)+`&brain=`+e})});