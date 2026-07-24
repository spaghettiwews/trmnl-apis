import json
import logging
import os
import random
from collections import defaultdict

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

base_dir = os.path.dirname(__file__)
json_path = os.path.join(base_dir, "german.json")
level = "a2"

# load_dotenv()

deutsch_bp = Blueprint("deutsch", __name__, url_prefix="/")


def load_words_by_cefr(json_path):
    """Load JSON once and index by CEFR level."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    words_by_level = defaultdict(list)

    for entry in data:
        level = entry.get("cefr_level")
        if level:
            words_by_level[level].append(entry)

    return words_by_level


words_by_level = load_words_by_cefr(json_path)


@deutsch_bp.route("/api/words")
def get_random_word():
    """Return a random word for a given CEFR level."""
    words = words_by_level.get(level.upper())

    if not words:
        return None

    return random.choice(words)
