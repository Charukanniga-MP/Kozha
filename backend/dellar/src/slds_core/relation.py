import torch
import torch.nn as nn
import torch.nn.functional as F

class EntityLocusBindingScorer(nn.Module):
    """
    Implements Equation 5: Entity-Locus Association Score Matrix
    """
    def __init__(self, embed_dim=256):
        super().__init__()
        self.W_entity = nn.Linear(embed_dim, embed_dim)
        self.W_locus = nn.Linear(3, embed_dim)

    def forward(self, entity_embeddings, locus_means, locus_covariances, hand_pointing_xyz):
        """
        entity_embeddings: (B, N, D)
        locus_means: (B, M, 3)
        locus_covariances: (B, M, 3, 3)
        hand_pointing_xyz: (B, 3)
        """
        B, N, D = entity_embeddings.shape
        _, M, _ = locus_means.shape
        
        # 1. Semantic Similarity
        proj_entities = self.W_entity(entity_embeddings) # (B, N, D)
        proj_loci = self.W_locus(locus_means) # (B, M, D)
        semantic_sim = torch.bmm(proj_entities, proj_loci.transpose(1, 2)) / (D ** 0.5) # (B, N, M)
        
        # 2. Spatial Mahalanobis Distance Component
        diff = hand_pointing_xyz.unsqueeze(1) - locus_means # (B, M, 3)
        eye3 = torch.eye(3, device=locus_means.device).unsqueeze(0).unsqueeze(0)
        cov_inv = torch.inverse(locus_covariances + 1e-4 * eye3) # (B, M, 3, 3)
        
        mahalanobis_sq = torch.einsum('bmi,bmij,bmj->bm', diff, cov_inv, diff) # (B, M)
        spatial_affinity = -0.5 * mahalanobis_sq.unsqueeze(1) # (B, N, M)
        
        # 3. Association Matrix (Softmax across Loci)
        association_matrix = F.softmax(semantic_sim + spatial_affinity, dim=-1)
        return association_matrix

class HypergraphLaplacianConv(nn.Module):
    """
    Implements Equation 8: Dynamic Hypergraph Laplacian Message Passing
    """
    def __init__(self, in_features=256, out_features=256):
        super().__init__()
        self.W = nn.Linear(in_features, out_features)

    def forward(self, node_features, incidence_matrix):
        """
        node_features: (B, V, D)
        incidence_matrix B: (B, V, E_h)
        """
        # Node degree matrix D_v
        D_v = torch.sum(incidence_matrix, dim=-1, keepdim=True) + 1e-5 # (B, V, 1)
        D_v_inv_sqrt = 1.0 / torch.sqrt(D_v)
        
        # Edge degree matrix D_e
        D_e = torch.sum(incidence_matrix, dim=1, keepdim=True) + 1e-5 # (B, 1, E_h)
        D_e_inv = 1.0 / D_e
        
        # Hypergraph Laplacian propagation: D_v^-1/2 * B * D_e^-1 * B^T * D_v^-1/2 * X * W
        norm_node = node_features * D_v_inv_sqrt # (B, V, D)
        edge_pass = torch.bmm(incidence_matrix.transpose(1, 2), norm_node) * D_e_inv.transpose(1, 2) # (B, E_h, D)
        node_pass = torch.bmm(incidence_matrix, edge_pass) * D_v_inv_sqrt # (B, V, D)
        
        out = self.W(node_pass)
        return F.relu(out)
