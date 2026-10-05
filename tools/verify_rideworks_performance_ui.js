// Actual browser acceptance; private sample metadata stays inside the browser.
async (page) => {
  const base = BASE_URL, expected = EXPECTED_COUNT;
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  await page.goto(base+'/');
  await page.getByRole('navigation',{name:'Main',exact:true}).getByRole('link',{name:'Performance',exact:true}).click();
  await page.waitForSelector('.performance-trend');
  const points=await page.locator('#performance-points').evaluate(node=>JSON.parse(node.textContent));
  const view=await page.locator('#performance-view').evaluate(node=>JSON.parse(node.textContent));
  check(points.length===expected,'Payload omits eligible history');
  check(await page.locator('nav a[aria-current="page"]').textContent()==='Performance','Active navigation is wrong');
  check(points.every(p=>p.classification.activity_type==='Virtual Ride'),'Excluded activity in chart');
  check(await page.locator('#native-records').count()===0,'Native streams in Performance');
  const html=await page.content();
  for(const token of ['stored_path','latitude','longitude','native_records']) check(!html.includes(token),'Private/native evidence in page');
  const verifyReadout=async p=>{
    const index=Number(await p.locator('#performance-readout').getAttribute('data-point-index'));
    check(await p.locator('#performance-activity').textContent()===points[index].title,'Source title differs');
    check(await p.locator('#performance-watts').textContent()===points[index].rounded_watts+' W','Watts differ');
    check(await p.locator('#performance-activity').getAttribute('href')==='/activities/'+points[index].activity_id,'Route differs');
    return index;
  };
  const chart=page.locator('#performance-chart');
  check(await chart.getAttribute('data-mode')==='trend'&&await chart.getAttribute('data-range')==='1yr','Wrong default view');
  check(await page.locator('.performance-point').count()===0,'Default chart is noisy ride scatter');
  check(await verifyReadout(page)===view.summaries.current,'Default selected result is not recent meaningful evidence');
  for(const key of ['current','latest','year','lifetime']) {
    const card=page.locator('[data-summary="'+key+'"]');
    check(Number(await card.getAttribute('data-point-index'))===view.summaries[key],'Summary context differs');
    check((await card.textContent()).includes(String(points[view.summaries[key]].rounded_watts)),'Summary watts missing');
  }
  for(const key of ['3mo','6mo','1yr','3yr','all']) {
    await page.locator('[data-range="'+key+'"]').click();
    const cutoff=key==='all'?-Infinity:Date.parse(view.range_starts[key]);
    const expectedCount=points.filter(p=>Date.parse(p.start_time)>=cutoff&&Date.parse(p.start_time)<=Date.parse(view.as_of)).length;
    check(Number(await chart.getAttribute('data-visible-rides'))===expectedCount,'Range count differs');
    check(await page.locator('.performance-trend').count()===1,'Range loses primary trend');
  }
  await page.locator('.performance-modes [data-mode="current"]').click();
  check(await chart.isHidden(),'Current should emphasize evidence without a large chart');
  check((await page.locator('#performance-current').textContent()).includes('days ago'),'Current freshness unavailable');
  check(await verifyReadout(page)===view.summaries.current,'Current result differs');
  await page.locator('.performance-modes [data-mode="history"]').click();
  const annual=await page.evaluate(points=>{
    const groups=new Map();
    points.forEach((p,i)=>{const year=new Date(p.start_time).getFullYear();const prior=groups.get(year);
      if(prior===undefined||p.average_watts>points[prior].average_watts)groups.set(year,i);});
    return [...groups].sort(([a],[b])=>a-b).map(([,i])=>i);
  },points);
  const bars=await page.locator('.performance-peak').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.pointIndex)));
  check(JSON.stringify(bars)===JSON.stringify(annual),'Annual peaks differ from raw result maxima');
  check(await verifyReadout(page)===annual.at(-1),'History defaults to oldest peak');
  await chart.focus();await page.keyboard.press('Home');check(await verifyReadout(page)===annual[0],'History Home failed');
  await page.keyboard.press('End');check(await verifyReadout(page)===annual.at(-1),'History End failed');
  await page.getByText('Eligible ride results',{exact:false}).last().click();
  const seen=new Set();
  while(true) {
    const indexes=await page.locator('#performance-rides tr').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.pointIndex)));
    check(indexes.length<=30,'Unbounded evidence table');indexes.forEach(i=>seen.add(i));
    if(await page.locator('#performance-rides-next').isDisabled())break;
    await page.locator('#performance-rides-next').click();
  }
  check(seen.size===expected,'Complete supporting history is not inspectable');
  await page.locator('.performance-modes [data-mode="trend"]').click();
  await page.locator('[data-evidence="rides"]').click();
  check(await page.locator('.performance-point').count()===expected,'All-range ride evidence omits points');
  check(await page.locator('.performance-trend').count()===1,'Ride evidence removes primary trend');
  for(const i of [0,Math.floor(points.length/2),points.length-1]) {
    const box=await page.locator('.performance-point').nth(i).boundingBox();
    await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await verifyReadout(page);
  }
  await chart.focus();await page.keyboard.press('Home');check(await verifyReadout(page)===0,'Ride Home failed');
  for(let i=0;i<Math.floor(points.length/2);i++)await page.keyboard.press('ArrowRight');
  check(await verifyReadout(page)===Math.floor(points.length/2),'Middle keyboard failed');
  await page.keyboard.press('End');check(await verifyReadout(page)===points.length-1,'Ride End failed');
  await page.keyboard.press('Enter');await page.waitForURL(base+'/activities/'+points.at(-1).activity_id);
  check(await page.locator('h1').textContent()===points.at(-1).title,'Activity title differs');
  await page.goBack();await page.waitForSelector('.performance-point');
  const box=await page.locator('.performance-point').last().boundingBox();
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
  const pointerRoute=await page.locator('#performance-activity').getAttribute('href');
  await page.mouse.click(box.x+box.width/2,box.y+box.height/2);await page.waitForURL(base+pointerRoute);
  await page.goBack();await page.waitForSelector('.performance-point');
  await page.getByText('Selected result provenance',{exact:true}).click();
  check((await page.locator('#performance-point-context').textContent()).includes('Extraction ID'),'Provenance missing');
  await page.getByText('Eligibility & method',{exact:true}).click();
  const policy=await page.locator('.performance-policy').textContent();
  check(policy.includes('best-average-power-v1')&&policy.includes('Outdoor Ride power is excluded')&&policy.includes('never substitute'),'Trust explanation missing');
  for(const zone of ['America/Los_Angeles','Asia/Tokyo']) {
    const context=await page.context().browser().newContext({timezoneId:zone,viewport:{width:1448,height:1086}});
    try {
      const probe=await context.newPage();await probe.goto(base+'/performance');await probe.waitForSelector('.performance-trend');
      const index=Number(await probe.locator('#performance-readout').getAttribute('data-point-index'));
      const expectedDate=await probe.evaluate(p=>new Intl.DateTimeFormat(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(p.start_time)),points[index]);
      check(await probe.locator('#performance-date').textContent()===expectedDate,'Date is not browser-local');
    } finally {await context.close();}
  }
  await page.goto(base+'/performance');await page.waitForSelector('.performance-trend');
  for(const [width,height] of [[1448,1086],[1024,900],[390,844]]) {
    await page.setViewportSize({width,height});
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Responsive horizontal overflow');
    check((await chart.boundingBox()).height>=300,'Responsive chart is decorative/tiny');
    for(const mode of ['current','history','trend']) {
      await page.locator('.performance-modes [data-mode="'+mode+'"]').click();
      check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mode horizontal overflow');
    }
  }
  await page.screenshot({path:'output/playwright/p2-03-performance-phone.png',fullPage:true});
  await page.setViewportSize({width:1448,height:1086});
  await page.screenshot({path:'output/playwright/p2-03-performance-desktop.png',fullPage:true});
  await page.locator('.performance-modes [data-mode="current"]').click();
  await page.screenshot({path:'output/playwright/p2-03-current-desktop.png',fullPage:true});
  await page.locator('.performance-modes [data-mode="history"]').click();await page.locator('[data-range="all"]').click();
  await page.screenshot({path:'output/playwright/p2-03-history-desktop.png',fullPage:true});
  await page.goto(base+'/performance');await page.waitForSelector('.performance-trend');
  return {result:'passed',browser:'Chromium',payload_eligible_results:points.length,all_range_ride_points:points.length,
    default_trend_one_year:true,rolling_line_dominant:true,current_trend_history:true,all_range_controls:true,
    summaries_and_freshness:true,annual_peaks_verified:true,complete_paged_evidence:true,
    first_middle_last_pointer:true,keyboard_inspection:true,point_activity_and_back:true,
    source_title_date_watts:true,eligibility_provenance:true,local_date_zones:['America/Los_Angeles','Asia/Tokyo'],
    desktop_tablet_phone_no_overflow:true,no_native_stream_payload:true};
}
