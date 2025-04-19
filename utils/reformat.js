import fs from 'fs';
import path from 'path';

// Read the input JSON file
fs.readFile('../data/results.json', 'utf8', (err, data) => {
  if (err) {
    console.error("Error reading ../data/results.json:", err);
    process.exit(1); // Exit with error code
  }

  let results;
  try {
    // Parse the JSON data
    results = JSON.parse(data);
  } catch (parseErr) {
    console.error("Error parsing JSON from results.json:", parseErr);
    process.exit(1);
  }

  // Check if results is an array
  if (!Array.isArray(results)) {
    console.error("Error: results.json does not contain a valid JSON array.");
    process.exit(1);
  }

  // Process the data: keep only message and author, rename keys
  const liteResults = results.map(item => {
    // Ensure item is an object and has the required keys before accessing them
    if (typeof item === 'object' && item !== null && 'message' in item && 'author' in item) {
      return {
        msg: item.message,
        usr: item.author
      };
    } else {
      // Handle items that don't have the expected structure
      // Log a warning and return null for filtering later
      console.warn("Skipping item due to missing 'message' or 'author' key, or invalid format:", item);
      return null;
    }
  }).filter(item => item !== null); // Filter out any nulls added for invalid items

  // Ensure the /data directory exists
  const dataDir = path.join('..', 'data'); // Go up one level to find the data directory
  if (!fs.existsSync(dataDir)) {
    // It's generally better to ensure the directory exists where needed,
    // but creating it might be unexpected. Let's assume it exists for now.
    // If needed, we could add: fs.mkdirSync(dataDir, { recursive: true });
    // For now, we'll just use the correct path.
    console.warn(`Output directory ${dataDir} does not exist. Files may not be written.`);
  }

  // Split liteResults into chunks of 100
  const chunkSize = 100;
  for (let i = 0; i < liteResults.length; i += chunkSize) {
    const chunk = liteResults.slice(i, i + chunkSize);
    const fileIndex = Math.floor(i / chunkSize) + 1;
    const outputPath = path.join(dataDir, `results-lite-${fileIndex}.json`); // Use dataDir

    // Write each chunk to its own file
    fs.writeFileSync(outputPath, JSON.stringify(chunk, null, 2), 'utf8');
    console.log(`Successfully created ${outputPath} with ${chunk.length} items.`);
  }
});
