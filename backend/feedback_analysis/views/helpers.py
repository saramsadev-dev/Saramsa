"""
Helper functions for feedback analysis views.

Contains shared utility functions used across different view modules.
"""

import json


def flattenComments(comments):
    """
    Flatten comments data structure to extract text content.
    
    Args:
        comments (list): List of comment objects with 'text' field
        
    Returns:
        str: JSON string of flattened comment texts
    """
    dataText = []
    for comment in comments:
        dataText.append(comment["text"])
    return json.dumps(dataText)
