const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state={matches:[],sel:null,mode:'auto'};
const EXAMPLES=[
 {a:'Brésil',b:'France',date:'1998-07-12',heure:'21:00',stade:'Stade de France',ville:'Saint-Denis',pays:'France',ko:true,fav:'a'},
 {a:'Real Madrid',b:'Bayer Leverkusen',date:'2002-05-15',heure:'19:45',stade:'Hampden Park',ville:'Glasgow',pays:'Royaume-Uni',ko:true,fav:'a'},
 {a:'Paris Saint-Germain',b:'Olympique de Marseille',date:null,heure:'21:00',stade:'Parc des Princes',ville:'Paris',pays:'France',ko:false,fav:''}
];
const fmtDay=d=>new Date(d+'T12:00:00Z').toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long',timeZone:'UTC'});
const parisTime=u=>{const d=new Date(u.replace(' ','T')+':00Z');return {day:d.toLocaleDateString('sv-SE',{timeZone:'Europe/Paris'}),h:d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Paris'})}};

// ---------- onglets
$$('.tab').forEach(b=>b.onclick=()=>{
  $$('.tab').forEach(x=>x.classList.toggle('on',x===b)); state.mode=b.dataset.tab;
  $('#tab-auto').hidden=state.mode!=='auto'; $('#tab-manu').hidden=state.mode!=='manu';
  if(state.mode==='manu') selectManual(); else if(state.sel&&state.sel.src==='auto') showStep2(); else {$('#step2').hidden=true;}
});

// ---------- liste des matchs
async function loadMatches(refresh=false){
  $('#matchList').innerHTML='<p class="muted" style="padding:12px"><span class="spin">☽</span> Chargement du calendrier…</p>';
  try{
    const r=await fetch('/api/matches?days=7'+(refresh?'&refresh=true':'')); const j=await r.json();
    state.matches=j.matches; const ok=j.auto;
    $('#srcBadge').textContent=ok?`automatique · ${j.matches.length}`:'manuel'; $('#srcBadge').className='badge '+(ok?'ok':'ko');
    $('#srcNote').innerHTML=(ok?'<b>Calendrier automatique</b> (7 prochains jours). ':'<b>Aucune source automatique disponible</b> : utilisez la saisie manuelle. ')+
      j.sources.map(s=>`${s.ok?'✅':'⛔'} ${esc(s.nom)} — ${esc(s.note)}`).join(' · ')+` <br>Mise à jour : ${esc(j.maj)}.`;
    const comps=[...new Set(j.matches.map(m=>m.competition))].sort();
    $('#fComp').innerHTML='<option value="">Toutes les compétitions</option>'+comps.map(c=>`<option>${esc(c)}</option>`).join('');
    renderList();
  }catch(e){ $('#srcBadge').textContent='manuel'; $('#srcBadge').className='badge ko'; $('#matchList').innerHTML='<p class="alert">Impossible de charger les matchs. Utilisez la saisie manuelle.</p>'; }
}
function renderList(){
  const c=$('#fComp').value, q=$('#fSearch').value.toLowerCase().trim();
  const ms=state.matches.filter(m=>(!c||m.competition===c)&&(!q||(m.home+' '+m.away).toLowerCase().includes(q)));
  if(!ms.length){$('#matchList').innerHTML='<p class="muted" style="padding:12px">Aucun match.</p>';return;}
  let html='',last='';
  for(const m of ms){
    const p=parisTime(m.kickoff_utc);
    if(p.day!==last){last=p.day;html+=`<div class="day">${fmtDay(p.day)} (heure de Paris)</div>`;}
    const od=m.odds?`cotes ${m.odds.home} / ${m.odds.draw??'–'} / ${m.odds.away}`:'cotes ?';
    html+=`<div class="m ${state.sel&&state.sel.id===m.id?'sel':''}" data-id="${esc(m.id)}" tabindex="0"><div class="t">${p.h}</div>
      <div class="teams">${esc(m.home)} – ${esc(m.away)}<div class="sub">${esc(m.competition)} · ${esc(m.venue||'stade ?')}${m.city?', '+esc(m.city):''}</div></div><div class="od">${od}</div></div>`;
  }
  $('#matchList').innerHTML=html;
  $$('.m').forEach(el=>{el.onclick=()=>selectAuto(el.dataset.id);el.onkeydown=e=>{if(e.key==='Enter')selectAuto(el.dataset.id)}});
}
$('#fComp').onchange=renderList; $('#fSearch').oninput=renderList; $('#btnRefresh').onclick=()=>loadMatches(true);

function selectAuto(id){
  const m=state.matches.find(x=>x.id===id); if(!m)return;
  state.sel={src:'auto',id,a:m.home,b:m.away,kickoff_utc:m.kickoff_utc,stade:m.venue,ville:m.city,pays:m.country,ko:m.knockout,odds:m.odds,comp:m.competition,fav:m.favorite||''};
  renderList(); showStep2();
  $('#step2').scrollIntoView({behavior:'smooth',block:'start'});
}
function selectManual(){
  const f=$('#manForm');
  state.sel={src:'manu',a:f.a.value||'Équipe A',b:f.b.value||'Équipe B',ko:f.ko.checked,fav:state.sel&&state.sel.src==='manu'?state.sel.fav:'',odds:null};
  showStep2();
}
$('#manForm').addEventListener('input',()=>{ if(state.mode==='manu'){const fav=state.sel?.fav||''; selectManual(); state.sel.fav=fav; $('#fav').value=fav; updateBtn();}});
$$('.chip').forEach(c=>c.onclick=()=>{
  const e=EXAMPLES[+c.dataset.ex],f=$('#manForm'); let d=e.date;
  if(!d){const t=new Date();t.setDate(t.getDate()+((7-t.getDay())%7||7));d=t.toISOString().slice(0,10);}
  f.a.value=e.a;f.b.value=e.b;f.date.value=d;f.heure.value=e.heure;f.stade.value=e.stade;f.ville.value=e.ville;f.pays.value=e.pays;f.ko.checked=e.ko;
  selectManual(); state.sel.fav=e.fav; $('#fav').value=e.fav; updateBtn();
});

function showStep2(){
  const s=state.sel; $('#step2').hidden=false; $('#result').hidden=true;
  let h;
  if(s.src==='auto'){
    const p=parisTime(s.kickoff_utc);
    h=`<div class="vs"><span style="color:var(--a)">${esc(s.a)}</span> – <span style="color:var(--b)">${esc(s.b)}</span></div>
       <div class="muted small">${esc(s.comp)} · coup d'envoi ${fmtDay(p.day)} ${p.h} (Paris) = ${esc(s.kickoff_utc)} UTC · ${esc(s.stade||'stade non indiqué')}${s.ville?', '+esc(s.ville):''}${s.ko?' · élimination directe':''}</div>
       <div class="small muted">Match issu du calendrier automatique ✅ — A = équipe à domicile.</div>`;
    $('#venueRow').hidden=!!(s.stade||s.ville); $('#vStade').value=s.stade||''; $('#vVille').value=s.ville||'';
  } else {
    h=`<div class="vs"><span style="color:var(--a)">${esc(s.a)}</span> – <span style="color:var(--b)">${esc(s.b)}</span></div><div class="small muted">Match saisi <b>manuellement</b> ✍️ (heure locale du coup d'envoi, converti en UTC avec le fuseau du lieu).</div>`;
    $('#venueRow').hidden=true;
  }
  $('#selSummary').innerHTML=h;
  $('#fav').innerHTML=`<option value="">— choisir —</option><option value="a">${esc(s.a)} (A) est favorite</option><option value="b">${esc(s.b)} (B) est favorite</option><option value="egal">Égalité (cotes quasi égales)</option>`;
  $('#fav').value=s.fav||'';
  $('#favNote').innerHTML=s.odds?`Favori présélectionné d'après les <b>cotes ${esc(s.odds.fournisseur)}</b> (victoire A ${s.odds.home} · nul ${s.odds.draw??'–'} · victoire B ${s.odds.away}) ; écart &lt; 10 % = égalité. Vous pouvez le modifier. <i>Les cotes ne servent qu'à désigner le favori.</i>`:
    (s.src==='auto'?'Cotes indisponibles pour ce match : <b>choisissez le favori vous-même</b>.':'Saisie manuelle : <b>choisissez le favori</b> (d\'après les cotes ou votre connaissance du sport).');
  updateBtn();
}
$('#fav').onchange=()=>{state.sel.fav=$('#fav').value;updateBtn();};
function updateBtn(){
  const f=$('#manForm'); const manOk=state.sel?.src!=='manu'||(f.a.value&&f.b.value&&f.date.value&&f.heure.value&&f.ville.value);
  $('#btnPredict').disabled=!(state.sel&&$('#fav').value&&manOk);
}

// ---------- prédiction
$('#btnPredict').onclick=async()=>{
  const s=state.sel,f=$('#manForm'); let body;
  if(s.src==='auto'){
    body={equipe_a:s.a,equipe_b:s.b,favori:$('#fav').value,kickoff_utc:s.kickoff_utc,stade:$('#vStade').value||s.stade,ville:$('#vVille').value||s.ville,pays:s.pays,elimination:s.ko};
  } else body={equipe_a:f.a.value,equipe_b:f.b.value,favori:$('#fav').value,date:f.date.value,heure:f.heure.value,stade:f.stade.value||null,ville:f.ville.value||null,pays:f.pays.value||null,elimination:f.ko.checked};
  const r=$('#result'); r.hidden=false; r.innerHTML='<div class="card"><span class="spin">☽</span> Calcul du thème…</div>'; $('#btnPredict').disabled=true;
  try{
    const res=await fetch('/api/predict',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
    const j=await res.json();
    if(!res.ok) throw new Error(typeof j.detail==='string'?j.detail:JSON.stringify(j.detail));
    renderResult(j);
  }catch(e){ r.innerHTML=`<div class="card"><div class="alert">Erreur : ${esc(e.message)}</div></div>`; }
  updateBtn(); r.scrollIntoView({behavior:'smooth',block:'start'});
};

const GL={Sun:'☉',Moon:'☽',Mercury:'☿',Venus:'♀',Mars:'♂',Jupiter:'♃',Saturn:'♄',Uranus:'♅',Neptune:'♆',Pluto:'♇'};
const SG='♈♉♊♋♌♍♎♏♐♑♒♓'.split('');
function wheel(j){
  const t=j.theme,m=j.match,asc=t.asc.lon,cx=210,cy=210,R=190,R2=158,R3=128;
  const ang=l=>(180+(l-asc))*Math.PI/180, pt=(l,r)=>[cx+r*Math.cos(ang(l)),cy-r*Math.sin(ang(l))];
  const favTeam=m.favori==='b'?'b':'a', dogTeam=favTeam==='a'?'b':'a';
  const lordTeam={}; for(const h of ['1','10']) if(t.seigneurs[h]) lordTeam[t.seigneurs[h]]=favTeam; for(const h of ['7','4']) if(t.seigneurs[h]) lordTeam[t.seigneurs[h]]=dogTeam;
  const col={a:'#7aa2ff',b:'#ffb36b'};
  let s=`<svg class="wheel" viewBox="0 0 420 420" role="img" aria-label="Roue du thème"><circle cx="210" cy="210" r="${R}" fill="#0d1226" stroke="#2a3566"/><circle cx="210" cy="210" r="${R2}" fill="none" stroke="#2a3566"/><circle cx="210" cy="210" r="${R3-20}" fill="#0a0e20" stroke="#222b58"/>`;
  for(let i=0;i<12;i++){const l=i*30,[x1,y1]=pt(l,R),[x2,y2]=pt(l,R2),[gx,gy]=pt(l+15,(R+R2)/2);
    s+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#2a3566"/><text x="${gx}" y="${gy+5}" text-anchor="middle" font-size="15" fill="${[0,4,8].includes(i)?'#ff9a8a':[1,5,9].includes(i)?'#9be59b':[2,6,10].includes(i)?'#ffe08a':'#8fd0ff'}">${SG[i]}\uFE0E</text>`;}
  const axes=[[t.asc.lon,'1','ASC',favTeam],[t.dsc.lon,'7','DSC',dogTeam],[t.mc.lon,'10','MC',favTeam],[t.ic.lon,'4','IC',dogTeam]];
  for(const [l,h,n,tm] of axes){const [x1,y1]=pt(l,R),[x2,y2]=pt(l,R3-20),[lx,ly]=pt(l,R+14);
    s+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col[tm]}" stroke-width="2"/>`;
    const [tx,ty]=pt(l,R3-8);
    s+=`<text x="${tx}" y="${ty+4}" text-anchor="middle" font-size="11" fill="${col[tm]}" font-weight="700">${n}</text>`;}
  // planètes (avec écartement)
  const items=t.planetes.map(p=>({...p,k:'p'}));
  items.push({id:'Fortuna',lon:t.fortuna.lon,gl:'⊗',nom:'Fortuna',k:'f'},{id:'FortunaA',lon:t.fortuna.antiscion_lon,gl:'⊗′',nom:"Antiscion de Fortuna",k:'fa'},
             {id:'NN',lon:t.noeud_nord.lon,gl:'☊',nom:'Nœud Nord',k:'n'},{id:'SN',lon:t.noeud_sud.lon,gl:'☋',nom:'Nœud Sud',k:'n'});
  items.sort((x,y)=>x.lon-y.lon); const disp=items.map(x=>x.lon);
  for(let it=0;it<30;it++)for(let i=1;i<items.length;i++){const d=disp[i]-disp[i-1];if(d<9){const c=(9-d)/2;disp[i-1]-=c;disp[i]+=c;}}
  items.forEach((p,i)=>{const [x,y]=pt(disp[i],(p.k==='fa')?R3+6:R3+ (i%2?10:22)+0); const [ox,oy]=pt(p.lon,R2);
    const c=lordTeam[p.nom]?col[lordTeam[p.nom]]:(p.k==='f'||p.k==='fa')?'#f2c46d':p.id==='Moon'?'#e8ebf7':'#c8cff0';
    const [px,py]=pt(p.lon,R2-2);
    s+=`<line x1="${px}" y1="${py}" x2="${x}" y2="${y}" stroke="#ffffff22"/><text x="${x}" y="${y+5}" text-anchor="middle" font-size="${p.k==='fa'?12:17}" fill="${c}"><title>${esc(p.nom)} ${esc(p.pos||'')}</title>${p.gl||GL[p.id]+'\uFE0E'}</text>`;
    if(lordTeam[p.nom]) s+=`<circle cx="${x}" cy="${y}" r="11" fill="none" stroke="${c}" stroke-dasharray="3 2"/>`;});
  s+=`<text x="210" y="205" text-anchor="middle" font-size="11" fill="#98a2c8">Thème du coup d'envoi</text><text x="210" y="222" text-anchor="middle" font-size="10" fill="#98a2c8">ASC à gauche</text></svg>
  <p class="small muted" style="text-align:center"><span style="color:var(--a)">■</span> ${esc(m.equipe_a)} &nbsp; <span style="color:var(--b)">■</span> ${esc(m.equipe_b)} &nbsp; ⊗ Fortuna (⊗′ son antiscion) · cercle pointillé = seigneur retenu</p>`;
  return s;
}
function tableTheme(j){
  const t=j.theme,m=j.match;
  const rows=[['Ascendant (maison 1)',t.asc.pos,'seigneur : '+t.asc.seigneur],['Milieu du Ciel (maison 10)',t.mc.pos,'seigneur : '+t.mc.seigneur],['Descendant (maison 7)',t.dsc.pos,'seigneur : '+t.dsc.seigneur],['Fond du Ciel (maison 4)',t.ic.pos,'seigneur : '+t.ic.seigneur],
    ['Lune',t.lune.pos,`reste ${t.lune.reste_dans_le_signe}° dans le signe · plage ${t.lune.plage_degres}°`],['Part de Fortune',t.fortuna.pos,'antiscion : '+t.fortuna.antiscion],['Nœud Nord / Sud',t.noeud_nord.pos,t.noeud_sud.pos]];
  let h='<table>'+rows.map(r=>`<tr><th>${r[0]}</th><td>${esc(r[1])}</td><td class="muted">${esc(r[2])}</td></tr>`).join('')+'</table>';
  h+='<h3>Maisons des équipes</h3><table><tr><th>Maison</th><th>Équipe</th><th>Pointe</th><th>Seigneur retenu</th></tr>'+
    Object.entries(t.maisons).sort((a,b)=>a[0]-b[0]).map(([k,v])=>`<tr><td>${k}</td><td>${esc(v.equipe)} <span class="muted">(${v.role})</span></td><td>${esc(v.pointe)}</td><td>${esc(v.seigneur_retenu||'— ('+v.seigneur_signe+' écarté)')}</td></tr>`).join('')+'</table>';
  h+='<details><summary>Positions des planètes</summary><table>'+t.planetes.map(p=>`<tr><td>${GL[p.id]}\uFE0E ${esc(p.nom)}</td><td>${esc(p.pos)}${p.retro?' ℞':''}</td></tr>`).join('')+'</table></details>';
  return h;
}
function renderResult(j){
  const p=j.prediction,m=j.match; let h='';
  const cls=p.resultat==='a'?'a':p.resultat==='b'?'b':'x';
  let title,sub='';
  if(p.resultat==='indetermine'){title='Indéterminé';sub='Méthode inutilisable : les deux équipes sont à égalité.';}
  else if(p.resultat==='nul'){title='Match nul possible';sub='Les témoignages se compensent (hypothèse hors livre).';}
  else{title=esc(p.vainqueur);sub='Vainqueur prédit';}
  h+=`<div class="card"><h2><span class="n">3</span> Résultat — ${esc(m.equipe_a)} – ${esc(m.equipe_b)}</h2><div class="verdict">
    <div class="vbox"><div class="muted small">${sub}</div><div class="winner ${cls}">${title}</div>
      <div>Confiance : <span class="conf ${esc(p.confiance)}">${esc(p.confiance)}</span> <span class="muted small">(indice interne, pas une probabilité)</span></div>
      ${p.score?`<div class="score">Score indicatif : <b>${esc(p.score.texte)}</b></div><div class="small muted">${esc(p.score.note||'')} ${esc(p.score.avertissement)}</div>`:''}</div>
    <div class="vbox small"><b>Coup d'envoi</b> : ${esc(m.coup_denvoi_local)} locale (${esc(m.abbr_fuseau||'')}, UTC${m.decalage_utc_h>=0?'+':''}${m.decalage_utc_h}) = ${esc(m.coup_denvoi_utc)} UTC<br>
      <b>Lieu</b> : ${esc(m.lieu.nom)} <span class="muted">(${esc(m.lieu.lat)}, ${esc(m.lieu.lon)} · géocodage : ${esc(m.lieu.source)})</span><br>
      <b>Favori retenu</b> : ${esc(m.favori_nom||'aucun (égalité)')} · <b>Profil</b> : ${esc(m.profil_libelle)}${p.points_favori!=null?`<br><b>Points</b> favori ${p.points_favori} · outsider ${p.points_outsider}`:''}</div></div>
    <p>${esc(p.raisonnement)}</p>`;
  for(const w of j.avertissements) h+=`<div class="alert">⚠️ ${esc(w)}</div>`;
  h+='</div>';
  h+=`<div class="card"><h2>Le thème d'événement</h2><div class="cols"><div>${wheel(j)}</div><div>${tableTheme(j)}</div></div></div>`;
  h+=`<div class="card"><h2>Pourquoi ? Les témoignages utilisés</h2>`;
  if(!j.temoignages.length) h+=`<p class="muted">${p.methode_utilisable?'Aucun témoignage détecté : le livre applique alors la règle par défaut « les favoris gagnent s\'il n\'y a pas de preuve du contraire » (p.114).':'Pas de témoignages : la méthode exige un favori.'}</p>`;
  else{
    h+='<p class="small muted">Du plus déterminant au moins déterminant (niveau 1 = le plus fort). Contour doré = témoignage du niveau qui a décidé en faveur du vainqueur. Les poids sont des hypothèses d\'implémentation.</p><ol class="tem" style="padding:0">';
    for(const t of j.temoignages) h+=`<li class="${t.equipe}${t.decisif?' dec':''}"><div class="meta"><span class="tag ${t.equipe}">pour ${esc(t.equipe_nom)} (${t.camp})</span><span class="tag">niveau ${t.niveau}</span><span class="tag">force ${t.force} · ${t.poids}</span>${t.decisif?'<span class="tag dec">★ décisif</span>':''}</div>${esc(t.texte)}<div class="ref">📖 ${esc(t.source_livre)}</div></li>`;
    h+='</ol>';}
  if(j.sequence_lune.length){h+='<h3>Parcours de la Lune (le « flux des événements »)</h3><ul class="seq">'+j.sequence_lune.map(s=>`<li>après ${s.distance}° : ${esc(s.aspect)} ${esc(s.cible)} → ${esc(s.nom_camp)}${s.final?' <b>(aspect final : il l\'emporte)</b>':''}</li>`).join('')+'</ul>';}
  if(j.theme.notes_seigneurs.length) h+='<h3>Notes sur les seigneurs</h3><ul class="seq">'+j.theme.notes_seigneurs.map(n=>`<li>${esc(n)}</li>`).join('')+'</ul>';
  h+=`<div class="info" style="margin-top:14px">ℹ️ ${esc(j.mentions)}</div></div>`;
  $('#result').innerHTML=h;
}
loadMatches();
