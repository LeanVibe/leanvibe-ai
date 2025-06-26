<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Setting Up and Using Qwen2.5-Coder-32B with MLX-LM: A Step-by-Step Tutorial

Qwen2.5-Coder-32B is currently the best coding LLM that can run locally on your MacBook M3 Max with 48GB RAM[^1]. This model has been shown to match the coding capabilities of GPT-4o and outperform many larger models[^1]. In this tutorial, I'll guide you through setting up and using this powerful coding model with MLX-LM, Apple's optimized framework for running LLMs on Apple Silicon.

## Prerequisites

Before we begin, ensure you have:

- A MacBook with Apple Silicon (M3 Max with 48GB RAM in your case)
- macOS installed (latest version recommended)
- Python installed on your system
- Terminal/Command Line access[^2][^3]


## Step 1: Install MLX-LM Package

First, we need to install the MLX-LM package, which is specifically designed for running large language models on Apple Silicon:

```bash
pip install mlx-lm
```

This command installs the MLX-LM Python package that provides tools for generating text and fine-tuning large language models on Apple Silicon[^2][^3].

## Step 2: Download the Qwen2.5-Coder-32B Model

There are two ways to download the model:

### Option 1: Automatic Download (Recommended)

When you first use the model with MLX-LM, it will automatically download from Hugging Face[^4][^5]. This is the simplest approach as it handles all the downloading and caching for you.

### Option 2: Manual Download

If you prefer to download the model manually:

```python
from huggingface_hub import snapshot_download

# Download the model files
model_path = snapshot_download(
    repo_id="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
    local_dir="./models/qwen2.5-coder-32b"
)
print(f"Model downloaded to: {model_path}")
```

The 4-bit quantized version requires approximately 18.5GB of storage space[^6], making it ideal for your 48GB MacBook M3 Max.

## Step 3: Using the Model from Command Line

The simplest way to interact with the model is through the command line:

```bash
mlx_lm.generate --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit --prompt "Write a Python function to calculate Fibonacci numbers" --max-tokens 500 --use-default-chat-template --verbose
```

Key parameters explained:

- `--model`: Specifies the model to use (Qwen2.5-Coder-32B-Instruct-4bit)
- `--prompt`: Your coding question or task
- `--max-tokens`: Maximum length of the generated response
- `--use-default-chat-template`: Applies the appropriate chat formatting for the model
- `--verbose`: Shows the generation process in real-time[^7][^8]

For better code generation, you can adjust the temperature and repetition penalty:

```bash
mlx_lm.generate --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit --prompt "Implement a REST API in Flask" --max-tokens 1000 --temp 0.7 --top-p 0.9 --repetition-penalty 1.05 --use-default-chat-template
```

The lower temperature (0.7) provides more focused and deterministic code generation, while the repetition penalty helps avoid redundant code patterns[^7][^5].

## Step 4: Using the Model with Python API

For more control and integration into your workflows, you can use the Python API:

```python
from mlx_lm import load, generate

# Load the model
model, tokenizer = load("mlx-community/Qwen2.5-Coder-32B-Instruct-4bit")

# Prepare the prompt using chat template
coding_prompt = "Write a Python class for a binary search tree with insert, delete, and search methods"
messages = [{"role": "user", "content": coding_prompt}]
prompt = tokenizer.apply_chat_template(
    messages, 
    tokenize=False, 
    add_generation_prompt=True
)

# Generate the response
response = generate(
    model, 
    tokenizer, 
    prompt=prompt, 
    verbose=True,
    max_tokens=1000,
    temp=0.7,
    repetition_penalty=1.05
)

print(response)
```

This approach gives you programmatic access to the model, allowing you to integrate it into your development environment or custom applications[^4][^5][^9].

## Step 5: Setting Up an Interactive Chat Session

For ongoing coding assistance, you can create an interactive chat session that maintains context:

```python
from mlx_lm import load, generate

# Load the model
model, tokenizer = load("mlx-community/Qwen2.5-Coder-32B-Instruct-4bit")

# Initialize chat history
chat_history = []

def chat_with_model(user_input):
    # Add user message to history
    chat_history.append({"role": "user", "content": user_input})
    
    # Create full prompt from chat history
    prompt = tokenizer.apply_chat_template(
        chat_history,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Generate response
    response = generate(
        model, 
        tokenizer, 
        prompt=prompt, 
        verbose=False,
        max_tokens=500,
        temp=0.7
    )
    
    # Add assistant response to history
    chat_history.append({"role": "assistant", "content": response})
    
    return response

# Example usage
print(chat_with_model("Write a Python function to check if a string is a palindrome"))
print(chat_with_model("Now optimize it for performance"))
```

This approach allows you to have multi-turn conversations with the model, which is particularly useful for iterative code development and refinement[^7][^10].

## Step 6: Setting Up a Server (Optional)

For a more persistent solution that can be accessed by multiple applications, you can set up an MLX-LLM server:

```bash
# Install the server package
pip install mlx-llm-server

# Start the server with the model
mlx-llm-server --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit
```

The server provides an OpenAI-compatible API at http://127.0.0.1:8080 by default[^11][^12]. You can configure the host and port using environment variables:

