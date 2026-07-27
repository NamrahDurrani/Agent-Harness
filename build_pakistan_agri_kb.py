#!/usr/bin/env python3
"""
build_pakistan_agri_kb.py  —  AgriBot Knowledge Base Builder
=============================================================
Builds a rich Pakistan-only agriculture knowledge base WITHOUT
downloading any PDFs manually.

Strategy 1 — Web Crawl  : Crawl official Pakistan agriculture websites,
                           extract clean text, chunk and embed directly.
Strategy 2 — Structured  : Write curated Pakistan agriculture facts as
                            structured text files — zero download time.
Strategy 3 — Smart Tavily: Configure Tavily to search ONLY Pakistan 
                            agriculture sources at query time.

Run:
    python build_pakistan_agri_kb.py --crawl     # Strategy 1
    python build_pakistan_agri_kb.py --structured # Strategy 2
    python build_pakistan_agri_kb.py --all        # Both (recommended)

Requirements:
    pip install requests trafilatura chromadb sentence-transformers --break-system-packages

After running:
    python main.py --stats   # see chunk count grow
"""

import os, sys, re, time, json, uuid, hashlib, argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

try:
    import requests
    import trafilatura          # best web text extractor — beats BeautifulSoup
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Install required: pip install requests trafilatura --break-system-packages")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
CRAWL_DIR   = BASE_DIR / "crawled_text"       # raw extracted text
STRUCT_DIR  = BASE_DIR / "structured_text"    # hand-curated text files
CRAWL_DIR.mkdir(exist_ok=True)
STRUCT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

CHUNK_SIZE = 800
OVERLAP    = 150
MIN_CHARS  = 200    # ignore pages with less than this much content


# ══════════════════════════════════════════════════════════════════════════════
#  STRATEGY 1 — WEB CRAWL
#  These are Pakistan-only official sites. Trafilatura extracts clean text
#  from HTML pages — same quality as a PDF without downloading files.
# ══════════════════════════════════════════════════════════════════════════════

# Each entry: { "url", "label", "depth" }
# depth=1 → just this page
# depth=2 → this page + all links on it that stay on the same domain
CRAWL_TARGETS = [

    # ── PARC — Pakistan Agricultural Research Council ─────────────────────────
    {"url": "https://parc.gov.pk/index.php/en/research/crops",
     "label": "PARC_crops_research", "depth": 2},
    {"url": "https://parc.gov.pk/index.php/en/research/livestock",
     "label": "PARC_livestock_research", "depth": 2},
    {"url": "https://parc.gov.pk/index.php/en/research/natural-resources",
     "label": "PARC_natural_resources", "depth": 2},
    {"url": "https://parc.gov.pk/index.php/en/crop-varieties",
     "label": "PARC_varieties", "depth": 2},

    # ── Punjab Agriculture Department ─────────────────────────────────────────
    {"url": "https://agripunjab.gov.pk/crop-production-technology",
     "label": "Punjab_crop_tech", "depth": 2},
    {"url": "https://agripunjab.gov.pk/pest-scouting",
     "label": "Punjab_pest_scouting", "depth": 2},
    {"url": "https://agripunjab.gov.pk/weather-advisory",
     "label": "Punjab_weather_advisory", "depth": 2},
    {"url": "https://agripunjab.gov.pk/on-farm-water-management",
     "label": "Punjab_water_mgmt", "depth": 2},
    {"url": "https://agripunjab.gov.pk/soil-fertility",
     "label": "Punjab_soil_fertility", "depth": 2},
    {"url": "https://agripunjab.gov.pk/horticulture",
     "label": "Punjab_horticulture", "depth": 2},

    # ── Sindh Agriculture Department ──────────────────────────────────────────
    {"url": "https://agri.sindh.gov.pk/",
     "label": "Sindh_agri_main", "depth": 2},
    {"url": "https://agri.sindh.gov.pk/crop-calendar",
     "label": "Sindh_crop_calendar", "depth": 1},

    # ── MNFSR ─────────────────────────────────────────────────────────────────
    {"url": "https://mnfsr.gov.pk/publications.php",
     "label": "MNFSR_publications", "depth": 1},
    {"url": "https://mnfsr.gov.pk/food-security.php",
     "label": "MNFSR_food_security", "depth": 2},

    # ── NARC — National Agricultural Research Centre ──────────────────────────
    {"url": "https://narc.gov.pk/research-programs",
     "label": "NARC_programs", "depth": 2},
    {"url": "https://narc.gov.pk/varieties-released",
     "label": "NARC_varieties", "depth": 2},

    # ── Plant Protection Department ───────────────────────────────────────────
    {"url": "https://plantprotection.gov.pk/",
     "label": "PlantProtection_main", "depth": 2},
    {"url": "https://plantprotection.gov.pk/pest-alerts",
     "label": "PlantProtection_alerts", "depth": 2},
    {"url": "https://plantprotection.gov.pk/locust",
     "label": "PlantProtection_locust", "depth": 1},

    # ── On-Farm Water Management Punjab ──────────────────────────────────────
    {"url": "https://ofwm.agripunjab.gov.pk/",
     "label": "OFWM_Punjab", "depth": 2},

    # ── PBS — Pakistan Bureau of Statistics (agriculture chapter) ─────────────
    {"url": "https://www.pbs.gov.pk/content/agricultural-statistics",
     "label": "PBS_agri_stats", "depth": 1},

    # ── Pakistan Economic Survey — Agriculture chapters (HTML versions) ───────
    {"url": "https://www.finance.gov.pk/survey/chapters_23/02-Agriculture.pdf",
     "label": "EconSurvey_2023_agri", "depth": 1},
    {"url": "https://www.finance.gov.pk/survey_2023.html",
     "label": "EconSurvey_2023_index", "depth": 1},

    # ── KPK Agriculture ───────────────────────────────────────────────────────
    {"url": "https://kpagri.gov.pk/",
     "label": "KPK_agriculture", "depth": 2},

    # ── Balochistan Agriculture ───────────────────────────────────────────────
    {"url": "https://agri.balochistan.gov.pk/",
     "label": "Balochistan_agri", "depth": 2},

    # ── AMIS — Agriculture Market Information System ──────────────────────────
    {"url": "https://www.amis.pk/",
     "label": "AMIS_market_prices", "depth": 2},

    # ── Crop For Life (Pakistan-focused ag extension) ─────────────────────────
    {"url": "https://cropforlife.com/",
     "label": "CropForLife", "depth": 2},

    # ── Pakistan Agriculture Wikipedia (high quality summary) ────────────────
    {"url": "https://en.wikipedia.org/wiki/Agriculture_in_Pakistan",
     "label": "Wiki_Pakistan_agriculture", "depth": 1},
    {"url": "https://en.wikipedia.org/wiki/Wheat_production_in_Pakistan",
     "label": "Wiki_wheat_Pakistan", "depth": 1},
    {"url": "https://en.wikipedia.org/wiki/Cotton_production_in_Pakistan",
     "label": "Wiki_cotton_Pakistan", "depth": 1},
    {"url": "https://en.wikipedia.org/wiki/Rice_production_in_Pakistan",
     "label": "Wiki_rice_Pakistan", "depth": 1},
    {"url": "https://en.wikipedia.org/wiki/Indus_Waters_Treaty",
     "label": "Wiki_indus_water", "depth": 1},
    {"url": "https://en.wikipedia.org/wiki/Pakistan_Agricultural_Research_Council",
     "label": "Wiki_PARC", "depth": 1},
]


def make_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    s.headers.update(HEADERS)
    return s


