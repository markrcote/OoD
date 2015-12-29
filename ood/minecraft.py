import errno
import logging
import re
import socket
from datetime import timedelta

from django.utils import timezone

from ood.contrib.MCRcon.mcrcon import MCRcon
from ood.models import MineCraftServerSettings, ServerPlayerState
from ood.settings import MAX_MINUTES_NO_PLAYERS

NUM_PLAYERS_RE = re.compile('There are (\d+)/\d+ players')
MAX_TIMEDELTA_NO_PLAYERS = timedelta(minutes=MAX_MINUTES_NO_PLAYERS)


class Client(object):

    """MineCraft controller.
    This instance is meant to be short lived; therefore, the OoD instance
    state is loaded in the constructor and not refreshed in any function
    (except when the function updates the state).
    """

    def __init__(self, ood_instance):
        self.settings, _ = MineCraftServerSettings.objects.get_or_create(
            ood=ood_instance)
        self.player_state, _ = ServerPlayerState.objects.get_or_create(
            ood=ood_instance)

    def update_host(self, ip_address, port, rcon_port, rcon_password):
        self.settings.ip_address = ip_address
        self.settings.port = port
        self.settings.rcon_port = rcon_port
        self.settings.rcon_password = rcon_password
        self.settings.save()

    def port_open(self):
        if not self._host_configured():
            return False

        try:
            logging.info('trying to connect on %s:%s' % (self.settings.ip_address, self.settings.port))
            s = socket.create_connection((self.settings.ip_address,
                                          self.settings.port),
                                         timeout=5)
        except socket.error as e:
            if e.errno != errno.ECONNREFUSED:
                logging.warning('Unexpected socket error when checking '
                                'Minecraft port: %s' % e)
            return False
        except socket.timeout:
            return False

        s.close()
        return True

    def reset_player_info(self):
        if not self._host_configured():
            return

        self.player_state.last_time_checked_players = timezone.now()
        self.player_state.last_time_seen_player = \
            self.player_state.last_time_checked_players
        self.player_state.num_players = 0
        self.player_state.save()

    def check_for_players(self):
        if not self._host_configured():
            return

        self.player_state.last_time_checked_players = timezone.now()
        self.player_state.save()
        rcon = MCRcon()

        try:
            rcon.connect(self.settings.ip_address, self.settings.rcon_port)
            rcon.login(self.settings.rcon_password)
            out = rcon.command('/list')
        except socket.error as e:
            # TODO: We should log errors if we get connection-refused
            # errors for too long.
            if e.errno != errno.ECONNREFUSED:
                logging.warning('Unexpected socket error when accessing '
                                'Minecraft RCON port: %s' % e)
            return 0

        m = NUM_PLAYERS_RE.match(out)

        if not m:
            logging.error('Invalid output from /list: %s' % out)
            return 0

        self.player_state.num_players = int(m.group(1))
        if self.player_state.num_players:
            self.player_state.last_time_seen_player = \
                self.player_state.last_time_checked_players
        self.player_state.save()

    def timeout_no_players(self):
        if not self._host_configured():
            return False

        return (timezone.now() > (self.player_state.last_time_seen_player +
                                  MAX_TIMEDELTA_NO_PLAYERS))

    def _host_configured(self):
        return self.settings.ip_address and self.settings.port
