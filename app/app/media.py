"""
Shunya — Media Gallery (Phase 2)

Per-lead media storage and sharing. Supports images, videos, documents.
Team can upload, view, share media directly from the dashboard.
Every file is linked to a lead for context.
"""

import os
import uuid
import mimetypes
from datetime import datetime
from flask import url_for

from app import db
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index


ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain", "text/csv",
}

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")


class MediaFile(db.Model):
    __tablename__ = "media_files"
    __table_args__ = (Index("ix_media_lead", "lead_id"),)

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_type = Column(String(60))  # image, video, document, audio
    mime_type = Column(String(120))
    file_size = Column(Integer, default=0)
    uploaded_by = Column(String(120), default="")
    caption = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "uploaded_by": self.uploaded_by,
            "caption": self.caption,
            "created_at": self.created_at.isoformat(),
            "url": f"/media/{self.storage_path}" if self.storage_path else None,
        }


class MediaGallery:
    """Manages media uploads, storage, and retrieval per lead."""

    def __init__(self, session=None):
        self._session = session or db.session
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def upload(self, file_data: bytes, filename: str, lead_id: int = None,
               uploaded_by: str = "", caption: str = "") -> MediaFile:
        """Store a file and create a MediaFile record."""
        ext = os.path.splitext(filename)[1] or ".bin"
        stored_name = f"{uuid.uuid4().hex}{ext}"
        subdir = datetime.utcnow().strftime("%Y/%m")
        dest_dir = os.path.join(UPLOAD_DIR, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, stored_name)

        with open(dest_path, "wb") as f:
            f.write(file_data)

        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type.startswith("image/"):
            file_type = "image"
        elif mime_type and mime_type.startswith("video/"):
            file_type = "video"
        elif mime_type == "application/pdf":
            file_type = "document"
        else:
            file_type = "other"

        storage_rel = os.path.join(subdir, stored_name)
        media = MediaFile(
            lead_id=lead_id,
            filename=filename,
            storage_path=storage_rel,
            file_type=file_type,
            mime_type=mime_type or "application/octet-stream",
            file_size=len(file_data),
            uploaded_by=uploaded_by,
            caption=caption,
        )
        self._session.add(media)
        self._session.commit()
        return media

    def get_by_lead(self, lead_id: int, file_type: str = "") -> list[dict]:
        """Get all media for a lead."""
        query = self._session.query(MediaFile).filter(MediaFile.lead_id == lead_id)
        if file_type:
            query = query.filter(MediaFile.file_type == file_type)
        files = query.order_by(MediaFile.created_at.desc()).all()
        return [f.to_dict() for f in files]

    def delete(self, media_id: int) -> bool:
        """Delete a media file and its record."""
        media = self._session.get(MediaFile, media_id)
        if not media:
            return False
        path = os.path.join(UPLOAD_DIR, media.storage_path)
        if os.path.exists(path):
            os.remove(path)
        self._session.delete(media)
        self._session.commit()
        return True

    def stats(self) -> dict:
        total = self._session.query(db.func.count(MediaFile.id)).scalar() or 0
        by_type = self._session.query(MediaFile.file_type, db.func.count(MediaFile.id)).group_by(MediaFile.file_type).all()
        return {"total_files": total, "by_type": dict(by_type), "storage": UPLOAD_DIR}