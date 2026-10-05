import torch
import torch.nn as nn

class PoseDecoder(nn.Module):
    """
    Implements Equation 10: Speech -> Sign 3D Pose Trajectory Generation
    Decodes Q_t into skeletal pose keypoints with spatial locus attractor offsets.
    """
    def __init__(self, in_dim=512, num_joints=25, max_len=50):
        super().__init__()
        self.num_joints = num_joints
        self.proj = nn.Linear(in_dim, max_len * num_joints * 3)

    def forward(self, Q_t, locus_means):
        """
        Q_t: (B, N, in_dim)
        locus_means: (B, M, 3)
        Returns: pose_trajectory of shape (B, T_out, J, 3)
        """
        B, N, _ = Q_t.shape
        pooled_q = torch.mean(Q_t, dim=1) # (B, in_dim)
        
        flat_pose = self.proj(pooled_q) # (B, max_len * J * 3)
        pose_traj = flat_pose.view(B, 50, self.num_joints, 3)
        
        # Add spatial locus offset attractor bias
        if locus_means is not None and locus_means.shape[1] > 0:
            mean_locus = torch.mean(locus_means, dim=1, keepdim=True).unsqueeze(1) # (B, 1, 1, 3)
            pose_traj = pose_traj + 0.1 * mean_locus
            
        return pose_traj

class TextDecoder(nn.Module):
    """
    Implements Equation 11: Sign -> Speech Text/Subword Generation
    Decodes Q_t into spoken language subword token probability distributions.
    """
    def __init__(self, in_dim=512, vocab_size=1000):
        super().__init__()
        self.vocab_size = vocab_size
        self.proj = nn.Linear(in_dim, vocab_size)

    def forward(self, Q_t):
        """
        Q_t: (B, N, in_dim)
        Returns: logits of shape (B, N, vocab_size)
        """
        logits = self.proj(Q_t)
        return logits
