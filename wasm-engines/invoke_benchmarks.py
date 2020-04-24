import os
import json
import shutil
import subprocess

output_dir = "output"
wasm_minify_docker_image = 'wasm-minify'
#rust_docker_image = 'rust:1.39-stretch'
rust_docker_image = 'rust-boi'

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
    stdoutlines = [str(line, 'utf8') for line in proc.stdout]
    print(stdoutlines)
    return proc.wait(None)

def build_rust(project_dir, build_target_wasm=False):
    mount_project_flag = os.path.abspath(project_dir) + ":/" + os.path.basename(project_dir) 
    mounted_project_path = "/" + os.path.basename(project_dir)

    build_target = ""
    if build_target_wasm:
        buld_target = "--target wasm32-unknown-unknown"

    mount_cargo_registry = os.getcwd() + "/cargo-registry:/home/rust-boi/.cargo"
    docker_cmd = [
        'docker',
        'run', 
        '-v',
        mount_cargo_registry,
        '-v',
        mount_project_flag,
        '-t',
        rust_docker_image,
        'bash -c "cd {} && cargo build {} --release"'.format(mounted_project_path, build_target),
    ]

    docker_cmd = " ".join(docker_cmd)

    import pdb; pdb.set_trace()

    proc = subprocess.Popen(docker_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    stdoutlines = [str(line, 'utf8') for line in proc.stdout]
    print("".join(stdoutlines))
    return proc.wait(None)
    
def do_rust_bench(benchname, input, rust_code_dir, wasm_out_dir):
    rust_code_path = os.path.abspath(os.path.join(rust_code_dir, benchname))
    rustsrc = rust_code_path
    rusttemplate = os.path.join(rust_code_path, "src/bench.rs")

    if not os.path.exists(rustsrc):
        return False

    filldir = os.path.abspath(os.path.join("./rust-code-filled/", benchname))
    if os.path.exists(filldir):
        shutil.rmtree(filldir)
    shutil.copytree(rustsrc, filldir)

    import pdb; pdb.set_trace()
    template_args = {}
    for key in input.keys():
        if key == "name":
            continue
        if key == "input":
            input_len = int(len(input['input']) / 2)
            input_str = "let input: [u8; {}] = {};".format(input_len, get_rust_bytes(input['input']))
            template_args["input"] = input_str
        elif key == "expected":
            expected_len = int(len(input['expected']) / 2)
            expected_str = "let expected: [u8; {}] = {};".format(expected_len, get_rust_bytes(input['expected']))
            template_args["expected"] = expected_str
        else:
            template_args[key] = input[key]

    # fill template if necessary
    if len(template_args.keys()) > 1:
        print("filling template for {}".format(input['name']))
        with open(rusttemplate) as file_:
            template = jinja2.Template(file_.read())
            filledrust = template.render(**template_args)

        #rustfileout = "{}/src/bench.rs".format(filldir)
        rustfileout = os.path.join(filldir, "src/bench.rs")
        with open(rustfileout, 'w') as outfile:
            outfile.write(filledrust)

    build_rust(filldir, build_target_wasm=True) # build wasm target
    # TODO: get rustc compile time
    # TODO: also build with optimization turned off

    # TODO: run wasm through wasm-gc

    # TODO minify wasm

    build_rust(rust_code_dir) # build native target

    # TODO: get cargo build compiler time and report along with exec time.

    benchmark_native_binary = "..."

    # TODO separate build/fill and bench into separate functions
    native_times = bench_rust_binary(filldir, input['name'], benchmark_native_binary)
    return { 'bench_times': native_times, 'exec_size': exec_size }

def fill_and_run_rust_benchmarks():
    rust_code_dir = 'rust-code'
    input_vectors_dir = 'inputvectors'

    wasm_out_dir = 'unused'

    rust_codes = [dI for dI in os.listdir(rust_code_dir) if os.path.isdir(os.path.join(rust_code_dir,dI))]
    for benchname in rust_codes:
        if benchname == "__pycache__":
            continue

        inputvecs_path = os.path.join(input_vectors_dir, "{}-inputs.json".format(benchname))
        with open(inputvecs_path) as f:
            bench_inputs = json.load(f)

            for input in bench_inputs:
                print("bench input:", input['name'])
                native_input_times = do_rust_bench(benchname, input, rust_code_dir, wasm_out_dir)
                if native_input_times:
                    native_benchmarks[input['name']] = native_input_times

                print("done with input:", input['name'])

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
