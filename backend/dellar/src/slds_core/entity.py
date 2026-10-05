import torch
import torch.nn as nn

class EntityExtractor(nn.Module):
    def __init__(self, embed_dim=256, max_entities=16):
        super().__init__()
        self.embed_dim = embed_dim
        self.max_entities = max_entities
        self.entity_queries = nn.Parameter(torch.randn(max_entities, embed_dim) * 0.02)
        self.cross_attn = nn.MultiheadAttention(embed_dim, num_heads=4, batch_first=True)
        self.layer_norm = nn.LayerNorm(embed_dim)

    def forward(self, input_features):
        """
        input_features: (B, T, D)
        Returns: entity_embeddings of shape (B, max_entities, D)
        """
        B, T, D = input_features.shape
        queries = self.entity_queries.unsqueeze(0).repeat(B, 1, 1) # (B, N, D)
        
        attn_out, _ = self.cross_attn(query=queries, key=input_features, value=input_features)
        entity_embeddings = self.layer_norm(queries + attn_out)
        return entity_embeddings
