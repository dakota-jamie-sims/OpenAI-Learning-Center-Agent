#!/usr/bin/env python3
"""
Build script for Dakota Content Generator Mac App
Creates a standalone .app bundle with embedded API keys
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def replace_api_keys(app_file, api_keys):
    """Replace placeholder API keys in the app file"""
    with open(app_file, 'r') as f:
        content = f.read()
    
    # Replace placeholders with actual keys
    for key, value in api_keys.items():
        placeholder = f"%%{key}%%"
        content = content.replace(placeholder, value)
    
    with open(app_file, 'w') as f:
        f.write(content)
    

def build_app(api_keys, app_name="Dakota Content Generator"):
    """Build the Mac app with PyInstaller"""
    
    # Paths
    project_root = Path(__file__).parent.parent
    mac_app_dir = Path(__file__).parent
    app_script = mac_app_dir / "dakota_mac_app.py"
    temp_script = mac_app_dir / "dakota_mac_app_temp.py"
    
    # Copy script and replace API keys
    shutil.copy(app_script, temp_script)
    replace_api_keys(temp_script, api_keys)
    
    # Prepare build directory
    build_dir = mac_app_dir / "build"
    dist_dir = mac_app_dir / "dist"
    
    # Clean previous builds
    shutil.rmtree(build_dir, ignore_errors=True)
    shutil.rmtree(dist_dir, ignore_errors=True)
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", app_name,
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(mac_app_dir),
        "--clean",
        "--noconfirm",
        
        # Mac-specific options
        "--osx-bundle-identifier", "com.dakota.contentgenerator",
        
        # Add the entire project as data
        f"--add-data={project_root}/src:src",
        f"--add-data={project_root}/scripts:scripts",
        f"--add-data={project_root}/data:data",
        
        # Hidden imports
        "--hidden-import=tkinter",
        "--hidden-import=openai",
        "--hidden-import=httpx",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=asyncio",
        "--hidden-import=tenacity",
        
        # Exclude unnecessary modules
        "--exclude-module=matplotlib",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        
        str(temp_script)
    ]
    
    # Add icon if available
    icon_path = mac_app_dir / "dakota_icon.icns"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    print(f"Building app with command: {' '.join(cmd)}")
    
    # Run PyInstaller
    result = subprocess.run(cmd, cwd=str(mac_app_dir))
    
    # Clean up temp file
    temp_script.unlink(missing_ok=True)
    
    if result.returncode != 0:
        print("Build failed!")
        return False
    
    print(f"\n✅ App built successfully!")
    print(f"📁 Location: {dist_dir / f'{app_name}.app'}")
    
    return True


def create_dmg(app_name="Dakota Content Generator"):
    """Create a DMG installer for distribution"""
    
    mac_app_dir = Path(__file__).parent
    dist_dir = mac_app_dir / "dist"
    app_path = dist_dir / f"{app_name}.app"
    dmg_path = dist_dir / f"{app_name.replace(' ', '-')}.dmg"
    
    if not app_path.exists():
        print("App not found. Build it first!")
        return False
    
    # Remove old DMG if exists
    dmg_path.unlink(missing_ok=True)
    
    # Create DMG
    cmd = [
        "hdiutil", "create",
        "-volname", app_name,
        "-srcfolder", str(app_path),
        "-ov",
        "-format", "UDZO",
        str(dmg_path)
    ]
    
    print(f"Creating DMG with command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("DMG creation failed!")
        return False
    
    print(f"\n✅ DMG created successfully!")
    print(f"📦 Location: {dmg_path}")
    print(f"📏 Size: {dmg_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return True


def main():
    """Main build process"""
    
    parser = argparse.ArgumentParser(description="Build Dakota Content Generator Mac App")
    parser.add_argument(
        "--openai-key",
        required=True,
        help="OpenAI API key to embed"
    )
    parser.add_argument(
        "--vector-store-id",
        required=True,
        help="Vector store ID to embed"
    )
    parser.add_argument(
        "--serper-key",
        required=True,
        help="Serper API key to embed"
    )
    parser.add_argument(
        "--dmg",
        action="store_true",
        help="Also create DMG installer"
    )
    parser.add_argument(
        "--name",
        default="Dakota Content Generator",
        help="App name (default: Dakota Content Generator)"
    )
    
    args = parser.parse_args()
    
    # Check for PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # API keys to embed
    api_keys = {
        "OPENAI_API_KEY": args.openai_key,
        "VECTOR_STORE_ID": args.vector_store_id,
        "SERPER_API_KEY": args.serper_key
    }
    
    print(f"🔨 Building {args.name}...")
    print("=" * 60)
    
    # Build the app
    if build_app(api_keys, args.name):
        
        # Create DMG if requested
        if args.dmg:
            print("\n📦 Creating DMG installer...")
            print("=" * 60)
            create_dmg(args.name)
        
        print("\n🎉 Build complete!")
        print("\nNext steps:")
        print("1. Test the app: open dist/Dakota\\ Content\\ Generator.app")
        print("2. Sign the app: codesign --deep -s 'Developer ID' dist/*.app")
        print("3. Distribute to team")
    
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()