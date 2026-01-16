import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional

class NovelWriterTools:
    """
    Novel Writer Skill Tools (Entity-ized)
    Implements the file operations and structure management defined in SKILL.md.
    """
    
    def __init__(self, novels_root: str = None):
        if novels_root:
            self.novels_root = Path(novels_root)
        else:
            # Default to ../../../Novels relative to this file
            self.novels_root = Path(__file__).parent.parent.parent.parent / "Novels"
            
        self.novels_root.mkdir(parents=True, exist_ok=True)

    def _get_book_path(self, book_name: str) -> Path:
        # Find book directory (handle slight name variations if needed, but strict for now)
        return self.novels_root / book_name

    def create_book(self, book_name: str, protagonist: str, genre: str, synopsis: str) -> Dict:
        """
        Initialize a new book project structure.
        """
        book_path = self._get_book_path(book_name)
        
        if book_path.exists():
            return {"status": "error", "message": f"Book '{book_name}' already exists."}
        
        # Create directories
        (book_path / "00_设定").mkdir(parents=True)
        (book_path / "10_正文").mkdir(parents=True)
        (book_path / "99_草稿").mkdir(parents=True)
        
        # Create Metadata
        metadata = {
            "title": book_name,
            "protagonist": protagonist,
            "genre": genre,
            "created_at": datetime.datetime.now().isoformat(),
            "status": "ongoing"
        }
        with open(book_path / "book_meta.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        # Create Initial Settings Template
        settings_content = f"""# {book_name} - 初始设定

## 基础信息
- **书名**: {book_name}
- **类型**: {genre}
- **主角**: {protagonist}

## 故事梗概
{synopsis}

## 世界观
(待补充)

## 核心人物
- {protagonist}: (待补充)
"""
        with open(book_path / "00_设定" / "001_世界观与人设.md", "w", encoding="utf-8") as f:
            f.write(settings_content)
            
        return {
            "status": "success", 
            "message": f"Book '{book_name}' created successfully.",
            "path": str(book_path)
        }

    def save_chapter(self, book_name: str, volume: str, chapter_title: str, content: str) -> Dict:
        """
        Save a chapter content.
        volume: e.g., "01_第一卷"
        chapter_title: e.g., "001_第一章_起始"
        """
        book_path = self._get_book_path(book_name)
        if not book_path.exists():
             return {"status": "error", "message": f"Book '{book_name}' not found."}
             
        # Handle volume directory
        volume_dir = book_path / volume / "10_正文"
        # If volume doesn't exist, maybe it's flat structure or user didn't create volume?
        # Let's support flat structure in 10_正文 if volume is empty/default, 
        # or create volume dir if specified.
        
        if volume:
            volume_path = book_path / volume
            volume_content_path = volume_path / "10_正文"
            volume_content_path.mkdir(parents=True, exist_ok=True)
            target_dir = volume_content_path
        else:
            target_dir = book_path / "10_正文"
            
        # Ensure filename ends with .txt
        filename = f"{chapter_title}.txt" if not chapter_title.endswith(".txt") else chapter_title
        file_path = target_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Update word count logic could go here
        
        return {
            "status": "success",
            "message": f"Chapter '{filename}' saved.",
            "path": str(file_path)
        }

    def get_book_context(self, book_name: str) -> Dict:
        """
        Retrieve settings and recent chapters for context.
        """
        book_path = self._get_book_path(book_name)
        if not book_path.exists():
            return {"status": "error", "message": f"Book '{book_name}' not found."}
            
        context = {
            "title": book_name,
            "settings": "",
            "recent_chapters": []
        }
        
        # Read Settings
        settings_dir = book_path / "00_设定"
        if settings_dir.exists():
            for file in settings_dir.glob("*.md"):
                with open(file, "r", encoding="utf-8") as f:
                    context["settings"] += f"\n--- {file.name} ---\n{f.read()}\n"
                    
        # Read Metadata
        meta_file = book_path / "book_meta.json"
        if meta_file.exists():
             with open(meta_file, "r", encoding="utf-8") as f:
                 context["metadata"] = json.load(f)
                 
        return context

    def list_books(self) -> List[str]:
        if not self.novels_root.exists():
            return []
        return [d.name for d in self.novels_root.iterdir() if d.is_dir()]

    def read_file(self, file_path: Path) -> str:
        """Helper to safely read file content."""
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def get_character_profiles(self, book_name: str, volume: str = None) -> str:
        """Read [CHAR]人物志.md from volume dir or root."""
        book_path = self._get_book_path(book_name)
        content = ""
        
        # 1. Root Profile
        root_char = book_path / "[CHAR]人物志.md"
        if root_char.exists():
            content += f"\n=== 全书人物志 ===\n{self.read_file(root_char)}\n"
            
        # 2. Volume Profile (if exists)
        if volume:
            vol_char = book_path / volume / "[CHAR]人物志.md"
            if vol_char.exists():
                content += f"\n=== {volume} 人物志 ===\n{self.read_file(vol_char)}\n"
                
        return content

    def get_outline(self, book_name: str, volume: str) -> str:
        """Read [PLOT]本卷细纲.md."""
        book_path = self._get_book_path(book_name)
        if volume:
            outline = book_path / volume / "[PLOT]本卷细纲.md"
            return self.read_file(outline)
        return ""

    def update_audit_log(self, book_name: str, volume: str, chapter: str, remarks: str):
        """
        Append consistency check remarks to chapter file and separate log.
        """
        book_path = self._get_book_path(book_name)
        
        # 1. Append to chapter file (bottom)
        if volume:
            chapter_path = book_path / volume / "10_正文" / f"{chapter}.txt"
        else:
            chapter_path = book_path / "10_正文" / f"{chapter}.txt"
            
        if chapter_path.exists():
            with open(chapter_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n[质控备注]\n{remarks}\n")
                
        # 2. Append to a centralized log
        log_path = book_path / "[LOG]质控记录.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## [{timestamp}] {volume}/{chapter}\n{remarks}\n")

    def update_status_sync_log(self, book_name: str, volume: str, chapter: str, updates: str):
        """
        Log state changes for manual or auto merging later.
        """
        book_path = self._get_book_path(book_name)
        log_path = book_path / "[LOG]状态同步.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## [{timestamp}] {volume}/{chapter} 同步请求\n{updates}\n")
