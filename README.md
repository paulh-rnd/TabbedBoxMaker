# TabbedBoxMaker: A free Inkscape extension for generating tab-jointed box patterns

[![CI - Test and Validate BoxMaker](https://github.com/rhuijben/TabbedBoxMaker/actions/workflows/ci.yml/badge.svg)](https://github.com/rhuijben/TabbedBoxMaker/actions/workflows/ci.yml)

_version 2.0 - 21 Jun 2025_

Original box maker by Elliot White (formerly of twot.eu, domain name now squatted)

Heavily modified by [Paul Hutchison](https://github.com/paulh-rnd)

Refactored for testability and CLI support by [Bert Huijben](https://github.com/rhuijben)

## What's New in Version 2.0

### ✨ New Features
- **🚀 CLI Support**: Generate box SVGs from command line without Inkscape
- **🧪 Comprehensive Testing**: Automated test suite with 11 test scenarios
- **🔧 Same Inkscape Experience**: Identical behavior when used as extension
- **⚡ Continuous Integration**: Automated testing on every commit and PR
- **📊 Cross-Platform**: Tested on Ubuntu, Windows, and macOS
- **🎯 Robust Validation**: Input validation with helpful error messages

### 🔧 Technical Improvements
- **Modular Architecture**: Core logic separated for testability
- **Error Handling**: Proper validation and clear error messages
- **Code Quality**: Clean, maintainable Python code with documentation
- **Automated Examples**: CLI examples that run automatically in CI

## About
 This tool is designed to simplify the process of making practical boxes from sheet material using almost any kind of CNC cutter (laser, plasma, water jet or mill). The box edges are "finger-jointed" or "tab-jointed", and may include press-fit dimples, internal dividers, dogbone corners (for endmill cutting), and more.

 The tool works by generating each side of the box with the tab and edge sizes corrected to account for the kerf (width of cut). Each box side is composed of a group of individual lines that make up each edge of the face, as well as any other cutouts for dividers. It is recommended that you join adjacent lines in your CNC software to cut efficiently.

 An additional extension which uses the same TabbedBoxMaker generator script is also included: Schroff Box Maker. The Schroff addition was created by [John Slee](https://github.com/jsleeio). If you create further derivative box generators, feel free to send me a pull request!

## Usage

### As Inkscape Extension (Original Usage)
Copy `boxmaker.py`, `boxmaker_core.py`, `boxmaker_constants.py`, `boxmaker_exceptions.py`, and `boxmaker.inx` to your Inkscape extensions folder. Use exactly as before - no changes to the interface or behavior.

### As CLI Tool (New!)
```bash
# Basic box (100x80x50mm, 3mm material, laser cutting)
python boxmaker.py --length 100 --width 80 --height 50 --thickness 3 --kerf 0.1 --output my_box.svg

# CNC milling with dogbone cuts
python boxmaker.py --length 100 --width 80 --height 50 --thickness 3 --tabtype 1 --output cnc_box.svg

# Box with dividers (2 length, 1 width)
python boxmaker.py --length 120 --width 100 --height 60 --div-l 2 --div-w 1 --output box_with_dividers.svg

# Thick material (6mm plywood)
python boxmaker.py --length 150 --width 100 --height 75 --thickness 6 --kerf 0.2 --tab 25 --output thick_box.svg

# Inside dimensions box (interior 100x80x50)
python boxmaker.py --length 100 --width 80 --height 50 --thickness 3 --inside --output inside_box.svg
```

### CLI Options
```
--length FLOAT      Length of box (mm)
--width FLOAT       Width of box (mm) 
--height FLOAT      Height of box (mm)
--thickness FLOAT   Material thickness (mm)
--kerf FLOAT        Kerf width (mm)
--tab FLOAT         Tab width (mm)
--style {1,2,3}     Layout style (1=diagramatic, 2=3-piece, 3=compact)
--boxtype {1-6}     Box type (1=full, 2=no top, etc.)
--tabtype {0,1}     Tab type (0=laser, 1=cnc/dogbone)
--div-l INT         Dividers along length
--div-w INT         Dividers along width
--inside            Dimensions are inside measurements
--output FILE       Output SVG file
```

## Testing and Quality Assurance

This project includes comprehensive automated testing:

### Run Tests Locally
```bash
# Run the full test suite (11 tests)
python test_boxmaker.py

# Run CLI examples (6 examples)
python cli_examples.py

# Run pre-commit validation
python pre_commit_test.py
```

### Continuous Integration
- **Automated Testing**: Full test suite runs on Python 3.11 and 3.12
- **Cross-Platform**: Tested on Ubuntu, Windows, and macOS  
- **SVG Validation**: All generated files validated for correctness
- **Example Generation**: CLI examples run automatically to ensure they work

### Test Coverage
- ✅ Basic box generation (multiple sizes)
- ✅ Boxes with dividers (various configurations)
- ✅ Different material thicknesses (3mm, 6mm)
- ✅ Laser vs CNC cutting modes
- ✅ Layout styles and box types
- ✅ Inside vs outside dimensions
- ✅ Error handling and validation
- ✅ Edge cases (large boxes, thin/thick tabs)
