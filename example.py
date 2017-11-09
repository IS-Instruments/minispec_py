#!/usr/bin/python
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

import matplotlib.pyplot as plt
from minispec import minispec, findDevices

mspec = minispec()

spectrometers = findDevices(find_first=True)

print("Found {} spectrometer(s).".format(len(spectrometers)))

if len(spectrometers) > 0:
    address, iface, serial = spectrometers.pop()

    print("Connecting to {}, via {}".format(address, iface.decode()))

    mspec.open(address[0])
    mspec.getCalibration()

    print("Exposure set to {} ms.".format(mspec.setExposure(10)))

    wavelengths = mspec.getWavelengths()
    spectrum = mspec.getSpectrum()

    print("Got spectrum")

    plt.plot(wavelengths, spectrum)
    plt.title('Spectrum')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Counts')
    plt.show()

    mspec.release()