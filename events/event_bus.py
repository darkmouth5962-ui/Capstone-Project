# Event Bus implementation

from typing import Callable, List, Dict
from collections import defaultdict
import json

class EventBus:
    # pub/sub event bus for CQRS+EDA
    
    def __init__(self):
        # dictionary mapping event types to list of subscriber callbacks
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # store event history for debugging
        self._event_log: List[Dict] = []
    
    def publish(self, event) -> None:
        # publish an event to all subscribers

        event_dict = event.to_dict()
        
        # log the event
        self._event_log.append(event_dict)
        print(f"EVENT PUBLISHED: {event.event_type}")
        
        # notify all subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event_dict)
                except Exception as e:
                    print(f"Error in subscriber for {event.event_type}: {e}")
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        # subscribe to a specific event type

        self._subscribers[event_type].append(callback)
        print(f"Subscribed to: {event_type}")
    
    def get_event_log(self) -> List[Dict]:
        # return all published events (for debugging)
        return self._event_log
    
    def clear_log(self) -> None:
        # clear event log
        self._event_log.clear()


# global singleton event bus
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    # get the global event bus instance
    return _event_bus