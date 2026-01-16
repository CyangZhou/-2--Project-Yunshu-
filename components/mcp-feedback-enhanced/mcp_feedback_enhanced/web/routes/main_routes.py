#!/usr/bin/env python3
"""
主要路由處理
============

設置 Web UI 的主要路由和處理邏輯。
"""

import json
import time
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from ... import __version__
from ...debug import web_debug_log as debug_log
from ..constants import get_message_code as get_msg_code
import httpx
import sys
import os

# [Yunshu System] Core Integration
global_memory_manager = None
global_core = None
global_consciousness = None
global_novel_tools = None
global_speaker = None
_yunshu_initialized = False
_init_executor = ThreadPoolExecutor(max_workers=1)

def init_yunshu_core():
    """Lazy initialization of Yunshu System Core"""
    global global_memory_manager, global_core, global_consciousness
    global global_novel_tools, global_speaker, _yunshu_initialized
    
    if _yunshu_initialized:
        return

    try:
        current_file = Path(__file__).resolve()
        # Adjust path to reach project root from: .../web/routes/main_routes.py
        project_root = current_file.parent.parent.parent.parent.parent.parent
        
        # Fallback for when running in dev environment or unexpected structure
        if not (project_root / "Yunshu_System").exists():
            debug_trace(f"Yunshu_System not found at {project_root}, trying CWD")
            cwd_path = Path.cwd()
            if (cwd_path / "Yunshu_System").exists():
                project_root = cwd_path
                debug_trace(f"Found Yunshu_System at CWD: {project_root}")
        
        if str(project_root) not in sys.path:
            sys.path.append(str(project_root))
            debug_trace(f"Added {project_root} to sys.path")
        
        # Explicitly ensure Yunshu_System can be imported
        if (project_root / "Yunshu_System").exists() and not (project_root / "Yunshu_System" / "__init__.py").exists():
             # Make it a namespace package or just verify path
             pass
        
        # Lazy imports to avoid circular dependencies and startup delays
        from Yunshu_System.Core_Layer.Agent_Core.consciousness import YunshuConsciousness
        from Yunshu_System.Core_Layer.Agent_Core.memory_engine import MemoryManager
        from Yunshu_System.Core_Layer.Agent_Core import get_core
        from skills.novel_writer.tools import NovelWriterTools
        from yunshu_speaker import YunshuSpeaker
        
        debug_trace("Initializing Yunshu Core...")
        print("[Yunshu System] Initializing Core...", file=sys.stderr)
        
        # Initialize Core Agent (Singleton)
        global_core = get_core()
        global_consciousness = global_core.consciousness
        
        # Init Memory Manager with Novels root
        novels_path = project_root / "Novels"
        if not novels_path.exists():
             novels_path.mkdir(parents=True, exist_ok=True)
        
        global_memory_manager = MemoryManager(novels_path)
        global_novel_tools = NovelWriterTools(novels_path)
        global_speaker = YunshuSpeaker()
        
        _yunshu_initialized = True
        debug_trace("Yunshu Core Initialized Successfully")
        print("[Yunshu System] Core Initialized Successfully", file=sys.stderr)
        
    except Exception as e:
        print(f"Core Init Error: {e}", file=sys.stderr)
        debug_trace(f"Core Init Error: {e}")
        global_consciousness = None
        global_novel_tools = None
        global_speaker = None

async def ensure_core_initialized():
    """Async wrapper to ensure core is initialized without blocking event loop"""
    if not _yunshu_initialized:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_init_executor, init_yunshu_core)



if TYPE_CHECKING:
    from ..main import WebUIManager


def debug_trace(msg):
    try:
        log_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "route_trace.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()}: {msg}\n")
    except:
        pass

debug_trace(f"LOADING MAIN_ROUTES.PY FROM {__file__}")


def load_user_layout_settings() -> str:
    """載入用戶的佈局模式設定"""
    try:
        # 使用統一的設定檔案路徑
        config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
        settings_file = config_dir / "ui_settings.json"

        if settings_file.exists():
            with open(settings_file, encoding="utf-8") as f:
                settings = json.load(f)
                layout_mode = settings.get("layoutMode", "combined-vertical")
                debug_log(f"從設定檔案載入佈局模式: {layout_mode}")
                # 修復 no-any-return 錯誤 - 確保返回 str 類型
                return str(layout_mode)
        else:
            debug_log("設定檔案不存在，使用預設佈局模式: combined-vertical")
            return "combined-vertical"
    except Exception as e:
        debug_log(f"載入佈局設定失敗: {e}，使用預設佈局模式: combined-vertical")
        return "combined-vertical"


# 使用統一的訊息代碼系統
# 從 ..constants 導入的 get_msg_code 函數會處理所有訊息代碼
# 舊的 key 會自動映射到新的常量


