import unittest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DELLAR_DIR = REPO_ROOT / "backend" / "dellar"
DELLAR_SRC = DELLAR_DIR / "src"
SERVER_DIR = REPO_ROOT / "server"

for p in [str(REPO_ROOT), str(DELLAR_DIR), str(DELLAR_SRC), str(SERVER_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load test cases directly
import tests.test_dellar_integration as t_integ
import backend.dellar.tests.test_sllsm_core as t_core
import backend.dellar.tests.test_dellar_bidirectional as t_bidi
import backend.dellar.tests.test_phase8_bidirectional as t_p8
import backend.dellar.tests.test_sllsm_adversarial as t_adv
import backend.dellar.tests.test_sllsm_counterfactual as t_cf

def run_all_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for mod in [t_core, t_bidi, t_p8, t_adv, t_cf, t_integ]:
        suite.addTests(loader.loadTestsFromModule(mod))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n==========================================")
    print(f"TOTAL TESTS EXECUTED: {result.testsRun}")
    print(f"TOTAL PASSED: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    print(f"==========================================")

    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
