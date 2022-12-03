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
_ = gettext.gettext

linethickness = 1 # default unless overridden by settings


# https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths

class PathSegment(object):
    def __init__(self, segtype: str, *args):
        self.type = segtype
        self.args = args

class LineSegment(PathSegment):
    def __init__(self, toX: float, toY: float) -> None:
        super().__init__('line', toX, toY)

class Circle(object):
    def __init__(self, cX: float, cY: float, r: float) -> None:
        self.centre = (cX, cY)
        self.radius = r

    def as_svg(self, inkex_group) -> None:
        inkex_group.add(getCircle(self.radius, self.centre))


class Path(object):
    """An abstract path object"""
    def __init__(self, initial_x: float, initial_y: float):
        self.initial_x = initial_x
        self.initial_y = initial_y
#        print(f'New path({self.initial_x}, {self.initial_y})')
        self.segments = []

    def __repr__(self):
        return f'Path({self.initial_x}, {self.initial_y}, segments={len(self.segments)})'

    def add(self, seg: PathSegment) -> None:
        self.segments.append(seg)

    def add_multiple(self, segs: List[PathSegment]) -> None:
        self.segments.extend(segs)

    def as_svg(self, inkex_group) -> None:
#        print(f'M {self.initial_x}, {self.initial_y} ')
        d = f'M {self.initial_x}, {self.initial_y} '
        for seg in self.segments:
            if seg.type == 'line':
                d += f'L {seg.args[0]} {seg.args[1]} '
            else:
                raise Exception(f'Unsupported segment type "{seg.type}"')
        inkex_group.add(getLine(d))

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


class TabbedBox(object):
  def __init__(self) -> None:
      self.boxtype = 1
      self.layout = 1
      self.thickness = 0
      self.inside = False
      self.dimpleHeight = 0
      self.dimpleLength = 0
      self.spacing = 0

      self.kerf = 0
      self.dogbone = 0

      self.nomTab = 0
      self.equalTabs = False
      self.tabSymmetry = 0

      self.divx = 0
      self.divy = 0
      self.keydivwalls = 0
      self.keydivfloor = 0

      # Schroff?
      self.schroff = False
      self.rows = 0
      self.rail_height = 0
      self.row_centre_spacing = 0
      self.row_spacing = 0
      self.rail_mount_depth = 0
      self.rail_mount_centre_offset = 0
      self.rail_mount_radius = 0

  def dimple(self, tabVector,vectorX,vectorY,dirX,dirY,dirxN,diryN,ddir,isTab) -> List[PathSegment]:
    segs = []
    if not isTab:
      ddir = -ddir
    if self.dimpleHeight>0 and tabVector!=0:
      if tabVector>0:
        dimpleStart=(tabVector-self.dimpleLength)/2-self.dimpleHeight
        tabSgn=1
      else:
        dimpleStart=(tabVector+self.dimpleLength)/2+self.dimpleHeight
        tabSgn=-1
      Vxd=vectorX+dirxN*dimpleStart
      Vyd=vectorY+diryN*dimpleStart
      segs.append(LineSegment(Vxd, Vyd))
      Vxd=Vxd+(tabSgn*dirxN-ddir*dirX)*self.dimpleHeight
      Vyd=Vyd+(tabSgn*diryN-ddir*dirY)*self.dimpleHeight
      segs.append(LineSegment(Vxd, Vyd))
      Vxd=Vxd+tabSgn*dirxN*self.dimpleLength
      Vyd=Vyd+tabSgn*diryN*self.dimpleLength
      segs.append(LineSegment(Vxd, Vyd))
      Vxd=Vxd+(tabSgn*dirxN+ddir*dirX)*self.dimpleHeight
      Vyd=Vyd+(tabSgn*diryN+ddir*dirY)*self.dimpleHeight
      segs.append(LineSegment(Vxd, Vyd))
    return segs

  def side(self, root,startOffset,endOffset,tabVec,length,direction,isTab,isDivider,numDividers,dividerSpacing) -> List[Path]:
    rootX, rootY = root
    startOffsetX, startOffsetY = startOffset
    endOffsetX, endOffsetY = endOffset
    dirX, dirY = direction
    notTab=0 if isTab else 1

    halfkerf = self.kerf/2

    if (self.tabSymmetry==1):        # waffle-block style rotationally symmetric tabs
        divisions=int((length-2*self.thickness)/self.nomTab)
        if divisions%2: divisions+=1      # make divs even
        divisions=float(divisions)
        tabs=divisions/2                  # tabs for side
    else:
        divisions=int(length/self.nomTab)
        if not divisions%2: divisions-=1  # make divs odd
        divisions=float(divisions)
        tabs=(divisions-1)/2              # tabs for side

    if (self.tabSymmetry==1):        # waffle-block style rotationally symmetric tabs
      gapWidth=tabWidth=(length-2*self.thickness)/divisions
    elif self.equalTabs:
      gapWidth=tabWidth=length/divisions
    else:
      tabWidth=self.nomTab
      gapWidth=(length-tabs*self.nomTab)/(divisions-tabs)

    if isTab:                 # kerf correction
      gapWidth-=self.kerf
      tabWidth+=self.kerf
      first=halfkerf
    else:
      gapWidth+=self.kerf
      tabWidth-=self.kerf
      first=-halfkerf
    firstholelenX=0
    firstholelenY=0
    firstVec=0; secondVec=tabVec
    dividerEdgeOffsetX = dividerEdgeOffsetY = self.thickness
    notDirX=0 if dirX else 1 # used to select operation on x or y
    notDirY=0 if dirY else 1
    paths = []
    p = None
    if (self.tabSymmetry==1):
      dividerEdgeOffsetX = dirX*self.thickness;
      #dividerEdgeOffsetY = ;
      vectorX = rootX + (startOffsetX*self.thickness if notDirX else 0)
