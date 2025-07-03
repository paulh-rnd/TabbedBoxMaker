#!/usr/bin/env python3
"""
Local pre-commit test script
Run this before committing to catch issues early
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"✅ {description} - SUCCESS")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"   Error: {e.stderr.strip()}")
        if e.stdout.strip():
            print(f"   Output: {e.stdout.strip()}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        size = Path(file_path).stat().st_size
        print(f"✅ {description} - EXISTS ({size} bytes)")
        return True
    else:
        print(f"❌ {description} - MISSING")
        return False

def validate_svg_file(file_path):
    """Basic SVG validation"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            if '<svg' in content and '</svg>' in content:
                return True
            else:
                print(f"   ⚠️  {file_path}: Missing SVG tags")
                return False
    except Exception as e:
        print(f"   ❌ {file_path}: Error reading file - {e}")
        return False

def main():
    """Run all pre-commit tests"""
    print("🚀 Running TabbedBox2 Pre-Commit Tests")
    print("=" * 50)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Create test directories
    print("\n📁 Setting up test directories...")
    os.makedirs("test_results", exist_ok=True)
    os.makedirs("test_assets", exist_ok=True)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Python syntax check
    total_tests += 1
    files_to_check = [
        "boxmaker.py", "boxmaker_core.py", "boxmaker_constants.py", 
        "boxmaker_exceptions.py", "test_boxmaker.py", "cli_examples.py"
    ]
    
    syntax_ok = True
    for file in files_to_check:
        if not run_command(f"python -m py_compile {file}", f"Syntax check: {file}"):
            syntax_ok = False
    
    if syntax_ok:
        success_count += 1
        print("✅ All Python files have valid syntax")
    else:
        print("❌ Some Python files have syntax errors")
    
    # Test 2: Module imports
    total_tests += 1
    imports_ok = True
    import_tests = [
        ("from boxmaker_core import BoxMakerCore", "Core module import"),
        ("from boxmaker_constants import BoxType", "Constants module import"),
        ("from boxmaker_exceptions import DimensionError", "Exceptions module import")
    ]
    
    for import_cmd, description in import_tests:
        if not run_command(f'python -c "{import_cmd}"', description):
            imports_ok = False
    
    if imports_ok:
        success_count += 1
    
    # Test 3: Core test suite
    total_tests += 1
    if run_command("python test_boxmaker.py", "Core test suite"):
        success_count += 1
    
    # Test 4: CLI examples
    total_tests += 1
    if run_command("python cli_examples.py", "CLI examples"):
        success_count += 1
    
    # Test 5: Basic CLI functionality
    total_tests += 1
    if run_command(
        "python boxmaker.py --length 100 --width 80 --height 50 --thickness 3 --tab 12 --output test_precommit.svg",
        "Basic CLI test"
    ):
        if check_file_exists("test_precommit.svg", "CLI output file"):
            if validate_svg_file("test_precommit.svg"):
                success_count += 1
                print("✅ CLI generates valid SVG")
            else:
                print("❌ CLI generated invalid SVG")
        else:
            print("❌ CLI did not generate output file")
    
    # Test 6: Error handling
    total_tests += 1
    error_handling_ok = True
    
    # Test dimension too small (should fail)
    result = subprocess.run(
        "python boxmaker.py --length 20 --width 50 --height 40 --output test_fail.svg",
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        print("❌ Should have failed with small dimensions")
        error_handling_ok = False
    else:
        print("✅ Correctly rejected small dimensions")
    
    # Test tab too large (should fail)  
    result = subprocess.run(
        "python boxmaker.py --length 100 --width 100 --height 100 --thickness 3 --tab 50 --output test_fail.svg",
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        print("❌ Should have failed with oversized tabs")
        error_handling_ok = False
    else:
        print("✅ Correctly rejected oversized tabs")
    
    if error_handling_ok:
        success_count += 1
    
    # Test 7: SVG validation
    total_tests += 1
    svg_files = []
    
    # Collect all generated SVG files
    for pattern in ["test_results/*.svg", "test_assets/*.svg"]:
        svg_files.extend(Path().glob(pattern))
    
    if Path("test_precommit.svg").exists():
        svg_files.append(Path("test_precommit.svg"))
    
    if svg_files:
        svg_valid = True
        print(f"\n📋 Validating {len(svg_files)} SVG files...")
        
        for svg_file in svg_files:
            if not validate_svg_file(svg_file):
                svg_valid = False
        
        if svg_valid:
            success_count += 1
            print(f"✅ All {len(svg_files)} SVG files are valid")
        else:
            print("❌ Some SVG files are invalid")
    else:
        print("❌ No SVG files found to validate")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PRE-COMMIT TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {success_count}/{total_tests}")
    print(f"Success rate: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 ALL TESTS PASSED! Ready to commit.")
        
        # Cleanup temporary files
        for temp_file in ["test_precommit.svg", "test_fail.svg"]:
            if Path(temp_file).exists():
                Path(temp_file).unlink()
        
        return 0
    else:
        print(f"\n❌ {total_tests - success_count} test(s) failed. Please fix before committing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
