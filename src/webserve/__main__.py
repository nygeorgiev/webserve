import argparse
import socket

from webserve.server import Server
from webserve.__version__ import __version__

def find_free_port(start=8010, end=8099):
    ports = list(range(start, end + 1))

    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue

    return None

def main():
    parser = argparse.ArgumentParser(prog="webserve")
    parser.add_argument("model", type=str, help="Model's HuggingFace path")

    # Server Configuration
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        required=False, help="Server Host Address")
    parser.add_argument("--port", type=int, default=None,
                        required=False, help="Server Port")
    
    # UI Configuration
    parser.add_argument("--darkmode", action="store_true",
                        help="Launch the UI in Dark Mode")
    parser.add_argument("--latex", action="store_true",
                        help="Compile LaTeX in real-time")
    
    # Model Configuration
    parser.add_argument("--context", type=int, default=2048,
                        required=False, help="Context Length (coresponds to vllm's 'max_model_len')")
    parser.add_argument("--temperature", type=float, default=0.6,
                        required=False, help="Model temperature")
    parser.add_argument("--max-tokens", type=int, default=2048,
                        required=False, help="Number of maximum new tokens per generation")

    # Environment Configuration
    parser.add_argument("--gpu-count", type=int, default=1,
                        required=False, help="Number of GPUs to use")

    # Other
    parser.add_argument("--version", action="version",
                        version=f"\033[34m(VERSION)\033[0m WebServe version {__version__}")

    args = parser.parse_args()

    print(f"\033[34m(NOTICE)\033[0m Launching WebServe version {__version__}...")

    port = args.port

    if port is None:
        print("\033[34m(Preparing server...)\033[0m Looking for port to bind to. Avoid this by specifying port with --port PORT.")
        port = find_free_port()
        if port is None:
            print("\033[31m(ERROR)\033[0m Failed to find port to run the server. Please use --port PORT.")
            return
        else:
            print(f"\033[34m(NOTICE)\033[0m Selected port {port}.")

    print("\033[34m(Preparing server...)\033[0m Starting vLLM engine.")

    server = Server(
        args.model,
        gpu_count=args.gpu_count,
        max_model_len=args.context,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        latex=args.latex,
        darkmode=args.darkmode,
        verbose=False
    )

    print(f"\033[34m(NOTICE)\033[0m vLLM Engine ready.")
    print("\033[34m(Preparing server...)\033[0m Starting HTTP server.")
    
    server.listen(port, host=args.host, daemon=True)

    print(f"\033[34m(NOTICE)\033[0m Server ready.\n")
    print(f"\033[34m(CONFIG)\033[0m Model: {args.model}")
    print(f"\033[34m(CONFIG)\033[0m Temperature: {args.temperature}")
    print(f"\033[34m(CONFIG)\033[0m Context Length: {args.context} tok.")
    print(f"\033[34m(CONFIG)\033[0m Max New Tokens: {args.max_tokens} tok.")
    print(f"\033[34m(CONFIG)\033[0m GPU count: {args.gpu_count}")
    print(f"\033[34m(CONFIG)\033[0m LaTeX: {'ON' if args.latex else 'OFF'}")
    print(f"\033[34m(CONFIG)\033[0m WebServe listening on HTTP port {port}.")
    print(f"\033[34m(CONFIG)\033[0m http://localhost:{port}/\n")
    print("Type 'exit' to close server.")
    
    while input() != 'exit':
        continue

if __name__ == "__main__":
    main()