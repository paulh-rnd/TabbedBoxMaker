#!/usr/bin/env python3
"""
Test script for BoxMaker functionality
Tests various configurations to ensure the refactored code works correctly
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to the path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from boxmaker_core import BoxMakerCore


def test_basic_box():
    """Test basic box generation"""
    print("Testing basic box generation...")
    
    core = BoxMakerCore()
    core.set_parameters(
        length=100.0,
        width=80.0,
        height=50.0,
        thickness=3.0,
        kerf=0.1,
        tab=15.0,
        tabtype=0  # Laser
    )
    
    try:
        result = core.generate_box()
        assert len(result['paths']) > 0, "Should generate some paths"
        print("✓ Basic box test passed")
        return True
    except Exception as e:
        print(f"✗ Basic box test failed: {e}")
        return False


def test_box_with_dividers():
    """Test box with 3 dividers"""
    print("Testing box with 3 dividers...")
    
    core = BoxMakerCore()
    core.set_parameters(
        length=120.0,
        width=100.0,
        height=60.0,
        thickness=3.0,
        kerf=0.1,
        tab=20.0,
        div_l=2,  # 2 dividers along length
        div_w=1,  # 1 divider along width
        tabtype=0  # Laser
    )
    
    try:
        result = core.generate_box()
        assert len(result['paths']) > 0, "Should generate paths for box and dividers"
        print("✓ Box with dividers test passed")
        return True
    except Exception as e:
        print(f"✗ Box with dividers test failed: {e}")
        return False


def test_different_material_thickness():
    """Test with different material thickness (6mm instead of 3mm)"""
    print("Testing with 6mm material thickness...")
    
    core = BoxMakerCore()
    core.set_parameters(
        length=150.0,
        width=100.0,
        height=75.0,
        thickness=6.0,  # Thicker material
        kerf=0.2,       # Larger kerf for thicker material
        tab=25.0,
        tabtype=0  # Laser
    )
    
    try:
        result = core.generate_box()
        assert len(result['paths']) > 0, "Should generate paths with thicker material"
        print("✓ Different material thickness test passed")
        return True
    except Exception as e:
        print(f"✗ Different material thickness test failed: {e}")
        return False


def test_cnc_vs_laser():
    """Test CNC (dogbone) vs Laser cutting"""
    print("Testing CNC vs Laser cutting...")
    
    # Test laser cutting
    core_laser = BoxMakerCore()
    core_laser.set_parameters(
        length=100.0,
        width=80.0,
        height=50.0,
        thickness=3.0,
        kerf=0.1,
        tab=15.0,
        tabtype=0  # Laser
    )
    
    # Test CNC cutting (dogbone)
    core_cnc = BoxMakerCore()
    core_cnc.set_parameters(
        length=100.0,
        width=80.0,
        height=50.0,
        thickness=3.0,
        kerf=0.1,
        tab=15.0,
        tabtype=1  # CNC/Dogbone
    )
    
    try:
        result_laser = core_laser.generate_box()
        result_cnc = core_cnc.generate_box()
        
        assert len(result_laser['paths']) > 0, "Laser should generate paths"
        assert len(result_cnc['paths']) > 0, "CNC should generate paths"
        
        # The paths should be different due to dogbone cuts
        assert result_laser['paths'] != result_cnc['paths'], "Laser and CNC paths should differ"
        
        print("✓ CNC vs Laser test passed")
        return True
    except Exception as e:
        print(f"✗ CNC vs Laser test failed: {e}")
        return False


def test_svg_generation():
    """Test SVG file generation"""
    print("Testing SVG generation...")
    
    core = BoxMakerCore()
    core.set_parameters(
        length=100.0,
        width=80.0,
        height=50.0,
        thickness=3.0,
        kerf=0.1,
        tab=15.0
    )
    
    try:
        svg_content = core.generate_svg()
        
        # Basic SVG validation
        assert svg_content.startswith('<?xml'), "Should start with XML declaration"
        assert '<svg' in svg_content, "Should contain SVG element"
        assert '</svg>' in svg_content, "Should end with SVG closing tag"
        assert 'path' in svg_content, "Should contain path elements"
        
        # Write to temporary file to test file I/O
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            temp_path = f.name
        
        # Verify file was written
        assert os.path.exists(temp_path), "SVG file should be created"
        
        # Clean up
        os.unlink(temp_path)
        
        print("✓ SVG generation test passed")
        return True
    except Exception as e:
        print(f"✗ SVG generation test failed: {e}")
        return False


def test_error_conditions():
    """Test error handling"""
    print("Testing error conditions...")
    
    core = BoxMakerCore()
    
    # Test zero dimensions
    try:
        core.set_parameters(length=0, width=100, height=50)
        core.generate_box()
        print("✗ Should have raised error for zero dimensions")
        return False
    except ValueError:
        print("✓ Correctly handled zero dimensions")
    
    # Test tab too large
    try:
        core.set_parameters(length=100, width=100, height=50, tab=50)  # Tab larger than dimension/3
        core.generate_box()
        print("✗ Should have raised error for oversized tab")
        return False
    except ValueError:
        print("✓ Correctly handled oversized tab")
    
    # Test thickness too large
    try:
        core.set_parameters(length=100, width=100, height=50, thickness=40)  # Thickness > dimension/3
        core.generate_box()
        print("✗ Should have raised error for excessive thickness")
        return False
    except ValueError:
        print("✓ Correctly handled excessive thickness")
    
    return True


def test_box_layouts():
    """Test different box layouts"""
    print("Testing different box layouts...")
    
    layouts = [1, 2, 3]  # Diagramatic, 3-piece, Inline
    
    for layout in layouts:
        core = BoxMakerCore()
        core.set_parameters(
            length=100.0,
            width=80.0,
            height=50.0,
            thickness=3.0,
            kerf=0.1,
            tab=15.0,
            style=layout
        )
        
        try:
            result = core.generate_box()
            assert len(result['paths']) > 0, f"Layout {layout} should generate paths"
        except Exception as e:
            print(f"✗ Layout {layout} test failed: {e}")
            return False
    
    print("✓ All layout tests passed")
    return True


def test_save_test_files():
    """Generate test files for manual inspection"""
    print("Generating test files for manual inspection...")
    
    # Ensure test_results directory exists
    test_results_dir = Path("test_results")
    test_results_dir.mkdir(exist_ok=True)
    
    test_cases = [
        {
            'name': 'basic_box_laser',
            'params': {
                'length': 100.0, 'width': 80.0, 'height': 50.0,
                'thickness': 3.0, 'kerf': 0.1, 'tab': 15.0, 'tabtype': 0
            }
        },
        {
            'name': 'basic_box_cnc',
            'params': {
                'length': 100.0, 'width': 80.0, 'height': 50.0,
                'thickness': 3.0, 'kerf': 0.1, 'tab': 15.0, 'tabtype': 1
            }
        },
        {
            'name': 'box_with_dividers',
            'params': {
                'length': 120.0, 'width': 100.0, 'height': 60.0,
                'thickness': 3.0, 'kerf': 0.1, 'tab': 20.0,
                'div_l': 2, 'div_w': 1, 'tabtype': 0
            }
        },
        {
            'name': 'thick_material_box',
            'params': {
                'length': 150.0, 'width': 100.0, 'height': 75.0,
                'thickness': 6.0, 'kerf': 0.2, 'tab': 25.0, 'tabtype': 0
            }
        }
    ]
    
    try:
        for test_case in test_cases:
            core = BoxMakerCore()
            core.set_parameters(**test_case['params'])
            
            svg_content = core.generate_svg()
            
            output_file = test_results_dir / f"test_{test_case['name']}.svg"
            with open(output_file, 'w') as f:
                f.write(svg_content)
            
            print(f"  Generated: {output_file}")
        
        print("✓ Test files generated successfully")
        return True
    except Exception as e:
        print(f"✗ Test file generation failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("Running BoxMaker tests...\n")
    
    tests = [
        test_basic_box,
        test_box_with_dividers,
        test_different_material_thickness,
        test_cnc_vs_laser,
        test_svg_generation,
        test_error_conditions,
        test_box_layouts,
        test_save_test_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Empty line between tests
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactor was successful.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