#      print(f'startofsX={startOffsetX} thickness={self.thickness}')
      vectorY = rootY + (startOffsetY*self.thickness if notDirY else 0)
#      print(f'startofsY={startOffsetY} thickness={self.thickness}')
#      print(f'Path({vectorX}, {vectorY})')
      p = Path(vectorX, vectorY)
      vectorX = rootX+(startOffsetX if startOffsetX else dirX)*self.thickness
      vectorY = rootY+(startOffsetY if startOffsetY else dirY)*self.thickness
      if notDirX: endOffsetX=0
      if notDirY: endOffsetY=0
    else:
      (vectorX,vectorY)=(rootX+startOffsetX*self.thickness,rootY+startOffsetY*self.thickness)
#      print(f'startofsY={startOffsetY} thickness={self.thickness} vectorY={vectorY}')
      dividerEdgeOffsetX=dirY*self.thickness
      dividerEdgeOffsetY=dirX*self.thickness
#      print(f'else Path({vectorX}, {vectorY})')
      p = Path(vectorX, vectorY)
      if notDirX: vectorY=rootY # set correct line start for tab generation
      if notDirY: vectorX=rootX

    # generate line as tab or hole using:
    #   last co-ord:Vx,Vy ; tab dir:tabVec  ; direction:dirx,diry ; thickness:thickness
    #   divisions:divs ; gap width:gapWidth ; tab width:tabWidth

    for tabDivision in range(1,int(divisions)):
      if ((tabDivision%2) ^ (not isTab)) and numDividers>0 and not isDivider: # draw holes for divider tabs to key into side walls
        w=gapWidth if isTab else tabWidth
        if tabDivision==1 and self.tabSymmetry==0:
          w-=startOffsetX*self.thickness
        holeLenX=dirX*w+notDirX*firstVec+first*dirX
        holeLenY=dirY*w+notDirY*firstVec+first*dirY
        if first:
          firstholelenX=holeLenX
          firstholelenY=holeLenY
        for dividerNumber in range(1,int(numDividers)+1):
          Dx=vectorX+-dirY*dividerSpacing*dividerNumber+notDirX*halfkerf+dirX*self.dogbone*halfkerf-self.dogbone*first*dirX
          Dy=vectorY+dirX*dividerSpacing*dividerNumber-notDirY*halfkerf+dirY*self.dogbone*halfkerf-self.dogbone*first*dirY
          if tabDivision==1 and self.tabSymmetry==0:
            Dx+=startOffsetX*self.thickness
          hole = Path(Dx, Dy)
          Dx=Dx+holeLenX
          Dy=Dy+holeLenY
          hole.add(LineSegment(Dx, Dy))
          Dx=Dx+notDirX*(secondVec-self.kerf)
          Dy=Dy+notDirY*(secondVec+self.kerf)
          hole.add(LineSegment(Dx, Dy))
          Dx=Dx-holeLenX
          Dy=Dy-holeLenY
          hole.add(LineSegment(Dx, Dy))
          Dx=Dx-notDirX*(secondVec-self.kerf)
          Dy=Dy-notDirY*(secondVec+self.kerf)
          hole.add(LineSegment(Dx, Dy))
          paths.append(hole)
      if tabDivision%2:
        if tabDivision==1 and numDividers>0 and isDivider: # draw slots for dividers to slot into each other
          for dividerNumber in range(1,int(numDividers)+1):
            Dx=vectorX+-dirY*dividerSpacing*dividerNumber-dividerEdgeOffsetX+notDirX*halfkerf
            Dy=vectorY+dirX*dividerSpacing*dividerNumber-dividerEdgeOffsetY+notDirY*halfkerf
            hole = Path(Dx, Dy)
            Dx=Dx+dirX*(first+length/2)
            Dy=Dy+dirY*(first+length/2)
            hole.add(LineSegment(Dx, Dy))
            Dx=Dx+notDirX*(self.thickness-self.kerf)
            Dy=Dy+notDirY*(self.thickness-self.kerf)
            hole.add(LineSegment(Dx, Dy))
            Dx=Dx-dirX*(first+length/2)
            Dy=Dy-dirY*(first+length/2)
            hole.add(LineSegment(Dx, Dy))
            Dx=Dx-notDirX*(self.thickness-self.kerf)
            Dy=Dy-notDirY*(self.thickness-self.kerf)
            hole.add(LineSegment(Dx, Dy))
            paths.append(hole)
        # draw the gap
        vectorX+=dirX*(gapWidth+(isTab&self.dogbone&1 ^ 0x1)*first+self.dogbone*self.kerf*isTab)+notDirX*firstVec
        vectorY+=dirY*(gapWidth+(isTab&self.dogbone&1 ^ 0x1)*first+self.dogbone*self.kerf*isTab)+notDirY*firstVec
        p.add(LineSegment(vectorX, vectorY))
        if self.dogbone and isTab:
          vectorX-=dirX*halfkerf
          vectorY-=dirY*halfkerf
          p.add(LineSegment(vectorX, vectorY))
        # draw the starting edge of the tab
        p.add_multiple(self.dimple(secondVec,vectorX,vectorY,dirX,dirY,notDirX,notDirY,1,isTab))
        vectorX+=notDirX*secondVec
        vectorY+=notDirY*secondVec
        p.add(LineSegment(vectorX, vectorY))
        if self.dogbone and notTab:
          vectorX-=dirX*halfkerf
          vectorY-=dirY*halfkerf
          p.add(LineSegment(vectorX, vectorY))
      else:
        # draw the tab
        vectorX+=dirX*(tabWidth+self.dogbone*self.kerf*notTab)+notDirX*firstVec
        vectorY+=dirY*(tabWidth+self.dogbone*self.kerf*notTab)+notDirY*firstVec
        p.add(LineSegment(vectorX, vectorY))
        if self.dogbone and notTab:
          vectorX-=dirX*halfkerf
          vectorY-=dirY*halfkerf
          p.add(LineSegment(vectorX, vectorY))
        # draw the ending edge of the tab
        p.add_multiple(self.dimple(secondVec,vectorX,vectorY,dirX,dirY,notDirX,notDirY,-1,isTab))
        vectorX+=notDirX*secondVec
        vectorY+=notDirY*secondVec
        p.add(LineSegment(vectorX, vectorY))
        if self.dogbone and isTab:
          vectorX-=dirX*halfkerf
          vectorY-=dirY*halfkerf
          p.add(LineSegment(vectorX, vectorY))
      (secondVec,firstVec)=(-secondVec,-firstVec) # swap tab direction
      first=0

    #finish the line off
    p.add(LineSegment(rootX+endOffsetX*self.thickness+dirX*length, rootY+endOffsetY*self.thickness+dirY*length))

    if isTab and numDividers>0 and self.tabSymmetry==0 and not isDivider: # draw last for divider joints in side walls
      for dividerNumber in range(1,int(numDividers)+1):
        Dx=vectorX+-dirY*dividerSpacing*dividerNumber+notDirX*halfkerf+dirX*self.dogbone*halfkerf-self.dogbone*first*dirX
        # Dy=vectorY+dirX*dividerSpacing*dividerNumber-notDirY*halfkerf+dirY*dogbone*halfkerf-dogbone*first*dirY
        # Dx=vectorX+-dirY*dividerSpacing*dividerNumber-dividerEdgeOffsetX+notDirX*halfkerf
        Dy=vectorY+dirX*dividerSpacing*dividerNumber-dividerEdgeOffsetY+notDirY*halfkerf
        hole = Path(Dx, Dy)
        Dx=Dx+firstholelenX
        Dy=Dy+firstholelenY
        hole.add(LineSegment(Dx, Dy))
        Dx=Dx+notDirX*(self.thickness-self.kerf)
        Dy=Dy+notDirY*(self.thickness-self.kerf)
        hole.add(LineSegment(Dx, Dy))
        Dx=Dx-firstholelenX
        Dy=Dy-firstholelenY
        hole.add(LineSegment(Dx, Dy))
        Dx=Dx-notDirX*(self.thickness-self.kerf)
        Dy=Dy-notDirY*(self.thickness-self.kerf)
        hole.add(LineSegment(Dx, Dy))
        paths.append(hole)
      # for dividerNumber in range(1,int(numDividers)+1):
      #   Dx=vectorX+-dirY*dividerSpacing*dividerNumber+notDirX*halfkerf+dirX*dogbone*halfkerf
      #   Dy=vectorY+dirX*dividerSpacing*dividerNumber-notDirY*halfkerf+dirY*dogbone*halfkerf
      #   # Dx=vectorX+dirX*dogbone*halfkerf
      #   # Dy=vectorY+dirX*dividerSpacing*dividerNumber-dirX*halfkerf+dirY*dogbone*halfkerf
      #   h='M '+str(Dx)+','+str(Dy)+' '
      #   Dx=rootX+endOffsetX*thickness+dirX*length
      #   Dy+=dirY*tabWidth+notDirY*firstVec+first*dirY
      #   h+='L '+str(Dx)+','+str(Dy)+' '
      #   Dx+=notDirX*(secondVec-kerf)
      #   Dy+=notDirY*(secondVec+kerf)
      #   h+='L '+str(Dx)+','+str(Dy)+' '
      #   Dx-=vectorX
      #   Dy-=(dirY*tabWidth+notDirY*firstVec+first*dirY)
      #   h+='L '+str(Dx)+','+str(Dy)+' '
      #   Dx-=notDirX*(secondVec-kerf)
      #   Dy-=notDirY*(secondVec+kerf)
      #   h+='L '+str(Dx)+','+str(Dy)+' '
      #   group.add(getLine(h))
    paths.append(p)
