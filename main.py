import requests
from bs4 import BeautifulSoup
import csv, os, time, random
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0 Safari/537.36"
}

BASE_URL = "https://lit.link/en/"

# Load wordlist
def load_wordlist(filename="names.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def scrape_profile(username):
    url = BASE_URL + username
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # Method 1: Extract ALL <a href> links
        all_links = [a.get("href") for a in soup.find_all("a", href=True)]

        # Method 2: Search for Discord patterns in the raw HTML text
        html_text = res.text
        discord_patterns = [
            r'https?://discord\.gg/[A-Za-z0-9]+',
            r'https?://discord\.com/invite/[A-Za-z0-9]+',
            r'https?://discordapp\.com/invite/[A-Za-z0-9]+',
            r'discord\.gg/[A-Za-z0-9]+',
            r'discord\.com/invite/[A-Za-z0-9]+'
        ]
        
        regex_found_links = []
        for pattern in discord_patterns:
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = 'https://' + match
                regex_found_links.append(match)

        # Method 3: Look for specific class patterns that might contain Discord links
        
        creator_detail_elements = soup.find_all(class_=re.compile(r'creator-detail-links'))
        nested_links = []
        for element in creator_detail_elements:
            nested_a_tags = element.find_all("a", href=True)
            for a_tag in nested_a_tags:
                href = a_tag.get("href")
                if href:
                    nested_links.append(href)

        # Method 4: Look for any element containing Discord-related attributes or data
        discord_elements = soup.find_all(attrs={"data-channel-name": re.compile(r'.*', re.I)})
        for element in discord_elements:
            # Check all attributes for Discord links
            for attr_name, attr_value in element.attrs.items():
                if isinstance(attr_value, str) and ('discord' in attr_value.lower()):
                    if attr_value.startswith('http'):
                        nested_links.append(attr_value)

        # Combine all found links
        all_found_links = all_links + regex_found_links + nested_links

        # Normalize & filter for Discord links
        discord_links = []
        for link in all_found_links:
            if link and isinstance(link, str):
                link_lower = link.lower()
                if any(pattern in link_lower for pattern in ["discord.gg", "discord.com/invite", "discordapp.com/invite"]):
                    # Clean up the link
                    if not link.startswith('http'):
                        link = 'https://' + link
                    if link not in discord_links:  # Avoid duplicates
                        discord_links.append(link)

        # Method 5: Also check for text content that might contain Discord invites
        page_text = soup.get_text()
        text_discord_matches = []
        for pattern in discord_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = 'https://' + match
                if match not in discord_links:
                    text_discord_matches.append(match)
        
        discord_links.extend(text_discord_matches)

        # Remove duplicates while preserving order
        unique_discord_links = []
        seen = set()
        for link in discord_links:
            if link not in seen:
                unique_discord_links.append(link)
                seen.add(link)

        # Check keywords in whole page text for crypto/trading content
        text = soup.get_text(separator=" ").lower()
        crypto_keywords = ["crypto", "trading", "forex", "bitcoin", "fx", "stock", "nft", "defi", "web3", "blockchain"]
        
        if unique_discord_links and any(word in text for word in crypto_keywords):
            return url, unique_discord_links

    except Exception as e:
        print(f"❌ Error with {url}: {e}")
    return None

# Save results
def save_result(profile, discords, filename="litlink_scraped.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Profile URL", "Discord Links", "Link Count"])
        writer.writerow([profile, " | ".join(discords), len(discords)])

if __name__ == "__main__":
    names = load_wordlist("names.txt")
    total = len(names)
    print(f"📂 Loaded {total} usernames to try.")

    for i, name in enumerate(names, 1):
        print(f"🔎 [{i}/{total}] Checking: {name} ...", end=" ")

        result = scrape_profile(name)
        if result:
            profile, discords = result
            print(f"✅ Found {len(discords)} Discord link(s): {discords[0] if discords else 'N/A'}")
            save_result(profile, discords)
        else:
            print("— no discord links found.")

        # Sleep to avoid detection
        time.sleep(random.uniform(2, 5))

    print("🎯 Finished scraping.")