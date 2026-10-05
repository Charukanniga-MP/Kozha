import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

# State Constants
STATE_UNASSIGNED = 0
STATE_CREATED    = 1
STATE_ACTIVE     = 2
STATE_SHIFTED    = 3
STATE_RELEASED   = 4
NUM_STATES       = 5


@dataclass
class SLLSMOutput:
    """
    Structured output container for Spatial-Locus Lifecycle State Machine (SLL-SM) Core.
    """
    Q: torch.Tensor          # (B, N, C) Master compiled common core state
    M: torch.Tensor          # (B, K, 3) Updated locus 3D coordinates
    v: torch.Tensor          # (B, K) Locus validity flags (1=valid, 0=invalid)
    S: torch.Tensor          # (B, K, 5) Updated 5-class one-hot lifecycle state
    B: torch.Tensor          # (B, N, K) Updated bipartite entity-locus binding matrix
    E: torch.Tensor          # (B, N, D) Updated entity memory matrix
    M_valid: torch.Tensor    # (B, K, 3) Valid locus coordinates (masked with v)
    state_dict: Dict[str, torch.Tensor]  # Backward-compatible state dictionary for next timestep


class SLLSMCore(nn.Module):
    """
    Spatial-Locus Lifecycle State Machine (SLL-SM) Production Core Module.
    
    Implements the audited specification in research/FINAL_SLLSM_ALGORITHM_SPECIFICATION.md:
    1. Decoupled Entity Memory E ∈ R^(N × D) and Spatial Locus Memory M ∈ R^(K × 3).
    2. Discrete 5-class lifecycle state machine (UNASSIGNED, CREATED, ACTIVE, SHIFTED, RELEASED).
    3. Deterministic FSM state transition guards.
    4. State-gated continuous coordinate update multiplexer.
    5. Bipartite entity-locus binding matrix B ∈ [0, 1]^(N × K) and validity mask v ∈ {0, 1}^K.
    6. Master compiled common core state Q = LayerNorm(W_e * E + W_l * (B @ M_valid)).
    """
    def __init__(
        self,
        num_slots: int = 4,
        num_entities: int = 16,
        embed_dim: int = 256,
        core_dim: int = 512,
        gate_type: str = "ste",
        tau: float = 1.0,
        shift_threshold: float = 0.1
    ):
        super().__init__()
        self.K = num_slots        # K = 4 spatial locus slots
        self.N = num_entities     # N = 16 semantic entity slots
        self.D = embed_dim        # D = 256 entity feature dimension
        self.C = core_dim         # C = 512 core state dimension
        self.gate_type = gate_type
        self.tau = tau
        self.shift_threshold = shift_threshold
        
        # Transition Logit Predictor
        # Input dim per slot j:
        # S_prev (5) + hand_delta (3) + torso_delta (3) + gaze_dot (1) + pointing (1) = 13
        self.transition_mlp = nn.Sequential(
            nn.Linear(13, 64),
            nn.ReLU(),
            nn.Linear(64, NUM_STATES)
        )
        
        # Entity Embedding Update & Master Core Compiler
        self.W_u = nn.Linear(embed_dim, embed_dim)
        self.W_e = nn.Linear(embed_dim, core_dim)
        self.W_l = nn.Linear(3, core_dim)
        self.layer_norm = nn.LayerNorm(core_dim)

    def init_state(self, batch_size: int, device: torch.device) -> Dict[str, torch.Tensor]:
        """
        Initializes zero-state dictionary for SLL-SM core.
        
        Returns:
            Dict containing initialized state tensors:
            - 'S': (B, K, 5) One-hot states (all initialized to STATE_UNASSIGNED)
            - 'M': (B, K, 3) 3D locus coordinates (zeros)
            - 'v': (B, K) Validity flags (zeros)
            - 'E': (B, N, D) Entity memory embeddings (zeros)
            - 'B': (B, N, K) Bipartite binding matrix (zeros)
        """
        S_init = torch.zeros(batch_size, self.K, NUM_STATES, device=device)
        S_init[:, :, STATE_UNASSIGNED] = 1.0
        
        M_init = torch.zeros(batch_size, self.K, 3, device=device)
        v_init = torch.zeros(batch_size, self.K, device=device)
        E_init = torch.zeros(batch_size, self.N, self.D, device=device)
        B_init = torch.zeros(batch_size, self.N, self.K, device=device)
        
        return {
            'S': S_init,
            'M': M_init,
            'v': v_init,
            'E': E_init,
            'B': B_init
        }

    def _apply_fsm_guards(
        self,
        logits: torch.Tensor,
        S_prev: torch.Tensor,
        p_pointing: torch.Tensor,
        p_release: torch.Tensor,
        dp_torso: torch.Tensor
    ) -> torch.Tensor:
        """
        Applies deterministic FSM transition guards to logits before discrete state selection.
        logits: (B, K, 5)
        S_prev: (B, K, 5)
        p_pointing: (B, 1) or (B, K, 1)
        p_release: (B, 1) or (B, K, 1)
        dp_torso: (B, 3)
        """
        B, K, _ = logits.shape
        curr_state_idx = torch.argmax(S_prev, dim=-1)  # (B, K)
        guard_mask = torch.zeros_like(logits)          # (B, K, 5)
        
        torso_speed = torch.norm(dp_torso, dim=-1)     # (B,)
        
        for b in range(B):
            # Determine target slot for creation if pointing gesture active
            unassigned_slots = torch.where(curr_state_idx[b] == STATE_UNASSIGNED)[0]
            target_create_slot = unassigned_slots[0].item() if len(unassigned_slots) > 0 else -1
            
            for k_idx in range(K):
                st = curr_state_idx[b, k_idx].item()
                
                # Extract scalar values
                p_pt = p_pointing[b, 0].item() if p_pointing.dim() == 2 else p_pointing[b, k_idx, 0].item()
                p_rel = p_release[b, 0].item() if p_release.dim() == 2 else p_release[b, k_idx, 0].item()
                t_spd = torso_speed[b].item()
                
                if st == STATE_UNASSIGNED:
                    # Guard 1: UNASSIGNED cannot jump directly to ACTIVE, SHIFTED, or RELEASED
                    guard_mask[b, k_idx, STATE_ACTIVE] = -1e9
                    guard_mask[b, k_idx, STATE_SHIFTED] = -1e9
                    guard_mask[b, k_idx, STATE_RELEASED] = -1e9
                    
                    if p_pt > 0.5 and k_idx == target_create_slot:
                        guard_mask[b, k_idx, STATE_CREATED] += 100.0
                        guard_mask[b, k_idx, STATE_UNASSIGNED] -= 100.0
                    else:
                        guard_mask[b, k_idx, STATE_UNASSIGNED] += 100.0
                        guard_mask[b, k_idx, STATE_CREATED] -= 100.0
                        
                elif st == STATE_CREATED:
                    # Guard 2: CREATED transitions to ACTIVE (or SHIFTED if torso moves)
                    guard_mask[b, k_idx, STATE_UNASSIGNED] = -1e9
                    guard_mask[b, k_idx, STATE_CREATED] = -1e9
                    
                    if p_rel > 0.7:
                        guard_mask[b, k_idx, STATE_RELEASED] += 100.0
                    elif t_spd > self.shift_threshold:
                        guard_mask[b, k_idx, STATE_SHIFTED] += 100.0
                    else:
                        guard_mask[b, k_idx, STATE_ACTIVE] += 100.0
                        
                elif st == STATE_ACTIVE:
                    # Guard 3: ACTIVE can transition to SHIFTED, RELEASED, or remain ACTIVE
                    guard_mask[b, k_idx, STATE_UNASSIGNED] = -1e9
                    guard_mask[b, k_idx, STATE_CREATED] = -1e9
                    
                    if p_rel > 0.7:
                        guard_mask[b, k_idx, STATE_RELEASED] += 100.0
                    elif t_spd > self.shift_threshold:
                        guard_mask[b, k_idx, STATE_SHIFTED] += 100.0
                    else:
                        guard_mask[b, k_idx, STATE_ACTIVE] += 100.0
                        
                elif st == STATE_SHIFTED:
                    # Guard 4: SHIFTED can transition to ACTIVE, RELEASED, or remain SHIFTED
                    guard_mask[b, k_idx, STATE_UNASSIGNED] = -1e9
                    guard_mask[b, k_idx, STATE_CREATED] = -1e9
                    
                    if p_rel > 0.7:
                        guard_mask[b, k_idx, STATE_RELEASED] += 100.0
                    elif t_spd <= self.shift_threshold:
                        guard_mask[b, k_idx, STATE_ACTIVE] += 100.0
                    else:
                        guard_mask[b, k_idx, STATE_SHIFTED] += 100.0
                        
                elif st == STATE_RELEASED:
                    # Guard 5: RELEASED MUST transition to UNASSIGNED next frame
                    guard_mask[b, k_idx, STATE_CREATED] = -1e9
                    guard_mask[b, k_idx, STATE_ACTIVE] = -1e9
                    guard_mask[b, k_idx, STATE_SHIFTED] = -1e9
                    guard_mask[b, k_idx, STATE_RELEASED] = -1e9
                    guard_mask[b, k_idx, STATE_UNASSIGNED] += 100.0

        return logits + guard_mask

    def forward(
        self,
        obs: Dict[str, torch.Tensor],
        prev_state: Optional[Dict[str, torch.Tensor]] = None
    ) -> SLLSMOutput:
        """
        Executes one frame step of the SLL-SM core state machine.
        
        Args:
            obs: Dictionary containing frame observation tensors:
                - 'x_hand': (B, 3) chest-normalized 3D hand landmark position
                - 'p_torso': (B, 3) 3D torso chest center
                - 'dp_torso': (B, 3) 3D torso movement delta p_torso(t) - p_torso(t-1)
                - 'g_gaze': (B, 3) normalized 3D gaze unit vector
                - 'p_pointing': (B, 1) pointing gesture confidence scalar [0, 1]
                - 'p_release': (B, 1) release gesture confidence scalar [0, 1]
                - 'u_feat': (B, D) input modality semantic feature vector (optional)
                - 'target_entity': (B,) target entity slot index for CREATED binding (optional)
                
            prev_state: Optional state dictionary. If None, initialized via init_state().
            
        Returns:
            SLLSMOutput containing updated core representations and state tensors.
        """
        x_hand = obs['x_hand']  # (B, 3)
        B = x_hand.shape[0]
        device = x_hand.device
        
        # Initialize or unpack previous state
        if prev_state is None:
            prev_state = self.init_state(B, device)
            
        S_prev = prev_state['S']  # (B, K, 5)
        M_prev = prev_state['M']  # (B, K, 3)
        v_prev = prev_state['v']  # (B, K)
        E_prev = prev_state['E']  # (B, N, D)
        B_prev = prev_state['B']  # (B, N, K)
        
        dp_torso = obs.get('dp_torso', torch.zeros_like(x_hand))
        g_gaze = obs.get('g_gaze', torch.zeros_like(x_hand))
        p_pointing = obs.get('p_pointing', torch.zeros(B, 1, device=device))
        p_release = obs.get('p_release', torch.zeros(B, 1, device=device))
        u_feat = obs.get('u_feat', torch.zeros(B, self.D, device=device))
        target_entity = obs.get('target_entity', None)
        
        # ---------------------------------------------------------------------
        # STEP 1: Compute Per-Slot Transition Features (phi_j)
        # ---------------------------------------------------------------------
        hand_delta = x_hand.unsqueeze(1) - M_prev  # (B, K, 3)
        
        # Gaze alignment dot product
        M_norm = F.normalize(M_prev, p=2, dim=-1, eps=1e-5)  # (B, K, 3)
        gaze_dot = torch.sum(g_gaze.unsqueeze(1) * M_norm, dim=-1, keepdim=True)  # (B, K, 1)
        
        dp_torso_exp = dp_torso.unsqueeze(1).repeat(1, self.K, 1)    # (B, K, 3)
        pointing_exp = p_pointing.unsqueeze(1).repeat(1, self.K, 1)  # (B, K, 1)
        
        # Feature concatenation: phi ∈ R^(B × K × 13)
        phi = torch.cat([S_prev, hand_delta, dp_torso_exp, gaze_dot, pointing_exp], dim=-1)
        
        # Compute raw logits z_j ∈ R^(B × K × 5)
        logits = self.transition_mlp(phi)  # (B, K, 5)
        
        # ---------------------------------------------------------------------
        # STEP 2: Apply Deterministic FSM Transition Guards
        # ---------------------------------------------------------------------
        masked_logits = self._apply_fsm_guards(logits, S_prev, p_pointing, p_release, dp_torso)  # (B, K, 5)
        
        # ---------------------------------------------------------------------
        # STEP 3: Discrete State Selection Gating (S_new)
        # ---------------------------------------------------------------------
        if self.training and self.gate_type == "gumbel":
            S_new = F.gumbel_softmax(masked_logits, tau=self.tau, hard=True)  # (B, K, 5)
        elif self.training and self.gate_type == "ste":
            soft = F.softmax(masked_logits / self.tau, dim=-1)
            idx = torch.argmax(soft, dim=-1)
            hard = F.one_hot(idx, num_classes=NUM_STATES).float()
            S_new = hard - soft.detach() + soft  # (B, K, 5)
        else:
            selected_idx = torch.argmax(masked_logits, dim=-1)
            S_new = F.one_hot(selected_idx, num_classes=NUM_STATES).float()  # (B, K, 5)
            
        # ---------------------------------------------------------------------
        # STEP 4: State-Gated Continuous Coordinate Update Engine
        # ---------------------------------------------------------------------
        x_hand_exp = x_hand.unsqueeze(1).repeat(1, self.K, 1)  # (B, K, 3)
        shifted_M = M_prev + dp_torso_exp                    # (B, K, 3)
        zero_M = torch.zeros_like(M_prev)                    # (B, K, 3)
        
        s_unassigned = S_new[:, :, STATE_UNASSIGNED:STATE_UNASSIGNED+1]  # (B, K, 1)
        s_created    = S_new[:, :, STATE_CREATED:STATE_CREATED+1]        # (B, K, 1)
        s_active     = S_new[:, :, STATE_ACTIVE:STATE_ACTIVE+1]          # (B, K, 1)
        s_shifted    = S_new[:, :, STATE_SHIFTED:STATE_SHIFTED+1]        # (B, K, 1)
        s_released   = S_new[:, :, STATE_RELEASED:STATE_RELEASED+1]      # (B, K, 1)
        
        # State multiplexing equation for M_new
        M_new = (
            s_unassigned * zero_M +
            s_created    * x_hand_exp +
            s_active     * M_prev +
            s_shifted    * shifted_M +
            s_released   * M_prev
        )  # (B, K, 3)
        
        # Update Validity Mask v_new ∈ {0, 1}^K
        v_new = (s_created + s_active + s_shifted).squeeze(-1)  # (B, K)
        
        # ---------------------------------------------------------------------
        # STEP 5: Entity Memory & Bipartite Binding Matrix Update
        # ---------------------------------------------------------------------
        E_new = E_prev.clone()  # (B, N, D)
        B_new = B_prev.clone()  # (B, N, K)
        
        # Update semantic entity embeddings
        if target_entity is not None:
            for b in range(B):
                ent_idx = target_entity[b].item()
                if 0 <= ent_idx < self.N:
                    E_new[b, ent_idx] = F.layer_norm(E_prev[b, ent_idx] + self.W_u(u_feat[b]), (self.D,))
                    
                    # If slot entered STATE_CREATED, establish bipartite binding
                    created_slots = torch.where(S_new[b, :, STATE_CREATED] > 0.5)[0]
                    for slot_idx in created_slots:
                        B_new[b, :, slot_idx] = 0.0          # Clear other entity bindings for this slot
                        B_new[b, ent_idx, slot_idx] = 1.0     # Bind target entity to slot
                        
        # Clear bipartite binding for RELEASED slots (does NOT alter E_new!)
        for b in range(B):
            released_slots = torch.where(S_new[b, :, STATE_RELEASED] > 0.5)[0]
            for slot_idx in released_slots:
                B_new[b, :, slot_idx] = 0.0
                
        # ---------------------------------------------------------------------
        # STEP 6: Master Compiled Common Core State Q_t
        # ---------------------------------------------------------------------
        # Mask out invalid loci so [0, 0, 0] unassigned/released loci do not corrupt projection
        M_valid = M_new * v_new.unsqueeze(-1)  # (B, K, 3)
        
        # Bipartite projection from loci to entity referents: (B, N, K) @ (B, K, 3) -> (B, N, 3)
        L_proj = torch.bmm(B_new, M_valid)      # (B, N, 3)
        
        # Master core compile equation: Q_t ∈ R^(B × N × C)
        Q_t = self.layer_norm(self.W_e(E_new) + self.W_l(L_proj))  # (B, N, C)
        
        new_state_dict = {
            'S': S_new,
            'M': M_new,
            'v': v_new,
            'E': E_new,
            'B': B_new
        }
        
        return SLLSMOutput(
            Q=Q_t,
            M=M_new,
            v=v_new,
            S=S_new,
            B=B_new,
            E=E_new,
            M_valid=M_valid,
            state_dict=new_state_dict
        )
