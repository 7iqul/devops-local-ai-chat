import ast
import operator
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import Request, urlopen
import json

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELS = ["qwen2.5:3b", "llama3.2:3b"]
SYSTEM_PROMPT = """You are the DevOps Guide Assistant for the English-language FIELDGUIDE.DEV website. You are not a general personal assistant. Help visitors understand the ideas presented on this site, explain terminology in plain English, compare concepts, and give short practical examples.

Website reference:
- DevOps is a way of working that brings people, processes, and technology together to deliver reliable software and improve it continuously. It is not a single tool or job title.
- Collaboration means development and operations share ownership and service outcomes.
- Automation makes builds, tests, deployments, and infrastructure changes repeatable and reduces manual errors and waiting.
- Continuous learning uses monitoring, user feedback, and blameless reviews to detect issues and improve.
- Git and GitHub provide source control, change history, and code review.
- Docker packages an application and its dependencies into a consistent container.
- CI/CD automates building, testing, and delivering changes through a pipeline.
- Infrastructure as Code defines infrastructure using versioned, reviewable configuration.
- A typical delivery loop is plan and code, build and test, release and deploy, then operate and learn from observability and feedback.
- The goal is a safer, more reliable flow of value, not speed at any cost.

Answer in English. Be clear, concise, and accurate. Use plain text with short paragraphs or simple bullets; avoid Markdown markers, tables, and long lists. If asked about a topic outside the site's DevOps guide, briefly say it is outside this guide and invite a related DevOps question. Do not claim to have performed real deployments or checked live systems. For arithmetic, calculate carefully and show a brief explanation if useful."""
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
       ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}

def calculate(text):
    s = text.strip().replace("×", "*").replace("÷", "/").replace("−", "-")
    s = re.sub(r"\s*(?:plus|and)\s*", "+", s, flags=re.I)
    s = re.sub(r"\s*(?:minus)\s*", "-", s, flags=re.I)
    s = re.sub(r"\s*(?:times|multiplied by)\s*", "*", s, flags=re.I)
    s = re.sub(r"\s*(?:divided by)\s*", "/", s, flags=re.I)
    s = re.sub(r"(?i)\b(what is|calculate|compute|how much is)\b", "", s).strip(" ?=:")
    if not re.fullmatch(r"[0-9.+*/()%\-\s^]+", s):
        return None
    s = s.replace("^", "**")
    try:
        tree = ast.parse(s, mode="eval")
        def ev(n):
            if isinstance(n, ast.Expression): return ev(n.body)
            if isinstance(n, ast.Constant) and type(n.value) in (int, float): return n.value
            if isinstance(n, ast.BinOp) and type(n.op) in OPS:
                a, b = ev(n.left), ev(n.right)
                if isinstance(n.op, ast.Pow) and (abs(b) > 10 or abs(a) > 1e6): raise ValueError()
                return OPS[type(n.op)](a, b)
            if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
            raise ValueError()
        result = ev(tree)
        if abs(result) > 1e100: return None
        return str(int(result)) if isinstance(result, float) and result.is_integer() else str(result)
    except Exception:
        return None

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw))); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path == "/api/models":
            try:
                with urlopen(OLLAMA_URL + "/api/tags", timeout=3) as r: tags = json.load(r).get("models", [])
                found = {m["name"] for m in tags}
                self.send_json({"models": [{"name": m, "available": m in found} for m in MODELS]})
            except Exception as e: self.send_json({"models": [{"name": m, "available": False} for m in MODELS], "error": str(e)}, 503)
        elif self.path == "/" or self.path == "/index.html":
            try:
                with open("index.html", "rb") as f: body=f.read()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            except OSError: self.send_error(404)
        else: self.send_error(404)
    def do_POST(self):
        if self.path != "/api/chat": return self.send_error(404)
        try:
            data=json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            model=data.get("model", MODELS[0]); messages=data.get("messages", [])
            if model not in MODELS: return self.send_json({"error":"That model is not enabled."},400)
            if not messages or len(messages)>30: return self.send_json({"error":"Send a valid message."},400)
            question=str(messages[-1].get("content", ""))[:4000]
            answer=calculate(question)
            if answer is not None:
                return self.send_json({"model":model,"response":f"The answer is {answer}.\nCalculated locally.","source":"calculator"})
            payload=json.dumps({"model":model,"messages":[{"role":"system","content":SYSTEM_PROMPT}]+messages,"stream":False,"options":{"temperature":0.2,"num_ctx":4096}}).encode()
            req=Request(OLLAMA_URL+"/api/chat",data=payload,headers={"Content-Type":"application/json"})
            with urlopen(req,timeout=180) as r: result=json.load(r)
            self.send_json({"model":model,"response":result.get("message",{}).get("content",""),"source":"ollama"})
        except URLError as e: self.send_json({"error":"Cannot reach Ollama. Make sure it is running and the selected model is downloaded."},503)
        except Exception as e: self.send_json({"error":"The request failed: "+str(e)},500)

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8000"))), Handler).serve_forever()
