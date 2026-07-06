print("######## MAIN LOADED ########")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tracers.python_tracer import PythonTracer
from tracers.cpp_tracer import CppTracer

app = FastAPI()

# CORS middleware — yeh frontend (jo alag port pe chalega) ko backend se
# baat karne ki permission deta hai. Bina iske browser security error dega.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # abhi sabko allow kar rahe hain, production me restrict karenge
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model — yeh define karta hai ki request body me kya data aana chahiye
# FastAPI automatically validate karega ki incoming request isi shape ki ho
class CodeRequest(BaseModel):
    code: str
    language: str = "python"  # default Python rakha hai abhi

@app.get("/")
def root():
    return {"message": "Hello from Pushkar"}

@app.post("/trace")
def trace_code(request: CodeRequest):
    print("Language:", request.language)

    if request.language == "cpp":
        print("CPP START")
        tracer = CppTracer()

        result = tracer.trace_code(request.code)

        print("CPP RESULT:", result)
        print(type(result))

        return result

    elif request.language == "python":
        tracer = PythonTracer()
        return tracer.trace_code(request.code)