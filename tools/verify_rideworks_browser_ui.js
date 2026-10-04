// CLI run-code template; private sample data is injected only at local execution.
async (page) => {
  const samples = SAMPLE_INPUT;
  const base = BASE_URL;
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const links = () => page.locator('.activity-row').evaluateAll(nodes => nodes.map(n => n.getAttribute('href')));
  const apply = async () => { await page.getByRole('button', {name:'Apply',exact:true}).click(); await page.waitForLoadState('load'); };
  await page.goto(base);
  const first = await links();
  check(first.length === 30, 'Unbounded default page');
  await page.locator('a[rel="next"]').click();
  const second = await links();
  check(second.length === 30 && second.every(url => !first.includes(url)), 'Pagination failed');
  await page.locator('a[rel="prev"]').click();
  check(JSON.stringify(await links()) === JSON.stringify(first), 'Previous failed');
  for (const [type,count] of [['Ride','146'],['Virtual Ride','1,264'],['all','1,434'],['Run','22']]) {
    await page.getByRole('combobox', {name:'Activity type', exact:true}).selectOption(type);
    await apply();
    check((await page.locator('.result-count').textContent()).includes('of '+count+' matching'), 'Type count failed');
  }
  await page.getByRole('combobox', {name:'Activity type', exact:true}).selectOption('all');
  await page.getByLabel('Title search',{exact:true}).fill(samples.FIT.title.toUpperCase());
  await apply();
  check((await links()).includes('/activities/'+samples.FIT.id), 'Private title search failed');
  await page.getByLabel('Title search',{exact:true}).fill('');
  await page.getByLabel('From',{exact:true}).fill(samples.FIT.date);
  await page.getByLabel('To',{exact:true}).fill(samples.FIT.date);
  await apply();
  check((await links()).includes('/activities/'+samples.FIT.id), 'Date range failed');
  await page.getByLabel('From',{exact:true}).fill('');
  await page.getByLabel('To',{exact:true}).fill('');
  for (const sort of ['oldest','duration','distance']) {
    await page.getByRole('combobox', {name:'Sort', exact:true}).selectOption(sort);
    await apply();
    const ordered = await links();
    await page.reload();
    check(JSON.stringify(await links())===JSON.stringify(ordered), 'Sort not stable');
  }
  for (const [fmt,sample] of Object.entries(samples)) {
    await page.goto(base+'/?type=all&q='+encodeURIComponent(sample.title));
    await page.locator('a.activity-row[href="/activities/'+sample.id+'"]').click();
    check((await page.locator('h1').textContent())===sample.title, 'Review title changed');
    if (fmt==='FIT') {
      check(await page.locator('#ride-chart svg .chart-power').count()>0, 'Native chart missing');
      check((await page.locator('.best-value').textContent())==='120 W', 'Best20 changed');
      await page.getByText('Source & provenance',{exact:true}).click();
      check((await page.locator('.provenance').textContent()).includes('Source-supplied Strava-export evidence'), 'Title provenance missing');
      await page.locator('#chart-svg').focus();
      await page.keyboard.press('ArrowRight');
      check((await page.locator('#sample-readout').textContent()).includes('Power'), 'Native chart interaction failed');
    } else {
      check(await page.getByRole('heading',{name:'Detailed RideWorks review unavailable',exact:true}).count()===1, 'Thin review missing');
      check(await page.locator('#native-records').count()===0, 'Thin review fabricated native chart');
    }
    await page.goBack();
    check((await links()).includes('/activities/'+sample.id), 'Browser back failed');
  }
  await page.goto(base);
  for (const [width,height] of [[1448,1086],[1024,900],[390,844]]) {
    await page.setViewportSize({width,height});
    check(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth), 'Horizontal overflow');
  }
  await page.setViewportSize({width:1448,height:1086});
  await page.screenshot({path:'output/playwright/p2-02-activities-desktop.png'});
  await page.getByRole('combobox', {name:'Activity type', exact:true}).selectOption('Run');
  await apply();
  await page.screenshot({path:'output/playwright/p2-02-noncycling-desktop.png'});
  await page.goto(base+'/activities/'+samples.FIT.id);
  await page.screenshot({path:'output/playwright/p2-02-enriched-fit-desktop.png'});
  await page.goto(base+'/activities/'+samples['CSV-only'].id);
  await page.screenshot({path:'output/playwright/p2-02-csv-only-desktop.png'});
  await page.goto(base);
  return ({result:'passed', browser:'Chromium', pagination:true, typeFilters:true, titleSearch:true, dateRange:true, alternateSorts:true, richAndThinRoutes:true, nativeChartInteraction:true, browserBack:true, desktopTabletMobileNoOverflow:true});
}