def extract_text_from_url(url: str, session) -> str:
    """Download a URL and extract clean text using Trafilatura."""
    try:
        resp = session.get(url, timeout=(10, 30), verify=False)
        resp.raise_for_status()
        # Trafilatura is purpose-built for this — much better than bs4
        text = trafilatura.extract(
            resp.text,
            include_tables=True,
            include_links=False,
            no_fallback=False,
            favor_recall=True,     # get more text, filter duplicates later
        )
        return text or ""
    except Exception as e:
        print(f"    SKIP {url[:60]}: {e}")
        return ""


def get_same_domain_links(url: str, html: str, base_domain: str) -> List[str]:
    """Extract all links on the page that stay on the same domain."""
    from html.parser import HTMLParser

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                href = dict(attrs).get("href", "")
                if href and not href.startswith("#"):
                    self.links.append(href)

    parser = LinkParser()
    try:
        parser.feed(html)
    except Exception:
        return []

    from urllib.parse import urljoin, urlparse
    links = []
    for href in parser.links:
        full = urljoin(url, href)
        parsed = urlparse(full)
        if base_domain in parsed.netloc:
            clean = parsed._replace(fragment="", query="").geturl()
            if clean not in links:
                links.append(clean)
    return links[:30]   # cap at 30 links per page to avoid infinite crawl


def chunk_text(text: str, source: str, url: str) -> List[Dict]:
    """Split text into overlapping chunks ready for embedding."""
    if len(text) < MIN_CHARS:
        return []
    chunks = []
    pos = 0
    page = 0
    while pos < len(text):
        chunk = text[pos:pos + CHUNK_SIZE].strip()
        if len(chunk) >= MIN_CHARS // 2:
            chunks.append({
                "chunk_text":  chunk,
                "source_file": source,
                "page_num":    page,
                "url":         url,
                "from_crawl":  True,
            })
        pos  += CHUNK_SIZE - OVERLAP
        page += 1
    return chunks


def crawl_and_extract(session) -> List[Dict]:
    """Crawl all targets, extract text, return chunks."""
    all_chunks  = []
    seen_urls   = set()
    seen_hashes = set()   # deduplicate by content hash

    for target in CRAWL_TARGETS:
        base_url   = target["url"]
        label      = target["label"]
        depth      = target["depth"]

        from urllib.parse import urlparse
        base_domain = urlparse(base_url).netloc

        queue = [base_url]
        if depth == 1:
            pages = [base_url]
        else:
            # Depth 2: fetch the root page, collect links, fetch those too
            pages = [base_url]
            try:
                resp = session.get(base_url, timeout=(10, 20), verify=False)
                extra = get_same_domain_links(base_url, resp.text, base_domain)
                pages += [u for u in extra if u not in seen_urls][:20]
            except Exception:
                pass

        for url in pages:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            text = extract_text_from_url(url, session)
            if not text or len(text) < MIN_CHARS:
                continue

            # Dedup by content hash
            h = hashlib.md5(text[:500].encode()).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            # Save raw text to disk (useful for debugging + re-indexing)
            slug = re.sub(r'[^\w]', '_', url)[:80]
            txt_path = CRAWL_DIR / f"{label}__{slug}.txt"
            txt_path.write_text(text, encoding="utf-8")

            chunks = chunk_text(text, label, url)
            all_chunks.extend(chunks)
            print(f"    ✓  {url[:65]:<65}  {len(chunks):>3} chunks")

            time.sleep(0.8)   # polite crawl

    return all_chunks


# ══════════════════════════════════════════════════════════════════════════════
#  STRATEGY 2 — STRUCTURED KNOWLEDGE FILES
#  Hand-curated text covering every major Pakistan agriculture topic.
#  Zero download. Zero crawl. Written once, indexed forever.
#  Each file is ~3000-5000 chars so it produces 5-8 rich chunks.
# ══════════════════════════════════════════════════════════════════════════════

