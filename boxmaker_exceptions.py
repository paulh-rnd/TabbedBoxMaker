"""
Custom exceptions for BoxMaker
"""


class BoxMakerError(Exception):
    """Base exception for BoxMaker errors"""
    pass


class DimensionError(BoxMakerError):
    """Raised when box dimensions are invalid"""
    def __init__(self, dimension_name, value, min_val=None, max_val=None):
        self.dimension_name = dimension_name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        
        if min_val and value < min_val:
            message = f"{dimension_name} ({value}) must be at least {min_val}"
        elif max_val and value > max_val:
            message = f"{dimension_name} ({value}) must be no more than {max_val}"
        else:
            message = f"{dimension_name} ({value}) is invalid"
            
        super().__init__(message)


class TabError(BoxMakerError):
    """Raised when tab configuration is invalid"""
    pass


class MaterialError(BoxMakerError):
    """Raised when material thickness configuration is invalid"""
    pass
