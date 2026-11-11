const { test, expect } = require('@playwright/test');
const base = process.env.E2E_URL || 'http://localhost:3000';
test('admin draft survives reload and clears after submission', async ({page}) => {
  await page.goto(base);
  await page.getByRole('button',{name:'Create Class'}).first().click();
  const className='E2E-'+Date.now();
  await page.locator('#classname').fill(className);
  await page.locator('#seats').fill('11');
  await page.reload();
  await page.getByRole('button',{name:'Create Class'}).first().click();
  await expect(page.locator('#classname')).toHaveValue(className);
  await expect(page.locator('#seats')).toHaveValue('11');
  await page.locator('.form-card button.primary').click();
  await expect(page.locator('#classname')).toHaveValue('');
});
test('student identifier persists across refresh', async ({page}) => {
  await page.goto(base);
  await page.locator('#student').fill('12345678901234567');
  await page.reload();
  await expect(page.locator('#student')).toHaveValue('12345678901234567');
});

test('client validation prevents an invalid class submission', async ({page}) => {
  await page.goto(base);
  await page.getByRole('button',{name:'Create Class'}).first().click();
  await page.locator('#classname').fill('Test invalid class');
  await page.locator('#seats').fill('1000001');
  await page.locator('.form-card button.primary').click();
  await expect(page.getByRole('alert').first()).toContainText('1,000,000');
});
test('submitted student hold reappears after browser reload', async ({page}) => {
  await page.goto(base);
  const student=String(Date.now()).padStart(17,'0').slice(-17);
  await page.locator('#student').fill(student);
  await page.getByRole('button',{name:'Create Class'}).first().click();
  const className='E2E resume '+Date.now();
  await page.locator('#classname').fill(className);
  await page.locator('#seats').fill('2');
  await page.locator('.form-card button.primary').click();
  await page.getByRole('button',{name:'Browse Classes'}).click();
  await page.locator('.class-card').filter({hasText:className}).getByRole('button',{name:'Apply Now'}).click();
  await page.getByRole('button',{name:'My Applications'}).click();
  await expect(page.locator('.application')).toHaveCount(1);
  await page.reload();
  await page.getByRole('button',{name:'My Applications'}).click();
  await expect(page.locator('.application')).toHaveCount(1);
});
