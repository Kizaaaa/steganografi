import numpy as np
import librosa
import warnings
import sys
import os

def psnr(audio_path_1, audio_path_2):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    # ini buat surpress warning mp3 dequantization failed
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            y1, sr1 = librosa.load(audio_path_1, sr=None)
            y2, sr2 = librosa.load(audio_path_2, sr=None)
    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    if sr1 != sr2:
        raise ValueError(f"Sample rates must match: {sr1} Hz vs {sr2} Hz")
    
    min_len = min(len(y1), len(y2))
    y1 = y1[:min_len]
    y2 = y2[:min_len]
    
    mse = np.mean((y1 - y2) ** 2)
    
    if mse == 0:
        return float('inf')
    
    MAX = max(np.max(np.abs(y1)), np.max(np.abs(y2)))
    
    psnr_value = 10 * np.log10((MAX ** 2) / mse)
    
    return psnr_value
