import librosa
import numpy as np

def psnr(audio_path_1, audio_path_2):
    y1, sr1 = librosa.load(audio_path_1, sr=None)
    y2, sr2 = librosa.load(audio_path_2, sr=None)

    if sr1 != sr2:
        raise ValueError("Sample rates of the two audio files must be the same.")

    P1 = np.mean(y1**2)
    P2 = np.mean(y2**2)

    return (10 * np.log10((P1**2) / ((P1 - P2)**2))) if P1 != P2 else float('inf')
