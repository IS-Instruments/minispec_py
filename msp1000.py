import socket
import ssl
import struct
import time
import numpy as np

def findDevices(find_first=False, sock_timeout=1, saerch_timeout=3):
        multicast_port  = 12345
        multicast_group = "0.0.0.0"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
        sock.bind(("", multicast_port ))
        sock.settimeout(1.5)

        t = time.time()

        spectrometers = set()

        while (time.time() - t) < saerch_timeout:
            data, address = sock.recvfrom(33)

            if data.find(b'msp1000') == 0:
                iface, serial = data.split(b',')[:2]
                spectrometers.add((address, iface[7:], serial))

                if find_first == True:
                    break
        
        sock.close()
        
        return spectrometers

class msp1000:
    
    def __init__(self, hostname = None, port = None):
        self.dark = None

    def open(self, hostname, port=8000):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            self.ssl_sock = ssl.wrap_socket(sock)
            self.ssl_sock.connect((hostname, port))
        except socket.error as msg:
            print("Error: {}.".format(msg))
            sock.close()

    def release(self):
        self.ssl_sock.close()
    
    def setExposure(self, exposure):
        self._sendMessage('set_exposure{}\r\n'.format(exposure).encode())
        return self.getExposure()

    def getExposure(self):
        self._sendMessage(b'get_exposure\r\n')
        msg = self._receiveMessage(b'exposure:')
        return int(msg[9:])

    def getRawSpectrum(self):
        self._sendMessage(b'take_spectrum\r\n')
        self._receiveMessage(b'spectrum_complete')

        self._sendMessage(b'get_spectrum\r\n')
        buffer = self._receiveMessage(b'spectrum:', 7389+9)
        
        return np.frombuffer(bytes(buffer[9:]), dtype='uint16', count=3694)

    def getSpectrum(self):
        spectrum_raw = self.getRawSpectrum()
        spectrum = spectrum_raw[32:3680].astype('float32')

        ccd_offset = spectrum_raw[17:30]

        spectrum -= ccd_offset.mean()

        if self.dark is not None:
            spectrum -= self.dark

        return spectrum

    def setDark(self, spectrum):
        self.dark = spectrum
  
    def clearDark(self):
        self.dark = None

    def setCalibration(self, c1, c2, c3, c4):

        float(c1)
        float(c2)
        float(c3)
        float(c4)

        msg = 'set_cal{},{},{},{}\r\n'.format(c1, c2, c3, c4)
        self._sendMessage(msg.encode())
        return self.getCalibration()

    def getCalibration(self):
        self._sendMessage(b'get_calibration\r\n')
        msg = self._receiveMessage(b'calibration:').decode()[12:].split(',')
        
        self.cal = np.array(msg, dtype='float32')[:4]

        return self.cal

    def pxToWavelength(self, px):
        out = 0
        for i, c in enumerate(self.cal[::-1]):
            out += c * (px**i)
        return out

    def getWavelengths(self):
        out = [self.pxToWavelength(x) for x in np.arange(3648, dtype='float32')]
        
        return np.array(out)

    def setWifi(self,ssid, key):
        pass

    def _sendMessage(self, msg):
        self.ssl_sock.send(msg)

    def _receiveMessage(self, magic=None, strlen=1024):
        
        msg = self.ssl_sock.recv(strlen)

        if magic is not None:
            while magic not in msg:
                msg = self.ssl_sock.recv(strlen)

        return msg
