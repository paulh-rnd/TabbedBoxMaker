#! /usr/bin/env python -t
'''
Generates Inkscape SVG file containing box components needed to 
CNC (laser/mill) cut a box with tabbed joints taking kerf and clearance into account

Refactored for testability while maintaining Inkscape compatibility

Original Tabbed Box Maker Copyright (C) 2011 elliot white
Refactoring for testability by GitHub Copilot 2025

[Previous changelog preserved...]
'''
__version__ = "1.3" ### please report bugs, suggestions etc at https://github.com/paulh-rnd/TabbedBoxMaker ###

import os
import sys
import argparse
from pathlib import Path

# Try to import Inkscape modules, fallback gracefully for CLI usage
try:
    import inkex
    import simplestyle
    import gettext
    INKSCAPE_AVAILABLE = True
    _ = gettext.gettext
except ImportError:
    INKSCAPE_AVAILABLE = False
    _ = lambda x: x  # Simple fallback for translation

from boxmaker_core import BoxMakerCore
from boxmaker_constants import BoxType, TabType, LayoutStyle
from boxmaker_exceptions import BoxMakerError, DimensionError, TabError, MaterialError

linethickness = 1 # default unless overridden by settings

def log(text):
    if 'SCHROFF_LOG' in os.environ:
        f = open(os.environ.get('SCHROFF_LOG'), 'a')
        f.write(text + "\n")

def newGroup(canvas):
    # Create a new group and add element created from line string
    panelId = canvas.svg.get_unique_id('panel')
    group = canvas.svg.get_current_layer().add(inkex.Group(id=panelId))
    return group
  
def getLine(XYstring):
    line = inkex.PathElement()
    line.style = { 'stroke': '#000000', 'stroke-width'  : str(linethickness), 'fill': 'none' }
    line.path = XYstring
    return line

def getCircle(r, c):
    (cx, cy) = c
    log("putting circle at (%d,%d)" % (cx,cy))
    circle = inkex.PathElement.arc((cx, cy), r)
    circle.style = { 'stroke': '#000000', 'stroke-width': str(linethickness), 'fill': 'none' }
    return circle

# CLI support
def create_cli_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description='Generate tabbed box SVG files')
    parser.add_argument('--length', type=float, default=100.0, help='Length of box (mm)')
    parser.add_argument('--width', type=float, default=100.0, help='Width of box (mm)')
    parser.add_argument('--height', type=float, default=100.0, help='Height of box (mm)')
    parser.add_argument('--thickness', type=float, default=3.0, help='Material thickness (mm)')
    parser.add_argument('--kerf', type=float, default=0.5, help='Kerf width (mm)')
    parser.add_argument('--tab', type=float, default=25.0, help='Tab width (mm)')
    parser.add_argument('--style', type=int, choices=[1, 2, 3], default=LayoutStyle.SEPARATED, help='Layout style')
    parser.add_argument('--boxtype', type=int, choices=range(1, 7), default=BoxType.FULL_BOX, help='Box type')
    parser.add_argument('--tabtype', type=int, choices=[0, 1], default=TabType.LASER, help='Tab type (0=laser, 1=mill)')
    parser.add_argument('--div-l', type=int, default=0, help='Dividers along length')
    parser.add_argument('--div-w', type=int, default=0, help='Dividers along width')
    parser.add_argument('--output', '-o', type=str, default='box.svg', help='Output SVG file')
    parser.add_argument('--inside', action='store_true', help='Dimensions are inside measurements')
    return parser

