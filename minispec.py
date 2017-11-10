"""
Copyright (c) 2017 IS-Instruments Ltd
Author: Josh Veitch-Michaelis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import socket
import time
import ssl
import numpy as np

def find_devices(find_first=False, sock_timeout=3, search_timeout=3):
    """Finds spectrometers broadcasting on the local network

    Args:
        find_first (bool): whether to return only the first spectrometer found
        sock_timeout (int): UDP socket timeout in seconds
        search_timeout (int): How long to look for systems in seconds

    Returns:
        A set of spectrometers with the following format:

        {(hostname,port), interface, serial}

        Where interface is typically wlan0 or eth0, depending on how your
        spectrometer is set up. Serial is a 64-bit identifier unique to
        each spectrometer.
    """
    multicast_port = 12345

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", multicast_port))
    sock.settimeout(sock_timeout)

    tstart = time.time()

    spectrometers = set()

    while (time.time() - tstart) < search_timeout:
        data, address = sock.recvfrom(33)

        if data.find(b'msp1000') == 0:
            iface, serial = data.split(b',')[:2]
            spectrometers.add((address, iface[7:], serial))

            if find_first is True:
                break

    sock.close()

    return spectrometers

class Minispec(object):
    """Interface class for the IS-Instruments MSP1000 miniature spectrometer
    """

    def __init__(self, hostname=None, port=8000):
        """Create a new spectrometer object

        Args:
            hostname: IP address or hostname of spectrometer
            port (int): Factory default is 8000

        Returns:
            None
        """
        self._dark = np.zeros(3648)
        self._calibration = np.array([0, 0, 1, 0])

        if hostname is not None:
            self.open(hostname, port)

    def open(self, hostname, port=8000):
        """Opens a connection to a spectrometer

        Args:
            hostname: IP address or hostname of spectrometer
            port (int): Factory default is 8000

        Returns:
            None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            self.ssl_sock = ssl.wrap_socket(sock)
            self.ssl_sock.connect((hostname, port))

            self.update_calibration()

        except socket.error as msg:
            print("Error: {}.".format(msg))
            sock.close()

    def release(self):
        """Close the connection to the spectrometer

        Returns:
            None
        """
        self.ssl_sock.close()

    @property
    def exposure(self):
        """Get the exposure time of the spectromter

        Returns:
            The exposure time reported by the spectrometer.
        """
        self._send_message(b'get_exposure\r\n')
        msg = self._receive_message(b'exposure:')
        return int(msg[9:])

    @exposure.setter
    def exposure(self, exposure=2):
        """Set the exposure time of the spectromter

        Args:
            exposure (int): Desired exposure time in ms

        Returns:
            The new exposure time reported by the spectrometer.
        """
        exposure = int(exposure)
        self._send_message('set_exposure{}\r\n'.format(exposure).encode())
        return

    def raw_spectrum(self):
        """Acquire a raw spectrum

        Performs an exposure and retrieves the raw spectrum. Most of the time
        you should just use minispec.spectrum. This data also includes
        light shielded and other non-data pixels. See the TCD1304 datasheet
        for details.

        Returns:
            raw_spectrum: the raw 16-bit counts from the CCD (3694 pixels).
        """
        self._send_message(b'take_spectrum\r\n')
        self._receive_message(b'spectrum_complete')

        self._send_message(b'get_spectrum\r\n')
        buffer = self._receive_message(b'spectrum:', 7389+9)

        return np.frombuffer(bytes(buffer[9:]), dtype='uint16', count=3694)

    def spectrum(self):
        """Acquire a spectrum

        Performs an exposure and retrieves the spectrum. The voltage offset from the
        CCD is automatically subtracted. If a dark spectrum has been set, this will
        also be subtracted.

        Returns:
            spectrum: numpy array of 3648 float32 values representing the acquired spectrum.
        """
        spectrum_raw = self.raw_spectrum()
        spectrum = spectrum_raw[32:3680].astype('float32')

        ccd_offset = spectrum_raw[17:30]

        spectrum -= ccd_offset.mean()

        if self._dark is not None:
            spectrum -= self._dark

        return spectrum

    @property
    def dark(self):
        """Get the dark spectrum

        Returns:
            The current dark spectrum
        """
        return self._dark

    @dark.setter
    def dark(self, spectrum):
        """Set the dark spectrum.

        This should be a 1x3648 float32 numpy array. It will be automatically subtracted
        from new spectra, to disable, call minispec.reset_dark.

        Args:
            spectrum: a dark spectrum.

        Returns:
            None
        """
        if len(spectrum) == 3648:
            self._dark = spectrum

    def reset_dark(self):
        """Reset the dark spectrum (to nothing)

        Returns:
            None
        """
        self._dark = None

    def update_calibration(self):
        """Update wavelength calibration coeffients.

        Get the new calibration coefficients from the spectrometer.

        Returns:
            None
        """
        self._send_message(b'get_calibration\r\n')
        msg = self._receive_message(b'calibration:').decode()[12:].split(',')

        self._calibration = np.array(msg, dtype='float32')[:4]


    @property
    def calibration(self):
        """Get wavelength calibration coeffients.

        The spectrum is corrected using a 3rd degree polynomial.

        c1 = x**3 coefficient
        c2 = x**2 coefficient
        c3 = x**1 coefficient
        c4 = x**0 coefficient

        That is, c4 contains the starting wavelength and the wavelengths are calculated as:

        x[i] = c4 + c3*i**1 + c2*i**2 + c1*i**3

        The units of x are nanometers.

        Returns:
            A numpy array containing the new calibration coeffients reported by the spectrometer.
        """
        return self._calibration

    @calibration.setter
    def calibration(self, coefficients):
        """Set wavelength calibration coeffients.

        The spectrum is corrected using a 3rd degree polynomial.

        c1 = x**3 coefficient
        c2 = x**2 coefficient
        c3 = x**1 coefficient
        c4 = x**0 coefficient

        That is, c4 contains the starting wavelength and the wavelengths are calculated as:

        x[i] = c4 + c3*i**1 + c2*i**2 + c1*i**3

        Args:
            c1,c2,c3,c4 (float): New calibration coefficients.

        Returns:
            A numpy array containing the new calibration coeffients reported by the spectrometer.
        """

        cal_1, cal_2, cal_3, cal_4 = coefficients

        float(cal_1)
        float(cal_2)
        float(cal_3)
        float(cal_4)

        msg = 'set_cal{},{},{},{}\r\n'.format(cal_1, cal_2, cal_3, cal_4)
        self._send_message(msg.encode())
        self.update_calibration()

    def px_to_wavelength(self, idx):
        """Convert a pixel index to a wavelength

        Make sure you call minispec.getCalibration at some point before calling this
        function.

        Args:
            iox (int): The index of a pixel on the CCD.

        Returns:
            The calculated wavelength for this pixel in nm.

        """
        out = 0
        for i, coeff in enumerate(self._calibration[::-1]):
            out += coeff * (idx**i)
        return out

    @property
    def wavelengths(self):
        """Get an array of wavelengths in nanometres

        Useful for plotting and for storing data.

        Returns:
            A numpy array containing wavelength values for each pixel on the
            detector (3648 values).

        """
        out = [self.px_to_wavelength(x) for x in np.arange(3648, dtype='float32')]

        return np.array(out)

    def set_wifi(self, ssid, key):
        """Set the WiFi details

        Update the WiFI credentials on the spectrometer so it can connect to your
        local hotspot. Assumes WPA(2).

        Args:
            ssid: The hotspot SSID.
            key: The hotspot password.

        Retuns:
            None
        """
        pass

    def _send_message(self, msg):
        """Send a message to the spectrometer

        Recommended for internal use only, abstraction around comminucation with
        the spectrometer.

        Args:
            msg: The message (byte) string to send.

        Retuns:
            None
        """
        self.ssl_sock.send(msg)

    def _receive_message(self, magic=None, strlen=1024, timeout=5):
        """Retrieve a specific to the spectrometer

        Recommended for internal use only, abstraction around comminucation with
        the spectrometer. Blocking. Will loop forever until the desired message
        is received, or until timeout.

        Iterates through returned messages from the spectrometer (delimited by
        newline) and looks for the provided magic string.

        Args:
            magic: Used to identify the returned commands. If None then the first
                   message back will be returned.
            strlen: How many characters to receive.
            timeout: Timeout length in seconds.

        Returns:
            msg: The string corresponding to the desired message.

        """
        msg = self.ssl_sock.recv(strlen)

        tstart = time.time()

        if magic is not None:
            while (magic not in msg) and (time.time()-tstart) < timeout:
                msg = self.ssl_sock.recv(strlen)

        return msg
