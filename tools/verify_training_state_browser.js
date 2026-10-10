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
    return {multi:d.findLast(p=>p.rides.length>1)?.day,missing:d.findLast(p=>p.unscored)?.day,noRecord:d.findLast(p=>p.no_record)?.day};});
  for(const [kind,date] of Object.entries(targets)){assert(!!date,kind+' fixture present');if(!date)continue;
    await page.locator('#training-date').fill(date);await page.locator('#training-date').dispatchEvent('change');const x=await sync();
    if(kind==='multi')assert(x.links.length>1,'multi-ride day links');
    if(kind==='missing')assert((await page.locator('#training-day-detail').textContent()).includes('unavailable'),'unscored evidence remains unavailable');
    if(kind==='noRecord')assert((await page.locator('#training-day-detail').textContent()).includes('rest is not established'),'no-record is not rest');
  }
  await page.locator('#training-chart').focus();await page.keyboard.press('Home');await sync();
  await page.keyboard.press('ArrowRight');await sync();await page.keyboard.press('End');await sync();
  await page.locator('#training-date').fill(targets.multi);await page.locator('#training-date').dispatchEvent('change');
  await page.locator('#training-day-detail details summary').first().click();
  assert((await page.locator('#training-day-detail pre').first().textContent()).includes('method'),'source calculation inspection');
  const url=await page.locator('#training-day-detail article a').first().getAttribute('href');
  await page.goto('http://127.0.0.1:8772'+url);assert((await page.title()).includes('RideWorks'),'stable Activity Review route');
  for(const route of ['/','/performance','/activities']){await page.goto('http://127.0.0.1:8772'+route);assert((await page.title()).includes('RideWorks'),'retained route '+route);}
  await page.goto('http://127.0.0.1:8772/training-state');await page.waitForSelector('#training-date');
  await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'All history',exact:true}).click();
  await sync();const x=await read();assert(x.width<=x.viewport,'phone has no horizontal overflow');
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
  return {checks,passed:true,ranges:4,lineToggles:3,multiRide:true,unscored:true,noRecord:true,keyboard:true,phone:true,touch:true,stableReview:true};
}
