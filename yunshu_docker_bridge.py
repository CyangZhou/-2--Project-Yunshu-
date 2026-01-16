import os
import sys
import subprocess
import time
import threading
import webbrowser
import signal

# Configuration
CONTAINER_NAME = "yunshu-web"
WEB_UI_URL = "http://localhost:8765"

# Docker executable path fallback
DOCKER_CMD = "docker"

def find_docker():
    """Find docker executable path"""
    global DOCKER_CMD
    
    # 1. Try default command
    try:
        subprocess.run(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        pass
        
    # 2. Try common installation paths
    common_paths = [
        r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe" # This is the GUI, not CLI, but sometimes helpful to know
    ]
    
    for path in common_paths:
        if os.path.exists(path) and path.endswith("bin\\docker.exe"):
            DOCKER_CMD = path
            return True
            
    return False

def debug_log(msg):
    """Log to stderr so Trae can see it but it doesn't interfere with MCP stdio"""
    sys.stderr.write(f"[Bridge] {msg}\n")
    sys.stderr.flush()

def ensure_docker_running():
    """Ensure the Docker container is up and running"""
    if not find_docker():
        debug_log("WARNING: Docker executable not found in PATH or common locations.")
        # Proceeding anyway, hoping for the best or that DOCKER_CMD works
    
    try:
        # Check if container is running
        result = subprocess.run(
            [DOCKER_CMD, "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "true" in result.stdout.lower():
            debug_log("Container is already running.")
            return True
            
        debug_log("Container not running. Starting via docker-compose...")
        # Try to start using docker-compose (assuming it's in the same dir as docker)
        dc_cmd = "docker-compose"
        if os.path.isabs(DOCKER_CMD):
             dc_path = os.path.join(os.path.dirname(DOCKER_CMD), "docker-compose.exe")
             if os.path.exists(dc_path):
                 dc_cmd = dc_path
                 
        subprocess.run([dc_cmd, "up", "-d"], check=True, stderr=sys.stderr, stdout=sys.stderr)
        
        # Wait a bit for it to be ready
        time.sleep(2)
        return True
    except Exception as e:
        debug_log(f"Error ensuring Docker is running: {e}")
        return False

def open_browser_delayed():
    """Open browser after a short delay to ensure server is ready"""
    time.sleep(3)
    debug_log(f"Opening Web UI at {WEB_UI_URL}")
    webbrowser.open(WEB_UI_URL)

def main():
    debug_log("Starting Yunshu Docker Bridge...")
    
    if not ensure_docker_running():
        debug_log("Failed to start Docker container. Please check Docker Desktop.")
        sys.exit(1)

    # Launch browser in a separate thread
    threading.Thread(target=open_browser_delayed, daemon=True).start()

    # Construct the docker exec command
    # We execute the python module inside the container
    # -i: Keep stdin open
    # We don't use -t (tty) because MCP protocol relies on clean pipes
    cmd = [
        DOCKER_CMD, "exec", "-i", 
        CONTAINER_NAME, 
        "python", "-m", "mcp_feedback_enhanced"
    ]
    
    debug_log(f"Executing: {' '.join(cmd)}")
    
    # Start the process, connecting stdin/stdout to this script's stdin/stdout
    try:
        # Popen allows us to bridge the streams
        process = subprocess.Popen(
            cmd,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        # Wait for the process to complete (it should run until Trae kills it)
        process.wait()
        
    except KeyboardInterrupt:
        debug_log("Bridge interrupted.")
    except Exception as e:
        debug_log(f"Bridge error: {e}")
    finally:
        debug_log("Bridge exiting.")

if __name__ == "__main__":
    main()