STRUCTURED_KB = {

"pakistan_wheat_comprehensive.txt": """
WHEAT PRODUCTION IN PAKISTAN — Comprehensive Guide
Source: PARC, Punjab Agriculture Department, FAO

OVERVIEW
Pakistan is the 7th largest wheat producer in the world. Wheat is the staple food
crop, covering approximately 9 million hectares annually. Punjab contributes ~75%
of total production. The crop is a Rabi (winter) crop sown Oct-Nov and harvested
Apr-May.

KEY VARIETIES (Released by PARC/Punjab)
- NARC-2011: High yielding, rust resistant, 5500 kg/ha potential
- Punjab-2011: Widely grown in Punjab, tolerates heat stress
- Akbar-2019: Released by ARI Faisalabad, high yield 6000+ kg/ha
- AARI-2011: Rust resistant, widely cultivated
- Zincol-2016: Zinc-biofortified variety, 5800 kg/ha, improves human nutrition
- Borlaug-2016: Climate-resilient, suits late-sown conditions
- Johar-2016: Good for Sindh and Balochistan
- Pakistan-2013: Medium to late maturity, suited to central Punjab

SOWING RECOMMENDATIONS (Punjab)
- Optimal sowing window: 1-15 November (Punjab plains)
- Late sowing: 15 Nov - 15 Dec (yield penalty 30-40 kg/ha per day late)
- Seed rate: 50-60 kg/acre for timely sown; 60-75 kg/acre for late sown
- Row spacing: 22.5 cm (9 inches) preferred
- Seed depth: 5-7 cm

FERTILIZER RECOMMENDATIONS (Punjab)
- Timely sown: Nitrogen 75 kg/acre, Phosphorus 35 kg/acre, Potassium 25 kg/acre
- Split N application: 50% at sowing, 50% at first irrigation (Crown Root Initiation)
- Zinc deficiency common in Punjab — apply 5 kg ZnSO4/acre if soil Zn < 0.8 ppm

IRRIGATION SCHEDULE
- Total irrigations: 3-5 depending on soil type and rainfall
- Critical stages: Crown Root Initiation (20-25 days), Tillering, Jointing, Heading, Grain Filling
- Do NOT irrigate at flowering (increases disease)

MAJOR DISEASES
- Yellow Rust (Puccinia striiformis): Most destructive. Stripe pattern on leaves.
  Management: Resistant varieties + Tebuconazole/Propiconazole spray if >5% severity
- Leaf Rust (Puccinia triticina): Circular orange pustules on leaves
- Stem Rust (Puccinia graminis): Orange-brown pustules on stem (Ug99 race — major threat)
- Karnal Bunt (Tilletia indica): Partially bunted grains, fishy smell
  Management: Thiram/Carboxin seed treatment, QS varieties
- Loose Smut: Treat seed with Vitavax-200 @ 2.5 g/kg seed

MAJOR INSECTS
- Aphids: Spray Imidacloprid 200SL @ 125 ml/acre at 200-250 aphids/tiller
- Termites: Apply Chlorpyrifos @ 1.5 litre/acre in irrigation water
- Army Worm: Spray Chlorpyrifos or Lambda-cyhalothrin

HARVESTING
- Harvest when grain moisture reaches 14-16%
- Combine harvester: Set concave clearance 12-15 mm for wheat
- Threshing losses should not exceed 1.5%

YIELD POTENTIAL vs ACTUAL
- National average: ~3000 kg/ha (30 mounds/acre)
- Achievable on-farm: 4500-5000 kg/ha
- Research station yield: 6000-7000 kg/ha
- Yield gap caused by: Late sowing, unbalanced fertilization, water stress, variety mismatch
""",

"pakistan_cotton_comprehensive.txt": """
COTTON PRODUCTION IN PAKISTAN — Comprehensive Guide
Source: PARC, Central Cotton Research Institute Multan, Punjab Agriculture Dept

OVERVIEW
Cotton is Pakistan's largest industrial crop — the backbone of the textile industry.
Formerly ~3 million hectares; declined to 2-2.2 million ha due to competition from
maize, sugarcane, and climate change. Major producing districts: Multan, Bahawalpur,
Rahim Yar Khan, Sanghar, Mirpur Khas.

KEY VARIETIES
- MNH-886: Released by Multan Nuclear Institute, very popular in Punjab
- CIM-602: Central Cotton Research Institute Multan — bollworm tolerant
- BH-187: Balochistan hybrid, suited to arid conditions  
- Cyto-179: Early-maturing for areas with shorter growing season
- FH-Lalazar: Faisalabad — dual-picking variety

SOWING CALENDAR
- Punjab: 1 May - 31 May (optimal); maximum by 15 June
- Sindh: 15 April - 15 May
- Seed rate: 5-6 kg/acre (delinted, treated seed)
- Row spacing: 75 cm × 30 cm or 90 cm × 22.5 cm
- Germination temperature: minimum 18°C soil temperature

FERTILIZER RECOMMENDATIONS (Punjab)
- Nitrogen: 75 kg N/acre; split in 3-4 applications
  * First application at 3-4 leaf stage (3 weeks after emergence)
  * Second at squaring (6-7 weeks)
  * Third at boll development (if yield potential warrants)
- Phosphorus: 25 kg P2O5/acre (at sowing)
- Potassium: 25 kg K2O/acre (at sowing — critical for fiber quality)
- Boron deficiency: Apply 1 kg Borax/acre as foliar spray (important for boll set)

IRRIGATION MANAGEMENT
- Total water requirement: 8-10 irrigations
- Critical stages: Germination, Squaring, Flowering/Boll set, Boll filling
- Drought stress at boll set reduces yield significantly
- Waterlogging for >24 hours can kill plants — avoid in heavy soils

MAJOR PEST MANAGEMENT (IPM Approach)
- Whitefly (Bemisia tabaci): Most damaging vector of CLCuV
  * Economic threshold: 6 adults/leaf
  * Management: Imidacloprid at emergence, rotate with Buprofezin, Spiromesifen
- Cotton Leaf Curl Virus (CLCuV): Vector = whitefly. No cure — use resistant varieties
- Pink Bollworm: Use pheromone traps. Spray Emamectin or Spinosad if 5 moths/trap/night
- Spotted Bollworm: Same as pink bollworm thresholds
- American Bollworm: Spray Chlorfenapyr or Emamectin @ egg hatching
- Thrips: Spray Dimethoate 40EC @ 300 ml/acre at seedling stage
- Mealy Bug: Apply Chlorpyrifos + Triazophos mixture

HARVESTING
- First picking: 100-110 days after sowing (August-September)
- Seed cotton: 3-4 pickings per season
- Lint turnout: 33-38% (lint:seed cotton ratio)
- Target moisture for ginning: 8-10%

COTTON CRISIS IN PAKISTAN
- Production dropped from 14 million bales (2015) to 5-6 million bales (2023)
- Key causes: CLCuV resistance breakdown, late-sown crop, pesticide resistance,
  heat stress during boll setting, small farm size reducing mechanization
""",

"pakistan_rice_comprehensive.txt": """
RICE PRODUCTION IN PAKISTAN — Comprehensive Guide
Source: Rice Research Institute Kala Shah Kaku, PARC, Punjab Agri Dept

OVERVIEW
Pakistan is 10th largest rice producer globally. Two types:
1. Basmati rice — aromatic, long-grain, premium export commodity
   Produced in: Sheikhupura, Gujranwala, Sialkot, Narowal, Hafizabad
2. IRRI/Coarse rice — short grain, high yield, grown in Sindh
   Produced in: Larkana, Sukkur, Shikarpur, Nawabshah

VARIETIES
Basmati varieties:
- Super Basmati: Most exported, 7.5-8mm grain length, very aromatic
- Basmati-515: Dwarf type, lodging resistant, 5.5-6.5 t/ha potential
- Kernal Basmati: Very fragrant, premium price but low yield 3-4 t/ha
- PK-386: Short duration basmati (125 days), suited for double cropping
IRRI varieties:
- KSK-282: High yielding 7-8 t/ha, suited to Sindh
- KSK-133: Disease resistant, medium maturity
- IR-6: Still widely grown in Sindh, early maturity

CROP CALENDAR
- Nursery raising: 15 May - 15 June
- Transplanting: 15 June - 15 July (optimal window)
- Harvest: October - November
- Crop duration: 120-145 days depending on variety

NURSERY MANAGEMENT
- Seed rate: 8-10 kg/acre for transplanted rice
- Nursery area: 1/10th of field area
- Apply 1 bag urea per kanal of nursery 10-12 days after sowing
- Transplant at 20-25 days age (seedling height 25-35 cm)

LAND PREPARATION (Puddling)
- Flood field, plough 2-3 times while flooded (puddling)
- Purpose: Reduces water percolation by 40-50%
- Level field to within ± 2 cm — critical for uniform water distribution

FERTILIZER (per acre, Punjab recommendations)
- Basmati: N 70 kg, P 25 kg, K 25 kg, Zinc 5 kg ZnSO4
- IRRI: N 80-100 kg, P 35 kg, K 30 kg
- Split N: 50% at transplanting, 25% at tillering, 25% at panicle initiation
- Zinc deficiency very common in calcareous soils — yellowing of leaves

WATER MANAGEMENT
- Continuous flooding traditional method — 1200-1400 mm water/season
- Alternate Wetting and Drying (AWD): 30% water saving, same yield
  * Install perforated pipe 25 cm deep, maintain water 15 cm below surface
  * Re-flood when water drops to 15 cm below surface
  * AVOID AWD during flowering (pollination needs standing water)

MAJOR DISEASES
- Rice Blast (Pyricularia oryzae): Most destructive fungal disease
  * Leaf blast: Diamond-shaped grey lesions with brown border
  * Neck blast: Most damaging — affects grain filling. Spray Tricyclazole
- Bacterial Leaf Blight (Xanthomonas oryzae): Water-soaked lesions from leaf tip
  * No effective fungicide — use resistant varieties, balanced N fertilization
- Brown Plant Hopper: Spray Buprofezin or Fipronil when 10 hoppers/hill

HARVESTING
- Harvest at 20-22% grain moisture (wait for field to dry somewhat)
- Combine adjusted for rice: slow cylinder speed, wide concave gap
- Delay of 1 week past optimal harvest = 5-7% yield loss (shattering)
""",

"pakistan_crop_calendar_all_crops.txt": """
PAKISTAN CROP CALENDAR — All Major Crops
Source: Punjab Agriculture Department, Sindh Agri Dept, PARC

RABI SEASON (Winter — Sown Oct-Nov, Harvested Apr-May)
─────────────────────────────────────────────────────────
Crop        | Sowing Window     | Harvest       | Province
Wheat       | Oct 15 - Nov 15   | Apr 15-May 15 | All provinces (Punjab = 75% area)
Gram/Chickpea| Oct 15-Nov 15    | Mar-Apr       | Punjab (Talagang, D.G.Khan), Balochistan
Lentil      | Oct 15-Nov 1      | Mar-Apr       | Punjab, Balochistan
Barley      | Oct 15-Nov 15     | Apr-May       | Balochistan, KPK, Punjab
Mustard/Canola| Oct 1-15        | Feb-Mar       | Punjab (Faisalabad, Sargodha, Jhang)
Potato (Rabi)| Sep 25-Oct 15   | Jan-Feb       | Punjab (Okara, Sahiwal, Pakpattan)
Sunflower   | Feb 1-Mar 1       | Jun-Jul       | Punjab, Sindh

KHARIF SEASON (Summer — Sown Apr-Jun, Harvested Oct-Dec)
──────────────────────────────────────────────────────────
Crop        | Sowing Window     | Harvest       | Province
Cotton      | Apr 20-Jun 15     | Sep-Dec       | Punjab (central), Sindh
Rice-Basmati| Jun 15-Jul 15     | Oct-Nov       | Punjab (Gujranwala, Sheikhupura)
Rice-IRRI   | Jun 1-Jul 1       | Oct-Nov       | Sindh (Larkana, Sukkur)
Maize       | Apr 15-May 15     | Aug-Sep       | KPK (Peshawar Valley), Punjab
Sugarcane   | Feb-Mar (spring)  | Nov-Apr       | Punjab (Faisalabad), Sindh
            | Sep-Oct (autumn)  |               |
Mung Bean   | Apr 15-May 15     | Jun-Jul       | Punjab (central districts)
Mash (Urd)  | Jul 1-15          | Sep-Oct       | Punjab
Sorghum     | May-Jun           | Sep-Oct       | Punjab, Sindh (fodder use)

YEAR-ROUND / PERENNIAL
──────────────────────────────────────────────────────────
Sugarcane: Perennial ratoon possible for 2-3 seasons
Mango: Flowering Jan-Mar, harvest May-Aug
Citrus: Kinnow harvest Dec-Feb; Oranges Nov-Jan; Malta Jan-Feb
Banana: Year-round in Sindh
Dates: Harvest Jul-Sep (Balochistan, South Punjab)

VEGETABLE CALENDAR (Punjab)
Tomato (autumn): Sep-Oct transplant, harvest Dec-Mar
Tomato (spring): Jan-Feb transplant, harvest Apr-Jun
Onion (Rabi): Oct sowing, Feb-Mar harvest
Onion (Kharif): May-Jun sowing, Sep-Oct harvest
Chilli: Mar-Apr transplant, Aug-Nov harvest
Okra/Bhindi: Apr-Jun sowing, Jul-Oct harvest

CROPPING INTENSITY
Pakistan cropping intensity: 126% (world average ~100%)
Key double-cropping systems in Punjab:
  Rice-Wheat (Gujranwala belt)
  Cotton-Wheat (central Punjab, Sindh)
  Maize-Wheat (KPK, upper Punjab)
  Sugarcane-Wheat (rarely — sugarcane usually takes full year)
""",

"pakistan_soil_types_fertility.txt": """
SOIL TYPES AND FERTILITY IN PAKISTAN
Source: Soil Fertility Research Institute Punjab, PARC Natural Resources Division

MAJOR SOIL TYPES
1. Alluvial Soils (60% of cultivated area)
   - Location: Indus plains — Punjab, Sindh
   - Formed by river deposits from Himalayan rivers
   - Generally fertile but deficient in N, P, and micronutrients
   - Sub-types: Loam, Clay Loam, Sandy Loam
   - pH: 7.5-8.5 (calcareous)

2. Saline-Alkaline Soils (Kallar) — 6.8 million hectares affected
   - Problem areas: Lower Punjab (Multan, Bahawalpur), Sindh
   - EC > 4 dS/m (saline) or pH > 8.5 (sodic)
   - Management: Gypsum @ 5-10 tons/acre, leaching, salt-tolerant varieties
   - Gypsum requirement: Based on soil test — apply CaSO4 to displace Na+

3. Sandy/Desert Soils (Cholistan, Thar)
   - Very low organic matter (<0.5%)
   - Poor water holding capacity
   - Wind erosion major issue

4. Mountain Soils (KPK, Balochistan, AJK)
   - Shallow, stony
   - Higher organic matter in higher elevations
   - Terracing required to prevent erosion

NUTRIENT DEFICIENCIES (Pakistan-wide survey results)
Nutrient     | % Deficient Soils | Critical Level    | Recommendation
Nitrogen     | 95%               | -                 | Apply as per crop requirement
Phosphorus   | 90%               | 7 ppm Olsen P     | DAP or SSP at sowing
Zinc         | 70%               | <0.8 ppm DTPA     | ZnSO4 5 kg/acre or foliar 0.5%
Boron        | 60%               | <0.5 ppm          | Borax 1 kg/acre foliar spray
Iron         | 40%               | <4.5 ppm DTPA     | FeSO4 foliar @ 0.5%
Potassium    | 30% in sandy soils| <100 ppm NH4OAc K | SOP or MOP in light soils
Sulphur      | 25%               | <10 ppm SO4-S     | Gypsum or elemental S

ORGANIC MATTER STATUS
- Punjab average: 0.8% (critically low — optimal >2%)
- Sindh: 0.5-0.7% (very low)
- KPK mountain soils: 2-4% (adequate)

IMPROVING SOIL ORGANIC MATTER
- Farmyard manure: 8-10 tons/acre (most farmers apply 3-4 tons)
- Green manuring: Senji (Trifolium alexandrinum) — sow in Oct, incorporate Mar
- Rice straw incorporation (Punjab): Spreads straw, disc-plough into soil
  Avoids burning (which emits 4 kg N/ton straw + CO2 + particulates)
- Compost: Municipal compost 5-8 tons/acre
- Recommended rotation: Include legume every 3rd crop for N addition

SOIL TESTING SERVICES
- Punjab: Soil Fertility Research Institute, Lahore — free testing for farmers
  Send 500g soil from 0-15cm depth
- Test parameters: pH, EC, OM, N, P, K, Zn, B minimum
- Frequency: Every 3 years minimum

WATER QUALITY FOR IRRIGATION
- Indus system water EC: 0.3-0.8 dS/m (good quality)
- Tube well water in saline areas: EC 1.5-4.0 dS/m (marginal to poor)
- RSC (Residual Sodium Carbonate) > 2.5 meq/L = harmful (use gypsum)
- SAR > 13 = sodification risk
""",

"pakistan_irrigation_system.txt": """
PAKISTAN IRRIGATION SYSTEM — Complete Guide
Source: IRSA, Punjab Irrigation Department, PARC

OVERVIEW — WORLD'S LARGEST CONTIGUOUS IRRIGATION SYSTEM
Pakistan's Indus Basin Irrigation System (IBIS) is the world's largest integrated
irrigation network:
- 3 major storage reservoirs: Tarbela (13.7 MAF), Mangla (7.4 MAF), Chashma (0.87 MAF)
- 19 barrages
- 45 major canal systems
- 107,000 watercourses
- 1.6 million farm outlets (moghas)
- Irrigates approximately 20 million hectares

WATER DISTRIBUTION HIERARCHY
Reservoir → Headworks/Barrage → Main Canal → Branch Canal → Distributary →
Minor Canal → Watercourse → Farm Outlet (Mogha) → Field

INDUS WATERS TREATY (1960)
- Treaty between India and Pakistan signed 1960 (World Bank arbitration)
- Pakistan allocated: Indus, Jhelum, Chenab rivers (Western rivers)
- India allocated: Ravi, Beas, Sutlej rivers (Eastern rivers)
- Pakistan receives ~145 MAF/year under the treaty
- Current dispute: India's dam construction on western rivers

WATER RIGHTS AND WARABANDI
- Warabandi system: Rotational water distribution by turns (baari)
- Each farmer gets water for fixed time proportional to farm area
- One warabandi cycle: 7 days (168 hours)
- Water flow rate: 1 cusec per 100 acres (benchmark)
- Problem: Head farmers (near canal) get more; tail farmers get less

ON-FARM WATER MANAGEMENT (OFWM) TECHNOLOGIES
1. Land Leveling (Laser Leveling)
   - Levels field to ±2 cm accuracy
   - Water saving: 25-30%
   - Yield increase: 10-15% (better germination uniformity)
   - Cost: Rs 1,500-2,500/acre (subsidized by Punjab govt)

2. Watercourse Lining
   - Reduces seepage losses from 30-40% to 5%
   - Reduces waterlogging in lower areas
   - Government subsidizes 75% of cost

3. Drip Irrigation
   - Water saving: 40-50% vs flood irrigation
   - Best for: Orchards, vegetables, sugar beet
   - Cost: Rs 60,000-90,000/acre (initial investment)
   - Punjab government subsidy: 60% for small farmers (<12.5 acres)

4. Sprinkler Irrigation
   - Water saving: 25-30% vs flood
   - Best for: Uneven terrain, sandy soils, fodder crops
   - Cost: Rs 25,000-40,000/acre

GROUNDWATER
- 700,000+ tube wells in Pakistan (mostly in Punjab)
- Groundwater overexploitation in many areas — water table dropping 0.5-1m/year
- Shallow water table areas: Waterlogging problem (South Punjab, Sindh)
  Managed by SCARP (Salinity Control and Reclamation Project) drains + tube wells
- Fresh groundwater zone (EC < 1.5 dS/m): Central Punjab
- Brackish groundwater zone: Bahawalpur, Dera Ghazi Khan, Sindh

WATER PRODUCTIVITY IN PAKISTAN (very low)
- Wheat: 1.0-1.2 kg/m3 (world best = 2.0 kg/m3)
- Rice: 0.3-0.5 kg/m3 (extremely low due to puddling + flooding)
- Cotton: 0.6-0.8 kg/m3
- Improvement path: Laser leveling + improved varieties + crop management
""",

"pakistan_fertilizer_guide.txt": """
FERTILIZER RECOMMENDATIONS FOR PAKISTAN — All Major Crops
Source: NFDC (National Fertilizer Development Centre), Punjab Agriculture Dept

FERTILIZER CONSUMPTION IN PAKISTAN
- Total NPK use: ~4.5 million nutrient tons/year
- Nitrogen: 3.2 million tons (Urea = 80% of N source)
- Phosphate: 0.9 million tons (DAP = dominant)
- Potash: 0.15 million tons (severely underused vs needed)
- Pakistan NPK ratio: 4.8 : 1.3 : 0.2 (recommended = 2:1:0.5)
- Potassium use is only 4% of recommended — biggest nutrient imbalance

FERTILIZER TYPES AVAILABLE IN PAKISTAN
Type            | Formula    | N  | P2O5 | K2O | Notes
Urea            | CO(NH2)2   | 46 | -    | -   | Most common N source; volatilization loss if broadcast
DAP             | NH4H2PO4   | 18 | 46   | -   | Most popular starter fertilizer
SSP             | Ca(H2PO4)2 | -  | 16   | -   | Also supplies Sulphur (11%) + Calcium; good for rice
CAN (Calcium    | -          | 26 | -    | -   | Less burning than urea; good for vegetables
Ammonium Nitrate)
SOP (Sulphate   | K2SO4      | -  | -    | 50  | Premium K source; contains S (17%); for Cl-sensitive crops
of Potash)
MOP (Muriate    | KCl        | -  | -    | 60  | Cheapest K source; avoid for potato, tobacco, citrus
of Potash)
ZnSO4           | -          | -  | -    | -   | Zinc sulphate 33% Zn — critical micronutrient

CROP-WISE FERTILIZER RECOMMENDATIONS (per acre, Punjab)
Crop          | N (kg) | P2O5 (kg) | K2O (kg) | Zn | Notes
Wheat         | 75     | 35        | 25       | 5  | Split N 50%+50%; top-dress 1st irrigation
Cotton        | 75     | 25        | 25       | -  | Add Boron 1 kg; split N 4 times
Rice (Basmati)| 70     | 25        | 25       | 5  | Split N 3 times; do NOT over-apply N (spikelet sterility)
Rice (IRRI)   | 100    | 35        | 30       | 5  | Higher N demand vs Basmati
Maize         | 100    | 45        | 30       | 5  | Most N-demanding crop; apply 30% at sowing, rest split
Sugarcane     | 150    | 60        | 60       | -  | Ratoon crop needs 80% of plant crop dose
Potato        | 100    | 60        | 80       | 5  | K critical for tuber quality; split N 3 times
Sunflower     | 50     | 35        | 25       | -  | Add Boron 1 kg/acre foliar
Gram/Chickpea | 12     | 35        | 15       | 5  | Rhizobium inoculation substitutes N
Canola        | 60     | 35        | 25       | -  | Add Sulphur (SSP or gypsum)

FERTILIZER APPLICATION METHODS
1. Broadcast + Incorporation: Most common; N losses high if no irrigation follows
2. Band Placement (2-3 inches from seed, 2 inches deep): 25-30% fertilizer saving
3. Fertigation (through drip system): Highest efficiency; apply little + often
4. Foliar Spray: For micronutrients only; not practical for macronutrients
5. Seed Treatment: Rhizobium for legumes; Zn + Fe for micronutrient priming

FERTILIZER SUBSIDY IN PAKISTAN (as of 2023-24)
- Urea: Subsidized price Rs 1,768/50kg bag (international parity ~Rs 3,000+)
- DAP: Rs 9,500/50kg bag
- SOP: Rs 4,500/50kg bag
- Subsidy disbursed through: Kissan Card (Punjab), BISP farmers list

NITROGEN USE EFFICIENCY IN PAKISTAN
- Current NUE: ~30-35% (world average 40-45%; best practice 60-70%)
- Improvement steps:
  1. Split applications (multiple small doses > one large dose)
  2. Apply just before rain/irrigation (not when fields are dry)
  3. Neem-coated urea (NEEM-UREA): 10-15% higher NUE
  4. Deep placement (Gora method): Urea 3-4 inches deep in rice — 40% saving
""",

"pakistan_pest_disease_management.txt": """
INTEGRATED PEST MANAGEMENT FOR PAKISTAN — All Major Crops
Source: Department of Plant Protection, Punjab IPM Programme

REGULATORY BODIES
- Department of Plant Protection (DPP), Karachi: National pesticide registration
- Punjab Pesticides Authority: Provincial enforcement
- Crop Disease Forecasting: Punjab Agriculture Department issues advisories

WHEAT PEST AND DISEASE MANAGEMENT
Diseases:
- Yellow/Stripe Rust (Puccinia striiformis f.sp. tritici)
  Symptoms: Yellow stripes along leaf veins
  Threshold: Spray at 1-5% severity before heading
  Fungicides: Propiconazole 250EC @ 160ml/acre, Tebuconazole 250EW @ 200ml/acre
  Timing: One spray at flag leaf, second at heading if needed
  
- Loose Smut (Ustilago tritici)
  Prevention ONLY: Treat seed with Raxil (Tebuconazole) @ 1g/kg or
  Vitavax-200 (Carboxin+Thiram) @ 2.5g/kg seed

- Karnal Bunt (Tilletia indica): Quarantine disease
  Management: Use certified seed, Propiconazole seed treatment

COTTON PEST MANAGEMENT (IPM Calendar)
April-May (seedling):
  - Thrips: Spray Dimethoate 40EC @ 300ml/acre if > 5 thrips/leaf
  - Aphids: Imidacloprid 200SL @ 80ml/acre if > 50 aphids/leaf
  
June-July (vegetative):
  - Whitefly: Buprofezin 25SC @ 400ml/acre if > 5 adults/leaf
  - Dusky cotton bug: Malathion spray on soil around plant base
  
August-September (flowering/boll setting):
  - Spotted bollworm: Pheromone trap monitoring; spray Emamectin if > 10 moths/trap/night
  - Pink bollworm: Helicoverpa-specific BT formulations or Chlorfenapyr
  - American bollworm: Spinosad 45SC @ 80ml/acre
  - Mealy bug: Spray mixture of Chlorpyrifos + Triazophos under leaves and stems

RICE PEST MANAGEMENT
- Stem Borer (Chilo suppressalis): Dead heart in vegetative, white ear at heading
  Spray Chlorpyrifos 40EC @ 500ml/acre when > 5% tillers affected
- Brown Plant Hopper: Spray Fipronil 5SC @ 400ml/acre at > 10 hoppers/hill
- Rice Blast: Spray Tricyclazole 75WP @ 80g/acre at initiation
- Bacterial Leaf Blight: No cure; prevent with balanced N and resistant varieties

LOCUST MANAGEMENT (Desert Locust — major threat)
- Early warning: FAO-DLIS monitoring; DPP Pakistan issues alerts
- Solitarious phase: No problem
- Gregarious phase: Swarms travel 100-200 km/day; can eat own weight daily
- Control: Malathion ULV spraying by aircraft/vehicle; best at dawn/dusk
- Pakistan locust outbreak: 2019-2020 was worst in 26 years

PESTICIDE SAFETY
- PPE mandatory: Gloves, mask, goggles, coverall
- Pre-harvest interval (PHI) must be observed
- Never spray flowering crops (kills pollinators including honeybees)
- Resistance management: Rotate chemical groups (IRAC classification)
- Pakistan Pesticide Act 1971: Registration and enforcement framework
""",

"pakistan_livestock_dairy.txt": """
LIVESTOCK AND DAIRY IN PAKISTAN
Source: Pakistan Bureau of Statistics, PARC Animal Sciences Division

OVERVIEW
Pakistan has one of the world's largest livestock populations:
- Total livestock value: Rs 2.1 trillion/year (56% of agriculture sector value)
- Employs 8-10 million rural households
- Livestock share in GDP: ~12%
- Buffalo and cattle milk Pakistan: 4th largest milk producer globally

LIVESTOCK POPULATION (2022-23)
Species         | Population    | Main Use
Buffalo         | 44 million    | Milk + Draft (90% of buffalo milk globally from Pakistan+India)
Cattle          | 53 million    | Milk + Beef + Draft
Goats           | 80 million    | Meat + Milk + Hair (Mohair from Angora breeds)
Sheep           | 32 million    | Meat + Wool
Camels          | 1.1 million   | Milk + Meat + Transport (Balochistan/Thar)
Poultry (broiler)| 1.4 billion/yr | Meat (urban markets)
Poultry (layers)| 55 million    | Eggs
Donkeys         | 5.7 million   | Draft (rural transport)

MILK PRODUCTION
- Total milk production: 66 billion litres/year
- Nili-Ravi buffalo: Premium milk breed; 8-12 litre/day; 7-8% fat content
- Sahiwal cattle: Indigenous dairy breed; 8-12 litre/day; heat tolerant
- Holstein-Friesian cross: 20-30 litre/day in good management; poor heat tolerance
- Frieswal (HF × Sahiwal cross): 15-20 litre/day; better heat adaptation

MAJOR DISEASES
Foot and Mouth Disease (FMD):
  Caused by: Aphthovirus (types O, A, Asia-1 prevalent in Pakistan)
  Symptoms: Blisters on mouth, feet, teats; high fever; severe production loss
  Vaccination: Trivalent vaccine (O+A+Asia-1) twice yearly
  Pakistan FMD status: Endemic — major trade barrier for livestock export

Brucellosis:
  Caused by: Brucella abortus (cattle) / B. melitensis (small ruminants)
  Symptoms: Abortion in last trimester, retained placenta, reduced fertility
  Control: Test and slaughter in organized farms; no effective vaccine in Pakistan
  Zoonotic: Humans get undulant fever from raw milk — serious public health issue
  
Lumpy Skin Disease (LSD):
  Emerged in Pakistan 2022-23; massive outbreak in Punjab and Sindh
  Caused by: Capripoxvirus; spread by biting insects
  Symptoms: Skin nodules (2-5 cm), fever, reduced milk, weight loss
  Mortality: 1-5% in affected animals
  Control: Sheeppox vaccine (heterologous protection); vector control

Peste des Petits Ruminants (PPR):
  Affects: Goats and sheep
  Symptoms: Fever, nasal discharge, diarrhoea, pneumonia; mortality 50-80%
  Control: Cell-culture attenuated vaccine; 3-yearly vaccination

ANIMAL HUSBANDRY PRACTICES
Feeding systems:
  - Landless urban dairy: Total mixed ration (TMR) with cotton seed cake, green fodder
  - Peri-urban: Gawala (traditional milkman) system
  - Rural: Extensive grazing + crop residue feeding (straw, husk, bhusa)
  
Green fodder crops:
  Berseem (Egyptian Clover): Sown Oct-Nov; cut Nov-Apr; 8-10 cuts/season
  Maize silage: Best energy feed; ensile at 30-35% DM; 6-8 ton DM/acre
  Sorghum-Sudan hybrid: High tonnage summer fodder; 4-6 cuts
  Mott grass: Perennial; 8-10 ton DM/acre/year; suited to Sindh

POULTRY INDUSTRY
- Broiler: 42-day cycle; FCR 1.7-1.8; Liveable liveweight 2.2 kg
- Layer: 72 weeks production; peak production 90-94%; 280-300 eggs/hen/year
- Key disease threats: Newcastle Disease, Infectious Bursal Disease (Gumboro),
  Marek's Disease, Avian Influenza (H5N1 and H9N2 enzootic in Pakistan)
""",

"pakistan_horticulture_fruits.txt": """
HORTICULTURE AND FRUITS IN PAKISTAN
Source: Punjab Horticulture Authority, PARC Horticulture Division

OVERVIEW
Pakistan's horticulture sector: Rs 450 billion value
Major fruits: Mango, citrus, dates, guava, apple, banana, peach
Pakistan mango: 4th largest global producer (1.8 million tonnes)
Pakistan citrus (Kinnow): 2nd largest globally; major export (Saudi Arabia, Russia, Indonesia)

MANGO
Varieties:
- Chaunsa: Most popular export variety; sweet, fibre-free; July-August
- Sindhri: Sindh origin; large fruit; June-July; excellent for export
- Langra: Punjab (Muzaffargarh, DG Khan); kidney-shaped; July
- Anwar Ratol: Very sweet, small fruit; Bahawalpur; August
- Dusehri: Small, aromatic; north Punjab; June-July
- Fajri: Late season (Aug-Sep); round; Multan

Crop management:
- Pruning: After harvest (Oct-Nov) to open canopy
- Fertilization: NPK 500:250:500 g/tree for bearing trees
- Critical irrigation: Flower emergence (Jan-Feb), fruit set (Mar-Apr), fruit enlargement
- Mango Mealybug: Spray Chlorpyrifos before shoot emergence (Dec-Jan)
- Mango Hoppers: Spray at 10% flowering — DO NOT spray at full bloom (kills bees)
- Anthracnose: Spray Mancozeb at pre-flowering; Carbendazim after fruit set
- Post-harvest: Hot water treatment @ 48°C for 60 min (phytosanitary for export)

CITRUS (Kinnow)
- Season: December-February
- Key districts: Sargodha, Mianwali, Khushab, Lahore (Punjab)
- Tree density: 100-150 trees/acre for kinnow
- Fertilization: Young tree Year 1-3: 200 g N, 100 g P, 100 g K/tree/year
               Bearing tree (>5 yr): 2 kg N, 600 g P, 800 g K/tree/year
  Split N: March 40%, June 30%, September 30%
- Irrigation: Critical at flowering (Feb-Mar) and fruit enlargement (Sep-Oct)
- Tristeza virus: Major threat; use certified tristeza-free budwood
- Citrus Psylla: Vector of Huanglongbing (HLB) — not in Pakistan yet but major risk
- Sooty mold on honeydew: Wash with soap water spray + Dimethoate for scale insects

GUAVA
- Varieties: Surahi (pear-shaped), Hafizabadi, Gola (round), Safeda
- Two crops/year: Amrood (spring, April-May) and Dunda (winter, October-November)
- Winter guava (Dunda) fetches higher price
- Key pest: Fruit fly — use methyl eugenol traps + Malathion bait
- Wilt disease (Fusarium): Soil sternization; resistant rootstocks being developed

APPLE (KPK, AJK, Balochistan)
- Growing areas: Swat, Dir, Chitral (KPK); Mastuj; Quetta-Kalat belt (Balochistan)
- Varieties: Golden Delicious, Red Delicious, Fuji (introduced), Kala Kulu (local)
- Apple requires 800-1200 chilling hours (below 7°C) — only high altitudes in Pakistan
- Post-harvest losses: 30-40% due to poor cold storage; government CA (Controlled
  Atmosphere) stores being established in Swat and Quetta

DATE PALM (Phoenix dactylifera)
- Growing areas: Khairpur (Sindh), Turbat, Panjgur (Balochistan), D.I.Khan (KPK)
- Pakistan: 5th largest date producer globally
- Varieties: Aseel (Sindh), Hillawi, Zahidi, Medjool (introduced)
- Pakistan date export: Saudi Arabia, UAE, USA
- Bayoud disease (Fusarium oxysporum f.sp. albedinis): Not yet in Pakistan; quarantine risk

BANANA
- Area: 30,000 hectares mainly in Sindh (Hyderabad, Tando Allahyar)
- Varieties: Williams, Grand Nain (Cavendish type)
- Panama Wilt (Fusarium oxysporum f.sp. cubense TR4): Present in Pakistan;
  use resistant varieties, quarantine infected fields
""",

"pakistan_agri_policy_schemes.txt": """
PAKISTAN AGRICULTURE POLICY, SCHEMES AND SUPPORT
Source: MNFSR, Punjab Agriculture Department, State Bank of Pakistan

MAJOR GOVERNMENT SCHEMES (2022-2024)

1. KISSAN CARD (Punjab)
   - Launched: 2020 (revived 2023 under Punjab Apna Ghar/Kissan Card scheme)
   - Benefit: Rs 25,000/crop season per acre (max 12.5 acres)
   - Use: Can spend at registered input dealers only (fertilizer, seed, pesticide)
   - Eligibility: Registered farmer, CNIC must match land record
   - Status 2023-24: Rs 25 billion disbursed to 1.4 million farmers

2. PRIME MINISTER'S AGRICULTURE EMERGENCY PROGRAMME
   - High-yield seed distribution at subsidized rates
   - 10% subsidy on DAP fertilizer
   - 50% subsidy on laser land leveling (Rs 1,500/acre)
   - Tube well solarization subsidy (covers 50% of solar panel cost)
   
3. KREDITHI / ZARAI TARAQIATI BANK (ZTBL)
   - Agricultural credit at 5-7% markup (concessionary)
   - Short-term: Seed, fertilizer, pesticide (6-12 months)
   - Medium-term: Farm machinery, tube wells (3-5 years)
   - Long-term: Land development, orchards (5-10 years)
   - Total ZTBL credit 2022-23: Rs 360 billion disbursed
   - Target for farmers < 12.5 acres: 70% of portfolio

4. CROP INSURANCE
   - Pakistan Agriculture Insurance Company (PAIC)
   - Mandated for ZTBL borrowers
   - Coverage: Yield loss from flood, drought, hail, frost, pests
   - Premium: 2-3% of sum insured (subsidized 50% by Govt)
   - Challenge: Low outreach; mostly formal credit borrowers covered

MINIMUM SUPPORT PRICES (MSP) 2023-24
- Wheat: Rs 3,900/40 kg (PKR 97.5/kg) — announced by federal govt
- Sugarcane: Rs 425/40 kg (Sindh); Rs 300/40 kg (Punjab)
- Cotton: No formal MSP; price discovered at ginning factory
- Paddy (fine basmati): Market-determined; no MSP
- Oilseeds: No MSP — imported at international prices

AGRICULTURE RESEARCH BUDGET
- PARC budget 2023-24: Rs 8.5 billion
  * Of which capital: Rs 1.2 billion
  * Of which salaries: Rs 6.8 billion
  * Research funds: Only Rs 0.5 billion (very limited)
- NARC Islamabad: Headquarters, 2600 acres research farm
- 4 Regional Agricultural Research Institutes (RARI):
  * ARI Faisalabad: Wheat, cotton, oilseeds
  * ARI Tarnab, Peshawar: Maize, tobacco, fruits (KPK)
  * ARI Sariab, Quetta: Drought-tolerant crops (Balochistan)
  * ARI Tandojam: Rice, sugarcane, vegetables (Sindh)

CROP REPORTING SERVICE
- Punjab CRS: Annual estimates of all crops by district
- Report: Monthly Agricultural Statistics (area, production, yield)
- Data access: mnfsr.gov.pk → Publications → Agricultural Statistics
- Pakistan Agriculture Census: Every 10 years (last completed: 2010; 2020 Mouza Census)

EXPORT OF AGRICULTURE COMMODITIES
- Rice (basmati): $1.1 billion/year (Afghanistan, Saudi Arabia, UAE, US)
- Mango: $70 million/year (UK, Middle East)
- Kinnow: $100 million/year (Russia, Iran, Afghanistan, Saudi Arabia)
- Cotton (raw): Pakistan is net importer due to domestic shortage
- Wheat: Export banned when domestic shortage; export allowed surplus years
- Trade body: TDAP (Trade Development Authority of Pakistan)

CLIMATE CHANGE IMPACT ON PAKISTAN AGRICULTURE
- Temperature rise: +0.3°C/decade in Pakistan (faster than global average)
- Glacier melt: 7,000+ glaciers in Pakistan; Indus water initially higher then crash
- Flood 2022: 33 million affected, $4.8 billion agriculture losses
  (Sindh: 80% cotton crop destroyed; Balochistan: 50% of orchards)
- Drought in Tharparkar, Cholistan: Recurring food insecurity
- Adaptation measures being promoted:
  * Heat-tolerant wheat varieties (NARC-2019, Borlaug-2016)
  * Zero-tillage for wheat (saves 3 litre diesel/acre, reduces moisture loss)
  * Crop diversification (oilseeds, pulses instead of mono-cotton)
"""
}


