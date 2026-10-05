import torch
import unittest
import sys
from pathlib import Path

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from slds_core.sllsm_core import (
    SLLSMCore,
    STATE_UNASSIGNED,
    STATE_CREATED,
    STATE_ACTIVE,
    STATE_SHIFTED,
    STATE_RELEASED
)


class TestSLLSMCore(unittest.TestCase):
    def setUp(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.core = SLLSMCore(num_slots=4, num_entities=16, embed_dim=256, core_dim=512).to(self.device)
        self.core.eval()

    def test_1_initialization(self):
        """TEST 1 — Initialization & tensor shape checks."""
        init_state = self.core.init_state(batch_size=2, device=self.device)
        
        self.assertEqual(init_state['S'].shape, (2, 4, 5))
        self.assertEqual(init_state['M'].shape, (2, 4, 3))
        self.assertEqual(init_state['v'].shape, (2, 4))
        self.assertEqual(init_state['E'].shape, (2, 16, 256))
        self.assertEqual(init_state['B'].shape, (2, 16, 4))
        
        # All slots should be UNASSIGNED (class 0 = 1.0)
        self.assertTrue(torch.all(init_state['S'][:, :, STATE_UNASSIGNED] == 1.0))
        self.assertTrue(torch.all(init_state['v'] == 0.0))

    def test_2_create(self):
        """TEST 2 — Create: Verify CREATED state, coordinate initialization, and binding establishment."""
        init_state = self.core.init_state(batch_size=1, device=self.device)
        
        # Target creation at slot 0 with pointing gesture
        obs = {
            'x_hand': torch.tensor([[0.5, 0.2, -0.3]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.5, 0.2, -0.3]], device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': torch.randn(1, 256, device=self.device),
            'target_entity': torch.tensor([0], device=self.device)
        }
        
        out = self.core(obs, init_state)
        
        # Verify slot 0 state is CREATED (one-hot index 1)
        self.assertEqual(out.S[0, 0, STATE_CREATED].item(), 1.0)
        self.assertEqual(out.v[0, 0].item(), 1.0)
        
        # Verify locus coordinate matches hand position
        torch.testing.assert_close(out.M[0, 0], obs['x_hand'][0])
        
        # Verify binding established between Entity 0 and Slot 0
        self.assertEqual(out.B[0, 0, 0].item(), 1.0)
        self.assertEqual(out.B[0, 1, 0].item(), 0.0)

    def test_3_active(self):
        """TEST 3 — Active: Verify ACTIVE locus retains coordinate across frames."""
        init_state = self.core.init_state(batch_size=1, device=self.device)
        
        # Frame 1: Create slot 0
        obs1 = {
            'x_hand': torch.tensor([[0.4, 0.1, -0.2]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.4, 0.1, -0.2]], device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': torch.randn(1, 256, device=self.device),
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, init_state)
        
        # Frame 2: Hand moves away, no pointing, no release, no torso shift -> ACTIVE
        obs2 = {
            'x_hand': torch.tensor([[0.8, 0.9, 0.5]], device=self.device),  # Hand moved
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.4, 0.1, -0.2]], device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': torch.randn(1, 256, device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)
        
        # State should transition CREATED -> ACTIVE (index 2)
        self.assertEqual(out2.S[0, 0, STATE_ACTIVE].item(), 1.0)
        self.assertEqual(out2.v[0, 0].item(), 1.0)
        
        # Locus coordinate MUST remain at established position [0.4, 0.1, -0.2], NOT new hand position!
        torch.testing.assert_close(out2.M[0, 0], torch.tensor([0.4, 0.1, -0.2], device=self.device))

    def test_4_shift(self):
        """TEST 4 — Shift: Verify SHIFTED updates locus according to torso displacement."""
        init_state = self.core.init_state(batch_size=1, device=self.device)
        
        # Step 1: Create
        obs1 = {
            'x_hand': torch.tensor([[0.3, 0.0, 0.0]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, init_state)
        
        # Step 2: Transition to ACTIVE
        obs2 = {
            'x_hand': torch.tensor([[0.3, 0.0, 0.0]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)
        
        # Step 3: Torso leans right (dp_torso = [0.15, 0.0, 0.0])
        obs3 = {
            'x_hand': torch.tensor([[0.3, 0.0, 0.0]], device=self.device),
            'p_torso': torch.tensor([[0.15, 0.0, 0.0]], device=self.device),
            'dp_torso': torch.tensor([[0.15, 0.0, 0.0]], device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out3 = self.core(obs3, out2.state_dict)
        
        # Slot 0 should be SHIFTED (index 3)
        self.assertEqual(out3.S[0, 0, STATE_SHIFTED].item(), 1.0)
        self.assertEqual(out3.v[0, 0].item(), 1.0)
        
        # Shifted coordinate must equal original (0.3) + torso delta (0.15) = 0.45
        expected_coord = torch.tensor([0.45, 0.0, 0.0], device=self.device)
        torch.testing.assert_close(out3.M[0, 0], expected_coord)

    def test_5_release(self):
        """TEST 5 — Release: Verify releasing slot clears validity & binding while preserving Entity A embedding."""
        init_state = self.core.init_state(batch_size=1, device=self.device)
        
        # Step 1: Create Entity 0 at Slot 0
        u_feat_A = torch.full((1, 256), 2.5, device=self.device)
        obs1 = {
            'x_hand': torch.tensor([[0.5, 0.5, 0.5]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': u_feat_A,
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, init_state)
        entity_A_embed_before = out1.E[0, 0].clone()
        
        # Step 2: Transition to ACTIVE
        obs2 = {
            'x_hand': torch.tensor([[0.5, 0.5, 0.5]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)
        
        # Step 3: Trigger RELEASE gesture (p_release = 1.0)
        obs3 = {
            'x_hand': torch.tensor([[0.5, 0.5, 0.5]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[1.0]], device=self.device)  # Open palm release
        }
        out3 = self.core(obs3, out2.state_dict)
        
        # CRITICAL VERIFICATIONS FOR RELEASE:
        # 1. State is RELEASED
        self.assertEqual(out3.S[0, 0, STATE_RELEASED].item(), 1.0)
        # 2. Validity flag v[0] == 0
        self.assertEqual(out3.v[0, 0].item(), 0.0)
        # 3. Binding B[0, 0] == 0
        self.assertEqual(out3.B[0, 0, 0].item(), 0.0)
        # 4. Entity A embedding E[0] MUST REMAIN UNCHANGED
        torch.testing.assert_close(out3.E[0, 0], entity_A_embed_before)
        # 5. Masked locus M_valid[0, 0] must be zeros
        torch.testing.assert_close(out3.M_valid[0, 0], torch.zeros(3, device=self.device))

    def test_6_locus_reuse(self):
        """TEST 6 — Locus reuse: Verify reusing physical slot 0 for Entity B preserves Entity A memory."""
        init_state = self.core.init_state(batch_size=1, device=self.device)
        
        # Step 1: Create Entity A (index 0) at Slot 0
        u_A = torch.full((1, 256), 1.0, device=self.device)
        obs1 = {
            'x_hand': torch.tensor([[0.2, 0.2, 0.2]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': u_A,
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, init_state)
        embed_A_saved = out1.E[0, 0].clone()
        
        # Step 2: Release Slot 0
        obs2 = {
            'x_hand': torch.tensor([[0.2, 0.2, 0.2]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[1.0]], device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)
        
        # Step 3: Transition RELEASED -> UNASSIGNED
        obs3 = {
            'x_hand': torch.tensor([[0.2, 0.2, 0.2]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out3 = self.core(obs3, out2.state_dict)
        self.assertEqual(out3.S[0, 0, STATE_UNASSIGNED].item(), 1.0)
        
        # Step 4: Reuse same physical Slot 0 for Entity B (index 1)
        u_B = torch.full((1, 256), 8.0, device=self.device)
        obs4 = {
            'x_hand': torch.tensor([[0.2, 0.2, 0.2]], device=self.device),  # Same physical location!
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': u_B,
            'target_entity': torch.tensor([1], device=self.device)
        }
        out4 = self.core(obs4, out3.state_dict)
        
        # CRITICAL VERIFICATIONS FOR LOCUS REUSE:
        # 1. Slot 0 bound to Entity B (1)
        self.assertEqual(out4.B[0, 1, 0].item(), 1.0)
        # 2. Slot 0 binding to Entity A (0) is CLEARED (0.0)
        self.assertEqual(out4.B[0, 0, 0].item(), 0.0)
        # 3. Entity A embedding E[0] MUST REMAIN PRESERVED
        torch.testing.assert_close(out4.E[0, 0], embed_A_saved)
        # 4. Entity B embedding E[1] is separate and updated
        self.assertFalse(torch.equal(out4.E[0, 1], out4.E[0, 0]))

    def test_7_invalid_locus_protection(self):
        """TEST 7 — Invalid locus protection: Unassigned/released loci have M_valid == 0."""
        init_state = self.core.init_state(batch_size=1, device=self.device)
        
        obs = {
            'x_hand': torch.tensor([[0.9, 0.9, 0.9]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out = self.core(obs, init_state)
        
        # All slots are UNASSIGNED, so M_valid must be all zeros
        torch.testing.assert_close(out.M_valid, torch.zeros(1, 4, 3, device=self.device))
        self.assertTrue(torch.all(out.v == 0.0))

    def test_8_shape_validation(self):
        """TEST 8 — Shape validation for all output tensors."""
        init_state = self.core.init_state(batch_size=3, device=self.device)
        obs = {
            'x_hand': torch.randn(3, 3, device=self.device),
            'p_torso': torch.randn(3, 3, device=self.device),
            'dp_torso': torch.randn(3, 3, device=self.device),
            'g_gaze': torch.randn(3, 3, device=self.device),
            'p_pointing': torch.zeros(3, 1, device=self.device),
            'p_release': torch.zeros(3, 1, device=self.device),
            'u_feat': torch.randn(3, 256, device=self.device)
        }
        out = self.core(obs, init_state)
        
        self.assertEqual(out.Q.shape, (3, 16, 512))
        self.assertEqual(out.M.shape, (3, 4, 3))
        self.assertEqual(out.v.shape, (3, 4))
        self.assertEqual(out.S.shape, (3, 4, 5))
        self.assertEqual(out.B.shape, (3, 16, 4))
        self.assertEqual(out.E.shape, (3, 16, 256))
        self.assertEqual(out.M_valid.shape, (3, 4, 3))

    def test_9_forward_pass(self):
        """TEST 9 — Forward pass sanity check: Verify no NaN or Inf in outputs."""
        init_state = self.core.init_state(batch_size=4, device=self.device)
        obs = {
            'x_hand': torch.randn(4, 3, device=self.device),
            'p_torso': torch.randn(4, 3, device=self.device),
            'dp_torso': torch.randn(4, 3, device=self.device),
            'g_gaze': torch.randn(4, 3, device=self.device),
            'p_pointing': torch.rand(4, 1, device=self.device),
            'p_release': torch.rand(4, 1, device=self.device),
            'u_feat': torch.randn(4, 256, device=self.device)
        }
        out = self.core(obs, init_state)
        
        self.assertFalse(torch.isnan(out.Q).any())
        self.assertFalse(torch.isinf(out.Q).any())
        self.assertFalse(torch.isnan(out.M).any())
        self.assertFalse(torch.isnan(out.B).any())
        self.assertFalse(torch.isnan(out.E).any())


if __name__ == "__main__":
    unittest.main()
