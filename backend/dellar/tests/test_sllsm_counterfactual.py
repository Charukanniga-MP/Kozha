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
    STATE_RELEASED
)


class TestSLLSMCounterfactual(unittest.TestCase):
    """
    Counterfactual Sensitivity Test for SLL-SM Decoupled Entity-Locus Binding.
    
    Evaluates paired sequence condition:
    CASE A: Create A @ L1 -> Release A -> Create B @ L1 -> Point @ L1 => Expected: Entity B
    CASE B: Create A @ L1 -> Active A -> Point @ L1                     => Expected: Entity A
    """

    def setUp(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.core = SLLSMCore(num_slots=4, num_entities=16, embed_dim=256, core_dim=512).to(self.device)
        self.core.eval()

    def run_case_a_reuse(self) -> dict:
        """Runs Case A: Create A -> Release A -> Create B at same location L1."""
        state = self.core.init_state(batch_size=1, device=self.device)
        L1 = torch.tensor([[0.5, 0.2, -0.1]], device=self.device)
        u_A = torch.full((1, 256), 1.5, device=self.device)
        u_B = torch.full((1, 256), 9.5, device=self.device)

        # Step 1: Create Entity A (index 0) at Location L1
        obs1 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': u_A,
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, state)

        # Step 2: Active A
        obs2 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out2 = self.core(obs2, out1.state_dict)

        # Step 3: Release A
        obs3 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[1.0]], device=self.device)
        }
        out3 = self.core(obs3, out2.state_dict)

        # Step 4: Unassigned transition
        obs4 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[0.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out4 = self.core(obs4, out3.state_dict)

        # Step 5: Create Entity B (index 1) at SAME location L1
        obs5 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': u_B,
            'target_entity': torch.tensor([1], device=self.device)
        }
        out5 = self.core(obs5, out4.state_dict)

        # Step 6: Point to L1 to reference the locus
        obs6 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[0.5]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out6 = self.core(obs6, out5.state_dict)

        return {
            'out': out6,
            'binding_A': out6.B[0, 0, 0].item(),  # Binding between Entity A (0) and Slot 0
            'binding_B': out6.B[0, 1, 0].item(),  # Binding between Entity B (1) and Slot 0
            'embed_A': out6.E[0, 0],
            'embed_B': out6.E[0, 1]
        }

    def run_case_b_persistence(self) -> dict:
        """Runs Case B: Create A -> Keep A Active -> Point @ L1."""
        state = self.core.init_state(batch_size=1, device=self.device)
        L1 = torch.tensor([[0.5, 0.2, -0.1]], device=self.device)
        u_A = torch.full((1, 256), 1.5, device=self.device)

        # Step 1: Create Entity A (index 0) at L1
        obs1 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[1.0]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device),
            'u_feat': u_A,
            'target_entity': torch.tensor([0], device=self.device)
        }
        out1 = self.core(obs1, state)

        # Steps 2-5: Keep Active
        out = out1
        for _ in range(4):
            obs_step = {
                'x_hand': L1,
                'p_torso': torch.zeros(1, 3, device=self.device),
                'dp_torso': torch.zeros(1, 3, device=self.device),
                'g_gaze': L1,
                'p_pointing': torch.tensor([[0.0]], device=self.device),
                'p_release': torch.tensor([[0.0]], device=self.device)
            }
            out = self.core(obs_step, out.state_dict)

        # Step 6: Point to L1
        obs6 = {
            'x_hand': L1,
            'p_torso': torch.zeros(1, 3, device=self.device),
            'dp_torso': torch.zeros(1, 3, device=self.device),
            'g_gaze': L1,
            'p_pointing': torch.tensor([[0.5]], device=self.device),
            'p_release': torch.tensor([[0.0]], device=self.device)
        }
        out6 = self.core(obs6, out.state_dict)

        return {
            'out': out6,
            'binding_A': out6.B[0, 0, 0].item(),  # Binding between Entity A (0) and Slot 0
            'binding_B': out6.B[0, 1, 0].item(),  # Binding between Entity B (1) and Slot 0
            'embed_A': out6.E[0, 0],
            'embed_B': out6.E[0, 1]
        }

    def test_counterfactual_sensitivity(self):
        """
        Executes both conditions and asserts whether the redesigned binding mechanism correctly
        distinguishes Case A (Reused slot -> Bound to B) from Case B (Active slot -> Bound to A).
        """
        res_A = self.run_case_a_reuse()
        res_B = self.run_case_b_persistence()

        print("\n--- SLL-SM COUNTERFACTUAL EXPERIMENTAL RESULTS ---")
        print(f"Case A (Locus Reuse)  : Slot 0 Binding -> Entity A: {res_A['binding_A']:.1f}, Entity B: {res_A['binding_B']:.1f}")
        print(f"Case B (Active Locus) : Slot 0 Binding -> Entity A: {res_B['binding_A']:.1f}, Entity B: {res_B['binding_B']:.1f}")

        # Check Case A: Locus 0 must be bound to Entity B (1.0) and NOT Entity A (0.0)
        self.assertEqual(res_A['binding_B'], 1.0, "Case A Failed: Reused slot 0 was not bound to Entity B")
        self.assertEqual(res_A['binding_A'], 0.0, "Case A Failed: Reused slot 0 remained bound to Entity A")

        # Check Case B: Locus 0 must be bound to Entity A (1.0) and NOT Entity B (0.0)
        self.assertEqual(res_B['binding_A'], 1.0, "Case B Failed: Active slot 0 was not bound to Entity A")
        self.assertEqual(res_B['binding_B'], 0.0, "Case B Failed: Active slot 0 was bound to Entity B")

        # Check Entity A Memory Preservation in Case A: Entity A embedding must still exist
        self.assertFalse(torch.all(res_A['embed_A'] == 0.0), "Entity A memory was wiped unexpectedly")

        print("COUNTERFACTUAL SENSITIVITY TEST PASSED: SLL-SM correctly resolves entity identity during locus reuse.")


if __name__ == "__main__":
    unittest.main()
