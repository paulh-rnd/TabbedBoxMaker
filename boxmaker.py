#! /usr/bin/env python -t
"""Generates SVG files for boxes with tabbed joints.

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
"""
__version__ = "1.0.1" ### please report bugs, suggestions etc at https://github.com/paulh-rnd/TabbedBoxMaker ###

import os
# import sys
import inkex
# import simplestyle
import gettext
# import math

from copy import deepcopy
_ = gettext.gettext

DEFAULT_THICKNESS = 1 # default unless overridden by settings

def log(text):
    """Adding line to SCHROFF_LOG."""
    if 'SCHROFF_LOG' in os.environ:
        f = open(os.environ.get('SCHROFF_LOG'), 'a', encoding="utf-8")
        f.write(text + "\n")

def new_group(canvas):
    """Create a new group and add element created from line string."""
    panel_id = canvas.svg.get_unique_id('panel')
    inkex_group = canvas.svg.get_current_layer().add(inkex.Group(id=panel_id))
    return inkex_group

def get_line(xy_string):
    """Create line."""
    line = inkex.PathElement()
    line.style = { 'stroke': '#000000', 'stroke-width': str(DEFAULT_THICKNESS), 'fill': 'none' }
    line.path = xy_string
    #inkex.etree.SubElement(parent, inkex.addNS('path','svg'), drw)
    return line

# jslee - shamelessly adapted from sample code on below Inkscape wiki page 2015-07-28
# http://wiki.inkscape.org/wiki/index.php/Generating_objects_from_extensions
def get_circle(r, c):
    """Create circle."""
    (cx, cy) = c
    log(f"putting circle at ({cx},{cy})")
    circle = inkex.PathElement.arc((cx, cy), r)
    circle.style = { 'stroke': '#000000', 'stroke-width': str(DEFAULT_THICKNESS), 'fill': 'none' }
    return circle

def dimple_str(tab_vector,vector_x,vector_y,dir_x,dir_y,dir_xn,dir_yn,ddir,is_tab):
    """Dimple things."""
    ds=''
    if not is_tab:
        ddir = -ddir
    if dimple_height>0 and tab_vector!=0:
        if tab_vector>0:
            dimple_start=(tab_vector-dimpleLength)/2-dimple_height
            tab_sgn=1
        else:
            dimple_start=(tab_vector+dimpleLength)/2+dimple_height
            tab_sgn=-1
        Vxd=vector_x+dir_xn*dimple_start
        Vyd=vector_y+dir_yn*dimple_start
        ds+='L '+str(Vxd)+','+str(Vyd)+' '
        Vxd=Vxd+(tab_sgn*dir_xn-ddir*dir_x)*dimple_height
        Vyd=Vyd+(tab_sgn*dir_yn-ddir*dir_y)*dimple_height
        ds+='L '+str(Vxd)+','+str(Vyd)+' '
        Vxd=Vxd+tab_sgn*dir_xn*dimpleLength
        Vyd=Vyd+tab_sgn*dir_yn*dimpleLength
        ds+='L '+str(Vxd)+','+str(Vyd)+' '
        Vxd=Vxd+(tab_sgn*dir_xn+ddir*dir_x)*dimple_height
        Vyd=Vyd+(tab_sgn*dir_yn+ddir*dir_y)*dimple_height
        ds+='L '+str(Vxd)+','+str(Vyd)+' '
    return ds

