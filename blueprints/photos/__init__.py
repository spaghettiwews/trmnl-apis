import logging
import os
import random

from flask import Blueprint, jsonify

import helpers
from helpers import ttl_cache

logger = logging.getLogger(__name__)

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
    try:
        photos = get_photos()
        if not photos:
            return jsonify({"error": "No photos found."}), 404
        return jsonify(random.choice(photos)), 200
    except helpers.ApiCallError as e:
        return jsonify({"error": str(e)}), e.status_code


@ttl_cache(seconds=3600)
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
        return results

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
