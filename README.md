# TabbedBoxMaker: A free Inkscape extension for generating tab-jointed box patterns

_version 1.2 - 27 Nov 2022_

Original box maker by Elliot White (formerly of twot.eu, domain name now squatted)

Heavily modified by [Paul Hutchison](https://github.com/paulh-rnd)

## About
 This tool is designed to simplify the process of making practical boxes from sheet material using almost any kind of CNC cutter (laser, plasma, water jet or mill). The box edges are "finger-jointed" or "tab-jointed", and may include press-fit dimples, internal dividers, dogbone corners (for endmill cutting), and more.

 The tool works by generating each side of the box with the tab and edge sizes corrected to account for the kerf (width of cut). Each box side is composed of a group of individual lines that make up each edge of the face, as well as any other cutouts for dividers. It is recommended that you join adjacent lines in your CNC software to cut efficiently.

 An additional extension which uses the same TabbedBoxMaker generator script is also included: Schroff Box Maker. The Schroff addition was created by [John Slee](https://github.com/jsleeio). If you create further derivative box generators, feel free to send me a pull request!

## Release Notes
This is a major upgrade to support Inkscape v1.0 and CNC mills (with dogbone cuts), plus an updated dialog layout and documentation, and a number of smaller fixes. So far no serious bugs (i.e causing runtime errors) have been found. The program works with Python 3 ONLY. See [issues](https://github.com/paulh-rnd/TabbedBoxMaker/issues) for known issues, or to log issues and enhancement requests.

Note that in this release the extension has *moved from the Laser Tools to the CNC Tools submenu*.  This is to better reflect that this tool can be used on a wide variety of CNC machinery, especially with the addition of dogbone corners: laser, water jet, milling, even 3D printing.
 
## Donate
 Any donations will be gratefully received:

 [![](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.me/SparkItUp)

 Many thanks to those who have donated.

## To do
* Tidy, modularise and simplify the code - it is rough and unpythonic.  Needs some work by a master Python guru.
* Add tests and perhaps get it submitted as a core extension to be installed with Inkscape?
* Improve input checking to restrict values to correct solutions.
* Dogbone only works on tabbed joins, NOT divider keyholes or slots yet
* Would be great to make shapes closed and do path subtraction to get slot cutouts and keyholes from faces, and perhaps offer to add fill colour
* [Schroff] Maybe replace the somewhat obscure collection of Schroff rail input data with a dropdown box listing well-documented rail types (Vector, Z-rails, whatever it is that Elby sells, others?)
* [Schroff] Add support for multiple mounting holes per rail where possible (this would definitely make the previous todo item worthwhile)
* [Schroff] Add support for 6U row height

## Use - regular tabbed boxes
 The interface is pretty self explanatory, the extension is 'Tabbed Box Maker' in the 'CNC Tools' group

Parameters in order of appearance:

* Units - unit of measurement used for drawing

* Box Dimensions: Inside/Outside - whether the box dimensions are internal or external measurements

* Length / Width / Height - the box dimensions

* Tab Width: Fixed/Proportional - for fixed the tab width is the value given in the Tab
                                 Width, for proportional the side of a piece is divided 
                                 equally into tabs and 'spaces' with the tabs size 
                                 greater or equal to the Tab Width setting

* Minimum/Preferred Tab Width - the size of the tabs used to hold the pieces together

* Symmetry - there are two styles of tabs avaiable:
    * XY Symmetrix - each piece is symmetric in both the X and Y axes
    * Rotate Symmetric ("waffle block") - each piece is symmetric under a 180-degree rotation
      (and 90 degrees if that piece is square)

* Tab Dimple Height - the height of the dimple to add to the side of each tab, 0 for no dimple.
  Dimples can be added to give tabbed joints a little extra material for a tighter press fit.

* Tab Dimple Length - the length of the tip of the dimple; dimples are trapezoid shaped with
  45-degree sides; using a dimple tip length of 0 gives a triangular dimple

* Line Thickness - Leave this as _Default_ unless you need hairline thickness (Use for Epilog lasers)

* Material Thickness - as it says
 
* Kerf - this is the diameter/width of the cut. Typical laser cutters will be between 0.1 - 0.25mm, 
  for CNC mills, this will be your end mill diameter. A larger kerf will assume more material is removed,
  hence joints will be tighter. Smaller or zero kerf will result in looser joints.

* Layout - controls how the pieces are laid out in the drawing

* Box Type - this allows you to choose how many jointed sides you want. Options are:
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

* Live Preview - you may need to turn this off when changing tab style, box type, or layout

## Use - Schroff enclosures

Much the same as for regular enclosures, except some options are removed, and some others are added. If you're using Elby rails, all you'll need to do is specify:

* Depth

* Number of 3U rows

* Row width in TE/HP units (divide rail length by 5.08mm/0.2")

* If multiple rows, inter-row spacing

## Installation

1. Download the extension from this GitHub page using the *[Clone or download > Download ZIP](archive/refs/heads/master.zip)* link. If you are using an older version of Inkscape, you will need to download the correct version of the extension (see [Version History](#version-history) below)
2. Extract the zip file
3. Copy all files except README.md and LICENSE into the Inkscape extensions directory.  The directory location varies depending on your operating system, and may be customised. The easiest way to find the directory is to open Inkscape, go to _Edit > Preferences > System_ (Win/Linux) or _Inkscape > Preferences > System_ (Mac).
4. You can either copy the files to the _User extensions_ directory or the _Inkscape extensions_ directory.  The former will install this extension for just the current user, the latter will install it for all users of the machine.
5. Inkscape *must* be restarted after copying the extension files.
6. If it has been installed correctly, you should find the extension under the _Extensions > CNC Tools_ menu. Enjoy!

Default installation directories are given below:

### Windows

* User: `%APPDATA%\inkscape\extensions`
* Machine: `C:\Program Files\Inkscape\share\extensions`

### Mac

* User: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions`
* Machine: `/Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions`

### Linux

* User: `~/.config/inkscape/extensions`
* Machine: Depends on installation method

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
0.93a | (21 Sept 2015) | Added hairline line thickness option for Epilog lasers
0.94 | (4 Jan 2017) | Divider keying options
0.95 | (20 Apr 2017) | Added optional dimples on tabs
0.96 | (24 Apr 2017) | Orthogonalized box type, layout, tab style; added rotate-symmetric tabs
0.99 | (4 June 2020) | Upgraded to support Inkscape v1.0, minor fixes and a tidy up of the parameters dialog layout
1.0 |  (17 June 2020) | v1.0 final released: fixes and dogbone added - Mills now supported!
1.1 |  (9 Aug 2021) | v1.1 with fixes for newer Inkscape versions - sorry for the delays
1.2 | (18 Dec 2022) | v1.2 retructure as python package
