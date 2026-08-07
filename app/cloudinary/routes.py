"""Cloudinary Integration — File uploads auto-optimized through CDN.

POST /api/v1/cloudinary/upload  — Upload a file to Cloudinary, return URL
GET  /api/v1/cloudinary/status  — Check if Cloudinary is configured
"""
import os
import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

cloudinary_bp = Blueprint("cloudinary", __name__, url_prefix="/api/v1/cloudinary")


def _is_configured() -> bool:
    """Return True when all three Cloudinary env vars are set."""
    return all([
        os.getenv("CLOUDINARY_CLOUD_NAME"),
        os.getenv("CLOUDINARY_API_KEY"),
        os.getenv("CLOUDINARY_API_SECRET"),
    ])


@cloudinary_bp.route("/status", methods=["GET"])
def status():
    """Return whether Cloudinary credentials are configured."""
    return jsonify({
        "configured": _is_configured(),
    })


@cloudinary_bp.route("/upload", methods=["POST"])
def upload():
    """Accept a multipart file, upload to Cloudinary, return the URL."""
    if not _is_configured():
        return jsonify({
            "url": None,
            "public_id": None,
            "secure_url": None,
            "error": "Cloudinary not configured. Set CLOUDINARY_CLOUD_NAME, "
                     "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in .env",
        }), 400

    if "file" not in request.files:
        return jsonify({
            "url": None,
            "public_id": None,
            "secure_url": None,
            "error": "No file provided",
        }), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({
            "url": None,
            "public_id": None,
            "secure_url": None,
            "error": "Empty filename",
        }), 400

    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )

        result = cloudinary.uploader.upload(file)
        return jsonify({
            "url": result.get("url"),
            "public_id": result.get("public_id"),
            "secure_url": result.get("secure_url"),
        })

    except Exception as e:
        logger.exception("Cloudinary upload failed")
        return jsonify({
            "url": None,
            "public_id": None,
            "secure_url": None,
            "error": str(e),
        }), 500