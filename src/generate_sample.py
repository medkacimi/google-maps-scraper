"""
Sample Data Generator
=====================
Generates realistic sample output data for the Google Maps Business Scraper.
Use this to create portfolio-ready sample datasets and screenshots.

Usage:
    python src/generate_sample.py
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta


# ──────────────────────────────────────────────
# Realistic Sample Data
# ──────────────────────────────────────────────

RESTAURANT_NAMES = [
    "Le Petit Bistrot", "Brasserie du Lac", "La Table d'Annecy",
    "Chez Marcel", "L'Auberge du Lyonnais", "Le Clos des Sens",
    "Restaurant Le Bilboquet", "Café Brunet", "L'Esquisse",
    "Le Belvédère", "La Ciboulette", "Les Trésoms",
    "L'Imperial Palace", "Le Denti", "La Rotonde du Lac",
    "Chez Mémère", "Le Moulin de la Galette", "Au Fidèle Berger",
    "La Maison de Marc Veyrat", "Le Chalet du Lac",
    "Pizzeria Toscana", "Sushi Yama", "Thai Garden",
    "La Crêperie Bretonne", "Le Comptoir Italien",
    "Burger Factory", "L'Atelier Gourmand", "Le Jardin Secret",
    "La Terrasse", "Café de la Place", "Le Bistrot du Port",
    "La Brasserie des Européens", "L'Etage", "Le Freti",
    "L'Instant Présent", "Les Chineurs", "Dino's Pizza",
    "Le Garage", "Ô Savoyard", "La Mangue Verte",
    "Le Refuge des Gourmets", "Nature & Saveur", "L'Alchimiste",
    "Sol Semilla", "Le Chalet des Iles", "Altitude 1000",
    "Au Bord du Thiou", "Le Pâquier Gourmand", "Villa Toscane",
    "Le Semnoz", "Le Café du Théâtre", "La Cuisine des Amis",
]

STREETS = [
    "Rue Royale", "Quai Eustache Chappuis", "Rue Sainte-Claire",
    "Place Notre-Dame", "Rue du Pâquier", "Avenue d'Albigny",
    "Rue Sommeiller", "Boulevard du Lac", "Rue Carnot",
    "Avenue de Genève", "Rue Jean-Jacques Rousseau", "Passage de l'Île",
    "Rue de la Gare", "Place aux Bois", "Chemin du Belvédère",
    "Rue de la République", "Quai des Cordeliers", "Avenue de Brogny",
    "Rue du Lac", "Impasse des Jardins", "Avenue de France",
    "Place de l'Hôtel de Ville", "Rue Filaterie", "Rue Perrière",
]

CATEGORIES = [
    "French restaurant", "Italian restaurant", "Japanese restaurant",
    "Thai restaurant", "Pizzeria", "Crêperie", "Brasserie",
    "Café", "Bistrot", "Fine dining restaurant", "Burger restaurant",
    "Vegetarian restaurant", "Gastropub", "Seafood restaurant",
    "Mediterranean restaurant", "Savoyard restaurant",
]

HOURS_TEMPLATES = [
    "Mon-Fri: 11:30-14:00, 19:00-22:00 | Sat-Sun: 12:00-22:30",
    "Tue-Sun: 12:00-14:30, 19:00-22:30 | Mon: Closed",
    "Daily: 11:00-23:00",
    "Mon-Sat: 12:00-14:00, 19:00-23:00 | Sun: Closed",
    "Wed-Sun: 12:00-14:30, 19:00-22:00 | Mon-Tue: Closed",
    "Mon-Sun: 10:00-22:00",
    "Tue-Sat: 12:00-14:00, 19:00-22:00 | Sun: 12:00-15:00 | Mon: Closed",
    "Thu-Mon: 12:00-14:00, 19:00-22:30 | Tue-Wed: Closed",
]

PHONE_PREFIXES = ["+33 4 50", "+33 4 56", "+33 6 12", "+33 6 45", "+33 7 82"]

WEBSITES_DOMAINS = [
    "restaurant-annecy.fr", "bistrot-annecy.com", "restaurant-lac.fr",
    "savoie-restaurant.com", "annecy-gourmet.fr", "tables-annecy.com",
]

# Annecy area coordinates
ANNECY_LAT = 45.899
ANNECY_LNG = 6.129


def generate_phone():
    prefix = random.choice(PHONE_PREFIXES)
    suffix = f"{random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"
    return f"{prefix} {suffix}"


def generate_website(name):
    slug = name.lower().replace(" ", "-").replace("'", "").replace("é", "e")
    slug = slug.replace("è", "e").replace("ê", "e").replace("ô", "o")
    domain = random.choice(WEBSITES_DOMAINS)
    return f"https://www.{slug}.fr" if random.random() > 0.3 else ""


def generate_business(index):
    name = RESTAURANT_NAMES[index % len(RESTAURANT_NAMES)]
    street_num = random.randint(1, 120)
    street = random.choice(STREETS)
    rating = round(random.uniform(3.2, 5.0), 1)
    review_count = random.randint(15, 2800)

    # Higher-rated restaurants tend to have more reviews
    if rating >= 4.5:
        review_count = random.randint(200, 2800)
    elif rating >= 4.0:
        review_count = random.randint(80, 1500)

    # Random offset around Annecy center
    lat = ANNECY_LAT + random.uniform(-0.03, 0.03)
    lng = ANNECY_LNG + random.uniform(-0.03, 0.03)

    scraped_time = datetime.now() - timedelta(minutes=random.randint(0, 120))

    return {
        "name": name,
        "address": f"{street_num} {street}, 74000 Annecy, France",
        "phone": generate_phone() if random.random() > 0.1 else "",
        "website": generate_website(name),
        "rating": rating,
        "review_count": review_count,
        "category": random.choice(CATEGORIES),
        "opening_hours": random.choice(HOURS_TEMPLATES) if random.random() > 0.15 else "",
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "google_maps_url": f"https://www.google.com/maps/place/{name.replace(' ', '+')}/@{lat:.6f},{lng:.6f},17z",
        "scraped_at": scraped_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def generate_dataset(n: int = 50):
    """Generate n sample business records."""
    return [generate_business(i) for i in range(n)]


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # Generate 50 sample businesses
    data = generate_dataset(50)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── CSV ──
    csv_path = os.path.join(output_dir, f"restaurants_in_Annecy_{timestamp}.csv")
    fieldnames = list(data[0].keys())

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ CSV exported: {csv_path}")

    # ── JSON ──
    json_path = os.path.join(output_dir, f"restaurants_in_Annecy_{timestamp}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {
                    "query": "restaurants in Annecy",
                    "total_results": len(data),
                    "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "scraper_version": "1.0",
                },
                "businesses": data,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"✅ JSON exported: {json_path}")

    # ── Excel (if pandas available) ──
    try:
        import pandas as pd

        xlsx_path = os.path.join(output_dir, f"restaurants_in_Annecy_{timestamp}.xlsx")
        df = pd.DataFrame(data)
        df.columns = [col.replace("_", " ").title() for col in df.columns]
        df.to_excel(xlsx_path, index=False, sheet_name="Google Maps Data")
        print(f"✅ Excel exported: {xlsx_path}")
    except ImportError:
        print("⚠️  pandas/openpyxl not installed — skipping Excel export")

    # ── Summary Stats ──
    ratings = [d["rating"] for d in data]
    reviews = [d["review_count"] for d in data]
    with_phone = sum(1 for d in data if d["phone"])
    with_website = sum(1 for d in data if d["website"])

    print(f"""
╔══════════════════════════════════════════════╗
║         Sample Data Summary                  ║
╠══════════════════════════════════════════════╣
║  Total businesses:   {len(data):>4}                    ║
║  Avg rating:         {sum(ratings)/len(ratings):>4.1f}                    ║
║  Total reviews:      {sum(reviews):>6,}                ║
║  With phone:         {with_phone:>4} ({with_phone/len(data)*100:.0f}%)                ║
║  With website:       {with_website:>4} ({with_website/len(data)*100:.0f}%)                ║
╚══════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
