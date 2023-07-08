#! /usr/bin/env python -t
'''
Generates Inkscape SVG file containing box components needed to
CNC (laser/mill) cut a box with tabbed joints taking kerf and clearance into account

Original Tabbed Box Maker Copyright (C) 2011 elliot white

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

from typing import List

import argparse
import os

from . import (TabbedBox, AbstractShape, Path)

def log(text):
  if 'SCHROFF_LOG' in os.environ:
    f = open(os.environ.get('SCHROFF_LOG'), 'a')
    f.write(text + "\n")


class Circle(AbstractShape):
    def __init__(self, cX: float, cY: float, r: float) -> None:
        self.centre = (cX, cY)
        self.radius = r

    def __repr__(self):
        return f'{__class__}({self.initial_x}, {self.initial_y}, r={self.radius})'

class SchroffBox(TabbedBox):

  @staticmethod
  def add_args(arg_parser: argparse.ArgumentParser) -> None:
        """Add ArgumentParser args needed to configure a schroff boxmaker run"""

        super(SchroffBox, SchroffBox).add_args(arg_parser)
        arg_parser.add_argument('--schroff', action='store', type=int,
            dest='schroff', default=0, help='Enable Schroff mode')
        arg_parser.add_argument('--rail_height', action='store', type=float,
            dest='rail_height', default=10.0, help='Height of rail')
        arg_parser.add_argument('--rail_mount_depth', action='store',
            type=float, dest='rail_mount_depth', default=17.4,
            help='Depth at which to place hole for rail mount bolt')
        arg_parser.add_argument('--rail_mount_centre_offset', action='store',
            type=float, dest='rail_mount_centre_offset', default=0.0,
            help='How far toward row centreline to offset rail mount bolt (from rail centreline)')
        arg_parser.add_argument('--rows', action='store', type=int,
            dest='rows', default=0, help='Number of Schroff rows')
        arg_parser.add_argument('--hp', action='store', type=int,
            dest='hp', default=0,help='Width (TE/HP units) of Schroff rows')
        arg_parser.add_argument('--row_spacing', action='store', type=float,
            dest='row_spacing', default=10.0,help='Height of rail')

  def piece(
      self, X: float, Y: float, Z: float, thickness: float, idx: int,
      rootx: List[float], rooty: List[float], dx: float, dy: float,
      tabs: int, tabbed: int, pieceType: int,
  ):
      groups = super().piece(
          X, Y, Z, thickness, idx,
          rootx, rooty, dx, dy, tabs, tabbed, pieceType
      )

      initOffsetX=0  # TODO: These look redundant, remove?
      initOffsetY=0

      (xs,xx,xy,xz)=rootx
      (ys,yx,yy,yz)=rooty

      x=xs*self.cfg.spacing+xx*X+xy*Y+xz*Z+initOffsetX  # root x co-ord for piece
      y=ys*self.cfg.spacing+yx*X+yy*Y+yz*Z+initOffsetY  # root y co-ord for piece

      railholes = 1 if pieceType==3 else 0
      if self.cfg.schroff and railholes:
#        log("rail holes enabled on piece %d at (%d, %d)" % (idx, x+thickness,y+thickness))
#        log("abcd = (%d,%d,%d,%d)" % (a,b,c,d))
#        log("dxdy = (%d,%d)" % (dx,dy))
        rhxoffset = self.cfg.rail_mount_depth + thickness
        if idx == 1:
          rhx=x+rhxoffset
        elif idx == 3:
          rhx=x-rhxoffset+dx
        else:
          rhx=0
        log("rhxoffset = %d, rhx= %d" % (rhxoffset, rhx))
        rystart=y+(self.cfg.rail_height/2)+thickness
        holes=[]
        if self.cfg.rows == 1:
          log("just one row this time, rystart = %d" % rystart)
          rh1y=rystart+self.cfg.rail_mount_centre_offset
          rh2y=rh1y+(self.cfg.row_centre_spacing-self.cfg.rail_mount_centre_offset)
          holes.append(Circle(rhx, rh1y, self.cfg.rail_mount_radius))
          holes.append(Circle(rhx, rh2y, self.cfg.rail_mount_radius))
        else:
          for n in range(0, self.cfg.rows):
            log("drawing row %d, rystart = %d" % (n+1, rystart))
            # if holes areo ffset (eg. Vector T-strut rails), they should be offset
            # toward each other, ie. toward the centreline of the Schroff row
            rh1y=rystart+self.cfg.rail_mount_centre_offset
            rh2y=rh1y+self.cfg.row_centre_spacing-self.cfg.rail_mount_centre_offset
            holes.append(Circle(rhx, rh1y, self.cfg.rail_mount_radius))
            holes.append(Circle(rhx, rh2y, self.cfg.rail_mount_radius))
            rystart+=self.cfg.row_centre_spacing+self.cfg.row_spacing+self.cfg.rail_height
        # Add to the start of the 'sides' group entry - the first group - to
        # keep the generated SVG the same as before separating the scrhoff code.
        groups[0] = holes + groups[0]

      return groups
