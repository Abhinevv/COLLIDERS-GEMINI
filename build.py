"""
Build script for AstroCleanAI
Sets up the project environment and verifies installation
"""

import os
import sys
import subprocess

def create_directories():
    """Create required directories"""
    print("Creating directories...")
    directories = ['data', 'output']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✓ {directory}/")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ Python {version.major}.{version.minor} detected")
        print("  Python 3.8+ is required")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    print()
    return True

def check_virtual_env():
    """Check if virtual environment is active"""
    print("Checking virtual environment...")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print(f"  ✓ Virtual environment active: {sys.prefix}")
    else:
        print("  ⚠ No virtual environment detected")
        print("  Recommendation: Create one with 'python -m venv spaceenv'")
    print()
    return in_venv

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("Installing dependencies...")
    if not os.path.exists('requirements.txt'):
        print("  ✗ requirements.txt not found")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("  ✓ Dependencies installed successfully")
        print()
        return True
    except subprocess.CalledProcessError:
        print("  ✗ Failed to install dependencies")
        print("  Try running manually: pip install -r requirements.txt")
        print()
        return False

def verify_structure():
    """Verify project structure"""
    print("Verifying project structure...")
    
    required_dirs = ['data', 'output', 'propagation', 'probability', 
                     'optimization', 'visualization']
    required_files = [
        'main.py',
        'fetch_tle.py',
        'requirements.txt',
        'propagation/propagate.py',
        'propagation/distance_check.py',
        'probability/collision_probability.py',
        'optimization/avoidance.py',
        'visualization/plot_orbits.py'
    ]
    
    all_good = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✓ {directory}/")
        else:
            print(f"  ✗ {directory}/ - MISSING")
            all_good = False
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            all_good = False
    
    print()
    return all_good

def main():
    """Main build process"""
    print("=" * 70)
    print("ASTROCLEANAI BUILD SCRIPT")
    print("=" * 70)
    print()
    
    # Step 1: Create directories
    create_directories()
    
    # Step 2: Check Python version
    if not check_python_version():
        print("Build failed: Python version incompatible")
        return 1
    
    # Step 3: Check virtual environment
    check_virtual_env()
    
    # Step 4: Verify structure
    if not verify_structure():
        print("Build failed: Missing required files/directories")
        return 1
    
    # Step 5: Install dependencies (optional, user can skip)
    print("=" * 70)
    response = input("Install dependencies now? (y/n): ").strip().lower()
    if response == 'y':
        install_dependencies()
    else:
        print("Skipping dependency installation")
        print("Run manually: pip install -r requirements.txt")
        print()
    
    print("=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Activate virtual environment:")
    print("     Windows: spaceenv\\Scripts\\activate")
    print("     Linux/Mac: source spaceenv/bin/activate")
    print("  2. Install dependencies (if not done):")
    print("     pip install -r requirements.txt")
    print("  3. Download TLE data:")
    print("     python fetch_tle.py")
    print("  4. Run the system:")
    print("     python main.py")
    print("  5. Test the system:")
    print("     python test_system.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
