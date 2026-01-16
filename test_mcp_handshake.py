import subprocess
import sys
import os
import json
import time

def test_mcp_server():
    python_exe = r"D:\新建文件夹\python.exe"
    script_path = r"E:\trae的工作区\01云舒系统02版\run_mcp.py"
    
    print(f"Testing MCP Server...")
    print(f"Python: {python_exe}")
    print(f"Script: {script_path}")
    
    # Start the process
    try:
        process = subprocess.Popen(
            [python_exe, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False  # Use binary mode to catch raw output
        )
    except Exception as e:
        print(f"FAILED to start process: {e}")
        return

    print("Process started. Waiting 2 seconds for any uninvited output...")
    time.sleep(2)
    
    # Check if process is still alive
    if process.poll() is not None:
        print(f"Process DIED immediately with return code {process.returncode}")
        stdout, stderr = process.communicate()
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr.decode('utf-8', errors='replace')}")
        return

    # Check for initial garbage on stdout
    # We use peek or non-blocking read if possible, but for simplicity in this script:
    # We'll try to read a small chunk. If it blocks, it means no output (Good).
    # But read() blocks.
    # So we'll skip reading for now and try to send handshake.
    
    handshake = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-script", "version": "1.0"}
        }
    }
    
    input_data = json.dumps(handshake).encode('utf-8') + b"\n"
    print(f"Sending handshake: {input_data}")
    
    try:
        stdout_data, stderr_data = process.communicate(input=input_data, timeout=5)
        
        print("--- STDOUT (Server Response) ---")
        print(stdout_data.decode('utf-8', errors='replace'))
        print("--------------------------------")
        
        print("--- STDERR (Logs) ---")
        print(stderr_data.decode('utf-8', errors='replace')[:500] + "...") # Show first 500 chars
        print("--------------------------------")
        
        if b"jsonrpc" in stdout_data:
            print("SUCCESS: Received JSON-RPC response.")
        else:
            print("FAILURE: No JSON-RPC response found.")
            
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Server did not respond in 5 seconds.")
        process.kill()
        stdout_data, stderr_data = process.communicate()
        print("--- STDOUT (Partial) ---")
        print(stdout_data.decode('utf-8', errors='replace'))
        print("--- STDERR (Partial) ---")
        print(stderr_data.decode('utf-8', errors='replace'))

if __name__ == "__main__":
    test_mcp_server()
