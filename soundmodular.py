"""
soundmodular is a library of functions designed to perform real-time signal processing on blocks of audio.
Each function takes inputs and outputs in a similar fashion, hence allowing them to
be aggregated into a signal chain to imitate modular synthesis.

An early version of soundmodular was called SoundModule, which was developed for SERIAL in December 2016.
https://github.com/reckoner165/TraceMelody

Sumanth Srinivasan - December 2017
"""

import math
import struct
from math import cos
from math import pi
import random

# Pans audio by applying different gains on left and right channels
def pan_stereo(x, gain_L, gain_R):

    x_stereo = [0 for n in range(0,2*len(x))]
    if gain_L > 1 or gain_L < 0 or gain_R > 1 or gain_R < 0:
        print "Invalid Gain. Try between 0 and 1"

    for n in range(0,len(x)):
        x_stereo[2*n] = gain_L * x[n]
        x_stereo[2*n + 1] = gain_R * x[n]

    stereo = struct.pack('h'*2*len(x), *x_stereo)  # 'h' for 16 bits
    return stereo

# All
# Oscilators
def oscTone(T, decay, f,Fs):

    N = int(T*Fs)    # N : Number of samples to play

    # r, omega values to build a filter
    om1 = 2.0*pi * float(f)/Fs
    r = 0.01**(1.0/(T*Fs))

    # Difference equation coefficients
    a1 = -2*r*cos(om1)
    a2 = r**2

    # Initialization
    y1 = 0.0
    y2 = 0.0
    gain = 1000.0

    outBlock = [0 for n in range(0,N)]
    for n in range(0, N):
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
        outBlock[n] = gain * y0

    return outBlock

# White noise generator - Takes duration, decay length, sampling rate and gain
def wnoise(T,decay,fs,gain):

    duration = int(T* fs)
    decay_samp = int(decay * fs)
    a = math.log(0.01)/decay_samp

    values = range(-32768, 32767)
    outBlock = [math.exp(a*n)*gain*random.choice(values) for n in range(0,duration)]

    return outBlock


# Effects modules

# Soft Clipping - Non linear compression with gain and ratio parameters
def clip(ratio,gain,block):
    outBlock = [0 for n in range(0,len(block))]

    for n in range(0,len(block)):
        if block[n] >= (ratio * gain * block[n]):
            outBlock[n] = int(ratio * gain * block[n])
        else:
            outBlock[n] = int(gain * block[n])

    return outBlock

# Vibrato
# Frequency Modulation function that takes LFO frequency, depth and sampling rate as parameters
def vibrato(block,fL,WL,fs):
    outBlock = [0 for n in range(0,len(block))]
    buffer_MAX = len(block)                          # Buffer length
    bufferL = [0.0 for i in range(buffer_MAX)]

    # Buffer (delay line) indices
    krL = 0  # read index
    kwL = int(0.5 * buffer_MAX)  # write index (initialize to middle of buffer)


    for n in range(0,len(block)):
        kr_prev = int(math.floor(krL))
        kr_next = kr_prev + 1
        frac = krL - kr_prev    # 0 <= frac < 1
        if kr_next >= buffer_MAX:
            kr_next = kr_next - buffer_MAX

        # Compute output value using interpolation
        outBlock[n] = (1-frac) * bufferL[kr_prev] + frac * bufferL[kr_next]

        # Update buffer (pure delay)
        bufferL[kwL] = block[n]

        # Increment read index
        krL = krL + 1 + WL * math.sin( 2 * math.pi * fL * n / fs )
            # Note: kr is fractional (not integer!)

        # Ensure that 0 <= kr < buffer_MAX
        if krL >= buffer_MAX:
            # End of buffer. Circle back to front.
            krL = 0

        # Increment write index
        kwL = kwL + 1
        if kwL == buffer_MAX:
            # End of buffer. Circle back to front.
            kwL = 0

    return outBlock

def filterbank_22k(filterN, gain, input):
    # A bank of bandpass filters at various frequencies triggered by coefficients.

    # List of coefficients and their center frequencies
    # 1 - 100Hz ***DOES NOT WORK***
    # 2 - 500Hz
    # 3 - 1000Hz
    # 4 - 2000Hz
    # 5 - 5000Hz
    # 6 - 10000Hz


    filtB = [[0.0001,0.0000,-0.0003,0.0000,0.0001],
             [0.0001,0.0000,-0.0003,0.0000,0.0001],
             [0.0001,0.0000,-0.0003,0.0000,0.0001],
             [0.0001,0.0000,-0.0003,0.0000,0.0001],
             [0.0001,0.0000,-0.0003,0.0000,0.0001],
             [0.0001,0.0000,-0.0003,0.0000,0.0001]]

    filtA = [[1.0000,-3.9584,5.8772,-3.8793,0.9604],
             [1.0000,-3.9197,5.8010,-3.8413,0.9604],
             [1.0000,-3.7996,5.5692,-3.7236,0.9604],
             [1.0000,-3.3314,4.7344,-3.2648,0.9604],
             [1.0000,-0.5636,2.0390,-0.5523,0.9604],
             [1.0000,3.7996,5.5692,3.7236,0.9604]]


    b = filtB[filterN-1]
    a = filtA[filterN-1]

    # Difference Equation

    y1 = 0.0000
    y2 = 0.0000
    y3 = 0.0000
    y4 = 0.0000

    x1 = 0.0000
    x2 = 0.0000
    x3 = 0.0000
    x4 = 0.0000


    outBlock = [0 for n in range(0,len(input))]
    for n in range(0, len(input)):
        # Use impulse as input signal
        x0 = input[n]

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
        outBlock[n] = gain*y0

    for k in range(0,len(outBlock)):
        if outBlock[k] > 32767:
            outBlock[k] = 32767
        elif outBlock[k] < -32768:
            outBlock[k] = -32768
    outBlock = [x for x in outBlock if not math.isnan(x)]
    return outBlock




# Mix function - adds two tracks. This function merely returns an element-wise sum.
# Does not normalize the sum.
# To avoid integer overflow, use clip() function to compress higher values.
def mix(track1, track2):
    len_list = [len(track1), len(track2)]
    max_len = max(len_list)

    track1 = [int(track1[n]) for n in range(0,len_list[0])]
    track2 = [int(track2[n]) for n in range(0,len_list[1])]

    track1.append([0 for n in range(0,max_len - len_list[0])])
    track2.append([0 for n in range(0,max_len - len_list[1])])

    track1 = [x for x in track1 if x != []]
    track2 = [x for x in track2 if x != []]

    outblock = [sum(x) for x in zip(track1, track2)]
    return outblock

