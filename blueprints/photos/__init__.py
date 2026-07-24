import logging
import os
import random

from dotenv import load_dotenv
from flask import Blueprint, jsonify

import helpers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

BASE_API_URL = os.getenv("BASE_PHOTOS_API_URL")
API_KEY = os.getenv("API_KEY")
ALBUM_ID = os.getenv("ALBUM_ID")
TIMEOUT = int(os.getenv("TIMEOUT", "60"))

photos_bp = Blueprint("photos", __name__, url_prefix="/")

headers = {"x-api-key": API_KEY}


@photos_bp.route("/api/photos")
def get_random_photo():
    """
    Calls get_photos and filters the response to one result
    """
    return jsonify(random.choice(get_photos())), 200


def get_photos():
    """
    Fetches a list of photo assets from the configured album ID.
    Includes robust error handling and detailed logging.
    """
    logger.info(f"Attempting to fetch photos for Album ID: {ALBUM_ID}")
    results = []
    album_url = f"{BASE_API_URL}/api/albums/{ALBUM_ID}"

    response = helpers.call_api(album_url, headers, TIMEOUT, logger)
    data = response.json()
    assets = data.get("assets", [])

    if not assets:
        logger.warning("The API response contained no assets.")
        return jsonify(results), 200

    logger.info(f"Found {len(assets)} assets to process.")

    for i, asset in enumerate(assets):
        try:
            exifInfo = asset.get("exifInfo", {})
            asset_id = asset.get("id")
            friendly_date = helpers.format_date(
                asset.get("exifInfo", {}).get("dateTimeOriginal"), "date"
            )
            relative_age = helpers.format_date(
                asset.get("exifInfo", {}).get("dateTimeOriginal"), "relative"
            )

            if asset_id:
                image_url = (
                    f"{BASE_API_URL}/api/assets/{asset_id}/original?apiKey={API_KEY}"
                )

                results.append(
                    {
                        "exifInfo": exifInfo,
                        "imageUrl": image_url,
                        "friendlyDate": friendly_date,
                        "relativeAge": relative_age,
                    }
                )
            else:
                logger.warning(f"Skipping asset {i} due to missing required ID field.")

        except Exception as e:
            # Handle unexpected errors during processing of a single asset
            logger.error(f"Failed to process asset at index {i}. Error: {e}")
            continue  # Skip this asset and continue the loop

    logger.info(f"Successfully processed and found {len(results)} photo records.")
    return results
