import sys
import json

class PythonTracer:
    def __init__(self):
        self.frames = []
        self.step_number = 0

    def trace_function(self, frame, event, arg):
        if event not in ('line', 'call', 'return'):
            return self.trace_function

        self.step_number += 1
        call_stack = self._build_call_stack(frame)

        step_data = {
            "step_number": self.step_number,
            "language": "python",
            "line_number": frame.f_lineno,
            "event_type": event,
            "call_stack": call_stack,
            "output": ""
        }

        self.frames.append(step_data)
        return self.trace_function

    def _clean_value(self, value):
        """Recursively clean a value taaki JSON-safe rahe aur circular reference na bane"""
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

        sys.settrace(self.trace_function)
        try:
            exec(code_string, {})
        finally:
            sys.settrace(None)

        return self.frames


if __name__ == "__main__":
    sample_code = """
def add(a, b):
    c = a + b
    return c

result = add(2, 3)
"""
    tracer = PythonTracer()
    frames = tracer.trace_code(sample_code)
    print(json.dumps(frames, indent=2))