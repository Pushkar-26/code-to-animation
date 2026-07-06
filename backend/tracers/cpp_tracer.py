import subprocess
import os
import re
import json
import traceback


MSYS2_BASH = r"C:\msys64\usr\bin\bash.exe"
GPP_PATH = "/c/msys64/ucrt64/bin/g++"
BACKEND_DIR = r"C:\Users\rakes\OneDrive\Desktop\VSCODE\code-to-animation\backend"
BACKEND_DIR_MSYS = "/c/Users/rakes/OneDrive/Desktop/VSCODE/code-to-animation/backend"

# Yeh variable names log statement me use nahi karenge - scope issues se bachne ke liye
SKIP_VARS = ['include', 'define', 'ifdef', 'endif', 'pragma', 'result', 'temp', 'mid']

class CppTracer:
    def __init__(self):
        self.frames = []

    def trace_code(self, code_string):
        self.frames = []

        try:
            transformed_code = self._inject_logging(code_string)
            print("STEP 1")
            cpp_path = os.path.join(BACKEND_DIR, "trace_code.cpp")
            exe_path = os.path.join(BACKEND_DIR, "trace_code.exe")
            log_path = os.path.join(BACKEND_DIR, "trace_log.txt")

            with open(cpp_path, 'w') as f:
                print("STEP 2")
                f.write(transformed_code)

            cpp_msys = f"{BACKEND_DIR_MSYS}/trace_code.cpp"
            exe_msys = f"{BACKEND_DIR_MSYS}/trace_code.exe"

            compile_cmd = f'{GPP_PATH} -o "{exe_msys}" "{cpp_msys}"'
            print("STEP 3")
            compile_result = subprocess.run(
                
                [MSYS2_BASH, '-c', compile_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, 'PATH': '/c/msys64/ucrt64/bin:/usr/bin:' + os.environ.get('PATH', '')}
            )
            print("=" * 50)
            print("Compile Return Code:", compile_result.returncode)
            print("Compile STDOUT:")
            print(compile_result.stdout)
            print("Compile STDERR:")
            print(compile_result.stderr)
            print("=" * 50)

            if not os.path.exists(exe_path):
                return {
                    "frames": [],
                    "error": f"Compilation Error:\n{compile_result.stdout}\n{compile_result.stderr}"
                }

            run_cmd = f'"{exe_msys}" 2>&1'

            run_result = subprocess.run(
                [MSYS2_BASH, '-c', run_cmd],
                capture_output=True,
                text=True,
                timeout=10
            )

            print("STEP 4")

            print("=" * 50)
            print("RUN RETURN CODE:", run_result.returncode)
            print("RUN STDOUT:")
            print(run_result.stdout)
            print("RUN STDERR:")
            print(run_result.stderr)
            print("=" * 50)

            if not os.path.exists(log_path):
                return {"frames": [], "error": "Program ran but produced no trace output."}

            with open(log_path, 'r') as f:
                print("STEP 5")
                log_content = f.read()

            frames = self._parse_log(log_content)
            return {"frames": frames, "error": None}

        except subprocess.TimeoutExpired:
            return {"frames": [], "error": "Timeout - possible infinite loop"}
        except Exception:
            print("=" * 80)
            traceback.print_exc()
            print("=" * 80)
            raise
        finally:
            for fname in ["trace_code.cpp", "trace_code.exe", "trace_log.txt"]:
                path = os.path.join(BACKEND_DIR, fname)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass

    def _inject_logging(self, code_string):
        lines = code_string.split('\n')
        VAR_TYPES = ['int', 'float', 'double', 'long', 'bool']

        user_headers = [l for l in lines if l.strip().startswith('#include')]
        other_lines = [l for l in lines if not l.strip().startswith('#include')]

        result = []

        result.extend(user_headers)
        if not any('fstream' in h for h in user_headers):
            result.append('#include <fstream>')

        result.append('std::ofstream __trace_log;')
        result.append('')

        known_vars = []
        in_main = False
        brace_depth = 0

        for i, line in enumerate(other_lines):
            original_line_num = lines.index(line) + 1 if line in lines else i + 1
            stripped = line.strip()

            if re.search(r'\bmain\s*\(', stripped) and '{' in stripped:
                in_main = True
                result.append(line)
                result.append('    __trace_log.open("trace_log.txt");')
                brace_depth += 1
                continue

            if in_main:
                brace_depth += stripped.count('{') - stripped.count('}')

                if stripped.startswith('return') and brace_depth <= 1:
                    result.append('    __trace_log.close();')

            result.append(line)

            if in_main and brace_depth >= 1:
                # Variable declaration detect karo — SKIP_VARS check add kiya
                for vtype in VAR_TYPES:
                    match = re.match(rf'^\s*{vtype}\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[=;\[]', line)
                    if match:
                        var_name = match.group(1)
                        if var_name not in known_vars and var_name not in SKIP_VARS:
                            known_vars.append(var_name)
                        break

                # Statement ke baad log karo — sirf simple statements pe
                # Array declarations aur complex statements skip karo
                is_array_decl = re.match(r'^\s*\w+\s+\w+\s*\[', line)
                is_for_loop = stripped.startswith('for')
                is_if_stmt = stripped.startswith('if')
                is_else = stripped.startswith('else')
                is_brace = stripped in ['{', '}']

                if (stripped.endswith(';') and
                    not stripped.startswith('//') and
                    not stripped.startswith('#') and
                    not stripped.startswith('return') and
                    not is_array_decl and
                    not is_for_loop and
                    not is_if_stmt and
                    not is_else and
                    not is_brace and
                    known_vars):

                    log_line = self._make_log_statement(original_line_num, known_vars)
                    result.append(log_line)

        return '\n'.join(result)

    def _make_log_statement(self, line_num, var_names):
        parts = [f'    __trace_log << "{{\\"line\\":{line_num},\\"vars\\":{{"']

        var_parts = []
        for i, var in enumerate(var_names):
            if i == 0:
                var_parts.append(f' << "\\"{var}\\":" << {var}')
            else:
                var_parts.append(f' << ",\\"{var}\\":" << {var}')

        parts.extend(var_parts)
        parts.append(' << "}}" << std::endl;')

        return ''.join(parts)

    def _parse_log(self, log_content):
        frames = []
        step_number = 0

        for line in log_content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                step_number += 1

                clean_vars = {}
                for k, v in data.get('vars', {}).items():
                    try:
                        clean_vars[k] = int(v)
                    except (ValueError, TypeError):
                        try:
                            clean_vars[k] = float(v)
                        except (ValueError, TypeError):
                            clean_vars[k] = str(v)

                frames.append({
                    "step_number": step_number,
                    "language": "cpp",
                    "line_number": data.get('line', 0),
                    "event_type": "line",
                    "call_stack": [{
                        "function_name": "main",
                        "locals": clean_vars,
                        "line_number": data.get('line', 0)
                    }],
                    "output": ""
                })
            except json.JSONDecodeError:
                continue

        return frames