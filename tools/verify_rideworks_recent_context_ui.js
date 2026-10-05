// Full-history Chromium acceptance; private routes/titles remain local.
async (page) => {
  const base=BASE_URL, links=REVIEW_LINKS;
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  await page.goto(base+'/performance');await page.waitForSelector('.performance-trend');
  // Use a real summary/evidence Activity link already rendered by Performance.
  await page.locator('a[href="'+links.representative+'"]').first().click();await page.waitForSelector('#recent-context-title');
  const title=await page.locator('h1').textContent();
  check(await page.locator('#recent-context-title').textContent()==='Compared with previous 6 weeks','Comparison purpose is unclear');
  check(await page.locator('#recent-difference').textContent()==='75 W below','Difference disagrees with displayed watts');
  check(await page.locator('#recent-prior-activity').textContent()==='Open prior ride','Explicit prior action missing');
  check(await page.locator('.best-value').textContent()==='120 W','Representative best-20 changed');
  check(await page.locator('#recent-current-watts').textContent()==='120 W','Trusted current result changed');
  check(await page.locator('#recent-prior-watts').textContent()===links.representative_prior_watts+' W','Prior watts differ from independent verification');
  check(await page.locator('#recent-prior-activity').getAttribute('href')===links.prior,'Prior Activity route differs');
  check(Number(await page.locator('#ride-chart').getAttribute('data-record-count'))===3621,'Native chart changed');
  check((await page.locator('.ride-summary').textContent()).includes('118 W'),'FIT source summary changed');
  check(await page.locator('#recent-context-details').getAttribute('open')===null,'Context details dominate default view');
  await page.getByText('Comparison details',{exact:true}).click();
  const details=await page.locator('#recent-context-details').textContent();
  check(details.includes('virtual-native-power-v1')&&details.includes('best-average-power-v1')&&details.includes('The current Activity is excluded')&&details.includes('exclusive'),'Comparison basis missing');
  check(!details.includes('stored_path')&&!details.includes('native_records'),'Comparison exposes native streams/runtime paths');
  await page.getByText('Comparison details',{exact:true}).click();
  await page.locator('#recent-prior-activity').click();await page.waitForURL(base+links.prior);
  await page.goBack();await page.waitForSelector('#recent-context-title');
  check(await page.locator('h1').textContent()===title,'Activity/back title changed');
  await page.locator('#recent-performance').click();await page.waitForSelector('.performance-trend');
  await page.goBack();await page.waitForSelector('#recent-context-title');
  await page.setViewportSize({width:1448,height:1086});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Desktop overflow');
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'output/playwright/p2-04-recent-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Phone overflow');
  await page.screenshot({path:'output/playwright/p2-04-recent-phone.png',fullPage:true});
  await page.goto(base+links.no_prior);await page.waitForSelector('#recent-context-title');
  check(await page.locator('#recent-prior-watts').textContent()==='Unavailable','No-baseline result fabricated');
  check((await page.locator('.recent-note').textContent()).includes('No qualifying prior result'),'No-baseline reason missing');
  check(await page.locator('#recent-prior-activity').count()===0,'No-baseline has invented Activity');
  check(await page.locator('#recent-difference').count()===0,'No-baseline has fabricated difference');
  await page.screenshot({path:'output/playwright/p2-04-no-prior-phone.png',fullPage:true});
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
  // Equal/sub-watt cases use synthetic evidence rendered by the production panel.
  const synthetic=await page.context().newPage();
  try{
    for(const fixture of SYNTHETIC_CASES){
      await synthetic.setContent(fixture.html);
      check(await synthetic.locator('#recent-current-watts').textContent()===fixture.current+' W','Synthetic current display differs');
      check(await synthetic.locator('#recent-prior-watts').textContent()===fixture.prior+' W','Synthetic prior display differs');
      check(await synthetic.locator('#recent-difference').textContent()===fixture.expected,'Equal/sub-watt display arithmetic differs');
      for(const [name,raw] of [['Current',fixture.current_raw],['Prior',fixture.prior_raw]]){
        const value=await synthetic.locator('#recent-context-details dl > div').filter({hasText:name+' raw average (W)'}).locator('dd').textContent();
        check(value===String(raw),'Raw evidence lost in details');
      }
    }
  }finally{await synthetic.close();}
  await page.setViewportSize({width:1448,height:1086});await page.goto(base+links.representative);await page.waitForSelector('#recent-context-title');
  return {result:'passed',browser:'Chromium',representative_this_ride_watts:120,representative_prior_watts:links.representative_prior_watts,
    comparison_heading_clear:true,explicit_prior_action:true,neutral_difference:'75 W below',
    difference_uses_displayed_whole_watts:true,synthetic_equal_sub_watt_cases:4,raw_details_preserved:true,
    representative_native_records:3621,fit_source_average_watts:118,prior_activity_and_back:true,view_performance_and_back:true,
    no_baseline_unavailable:true,ineligible_rich_unavailable:true,secondary_provenance:true,accepted_chart_summary_title_preserved:true,
    desktop_phone_no_overflow:true,local_dates_zones:['America/Los_Angeles','Asia/Tokyo']};
}
