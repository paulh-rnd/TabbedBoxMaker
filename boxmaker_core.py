#! /usr/bin/env python -t
'''
Core BoxMaker functionality - refactored for testability
'''

import math
import os
import sys
from copy import deepcopy


class BoxMakerCore:
    def __init__(self):
        # Default values
        self.unit = 'mm'
        self.inside = 0
        self.length = 100.0
        self.width = 100.0
        self.height = 100.0
        self.tab = 25.0
        self.equal = 0
        self.tabsymmetry = 0
        self.tabtype = 0
        self.dimpleheight = 0.0
        self.dimplelength = 0.0
        self.hairline = 0
        self.thickness = 3.0
        self.kerf = 0.5
        self.style = 1
        self.spacing = 25.0
        self.boxtype = 1
        self.div_l = 0
        self.div_w = 0
        self.keydiv = 3
        self.optimize = True
        
        # Internal state
        self.linethickness = 1
        self.paths = []
        self.circles = []
        
    def set_parameters(self, **kwargs):
        """Set box parameters from keyword arguments"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def log(self, text):
        if 'SCHROFF_LOG' in os.environ:
            f = open(os.environ.get('SCHROFF_LOG'), 'a')
            f.write(text + "\n")

    def get_line_path(self, XYstring):
        """Return path data for a line"""
        return {
            'type': 'path',
            'data': XYstring,
            'style': {
                'stroke': '#000000',
                'stroke-width': str(self.linethickness),
                'fill': 'none'
            }
        }

    def get_circle_path(self, r, c):
        """Return path data for a circle"""
        (cx, cy) = c
        self.log("putting circle at (%d,%d)" % (cx, cy))
        return {
            'type': 'circle',
            'cx': cx,
            'cy': cy,
            'r': r,
            'style': {
                'stroke': '#000000',
                'stroke-width': str(self.linethickness),
                'fill': 'none'
            }
        }

    def dimple_str(self, tabVector, vectorX, vectorY, dirX, dirY, dirxN, diryN, ddir, isTab):
        ds = ''
        if not isTab:
            ddir = -ddir
        if self.dimpleHeight > 0 and tabVector != 0:
            if tabVector > 0:
                dimpleStart = (tabVector - self.dimpleLength) / 2 - self.dimpleHeight
                tabSgn = 1
            else:
                dimpleStart = (tabVector + self.dimpleLength) / 2 + self.dimpleHeight
                tabSgn = -1
            Vxd = vectorX + dirxN * dimpleStart
            Vyd = vectorY + diryN * dimpleStart
            ds += 'L ' + str(Vxd) + ',' + str(Vyd) + ' '
            Vxd = Vxd + (tabSgn * dirxN - ddir * dirX) * self.dimpleHeight
            Vyd = Vyd + (tabSgn * diryN - ddir * dirY) * self.dimpleHeight
            ds += 'L ' + str(Vxd) + ',' + str(Vyd) + ' '
            Vxd = Vxd + tabSgn * dirxN * self.dimpleLength
            Vyd = Vyd + tabSgn * diryN * self.dimpleLength
            ds += 'L ' + str(Vxd) + ',' + str(Vyd) + ' '
            Vxd = Vxd + (tabSgn * dirxN + ddir * dirX) * self.dimpleHeight
            Vyd = Vyd + (tabSgn * diryN + ddir * dirY) * self.dimpleHeight
            ds += 'L ' + str(Vxd) + ',' + str(Vyd) + ' '
        return ds

    def side(self, group_id, root, startOffset, endOffset, tabVec, prevTab, length, direction, isTab, isDivider, numDividers, dividerSpacing):
        rootX, rootY = root
        startOffsetX, startOffsetY = startOffset
        endOffsetX, endOffsetY = endOffset
        dirX, dirY = direction
        notTab = 0 if isTab else 1

        if self.tabSymmetry == 1:        # waffle-block style rotationally symmetric tabs
            divisions = int((length - 2 * self.thickness) / self.nomTab)
            if divisions % 2:
                divisions += 1      # make divs even
            divisions = float(divisions)
            tabs = divisions / 2                  # tabs for side
        else:
            divisions = int(length / self.nomTab)
            if not divisions % 2:
                divisions -= 1  # make divs odd
            divisions = float(divisions)
            tabs = (divisions - 1) / 2              # tabs for side

        if self.tabSymmetry == 1:        # waffle-block style rotationally symmetric tabs
            gapWidth = tabWidth = (length - 2 * self.thickness) / divisions
        elif self.equalTabs:
            gapWidth = tabWidth = length / divisions
        else:
            tabWidth = self.nomTab
            gapWidth = (length - tabs * self.nomTab) / (divisions - tabs)

        if isTab:                 # kerf correction
            gapWidth -= self.kerf
            tabWidth += self.kerf
            first = self.halfkerf
        else:
            gapWidth += self.kerf
            tabWidth -= self.kerf
            first = -self.halfkerf

        firstholelenX = 0
        firstholelenY = 0
        s = []
        h = []
        firstVec = 0
        secondVec = tabVec
        dividerEdgeOffsetX = dividerEdgeOffsetY = self.thickness
        notDirX = 0 if dirX else 1 # used to select operation on x or y
        notDirY = 0 if dirY else 1

        if self.tabSymmetry == 1:
            dividerEdgeOffsetX = dirX * self.thickness
            vectorX = rootX + (0 if dirX and prevTab else startOffsetX * self.thickness)
            vectorY = rootY + (0 if dirY and prevTab else startOffsetY * self.thickness)
            s = 'M ' + str(vectorX) + ',' + str(vectorY) + ' '
            vectorX = rootX + (startOffsetX if startOffsetX else dirX) * self.thickness
            vectorY = rootY + (startOffsetY if startOffsetY else dirY) * self.thickness
            if notDirX and tabVec:
                endOffsetX = 0
            if notDirY and tabVec:
                endOffsetY = 0
        else:
            (vectorX, vectorY) = (rootX + startOffsetX * self.thickness, rootY + startOffsetY * self.thickness)
            dividerEdgeOffsetX = dirY * self.thickness
            dividerEdgeOffsetY = dirX * self.thickness
            s = 'M ' + str(vectorX) + ',' + str(vectorY) + ' '
            if notDirX:
                vectorY = rootY # set correct line start for tab generation
            if notDirY:
                vectorX = rootX

        # generate line as tab or hole using various parameters
        for tabDivision in range(1, int(divisions)):
            if ((tabDivision % 2) ^ (not isTab)) and numDividers > 0 and not isDivider: # draw holes for divider tabs to key into side walls
                w = gapWidth if isTab else tabWidth
                if tabDivision == 1 and self.tabSymmetry == 0:
                    w -= startOffsetX * self.thickness
                holeLenX = dirX * w + notDirX * firstVec + first * dirX
                holeLenY = dirY * w + notDirY * firstVec + first * dirY
                if first:
                    firstholelenX = holeLenX
                    firstholelenY = holeLenY
                for dividerNumber in range(1, int(numDividers) + 1):
                    Dx = vectorX + -dirY * dividerSpacing * dividerNumber + notDirX * self.halfkerf + dirX * self.dogbone * self.halfkerf - self.dogbone * first * dirX
                    Dy = vectorY + dirX * dividerSpacing * dividerNumber - notDirY * self.halfkerf + dirY * self.dogbone * self.halfkerf - self.dogbone * first * dirY
                    if tabDivision == 1 and self.tabSymmetry == 0:
                        Dx += startOffsetX * self.thickness
                    h = 'M ' + str(Dx) + ',' + str(Dy) + ' '
                    Dx = Dx + holeLenX
                    Dy = Dy + holeLenY
                    h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                    Dx = Dx + notDirX * (secondVec - self.kerf)
                    Dy = Dy + notDirY * (secondVec + self.kerf)
                    h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                    Dx = Dx - holeLenX
                    Dy = Dy - holeLenY
                    h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                    Dx = Dx - notDirX * (secondVec - self.kerf)
                    Dy = Dy - notDirY * (secondVec + self.kerf)
                    h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                    self.paths.append(self.get_line_path(h))

            if tabDivision % 2:
                if tabDivision == 1 and numDividers > 0 and isDivider: # draw slots for dividers to slot into each other
                    for dividerNumber in range(1, int(numDividers) + 1):
                        Dx = vectorX + -dirY * dividerSpacing * dividerNumber - dividerEdgeOffsetX + notDirX * self.halfkerf
                        Dy = vectorY + dirX * dividerSpacing * dividerNumber - dividerEdgeOffsetY + notDirY * self.halfkerf
                        h = 'M ' + str(Dx) + ',' + str(Dy) + ' '
                        Dx = Dx + dirX * (first + length / 2)
                        Dy = Dy + dirY * (first + length / 2)
                        h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                        Dx = Dx + notDirX * (self.thickness - self.kerf)
                        Dy = Dy + notDirY * (self.thickness - self.kerf)
                        h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                        Dx = Dx - dirX * (first + length / 2)
                        Dy = Dy - dirY * (first + length / 2)
                        h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                        Dx = Dx - notDirX * (self.thickness - self.kerf)
                        Dy = Dy - notDirY * (self.thickness - self.kerf)
                        h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                        self.paths.append(self.get_line_path(h))
                        
                # draw the gap
                vectorX += dirX * (gapWidth + (isTab & self.dogbone & 1 ^ 0x1) * first + self.dogbone * self.kerf * isTab) + notDirX * firstVec
                vectorY += dirY * (gapWidth + (isTab & self.dogbone & 1 ^ 0x1) * first + self.dogbone * self.kerf * isTab) + notDirY * firstVec
                s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
                if self.dogbone and isTab:
                    vectorX -= dirX * self.halfkerf
                    vectorY -= dirY * self.halfkerf
                    s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
                # draw the starting edge of the tab
                s += self.dimple_str(secondVec, vectorX, vectorY, dirX, dirY, notDirX, notDirY, 1, isTab)
                vectorX += notDirX * secondVec
                vectorY += notDirY * secondVec
                s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
                if self.dogbone and notTab:
                    vectorX -= dirX * self.halfkerf
                    vectorY -= dirY * self.halfkerf
                    s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '

            else:
                # draw the tab
                vectorX += dirX * (tabWidth + self.dogbone * self.kerf * notTab) + notDirX * firstVec
                vectorY += dirY * (tabWidth + self.dogbone * self.kerf * notTab) + notDirY * firstVec
                s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
                if self.dogbone and notTab:
                    vectorX -= dirX * self.halfkerf
                    vectorY -= dirY * self.halfkerf
                    s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
                # draw the ending edge of the tab
                s += self.dimple_str(secondVec, vectorX, vectorY, dirX, dirY, notDirX, notDirY, -1, isTab)
                vectorX += notDirX * secondVec
                vectorY += notDirY * secondVec
                s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
                if self.dogbone and isTab:
                    vectorX -= dirX * self.halfkerf
                    vectorY -= dirY * self.halfkerf
                    s += 'L ' + str(vectorX) + ',' + str(vectorY) + ' '
            (secondVec, firstVec) = (-secondVec, -firstVec) # swap tab direction
            first = 0

        # finish the line off
        s += 'L ' + str(rootX + endOffsetX * self.thickness + dirX * length) + ',' + str(rootY + endOffsetY * self.thickness + dirY * length) + ' '

        if isTab and numDividers > 0 and self.tabSymmetry == 0 and not isDivider: # draw last for divider joints in side walls
            for dividerNumber in range(1, int(numDividers) + 1):
                Dx = vectorX + -dirY * dividerSpacing * dividerNumber + notDirX * self.halfkerf + dirX * self.dogbone * self.halfkerf - self.dogbone * first * dirX
                Dy = vectorY + dirX * dividerSpacing * dividerNumber - dividerEdgeOffsetY + notDirY * self.halfkerf
                h = 'M ' + str(Dx) + ',' + str(Dy) + ' '
                Dx = Dx + firstholelenX
                Dy = Dy + firstholelenY
                h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                Dx = Dx + notDirX * (self.thickness - self.kerf)
                Dy = Dy + notDirY * (self.thickness - self.kerf)
                h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                Dx = Dx - firstholelenX
                Dy = Dy - firstholelenY
                h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                Dx = Dx - notDirX * (self.thickness - self.kerf)
                Dy = Dy - notDirY * (self.thickness - self.kerf)
                h += 'L ' + str(Dx) + ',' + str(Dy) + ' '
                self.paths.append(self.get_line_path(h))

        self.paths.append(self.get_line_path(s))
        return s

    def generate_box(self):
        """Main function to generate the box geometry"""
        # Clear previous paths
        self.paths = []
        self.circles = []
        
        # Setup global variables (converted from original)
        self.nomTab = self.tab
        self.equalTabs = self.equal
        self.tabSymmetry = self.tabsymmetry
        self.dimpleHeight = self.dimpleheight
        self.dimpleLength = self.dimplelength
        self.halfkerf = self.kerf / 2
        self.dogbone = 1 if self.tabtype == 1 else 0
        self.divx = self.div_l
        self.divy = self.div_w
        self.keydivwalls = 0 if self.keydiv == 3 or self.keydiv == 1 else 1
        self.keydivfloor = 0 if self.keydiv == 3 or self.keydiv == 2 else 1

        # Set line thickness
        if self.hairline:
            self.linethickness = 0.002 * 25.4  # Convert from inches to mm
        else:
            self.linethickness = 1

        # Get dimensions (assuming mm units for simplicity)
        X = self.length + self.kerf
        Y = self.width + self.kerf
        Z = self.height + self.kerf

        if self.inside:  # if inside dimension selected correct values to outside dimension
            X += self.thickness * 2
            Y += self.thickness * 2
            Z += self.thickness * 2

        # Input validation
        error = 0
        if min(X, Y, Z) == 0:
            raise ValueError('Error: Dimensions must be non zero')
        if min(X, Y, Z) < 3 * self.nomTab:
            raise ValueError('Error: Tab size too large')
        if self.nomTab < self.thickness:
            raise ValueError('Error: Tab size too small')
        if self.thickness == 0:
            raise ValueError('Error: Thickness is zero')
        if self.thickness > min(X, Y, Z) / 3:
            raise ValueError('Error: Material too thick')
        if self.kerf > min(X, Y, Z) / 3:
            raise ValueError('Error: Kerf too large')
        if self.spacing < self.kerf:
            raise ValueError('Error: Spacing too small')

        # Determine which faces the box has based on the box type
        hasTp = hasBm = hasFt = hasBk = hasLt = hasRt = True
        if self.boxtype == 2:
            hasTp = False
        elif self.boxtype == 3:
            hasTp = hasFt = False
        elif self.boxtype == 4:
            hasTp = hasFt = hasRt = False
        elif self.boxtype == 5:
            hasTp = hasBm = False
        elif self.boxtype == 6:
            hasTp = hasFt = hasBk = hasRt = False

        # Determine where the tabs go based on the tab style
        if self.tabSymmetry == 2:     # Antisymmetric (deprecated)
            tpTabInfo = 0b0110
            bmTabInfo = 0b1100
            ltTabInfo = 0b1100
            rtTabInfo = 0b0110
            ftTabInfo = 0b1100
            bkTabInfo = 0b1001
        elif self.tabSymmetry == 1:   # Rotationally symmetric (Waffle-blocks)
            tpTabInfo = 0b1111
            bmTabInfo = 0b1111
            ltTabInfo = 0b1111
            rtTabInfo = 0b1111
            ftTabInfo = 0b1111
            bkTabInfo = 0b1111
        else:               # XY symmetric
            tpTabInfo = 0b0000
            bmTabInfo = 0b0000
            ltTabInfo = 0b1111
            rtTabInfo = 0b1111
            ftTabInfo = 0b1010
            bkTabInfo = 0b1010

        def fixTabBits(tabbed, tabInfo, bit):
            newTabbed = tabbed & ~bit
            if self.inside:
                newTabInfo = tabInfo | bit      # set bit to 1 to use tab base line
            else:
                newTabInfo = tabInfo & ~bit     # set bit to 0 to use tab tip line
            return newTabbed, newTabInfo

        # Update the tab bits based on which sides of the box don't exist
        tpTabbed = bmTabbed = ltTabbed = rtTabbed = ftTabbed = bkTabbed = 0b1111
        if not hasTp:
            bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b0010)
            ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b1000)
            ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b0001)
            rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b0100)
            tpTabbed = 0
        if not hasBm:
            bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b1000)
            ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b0010)
            ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b0100)
            rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b0001)
            bmTabbed = 0
        if not hasFt:
            tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b1000)
            bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b1000)
            ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b1000)
            rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b1000)
            ftTabbed = 0
        if not hasBk:
            tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b0010)
            bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b0010)
            ltTabbed, ltTabInfo = fixTabBits(ltTabbed, ltTabInfo, 0b0010)
            rtTabbed, rtTabInfo = fixTabBits(rtTabbed, rtTabInfo, 0b0010)
            bkTabbed = 0
        if not hasLt:
            tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b0100)
            bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b0001)
            bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b0001)
            ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b0001)
            ltTabbed = 0
        if not hasRt:
            tpTabbed, tpTabInfo = fixTabBits(tpTabbed, tpTabInfo, 0b0001)
            bmTabbed, bmTabInfo = fixTabBits(bmTabbed, bmTabInfo, 0b0100)
            bkTabbed, bkTabInfo = fixTabBits(bkTabbed, bkTabInfo, 0b0100)
            ftTabbed, ftTabInfo = fixTabBits(ftTabbed, ftTabInfo, 0b0100)
            rtTabbed = 0

        # Layout positions
        row0 = (1, 0, 0, 0)      # top row
        row1y = (2, 0, 1, 0)     # second row, offset by Y
        row1z = (2, 0, 0, 1)     # second row, offset by Z
        row2 = (3, 0, 1, 1)      # third row, always offset by Y+Z

        col0 = (1, 0, 0, 0)      # left column
        col1x = (2, 1, 0, 0)     # second column, offset by X
        col1z = (2, 0, 0, 1)     # second column, offset by Z
        col2xx = (3, 2, 0, 0)    # third column, offset by 2*X
        col2xz = (3, 1, 0, 1)    # third column, offset by X+Z
        col3xzz = (4, 1, 0, 2)   # fourth column, offset by X+2*Z
        col3xxz = (4, 2, 0, 1)   # fourth column, offset by 2*X+Z
        col4 = (5, 2, 0, 2)      # fifth column, always offset by 2*X+2*Z
        col5 = (6, 3, 0, 2)      # sixth column, always offset by 3*X+2*Z

        # Face types
        tpFace = 1
        bmFace = 1
        ftFace = 2
        bkFace = 2
        ltFace = 3
        rtFace = 3

        def reduceOffsets(aa, start, dx, dy, dz):
            for ix in range(start + 1, len(aa)):
                (s, x, y, z) = aa[ix]
                aa[ix] = (s - 1, x - dx, y - dy, z - dz)

        # Layout pieces based on style
        pieces = []
        if self.style == 1:  # Diagramatic Layout
            rr = deepcopy([row0, row1z, row2])
            cc = deepcopy([col0, col1z, col2xz, col3xzz])
            if not hasFt:
                reduceOffsets(rr, 0, 0, 0, 1)     # remove row0, shift others up by Z
            if not hasLt:
                reduceOffsets(cc, 0, 0, 0, 1)
            if not hasRt:
                reduceOffsets(cc, 2, 0, 0, 1)
            if hasBk:
                pieces.append([cc[1], rr[2], X, Z, bkTabInfo, bkTabbed, bkFace])
            if hasLt:
                pieces.append([cc[0], rr[1], Z, Y, ltTabInfo, ltTabbed, ltFace])
            if hasBm:
                pieces.append([cc[1], rr[1], X, Y, bmTabInfo, bmTabbed, bmFace])
            if hasRt:
                pieces.append([cc[2], rr[1], Z, Y, rtTabInfo, rtTabbed, rtFace])
            if hasTp:
                pieces.append([cc[3], rr[1], X, Y, tpTabInfo, tpTabbed, tpFace])
            if hasFt:
                pieces.append([cc[1], rr[0], X, Z, ftTabInfo, ftTabbed, ftFace])
        elif self.style == 2:  # 3 Piece Layout
            rr = deepcopy([row0, row1y])
            cc = deepcopy([col0, col1z])
            if hasBk:
                pieces.append([cc[1], rr[1], X, Z, bkTabInfo, bkTabbed, bkFace])
            if hasLt:
                pieces.append([cc[0], rr[0], Z, Y, ltTabInfo, ltTabbed, ltFace])
            if hasBm:
                pieces.append([cc[1], rr[0], X, Y, bmTabInfo, bmTabbed, bmFace])
        elif self.style == 3:  # Inline(compact) Layout
            rr = deepcopy([row0])
            cc = deepcopy([col0, col1x, col2xx, col3xxz, col4, col5])
            if not hasTp:
                reduceOffsets(cc, 0, 1, 0, 0)     # remove col0, shift others left by X
            if not hasBm:
                reduceOffsets(cc, 1, 1, 0, 0)
            if not hasLt:
                reduceOffsets(cc, 2, 0, 0, 1)
            if not hasRt:
                reduceOffsets(cc, 3, 0, 0, 1)
            if not hasBk:
                reduceOffsets(cc, 4, 1, 0, 0)
            if hasBk:
                pieces.append([cc[4], rr[0], X, Z, bkTabInfo, bkTabbed, bkFace])
            if hasLt:
                pieces.append([cc[2], rr[0], Z, Y, ltTabInfo, ltTabbed, ltFace])
            if hasTp:
                pieces.append([cc[0], rr[0], X, Y, tpTabInfo, tpTabbed, tpFace])
            if hasBm:
                pieces.append([cc[1], rr[0], X, Y, bmTabInfo, bmTabbed, bmFace])
            if hasRt:
                pieces.append([cc[3], rr[0], Z, Y, rtTabInfo, rtTabbed, rtFace])
            if hasFt:
                pieces.append([cc[5], rr[0], X, Z, ftTabInfo, ftTabbed, ftFace])

        # Generate each piece
        initOffsetX = 0
        initOffsetY = 0
        
        for idx, piece in enumerate(pieces):
            (xs, xx, xy, xz) = piece[0]
            (ys, yx, yy, yz) = piece[1]
            x = xs * self.spacing + xx * X + xy * Y + xz * Z + initOffsetX  # root x co-ord for piece
            y = ys * self.spacing + yx * X + yy * Y + yz * Z + initOffsetY  # root y co-ord for piece
            dx = piece[2]
            dy = piece[3]
            tabs = piece[4]
            a = tabs >> 3 & 1
            b = tabs >> 2 & 1
            c = tabs >> 1 & 1
            d = tabs & 1
            tabbed = piece[5]
            atabs = tabbed >> 3 & 1
            btabs = tabbed >> 2 & 1
            ctabs = tabbed >> 1 & 1
            dtabs = tabbed & 1
            xspacing = (X - self.thickness) / (self.divy + 1)
            yspacing = (Y - self.thickness) / (self.divx + 1)
            xholes = 1 if piece[6] < 3 else 0
            yholes = 1 if piece[6] != 2 else 0
            wall = 1 if piece[6] > 1 else 0
            floor = 1 if piece[6] == 1 else 0

            group_id = f"panel_{idx}"

            # Generate and draw the sides of each piece
            self.side(group_id, (x, y), (d, a), (-b, a), atabs * (-self.thickness if a else self.thickness), dtabs, dx, (1, 0), a, 0, (self.keydivfloor | wall) * (self.keydivwalls | floor) * self.divx * yholes * atabs, yspacing)
            self.side(group_id, (x + dx, y), (-b, a), (-b, -c), btabs * (self.thickness if b else -self.thickness), atabs, dy, (0, 1), b, 0, (self.keydivfloor | wall) * (self.keydivwalls | floor) * self.divy * xholes * btabs, xspacing)
            if atabs:
                self.side(group_id, (x + dx, y + dy), (-b, -c), (d, -c), ctabs * (self.thickness if c else -self.thickness), btabs, dx, (-1, 0), c, 0, 0, 0)
            else:
                self.side(group_id, (x + dx, y + dy), (-b, -c), (d, -c), ctabs * (self.thickness if c else -self.thickness), btabs, dx, (-1, 0), c, 0, (self.keydivfloor | wall) * (self.keydivwalls | floor) * self.divx * yholes * ctabs, yspacing)
            if btabs:
                self.side(group_id, (x, y + dy), (d, -c), (d, a), dtabs * (-self.thickness if d else self.thickness), ctabs, dy, (0, -1), d, 0, 0, 0)
            else:
                self.side(group_id, (x, y + dy), (d, -c), (d, a), dtabs * (-self.thickness if d else self.thickness), ctabs, dy, (0, -1), d, 0, (self.keydivfloor | wall) * (self.keydivwalls | floor) * self.divy * xholes * dtabs, xspacing)

            # Handle dividers if this is the first piece (template)
            if idx == 0:
                # remove tabs from dividers if not required
                if not self.keydivfloor:
                    a = c = 1
                    atabs = ctabs = 0
                if not self.keydivwalls:
                    b = d = 1
                    btabs = dtabs = 0

                y = 4 * self.spacing + 1 * Y + 2 * Z  # root y co-ord for piece
                for n in range(0, self.divx):  # generate X dividers
                    x = n * (self.spacing + X)  # root x co-ord for piece
                    group_id = f"x_divider_{n}"
                    self.side(group_id, (x, y), (d, a), (-b, a), self.keydivfloor * atabs * (-self.thickness if a else self.thickness), dtabs, dx, (1, 0), a, 1, 0, 0)
                    self.side(group_id, (x + dx, y), (-b, a), (-b, -c), self.keydivwalls * btabs * (self.thickness if b else -self.thickness), atabs, dy, (0, 1), b, 1, self.divy * xholes, xspacing)
                    self.side(group_id, (x + dx, y + dy), (-b, -c), (d, -c), self.keydivfloor * ctabs * (self.thickness if c else -self.thickness), btabs, dx, (-1, 0), c, 1, 0, 0)
                    self.side(group_id, (x, y + dy), (d, -c), (d, a), self.keydivwalls * dtabs * (-self.thickness if d else self.thickness), ctabs, dy, (0, -1), d, 1, 0, 0)
            elif idx == 1:
                y = 5 * self.spacing + 1 * Y + 3 * Z  # root y co-ord for piece
                for n in range(0, self.divy):  # generate Y dividers
                    x = n * (self.spacing + Z)  # root x co-ord for piece
                    group_id = f"y_divider_{n}"
                    self.side(group_id, (x, y), (d, a), (-b, a), self.keydivwalls * atabs * (-self.thickness if a else self.thickness), dtabs, dx, (1, 0), a, 1, self.divx * yholes, yspacing)
                    self.side(group_id, (x + dx, y), (-b, a), (-b, -c), self.keydivfloor * btabs * (self.thickness if b else -self.thickness), atabs, dy, (0, 1), b, 1, 0, 0)
                    self.side(group_id, (x + dx, y + dy), (-b, -c), (d, -c), self.keydivwalls * ctabs * (self.thickness if c else -self.thickness), btabs, dx, (-1, 0), c, 1, 0, 0)
                    self.side(group_id, (x, y + dy), (d, -c), (d, a), self.keydivfloor * dtabs * (-self.thickness if d else self.thickness), ctabs, dy, (0, -1), d, 1, 0, 0)

        return {
            'paths': self.paths,
            'circles': self.circles,
            'bounds': self.calculate_bounds()
        }

    def calculate_bounds(self):
        """Calculate the bounding box of all generated paths"""
        if not self.paths:
            return {'min_x': 0, 'min_y': 0, 'max_x': 0, 'max_y': 0}
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for path in self.paths:
            coords = self.extract_coords_from_path(path['data'])
            for x, y in coords:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        return {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y}
    
    def extract_coords_from_path(self, path_data):
        """Extract coordinates from SVG path data"""
        coords = []
        parts = path_data.split()
        i = 0
        while i < len(parts):
            if parts[i] in ['M', 'L']:
                if i + 1 < len(parts):
                    coord_str = parts[i + 1]
                    if ',' in coord_str:
                        x_str, y_str = coord_str.split(',')
                        try:
                            x, y = float(x_str), float(y_str)
                            coords.append((x, y))
                        except ValueError:
                            pass
                i += 2
            else:
                i += 1
        return coords

    def generate_svg(self, width=None, height=None):
        """Generate SVG content"""
        result = self.generate_box()
        bounds = result['bounds']
        
        if width is None:
            width = bounds['max_x'] - bounds['min_x'] + 20
        if height is None:
            height = bounds['max_y'] - bounds['min_y'] + 20
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}mm" height="{height}mm" 
     viewBox="{bounds['min_x']-10} {bounds['min_y']-10} {width} {height}">
  <g id="box_parts">
'''
        
        for path in result['paths']:
            svg_content += f'''    <path d="{path['data']}" style="stroke:{path['style']['stroke']};stroke-width:{path['style']['stroke-width']};fill:{path['style']['fill']}" />
'''
        
        for circle in result['circles']:
            svg_content += f'''    <circle cx="{circle['cx']}" cy="{circle['cy']}" r="{circle['r']}" style="stroke:{circle['style']['stroke']};stroke-width:{circle['style']['stroke-width']};fill:{circle['style']['fill']}" />
'''
        
        svg_content += '''  </g>
</svg>'''
        
        return svg_content
