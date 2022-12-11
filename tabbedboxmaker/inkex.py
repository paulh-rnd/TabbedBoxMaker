#! /usr/bin/env python -t
'''
Generates Inkscape SVG file containing box components needed to
CNC (laser/mill) cut a box with tabbed joints taking kerf and clearance into account

Original Tabbed Box Maker Copyright (C) 2011 elliot white

Changelog:
19/12/2014 Paul Hutchison:
 - Ability to generate 6, 5, 4, 3 or 2-panel cutouts
 - Ability to also generate evenly spaced dividers within the box
   including tabbed joints to box sides and slots to slot into each other

23/06/2015 by Paul Hutchison:
 - Updated for Inkscape's 0.91 breaking change (unittouu)

v0.93 - 15/8/2016 by Paul Hutchison:
 - Added Hairline option and fixed open box height bug

v0.94 - 05/01/2017 by Paul Hutchison:
 - Added option for keying dividers into walls/floor/none

v0.95 - 2017-04-20 by Jim McBeath
 - Added optional dimples

v0.96 - 2017-04-24 by Jim McBeath
 - Refactored to make box type, tab style, and layout all orthogonal
 - Added Tab Style option to allow creating waffle-block-style tabs
 - Made open box size correct based on inner or outer dimension choice
 - Fixed a few tab bugs

v0.99 - 2020-06-01 by Paul Hutchison
 - Preparatory release with Inkscape 1.0 compatibility upgrades (further fixes to come!)
 - Removed Antisymmetric option as it's broken, kinda pointless and looks weird
 - Fixed divider issues with Rotate Symmetric
 - Made individual panels and their keyholes/slots grouped

v1.0 - 2020-06-17 by Paul Hutchison
 - Removed clearance parameter, as this was just subtracted from kerf - pointless?
 - Corrected kerf adjustments for overall box size and divider keyholes
 - Added dogbone cuts: CNC mills now supported!
 - Fix for floor/ceiling divider key issue (#17)
 - Increased max dividers to 20 (#35)

v1.1 - 2021-08-09 by Paul Hutchison
 - Fixed for current Inkscape release version 1.1 - thanks to PR from https://github.com/roastedneutrons

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "1.0" ### please report bugs, suggestions etc at https://github.com/paulh-rnd/TabbedBoxMaker ###

from typing import List

import os,sys,inkex,simplestyle,gettext,math
from copy import deepcopy
import tabbedboxmaker

_ = gettext.gettext

linethickness = 1 # default unless overridden by settings

def newGroup(canvas):
  # Create a new group and add element created from line string
  panelId = canvas.svg.get_unique_id('panel')
  group = canvas.svg.get_current_layer().add(inkex.Group(id=panelId))
  return group

def getLine(XYstring):
  line = inkex.PathElement()
  line.style = { 'stroke': '#000000', 'stroke-width'  : str(linethickness), 'fill': 'none' }
  line.path = XYstring
  #inkex.etree.SubElement(parent, inkex.addNS('path','svg'), drw)
  return line

# jslee - shamelessly adapted from sample code on below Inkscape wiki page 2015-07-28
# http://wiki.inkscape.org/wiki/index.php/Generating_objects_from_extensions
def getCircle(r, c):
    (cx, cy) = c
    log("putting circle at (%d,%d)" % (cx,cy))
    circle = inkex.PathElement.arc((cx, cy), r)
    circle.style = { 'stroke': '#000000', 'stroke-width': str(linethickness), 'fill': 'none' }

    # ell_attribs = {'style':simplestyle.formatStyle(style),
    #     inkex.addNS('cx','sodipodi')        :str(cx),
    #     inkex.addNS('cy','sodipodi')        :str(cy),
    #     inkex.addNS('rx','sodipodi')        :str(r),
    #     inkex.addNS('ry','sodipodi')        :str(r),
    #     inkex.addNS('start','sodipodi')     :str(0),
    #     inkex.addNS('end','sodipodi')       :str(2*math.pi),
    #     inkex.addNS('open','sodipodi')      :'true', #all ellipse sectors we will draw are open
    #     inkex.addNS('type','sodipodi')      :'arc',
    #     'transform'                         :'' }
    #inkex.etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )
    return circle


class SvgExporter(object):
    """Export AbstractShape objects as SVG"""

    def export(self, shape, inkex_group) -> None:
        """Write the shape into the given inkex_group"""
        try:
            export_method = 'export_' + shape.__class__.__name__
            exporter = getattr(self, export_method)
            exporter(shape, inkex_group)
        except AttributeError:
            print(f'No exporter for shape type "{type(shape)}" (looking for "{export_method}")')
            raise

    def export_Circle(self, circle, inkex_group) -> None:
        inkex_group.add(getCircle(circle.radius, circle.centre))

    def export_Path(self, path, inkex_group) -> None:
        d = f'M {path.initial_x}, {path.initial_y} '
        for seg in path.segments:
            if seg.type == 'line':
                d += f'L {seg.args[0]} {seg.args[1]} '
            else:
                raise Exception(f'Unsupported segment type "{seg.type}"')
        inkex_group.add(getLine(d))


class InkexBoxMaker(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)

      # Add common boxmaker args.
      tabbedboxmaker.add_args(self.arg_parser)

      # Add inkex plugin specific args.
      self.arg_parser.add_argument('--hairline',action='store',type=int,
        dest='hairline',default=0,help='Line Thickness')


  def _to_svg_units(self, value: float, unit: str) -> float:
      return self.svg.unittouu(str(value) + unit)

  def effect(self):
    global linethickness

        # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()

        # Get the attributes:
    widthDoc  = self.svg.unittouu(svg.get('width'))
    heightDoc = self.svg.unittouu(svg.get('height'))

    # Get script's option values.

    # Set the line thickness
    hairline=self.options.hairline
    if hairline:
        linethickness=self.svg.unittouu('0.002in')
    else:
        linethickness=1

    unit = self.options.unit

    if self.options.schroff:
        self.options.rail_height = self._to_svg_units(self.options.rail_height, unit)
        self.options.row_centre_spacing = self._to_svg_units(122.5, unit)  # TODO(desbonne): Fixed number with variable unit? Feels wrong.
        self.options.row_spacing = self._to_svg_units(self.options.row_spacing, unit)
        self.options.rail_mount_depth = self._to_svg_units(self.options.rail_mount_depth, unit)
        self.options.rail_mount_centre_offset = self._to_svg_units(self.options.rail_mount_centre_offset, unit)
        self.options.rail_mount_radius=self._to_svg_units(2.5, unit) # TODO(desbonne): Same - fixed number with variable unit.

    ## minimally different behaviour for schroffmaker.inx vs. boxmaker.inx
    ## essentially schroffmaker.inx is just an alternate interface with different
    ## default settings, some options removed, and a tiny amount of extra logic
    if self.options.schroff:
        ## schroffmaker.inx
        X = self._to_svg_units(self.options.hp * 5.08, unit) # TODO(desbonne): Same - fixed number with variable unit.
        # 122.5mm vertical distance between mounting hole centres of 3U Schroff panels
        row_height = rows * (self.options.row_centre_spacing + self.options.rail_height)
        # rail spacing in between rows but never between rows and case panels
        row_spacing_total = (self.options.rows - 1) * self.options.row_spacing
        Y = row_height + row_spacing_total
    else:
        ## boxmaker.inx
        X = self._to_svg_units(self.options.length + self.options.kerf, unit)
        Y = self._to_svg_units(self.options.width + self.options.kerf, unit)

    Z = self._to_svg_units(self.options.height + self.options.kerf, unit)

    self.options.kerf = self._to_svg_units(self.options.kerf, self.options.unit)
    self.options.thickness = self._to_svg_units(self.options.thickness, unit)
    self.options.tab = self._to_svg_units(self.options.tab, unit)
    self.options.spacing = self._to_svg_units(self.options.spacing, unit)

    # check input values mainly to avoid python errors
    # TODO restrict values to *correct* solutions
    # TODO restrict divisions to logical values
    error=0

    if min(X,Y,Z)==0:
      inkex.errormsg(_('Error: Dimensions must be non zero'))
      error=1
    if max(X,Y,Z)>max(widthDoc,heightDoc)*10: # crude test
      inkex.errormsg(_('Error: Dimensions Too Large'))
      error=1
    if min(X,Y,Z)<3*self.options.tab:
      inkex.errormsg(_('Error: Tab size too large'))
      error=1
    if self.options.tab<self.options.thickness:
      inkex.errormsg(_('Error: Tab size too small'))
      error=1
    if self.options.thickness==0:
      inkex.errormsg(_('Error: Thickness is zero'))
      error=1
    if self.options.thickness>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Material too thick'))
      error=1
    if self.options.kerf>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Kerf too large'))
      error=1
    if self.options.spacing>max(X,Y,Z)*10: # crude test
      inkex.errormsg(_('Error: Spacing too large'))
      error=1
    if self.options.spacing<self.options.kerf:
      inkex.errormsg(_('Error: Spacing too small'))
      error=1

    if error: exit()

    box = tabbedboxmaker.TabbedBox(self.options)
    groups = box.make(X, Y, Z)
    svg_exporter = SvgExporter()

    for group in groups:
        inkex_grp = newGroup(self)
        for path in group:
            svg_exporter.export(path, inkex_grp)

if __name__ == '__main__':
  # Create effect instance and apply it.
  effect = InkexBoxMaker()
  effect.run()
