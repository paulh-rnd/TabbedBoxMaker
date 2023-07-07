import io
import os
import re
import unittest
import tabbedboxmaker

class TestPath(unittest.TestCase):

    def test_boundingbox(self):
        path = tabbedboxmaker.Path(0,0)
        path.add(tabbedboxmaker.LineSegment(1,1))
        path.add(tabbedboxmaker.LineSegment(1,-1))
        bb = path.boundingbox()
        self.assertEqual(bb, ((0,-1), (1,1)))
        
