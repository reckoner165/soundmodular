__author__ = 'Srinivasan'

import pyaudio
import wave

import math
import struct
from math import cos, pi
from datetime import datetime
import random

class Patcher:

    """
    Constructor takes in a dictionary of parameters:
    options = {'format': pyaudio format (pyaudio object),
               'channels' : number of channels (int),
               'sampling_rate' : sampling rate (int),
               'save_file' : path to save output audio (string)
               }
    """

    def __init__(self, user_dict):
        self.module = Module(user_dict['sampling_rate'])

        self.audio = pyaudio.PyAudio()
        self.format = user_dict.get('format', pyaudio.paInt16)
        self.stream = self.audio.open(format=self.format,
                                      channels=user_dict['channels'],
                                      rate=user_dict['sampling_rate'],
                                      input=False,
                                      output=True)

        # Setup fallback string for filename
        timestamp = str(datetime.now()).split('.')
        fallback_filename = 'output'+'-'.join('_'.join(timestamp[0].split(' ')).split(':'))+'.wav'
        filename = user_dict.get('save_file', fallback_filename)
        self.file = wave.open(filename, 'w')		        # self.file : wave file

        self.file.setnchannels(user_dict['channels'])		# stereo
        self.file.setsampwidth(2)		                    # four bytes per sample
        self.file.setframerate(user_dict['sampling_rate'])

        self.range = self.set_range()

    def set_range(self):
        # https://people.csail.mit.edu/hubert/pyaudio/docs/#pyaudio.paInt16
        # Soundmodular currently only supports integer format
        audio_format_range_mapper = {
            16: [-128, 127],                # int8
            8: [-32768, 32767],             # int16
            2: [-2147483648, 2147483647]    # int32
        }

        try:
            return audio_format_range_mapper[self.format]
        except KeyError:
            print "Format must be int8, int16 or int32. See PyAudio docs"
            quit()

    def to_master(self, block, gain_left, gain_right):
        """
        Sends audio to master - handles playback writing to file
        :param block: Input audio block (list)
        :param gain_left: Left channel gain (float)
        :param gain_right: Right channel gain (float)
        """

        # Hard Clip amplitude to fit in bit range to avoid overflow
        for k in range(0,len(block)):
            if block[k] > self.range[1]:
                block[k] = self.range[1]
            elif block[k] < self.range[0]:
                block[k] = self.range[0]

        str_out = self.module.pan_stereo(block, gain_left, gain_right)  # Returns a packed struct ready to write

        self.stream.write(str_out)              # Write to playback stream
        self.file.writeframes(str_out)          # Write to file

    def terminate(self):
        """
        Cleans up PyAudio and wave instances
        """
        self.file.close()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

