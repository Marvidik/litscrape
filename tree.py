import requests
from bs4 import BeautifulSoup
import csv, os, time, random
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

BASE_URL = "https://linktr.ee/"

# Load wordlist
def load_wordlist(filename="names.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def scrape_linktree_profile(username):
    url = BASE_URL + username
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # Method 1: Extract ALL <a href> links
        all_links = [a.get("href") for a in soup.find_all("a", href=True)]

        # Method 2: Search for Discord patterns in raw HTML
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

        # Method 3: Linktree-specific link extraction
        nested_links = []
        
        # Look for Linktree's data-testid attributes
        link_containers = soup.find_all(attrs={"data-testid": True})
        for container in link_containers:
            testid = container.get("data-testid", "").lower()
            if "link" in testid:
                nested_a_tags = container.find_all("a", href=True)
                for a_tag in nested_a_tags:
                    href = a_tag.get("href")
                    if href:
                        nested_links.append(href)

        # Look for common Linktree link structures
        # Linktree often uses div elements with specific classes
        link_elements = soup.find_all("div", class_=re.compile(r'.*(link|button|item).*', re.I))
        for element in link_elements:
            nested_a_tags = element.find_all("a", href=True)
            for a_tag in nested_a_tags:
                href = a_tag.get("href")
                if href:
                    nested_links.append(href)

        # Look for span elements that might contain links
        span_elements = soup.find_all("span")
        for span in span_elements:
            parent = span.parent
            if parent and parent.name == "a":
                href = parent.get("href")
                if href:
                    nested_links.append(href)

        # Method 4: Check for JSON data embedded in script tags
        script_tags = soup.find_all("script", type="application/json")
        for script in script_tags:
            try:
                json_data = json.loads(script.string or "")
                json_str = json.dumps(json_data)
                for pattern in discord_patterns:
                    matches = re.findall(pattern, json_str, re.IGNORECASE)
                    for match in matches:
                        if not match.startswith('http'):
                            match = 'https://' + match
                        nested_links.append(match)
            except:
                pass

        # Method 5: Check all script tags for Discord links
        all_scripts = soup.find_all("script")
        for script in all_scripts:
            if script.string:
                for pattern in discord_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    for match in matches:
                        if not match.startswith('http'):
                            match = 'https://' + match
                        nested_links.append(match)

        # Method 6: Look for href attributes in any element
        all_elements_with_href = soup.find_all(attrs={"href": True})
        for element in all_elements_with_href:
            href = element.get("href")
            if href:
                nested_links.append(href)

        # Combine all found links
        all_found_links = all_links + regex_found_links + nested_links

        # Normalize & filter for Discord links
        discord_links = []
        for link in all_found_links:
            if link and isinstance(link, str):
                # Handle relative URLs or malformed URLs
                link = link.strip()
                if link.startswith('//'):
                    link = 'https:' + link
                elif link.startswith('/'):
                    continue  # Skip relative paths
                
                link_lower = link.lower()
                if any(pattern in link_lower for pattern in ["discord.gg", "discord.com/invite", "discordapp.com/invite"]):
                    # Clean up the link
                    if not link.startswith('http'):
                        link = 'https://' + link
                    if link not in discord_links:  # Avoid duplicates
                        discord_links.append(link)

        # Method 7: Search in page text for Discord invites
        page_text = soup.get_text(separator=" ")
        for pattern in discord_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = 'https://' + match
                if match not in discord_links:
                    discord_links.append(match)

        # Remove duplicates while preserving order
        unique_discord_links = []
        seen = set()
        for link in discord_links:
            if link not in seen:
                unique_discord_links.append(link)
                seen.add(link)

        # Check keywords in whole page text for crypto/trading content
        text = soup.get_text(separator=" ").lower()
        crypto_keywords = [
            "crypto", "trading", "forex", "bitcoin", "btc", "eth", "ethereum", 
            "fx", "stock", "nft", "defi", "web3", "blockchain", "altcoin", 
            "trading signals", "pump", "signals", "investment", "portfolio"
        ]
        
        if unique_discord_links and any(word in text for word in crypto_keywords):
            return url, unique_discord_links

    except Exception as e:
        print(f"❌ Error with {url}: {e}")
    return None

# Save results
def save_result(profile, discords, filename="linktree_scraped.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Profile URL", "Discord Links", "Link Count", "Timestamp"])
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([profile, " | ".join(discords), len(discords), timestamp])

if __name__ == "__main__":
    names = load_wordlist("namess.txt")
    total = len(names)
    print(f"📂 Loaded {total} usernames to check on Linktree.")
    print(f"🎯 Looking for crypto/trading profiles with Discord links...\n")

    found_count = 0
    
    for i, name in enumerate(names, 1):
        print(f"🔎 [{i}/{total}] Checking: linktr.ee/{name} ...", end=" ")

        result = scrape_linktree_profile(name)
        if result:
            profile, discords = result
            found_count += 1
            print(f"✅ Found {len(discords)} Discord link(s)")
            print(f"   └─ Links: {', '.join(discords[:2])}")  # Show first 2 links
            save_result(profile, discords)
        else:
            print("— no crypto discord links found")

        # Sleep to avoid rate limiting
        time.sleep(random.uniform(3, 6))

    print(f"\n🎯 Finished scraping Linktree!")
    print(f"📊 Found {found_count} profiles with Discord links out of {total} checked.")