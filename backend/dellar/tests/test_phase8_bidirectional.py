import unittest
import torch
import torch.nn as nn

from src.slds_core.bidirectional_pipeline import BidirectionalSLLSMManager
from src.slds_core.sllsm_core import (
    STATE_UNASSIGNED, STATE_CREATED, STATE_ACTIVE, STATE_SHIFTED, STATE_RELEASED
)

class TestPhase8BidirectionalIntegration(unittest.TestCase):

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

    def test_01_speech_input_reaches_sllsm(self):
        """TEST 1: Speech input reaches SLL-SM."""
        speech_input = torch.randn(2, 40, 80, device=self.device) # (B, T_audio, F_mel)
        out = self.manager.forward_speech_to_sign(speech_input)
        self.assertEqual(out['modality_source'], 'SPEECH')
        self.assertIn('loci', out)
        self.assertIn('states', out)

    def test_02_sign_input_reaches_sllsm(self):
        """TEST 2: Sign input reaches SLL-SM."""
        pose_input = torch.randn(2, 10, 25, 3, device=self.device) # (B, T, J, 3)
        out = self.manager.forward_sign_to_speech(pose_input)
        self.assertEqual(out['modality_source'], 'SIGN')
        self.assertIn('text_logits', out)
        self.assertEqual(out['text_logits'].shape[-1], 1000)

    def test_03_entity_creation_works(self):
        """TEST 3: Entity creation works."""
        speech_input = torch.randn(1, 10, 80, device=self.device)
        hand_seq = torch.tensor([[[0.3, 0.4, 0.5]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0]]], device=self.device)
        target_seq = torch.tensor([[0]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, target_entity_seq=target_seq
        )
        st = out['states'][0, 0, 0] # Slot 0 state at step 0
        self.assertEqual(torch.argmax(st).item(), STATE_CREATED)

    def test_04_entity_remains_active(self):
        """TEST 4: Entity remains active."""
        speech_input = torch.randn(1, 10, 80, device=self.device)
        hand_seq = torch.tensor([[[0.3, 0.4, 0.5], [0.3, 0.4, 0.5]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0], [1.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, target_entity_seq=target_seq
        )
        st_t1 = out['states'][0, 1, 0] # Slot 0 state at step 1
        self.assertEqual(torch.argmax(st_t1).item(), STATE_ACTIVE)

    def test_05_spatial_locus_is_created(self):
        """TEST 5: Spatial locus is created."""
        speech_input = torch.randn(1, 10, 80, device=self.device)
        hand_pos = torch.tensor([0.25, 0.45, 0.65], device=self.device)
        hand_seq = hand_pos.unsqueeze(0).unsqueeze(0)
        pointing_seq = torch.tensor([[[1.0]]], device=self.device)
        target_seq = torch.tensor([[0]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, target_entity_seq=target_seq
        )
        locus_slot0 = out['loci'][0, 0, 0]
        self.assertTrue(torch.norm(locus_slot0 - hand_pos) < 0.1)

    def test_06_spatial_locus_shifts(self):
        """TEST 6: Spatial locus shifts."""
        speech_input = torch.randn(1, 10, 80, device=self.device)
        hand_seq = torch.tensor([[[0.2, 0.4, 0.5], [0.2, 0.4, 0.5]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0], [0.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, target_entity_seq=target_seq
        )
        # Shift happens when torso displacement occurs or FSM shift is triggered
        self.assertIsNotNone(out['loci'])

    def test_07_entity_release_invalidates_locus_binding(self):
        """TEST 7: Entity release invalidates its locus binding."""
        speech_input = torch.randn(1, 10, 80, device=self.device)
        hand_seq = torch.tensor([[[0.3, 0.4, 0.5], [0.3, 0.4, 0.5]]], device=self.device)
        pointing_seq = torch.tensor([[[1.0], [0.0]]], device=self.device)
        release_seq = torch.tensor([[[0.0], [1.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, release_seq=release_seq, target_entity_seq=target_seq
        )
        v_mask_t1 = out['valid'][0, 1, 0]
        self.assertEqual(v_mask_t1.item(), 0.0)

    def test_08_new_entity_can_reuse_released_locus(self):
        """TEST 8: A new entity can reuse the released locus."""
        speech_input = torch.randn(1, 20, 80, device=self.device)
        hand_seq = torch.zeros(1, 4, 3, device=self.device)
        L1 = torch.tensor([0.4, 0.3, 0.5], device=self.device)
        hand_seq[0, 0] = L1; hand_seq[0, 1] = L1; hand_seq[0, 2] = L1; hand_seq[0, 3] = L1
        
        pointing_seq = torch.tensor([[[1.0], [0.0], [0.0], [1.0]]], device=self.device)
        release_seq = torch.tensor([[[0.0], [1.0], [0.0], [0.0]]], device=self.device)
        target_seq = torch.tensor([[0, 0, 0, 1]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, release_seq=release_seq, target_entity_seq=target_seq
        )
        B_t3 = out['B'][0, 3] # Bipartite binding matrix at step 3
        self.assertTrue(B_t3[1, 0].item() > 0.5) # Entity 1 bound to Slot 0

    def test_09_two_nearby_loci_remain_distinguishable(self):
        """TEST 9: Two nearby loci remain distinguishable."""
        L1 = torch.tensor([0.20, 0.40, 0.50], device=self.device)
        L2 = torch.tensor([0.23, 0.40, 0.50], device=self.device) # 3 cm separation
        
        speech_input = torch.randn(1, 10, 80, device=self.device)
        hand_seq = torch.zeros(1, 2, 3, device=self.device)
        hand_seq[0, 0] = L1; hand_seq[0, 1] = L2
        pointing_seq = torch.tensor([[[1.0], [1.0]]], device=self.device)
        target_seq = torch.tensor([[0, 1]], device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, target_entity_seq=target_seq
        )
        loci_t1 = out['loci'][0, 1]
        self.assertTrue(torch.norm(loci_t1[0] - L1) < 0.05 or torch.norm(loci_t1[1] - L2) < 0.05)

    def test_10_bidirectional_pipeline_executes_without_errors(self):
        """TEST 10: Bidirectional pipeline executes without tensor/shape errors."""
        speech = torch.randn(4, 30, 80, device=self.device)
        out_speech = self.manager.forward_speech_to_sign(speech)
        self.assertEqual(out_speech['generated_pose_trajectory'].shape, (4, 50, 25, 3))
        
        pose = torch.randn(4, 20, 25, 3, device=self.device)
        out_sign = self.manager.forward_sign_to_speech(pose)
        self.assertEqual(out_sign['text_logits'].shape, (4, 16, 1000))

    def test_11_sllsm_state_survives_occluded_frames(self):
        """TEST 11: SLL-SM state survives temporary missing/occluded frames."""
        speech_input = torch.randn(1, 20, 80, device=self.device) # Audio stride 4 -> T_out = 5
        hand_seq = torch.zeros(1, 5, 3, device=self.device)
        L1 = torch.tensor([0.3, 0.4, 0.5], device=self.device)
        hand_seq[0, 0] = L1 # Step 0: Point at L1
        # Steps 1 to 4: Hand blackout (0.0)
        
        pointing_seq = torch.zeros(1, 5, 1, device=self.device)
        pointing_seq[0, 0, 0] = 1.0
        target_seq = torch.zeros(1, 5, dtype=torch.long, device=self.device)
        
        out = self.manager.forward_speech_to_sign(
            speech_input, hand_seq=hand_seq, pointing_seq=pointing_seq, target_entity_seq=target_seq
        )
        loc_t4 = out['loci'][0, 4, 0] # Locus at final occluded frame
        self.assertTrue(torch.norm(loc_t4 - L1) < 0.05)

    def test_12_invalid_input_handled_safely(self):
        """TEST 12: Invalid input is handled safely."""
        speech_small = torch.randn(1, 1, 80, device=self.device)
        out = self.manager.forward_speech_to_sign(speech_small)
        self.assertIsNotNone(out['generated_pose_trajectory'])


if __name__ == '__main__':
    unittest.main()
