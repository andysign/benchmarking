import os

output_dir = "output"

def minify_wasm(test_vectors):
    pass
    
def main():
    try:
        os.remove(output_dir)
    except FileNotFoundError as e:
        pass

    # TODO this command isn't compatible with /proc/cpuinfo format on all systems
    # TODO fail if this command fails
    os.system("grep -E '^model name ^cpu MHz' /proc/cpuinfo > results-cpu-info.txt")

    # fill rust templates with input vectors (benchnativerust_prepwasm.py)
    # run rust benchmarks

    fill_and_run_rust_benchmarks()

    # invoke sentinel-rs (minifier) on wasm test vectors

    # run benchmarks (native rust)

    # run benchmarks (wasm)

main()
