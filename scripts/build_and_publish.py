#!/usr/bin/env python3
"""
Automated build and publish script for SFTP GUI Manager
This script:
1. Updates version numbers
2. Builds the application
3. Creates a Git tag
4. Pushes to GitHub
5. Creates a GitHub release
"""
import os
import sys
import json
import re
import subprocess
import argparse
import shutil
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class BuildAndPublish:
    """Handles the build and publish process"""
    
    def __init__(self, version=None, dry_run=False, skip_build=False, skip_git=False):
        """Initialize build and publish process
        
        Args:
            version: Version to build (format: x.y.z)
            dry_run: If True, don't actually push to Git
            skip_build: If True, skip the build process
            skip_git: If True, skip Git operations
        """
        self.version = version
        self.dry_run = dry_run
        self.skip_build = skip_build
        self.skip_git = skip_git
        
        self.project_root = project_root
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        
        # Git configuration
        self.git_repo = "https://github.com/DenisToxic/SFTP"
        self.git_username = None
        self.git_token = None
        
        # Files to update version in
        self.version_files = [
            self.project_root / "version.json",
            self.project_root / "core" / "version_manager.py",
            self.project_root / "version_info.txt"
        ]
        
        # Output files
        self.exe_file = self.dist_dir / "SFTPGUIManager.exe"
        self.zip_file = None
        self.installer_file = None
        
        # Load environment variables
        self._load_env_vars()
        
    def _load_env_vars(self):
        """Load environment variables"""
        self.git_username = os.environ.get("GIT_USERNAME")
        self.git_token = os.environ.get("GIT_TOKEN")
        
        # Check if we have Git credentials when needed
        if not self.skip_git and not self.dry_run:
            if not self.git_username or not self.git_token:
                print("⚠️  Warning: GIT_USERNAME or GIT_TOKEN environment variables not set.")
                print("    Git operations that require authentication may fail.")
                print("    Set these variables or use --dry-run or --skip-git options.")
                
    def run(self):
        """Run the build and publish process"""
        print("🚀 SFTP GUI Manager - Build and Publish")
        print("=" * 50)
        
        # Validate and update version
        if not self._validate_and_update_version():
            return False
            
        # Build the application
        if not self.skip_build:
            if not self._build_application():
                return False
        else:
            print("Skipping build process...")
            
        # Git operations
        if not self.skip_git:
            if not self._git_operations():
                return False
        else:
            print("Skipping Git operations...")
            
        print("\n✅ Build and publish process completed successfully!")
        return True
        
    def _validate_and_update_version(self):
        """Validate and update version numbers
        
        Returns:
            True if successful, False otherwise
        """
        print("\n📋 Validating and updating version...")
        
        # Get current version if not specified
        if not self.version:
            current_version = self._get_current_version()
            if not current_version:
                print("❌ Failed to determine current version")
                return False
                
            # Auto-increment patch version
            version_parts = current_version.split('.')
            if len(version_parts) >= 3:
                version_parts[2] = str(int(version_parts[2]) + 1)
                self.version = '.'.join(version_parts)
                print(f"Auto-incrementing version: {current_version} -> {self.version}")
            else:
                print(f"❌ Invalid current version format: {current_version}")
                return False
                
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+$', self.version):
            print(f"❌ Invalid version format: {self.version}")
            print("   Version must be in format: x.y.z")
            return False
            
        # Update version in files
        if not self._update_version_in_files():
            return False
            
        print(f"✅ Version updated to {self.version}")
        return True
        
    def _get_current_version(self):
        """Get current version from version.json
        
        Returns:
            Current version string or None if not found
        """
        version_json = self.project_root / "version.json"
        if version_json.exists():
            try:
                with open(version_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("version")
            except Exception as e:
                print(f"❌ Failed to read version.json: {e}")
                
        return None
        
    def _update_version_in_files(self):
        """Update version in all relevant files
        
        Returns:
            True if successful, False otherwise
        """
        # Update version.json
        version_json = self.project_root / "version.json"
        try:
            if version_json.exists():
                with open(version_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                data["version"] = self.version
                data["release_date"] = datetime.now().isoformat()
                data["build_date"] = datetime.now().isoformat()
                
                with open(version_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                    
                print(f"✅ Updated {version_json}")
            else:
                print(f"⚠️  {version_json} not found, creating...")
                with open(version_json, 'w', encoding='utf-8') as f:
                    data = {
                        "version": self.version,
                        "release_date": datetime.now().isoformat(),
                        "build_date": datetime.now().isoformat()
                    }
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to update {version_json}: {e}")
            return False
            
        # Update version in version_manager.py
        version_manager_py = self.project_root / "core" / "version_manager.py"
        if version_manager_py.exists():
            try:
                with open(version_manager_py, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Replace version in CURRENT_VERSION
                new_content = re.sub(
                    r'CURRENT_VERSION\s*=\s*"[^"]+"',
                    f'CURRENT_VERSION = "{self.version}"',
                    content
                )
                
                with open(version_manager_py, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                print(f"✅ Updated {version_manager_py}")
            except Exception as e:
                print(f"❌ Failed to update {version_manager_py}: {e}")
                return False
                
        # Update version in version_info.txt
        version_info_txt = self.project_root / "version_info.txt"
        if version_info_txt.exists():
            try:
                with open(version_info_txt, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse version parts
                version_parts = self.version.split('.')
                if len(version_parts) >= 3:
                    major = int(version_parts[0])
                    minor = int(version_parts[1])
                    patch = int(version_parts[2])
                    build = 0
                    
                    # Replace version in filevers and prodvers
                    new_content = re.sub(
                        r'filevers=$$[^)]+$$',
                        f'filevers=({major}, {minor}, {patch}, {build})',
                        content
                    )
                    new_content = re.sub(
                        r'prodvers=$$[^)]+$$',
                        f'prodvers=({major}, {minor}, {patch}, {build})',
                        content
                    )
                    
                    # Replace version strings
                    new_content = re.sub(
                        r'StringStruct$$u\'FileVersion\', u\'[^\']+\'$$',
                        f'StringStruct(u\'FileVersion\', u\'{self.version}.0\')',
                        new_content
                    )
                    new_content = re.sub(
                        r'StringStruct$$u\'ProductVersion\', u\'[^\']+\'$$',
                        f'StringStruct(u\'ProductVersion\', u\'{self.version}.0\')',
                        new_content
                    )
                    
                    with open(version_info_txt, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
                    print(f"✅ Updated {version_info_txt}")
            except Exception as e:
                print(f"❌ Failed to update {version_info_txt}: {e}")
                return False
                
        return True
        
    def _build_application(self):
        """Build the application
        
        Returns:
            True if successful, False otherwise
        """
        print("\n🔨 Building application...")
        
        # Clean previous builds
        if self.build_dir.exists():
            print(f"Cleaning {self.build_dir}...")
            shutil.rmtree(self.build_dir)
            
        if self.dist_dir.exists():
            print(f"Cleaning {self.dist_dir}...")
            shutil.rmtree(self.dist_dir)
            
        # Run PyInstaller
        print("Running PyInstaller...")
        try:
            # Use main_onefile_fixed.spec if it exists
            spec_file = self.project_root / "main_onefile_fixed.spec"
            if not spec_file.exists():
                spec_file = self.project_root / "main_onefile.spec"
                
            if not spec_file.exists():
                print(f"❌ Spec file not found: {spec_file}")
                return False
                
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_file)
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=str(self.project_root))
            
            if result.returncode != 0:
                print("❌ PyInstaller build failed")
                return False
                
            # Check if executable was created
            if not self.exe_file.exists():
                print(f"❌ Executable not found: {self.exe_file}")
                return False
                
            print(f"✅ PyInstaller build successful: {self.exe_file}")
            
            # Create distribution package
            if not self._create_distribution_package():
                return False
                
            # Create installer
            if not self._create_installer():
                print("⚠️  Installer creation failed, continuing anyway...")
                
            return True
            
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False
            
    def _create_distribution_package(self):
        """Create distribution package
        
        Returns:
            True if successful, False otherwise
        """
        print("\n📦 Creating distribution package...")
        
        try:
            # Create package directory
            package_dir = self.dist_dir / f"SFTP_GUI_Manager_v{self.version}"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy executable
            shutil.copy2(self.exe_file, package_dir / "SFTPGUIManager.exe")
            
            # Create README
            readme_content = f"""SFTP GUI Manager v{self.version}

A modern, feature-rich SFTP client with integrated terminal support.

QUICK START:
1. Double-click SFTPGUIManager.exe
2. Enter your SSH connection details
3. Start managing your remote files!

FEATURES:
• Modern file browser with drag & drop support
• Integrated SSH terminal
• Edit remote files with your preferred editor
• Automatic file synchronization
• Progress tracking for large transfers
• Command shortcuts and automation
• Built-in update system

SYSTEM REQUIREMENTS:
• Windows 10 or later (64-bit)
• No additional software required

For support and updates:
https://github.com/DenisToxic/SFTP
"""
            
            with open(package_dir / "README.txt", 'w', encoding='utf-8') as f:
                f.write(readme_content)
                
            # Copy license if exists
            license_file = self.project_root / "LICENSE"
            if license_file.exists():
                shutil.copy2(license_file, package_dir / "LICENSE.txt")
                
            # Create ZIP archive
            zip_path = self.dist_dir / f"SFTP_GUI_Manager_v{self.version}"
            shutil.make_archive(str(zip_path), 'zip', str(package_dir))
            
            self.zip_file = Path(f"{zip_path}.zip")
            print(f"✅ Distribution package created: {package_dir}")
            print(f"✅ ZIP archive created: {self.zip_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create distribution package: {e}")
            return False
            
    def _create_installer(self):
        """Create installer
        
        Returns:
            True if successful, False otherwise
        """
        print("\n📦 Creating installer...")
        
        try:
            # Check if Inno Setup is available
            inno_paths = [
                r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"C:\Program Files\Inno Setup 6\ISCC.exe",
            ]
            
            iscc_exe = None
            for path in inno_paths:
                if os.path.exists(path):
                    iscc_exe = path
                    break
                    
            if not iscc_exe:
                print("⚠️  Inno Setup not found, skipping installer creation")
                return False
                
            # Create installer script
            installer_dir = self.project_root / "installer"
            installer_dir.mkdir(exist_ok=True)
            
            output_dir = installer_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            iss_file = installer_dir / "setup.iss"
            
            iss_content = f'''[Setup]
AppId={{{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}}}
AppName=SFTP GUI Manager
AppVersion={self.version}
AppPublisher=SFTP Development Team
AppPublisherURL=https://github.com/DenisToxic/SFTP
DefaultDirName={{autopf}}\\SFTP
DefaultGroupName=SFTP GUI Manager
OutputDir={output_dir}
OutputBaseFilename=SFTPGUIManager_v{self.version}_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={{app}}\\SFTPGUIManager.exe

[Files]
Source: "{self.exe_file}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\SFTP GUI Manager"; Filename: "{{app}}\\SFTPGUIManager.exe"
Name: "{{autodesktop}}\\SFTP GUI Manager"; Filename: "{{app}}\\SFTPGUIManager.exe"

[Registry]
Root: HKLM; Subkey: "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\SFTPGUIManager.exe"; ValueType: string; ValueName: ""; ValueData: "{{app}}\\SFTPGUIManager.exe"; Flags: uninsdeletekey

[Run]
Filename: "{{app}}\\SFTPGUIManager.exe"; Description: "Launch SFTP GUI Manager"; Flags: nowait postinstall skipifsilent

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  Exec('taskkill.exe', '/F /IM SFTPGUIManager.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(1000);
end;
'''
            
            with open(iss_file, 'w', encoding='utf-8') as f:
                f.write(iss_content)
                
            # Run Inno Setup
            print(f"Running Inno Setup: {iscc_exe} {iss_file}")
            result = subprocess.run([iscc_exe, str(iss_file)], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Inno Setup failed: {result.stderr}")
                return False
                
            # Find installer file
            installer_file = list(output_dir.glob(f"SFTPGUIManager_v{self.version}_Setup.exe"))
            if installer_file:
                self.installer_file = installer_file[0]
                print(f"✅ Installer created: {self.installer_file}")
                return True
            else:
                print("❌ Installer file not found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create installer: {e}")
            return False
            
    def _git_operations(self):
        """Perform Git operations
        
        Returns:
            True if successful, False otherwise
        """
        print("\n🔄 Performing Git operations...")
        
        # Check if Git is available
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except Exception:
            print("❌ Git not found or not in PATH")
            return False
            
        try:
            # Check if we're in a Git repository
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0 or result.stdout.strip() != "true":
                print("❌ Not in a Git repository")
                return False
                
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True
            )
            
            current_branch = result.stdout.strip()
            print(f"Current branch: {current_branch}")
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True
            )
            
            if result.stdout.strip():
                print("Uncommitted changes detected, committing...")
                
                # Add all changes
                subprocess.run(["git", "add", "."], check=True)
                
                # Commit changes
                commit_message = f"Version {self.version} - Automated release commit"
                if self.dry_run:
                    print(f"[DRY RUN] Would commit with message: {commit_message}")
                else:
                    subprocess.run(
                        ["git", "commit", "-m", commit_message],
                        check=True
                    )
                    print(f"✅ Committed changes with message: {commit_message}")
            else:
                print("No uncommitted changes")
                
            # Create tag
            tag_name = f"v{self.version}"
            tag_message = f"Release {self.version}"
            
            if self.dry_run:
                print(f"[DRY RUN] Would create tag: {tag_name}")
            else:
                try:
                    subprocess.run(
                        ["git", "tag", "-a", tag_name, "-m", tag_message],
                        check=True
                    )
                    print(f"✅ Created tag: {tag_name}")
                except subprocess.CalledProcessError:
                    # Tag might already exist
                    print(f"⚠️  Tag {tag_name} might already exist, continuing...")
                    
            # Push changes
            if self.dry_run:
                print("[DRY RUN] Would push changes and tags")
            else:
                # Push commits
                print("Pushing commits...")
                subprocess.run(
                    ["git", "push", "origin", current_branch],
                    check=True
                )
                
                # Push tags
                print("Pushing tags...")
                subprocess.run(
                    ["git", "push", "origin", "--tags"],
                    check=True
                )
                
                print("✅ Pushed changes and tags")
                
            # Create GitHub release
            if self.git_username and self.git_token and not self.dry_run:
                self._create_github_release(tag_name)
                
            return True
            
        except Exception as e:
            print(f"❌ Git operations failed: {e}")
            return False
            
    def _create_github_release(self, tag_name):
        """Create GitHub release
        
        Args:
            tag_name: Tag name for the release
        """
        print("\n🌐 Creating GitHub release...")
        
        try:
            # Check if we have the GitHub CLI
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            has_gh_cli = result.returncode == 0
            
            if has_gh_cli:
                return self._create_release_with_gh_cli(tag_name)
            else:
                print("GitHub CLI not found, using API...")
                return self._create_release_with_api(tag_name)
                
        except Exception as e:
            print(f"❌ Failed to create GitHub release: {e}")
            return False
            
    def _create_release_with_gh_cli(self, tag_name):
        """Create GitHub release using GitHub CLI
        
        Args:
            tag_name: Tag name for the release
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create release notes file
            notes_file = self.project_root / "release_notes.md"
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write(f"# SFTP GUI Manager {self.version}\n\n")
                f.write(f"Release date: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write("## Changes\n\n")
                f.write("- Bug fixes and improvements\n")
                f.write("- Updated dependencies\n\n")
                f.write("## Installation\n\n")
                f.write("- Download the installer and run it\n")
                f.write("- Or download the ZIP file and extract it to a location of your choice\n")
                
            # Create release
            cmd = [
                "gh", "release", "create", tag_name,
                "--title", f"SFTP GUI Manager {self.version}",
                "--notes-file", str(notes_file)
            ]
            
            # Add assets if they exist
            if self.zip_file and self.zip_file.exists():
                cmd.extend(["--attach", str(self.zip_file)])
                
            if self.installer_file and self.installer_file.exists():
                cmd.extend(["--attach", str(self.installer_file)])
                
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up notes file
            if notes_file.exists():
                notes_file.unlink()
                
            if result.returncode == 0:
                print(f"✅ Created GitHub release: {tag_name}")
                print(f"Release URL: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ Failed to create GitHub release: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create GitHub release with CLI: {e}")
            return False
            
    def _create_release_with_api(self, tag_name):
        """Create GitHub release using GitHub API
        
        Args:
            tag_name: Tag name for the release
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import requests
            
            # Check if we have credentials
            if not self.git_username or not self.git_token:
                print("❌ GitHub credentials not available")
                return False
                
            # Extract owner and repo from git_repo URL
            repo_parts = self.git_repo.split('/')
            owner = repo_parts[-2]
            repo = repo_parts[-1]
            
            # Create release
            url = f"https://api.github.com/repos/{owner}/{repo}/releases"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {self.git_token}"
            }
            
            data = {
                "tag_name": tag_name,
                "name": f"SFTP GUI Manager {self.version}",
                "body": f"# SFTP GUI Manager {self.version}\n\n"
                       f"Release date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                       "## Changes\n\n"
                       "- Bug fixes and improvements\n"
                       "- Updated dependencies\n\n"
                       "## Installation\n\n"
                       "- Download the installer and run it\n"
                       "- Or download the ZIP file and extract it to a location of your choice\n",
                "draft": False,
                "prerelease": False
            }
            
            print(f"Creating release for {owner}/{repo}...")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                release_data = response.json()
                release_id = release_data["id"]
                release_url = release_data["html_url"]
                
                print(f"✅ Created GitHub release: {release_url}")
                
                # Upload assets
                if self.zip_file and self.zip_file.exists():
                    self._upload_asset_to_release(release_id, self.zip_file, owner, repo)
                    
                if self.installer_file and self.installer_file.exists():
                    self._upload_asset_to_release(release_id, self.installer_file, owner, repo)
                    
                return True
            else:
                print(f"❌ Failed to create GitHub release: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Failed to create GitHub release with API: {e}")
            return False
            
    def _upload_asset_to_release(self, release_id, asset_path, owner, repo):
        """Upload asset to GitHub release
        
        Args:
            release_id: Release ID
            asset_path: Path to asset file
            owner: Repository owner
            repo: Repository name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import requests
            
            url = f"https://uploads.github.com/repos/{owner}/{repo}/releases/{release_id}/assets"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {self.git_token}",
                "Content-Type": "application/octet-stream"
            }
            
            params = {
                "name": asset_path.name
            }
            
            print(f"Uploading asset: {asset_path.name}...")
            with open(asset_path, 'rb') as f:
                response = requests.post(url, headers=headers, params=params, data=f)
                
            if response.status_code == 201:
                print(f"✅ Uploaded asset: {asset_path.name}")
                return True
            else:
                print(f"❌ Failed to upload asset: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Failed to upload asset: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build and publish SFTP GUI Manager")
    parser.add_argument("--version", help="Version to build (format: x.y.z)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually push to Git")
    parser.add_argument("--skip-build", action="store_true", help="Skip the build process")
    parser.add_argument("--skip-git", action="store_true", help="Skip Git operations")
    
    args = parser.parse_args()
    
    builder = BuildAndPublish(
        version=args.version,
        dry_run=args.dry_run,
        skip_build=args.skip_build,
        skip_git=args.skip_git
    )
    
    success = builder.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
