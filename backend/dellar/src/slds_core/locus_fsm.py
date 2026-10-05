import torch
import torch.nn as nn
import torch.nn.functional as F

# State Definitions
STATE_UNASSIGNED = 0
STATE_CREATED    = 1
STATE_ACTIVE     = 2
STATE_SHIFTED    = 3
STATE_RELEASED   = 4
NUM_STATES       = 5

class BaselineTracker(nn.Module):
    """
    SYSTEM A: Baseline Spatial Tracker
    Direct mapping from observation keypoints to 3D locus prediction.
    No lifecycle state and no persistent memory.
    """
    def __init__(self, max_slots=4):
        super().__init__()
        self.max_slots = max_slots
        self.mlp = nn.Sequential(
            nn.Linear(10, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, max_slots * 3 + max_slots)
        )

    def forward(self, obs_t):
        B = obs_t.shape[0]
        out = self.mlp(obs_t)
        locus_preds = out[:, :self.max_slots * 3].view(B, self.max_slots, 3)
        entity_logits = out[:, self.max_slots * 3:]
        return locus_preds, entity_logits


class TrackerWithMemory(nn.Module):
    """
    SYSTEM B: Spatial Tracker + Persistent Vector Memory
    Uses a recurrent GRU cell to maintain continuous latent state.
    No explicit discrete lifecycle FSM states.
    """
    def __init__(self, max_slots=4, hidden_dim=128):
        super().__init__()
        self.max_slots = max_slots
        self.hidden_dim = hidden_dim
        
        self.encoder = nn.Sequential(
            nn.Linear(10, 64),
            nn.ReLU()
        )
        self.gru = nn.GRUCell(64, hidden_dim)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, max_slots * 3 + max_slots)
        )

    def forward(self, obs_t, h_prev=None):
        B = obs_t.shape[0]
        if h_prev is None:
            h_prev = torch.zeros(B, self.hidden_dim, device=obs_t.device)
            
        feat = self.encoder(obs_t)
        h_new = self.gru(feat, h_prev)
        out = self.head(h_new)
        
        locus_preds = out[:, :self.max_slots * 3].view(B, self.max_slots, 3)
        entity_logits = out[:, self.max_slots * 3:]
        return locus_preds, entity_logits, h_new


class SpatialLocusLifecycleFSM(nn.Module):
    """
    SYSTEM C: Spatial-Locus Lifecycle State Machine (SLL-SM)
    Implements discrete-continuous state gating over 5 lifecycle states:
    UNASSIGNED (0), CREATED (1), ACTIVE (2), SHIFTED (3), RELEASED (4).
    """
    def __init__(
        self,
        max_slots=4,
        gate_type="gumbel",
        tau=1.0,
        disable_released=False,
        disable_shifted=False,
        disable_constraints=False,
        disable_memory=False
    ):
        super().__init__()
        self.max_slots = max_slots
        self.gate_type = gate_type
        self.tau = tau
        self.disable_released = disable_released
        self.disable_shifted = disable_shifted
        self.disable_constraints = disable_constraints
        self.disable_memory = disable_memory
        
        # Transition Network
        self.transition_net = nn.Sequential(
            nn.Linear(15, 64),
            nn.ReLU(),
            nn.Linear(64, NUM_STATES)
        )

    def compute_state_gate(self, logits):
        if self.disable_released:
            logits = logits.clone()
            logits[:, :, STATE_RELEASED] = -1e9
        if self.disable_shifted:
            logits = logits.clone()
            logits[:, :, STATE_SHIFTED] = -1e9
            
        if self.gate_type == "gumbel" and self.training:
            return F.gumbel_softmax(logits, tau=self.tau, hard=True)
        elif self.gate_type == "ste":
            soft = F.softmax(logits / self.tau, dim=-1)
            idx = torch.argmax(soft, dim=-1)
            hard = F.one_hot(idx, num_classes=NUM_STATES).float()
            return hard - soft.detach() + soft
        else:
            idx = torch.argmax(logits, dim=-1)
            return F.one_hot(idx, num_classes=NUM_STATES).float()

    def forward(self, obs_t, prev_loci=None, prev_states=None, prev_torso=None):
        B = obs_t.shape[0]
        device = obs_t.device
        
        hand_pos = obs_t[:, :3]
        torso_pos = obs_t[:, 3:6]
        gaze = obs_t[:, 6:9]
        pointing = obs_t[:, 9:10]
        
        if prev_loci is None or self.disable_memory:
            prev_loci = torch.zeros(B, self.max_slots, 3, device=device)
        if prev_states is None or self.disable_memory:
            prev_states = torch.zeros(B, self.max_slots, NUM_STATES, device=device)
            prev_states[:, :, STATE_UNASSIGNED] = 1.0
        if prev_torso is None or self.disable_memory:
            prev_torso = torso_pos.clone()
            
        torso_delta = torso_pos - prev_torso
        hand_delta = hand_pos.unsqueeze(1) - prev_loci
        
        slot_inputs = torch.cat([
            prev_states,
            hand_delta,
            torso_delta.unsqueeze(1).repeat(1, self.max_slots, 1),
            gaze.unsqueeze(1).repeat(1, self.max_slots, 1),
            pointing.unsqueeze(1).repeat(1, self.max_slots, 1)
        ], dim=-1)
        
        transition_logits = self.transition_net(slot_inputs)
        
        # Vectorized constraint masking
        if not self.disable_constraints:
            curr_state_idx = torch.argmax(prev_states, dim=-1) # (B, M)
            is_unassigned = (curr_state_idx == STATE_UNASSIGNED).unsqueeze(-1) # (B, M, 1)
            is_released   = (curr_state_idx == STATE_RELEASED).unsqueeze(-1)   # (B, M, 1)
            
            mask = torch.zeros_like(transition_logits)
            mask[:, :, STATE_ACTIVE]   += (is_unassigned | is_released).squeeze(-1) * -1e9
            mask[:, :, STATE_SHIFTED]  += (is_unassigned | is_released).squeeze(-1) * -1e9
            mask[:, :, STATE_RELEASED] += is_unassigned.squeeze(-1) * -1e9
            
            transition_logits = transition_logits + mask

        state_gates = self.compute_state_gate(transition_logits)
        
        hand_pos_expanded = hand_pos.unsqueeze(1).repeat(1, self.max_slots, 1)
        torso_shifted_loci = prev_loci + torso_delta.unsqueeze(1)
        zero_loci = torch.zeros_like(prev_loci)
        
        new_loci = (
            state_gates[:, :, STATE_UNASSIGNED:STATE_UNASSIGNED+1] * zero_loci +
            state_gates[:, :, STATE_CREATED:STATE_CREATED+1]       * hand_pos_expanded +
            state_gates[:, :, STATE_ACTIVE:STATE_ACTIVE+1]         * prev_loci +
            state_gates[:, :, STATE_SHIFTED:STATE_SHIFTED+1]       * torso_shifted_loci +
            state_gates[:, :, STATE_RELEASED:STATE_RELEASED+1]     * zero_loci
        )
        
        entity_logits = torch.bmm(state_gates, state_gates.transpose(1, 2))
        return new_loci, state_gates, entity_logits
