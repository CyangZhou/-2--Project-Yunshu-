import sys
import os
import warnings
import io

# =======================================================
# 云舒系统 MCP 纯 Python 启动脚本 (终极净土版)
# 作用：
# 1. 强制 stderr 重定向到日志文件
# 2. 劫持 stdout，只允许 JSON 数据通过，其他一律进日志
# =======================================================

class StdoutFilter(io.TextIOBase):
    def __init__(self, real_stdout, log_file):
        # Initialize TextIOWrapper with a dummy buffer, but we won't use it much
        # We need to satisfy TextIOWrapper's init if we inherit from it
        # But actually, inheriting from TextIOWrapper is risky because it expects a buffer.
        # Let's just inherit from object or io.TextIOBase
        self.real_stdout = real_stdout
        self.log_file = log_file
        
    @property
    def buffer(self):
        # Return the underlying buffer of real stdout, or a dummy one
        # Some libraries might try to write bytes to .buffer
        return getattr(self.real_stdout, 'buffer', None)

    @property
    def encoding(self):
        return 'utf-8'

    def write(self, s):
        if not s:
            return
            
        # 简单启发式：只有以 '{' 开头的行才可能是 JSON-RPC
        # 注意：这可能有点过于严格，但对于 MCP 握手来说是安全的。
        # FastMCP 可能分多次 write，所以这需要更复杂的缓冲逻辑？
        # 不，通常 print 或 sys.stdout.write 是一次性写入完整内容的，
        # 或者是按行缓冲。
        # 为了安全起见，我们检查 stripped string。
        
        # 实际上，FastMCP 使用 starlette/uvicorn，可能会有复杂的输出。
        # 但我们最关心的是握手。
        # 如果是 JSON，通常整行都是。
        
        clean_s = s.strip()
        # 放行 JSON、协议头和纯空白字符（保留协议格式）
        if not clean_s or clean_s.startswith('{') or clean_s.startswith('Content-Length:'):
            try:
                return self.real_stdout.write(s)
            except Exception as e:
                self.log_file.write(f"[STDOUT FILTER ERROR] {e}\n")
        else:
            # Divert to stderr log
            # Avoid logging empty newlines alone to save space
            if clean_s:
                self.log_file.write(f"[STDOUT INTERCEPTED] {clean_s}\n")
            
    def flush(self):
        try:
            self.real_stdout.flush()
            self.log_file.flush()
        except:
            pass
            
    # Proxy other methods if needed
    def isatty(self):
        return False

def run():
    # 1. 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(project_root, "mcp_stderr.log")

    # 2. 核弹级 stderr 重定向 (os.dup2)
    try:
        log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.dup2(log_fd, 2)
        os.close(log_fd)
        sys.stderr = os.fdopen(2, "w", encoding="utf-8", buffering=1)
    except Exception:
        pass

    # 3. 强力屏蔽 Python 警告
    os.environ["PYTHONWARNINGS"] = "ignore"
    warnings.simplefilter("ignore")

    # 4. Stdout 劫持 (Filter)
    # 保存原始 stdout
    original_stdout = sys.stdout
    
    # 启用过滤器
    # 注意：sys.stderr 已经被重定向到日志文件了，所以我们可以安全地把拦截到的内容写给它
    sys.stdout = StdoutFilter(original_stdout, sys.stderr)

    # 5. 设置环境变量
    os.environ["MCP_DEBUG"] = "false"  # 强制关闭调试
    components_dir = os.path.join(project_root, "components", "mcp-feedback-enhanced")
    if components_dir not in sys.path:
        sys.path.insert(0, components_dir)

    # 6. 启动服务器
    try:
        from mcp_feedback_enhanced.server import main
        main()
    except ImportError as e:
        sys.stderr.write(f"Import Error: {e}\n")
    except Exception as e:
        sys.stderr.write(f"Runtime Error: {e}\n")

if __name__ == "__main__":
    run()
