
class IllegalStateSwitchException(Exception):
    pass


class RunHandlerException(Exception):
    pass


class ControllerState(object):
    def switch(self, state):
        self.__class__ = state

    def run(self):
        pass


class IdleControllerState(ControllerState):
    pass


class CalibrateControllerState(ControllerState):
    pass


class DetectRobotControllerState(ControllerState):
    pass


class HandlerWrapper(object):
    def __init__(self, handler, next_states):
        if next_states is None:
            next_states = {}
        self.handler = handler
        self.next_states = next_states

    def __call__(self, *args, **kwargs):
        return self.next_states.get(self.handler(*args, **kwargs))


class Controller(object):
    def __init__(self):
        self._state = IdleControllerState()
        self._handlers = {}

    def get_state(self):
        return self._state

    def start(self):
        if self._state.__class__ != IdleControllerState:
            raise IllegalStateSwitchException()

        self._state.switch(CalibrateControllerState)

    def register_handler(self, cls, handler, next_states=None):
        if cls not in self._handlers:
            self._handlers[cls] = []

        self._handlers[cls].append(HandlerWrapper(handler, next_states))

    def run(self):
        state = None
        for handler in self._handlers.get(self._state.__class__):
            new_state = handler()
            if state is not None and new_state is not None:
                raise RunHandlerException("Trying to change the state of controller by multiple handlers")
            state = new_state

        if state is not None:
            self._state.switch(state)
