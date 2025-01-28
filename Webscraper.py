import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

# ✅ Corrected board game list syntax
board_games = [
    "Gesjaakt",

]

BASE_URL = "https://www.marktplaats.nl/q/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_search_results(query):
    """
    Fetches the search results page for a given search query.
    """
    search_query = urllib.parse.quote_plus(query + " bordspel")
    url = BASE_URL.format(search_query)

    # ✅ Print the URL being searched
    print(f"\n🔎 Search request URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        time.sleep(0.5)  # ✅ Prevents blocking by adding slight delay
        return response.text
    except requests.Timeout:
        print(f"⏳ Request timed out for {query}")
        return None
    except requests.RequestException as e:
        print(f"❌ Request failed for {query}: {e}")
        return None


def parse_results(html_content, full_name, main_name):
    """
    Parses the HTML content and extracts relevant listings.
    Matches either the full game name OR the main name (before `:`).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    items = soup.find_all("li", class_="hz-Listing hz-Listing--list-item")

    results = []
    seen_titles = set()

    full_name_lower = full_name.lower().replace(":", "")
    main_name_lower = main_name.lower().replace(":", "")

    for item in items:
        title_element = item.find("h3")
        price_element = item.find("span", class_="hz-Listing-price")
        description_element = item.find("p", class_="hz-Listing-description")

        title = title_element.get_text(strip=True) if title_element else "No Title"
        price = price_element.get_text(strip=True) if price_element else "No Price"
        description = description_element.get_text(strip=True) if description_element else ""

        title_lower = title.lower().replace(":", "")
        description_lower = description.lower().replace(":", "")

        # ✅ Match full name OR at least the main title
        if full_name_lower in title_lower or full_name_lower in description_lower or \
                main_name_lower in title_lower or main_name_lower in description_lower:

            # ✅ Improved Link Extraction:
            link_element = item.find("a", class_="hz-Link hz-Listing-coverLink", href=True)
            link = ""

            if link_element:
                href = link_element.get("href", "")
                link = "https://www.marktplaats.nl" + href if href.startswith("/") else href

            if not link:
                # 🔍 Alternative method: Find first `<a>` in listing
                alt_link_element = item.find("a", href=True)
                if alt_link_element:
                    alt_href = alt_link_element.get("href", "")
                    link = "https://www.marktplaats.nl" + alt_href if alt_href.startswith("/") else alt_href

            if not link and item.has_attr("data-url"):
                link = "https://www.marktplaats.nl" + item["data-url"]

            results.append({
                "title": title,
                "price": price,
                "description": description,
                "link": link if link else "🔗 No link found"
            })
            seen_titles.add(title)

    print(f"\n✅ Found {len(results)} results for: {full_name}")

    # ✅ Print all listings properly
    for result in results:
        print(f"- Title: {result['title']}")
        print(f"  Price: {result['price']}")
        print(f"  Description: {result['description']}")
        print(f"  Link: {result['link']}\n")

    return results


def scrape():
    """
    Runs the scraper for all board games.
    Searches for both full title and main title if there's a `:`.
    """
    all_results = {}
    for game in board_games:
        main_title = game.split(":")[0].strip()
        queries = [game] if ":" not in game else [game, main_title]

        all_game_results = []
        for query in queries:
            html_content = fetch_search_results(query)
            if html_content:
                results = parse_results(html_content, game, main_title)
                all_game_results.extend(results)

        # ✅ Remove duplicates while keeping best results
        unique_results = {r['title']: r for r in all_game_results}.values()
        all_results[game] = list(unique_results)

    return all_results


if __name__ == '__main__':
    scrape()
