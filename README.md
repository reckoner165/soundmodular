# soundmodular

soundmodular is a library of functions designed to perform real-time signal processing on blocks of audio.
Each function takes inputs and outputs in a similar fashion, hence allowing them to
be aggregated into a signal chain to imitate modular synthesis.

An early version of soundmodular was called SoundModule, which was developed for SERIAL in December 2016.
Here is a [paper](https://github.com/reckoner165/TraceMelody/blob/master/SERIAL%20(1).pdf).

## Requirements

(Updated: 12 January 2018)

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

Create a python file and paste this code. Ensure dependencies are available and installed. It should output a sequence of sounds upon running.

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
T = 0.3                 # Time in seconds

noise = module.wnoise(0.7*T, 0.2*T, 0.6)

for n in range(2,6):
    filt = module.filterbank_22k(noise, n, 1)
    patcher.to_master(filt, 0.5, 0.5)

osc = module.osc_tone(T, 440)
patcher.to_master(osc, 0.5, 0.5)

patcher.terminate()
```
`options` contains parameters necessary to setup the PyAudio and wave instances. soundmodular offers a limited API to these libraries.

## Development

One of the long term goals is to use soundmodular as a framework to build additional modules that can be plugged into the signal chain.
This calls for a set of conventions, IO specifications and if necessary, abstract classes that define what constitutes a sound module.
These definitions are likely to change with time as well as a wider variety of applications.
Feel free to open issues/contact the author(s) in this regard.

## Structure/Documentation

Following is a documentation of currently available functions in soundmodular.

### Patcher Class

The Patcher Class attempts to imitate a patch bay. Each Patcher instance creates wave and PyAudio objects, hence setting up playback and recording.
The parameters are passed to the constructor in the form of an `options` dictionary.
```python
    options = {'format': pyaudio format (int),                      # Recommended to use PyAudio constants
               'channels' : number of channels (int),
               'sampling_rate' : sampling rate (int),
               'save_file' : path to save output audio (string)
               }
```
Usage:
```python
options = {
    'format': paInt16,
    'channels': 2,
    'sampling_rate': 22000,
    'save_file': 'testfile.wav'
}

patcher = Patcher(options)
```
### Module Class

The Module class is contains a suite of functions that operate on lists corresponding to audio blocks. These may be sound sources (oscilators, generators), effects modules or utility modules.
An instance of the Module class is created during the initiation of the Patcher class.
It is however, possible to create your own custom PyAudio/wave instance and merely use a Module object without Patcher.

Usage:
```python
sampling_rate = 11000
module = Module(sampling_rate)
```
Following are the currently available functions in Module.

#### osc_tone()
>Generates impulse response of a second order linear filter
```
osc_tone(duration, frequency)

    :param duration: Duration in seconds (int)
    :param frequency: Frequency in Hz (int)
    :return: Output audio block (list)
```

Usage:
```python
# Oscillator -> Out
tone = module.osc_tone(1, 440)
patcher.to_master(tone, 0.5, 0.5)
```

#### wnoise()
>White noise generator. Returns stereo interleaved list.  
```
wnoise(duration,decay,gain)

    :param duration: Duration in seconds (int)
    :param decay: Logarithmic decay time in seconds (int)
    :param gain: Initial gain (float)
    :return: Output audio block (list)
``` 
Usage:
```python
# Noise -> Out
noise = module.wnoise(1, 0.5, 0.5)
patcher.to_master(noise, 0.5, 0.5)
```

#### clip()
>Non-linear clipping. Works like a compressor.
```
clip(block,ratio,gain)

    :param block: Input audio block (list)
    :param ratio: Compression ratio (float)
    :param gain: Output gain (float)
    :return: Output audio block (list)
```

Usage:
```python
# Noise -> Compression -> Out
noise = module.wnoise(1, 0.5, 0.5)
comp = module.clip(noise, 0.5, 1)
patcher.to_master(comp, 0.5, 0.5)
```

#### sinusoid_fm()
>Produces vibrato effect using frequency modulation with a sinusoid LFO.
```
sinusoid_fm(block,freq_lfo, depth)

    :param block: Input audio block (list)
    :param freq_lfo: LFO frequency (int)
    :param depth:  LFO depth (float)
    :return: Output audio block (list)
```

Usage:
```python
# Oscillator -> Sinusoid_FM -> Out
tone = module.osc_tone(1, 0.5, 440)
fm = module.sinusoid_fm(tone, 10, 0.5)
patcher.to_master(fm, 0.5, 0.5)
```

#### filterbank_22k()
>A bank of bandpass filters. *The filters are operational only at 22000Hz sampling rate.*
```
filterbank_22k(block, filter_index, gain)

    :param block: Input audio block (list)
    :param filter_index: Index of filter in filterbank (int) Values can range from : 1-6
    :param gain: Output gain (float)
    :return: Output audio block (list)
```

Usage:
```python
# Noise -> Filter -> Out
noise = module.wnoise(0.7, 0.9, 1)
filt = module.filterbank_22k(noise, 3, 1)
patcher.to_master(filt, 0.5, 0.5)
```

#### mix()
>Adds two tracks and returns a block of the mix. This function does not normalize the output, hence it's recommended to use the clip() function to avoid overflow. Gain staging needs to be done before calling `mix()`.

```
mix(track1, track2)

    :param track1: Audio block track1 (list)
    :param track2: Audio block track2 (list)
    :return: Output audio block (list)
```

Usage:
```python
# Oscilator -> Vibrato (+)
# Noise -> Filterbank (+) Mix -> Out
osc = module.osc_tone(1, 0.5, 440)
vib = module.vibrato(osc, 30, 0.3)

noise = module.wnoise(1, 1.5, 1)
bass = module.filterbank_22k(noise, 3, 0.8)

out = module.mix(module.clip(0.5,1,vib),module.clip(0.6,1,bass))
patcher.to_master(out, 0.5, 0.5)
```

