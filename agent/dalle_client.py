"""
Oeconomia Twitter Agent — DALL-E 3 Client
Generates images via OpenAI API with Oeconomia brand styling.
Handles content policy blocks gracefully. Saves to data/generated_images/.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from openai import OpenAI, BadRequestError

from config.settings import OPENAI_API_KEY, GENERATED_IMAGES_DIR
from config.brand_voice import DALLE_STYLE_ANCHOR

logger = logging.getLogger(__name__)


def generate_image(
    image_prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
) -> Optional[Path]:
    """
    Generate an image with DALL-E 3 and save it locally.

    The brand style anchor is prepended automatically to every prompt.

    Args:
        image_prompt: The descriptive prompt from content_generator.
        size: Image dimensions ("1024x1024", "1792x1024", "1024x1792").
        quality: "standard" (~$0.040) or "hd" (~$0.080).

    Returns:
        Path to the saved image file, or None on failure.
    """
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set — cannot generate image")
        return None

    if not image_prompt:
        logger.warning("Empty image_prompt — skipping DALL-E generation")
        return None

    # Prepend brand style anchor
    full_prompt = f"{DALLE_STYLE_ANCHOR} {image_prompt}"
    logger.info("DALL-E prompt: %s", full_prompt[:120])

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_url = response.data[0].url
        if not image_url:
            logger.error("DALL-E returned empty URL")
            return None

        # Download the image
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()

        # Save with timestamp + UUID for uniqueness
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"oec_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        filepath = GENERATED_IMAGES_DIR / filename

        with open(filepath, "wb") as f:
            f.write(img_response.content)

        logger.info("Image saved: %s (%d bytes)", filepath, len(img_response.content))
        return filepath

    except BadRequestError as e:
        # Content policy violation — DALL-E refused the prompt
        logger.warning(
            "DALL-E content policy block — image skipped. Reason: %s",
            str(e),
        )
        return None
    except requests.RequestException as e:
        logger.error("Failed to download generated image: %s", e)
        return None
    except Exception as e:
        logger.error("DALL-E generation failed: %s", e)
        return None