#    print(f'paths={paths}')
    return paths

  def make(self, X: float, Y: float, Z: float) -> List[List[Path]]:
    # For code spacing consistency, we use two-character abbreviations for the six box faces,
    # where each abbreviation is the first and last letter of the face name:
    # tp=top, bm=bottom, ft=front, bk=back, lt=left, rt=right

    # Determine which faces the box has based on the box type
    hasTp=hasBm=hasFt=hasBk=hasLt=hasRt = True
    if   self.boxtype==2: hasTp=False
    elif self.boxtype==3: hasTp=hasFt=False
    elif self.boxtype==4: hasTp=hasFt=hasRt=False
    elif self.boxtype==5: hasTp=hasBm=False
    elif self.boxtype==6: hasTp=hasFt=hasBk=hasRt=False
    # else self.boxtype==1, full box, has all sides

    initOffsetX=0
    initOffsetY=0

    # Determine where the tabs go based on the tab style
    if self.tabSymmetry==2:     # Antisymmetric (deprecated)
      tpTabInfo=0b0110
      bmTabInfo=0b1100
      ltTabInfo=0b1100
      rtTabInfo=0b0110
      ftTabInfo=0b1100
      bkTabInfo=0b1001
    elif self.tabSymmetry==1:   # Rotationally symmetric (Waffle-blocks)
      tpTabInfo=0b1111
      bmTabInfo=0b1111
      ltTabInfo=0b1111
      rtTabInfo=0b1111
      ftTabInfo=0b1111
      bkTabInfo=0b1111
    else:               # XY symmetric
      tpTabInfo=0b0000
      bmTabInfo=0b0000
      ltTabInfo=0b1111
      rtTabInfo=0b1111
      ftTabInfo=0b1010
      bkTabInfo=0b1010

    def fixTabBits(tabbed, tabInfo, bit):
        newTabbed = tabbed & ~bit
        if self.inside:
          newTabInfo = tabInfo | bit      # set bit to 1 to use tab base line
        else:
          newTabInfo = tabInfo & ~bit     # set bit to 0 to use tab tip line
        return newTabbed, newTabInfo

    # Update the tab bits based on which sides of the box don't exist
    tpTabbed=bmTabbed=ltTabbed=rtTabbed=ftTabbed=bkTabbed=0b1111
    if not hasTp:
      bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b0010)
      ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b1000)
      ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b0001)
      rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b0100)
      tpTabbed=0
    if not hasBm:
      bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b1000)
      ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b0010)
      ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b0100)
      rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b0001)
      bmTabbed=0
    if not hasFt:
      tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b1000)
      bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b1000)
      ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b1000)
      rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b1000)
      ftTabbed=0
    if not hasBk:
      tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b0010)
      bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b0010)
      ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b0010)
      rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b0010)
      bkTabbed=0
    if not hasLt:
      tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b0100)
      bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b0001)
      bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b0001)
      ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b0001)
      ltTabbed=0
    if not hasRt:
      tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b0001)
      bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b0100)
      bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b0100)
      ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b0100)
      rtTabbed=0

    # Layout positions are specified in a grid of rows and columns
    row0=(1,0,0,0)      # top row
    row1y=(2,0,1,0)     # second row, offset by Y
    row1z=(2,0,0,1)     # second row, offset by Z
    row2=(3,0,1,1)      # third row, always offset by Y+Z

    col0=(1,0,0,0)      # left column
    col1x=(2,1,0,0)     # second column, offset by X
    col1z=(2,0,0,1)     # second column, offset by Z
    col2xx=(3,2,0,0)    # third column, offset by 2*X
    col2xz=(3,1,0,1)    # third column, offset by X+Z
    col3xzz=(4,1,0,2)   # fourth column, offset by X+2*Z
    col3xxz=(4,2,0,1)   # fourth column, offset by 2*X+Z
    col4=(5,2,0,2)      # fifth column, always offset by 2*X+2*Z
    col5=(6,3,0,2)      # sixth column, always offset by 3*X+2*Z

    # layout format:(rootx),(rooty),Xlength,Ylength,tabInfo,tabbed,pieceType
    # root= (spacing,X,Y,Z) * values in tuple
    # tabInfo= <abcd> 0=holes 1=tabs
    # tabbed= <abcd> 0=no tabs 1=tabs on this side
    # (sides: a=top, b=right, c=bottom, d=left)
    # pieceType: 1=XY, 2=XZ, 3=ZY
    tpFace=1
    bmFace=1
    ftFace=2
    bkFace=2
    ltFace=3
    rtFace=3

    def reduceOffsets(aa, start, dx, dy, dz):
      for ix in range(start+1,len(aa)):
        (s,x,y,z) = aa[ix]
        aa[ix] = (s-1, x-dx, y-dy, z-dz)

    # note first two pieces in each set are the X-divider template and Y-divider template respectively
    pieces=[]
    if   self.layout==1: # Diagramatic Layout
      rr = deepcopy([row0, row1z, row2])
      cc = deepcopy([col0, col1z, col2xz, col3xzz])
      if not hasFt: reduceOffsets(rr, 0, 0, 0, 1)     # remove row0, shift others up by Z
      if not hasLt: reduceOffsets(cc, 0, 0, 0, 1)
      if not hasRt: reduceOffsets(cc, 2, 0, 0, 1)
      if hasBk: pieces.append([cc[1], rr[2], X,Z, bkTabInfo, bkTabbed, bkFace])
      if hasLt: pieces.append([cc[0], rr[1], Z,Y, ltTabInfo, ltTabbed, ltFace])
      if hasBm: pieces.append([cc[1], rr[1], X,Y, bmTabInfo, bmTabbed, bmFace])
      if hasRt: pieces.append([cc[2], rr[1], Z,Y, rtTabInfo, rtTabbed, rtFace])
      if hasTp: pieces.append([cc[3], rr[1], X,Y, tpTabInfo, tpTabbed, tpFace])
      if hasFt: pieces.append([cc[1], rr[0], X,Z, ftTabInfo, ftTabbed, ftFace])
    elif self.layout==2: # 3 Piece Layout
      rr = deepcopy([row0, row1y])
      cc = deepcopy([col0, col1z])
      if hasBk: pieces.append([cc[1], rr[1], X,Z, bkTabInfo, bkTabbed, bkFace])
      if hasLt: pieces.append([cc[0], rr[0], Z,Y, ltTabInfo, ltTabbed, ltFace])
      if hasBm: pieces.append([cc[1], rr[0], X,Y, bmTabInfo, bmTabbed, bmFace])
    elif self.layout==3: # Inline(compact) Layout
      rr = deepcopy([row0])
      cc = deepcopy([col0, col1x, col2xx, col3xxz, col4, col5])
      if not hasTp: reduceOffsets(cc, 0, 1, 0, 0)     # remove col0, shift others left by X
      if not hasBm: reduceOffsets(cc, 1, 1, 0, 0)
      if not hasLt: reduceOffsets(cc, 2, 0, 0, 1)
      if not hasRt: reduceOffsets(cc, 3, 0, 0, 1)
      if not hasBk: reduceOffsets(cc, 4, 1, 0, 0)
      if hasBk: pieces.append([cc[4], rr[0], X,Z, bkTabInfo, bkTabbed, bkFace])
      if hasLt: pieces.append([cc[2], rr[0], Z,Y, ltTabInfo, ltTabbed, ltFace])
      if hasTp: pieces.append([cc[0], rr[0], X,Y, tpTabInfo, tpTabbed, tpFace])
      if hasBm: pieces.append([cc[1], rr[0], X,Y, bmTabInfo, bmTabbed, bmFace])
      if hasRt: pieces.append([cc[3], rr[0], Z,Y, rtTabInfo, rtTabbed, rtFace])
      if hasFt: pieces.append([cc[5], rr[0], X,Z, ftTabInfo, ftTabbed, ftFace])

    groups = []
    for idx, piece in enumerate(pieces): # generate and draw each piece of the box
      (xs,xx,xy,xz)=piece[0]
      (ys,yx,yy,yz)=piece[1]
      x=xs*self.spacing+xx*X+xy*Y+xz*Z+initOffsetX  # root x co-ord for piece
      y=ys*self.spacing+yx*X+yy*Y+yz*Z+initOffsetY  # root y co-ord for piece
      dx=piece[2]
      dy=piece[3]
      tabs=piece[4]
      a=tabs>>3&1; b=tabs>>2&1; c=tabs>>1&1; d=tabs&1 # extract tab status for each side
      tabbed=piece[5]
      atabs=tabbed>>3&1; btabs=tabbed>>2&1; ctabs=tabbed>>1&1; dtabs=tabbed&1 # extract tabbed flag for each side
      xspacing=(X-self.thickness)/(self.divy+1)
      yspacing=(Y-self.thickness)/(self.divx+1)
      xholes = 1 if piece[6]<3 else 0
      yholes = 1 if piece[6]!=2 else 0
      wall = 1 if piece[6]>1 else 0
      floor = 1 if piece[6]==1 else 0
      railholes = 1 if piece[6]==3 else 0

      sides = []
      groups.append(sides)

      if self.schroff and railholes:
        log("rail holes enabled on piece %d at (%d, %d)" % (idx, x+self.thickness,y+self.thickness))
        log("abcd = (%d,%d,%d,%d)" % (a,b,c,d))
        log("dxdy = (%d,%d)" % (dx,dy))
        rhxoffset = self.rail_mount_depth + self.thickness
        if idx == 1:
          rhx=x+rhxoffset
        elif idx == 3:
          rhx=x-rhxoffset+dx
        else:
          rhx=0
        log("rhxoffset = %d, rhx= %d" % (rhxoffset, rhx))
        rystart=y+(self.rail_height/2)+self.thickness
        if self.rows == 1:
          log("just one row this time, rystart = %d" % rystart)
          rh1y=rystart+self.rail_mount_centre_offset
          rh2y=rh1y+(self.row_centre_spacing-self.rail_mount_centre_offset)
          groups.append(Circle(self.rail_mount_radius,(rhx,rh1y)))
          groups.append(Circle(self.rail_mount_radius,(rhx,rh2y)))
        else:
          for n in range(0, self.rows):
            log("drawing row %d, rystart = %d" % (n+1, rystart))
            # if holes areo ffset (eg. Vector T-strut rails), they should be offset
            # toward each other, ie. toward the centreline of the Schroff row
            rh1y=rystart+self.rail_mount_centre_offset
            rh2y=rh1y+self.row_centre_spacing-self.rail_mount_centre_offset
            groups.append(Circle(self.rail_mount_radius,(rhx,rh1y)))
            group.append(Circle(self.rail_mount_radius,(rhx,rh2y)))
            rystart+=self.row_centre_spacing+self.row_spacing+self.rail_height

      # generate and draw the sides of each piece
      sides.extend( # side a
        self.side((x,y), (d,a), (-b,a), atabs * (-self.thickness if a else self.thickness),
                  dx, (1,0), a, 0,
                  (self.keydivfloor|wall) * (self.keydivwalls|floor) * self.divx*yholes*atabs,
                  yspacing)
      )
      sides.extend(
        self.side((x+dx,y),(-b,a),(-b,-c),btabs * (self.thickness if b else -self.thickness),dy,(0,1),b,0,(self.keydivfloor|wall) * (self.keydivwalls|floor) * self.divy*xholes*btabs,xspacing)     # side b
      )
      if atabs:
          sides.extend(
            self.side((x+dx,y+dy),(-b,-c),(d,-c),ctabs * (self.thickness if c else -self.thickness),dx,(-1,0),c,0,0,0) # side c
          )
      else:
          sides.extend(
            self.side((x+dx,y+dy),(-b,-c),(d,-c),ctabs * (self.thickness if c else -self.thickness),dx,(-1,0),c,0,(self.keydivfloor|wall) * (self.keydivwalls|floor) * self.divx*yholes*ctabs,yspacing) # side c
          )
      if btabs:
        sides.extend(
          self.side((x,y+dy),(d,-c),(d,a),dtabs * (-self.thickness if d else self.thickness),dy,(0,-1),d,0,0,0)      # side d
        )
      else:
        sides.extend(
          self.side((x,y+dy),(d,-c),(d,a),dtabs * (-self.thickness if d else self.thickness),dy,(0,-1),d,0,(self.keydivfloor|wall) * (self.keydivwalls|floor) * self.divy*xholes*dtabs,xspacing)      # side d
        )

      if idx==0:
        # remove tabs from dividers if not required
        if not self.keydivfloor:
          a=c=1
          atabs=ctabs=0
        if not self.keydivwalls:
          b=d=1
          btabs=dtabs=0

        y=4*self.spacing+1*Y+2*Z  # root y co-ord for piece
        for n in range(0,self.divx): # generate X dividers
          #group = newGroup(self)
          tab = []
          groups.append(tab)
          x=n*(self.spacing+X)  # root x co-ord for piece
          tab.extend(
            self.side((x,y),(d,a),(-b,a),self.keydivfloor*atabs*(-self.thickness if a else self.thickness),dx,(1,0),a,1,0,0)          # side a
          )
          tab.extend(
            self.side((x+dx,y),(-b,a),(-b,-c),self.keydivwalls*btabs*(self.thickness if b else -self.thickness),dy,(0,1),b,1,self.divy*xholes,xspacing)    # side b
          )
          tab.extend(
            self.side((x+dx,y+dy),(-b,-c),(d,-c),self.keydivfloor*ctabs*(self.thickness if c else -self.thickness),dx,(-1,0),c,1,0,0) # side c
          )
          tab.extend(
            self.side((x,y+dy),(d,-c),(d,a),self.keydivwalls*dtabs*(-self.thickness if d else self.thickness),dy,(0,-1),d,1,0,0)      # side d
          )
      elif idx==1:
        y=5*self.spacing+1*Y+3*Z  # root y co-ord for piece
        for n in range(0,self.divy): # generate Y dividers
          #group = newGroup(self)
          tab = []
          groups.append(tab)
          x=n*(self.spacing+Z)  # root x co-ord for piece
          tab.extend(
            self.side((x,y),(d,a),(-b,a),self.keydivwalls*atabs*(-self.thickness if a else self.thickness),dx,(1,0),a,1,self.divx*yholes,yspacing)          # side a
          )
          tab.extend(
            self.side((x+dx,y),(-b,a),(-b,-c),self.keydivfloor*btabs*(self.thickness if b else -self.thickness),dy,(0,1),b,1,0,0)     # side b
          )
          tab.extend(
            self.side((x+dx,y+dy),(-b,-c),(d,-c),self.keydivwalls*ctabs*(self.thickness if c else -self.thickness),dx,(-1,0),c,1,0,0) # side c
          )
          tab.extend(
            self.side((x,y+dy),(d,-c),(d,a),self.keydivfloor*dtabs*(-self.thickness if d else self.thickness),dy,(0,-1),d,1,0,0)      # side d
          )
    return groups



