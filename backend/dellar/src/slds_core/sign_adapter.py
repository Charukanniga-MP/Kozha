import torch
import torch.nn as nn
from .locus import CoordinateNormalizer

class SignAdapter(nn.Module):
    """
    Implements Equation 1 (Sign Adapter Branch)
    Linear keypoint projection after SO(3) shoulder normalization.
    """
    def __init__(self, num_joints=25, out_dim=256):
        super().__init__()
        self.normalizer = CoordinateNormalizer()
        self.proj = nn.Linear(num_joints * 3, out_dim)

    def forward(self, pose_input):
        """
        pose_input: (B, T, J, 3) or (B, T, J*3)
        Returns: (B, T, out_dim)
        """
        if pose_input.dim() == 4:
            norm_pose = self.normalizer(pose_input)
            B, T, J, C = norm_pose.shape
            flat_pose = norm_pose.view(B, T, J * C)
        else:
            flat_pose = pose_input
            
        return self.proj(flat_pose)
