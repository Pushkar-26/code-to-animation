import sys
import json
import io

class PythonTracer:
    def __init__(self):
        self.frames = []
        self.step_number = 0
        self.captured_output = []  # har step ka print output store karega

    def trace_function(self, frame, event, arg):
        if event not in ('line', 'call', 'return'):
            return self.trace_function

        self.step_number += 1
        call_stack = self._build_call_stack(frame)

        # Abhi tak jo output capture hua hai woh is step ka output hai
        current_output = self.stdout_capture.getvalue()

        step_data = {
            "step_number": self.step_number,
            "language": "python",
            "line_number": frame.f_lineno,
            "event_type": event,
            "call_stack": call_stack,
            "output": current_output
        }

        self.frames.append(step_data)
        return self.trace_function

    def _clean_value(self, value):
        if isinstance(value, (int, float, str, bool)) or value is None:
            return value
        elif isinstance(value, list):
            return [self._clean_value(v) for v in value[:20]]
        elif isinstance(value, dict):
            return {str(k): self._clean_value(v) for k, v in list(value.items())[:20]}
        else:
            return f"<{type(value).__name__}>"

    def _clean_locals(self, locals_dict):
        clean = {}
        for key, value in locals_dict.items():
            if key.startswith('__'):
                continue
            clean[key] = self._clean_value(value)
        return clean

    def _build_call_stack(self, frame):
        stack = []
        current = frame
        while current is not None:
            stack.append({
                "function_name": current.f_code.co_name,
                "locals": self._clean_locals(current.f_locals),
                "line_number": current.f_lineno
            })
            if current.f_code.co_name == '<module>':
                break
            current = current.f_back
        stack.reverse()
        return stack

    def trace_code(self, code_string):
        self.frames = []
        self.step_number = 0
        self.captured_output = []
        error_info = None

        # Syntax check
        try:
            compile(code_string, '<string>', 'exec')
        except SyntaxError as e:
            return {
                "frames": [],
                "error": f"Syntax Error: {e.msg} (line {e.lineno})"
            }

        # stdout ko capture karne ke liye redirect karo
        self.stdout_capture = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = self.stdout_capture

        sys.settrace(self.trace_function)
        try:
            exec(code_string, {})
        except Exception as e:
            error_info = f"{type(e).__name__}: {str(e)}"
        finally:
            sys.settrace(None)
            # IMPORTANT: stdout wapas restore karo, chahe kuch bhi ho
            sys.stdout = original_stdout

        if error_info:
            return {
                "frames": self.frames,
                "error": error_info
            }

        return {
            "frames": self.frames,
            "error": None
        }


if __name__ == "__main__":
    sample_code = """
def greet(name):
    print("Hello, " + name)
    return name

greet("Pushkar")
"""
    tracer = PythonTracer()
    result = tracer.trace_code(sample_code)
    print(json.dumps(result, indent=2))