# ══════════════════════════════════════════════════════════════════════════════
#  STRATEGY 3 — SMART TAVILY CONFIG FOR QUERY TIME
#  Instead of downloading everything, configure Tavily to ONLY search
#  trusted Pakistan agriculture sources. Add to mcp_tools.py or api_server.
# ══════════════════════════════════════════════════════════════════════════════

TAVILY_PAKISTAN_AGRI_CONFIG = {
    "include_domains": [
        "parc.gov.pk",
        "narc.gov.pk",
        "agripunjab.gov.pk",
        "mnfsr.gov.pk",
        "agri.sindh.gov.pk",
        "kpagri.gov.pk",
        "plantprotection.gov.pk",
        "ofwm.agripunjab.gov.pk",
        "pbs.gov.pk",
        "finance.gov.pk",
        "ztbl.com.pk",
        "amis.pk",
        "cropforlife.com",
        "pakissan.com",
        "pakagritech.com",
        "dawn.com",          # best English newspaper — good agriculture coverage
        "geo.tv",
        "thenews.com.pk",
        "brecorder.com",     # business recorder — commodity prices
        "propakistani.com",  # tech + agri content
        "mdpi.com",          # open access journals
        "cgspace.cgiar.org",
        "fao.org",
    ],
    # Exclude non-Pakistan domains when doing agriculture search
    "exclude_domains": [
        "india.gov.in",
        "agricoop.nic.in",
        "icar.org.in",
    ],
    "search_depth": "advanced",
    "max_results": 8,
    "include_answer": True,
}