def side(group,root,start_offset,end_offset,tab_vec,length,direction,is_tab,is_divider,num_dividers,divider_spacing):
    """Side things."""
    root_x, root_y = root
    start_offset_x, start_offset_y = start_offset
    end_offset_x, end_offset_y = end_offset
    dir_x, dir_y = direction
    not_tab=0 if is_tab else 1

    if tab_symmetry==1:        # waffle-block style rotationally symmetric tabs
        divisions=int((length-2*thickness)/nom_tab)
        if divisions%2:
            divisions+=1      # make divs even
        divisions=float(divisions)
        tabs=divisions/2                  # tabs for side
    else:
        divisions=int(length/nom_tab)
        if not divisions%2:
            divisions-=1  # make divs odd
        divisions=float(divisions)
        tabs=(divisions-1)/2              # tabs for side

    if tab_symmetry==1:        # waffle-block style rotationally symmetric tabs
        gap_width=tab_width=(length-2*thickness)/divisions
    elif equalTabs:
        gap_width=tab_width=length/divisions
    else:
        tab_width=nom_tab
        gap_width=(length-tabs*nom_tab)/(divisions-tabs)

    if is_tab:                 # kerf correction
        gap_width-=kerf
        tab_width+=kerf
        first=halfkerf
    else:
        gap_width+=kerf
        tab_width-=kerf
        first=-halfkerf
    first_hole_len_x=0
    first_hole_len_y=0
    s=[]
    h=[]
    first_vec=0
    second_vec=tab_vec
    divider_edge_offset_x = divider_edge_offset_y = thickness
    notdir_x=0 if dir_x else 1 # used to select operation on x or y
    notdir_y=0 if dir_y else 1
    if tab_symmetry==1:
        divider_edge_offset_x = dir_x*thickness
        #divider_edge_offset_y = ;
        vector_x = root_x + (start_offset_x*thickness if notdir_x else 0)
        vector_y = root_y + (start_offset_y*thickness if notdir_y else 0)
        s='M '+str(vector_x)+','+str(vector_y)+' '
        vector_x = root_x+(start_offset_x if start_offset_x else dir_x)*thickness
        vector_y = root_y+(start_offset_y if start_offset_y else dir_y)*thickness
        if notdir_x:
            end_offset_x=0
        if notdir_y:
            end_offset_y=0
    else:
        (vector_x,vector_y)=(root_x+start_offset_x*thickness,root_y+start_offset_y*thickness)
        divider_edge_offset_x=dir_y*thickness
        divider_edge_offset_y=dir_x*thickness
        s='M '+str(vector_x)+','+str(vector_y)+' '
        if notdir_x:
            vector_y=root_y # set correct line start for tab generation
        if notdir_y:
            vector_x=root_x

    # generate line as tab or hole using:
    #   last co-ord:Vx,Vy ; tab dir:tab_vec  ; direction:dir_x,dir_y ; thickness:thickness
    #   divisions:divs ; gap width:gap_width ; tab width:tab_width

    for tab_division in range(1,int(divisions)):
        if ((tab_division%2) ^ (not is_tab)) and num_dividers>0 and not is_divider:
            # draw holes for divider tabs to key into side walls
            w=gap_width if is_tab else tab_width
            if tab_division==1 and tab_symmetry==0:
                w-=start_offset_x*thickness
            hole_len_x=dir_x*w+notdir_x*first_vec+first*dir_x
            hole_len_y=dir_y*w+notdir_y*first_vec+first*dir_y
            if first:
                first_hole_len_x=hole_len_x
                first_hole_len_y=hole_len_y
            for divider_number in range(1,int(num_dividers)+1):
                Dx=vector_x+-dir_y*divider_spacing*divider_number+notdir_x*halfkerf+dir_x*dogbone*halfkerf-dogbone*first*dir_x
                Dy=vector_y+dir_x*divider_spacing*divider_number-notdir_y*halfkerf+dir_y*dogbone*halfkerf-dogbone*first*dir_y
                if tab_division==1 and tab_symmetry==0:
                    Dx+=start_offset_x*thickness
                h='M '+str(Dx)+','+str(Dy)+' '
                Dx=Dx+hole_len_x
                Dy=Dy+hole_len_y
                h+='L '+str(Dx)+','+str(Dy)+' '
                Dx=Dx+notdir_x*(second_vec-kerf)
                Dy=Dy+notdir_y*(second_vec+kerf)
                h+='L '+str(Dx)+','+str(Dy)+' '
                Dx=Dx-hole_len_x
                Dy=Dy-hole_len_y
                h+='L '+str(Dx)+','+str(Dy)+' '
                Dx=Dx-notdir_x*(second_vec-kerf)
                Dy=Dy-notdir_y*(second_vec+kerf)
                h+='L '+str(Dx)+','+str(Dy)+' '
                group.add(get_line(h)) 
        if tab_division%2:
            if tab_division==1 and num_dividers>0 and is_divider:
                # draw slots for dividers to slot into each other
                for divider_number in range(1,int(num_dividers)+1):
                    Dx=vector_x+-dir_y*divider_spacing*divider_number-divider_edge_offset_x+notdir_x*halfkerf
                    Dy=vector_y+dir_x*divider_spacing*divider_number-divider_edge_offset_y+notdir_y*halfkerf
                    h='M '+str(Dx)+','+str(Dy)+' '
                    Dx=Dx+dir_x*(first+length/2)
                    Dy=Dy+dir_y*(first+length/2)
                    h+='L '+str(Dx)+','+str(Dy)+' '
                    Dx=Dx+notdir_x*(thickness-kerf)
                    Dy=Dy+notdir_y*(thickness-kerf)
                    h+='L '+str(Dx)+','+str(Dy)+' '
                    Dx=Dx-dir_x*(first+length/2)
                    Dy=Dy-dir_y*(first+length/2)
                    h+='L '+str(Dx)+','+str(Dy)+' '
                    Dx=Dx-notdir_x*(thickness-kerf)
                    Dy=Dy-notdir_y*(thickness-kerf)
                    h+='L '+str(Dx)+','+str(Dy)+' '
                    group.add(get_line(h))
            # draw the gap
            vector_x+=dir_x*(gap_width+(is_tab&dogbone&1 ^ 0x1)*first+dogbone*kerf*is_tab)+notdir_x*first_vec
            vector_y+=dir_y*(gap_width+(is_tab&dogbone&1 ^ 0x1)*first+dogbone*kerf*is_tab)+notdir_y*first_vec
            s+='L '+str(vector_x)+','+str(vector_y)+' '
            if dogbone and is_tab:
                vector_x-=dir_x*halfkerf
                vector_y-=dir_y*halfkerf
                s+='L '+str(vector_x)+','+str(vector_y)+' '
            # draw the starting edge of the tab
            s+=dimple_str(second_vec,vector_x,vector_y,dir_x,dir_y,notdir_x,notdir_y,1,is_tab)
            vector_x+=notdir_x*second_vec
            vector_y+=notdir_y*second_vec
            s+='L '+str(vector_x)+','+str(vector_y)+' '
            if dogbone and not_tab:
                vector_x-=dir_x*halfkerf
                vector_y-=dir_y*halfkerf
                s+='L '+str(vector_x)+','+str(vector_y)+' '

        else:
            # draw the tab
            vector_x+=dir_x*(tab_width+dogbone*kerf*not_tab)+notdir_x*first_vec
            vector_y+=dir_y*(tab_width+dogbone*kerf*not_tab)+notdir_y*first_vec
            s+='L '+str(vector_x)+','+str(vector_y)+' '
            if dogbone and not_tab:
                vector_x-=dir_x*halfkerf
                vector_y-=dir_y*halfkerf
                s+='L '+str(vector_x)+','+str(vector_y)+' '
            # draw the ending edge of the tab
            s+=dimple_str(second_vec,vector_x,vector_y,dir_x,dir_y,notdir_x,notdir_y,-1,is_tab)
            vector_x+=notdir_x*second_vec
            vector_y+=notdir_y*second_vec
            s+='L '+str(vector_x)+','+str(vector_y)+' '
            if dogbone and is_tab:
                vector_x-=dir_x*halfkerf
                vector_y-=dir_y*halfkerf
                s+='L '+str(vector_x)+','+str(vector_y)+' '
        (second_vec,first_vec)=(-second_vec,-first_vec) # swap tab direction
        first=0

    #finish the line off
    s+='L '+str(root_x+end_offset_x*thickness+dir_x*length)+','+str(root_y+end_offset_y*thickness+dir_y*length)+' '

    if is_tab and num_dividers>0 and tab_symmetry==0 and not is_divider: # draw last for divider joints in side walls
        for divider_number in range(1,int(num_dividers)+1):
            Dx=vector_x+-dir_y*divider_spacing*divider_number+notdir_x*halfkerf+dir_x*dogbone*halfkerf-dogbone*first*dir_x
            Dy=vector_y+dir_x*divider_spacing*divider_number-divider_edge_offset_y+notdir_y*halfkerf
            h='M '+str(Dx)+','+str(Dy)+' '
            Dx=Dx+first_hole_len_x
            Dy=Dy+first_hole_len_y
            h+='L '+str(Dx)+','+str(Dy)+' '
            Dx=Dx+notdir_x*(thickness-kerf)
            Dy=Dy+notdir_y*(thickness-kerf)
            h+='L '+str(Dx)+','+str(Dy)+' '
            Dx=Dx-first_hole_len_x
            Dy=Dy-first_hole_len_y
            h+='L '+str(Dx)+','+str(Dy)+' '
            Dx=Dx-notdir_x*(thickness-kerf)
            Dy=Dy-notdir_y*(thickness-kerf)
            h+='L '+str(Dx)+','+str(Dy)+' '
            group.add(get_line(h))
    group.add(get_line(s))
    return s


