import os
import re
import json
import shutil
import subprocess
import nanodurationpy as durationpy

output_dir = "output"
wasm_minify_docker_image = 'wasm-minify'
#rust_docker_image = 'rust:1.39-stretch'
rust_docker_image = 'rust-boi'

RUST_BENCH_REPEATS = 50

def get_rust_bytes(hex_str):
    tmp = map(''.join, zip(*[iter(hex_str)]*2))
    tmp = map(lambda x: int(x, 16), tmp)
    tmp = map(lambda x: '{}u8'.format(x), tmp)
    tmp = reduce(lambda x, y: x+', '+y, tmp)
    return '[ '+tmp+' ]'

def minify_wasm_docker(input_file, output_file):
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
    cargo_build_cmd = ""
    if build_target_wasm:
        cargo_build_cmd = "cargo build --target wasm32-unknown-unknown --release"
    else:
        cargo_build_cmd = "cargo build --bin {}_native --release".format(os.path.basename(project_dir))

    proc = subprocess.Popen(cargo_build_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True, cwd=project_dir)
    stdoutlines = [str(line, 'utf8') for line in proc.stdout]
    print("".join(stdoutlines))

    # TODO fail hard if this breaks
    return proc.wait(None)


def bench_rust_binary(rustdir, input_name, native_exec):
    print("running rust native {}...\n{}".format(input_name, native_exec))
    bench_times = []
    for i in range(1,RUST_BENCH_REPEATS):
        rust_process = subprocess.Popen(native_exec, cwd=rustdir, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        rust_process.wait(None)
        stdoutlines = [str(line, 'utf8') for line in rust_process.stdout]
        print(("").join(stdoutlines), end="")
        elapsedline = stdoutlines[0]
        elapsedmatch = re.search("Time elapsed in bench\(\) is: ([\w\.]+)", elapsedline)
        elapsed_time = durationpy.from_str(elapsedmatch[1])
        bench_times.append(elapsed_time.total_seconds())
    return bench_times

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

    build_rust(filldir) # build native target

    # TODO: get cargo build compiler time and report along with exec time.

    import pdb; pdb.set_trace()
    benchmark_native_binary = filldir + "/target/release/" + os.path.basename(filldir) + "_native" 
    exec_size = os.path.getsize(benchmark_native_binary)

    # TODO separate build/fill and bench into separate functions
    native_times = bench_rust_binary(filldir, input['name'], benchmark_native_binary)
    return { 'bench_times': native_times, 'exec_size': exec_size }

def saveResults(native_benchmarks, result_file):
    #result_file = os.path.join(RESULT_CSV_OUTPUT_PATH, RESULT_CSV_FILENAME)
    # move existing files to old-datetime-folder
    ts = time.time()
    date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    ts_folder_name = "{}-{}".format(date_str, round(ts))
    result_path = os.path.dirname(result_file)
    dest_backup_path = os.path.join(result_path, ts_folder_name)
    os.makedirs(dest_backup_path)

    #for file in glob.glob(r"{}/*.csv".format(RESULT_CSV_OUTPUT_PATH)):
    #    print("backing up existing {}".format(file))
    #    shutil.move(file, dest_backup_path)
    if os.path.isfile(result_file):
        print("backing up existing {}".format(result_file))
        shutil.move(result_file, dest_backup_path)
    print("existing csv file backed up to {}".format(dest_backup_path))

    with open(result_file, 'w', newline='') as bench_result_file:
        fieldnames = ['test_name', 'elapsed_times', 'native_file_size']
        writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
        writer.writeheader()
        for test_name, test_results in native_benchmarks.items():
            bench_times = [str(t) for t in test_results['bench_times']]
            times_str = ", ".join(bench_times)
            writer.writerow({"test_name" : test_name, "elapsed_times" : times_str, "native_file_size" : test_results['exec_size']})

def fill_and_run_rust_benchmarks():
    rust_code_dir = 'rust-code'
    input_vectors_dir = 'inputvectors'

    wasm_out_dir = 'unused'

    rust_codes = [dI for dI in os.listdir(rust_code_dir) if os.path.isdir(os.path.join(rust_code_dir,dI))]
    for benchname in rust_codes:
        if benchname == "__pycache__":
            continue

        native_benchmarks = {}

        inputvecs_path = os.path.join(input_vectors_dir, "{}-inputs.json".format(benchname))
        with open(inputvecs_path) as f:
            bench_inputs = json.load(f)

            for input in bench_inputs:
                print("bench input:", input['name'])
                native_input_times = do_rust_bench(benchname, input, rust_code_dir, wasm_out_dir)
                if native_input_times:
                    native_benchmarks[input['name']] = native_input_times

                print("done with input:", input['name'])
    saveResults(native_benchmarks, csv_file_path)

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
