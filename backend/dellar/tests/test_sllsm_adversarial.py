import unittest
import torch

from src.slds_core.sllsm_core import (
    SLLSMCore,
    STATE_UNASSIGNED, STATE_CREATED, STATE_ACTIVE, STATE_SHIFTED, STATE_RELEASED
)

class TestSLLSMAdversarial(unittest.TestCase):
    """
    Phase 9 Adversarial Test Suite for SLLSMCore engine edge cases.
    """
    def setUp(self):
        self.device = torch.device("cpu")
        self.core = SLLSMCore(num_slots=4, num_entities=16, embed_dim=256, core_dim=512).to(self.device)
        self.core.eval()

    def test_01_entity_creation_edge_case(self):
        """Case 1: Entity creation under boundary pointing probability."""
        st = self.core.init_state(1, self.device)
        obs = {
            'x_hand': torch.tensor([[0.1, 0.2, 0.3]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.0, 0.0, 1.0]], device=self.device),
            'p_pointing': torch.tensor([[0.99]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': torch.randn(1, 256, device=self.device),
            'target_entity': torch.tensor([0], device=self.device)
        }
        out = self.core(obs, st)
        self.assertEqual(torch.argmax(out.S[0, 0]).item(), STATE_CREATED)
        self.assertEqual(out.v[0, 0].item(), 1.0)

    def test_02_entity_persistence_under_zero_pointing(self):
        """Case 2: Entity persistence when pointing drops to 0.0."""
        st = self.core.init_state(1, self.device)
        obs1 = {
            'x_hand': torch.tensor([[0.1, 0.2, 0.3]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.0, 0.0, 1.0]], device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, st)
        
        obs2 = {
            'x_hand': torch.tensor([[0.1, 0.2, 0.3]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.0, 0.0, 1.0]], device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)
        self.assertEqual(out2.v[0, 0].item(), 1.0) # Locus remains valid and active

    def test_03_entity_release_trigger(self):
        """Case 3: Entity release explicitly invalidates validity mask."""
        st = self.core.init_state(1, self.device)
        obs1 = {
            'x_hand': torch.tensor([[0.1, 0.2, 0.3]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.0, 0.0, 1.0]], device=self.device),
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, st)
        
        obs2 = {
            'x_hand': torch.tensor([[0.1, 0.2, 0.3]], device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.tensor([[0.0, 0.0, 1.0]], device=self.device),
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[1.0]], device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)
        self.assertEqual(torch.argmax(out2.S[0, 0]).item(), STATE_RELEASED)
        self.assertEqual(out2.v[0, 0].item(), 0.0)

    def test_04_same_locus_reuse(self):
        """Case 4: Same-locus binding reuse by new Entity B."""
        st = self.core.init_state(1, self.device)
        L1 = torch.tensor([[0.4, 0.3, 0.5]], device=self.device)
        
        # Step 1: Entity A created at L1
        obs1 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([0], device=self.device)}
        out1 = self.core(obs1, st)
        
        # Step 2: Entity A released (STATE_RELEASED)
        obs2 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[0.0]], device=self.device), 'p_release': torch.tensor([[1.0]], device=self.device)}
        out2 = self.core(obs2, out1.state_dict)
        
        # Step 3: Idle step (STATE_RELEASED -> STATE_UNASSIGNED)
        obs3 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[0.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device)}
        out3 = self.core(obs3, out2.state_dict)
        
        # Step 4: Entity B created at exact same locus L1 (STATE_UNASSIGNED -> STATE_CREATED)
        obs4 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([1], device=self.device)}
        out4 = self.core(obs4, out3.state_dict)
        self.assertTrue(out4.B[0, 1, 0].item() > 0.5)

    def test_05_two_nearby_loci_3cm(self):
        """Case 5: Sub-5cm loci (3cm distance)."""
        st = self.core.init_state(1, self.device)
        L1 = torch.tensor([[0.20, 0.40, 0.50]], device=self.device)
        L2 = torch.tensor([[0.23, 0.40, 0.50]], device=self.device)
        
        obs1 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([0], device=self.device)}
        out1 = self.core(obs1, st)
        
        obs2 = {'x_hand': L2, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L2, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([1], device=self.device)}
        out2 = self.core(obs2, out1.state_dict)
        self.assertTrue(out2.B[0, 0, 0].item() > 0.5)
        self.assertTrue(out2.B[0, 1, 1].item() > 0.5)

    def test_06_shifted_locus_torso_movement(self):
        """Case 6: Torso movement causes locus shift."""
        st = self.core.init_state(1, self.device)
        L1 = torch.tensor([[0.3, 0.4, 0.5]], device=self.device)
        obs1 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([0], device=self.device)}
        out1 = self.core(obs1, st)
        
        dp = torch.tensor([[0.1, 0.0, 0.0]], device=self.device)
        obs2 = {'x_hand': L1 + dp, 'p_torso': dp, 'dp_torso': dp,
                'g_gaze': L1, 'p_pointing': torch.tensor([[0.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device)}
        out2 = self.core(obs2, out1.state_dict)
        self.assertTrue(torch.norm(out2.M[0, 0] - (L1 + dp)) < 0.05)

    def test_07_temporary_occlusion(self):
        """Case 7: Hand blackout (0.0 coordinates)."""
        st = self.core.init_state(1, self.device)
        L1 = torch.tensor([[0.3, 0.4, 0.5]], device=self.device)
        obs1 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([0], device=self.device)}
        out1 = self.core(obs1, st)
        
        # Blackout frame
        obs2 = {'x_hand': torch.zeros(1,3,device=self.device), 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': torch.tensor([[0.0, 0.0, 1.0]], device=self.device), 'p_pointing': torch.tensor([[0.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device)}
        out2 = self.core(obs2, out1.state_dict)
        self.assertEqual(out2.v[0, 0].item(), 1.0)
        self.assertTrue(torch.norm(out2.M[0, 0] - L1) < 0.01)

    def test_08_multiple_entities_capacity(self):
        """Case 8: Creating 4 entities across 4 slots."""
        st = self.core.init_state(1, self.device)
        curr_st = st
        for k in range(4):
            L = torch.tensor([[0.1 * k, 0.4, 0.5]], device=self.device)
            obs = {'x_hand': L, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                   'g_gaze': L, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                   'target_entity': torch.tensor([k], device=self.device)}
            out = self.core(obs, curr_st)
            curr_st = out.state_dict
        self.assertEqual(out.v[0].sum().item(), 4.0)

    def test_09_invalid_released_locus(self):
        """Case 9: M_valid returns zero for released locus."""
        st = self.core.init_state(1, self.device)
        L1 = torch.tensor([[0.3, 0.4, 0.5]], device=self.device)
        obs1 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[1.0]], device=self.device), 'p_release': torch.tensor([[0.0]], device=self.device),
                'target_entity': torch.tensor([0], device=self.device)}
        out1 = self.core(obs1, st)
        
        obs2 = {'x_hand': L1, 'p_torso': torch.zeros(1,3,device=self.device), 'dp_torso': torch.zeros(1,3,device=self.device),
                'g_gaze': L1, 'p_pointing': torch.tensor([[0.0]], device=self.device), 'p_release': torch.tensor([[1.0]], device=self.device)}
        out2 = self.core(obs2, out1.state_dict)
        self.assertTrue(torch.all(out2.M_valid[0, 0] == 0.0))

    def test_10_empty_or_invalid_input_handling(self):
        """Case 10: Empty/zero observation input doesn't crash engine."""
        st = self.core.init_state(1, self.device)
        obs_empty = {
            'x_hand': torch.zeros(1, 3, device=self.device),
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': torch.zeros(1, 3, device=self.device),
            'p_pointing': torch.zeros(1, 1, device=self.device),
            'p_release': torch.zeros(1, 1, device=self.device)
        }
        out = self.core(obs_empty, st)
        self.assertIsNotNone(out.Q)
        self.assertEqual(out.Q.shape, (1, 16, 512))


if __name__ == '__main__':
    unittest.main()
