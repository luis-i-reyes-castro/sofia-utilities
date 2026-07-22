"""
Pydantic-related Helpers
"""

from __future__ import annotations

from pydantic import ValidationError

from .printing import print_ind


def print_validation_errors( ve : ValidationError, indent : int = 4) -> None :
    """
    Pretty-print pydantic validation errors with indentation \\
    Args:
        validation_error : ValidationError object raised by pydantic
        indent           : Indentation level when printing
    """
    
    for error in ve.errors() :
        
        location_raw = error.get( "loc", ())
        if location_raw :
            location = str(" -> ").join( str(part) for part in location_raw )
        else :
            location = "<root>"
        
        message = error.get( "msg", "Validation error")
        
        print_ind( f"Location : {location}", indent)
        print_ind( f"Message  : {message}",  indent)
    
    return
