<h1 id="minispec">minispec</h1>


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

<h2 id="minispec.find_devices">find_devices</h2>

```python
find_devices(find_first=False, sock_timeout=3, search_timeout=3)
```
Finds spectrometers broadcasting on the local network

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

<h2 id="minispec.Minispec">Minispec</h2>

```python
Minispec(self, hostname=None, port=8000)
```
Interface class for the IS-Instruments MSP1000 miniature spectrometer

<h3 id="minispec.Minispec.open">open</h3>

```python
Minispec.open(self, hostname, port=8000)
```
Opens a connection to a spectrometer

        Args:
            hostname: IP address or hostname of spectrometer
            port (int): Factory default is 8000

        Returns:
            None

<h3 id="minispec.Minispec.release">release</h3>

```python
Minispec.release(self)
```
Close the connection to the spectrometer

        Returns:
            None

<h3 id="minispec.Minispec.exposure">exposure</h3>

Get the exposure time of the spectromter

        Returns:
            The exposure time reported by the spectrometer.

<h3 id="minispec.Minispec.raw_spectrum">raw_spectrum</h3>

```python
Minispec.raw_spectrum(self)
```
Acquire a raw spectrum

        Performs an exposure and retrieves the raw spectrum. Most of the time
        you should just use minispec.spectrum. This data also includes
        light shielded and other non-data pixels. See the TCD1304 datasheet
        for details.

        Returns:
            raw_spectrum: the raw 16-bit counts from the CCD (3694 pixels).

<h3 id="minispec.Minispec.spectrum">spectrum</h3>

```python
Minispec.spectrum(self)
```
Acquire a spectrum

        Performs an exposure and retrieves the spectrum. The voltage offset from the
        CCD is automatically subtracted. If a dark spectrum has been set, this will
        also be subtracted.

        Returns:
            spectrum: numpy array of 3648 float32 values representing the acquired spectrum.

<h3 id="minispec.Minispec.dark">dark</h3>

Get the dark spectrum

        Returns:
            The current dark spectrum

<h3 id="minispec.Minispec.reset_dark">reset_dark</h3>

```python
Minispec.reset_dark(self)
```
Reset the dark spectrum (to nothing)

        Returns:
            None

<h3 id="minispec.Minispec.update_calibration">update_calibration</h3>

```python
Minispec.update_calibration(self)
```
Update wavelength calibration coeffients.

        Get the new calibration coefficients from the spectrometer.

        Returns:
            None

<h3 id="minispec.Minispec.calibration">calibration</h3>

Get wavelength calibration coeffients.

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

<h3 id="minispec.Minispec.px_to_wavelength">px_to_wavelength</h3>

```python
Minispec.px_to_wavelength(self, idx)
```
Convert a pixel index to a wavelength

        Make sure you call minispec.getCalibration at some point before calling this
        function.

        Args:
            iox (int): The index of a pixel on the CCD.

        Returns:
            The calculated wavelength for this pixel in nm.


<h3 id="minispec.Minispec.wavelengths">wavelengths</h3>

Get an array of wavelengths in nanometres

        Useful for plotting and for storing data.

        Returns:
            A numpy array containing wavelength values for each pixel on the
            detector (3648 values).


<h3 id="minispec.Minispec.set_wifi">set_wifi</h3>

```python
Minispec.set_wifi(self, ssid, key)
```
Set the WiFi details

        Update the WiFI credentials on the spectrometer so it can connect to your
        local hotspot. Assumes WPA(2).

        Args:
            ssid: The hotspot SSID.
            key: The hotspot password.

        Retuns:
            None

