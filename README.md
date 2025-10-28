# WebServe - Quick Guide
WebServe is a small tool for running LLM web chat interfaces backed by vLLM. It supports streaming and live LaTeX parsing (powered by MathJax).

<p align="center">
  <img src="/assets/demo.png" alt="Demo" width="550"/>
</p>

## Setup
To install WebServe run:
```
pip install webserve
```

## Running WebServe
All functionallity is contained within the `webserve` command (`python -m webserve` if `PATH` is not configured with `pip`). The syntax is as follows:
```
webserve MODEL (--host HOST) (--port PORT) (--context CONTEXT_LEN) (--temperature TEMP) 
(--max-tokens MAX_TOKENS) (--gpu-count GPU_COUNT) (--latex) (--darkmode)
```
The above arguments are:
- `MODEL` - HuggingFace Path of the model to run
- `--host HOST` - The Server Host Address (Default: `0.0.0.0`)
- `--port PORT` - The Server Port (Default: searches for a free port in the `8010-8099` range)
- `--context CONTEXT_LEN` - How many tokens context length to allocate (Default: `2048`)
- `--temperature TEMP`  - Model's temperature (Default: `0.6`)
- `--gpu-count GPU_COUNT` - Number of GPUs (or other devices) for vLLM to use (Default: `1`) 
- `--latex` - Activate LaTeX parsing
- `--darkmode` - Set default theme to Dark Mode

## Example
The following command:
```
webserve openai/gpt-oss-20b --port 8080 --context 128000 --max-tokens 81920 --latex
```
runs a chat interface for `openai/gpt-oss-20b` on local port `8080` (access via URL: `http://localhost:8080/`) with context length of `128000` tokens are a limit for max tokens generated per query `81920`. By adding `--latex` it enables LaTeX parsing.

## vLLM notice
As of version `0.11.0` vLLM requires GPU UIDs to be integers starting with 0. In many cases proper GPU IDs are not numeric. To handle this please call:
```
export CUDA_VISIBLE_DEVICES=0,1,...(NUMBER_OF_GPUS - 1)
``` 