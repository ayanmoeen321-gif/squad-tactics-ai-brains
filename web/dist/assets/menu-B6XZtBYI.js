/* empty css              */var e=document.getElementById(`app`);e.style.cssText=`color:#eee;font-family:sans-serif;max-width:560px;margin:40px auto;padding:0 16px;line-height:1.5`,e.innerHTML=`
  <h1 style="margin:0 0 4px">Squad Tactics</h1>
  <p style="color:#aaa;margin:0 0 20px">Lead 3 heroes against a team of monsters that plan together.</p>
  <p><b>Goal:</b> kill all monsters before your heroes die. You have 30 rounds.</p>
  <p style="margin:20px 0 6px"><b>Monster brain:</b></p>
  <select id="brain" style="font-size:16px;padding:6px">
    <option value="scripted">Scripted (hand-made rules)</option>
    <option value="random">Random (easy)</option>
    <option value="laya">Laya (needs a GPU server)</option>
  </select>
  <p style="margin:20px 0 6px"><b>Choose a level:</b></p>
  <div id="levels"></div>
`;var t=[`1 - Open room (5 monsters)`,`2 - Split room (8 monsters)`,`3 - Two doors (10 monsters, hard)`],n=document.createElement(`button`);n.textContent=`Tutorial - learn the game step by step (recommended for new players)`,n.style.cssText=`display:block;width:100%;margin:8px 0;padding:12px;font-size:16px;cursor:pointer;background:#cfe3ff`,n.onclick=()=>{location.href=`/?level=0&tutorial=1&brain=scripted`},document.getElementById(`levels`).appendChild(n),t.forEach((e,t)=>{let n=document.createElement(`button`);n.textContent=`Level `+e,n.style.cssText=`display:block;width:100%;margin:8px 0;padding:12px;font-size:16px;cursor:pointer`,n.onclick=()=>{let e=document.getElementById(`brain`).value;location.href=`/?level=`+(t+1)+`&brain=`+e},document.getElementById(`levels`).appendChild(n)});