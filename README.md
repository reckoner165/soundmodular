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

Create a python file and paste this code. Ensure dependencies are available and installed. It should output a sequence of sounds.

```python
from soundmodular import Patcher
from pyaudio import paInt16

options = {
    'format': paInt16,
    'channels': 2,
    'sampling_rate': 22000,
    'save_file': 'testfile.wav'
}

patcher = Patcher(options)
module = patcher.module
T = 0.3

noise = module.wnoise(0.7*T, 0.2*T, 0.6)

for n in range(2,6):
    filt = module.filterbank_22k(noise, n, 1)
    patcher.to_master(filt, 0.5, 0.5)

osc = module.osc_tone(T, 440)
patcher.to_master(osc, 0.5, 0.5)

patcher.terminate()
```
`options` contains parameters necessary to setup the PyAudio and wave instances. soundmodular offers a limited API to these libraries.

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

