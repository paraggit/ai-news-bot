"""
Model optimization utilities for Raspberry Pi deployment.

This module provides utilities for optimizing local models for 
ARM64 architecture and limited memory environments.
"""

import psutil
import platform
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ModelOptimizer:
    """Utility class for optimizing model configuration for Raspberry Pi."""
    
    def __init__(self):
        """Initialize the model optimizer."""
        self.system_info = self._get_system_info()
        self.memory_info = self._get_memory_info()
        self.recommended_models = self._get_model_recommendations()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for optimization decisions."""
        return {
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "system": platform.system(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    def _get_memory_info(self) -> Dict[str, float]:
        """Get memory information in GB."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_ram_gb": memory.total / (1024**3),
            "available_ram_gb": memory.available / (1024**3),
            "used_ram_gb": memory.used / (1024**3),
            "ram_percent": memory.percent,
            "total_swap_gb": swap.total / (1024**3),
            "free_swap_gb": swap.free / (1024**3)
        }
    
    def _get_model_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """Get model recommendations based on memory and performance."""
        return {
            "ultra_light": {
                "models": ["sshleifer/distilbart-cnn-6-6", "google/pegasus-xsum"],
                "memory_requirement_gb": 0.5,
                "description": "Smallest models for very limited memory",
                "quality": "basic",
                "speed": "fastest"
            },
            "light": {
                "models": ["sshleifer/distilbart-cnn-12-6", "facebook/bart-large-cnn"],
                "memory_requirement_gb": 1.5,
                "description": "Balanced models for moderate memory",
                "quality": "good",
                "speed": "fast"
            },
            "standard": {
                "models": ["facebook/bart-large-cnn", "google/pegasus-cnn_dailymail"],
                "memory_requirement_gb": 3.0,
                "description": "Standard models for good memory availability",
                "quality": "high",
                "speed": "moderate"
            },
            "heavy": {
                "models": ["microsoft/DialoGPT-large", "t5-base"],
                "memory_requirement_gb": 6.0,
                "description": "Large models for high-memory systems",
                "quality": "highest",
                "speed": "slow"
            }
        }
    
    def get_optimal_config(self) -> Dict[str, Any]:
        """Get optimal configuration based on system resources."""
        available_memory = self.memory_info["available_ram_gb"]
        total_memory = self.memory_info["total_ram_gb"]
        
        logger.info(f"System: {self.system_info['architecture']} with {total_memory:.1f}GB RAM")
        logger.info(f"Available memory: {available_memory:.1f}GB")
        
        # Determine optimal configuration tier
        if available_memory < 1.0:
            tier = "ultra_light"
            config = {
                "precision": "float16",
                "quantization": True,
                "load_in_4bit": True,
                "max_length": 256,
                "batch_size": 1,
                "num_beams": 1,
                "recommended_model": "sshleifer/distilbart-cnn-6-6"
            }
        elif available_memory < 2.0:
            tier = "light"
            config = {
                "precision": "float16",
                "quantization": True,
                "load_in_8bit": True,
                "max_length": 512,
                "batch_size": 1,
                "num_beams": 2,
                "recommended_model": "sshleifer/distilbart-cnn-12-6"
            }
        elif available_memory < 4.0:
            tier = "standard"
            config = {
                "precision": "float16",
                "quantization": False,
                "load_in_8bit": False,
                "max_length": 1024,
                "batch_size": 1,
                "num_beams": 2,
                "recommended_model": "facebook/bart-large-cnn"
            }
        else:
            tier = "heavy"
            config = {
                "precision": "float32",
                "quantization": False,
                "load_in_8bit": False,
                "max_length": 1024,
                "batch_size": 1,
                "num_beams": 4,
                "recommended_model": "facebook/bart-large-cnn"
            }
        
        # Add tier information
        config.update({
            "tier": tier,
            "tier_info": self.recommended_models[tier],
            "system_info": self.system_info,
            "memory_info": self.memory_info
        })
        
        logger.info(f"Recommended tier: {tier}")
        logger.info(f"Recommended model: {config['recommended_model']}")
        
        return config
    
    def validate_model_requirements(self, model_name: str) -> Dict[str, Any]:
        """Validate if a model can run on current system."""
        validation = {
            "can_run": False,
            "warnings": [],
            "recommendations": []
        }
        
        # Estimate memory requirements based on model name
        estimated_memory = self._estimate_model_memory(model_name)
        available_memory = self.memory_info["available_ram_gb"]
        
        if estimated_memory > available_memory:
            validation["warnings"].append(
                f"Model may require {estimated_memory:.1f}GB but only {available_memory:.1f}GB available"
            )
            validation["recommendations"].append("Consider using quantization or a smaller model")
        else:
            validation["can_run"] = True
        
        # Check for ARM64 compatibility
        if self.system_info["architecture"] in ["aarch64", "arm64"]:
            validation["recommendations"].append("Consider using ARM64-optimized PyTorch")
        
        # Memory efficiency recommendations
        if available_memory < 2.0:
            validation["recommendations"].extend([
                "Enable 4-bit quantization for memory efficiency",
                "Use batch_size=1",
                "Set max_length=512 or lower",
                "Consider distilbart models for better performance"
            ])
        elif available_memory < 4.0:
            validation["recommendations"].extend([
                "Enable 8-bit quantization for better memory usage",
                "Use float16 precision"
            ])
        
        return validation
    
    def _estimate_model_memory(self, model_name: str) -> float:
        """Estimate memory requirements for a model (in GB)."""
        # Rough estimates based on common models
        memory_estimates = {
            "sshleifer/distilbart-cnn-6-6": 0.4,
            "sshleifer/distilbart-cnn-12-6": 0.8,
            "facebook/bart-large-cnn": 1.6,
            "google/pegasus-xsum": 0.6,
            "google/pegasus-cnn_dailymail": 2.2,
            "t5-small": 0.3,
            "t5-base": 0.9,
            "t5-large": 3.0,
        }
        
        # Default estimate for unknown models
        default_estimate = 1.5
        
        return memory_estimates.get(model_name, default_estimate)
    
    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations for Raspberry Pi."""
        recommendations = []
        
        # CPU-specific recommendations
        cpu_count = self.system_info.get("cpu_count", 1)
        if cpu_count <= 4:
            recommendations.append("Consider using batch_size=1 for single-threaded inference")
            recommendations.append("Enable torch.set_num_threads(1) for better CPU utilization")
        
        # Memory-specific recommendations
        if self.memory_info["total_ram_gb"] <= 4:
            recommendations.extend([
                "Enable model quantization to reduce memory usage",
                "Use gradient checkpointing if training",
                "Consider model pruning for production deployment"
            ])
        
        # ARM64-specific recommendations
        if self.system_info["architecture"] in ["aarch64", "arm64"]:
            recommendations.extend([
                "Use ARM64-optimized PyTorch builds when available",
                "Consider ONNX Runtime for better ARM performance",
                "Enable CPU-specific optimizations (NEON, etc.)"
            ])
        
        # Storage recommendations
        recommendations.extend([
            "Store models on fast storage (SSD preferred over SD card)",
            "Use model caching to avoid re-downloading",
            "Consider model compression for storage efficiency"
        ])
        
        return recommendations
    
    def monitor_resource_usage(self) -> Dict[str, float]:
        """Monitor current resource usage."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get temperature if available (Raspberry Pi specific)
        temperature = None
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temperature = float(f.read()) / 1000.0  # Convert to Celsius
        except (FileNotFoundError, ValueError, PermissionError):
            pass
        
        usage = {
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
        }
        
        if temperature:
            usage["temperature_celsius"] = temperature
        
        return usage
    
    def get_model_download_instructions(self, model_name: str) -> Dict[str, Any]:
        """Get instructions for downloading and setting up a model."""
        return {
            "model_name": model_name,
            "download_command": f"huggingface-cli download {model_name}",
            "cache_location": "~/.cache/huggingface/transformers/",
            "estimated_size": f"{self._estimate_model_memory(model_name):.1f}GB",
            "requirements": [
                "transformers>=4.20.0",
                "torch>=1.12.0",
                "tokenizers>=0.13.0"
            ],
            "optional_optimizations": [
                "accelerate (for device_map='auto')",
                "bitsandbytes (for quantization)",
                "optimum (for ONNX conversion)"
            ]
        }


