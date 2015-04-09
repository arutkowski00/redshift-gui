import re
import os
import time
import signal
from subprocess import Popen, DEVNULL, PIPE


class RedshiftHelper:
    _brightness = (1, 0.9)
    _temp = (6500, 3500)
    _location = (52.2, -30)
    _process = None
    _lastreload = None

    def __init__(self):
        self._name = str(Popen("redshift -V", shell=True, stdout=PIPE).stdout.read(), 'ascii')

    def getinfo(self):
        if not self.isavailable():
            return None
        params = self._genparams()
        lines = Popen('redshift -p ' + params, shell=True, stdout=PIPE).stdout.readlines()
        info = []
        if len(lines) < 3:
            return None
        for line in lines[-3:]:
            info.append(str(line, 'utf-8').split(': ')[1].strip())
        return tuple(info)

    def getname(self):
        if self.isavailable():
            return self._name

    def getver(self):
        if self.isavailable():
            return re.search(r'((?:\d+\.)?(?:\d+\.)?(?:\*|\d+))', self._name).group(1)

    def isavailable(self):
        if re.match(r'^redshift (\d+\.)?(\d+\.)?(\*|\d+)$', self._name):
            return True
        return False

    def start(self):
        if self._process:
            return

        Popen('killall redshift', shell=True, stderr=DEVNULL).wait()  # kill all running 'redshift' processes
        self._load()

    def stop(self):
        if self._process:
            self._kill()
            self._reset()
            self._process = None

    @staticmethod
    def _reset():
        """Reset the screen"""
        Popen('redshift -x', shell=True)  # reset screen

    def _kill(self):
        """End the process without removing screen settings"""
        if self._process:
            os.killpg(self._process.pid, signal.SIGKILL)

    def _load(self, fading=False):
        cmd = 'redshift '
        if not fading:
            cmd += '-r '
        params = self._genparams()
        self._process = Popen(cmd + params, shell=True, preexec_fn=os.setsid, stdout=DEVNULL)

    def _reload(self):
        if self._lastreload and time.time() - self._lastreload < 0.01:
            return
        if not self._process:
            return
        self._kill()
        self._load()
        self._lastreload = time.time()

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        if self.brightness == value:
            return
        self._brightness = self._totuple(value)
        self._reload()

    @property
    def temperature(self):
        return self._temp

    @temperature.setter
    def temperature(self, value):
        if self.temperature == value:
            return
        self._temp = self._totuple(value)
        self._reload()

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if self.location == value:
            return
        self._location = self._totuple(value)
        self._reload()

    def _genparams(self):
        def tocolonstr(x):
            return '{}:{}'.format(x[0], x[1])

        params = ''
        if self.brightness:
            params += ' -b ' + tocolonstr(self.brightness)
        if self.temperature:
            params += ' -t ' + tocolonstr(self.temperature)
        if self.location:
            params += ' -l ' + tocolonstr(self.location)
        return params.strip()

    @staticmethod
    def _totuple(x):
        if isinstance(x, tuple):
            return x
        if isinstance(x, list):
            return tuple(x)
        x = float(x)
        return x, x
