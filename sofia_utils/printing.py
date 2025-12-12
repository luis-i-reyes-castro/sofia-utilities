#!/usr/bin/env python3
"""
Utilities for printing and formatting string
"""

from re import match
from typing import Any

""" Indentation default mode"""
DEFAULT_INDENT = 'tabs'
""" Indentation spaces when in 'spaces' mode """
INDENT_SPACES  = 4

""" Base64 check length. Strings of this length or longer will be suspected to being Base64 image encondings. """
B64_CHECK_LEN = 2000
""" Maximum recursion depth """
MAX_RECURSION_DEPTH = 10

def str_ind( arg : str,
             indent = 0,
             indent_type : str = DEFAULT_INDENT ) -> str :
    
    space = None
    match indent_type :
        case 'spaces' :
            space = ' ' * INDENT_SPACES * indent
        case 'tabs' :
            space = '\t' * indent
        case _ :
            raise ValueError(f"In str_ind: Invalid ind_type '{indent_type}'")
    
    lines  = str(arg).split('\n')
    result = []
    for line in lines :
        result.append(f'{space}{line}')
    
    return '\n'.join(result)

def str_recursively( data : Any,
                     indent = 0,
                     indent_type : str = DEFAULT_INDENT,
                     visited : set = None ) -> str :
    
    # Initialize visited set to track circular references
    if visited is None :
        visited = set()
    
    # Check for circular references
    data_id = id(data)
    if data_id in visited :
        msg = f"<circular reference to {type(data).__name__}>"
        return str_ind( msg, indent, indent_type)
    
    # Add current object to visited set
    visited.add(data_id)
    
    # None
    if data is None :
        visited.remove(data_id)
        return str_ind( "None", indent, indent_type)
    
    # Raw binary data (bytes)
    elif isinstance( data, bytes):
        display_len = min( 4, len(data))
        shown       = data[:display_len]
        shown_str   = ' '.join( f'{b:02x}' for b in shown )
        
        if len(data) > 4 :
            shown_str += ' ...'
        
        visited.remove(data_id)
        return str_ind( f"bytes: {shown_str}", indent, indent_type)
    
    # Strings
    elif isinstance( data, str) :

        # Check for Base64 image encoding
        if len(data) >= B64_CHECK_LEN :
            b64_chars = "A-Za-z0-9+/="
            if match( fr'data:image/[a-z]+;base64,[{b64_chars}]+$', data) \
            or match( fr'[{b64_chars}]+$', data) :
                visited.remove(data_id)
                return str_ind( "str: [Base64 Image Enconding]", indent, indent_type)
        
        visited.remove(data_id)
        return str_ind( f"str: {data}", indent, indent_type)
    
    # Numbers
    elif isinstance( data, int) or isinstance( data, float) :
        data_t = data.__class__.__name__
        visited.remove(data_id)
        return str_ind( f"{data_t}: {str(data)}", indent, indent_type)
    
    # Lists and tuples
    elif isinstance( data, list) or isinstance( data, tuple) :
        
        title  = "list:" if isinstance( data, list) else "tuple:"
        border = '[]' if isinstance( data, list) else '()'
        
        if not data :
            visited.remove(data_id)
            return str_ind( f"{title} {border}", indent, indent_type)
        
        result = []
        result.append( str_ind( title,     indent, indent_type) )
        result.append( str_ind( border[0], indent, indent_type) )
        
        for item in data :
            result.append( str_ind( '[>] item:',  indent,     indent_type) )
            result.append( str_recursively( item, indent + 1, indent_type, visited) )
        
        result.append( str_ind( border[1], indent, indent_type) )
        
        visited.remove(data_id)
        return '\n'.join(result)
    
    # Dictionaries
    elif isinstance( data, dict) :
        
        if not data :
            visited.remove(data_id)
            return str_ind( "dict: {}", indent, indent_type)
        
        result = []
        result.append( str_ind( 'dict:', indent, indent_type) )
        result.append( str_ind( '{',     indent, indent_type) )
        
        for key, val in data.items() :
            result.append( str_ind( f'[>] {key}:', indent,     indent_type) )
            result.append( str_recursively( val,   indent + 1, indent_type, visited) )
        
        result.append( str_ind( '}', indent, indent_type) )
        
        visited.remove(data_id)
        return '\n'.join(result)
    
    # Class definitions (uninstantiated)
    elif isinstance( data, type) :
        visited.remove(data_id)
        return str_ind( f"definition of class '{data.__name__}'", indent, indent_type)
    
    # Class objects (instantiated)
    elif hasattr( data, "__class__") and hasattr( data.__class__, "__name__") :
        
        result  = []
        data_t  = data.__class__.__name__
        msg_str = f"object of class '{data_t}'"
        result.append( str_ind( msg_str, indent, indent_type) )

        # Prevent infinite recursion
        if indent > MAX_RECURSION_DEPTH :
            result.append( str_ind( f"<max depth reached>", indent + 1, indent_type) )
            visited.remove(data_id)
            return '\n'.join(result)

        if hasattr( data, "__dict__") or hasattr( data, "__slots__") :            
            
            attrs = {}
            if hasattr( data, "__dict__") :
                attrs = data.__dict__
            else :
                slots = getattr( data, "__slots__")
                if isinstance( slots, str) :
                    slots = [slots]
                for slot_ in slots :
                    if hasattr( data, slot_) :
                        attrs[slot_] = getattr( data, slot_)
            
            # Filter out internal/private attributes
            filtered_attrs = {}
            for att, val in attrs.items() :
                if not ( att.startswith( '_' ) or att.startswith( '__' ) ) :
                    filtered_attrs[att] = val
            
            if filtered_attrs :
                result.append( str_ind( '{', indent, indent_type) )
                for att, val in filtered_attrs.items() :
                    result.append( str_ind( f"[>] {att}:", indent, indent_type) )
                    result.append( str_recursively( val, indent + 1, indent_type, visited) )
                result.append( str_ind( '}', indent, indent_type) )
        
        visited.remove(data_id)
        return '\n'.join(result)
    
    # Fallback
    visited.remove(data_id)
    return str_ind( f"object of type {type(data)}", indent, indent_type)

def str_sep( width : int = 80) -> str :
    
    return '-' * width

def print_ind( arg : str,
               indent = 0,
               indent_type : str = DEFAULT_INDENT ) -> None :
    
    print(str_ind( arg, indent, indent_type))
    
    return

def print_recursively( data : Any,
                       indent = 0,
                       indent_type : str = DEFAULT_INDENT ) -> None :
    
    print(str_recursively( data, indent, indent_type))
    
    return

def print_sep( width : int = 80) -> None :
    
    print(str_sep(width))
    
    return

def print_validation_errors( errors : list[ dict[ str, Any] ],
                             indent : int = 2 ) -> None :
    
    for error in errors :
        
        location_raw = error.get( "loc", ())
        if location_raw :
            location = " -> ".join( str(part) for part in location_raw )
        else :
            location = "<root>"
        
        message = error.get("msg", "Validation error")
        
        print_ind( f"Location : {location}", indent)
        print_ind( f"Message  : {message}",  indent)
    
    return
