#!/usr/bin/env python3
"""
Verification script to check if the StorySign Platform setup is complete
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - MISSING")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists and print status"""
    if Path(dirpath).is_dir():
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} - MISSING")
        return False

def main():
    """Main verification function"""
    print("🔍 Verifying StorySign Platform setup...\n")
    
    all_good = True
    
    # Check main directories
    print("📁 Directory Structure:")
    all_good &= check_directory_exists("backend", "Backend directory")
    all_good &= check_directory_exists("frontend", "Frontend directory")
    all_good &= check_directory_exists("frontend/src", "Frontend source directory")
    all_good &= check_directory_exists("frontend/public", "Frontend public directory")
    
    print("\n📄 Backend Files:")
    all_good &= check_file_exists("backend/environment.yml", "Conda environment file")
    all_good &= check_file_exists("backend/requirements.txt", "Python requirements")
    all_good &= check_file_exists("backend/dev_server.py", "Development server script")
    all_good &= check_file_exists("backend/.gitignore", "Backend gitignore")
    all_good &= check_file_exists("backend/README.md", "Backend README")
    
    print("\n📄 Frontend Files:")
    all_good &= check_file_exists("frontend/package.json", "NPM package configuration")
    all_good &= check_file_exists("frontend/public/electron.js", "Electron main process")
    all_good &= check_file_exists("frontend/public/index.html", "HTML template")
    all_good &= check_file_exists("frontend/src/index.js", "React entry point")
    all_good &= check_file_exists("frontend/src/App.js", "Main React component")
    all_good &= check_file_exists("frontend/src/App.css", "App styles")
    all_good &= check_file_exists("frontend/.gitignore", "Frontend gitignore")
    
    print("\n📄 Project Files:")
    all_good &= check_file_exists("README.md", "Project README")
    all_good &= check_file_exists("setup_dev.sh", "Development setup script")
    all_good &= check_file_exists(".gitignore", "Git ignore file")
    all_good &= check_file_exists(".gitattributes", "Git attributes file")
    all_good &= check_file_exists("LICENSE", "License file")
    all_good &= check_file_exists("CONTRIBUTING.md", "Contributing guidelines")
    all_good &= check_file_exists("CHANGELOG.md", "Changelog")
    all_good &= check_file_exists(".editorconfig", "Editor configuration")
    all_good &= check_file_exists("pyproject.toml", "Python project configuration")
    all_good &= check_file_exists(".nvmrc", "Node.js version file")
    
    print("\n📁 GitHub Templates:")
    all_good &= check_directory_exists(".github", "GitHub directory")
    all_good &= check_file_exists(".github/ISSUE_TEMPLATE/bug_report.md", "Bug report template")
    all_good &= check_file_exists(".github/ISSUE_TEMPLATE/feature_request.md", "Feature request template")
    all_good &= check_file_exists(".github/pull_request_template.md", "Pull request template")
    all_good &= check_file_exists(".github/workflows/ci.yml", "CI/CD workflow")
    
    print("\n" + "="*50)
    if all_good:
        print("🎉 All files and directories are present!")
        print("✅ Project structure setup is COMPLETE")
        print("\nNext steps:")
        print("1. Run ./setup_dev.sh to install dependencies")
        print("2. Start backend: cd backend && conda activate storysign-backend && python dev_server.py")
        print("3. Start frontend: cd frontend && npm run electron-dev")
    else:
        print("❌ Some files or directories are missing!")
        print("Please check the setup and try again.")
        sys.exit(1)

if __name__ == "__main__":
    # Change to the StorySign_Platform directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    main()