import gdown
import os

target_dir = os.path.join(os.getcwd(), "backend", "dellar")

files = [
    # src/slds_core
    ("1ciNE8stSzeKBMRBUPe5Lm_t15H6sDyDC", "src/slds_core/__init__.py"),
    ("116kXjQ347JdAIsOGRvwMKoUTfY3w0tOy", "src/slds_core/bidirectional_pipeline.py"),
    ("1q3v-BUV1QmeqB6c6uXPKK17Wvhv6Ykhw", "src/slds_core/common_representation.py"),
    ("1QnAniCuV1oW6rK4CU3Tc4HgmO55bjoB8", "src/slds_core/core.py"),
    ("1w0IfdYtBtdriagEaKfh5kDgon7WQwnrq", "src/slds_core/decoders.py"),
    ("14iEAJhA9bm3YjioDbQlqOFK3Tl_nLQvb", "src/slds_core/entity.py"),
    ("1qDdo2xEBSBHZJTMsAcTutKjsdNS54LOp", "src/slds_core/locus.py"),
    ("1Gzsj5VTxCfbe1QkoJHv-umsGf6tB3kPD", "src/slds_core/locus_fsm.py"),
    ("1yeM7kb9Q1VsZEGVwnXauwlm0L4TJwbpM", "src/slds_core/memory.py"),
    ("1g_HhsxNk3KKxe_lnH9lpObYviWTEAURb", "src/slds_core/relation.py"),
    ("1VrADXG7k3eJLgsYBs7xZkHBP4eRA292c", "src/slds_core/sign_adapter.py"),
    ("1n23u1r_Em-3UO0wuoY42kG2bcwTFo8E9", "src/slds_core/sllsm_core.py"),
    ("1_WtHnBZvd3YJS2K3KgjXd70EcCrJ8aB5", "src/slds_core/speech_adapter.py"),
    ("1xvMty-oD9S_T4KWvD2INLhhcIYEQfBye", "src/slds_core/state.py"),
    
    # tests
    ("1mdiBgcx0F63uiXBULLq1LvYydbYN-bk5", "tests/__init__.py"),
    ("1EgTo_4fbUAyCNKF3oXz5hTxUDfGf1cm9", "tests/test_dellar_bidirectional.py"),
    ("1xmv3TVbaBaHv4pALSxHjDE6uyLCnOlfT", "tests/test_phase8_bidirectional.py"),
    ("1tmsqTNsO2L0mjhYMZBGFUg4yizIzj0n1", "tests/test_sllsm_adversarial.py"),
    ("1vxm2oqAbNXo4A5llMvV1OLkXc12Aic18", "tests/test_sllsm_core.py"),
    ("1FSQdkXdQN1_eesAgBRtp77a5Pt4PVFF8", "tests/test_sllsm_counterfactual.py"),

    # scripts & root
    ("1iqvHUD7zO-jEHTOhYYvrTnsgeG-674nP", "scripts/real_world_validation.py"),
    ("1IOtIe8egquYaLcZ0FRLMMeLHAWeveNtL", "scripts/run_phase12_fast_training.py"),
    ("1220CnyhGM3-iDWI-YnYvj9hoVqNs2ADu", "README.md"),
    ("1FfWG5jklhZyfzw9OGba9gr70gGayLwLY", "DELLAR_BIDIRECTIONAL_VERIFICATION.md"),
    ("10DreUqwTPsrHUbeIxpuseD6sdr7b33IB", "FINAL_ALGORITHM_STATUS.md"),
]

for fid, rel_path in files:
    full_path = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    if os.path.exists(full_path) and os.path.getsize(full_path) > 10:
        print("Skipping existing:", rel_path)
        continue
    print("Downloading:", rel_path)
    gdown.download(id=fid, output=full_path, quiet=True)

print("ALL DELLAR FILES DOWNLOADED SUCCESSFULLY!")