TAVILY_CONFIG_SNIPPET = '''
# ── Add this to mcp_tools.py → tavily_web_search() ──────────────────────────
# Replace the current client.search() call with:

def tavily_web_search(query: str, max_results: int = 6,
                      pakistan_only: bool = True) -> List[Dict]:
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        # Prepend "Pakistan agriculture" to every query for better focus
        focused_query = f"Pakistan agriculture {query}" if pakistan_only else query
        
        # Build search params
        search_params = {
            "query":        focused_query,
            "max_results":  max_results,
            "search_depth": "advanced",   # better results than "basic"
        }
        
        if pakistan_only:
            search_params["include_domains"] = [
                "parc.gov.pk", "agripunjab.gov.pk", "mnfsr.gov.pk",
                "narc.gov.pk", "plantprotection.gov.pk", "pbs.gov.pk",
                "finance.gov.pk", "amis.pk", "pakissan.com",
                "cropforlife.com", "mdpi.com", "cgspace.cgiar.org",
                "fao.org", "dawn.com", "brecorder.com",
            ]
        
        raw = client.search(**search_params)
        results = []
        for r in raw.get("results", []):
            results.append({
                "title":     r.get("title", ""),
                "url":       r.get("url", ""),
                "content":   r.get("content", ""),
                "site_name": r.get("url", "").split("/")[2].replace("www.", ""),
                "score":     r.get("score", 0.0),
            })
        return results
    except Exception as e:
        print(f"  [TAVILY] Error: {e}")
        return []
'''


