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
T = 0.3                     # Time in seconds

noise = module.wnoise(0.7*T, 0.2*T, 0.6)
osc = module.osc_tone(T, 440)

for n in range(2,6):
    print n
    filt = module.filterbank_22k(noise, n, 1)
    patcher.to_master(filt, 0.5, 0.5)

sil = module.silence(5*T)
patcher.to_master(osc, 0.5, 0.5)
patcher.to_master(sil, 0.5, 0.5)
patcher.to_master(osc, 0.5, 0.5)

patcher.terminate()

