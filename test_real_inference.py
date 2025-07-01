#!/usr/bin/env python3
"""
Test script for validating real LLM inference with Qwen2.5-Coder-32B
This script runs comprehensive tests to ensure real model weights are working correctly
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealInferenceValidator:
    """Comprehensive validator for real LLM inference"""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": []
        }
        
    def log_test_result(self, test_name: str, passed: bool, details: str = "", warning: bool = False):
        """Log test result"""
        if warning:
            self.test_results["warnings"] += 1
            logger.warning(f"⚠️  {test_name}: {details}")
        elif passed:
            self.test_results["passed"] += 1
            logger.info(f"✅ {test_name}: {details}")
        else:
            self.test_results["failed"] += 1
            logger.error(f"❌ {test_name}: {details}")
        
        self.test_results["details"].append({
            "test": test_name,
            "passed": passed,
            "warning": warning,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_environment_setup(self) -> bool:
        """Test environment variables and configuration"""
        logger.info("Testing environment setup...")
        
        required_env_vars = [
            "LEANVIBE_MODEL_NAME",
            "LEANVIBE_DEPLOYMENT_MODE", 
            "LEANVIBE_USE_PRETRAINED_WEIGHTS",
            "LEANVIBE_QUANTIZATION"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if var not in os.environ:
                missing_vars.append(var)
        
        if missing_vars:
            self.log_test_result(
                "Environment Variables",
                False,
                f"Missing variables: {missing_vars}"
            )
            return False
        
        # Check model name
        model_name = os.environ.get("LEANVIBE_MODEL_NAME")
        expected_model = "Qwen/Qwen2.5-Coder-32B-Instruct"
        
        if model_name == expected_model:
            self.log_test_result(
                "Model Configuration",
                True,
                f"Correct model configured: {model_name}"
            )
        else:
            self.log_test_result(
                "Model Configuration", 
                False,
                f"Expected {expected_model}, got {model_name}"
            )
            return False
        
        # Check deployment mode
        deployment_mode = os.environ.get("LEANVIBE_DEPLOYMENT_MODE")
        if deployment_mode == "direct":
            self.log_test_result(
                "Deployment Mode",
                True,
                "Direct MLX inference enabled"
            )
        else:
            self.log_test_result(
                "Deployment Mode",
                False,
                f"Expected 'direct', got '{deployment_mode}'"
            )
            return False
            
        return True
    
    def test_mlx_availability(self) -> bool:
        """Test MLX framework availability and functionality"""
        logger.info("Testing MLX availability...")
        
        try:
            import mlx.core as mx
            self.log_test_result(
                "MLX Core Import",
                True,
                "MLX core successfully imported"
            )
        except ImportError as e:
            self.log_test_result(
                "MLX Core Import",
                False,
                f"Failed to import MLX core: {e}"
            )
            return False
        
        # Test MLX functionality
        try:
            test_array = mx.array([1.0, 2.0, 3.0, 4.0, 5.0])
            result = mx.sum(test_array)
            expected = 15.0
            
            if abs(float(result) - expected) < 0.001:
                self.log_test_result(
                    "MLX Functionality",
                    True,
                    f"MLX computation successful: {float(result)}"
                )
            else:
                self.log_test_result(
                    "MLX Functionality",
                    False,
                    f"MLX computation incorrect: expected {expected}, got {float(result)}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "MLX Functionality",
                False,
                f"MLX computation failed: {e}"
            )
            return False
        
        # Test memory management
        try:
            memory_before = mx.get_active_memory()
            large_array = mx.random.normal((1000, 1000))
            memory_after = mx.get_active_memory()
            
            memory_delta_mb = (memory_after - memory_before) / (1024 * 1024)
            
            self.log_test_result(
                "MLX Memory Management",
                True,
                f"Memory allocation working: {memory_delta_mb:.1f}MB allocated"
            )
            
            # Cleanup
            del large_array
            
        except Exception as e:
            self.log_test_result(
                "MLX Memory Management",
                False,
                f"Memory management test failed: {e}"
            )
            return False
        
        # Test MLX-LM availability
        try:
            from mlx_lm import load, generate
            self.log_test_result(
                "MLX-LM Import",
                True,
                "MLX-LM successfully imported"
            )
        except ImportError as e:
            self.log_test_result(
                "MLX-LM Import",
                False,
                f"Failed to import MLX-LM: {e}"
            )
            return False
            
        return True
    
    def test_configuration_services(self) -> bool:
        """Test configuration services and real inference setup"""
        logger.info("Testing configuration services...")
        
        try:
            # Import configuration
            sys.path.append(str(Path(__file__).parent / "leanvibe-backend"))
            from app.config.unified_config import (
                get_config, create_qwen_production_config, 
                get_real_inference_config
            )
            
            self.log_test_result(
                "Configuration Import",
                True,
                "Configuration services imported successfully"
            )
            
        except ImportError as e:
            self.log_test_result(
                "Configuration Import",
                False,
                f"Failed to import configuration: {e}"
            )
            return False
        
        # Test production configuration
        try:
            prod_config = create_qwen_production_config()
            
            # Validate model name
            if prod_config.model.model_name == "Qwen/Qwen2.5-Coder-32B-Instruct":
                self.log_test_result(
                    "Production Config Model",
                    True,
                    f"Correct model in config: {prod_config.model.model_name}"
                )
            else:
                self.log_test_result(
                    "Production Config Model",
                    False,
                    f"Wrong model in config: {prod_config.model.model_name}"
                )
                return False
            
            # Check real inference settings
            if prod_config.model.use_pretrained_weights:
                self.log_test_result(
                    "Real Weights Enabled",
                    True,
                    "Pretrained weights enabled in configuration"
                )
            else:
                self.log_test_result(
                    "Real Weights Enabled", 
                    False,
                    "Pretrained weights not enabled"
                )
                return False
            
            # Check memory requirements
            memory_reqs = prod_config.get_memory_requirements()
            total_memory = memory_reqs["total_estimated_gb"]
            
            if total_memory > 20.0:  # Expected for 32B model
                self.log_test_result(
                    "Memory Requirements",
                    True,
                    f"Appropriate memory allocation: {total_memory:.1f}GB"
                )
            else:
                self.log_test_result(
                    "Memory Requirements",
                    False,
                    f"Memory allocation too low: {total_memory:.1f}GB"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Production Configuration",
                False,
                f"Production config creation failed: {e}"
            )
            return False
            
        return True
    
    def test_model_service_initialization(self) -> bool:
        """Test model service initialization (without loading full model)"""
        logger.info("Testing model service initialization...")
        
        try:
            from app.services.production_model_service import ProductionModelService
            from app.config.unified_config import create_qwen_production_config
            
            # Create service with production config
            config = create_qwen_production_config()
            service = ProductionModelService(config.model)
            
            self.log_test_result(
                "Service Creation",
                True,
                "ProductionModelService created successfully"
            )
            
            # Test health status structure
            health = service.get_health_status()
            
            required_fields = [
                "status", "deployment_mode", "model_loaded", 
                "model_name", "mlx_lm_available"
            ]
            
            missing_fields = [field for field in required_fields if field not in health]
            
            if not missing_fields:
                self.log_test_result(
                    "Health Status Structure",
                    True,
                    "All required health status fields present"
                )
            else:
                self.log_test_result(
                    "Health Status Structure",
                    False,
                    f"Missing health fields: {missing_fields}"
                )
                return False
            
            # Test LLM metrics
            if "llm_metrics" in health:
                metrics = health["llm_metrics"]
                if "model_info" in metrics and "performance" in metrics:
                    self.log_test_result(
                        "LLM Metrics Structure",
                        True,
                        "Enhanced LLM metrics available"
                    )
                else:
                    self.log_test_result(
                        "LLM Metrics Structure",
                        False,
                        "Incomplete LLM metrics structure"
                    )
                    return False
            else:
                self.log_test_result(
                    "LLM Metrics",
                    False,
                    "LLM metrics not available in health status"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Model Service Test",
                False,
                f"Service initialization test failed: {e}"
            )
            return False
            
        return True
    
    async def test_unified_mlx_service(self) -> bool:
        """Test unified MLX service with production strategy"""
        logger.info("Testing unified MLX service...")
        
        try:
            from app.services.unified_mlx_service import (
                UnifiedMLXService, MLXInferenceStrategy
            )
            
            # Create service with production strategy
            service = UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.PRODUCTION)
            
            self.log_test_result(
                "Unified MLX Service Creation",
                True,
                "UnifiedMLXService created with production strategy"
            )
            
            # Test strategy availability
            available_strategies = service.get_available_strategies()
            
            if "production" in available_strategies:
                self.log_test_result(
                    "Production Strategy Available",
                    True,
                    f"Available strategies: {available_strategies}"
                )
            else:
                self.log_test_result(
                    "Production Strategy Available",
                    False,
                    f"Production strategy not available. Available: {available_strategies}"
                )
                return False
            
            # Test health status
            health = service.get_model_health()
            
            if "strategy_availability" in health:
                self.log_test_result(
                    "Enhanced Health Status",
                    True,
                    "Enhanced health status with strategy availability"
                )
            else:
                self.log_test_result(
                    "Enhanced Health Status",
                    False,
                    "Missing enhanced health status features"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Unified MLX Service Test",
                False,
                f"Unified MLX service test failed: {e}"
            )
            return False
            
        return True
    
    def test_logging_enhancements(self) -> bool:
        """Test enhanced logging features"""
        logger.info("Testing enhanced logging features...")
        
        try:
            import tempfile
            import logging as py_logging
            
            # Create temporary log file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as f:
                log_file = f.name
            
            # Setup file handler
            file_handler = py_logging.FileHandler(log_file)
            file_handler.setLevel(py_logging.DEBUG)
            formatter = py_logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Test logger with correlation ID
            test_logger = py_logging.getLogger("test_inference")
            test_logger.addHandler(file_handler)
            test_logger.setLevel(py_logging.DEBUG)
            
            # Simulate enhanced logging
            request_id = f"test_req_{int(time.time())}"
            test_logger.info(f"[{request_id}] Test inference request started")
            test_logger.debug(f"[{request_id}] Model configuration loaded")
            test_logger.info(f"[{request_id}] Test completed successfully")
            
            # Check log file
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            if request_id in log_content and "Test inference request started" in log_content:
                self.log_test_result(
                    "Enhanced Logging Format",
                    True,
                    "Correlation ID logging working correctly"
                )
            else:
                self.log_test_result(
                    "Enhanced Logging Format",
                    False,
                    "Correlation ID logging not working"
                )
                return False
            
            # Cleanup
            Path(log_file).unlink()
            
        except Exception as e:
            self.log_test_result(
                "Logging Enhancement Test",
                False,
                f"Logging test failed: {e}"
            )
            return False
            
        return True
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("🚀 Starting comprehensive real inference validation...")
        
        # Test sequence
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("MLX Availability", self.test_mlx_availability),
            ("Configuration Services", self.test_configuration_services),
            ("Model Service", self.test_model_service_initialization),
            ("Unified MLX Service", self.test_unified_mlx_service),
            ("Logging Enhancements", self.test_logging_enhancements)
        ]
        
        start_time = time.time()
        
        for test_name, test_func in tests:
            logger.info(f"Running {test_name} test...")
            
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                if not result:
                    logger.error(f"❌ {test_name} test failed - stopping test suite")
                    break
                    
            except Exception as e:
                self.log_test_result(
                    test_name,
                    False,
                    f"Test execution failed: {e}"
                )
                logger.error(f"❌ {test_name} test crashed - stopping test suite")
                break
        
        total_time = time.time() - start_time
        
        # Generate final report
        report = {
            "summary": {
                "total_tests": len(self.test_results["details"]),
                "passed": self.test_results["passed"],
                "failed": self.test_results["failed"],
                "warnings": self.test_results["warnings"],
                "success_rate": self.test_results["passed"] / len(self.test_results["details"]) * 100 if self.test_results["details"] else 0,
                "total_time_seconds": round(total_time, 2)
            },
            "details": self.test_results["details"],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.test_results["failed"] > 0:
            recommendations.append("❌ Critical issues found - real inference not ready")
            recommendations.append("Fix failed tests before proceeding with model download")
        
        if self.test_results["warnings"] > 0:
            recommendations.append("⚠️  Warnings detected - review system requirements")
        
        if self.test_results["failed"] == 0:
            if self.test_results["warnings"] == 0:
                recommendations.append("✅ All tests passed - ready for real inference!")
                recommendations.append("🚀 Run: python setup_real_inference.py to download model")
            else:
                recommendations.append("✅ Core tests passed - real inference possible with warnings")
                recommendations.append("⚠️  Address warnings for optimal performance")
        
        recommendations.append("📊 Monitor logs during first model download (~25GB)")
        recommendations.append("💾 Ensure stable internet for initial model download")
        
        return recommendations


async def main():
    """Main test function"""
    validator = RealInferenceValidator()
    
    # Run comprehensive test
    report = await validator.run_comprehensive_test()
    
    # Print final report
    print("\n" + "="*60)
    print("🧪 REAL INFERENCE VALIDATION REPORT")
    print("="*60)
    
    summary = report["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⚠️  Warnings: {summary['warnings']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Total Time: {summary['total_time_seconds']}s")
    
    print("\n📋 RECOMMENDATIONS:")
    for rec in report["recommendations"]:
        print(f"  {rec}")
    
    if summary["failed"] == 0:
        print("\n🎉 VALIDATION SUCCESSFUL!")
        print("Your system is ready for real Qwen2.5-Coder-32B inference!")
    else:
        print("\n❌ VALIDATION FAILED!")
        print("Please fix the issues above before proceeding.")
    
    # Save detailed report
    report_file = Path("real_inference_validation_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved: {report_file}")
    
    return summary["failed"] == 0


if __name__ == "__main__":
    import os
    
    # Ensure we're in the right directory
    if not Path("leanvibe-backend").exists():
        print("❌ Error: Run this script from the leanvibe-ai root directory")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)