# ══════════════════════════════════════════════════════════════════════════════
#  Index chunks into vector store
# ══════════════════════════════════════════════════════════════════════════════

def index_chunks_to_chromadb(chunks: List[Dict], collection_name: str = "agribot_kb"):
    """Index chunks into ChromaDB using the existing vector_store module."""
    try:
        import vector_store
        print(f"\n  Indexing {len(chunks)} chunks into ChromaDB ({collection_name})...")
        added = vector_store.index_chunks(chunks, verbose=True)
        print(f"  ✓ {added} chunks indexed. Total: {vector_store.collection_size()}")
        return added
    except ImportError:
        print("\n  vector_store module not found — saving chunks to JSON for manual indexing")
        out = BASE_DIR / "chunks_for_indexing.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"  Saved to {out} — run: python main.py --index")
        return 0


def write_structured_files():
    """Write all curated knowledge files to STRUCT_DIR."""
    for filename, content in STRUCTURED_KB.items():
        path = STRUCT_DIR / filename
        path.write_text(content.strip(), encoding="utf-8")
        print(f"  ✓  Written: {filename} ({len(content):,} chars)")
    print(f"\n  {len(STRUCTURED_KB)} structured files written to {STRUCT_DIR}/")


def chunk_structured_files() -> List[Dict]:
    """Chunk all files in STRUCT_DIR."""
    all_chunks = []
    for path in sorted(STRUCT_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, path.stem, str(path))
        all_chunks.extend(chunks)
        print(f"  ✓  {path.name}: {len(chunks)} chunks")
    return all_chunks


