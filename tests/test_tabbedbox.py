import io
import os
import re
import unittest
import tabbedboxmaker.inkex

blank_svg=b'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   width="210mm"
   height="297mm"
   viewBox="0 0 210 297"
   version="1.1"
   id="svg5"
   inkscape:version="1.1.2 (0a00cf5339, 2022-02-04)"
   sodipodi:docname="blank.svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <sodipodi:namedview
     id="namedview7"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageshadow="2"
     inkscape:pageopacity="0.0"
     inkscape:pagecheckerboard="0"
     inkscape:document-units="mm"
     showgrid="false"
     inkscape:zoom="0.64052329"
     inkscape:cx="397.33138"
     inkscape:cy="561.25984"
     inkscape:window-width="2086"
     inkscape:window-height="1376"
     inkscape:window-x="0"
     inkscape:window-y="0"
     inkscape:window-maximized="1"
     inkscape:current-layer="layer1" />
  <defs
     id="defs2" />
  <g
     inkscape:label="Layer 1"
     inkscape:groupmode="layer"
     id="layer1" />
</svg>
'''


def mask_panel_ids(svgin: str) -> str:
    return re.sub(r'"panel\d+"', '"panelTEST"', svgin)

class TestTabbedBox(unittest.TestCase):

    def test_tabbed(self):
        # See boxmaker.inx for arg descriptions
        cases = [
            {
                'label': 'fully_enclosed',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=1', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'open_top',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'two_sides_open',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=3', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'three_sides_open',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=4', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'opposite_ends_open',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=5', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'two_panels_only',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=6', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'outside_measurement',
                'args': [
                    '--unit=mm', '--inside=0', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_dogbone',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=1',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_dimple',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0.2', '--dimplelength=0.2',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_rotate_symmetry_tabs',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=1', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_thick_lines',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=0', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_nonzero_kerf',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0.1', '--style=1',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'threepiece_layout',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=2',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'inline_layout',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=3',
                    '--boxtype=2', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_dividers_keyed_all',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=1', '--div_w=1', '--keydiv=0',
                    '--spacing=1'],
            },
            {
                'label': 'with_dividers_keyed_floor',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=1', '--div_w=1', '--keydiv=1',
                    '--spacing=1'],
            },
            {
                'label': 'with_dividers_keyed_walls',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=1', '--div_w=1', '--keydiv=2',
                    '--spacing=1'],
            },
            {
                'label': 'with_dividers_keyed_none',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tab=6', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=2', '--div_l=1', '--div_w=1', '--keydiv=3',
                    '--spacing=1'],
            },
            {
                'label': 'default_tabs',
                'args': [
                    '--unit=mm', '--inside=1', '--length=80', '--width=100',
                    '--depth=40', '--equal=0', '--tabtype=0',
                    '--tabsymmetry=0', '--dimpleheight=0', '--dimplelength=0',
                    '--hairline=1', '--thickness=3', '--kerf=0', '--style=1',
                    '--boxtype=1', '--div_l=0', '--div_w=0', '--keydiv=1',
                    '--spacing=1'],
            },
        ]

        for case in cases:
            with self.subTest(label=case['label']):
                infh = io.BytesIO(blank_svg)
                outfh = io.BytesIO()
                expected_output_dir = os.path.join(
                    os.path.dirname(__file__), 'expected'
                )
                expected_file = os.path.join(
                    expected_output_dir, case['label'] + '.svg'
                )
                expected = ''
                with open(expected_file, 'r') as f:
                    expected = mask_panel_ids(f.read())

                tbm = tabbedboxmaker.inkex.InkexBoxMaker()

                tbm.parse_arguments(case['args'])
                tbm.options.input_file = infh
                tbm.options.output = outfh

                tbm.load_raw()
                tbm.save_raw(tbm.effect())

                output = mask_panel_ids(outfh.getvalue().decode('utf-8'))

                # Set self.maxDiff to None to see full diff.
                #self.maxDiff = None
                self.assertEqual(expected, output)
