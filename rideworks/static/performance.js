(() => {
  const payload = document.getElementById('performance-points');
  const svg = document.getElementById('performance-chart');
  if (!svg || !payload) return;
  const points = JSON.parse(payload.textContent);
  const view = JSON.parse(document.getElementById('performance-view').textContent);
  if (!points.length) return;
  const $ = id => document.getElementById(id), ns = 'http://www.w3.org/2000/svg';
  const asOf = Date.parse(view.as_of);
  // Unknown source days have calendar coordinates, never an inferred instant.
  const dates = points.map(p => Date.parse(p.absolute_time ? p.start_time : p.date_key + 'Z'));
  const localDate = (p, clock = true) => p.absolute_time
    ? new Intl.DateTimeFormat(undefined, {year:'numeric', month:'short', day:'numeric',
      ...(clock ? {hour:'numeric', minute:'2-digit'} : {})}).format(new Date(p.start_time))
    : (clock ? p.start_time.replace('T', ' ') : p.date_day) + ' · timezone unknown';
  const year = p => p.absolute_time ? new Date(p.start_time).getFullYear() : Number(p.date_day.slice(0, 4));
  const query = new URLSearchParams(location.search);
  let mode = ['current','trend','history'].includes(query.get('mode')) ? query.get('mode') : 'trend';
  let range = ['3mo','6mo','1yr','3yr','all'].includes(query.get('range')) ? query.get('range') : '1yr';
  let rides = query.get('rides') === '1', pageNumber = 0;
  let visible = [], series = [], peaks = [], targets = [], selected = null, geometry, marker;
  const make = (tag, attrs, text) => {
    const node = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    svg.appendChild(node); return node;
  };
  const best = indexes => indexes.reduce((winner, i) => winner === null || points[i].average_watts > points[winner].average_watts
    || (points[i].average_watts === points[winner].average_watts &&
      (points[i].date_key < points[winner].date_key || (points[i].date_key === points[winner].date_key && points[i].activity_id < points[winner].activity_id))) ? i : winner, null);
  const saveState = () => {
    const url = new URL(location.href);
    url.searchParams.set('mode', mode); url.searchParams.set('range', range); url.searchParams.set('rides', rides ? '1' : '0');
    history.replaceState(null, '', url);
  };
  function inspect(target) {
    selected = target;
    const index = target?.index, p = index === null || index === undefined ? null : points[index];
    $('performance-readout').dataset.pointIndex = p ? index : '';
    $('performance-selection-label').textContent = target?.kind === 'trend'
      ? '42-day best at ' + new Intl.DateTimeFormat(undefined, {year:'numeric',month:'short',day:'numeric'}).format(target.time)
      : mode === 'history' ? 'Annual peak in selected range' : 'Eligible ride result';
    $('performance-point-context').replaceChildren();
    if (!p) {
      $('performance-date').textContent = '';
      $('performance-activity').textContent = 'No qualifying result in this 42-day window';
      $('performance-activity').removeAttribute('href'); $('performance-watts').textContent = 'Unavailable';
      if (marker) marker.setAttribute('visibility', 'hidden'); return;
    }
    $('performance-date').dateTime = p.start_time; $('performance-date').textContent = localDate(p);
    $('performance-activity').textContent = p.title; $('performance-activity').href = '/activities/' + p.activity_id;
    $('performance-watts').textContent = p.rounded_watts + ' W';
    const values = [['Source format', p.content_format], ['Native Source ID', p.source_id],
      ['Extraction ID', p.extraction_id], ['Classification basis', p.classification.basis],
      ['Classification Sources', p.classification.source_ids.join(', ')],
      ['Raw best-20 average (W)', p.average_watts], ['Window start', p.start_timestamp],
      ['Window end (exclusive)', p.end_exclusive_timestamp]];
    values.forEach(([label, value]) => {
      const div = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = label; dd.textContent = value; div.append(dt, dd); $('performance-point-context').append(div);
    });
    if (marker && geometry) {
      marker.setAttribute('visibility', 'visible');
      marker.setAttribute('cx', mode === 'history' ? geometry.peakX(index) : geometry.x(target.time));
      marker.setAttribute('cy', geometry.y(p.average_watts));
    }
  }
  function evidenceTable() {
    const ordered = [...visible].reverse(), pages = Math.max(1, Math.ceil(ordered.length / 30));
    pageNumber = Math.max(0, Math.min(pageNumber, pages - 1));
    const body = $('performance-rides'); body.replaceChildren();
    ordered.slice(pageNumber * 30, (pageNumber + 1) * 30).forEach(i => {
      const p = points[i], tr = document.createElement('tr'); tr.dataset.pointIndex = i;
      const dateCell = document.createElement('td'), titleCell = document.createElement('td'), wattCell = document.createElement('td');
      const time = document.createElement('time'); time.dateTime = p.start_time; time.textContent = localDate(p, false); dateCell.append(time);
      const a = document.createElement('a'); a.href = '/activities/' + p.activity_id; a.textContent = p.title; titleCell.append(a);
      wattCell.textContent = p.rounded_watts + ' W'; tr.append(dateCell, titleCell, wattCell); body.append(tr);
    });
    $('performance-evidence-count').textContent = '(' + visible.length.toLocaleString() + ')';
    $('performance-rides-page').textContent = 'Page ' + (pageNumber + 1) + ' of ' + pages;
    $('performance-rides-prev').disabled = pageNumber === 0; $('performance-rides-next').disabled = pageNumber === pages - 1;
  }
  function prepare() {
    const minimum = range === 'all' ? Math.min(...dates, asOf) : Date.parse(view.range_starts[range]);
    visible = points.map((_, i) => i).filter(i => dates[i] >= minimum && dates[i] <= asOf);
    const before = view.rolling.filter(s => Date.parse(s.at) <= minimum).at(-1);
    series = [{time:minimum, index:before?.index ?? null, kind:'trend'}];
    view.rolling.forEach(s => {const time = Date.parse(s.at); if (time > minimum && time <= asOf) series.push({time, index:s.index, kind:'trend'});});
    series.push({time:asOf, index:series.at(-1).index, kind:'trend'});
    const groups = new Map();
    visible.forEach(i => {const key = year(points[i]); if (!groups.has(key)) groups.set(key, []); groups.get(key).push(i);});
    peaks = [...groups].sort(([a],[b]) => a - b).map(([label, indexes]) => ({index:best(indexes), label, kind:'peak'}));
    targets = mode === 'history' ? peaks : rides ? visible.map(i => ({index:i,time:dates[i],kind:'ride'})) : series.filter(s => s.index !== null);
    svg.dataset.mode = mode; svg.dataset.range = range; svg.dataset.visibleRides = visible.length;
    $('performance-chart-title').textContent = mode === 'current' ? 'Recently demonstrated' : mode === 'history' ? 'Annual peaks' : 'Rolling 42-day best';
    $('performance-chart-caption').textContent = mode === 'current' ? 'Recent qualifying evidence and its freshness'
      : mode === 'history' ? 'Strongest eligible result in each displayed year within this range' : 'Strongest qualifying ride in each trailing 42-day window';
    document.querySelectorAll('.performance-modes [data-mode]').forEach(b => b.setAttribute('aria-selected', b.dataset.mode === mode));
    document.querySelectorAll('[data-range]').forEach(b => b.setAttribute('aria-pressed', b.dataset.range === range));
    document.querySelectorAll('[data-evidence]').forEach(b => b.setAttribute('aria-pressed', (b.dataset.evidence === 'rides') === rides));
    document.querySelector('.performance-ranges').hidden = mode === 'current';
    document.querySelector('.performance-evidence-control').hidden = mode !== 'trend';
    svg.toggleAttribute('hidden', mode === 'current'); $('performance-current').hidden = mode !== 'current'; $('performance-chart-help').hidden = mode === 'current';
    $('performance-visible-count').textContent = visible.length.toLocaleString() + ' eligible rides in range';
    const freshness = index => index === null ? 'No qualifying result' : view.ages_days[String(index)] === undefined ? 'Source timezone unknown' : 'Demonstrated ' + view.ages_days[String(index)] + ' days ago';
    $('performance-current').replaceChildren();
    for (const [label, index] of [['42-day best evidence', view.summaries.current], ['Latest ride evidence', view.summaries.latest]]) {
      const p = document.createElement('p'), strong = document.createElement('strong'); strong.textContent = label;
      p.append(strong, document.createTextNode(freshness(index))); $('performance-current').append(p);
    }
    evidenceTable(); return {minimum, maximum:asOf};
  }
  function draw(reset = false) {
    const bounds = prepare(); svg.replaceChildren(); marker = null;
    if (mode === 'current') { $('performance-chart-empty').hidden = true; inspect({index:view.summaries.current,kind:'ride',time:asOf}); return; }
    const width = Math.max(260, svg.clientWidth), height = 310, left = 44, right = width - 18, top = 18, bottom = height - 34;
    const chartIndexes = mode === 'history' ? peaks.map(p => p.index) : [...visible, ...series.filter(s => s.index !== null).map(s => s.index)];
    const maxPower = Math.max(0, ...chartIndexes.map(i => points[i].average_watts));
    const step = Math.max(10, Math.ceil(maxPower / 50) * 10), ceiling = Math.max(step, Math.ceil(maxPower / step) * step);
    geometry = {x:time => left + (time - bounds.minimum) / Math.max(86400000,bounds.maximum - bounds.minimum) * (right - left),
      y:power => bottom - power / ceiling * (bottom - top), peakX:index => left + (peaks.findIndex(p => p.index === index) + .5) / Math.max(1,peaks.length) * (right - left)};
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`); make('text', {x:4,y:14}, 'W');
    for (let power = 0; power <= ceiling; power += step) {
      const y = geometry.y(power); make('line', {x1:left,x2:right,y1:y,y2:y,class:'chart-grid'});
      make('text', {x:left - 8,y:y + 4,'text-anchor':'end'}, power);
    }
    if (mode === 'history') {
      peaks.forEach(p => {
        const x = geometry.peakX(p.index), y = geometry.y(points[p.index].average_watts), barWidth = Math.min(34,(right-left)/peaks.length*.35);
        make('rect', {x:x-barWidth/2,y,width:barWidth,height:Math.max(1,bottom-y),class:'performance-peak','data-point-index':p.index});
        if (width >= 500 || peaks.length <= 5) make('text', {x,y:y-8,'text-anchor':'middle'}, points[p.index].rounded_watts+' W');
        make('text', {x,y:height-10,'text-anchor':'middle'}, p.label);
      });
    } else {
      const ticks = width < 500 ? 3 : 6;
      for (let i = 0; i < ticks; i++) {
        const time = bounds.minimum + (bounds.maximum - bounds.minimum) * i / (ticks - 1);
        make('text', {x:geometry.x(time),y:height-10,'text-anchor':i===0?'start':i===ticks-1?'end':'middle'},
          new Intl.DateTimeFormat(undefined,{month:'short',year:range==='all'||range==='3yr'?'numeric':undefined}).format(time));
      }
      if (rides) visible.forEach(i => make('circle', {cx:geometry.x(dates[i]),cy:geometry.y(points[i].average_watts),r:2,class:'performance-point','data-point-index':i}));
      let path = '', active = false;
      series.forEach(s => {
        const x = geometry.x(s.time);
        if (s.index === null) {if (active) path += ` H${x}`; active=false; return;}
        const y=geometry.y(points[s.index].average_watts); path += active ? ` H${x} V${y}` : ` M${x},${y}`; active=true;
      });
      if (path) make('path',{d:path,class:'performance-trend'});
    }
    marker=make('circle',{r:4,class:'performance-selected','pointer-events':'none'});
    $('performance-chart-empty').hidden=targets.length!==0;
    const previous=selected&&targets.find(t=>t.index===selected.index&&t.kind===selected.kind&&t.time===selected.time);
    inspect(!reset&&previous?previous:targets.at(-1)??null);
  }
  function pointerTarget(event) {
    const box=svg.getBoundingClientRect(),x=event.clientX-box.left,y=event.clientY-box.top;
    if(mode==='history') return peaks.reduce((best,p)=>!best||Math.abs(geometry.peakX(p.index)-x)<Math.abs(geometry.peakX(best.index)-x)?p:best,null);
    if(rides) {
      let nearest=null,distance=64;
      visible.forEach(i=>{const d=(geometry.x(dates[i])-x)**2+(geometry.y(points[i].average_watts)-y)**2;
        if(d<distance){distance=d;nearest={index:i,time:dates[i],kind:'ride'};}});
      if(nearest)return nearest;
    }
    return series.filter(s=>geometry.x(s.time)<=x).at(-1)??series[0];
  }
  document.querySelectorAll('.performance-modes [data-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;pageNumber=0;saveState();draw(true);}));
  document.querySelectorAll('[data-range]').forEach(b=>b.addEventListener('click',()=>{range=b.dataset.range;pageNumber=0;saveState();draw(true);}));
  document.querySelectorAll('[data-evidence]').forEach(b=>b.addEventListener('click',()=>{rides=b.dataset.evidence==='rides';saveState();draw(true);}));
  $('performance-rides-prev').addEventListener('click',()=>{pageNumber--;evidenceTable();});
  $('performance-rides-next').addEventListener('click',()=>{pageNumber++;evidenceTable();});
  svg.addEventListener('pointermove',event=>inspect(pointerTarget(event)));
  svg.addEventListener('click',event=>{inspect(pointerTarget(event));if($('performance-activity').hasAttribute('href'))location.href=$('performance-activity').href;});
  svg.addEventListener('keydown',event=>{
    if(event.key==='Enter'){event.preventDefault();if($('performance-activity').hasAttribute('href'))location.href=$('performance-activity').href;return;}
    const index=targets.findIndex(t=>t.index===selected?.index&&t.time===selected?.time&&t.kind===selected?.kind);
    const choices={ArrowLeft:index-1,ArrowRight:index+1,Home:0,End:targets.length-1};
    if(event.key in choices){event.preventDefault();inspect(targets[Math.max(0,Math.min(targets.length-1,choices[event.key]))]??null);}
  });
  draw(true);new ResizeObserver(()=>draw()).observe(svg);
})();
