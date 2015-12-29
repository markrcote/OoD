import inspect
import types

from django.utils import timezone


class State(object):
    # Override 'name' to include in a StateMachine's state_map.
    name = None
    # Override timeout with a value in seconds to have on_timeout() called
    # periodically by StateMachine.  A value of None means on_timeout() will
    # never be called.  Note that the value in the UPDATE_STATE_PERIOD_SECONDS
    # is the lower bound.
    # TODO: A default timeout is probably a good thing here; see if there's
    # any reason not to have it.
    timeout = None

    def __init__(self, machine):
        self.machine = machine

    def on_timeout(self):
        """Handle state timeout, generally polling for conditions.

        Returns True if state has changed and on_timeout() should be called
        immediately again; otherwise returns False.

        Defaults to doing nothing; override to check timeouts and such.
        """
        return False


class StateMachine(object):
    module = None
    controller_class = None
    unknown_state_name = None
    start_state_name = None
    stop_state_name = None

    def __init__(self, ood_instance):
        self.ood_instance = ood_instance
        self.controller = self.controller_class(self.ood_instance)
        self.state_map = {member.name: member for name, member
                          in inspect.getmembers(self.module)
                          if isinstance(member, types.TypeType)
                          and issubclass(member, State)
                          and member.name is not None}
        if self.ood_instance.state is None:
            self.go_to_state(self.unknown_state_name)

    def go_to_state(self, state_name):
        self.ood_instance.state = state_name
        self.ood_instance.last_state_update = timezone.now()
        self.ood_instance.save()

    def update(self):
        state = self.current_state()
        if state.timeout is None:
            return

        now = timezone.now()
        elapsed_seconds = (now - self.ood_instance.last_state_update).seconds
        if elapsed_seconds >= state.timeout:
            self._update_state()

    def current_state(self):
        return self.state_map[self.ood_instance.state](self)

    def _update_state(self):
        self.current_state().on_timeout()
        self.ood_instance.last_state_update = timezone.now()
        self.ood_instance.save()
