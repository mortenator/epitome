const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

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
  await page.setViewport({ width: 1440, height: 900 });

  const baseUrl = 'http://localhost:8080';

  try {
    // 1. Dashboard / Main Page
    console.log('📸 1. Capturing Dashboard...');
    await page.goto(baseUrl, { waitUntil: 'networkidle2' });
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for animations
    await takeScreenshot(page, '01_Dashboard_View');

    // 2. Project Switcher
    console.log('📸 2. Capturing Project Switcher...');
    await page.click('button:has(span:text("Spring \'26 Campaign - Nike"))');
    await new Promise(resolve => setTimeout(resolve, 500)); // Wait for dropdown animation
    await takeScreenshot(page, '02_Project_Switcher_Open');
    await page.keyboard.press('Escape'); // Close dropdown

    // 3. Call Sheet View & Info Cards
    console.log('📸 3. Capturing Call Sheet View & Info Cards...');
    // Assuming the first project navigates to a call sheet, or we can click a link
    // For this script, we'll navigate directly if needed.
    await page.goto(`${baseUrl}/?project=proj_1`, { waitUntil: 'networkidle2' });
    await new Promise(resolve => setTimeout(resolve, 1000));
    await takeScreenshot(page, '03_Call_Sheet_Info_Cards');
    
    // 4. Inline Editing
    console.log('📸 4. Capturing Inline Editing...');
    await page.click('div[title="Click to edit"]'); // Clicks the first editable field
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '04_Inline_Editing_Active');
    await page.keyboard.press('Escape'); // Cancel edit

    // 5. Hide Contact Info
    console.log('📸 5. Capturing Hide Contact Feature...');
    // First, expand a department
    await page.click('button:has(span:text("Camera (8)"))');
    await new Promise(resolve => setTimeout(resolve, 500));
    // Click the Kebab menu on the first crew member
    await page.click('.group:first-child button:has(svg[lucide="more-vertical"])');
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '05_Hide_Contact_Menu_Open');
    // Click the "Hide" switch
    await page.click('div[role="menuitem"]:has(span:text("Hide contact info on export"))');
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '06_Hide_Contact_Enabled');
    
    // 6. Crew Management - Add Crew Dropdown
    console.log('📸 6. Capturing Add Crew Dropdown...');
    // Open the add dropdown for an unassigned role
    const unassignedAddButton = await page.$('button:has(span:text("Add person"))');
    if (unassignedAddButton) {
      await unassignedAddButton.click();
      await new Promise(resolve => setTimeout(resolve, 500));
      await takeScreenshot(page, '07_Add_Crew_Dropdown_Open');
      
      // Test manual add UI
      await page.type('input[placeholder="Search by name or role..."]', 'Non Existent Person');
      await new Promise(resolve => setTimeout(resolve, 500));
      await takeScreenshot(page, '08_Add_Crew_Manual_Button');
    } else {
      console.log('⚠️ Could not find an unassigned role to test crew adding.');
    }

  } catch (error) {
    console.error('An error occurred during the QA process:', error);
  } finally {
    await browser.close();
    console.log('✅ QA script finished.');
  }
})();
