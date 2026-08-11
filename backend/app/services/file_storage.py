import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1MB per chunk
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"


class FileStorage:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or UPLOAD_DIR
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "chunks").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "files").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "images").mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, file_id: str, extension: str = "") -> Path:
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        file_dir = self.base_dir / "files" / date_prefix
        file_dir.mkdir(parents=True, exist_ok=True)
        return file_dir / f"{file_id}{extension}"
    
    def _get_chunk_dir(self, file_id: str) -> Path:
        chunk_dir = self.base_dir / "chunks" / file_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        return chunk_dir
    
    def save_file(self, file_id: str, content: bytes, extension: str = "") -> Tuple[str, bool]:
        is_chunked = len(content) > CHUNK_SIZE * 10
        
        if is_chunked:
            return self._save_chunked(file_id, content, extension), True
        else:
            return self._save_single(file_id, content, extension), False
    
    def _save_single(self, file_id: str, content: bytes, extension: str) -> str:
        file_path = self._get_file_path(file_id, extension)
        file_path.write_bytes(content)
        logger.info(f"File saved: {file_path} ({len(content)} bytes)")
        return str(file_path.relative_to(self.base_dir))
    
    def _save_chunked(self, file_id: str, content: bytes, extension: str) -> str:
        chunk_dir = self._get_chunk_dir(file_id)
        chunk_count = 0
        md5_hash = hashlib.md5()
        
        for i in range(0, len(content), CHUNK_SIZE):
            chunk = content[i:i + CHUNK_SIZE]
            chunk_path = chunk_dir / f"chunk_{chunk_count:04d}"
            chunk_path.write_bytes(chunk)
            md5_hash.update(chunk)
            chunk_count += 1
        
        manifest = {
            "file_id": file_id,
            "total_size": len(content),
            "chunk_size": CHUNK_SIZE,
            "chunk_count": chunk_count,
            "md5": md5_hash.hexdigest(),
            "extension": extension
        }
        
        manifest_path = chunk_dir / "manifest.txt"
        with open(manifest_path, "w") as f:
            for key, value in manifest.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"File saved in chunks: {chunk_count} chunks, {len(content)} bytes")
        return str(chunk_dir.relative_to(self.base_dir))
    
    def read_file(self, relative_path: str) -> bytes:
        file_path = self.base_dir / relative_path
        
        if file_path.is_file():
            return file_path.read_bytes()
        
        if file_path.is_dir():
            return self._read_chunked(file_path)
        
        raise FileNotFoundError(f"File not found: {file_path}")
    
    def _read_chunked(self, chunk_dir: Path) -> bytes:
        manifest_path = chunk_dir / "manifest.txt"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {chunk_dir}")
        
        manifest = {}
        with open(manifest_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    manifest[key] = value
        
        chunk_count = int(manifest["chunk_count"])
        chunks = []
        
        for i in range(chunk_count):
            chunk_path = chunk_dir / f"chunk_{i:04d}"
            if not chunk_path.exists():
                raise FileNotFoundError(f"Chunk not found: {chunk_path}")
            chunks.append(chunk_path.read_bytes())
        
        content = b"".join(chunks)
        
        md5_hash = hashlib.md5(content).hexdigest()
        if md5_hash != manifest["md5"]:
            raise ValueError(f"MD5 mismatch: expected {manifest['md5']}, got {md5_hash}")
        
        return content
    
    def delete_file(self, relative_path: str) -> bool:
        file_path = self.base_dir / relative_path
        
        if file_path.is_file():
            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True
        
        if file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
            logger.info(f"Chunked file deleted: {file_path}")
            return True
        
        return False
    
    def file_exists(self, relative_path: str) -> bool:
        file_path = self.base_dir / relative_path
        return file_path.exists()
    
    def get_file_size(self, relative_path: str) -> int:
        file_path = self.base_dir / relative_path
        
        if file_path.is_file():
            return file_path.stat().st_size
        
        if file_path.is_dir():
            manifest_path = file_path / "manifest.txt"
            if manifest_path.exists():
                with open(manifest_path, "r") as f:
                    for line in f:
                        if line.startswith("total_size="):
                            return int(line.strip().split("=")[1])
        
        return 0
    
    def save_image(self, image_id: str, content: bytes, image_format: str) -> str:
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        image_dir = self.base_dir / "images" / date_prefix
        image_dir.mkdir(parents=True, exist_ok=True)
        
        extension = f".{image_format.lower()}"
        image_path = image_dir / f"{image_id}{extension}"
        image_path.write_bytes(content)
        logger.info(f"Image saved: {image_path} ({len(content)} bytes)")
        
        return str(image_path.relative_to(self.base_dir))
    
    def read_image(self, relative_path: str) -> bytes:
        image_path = self.base_dir / relative_path
        
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        return image_path.read_bytes()
    
    def delete_image(self, relative_path: str) -> bool:
        image_path = self.base_dir / relative_path
        
        if image_path.is_file():
            image_path.unlink()
            logger.info(f"Image deleted: {image_path}")
            return True
        
        return False
    
    def get_file_content_chunks(self, relative_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        file_path = self.base_dir / relative_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        from app.services.text_extractor import TextExtractor
        
        file_data = file_path.read_bytes()
        extension = file_path.suffix.lstrip(".").lower()
        
        extractor = TextExtractor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        text = extractor.extract_text(file_data, extension)
        
        if not text:
            return []
        
        chunks = extractor.split_text_into_chunks(text)
        return [chunk_text for chunk_text, _ in chunks]


file_storage = FileStorage()
