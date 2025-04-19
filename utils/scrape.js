import { PlaywrightCrawler, Dataset } from 'crawlee';
import { chromium } from 'playwright'; // Or firefox, webkit

console.log('Starting the scrape...');

// Array to hold all results
const results = [];
const maxPages = -9; // Stop after this many pages if > 0
let pagesProcessed = 0; // Counter for processed pages

const crawler = new PlaywrightCrawler({
    // Use the browser instance provided by Crawlee
    // launchContext: {
    //     // You can specify launch options here if needed
    //     // e.g., userDataDir for persistent sessions
    //     launchOptions: {
    //         headless: false, // Show the browser
    //         slowMo: 50, // Slow down operations by 50ms if needed for debugging
    //     },
    // },
    headless: true, // Show the browser window
    minConcurrency: 1,
    // maxConcurrency: 1, // Run one browser instance at a time to easily see pagination
    maxRequestRetries: 1,
    requestHandlerTimeoutSecs: 60,

    async requestHandler({ request, page, enqueueLinks, log }) {
        log.info(`Processing ${request.url}...`);
        pagesProcessed++; // Increment page counter

        // Wait for the posts to load if necessary (adjust selector as needed)
        try {
            await page.waitForSelector('li.forum-post-container', { timeout: 10000 });
        } catch (error) {
            log.error(`Selector li.forum-post-container not found on ${request.url}. Skipping page.`);
            return;
        }

        // Extract data from the current page
        const pageData = await page.evaluate(() => {
            const posts = [];
            const postElements = document.querySelectorAll('li.forum-post-container');

            postElements.forEach(postElement => {
                // Skip ad containers if they match the selector somehow
                if (postElement.querySelector('[data-aaad="true"]')) {
                    return;
                }
                 // Skip removed posts - Check paragraph text content directly
                const paragraphs = postElement.querySelectorAll('.post-body .body-text p');
                let isRemoved = false;
                paragraphs.forEach(p => {
                    if (p.textContent.includes("This post was removed.")) {
                        isRemoved = true;
                    }
                });
                if (isRemoved) {
                    return;
                }

                const authorElement = postElement.querySelector('.author-container .dbr-username-dropdown span span');
                const messageElement = postElement.querySelector('.post-body .body-text');
                const linkElement = postElement.querySelector('button[title="Copy to clipboard."]');
                const datetimeElement = postElement.querySelector('.post-meta-container .time-and-date span.text-xs.text-gray-700');

                const author = authorElement ? authorElement.innerText.trim() : 'Author not found';

                // Extract link
                let link = 'Link not found';
                if (linkElement) {
                    const clickAttribute = linkElement.getAttribute('x-on:click');
                    const urlMatch = clickAttribute.match(/copyToClipboard\('([^']+)'/);
                    if (urlMatch && urlMatch[1]) {
                        link = urlMatch[1];
                    }
                }

                // Extract datetime
                const datetime = datetimeElement ? datetimeElement.innerText.trim() : 'Datetime not found';

                 // Get only the direct text content of the body-text div, excluding blockquotes
                let message = '';
                if (messageElement) {
                    messageElement.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE) {
                            message += node.textContent.trim() + ' ';
                        } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() === 'p') {
                             // Extract text from direct child paragraphs, avoiding blockquote paragraphs
                            let paragraphText = '';
                             node.childNodes.forEach(pNode => {
                                if (pNode.nodeType === Node.TEXT_NODE) {
                                    paragraphText += pNode.textContent.trim() + ' ';
                                }
                             });
                             if (paragraphText.trim()) {
                                message += paragraphText.trim() + ' ';
                             }
                        }
                    });
                    message = message.replace(/\s+/g, ' ').trim(); // Clean up whitespace
                } else {
                    message = 'Message not found';
                }


                if (author !== 'Author not found' && message !== 'Message not found') {
                    // Add link and datetime to the pushed object
                    posts.push({ author, message, link, datetime });
                }
            });
            return posts;
        });

        log.info(`Found ${pageData.length} posts on ${request.url}`);
        results.push(...pageData);

        // Find and enqueue the "Next" link only if maxPages limit not reached
        if (maxPages <= 0 || pagesProcessed < maxPages) {
            log.info(`Pages processed: ${pagesProcessed}. Enqueuing next page.`);
            await enqueueLinks({
                selector: 'a[title="Go to next page of thread"]',
                label: 'next-page', // Optional label for tracking
            });
        } else {
            log.info(`Max pages (${maxPages}) reached. Not enqueuing next page.`);
        }
    },

    async failedRequestHandler({ request, log }) {
        log.error(`Request ${request.url} failed too many times.`);
    },
});

// Add the starting URL to the queue
await crawler.addRequests(['https://www.letsrun.com/forum/flat_read.php?thread=12130781']);

// Run the crawler
await crawler.run();

console.log('Scrape finished.');
console.log(`Total results found: ${results.length}`);
// console.log(results); // Log all results

// Optionally, save to a Dataset (Crawlee's way of storing data)
// await Dataset.pushData(results);
// console.log('Results saved to dataset.');

// Or save to a JSON file
import fs from 'fs';
import path from 'path'; // Import path module

// Ensure the data directory exists (optional, but good practice)
const dataDir = path.join('..', 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
  console.log(`Created directory: ${dataDir}`);
}

const outputPath = path.join(dataDir, 'results.json');
fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
console.log(`Results saved to ${outputPath}`);
