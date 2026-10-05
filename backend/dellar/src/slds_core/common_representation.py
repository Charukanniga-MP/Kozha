import torch
import torch.nn as nn
from typing import Dict, Any, Optional

class CommonRepresentation:
    """
    Standardized Modality-Independent Intermediate Representation payload for SLLSMCore.
    Unifies Speech and Sign inputs into a common semantic/spatial-locus format.
    """
    def __init__(
        self,
        u_feat: torch.Tensor,              # (B, D) Feature embedding
        x_hand: Optional[torch.Tensor] = None, # (B, 3) Hand spatial position
        p_torso: Optional[torch.Tensor] = None, # (B, 3) Torso reference position
        g_gaze: Optional[torch.Tensor] = None,  # (B, 3) Gaze direction vector
        p_pointing: Optional[torch.Tensor] = None, # (B, 1) Pointing gesture probability
        p_release: Optional[torch.Tensor] = None,  # (B, 1) Open-palm release probability
        target_entity: Optional[torch.Tensor] = None, # (B,) Target entity index
        confidence: float = 1.0,
        modality_source: str = "GENERIC"
    ):
        B = u_feat.shape[0]
        device = u_feat.device
        
        self.u_feat = u_feat
        self.x_hand = x_hand if x_hand is not None else torch.zeros(B, 3, device=device)
        self.p_torso = p_torso if p_torso is not None else torch.zeros(B, 3, device=device)
        self.dp_torso = torch.zeros(B, 3, device=device)
        self.g_gaze = g_gaze if g_gaze is not None else torch.tensor([[0.0, 0.0, 1.0]], device=device).expand(B, 3)
        self.p_pointing = p_pointing if p_pointing is not None else torch.zeros(B, 1, device=device)
        self.p_release = p_release if p_release is not None else torch.zeros(B, 1, device=device)
        self.target_entity = target_entity
        self.confidence = confidence
        self.modality_source = modality_source

    def to_obs_frame(self) -> Dict[str, Any]:
        """
        Converts payload into dictionary format expected by SLLSMCore.forward()
        """
        return {
            'x_hand': self.x_hand,
            'p_torso': self.p_torso,
            'dp_torso': self.dp_torso,
            'g_gaze': self.g_gaze,
            'p_pointing': self.p_pointing,
            'p_release': self.p_release,
            'u_feat': self.u_feat,
            'target_entity': self.target_entity
        }
