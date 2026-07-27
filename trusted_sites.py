# https://agripunjab.gov.pk/aari-inst-Wheat
# https://agripunjab.gov.pk/aari-inst-potato
# https://www.parc.gov.pk/index
# https://agripunjab.gov.pk/aari-inst-Mango
# https://www.luawms.edu.pk/
# https://su.edu.pk/faculty/Faculty-of-Agriculture
# https://sau.edu.pk/
# https://www.fao.org/home/en/
# https://www.irri.org/
# https://www.cgiar.org/
# https://ztbl.com.pk/agriculture-loans/
# https://www.passco.gov.pk/
# https://nfdc.gov.pk/
# https://pccc.gov.pk/
# https://icarda.org/
# https://www.nifa.org.pk/
# https://agripunjab.gov.pk/aari-inst-PPRI
# https://agripunjab.gov.pk/aari-overview
# https://agri.sindh.gov.pk/
# https://www.pbs.gov.pk/agriculture-sector-of-pakistan-importance-role-key-statistics/


"""
trusted_sites.py
================
The 20 agriculture-focused trusted domains used for web search fallback.

When the local PDF knowledge base cannot answer a query, the pipeline
searches ONLY these domains (via DuckDuckGo site: filters) rather than
the open internet — guaranteeing sources stay domain-specific, credible,
and agriculture-relevant.

Each entry has:
  domain     — the bare domain string used in the DuckDuckGo site: filter
  name       — human-readable label shown in the SOURCES block to the user
  seed_url   — canonical URL (used only for display / documentation)
  category   — grouping for reference
"""

TRUSTED_SITES = [
    # ── Pakistan government / research ────────────────────────────────────────
    {
        "domain":   "agripunjab.gov.pk",
        "name":     "Agriculture Department Punjab (AARI)",
        "seed_url": "https://agripunjab.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "parc.gov.pk",
        "name":     "Pakistan Agricultural Research Council (PARC)",
        "seed_url": "https://www.parc.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "agri.sindh.gov.pk",
        "name":     "Agriculture Department Sindh",
        "seed_url": "https://agri.sindh.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "passco.gov.pk",
        "name":     "Pakistan Agriculture Storage & Services Corporation (PASSCO)",
        "seed_url": "https://www.passco.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "nfdc.gov.pk",
        "name":     "National Fertilizer Development Centre (NFDC)",
        "seed_url": "https://nfdc.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "pccc.gov.pk",
        "name":     "Pakistan Central Cotton Committee (PCCC)",
        "seed_url": "https://pccc.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "pbs.gov.pk",
        "name":     "Pakistan Bureau of Statistics (PBS)",
        "seed_url": "https://www.pbs.gov.pk",
        "category": "Pakistan Government",
    },
    {
        "domain":   "nifa.org.pk",
        "name":     "Nuclear Institute for Food and Agriculture (NIFA)",
        "seed_url": "https://www.nifa.org.pk",
        "category": "Pakistan Research",
    },
    {
        "domain":   "ztbl.com.pk",
        "name":     "Zarai Taraqiati Bank Ltd (ZTBL)",
        "seed_url": "https://ztbl.com.pk",
        "category": "Pakistan Finance",
    },

    # ── Pakistan universities ─────────────────────────────────────────────────
    {
        "domain":   "luawms.edu.pk",
        "name":     "Lasbela University of Agriculture (LUAWMS)",
        "seed_url": "https://www.luawms.edu.pk",
        "category": "Pakistan University",
    },
    {
        "domain":   "su.edu.pk",
        "name":     "University of Sindh — Faculty of Agriculture",
        "seed_url": "https://su.edu.pk/faculty/Faculty-of-Agriculture",
        "category": "Pakistan University",
    },
    {
        "domain":   "sau.edu.pk",
        "name":     "Sindh Agriculture University",
        "seed_url": "https://sau.edu.pk",
        "category": "Pakistan University",
    },

    # ── International agriculture organizations ────────────────────────────────
    {
        "domain":   "fao.org",
        "name":     "Food and Agriculture Organization (FAO)",
        "seed_url": "https://www.fao.org",
        "category": "International Organization",
    },
    {
        "domain":   "irri.org",
        "name":     "International Rice Research Institute (IRRI)",
        "seed_url": "https://www.irri.org",
        "category": "International Research",
    },
    {
        "domain":   "cgiar.org",
        "name":     "CGIAR (Consultative Group on International Agricultural Research)",
        "seed_url": "https://www.cgiar.org",
        "category": "International Research",
    },
    {
        "domain":   "icarda.org",
        "name":     "International Center for Agricultural Research in the Dry Areas (ICARDA)",
        "seed_url": "https://icarda.org",
        "category": "International Research",
    },
]

# ── Convenience helpers ───────────────────────────────────────────────────────

# Flat list of bare domains — used to build the DuckDuckGo site: query
TRUSTED_DOMAINS = [s["domain"] for s in TRUSTED_SITES]

# Domain → display name mapping — used in the SOURCES block
DOMAIN_NAMES = {s["domain"]: s["name"] for s in TRUSTED_SITES}


def get_display_name(url: str) -> str:
    """Return the human-readable site name for a given URL, or the domain."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lstrip("www.")
    # Try exact match first, then partial match
    if domain in DOMAIN_NAMES:
        return DOMAIN_NAMES[domain]
    for d, name in DOMAIN_NAMES.items():
        if domain.endswith(d) or d.endswith(domain):
            return name
    return domain


def build_ddg_site_filter() -> str:
    """
    Build the DuckDuckGo site: filter string for all trusted domains.
    Example: 'site:parc.gov.pk OR site:fao.org OR site:irri.org ...'
    DuckDuckGo supports OR between site: filters in a single query.
    """
    return " OR ".join(f"site:{d}" for d in TRUSTED_DOMAINS)


if __name__ == "__main__":
    print("Trusted domains:", len(TRUSTED_DOMAINS))
    for s in TRUSTED_SITES:
        print(f"  [{s['category']}] {s['name']}  ({s['domain']})")
    print("\nDDG filter snippet:", build_ddg_site_filter()[:120], "...")