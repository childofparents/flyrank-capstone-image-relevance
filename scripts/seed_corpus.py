import os
import requests
from dotenv import load_dotenv

# Load environment variables safely
load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

if not PEXELS_API_KEY:
    raise ValueError("PEXELS_API_KEY is missing from your .env file.")

# The categories designed to test the mismatch guard's semantic matching capability
CATEGORIES = [
    "red fox",
    "wolf",
    "dog",
    "bear",
    "deer"
]

IMAGES_PER_CATEGORY = 10
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
HEADERS = {"Authorization": PEXELS_API_KEY}
OUTPUT_DIR = "images"


def setup_directories():
    """Ensure the target output directories exist."""
    for category in CATEGORIES:
        category_path = os.path.join(OUTPUT_DIR, category.replace(" ", "_"))
        os.makedirs(category_path, exist_ok=True)


def download_image(url, save_path):
    """Download an individual image from a URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")


def seed_corpus():
    """Query the Pexels API and download the image dataset."""
    setup_directories()

    for category in CATEGORIES:
        print(f"Fetching images for category: {category}...")

        params = {
            "query": category,
            "per_page": IMAGES_PER_CATEGORY,
            "orientation": "landscape"  # Standardizing orientation helps visual consistency
        }

        try:
            response = requests.get(PEXELS_SEARCH_URL, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()

            photos = data.get("photos", [])
            for index, photo in enumerate(photos):
                # We'll use the medium size to save on your local storage space
                image_url = photo["src"]["medium"]
                safe_category = category.replace(" ", "_")
                filename = f"{safe_category}_{index + 1}.jpg"
                save_path = os.path.join(OUTPUT_DIR, safe_category, filename)

                download_image(image_url, save_path)
                print(f"  -> Saved {filename}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch metadata for {category}: {e}")


if __name__ == "__main__":
    print("Starting dataset generation...")
    seed_corpus()
    print("Corpus seeding complete! ~50 images downloaded successfully.")