class BoxMaker(inkex.Effect):
    """Make SVG for tabbed joint boxes."""
    def __init__(self):
        # Call the base cl  ass constructor.
        inkex.Effect.__init__(self)
        # Define options
        self.arg_parser.add_argument('--schroff',action='store',type=int,
            dest='schroff',default=0,help='Enable Schroff mode')
        self.arg_parser.add_argument('--rail_height',action='store',type=float,
            dest='rail_height',default=10.0,help='Height of rail')
        self.arg_parser.add_argument('--rail_mount_depth',action='store',type=float,
            dest='rail_mount_depth',default=17.4,
            help='Depth at which to place hole for rail mount bolt')
        self.arg_parser.add_argument('--rail_mount_centre_offset',action='store',type=float,
            dest='rail_mount_centre_offset',default=0.0,
            help='How far toward row centreline to offset rail mount bolt (from rail centreline)')
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
            dest='tab',default= 25,help='Nominal Tab Width')
        self.arg_parser.add_argument('--equal',action='store',type=int,
            dest='equal',default=0,help='Equal/Prop Tabs')
        self.arg_parser.add_argument('--tabsymmetry',action='store',type=int,
            dest='tabsymmetry',default=0,help='Tab style')
        self.arg_parser.add_argument('--tabtype',action='store',type=int,
            dest='tabtype',default=0,help='Tab type: regular or dogbone')
        self.arg_parser.add_argument('--dimple_height',action='store',type=float,
            dest='dimple_height',default=0,help='Tab Dimple Height')
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
        global group,nom_tab,equalTabs,tab_symmetry,dimple_height,dimpleLength,thickness,kerf,halfkerf,dogbone,divx,divy,hairline,DEFAULT_THICKNESS,keydivwalls,keydivfloor

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
            DEFAULT_THICKNESS=self.svg.unittouu('0.002in')
        else:
            DEFAULT_THICKNESS=1

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
            X = self.svg.unittouu( str(self.options.length + kerf)  + unit )
            Y = self.svg.unittouu( str(self.options.width + kerf) + unit )

        Z = self.svg.unittouu( str(self.options.height + kerf)  + unit )
        thickness = self.svg.unittouu( str(self.options.thickness)  + unit )
        nom_tab = self.svg.unittouu( str(self.options.tab) + unit )
        equalTabs=self.options.equal
        tab_symmetry=self.options.tabsymmetry
        dimple_height=self.options.dimple_height
        dimpleLength=self.options.dimplelength
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
        if min(X,Y,Z)<3*nom_tab:
            inkex.errormsg(_('Error: Tab size too large'))
            error=1
        if nom_tab<thickness:
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
        if tab_symmetry==2:     # Antisymmetric (deprecated)
            tpTabInfo=0b0110
            bmTabInfo=0b1100
            ltTabInfo=0b1100
            rtTabInfo=0b0110
            ftTabInfo=0b1100
            bkTabInfo=0b1001
        elif tab_symmetry==1:   # Rotationally symmetric (Waffle-blocks)
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

        # layout format:(root_x),(root_y),Xlength,Ylength,tabInfo,tabbed,pieceType
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

            group = new_group(self)

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
                    group.add(get_circle(rail_mount_radius,(rhx,rh1y)))
                    group.add(get_circle(rail_mount_radius,(rhx,rh2y)))
                else:
                    for n in range(0,rows):
                        log("drawing row %d, rystart = %d" % (n+1, rystart))
                        # if holes are offset (eg. Vector T-strut rails), they should be offset
                        # toward each other, ie. toward the centreline of the Schroff row
                        rh1y=rystart+rail_mount_centre_offset
                        rh2y=rh1y+row_centre_spacing-rail_mount_centre_offset
                        group.add(get_circle(rail_mount_radius,(rhx,rh1y)))
                        group.add(get_circle(rail_mount_radius,(rhx,rh2y)))
                        rystart+=row_centre_spacing+row_spacing+rail_height

            # generate and draw the sides of each piece
            side(group,(x,y),(d,a),(-b,a),atabs * (-thickness if a else thickness),dx,(1,0),a,0,(keydivfloor|wall) * (keydivwalls|floor) * divx*yholes*atabs,yspacing)          # side a
            side(group,(x+dx,y),(-b,a),(-b,-c),btabs * (thickness if b else -thickness),dy,(0,1),b,0,(keydivfloor|wall) * (keydivwalls|floor) * divy*xholes*btabs,xspacing)     # side b
            if atabs:
                side(group,(x+dx,y+dy),(-b,-c),(d,-c),ctabs * (thickness if c else -thickness),dx,(-1,0),c,0,0,0) # side c
            else:
                side(group,(x+dx,y+dy),(-b,-c),(d,-c),ctabs * (thickness if c else -thickness),dx,(-1,0),c,0,(keydivfloor|wall) * (keydivwalls|floor) * divx*yholes*ctabs,yspacing) # side c
            if btabs:
                side(group,(x,y+dy),(d,-c),(d,a),dtabs * (-thickness if d else thickness),dy,(0,-1),d,0,0,0)      # side d
            else:
                side(group,(x,y+dy),(d,-c),(d,a),dtabs * (-thickness if d else thickness),dy,(0,-1),d,0,(keydivfloor|wall) * (keydivwalls|floor) * divy*xholes*dtabs,xspacing)      # side d

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
                    group = new_group(self)
                    x=n*(spacing+X)  # root x co-ord for piece
                    side(group,(x,y),(d,a),(-b,a),keydivfloor*atabs*(-thickness if a else thickness),dx,(1,0),a,1,0,0)          # side a
                    side(group,(x+dx,y),(-b,a),(-b,-c),keydivwalls*btabs*(thickness if b else -thickness),dy,(0,1),b,1,divy*xholes,xspacing)    # side b
                    side(group,(x+dx,y+dy),(-b,-c),(d,-c),keydivfloor*ctabs*(thickness if c else -thickness),dx,(-1,0),c,1,0,0) # side c
                    side(group,(x,y+dy),(d,-c),(d,a),keydivwalls*dtabs*(-thickness if d else thickness),dy,(0,-1),d,1,0,0)      # side d
            elif idx==1:
                y=5*spacing+1*Y+3*Z  # root y co-ord for piece
                for n in range(0,divy): # generate Y dividers
                    group = new_group(self)
                    x=n*(spacing+Z)  # root x co-ord for piece
                    side(group,(x,y),(d,a),(-b,a),keydivwalls*atabs*(-thickness if a else thickness),dx,(1,0),a,1,divx*yholes,yspacing)          # side a
                    side(group,(x+dx,y),(-b,a),(-b,-c),keydivfloor*btabs*(thickness if b else -thickness),dy,(0,1),b,1,0,0)     # side b
                    side(group,(x+dx,y+dy),(-b,-c),(d,-c),keydivwalls*ctabs*(thickness if c else -thickness),dx,(-1,0),c,1,0,0) # side c
                    side(group,(x,y+dy),(d,-c),(d,a),keydivfloor*dtabs*(-thickness if d else thickness),dy,(0,-1),d,1,0,0)      # side d

# Create effect instance and apply it.
effect = BoxMaker()
effect.run()