def chunk_pdfs_if_present() -> List[Dict]:
    """Also chunk any PDFs already in the pdfs/ folder."""
    pdf_dir = BASE_DIR / "pdfs"
    if not pdf_dir.exists():
        return []
    chunks = []
    try:
        import fitz   # PyMuPDF
    except ImportError:
        print("  PyMuPDF not installed — skipping PDF chunking")
        return []
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        try:
            doc   = fitz.open(str(pdf))
            pages = [page.get_text() for page in doc]
            doc.close()
            text = "\n\n".join(pages)
            if len(text) < MIN_CHARS:
                continue
            c = chunk_text(text, pdf.stem, str(pdf))
            chunks.extend(c)
            print(f"  ✓  {pdf.name}: {len(c)} chunks from {len(pages)} pages")
        except Exception as e:
            print(f"  SKIP {pdf.name}: {e}")
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import urllib3
    urllib3.disable_warnings()

    parser = argparse.ArgumentParser(description="AgriBot Pakistan KB Builder")
    parser.add_argument("--crawl",      action="store_true", help="Crawl official Pakistan agri websites")
    parser.add_argument("--structured", action="store_true", help="Write and index curated knowledge files")
    parser.add_argument("--pdfs",       action="store_true", help="Index existing PDFs in pdfs/ folder")
    parser.add_argument("--tavily",     action="store_true", help="Print Tavily config snippet for mcp_tools.py")
    parser.add_argument("--all",        action="store_true", help="Run everything: structured + pdfs + crawl")
    args = parser.parse_args()

    if args.tavily:
        print("\n" + "="*60)
        print("TAVILY PAKISTAN-ONLY CONFIG — paste into mcp_tools.py")
        print("="*60)
        print(TAVILY_CONFIG_SNIPPET)
        return

    all_chunks = []

    if args.structured or args.all:
        print("\n" + "━"*60)
        print("  STRATEGY 2 — Writing curated Pakistan agriculture knowledge")
        print("━"*60)
        write_structured_files()
        chunks = chunk_structured_files()
        all_chunks.extend(chunks)
        print(f"\n  Structured knowledge: {len(chunks)} chunks from {len(STRUCTURED_KB)} files")

    if args.pdfs or args.all:
        print("\n" + "━"*60)
        print("  Chunking existing PDFs in pdfs/ folder")
        print("━"*60)
        chunks = chunk_pdfs_if_present()
        all_chunks.extend(chunks)
        if chunks:
            print(f"\n  PDF chunks: {len(chunks)}")

    if args.crawl or args.all:
        print("\n" + "━"*60)
        print("  STRATEGY 1 — Crawling official Pakistan agriculture websites")
        print("━"*60)
        session = make_session()
        chunks  = crawl_and_extract(session)
        all_chunks.extend(chunks)
        print(f"\n  Web crawl: {len(chunks)} chunks from {len(CRAWL_TARGETS)} targets")

    if not any([args.crawl, args.structured, args.pdfs, args.all]):
        parser.print_help()
        print("\n  Quick start:  python build_pakistan_agri_kb.py --all")
        return

    if all_chunks:
        print(f"\n  Total chunks to index: {len(all_chunks)}")
        index_chunks_to_chromadb(all_chunks)
        print(f"\n  Done. Run:  python main.py --stats  to see total chunk count.")
        print(f"  Then restart:  uvicorn api_server:app --reload --port 8001")


if __name__ == "__main__":
    main()
