/* Additional before-ride / explicit-intent check on source-neutral preview only. */
async (page) => {
  const base=new URL(page.url()).origin;let assertions=0;
  const check=(v,m)=>{assertions++;if(!v)throw Error(m);};
  const data=async()=>JSON.parse(await page.locator('#plan-data').textContent());
  const next=async()=>page.locator('.next-recommended').evaluate(el=>({day:el.dataset.nextDay,type:el.querySelector('.recommended-type').textContent}));
  await page.setViewportSize({width:1440,height:1080});await page.goto(base+'/plan');await page.waitForLoadState('networkidle');
  const initial=await data();check(initial.today_actual.length===0,'preview before ride');
  check(initial.next_ride.day===initial.today && initial.next_ride.category==='Race','today quality after two recovery dates');
  const primary=await next();
  await page.getByRole('link',{name:'Home',exact:true}).click();await page.waitForLoadState('networkidle');
  check(JSON.stringify(await next())===JSON.stringify(primary),'before-ride Home Plan parity');
  check(await page.locator('.plan-completed').count()===0,'no invented completed today');
  await page.getByRole('link',{name:'View Plan',exact:true}).click();await page.waitForLoadState('networkidle');
  await page.getByRole('button',{name:'Confirm this was a race'}).click();await page.waitForLoadState('networkidle');
  const confirmed=await data();check(confirmed.next_ride.frequency_exception,'third in seven allowed');
  check(confirmed.next_ride.hard_dates_in_window===3,'actual plus upcoming count');
  check(confirmed.next_ride.reason.includes('above the usual two'),'exception reason');
  check(confirmed.days.filter(r=>r.frequency_exception).length===1,'future tail favors two');
  check(await page.locator('.plan-milestone').count()===3,'today hard counts as milestone one');
  await page.evaluate(()=>{const p=document.createElement('p');p.className='plan-status';p.textContent='Synthetic before-ride illustration · conditional third-in-seven opportunity, not live rider data';document.querySelector('main').prepend(p);});
  await page.screenshot({path:'reports/P5-01/plan-v2-synthetic-before.png'});
  await page.getByRole('button',{name:'I plan to do this'}).click();await page.waitForLoadState('networkidle');
  check(await page.locator('.plan-intent-note').textContent().then(t=>t.includes('Recorded intent: Race')),'explicit intent supported before riding');
  await page.getByLabel('Legs today').selectOption('heavy');await page.getByRole('button',{name:'Update',exact:true}).click();await page.waitForLoadState('networkidle');
  check((await data()).next_ride.category==='Recovery','before-ride heavy downgrade');
  check(await page.locator('.plan-intent-note').textContent().then(t=>t.includes('Recorded intent: Race')),'earlier intent not rewritten as current suggestion');
  await page.getByLabel('Legs today').selectOption('unknown');await page.getByRole('button',{name:'Update',exact:true}).click();await page.waitForLoadState('networkidle');
  return {assertions,before_ride:true,third_in_seven:true,explicit_intent:true,synthetic_only:true};
}
