"""File Upload Storage Provider — Free-first file storage abstraction with compression.

Chain: Local filesystem → MinIO (S3-compatible)
Compression: gzip for text, lossless PNG optimize for images.
"""
from abc import ABC, abstractmethod
from typing import Optional
import os, uuid, gzip, io, logging
from datetime import datetime, timezone

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "uploads")

TEXT_EXTS = {'txt', 'csv', 'json', 'xml', 'html', 'htm', 'css', 'js', 'md', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'log', 'svg'}


class StorageProvider(ABC):
    """Abstract base for file storage."""

    name: str = "base"

    @abstractmethod
    def save(self, file_bytes: bytes, filename: str, content_type: str) -> dict:
        """Save file and return metadata dict with at least: url, path, filename."""
        ...

    @abstractmethod
    def get(self, path: str) -> Optional[bytes]:
        ...

    @abstractmethod
    def delete(self, path: str) -> bool:
        ...


class LocalStorageProvider(StorageProvider):
    """Free — saves to local filesystem under static/uploads/ with compression."""

    name = "local"

    def __init__(self, base_dir: str = UPLOAD_DIR):
        os.makedirs(base_dir, exist_ok=True)
        self.base_dir = base_dir

    def _compress(self, data: bytes, filename: str, content_type: str) -> tuple[bytes, str, dict]:
        """Compress in-place. Returns (compressed_bytes, stored_ext, meta)."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        original = len(data)
        meta = {"original_size": original, "compression": "none", "compressed_size": original}

        # Gzip text
        if ext in TEXT_EXTS or (content_type or "").startswith("text/"):
            compressed = gzip.compress(data, compresslevel=6)
            if len(compressed) < original:
                meta["compression"] = "gzip"
                meta["compressed_size"] = len(compressed)
                return compressed, ext + ".gz", meta
            return data, ext, meta

        # Lossless PNG
        if ext == "png" and HAS_PIL:
            try:
                img = Image.open(io.BytesIO(data))
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                compressed = buf.getvalue()
                if len(compressed) < original:
                    meta["compression"] = "png_optimize"
                    meta["compressed_size"] = len(compressed)
                    return compressed, ext, meta
            except Exception:
                pass

        return data, ext, meta

    def save(self, file_bytes: bytes, filename: str, content_type: str) -> dict:
        compressed_bytes, stored_ext, compress_meta = self._compress(file_bytes, filename, content_type)

        stored_name = f"{uuid.uuid4().hex}.{stored_ext}"
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        rel_dir = os.path.join(date_prefix)
        abs_dir = os.path.join(self.base_dir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        abs_path = os.path.join(abs_dir, stored_name)
        with open(abs_path, "wb") as f:
            f.write(compressed_bytes)

        rel_path = f"uploads/{rel_dir}/{stored_name}"
        return {
            "url": f"/static/{rel_path}",
            "path": rel_path,
            "filename": filename,
            "content_type": content_type,
            "size": len(compressed_bytes),
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "compression": compress_meta,
        }

    def get(self, path: str) -> Optional[bytes]:
        abs_path = os.path.join(self.base_dir, path)
        if not os.path.exists(abs_path):
            return None
        with open(abs_path, "rb") as f:
            data = f.read()
        # Auto-decompress gzip
        if path.endswith(".gz"):
            try:
                return gzip.decompress(data)
            except Exception:
                pass
        return data

    def delete(self, path: str) -> bool:
        abs_path = os.path.join(self.base_dir, path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
            return True
        return False


def resolve_storage_provider() -> StorageProvider:
    """Resolve best available storage provider. Free-first."""
    return LocalStorageProvider()