def create_model_config_file(output_path: str = "./model_config.json") -> None:
    """Create a model configuration file based on current system."""
    import json
    
    optimizer = ModelOptimizer()
    config = optimizer.get_optimal_config()
    
    # Add additional recommendations
    config["performance_tips"] = optimizer.get_performance_recommendations()
    config["resource_usage"] = optimizer.monitor_resource_usage()
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2, default=str)
    
    logger.info(f"Model configuration saved to {output_path}")


if __name__ == "__main__":
    # Command-line utility for system analysis
    optimizer = ModelOptimizer()
    
    print("=== Raspberry Pi Model Optimization Analysis ===")
    print(f"Architecture: {optimizer.system_info['architecture']}")
    print(f"Total RAM: {optimizer.memory_info['total_ram_gb']:.1f}GB")
    print(f"Available RAM: {optimizer.memory_info['available_ram_gb']:.1f}GB")
    print()
    
    config = optimizer.get_optimal_config()
    print(f"Recommended Tier: {config['tier']}")
    print(f"Recommended Model: {config['recommended_model']}")
    print(f"Precision: {config['precision']}")
    print(f"Quantization: {config['quantization']}")
    print()
    
    print("Performance Recommendations:")
    for tip in optimizer.get_performance_recommendations():
        print(f"  • {tip}")
    print()
    
    # Create config file
    create_model_config_file()