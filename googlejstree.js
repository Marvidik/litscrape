let usernames = new Set();

function scrapePage() {
  // collect linktree usernames
  [...document.querySelectorAll("a")]
    .map(a => a.href)
    .filter(h => h.includes("linktr.ee/"))
    .map(h => h.split("linktr.ee/")[1].split(/[/?#]/)[0]) // clean username
    .forEach(u => usernames.add(u));

  console.log("✅ Found so far:", [...usernames]);

  // find next page button
  let nextBtn = document.querySelector("#pnnext"); // Google "Next"
  let moreBtn = [...document.querySelectorAll("div[jsname='oHxHid'] span")]
                  .find(el => el.innerText.includes("More search results"));

  if (nextBtn) {
    console.log("➡️ Going to next page...");
    nextBtn.click();
    setTimeout(scrapePage, 3000);
  } else if (moreBtn) {
    console.log("➡️ Clicking 'More search results'...");
    moreBtn.click();
    setTimeout(scrapePage, 3000);
  } else {
    console.log("🎉 Done! Final list:", [...usernames]);
  }
}

scrapePage();
