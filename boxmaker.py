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

def dimpleStr(tabVector,vectorX,vectorY,dirX,dirY,dirxN,diryN,ddir,isTab):
  ds=''
  if not isTab:
    ddir = -ddir
  if dimpleHeight>0 and tabVector!=0:
    if tabVector>0:
      dimpleStart=(tabVector-dimpleLength)/2-dimpleHeight
      tabSgn=1
    else:
      dimpleStart=(tabVector+dimpleLength)/2+dimpleHeight
      tabSgn=-1
    Vxd=vectorX+dirxN*dimpleStart
    Vyd=vectorY+diryN*dimpleStart
    ds+='L '+str(Vxd)+','+str(Vyd)+' '
    Vxd=Vxd+(tabSgn*dirxN-ddir*dirX)*dimpleHeight
    Vyd=Vyd+(tabSgn*diryN-ddir*dirY)*dimpleHeight
    ds+='L '+str(Vxd)+','+str(Vyd)+' '
    Vxd=Vxd+tabSgn*dirxN*dimpleLength
    Vyd=Vyd+tabSgn*diryN*dimpleLength
    ds+='L '+str(Vxd)+','+str(Vyd)+' '
    Vxd=Vxd+(tabSgn*dirxN+ddir*dirX)*dimpleHeight
    Vyd=Vyd+(tabSgn*diryN+ddir*dirY)*dimpleHeight
    ds+='L '+str(Vxd)+','+str(Vyd)+' '
  return ds

