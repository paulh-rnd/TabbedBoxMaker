"""
Constants and enums for BoxMaker
"""
from enum import IntEnum


class BoxType(IntEnum):
    """Box types available"""
    FULL_BOX = 1
    NO_TOP = 2
    NO_BOTTOM = 3
    NO_SIDES = 4
    NO_FRONT_BACK = 5
    NO_LEFT_RIGHT = 6


class TabType(IntEnum):
    """Tab cutting types"""
    LASER = 0  # Standard tabs for laser cutting
    CNC = 1    # Dogbone tabs for CNC milling


class LayoutStyle(IntEnum):
    """Layout styles for arranging box pieces"""
    SEPARATED = 1
    NESTED = 2
    COMPACT = 3


class KeyDividerType(IntEnum):
    """Key divider types"""
    WALLS_AND_FLOOR = 0
    WALLS_ONLY = 1
    FLOOR_ONLY = 2
    NONE = 3


# Default values
DEFAULT_LENGTH = 100.0
DEFAULT_WIDTH = 100.0
DEFAULT_HEIGHT = 100.0
DEFAULT_TAB_WIDTH = 25.0
DEFAULT_THICKNESS = 3.0
DEFAULT_KERF = 0.5
DEFAULT_SPACING = 25.0

# Minimum values for validation (realistic for woodworking)
MIN_DIMENSION = 40.0  # 4cm minimum for practical boxes
MIN_THICKNESS = 0.1
MIN_TAB_WIDTH = 2.0   # Minimum practical tab width (2mm is reasonable for thin materials)

# Tab sizing guidelines (based on material thickness)
MIN_TAB_TO_THICKNESS_RATIO = 0.5  # Tabs can be thinner but become weak
RECOMMENDED_MIN_TAB_TO_THICKNESS_RATIO = 1.0  # Recommended minimum for strength
MAX_TAB_TO_THICKNESS_RATIO = 20.0  # Very large tabs for big boxes (was 8.0)
RECOMMENDED_MAX_TAB_TO_THICKNESS_RATIO = 8.0  # Typical maximum for most boxes
RECOMMENDED_TAB_TO_THICKNESS_RATIO = 3.0  # 3x thickness is typical

# Maximum reasonable values
MAX_DIMENSION = 10000.0
MAX_THICKNESS = 100.0

# Conversion factors
INCHES_TO_MM = 25.4
HAIRLINE_THICKNESS_INCHES = 0.002
