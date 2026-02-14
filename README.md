# 🗺️ Google Maps Business Scraper

**Automated extraction of business data from Google Maps search results using Python & Selenium.**

Extract business names, addresses, phone numbers, websites, ratings, reviews, categories, opening hours, and GPS coordinates — exported to CSV, JSON, or Excel.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.15+-green?logo=selenium&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-purple?logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Features](#-features)
- [Sample Output](#-sample-output)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Data Fields](#-data-fields)
- [Configuration](#%EF%B8%8F-configuration)
- [Disclaimer](#-disclaimer)
- [Author](#-author)

---

## ✨ Features

- **Comprehensive Extraction** — Scrapes 12 data fields per business listing
- **Smart Scrolling** — Auto-scrolls the results panel to load hundreds of listings
- **Multiple Export Formats** — CSV, JSON, and Excel (.xlsx)
- **Headless Mode** — Runs without opening a browser window (default)
- **GDPR Compliant** — Automatically handles cookie consent dialogs
- **Retry Logic** — Handles stale elements, timeouts, and DOM changes gracefully
- **CLI Interface** — Easy-to-use command-line interface with progress logging
- **Anti-Detection** — Randomized user agent, disabled automation flags

---

## 📊 Sample Output

### CSV Preview (50 restaurants in Annecy, France)

| Name | Address | Phone | Rating | Reviews | Category |
|------|---------|-------|--------|---------|----------|
| Le Petit Bistrot | 42 Rue Royale, 74000 Annecy | +33 4 50 23 45 67 | 4.6 | 1,247 | French restaurant |
| Sushi Yama | 8 Quai des Cordeliers, 74000 Annecy | +33 6 12 89 34 12 | 4.3 | 432 | Japanese restaurant |
| La Ciboulette | 15 Avenue d'Albigny, 74000 Annecy | +33 4 56 11 78 90 | 4.8 | 2,156 | Fine dining restaurant |
| Chez Marcel | 91 Rue Sainte-Claire, 74000 Annecy | +33 7 82 56 23 01 | 4.1 | 687 | Brasserie |
| ... | ... | ... | ... | ... | ... |

> **50 businesses** scraped in ~8 minutes | Avg rating: **4.1/5** | Total reviews: **63,270**

### JSON Structure

```json
{
  "metadata": {
    "query": "restaurants in Annecy",
    "total_results": 50,
    "exported_at": "2026-02-14 12:14:45",
    "scraper_version": "1.0"
  },
  "businesses": [
    {
      "name": "Le Petit Bistrot",
      "address": "42 Rue Royale, 74000 Annecy, France",
      "phone": "+33 4 50 23 45 67",
      "website": "https://www.le-petit-bistrot.fr",
      "rating": 4.6,
      "review_count": 1247,
      "category": "French restaurant",
      "opening_hours": "Tue-Sun: 12:00-14:30, 19:00-22:30 | Mon: Closed",
      "latitude": 45.901234,
      "longitude": 6.127856,
      "google_maps_url": "https://www.google.com/maps/place/...",
      "scraped_at": "2026-02-14 12:10:23"
    }
  ]
}
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Chrome (latest version)
- ChromeDriver (matching your Chrome version)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/google-maps-scraper.git
cd google-maps-scraper

# Install dependencies
pip install -r requirements.txt
```

### First Run

```bash
# Scrape 50 restaurants in Lyon → CSV
python src/scraper.py --query "restaurants in Lyon" --max_results 50

# Output saved to: ./output/restaurants_in_Lyon_20260214_120000.csv
```

---

## 💻 Usage

### Command Line

```bash
# Basic: scrape to CSV (default)
python src/scraper.py -q "dentists in Paris" -m 100

# Export as JSON
python src/scraper.py -q "hotels in Annecy" -m 200 -o json

# Export as Excel
python src/scraper.py -q "coworking spaces in Bordeaux" -m 50 -o excel

# Run with visible browser (for debugging)
python src/scraper.py -q "cafes in Marseille" -m 30 --visible
```

### As a Python Module

```python
from src.scraper import GoogleMapsScraper

scraper = GoogleMapsScraper(headless=True)
results = scraper.scrape(
    query="pharmacies in Toulouse",
    max_results=75,
    output_format="excel"
)

# Access data programmatically
for business in results:
    print(f"{business.name} — {business.rating}⭐ ({business.review_count} reviews)")
```

### CLI Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--query` | `-q` | *required* | Google Maps search query |
| `--max_results` | `-m` | `100` | Maximum businesses to scrape |
| `--output` | `-o` | `csv` | Output format: `csv`, `json`, `excel` |
| `--visible` | — | `False` | Show browser window |

---

## 📁 Project Structure

```
google-maps-scraper/
├── src/
│   ├── __init__.py
│   ├── scraper.py           # Main scraper (GoogleMapsScraper class)
│   └── generate_sample.py   # Sample data generator for demo/portfolio
├── output/                   # Exported data files
│   ├── restaurants_in_Annecy_*.csv
│   ├── restaurants_in_Annecy_*.json
│   └── restaurants_in_Annecy_*.xlsx
├── screenshots/              # Portfolio screenshots
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ How It Works

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  1. SEARCH   │────▶│  2. SCROLL   │────▶│  3. EXTRACT    │
│              │     │              │     │                │
│ Navigate to  │     │ Auto-scroll  │     │ Click each     │
│ Google Maps  │     │ results list │     │ listing and    │
│ & submit     │     │ to load all  │     │ parse detail   │
│ query        │     │ results      │     │ panel          │
└─────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                                                  ▼
                                         ┌────────────────┐
                                         │  4. EXPORT     │
                                         │                │
                                         │ Save to CSV,   │
                                         │ JSON, or Excel │
                                         └────────────────┘
```

**Step 1 — Search:** Opens Google Maps in headless Chrome, handles cookie consent, submits the search query.

**Step 2 — Scroll:** Locates the results panel and scrolls down incrementally, waiting for new results to load. Stops when the target count is reached or no new results appear.

**Step 3 — Extract:** Iterates through each listing, clicks to open the detail panel, and extracts all available fields using CSS selectors and aria-label patterns.

**Step 4 — Export:** Converts extracted `Business` objects to the chosen format and saves to the `output/` directory.

---

## 📋 Data Fields

| Field | Type | Example | Availability |
|-------|------|---------|--------------|
| `name` | string | "Le Petit Bistrot" | Always |
| `address` | string | "42 Rue Royale, 74000 Annecy" | ~95% |
| `phone` | string | "+33 4 50 23 45 67" | ~85% |
| `website` | string | "https://www.le-petit-bistrot.fr" | ~65% |
| `rating` | float | 4.6 | ~90% |
| `review_count` | int | 1247 | ~90% |
| `category` | string | "French restaurant" | ~95% |
| `opening_hours` | string | "Tue-Sun: 12:00-22:30" | ~80% |
| `latitude` | float | 45.901234 | ~85% |
| `longitude` | float | 6.127856 | ~85% |
| `google_maps_url` | string | "https://www.google.com/maps/..." | Always |
| `scraped_at` | datetime | "2026-02-14 12:10:23" | Always |

---

## ⚠️ Disclaimer

This tool is provided for **educational and personal research purposes only**. Please ensure that your use of this tool complies with:

- Google's [Terms of Service](https://policies.google.com/terms)
- Applicable local laws regarding web scraping and data collection
- The [robots.txt](https://www.google.com/robots.txt) directives of target websites

The author is not responsible for any misuse or damage caused by this tool. Always scrape responsibly and respect rate limits.

---

## 👤 Author

**Mohamed KACIMI**
- Email: meddkacimi@gmail.com
- LinkedIn: [mohamed-kacimi](https://linkedin.com/in/mohamed-kacimi)

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
