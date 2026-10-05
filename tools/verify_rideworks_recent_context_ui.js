// Full-history Chromium acceptance; private routes/titles remain local.
async (page) => {
  const base=BASE_URL, links=REVIEW_LINKS;
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  await page.goto(base+'/performance');await page.waitForSelector('.performance-trend');
  // Use a real summary/evidence Activity link already rendered by Performance.
  await page.locator('a[href="'+links.representative+'"]').first().click();await page.waitForSelector('#recent-context-title');
  const title=await page.locator('h1').textContent();
  check(await page.locator('.best-value').textContent()==='120 W','Representative best-20 changed');
  check(await page.locator('#recent-current-watts').textContent()==='120 W','Trusted current result changed');
  check(await page.locator('#recent-prior-watts').textContent()===links.representative_prior_watts+' W','Prior watts differ from independent verification');
  check(await page.locator('#recent-prior-activity').getAttribute('href')===links.prior,'Prior Activity route differs');
  check(Number(await page.locator('#ride-chart').getAttribute('data-record-count'))===3621,'Native chart changed');
  check((await page.locator('.ride-summary').textContent()).includes('118 W'),'FIT source summary changed');
  check(await page.locator('#recent-context-details').getAttribute('open')===null,'Context details dominate default view');
  await page.getByText('Recent context details',{exact:true}).click();
  const details=await page.locator('#recent-context-details').textContent();
  check(details.includes('virtual-native-power-v1')&&details.includes('best-average-power-v1')&&details.includes('The current Activity is excluded')&&details.includes('exclusive'),'Comparison basis missing');
  check(!details.includes('stored_path')&&!details.includes('native_records'),'Comparison exposes native streams/runtime paths');
  await page.getByText('Recent context details',{exact:true}).click();
  await page.locator('#recent-prior-activity').click();await page.waitForURL(base+links.prior);
  await page.goBack();await page.waitForSelector('#recent-context-title');
  check(await page.locator('h1').textContent()===title,'Activity/back title changed');
  await page.locator('#recent-performance').click();await page.waitForSelector('.performance-trend');
  await page.goBack();await page.waitForSelector('#recent-context-title');
  await page.setViewportSize({width:1448,height:1086});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Desktop overflow');
  await page.screenshot({path:'output/playwright/p2-04-recent-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Phone overflow');
  await page.screenshot({path:'output/playwright/p2-04-recent-phone.png',fullPage:true});
  await page.goto(base+links.no_prior);await page.waitForSelector('#recent-context-title');
  check(await page.locator('#recent-prior-watts').textContent()==='Unavailable','No-baseline result fabricated');
  check((await page.locator('.recent-note').textContent()).includes('No qualifying prior result'),'No-baseline reason missing');
  check(await page.locator('#recent-prior-activity').count()===0,'No-baseline has invented Activity');
  await page.goto(base+links.outdoor);await page.waitForSelector('#recent-context-title');
  check(await page.locator('.recent-context').getAttribute('data-recent-status')==='unavailable','Outdoor promoted to trusted context');
  check((await page.locator('.recent-note').textContent()).includes('Outdoor Ride power is excluded'),'Outdoor exclusion unclear');
  check(await page.locator('#recent-current-watts').count()===0,'Untrusted context invents current trusted watts');
  check(await page.locator('#ride-chart').count()===1&&await page.locator('.best-value').count()===1,'Outdoor ordinary review lost');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Unavailable phone overflow');
  for(const zone of ['America/Los_Angeles','Asia/Tokyo']){
    const context=await page.context().browser().newContext({timezoneId:zone});
    try{
      const probe=await context.newPage();await probe.goto(base+links.representative);await probe.waitForSelector('#recent-prior-activity');
      const stamp=await probe.locator('.recent-contribution time').getAttribute('datetime');
      const expected=await probe.evaluate(stamp=>new Intl.DateTimeFormat(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(stamp)),stamp);
      check(await probe.locator('.recent-contribution time').textContent()===expected,'Prior date is not browser-local/compact');
    }finally{await context.close();}
  }
  await page.setViewportSize({width:1448,height:1086});await page.goto(base+links.representative);await page.waitForSelector('#recent-context-title');
  return {result:'passed',browser:'Chromium',representative_this_ride_watts:120,representative_prior_watts:links.representative_prior_watts,
    representative_native_records:3621,fit_source_average_watts:118,prior_activity_and_back:true,view_performance_and_back:true,
    no_baseline_unavailable:true,ineligible_rich_unavailable:true,secondary_provenance:true,accepted_chart_summary_title_preserved:true,
    desktop_phone_no_overflow:true,local_dates_zones:['America/Los_Angeles','Asia/Tokyo']};
}
