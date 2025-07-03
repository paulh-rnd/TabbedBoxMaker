#!/usr/bin/env python3
"""
Example CLI usage of the BoxMaker
Demonstrates how to use the boxmaker from command line
"""

import sys
import subprocess
from pathlib import Path

def run_example(description, args):
    """Run a single example"""
    print(f"\n{description}")
    print(f"Command: python boxmaker.py {' '.join(args)}")
    print("-" * 50)
    
    try:
        # Run the boxmaker with the given arguments
        result = subprocess.run([sys.executable, 'boxmaker.py'] + args, 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def main():
    """Run CLI examples"""
    print("BoxMaker CLI Examples")
    print("=" * 50)
    
    # Ensure test_assets directory exists
    import os
    os.makedirs("test_assets", exist_ok=True)
    
    examples = [
        {
            'description': "1. Basic 100x80x50mm box for laser cutting",
            'args': ['--length', '100', '--width', '80', '--height', '50', 
                    '--thickness', '3', '--kerf', '0.1', '--tab', '15', '--tabtype', '0',
                    '--output', 'test_assets/basic_laser_box.svg']
        },
        {
            'description': "2. Same box but for CNC milling (with dogbone cuts)",
            'args': ['--length', '100', '--width', '80', '--height', '50', 
                    '--thickness', '3', '--kerf', '0.1', '--tab', '15', '--tabtype', '1',
                    '--output', 'test_assets/basic_cnc_box.svg']
        },
        {
            'description': "3. Box with dividers (2 length, 1 width)",
            'args': ['--length', '120', '--width', '100', '--height', '60', 
                    '--thickness', '3', '--kerf', '0.1', '--tab', '20', '--div-l', '2', '--div-w', '1',
                    '--output', 'test_assets/box_with_dividers.svg']
        },
        {
            'description': "4. Thick material box (6mm plywood)",
            'args': ['--length', '150', '--width', '100', '--height', '75', 
                    '--thickness', '6', '--kerf', '0.2', '--tab', '25',
                    '--output', 'test_assets/thick_material_box.svg']
        },
        {
            'description': "5. Inside dimensions box (interior 100x80x50)",
            'args': ['--length', '100', '--width', '80', '--height', '50', 
                    '--thickness', '3', '--kerf', '0.1', '--tab', '15', '--inside',
                    '--output', 'test_assets/inside_dimensions_box.svg']
        },
        {
            'description': "6. Compact layout style",
            'args': ['--length', '100', '--width', '80', '--height', '50', 
                    '--thickness', '3', '--kerf', '0.1', '--tab', '15', '--style', '3',
                    '--output', 'test_assets/compact_layout_box.svg']
        }    ]
    
    success_count = 0
    
    for example in examples:
        if run_example(example['description'], example['args']):
            success_count += 1
    
    print(f"\n\nSummary: {success_count}/{len(examples)} examples completed successfully")
    
    if success_count == len(examples):
        print("\n🎉 All examples generated successfully!")
        print("\nGenerated files in test_assets/:")
        for example in examples:
            output_file = None
            args = example['args']
            for i, arg in enumerate(args):
                if arg == '--output' and i + 1 < len(args):
                    output_file = args[i + 1]
                    break
            if output_file and Path(output_file).exists():
                print(f"  - {output_file}")
    else:
        print(f"\n❌ {len(examples) - success_count} examples failed")

if __name__ == '__main__':
    main()
