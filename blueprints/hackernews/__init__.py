import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, jsonify

import helpers
from helpers import ttl_cache

logger = logging.getLogger(__name__)

hackernews_bp = Blueprint("hackernews", __name__, url_prefix="/")

TIMEOUT = int(os.getenv("TIMEOUT", "60"))


@ttl_cache(seconds=600)
def fetch_headlines() -> list:
    """
    Fetches top story ids and headlines from HN.
    """
    logger.info("Attempting to fetch HN stories")

    ids = helpers.call_api(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        "",
        TIMEOUT,
        logger,
    ).json()

    def fetch_item(id):
        return helpers.call_api(
            f"https://hacker-news.firebaseio.com/v0/item/{id}.json",
            "",
            TIMEOUT,
            logger,
        ).json()

    top_ids = ids[:10]
    headlines = [None] * len(top_ids)

    with ThreadPoolExecutor(max_workers=len(top_ids)) as executor:
        futures = {executor.submit(fetch_item, id): i for i, id in enumerate(top_ids)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                headlines[idx] = future.result()
            except Exception as e:
                logger.warning(f"Skipping story {top_ids[idx]}: {e}")

    return [h for h in headlines if h is not None]


@hackernews_bp.route("/api/headlines")
def get_headlines():
    try:
        return jsonify(fetch_headlines()), 200
    except helpers.ApiCallError as e:
        return jsonify({"error": str(e)}), e.status_code