class Module:

    def __init__(self, sampling_rate):
        self.sampling_rate = sampling_rate

    # Utility Modules
    # Pans audio by applying different gains on left and right channels
    @staticmethod
    def pan_stereo(input_block, gain_left, gain_right):
        """
        Pans input audio across 2 channels
        :param input_block: Input audio block (list)
        :param gain_left: Left channel gain (float)
        :param gain_right: Right channel gain (float)
        :return:
        """

        if gain_left > 1 or gain_left < 0 or gain_right > 1 or gain_right < 0:
            # print "Invalid Gain. Try between 0 and 1"
            raise ValueError("Invalid Gain. Try values between 0 and 1")

        x_stereo = [0 for n in range(0, 2*len(input_block))]

        for n in range(0,len(input_block)):
            x_stereo[2*n] = gain_left * input_block[n]
            x_stereo[2*n + 1] = gain_right * input_block[n]

        output_str = struct.pack('h'*2*len(input_block), *x_stereo)  # 'h' for 16 bits
        return output_str

    @staticmethod
    def mix(track1, track2):
        """
        Mixer - Adds two tracks.
        This function merely returns an element-wise sum. Does not normalize the sum.
        To avoid integer overflow, use clip() function to compress higher values.
        :param track1: Audio block track1 (list)
        :param track2: Audio block track2 (list)
        :return: Output audio block (list)
        """
        len_list = [len(track1), len(track2)]
        max_len = max(len_list)

        track1 = [int(track1[n]) for n in range(0,len_list[0])]
        track2 = [int(track2[n]) for n in range(0,len_list[1])]

        track1.append([0 for n in range(0,max_len - len_list[0])])
        track2.append([0 for n in range(0,max_len - len_list[1])])

        track1 = [x for x in track1 if x != []]
        track2 = [x for x in track2 if x != []]

        out_block = [sum(x) for x in zip(track1, track2)]
        return out_block

    # Source Modules

    def wnoise(self, duration, decay, gain):
        """
        White noise generator

        :param duration: Duration in seconds (int)
        :param decay: Logarithmic decay time in seconds (int)
        :param gain: Initial gain (float)
        :return: Output audio block (list)
        """
        duration = int(duration* self.sampling_rate)
        decay_samples = int(decay * self.sampling_rate)
        a = math.log(0.01)/decay_samples

        values = range(-32768, 32767)
        out_block = [math.exp(a*n)*gain*random.choice(values) for n in range(0, duration)]

        return out_block

    def osc_tone(self, duration, frequency):
        """
        Oscillator - Generates waveform from the impulse response of a second order filter

        :param duration: Duration in seconds (int)
        :param frequency: Frequency (int)
        :return: Output audio block (list)
        """

        num_samples = int(duration*self.sampling_rate)    # N : Number of samples to play

        # r, omega values to build a second order filter
        om1 = 2.0*pi * float(frequency)/self.sampling_rate
        r = 0.01**(1.0/(duration*self.sampling_rate))

        # Difference equation coefficients
        a1 = -2*r*cos(om1)
        a2 = r**2

        # Initialization
        y1 = 0.0
        y2 = 0.0
        gain = 1000.0

        out_block = [0 for n in range(0, num_samples)]
        for n in range(0, num_samples):
            # Use impulse as input signal
            if n == 0:
                x0 = 1.0
            else:
                x0 = 0.0

            # Difference equation
            y0 = x0 - a1 * y1 - a2 * y2

            # Delays
            y2 = y1
            y1 = y0

            # Output
            out_block[n] = gain * y0

        return out_block

    # Effects modules

    def sinusoid_fm(self, block, freq_lfo, depth):
        """
        Vibrato - varies delay using a sinusoid. Equivalent to FM with a sinusoid
        :param block: Input audio block (list)
        :param freq_lfo: LFO frequency (int)
        :param depth:  LFO depth (float)
        :return: Output audio block (list)
        """
        out_block = [0 for n in range(0,len(block))]
        buffer_MAX = len(block)                          # Buffer length
        delay_buffer = [0.0 for i in range(buffer_MAX)]

        # Buffer (delay line) indices
        kr = 0  # read index
        kw = int(0.5 * buffer_MAX)  # write index (initialize to middle of buffer)

        for n in range(0,len(block)):
            kr_prev = int(math.floor(kr))
            kr_next = kr_prev + 1
            frac = kr - kr_prev    # 0 <= frac < 1
            if kr_next >= buffer_MAX:
                kr_next -= buffer_MAX

            # Compute output value using interpolation
            out_block[n] = (1-frac) * delay_buffer[kr_prev] + frac * delay_buffer[kr_next]

            # Update buffer (pure delay)
            delay_buffer[kw] = block[n]

            # Increment read index
            kr = kr + 1 + depth * math.sin( 2 * math.pi * freq_lfo * n / self.sampling_rate)
            # Note: kr is fractional (not integer!)

            # Ensure that 0 <= kr < buffer_MAX
            if kr >= buffer_MAX:
                # End of buffer. Circle back to front.
                kr = 0

            # Increment write index
            kw += 1
            if kw == buffer_MAX:
                # End of buffer. Circle back to front.
                kw = 0

        return out_block

    @staticmethod
    def filterbank_22k(block, filter_index, gain):
        """
        Filterbank for 22k sampling rate signals
        A bank of bandpass filters at various frequencies triggered by coefficients.

        List of coefficients and their center frequencies
        1 - 100Hz ***DOES NOT WORK*** (TODO)
        2 - 500Hz
        3 - 1000Hz
        4 - 2000Hz
        5 - 5000Hz
        6 - 10000Hz

        :param block: Input audio block (list)
        :param filter_index: Index of filter in filterbank (int)
        :param gain: Output gain (float)
        :return: Output audio block (list)
        """
        if filter_index not in range(1,7):
            raise ValueError("Filter index must be a value between 1-6")

        # Filter coefficients hardcoded for 6 filters
        filterbank_b = [[0.0001,0.0000,-0.0003,0.0000,0.0001],
                        [0.0001,0.0000,-0.0003,0.0000,0.0001],
                        [0.0001,0.0000,-0.0003,0.0000,0.0001],
                        [0.0001,0.0000,-0.0003,0.0000,0.0001],
                        [0.0001,0.0000,-0.0003,0.0000,0.0001],
                        [0.0001,0.0000,-0.0003,0.0000,0.0001]]

        filterbank_a = [[1.0000,-3.9584,5.8772,-3.8793,0.9604],
                        [1.0000,-3.9197,5.8010,-3.8413,0.9604],
                        [1.0000,-3.7996,5.5692,-3.7236,0.9604],
                        [1.0000,-3.3314,4.7344,-3.2648,0.9604],
                        [1.0000,-0.5636,2.0390,-0.5523,0.9604],
                        [1.0000,3.7996,5.5692,3.7236,0.9604]]

        b = filterbank_b[filter_index-1]
        a = filterbank_a[filter_index-1]

        # Difference Equation

        y1 = 0.0000
        y2 = 0.0000
        y3 = 0.0000
        y4 = 0.0000

        x1 = 0.0000
        x2 = 0.0000
        x3 = 0.0000
        x4 = 0.0000

        out_block = [0 for n in range(0,len(block))]
        for n in range(0, len(block)):
            # Use impulse as input signal
            x0 = block[n]

            # Difference equation
            y0 = b[0]*x0 + b[1]*x1 + b[2]*x2 + b[3]*x3 + b[4]*x4 - a[1]*y1 - a[2]*y2 - a[3]*y3 - a[4]*y4

            # Delays
            y4 = y3
            y3 = y2
            y2 = y1
            y1 = y0

            x4 = x3
            x3 = x2
            x2 = x1
            x1 = x0

            # Output
            out_block[n] = gain*y0

        for k in range(0,len(out_block)):
            if out_block[k] > 32767:
                out_block[k] = 32767
            elif out_block[k] < -32768:
                out_block[k] = -32768
        out_block = [x for x in out_block if not math.isnan(x)]
        return out_block

    @staticmethod
    def clip(block, ratio, gain):
        """
        Soft Clipping - Non linear compression with gain and ratio parameters
        :param block: Input audio block (list)
        :param ratio: Compression ratio (float)
        :param gain: Output gain (float)
        :return: Output audio block (list)
        """
        out_block = [0 for n in range(0,len(block))]

        for n in range(0,len(block)):
            if block[n] >= (ratio * gain * block[n]):
                out_block[n] = int(ratio * gain * block[n])
            else:
                out_block[n] = int(gain * block[n])

        return out_block
