import re
import os
import signal
from subprocess import Popen, PIPE
from threading import Thread, Event
from enum import Enum


class RedshiftHelper:
    _brightness = (1, 0.5)
    _temp = (6500, 3500)
    _location = (52.2, 15.5)

    def __init__(self):
        self._name = str(Popen("redshift -V", shell=True, stdout=PIPE).stdout.read(), 'ascii')
        self._stopflag = Event()

    def getinfo(self):
        if not self.isavailable():
            return None
        params = ''
        if self.brightness:
            params += ' -b ' + _tocolonstr(self.brightness)
        if self.temperature:
            params += ' -t ' + _tocolonstr(self.temperature)
        if self.location:
            params += ' -l ' + _tocolonstr(self.location)
        lines = Popen('redshift -p' + params, shell=True, stdout=PIPE).stdout.readlines()
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
        RedshiftThread(self._stopflag, self.temperature, self.brightness, self.location).start()

    def stop(self):
        self._stopflag.set()

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = self._totuple(value)

    @property
    def temperature(self):
        return self._temp

    @temperature.setter
    def temperature(self, value):
        self._temp = self._totuple(value)

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = self._totuple(value)

    @staticmethod
    def _totuple(x):
        if isinstance(x, tuple):
            return x
        if isinstance(x, list):
            return tuple(x)
        x = int(x)
        return x, x


class EndSignal:
    KEEP = 9  # SIGKILL
    FADE = 15  # SIGTERM
    SOLID = 9


class RedshiftThread(Thread):
    def __init__(self, event, temperature, brightness, location, endsig=EndSignal.KEEP):
        Thread.__init__(self)
        self.stopped = event
        """@type: Event"""
        self.params = ""
        if temperature:
            self.params += ' -t ' + _tocolonstr(temperature)
        if brightness:
            self.params += ' -b ' + _tocolonstr(brightness)
        if location:
            self.params += ' -l ' + _tocolonstr(location)
        self.endsig = endsig

    def run(self):
        prog = Popen('redshift ' + self.params, shell=True, preexec_fn=os.setsid)
        self.stopped.wait()

        os.killpg(prog.pid, self.endsig)
        if self.endsig == EndSignal.SOLID:
            Popen('redshift -x', shell=True)


def _tocolonstr(x):
    return '{}:{}'.format(x[0], x[1])
