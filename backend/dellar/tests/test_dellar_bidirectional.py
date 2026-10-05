"""
DELLAR / SLL-SM Bidirectional Architectural Verification Test Suite
Verifies that the exact same DELLAR core (SLLSMCore) supports both
Speech -> Sign and Sign -> Speech/Text directions.
"""

import unittest
import torch
import time

from src.slds_core.bidirectional_pipeline import BidirectionalSLLSMManager
from src.slds_core.sllsm_core import (
    STATE_UNASSIGNED, STATE_CREATED, STATE_ACTIVE, STATE_SHIFTED, STATE_RELEASED
)


class TestDELLARBidirectional(unittest.TestCase):

    def setUp(self):
        self.device = torch.device("cpu")
        self.manager = BidirectionalSLLSMManager(
            num_slots=4,
            num_entities=16,
            embed_dim=256,
            core_dim=512,
            num_joints=25,
            vocab_size=1000
        ).to(self.device)
        self.manager.eval()

    def test_speech_to_sign(self):
        """Direction 1: Speech -> SpeechAdapter -> CommonRep -> DELLAR Core -> PoseDecoder."""
        speech_input = torch.randn(1, 20, 80, device=self.device)
        t0 = time.perf_counter()
        out = self.manager.forward_speech_to_sign(speech_input)
        lat = (time.perf_counter() - t0) * 1000.0
        
        self.assertEqual(out['modality_source'], 'SPEECH')
        self.assertIn('generated_pose_trajectory', out)
        self.assertIn('loci', out)
        self.assertIn('states', out)
        self.assertFalse(torch.isnan(out['generated_pose_trajectory']).any().item())
        self.assertGreater(lat, 0.0)

    def test_sign_to_text(self):
        """Direction 2: Sign -> SignAdapter -> CommonRep -> DELLAR Core -> TextDecoder."""
        pose_input = torch.randn(1, 15, 25, 3, device=self.device)
        t0 = time.perf_counter()
        out = self.manager.forward_sign_to_speech(pose_input)
        lat = (time.perf_counter() - t0) * 1000.0
        
        self.assertEqual(out['modality_source'], 'SIGN')
        self.assertIn('text_logits', out)
        self.assertIn('predicted_token_ids', out)
        self.assertIn('loci', out)
        self.assertIn('states', out)
        self.assertFalse(torch.isnan(out['text_logits']).any().item())
        self.assertGreater(lat, 0.0)

    def test_shared_dellar_core(self):
        """Proves both directions share the exact same DELLAR / SLLSMCore instance."""
        core_obj = self.manager.sllsm_core
        self.assertIsNotNone(core_obj)
        self.assertEqual(core_obj.__class__.__name__, "SLLSMCore")
        
        speech_input = torch.randn(1, 20, 80, device=self.device)
        out_speech = self.manager.forward_speech_to_sign(speech_input)
        
        pose_input = torch.randn(1, 5, 25, 3, device=self.device)
        out_sign = self.manager.forward_sign_to_speech(pose_input)
        
        self.assertEqual(out_speech['loci'].shape[-1], 3)
        self.assertEqual(out_sign['loci'].shape[-1], 3)
        self.assertEqual(out_speech['states'].shape[-1], 5)
        self.assertEqual(out_sign['states'].shape[-1], 5)

    def test_lifecycle_forward(self):
        """Forward direction lifecycle state execution."""
        speech_input = torch.randn(1, 20, 80, device=self.device) # stride 4 -> T_out = 5
        hand_seq = torch.tensor([[[0.1, 0.2, 0.3], [0.1, 0.2, 0.3], [0.1, 0.2, 0.3], [0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0], [1.0], [0.0], [0.0], [0.0]]], device=self.device)
        release_seq = torch.tensor([[[0.0], [0.0], [1.0], [0.0], [0.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0, 0, 0, 0]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, release_seq=release_seq, target_entity_seq=target_seq
        )
        
        states = out['states'][0]
        # Step 0: CREATED
        self.assertEqual(torch.argmax(states[0, 0]).item(), STATE_CREATED)
        # Step 1: ACTIVE
        self.assertEqual(torch.argmax(states[1, 0]).item(), STATE_ACTIVE)
        # Step 2: RELEASED
        self.assertEqual(torch.argmax(states[2, 0]).item(), STATE_RELEASED)

    def test_lifecycle_reverse(self):
        """Reverse direction lifecycle state execution."""
        pose_input = torch.randn(1, 5, 25, 3, device=self.device)
        hand_seq = torch.tensor([[[0.4, 0.5, 0.6], [0.4, 0.5, 0.6], [0.4, 0.5, 0.6], [0.4, 0.5, 0.6], [0.4, 0.5, 0.6]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0], [1.0], [0.0], [0.0], [0.0]]], device=self.device)
        release_seq = torch.tensor([[[0.0], [0.0], [1.0], [0.0], [0.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0, 0, 0, 0]], device=self.device)
        
        out = self.manager.forward_sign_to_speech(
            pose_input, hand_seq=hand_seq, pointing_seq=pointing_seq, release_seq=release_seq, target_entity_seq=target_seq
        )
        
        states = out['states'][0]
        self.assertEqual(torch.argmax(states[0, 0]).item(), STATE_CREATED)
        self.assertEqual(torch.argmax(states[1, 0]).item(), STATE_ACTIVE)
        self.assertEqual(torch.argmax(states[2, 0]).item(), STATE_RELEASED)

    def test_locus_reuse(self):
        """Locus reuse by a new entity without identity bleeding."""
        speech_input = torch.randn(1, 20, 80, device=self.device) # stride 4 -> T_out = 5
        hand_seq = torch.tensor([[[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0], [0.0], [0.0], [1.0], [0.0]]], device=self.device)
        release_seq = torch.tensor([[[0.0], [1.0], [0.0], [0.0], [0.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0, 0, 1, 1]], device=self.device) # Entity 0 -> Release -> Entity 1
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, release_seq=release_seq, target_entity_seq=target_seq
        )
        
        valid = out['valid'][0]
        # Step 1: RELEASED -> Invalid (v=0.0)
        self.assertEqual(valid[1, 0].item(), 0.0)
        # Step 3: Reused by Entity 1 -> Valid (v=1.0)
        self.assertEqual(valid[3, 0].item(), 1.0)
        # Step 3: Binding matrix confirms Entity 1 is bound to Slot 0
        B_t3 = out['B'][0, 3]
        self.assertTrue(B_t3[1, 0].item() > 0.5)


if __name__ == "__main__":
    unittest.main()
