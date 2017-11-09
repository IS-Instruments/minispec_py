# minispec_py
This repository provides an example python interface to the IS Instruments MSP1000 miniature spectrometer - we call it the minispec for short. There are minimal dependencies - spectra are returned as Numpy arrays and the connection to the spectrometer is made via SSL. This code was written to target Python 3, but should work on Python 2.7 as well.

A standalone C++ interface will be released in the near future.

# About the spectrometer
The MSP1000 is a scientific-grade VIS/NIR spectrometer with a typical spectral range of 400-850nm and a (fibre-dependent) resolution of less than 1 nm. The spectrometer connects via your local network by one of four methods:

- A direct ethernet connection to your computer
- A direct ethernet connection to your router
- Connected to your local WiFi network
- Connected to your computer via the spectrometer's local WiFi hotspot

We believe this flexibility is unique for a device at this price point and allows you to do some nifty things like leave the spectrometer in the darkroom while you work in the comfort of your office.

Because the spectrometer is effectively operating as a web server, it can be accessed by multiple people. To keep things simple, access is 'greedy' - the first person to connect to the spectrometer is in control. Other users can connect, but are only able to read parameters.

The interface to the spectrometer is via a web socket. This means that you can connect using pretty much any language you like.

# About this library

We designed our minispec to be easy to use and we provide a free GUI application for live spectral plotting and analysis. However, we also understand that you'd probably like to integrate the spectrometer in your own system.

This python library is designed as a basic, but functional, interface to the spectrometer. It is expected that you will write additional code to handle visualisation, saving and so on. As this functionality is provided by standard Python packages like Numpy and Matplotlib there's no need for us to reinvent the wheel! The library provides the following capabilties:

- Locate spectrometers on the local network
- Connect/disconnect from the spectrometer
- Query if the spectromter is in 'read only' mode
- Get and set exposure value (ms)
- Acquire a spectrum with CCD bias removed
- Acquire a raw spectrum (the raw readout from the ADC)
- Store and automatically subtract a dark frame
- Get and set calibration coefficients
- Get the wavelengths corresponding to pixel numbers

The ability to update the WiFi settings will be added soon.

An example python script is provided which will locate a spectrometer on the network, connect to it, set the exposure time, capture a spectrum and plot it.

# Function reference

## Locating devices

The `findDevices` function can be used to locate any connected spectrometers on the local network. Connected minispecs broadcast via UDP on port `12345`. This returns a Python set containing all the spectrometers which were found before timeout (3 seconds by default). The minispec broadcast message frequency is 1Hz, so this should catch most connected devices.

The set contains tuples of the form: `((hostname, port), interface, serial)`.

The serial number is a 64-bit integer unique to each PCB in the spectrometer.

## Connecting

Once you've found your spectrometer, you can connect to it:

    address, iface, serial = spectrometers.pop()
    
    mspec = minispec()
    mspec.open(address[0])

Here we `pop` the first spectrometer on the list.

## Get the calibration coefficients

To do anything useful with our spectra, we need to know what wavelengths we're measuring. This is unique to each spectrometer which is calibrated on leaving our workshop.

    cal = mspec.getCalibration()
    print(cal)
    
This should output something like:

    [  1.21419996e-12  -8.04026968e-06   1.61927998e-01   3.99615997e+02]

This represents a 3rd order polynomial to convert pixel number to nanometers. The last coefficient is the starting wavelength, and the calibration (for pixel number `i`) is performed as:

    wavelength[i] = cal[4] + cal[3]*i**1 + cal[2]*i**2 + cal[1]*i**3

We provide this as a function for you:

    wavelengths = mspec.getWavelengths()

Which returns a numpy array containing the wavelength conversion for each pixel on the detector.

If you need to update the calibration coefficients, you can do this by using the `setCalibration()` function which is used as follows:

    new_cal = mspec.setCalibration(c1, c2, c3, c4)

Where `c1-c4` are the new calibration coefficients as described above. After sending the values, this function queries the spectrometer for the current (i.e. new) calibration so you can check that it was applied successfully.

## Get a spectrum and changing exposure

Finally, we get to the good stuff!

Simply call:

    spectrum = mspec.getSpectrum()

To acquire and retrieve a spectrum. The default exposure time is 2 ms, but it may be different if you're in read-only mode and someone else has modified it. You can check with:

    print("Exposure set to {} ms.".format(mspec.getExposure()))

If you find that you need a longer exposure time, then you can call:

    new_exposure = mspec.setExposure(10)

The provided value (in this case 10) is in ms. Just like with `setCalibration`, this function will query the spectrometer to see what value it actually set (useful for troubleshooting).

## Dark subtraction

It's often useful to subtract dark counts from the spectrometer, which will change due to temperature variation or other noise sources.

First make sure your exposure time is correct, as the dark spectrum is only valid for that exposure setting. Then, capture a spectrum with your equipment set up in a 'dark' mode (e.g. cover the fibre end).

    dark_spectrum = mspec.getSpectrum()
    mspec.setDark(dark_spectrum)

Then call `setDark` to store this new spectrum as your dark frame. It will be automatically subtracted from new data (for convenience) until you call `clearDark`.

## To sum up:

Here's a brief code example that finds a spectrometer, connects to it and plots the spectrum.

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

## What next?

Some functionality which you'll find in our GUI software are things like:

- Spectral averaging and smoothing
- Peak fitting

This is fairly simple to achieve in Python, for example to perform a 10-spectrum average:

    num_averages = 10
    spectrum = np.zeros(3648)
    
    for i in range(num_averages):
        spectrum += mspec.getSpectrum()
    
    spectrum_average = spectrum.mean()

For further processing we direct you to the excellent and mature Scipy library which contains a huge number of signal processing functions, for example [smoothing](http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html).

## License

Copyright (c) 2017 IS-Instruments Ltd

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

Happy measurements!
