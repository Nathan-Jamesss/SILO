from bs4 import BeautifulSoup

# ============================================================
# Analyze Devpost HTML
# ============================================================
print("=== DEVPOST SELECTORS ===")
with open("devpost.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

for sel in [
    "#challenges-list li",
    ".challenge-listing",
    ".hackathon-tile",
    "article.challenge-listing",
    "li.clearfix",
    "li[data-challenge-id]",
    ".challenge-tile",
    "a.challenge-tile",
]:
    found = soup.select(sel)
    print(f"  {sel!r}: {len(found)} found")

cl = soup.select_one("#challenges-list")
if cl:
    items = cl.find_all("li", recursive=False)
    print(f"\n#challenges-list has {len(items)} top-level <li>")
    if items:
        first = items[0]
        print("  First li attrs:", {k: v for k, v in list(first.attrs.items())[:6]})
        h = first.find(["h1", "h2", "h3", "h4"])
        if h:
            print(f"  Heading: <{h.name}> '{h.get_text()[:80]}'")
        a = first.find("a")
        if a:
            print(f"  Link: {a.get('href', '')[:100]}")
        # show all class names used inside
        classes = set()
        for el in first.find_all(True):
            for c in (el.get("class") or []):
                classes.add(c)
        print("  Classes inside:", sorted(classes)[:30])
else:
    print("NO #challenges-list — looking for alternatives...")
    for sel in ["ul[id*=challenge]", "ul[class*=challenge]", "div[id*=challenge]"]:
        found = soup.select(sel)
        if found:
            print(f"  Found {len(found)} via {sel!r}")

# ============================================================
# Analyze MassChallenge HTML
# ============================================================
print("\n=== MASSCHALLENGE SELECTORS ===")
with open("mc.html", "r", encoding="utf-8") as f:
    html2 = f.read()

soup2 = BeautifulSoup(html2, "lxml")

for sel in [
    ".program-card",
    "article.type-program",
    ".card-grid__item",
    ".grid-item",
    ".elementor-post",
    "article",
    ".program",
    "a[href*='/programs/']",
]:
    found = soup2.select(sel)
    print(f"  {sel!r}: {len(found)} found")

# Find any card-like structure
cards = soup2.select("article") or soup2.select("[class*=card]") or soup2.select("[class*=program]")
if cards:
    first = cards[0]
    print(f"\nFirst card tag: {first.name}, classes: {first.get('class')}")
    h = first.find(["h1", "h2", "h3", "h4"])
    if h:
        print(f"  Heading: <{h.name}> '{h.get_text()[:80]}'")
    a = first.find("a")
    if a:
        print(f"  Link: {a.get('href', '')[:100]}")

# ============================================================
# Analyze Graham Walker HTML
# ============================================================
print("\n=== GRAHAM WALKER SELECTORS ===")
with open("gw.html", "r", encoding="utf-8") as f:
    html3 = f.read()

soup3 = BeautifulSoup(html3, "lxml")

for sel in [
    "article h2",
    "article h3",
    ".entry-content h2",
    ".entry-content h3",
    ".post-content h2",
    ".post-content h3",
    "main h2",
    "main h3",
    ".wp-block-heading",
]:
    found = soup3.select(sel)
    print(f"  {sel!r}: {len(found)} found")

h2s = soup3.select("article h2, .entry-content h2, main h2, .wp-block-heading")
if h2s:
    print(f"\nFound {len(h2s)} headings. First 5:")
    for h in h2s[:5]:
        print(f"  '{h.get_text()[:80]}'")

print("\nDone!")
