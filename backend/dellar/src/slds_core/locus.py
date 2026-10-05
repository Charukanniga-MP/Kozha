import torch
import torch.nn as nn
import torch.nn.functional as F

class CoordinateNormalizer(nn.Module):
    """
    Implements Equation 2: Body-centered SO(3) Shoulder Transformation
    Transforms raw keypoints (B, T, J, 3) to invariant normalized keypoints.
    """
    def __init__(self, left_shoulder_idx=11, right_shoulder_idx=12):
        super().__init__()
        self.ls_idx = left_shoulder_idx
        self.rs_idx = right_shoulder_idx

    def forward(self, raw_keypoints):
        # raw_keypoints: (B, T, J, 3)
        ls = raw_keypoints[..., self.ls_idx, :]
        rs = raw_keypoints[..., self.rs_idx, :]
        
        # 1. Origin at Chest Midpoint
        chest = 0.5 * (ls + rs) # (B, T, 3)
        centered = raw_keypoints - chest.unsqueeze(-2)
        
        # 2. Scale by Shoulder Width
        shoulder_width = torch.norm(rs - ls, p=2, dim=-1, keepdim=True) # (B, T, 1)
        scale = torch.clamp(shoulder_width, min=1e-5)
        normalized = centered / scale.unsqueeze(-2)
        
        return normalized

class SpatialLocusTracker(nn.Module):
    """
    Implements Equation 4: 3D Spatial Locus Dynamics & Covariance Updates
    """
    def __init__(self, max_loci=8, inertia=0.9):
        super().__init__()
        self.max_loci = max_loci
        self.inertia = inertia
        self.locus_mlp = nn.Sequential(
            nn.Linear(256 + 3, 128),
            nn.ReLU(),
            nn.Linear(128, 3)
        )

    def forward(self, prev_means, prev_covs, entity_embeddings, hand_pointing_xyz):
        """
        prev_means: (B, M, 3)
        prev_covs: (B, M, 3, 3)
        entity_embeddings: (B, M, 256)
        hand_pointing_xyz: (B, 3)
        """
        B, M, _ = prev_means.shape
        
        # Predict delta locus coordinates
        locus_in = torch.cat([entity_embeddings[:, :M, :], hand_pointing_xyz.unsqueeze(1).repeat(1, M, 1)], dim=-1)
        delta_locus = self.locus_mlp(locus_in) # (B, M, 3)
        
        new_means = self.inertia * prev_means + (1.0 - self.inertia) * (prev_means + delta_locus)
        
        # Update covariance matrices
        diff = hand_pointing_xyz.unsqueeze(1) - new_means # (B, M, 3)
        outer_product = torch.einsum('bmi,bmj->bmij', diff, diff) # (B, M, 3, 3)
        
        new_covs = self.inertia * prev_covs + (1.0 - self.inertia) * outer_product
        return new_means, new_covs
