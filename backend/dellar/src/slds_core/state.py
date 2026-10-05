import torch
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Entity:
    entity_id: int
    name: str
    embedding: torch.Tensor # (d_e,)
    activation: float = 1.0

@dataclass
class SpatialLocus:
    locus_id: int
    mean_xyz: torch.Tensor # (3,)
    covariance: torch.Tensor # (3, 3)
    confidence: float = 1.0

@dataclass
class Hyperedge:
    hyperedge_id: int
    entity_ids: List[int]
    locus_ids: List[int]
    relation_type: str
    weight: float = 1.0

@dataclass
class CommunicationState:
    entities: List[Entity] = field(default_factory=list)
    loci: List[SpatialLocus] = field(default_factory=list)
    hyperedges: List[Hyperedge] = field(default_factory=list)
    temporal_step: int = 0
    discourse_context: Optional[torch.Tensor] = None # (d_c,)
    core_tensor: Optional[torch.Tensor] = None # (B, N, d_core)
