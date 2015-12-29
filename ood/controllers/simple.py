import socket

from ood.minecraft import Client
from ood.models import SimpleServerState


class SimpleServerController(object):

    def __init__(self, ood_instance):
        self.state = SimpleServerState.objects.get(ood=ood_instance)
        self.mcc = Client(ood_instance)

    def start(self):
        self.mcc.reset_player_info()
        return self._send_cmd('start')

    def stop(self):
        return self._send_cmd('stop')

    def running(self):
        response = self._send_cmd('running').lower()
        return response == 'true'

    def _send_cmd(self, cmd):
        buf = ''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.state.ip_address, self.state.port))
        s.sendall('%s\n' % cmd)

        while '\n' not in buf:
            buf += s.recv(1024)

        response, nl, buf = buf.partition('\n')
        s.close()
        return response
