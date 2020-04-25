import os
import shutil
from benchnativerust_prepwasm import build_and_bench_rust_wasm_and_native

def recreate_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    os.mkdir(dir_path)

def main():
    wasm_files_dir = os.path.join(os.getcwd(), "output/wasmfiles")
    csv_native_results = os.path.join(os.getcwd(), "output/native_results.csv")
    # filled_rust_code_dir = os.path.join(os.getcwd(), "output/rust-code")
    input_vectors_dir = os.path.join(os.getcwd(), "inputvectors")

    recreate_dir(wasm_files_dir)

    algos = {"bn128_pairing": ["bn128_pairing-ten_point_match_1"]}

    build_and_bench_rust_wasm_and_native(wasm_files_dir,
        csv_native_results,
        "rust-code",
        input_vectors_dir,
        limit_benchmark_algos=algos)

if __name__ == "__main__":
    main()
