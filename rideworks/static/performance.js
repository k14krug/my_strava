(() => {
  const payload = document.getElementById('performance-points');
  const svg = document.getElementById('performance-chart');
  if (!svg || !payload) return;
  const points = JSON.parse(payload.textContent);
  if (!points.length) return;
  const readout = document.getElementById('performance-readout');
  const dateLabel = document.getElementById('performance-date');
  const activity = document.getElementById('performance-activity');
  const watts = document.getElementById('performance-watts');
  const context = document.getElementById('performance-point-context');
  const ns = 'http://www.w3.org/2000/svg';
  // Coordinate only: unknown-zone dates keep their source calendar position.
  // The readout never converts or labels those dates as an absolute instant.
  const dates = points.map(p => Date.parse(p.absolute_time ? p.start_time : p.date_key + 'Z'));
  let selected = 0, geometry, marker;
  const make = (tag, attrs, text) => {
    const node = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    svg.appendChild(node); return node;
  };
  function inspect(index) {
    selected = Math.max(0, Math.min(points.length - 1, index));
    const p = points[selected];
    readout.dataset.pointIndex = selected;
    dateLabel.dateTime = p.start_time;
    dateLabel.textContent = p.absolute_time ? new Intl.DateTimeFormat(undefined, {
      year:'numeric', month:'short', day:'numeric', hour:'numeric', minute:'2-digit'
    }).format(new Date(p.start_time)) : p.start_time.replace('T', ' ') + ' · timezone unknown';
    activity.textContent = p.title;
    activity.href = '/activities/' + p.activity_id;
    watts.textContent = p.rounded_watts + ' W';
    context.replaceChildren();
    const values = [['Source format', p.content_format], ['Native Source ID', p.source_id],
      ['Extraction ID', p.extraction_id], ['Classification basis', p.classification.basis],
      ['Classification Sources', p.classification.source_ids.join(', ')],
      ['Raw best-20 average (W)', p.average_watts], ['Window start', p.start_timestamp],
      ['Window end (exclusive)', p.end_exclusive_timestamp]];
    values.forEach(([label, value]) => {
      const div = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = label; dd.textContent = value; div.append(dt, dd); context.append(div);
    });
    marker.setAttribute('cx', geometry.x(dates[selected]));
    marker.setAttribute('cy', geometry.y(p.average_watts));
  }
  function draw() {
    const width = Math.max(260, svg.clientWidth), height = 320;
    const left = 48, right = width - 18, top = 24, bottom = height - 38;
    const minimum = Math.min(...dates), maximum = Math.max(...dates);
    const span = Math.max(86400000, maximum - minimum);
    const maximumPower = Math.max(...points.map(p => p.average_watts));
    const tickStep = Math.max(10, Math.ceil(maximumPower / 50) * 10);
    const ceiling = Math.max(tickStep, Math.ceil(maximumPower / tickStep) * tickStep);
    geometry = {x: time => left + (time - minimum) / span * (right - left),
                y: power => bottom - power / ceiling * (bottom - top)};
    svg.replaceChildren(); svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    make('text', {x:6, y:14}, 'W');
    for (let power = 0; power <= ceiling; power += tickStep) {
      const y = geometry.y(power);
      make('line', {x1:left, x2:right, y1:y, y2:y, class:'chart-grid'});
      make('text', {x:left - 8, y:y + 4, 'text-anchor':'end'}, Math.round(power));
    }
    const ticks = width < 500 ? 2 : 5;
    for (let i = 0; i < ticks; i++) {
      const stamp = minimum + (maximum - minimum) * i / (ticks - 1);
      make('text', {x:geometry.x(stamp), y:height - 10,
        'text-anchor':i === 0 ? 'start' : i === ticks - 1 ? 'end' : 'middle'},
        new Intl.DateTimeFormat(undefined, {year:'numeric', month:'short', timeZone:'UTC'}).format(stamp));
    }
    points.forEach((p, i) => make('circle', {cx:geometry.x(dates[i]), cy:geometry.y(p.average_watts),
      r:2.5, class:'performance-point', 'data-point-index':i}));
    marker = make('circle', {r:5, class:'performance-selected', 'pointer-events':'none'});
    inspect(selected);
  }
  function nearest(event) {
    const box = svg.getBoundingClientRect(), x = event.clientX - box.left, y = event.clientY - box.top;
    let best = Infinity, index = 0;
    points.forEach((p, i) => {
      const distance = (geometry.x(dates[i]) - x) ** 2 + (geometry.y(p.average_watts) - y) ** 2;
      if (distance < best) { best = distance; index = i; }
    });
    return index;
  }
  svg.addEventListener('pointermove', event => inspect(nearest(event)));
  svg.addEventListener('click', event => { inspect(nearest(event)); location.href = activity.href; });
  svg.addEventListener('keydown', event => {
    if (event.key === 'Enter') { event.preventDefault(); location.href = activity.href; return; }
    const choices = {ArrowLeft:selected - 1, ArrowRight:selected + 1, Home:0, End:points.length - 1};
    if (event.key in choices) { event.preventDefault(); inspect(choices[event.key]); }
  });
  new ResizeObserver(draw).observe(svg);
})();
