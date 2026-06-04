#!/usr/bin/python

class GEAException(Exception):
    """Base class for all the GEA exceptions.
    """
    pass

class RemedyException(GEAException):
    pass
    
class PlotException(GEAException):
    pass
    
class DataHandlerException(GEAException):
    pass

class DataExportException(GEAException):
    """Raised by the long-term data export path (csv export / export jobs)."""
    pass

class RequestException(GEAException):
    pass

class NotImplemented(GEAException):
    pass

class RunTimeException(GEAException):
    pass
    
class SiteException(GEAException):
    """To be used when a site-specific page is requested on at the wrong site.
    """
    pass
