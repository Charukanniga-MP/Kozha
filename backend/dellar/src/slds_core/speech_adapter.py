import torch
import torch.nn as nn

class SpeechAdapter(nn.Module):
    """
    Implements Equation 1 (Speech Adapter Branch)
    1D Convolutional Downsampling for Mel-spectrogram speech features.
    """
    def __init__(self, in_channels=80, out_dim=256):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, out_dim, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(out_dim),
            nn.ReLU(),
            nn.Conv1d(out_dim, out_dim, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(out_dim),
            nn.ReLU()
        )

    def forward(self, speech_input):
        """
        speech_input: (B, T_audio, F_mel) or (B, F_mel, T_audio)
        Returns: (B, T_out, out_dim)
        """
        if speech_input.dim() == 3 and speech_input.shape[1] != 80 and speech_input.shape[2] == 80:
            speech_input = speech_input.transpose(1, 2)
            
        feat = self.conv(speech_input) # (B, out_dim, T_out)
        return feat.transpose(1, 2) # (B, T_out, out_dim)