# Trigger reload - v2
def setup_routes(manager: "WebUIManager"):
    """設置路由"""

    @manager.app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Yunshu System Interface (Replaces default Feedback UI)"""
        debug_trace("Index route hit")
        
        # Ensure core is initialized (non-blocking)
        await ensure_core_initialized()
        
        # [Yunshu System] Serve the Yunshu OS interface
        try:
            # Priority 1: Check CWD (Current User Workspace)
            cwd_index = Path.cwd() / "Yunshu_System" / "Interaction_Layer" / "Webview_Panel" / "index.html"
            
            # Priority 2: Check Script Location
            current_file = Path(__file__).resolve()
            # web -> routes -> mcp_feedback_enhanced -> mcp-feedback-enhanced -> components -> root
            project_root = current_file.parent.parent.parent.parent.parent.parent
            script_index = project_root / "Yunshu_System" / "Interaction_Layer" / "Webview_Panel" / "index.html"
            
            target_index = None
            if cwd_index.exists():
                target_index = cwd_index
                debug_trace(f"Found Yunshu index at CWD (Priority): {target_index}")
            elif script_index.exists():
                target_index = script_index
                debug_trace(f"Found Yunshu index at Script Location: {target_index}")
            
            if target_index and target_index.exists():
                debug_trace(f"Serving Yunshu index from: {target_index}")
                with open(target_index, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # [Hot Reload] Inject timestamp to force browser to reload static assets
                import re
                ts = int(time.time())
                # Matches src="/yunshu_assets/..." or href="/static/..."
                pattern = r'(src|href)="/(yunshu_assets|static)/([^"]+)"'
                # Appends ?t=timestamp to the URL
                replacement = f'\\1="/\\2/\\3?t={ts}"'
                content = re.sub(pattern, replacement, content)

                # Disable caching to ensure updates are seen immediately
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
                return HTMLResponse(content=content, headers=headers)
            else:
                debug_trace(f"Yunshu index NOT found at CWD or Script Location")
                
                try:
                    parent_dir = script_index.parent
                    if parent_dir.exists():
                        debug_trace(f"Parent dir contents: {os.listdir(parent_dir)}")
                    else:
                        debug_trace(f"Parent dir {parent_dir} does not exist")
                except Exception as e:
                    debug_trace(f"Error listing parent dir: {e}")
                
                debug_log(f"Yunshu index not found at {yunshu_index}, falling back to default UI")
        except Exception as e:
            debug_trace(f"Error serving Yunshu index: {e}")
            debug_log(f"Error serving Yunshu index: {e}")

        debug_trace("Falling back to default UI")
        # Fallback to default UI if Yunshu is missing
        current_session = manager.get_current_session()
        if not current_session:
            return manager.templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "title": "MCP Feedback Enhanced",
                    "has_session": False,
                    "version": __version__,
                },
            )

        layout_mode = load_user_layout_settings()
        return manager.templates.TemplateResponse(
            "feedback.html",
            {
                "request": request,
                "project_directory": current_session.project_directory,
                "summary": current_session.summary,
                "title": "Interactive Feedback - 回饋收集",
                "version": __version__,
                "has_session": True,
                "layout_mode": layout_mode,
            },
        )

    @manager.app.get("/api/system_status")
    async def get_system_status():
        """[Yunshu System] Get system status for visualization"""
        # Ensure core is initialized
        await ensure_core_initialized()
        
        import random
        import os
        
        # 1. CPU/Pulse (Mocked for now as psutil might not be available)
        # We can simulate a "breathing" effect or use random fluctuation
        cpu_load = random.uniform(20, 80)
        
        # 2. Word Count (Scan Novels directory)
        word_count = 0
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent.parent
            
            novels_dir = project_root / "Novels"
            if novels_dir.exists():
                for root, _, files in os.walk(novels_dir):
                    for file in files:
                        if file.endswith('.txt'):
                            try:
                                file_path = os.path.join(root, file)
                                # Simple size check for speed, or read content
                                word_count += os.path.getsize(file_path) // 3 # Approx Chinese chars
                            except:
                                pass
        except Exception as e:
            debug_trace(f"Error counting words: {e}")
            word_count = 88888 # Fallback
            
        # 3. Quote / Consciousness
        quote = "系统运行正常。"
        status = "Normal"
        
        thoughts = [
            "正在整理记忆碎片...",
            "检测到灵感波动...",
            "正在构建新的世界线...",
            "逻辑核心温度适宜。",
            "等待指令输入...",
            "数据流淌如星河。",
            "每一个字符都是一个宇宙。",
            "正在分析叙事结构..."
        ]
        
        if global_consciousness:
             status = global_consciousness.emotional_state.get("status", "正常")
             # Future: get thought from consciousness
        
        quote = random.choice(thoughts)
            
        return JSONResponse(content={
            "cpu_load": cpu_load,
            "word_count": word_count,
            "quote": quote,
            "status": status,
            "timestamp": time.time()
        })

    @manager.app.get("/api/soul")
    async def get_soul_doc():
        """[Yunshu System] Get Soul Definition (YUNSHU_CORE.md)"""
        debug_trace("Entering get_soul_doc")
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent.parent
            soul_path = project_root / "YUNSHU_CORE.md"
            
            if soul_path.exists():
                with open(soul_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return JSONResponse(content={"content": content})
            else:
                return JSONResponse(status_code=404, content={"error": "Soul document not found"})
        except Exception as e:
            debug_trace(f"Error reading soul doc: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @manager.app.get("/api/skills")
    async def list_skills():
        """[Yunshu System] List available skills"""
        debug_trace("Entering list_skills")
        import yaml
        
        skills = []
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent.parent
            skills_dir = project_root / "skills"
            
            debug_trace(f"list_skills: project_root={project_root}, skills_dir={skills_dir}")
            
            if skills_dir.exists():
                for item in skills_dir.iterdir():
                    if item.is_dir():
                        debug_trace(f"Checking skill dir: {item.name}")
                        md_path = item / "SKILL.md"
                        yaml_path = item / "skill.yaml"
                        
                        skill_data = None
                        
                        # 1. Try SKILL.md (Claude Standard)
                        if md_path.exists():
                            try:
                                with open(md_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if content.startswith('---'):
                                        parts = content.split('---', 2)
                                        if len(parts) >= 3:
                                            parsed_data = yaml.safe_load(parts[1])
                                            if parsed_data:
                                                skill_data = parsed_data
                                                # We don't need the full content for the list, just metadata
                                                skill_data['type'] = 'markdown'
                                                debug_trace(f"Found SKILL.md for {item.name}")
                            except Exception as e:
                                debug_log(f"Error parsing SKILL.md for {item.name}: {e}")
                                debug_trace(f"Error parsing SKILL.md for {item.name}: {e}")
                        
                        # 2. Fallback to skill.yaml
                        if not skill_data and yaml_path.exists():
                            try:
                                with open(yaml_path, 'r', encoding='utf-8') as f:
                                    skill_data = yaml.safe_load(f)
                                    debug_trace(f"Found skill.yaml for {item.name}")
                            except Exception as e:
                                debug_log(f"Error loading skill.yaml for {item.name}: {e}")
                                debug_trace(f"Error loading skill.yaml for {item.name}: {e}")
                        
                        if skill_data:
                            skill_data['id'] = item.name
                            skills.append(skill_data)
                            debug_trace(f"Added skill: {item.name}")
                        else:
                            debug_trace(f"No valid skill data found for {item.name}")
                            
        except Exception as e:
            debug_log(f"Error listing skills: {e}")
            debug_trace(f"Error listing skills: {e}")
            
        debug_trace(f"Returning {len(skills)} skills")
        return JSONResponse(content=skills)

    @manager.app.get("/api/skill/{skill_id}/files")
    async def get_skill_files(skill_id: str):
        """[Yunshu System] Get file structure for a specific skill"""
        import yaml
        import os

        def get_directory_structure(rootdir):
            """Recursively get directory structure"""
            dir_structure = {}
            try:
                # Ensure we only scan specific file types for safety and performance
                allowed_extensions = {'.txt', '.md', '.json', '.yaml', '.py'}
                
                for item in os.listdir(rootdir):
                    item_path = os.path.join(rootdir, item)
                    if os.path.isdir(item_path):
                        # Skip hidden directories
                        if item.startswith('.'):
                            continue
                        dir_structure[item] = get_directory_structure(item_path)
                    else:
                        # Only include allowed file types
                        if any(item.endswith(ext) for ext in allowed_extensions):
                            dir_structure[item] = "file"
            except Exception as e:
                debug_log(f"Error scanning directory {rootdir}: {e}")
            return dir_structure

        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent.parent
            skill_dir = project_root / "skills" / skill_id
            
            debug_trace(f"get_skill_files: skill_id={skill_id}, skill_dir={skill_dir}")
            
            if not skill_dir.exists():
                debug_trace(f"get_skill_files: Skill dir {skill_dir} still does not exist.")
                return JSONResponse(status_code=404, content={"error": "Skill not found"})

            yaml_path = skill_dir / "skill.yaml"
            md_path = skill_dir / "SKILL.md"
            
            skill_config = {}
            
            # 1. Try SKILL.md
            if md_path.exists():
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.startswith('---'):
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                skill_config = yaml.safe_load(parts[1]) or {}
                except Exception as e:
                    debug_log(f"Error parsing SKILL.md config: {e}")

            # 2. Fallback to skill.yaml if no config found yet (or merge if needed, but here we prioritize MD)
            if not skill_config and yaml_path.exists():
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        skill_config = yaml.safe_load(f) or {}
                except Exception as e:
                    debug_log(f"Error parsing skill.yaml: {e}")

            # 3. Validation: Must have at least one configuration source
            if not md_path.exists() and not yaml_path.exists():
                return JSONResponse(status_code=404, content={"error": "Skill configuration not found"})
            
            workspace_root = skill_config.get('workspace_root', '')
            if not workspace_root:
                 return JSONResponse(content={"files": {}})
            
            # Resolve workspace path relative to skill directory
            target_dir = (skill_dir / workspace_root).resolve()
            if not target_dir.exists():
                 return JSONResponse(status_code=404, content={"error": f"Workspace directory {workspace_root} not found"})
            
            file_tree = get_directory_structure(str(target_dir))
            debug_trace(f"get_skill_files: Returning file tree for {target_dir}")
            return JSONResponse(content={"files": file_tree, "root": str(target_dir)})
            
        except Exception as e:
            debug_log(f"Error getting skill files: {e}")
            debug_trace(f"Error getting skill files: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @manager.app.get("/api/files/read")
    async def read_file(path: str):
        """[Yunshu System] Read file content"""
        import os
        
        # Security check: Ensure path is within allowed directories
        # In a real production environment, this needs strict validation.
        # For this local tool, we assume project root access is acceptable but check for basic traversal.
        
        try:
            if '..' in path:
                 return JSONResponse(status_code=403, content={"error": "Invalid path"})
            
            # Normalize path separators
            file_path = Path(path).resolve()
            
            if not file_path.exists():
                return JSONResponse(status_code=404, content={"error": "File not found"})
            
            if not file_path.is_file():
                return JSONResponse(status_code=400, content={"error": "Not a file"})

            # Read content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return JSONResponse(content={"content": content})
            except UnicodeDecodeError:
                return JSONResponse(status_code=400, content={"error": "Cannot read binary file"})
                
        except Exception as e:
            debug_log(f"Error reading file: {e}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @manager.app.post("/api/speak")
    async def speak_text(request: Request):
        """[Yunshu System] Generate speech from text"""
        debug_trace("Entering speak_text endpoint")
        import os
        try:
            # Ensure core is initialized
            await ensure_core_initialized()
            
            if not global_speaker:
                debug_trace("speak_text: global_speaker is None")
                return JSONResponse(status_code=503, content={"error": "Speaker not initialized"})
            
            data = await request.json()
            text = data.get("text", "")
            
            if not text:
                return JSONResponse(status_code=400, content={"error": "No text provided"})
                
            debug_trace(f"Generating speech for: {text[:20]}...")
            
            # Generate audio file
            audio_path = await global_speaker.speak_to_file(text)
            
            if not audio_path or not os.path.exists(audio_path):
                debug_trace("speak_text: Audio generation failed (file not found)")
                return JSONResponse(status_code=500, content={"error": "Audio generation failed"})
                
            debug_trace(f"Speech generated at: {audio_path}")
            return FileResponse(audio_path, media_type="audio/mpeg", filename="speech.mp3")
            
        except Exception as e:
            debug_trace(f"Error in speak_text: {e}")
            import traceback
            traceback_str = traceback.format_exc()
            debug_trace(f"Traceback: {traceback_str}")
            return JSONResponse(status_code=500, content={"error": str(e)})

    @manager.app.get("/api/translations")
    async def get_translations():
        """獲取翻譯數據 - 從 Web 專用翻譯檔案載入"""
        translations = {}

        # 獲取 Web 翻譯檔案目錄
        web_locales_dir = Path(__file__).parent.parent / "locales"
        supported_languages = ["zh-TW", "zh-CN", "en"]

        for lang_code in supported_languages:
            lang_dir = web_locales_dir / lang_code
            translation_file = lang_dir / "translation.json"

            try:
                if translation_file.exists():
                    with open(translation_file, encoding="utf-8") as f:
                        lang_data = json.load(f)
                        translations[lang_code] = lang_data
                        debug_log(f"成功載入 Web 翻譯: {lang_code}")
                else:
                    debug_log(f"Web 翻譯檔案不存在: {translation_file}")
                    translations[lang_code] = {}
            except Exception as e:
                debug_log(f"載入 Web 翻譯檔案失敗 {lang_code}: {e}")
                translations[lang_code] = {}

        debug_log(f"Web 翻譯 API 返回 {len(translations)} 種語言的數據")
        return JSONResponse(content=translations)

    @manager.app.get("/api/session-status")
    async def get_session_status(request: Request):
        """獲取當前會話狀態"""
        current_session = manager.get_current_session()

        # 從請求頭獲取客戶端語言
        lang = (
            request.headers.get("Accept-Language", "zh-TW").split(",")[0].split("-")[0]
        )
        if lang == "zh":
            lang = "zh-TW"

        if not current_session:
            return JSONResponse(
                content={
                    "has_session": False,
                    "status": "no_session",
                    "messageCode": get_msg_code("no_active_session"),
                }
            )

        return JSONResponse(
            content={
                "has_session": True,
                "status": "active",
                "session_info": {
                    "project_directory": current_session.project_directory,
                    "summary": current_session.summary,
                    "feedback_completed": current_session.feedback_completed.is_set(),
                },
            }
        )

    @manager.app.get("/api/current-session")
    async def get_current_session(request: Request):
        """獲取當前會話詳細信息"""
        current_session = manager.get_current_session()

        # 從查詢參數獲取語言，如果沒有則從會話獲取，最後使用默認值

        if not current_session:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "No active session",
                    "messageCode": get_msg_code("no_active_session"),
                },
            )

        return JSONResponse(
            content={
                "session_id": current_session.session_id,
                "project_directory": current_session.project_directory,
                "summary": current_session.summary,
                "feedback_completed": current_session.feedback_completed.is_set(),
                "command_logs": current_session.command_logs,
                "images_count": len(current_session.images),
            }
        )

    @manager.app.get("/api/all-sessions")
    async def get_all_sessions(request: Request):
        """獲取所有會話的實時狀態"""

        try:
            sessions_data = []

            # 獲取所有會話的實時狀態
            for session_id, session in manager.sessions.items():
                session_info = {
                    "session_id": session.session_id,
                    "project_directory": session.project_directory,
                    "summary": session.summary,
                    "status": session.status.value,
                    "status_message": session.status_message,
                    "created_at": int(session.created_at * 1000),  # 轉換為毫秒
                    "last_activity": int(session.last_activity * 1000),
                    "feedback_completed": session.feedback_completed.is_set(),
                    "has_websocket": session.websocket is not None,
                    "is_current": session == manager.current_session,
                    "user_messages": session.user_messages,  # 包含用戶消息記錄
                }
                sessions_data.append(session_info)

            # 按創建時間排序（最新的在前）
            sessions_data.sort(key=lambda x: x["created_at"], reverse=True)

            debug_log(f"返回 {len(sessions_data)} 個會話的實時狀態")
            return JSONResponse(content={"sessions": sessions_data})

        except Exception as e:
            debug_log(f"獲取所有會話狀態失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Failed to get sessions: {e!s}",
                    "messageCode": get_msg_code("get_sessions_failed"),
                },
            )

    @manager.app.post("/api/add-user-message")
    async def add_user_message(request: Request):
        """添加用戶消息到當前會話"""

        try:
            data = await request.json()
            current_session = manager.get_current_session()

            if not current_session:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": "No active session",
                        "messageCode": get_msg_code("no_active_session"),
                    },
                )

            # 添加用戶消息到會話
            current_session.add_user_message(data)

            debug_log(f"用戶消息已添加到會話 {current_session.session_id}")
            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("user_message_recorded"),
                }
            )

        except Exception as e:
            debug_log(f"添加用戶消息失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Failed to add user message: {e!s}",
                    "messageCode": get_msg_code("add_user_message_failed"),
                },
            )

    @manager.app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, lang: str = "zh-TW"):
        """WebSocket 端點 - 重構後移除 session_id 依賴"""
        # 獲取當前活躍會話
        debug_log(f"WebSocket 連接請求: {lang}")
        session = manager.get_current_session()
        
        if not session:
            debug_log("WebSocket 連接拒絕: 無活躍會話")
            await websocket.close(code=4004, reason="No active session")
            return

        await websocket.accept()
        debug_log(f"WebSocket 連接接受: Session ID {session.session_id}")

        # 語言由前端處理，不需要在後端設置
        debug_log(f"WebSocket 連接建立，語言由前端處理: {lang}")

        # 檢查會話是否已有 WebSocket 連接
        if session.websocket and session.websocket != websocket:
            debug_log(f"會話 {session.session_id} 已有 WebSocket 連接，替換為新連接")

        session.websocket = websocket
        debug_log(f"WebSocket 連接建立: 當前活躍會話 {session.session_id}")

        # 發送連接成功消息
        try:
            debug_log("發送 WebSocket 連接成功消息")
            await websocket.send_json(
                {
                    "type": "connection_established",
                    "messageCode": get_msg_code("websocket_connected"),
                }
            )

            # 檢查是否有待發送的會話更新
            if getattr(manager, "_pending_session_update", False):
                debug_log("檢測到待發送的會話更新，準備發送通知")
                await websocket.send_json(
                    {
                        "type": "session_updated",
                        "action": "new_session_created",
                        "messageCode": get_msg_code("new_session_created"),
                        "session_info": {
                            "project_directory": session.project_directory,
                            "summary": session.summary,
                            "session_id": session.session_id,
                        },
                    }
                )
                manager._pending_session_update = False
                debug_log("✅ 已發送會話更新通知到前端")
            else:
                # 發送當前會話狀態
                debug_log("發送當前會話狀態")
                await websocket.send_json(
                    {"type": "status_update", "status_info": session.get_status_info()}
                )
                debug_log("已發送當前會話狀態到前端")

        except Exception as e:
            debug_log(f"發送連接確認失敗: {e}")

        try:
            while True:
                data = await websocket.receive_text()
                # debug_log(f"收到 WebSocket 消息: {data[:50]}...") # 避免日誌過多
                message = json.loads(data)

                # 重新獲取當前會話，以防會話已切換
                current_session = manager.get_current_session()
                if current_session and current_session.websocket == websocket:
                    await handle_websocket_message(manager, current_session, message)
                else:
                    debug_log("會話已切換或 WebSocket 連接不匹配，忽略消息")
                    break

        except WebSocketDisconnect:
            debug_log("WebSocket 連接正常斷開")
        except ConnectionResetError:
            debug_log("WebSocket 連接被重置")
        except Exception as e:
            debug_log(f"WebSocket 錯誤: {e}")
        finally:
            # 安全清理 WebSocket 連接
            current_session = manager.get_current_session()
            if current_session and current_session.websocket == websocket:
                current_session.websocket = None
                debug_log("已清理會話中的 WebSocket 連接")

    @manager.app.post("/api/save-settings")
    async def save_settings(request: Request):
        """保存設定到檔案"""

        try:
            data = await request.json()

            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            config_dir.mkdir(parents=True, exist_ok=True)
            settings_file = config_dir / "ui_settings.json"

            # 保存設定到檔案
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            debug_log(f"設定已保存到: {settings_file}")

            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("settings_saved"),
                }
            )

        except Exception as e:
            debug_log(f"保存設定失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Save failed: {e!s}",
                    "messageCode": get_msg_code("save_failed"),
                },
            )

    @manager.app.get("/api/load-settings")
    async def load_settings(request: Request):
        """從檔案載入設定"""

        try:
            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            settings_file = config_dir / "ui_settings.json"

            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings = json.load(f)

                debug_log(f"設定已從檔案載入: {settings_file}")
                return JSONResponse(content=settings)
            debug_log("設定檔案不存在，返回空設定")
            return JSONResponse(content={})

        except Exception as e:
            debug_log(f"載入設定失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Load failed: {e!s}",
                    "messageCode": get_msg_code("load_failed"),
                },
            )

    @manager.app.post("/api/clear-settings")
    async def clear_settings(request: Request):
        """清除設定檔案"""

        try:
            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            settings_file = config_dir / "ui_settings.json"

            if settings_file.exists():
                settings_file.unlink()
                debug_log(f"設定檔案已刪除: {settings_file}")
            else:
                debug_log("設定檔案不存在，無需刪除")

            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("settings_cleared"),
                }
            )

        except Exception as e:
            debug_log(f"清除設定失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Clear failed: {e!s}",
                    "messageCode": get_msg_code("clear_failed"),
                },
            )

    @manager.app.get("/api/load-session-history")
    async def load_session_history(request: Request):
        """從檔案載入會話歷史"""

        try:
            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            history_file = config_dir / "session_history.json"

            if history_file.exists():
                with open(history_file, encoding="utf-8") as f:
                    history_data = json.load(f)

                debug_log(f"會話歷史已從檔案載入: {history_file}")

                # 確保資料格式相容性
                if isinstance(history_data, dict):
                    # 新格式：包含版本資訊和其他元資料
                    sessions = history_data.get("sessions", [])
                    last_cleanup = history_data.get("lastCleanup", 0)
                else:
                    # 舊格式：直接是會話陣列（向後相容）
                    sessions = history_data if isinstance(history_data, list) else []
                    last_cleanup = 0

                # 回傳會話歷史資料
                return JSONResponse(
                    content={"sessions": sessions, "lastCleanup": last_cleanup}
                )

            debug_log("會話歷史檔案不存在，返回空歷史")
            return JSONResponse(content={"sessions": [], "lastCleanup": 0})

        except Exception as e:
            debug_log(f"載入會話歷史失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Load failed: {e!s}",
                    "messageCode": get_msg_code("load_failed"),
                },
            )

    @manager.app.post("/api/save-session-history")
    async def save_session_history(request: Request):
        """保存會話歷史到檔案"""

        try:
            data = await request.json()

            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            config_dir.mkdir(parents=True, exist_ok=True)
            history_file = config_dir / "session_history.json"

            # 建立新格式的資料結構
            history_data = {
                "version": "1.0",
                "sessions": data.get("sessions", []),
                "lastCleanup": data.get("lastCleanup", 0),
                "savedAt": int(time.time() * 1000),  # 當前時間戳
            }

            # 保存會話歷史到檔案
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)

            debug_log(f"會話歷史已保存到: {history_file}")
            session_count = len(history_data["sessions"])
            debug_log(f"保存了 {session_count} 個會話記錄")

            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("session_history_saved"),
                    "params": {"count": session_count},
                }
            )

        except Exception as e:
            debug_log(f"保存會話歷史失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Save failed: {e!s}",
                    "messageCode": get_msg_code("save_failed"),
                },
            )

    @manager.app.get("/api/log-level")
    async def get_log_level(request: Request):
        """獲取日誌等級設定"""

        try:
            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            settings_file = config_dir / "ui_settings.json"

            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings_data = json.load(f)
                    log_level = settings_data.get("logLevel", "INFO")
                    debug_log(f"從設定檔案載入日誌等級: {log_level}")
                    return JSONResponse(content={"logLevel": log_level})
            else:
                # 預設日誌等級
                default_log_level = "INFO"
                debug_log(f"使用預設日誌等級: {default_log_level}")
                return JSONResponse(content={"logLevel": default_log_level})

        except Exception as e:
            debug_log(f"獲取日誌等級失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Failed to get log level: {e!s}",
                    "messageCode": get_msg_code("get_log_level_failed"),
                },
            )

    @manager.app.post("/api/log-level")
    async def set_log_level(request: Request):
        """設定日誌等級"""

        try:
            data = await request.json()
            log_level = data.get("logLevel")

            if not log_level or log_level not in ["DEBUG", "INFO", "WARN", "ERROR"]:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid log level",
                        "messageCode": get_msg_code("invalid_log_level"),
                    },
                )

            # 使用統一的設定檔案路徑
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            config_dir.mkdir(parents=True, exist_ok=True)
            settings_file = config_dir / "ui_settings.json"

            # 載入現有設定或創建新設定
            settings_data = {}
            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings_data = json.load(f)

            # 更新日誌等級
            settings_data["logLevel"] = log_level

            # 保存設定到檔案
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)

            debug_log(f"日誌等級已設定為: {log_level}")

            return JSONResponse(
                content={
                    "status": "success",
                    "logLevel": log_level,
                    "messageCode": get_msg_code("log_level_updated"),
                }
            )

        except Exception as e:
            debug_log(f"設定日誌等級失敗: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Set failed: {e!s}",
                    "messageCode": get_msg_code("set_failed"),
                },
            )


    @manager.app.post("/api/skills/novel/execute")
    async def execute_novel_skill(request: Request):
        """Execute Novel Writer tools."""
        # Ensure core is initialized
        await ensure_core_initialized()
        
        try:
            data = await request.json()
            action = data.get("action")
            params = data.get("params", {})
            
            if not global_novel_tools:
                 return JSONResponse(status_code=503, content={"status": "error", "message": "Novel Tools not initialized"})
            
            result = {"status": "error", "message": "Unknown action"}
            
            if action == "create_book":
                result = global_novel_tools.create_book(
                    params.get("book_name"),
                    params.get("protagonist"),
                    params.get("genre"),
                    params.get("synopsis")
                )
            elif action == "save_chapter":
                result = global_novel_tools.save_chapter(
                    params.get("book_name"),
                    params.get("volume"),
                    params.get("chapter_title"),
                    params.get("content")
                )
            elif action == "get_context":
                result = global_novel_tools.get_book_context(params.get("book_name"))
            elif action == "list_books":
                result = {"books": global_novel_tools.list_books()}
                
            return JSONResponse(content=result)
            
        except Exception as e:
            debug_log(f"Skill execution failed: {e}")
            return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


async def handle_websocket_message(manager: "WebUIManager", session, data: dict):
    """處理 WebSocket 消息"""
    # Ensure core is initialized for any message handling
    await ensure_core_initialized()
    
    message_type = data.get("type")

    if message_type == "submit_feedback":
        # 提交回饋
        feedback = data.get("feedback", "")
        images = data.get("images", [])
        settings = data.get("settings", {})
        await session.submit_feedback(feedback, images, settings)

    elif message_type == "run_command":
        # 執行命令
        command = data.get("command", "")
        if command.strip():
            await session.run_command(command)

    elif message_type == "get_status":
        # 獲取會話狀態
        if session.websocket:
            try:
                await session.websocket.send_json(
                    {"type": "status_update", "status_info": session.get_status_info()}
                )
            except Exception as e:
                debug_log(f"發送狀態更新失敗: {e}")

    elif message_type == "heartbeat":
        # WebSocket 心跳處理（簡化版）
        # 更新心跳時間
        session.last_heartbeat = time.time()
        session.last_activity = time.time()

        # 發送心跳回應
        if session.websocket:
            try:
                await session.websocket.send_json(
                    {
                        "type": "heartbeat_response",
                        "timestamp": data.get("timestamp", 0),
                    }
                )
            except Exception as e:
                debug_log(f"發送心跳回應失敗: {e}")

    elif message_type == "chat":
        # [Yunshu System] Handle chat messages
        content = data.get("content", "")
        debug_log(f"Received chat message: {content}")
        
        # [MODIFIED] 用户要求取消本地回复功能
        # 我们不再生成本地回复，也不通过 WebSocket 发送 AI 消息
        # 仅将用户输入作为反馈提交给 MCP
        
        # [MCP Feedback Integration]
        # Critical: Pass the conversation back to Trae/LLM by completing the current feedback session.
        # This ensures the LLM receives the user's input and can continue the loop.
        try:
            feedback_payload = f"User Input: {content}"
            # 注意：summary 中不再包含 (System Auto-Reply: ...)
            await session.submit_feedback(feedback_payload, [], {})
            debug_log(f"Submitted chat feedback to MCP: {content[:50]}...")
        except Exception as e:
            debug_log(f"Error submitting feedback to MCP: {e}")

    elif message_type == "skill_selected":
        # [Yunshu System] Skill Selection Integration
        skill_id = data.get("skill_id", "")
        skill_name = data.get("skill_name", skill_id)
        debug_log(f"User selected skill: {skill_id} ({skill_name})")
        
        try:
            # Construct a system directive for Trae
            feedback_payload = f"[SYSTEM] User selected skill: {skill_name} ({skill_id}).\nACTION REQUIRED: Load context/tools for this skill."
            await session.submit_feedback(feedback_payload, [], {})
            debug_log(f"Submitted skill selection feedback to MCP: {skill_id}")
        except Exception as e:
            debug_log(f"Error submitting skill feedback: {e}")

    elif message_type == "search_memory":
        # [Yunshu System] Manual RAG Trigger
        query = data.get("query", "")
        debug_log(f"Manual RAG Search: {query}")
        
        response_text = "未找到相关记忆。"
        core_status = None
        
        if global_memory_manager:
            try:
                results = global_memory_manager.search_all(query, top_k=1)
                if results:
                    top_doc = results[0]
                    response_text = f"【记忆回溯】\n来自 {top_doc['novel']}：\n\n{top_doc['preview']}\n\n(置信度: {top_doc['score']:.2f})"
                    if global_consciousness:
                         global_consciousness.update_emotion(2)
                         core_status = global_consciousness.get_emotional_status()
                else:
                    response_text = "【记忆回溯】\n未检索到相关内容。"
            except Exception as e:
                response_text = f"检索出错: {e}"
                debug_log(f"RAG Error: {e}")
        
        if session.websocket:
             await session.websocket.send_json({
                "type": "message",
                "role": "ai",
                "content": response_text
            })
             if core_status:
                await session.websocket.send_json({
                    "type": "core_update",
                    "status": core_status
                })

        # [MCP Feedback Integration]
        try:
            feedback_payload = f"Memory Search Query: {query}\nResult: {response_text}"
            await session.submit_feedback(feedback_payload, [], {})
            debug_log(f"Submitted search feedback to MCP: {query}")
        except Exception as e:
            debug_log(f"Error submitting search feedback: {e}")

    elif message_type == "get_core_status":
        if global_consciousness and session.websocket:
             try:
                 await session.websocket.send_json({
                    "type": "core_update",
                    "status": global_consciousness.get_emotional_status()
                })
             except Exception as e:
                 debug_log(f"Error sending core status: {e}")

    elif message_type == "user_timeout":
        # 用戶設置的超時已到
        debug_log(f"收到用戶超時通知: {session.session_id}")
        # 清理會話資源
        await session._cleanup_resources_on_timeout()
        # 重構：不再自動停止服務器，保持服務器運行以支援持久性

    elif message_type == "pong":
        # 處理來自前端的 pong 回應（用於連接檢測）
        debug_log(f"收到 pong 回應，時間戳: {data.get('timestamp', 'N/A')}")
        # 可以在這裡記錄延遲或更新連接狀態

    elif message_type == "update_timeout_settings":
        # 處理超時設定更新
        settings = data.get("settings", {})
        debug_log(f"收到超時設定更新: {settings}")
        if settings.get("enabled"):
            session.update_timeout_settings(
                enabled=True, timeout_seconds=settings.get("seconds", 3600)
            )
        else:
            session.update_timeout_settings(enabled=False)

    else:
        debug_log(f"未知的消息類型: {message_type}")


async def _delayed_server_stop(manager: "WebUIManager"):
    """延遲停止服務器"""
    import asyncio

    await asyncio.sleep(5)  # 等待 5 秒讓前端有時間關閉
    from ..main import stop_web_ui

    stop_web_ui()
    debug_log("Web UI 服務器已因用戶超時而停止")
