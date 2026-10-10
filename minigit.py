import os
import sys
import json
import hashlib
import shutil
from datetime import datetime

# DIR names
REPO_DIR = ".minigit"
OBJECTS_DIR = os.path.join(REPO_DIR, "objects")
COMMITS_DIR = os.path.join(REPO_DIR, "commits")
HEAD_FILE = os.path.join(REPO_DIR, "HEAD")

def hash_file(filepath):
    """Generate SHA-1 hash for file contents."""
    sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()

def cmd_init():
    if os.path.exists(REPO_DIR):
        print("Repository already initialized.")
        return

    os.makedirs(OBJECTS_DIR)
    os.makedirs(COMMITS_DIR)
    
    # Initialize HEAD to empty
    with open(HEAD_FILE, "w") as f:
        f.write("")

    print("Initialized empty minigit repository.")

def cmd_commit(message):
    if not os.path.exists(REPO_DIR):
        print("Error: Not a minigit repository. Run 'init' first.")
        return

    # Gather all files in the project directory
    file_map = {}
    for root, dirs, files in os.walk("."):
        # Skip the .minigit folder itself
        if REPO_DIR in root:
            continue
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.normpath(full_path)
            
            # Hash file and save to objects folder
            file_hash = hash_file(full_path)
            dest_path = os.path.join(OBJECTS_DIR, file_hash)
            
            if not os.path.exists(dest_path):
                shutil.copyfile(full_path, dest_path)
                
            file_map[rel_path] = file_hash

    # Get parent commit from HEAD
    parent_commit = ""
    if os.path.exists(HEAD_FILE):
        with open(HEAD_FILE, "r") as f:
            parent_commit = f.read().strip()

    # Create commit metadata
    commit_data = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "parent": parent_commit,
        "files": file_map
    }

    # Generate a unique commit ID based on content
    commit_id = hashlib.sha1(json.dumps(commit_data).encode()).hexdigest()[:8]
    commit_path = os.path.join(COMMITS_DIR, f"{commit_id}.json")

    with open(commit_path, "w") as f:
        json.dump(commit_data, f, indent=4)

    # 4. Update HEAD pointer
    with open(HEAD_FILE, "w") as f:
        f.write(commit_id)

    print(f"Committed successfully! Commit ID: {commit_id}")

def cmd_log():
    if not os.path.exists(REPO_DIR):
        print("Error: Not a minigit repository.")
        return

    if not os.path.exists(HEAD_FILE):
        print("No commits yet.")
        return

    with open(HEAD_FILE, "r") as f:
        current_commit_id = f.read().strip()

    if not current_commit_id:
        print("No commits yet.")
        return

    while current_commit_id:
        commit_path = os.path.join(COMMITS_DIR, f"{current_commit_id}.json")
        if not os.path.exists(commit_path):
            break

        with open(commit_path, "r") as f:
            data = json.load(f)

        print(f"Commit:  {current_commit_id}")
        print(f"Date:    {data['timestamp']}")
        print(f"Message: {data['message']}\n")

        current_commit_id = data.get("parent", "")

def cmd_checkout(commit_id):
    commit_path = os.path.join(COMMITS_DIR, f"{commit_id}.json")
    if not os.path.exists(commit_path):
        print(f"Error: Commit {commit_id} not found.")
        return

    with open(commit_path, "r") as f:
        data = json.load(f)

    # Restore files from objects database
    for rel_path, file_hash in data["files"].items():
        src_path = os.path.join(OBJECTS_DIR, file_hash)
        os.makedirs(os.path.dirname(rel_path), exist_ok=True)
        
        if os.path.exists(src_path):
            shutil.copyfile(src_path, rel_path)

    # Update HEAD to point to this checked-out commit
    with open(HEAD_FILE, "w") as f:
        f.write(commit_id)

    print(f"Checked out commit {commit_id}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python minigit.py <command> [<args>]")
        print("Commands: init, commit <msg>, log, checkout <commit_id>")
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "init":
        cmd_init()
    elif command == "commit":
        if len(sys.argv) < 3:
            print("Error: Commit message required. Example: python minigit.py commit \"my message\"")
            sys.exit(1)
        cmd_commit(sys.argv[2])
    elif command == "log":
        cmd_log()
    elif command == "checkout":
        if len(sys.argv) < 3:
            print("Error: Commit ID required. Example: python minigit.py checkout abc12345")
            sys.exit(1)
        cmd_checkout(sys.argv[2])
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()