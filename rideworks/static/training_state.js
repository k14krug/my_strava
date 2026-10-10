/* Exact server-calculated daily evidence. Rendering never changes model math. */
(() => {
  'use strict';
  const payload = document.querySelector('#training-state-data');
  if (!payload) return;
  const data = JSON.parse(payload.textContent), days = data.days;
  const chart = document.querySelector('#training-chart');
  const dateInput = document.querySelector('#training-date');
  const rangeFirst = value => {
    if (value === 'all') return 0;
    if (value === '42') return Math.max(0,days.length-42);
    const end = new Date(days.at(-1).day+'T00:00:00Z'), months = value === '3months' ? 3 : 12;
    const target = new Date(Date.UTC(end.getUTCFullYear(),end.getUTCMonth()-months,1));
    const last = new Date(Date.UTC(target.getUTCFullYear(),target.getUTCMonth()+1,0)).getUTCDate();
    target.setUTCDate(Math.min(end.getUTCDate(),last));
    const cutoff=target.toISOString().slice(0,10), index=days.findIndex(d=>d.day>cutoff);
    return index < 0 ? days.length-1 : index;
  };
  let range = '3months', first = rangeFirst(range), selected = days.length - 1;
  const colors = {fitness: '#2563eb', fatigue: '#b77815', form: '#078675'};
  const classes = {calculated: 'Calculated power interval', corrected_estimate: 'Estimated FIT interval',
    hr_estimate: 'HR estimate', partial: 'Partial power', unavailable: 'Stress unavailable'};
  const fmt = v => v == null ? 'Unavailable' : v.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1});
  const node = (tag, text, className) => {
    const result = document.createElement(tag); if (text != null) result.textContent = text;
    if (className) result.className = className; return result;
  };
  const svg = (tag, attrs, text) => {
    const result = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key,value] of Object.entries(attrs)) result.setAttribute(key,value);
    if (text != null) result.textContent = text; chart.append(result); return result;
  };
  const enabled = () => [...document.querySelectorAll('[data-line]:checked')].map(input => input.dataset.line);
  let plotWidth = 920, left = 55;
  const px = i => left + plotWidth * (i-first) / Math.max(1, days.length-1-first);
  const sourceText = counts => Object.entries(counts).map(([key,count]) => `${count} ${classes[key]}`).join(' · ') || 'No scored rides';
  function render() {
    const day = days[selected], lines = enabled(), visible = days.slice(first);
    dateInput.value = day.day; dateInput.min = days[first].day; dateInput.max = days.at(-1).day;
    for (const key of ['fitness','fatigue','form']) {
      document.querySelector(`#training-${key}`).textContent = fmt(day[key]);
      const change = day.changes7[key];
      document.querySelector(`#training-${key}-change`).textContent = change == null ? '7-day change unavailable' : `${change > 0 ? '+' : ''}${fmt(change)} vs 7 days earlier`;
    }
    chart.replaceChildren();
    const widthPixels = Math.max(320,chart.clientWidth), right = widthPixels-15;
    left = 45; plotWidth = right-left;
    chart.setAttribute('viewBox', `0 0 ${widthPixels} 390`);
    const values = visible.flatMap(d => lines.map(key => d[key]));
    let low = Math.min(0,...values), high = Math.max(1,...values);
    const pad = Math.max(2,(high-low)*.08); low -= pad; high += pad;
    const py = value => 245 - 220 * (value-low)/(high-low);
    for (let i=0;i<=4;i++) {
      const value = low+(high-low)*i/4, y=py(value);
      svg('line',{x1:left,x2:right,y1:y,y2:y,class:'chart-grid'});
      svg('text',{x:left-8,y:y+4,'text-anchor':'end'},fmt(value));
    }
    svg('line',{x1:left,x2:right,y1:py(0),y2:py(0),class:'training-zero'});
    svg('text',{x:right,y:py(0)-4,'text-anchor':'end'},'Form zero');
    for (const key of lines) {
      // Every exact day is rendered; selection remains independent of SVG paths.
      const step = 1; let path='';
      for (let i=first;i<days.length;i+=step) path += `${path ? 'L' : 'M'}${px(i).toFixed(2)},${py(days[i][key]).toFixed(2)} `;
      if ((days.length-1-first)%step) path+=`L${px(days.length-1)},${py(days.at(-1)[key])}`;
      svg('path',{d:path,fill:'none',stroke:colors[key],'stroke-width':2,'data-series':key});
      svg('circle',{cx:px(selected),cy:py(day[key]),r:4,fill:colors[key]});
    }
    svg('line',{x1:px(selected),x2:px(selected),y1:20,y2:355,class:'chart-cursor'});
    svg('text',{x:left,y:280},'Daily selected stress');
    const maximum = Math.max(1,...visible.map(d => d.stress));
    const width = Math.max(.4,Math.min(12,plotWidth/visible.length*.75));
    for (let i=first;i<days.length;i++) {
      const d=days[i], keys=Object.keys(d.source_classes);
      const color = keys.length !== 1 || keys[0]==='partial' ? '#768292' : keys[0]==='hr_estimate' ? '#078675' : '#2563eb';
      if (d.stress > 0) svg('rect',{x:px(i)-width/2,y:345-d.stress/maximum*50,width,height:d.stress/maximum*50,fill:color});
      if (d.unscored) svg('text',{x:px(i),y:357,'text-anchor':'middle'},'×');
    }
    svg('line',{x1:left,x2:right,y1:345,y2:345,class:'chart-grid'});
    const tickCount = Math.max(2,Math.min(4,Math.floor(plotWidth/110)));
    for (let tick=0;tick<=tickCount;tick++) {
      const i=first+Math.round((days.length-1-first)*tick/tickCount);
      svg('text',{x:px(i),y:383,'text-anchor':tick===0?'start':tick===tickCount?'end':'middle'},days[i].day);
    }
    chart.setAttribute('aria-label', `${day.day}. Fitness ${fmt(day.fitness)}, Fatigue ${fmt(day.fatigue)}, Form ${fmt(day.form)}. Arrow keys change date.`);
    document.querySelector('#training-chart-readout').textContent = `${day.day} · ${fmt(day.stress)} selected stress · ${day.rides.length} recorded rides${day.early_history_provisional ? ' · early model history provisional' : ''}`;
    document.querySelector('#training-day-heading').textContent = `Selected day · ${day.day}`;
    const detail=document.querySelector('#training-day-detail'); detail.replaceChildren(node('p', `${fmt(day.stress)} selected model stress`));
    if (day.no_record) detail.append(node('p','No recorded ride. Zero recorded model load; rest is not established.'));
    for (const ride of day.rides) {
      const article=node('article',null,'training-ride');
      const link=node('a',ride.title); link.href=`/activities/${ride.activity_id}`; article.append(link);
      article.append(node('p',`${fmt(ride.selected.stress)} · ${classes[ride.selected.status]} · ${ride.selected.scope}`));
      if (ride.selected.status==='unavailable') article.append(node('p','Zero numeric model contribution; stress evidence remains unavailable.'));
      const inspection=node('details'), summary=node('summary','Source and calculation'); inspection.append(summary);
      const evidence={selected:ride.selected,power:ride.power,hr:ride.hr,hr_candidates:ride.hr_candidates,
        ftp:ride.ftp,hr_settings:ride.hr_settings,version:ride.version,timezone_unknown:ride.timezone_unknown};
      inspection.append(node('pre',JSON.stringify(evidence,null,2))); article.append(inspection); detail.append(article);
    }
    const workload=document.querySelector('#training-workload'); workload.replaceChildren();
    for (const n of [7,42]) {
      const w=day[`window${n}`], section=node('section',null,'training-window');
      section.append(node('h3',`Trailing ${n} days`),node('p',`${fmt(w.stress)} stress points · ${w.contributors}/${w.rides} rides scored · ${w.unscored} unscored`),
        node('p',sourceText(w.source_classes)),node('p',`${w.work_contributors===0 && w.rides>0 ? 'Unavailable' : fmt(w.work_kj)} observed kJ · ${w.work_contributors} contributors · ${w.work_omissions} omissions`),
        node('p',`${w.known_missing_power_seconds} known interior missing power seconds · ${w.verified_boundary_missing_seconds} verified boundary missing seconds · ${w.excluded_short_power_seconds} observed seconds excluded from partial stress · ${w.no_record_days} no-record dates`));
      if (w.calendar_days<n) section.append(node('p',`${w.calendar_days} days available since model start`));
      workload.append(section);
    }
  }
  function select(index) { selected=Math.max(first,Math.min(days.length-1,index)); render(); }
  function pointer(event) {
    const bounds=chart.getBoundingClientRect(), x=event.clientX-bounds.left;
    select(first+Math.round((x-left)/plotWidth*(days.length-1-first)));
  }
  chart.addEventListener('pointerdown',event=>{pointer(event);chart.focus();});
  chart.addEventListener('pointermove',event=>{
    if(event.buttons===1) {pointer(event);return;}
    const bounds=chart.getBoundingClientRect(), x=event.clientX-bounds.left;
    const index=Math.max(first,Math.min(days.length-1,first+Math.round((x-left)/plotWidth*(days.length-1-first))));
    const d=days[index];
    document.querySelector('#training-chart-readout').textContent=`Inspect ${d.day} · Fitness ${fmt(d.fitness)} · Fatigue ${fmt(d.fatigue)} · Form ${fmt(d.form)} · ${fmt(d.stress)} stress. Click to select.`;
  });
  chart.addEventListener('pointerleave',render);
  new ResizeObserver(render).observe(chart);
  chart.addEventListener('keydown',event=>{
    const movement={ArrowLeft:-1,ArrowRight:1,ArrowUp:7,ArrowDown:-7};
    if (event.key in movement) {event.preventDefault();select(selected+movement[event.key]);}
    if (event.key==='Home' || event.key==='End') {event.preventDefault();select(event.key==='Home'?first:days.length-1);}
  });
  dateInput.addEventListener('change',()=>{const i=days.findIndex(d=>d.day===dateInput.value);if(i>=first)select(i);else render();});
  for (const input of document.querySelectorAll('[data-line]')) input.addEventListener('change',render);
  for (const button of document.querySelectorAll('[data-range]')) button.addEventListener('click',()=>{
    range=button.dataset.range; first=rangeFirst(range);
    if(selected<first)selected=days.length-1;
    for (const item of document.querySelectorAll('[data-range]')) item.setAttribute('aria-pressed',String(item===button));
    render();
  });
  render();
})();