```bash
export HOST=0.0.0.0
export PORT=5000
mlx-llm-server --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit
```

This allows you to access the model from various applications, IDEs, or even from your phone on the same network[^13][^11].

## Performance Optimization Tips

To get the best performance from Qwen2.5-Coder-32B on your MacBook M3 Max:

1. **Memory Management**: The 4-bit quantized version requires approximately 18.5GB of RAM, leaving plenty of headroom on your 48GB system[^6].
2. **Long Context Handling**: For working with large codebases, use the rotating key-value cache:

```bash
mlx_lm.generate --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit --prompt "Explain this code..." --max-kv-size 4096
```

3. **Prompt Caching**: For repeatedly using the same context (like a large codebase), cache the prompt:

```bash
cat large_codebase.py | mlx_lm.cache_prompt --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit --prompt - --prompt-cache-file codebase_cache.safetensors
```

Then use it for queries:

```bash
mlx_lm.generate --prompt-cache-file codebase_cache.safetensors --prompt "Explain the main algorithm in this code"
```


These optimizations help maintain responsive performance even with large code files and complex queries[^2][^7].

## Conclusion

You now have a powerful coding assistant running locally on your MacBook M3 Max. Qwen2.5-Coder-32B offers exceptional coding capabilities that rival cloud-based models like GPT-4o, but with the privacy, security, and cost benefits of running locally[^1]. The MLX framework, optimized specifically for Apple Silicon, ensures you get the best possible performance from your hardware[^14].

Whether you're using the command line for quick queries, the Python API for deeper integration, or setting up a server for persistent access, you now have a state-of-the-art coding assistant at your fingertips[^2][^1][^7].

<div style="text-align: center">⁂</div>

[^1]: https://simonwillison.net/2024/Nov/12/qwen25-coder/

[^2]: https://github.com/ml-explore/mlx-lm

[^3]: https://huggingface.co/docs/hub/en/mlx

[^4]: https://huggingface.co/mlx-community/Qwen2.5-Coder-32B-Instruct-bf16

[^5]: https://huggingface.co/mlx-community/Qwen2.5-Coder-32B-Instruct-4bit

[^6]: https://llm.extractum.io/model/mlx-community%2FQwen2.5-Coder-32B-Instruct-4bit,1Nzqwk2AIOokdvw9J5UoZn

[^7]: https://libraries.io/pypi/mlx-lm

[^8]: https://huggingface.co/mlx-community

[^9]: https://huggingface.co/mlx-community/Qwen2.5-Coder-14B-Instruct-8bit/blob/refs%2Fpr%2F1/README.md

[^10]: https://github.com/ml-explore/mlx-examples/issues/761

[^11]: https://github.com/mzbac/mlx-llm-server

[^12]: https://github.com/toogle/mlx-dev-server

[^13]: https://www.youtube.com/watch?v=mStqWk0aCc4

[^14]: https://github.com/ml-explore/mlx

[^15]: https://harm-smits.github.io/42docs/libs/minilibx/getting_started.html

[^16]: https://www.reddit.com/r/LocalLLaMA/comments/1gxs34g/comment_your_qwen_coder_25_setup_ts_here/

[^17]: https://lmstudio.ai/mlx

[^18]: https://simonwillison.net/2025/Feb/15/llm-mlx/

[^19]: https://apidog.com/blog/qwen2-5-vl-32b-locally-mlx/

[^20]: https://github.com/QwenLM/Qwen2.5-Coder

[^21]: https://qwen.readthedocs.io/en/latest/run_locally/mlx-lm.html

[^22]: https://qwen.readthedocs.io/en/v2.5/run_locally/mlx-lm.html

[^23]: https://huggingface.co/mlx-community/Qwen2.5-Coder-7B-Instruct-4bit

[^24]: https://github.com/ml-explore/mlx-lm/issues/215

[^25]: https://github.com/inferless/Qwen2.5-Coder-32B-Instruct/blob/main/README.md

[^26]: https://fxis.ai/edu/how-to-use-the-mlx-community-codelama-7b-model-for-text-generation/

[^27]: https://lmstudio.ai/models/qwen/qwen2.5-coder-32b

[^28]: https://llm.extractum.io/model/mlx-community%2FQwen2.5-Coder-32B-Instruct-bf16,4BAxJNSihV81HuXb9ajghM

[^29]: https://survivor.togaware.com/mlhub/ml-command-line-options.html

[^30]: https://huggingface.co/spaces/mlx-community/README

[^31]: https://blog.csdn.net/jkgSFS/article/details/144979115

[^32]: https://huggingface.co/mlx-community/dbrx-instruct-4bit/discussions/7

[^33]: https://huggingface.co/docs/hub/mlx

[^34]: https://distilabel.argilla.io/pr-1089/components-gallery/llms/mlxllm/

[^35]: https://huggingface.co/mingineer/Qwen2.5-Coder-7B-Instruct-Q4-mlx/blob/main/README.md

[^36]: https://huggingface.co/mlx-community/Qwen2.5-Coder-14B-Instruct-8bit/blob/main/README.md

[^37]: https://heidloff.net/article/apple-mlx-fine-tuning/

[^38]: https://ml-explore.github.io/mlx/build/html/examples/llama-inference.html

