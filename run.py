import os
import shutil
import subprocess
import sys


def clear_pycache(project_root: str) -> int:
    removed_count = 0
    for current_root, dirs, _ in os.walk(project_root):
        if "__pycache__" in dirs:
            pycache_dir = os.path.join(current_root, "__pycache__")
            shutil.rmtree(pycache_dir, ignore_errors=True)
            dirs.remove("__pycache__")
            removed_count += 1
    return removed_count


project_root = os.path.dirname(os.path.abspath(__file__))
removed_count = clear_pycache(project_root)
if removed_count > 0:
    print(f"Removed {removed_count} __pycache__ directories.")
else:
    print("No __pycache__ directories found.")

env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"

cmd = [sys.executable, "manage.py", "runserver"]
subprocess.run(cmd, env=env)
