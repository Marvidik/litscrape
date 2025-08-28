let usernames = new Set();

function scrapePage() {
  [...document.querySelectorAll("a")]
    .map(a => a.href)
    .filter(h => h.includes("lit.link/en/"))
    .map(h => h.split("lit.link/en/")[1].split("/")[0]) // username
    .forEach(u => usernames.add(u));

  console.log("✅ Found so far:", [...usernames]);

  // find "Next" button
  let nextBtn = document.querySelector("#pnnext");
  if (nextBtn) {
    console.log("➡️ Going to next page...");
    nextBtn.click();
    setTimeout(scrapePage, 3000); // wait for next page load then scrape again
  } else {
    console.log("🎉 Done! Final list:", [...usernames]);
  }
}

scrapePage();