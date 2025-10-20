import json
import os
import threading

import fastapi
from transformers import AutoTokenizer
import uvicorn

from webserve.__version__ import __version__

class Server:
    _STATIC_FILES = ["index.html", "main.css", "display.js", "stream.js"]

    def __init__(
        self,
        model: str,
        *,
        gpu_count: int | None = 1,
        max_model_len: int | None = 2048,
        max_tokens: int | None = 2048,
        temperature: float | None = 0.6,
        latex: bool | None = False,
        darkmode: bool | None = False,
        verbose: bool | None = False,
    ):
        from vllm import SamplingParams
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.v1.engine.async_llm import AsyncLLM

        self.darkmode = darkmode
        self.verbose = verbose
        self.latex = latex

        self._tokenizer = AutoTokenizer.from_pretrained(model)

        self._model = model
        self._temperature = temperature
        self._id_status = 0

        engine_args = AsyncEngineArgs(
            model=model,
            gpu_memory_utilization=0.9,
            max_model_len=max_model_len,
            tensor_parallel_size=gpu_count,
            enforce_eager=True, # load faster
        )

        self._engine = AsyncLLM.from_engine_args(engine_args)

        self._samp = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._app = fastapi.FastAPI()
        self._static = self._load_static()
        self._setup_routes()

    def _get_id(self) -> str:
        id_ = f"vllm-request-{self._id_status}"
        self._id_status += 1
        return id_

    def _get_actual_query(self, messages: list) -> str:
        return self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def _setup_routes(self) -> None:
        @self._app.get("/", response_class=fastapi.responses.HTMLResponse)
        async def get_index():
            return self._static["index.html"]
        
        @self._app.get("/version")
        async def get_main_css():
            content = f"webserve v{__version__}"
            return fastapi.responses.Response(content, media_type="text/plain")

        @self._app.get("/robots.txt")
        async def get_robots_txt():
            content = "User-agent: *\nDisallow: /"
            return fastapi.responses.Response(content, media_type="text/plain")

        @self._app.get("/main.css")
        async def get_main_css():
            return fastapi.responses.Response(self._static["main.css"], media_type="text/css")

        @self._app.get("/display.js")
        async def get_display_js():
            return fastapi.responses.Response(self._static["display.js"], media_type="application/javascript")
        
        @self._app.get("/stream.js")
        async def get_stream_js():
            return fastapi.responses.Response(self._static["stream.js"], media_type="application/javascript")
        
        @self._app.get("/config.js")
        async def get_config_js():
            return fastapi.responses.Response(self._get_config(), media_type="application/javascript")

        @self._app.websocket("/v1/retrieveResponse")
        async def websocket_endpoint(websocket: fastapi.WebSocket):
            await websocket.accept()
            try:
                incomming = await websocket.receive_text()
                data = json.loads(incomming)
                query = self._get_actual_query(data)
                if query:
                    text = None
                    async for output in self._engine.generate(request_id=self._get_id(), prompt=query, sampling_params=self._samp):
                        text = output.outputs[0].text

                        await websocket.send_json({
                            "completed": False,
                            "output": text,
                            "error": None
                        })

                        if output.finished: 
                            await websocket.send_json({
                                "completed": True,
                                "output": text,
                                "error": None
                            })
                            break

            except fastapi.WebSocketDisconnect:
                pass
            except Exception as e:
                await websocket.send_json({
                    "completed": False,
                    "output": "",
                    "error": str(e)
                })
                print(f"\033[31m(ERROR)\033[0m {e}")
            finally:
                await websocket.close()

    def _load_static(self) -> dict[str, str]:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(current_directory, "static/")
        output = {}
        for filename in self._STATIC_FILES:
            with open(os.path.join(static_path, filename), 'r') as file:
                output[filename] = file.read()
        return output
    
    def _get_config(self) -> str:
        config = {
            "mode": 'dark' if self.darkmode else 'light',
            "model": self._model,
            "temperature": self._temperature,
            "latex": self.latex
        }
        return f"const config = {json.dumps(config, indent=4)}"

    def _run(self, host: str, port: int) -> None:
        config = uvicorn.Config(
            self._app, 
            host=host, 
            port=port, 
            log_level=('info' if self.verbose else 'critical')
        )
        server = uvicorn.Server(config)
        server.run()

    def listen(
        self, 
        port: int = 80, 
        *, 
        host: str | None = "0.0.0.0",
        daemon: bool | None = False
    ) -> None:
        if daemon:
            server_thread = threading.Thread(target=self._run, args=(host, port), daemon=True)
            server_thread.start()
        else:
            self._run(host, port)