def side(group,root,startOffset,endOffset,tabVec,prevTab,length,direction,isTab,isDivider,numDividers,dividerSpacing):
  rootX, rootY = root
  startOffsetX, startOffsetY = startOffset
  endOffsetX, endOffsetY = endOffset
  dirX, dirY = direction
  notTab=0 if isTab else 1

  if (tabSymmetry==1):        # waffle-block style rotationally symmetric tabs
      divisions=int((length-2*thickness)/nomTab)
      if divisions%2: divisions+=1      # make divs even
      divisions=float(divisions)
      tabs=divisions/2                  # tabs for side
  else:
      divisions=int(length/nomTab)
      if not divisions%2: divisions-=1  # make divs odd
      divisions=float(divisions)
      tabs=(divisions-1)/2              # tabs for side
  
  if (tabSymmetry==1):        # waffle-block style rotationally symmetric tabs
    gapWidth=tabWidth=(length-2*thickness)/divisions
  elif equalTabs:
    gapWidth=tabWidth=length/divisions
  else:
    tabWidth=nomTab
    gapWidth=(length-tabs*nomTab)/(divisions-tabs)
    
  if isTab:                 # kerf correction
    gapWidth-=kerf
    tabWidth+=kerf
    first=halfkerf
  else:
    gapWidth+=kerf
    tabWidth-=kerf
    first=-halfkerf
  firstholelenX=0
  firstholelenY=0
  s=[] 
  h=[]
  firstVec=0; secondVec=tabVec
  dividerEdgeOffsetX = dividerEdgeOffsetY = thickness
  notDirX=0 if dirX else 1 # used to select operation on x or y
  notDirY=0 if dirY else 1
  if (tabSymmetry==1):
    dividerEdgeOffsetX = dirX*thickness;
    #dividerEdgeOffsetY = ;
    vectorX = rootX + (0 if dirX and prevTab else startOffsetX*thickness)
    vectorY = rootY + (0 if dirY and prevTab else startOffsetY*thickness)
    s='M '+str(vectorX)+','+str(vectorY)+' '
    vectorX = rootX+(startOffsetX if startOffsetX else dirX)*thickness
    vectorY = rootY+(startOffsetY if startOffsetY else dirY)*thickness
    if notDirX and tabVec: endOffsetX=0
    if notDirY and tabVec: endOffsetY=0
  else:
    (vectorX,vectorY)=(rootX+startOffsetX*thickness,rootY+startOffsetY*thickness)
    dividerEdgeOffsetX=dirY*thickness
    dividerEdgeOffsetY=dirX*thickness
    s='M '+str(vectorX)+','+str(vectorY)+' '
    if notDirX: vectorY=rootY # set correct line start for tab generation
    if notDirY: vectorX=rootX

  # generate line as tab or hole using:
  #   last co-ord:Vx,Vy ; tab dir:tabVec  ; direction:dirx,diry ; thickness:thickness
  #   divisions:divs ; gap width:gapWidth ; tab width:tabWidth

  for tabDivision in range(1,int(divisions)):
    if ((tabDivision%2) ^ (not isTab)) and numDividers>0 and not isDivider: # draw holes for divider tabs to key into side walls
      w=gapWidth if isTab else tabWidth
      if tabDivision==1 and tabSymmetry==0:
        w-=startOffsetX*thickness
      holeLenX=dirX*w+notDirX*firstVec+first*dirX
      holeLenY=dirY*w+notDirY*firstVec+first*dirY
      if first:
        firstholelenX=holeLenX
        firstholelenY=holeLenY
      for dividerNumber in range(1,int(numDividers)+1):
        Dx=vectorX+-dirY*dividerSpacing*dividerNumber+notDirX*halfkerf+dirX*dogbone*halfkerf-dogbone*first*dirX
        Dy=vectorY+dirX*dividerSpacing*dividerNumber-notDirY*halfkerf+dirY*dogbone*halfkerf-dogbone*first*dirY
        if tabDivision==1 and tabSymmetry==0:
          Dx+=startOffsetX*thickness
        h='M '+str(Dx)+','+str(Dy)+' '
        Dx=Dx+holeLenX
        Dy=Dy+holeLenY
        h+='L '+str(Dx)+','+str(Dy)+' '
        Dx=Dx+notDirX*(secondVec-kerf)
        Dy=Dy+notDirY*(secondVec+kerf)
        h+='L '+str(Dx)+','+str(Dy)+' '
        Dx=Dx-holeLenX
        Dy=Dy-holeLenY
        h+='L '+str(Dx)+','+str(Dy)+' '
        Dx=Dx-notDirX*(secondVec-kerf)
        Dy=Dy-notDirY*(secondVec+kerf)
        h+='L '+str(Dx)+','+str(Dy)+' '
        group.add(getLine(h))
    if tabDivision%2:
      if tabDivision==1 and numDividers>0 and isDivider: # draw slots for dividers to slot into each other
        for dividerNumber in range(1,int(numDividers)+1):
          Dx=vectorX+-dirY*dividerSpacing*dividerNumber-dividerEdgeOffsetX+notDirX*halfkerf
          Dy=vectorY+dirX*dividerSpacing*dividerNumber-dividerEdgeOffsetY+notDirY*halfkerf
          h='M '+str(Dx)+','+str(Dy)+' '
          Dx=Dx+dirX*(first+length/2)
          Dy=Dy+dirY*(first+length/2)
          h+='L '+str(Dx)+','+str(Dy)+' '
          Dx=Dx+notDirX*(thickness-kerf)
          Dy=Dy+notDirY*(thickness-kerf)
          h+='L '+str(Dx)+','+str(Dy)+' '
          Dx=Dx-dirX*(first+length/2)
          Dy=Dy-dirY*(first+length/2)
          h+='L '+str(Dx)+','+str(Dy)+' '
          Dx=Dx-notDirX*(thickness-kerf)
          Dy=Dy-notDirY*(thickness-kerf)
          h+='L '+str(Dx)+','+str(Dy)+' '
          group.add(getLine(h))
      # draw the gap
      vectorX+=dirX*(gapWidth+(isTab&dogbone&1 ^ 0x1)*first+dogbone*kerf*isTab)+notDirX*firstVec
      vectorY+=dirY*(gapWidth+(isTab&dogbone&1 ^ 0x1)*first+dogbone*kerf*isTab)+notDirY*firstVec
      s+='L '+str(vectorX)+','+str(vectorY)+' '
      if dogbone and isTab:
        vectorX-=dirX*halfkerf
        vectorY-=dirY*halfkerf
        s+='L '+str(vectorX)+','+str(vectorY)+' '
      # draw the starting edge of the tab
      s+=dimpleStr(secondVec,vectorX,vectorY,dirX,dirY,notDirX,notDirY,1,isTab)
      vectorX+=notDirX*secondVec
      vectorY+=notDirY*secondVec
      s+='L '+str(vectorX)+','+str(vectorY)+' '
      if dogbone and notTab:
        vectorX-=dirX*halfkerf
        vectorY-=dirY*halfkerf
        s+='L '+str(vectorX)+','+str(vectorY)+' '

    else:
      # draw the tab
      vectorX+=dirX*(tabWidth+dogbone*kerf*notTab)+notDirX*firstVec
      vectorY+=dirY*(tabWidth+dogbone*kerf*notTab)+notDirY*firstVec
      s+='L '+str(vectorX)+','+str(vectorY)+' '
      if dogbone and notTab:
        vectorX-=dirX*halfkerf
        vectorY-=dirY*halfkerf
        s+='L '+str(vectorX)+','+str(vectorY)+' '
      # draw the ending edge of the tab
      s+=dimpleStr(secondVec,vectorX,vectorY,dirX,dirY,notDirX,notDirY,-1,isTab)
      vectorX+=notDirX*secondVec
      vectorY+=notDirY*secondVec
      s+='L '+str(vectorX)+','+str(vectorY)+' '
      if dogbone and isTab:
        vectorX-=dirX*halfkerf
        vectorY-=dirY*halfkerf
        s+='L '+str(vectorX)+','+str(vectorY)+' '
    (secondVec,firstVec)=(-secondVec,-firstVec) # swap tab direction
    first=0
    
  #finish the line off
  s+='L '+str(rootX+endOffsetX*thickness+dirX*length)+','+str(rootY+endOffsetY*thickness+dirY*length)+' '

  if isTab and numDividers>0 and tabSymmetry==0 and not isDivider: # draw last for divider joints in side walls
    for dividerNumber in range(1,int(numDividers)+1):
      Dx=vectorX+-dirY*dividerSpacing*dividerNumber+notDirX*halfkerf+dirX*dogbone*halfkerf-dogbone*first*dirX
      # Dy=vectorY+dirX*dividerSpacing*dividerNumber-notDirY*halfkerf+dirY*dogbone*halfkerf-dogbone*first*dirY
      # Dx=vectorX+-dirY*dividerSpacing*dividerNumber-dividerEdgeOffsetX+notDirX*halfkerf
      Dy=vectorY+dirX*dividerSpacing*dividerNumber-dividerEdgeOffsetY+notDirY*halfkerf
      h='M '+str(Dx)+','+str(Dy)+' '
      Dx=Dx+firstholelenX
      Dy=Dy+firstholelenY
      h+='L '+str(Dx)+','+str(Dy)+' '
      Dx=Dx+notDirX*(thickness-kerf)
      Dy=Dy+notDirY*(thickness-kerf)
      h+='L '+str(Dx)+','+str(Dy)+' '
      Dx=Dx-firstholelenX
      Dy=Dy-firstholelenY
      h+='L '+str(Dx)+','+str(Dy)+' '
      Dx=Dx-notDirX*(thickness-kerf)
      Dy=Dy-notDirY*(thickness-kerf)
      h+='L '+str(Dx)+','+str(Dy)+' '
      group.add(getLine(h))
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
  group.add(getLine(s))
  return s

  
