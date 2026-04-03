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
from PIL import Image as PILImage
from openai import OpenAI, BadRequestError

from config.settings import OPENAI_API_KEY, GENERATED_IMAGES_DIR, get_supabase, DATA_DIR
from config.brand_voice import DALLE_STYLE_ANCHOR

LOGO_PATH = DATA_DIR / "oec-logo.png"

logger = logging.getLogger(__name__)


def _apply_logo_watermark(filepath: Path) -> None:
    """Overlay the OEC logo on the bottom-right corner of the image."""
    if not LOGO_PATH.exists():
        logger.warning("Logo file not found at %s — skipping watermark", LOGO_PATH)
        return

    try:
        base = PILImage.open(filepath).convert("RGBA")
        logo = PILImage.open(LOGO_PATH).convert("RGBA")

        # Resize logo to ~12% of the image width
        logo_size = int(base.width * 0.12)
        logo = logo.resize((logo_size, logo_size), PILImage.LANCZOS)

        # Position: bottom-right with padding
        padding = int(base.width * 0.02)
        x = base.width - logo_size - padding
        y = base.height - logo_size - padding

        # Paste with transparency
        base.paste(logo, (x, y), logo)

        # Save back as RGB (PNG)
        base.convert("RGB").save(filepath, "PNG")
        logger.info("Logo watermark applied to %s", filepath.name)
    except Exception as e:
        logger.warning("Failed to apply logo watermark: %s", e)


def _upload_to_supabase(filepath: Path, filename: str) -> Optional[str]:
    """Upload image to Supabase Storage and return the public URL."""
    try:
        sb = get_supabase()
        with open(filepath, "rb") as f:
            sb.storage.from_("twitter-images").upload(
                filename, f.read(), {"content-type": "image/png"}
            )
        public_url = sb.storage.from_("twitter-images").get_public_url(filename)
        logger.info("Image uploaded to Supabase Storage: %s", filename)
        return public_url
    except Exception as e:
        logger.warning("Failed to upload image to Supabase Storage: %s", e)
        return None


def generate_image(
    image_prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
) -> tuple[Optional[Path], Optional[str]]:
    """
    Generate an image with DALL-E 3 and save it locally.

    The brand style anchor is prepended automatically to every prompt.

    Args:
        image_prompt: The descriptive prompt from content_generator.
        size: Image dimensions ("1024x1024", "1792x1024", "1024x1792").
        quality: "standard" (~$0.040) or "hd" (~$0.080).

    Returns:
        Tuple of (local_path, public_url) or (None, None) on failure.
    """
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set — cannot generate image")
        return None, None

    if not image_prompt:
        logger.warning("Empty image_prompt — skipping DALL-E generation")
        return None, None

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

        # Apply OEC logo watermark
        _apply_logo_watermark(filepath)

        # Upload to Supabase Storage
        public_url = _upload_to_supabase(filepath, filename)

        return filepath, public_url

    except BadRequestError as e:
        # Content policy violation — DALL-E refused the prompt
        logger.warning(
            "DALL-E content policy block — image skipped. Reason: %s",
            str(e),
        )
        return None, None
    except requests.RequestException as e:
        logger.error("Failed to download generated image: %s", e)
        return None, None
    except Exception as e:
        logger.error("DALL-E generation failed: %s", e)
        return None, None
