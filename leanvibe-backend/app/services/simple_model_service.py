"""
Simple Model Service for testing real models with MLX
This bypasses mlx-lm complexities and provides direct model loading
"""

import logging
import time
from typing import Any, Dict, List, Optional

import mlx.core as mx
import mlx.nn as nn

logger = logging.getLogger(__name__)


class SimpleCodeModel(nn.Module):
    """Simple transformer model for code generation testing"""

    def __init__(
        self, vocab_size: int = 32000, hidden_size: int = 512, num_layers: int = 4
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size

        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.layers = [nn.Linear(hidden_size, hidden_size) for _ in range(num_layers)]
        self.output_proj = nn.Linear(hidden_size, vocab_size)

    def __call__(self, x):
        # Simple forward pass
        x = self.embedding(x)

        # Apply layers with residual connections and ReLU
        for layer in self.layers:
            residual = x
            x = nn.relu(layer(x))
            x = x + residual  # Residual connection

        return self.output_proj(x)


class SimpleModelService:
    """Service for testing real model inference with MLX"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.vocab_size = 32000
        self.max_tokens = 128
        self.temperature = 0.7

        # Simple vocabulary for testing (in real implementation, load from model)
        self.vocab = {
            "<pad>": 0,
            "<unk>": 1,
            "<s>": 2,
            "</s>": 3,
            "def": 10,
            "class": 11,
            "import": 12,
            "from": 13,
            "if": 20,
            "else": 21,
            "for": 22,
            "while": 23,
            "print": 30,
            "return": 31,
            "self": 32,
            "True": 33,
            "False": 34,
            "(": 40,
            ")": 41,
            "{": 42,
            "}": 43,
            "[": 44,
            "]": 45,
            ":": 50,
            ",": 51,
            ".": 52,
            "=": 53,
            "+": 54,
            "-": 55,
            " ": 60,
            "\n": 61,
            "\t": 62,
        }

        # Reverse mapping
        self.idx_to_token = {v: k for k, v in self.vocab.items()}

        self.health_status = {
            "status": "not_initialized",
            "model_loaded": False,
            "memory_usage_mb": 0,
            "last_inference_time": None,
            "total_inferences": 0,
        }

    async def initialize(self) -> bool:
        """Initialize the model service"""
        try:
            logger.info("Initializing Simple Model Service...")

            # Create and initialize the model
            self.model = SimpleCodeModel(
                vocab_size=self.vocab_size, hidden_size=512, num_layers=6
            )

            # Initialize model parameters (random for testing)
            # In real implementation, you'd load trained weights
            self._initialize_weights()

            self.is_initialized = True
            self.health_status["status"] = "ready"
            self.health_status["model_loaded"] = True

            logger.info("Simple Model Service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize model service: {e}")
            self.health_status["status"] = "error"
            return False

    def _initialize_weights(self):
        """Initialize model weights (random for testing)"""
        # In a real implementation, you'd load pre-trained weights here
        # For testing, we'll use the default MLX initialization
        logger.info("Model weights initialized (random for testing)")

    def _tokenize(self, text: str) -> List[int]:
        """Simple tokenization for testing"""
        tokens = []
        i = 0
        while i < len(text):
            found = False
            # Try to match longer tokens first
            for length in range(3, 0, -1):
                if i + length <= len(text):
                    substr = text[i : i + length]
                    if substr in self.vocab:
                        tokens.append(self.vocab[substr])
                        i += length
                        found = True
                        break

            if not found:
                # Use unknown token
                tokens.append(self.vocab["<unk>"])
                i += 1

        return tokens

    def _detokenize(self, token_ids: List[int]) -> str:
        """Convert token IDs back to text"""
        tokens = []
        for token_id in token_ids:
            token = self.idx_to_token.get(token_id, "<unk>")
            tokens.append(token)
        return "".join(tokens)

    async def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using the model"""
        if not self.is_initialized or self.model is None:
            raise RuntimeError("Model service not initialized")

        if max_tokens is None:
            max_tokens = self.max_tokens

        start_time = time.time()

        try:
            # Tokenize input
            input_tokens = self._tokenize(prompt)
            if not input_tokens:
                input_tokens = [self.vocab["<s>"]]  # Start token

            # Convert to MLX array
            input_ids = mx.array(input_tokens)

            # Generate tokens
            generated_tokens = []
            current_input = input_ids

            for _ in range(max_tokens):
                # Forward pass
                with mx.stream(mx.gpu):
                    logits = self.model(current_input)

                # Get last token's logits
                last_logits = logits[-1]

                # Apply temperature sampling
                if self.temperature > 0:
                    probs = mx.softmax(last_logits / self.temperature)
                    # Simple sampling (in real implementation, use proper sampling)
                    next_token = mx.argmax(probs).item()
                else:
                    next_token = mx.argmax(last_logits).item()

                # Check for end token
                if next_token == self.vocab.get("</s>", -1):
                    break

                generated_tokens.append(next_token)

                # Update input for next iteration
                current_input = mx.concatenate([current_input, mx.array([next_token])])

            # Convert back to text
            generated_text = self._detokenize(generated_tokens)
            prompt + generated_text

            # Update metrics
            inference_time = time.time() - start_time
            self.health_status["last_inference_time"] = inference_time
            self.health_status["total_inferences"] += 1
            self.health_status["memory_usage_mb"] = mx.get_active_memory() / 1024 / 1024

            logger.info(
                f"Generated {len(generated_tokens)} tokens in {inference_time:.2f}s"
            )

            # For testing, provide a structured response
            return f"""**Generated Response** (Real MLX Model - {len(generated_tokens)} tokens)

Input: {prompt}

Generated: {generated_text}

---
*Model: SimpleCodeModel (6 layers, 512 hidden)*
*Generation time: {inference_time:.2f}s*
*Memory usage: {self.health_status['memory_usage_mb']:.2f}MB*
*Total inferences: {self.health_status['total_inferences']}*
"""

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        status = self.health_status.copy()
        status["is_initialized"] = self.is_initialized
        status["model_type"] = "SimpleCodeModel"
        status["vocab_size"] = self.vocab_size
        return status

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Simple Model Service...")
        self.model = None
        self.is_initialized = False
        self.health_status["status"] = "shutdown"
        self.health_status["model_loaded"] = False
        logger.info("Simple Model Service cleanup completed")
