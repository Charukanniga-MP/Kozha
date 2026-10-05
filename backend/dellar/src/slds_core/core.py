import torch
import torch.nn as nn
import torch.nn.functional as F

from .entity import EntityExtractor
from .locus import SpatialLocusTracker
from .relation import EntityLocusBindingScorer, HypergraphLaplacianConv
from .memory import MemoryStateTracker
from .speech_adapter import SpeechAdapter
from .sign_adapter import SignAdapter
from .decoders import PoseDecoder, TextDecoder
from .sllsm_core import SLLSMCore, SLLSMOutput

class SLDSCore(nn.Module):
    """
    Spatial-Locus Dynamic Hypergraph State Core (SLDS-Core)
    Master Unified Bidirectional Model implementing Equations 1 through 12,
    integrated with the production Spatial-Locus Lifecycle State Machine (SLL-SM) Core.
    """
    def __init__(self, embed_dim=256, core_dim=512, max_entities=16, max_loci=8, num_joints=25, vocab_size=1000, use_sllsm=False):
        super().__init__()
        self.embed_dim = embed_dim
        self.core_dim = core_dim
        self.max_entities = max_entities
        self.max_loci = max_loci
        self.use_sllsm = use_sllsm
        
        # Modality Adapters
        self.speech_adapter = SpeechAdapter(in_channels=80, out_dim=embed_dim)
        self.sign_adapter = SignAdapter(num_joints=num_joints, out_dim=embed_dim)
        
        # Core State Extractors & Reasoners
        self.entity_extractor = EntityExtractor(embed_dim=embed_dim, max_entities=max_entities)
        self.locus_tracker = SpatialLocusTracker(max_loci=max_loci)
        self.binding_scorer = EntityLocusBindingScorer(embed_dim=embed_dim)
        self.hypergraph_conv = HypergraphLaplacianConv(in_features=embed_dim, out_features=embed_dim)
        self.memory_tracker = MemoryStateTracker()
        
        # Production SLL-SM Lifecycle Core Engine
        self.sllsm_core = SLLSMCore(
            num_slots=max_loci,
            num_entities=max_entities,
            embed_dim=embed_dim,
            core_dim=core_dim
        )
        
        # Legacy Core State Compiler (Equation 9)
        self.core_compiler = nn.Sequential(
            nn.Linear(embed_dim * 2 + 3, core_dim),
            nn.LayerNorm(core_dim),
            nn.ReLU()
        )
        
        # Modality Decoders
        self.pose_decoder = PoseDecoder(in_dim=core_dim, num_joints=num_joints)
        self.text_decoder = TextDecoder(in_dim=core_dim, vocab_size=vocab_size)

    def compile_common_state(self, entity_embeds, locus_means, locus_covs, incidence_matrix):
        """
        Implements Equation 9: Compiles entity nodes, 3D loci, and hypergraph relations into Q_t.
        """
        B, N, D = entity_embeds.shape
        _, M, _ = locus_means.shape
        
        # Hypergraph Message Passing
        hg_nodes = self.hypergraph_conv(entity_embeds, incidence_matrix) # (B, N, D)
        
        # Repeat/truncate locus means to match N entities
        locus_proj = F.pad(locus_means, (0, 0, 0, max(0, N - M)))[:, :N, :] # (B, N, 3)
        
        # Concatenate components
        combined = torch.cat([entity_embeds, hg_nodes, locus_proj], dim=-1) # (B, N, D*2 + 3)
        
        Q_t = self.core_compiler(combined) # (B, N, core_dim)
        return Q_t

    def forward(self, input_tensor, direction="Speech2Sign", hand_pointing=None, prev_loci=None, prev_covs=None, sllsm_obs=None, sllsm_state=None):
        """
        Execution Pipeline for Speech2Sign or Sign2Speech.
        Supports both legacy evaluation pipeline and SLL-SM production core pipeline.
        """
        B = input_tensor.shape[0]
        
        # 1. Modality Adaptation (Equation 1)
        if direction == "Speech2Sign":
            x_feat = self.speech_adapter(input_tensor) # (B, T, D)
        else:
            x_feat = self.sign_adapter(input_tensor) # (B, T, D)
            
        # 2. Extract Semantic Entity Nodes (Equation 3)
        entity_embeds = self.entity_extractor(x_feat) # (B, N, D)
        
        if self.use_sllsm and sllsm_obs is not None:
            # Production SLL-SM Core Execution Path
            sllsm_out: SLLSMOutput = self.sllsm_core(sllsm_obs, sllsm_state)
            Q_t = sllsm_out.Q
            binding_matrix = sllsm_out.B
            locus_means = sllsm_out.M
        else:
            # Legacy Prototype Core Execution Path (Backward Compatible)
            if prev_loci is None:
                prev_loci = torch.zeros(B, self.max_loci, 3, device=input_tensor.device)
            if prev_covs is None:
                prev_covs = torch.eye(3, device=input_tensor.device).unsqueeze(0).unsqueeze(0).repeat(B, self.max_loci, 1, 1)
            if hand_pointing is None:
                hand_pointing = torch.zeros(B, 3, device=input_tensor.device)
                
            locus_means, locus_covs = self.locus_tracker(prev_loci, prev_covs, entity_embeds, hand_pointing)
            
            # Entity-Locus Mahalanobis Association Score (Equation 5)
            binding_matrix = self.binding_scorer(entity_embeds, locus_means, locus_covs, hand_pointing) # (B, N, M)
            
            # Build Incidence Matrix for Hypergraph
            incidence_matrix = F.pad(binding_matrix, (0, max(0, self.max_entities - self.max_loci))) # (B, N, N)
            
            # Compile Common State Q_t (Equation 9)
            Q_t = self.compile_common_state(entity_embeds, locus_means, locus_covs, incidence_matrix)
        
        # 3. Decode Output
        if direction == "Speech2Sign":
            output = self.pose_decoder(Q_t, locus_means) # (B, T_out, J, 3)
        else:
            output = self.text_decoder(Q_t) # (B, N, vocab_size)
            
        return output, Q_t, binding_matrix, locus_means
