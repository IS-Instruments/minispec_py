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

We designed our minispec to be incredibly easy to use and we provide a free GUI application for live spectral plotting and analysis. However, we also understand that you'd probably like to integrate the spectrometer in your own system.

This python library is designed as a basic, but functional, interface to the spectrometer. You can capture a spectrum in just three lines of code, including the import!

```python
    from minispec import minispec

    mspec = minispec('192.168.1.10')
    spectrum = mspec.spectrum()
```

It is expected that you will write additional code to handle visualisation, saving and so on. As this functionality is provided by standard Python packages like Numpy and Matplotlib there's no need for us to reinvent the wheel! The library provides the following capabilties:

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

# Getting Started

## Discovering spectrometers

Connected minispecs continually broadcast a message via UDP on port `12345`. This lets other systems discover the IP address of any spectrometers available.

The `minispec.findDevices()` function can be used to locate any connected spectrometers on the local network. This returns a Python set containing all the spectrometers which were found before timeout (3 seconds by default). The minispec broadcast message frequency is 1Hz, so this should catch most connected devices.

```python
    spectrometers = minispec.findDevices(find_first=True)
```

The set contains tuples of the form: `((hostname, port), interface, serial)`.

`hostname` is the IP address of the spectrometer. `interface` tells you if your spectrometer is using WiFi (`wlan0`) or ethernet (`eth0`). The `port` defaults to `8000`. The `serial` number is a 64-bit integer unique to each PCB in the spectrometer.

## Connecting

Once you've found your spectrometer, you can connect to it. Here we `pop` the first spectrometer on the list:

```python
    (hostname, port), iface, serial = spectrometers.pop()
```

Then make a new `minispec` object and pass in the `hostname`:

```python
    mspec = minispec(hostname)
```

If you just want to create an object and open the connection later, you can call:

```python
    mspec = minispec()
    mspec.open(hostname)
```

Note you don't need to supply the ports here, it will be set by default to 8000. If you've changed this, then you can use:

```python
    mspec = minispec(hostname, port)
```

## Get the calibration coefficients

To do anything useful with our spectra, we need to know what wavelengths we're measuring. This is unique to each spectrometer which is calibrated on leaving our workshop. The calibration coefficients are implicitly requested when you call `open()`.

```python
    print(mspec.calibration)
```

This should output something like:

```python
    [  1.21419996e-12  -8.04026968e-06   1.61927998e-01   3.99615997e+02]
```

This represents a 3rd order polynomial to convert pixel number to nanometers. The last coefficient is the starting wavelength (e.g. 399 nm here), and the calibration for pixel number `i` is performed as:

```python
    wavelength[i] = cal[4] + cal[3]*i**1 + cal[2]*i**2 + cal[1]*i**3
```

We provide this for you:

```python
    print(mspec.wavelengths)
```

`mspec.wavelengths` returns a numpy array containing the wavelength conversion for each pixel on the detector.

If you need to update the calibration coefficients, you can do this by writing to the calibration attribute:

```python
    mspec.calibration = (c1, c2, c3, c4)
```

Where `c1-c4` are the new calibration coefficients as described above. After sending the values, this function queries the spectrometer for the current (i.e. new) calibration so you can check that it was applied successfully.

## Get a spectrum and changing exposure

Finally, we get to the good stuff!

Simply call:

```python
    spectrum = mspec.spectrum()
```

To acquire and retrieve a spectrum. The default exposure time is 2 ms, but it may be different if you're in read-only mode and someone else has modified it. You can check with:

```python
    print("Exposure set to {} ms.".format(mspec.exposure))
```

If you find that you need a longer exposure time, then you can call:

```python
    mspec.exposure = 10
```

The provided value (in this case 10) is in ms. Just like when you update the calibration, updating the exposure will trigger a request to read back what value was acutally set, so you can check with e.g.:

```python
    mspec.exposure = 100
    assert(mspec.exposure == 100)
```

## Dark subtraction

It's often useful to subtract dark counts from the spectrometer, which will change due to temperature variation or other noise sources.

First make sure your exposure time is correct, as the dark spectrum is only valid for that exposure setting. Then, capture a spectrum with your equipment set up in a 'dark' mode (e.g. cover the fibre end).

```python
    dark_spectrum = mspec.spectrum()
    mspec.dark = dark_spectrum
```

Simply write to the `.dark` attribute to store this new spectrum as your dark frame. It will be automatically subtracted from new data (for convenience). If you decide you want to stop subtracting darks, you can do:

```python
    mspec.dark = None
```

## To sum up:

The `example.py` script in this repository wraps all of these things together and adds some plotting code so you can see what your spectrometer captured.

## What next?

Some functionality which you'll find in our GUI software are things like:

- Spectral averaging and smoothing
- Peak fitting

This is fairly simple to achieve in Python, for example to perform a 10-spectrum average:

```python
    num_averages = 10
    spectrum = np.zeros(3648)
    
    for i in range(num_averages):
        spectrum += mspec.getSpectrum()
    
    spectrum_average = spectrum.mean()
```

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
