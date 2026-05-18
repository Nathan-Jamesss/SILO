from bs4 import BeautifulSoup

# ============================================================
# Deep analysis of Devpost .hackathon-tile
# ============================================================
print("=== DEVPOST .hackathon-tile DEEP ANALYSIS ===")
with open("devpost.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
tiles = soup.select(".hackathon-tile")
print(f"Found {len(tiles)} tiles\n")

if tiles:
    first = tiles[0]
    print("=== First tile HTML (truncated) ===")
    print(str(first)[:3000])
    print("\n=== All classes within first tile ===")
    classes = set()
    for el in first.find_all(True):
        for c in (el.get("class") or []):
            classes.add(c)
    print(sorted(classes))

# ============================================================
# Deep analysis of Graham Walker
# ============================================================
print("\n\n=== GRAHAM WALKER DEEP ANALYSIS ===")
with open("gw.html", "r", encoding="utf-8") as f:
    html3 = f.read()

soup3 = BeautifulSoup(html3, "lxml")

# Show main h3 headings  
h3s = soup3.select("main h3")
print(f"Found {len(h3s)} main h3 headings:")
for h in h3s:
    print(f"  '{h.get_text()[:100]}'")
    # Show next sibling content
    for sib in list(h.next_siblings)[:3]:
        sib_text = getattr(sib, 'get_text', lambda: str(sib))()
        print(f"    sibling: '{str(sib_text)[:200]}'")
    print()

# Look for links in the article
print("=== All links in the article ===")
article = soup3.select_one("article, .entry-content, main")
if article:
    links = article.find_all("a", href=True)
    for link in links[:20]:
        print(f"  '{link.get_text()[:60]}' -> {link['href'][:100]}")

# ============================================================
# MassChallenge - check if page loaded
# ============================================================
print("\n\n=== MASSCHALLENGE HTML SAMPLE ===")
with open("mc.html", "r", encoding="utf-8") as f:
    html2 = f.read()

soup2 = BeautifulSoup(html2, "lxml")
print(f"Total HTML length: {len(html2)}")
title = soup2.find("title")
print(f"Page title: {title.get_text() if title else 'N/A'}")
# Show body text  
body = soup2.find("body")
if body:
    text = body.get_text()[:2000]
    print(f"Body text (first 2000 chars):\n{text}")
