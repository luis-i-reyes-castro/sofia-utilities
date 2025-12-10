"""
Utilities for generating stamps (UUIDs, timestamps, sha256, etc.)
"""

from datetime import datetime
from datetime import timezone
from git import Repo
from hashlib import sha256
from random import choices
from string import ascii_letters
from string import digits
from uuid import uuid4

def generate_B62ID( length : int) -> str :
    """
    Generate Base62 random ID. (Characters in A-Z, a-z and 0-9.)
    
    Args:
        length: Desired ID length (number of characters)
    Returns:
        str: Random ID of the desired length
    """
    return "".join( choices( list( ascii_letters + digits ), k = length) )

def generate_UUID() -> str :
    """
    Generate UUID
    """
    return str(uuid4())

def get_now_utc_iso() -> str :
    """
    Get current UTC time as ISO 8601 formatted string.
    
    Returns a timestamp in ISO 8601 format with UTC timezone indicator (Z suffix).
    Microseconds are removed for consistency.
    
    Returns:
        str: ISO 8601 formatted UTC timestamp (e.g., "2024-01-15T10:30:00Z")
    """
    now_dt  = datetime.now(timezone.utc)
    now_str = now_dt.isoformat( timespec = "microseconds")
    now_str = now_str.replace( "+00:00", "Z")
    
    return now_str

def get_repo_main_hash() -> str :
    """
    Get the hash of the repository's main branch
    Returns:
        str: Hash as hexadecimal number
    """
    repo = Repo( search_parent_directories = True)
    return repo.heads.main.commit.hexsha

def get_sha256( data : bytes) -> str :
    """
    Calculate SHA-256 hash of binary data.
    
    Args:
        data: Binary data to hash
    
    Returns:
        str: Hexadecimal representation of the SHA-256 hash
    """
    h = sha256()
    h.update(data)
    return h.hexdigest()

def unix_to_utc_iso( epoch : int | str | None) -> str | None :
    """
    Convert a Unix epoch timestamp string to ISO 8601 formatted string.
    
    Returns a timestamp in ISO 8601 format with UTC timezone indicator (Z suffix).
    Microseconds are removed for consistency.
    
    Args:
        epoch: Unix epoch time string
    
    Returns:
        str: ISO 8601 formatted UTC timestamp (e.g., "2024-01-15T10:30:00Z") or 
             None (if conversion fails)
    """
    if epoch and isinstance( epoch, int) :
        epoch = str(epoch)
    
    if epoch and isinstance( epoch, str) :
        try:
            epoch = epoch.strip()
            if epoch :
                ts_dt  = datetime.fromtimestamp( float(epoch), tz = timezone.utc)
                ts_str = ts_dt.isoformat( timespec = "seconds")
                ts_str = ts_str.replace( "+00:00", "Z")
                
                return ts_str
            
        except Exception as ex:
            print(f"In unix_epoch_to_utc_iso: {ex}")
    
    return None

def utc_iso_to_dt( ts : str | None) -> datetime | None :
    """
    Convert ISO 8601 timestamp string to datetime object.
    
    Handles both formats with and without 'Z' suffix for UTC timezone.
    
    Args:
        ts: ISO 8601 timestamp string
            (e.g., "2024-01-15T10:30:00Z" or "2024-01-15T10:30:00+00:00")
    
    Returns:
        datetime: datetime object or None (if conversion fails)
    """
    if ts :
        try :
            if ts.endswith("Z") :
                ts = ts.replace( "Z", "+00:00")
            return datetime.fromisoformat(ts)
        
        except Exception as ex :
            print(f"In utc_iso_to_dt: {ex}")
    
    return None
