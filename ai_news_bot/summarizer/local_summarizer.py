"""
Local model summarizer implementation.

This module uses local HuggingFace transformers for summarization,
optimized for Raspberry Pi with quantization and memory management.
"""

from typing import Optional
import asyncio
import threading
import queue
import os
from pathlib import Path
import psutil

from .base import BaseSummarizer


class LocalSummarizer(BaseSummarizer):
    """Summarizer that uses local HuggingFace models optimized for Raspberry Pi."""
    
    def __init__(self, config) -> None:
        """Initialize local summarizer with Raspberry Pi optimizations."""
        super().__init__(config, "Local")
        
        self.model = None
        self.tokenizer = None
        self.model_name = config.local_model_name
        self.device = config.local_model_device
        self.precision = config.local_model_precision
        self.max_length = config.local_model_max_length
        self.batch_size = config.local_model_batch_size
        self.cache_dir = Path(config.local_model_cache_dir)
        self.use_quantization = config.local_model_use_quantization
        self.load_in_8bit = config.local_model_load_in_8bit
        self.load_in_4bit = config.local_model_load_in_4bit
        
        # Thread pool for CPU-intensive tasks
        self.executor = None
        
        # Memory monitoring
        self.memory_threshold = 0.85  # 85% memory usage threshold
        
        self.logger.info(f"Initializing local summarizer with model: {self.model_name}")
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the local summarization model with Raspberry Pi optimizations."""
        try:
            # Import here to make it optional
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BitsAndBytesConfig
            import torch
            
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Check available memory
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            self.logger.info(f"Available memory: {available_memory_gb:.2f} GB")
            
            # Determine optimal configuration based on available resources
            model_config = self._get_optimal_config(available_memory_gb)
            
            self.logger.info(f"Loading model {self.model_name} with config: {model_config}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                trust_remote_code=False
            )
            
            # Configure quantization if requested
            quantization_config = None
            if self.use_quantization and (self.load_in_8bit or self.load_in_4bit):
                try:
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=self.load_in_8bit,
                        load_in_4bit=self.load_in_4bit,
                        bnb_4bit_compute_dtype=torch.float16 if self.load_in_4bit else None,
                        bnb_4bit_use_double_quant=True if self.load_in_4bit else False,
                    )
                    self.logger.info("Quantization enabled")
                except ImportError:
                    self.logger.warning("bitsandbytes not available, disabling quantization")
                    quantization_config = None
            
            # Load model with optimizations
            model_kwargs = {
                "cache_dir": str(self.cache_dir),
                "trust_remote_code": False,
                "low_cpu_mem_usage": True,
                "torch_dtype": getattr(torch, self.precision) if hasattr(torch, self.precision) else torch.float32,
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
                model_kwargs["device_map"] = "auto"
            elif self.device != "auto":
                model_kwargs["device_map"] = None
            else:
                model_kwargs["device_map"] = "auto"
            
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # Move to device if not using device_map
            if not quantization_config and self.device != "auto":
                device = torch.device(self.device if torch.cuda.is_available() or self.device == "cpu" else "cpu")
                self.model = self.model.to(device)
                self.logger.info(f"Model moved to device: {device}")
            
            # Set to evaluation mode and optimize for inference
            self.model.eval()
            
            # Enable optimizations for inference
            if hasattr(torch, 'compile') and not quantization_config:
                try:
                    self.model = torch.compile(self.model, mode="reduce-overhead")
                    self.logger.info("Model compiled for faster inference")
                except Exception as e:
                    self.logger.warning(f"Could not compile model: {e}")
            
            # Memory cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("Local model loaded successfully")
            
        except ImportError as e:
            self.logger.error(f"Required packages not installed: {e}")
            self.logger.error("Install with: poetry install --extras local-models")
            raise
        
        except Exception as e:
            self.logger.error(f"Error loading local model: {e}")
            raise
    
    def _get_optimal_config(self, available_memory_gb: float) -> dict:
        """Get optimal model configuration based on available memory."""
        config = {}
        
        if available_memory_gb < 2:
            # Very low memory - use smallest models and aggressive optimizations
            config.update({
                "model_recommendation": "sshleifer/distilbart-cnn-6-6",
                "precision": "float16",
                "quantization": "4bit",
                "max_length": 512
            })
            self.logger.warning("Low memory detected, consider using distilbart model")
            
        elif available_memory_gb < 4:
            # Low memory - use quantization
            config.update({
                "precision": "float16",
                "quantization": "8bit",
                "max_length": 768
            })
            
        elif available_memory_gb < 8:
            # Medium memory - balanced settings
            config.update({
                "precision": "float16",
                "quantization": "optional",
                "max_length": 1024
            })
            
        else:
            # High memory - full precision
            config.update({
                "precision": "float32",
                "quantization": "none",
                "max_length": 1024
            })
        
        return config
    
    async def summarize(
        self, 
        title: str, 
        content: str, 
        source_url: Optional[str] = None
    ) -> str:
        """Summarize content using local model with memory monitoring."""
        if not self.model or not self.tokenizer:
            return f"Local model not available. Title: {title}"
        
        # Check memory usage before processing
        memory_percent = psutil.virtual_memory().percent / 100
        if memory_percent > self.memory_threshold:
            self.logger.warning(f"High memory usage ({memory_percent:.1%}), skipping local processing")
            return self._build_fallback_summary(title, content)
        
        try:
            # Prepare content with aggressive truncation for Pi
            cleaned_content = self._prepare_content_for_pi(title, content)
            
            self.logger.debug(f"Generating summary for: {title}")
            
            # Run model in thread to avoid blocking
            summary = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_summary_sync, cleaned_content
            )
            
            # Validate and post-process
            if not self._validate_summary(summary):
                self.logger.warning(f"Generated summary failed validation for: {title}")
                return self._build_fallback_summary(title, content)
            
            processed_summary = self._post_process_summary(summary)
            
            self.logger.info(f"Successfully generated summary for: {title}")
            return processed_summary
            
        except Exception as e:
            self.logger.error(f"Error in local summarization: {e}")
            return self._build_fallback_summary(title, content)
    
    def _generate_summary_sync(self, content: str) -> str:
        """Generate summary synchronously (runs in thread) with memory optimization."""
        try:
            import torch
        except ImportError:
            self.logger.error("PyTorch not available")
            return ""
        
        try:
            # Monitor memory during processing
            initial_memory = psutil.virtual_memory().percent
            
            # Prepare input with model-specific formatting
            if "bart" in self.model_name.lower():
                input_text = content  # BART doesn't need prefix
            elif "t5" in self.model_name.lower():
                input_text = f"summarize: {content}"
            elif "pegasus" in self.model_name.lower():
                input_text = content  # Pegasus doesn't need prefix
            else:
                input_text = f"summarize: {content}"
            
            # Tokenize with length limits
            max_input_length = min(self.max_length, 512)  # Conservative for Pi
            inputs = self.tokenizer(
                input_text,
                max_length=max_input_length,
                truncation=True,
                return_tensors="pt",
                padding=False
            )
            
            # Move inputs to same device as model
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate summary with conservative settings for Pi
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs["input_ids"],
                    attention_mask=inputs.get("attention_mask"),
                    max_length=min(200, max_input_length // 2),  # Conservative length
                    min_length=30,
                    length_penalty=1.2,
                    num_beams=2,  # Reduced beams for Pi
                    early_stopping=True,
                    no_repeat_ngram_size=2,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode summary
            summary = self.tokenizer.decode(
                summary_ids[0], 
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            # Memory cleanup
            del inputs, summary_ids
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Check memory usage after processing
            final_memory = psutil.virtual_memory().percent
            self.logger.debug(f"Memory usage: {initial_memory:.1f}% -> {final_memory:.1f}%")
            
            return summary.strip()
            
        except torch.cuda.OutOfMemoryError:
            self.logger.error("CUDA out of memory during summarization")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return ""
            
        except Exception as e:
            self.logger.error(f"Error in sync summary generation: {e}")
            return ""
    
    def _prepare_content_for_pi(self, title: str, content: str) -> str:
        """Prepare content for Raspberry Pi with aggressive optimization."""
        # More aggressive truncation for Pi
        cleaned_content = self._clean_text(content)
        
        # Very conservative limits for Pi
        max_chars = min(1500, self.max_length * 2)  # Much smaller for Pi
        if len(cleaned_content) > max_chars:
            # Try to cut at sentence boundary
            sentences = cleaned_content.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '. ') <= max_chars:
                    truncated += sentence + '. '
                else:
                    break
            
            if truncated:
                cleaned_content = truncated.strip()
            else:
                cleaned_content = cleaned_content[:max_chars] + "..."
            
            self.logger.debug(f"Truncated content to {len(cleaned_content)} characters for Pi")
        
        return cleaned_content
    
    def _build_fallback_summary(self, title: str, content: str) -> str:
        """Create a simple extractive summary as fallback."""
        sentences = content.split('.')
        
        # Take first few sentences up to a reasonable length
        summary_sentences = []
        total_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and total_length + len(sentence) < 200:  # Shorter for fallback
                summary_sentences.append(sentence)
                total_length += len(sentence)
            else:
                break
        
        if summary_sentences:
            return '. '.join(summary_sentences) + '.'
        else:
            return f"AI news update: {title}. Read full article for details."
    
    async def close(self) -> None:
        """Clean up model resources."""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        # Clear GPU cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        
        self.logger.info("Local model resources cleaned up")