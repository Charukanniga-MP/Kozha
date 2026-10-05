import torch
import torch.nn as nn

class MemoryStateTracker(nn.Module):
    """
    Implements Equation 6: Exponential Decay Temporal Memory Tracking
    """
    def __init__(self, retention_factor=0.95, threshold=0.05):
        super().__init__()
        self.gamma = retention_factor
        self.threshold = threshold

    def forward(self, current_activations, active_mask, delta_t=1.0):
        """
        current_activations: (B, N)
        active_mask: (B, N) boolean mask of active entities in current step
        delta_t: float time step interval
        """
        decay_factor = self.gamma ** delta_t
        decayed = current_activations * decay_factor
        
        # Active entities reset to 1.0
        updated = torch.where(active_mask, torch.ones_like(current_activations), decayed)
        keep_mask = updated > self.threshold
        return updated, keep_mask
