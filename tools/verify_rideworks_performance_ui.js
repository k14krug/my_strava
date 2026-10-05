// Executed locally in Playwright CLI; emits aggregate verification only.
async (page) => {
  const base = BASE_URL;
  const expected = EXPECTED_COUNT;
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  await page.goto(base+'/');
  await page.getByRole('navigation',{name:'Main',exact:true}).getByRole('link',{name:'Performance',exact:true}).click();
  await page.waitForSelector('.performance-point');
  const points=await page.locator('#performance-points').evaluate(node=>JSON.parse(node.textContent));
  check(points.length===expected,'Payload omits eligible history');
  check(await page.locator('.performance-point').count()===expected,'Chart omits points');
  check(await page.locator('nav a[aria-current="page"]').textContent()==='Performance','Active navigation is wrong');
  check(points.every(p=>p.classification.activity_type==='Virtual Ride'),'Excluded activity in chart');
  check(await page.locator('#native-records').count()===0,'Native streams in Performance page');
  const verifyReadout=async p=>{
    const index=Number(await p.locator('#performance-readout').getAttribute('data-point-index'));
    check(await p.locator('#performance-activity').textContent()===points[index].title,'Source title readout differs');
    check(await p.locator('#performance-watts').textContent()===points[index].rounded_watts+' W','Watt readout differs');
    check(await p.locator('#performance-activity').getAttribute('href')==='/activities/'+points[index].activity_id,'Point route differs');
    return index;
  };
  const chart=page.locator('#performance-chart');
  for(const i of [0,Math.floor(points.length/2),points.length-1]) {
    const box=await page.locator('.performance-point').nth(i).boundingBox();
    await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
    await verifyReadout(page);
  }
  const pointerRoute=await page.locator('#performance-activity').getAttribute('href');
  const pointerBox=await page.locator('.performance-point').last().boundingBox();
  await page.mouse.click(pointerBox.x+pointerBox.width/2,pointerBox.y+pointerBox.height/2);
  await page.waitForURL(base+pointerRoute);
  await page.goBack(); await page.waitForSelector('.performance-point');
  await chart.focus();
  await page.keyboard.press('Home'); check(await verifyReadout(page)===0,'Home inspection failed');
  for(let i=0;i<Math.floor(points.length/2);i++) await page.keyboard.press('ArrowRight');
  check(await verifyReadout(page)===Math.floor(points.length/2),'Middle keyboard inspection failed');
  await page.keyboard.press('End'); check(await verifyReadout(page)===points.length-1,'End inspection failed');
  const last=points[points.length-1];
  await page.keyboard.press('Enter');
  await page.waitForURL(base+'/activities/'+last.activity_id);
  check(await page.locator('h1').textContent()===last.title,'Point Activity title differs');
  await page.goBack(); await page.waitForSelector('.performance-point');
  await page.getByText('Eligibility & calculation',{exact:true}).click();
  const policy=await page.locator('.performance-policy').textContent();
  check(policy.includes('best-average-power-v1')&&policy.includes('Outdoor Ride power is excluded')&&policy.includes('never substitute'),'Trust explanation missing');
  await page.getByText('Selected result provenance',{exact:true}).click();
  check((await page.locator('#performance-point-context').textContent()).includes('Extraction ID'),'Selected provenance missing');
  for(const zone of ['America/Los_Angeles','Asia/Tokyo']) {
    const context=await page.context().browser().newContext({timezoneId:zone,viewport:{width:1448,height:1086}});
    try {
      const probe=await context.newPage(); await probe.goto(base+'/performance');
      await probe.waitForSelector('.performance-point');
      const expectedDate=await probe.evaluate(p=>new Intl.DateTimeFormat(undefined,{
        year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'
      }).format(new Date(p.start_time)),points[0]);
      check(await probe.locator('#performance-date').textContent()===expectedDate,'Performance date is not browser-local');
    } finally {await context.close();}
  }
  for(const [width,height] of [[1448,1086],[390,844]]) {
    await page.setViewportSize({width,height});
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Performance horizontal overflow');
    check(await page.locator('.performance-point').count()===expected,'Responsive chart omits history');
  }
  await page.screenshot({path:'output/playwright/p2-03-performance-phone.png'});
  await page.setViewportSize({width:1448,height:1086});
  await page.screenshot({path:'output/playwright/p2-03-performance-desktop.png'});
  await page.getByRole('navigation',{name:'Main',exact:true}).getByRole('link',{name:'Activities',exact:true}).click();
  await page.waitForURL(url=>url.pathname==='/');
  check(await page.locator('.activity-row').count()===30,'Activities navigation regressed');
  return {result:'passed',browser:'Chromium',chart_points:points.length,navigation:true,
    first_middle_last_pointer:true,keyboard_inspection:true,point_activity_and_back:true,
    source_title_date_watts:true,eligibility_provenance:true,local_date_zones:['America/Los_Angeles','Asia/Tokyo'],
    desktop_phone_no_overflow:true,no_native_stream_payload:true};
}
