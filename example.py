import matplotlib.pyplot as plt
from msp1000 import msp1000, findDevices

mspec = msp1000()

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