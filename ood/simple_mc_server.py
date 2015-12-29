import asynchat
import asyncore
import datetime
import os
import socket
import subprocess


minecraft_proc = None


class Handler(asynchat.async_chat):

    def __init__(self, minecraft_path, minecraft_jar, sock):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator('\n')
        self.minecraft_path = minecraft_path
        self.minecraft_jar = minecraft_jar
        self.ibuffer = []
        self.out = file(os.path.join(self.minecraft_path, 'ood_local.log'),
                        'a')
        self.log('OoD simple server starting.')

    def log(self, msg):
        self.out.write('[%s] OOD_SIMPLE %s\n' % (datetime.datetime.now(), msg))

    def start_mc(self):
        global minecraft_proc

        if minecraft_proc:
            if self._check_running():
                return 'already running'

        minecraft_proc = subprocess.Popen(
            ['java', '-Xmx1024M', '-Xms1024M', '-jar', self.minecraft_jar,
             'nogui'],
            stdout=self.out,
            stderr=subprocess.STDOUT,
            cwd=self.minecraft_path)

        return 'started'

    def stop_mc(self):
        global minecraft_proc

        if not self._check_running():
            self.log('Minecraft server is not running!')
            return 'not running'

        minecraft_proc.terminate()
        return 'stopping'

    def mc_running(self):
        return self._check_running()

    def collect_incoming_data(self, data):
        self.ibuffer.append(data)

    def found_terminator(self):
        cmd = ''.join(self.ibuffer).strip()
        self.ibuffer = []
        response = None

        if cmd == 'start':
            response = self.start_mc()
        elif cmd == 'stop':
            response = self.stop_mc()
        elif cmd == 'running':
            response = str(self.mc_running())
        else:
            response = 'Unknown command "%s".' % cmd

        if response is not None:
            self.push('%s\n' % response)

    def _check_running(self):
        global minecraft_proc

        if not minecraft_proc:
            return False

        if not minecraft_proc.poll():
            return True

        self.log('MineCraft server exited with return code %d.' %
                 minecraft_proc.returncode)
        minecraft_proc = None
        return False


class Server(asyncore.dispatcher):

    def __init__(self, minecraft_path, minecraft_jar, port):
        asyncore.dispatcher.__init__(self)
        self.minecraft_path = minecraft_path
        self.minecraft_jar = minecraft_jar
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('127.0.0.1', port))
        self.listen(0)

    def handle_accept(self):
        client_info = self.accept()
        Handler(self.minecraft_path, self.minecraft_jar, client_info[0])


if __name__ == '__main__':
    import errno
    import sys

    if len(sys.argv) < 3:
        print 'Usage: %s <path to minecraft> <port>' % sys.argv[0]
        sys.exit(errno.EINVAL)

    path = sys.argv[1]

    try:
        port = int(sys.argv[2])
    except (TypeError, ValueError):
        print '<port> must be an integer.'
        sys.exit(errno.EINVAL)

    if len(sys.argv) > 3:
        jar_file = sys.argv[3]
    else:
        jar_file = 'minecraft_server.jar'

    lcs = Server(path, jar_file, port)

    asyncore.loop()
