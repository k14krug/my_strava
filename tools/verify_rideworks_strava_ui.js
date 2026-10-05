// Actual Chromium, isolated synthetic API evidence only; no Strava requests.
async (page) => {
  const base=BASE_URL,links=REVIEW_LINKS;
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  await page.goto(base+'/?type=all');await page.waitForSelector('.activity-row');
  check(await page.locator('.activity-row').count()===3,'Unexpected synthetic Activity count');
  await page.locator('a.activity-row[href="'+links.thin+'"]').click();await page.waitForSelector('.review-unavailable');
  check(await page.locator('h1').textContent()==='Synthetic API-only ride','API-only title unavailable');
  check((await page.locator('body').textContent()).includes('Strava API metadata'),'API provenance missing');
  check((await page.locator('body').textContent()).includes('Average watts (W)'),'API watts not attributable');
  check(await page.locator('#ride-chart,.best-value,#recent-context-title').count()===0,'API summaries promoted to native analysis');
  check(!(await page.locator('body').textContent()).includes('polyline'),'Unneeded geometry retained');
  const stamp=await page.locator('.ride-meta time').getAttribute('datetime');
  check(await page.locator('.ride-meta time').textContent()!==stamp+' (UTC source time)','API date did not localize');
  await page.setViewportSize({width:390,height:844});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'API-only phone overflow');
  await page.screenshot({path:'output/playwright/p2-05-synthetic-thin-phone.png',fullPage:true});
  await page.goBack();await page.waitForSelector('.activity-row');
  await page.locator('a.activity-row[href="'+links.rich+'"]').click();await page.waitForSelector('#ride-chart');
  check(await page.locator('h1').textContent()==='Synthetic API enriched ride','New API title not preferred');
  check(await page.locator('.best-value').textContent()==='120 W','FIT best-20 changed');
  const native=await page.locator('#native-records').textContent();
  const records=JSON.parse(native);check(records.length===1200&&records.every(r=>r.power===120&&r.heart_rate===100),'Native chart evidence changed');
  const provenance=await page.locator('.provenance').textContent();
  check(provenance.includes('Synthetic export title')&&provenance.includes('Synthetic API enriched ride'),'Old export/API title provenance lost');
  check((await page.locator('.recent-note').textContent()).includes('Performance rebuild'),'Stale Performance was silently reused/rebuilt');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Enriched phone overflow');
  await page.setViewportSize({width:1448,height:1086});await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'output/playwright/p2-05-synthetic-rich-desktop.png',fullPage:true});
  await page.goto(base+'/performance');await page.waitForSelector('.performance-trend',{state:'attached'});
  check(JSON.parse(await page.locator('#performance-points').textContent()).length===1,'API-only or stale native result entered Performance');
  await page.goto(base+'/?q=API&type=cycling&sort=oldest');await page.waitForSelector('.activity-row');
  check(await page.locator('.activity-row').count()===2,'API title/filter/sort integration changed');
  return {status:'passed',mode:'isolated_synthetic',api_only_thin:true,enriched_fit_rich:true,
    native_chart_best20_unchanged:true,old_export_and_new_api_titles_inspectable:true,browser_local_api_date:true,
    stale_performance_honest_no_rebuild:true,api_summary_watts_excluded:true,activities_search_sort_type:true,
    desktop_phone_no_overflow:true};
}