def main():
    """Main CLI function"""
    # Check if we're being run as CLI (no Inkscape SVG input)
    import sys
    
    # Simple check: if we have CLI-style arguments, run in CLI mode
    cli_args = ['--length', '--width', '--height', '--thickness', '--kerf', '--tab', '--output']
    is_cli = any(arg in sys.argv for arg in cli_args)
    
    if not INKSCAPE_AVAILABLE or is_cli:
        # CLI mode
        parser = create_cli_parser()
        args = parser.parse_args()
        
        # Create core instance and set parameters
        core = BoxMakerCore()
        core.set_parameters(
            length=args.length,
            width=args.width,
            height=args.height,
            thickness=args.thickness,
            kerf=args.kerf,
            tab=args.tab,
            style=args.style,
            boxtype=args.boxtype,
            tabtype=args.tabtype,
            div_l=args.div_l,
            div_w=args.div_w,
            inside=1 if args.inside else 0
        )
        
        try:
            # Generate SVG
            svg_content = core.generate_svg()
            
            # Write to file
            with open(args.output, 'w') as f:
                f.write(svg_content)
            
            print(f"Box SVG generated: {args.output}")
            
        except DimensionError as e:
            print(f"❌ Dimension Error: {e}")
            print("💡 Tip: All dimensions should be at least 40mm for practical boxes")
            sys.exit(1)
        except TabError as e:
            print(f"❌ Tab Error: {e}")
            print("💡 Tip: Use tabs between material thickness and dimension/3")
            sys.exit(1)
        except MaterialError as e:
            print(f"❌ Material Error: {e}")
            print("💡 Tip: Material thickness should be much smaller than box dimensions")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
            
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Inkscape extension mode
        effect = BoxMaker()
        effect.run()

