async (page) => {
  const failures=[];let checks=0;
  const assert=(value,message)=>{checks++;if(!value)failures.push(message);};
  const read=async()=>await page.evaluate(()=>{
    const data=JSON.parse(document.querySelector('#training-state-data').textContent);
    const date=document.querySelector('#training-date').value;
    const day=data.days.find(d=>d.day===date);
    return {date,day,values:['fitness','fatigue','form'].map(k=>document.querySelector(`#training-${k}`).textContent),
      heading:document.querySelector('#training-day-heading').textContent,
      links:[...document.querySelectorAll('#training-day-detail article a')].map(a=>a.getAttribute('href')),
      width:document.documentElement.scrollWidth,viewport:innerWidth,
      sourceCount:document.querySelectorAll('#training-chart [data-series]').length};
  });
  const sync=async()=>{const x=await read();assert(x.heading.includes(x.date),'selected date/detail synchronization');
    for(let i=0;i<3;i++)assert(x.values[i]===x.day[['fitness','fatigue','form'][i]].toLocaleString(undefined,{minimumFractionDigits:1,maximumFractionDigits:1}),'selected numeric synchronization');
    assert(x.links.length===x.day.rides.length,'selected activity links match exact daily records');return x;};
  await page.setViewportSize({width:1280,height:900});
  await page.goto('http://127.0.0.1:8772/training-state');await page.waitForSelector('#training-date');
  await sync();
  for(const name of ['Fitness','Fatigue','Form']){await page.getByRole('checkbox',{name,exact:true}).uncheck();}
  assert((await read()).sourceCount===0,'all line toggles off');
  for(const name of ['Fitness','Fatigue','Form']){await page.getByRole('checkbox',{name,exact:true}).check();}
  assert((await read()).sourceCount===3,'all line toggles on');
  for(const name of ['6 weeks','3 months','12 months','All history']){await page.getByRole('button',{name,exact:true}).click();await sync();}
  const targets=await page.evaluate(()=>{const d=JSON.parse(document.querySelector('#training-state-data').textContent).days;
    return {multi:d.findLast(p=>p.rides.length>1)?.day,missing:d.findLast(p=>p.unscored)?.day,noRecord:d.findLast(p=>p.no_record)?.day,summary:d.findLast(p=>p.rides.some(r=>r.selected.method==='hr'&&r.hr.evidence_kind==='summary'&&r.hr.stream_rejections.length))?.day};});
  for(const [kind,date] of Object.entries(targets)){assert(!!date,kind+' fixture present');if(!date)continue;
    await page.locator('#training-date').fill(date);await page.locator('#training-date').dispatchEvent('change');const x=await sync();
    if(kind==='summary')assert((await page.locator('#training-day-detail').textContent()).includes('HR summary estimate')&&(await page.locator('#training-day-detail').textContent()).includes('unverified'),'summary fallback label and uncertainty in persistent inspection');
    if(kind==='multi')assert(x.links.length>1,'multi-ride day links');
    if(kind==='missing')assert((await page.locator('#training-day-detail').textContent()).includes('unavailable'),'unscored evidence remains unavailable');
    if(kind==='noRecord')assert((await page.locator('#training-day-detail').textContent()).includes('rest is not established'),'no-record is not rest');
  }
  const hover=async(date,y=110)=>{
    const point=await page.evaluate(({date,y})=>{
      const chart=document.querySelector('#training-chart'),days=JSON.parse(document.querySelector('#training-state-data').textContent).days;
      const first=days.findIndex(d=>d.day===document.querySelector('#training-date').min),i=days.findIndex(d=>d.day===date);
      const p=chart.createSVGPoint();p.x=45+(chart.viewBox.baseVal.width-60)*(i-first)/Math.max(1,days.length-1-first);p.x+=i===first?.01:i===days.length-1?-.01:0;p.y=y;
      const screen=p.matrixTransform(chart.getScreenCTM());return {x:screen.x,y:screen.y};
    },{date,y});
    await page.mouse.move(point.x,point.y);await page.locator('#training-tooltip').waitFor({state:'visible'});
    const t=await page.locator('#training-tooltip').evaluate(el=>({day:el.dataset.day,text:el.textContent,
      x:el.getBoundingClientRect().x,y:el.getBoundingClientRect().y,w:el.offsetWidth,h:el.offsetHeight}));
    assert(t.day===date,'hover exact nearest day');
    assert(t.x>=7&&t.y>=7&&t.x+t.w<=1280-7&&t.y+t.h<=900-7,'hover fits viewport edges');
    assert(Math.min(Math.abs(t.x-point.x),Math.abs(t.x+t.w-point.x))<=15,'tooltip near cursor horizontally');
    assert(await page.locator('.training-hover-guide').getAttribute('visibility')==='visible','vertical hover guide visible');
    const expected=await page.evaluate(date=>JSON.parse(document.querySelector('#training-state-data').textContent).days.find(d=>d.day===date),date);
    for(const k of ['fitness','fatigue','form'])assert(t.text.includes(expected[k].toLocaleString(undefined,{minimumFractionDigits:1,maximumFractionDigits:1})),'hover '+k+' exact numeric value');
    assert(t.text.includes('start of day'),'hover Form timing');
    assert(t.text.includes(expected.rides.length+' recorded'),'hover ride count');
    for(const ride of expected.rides){
      assert(t.text.includes(ride.title),'hover full ride title');
      const candidate=ride.selected.method==='hr'?ride.hr:ride.power;
      if(candidate.source?.format)assert(t.text.includes(candidate.source.format),'hover selected source format');
    }
    if(expected.rides.some(r=>r.selected.method==='hr'&&r.hr.evidence_kind==='summary')){
      assert(t.text.includes('HR summary estimate'),'hover summary estimate label');
      assert(t.text.includes('active coverage and pause treatment unverified'),'hover summary uncertainty');
    }
    if(expected.unscored)assert(t.text.includes('Stress unavailable'),'hover missing stress explicit');
    return point;
  };
  for(const name of ['6 weeks','3 months','12 months','All history']){
    await page.getByRole('button',{name,exact:true}).click();await page.locator('#training-chart').scrollIntoViewIfNeeded();
    await page.waitForTimeout(80);
    const edges=await page.evaluate(()=>({first:document.querySelector('#training-date').min,last:document.querySelector('#training-date').max}));
    const selected=await page.locator('#training-date').inputValue();
    await hover(edges.first);await hover(edges.last,320);
    assert(await page.locator('#training-date').inputValue()===selected,'hover preserves selected date in '+name);
    await page.mouse.move(5,5);assert(!await page.locator('#training-tooltip').isVisible(),'mouseleave dismisses overlay');
    assert(await page.locator('.training-hover-guide').getAttribute('visibility')==='hidden','mouseleave dismisses hover guide');
  }
  for(const date of Object.values(targets)){
    const point=await hover(date,320);await page.mouse.click(point.x,point.y);await sync();
    await page.mouse.move(5,5);assert(!await page.locator('#training-tooltip').isVisible(),'click overlay dismissed on leave');
    assert(await page.locator('#training-date').inputValue()===date,'clicked selection persists after leave');
  }
  const longest=await page.evaluate(()=>JSON.parse(document.querySelector('#training-state-data').textContent).days.filter(d=>d.rides.length).sort((a,b)=>Math.max(...b.rides.map(r=>r.title.length))-Math.max(...a.rides.map(r=>r.title.length)))[0].day);
  await hover(longest);await page.mouse.move(5,5);
  await page.locator('#training-chart').focus();await page.keyboard.press('Home');await sync();
  await page.keyboard.press('ArrowRight');await sync();
  assert(await page.locator('#training-tooltip').getAttribute('data-day')===await page.locator('#training-date').inputValue(),'keyboard tooltip date equivalence');
  await page.keyboard.press('Escape');assert(!await page.locator('#training-tooltip').isVisible(),'Escape dismisses tooltip');
  await page.keyboard.press('End');await sync();
  await page.locator('#training-date').fill(targets.multi);await page.locator('#training-date').dispatchEvent('change');
  await page.locator('#training-day-detail details summary').first().click();
  assert((await page.locator('#training-day-detail pre').first().textContent()).includes('method'),'source calculation inspection');
  const url=await page.locator('#training-day-detail article a').first().getAttribute('href');
  await page.goto('http://127.0.0.1:8772'+url);assert((await page.title()).includes('RideWorks'),'stable Activity Review route');
  for(const route of ['/','/performance','/activities']){await page.goto('http://127.0.0.1:8772'+route);assert((await page.title()).includes('RideWorks'),'retained route '+route);}
  await page.goto('http://127.0.0.1:8772/training-state');await page.waitForSelector('#training-date');
  await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'All history',exact:true}).click();
  await sync();const x=await read();assert(x.width<=x.viewport,'phone has no horizontal overflow');
  await page.locator('#training-chart').focus();
  for(const key of ['Home','End']){
    await page.keyboard.press(key);await sync();
    const t=await page.locator('#training-tooltip').boundingBox();
    assert(!!t,'phone keyboard overlay visible');
    assert(t&&t.x>=7&&t.y>=7&&t.x+t.width<=383&&t.y+t.height<=837,'phone overlay fits after date change');
  }
  const box=await page.locator('#training-chart').boundingBox();await page.mouse.click(box.x+box.width*.7,box.y+box.height*.4);await sync();
  await page.screenshot({path:'output/playwright/p4-02-phone-final.png',fullPage:true});
  await page.setViewportSize({width:1280,height:900});await page.getByRole('button',{name:'3 months',exact:true}).click();await sync();
  await page.screenshot({path:'output/playwright/p4-02-desktop-final.png',fullPage:true});
  const context=await page.context().browser().newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,timezoneId:'America/Los_Angeles'});
  const touchPage=await context.newPage();await touchPage.goto('http://127.0.0.1:8772/training-state');await touchPage.waitForSelector('#training-date');
  const oldDate=await touchPage.locator('#training-date').inputValue();await touchPage.locator('#training-chart').scrollIntoViewIfNeeded();
  const touchBox=await touchPage.locator('#training-chart').boundingBox();
  await touchPage.touchscreen.tap(touchBox.x+touchBox.width*.35,touchBox.y+touchBox.height*.35);
  const touchDate=await touchPage.locator('#training-date').inputValue();assert(oldDate!==touchDate,'touch selects historical date');
  assert((await touchPage.locator('#training-day-heading').textContent()).includes(touchDate),'touch synchronizes selected-day details');
  await context.close();
  if(failures.length)throw new Error(JSON.stringify({checks,failures}));
  return {checks,passed:true,ranges:4,lineToggles:3,multiRide:true,unscored:true,noRecord:true,keyboard:true,phone:true,touch:true,stableReview:true,floatingHover:true,hoverPersistence:true,hoverAllRanges:true};
}