class BoxMaker(inkex.Effect):
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
    global group,nomTab,equalTabs,tabSymmetry,dimpleHeight,dimpleLength,thickness,kerf,halfkerf,dogbone,divx,divy,hairline,linethickness,keydivwalls,keydivfloor
    
        # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
        # Get the attributes:
    widthDoc  = self.svg.unittouu(svg.get('width'))
    heightDoc = self.svg.unittouu(svg.get('height'))
    
    # Get script's option values.
    hairline=self.options.hairline
    unit=self.options.unit
    inside=self.options.inside
    schroff=self.options.schroff
    kerf = self.svg.unittouu( str(self.options.kerf)  + unit )
    halfkerf=kerf/2

    # Set the line thickness
    if hairline:
        linethickness=self.svg.unittouu('0.002in')
    else:
        linethickness=1
        
    if schroff:
        rows=self.options.rows
        rail_height=self.svg.unittouu(str(self.options.rail_height)+unit)
        row_centre_spacing=self.svg.unittouu(str(122.5)+unit)
        row_spacing=self.svg.unittouu(str(self.options.row_spacing)+unit)
        rail_mount_depth=self.svg.unittouu(str(self.options.rail_mount_depth)+unit)
        rail_mount_centre_offset=self.svg.unittouu(str(self.options.rail_mount_centre_offset)+unit)
        rail_mount_radius=self.svg.unittouu(str(2.5)+unit)
    
    ## minimally different behaviour for schroffmaker.inx vs. boxmaker.inx
    ## essentially schroffmaker.inx is just an alternate interface with different
    ## default settings, some options removed, and a tiny amount of extra logic
    if schroff:
        ## schroffmaker.inx
        X = self.svg.unittouu(str(self.options.hp * 5.08) + unit)
        # 122.5mm vertical distance between mounting hole centres of 3U Schroff panels
        row_height = rows * (row_centre_spacing + rail_height)
        # rail spacing in between rows but never between rows and case panels
        row_spacing_total = (rows - 1) * row_spacing
        Y = row_height + row_spacing_total
    else:
        ## boxmaker.inx
        X = self.svg.unittouu( str(self.options.length + self.options.kerf)  + unit )
        Y = self.svg.unittouu( str(self.options.width + self.options.kerf) + unit )

    Z = self.svg.unittouu( str(self.options.height + self.options.kerf)  + unit )
    thickness = self.svg.unittouu( str(self.options.thickness)  + unit )
    nomTab = self.svg.unittouu( str(self.options.tab) + unit )
    equalTabs=self.options.equal
    tabSymmetry=self.options.tabsymmetry
    dimpleHeight=self.svg.unittouu( str(self.options.dimpleheight) + unit )
    dimpleLength=self.svg.unittouu( str(self.options.dimplelength) + unit )
    dogbone = 1 if self.options.tabtype == 1 else 0
    layout=self.options.style
    spacing = self.svg.unittouu( str(self.options.spacing)  + unit )
    boxtype = self.options.boxtype
    divx = self.options.div_l
    divy = self.options.div_w
    keydivwalls = 0 if self.options.keydiv == 3 or self.options.keydiv == 1 else 1
    keydivfloor = 0 if self.options.keydiv == 3 or self.options.keydiv == 2 else 1
    initOffsetX=0
    initOffsetY=0
        
    if inside: # if inside dimension selected correct values to outside dimension
      X+=thickness*2
      Y+=thickness*2
      Z+=thickness*2

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
    if min(X,Y,Z)<3*nomTab:
      inkex.errormsg(_('Error: Tab size too large'))
      error=1
    if nomTab<thickness:
      inkex.errormsg(_('Error: Tab size too small'))
      error=1     
    if thickness==0:
      inkex.errormsg(_('Error: Thickness is zero'))
      error=1     
    if thickness>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Material too thick'))
      error=1     
    if kerf>min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Kerf too large'))
      error=1     
    if spacing>max(X,Y,Z)*10: # crude test
      inkex.errormsg(_('Error: Spacing too large'))
      error=1     
    if spacing<kerf:
      inkex.errormsg(_('Error: Spacing too small'))
      error=1     

    if error: exit()

    # For code spacing consistency, we use two-character abbreviations for the six box faces,
    # where each abbreviation is the first and last letter of the face name:
    # tp=top, bm=bottom, ft=front, bk=back, lt=left, rt=right

    # Determine which faces the box has based on the box type
    hasTp=hasBm=hasFt=hasBk=hasLt=hasRt = True
    if   boxtype==2: hasTp=False
    elif boxtype==3: hasTp=hasFt=False
    elif boxtype==4: hasTp=hasFt=hasRt=False
    elif boxtype==5: hasTp=hasBm=False
    elif boxtype==6: hasTp=hasFt=hasBk=hasRt=False
    # else boxtype==1, full box, has all sides

    # Determine where the tabs go based on the tab style
    if tabSymmetry==2:     # Antisymmetric (deprecated)
      tpTabInfo=0b0110
      bmTabInfo=0b1100
      ltTabInfo=0b1100
      rtTabInfo=0b0110
      ftTabInfo=0b1100
      bkTabInfo=0b1001
    elif tabSymmetry==1:   # Rotationally symmetric (Waffle-blocks)
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
        if inside:
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
    if   layout==1: # Diagramatic Layout
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
    elif layout==2: # 3 Piece Layout
      rr = deepcopy([row0, row1y])
      cc = deepcopy([col0, col1z])
      if hasBk: pieces.append([cc[1], rr[1], X,Z, bkTabInfo, bkTabbed, bkFace])
      if hasLt: pieces.append([cc[0], rr[0], Z,Y, ltTabInfo, ltTabbed, ltFace])
      if hasBm: pieces.append([cc[1], rr[0], X,Y, bmTabInfo, bmTabbed, bmFace])
    elif layout==3: # Inline(compact) Layout
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

    for idx, piece in enumerate(pieces): # generate and draw each piece of the box
      (xs,xx,xy,xz)=piece[0]
      (ys,yx,yy,yz)=piece[1]
      x=xs*spacing+xx*X+xy*Y+xz*Z+initOffsetX  # root x co-ord for piece
      y=ys*spacing+yx*X+yy*Y+yz*Z+initOffsetY  # root y co-ord for piece
      dx=piece[2]
      dy=piece[3]
      tabs=piece[4]
      a=tabs>>3&1; b=tabs>>2&1; c=tabs>>1&1; d=tabs&1 # extract tab status for each side
      tabbed=piece[5]
      atabs=tabbed>>3&1; btabs=tabbed>>2&1; ctabs=tabbed>>1&1; dtabs=tabbed&1 # extract tabbed flag for each side
      xspacing=(X-thickness)/(divy+1)
      yspacing=(Y-thickness)/(divx+1)
      xholes = 1 if piece[6]<3 else 0
      yholes = 1 if piece[6]!=2 else 0
      wall = 1 if piece[6]>1 else 0
      floor = 1 if piece[6]==1 else 0
      railholes = 1 if piece[6]==3 else 0

      group = newGroup(self)
      
      if schroff and railholes:
        log("rail holes enabled on piece %d at (%d, %d)" % (idx, x+thickness,y+thickness))
        log("abcd = (%d,%d,%d,%d)" % (a,b,c,d))
        log("dxdy = (%d,%d)" % (dx,dy))
        rhxoffset = rail_mount_depth + thickness
        if idx == 1:
          rhx=x+rhxoffset
        elif idx == 3:
          rhx=x-rhxoffset+dx
        else:
          rhx=0
        log("rhxoffset = %d, rhx= %d" % (rhxoffset, rhx))
        rystart=y+(rail_height/2)+thickness
        if rows == 1:
          log("just one row this time, rystart = %d" % rystart)
          rh1y=rystart+rail_mount_centre_offset
          rh2y=rh1y+(row_centre_spacing-rail_mount_centre_offset)
          group.add(getCircle(rail_mount_radius,(rhx,rh1y)))
          group.add(getCircle(rail_mount_radius,(rhx,rh2y)))
        else:
          for n in range(0,rows):
            log("drawing row %d, rystart = %d" % (n+1, rystart))
            # if holes are offset (eg. Vector T-strut rails), they should be offset
            # toward each other, ie. toward the centreline of the Schroff row
            rh1y=rystart+rail_mount_centre_offset
            rh2y=rh1y+row_centre_spacing-rail_mount_centre_offset
            group.add(getCircle(rail_mount_radius,(rhx,rh1y)))
            group.add(getCircle(rail_mount_radius,(rhx,rh2y)))
            rystart+=row_centre_spacing+row_spacing+rail_height

      # generate and draw the sides of each piece
      side(group,(x,y),(d,a),(-b,a),atabs * (-thickness if a else thickness),dtabs,dx,(1,0),a,0,(keydivfloor|wall) * (keydivwalls|floor) * divx*yholes*atabs,yspacing)          # side a
      side(group,(x+dx,y),(-b,a),(-b,-c),btabs * (thickness if b else -thickness),atabs,dy,(0,1),b,0,(keydivfloor|wall) * (keydivwalls|floor) * divy*xholes*btabs,xspacing)     # side b
      if atabs:
        side(group,(x+dx,y+dy),(-b,-c),(d,-c),ctabs * (thickness if c else -thickness),btabs,dx,(-1,0),c,0,0,0) # side c
      else:
        side(group,(x+dx,y+dy),(-b,-c),(d,-c),ctabs * (thickness if c else -thickness),btabs,dx,(-1,0),c,0,(keydivfloor|wall) * (keydivwalls|floor) * divx*yholes*ctabs,yspacing) # side c
      if btabs:
        side(group,(x,y+dy),(d,-c),(d,a),dtabs * (-thickness if d else thickness),ctabs,dy,(0,-1),d,0,0,0)      # side d
      else:
        side(group,(x,y+dy),(d,-c),(d,a),dtabs * (-thickness if d else thickness),ctabs,dy,(0,-1),d,0,(keydivfloor|wall) * (keydivwalls|floor) * divy*xholes*dtabs,xspacing)      # side d

      if idx==0:
        # remove tabs from dividers if not required
        if not keydivfloor:
          a=c=1
          atabs=ctabs=0
        if not keydivwalls:
          b=d=1 
          btabs=dtabs=0

        y=4*spacing+1*Y+2*Z  # root y co-ord for piece 
        for n in range(0,divx): # generate X dividers
          group = newGroup(self)
          x=n*(spacing+X)  # root x co-ord for piece      
          side(group,(x,y),(d,a),(-b,a),keydivfloor*atabs*(-thickness if a else thickness),dtabs,dx,(1,0),a,1,0,0)          # side a
          side(group,(x+dx,y),(-b,a),(-b,-c),keydivwalls*btabs*(thickness if b else -thickness),atabs,dy,(0,1),b,1,divy*xholes,xspacing)    # side b
          side(group,(x+dx,y+dy),(-b,-c),(d,-c),keydivfloor*ctabs*(thickness if c else -thickness),btabs,dx,(-1,0),c,1,0,0) # side c
          side(group,(x,y+dy),(d,-c),(d,a),keydivwalls*dtabs*(-thickness if d else thickness),ctabs,dy,(0,-1),d,1,0,0)      # side d
      elif idx==1:
        y=5*spacing+1*Y+3*Z  # root y co-ord for piece 
        for n in range(0,divy): # generate Y dividers
          group = newGroup(self)
          x=n*(spacing+Z)  # root x co-ord for piece
          side(group,(x,y),(d,a),(-b,a),keydivwalls*atabs*(-thickness if a else thickness),dtabs,dx,(1,0),a,1,divx*yholes,yspacing)          # side a
          side(group,(x+dx,y),(-b,a),(-b,-c),keydivfloor*btabs*(thickness if b else -thickness),atabs,dy,(0,1),b,1,0,0)     # side b
          side(group,(x+dx,y+dy),(-b,-c),(d,-c),keydivwalls*ctabs*(thickness if c else -thickness),btabs,dx,(-1,0),c,1,0,0) # side c
          side(group,(x,y+dy),(d,-c),(d,a),keydivfloor*dtabs*(-thickness if d else thickness),ctabs,dy,(0,-1),d,1,0,0)      # side d

# Create effect instance and apply it.
effect = BoxMaker()
effect.run()
