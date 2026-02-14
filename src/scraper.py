"""
Google Maps Business Scraper
=============================
Extracts business data (name, address, phone, website, rating, reviews, hours)
from Google Maps search results using Selenium.

Author: Mohamed KACIMI
GitHub: https://github.com/your-username/google-maps-scraper

Usage:
    python src/scraper.py --query "restaurants in Lyon" --max_results 100
    python src/scraper.py --query "dentists in Paris" --max_results 50 --output csv
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

GOOGLE_MAPS_URL = "https://www.google.com/maps"
DEFAULT_WAIT = 10
SCROLL_PAUSE = 1.5
MAX_RETRIES = 3

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Data Model
# ──────────────────────────────────────────────

@dataclass
class Business:
    """Represents a single business extracted from Google Maps."""
    name: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: str = ""
    opening_hours: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_url: str = ""
    scraped_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def is_valid(self) -> bool:
        """Check if the business has minimum required data."""
        return bool(self.name and (self.address or self.phone))


# ──────────────────────────────────────────────
# Scraper Class
# ──────────────────────────────────────────────

class GoogleMapsScraper:
    """
    Scrapes business listings from Google Maps search results.

    Features:
        - Headless or visible browser mode
        - Auto-scrolling to load all results
        - Extracts: name, address, phone, website, rating, reviews,
          category, opening hours, coordinates, Google Maps URL
        - Export to CSV, JSON, or Excel
        - Built-in retry logic and error handling
    """

    def __init__(self, headless: bool = True, browser: str = "chrome"):
        """
        Initialize the scraper with Chrome or Firefox WebDriver.

        Args:
            headless: Run browser in headless mode (no GUI). Default True.
            browser: Browser to use — 'chrome' or 'firefox'. Default 'chrome'.
        """
        self.headless = headless
        self.browser = browser.lower()
        self.driver = None
        self.businesses: list[Business] = []

    def _init_driver(self):
        """Configure and launch the selected WebDriver (Chrome or Firefox)."""

        if self.browser == "firefox":
            self._init_firefox()
        else:
            self._init_chrome()

        self.driver.implicitly_wait(DEFAULT_WAIT)

        # Remove webdriver flag
        try:
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except Exception:
            pass  # Some Firefox versions block this — safe to skip

        logger.info(
            "%s WebDriver initialized (headless=%s)",
            self.browser.capitalize(), self.headless,
        )

    def _init_chrome(self):
        """Configure and launch Chrome WebDriver."""
        options = ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=en-US")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        # Reduce detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)

    def _init_firefox(self):
        """Configure and launch Firefox (GeckoDriver) WebDriver."""
        options = FirefoxOptions()

        if self.headless:
            options.add_argument("--headless")

        options.add_argument("--width=1920")
        options.add_argument("--height=1080")

        # Set language to English for consistent selectors
        options.set_preference("intl.accept_languages", "en-US, en")

        # Custom user agent
        options.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0",
        )

        # Disable webdriver detection
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)

        # Disable notifications and popups
        options.set_preference("dom.push.enabled", False)
        options.set_preference("permissions.default.desktop-notification", 2)

        self.driver = webdriver.Firefox(options=options)

    def search(self, query: str):
        """
        Navigate to Google Maps and execute a search query.

        Args:
            query: Search string (e.g., "restaurants in Paris").
        """
        logger.info("Searching Google Maps for: '%s'", query)
        self.driver.get(GOOGLE_MAPS_URL)
        time.sleep(3)

        # Handle cookie consent (EU / GDPR) — must be done BEFORE search box is accessible
        self._handle_consent()

        # Wait for page to fully load after consent
        time.sleep(2)

        # Find and fill the search box — try multiple selectors
        search_box = None
        selectors = [
            (By.ID, "searchboxinput"),
            (By.CSS_SELECTOR, "input#searchboxinput"),
            (By.CSS_SELECTOR, "input[aria-label='Search Google Maps']"),
            (By.CSS_SELECTOR, "input[aria-label='Rechercher sur Google Maps']"),
            (By.CSS_SELECTOR, "input[name='q']"),
        ]

        for by, selector in selectors:
            try:
                search_box = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((by, selector))
                )
                logger.info("Search box found with selector: %s", selector)
                break
            except TimeoutException:
                continue

        if search_box is None:
            # Last resort: take a screenshot for debugging and save current URL
            logger.error("Could not find the search box after trying all selectors.")
            logger.error("Current URL: %s", self.driver.current_url)
            logger.error("Page title: %s", self.driver.title)
            try:
                debug_path = os.path.join(
                    os.path.dirname(__file__), "..", "output", "debug_screenshot.png"
                )
                self.driver.save_screenshot(debug_path)
                logger.error("Debug screenshot saved to: %s", debug_path)
            except Exception:
                pass
            raise TimeoutException(
                "Search box not found. This is usually caused by:\n"
                "  1. Cookie consent dialog not dismissed properly\n"
                "  2. Google Maps changed its layout\n"
                "  3. Network issue preventing page load\n"
                "Try running with --visible to see what's happening."
            )

        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(3)
        logger.info("Search submitted successfully")

    def _handle_consent(self):
        """
        Dismiss Google's cookie consent dialog if present.

        Google shows consent in different ways:
          - Direct buttons on the page
          - Inside an iframe (common in EU / Firefox)
          - Different button texts by language (EN/FR/DE/etc.)
        """
        logger.info("Checking for cookie consent dialog...")

        # ── Attempt 1: Consent button directly on the page ──
        button_xpaths = [
            "//button[contains(., 'Accept all')]",
            "//button[contains(., 'Tout accepter')]",
            "//button[contains(., 'Alle akzeptieren')]",
            "//button[contains(., 'Aceptar todo')]",
            "//button[contains(., 'Accetta tutto')]",
            "//button[contains(., 'Accept')]",
            "//form//button[contains(@aria-label, 'Accept')]",
            "//button[contains(@aria-label, 'Tout accepter')]",
            "//button[contains(@aria-label, 'Accept all')]",
        ]

        for xpath in button_xpaths:
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                btn.click()
                logger.info("Cookie consent accepted (direct button)")
                time.sleep(2)
                return
            except (TimeoutException, NoSuchElementException,
                    ElementClickInterceptedException):
                continue

        # ── Attempt 2: Consent inside an iframe (common in EU on Firefox) ──
        iframe_selectors = [
            "iframe[src*='consent.google']",
            "iframe[src*='consent']",
            "iframe#usercentrics-cmp-ui",
        ]

        for iframe_css in iframe_selectors:
            try:
                iframe = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, iframe_css))
                )
                self.driver.switch_to.frame(iframe)
                logger.info("Switched to consent iframe: %s", iframe_css)

                # Try to find the accept button inside the iframe
                for xpath in button_xpaths:
                    try:
                        btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        btn.click()
                        logger.info("Cookie consent accepted (inside iframe)")
                        self.driver.switch_to.default_content()
                        time.sleep(2)
                        return
                    except (TimeoutException, NoSuchElementException):
                        continue

                # Also try generic buttons inside iframe
                try:
                    btn = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[aria-label*='ccept'], button[aria-label*='Agree']"
                    )
                    btn.click()
                    logger.info("Cookie consent accepted (iframe generic button)")
                    self.driver.switch_to.default_content()
                    time.sleep(2)
                    return
                except NoSuchElementException:
                    pass

                self.driver.switch_to.default_content()
            except (TimeoutException, NoSuchElementException):
                continue

        # ── Attempt 3: Click any visible "Accept" / "Agree" button as last resort ──
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                try:
                    text = btn.text.lower()
                    if any(keyword in text for keyword in [
                        "accept", "accepter", "agree", "consent",
                        "akzeptieren", "aceptar", "accetta", "j'accepte",
                    ]):
                        btn.click()
                        logger.info("Cookie consent accepted (fallback: '%s')", btn.text.strip())
                        time.sleep(2)
                        return
                except (StaleElementReferenceException, ElementClickInterceptedException):
                    continue
        except Exception:
            pass

        logger.info("No cookie consent dialog detected (or already accepted)")

    def scroll_results(self, max_results: int = 100):
        """
        Scroll the results panel to load more business listings.

        Args:
            max_results: Target number of results to load.
        """
        logger.info("Scrolling to load up to %d results...", max_results)

        # Locate the scrollable results panel
        try:
            results_panel = WebDriverWait(self.driver, DEFAULT_WAIT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[role='feed']")
                )
            )
        except TimeoutException:
            logger.warning("Could not find results feed panel. Trying alternative selector...")
            try:
                results_panel = self.driver.find_element(
                    By.CSS_SELECTOR, "div.m6QErb[aria-label]"
                )
            except NoSuchElementException:
                logger.error("Results panel not found. Search may have returned no results.")
                return

        prev_count = 0
        stale_rounds = 0

        while True:
            # Scroll down inside the results panel
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", results_panel
            )
            time.sleep(SCROLL_PAUSE)

            # Count currently loaded results
            items = self.driver.find_elements(By.CSS_SELECTOR, "[data-result-index]")
            if not items:
                items = self.driver.find_elements(
                    By.CSS_SELECTOR, "div.Nv2PK"
                )

            current_count = len(items)
            logger.info("  Loaded %d / %d results", current_count, max_results)

            if current_count >= max_results:
                logger.info("Reached target of %d results", max_results)
                break

            # Check if we've hit the bottom (no new results loaded)
            if current_count == prev_count:
                stale_rounds += 1
                if stale_rounds >= 3:
                    logger.info("No more results to load (total: %d)", current_count)
                    break
            else:
                stale_rounds = 0

            prev_count = current_count

            # Check for "end of list" indicator
            try:
                self.driver.find_element(
                    By.XPATH, "//*[contains(text(), \"You've reached the end\")]"
                )
                logger.info("Reached end of results list")
                break
            except NoSuchElementException:
                pass

    def extract_businesses(self, max_results: int = 100):
        """
        Click on each listing and extract detailed business data.

        Args:
            max_results: Maximum number of businesses to extract.
        """
        logger.info("Extracting business details...")

        # Get all listing elements
        listings = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        if not listings:
            listings = self.driver.find_elements(By.CSS_SELECTOR, "[data-result-index]")

        total = min(len(listings), max_results)
        logger.info("Found %d listings to process", total)

        for i in range(total):
            try:
                # Re-fetch listings (DOM may have changed after scrolling back)
                listings = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
                if not listings:
                    listings = self.driver.find_elements(
                        By.CSS_SELECTOR, "[data-result-index]"
                    )

                if i >= len(listings):
                    break

                listing = listings[i]

                # Scroll listing into view and click
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", listing
                )
                time.sleep(0.5)

                try:
                    listing.click()
                except ElementClickInterceptedException:
                    ActionChains(self.driver).move_to_element(listing).click().perform()

                time.sleep(2)

                # Extract data from the detail panel
                business = self._extract_detail()
                business.scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if business.is_valid():
                    self.businesses.append(business)
                    logger.info(
                        "  [%d/%d] ✓ %s", i + 1, total, business.name
                    )
                else:
                    logger.warning("  [%d/%d] ✗ Skipped (insufficient data)", i + 1, total)

            except (StaleElementReferenceException, TimeoutException) as e:
                logger.warning("  [%d/%d] ✗ Error: %s", i + 1, total, str(e))
                continue
            except Exception as e:
                logger.warning("  [%d/%d] ✗ Unexpected error: %s", i + 1, total, str(e))
                continue

        logger.info("Extraction complete: %d businesses collected", len(self.businesses))

    def _extract_detail(self) -> Business:
        """Extract all available fields from the currently open detail panel."""
        biz = Business()

        # Name
        biz.name = self._safe_text("h1.DUwDvf")

        # Rating
        rating_text = self._safe_text("div.F7nice span[aria-hidden='true']")
        if rating_text:
            try:
                biz.rating = float(rating_text.replace(",", "."))
            except ValueError:
                pass

        # Review count
        review_text = self._safe_text("div.F7nice span span")
        if review_text:
            numbers = re.findall(r"[\d,.\s]+", review_text)
            if numbers:
                try:
                    biz.review_count = int(
                        numbers[0].replace(",", "").replace(".", "").replace(" ", "").strip()
                    )
                except ValueError:
                    pass

        # Category
        biz.category = self._safe_text("button.DkEaL")

        # Address
        biz.address = self._safe_aria_text("Address|Adresse")

        # Phone
        biz.phone = self._safe_aria_text("Phone|Téléphone")

        # Website
        biz.website = self._safe_aria_text("Website|Site web")

        # Opening hours
        biz.opening_hours = self._safe_aria_text(
            "Hours|Horaires", fallback_selector="div.o0Svhf span"
        )

        # Coordinates from URL
        try:
            current_url = self.driver.current_url
            biz.google_maps_url = current_url
            coord_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
            if coord_match:
                biz.latitude = float(coord_match.group(1))
                biz.longitude = float(coord_match.group(2))
        except Exception:
            pass

        return biz

    def _safe_text(self, css_selector: str) -> str:
        """Safely extract text from a CSS selector."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            return el.text.strip()
        except NoSuchElementException:
            return ""

    def _safe_aria_text(
        self, aria_pattern: str, fallback_selector: str = ""
    ) -> str:
        """
        Extract text from an element matching an aria-label pattern.
        Used for address, phone, website, hours buttons.
        """
        patterns = aria_pattern.split("|")
        for pattern in patterns:
            try:
                el = self.driver.find_element(
                    By.CSS_SELECTOR,
                    f"button[aria-label*='{pattern}'], "
                    f"a[aria-label*='{pattern}'], "
                    f"div[aria-label*='{pattern}']",
                )
                label = el.get_attribute("aria-label") or ""
                # The aria-label typically contains "Address: 123 Main St"
                if ":" in label:
                    return label.split(":", 1)[1].strip()
                return label.strip()
            except NoSuchElementException:
                continue

        # Fallback selector
        if fallback_selector:
            return self._safe_text(fallback_selector)
        return ""

    # ──────────────────────────────────────────
    # Export Methods
    # ──────────────────────────────────────────

    def export_csv(self, filepath: str):
        """Export scraped data to a CSV file."""
        if not self.businesses:
            logger.warning("No data to export.")
            return

        fieldnames = list(Business().to_dict().keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for biz in self.businesses:
                writer.writerow(biz.to_dict())

        logger.info("Exported %d businesses to %s", len(self.businesses), filepath)

    def export_json(self, filepath: str):
        """Export scraped data to a JSON file."""
        if not self.businesses:
            logger.warning("No data to export.")
            return

        data = {
            "metadata": {
                "total_results": len(self.businesses),
                "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "businesses": [biz.to_dict() for biz in self.businesses],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Exported %d businesses to %s", len(self.businesses), filepath)

    def export_excel(self, filepath: str):
        """Export scraped data to an Excel file (requires pandas + openpyxl)."""
        if not HAS_PANDAS:
            logger.error("pandas is required for Excel export. Install: pip install pandas openpyxl")
            logger.info("Falling back to CSV export...")
            csv_path = filepath.replace(".xlsx", ".csv")
            self.export_csv(csv_path)
            return

        if not self.businesses:
            logger.warning("No data to export.")
            return

        df = pd.DataFrame([biz.to_dict() for biz in self.businesses])

        # Clean up columns for readability
        df.columns = [col.replace("_", " ").title() for col in df.columns]

        df.to_excel(filepath, index=False, sheet_name="Google Maps Data")
        logger.info("Exported %d businesses to %s", len(self.businesses), filepath)

    # ──────────────────────────────────────────
    # Main Workflow
    # ──────────────────────────────────────────

    def scrape(self, query: str, max_results: int = 100, output_format: str = "csv"):
        """
        Full scraping pipeline: search → scroll → extract → export.

        Args:
            query: Google Maps search query.
            max_results: Max number of businesses to scrape.
            output_format: Export format ('csv', 'json', or 'excel').

        Returns:
            list[Business]: List of scraped businesses.

        Supports both Chrome and Firefox browsers (set in __init__).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r"[^\w\s-]", "", query).replace(" ", "_")[:40]

        try:
            self._init_driver()
            self.search(query)
            self.scroll_results(max_results)
            self.extract_businesses(max_results)

            # Export
            output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
            os.makedirs(output_dir, exist_ok=True)

            if output_format == "csv":
                path = os.path.join(output_dir, f"{safe_query}_{timestamp}.csv")
                self.export_csv(path)
            elif output_format == "json":
                path = os.path.join(output_dir, f"{safe_query}_{timestamp}.json")
                self.export_json(path)
            elif output_format == "excel":
                path = os.path.join(output_dir, f"{safe_query}_{timestamp}.xlsx")
                self.export_excel(path)
            else:
                logger.error("Unknown format: %s. Use 'csv', 'json', or 'excel'.", output_format)

            return self.businesses

        except Exception as e:
            logger.error("Scraping failed: %s", str(e))
            raise

        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")

    def close(self):
        """Clean up: close the browser."""
        if self.driver:
            self.driver.quit()


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Google Maps Business Scraper — Extract business data from Google Maps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/scraper.py --query "restaurants in Lyon" --max_results 100
  python src/scraper.py --query "dentists in Paris" --max_results 50 --output json
  python src/scraper.py --query "hotels in Annecy" -m 200 -o excel --browser firefox
  python src/scraper.py --query "cafes in Nice" -m 30 --visible --browser firefox
        """,
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        required=True,
        help="Search query (e.g., 'restaurants in Paris')",
    )
    parser.add_argument(
        "--max_results", "-m",
        type=int,
        default=100,
        help="Maximum number of results to scrape (default: 100)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Run browser in visible mode (not headless)",
    )
    parser.add_argument(
        "--browser", "-b",
        type=str,
        choices=["chrome", "firefox"],
        default="chrome",
        help="Browser to use: 'chrome' or 'firefox' (default: chrome)",
    )

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════╗
║     Google Maps Business Scraper v1.0        ║
║     by Mohamed KACIMI                        ║
╚══════════════════════════════════════════════╝

  Query:       {args.query}
  Max Results: {args.max_results}
  Format:      {args.output}
  Browser:     {args.browser.capitalize()}
  Mode:        {"Visible" if args.visible else "Headless"}
""")

    scraper = GoogleMapsScraper(headless=not args.visible, browser=args.browser)
    results = scraper.scrape(
        query=args.query,
        max_results=args.max_results,
        output_format=args.output,
    )

    print(f"\n✅ Done! Scraped {len(results)} businesses.")
    print(f"📁 Output saved to: ./output/")


if __name__ == "__main__":
    main()