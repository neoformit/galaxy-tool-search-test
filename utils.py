"""Auxilliary utilities."""


def to_unicode(a_string):
    """
    Convert a string to unicode in utf-8 format; if string is already unicode,
    does nothing because string's encoding cannot be determined by introspection.
    """
    return unicodify(a_string, encoding='utf-8')


def unicodify(value, encoding='utf-8', error="replace", strip_null=False, log_exception=True):
    """
    Returns a Unicode string or None.

    >>> assert unicodify(None) is None
    >>> assert unicodify('simple string') == 'simple string'
    >>> assert unicodify(3) == '3'
    >>> assert unicodify(bytearray([115, 116, 114, 196, 169, 195, 177, 103])) == 'strĩñg'
    >>> assert unicodify(Exception('strĩñg')) == 'strĩñg'
    >>> assert unicodify('cómplǐcḁtëd strĩñg') == 'cómplǐcḁtëd strĩñg'
    >>> s = 'cómplǐcḁtëd strĩñg'; assert unicodify(s) == s
    >>> s = 'lâtín strìñg'; assert unicodify(s.encode('latin-1'), 'latin-1') == s
    >>> s = 'lâtín strìñg'; assert unicodify(s.encode('latin-1')) == 'l\ufffdt\ufffdn str\ufffd\ufffdg'
    >>> s = 'lâtín strìñg'; assert unicodify(s.encode('latin-1'), error='ignore') == 'ltn strg'
    """
    if value is None:
        return value
    try:
        if isinstance(value, bytearray):
            value = bytes(value)
        elif not isinstance(value, (str, bytes)):
            value = str(value)
        # Now value is an instance of bytes or str
        if not isinstance(value, str):
            value = str(value, encoding, error)
    except Exception as e:
        if log_exception:
            msg = f"Value '{repr(value)}' could not be coerced to Unicode: {type(e).__name__}('{e}')"
            log.exception(msg)
        raise
    if strip_null:
        return value.replace("\0", "")
    return value
