#!/usr/bin/env python3
"""
Deployment Validation Script for StorySign Platform
Validates deployment configuration files and environment setup
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

class DeploymentValidator:
    """Validates deployment configuration and setup"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors = []
        self.warnings = []
        
    def validate_file_exists(self, file_path: Path, description: str) -> bool:
        """Check if a required file exists"""
        if file_path.exists():
            print_success(f"{description} exists: {file_path}")
            return True
        else:
            self.errors.append(f"{description} not found: {file_path}")
            print_error(f"{description} not found: {file_path}")
            return False
    
    def validate_yaml_file(self, file_path: Path, description: str) -> bool:
        """Validate YAML file syntax"""
        if not self.validate_file_exists(file_path, description):
            return False
        
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            print_success(f"{description} has valid YAML syntax")
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"{description} has invalid YAML syntax: {e}")
            print_error(f"{description} has invalid YAML syntax: {e}")
            return False
    
    def validate_json_file(self, file_path: Path, description: str) -> bool:
        """Validate JSON file syntax"""
        if not self.validate_file_exists(file_path, description):
            return False
        
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            print_success(f"{description} has valid JSON syntax")
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"{description} has invalid JSON syntax: {e}")
            print_error(f"{description} has invalid JSON syntax: {e}")
            return False
    
    def validate_render_config(self) -> bool:
        """Validate Render deployment configuration"""
        print_status("Validating Render configuration...")
        
        render_yaml = self.root_dir / "render.yaml"
        if not self.validate_yaml_file(render_yaml, "Render configuration"):
            return False
        
        # Load and validate content
        with open(render_yaml, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required fields
        if 'services' not in config:
            self.errors.append("render.yaml missing 'services' section")
            return False
        
        service = config['services'][0] if config['services'] else {}
        
        required_fields = ['type', 'name', 'env']
        for field in required_fields:
            if field not in service:
                self.errors.append(f"render.yaml missing required field: {field}")
        
        # Check for either buildCommand or startCommand (both are optional but at least one should exist)
        if 'buildCommand' not in service and 'startCommand' not in service:
            self.warnings.append("render.yaml should have either buildCommand or startCommand")
        
        # Check if Gunicorn is in start command
        start_command = service.get('startCommand', '')
        if 'gunicorn' not in start_command:
            self.warnings.append("Start command should use Gunicorn for production")
        
        # Check environment variables
        env_vars = service.get('envVars', [])
        required_env_vars = ['DATABASE_HOST', 'JWT_SECRET', 'GROQ_API_KEY']
        
        env_var_keys = [var.get('key') for var in env_vars if isinstance(var, dict)]
        for required_var in required_env_vars:
            if required_var not in env_var_keys:
                self.warnings.append(f"Missing environment variable in render.yaml: {required_var}")
        
        return True
    
    def validate_netlify_config(self) -> bool:
        """Validate Netlify deployment configuration"""
        print_status("Validating Netlify configuration...")
        
        netlify_toml = self.root_dir / "netlify.toml"
        if not self.validate_file_exists(netlify_toml, "Netlify configuration"):
            return False
        
        # Check _redirects file
        redirects_file = self.root_dir / "frontend" / "public" / "_redirects"
        self.validate_file_exists(redirects_file, "Netlify redirects file")
        
        return True
    
    def validate_frontend_config(self) -> bool:
        """Validate frontend configuration"""
        print_status("Validating frontend configuration...")
        
        frontend_dir = self.root_dir / "frontend"
        
        # Check package.json
        package_json = frontend_dir / "package.json"
        if not self.validate_json_file(package_json, "Frontend package.json"):
            return False
        
        # Load and check scripts
        with open(package_json, 'r') as f:
            package_data = json.load(f)
        
        scripts = package_data.get('scripts', {})
        required_scripts = ['build', 'build:production', 'test:ci', 'lint:ci']
        
        for script in required_scripts:
            if script not in scripts:
                self.warnings.append(f"Missing npm script: {script}")
        
        # Check environment files
        env_files = [
            (frontend_dir / ".env.example", "Environment variables example"),
            (frontend_dir / ".env.production", "Production environment variables")
        ]
        
        for env_file, description in env_files:
            self.validate_file_exists(env_file, description)
        
        return True
    
    def validate_backend_config(self) -> bool:
        """Validate backend configuration"""
        print_status("Validating backend configuration...")
        
        backend_dir = self.root_dir / "backend"
        
        # Check requirements.txt
        requirements_file = backend_dir / "requirements.txt"
        if not self.validate_file_exists(requirements_file, "Backend requirements.txt"):
            return False
        
        # Check if Gunicorn is in requirements
        with open(requirements_file, 'r') as f:
            requirements = f.read()
        
        if 'gunicorn' not in requirements.lower():
            self.errors.append("Gunicorn not found in requirements.txt")
        
        # Check main application files
        main_files = [
            (backend_dir / "main_api.py", "Main API application"),
            (backend_dir / "config.py", "Configuration module")
        ]
        
        for main_file, description in main_files:
            self.validate_file_exists(main_file, description)
        
        return True
    
    def validate_github_workflows(self) -> bool:
        """Validate GitHub Actions workflows"""
        print_status("Validating GitHub Actions workflows...")
        
        workflows_dir = self.root_dir / ".github" / "workflows"
        
        workflow_files = [
            (workflows_dir / "ci.yml", "CI workflow"),
            (workflows_dir / "deploy.yml", "Deployment workflow"),
            (workflows_dir / "preview.yml", "Preview deployment workflow"),
            (workflows_dir / "maintenance.yml", "Maintenance workflow")
        ]
        
        for workflow_file, description in workflow_files:
            self.validate_yaml_file(workflow_file, description)
        
        return True
    
    def validate_documentation(self) -> bool:
        """Validate deployment documentation"""
        print_status("Validating documentation...")
        
        doc_files = [
            (self.root_dir / "DEPLOYMENT.md", "Deployment guide"),
            (self.root_dir / "deploy.sh", "Deployment script")
        ]
        
        for doc_file, description in doc_files:
            self.validate_file_exists(doc_file, description)
        
        return True
    
    def check_node_version(self) -> bool:
        """Check Node.js version"""
        print_status("Checking Node.js version...")
        
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                major_version = int(version.lstrip('v').split('.')[0])
                
                if major_version >= 18:
                    print_success(f"Node.js version is compatible: {version}")
                    return True
                else:
                    self.warnings.append(f"Node.js version {version} is below recommended version 18")
                    return False
            else:
                self.warnings.append("Could not determine Node.js version")
                return False
        except (subprocess.SubprocessError, FileNotFoundError):
            self.warnings.append("Node.js not found or not accessible")
            return False
    
    def check_python_version(self) -> bool:
        """Check Python version"""
        print_status("Checking Python version...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            print_success(f"Python version is compatible: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.warnings.append(f"Python version {version.major}.{version.minor} is below recommended version 3.11")
            return False
    
    def run_validation(self) -> bool:
        """Run all validation checks"""
        print("🔍 StorySign Platform Deployment Validation")
        print("=" * 50)
        
        validation_steps = [
            ("System Requirements", [
                self.check_node_version,
                self.check_python_version
            ]),
            ("Configuration Files", [
                self.validate_render_config,
                self.validate_netlify_config,
                self.validate_frontend_config,
                self.validate_backend_config
            ]),
            ("CI/CD Configuration", [
                self.validate_github_workflows
            ]),
            ("Documentation", [
                self.validate_documentation
            ])
        ]
        
        all_passed = True
        
        for section_name, checks in validation_steps:
            print(f"\n📋 {section_name}")
            print("-" * 30)
            
            section_passed = True
            for check in checks:
                try:
                    if not check():
                        section_passed = False
                except Exception as e:
                    self.errors.append(f"Validation error in {check.__name__}: {e}")
                    section_passed = False
            
            if section_passed:
                print_success(f"{section_name} validation passed")
            else:
                print_error(f"{section_name} validation failed")
                all_passed = False
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Validation Summary")
        print("=" * 50)
        
        if self.errors:
            print_error(f"Found {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  ❌ {error}")
        
        if self.warnings:
            print_warning(f"Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  ⚠️ {warning}")
        
        if all_passed and not self.errors:
            print_success("🎉 All validation checks passed! Ready for deployment.")
            return True
        else:
            print_error("❌ Validation failed. Please fix the issues above before deploying.")
            return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Usage: python validate-deployment.py")
        print("\nValidates StorySign Platform deployment configuration.")
        print("Run this script from the project root directory.")
        return 0
    
    # Find project root
    current_dir = Path.cwd()
    
    # Look for project indicators
    if not (current_dir / "render.yaml").exists():
        print_error("Please run this script from the StorySign_Platform root directory")
        return 1
    
    validator = DeploymentValidator(current_dir)
    success = validator.run_validation()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())