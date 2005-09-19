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
    def __init__(self, prefix="evt_", suffix="", default="eventPerformed", silent=True):
        """ EventListener constructor.
        """
        evt.EventListener.__init__(self, prefix, suffix, "happyboomEventPerformed", silent)
        self.event_hb_default = default
        
    def getEventName(self, feature, event):
        return "%s_%s" %(feature, event)
        
    def happyboomEventPerformed(self, event):
        if issubclass(event.__class__, Event):
            # Try to call event-specific handle method
            fctname = self.event_pattern %(self.getEventName(event.type, event.event))
            if hasattr(self, fctname):
                function = getattr(self, fctname)
                if callable(function):
                    function(*event.content)
                    return

        # Try to call default handle method
        if hasattr(self, self.event_hb_default):
            function = getattr(self, self.event_hb_default)
            if callable(function):
                function(event)
                return
        # No handle method found, raise error ?
        if not self.event_silent:
            raise evt.UnhandledEventError("%s has no method to handle %s" %(self, event))

class EventLauncher(evt.EventLauncher):
    """ Happyboom generic class for launching events.
    """
    def __init__(self):
        """ EventLauncher constructor. """
        evt.EventLauncher.__init__(self)
        
    def launchEvent(self, feature, event, *args):
        """ Launches a new event to the listeners.
        """
        e = Event(feature, event, self, args)
        self.event_manager.dispatchEvent(e)

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
    
    def getFeature(self): return feature
    feature = property(getFeature)
