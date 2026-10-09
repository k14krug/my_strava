// CLI run-code template; private sample data is injected only at local execution.
async (page) => {
  const samples = SAMPLE_INPUT;
  const boundary = BOUNDARY_INPUT;
  const base = BASE_URL;
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const links = () => page.locator('.activity-row').evaluateAll(nodes => nodes.map(n => n.getAttribute('href')));
  const apply = async () => { await page.getByRole('button', {name:'Apply',exact:true}).click(); await page.waitForLoadState('load'); };
  const waitForLocalQuery = async p => {
    const zone = await p.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone);
    await p.waitForURL(url => url.searchParams.get('tz') === zone);
    await p.waitForLoadState('load');
  };
  const calendarDay = async (p,sample) => sample.absolute === false ? sample.date : p.evaluate(stamp => {
    const parts=new Intl.DateTimeFormat('en-CA',{year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(stamp));
    return ['year','month','day'].map(type => parts.find(part => part.type===type).value).join('-');
  },sample.start);
  await page.goto(base+'/activities');
  await waitForLocalQuery(page);
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
  const seedLocalDay=await calendarDay(page,samples.FIT);
  await page.getByLabel('From',{exact:true}).fill(seedLocalDay);
  await page.getByLabel('To',{exact:true}).fill(seedLocalDay);
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
    await page.goto(base+'/activities?type=all&q='+encodeURIComponent(sample.title));
    await waitForLocalQuery(page);
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
  // Independent browser contexts prove UTC-midnight crossing and preserve
  // unknown source dates. No fixed "current offset" is used by the server.
  for (const zone of ['America/Los_Angeles','Asia/Tokyo','UTC']) {
    const context=await page.context().browser().newContext({timezoneId:zone, viewport:{width:1448,height:1086}});
    try {
      const probe=await context.newPage();
      const day=await calendarDay(probe,boundary);
      const route=base+'/activities?type=all&q='+encodeURIComponent(boundary.title)+'&from='+day+'&to='+day;
      await probe.goto(route);
      await waitForLocalQuery(probe);
      const anchor=probe.locator('a.activity-row[href="/activities/'+boundary.id+'"]');
      check(await anchor.count()===1,'Local calendar day excluded known instant');
      const time=anchor.locator('.row-date time');
      await probe.waitForFunction(() => !!document.querySelector('.row-date time')?.dataset.localDay);
      check(await time.getAttribute('data-local-day')===day,'Displayed day differs from filtered day');
      check(await time.getAttribute('data-timezone')===zone,'Known time not browser-local');
      check(await time.evaluate(node => node.textContent === new Intl.DateTimeFormat(undefined, {
        year:'numeric', month:'short', day:'numeric', hour:'numeric', minute:'2-digit'
      }).format(new Date(node.dateTime))), 'Compact date includes unwanted timezone text');
      check(await anchor.locator('.row-identity time').count()===0,'Date nested under Title');
      if (zone==='America/Los_Angeles') {
        const utcDay=boundary.start.slice(0,10);
        check(day!==utcDay,'Boundary sample did not cross UTC midnight');
        await probe.getByLabel('From',{exact:true}).fill(utcDay);
        await probe.getByLabel('To',{exact:true}).fill(utcDay);
        await probe.getByRole('button',{name:'Apply',exact:true}).click();
        check(await probe.locator('a.activity-row[href="/activities/'+boundary.id+'"]').count()===0,'UTC day incorrectly matched local-day filter');
      }
      const unknown=samples['CSV-only'];
      await probe.goto(base+'/activities?type=all&q='+encodeURIComponent(unknown.title)+'&from='+unknown.date+'&to='+unknown.date);
      await waitForLocalQuery(probe);
      const unknownDate=probe.locator('a.activity-row[href="/activities/'+unknown.id+'"] .row-date');
      check((await unknownDate.textContent()).includes(unknown.date),'Unknown source day shifted');
      check((await unknownDate.textContent()).includes('timezone unknown'),'Unknown timezone label missing');
      check(await unknownDate.locator('time[data-local-time]').count()===0,'Unknown timestamp falsely converted');
    } finally { await context.close(); }
  }
  await page.goto(base);
  await waitForLocalQuery(page);
  const titleBox=await page.locator('.activity-row').first().locator('.row-identity').boundingBox();
  const dateBox=await page.locator('.activity-row').first().locator('.row-date').boundingBox();
  check(dateBox.x>=titleBox.x+titleBox.width,'Date is not an independent column');
  for (const [width,height] of [[1448,1086],[1024,900],[390,844]]) {
    await page.setViewportSize({width,height});
    check(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth), 'Horizontal overflow');
    check(await page.locator('.row-date time[data-compact-time]').evaluateAll(nodes => nodes.every(node => {
      const range=document.createRange(); range.selectNodeContents(node);
      return range.getClientRects().length===1;
    })), 'Activity date wraps to multiple lines');
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
  await waitForLocalQuery(page);
  return ({result:'passed', browser:'Chromium', pagination:true, typeFilters:true, titleSearch:true, dateRange:true, alternateSorts:true, richAndThinRoutes:true, nativeChartInteraction:true, browserBack:true, desktopTabletMobileNoOverflow:true, dedicatedDateColumn:true, singleLineDateWithoutTimezoneSuffix:true, localDateFiltering:true, timezoneUnknownDayPreserved:true, testedTimezones:['America/Los_Angeles','Asia/Tokyo','UTC']});
}
