# BoxMaker: A free tool for creating boxes using tabbed construction

_version 0.94 - 5 Jan 2017_

Original box maker by Elliot White - http://www.twot.eu/111000/111000.html

Updated Dec 2014 by Paul Hutchison - additional box options for 2,3,4,5 sides and internal dividers

Updated June 2015 by Paul Hutchison - Inkscape 0.91 compatibility, more logical defaults

Updated July 2015 by John Slee - Added Schroff enclosure generator option. Currently 3U rows only.

Updated Sept 2015 by Paul Hutchison - Elliot White got in touch to provide updated contact details

v0.93 - 15/8/2016 by Paul Hutchison - Added Hairline option and fixed open box height bug
 
v0.94 - 05/01/2017 by Paul Hutchison - Added option for keying dividers into walls/floor/none


## About
 This tool is designed to simplify and speed up process of making practical boxes using a laser cutter (though it can be used with any CNC cutter) to prepare the pieces.

 The tool works by generating a drawing of the pieces of the box with the tab and hole size corrected to account for the kerf (width of cut), these pieces are composed of sides, each side being a discreet object, to move a piece in the drawing the edges need to be grouped together.

## Release Notes
 So far no serious bugs( i.e causing runtime errors ) have been found. The program works with python versions 2.6.5, 2.6.7 and 2.7.2, other version have not yet been tried except python 2.5.1 which fails with a syntax error.

This version has been tried on windows XP, windows 7, Ubuntu and Mac OS X with no serious problems ( the live preview works most of the time but can be flaky).

 Only crude input checking has been implemented in the program but as the only output is a drawing the worst that can happen is a messed up picture ( control-Z cures that problem ).

## To do
* Tidy the code - it is rough and unpythonic.  Needs some work by a master Python guru.
* Improve program documentation. Improve input checking to restrict values to correct solutions.
* [Schroff] Maybe replace the somewhat obscure collection of Schroff rail input data with a dropdown box listing well-documented rail types (Vector, Z-rails, whatever it is that Elby sells, others?)
* [Schroff] Add support for multiple mounting holes per rail where possible (this would definitely make the previous todo item worthwhile)
* [Schroff] Add support for 6U row height

## Use - regular tabbed boxes
 The interface is pretty self explanatory, the extension is 'Tabbed Box Maker' in the 'Laser Tools' group ( hopefully more tools will soon{ish} join it ).

In order of appearance:

* Unit - unit of measurement used for drawing

* Box Dimensions: Inside/Outside - whether the box dimensions are internal or external

* Length; Width; Height - the box dimensions

* Minimum/Preferred Tab Width - the size of the tabs used to hold the pieces together

* Tab Width: Fixed/Proportional - for fixed the tab width is the value given in the Tab
                                 Width, for proportional the side of a piece is divided 
                                 equally into tabs and 'spaces' with the tabs size 
                                 greater or equal to the Tab Width setting

* Material Thickness - as it says
 
* Kerf - this is the width of the cut ( e.g for 3mm acrylic on an epilog cutter this is
        approximately 0.25mm )

* Clearance - this value is subtracted from the kerf in cases where you deliberately want
             slightly slacker joints ( usually zero )

* Layout/Style - { This is where additions/changes will most likely occur, also having a
                problem with live preview: it is best to turn preview off when changing this 
                setting }
                this setting determines both the type of drawing produced and the way tabs
                are used on the sides of pieces.

* Box style - this allows you to choose how many jointed sides you want. Options are:
    * Fully enclosed (6 sides)
    * One side open (LxW) - one of the Length x Width panels will be omitted
    * Two sides open (LxW and LxH) - two adjacent panels will be omitted
    * Three sides open (LxW, LxH, HxW) - one of each panel omitted
    * Opposite ends open (LxW) - an open-ended "tube" with the LxW panels omitted
    * Two panels only (LxW and LxH) - two panels with a single joint down the Length axis
 

			
* Dividers (Length axis) - use this to create additional LxH panels that mount inside the box 
						 along the length axis and have finger joints into the side panels
						 and slots for Width dividers to slot into
				
* Dividers (Width axis) - use this to create additional WxH panels that mount inside the box 
						 along the width axis and have finger joints into the side panels
						 and slots for Length dividers to slot into
						 
* Key the dividers into - this allows you to choose if/how the dividers are keyed into the sides of the box. Options are:
	* None - no keying, dividers will be free to slide in and out
	* Walls - dividers will only be keyed into the side walls of the box
	* Floor/Ceiling - dividers will only be keyed into the top/bottom of the box
	* All Sides
				
* Space Between Parts - how far apart the pieces are in the drawing produced

## Use - Schroff enclosures

Much the same as for regular enclosures, except some options are removed, and some others are added. If you're using Elby rails, all you'll need to do is specify:

* Depth

* Number of 3U rows

* Row width in TE/HP units (divide rail length by 5.08mm/0.2")

* If multiple rows, inter-row spacing

## Installation
Boxmaker.inx, Schroffmaker.inx and Boxmaker.py need to be put in the inkscape extensions folder  generally in: 

   `...\Inkscape\share\extensions `

or linux:

   `usr/.../Inkscape/share/extensions`

(NOTE: you need to make boxmaker.py executable)

## Version History
version | Date | Notes
--------|------|--------
0.5  | ( 9 Oct 2011) | beta
0.7  | (24 Oct 2011) | first release
0.8  | (26 Oct 2011) | basic input checking implemented
0.86 | (19 Dec 2014) | updates to allow different box types and internal dividers
0.86a | (23 June 2015) | Updated for compatibility with Inkscape 0.91
0.87 | (28 July 2015) | Schroff enclosure add-on
0.93 | (21 Sept 2015) | Updated versioning to match original author's updated v0.91 plus adding my 0.02 
