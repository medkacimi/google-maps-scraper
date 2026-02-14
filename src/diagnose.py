"""
Google Maps Diagnostic Tool
============================
Opens Firefox, navigates to Google Maps, and takes screenshots
at each stage to debug consent/loading issues.

Usage:
    python src/diagnose.py
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def diagnose():
    print("=" * 55)
    print("  Google Maps Diagnostic — Firefox")
    print("=" * 55)

    # ── Launch Firefox (visible) ──
    options = FirefoxOptions()
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    options.set_preference("intl.accept_languages", "en-US, en")

    print("\n[1/5] Launching Firefox...")
    driver = webdriver.Firefox(options=options)

    try:
        # ── Navigate to Google Maps ──
        print("[2/5] Navigating to Google Maps...")
        driver.get("https://www.google.com/maps")
        time.sleep(5)

        # ── Screenshot 1: Initial page load ──
        path1 = os.path.join(OUTPUT_DIR, "diag_1_initial_load.png")
        driver.save_screenshot(path1)
        print(f"[3/5] Screenshot saved: {path1}")
        print(f"       Page title: {driver.title}")
        print(f"       Current URL: {driver.current_url}")

        # ── Check what's on the page ──
        print("\n[4/5] Analyzing page content...")

        # Check for iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"       Iframes found: {len(iframes)}")
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src") or "(no src)"
            print(f"         iframe[{i}]: {src[:100]}")

        # Check for buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"       Buttons found: {len(buttons)}")
        for btn in buttons:
            try:
                text = btn.text.strip()
                if text:
                    aria = btn.get_attribute("aria-label") or ""
                    print(f"         Button: '{text}' (aria-label='{aria}')")
            except Exception:
                pass

        # Check for search box
        searchbox = driver.find_elements(By.ID, "searchboxinput")
        print(f"       Search box found: {'YES' if searchbox else 'NO'}")

        # ── Try switching into consent iframe ──
        consent_iframe = None
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "consent" in src.lower():
                consent_iframe = iframe
                break

        if consent_iframe:
            print("\n       >> Consent iframe detected! Switching into it...")
            driver.switch_to.frame(consent_iframe)
            time.sleep(2)

            # Screenshot inside iframe
            path_iframe = os.path.join(OUTPUT_DIR, "diag_2_consent_iframe.png")
            driver.save_screenshot(path_iframe)
            print(f"       Screenshot saved: {path_iframe}")

            # Check buttons inside iframe
            iframe_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"       Buttons inside iframe: {len(iframe_buttons)}")
            for btn in iframe_buttons:
                try:
                    text = btn.text.strip()
                    if text:
                        print(f"         Button: '{text}'")
                except Exception:
                    pass

            driver.switch_to.default_content()
        else:
            print("       >> No consent iframe found")

        # ── Wait a bit more and take final screenshot ──
        time.sleep(3)
        path2 = os.path.join(OUTPUT_DIR, "diag_3_after_wait.png")
        driver.save_screenshot(path2)
        print(f"\n[5/5] Final screenshot saved: {path2}")

        print("\n" + "=" * 55)
        print("  DIAGNOSTIC COMPLETE")
        print("=" * 55)
        print(f"\n  Screenshots saved in: {os.path.abspath(OUTPUT_DIR)}")
        print(f"  Open the folder:  explorer output")
        print(f"\n  Upload the screenshots here so I can see")
        print(f"  exactly what's blocking the scraper.")
        print("=" * 55)

    except Exception as e:
        print(f"\n  ERROR: {e}")
        try:
            err_path = os.path.join(OUTPUT_DIR, "diag_error.png")
            driver.save_screenshot(err_path)
            print(f"  Error screenshot saved: {err_path}")
        except Exception:
            pass

    finally:
        input("\n  Press ENTER to close Firefox...")
        driver.quit()
        print("  Firefox closed.")


if __name__ == "__main__":
    diagnose()