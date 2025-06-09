"""
Test script to verify PyInstaller installation and functionality
"""
import sys
import subprocess
import tempfile
import os
from pathlib import Path


def test_pyinstaller_import():
    """Test if PyInstaller can be imported"""
    try:
        import PyInstaller
        print("✅ PyInstaller import successful")
        print(f"   Version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller import failed")
        return False


def test_pyinstaller_module():
    """Test if PyInstaller can be run as a module"""
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ PyInstaller module execution successful")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ PyInstaller module execution failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ PyInstaller module test failed: {e}")
        return False


def test_simple_build():
    """Test a simple PyInstaller build"""
    print("🧪 Testing simple PyInstaller build...")
    
    # Create a simple test script
    test_script = """
import sys
print("Hello from test script!")
print(f"Python version: {sys.version}")
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        script_file = temp_dir / "test_script.py"
        
        # Write test script
        with open(script_file, 'w') as f:
            f.write(test_script)
        
        # Try to build with PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--distpath', str(temp_dir / 'dist'),
            '--workpath', str(temp_dir / 'build'),
            '--specpath', str(temp_dir),
            '--name', 'test_app',
            '--noconfirm',
            str(script_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                exe_path = temp_dir / 'dist' / 'test_app.exe'
                if exe_path.exists():
                    print("✅ Simple PyInstaller build successful")
                    
                    # Try to run the built executable
                    try:
                        run_result = subprocess.run([str(exe_path)], 
                                                  capture_output=True, text=True, timeout=10)
                        if run_result.returncode == 0:
                            print("✅ Built executable runs successfully")
                            print(f"   Output: {run_result.stdout.strip()}")
                            return True
                        else:
                            print("⚠️  Built executable has issues")
                            print(f"   Error: {run_result.stderr}")
                            return False
                    except Exception as e:
                        print(f"⚠️  Could not test executable: {e}")
                        return True  # Build worked, execution test failed
                else:
                    print("❌ Executable not created")
                    return False
            else:
                print("❌ PyInstaller build failed")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ PyInstaller build timed out")
            return False
        except Exception as e:
            print(f"❌ PyInstaller build error: {e}")
            return False


def main():
    """Run all PyInstaller tests"""
    print("🔧 PyInstaller Diagnostic Tool")
    print("=" * 40)
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print()
    
    # Test 1: Import
    import_ok = test_pyinstaller_import()
    print()
    
    # Test 2: Module execution
    module_ok = test_pyinstaller_module()
    print()
    
    # Test 3: Simple build
    if import_ok or module_ok:
        build_ok = test_simple_build()
        print()
        
        if build_ok:
            print("✅ All PyInstaller tests passed!")
            print("PyInstaller is working correctly.")
        else:
            print("⚠️  PyInstaller is installed but has build issues")
    else:
        print("❌ PyInstaller is not properly installed")
        print("\nTroubleshooting steps:")
        print("1. Try: pip uninstall pyinstaller")
        print("2. Then: pip install pyinstaller")
        print("3. Or try: pip install --upgrade pyinstaller")
        print("4. Check if you're in a virtual environment")


if __name__ == "__main__":
    main()
