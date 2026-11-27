"""Loopback-only inference server and static website. Generated code is never executed."""
import argparse
import json
import os
from pathlib import Path
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from core import BASE_MODEL, validate_chat

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME', str(ROOT / '.cache' / 'huggingface'))
LOCK = threading.Lock()

class Engine:
    def __init__(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        self.torch = torch
        torch.set_num_threads(4)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        adapter = ROOT / 'adapter'
        if not (adapter / 'adapter_model.safetensors').is_file():
            raise RuntimeError('No trained adapter found. Run python training/train.py first.')
        revision = json.loads((adapter / 'adapter_config.json').read_text()).get('revision')
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=revision)
        base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, revision=revision, torch_dtype=torch.bfloat16 if self.device == 'cuda' else torch.float32).to(self.device)
        self.model = PeftModel.from_pretrained(base, adapter).eval()

    def generate(self, messages):
        tokens = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors='pt', return_dict=True).to(self.device)
        if tokens['input_ids'].shape[-1] > 2048:
            raise ValueError('Conversation exceeds 2048 tokens. Start a new chat or shorten your code.')
        with self.torch.inference_mode():
            output = self.model.generate(**tokens, max_new_tokens=384, do_sample=False, pad_token_id=self.tokenizer.eos_token_id)
        return self.tokenizer.decode(output[0, tokens['input_ids'].shape[-1]:], skip_special_tokens=True).strip()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'docs'), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()

    def respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == '/api/health':
            return self.respond(200, {'ready': True, 'model': BASE_MODEL, 'adapter': 'Forge LoRA', 'device': self.server.engine.device})
        # The model cache and adapter live outside the served directory.
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/chat':
            return self.respond(404, {'error': 'Not found.'})
        origin = self.headers.get('Origin')
        allowed = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if origin and origin not in allowed:
            return self.respond(403, {'error': 'Use the website served by this local server.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond(415, {'error': 'Expected application/json.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= 100000:
                raise ValueError('Request must be between 1 and 100000 bytes.')
            messages = validate_chat(json.loads(self.rfile.read(size)))
        except (ValueError, UnicodeDecodeError) as exc:
            return self.respond(400, {'error': str(exc)})
        if not LOCK.acquire(blocking=False):
            return self.respond(429, {'error': 'The model is busy. Try again shortly.'})
        try:
            reply = self.server.engine.generate(messages)
            self.respond(200, {'reply': reply})
        except ValueError as exc:
            self.respond(400, {'error': str(exc)})
        except Exception:
            import traceback
            traceback.print_exc()
            self.respond(500, {'error': 'Generation failed. Check the server terminal.'})
        finally:
            LOCK.release()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print('Loading Forge and its trained adapter...', flush=True)
    engine = Engine()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.engine = engine
    print(f'Forge is ready at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    main()