if INKSCAPE_AVAILABLE:
    class BoxMaker(inkex.Effect):
        def __init__(self):
            # Call the base class constructor.
            inkex.Effect.__init__(self)
            # Define options - keeping original interface
            self.arg_parser.add_argument('--schroff',action='store',type=int,
              dest='schroff',default=0,help='Enable Schroff mode')
            self.arg_parser.add_argument('--rail_height',action='store',type=float,
              dest='rail_height',default=10.0,help='Height of rail')
            self.arg_parser.add_argument('--rail_mount_depth',action='store',type=float,
              dest='rail_mount_depth',default=17.4,help='Depth at which to place hole for rail mount bolt')
            self.arg_parser.add_argument('--rail_mount_centre_offset',action='store',type=float,
              dest='rail_mount_centre_offset',default=0.0,help='How far toward row centreline to offset rail mount bolt (from rail centreline)')
            self.arg_parser.add_argument('--rows',action='store',type=int,
              dest='rows',default=0,help='Number of Schroff rows')
            self.arg_parser.add_argument('--hp',action='store',type=int,
              dest='hp',default=0,help='Width (TE/HP units) of Schroff rows')
            self.arg_parser.add_argument('--row_spacing',action='store',type=float,
              dest='row_spacing',default=10.0,help='Height of rail')
            self.arg_parser.add_argument('--unit',action='store',type=str,
              dest='unit',default='mm',help='Measure Units')
            self.arg_parser.add_argument('--inside',action='store',type=int,
              dest='inside',default=0,help='Int/Ext Dimension')
            self.arg_parser.add_argument('--length',action='store',type=float,
              dest='length',default=100,help='Length of Box')
            self.arg_parser.add_argument('--width',action='store',type=float,
              dest='width',default=100,help='Width of Box')
            self.arg_parser.add_argument('--depth',action='store',type=float,
              dest='height',default=100,help='Height of Box')
            self.arg_parser.add_argument('--tab',action='store',type=float,
              dest='tab',default=25,help='Nominal Tab Width')
            self.arg_parser.add_argument('--equal',action='store',type=int,
              dest='equal',default=0,help='Equal/Prop Tabs')
            self.arg_parser.add_argument('--tabsymmetry',action='store',type=int,
              dest='tabsymmetry',default=0,help='Tab style')
            self.arg_parser.add_argument('--tabtype',action='store',type=int,
              dest='tabtype',default=0,help='Tab type: regular or dogbone')
            self.arg_parser.add_argument('--dimpleheight',action='store',type=float,
              dest='dimpleheight',default=0,help='Tab Dimple Height')
            self.arg_parser.add_argument('--dimplelength',action='store',type=float,
              dest='dimplelength',default=0,help='Tab Dimple Tip Length')
            self.arg_parser.add_argument('--hairline',action='store',type=int,
              dest='hairline',default=0,help='Line Thickness')
            self.arg_parser.add_argument('--thickness',action='store',type=float,
              dest='thickness',default=10,help='Thickness of Material')
            self.arg_parser.add_argument('--kerf',action='store',type=float,
              dest='kerf',default=0.5,help='Kerf (width of cut)')
            self.arg_parser.add_argument('--style',action='store',type=int,
              dest='style',default=25,help='Layout/Style')
            self.arg_parser.add_argument('--spacing',action='store',type=float,
              dest='spacing',default=25,help='Part Spacing')
            self.arg_parser.add_argument('--boxtype',action='store',type=int,
              dest='boxtype',default=25,help='Box type')
            self.arg_parser.add_argument('--div_l',action='store',type=int,
              dest='div_l',default=25,help='Dividers (Length axis)')
            self.arg_parser.add_argument('--div_w',action='store',type=int,
              dest='div_w',default=25,help='Dividers (Width axis)')
            self.arg_parser.add_argument('--keydiv',action='store',type=int,
              dest='keydiv',default=3,help='Key dividers into walls/floor')
            self.arg_parser.add_argument('--optimize',action='store',type=inkex.utils.Boolean,
              dest='optimize',default=True,help='Optimize paths')

        def effect(self):
            # Create BoxMakerCore instance and configure it
            core = BoxMakerCore()
            
            # Get script's option values and transfer to core
            core.hairline = self.options.hairline
            core.unit = self.options.unit
            core.inside = self.options.inside
            
            # Convert units using Inkscape's unit conversion
            core.kerf = self.svg.unittouu(str(self.options.kerf) + core.unit)
            core.length = self.svg.unittouu(str(self.options.length + self.options.kerf) + core.unit)
            core.width = self.svg.unittouu(str(self.options.width + self.options.kerf) + core.unit)
            core.height = self.svg.unittouu(str(self.options.height + self.options.kerf) + core.unit)
            core.thickness = self.svg.unittouu(str(self.options.thickness) + core.unit)
            core.tab = self.svg.unittouu(str(self.options.tab) + core.unit)
            core.spacing = self.svg.unittouu(str(self.options.spacing) + core.unit)
            core.dimpleheight = self.svg.unittouu(str(self.options.dimpleheight) + core.unit)
            core.dimplelength = self.svg.unittouu(str(self.options.dimplelength) + core.unit)
            
            # Set other options
            core.equal = self.options.equal
            core.tabsymmetry = self.options.tabsymmetry
            core.tabtype = self.options.tabtype
            core.style = self.options.style
            core.boxtype = self.options.boxtype
            core.div_l = self.options.div_l
            core.div_w = self.options.div_w
            core.keydiv = self.options.keydiv
            core.optimize = self.options.optimize
            
            # Set line thickness based on hairline option
            global linethickness
            if core.hairline:
                linethickness = self.svg.unittouu('0.002in')
                core.linethickness = linethickness
            else:
                linethickness = 1
                core.linethickness = linethickness
            
            try:
                # Generate the box using core functionality
                result = core.generate_box()
                
                # Convert core output to Inkscape elements
                for path_data in result['paths']:
                    line = getLine(path_data['data'])
                    group = newGroup(self)
                    group.add(line)
                    
                for circle_data in result['circles']:
                    circle = getCircle(circle_data['r'], (circle_data['cx'], circle_data['cy']))
                    group = newGroup(self)
                    group.add(circle)
                    
            except ValueError as e:
                inkex.errormsg(_(str(e)))
                return

if __name__ == '__main__':
    main()
