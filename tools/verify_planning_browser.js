/* Run in a Playwright CLI session against the disposable P5-01 review server. */
async (page) => {
  const base = new URL(page.url()).origin;
  const zone = 'America/Los_Angeles';
  let assertions = 0;
  const check = (condition, message) => { assertions++; if (!condition) throw new Error(message); };
  const errors = [];
  page.on('pageerror', e => errors.push(e.name));
  async function open(path) {
    const response = await page.goto(base + path);
    check(response.status() === 200, 'route status');
    await page.waitForLoadState('networkidle');
  }
  async function data() {return JSON.parse(await page.locator('#plan-data').textContent());}
  async function horizon() {
    const p = await data();
    const hard = p.days.filter(d => d.hard);
    check(hard.length === 3, 'exactly three prospective hard days');
    check(hard.map(d => d.hard_number).join() === '1,2,3', 'hard numbers');
    check(p.days.at(-1).hard_number === 3, 'ends on third hard');
    check(p.days.length > 7, 'variable length beyond a week');
    check(await page.locator('.plan-day').count() === p.days.length-1, 'today shown once, every future date shown');
    check(!p.days.some(d => /^(Rest|No ride)$/.test(d.category)), 'ride option every date');
    check(await page.locator('nav a[aria-current=page]').textContent() === 'Plan', 'active nav');
    check(await page.locator('[data-recommended-day]').getAttribute('data-recommended-day') === p.today, 'rider-local today');
    return p;
  }
  async function recommendation() {
    return page.locator('.next-recommended').evaluate(el => ['recommended-type','recommended-target','recommended-reason'].map(c => el.querySelector('.'+c).textContent));
  }
  await open('/plan');
  const first = await horizon();
  check(first.timezone === zone, 'browser timezone automatically selected');
  check(await page.locator('#plan-legs').inputValue() === 'unknown', 'feedback not silently normal');
  await page.getByLabel('Legs today').selectOption('heavy');
  await page.getByRole('button',{name:'Update',exact:true}).click();
  await page.waitForLoadState('networkidle');
  check((await data()).days[0].category === 'Recovery', 'heavy legs recovery');
  const heavy = await recommendation();
  await page.getByRole('link',{name:'Home',exact:true}).click();
  await page.waitForLoadState('networkidle');
  check(JSON.stringify(await recommendation()) === JSON.stringify(heavy), 'Home / Plan shared calculation');
  check(await page.locator('.home-recent-row').count() > 0, 'recent Activities retained');
  check(await page.locator('#home-mileage-chart').count() === 1, 'mileage chart retained');
  check(await page.locator('.home-training').count() === 1, 'Training State snapshot retained');
  const placement = await page.locator('.next-recommended').evaluate(el => ({a:el.getBoundingClientRect().top,b:document.querySelector('.home-recent').getBoundingClientRect().top}));
  check(Math.abs(placement.a-placement.b)<2, 'recommendation beside Recent Activities');
  await page.getByRole('link',{name:'View Plan',exact:true}).click();
  await page.waitForLoadState('networkidle');
  await page.getByLabel('Legs today').selectOption('unknown');
  await page.getByRole('button',{name:'Update',exact:true}).click();
  await page.waitForLoadState('networkidle');
  const ordinary = await horizon();
  check(ordinary.days[0].category === first.days[0].category, 'feedback reset');
  await page.getByRole('button',{name:'I plan to do this',exact:true}).click();
  await page.waitForLoadState('networkidle');
  check(await page.locator('.plan-intent-note').textContent().then(t=>t.includes('Recorded intent:')), 'explicit intent persisted');
  const latest = (await data()).latest_hard.activity_id;
  await open('/activities/'+latest);
  check(await page.locator('.activity-plan-context').textContent().then(t=>t.includes('No recorded intent')), 'today confirmation not retroactively assigned');
  check(await page.locator('.activity-plan-context strong').textContent() === 'VO2', 'known interval actual type');
  const form = page.locator('.activity-plan-context .plan-correction');
  check(await form.locator('input[name=tz]').inputValue() === zone, 'review correction browser timezone');
  await form.locator('select').selectOption('Race');
  await form.getByRole('button',{name:'Save category'}).click();
  await page.waitForLoadState('networkidle');
  check(await page.locator('.activity-plan-context strong').textContent() === 'Race', 'separate classification correction');
  await page.getByRole('link',{name:'View Plan',exact:true}).click();
  await page.waitForLoadState('networkidle');
  check((await data()).latest_hard.classification.category === 'Race', 'actual correction changes rotation');
  check((await data()).days.find(d=>d.hard).category !== 'Race', 'after race structured next');
  await open('/activities/'+latest);
  await page.locator('.activity-plan-context select').selectOption('automatic');
  await page.getByRole('button',{name:'Save category'}).click();
  await page.waitForLoadState('networkidle');
  check(await page.locator('.activity-plan-context strong').textContent() === 'VO2', 'original inference restored');
  for (const path of ['/activities','/performance','/training-state','/settings']) {
    await open(path);
    check(await page.locator('h1').count() === 1, 'existing primary route remains usable');
  }
  await open('/plan');
  const stable = (await data()).days;
  await page.reload();await page.waitForLoadState('networkidle');
  check(JSON.stringify((await data()).days) === JSON.stringify(stable), 'repeat load deterministic');
  await page.getByLabel('Legs today').focus();
  await page.keyboard.press('Tab');
  check(await page.evaluate(()=>document.activeElement.textContent === 'Update'), 'keyboard form order');
  await page.screenshot({path:'output/playwright/p501-plan-desktop.png'});
  for (const width of [390,320]) {
    await page.setViewportSize({width,height:844});
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth), 'mobile overflow');
    check(await page.locator('#plan-legs').isVisible(), 'mobile leg control');
    check(await page.locator('a[aria-current=page]').isVisible(), 'mobile nav');
    await horizon();
    await page.screenshot({path:`output/playwright/p501-plan-${width}.png`});
  }
  await page.setViewportSize({width:1280,height:900});
  await open('/');
  await page.screenshot({path:'output/playwright/p501-home-desktop.png'});
  check(errors.length === 0, 'no browser script errors');
  return {assertions,errors,desktop:true,mobile:[390,320],home_plan_parity:true,explicit_intent:true,correction_flow:true};
}
