"""
Module to use event-system very easily.
@author: Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 1.0
"""
import generic_event as evt

class EventListener(evt.EventListener):
    """ Happyboom generic class for listening to events.
    """
    def __init__(self, prefix="evt", suffix="", default="eventPerformed", silent=False):
        """ EventListener constructor.
        """
        evt.EventListener.__init__(self, prefix, suffix, __eventPerformed, silent)
        self.hb_default = default
        
    def getEventName(self, feature, event):
        return "%s_%s" %(feature, event)
        
    def __eventPerformed(self, event):
        if issubclass(event, Event):
            # Try to call event-specific handle method
            fctname = self.pattern %(self.getEventName(event.type, event.event))
            if hasattr(self, fctname):
                function = getattr(self, fctname)
                if callable(function):
                    function(event)
                    return
        # Try to call default handle method
        if hasattr(self, self.hb_default):
            function = getattr(self, self.hb_default)
            if callable(function):
                function(event)
                return
        # No handle method found, raise error ?
        if not obj.silent:
            raise UnhandledEventError("%s has no method to handle %s" %(obj, event))

class EventLauncher(evt.EventLauncher):
    """ Happyboom generic class for launching events.
    """
    def __init__(self):
        """ EventLauncher constructor. """
        evt.EventLauncher.__init__(self)
        
    def launchEvent(self, feature, event, *args):
        """ Launches a new event to the listeners.
        """
        self.manager.dispatchEvent(Event(feature, event, self, args))

class Event(evt.Event):
    """ Represents an happyboom event entity.
    """
    def __init__(self, feature, event, source, content):
        """ Event constructor.
        """
        evt.Event.__init__(self, feature, source, content)
        self.event = event
    
    def __str__(self):
        """ Converts object itself to string.
        @return: Object converted string.
        @rtype: C{str}
        """
        return "<event.Event feature=%s event=%s source=%s content=%s>" %(self.type, self.event, self.source, self.content)
    