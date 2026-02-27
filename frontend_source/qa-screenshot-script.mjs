import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const screenshotDir = path.join(__dirname, 'qa_screenshots');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir);
}

const takeScreenshot = async (page, name, options = {}) => {
  const filePath = path.join(screenshotDir, `${name}.png`);
  await page.screenshot({ path: filePath, ...options });
  console.log(`✅ Screenshot saved: ${filePath}`);
};

(async () => {
  console.log('🚀 Launching browser...');
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1080 });

  const baseUrl = 'http://localhost:8080';

  try {
    console.log('📸 1. Capturing Main Call Sheet View...');
    await page.goto(`${baseUrl}/?project=proj_1`, { waitUntil: 'networkidle2' });
    await page.waitForSelector('h1.font-display', { timeout: 10000 });
    await new Promise(resolve => setTimeout(resolve, 1500));
    await takeScreenshot(page, '01_Main_Call_Sheet_View');

    console.log('📸 2. Capturing Project Switcher...');
    const switcherButton = await page.waitForSelector('.px-1.mb-4 button');
    await switcherButton.click();
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '02_Project_Switcher_Open');
    await page.keyboard.press('Escape');

    console.log('📸 3. Capturing Inline Editing...');
    const editableField = await page.waitForSelector('div.font-medium.text-foreground.truncate > div');
    await editableField.click();
    await page.waitForSelector('input[value="Spring \'26 Campaign - Nike"]');
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '03_Inline_Editing_Active');
    await page.keyboard.press('Escape');

    console.log('📸 4. Capturing Hide Contact Feature...');
    const [cameraDepartmentButton] = await page.$x("//button[contains(., 'Camera (8)')]");
    if (cameraDepartmentButton) await cameraDepartmentButton.click();
    else throw new Error('Camera department button not found');
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const firstRowKebab = await page.waitForSelector('tbody tr.group:first-child button');
    await firstRowKebab.click();
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '04_Hide_Contact_Menu_Open');
    
    const [hideMenuItem] = await page.$x("//div[contains(., 'Hide contact info on export')]");
    if (hideMenuItem) await hideMenuItem.click();
    else throw new Error('Hide menu item not found');
    
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '05_Hide_Contact_Enabled');
    
    console.log('📸 5. Capturing Add Crew Dropdown...');
    const [addCrewButton] = await page.$x("//button[contains(., 'Add crew member')]");
    if (addCrewButton) await addCrewButton.click();
    else throw new Error('Add crew member button not found');
    
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '06_Add_Crew_Dropdown_Open');
      
    await page.type('input[placeholder="Search by name or role..."]', 'Non Existent Person');
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '07_Add_Crew_Manual_Button');
    await page.keyboard.press('Escape');

  } catch (error) {
    console.error('An error occurred during the QA process:', error);
  } finally {
    await browser.close();
    console.log('✅ QA script finished.');
  }
})();
