# FreqShow main application model/state.
# Author: Tony DiCola (tony@tonydicola.com)
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import numpy as np
from rtlsdr import *

import freqshow

CENTER_OFFSET_MHZ = 0.010
DISPLAY_OFFSET_MHZ = 0.07

class FreqShowModel(object):
        def __init__(self, width, height):
                """Create main FreqShow application model.  Must provide the width and
                height of the screen in pixels.
                """
                # Set properties that will be used by views.
                self.width = width
                self.height = height
                # Initialize auto scaling both min and max intensity (Y axis of plots).
                self.min_auto_scale = True
                self.max_auto_scale = True
                self.set_min_intensity(-3)
                self.set_max_intensity(50)
                # Initialize RTL-SDR library.
                self.sdr = RtlSdr()
                self.sdr.offset_tuning = False
                self.sdr.freq_correction = 31
                self.tune_offset_hz = 000000.0
                self.set_center_freq(99.5)
                self.set_sample_rate(2.4)
                self.set_gain(10)
                self.waterfall_speed_index = 1
                self.waterfall_speed_labels = ['SLOW', 'MED', 'FAST', 'MAX']
                self.waterfall_speed_intervals = [1.0, 1.0 / 3.0, 0.1, 1.0 / 30.0]

        def get_waterfall_speed_label(self):
                return self.waterfall_speed_labels[self.waterfall_speed_index]
        
        def get_waterfall_speed_interval(self):
                return self.waterfall_speed_intervals[self.waterfall_speed_index]
        
        def cycle_waterfall_speed(self):
                self.waterfall_speed_index = (self.waterfall_speed_index + 1) % len(self.waterfall_speed_labels)
        

        def _clear_intensity(self):
                if self.min_auto_scale:
                        self.min_intensity = None
                if self.max_auto_scale:
                        self.max_intensity = None
                self.range = None

        def find_strongest_signal(self):
                """Find the strongest peak and tune to it with a coarse + fine pass."""
                def get_smoothed_spectrum():
                        acc = None
                        frames = 4
                        for _ in range(frames):
                                samples = self.sdr.read_samples(freqshow.SDR_SAMPLE_SIZE)
                                spectrum = 20.0 * np.log10(
                                        np.abs(np.fft.fftshift(np.fft.fft(samples)))[1:-1] + 1e-12
                                )
                                if acc is None:
                                        acc = spectrum
                                else:
                                        acc += spectrum
                        spectrum = acc / frames

                        kernel = np.array([1, 2, 3, 2, 1], dtype=float)
                        kernel /= kernel.sum()
                        return np.convolve(spectrum, kernel, mode='same')

                def find_peak_offset_mhz(smoothed):
                        center = (len(smoothed) - 1) / 2.0
                        center_idx = len(smoothed) // 2
                        search = smoothed.copy()

                        ignore = 8
                        edge = 8
                        search[center_idx-ignore:center_idx+ignore] = -9999
                        search[:edge] = -9999
                        search[-edge:] = -9999

                        peak_index = int(np.argmax(search))

                        # Quadratic interpolation using peak bin and neighbors.
                        if 1 <= peak_index < len(smoothed) - 1:
                                y1 = smoothed[peak_index - 1]
                                y2 = smoothed[peak_index]
                                y3 = smoothed[peak_index + 1]
                                denom = (y1 - 2 * y2 + y3)
                                if abs(denom) > 1e-12:
                                        delta = 0.5 * (y1 - y3) / denom
                                else:
                                        delta = 0.0
                        else:
                                delta = 0.0

                        refined_index = peak_index + delta
                        bin_offset = refined_index - center
                        bin_hz = self.sdr.get_sample_rate() / float(len(smoothed))
                        freq_offset_mhz = (bin_offset * bin_hz) / 1000000.0
                        return freq_offset_mhz, peak_index, refined_index

                # Pass 1: coarse
                smoothed = get_smoothed_spectrum()
                freq_offset_mhz, peak_index, refined_index = find_peak_offset_mhz(smoothed)
                new_freq = self.get_center_freq() + freq_offset_mhz
                print(
                        f"FIND coarse peak_index={peak_index} refined_index={refined_index:.3f} "
                        f"offset_mhz={freq_offset_mhz:.6f} new_freq={new_freq:.6f}",
                        flush=True
                )
                self.set_center_freq(new_freq)

                # Pass 2: fine
                smoothed = get_smoothed_spectrum()
                freq_offset_mhz, peak_index, refined_index = find_peak_offset_mhz(smoothed)
                new_freq = self.get_center_freq() + freq_offset_mhz
                print(
                        f"FIND fine peak_index={peak_index} refined_index={refined_index:.3f} "
                        f"offset_mhz={freq_offset_mhz:.6f} new_freq={new_freq:.6f}",
                        flush=True
                )
                self.set_center_freq(new_freq)



        def get_center_freq(self):
                """Return requested center frequency of tuner in megahertz."""
                return self.sdr.get_center_freq()/1000000.0

        def set_center_freq(self, freq_mhz):
                """Set tuner center frequency to provided megahertz value."""
                try:
                        tuned_hz = freq_mhz * 1000000.0
                        self.sdr.set_center_freq(tuned_hz)
                        actual = self.sdr.get_center_freq() / 1000000.0
                        print(f"SET FREQ requested={freq_mhz} actual_tuned={actual}", flush=True)

                        for _ in range(3):
                                self.sdr.read_samples(256 * 1024)

                        self._clear_intensity()
                except Exception as e:
                        print(f"SET FREQ FAILED requested={freq_mhz} error={e}", flush=True)

        def get_sample_rate(self):
                """Return sample rate of tuner in megahertz."""
                return self.sdr.get_sample_rate()/1000000.0

        def set_sample_rate(self, sample_rate_mhz):
                """Set tuner sample rate to provided frequency in megahertz."""
                try:
                        self.sdr.set_sample_rate(sample_rate_mhz*1000000.0)
                except IOError:
                        # Error setting value, ignore it for now but in the future consider
                        # adding an error message dialog.
                        pass

        def get_gain(self):
                """Return gain of tuner.  Can be either the string 'AUTO' or a numeric
                value that is the gain in decibels.
                """
                if self.auto_gain:
                        return 'AUTO'
                else:
                        return '{0:0.1f}'.format(self.sdr.get_gain())

        def set_gain(self, gain_db):
                """Set gain of tuner.  Can be the string 'AUTO' for automatic gain
                or a numeric value in decibels for fixed gain.
                """
                if gain_db == 'AUTO':
                        self.sdr.set_manual_gain_enabled(False)
                        self.auto_gain = True
                        self._clear_intensity()
                else:
                        try:
                                self.sdr.set_gain(float(gain_db))
                                self.auto_gain = False
                                self._clear_intensity()
                        except IOError:
                                # Error setting value, ignore it for now but in the future consider
                                # adding an error message dialog.
                                pass

        def get_min_string(self):
                """Return string with the appropriate minimum intensity value, either
                'AUTO' or the min intensity in decibels (rounded to no decimals).
                """
                if self.min_auto_scale:
                        return 'AUTO'
                else:
                        return '{0:0.0f}'.format(self.min_intensity)

        def set_min_intensity(self, intensity):
                """Set Y axis minimum intensity in decibels (i.e. dB value at bottom of 
                spectrograms).  Can also pass 'AUTO' to enable auto scaling of value.
                """
                if intensity == 'AUTO':
                        self.min_auto_scale = True
                else:
                        self.min_auto_scale = False
                        self.min_intensity = float(intensity)
                self._clear_intensity()

        def get_max_string(self):
                """Return string with the appropriate maximum intensity value, either
                'AUTO' or the min intensity in decibels (rounded to no decimals).
                """
                if self.max_auto_scale:
                        return 'AUTO'
                else:
                        return '{0:0.0f}'.format(self.max_intensity)

        def set_max_intensity(self, intensity):
                """Set Y axis maximum intensity in decibels (i.e. dB value at top of 
                spectrograms).  Can also pass 'AUTO' to enable auto scaling of value.
                """
                if intensity == 'AUTO':
                        self.max_auto_scale = True
                else:
                        self.max_auto_scale = False
                        self.max_intensity = float(intensity)
                self._clear_intensity()

        def get_data(self):
                """Get spectrogram data from the tuner. Will return width number of
                values which are the intensities of each frequency bucket.
                """
                # Read a large block of samples from the SDR.
                samples = self.sdr.read_samples(freqshow.SDR_SAMPLE_SIZE)

                # Run FFT on the full sample block.
                freqs = np.absolute(np.fft.fft(samples))

                # Shift FFT result positions to put center frequency in center.
                freqs = np.fft.fftshift(freqs)

                # Apply display-only offset so the visual peak lands under the center marker.
                bin_hz = self.sdr.get_sample_rate() / len(freqs)
                offset_bins = int(round((DISPLAY_OFFSET_MHZ * 1000000.0) / bin_hz))
                freqs = np.roll(freqs, -offset_bins)

                # Compress the FFT down to the display width by averaging bins.
                bins_per_pixel = len(freqs) // self.width
                if bins_per_pixel > 1:
                                freqs = freqs[:bins_per_pixel * self.width]
                                freqs = freqs.reshape(self.width, bins_per_pixel).mean(axis=1)
                else:
                                freqs = freqs[:self.width]

                # Convert to decibels.
                freqs = 20.0 * np.log10(freqs + 1e-12)

                # Update model's min and max intensities when auto scaling each value.
                if self.min_auto_scale:
                                min_intensity = np.min(freqs)
                                self.min_intensity = min_intensity if self.min_intensity is None \
                                                else min(min_intensity, self.min_intensity)
                if self.max_auto_scale:
                                max_intensity = np.max(freqs)
                                self.max_intensity = max_intensity if self.max_intensity is None \
                                                else max(max_intensity, self.max_intensity)

                # Update intensity range.
                self.range = self.max_intensity - self.min_intensity

                return freqs

        