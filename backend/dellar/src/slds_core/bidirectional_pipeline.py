import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple

from .sllsm_core import SLLSMCore, SLLSMOutput
from .speech_adapter import SpeechAdapter
from .sign_adapter import SignAdapter
from .decoders import PoseDecoder, TextDecoder
from .common_representation import CommonRepresentation


class BidirectionalSLLSMManager(nn.Module):
    """
    Phase 8 Production Bidirectional Pipeline Manager.
    Integrates SpeechAdapter and SignAdapter with the validated SLLSMCore central engine,
    supporting Mode 1 (Speech -> Sign) and Mode 2 (Sign -> Speech/Text).
    """
    def __init__(
        self,
        num_slots: int = 4,
        num_entities: int = 16,
        embed_dim: int = 256,
        core_dim: int = 512,
        num_joints: int = 25,
        vocab_size: int = 1000
    ):
        super().__init__()
        self.num_slots = num_slots
        self.num_entities = num_entities
        self.embed_dim = embed_dim
        
        # Central Validated SLL-SM Core Mechanism
        self.sllsm_core = SLLSMCore(
            num_slots=num_slots,
            num_entities=num_entities,
            embed_dim=embed_dim,
            core_dim=core_dim
        )
        
        # Modality Adapters
        self.speech_adapter = SpeechAdapter(in_channels=80, out_dim=embed_dim)
        self.sign_adapter = SignAdapter(num_joints=num_joints, out_dim=embed_dim)
        
        # Modality Decoders
        self.pose_decoder = PoseDecoder(in_dim=core_dim, num_joints=num_joints, max_len=50)
        self.text_decoder = TextDecoder(in_dim=core_dim, vocab_size=vocab_size)

    def forward_speech_to_sign(
        self,
        speech_input: torch.Tensor,                # (B, T_audio, 80) or (B, 80, T_audio)
        hand_seq: Optional[torch.Tensor] = None,     # (B, T, 3) optional hand positions
        pointing_seq: Optional[torch.Tensor] = None, # (B, T, 1) optional pointing flags
        release_seq: Optional[torch.Tensor] = None,  # (B, T, 1) optional release flags
        gaze_seq: Optional[torch.Tensor] = None,     # (B, T, 3) optional gaze vectors
        target_entity_seq: Optional[torch.Tensor] = None # (B, T) optional target entities
    ) -> Dict[str, Any]:
        """
        MODE 1: Speech -> Language/Semantic Representation -> SLL-SM -> 3D Sign Pose Output
        """
        device = speech_input.device
        u_seq = self.speech_adapter(speech_input) # (B, T_out, D)
        B, T, _ = u_seq.shape
        
        state = self.sllsm_core.init_state(B, device)
        
        loci_steps = []
        valid_steps = []
        state_steps = []
        Q_steps = []
        B_steps = []
        
        prev_torso = torch.zeros(B, 3, device=device)
        
        for t in range(T):
            u_t = u_seq[:, t]
            x_h = hand_seq[:, t] if (hand_seq is not None and t < hand_seq.shape[1]) else torch.zeros(B, 3, device=device)
            p_pt = pointing_seq[:, t] if (pointing_seq is not None and t < pointing_seq.shape[1]) else torch.zeros(B, 1, device=device)
            p_rel = release_seq[:, t] if (release_seq is not None and t < release_seq.shape[1]) else torch.zeros(B, 1, device=device)
            g_gz = gaze_seq[:, t] if (gaze_seq is not None and t < gaze_seq.shape[1]) else torch.tensor([[0.0, 0.0, 1.0]], device=device).expand(B, 3)
            tgt_ent = target_entity_seq[:, t] if (target_entity_seq is not None and t < target_entity_seq.shape[1]) else None
            
            common_rep = CommonRepresentation(
                u_feat=u_t,
                x_hand=x_h,
                p_torso=prev_torso,
                g_gaze=g_gz,
                p_pointing=p_pt,
                p_release=p_rel,
                target_entity=tgt_ent,
                modality_source="SPEECH"
            )
            
            out: SLLSMOutput = self.sllsm_core(common_rep.to_obs_frame(), state)
            state = out.state_dict
            
            loci_steps.append(out.M_valid)
            valid_steps.append(out.v)
            state_steps.append(out.S)
            Q_steps.append(out.Q)
            B_steps.append(out.B)
            
        stacked_Q = torch.stack(Q_steps, dim=1) # (B, T, N, C)
        stacked_M = torch.stack(loci_steps, dim=1) # (B, T, K, 3)
        
        # Decode into 3D skeletal pose trajectory
        latest_Q = Q_steps[-1] # (B, N, C)
        latest_M = loci_steps[-1] # (B, K, 3)
        generated_pose_traj = self.pose_decoder(latest_Q, latest_M) # (B, 50, 25, 3)
        
        return {
            'modality_source': 'SPEECH',
            'generated_pose_trajectory': generated_pose_traj,
            'loci': stacked_M,
            'valid': torch.stack(valid_steps, dim=1),
            'states': torch.stack(state_steps, dim=1),
            'Q': stacked_Q,
            'B': torch.stack(B_steps, dim=1),
            'final_state': state
        }

    def forward_sign_to_speech(
        self,
        pose_input: torch.Tensor,                  # (B, T, 25, 3) or (B, T, 75)
        hand_seq: Optional[torch.Tensor] = None,     # (B, T, 3) optional hand positions
        pointing_seq: Optional[torch.Tensor] = None, # (B, T, 1) optional pointing flags
        release_seq: Optional[torch.Tensor] = None,  # (B, T, 1) optional release flags
        gaze_seq: Optional[torch.Tensor] = None,     # (B, T, 3) optional gaze vectors
        target_entity_seq: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        """
        MODE 2: Sign/Pose -> Spatial/Temporal Representation -> SLL-SM -> Text/Speech Output
        """
        device = pose_input.device
        u_seq = self.sign_adapter(pose_input) # (B, T, D)
        B, T, _ = u_seq.shape
        
        state = self.sllsm_core.init_state(B, device)
        
        loci_steps = []
        valid_steps = []
        state_steps = []
        Q_steps = []
        B_steps = []
        
        prev_torso = torch.zeros(B, 3, device=device)
        
        for t in range(T):
            u_t = u_seq[:, t]
            
            # Default hand position from pose keypoints if not explicitly passed
            if hand_seq is not None and t < hand_seq.shape[1]:
                x_h = hand_seq[:, t]
            elif pose_input.dim() == 4:
                x_h = pose_input[:, t, 7] # Use wrist/hand joint
            else:
                x_h = torch.zeros(B, 3, device=device)
                
            p_pt = pointing_seq[:, t] if (pointing_seq is not None and t < pointing_seq.shape[1]) else torch.zeros(B, 1, device=device)
            p_rel = release_seq[:, t] if (release_seq is not None and t < release_seq.shape[1]) else torch.zeros(B, 1, device=device)
            g_gz = gaze_seq[:, t] if (gaze_seq is not None and t < gaze_seq.shape[1]) else torch.tensor([[0.0, 0.0, 1.0]], device=device).expand(B, 3)
            tgt_ent = target_entity_seq[:, t] if (target_entity_seq is not None and t < target_entity_seq.shape[1]) else None
            
            common_rep = CommonRepresentation(
                u_feat=u_t,
                x_hand=x_h,
                p_torso=prev_torso,
                g_gaze=g_gz,
                p_pointing=p_pt,
                p_release=p_rel,
                target_entity=tgt_ent,
                modality_source="SIGN"
            )
            
            out: SLLSMOutput = self.sllsm_core(common_rep.to_obs_frame(), state)
            state = out.state_dict
            
            loci_steps.append(out.M_valid)
            valid_steps.append(out.v)
            state_steps.append(out.S)
            Q_steps.append(out.Q)
            B_steps.append(out.B)
            
        stacked_Q = torch.stack(Q_steps, dim=1) # (B, T, N, C)
        stacked_M = torch.stack(loci_steps, dim=1) # (B, T, K, 3)
        
        # Decode into subword text token logits
        latest_Q = Q_steps[-1] # (B, N, C)
        text_logits = self.text_decoder(latest_Q) # (B, N, V)
        pred_token_ids = torch.argmax(text_logits, dim=-1) # (B, N)
        
        return {
            'modality_source': 'SIGN',
            'text_logits': text_logits,
            'predicted_token_ids': pred_token_ids,
            'loci': stacked_M,
            'valid': torch.stack(valid_steps, dim=1),
            'states': torch.stack(state_steps, dim=1),
            'Q': stacked_Q,
            'B': torch.stack(B_steps, dim=1),
            'final_state': state
        }