class InkexBoxMaker(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
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

  def effect(self):
#    global group,nomTab,equalTabs,tabSymmetry,dimpleHeight,dimpleLength,thickness
#    global kerf,halfkerf,dogbone,divx,divy,hairline,linethickness,keydivwalls,keydivfloor
    global linethickness

        # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    box = TabbedBox()

        # Get the attributes:
    widthDoc  = self.svg.unittouu(svg.get('width'))
    heightDoc = self.svg.unittouu(svg.get('height'))

    # Get script's option values.
    hairline=self.options.hairline
    unit=self.options.unit
    box.inside=self.options.inside
    box.schroff=self.options.schroff
    box.kerf = self.svg.unittouu( str(self.options.kerf)  + unit )

    # Set the line thickness
    if hairline:
        linethickness=self.svg.unittouu('0.002in')
    else:
        linethickness=1

    if box.schroff:
        box.rows=self.options.rows
        box.rail_height=self.svg.unittouu(str(self.options.rail_height)+unit)
        box.row_centre_spacing=self.svg.unittouu(str(122.5)+unit)
        box.row_spacing=self.svg.unittouu(str(self.options.row_spacing)+unit)
        box.rail_mount_depth=self.svg.unittouu(str(self.options.rail_mount_depth)+unit)
        box.rail_mount_centre_offset=self.svg.unittouu(str(self.options.rail_mount_centre_offset)+unit)
        box.rail_mount_radius=self.svg.unittouu(str(2.5)+unit)

    ## minimally different behaviour for schroffmaker.inx vs. boxmaker.inx
    ## essentially schroffmaker.inx is just an alternate interface with different
    ## default settings, some options removed, and a tiny amount of extra logic
    if box.schroff:
        ## schroffmaker.inx
        X = self.svg.unittouu(str(self.options.hp * 5.08) + unit)
        # 122.5mm vertical distance between mounting hole centres of 3U Schroff panels
        row_height = rows * (box.row_centre_spacing + box.rail_height)
        # rail spacing in between rows but never between rows and case panels
        row_spacing_total = (box.rows - 1) * box.row_spacing
        Y = row_height + row_spacing_total
    else:
        ## boxmaker.inx
        X = self.svg.unittouu( str(self.options.length + box.kerf)  + unit )
        Y = self.svg.unittouu( str(self.options.width + box.kerf) + unit )

    Z = self.svg.unittouu( str(self.options.height + box.kerf)  + unit )
    box.thickness = self.svg.unittouu( str(self.options.thickness)  + unit )
    box.nomTab = self.svg.unittouu( str(self.options.tab) + unit )
    box.equalTabs=self.options.equal
    box.tabSymmetry=self.options.tabsymmetry
    box.dimpleHeight=self.options.dimpleheight
    box.dimpleLength=self.options.dimplelength
    box.dogbone = 1 if self.options.tabtype == 1 else 0
    box.layout=self.options.style
    box.spacing = self.svg.unittouu( str(self.options.spacing)  + unit )
    box.boxtype = self.options.boxtype
    box.divx = self.options.div_l
    box.divy = self.options.div_w
    box.keydivwalls = 0 if self.options.keydiv == 3 or self.options.keydiv == 1 else 1
    box.keydivfloor = 0 if self.options.keydiv == 3 or self.options.keydiv == 2 else 1

    if box.inside: # if inside dimension selected correct values to outside dimension
      X+=box.thickness*2
      Y+=box.thickness*2
      Z+=box.thickness*2

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
    if min(X,Y,Z)<3*box.nomTab:
      inkex.errormsg(_('Error: Tab size too large'))
      error=1
    if box.nomTab<box.thickness:
      inkex.errormsg(_('Error: Tab size too small'))
      error=1
    if box.thickness==0:
      inkex.errormsg(_('Error: Thickness is zero'))
      error=1
    if box.thickness>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Material too thick'))
      error=1
    if box.kerf>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Kerf too large'))
      error=1
    if box.spacing>max(X,Y,Z)*10: # crude test
      inkex.errormsg(_('Error: Spacing too large'))
      error=1
    if box.spacing<box.kerf:
      inkex.errormsg(_('Error: Spacing too small'))
      error=1

    if error: exit()

    groups = box.make(X, Y, Z)
#    print(f'groups={groups}')
    for group in groups:
        inkex_grp = newGroup(self)
        for path in group:
            path.as_svg(inkex_grp)

if __name__ == '__main__':
  # Create effect instance and apply it.
  effect = InkexBoxMaker()
  effect.run()
