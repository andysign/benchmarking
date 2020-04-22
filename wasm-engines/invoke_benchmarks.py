import os

output_dir = "output"
wasm_minify_docker_image = 'wasm-minify'
rust_docker_image = 'rust-build-env'

def minify_wasm(input_file, output_file):
    mount_input_file = os.path.abspath(input_file) + ":/"
    mount_output_file = os.path.abspath(output_file) + ":/"

    docker_cmd = [
            'docker',
            'run',
            '-v',
            mount_input_file,
            '-v',
            mount_output_file,
            wasm_minify_docker_image,
            '/usrc/bin/wasm-minify'
    ]

    proc = subprocess.Popen(native_exec, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    return proc.wait(None)

def build_rust(project_dir, output_file, build_target_wasm=False):
    if build_target_wasm:
        buld_target = "--target wasm32-unknown-unknown"

    docker_cmd = [
        'docker',
        'run', 
        '-v',
        mount_project_dir,
        '-v',
        mount_output_file_dir,
        '-t',
        rust_docker_image,
        '"cargo build {} --release /project_dir && cp /project_dir/target/wasm32-unknown-unknown/release/*.wasm /output/"'.format(build_target),
    ]

    proc = subprocess.Popen(docker_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    return proc.wait(None)
    
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
