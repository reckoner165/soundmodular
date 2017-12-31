# soundmodular

soundmodular is a library of functions designed to perform real-time signal processing on blocks of audio.
Each function takes inputs and outputs in a similar fashion, hence allowing them to
be aggregated into a signal chain to imitate modular synthesis.

An early version of soundmodular was called SoundModule, which was developed for SERIAL in December 2016.
Here is a [paper](https://github.com/reckoner165/TraceMelody/blob/master/SERIAL%20(1).pdf).

## Requirements

(Updated: 31 December 2017)

You need PyAudio to use soundmodular.   
On Debian systems, `sudo apt-get install python-pyaudio python3-pyaudio`  
On Fedora or similar, `sudo dnf build-dep python3-pyaudio`  
On Mac OS, use Homebrew to install a dependency and then use pip  
```
brew install portaudio 
pip install pyaudio
```


## Installation

Clone this repository and copy soundmodular.py into your project directory.

## How To

The following is example code that interfaces `soundmodular` with PyAudio, file output as well as the syntax for patching sounds.
Create a file called patcher.py and paste this code. Ensure dependencies are installed. It should output a sequence of sounds.

```python
import pyaudio
import soundmodular as sm
import wave

# Setup PyAudio and File
Fs = 22000

# Setup playback stream on pyaudio and set parameters
p = pyaudio.PyAudio()
stream = p.open(format = pyaudio.paInt16,
                channels = 2,
                rate = Fs,
                input = False,
                output = True)

# Open a wavefile in write mode and set parameters
filename = 'test_file' + '.wav'
wf = wave.open(filename, 'w')
wf.setnchannels(2)		# stereo
wf.setsampwidth(2)		# four bytes per sample
wf.setframerate(Fs)


# Single function to handle playback and file save
def to_master(x, L, R):

    # Hard Clip amplitude to fit in bit range
    for k in range(0,len(x)):
        if x[k] > 32767:
            x[k] = 32767
        elif x[k] < -32768:
            x[k] = -32768

    str_out = sm.pan_stereo(x, L, R) # Returns a packed struct ready to write

    stream.write(str_out) # Write to playback stream
    wf.writeframes(str_out) # Write to file


T = 1 # Create 1 second of audio
to_master(sm.oscTone(T,0.5*T,440,Fs),0.8,0.3) # Oscillator -> Master
to_master(sm.wnoise(0.7*T,0.5*T,Fs,0.6),0.5,1) # WhiteNoise -> Master
to_master(sm.filterbank_22k(3,1,sm.wnoise(0.7*T,0.9*T,Fs,1)),0.5,0.5) # WhiteNoise -> Filterbank -> Master

wf.close()
stream.close()
p.terminate()
print 'Done'
```

All functions except `pan_stereo()` return a list corresponding to a block of stereo audio, and hence each output can be passed as parameter into another function.

## Available Functions

### pan_stereo()
>Pans audio across left and right channels. Returns packed struct.
```
pan_stereo(x, gain_L, gain_R)

x - input stereo audio vector  
gain_L - left channel gain  
gain_R - right channel gain  
```
Usage:
```python
out = pan_stereo(x, 1, 0)
stream.write(out)
``` 

### oscTone()
>Generates impulse response of a second order linear filter
```
oscTone(T, decay, f, Fs)

T - Block duration in seconds
decay - Logarithmic decay time in seconds 
Fs - Sampling rate
```

Usage:
```python
# Oscillator -> Out
tone = oscTone(1, 0.5, 440, 22000)
out = pan_stereo(tone, 1, 1) 
stream.write(out)
```

### wnoise()
>White noise generator. Returns stereo interleaved list.  
```
wnoise(T,decay,fs,gain)  

T - Block duration in seconds  
decay - Logarithmic decay time in seconds  
fs - Sampling Rate  
gain - Initial Gain 
``` 
Usage:
```python
# Noise -> Out
noise = wnoise(1, 0.5, 22000, 0.5)
out = pan_stereo(noise, 1, 1)
stream.write(out)
```

### clip()
>Non-linear clipping. Works like a compressor.
```
clip(ratio,gain,block)

ratio - Compression ratio
gain -  Threshold gain when compression must engage
block - Input block
```

Usage:
```python
# Noise -> Compression -> Out
noise = wnoise(1, 0.5, 22000, 0.5)
comp = clip(0.5, 1, noise)
out = pan_stereo(comp, 1, 1)
stream.write(out)
```

### vibrato()
>Produces vibrato effect using frequency modulation with a sinusoid LFO.
```
vibrato(block,fL,WL,fs)

block - Input block
fL - LFO frequency
WL - LFO depth
fs - Sampling rate
```

Usage:
```python
# Oscillator -> Vibrato -> Out
tone = oscTone(1, 0.5, 440, 22000)
vib = vibrato(tone, 10, 0.5, 22000)
out = pan_stereo(vib, 1, 1) 
stream.write(out)
```

### filterbank_22k()
>A bank of bandpass filters. *The filters are operational only at 22000Hz sampling rate.*
```
filterbank_22k(filterN, gain, input)

filterN - Filter coefficient (can be values 1-6)
gain - Output gain
input - Input block
```

Usage:
```python
# Noise -> Filter -> Out
noise = wnoise(0.7, 0.9, 22000, 1)
filt = filterbank_22k(3, 1, noise)
out = pan_stereo(filt, 1, 1) 
stream.write(out)
```

### mix()
>Adds two tracks and returns 1. This function does not normalize the output, hence it's recommended to use the clip() function to avoid overflow.
```
mix(track1, track2)

track1 - Input block1
track2 - Input block2
```

Usage:
```python
# Oscilator -> Vibrato (+)
# Noise -> Filterbank (+) Mix -> Out
osc = oscTone(1, 0.5, 440, 22000)
vib = vibrato(osc, 30, 0.3, 22000)

noise = wnoise(1, 1.5, 22000, 1)
bass = filterbank_22k(3, 0.8, noise)

out = mix(sm.clip(0.5,1,vib),sm.clip(0.6,1,bass))
```

