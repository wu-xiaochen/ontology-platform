#!/usr/bin/env python3
"""
自动监督脚本 - 确保团队任务持续执行
"""

import os
import json
import time
from datetime import datetime

TEAM_DIR = "/Users/xiaochenwu/.openclaw/workspace/ontology-platform"
LOG_FILE = f"{TEAM_DIR}/logs/supervisor.log"

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line.strip())

def check_workspace():
    """检查工作区产出"""
    log("=== 检查工作区产出 ===")
    
    dirs = ["ceo", "pm", "cto", "domain_expert", "reasoner", "consultant"]
    outputs = {}
    
    for d in dirs:
        path = f"{TEAM_DIR}/{d}"
        files = os.listdir(path) if os.path.exists(path) else []
        # 过滤隐藏文件
        files = [f for f in files if not f.startswith('.')]
        outputs[d] = files
        
        # 检查每个文件的大小
        for f in files:
            fpath = f"{path}/{f}"
            size = os.path.getsize(fpath)
            log(f"  {d}/{f}: {size} bytes")
    
    return outputs

def get_subagent_sessions():
    """获取当前运行的subagent"""
    log("=== 检查Subagent状态 ===")
    # 使用sessions_list API
    import subprocess
    result = subprocess.run(
        ["openclaw", "sessions", "list", "--active"],
        capture_output=True, text=True
    )
    log(result.stdout[:500] if result.stdout else "No sessions")
    return result.stdout

def main():
    log("启动自动监督...")
    
    while True:
        try:
            # 检查产出
            outputs = check_workspace()
            
            # 统计
            total_files = sum(len(v) for v in outputs.values())
            log(f"总产出文件: {total_files}")
            
            # 检查是否有空目录需要任务
            empty_dirs = [k for k, v in outputs.items() if len(v) == 0]
            if empty_dirs:
                log(f"警告: 空目录 {empty_dirs}")
            
            log("---")
            
        except Exception as e:
            log(f"Error: {e}")
        
        time.sleep(60)  # 每分钟检查

if __name__ == "__main__":
    main()
