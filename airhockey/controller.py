class IllegalStateSwitchException(Exception):
    pass


class RunHandlerException(Exception):
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
    def __init__(self, initial_state, terminal_state):
        self._state = initial_state
        self._terminal_state = terminal_state
        self._handlers = {}

    def get_state(self):
        return self._state

    def register_handler(self, state, handler, next_states=None):
        if state not in self._handlers:
            self._handlers[state] = []

        self._handlers[state].append(HandlerWrapper(handler, next_states))

    def run(self):
        while True:
            next_state = None
            handlers = self._handlers.get(self._state)
            if handlers is None:
                raise Exception(
                    "No handlers registered for the '{state}' state".format(
                        state=self._state))
            for handler in handlers:
                returned_state = handler()
                if next_state is not None and returned_state is not None:
                    raise RunHandlerException(
                        "Trying to change the state of controller by multiple "
                        "handlers")
                next_state = returned_state

            if self._state == self._terminal_state:
                break

            if next_state is not None:
                self._state = next_state
