#! /usr/bin/env python -t
'''
Generates Inkscape SVG file containing box components needed to 
CNC (laser/mill) cut a card board box

Original Tabbed Box Maker Copyright (C) 2011 elliot white
Cardboard Box Maker Copyright (C) 2024 Brad Goodman

Changelog:
14/05/2024 Brad Goodman:
    - Created from Tabbed Box Maker

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
__version__ = "1.2" ### please report bugs, suggestions etc at https://github.com/paulh-rnd/TabbedBoxMaker ###

import os,sys,inkex,simplestyle,gettext,math
from copy import deepcopy
_ = gettext.gettext

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
  #inkex.etree.SubElement(parent, inkex.addNS('path','svg'), drw)
  return line

# jslee - shamelessly adapted from sample code on below Inkscape wiki page 2015-07-28
# http://wiki.inkscape.org/wiki/index.php/Generating_objects_from_extensions
def getCircle(r, c):
    (cx, cy) = c
    log("putting circle at (%d,%d)" % (cx,cy))
    circle = inkex.PathElement.arc((cx, cy), r)
    circle.style = { 'stroke': '#000000', 'stroke-width': str(linethickness), 'fill': 'none' }
    return circle

  
# Draws each top or bottom edge
# Sidenumber is 1-4
# topside is true of top
# sidetype is the "boxbottom" or "boxtop" as applicable

def boxedge(hh,ww,dd,k2,t5,t2,sidetype,topside,sidenumber):
    h=""
    if not topside:
        # Invert offsets for bottom side
        dd *= -1
        ww *= -1
        t5 *= -1
        t2 *= -1
        k2 *= -1

    if ((sidenumber == 1) or (sidenumber == 3)):
        wd = ww
        dw = dd
    else:
        wd = dd
        dw = ww


    #if (sidetype == 1) or ((sidetype == 2) and (sidenumber != 1)):
    if (sidetype == 1):
        h+=f"l {wd+k2},0 " # Top open (plain flat side)
    else:
        if ((sidetype == 2) and (sidenumber !=1)):
            ## SPECIAL CASE - because this is a double fold (all the way down!)
            h+=f"l {t5},0 l 0,{-1*((t2*2)-(k2))} l {-1*t5},0 " # DOUBLE Leading Vertical Fold Notch
        else:
            h+=f"l {t5},0 l 0,{-1*(t2-k2)} l {-1*t5},0 " # Leading Vertical Fold Notch

        if (sidetype == 2):
            # Flat top w/ Side Folds - Full Depth top on one side, Full height on all else
            if (sidenumber == 1):
                # Top side full depth 
                h+=f"l 0,{-1*(dw+k2)} "
                # Top Tab - Fill width will be wd+k2
                #h+=f"l {wd+(k2)},0 "
                h+=f"l {t5},0 "
                h+=f"l {t2},0 l 0,{-1*(t2-k2)} l {-1*t2},0 " # Leading Vertical Fold Notch
                h+=f"l {t5},{-(hh+k2)} "
                h+=f"l {(wd+k2)-(t5*4)},0 "
                h+=f"l {t5},{(hh+k2)} "
                h+=f"l {-1*t2},0 l 0,{t2-k2} l {t2},0 " # Trailing Vertical Fold Notch
                h+=f"l {t5},0 "

                h+=f"l 0,{dw+(k2)} "
            else:
                # Side down-folds - since they are 180 degree, will have double knockouts
                h+=f"l {t2},{-1*(hh+k2)} "
                h+=f"l {wd+k2-(2*t2)},0 "
                h+=f"l {t2},{hh+(k2)} "
        else:
            # Standard fold - half depth/width on each side
            h+=f"l 0,{-1*((dw/2)+(k2))} "
            h+=f"l {wd+(k2)},0 "
            h+=f"l 0,{(dw/2)+(k2)} "

        if ((sidetype == 2) and (sidenumber !=1)):
            ## SPECIAL CASE - because this is a double fold (all the way down!)
            h+=f"l {-1*t5},0 l 0,{(2*t2)-(k2)} l {t5},0 " # Trailing Vertical Fold Notch
        else:
            h+=f"l {-1*t5},0 l 0,{t2-k2} l {t5},0 " # Trailing Vertical Fold Notch

    if ((topside) and (sidenumber != 4)) or ((not topside) and (sidenumber != 1)):
        h+=f"l 0,{t5} l {t2-(k2)},0 l 0,{-1*t5} " # Trailing Horizontal Fold Notch

    return h

class BoxMaker(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.arg_parser.add_argument('--unit',action='store',type=str,
        dest='unit',default='mm',help='Measure Units')
      self.arg_parser.add_argument('--width',action='store',type=float,
        dest='width',default=100,help='Width of Box')
      self.arg_parser.add_argument('--depth',action='store',type=float,
        dest='depth',default=100,help='Depth of Box')
      self.arg_parser.add_argument('--height',action='store',type=float,
        dest='height',default=100,help='Height of Box')
      self.arg_parser.add_argument('--hairline',action='store',type=int,
        dest='hairline',default=0,help='Line Thickness')
      self.arg_parser.add_argument('--thickness',action='store',type=float,
        dest='thickness',default=10,help='Thickness of Material')
      self.arg_parser.add_argument('--kerf',action='store',type=float,
        dest='kerf',default=0.5,help='Kerf (width of cut)')
      self.arg_parser.add_argument('--boxtype',action='store',type=int,
        dest='boxtype',default=25,help='Box type')
      self.arg_parser.add_argument('--boxtop',action='store',type=int,
        dest='boxtop',default=25,help='Box Top')
      self.arg_parser.add_argument('--boxbottom',action='store',type=int,
        dest='boxbottom',default=25,help='Box Bottom')

  def effect(self):
    global group,nomTab,equalTabs,tabSymmetry,dimpleHeight,dimpleLength,thickness,kerf,halfkerf,dogbone,divx,divy,hairline,linethickness,keydivwalls,keydivfloor
    
        # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
        # Get the attributes:
    widthDoc  = self.svg.unittouu(svg.get('width'))
    heightDoc = self.svg.unittouu(svg.get('height'))
    group = newGroup(self)
    unit=self.options.unit
    boxtop = self.options.boxtop
    boxbottom = self.options.boxbottom
    # Set the line thickness
    if self.options.hairline:
        linethickness=self.svg.unittouu('0.002in')
    else:
        linethickness=1
    h=f"M 10,10 "
    hh=self.svg.unittouu(str(self.options.height)+unit)
    ww=self.svg.unittouu(str(self.options.width)+unit)
    dd=self.svg.unittouu(str(self.options.depth)+unit)
    t2=self.svg.unittouu(str(self.options.thickness*2)+unit)
    t5=self.svg.unittouu(str(self.options.thickness*5)+unit)
    k=self.svg.unittouu(str(self.options.kerf*5)+unit)
    k2 = k

    # First Side
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxtop,True,1)
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxtop,True,2)
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxtop,True,3)
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxtop,True,4)


    ## RIGHT EDGE 

    # Straight - no tab: h+=f"l 0,{hh+k2} "

    h+=f"l 0,{t2} l {t2-(k2)},0 l 0,{-1*t2} " # Leading Vertical Fold Notch
    h+=f"l {t5+k2},{t2} "
    h+=f"l 0,{hh+k2-(2*t2)} "
    h+=f"l {-(t5+k2)},{t2} "
    h+=f"l 0,{-t2} l {-(t2-(k2))},0 l 0,{t2} " # Leading Vertical Fold Notch
                # Add tab along right edge:

    ## BOTTOM SIDE

    h+= boxedge(hh,ww,dd,k2,t5,t2,boxbottom,False,4)
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxbottom,False,3)
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxbottom,False,2)
    h+= boxedge(hh,ww,dd,k2,t5,t2,boxbottom,False,1)

    h+=f"Z"
    group.add(getLine(h))
    return
    

# Create effect instance and apply it.
effect = BoxMaker()
effect.run()
