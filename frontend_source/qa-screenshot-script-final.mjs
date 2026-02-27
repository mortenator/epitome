import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Helper to setup directories and paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const screenshotDir = path.join(__dirname, 'qa_screenshots_final');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

// Helper to take a screenshot
const takeScreenshot = async (page, name) => {
  const filePath = path.join(screenshotDir, `${name}.png`);
  await page.screenshot({ path: filePath });
  console.log(`✅ Screenshot saved: ${filePath}`);
};

// Helper to click an element found by text using XPath
async function clickElementByText(page, text) {
    const safeText = text.replace(/'/g, "\\'");
    const handle = await page.evaluateHandle((text) => {
        const xPath = `//button[contains(., "${text}")]`;
        const result = document.evaluate(xPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        return result.singleNodeValue;
    }, safeText);
    const element = handle.asElement();
    if (element) {
        await element.click();
        return true;
    }
    console.error(`Element with text "${text}" not found.`);
    return false;
}

// Main QA Function
(async () => {
  console.log('🚀 Launching browser...');
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1080 });
  const baseUrl = 'http://localhost:8080';

  try {
    // 1. Load the page and capture the main view
    console.log('📸 1. Capturing Refined Main View...');
    await page.goto(`${baseUrl}/?project=proj_1`, { waitUntil: 'networkidle2' });
    await page.waitForSelector('h1.font-display', { timeout: 10000 });
    await new Promise(resolve => setTimeout(resolve, 1500)); // Wait for animations
    await takeScreenshot(page, '01_Refined_Main_View');
    console.log('Main view captured. Note the new dark "glass" cards and monochrome logo.');

    // 2. Capture the updated NavItem active state
    console.log('📸 2. Capturing Refined Active Nav Item...');
    // The "Crew list builder" is active by default. The screenshot will show the new style.
    // To make it extra clear, I'll take a screenshot of just the sidebar.
    const sidebar = await page.$('aside');
    if(sidebar) {
        await sidebar.screenshot({ path: path.join(screenshotDir, '02_Refined_Active_Nav.png') });
        console.log(`✅ Screenshot saved: ${path.join(screenshotDir, '02_Refined_Active_Nav.png')}`);
    }
    console.log('Active nav item captured. Note the subtle background and vertical accent bar.');

    // 3. Capture the updated Project Switcher dropdown
    console.log('📸 3. Capturing Refined Project Switcher...');
    const switcherButton = await page.waitForSelector('.px-1.mb-4 button');
    await switcherButton.click();
    await new Promise(resolve => setTimeout(resolve, 500));
    await takeScreenshot(page, '03_Refined_Project_Switcher');
    await page.keyboard.press('Escape');
    console.log('Project switcher captured. Note it now uses the consistent "glass" style.');

  } catch (error) {
    console.error('An error occurred during the QA process:', error);
  } finally {
    await browser.close();
    console.log('✅ QA script finished.');
  }
})();
