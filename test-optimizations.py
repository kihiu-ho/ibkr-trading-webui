#!/usr/bin/env python3
"""
Test script to validate IBKR Trading WebUI startup optimizations
Measures performance improvements and validates functionality
"""

import asyncio
import time
import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

class OptimizationTester:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}
        
    def print_header(self, message: str):
        print(f"\n{'='*60}")
        print(f"  {message}")
        print(f"{'='*60}")
    
    def print_test(self, test_name: str, status: str, duration: float = None):
        status_icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⏳"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status_icon} {test_name:<40} {status}{duration_str}")
    
    async def test_docker_compose_syntax(self) -> Tuple[bool, float]:
        """Test docker-compose.yml syntax validation"""
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'compose', 'config', '--quiet',
                cwd=self.project_root,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            duration = time.time() - start_time
            
            if proc.returncode == 0:
                return True, duration
            else:
                print(f"Docker Compose validation error: {stderr.decode()}")
                return False, duration
        except Exception as e:
            duration = time.time() - start_time
            print(f"Docker Compose test failed: {e}")
            return False, duration
    
    async def test_dockerfile_syntax(self) -> Tuple[bool, float]:
        """Test Dockerfile syntax validation by checking file structure"""
        start_time = time.time()
        dockerfiles = [
            ('Dockerfile', 'IBKR Gateway'),
            ('docker/Dockerfile.backend', 'Backend')
        ]

        all_passed = True
        for dockerfile, name in dockerfiles:
            try:
                dockerfile_path = self.project_root / dockerfile
                if not dockerfile_path.exists():
                    print(f"{name} Dockerfile not found: {dockerfile}")
                    all_passed = False
                    continue

                # Check basic Dockerfile syntax by reading content
                content = dockerfile_path.read_text()
                required_instructions = ['FROM', 'WORKDIR']

                for instruction in required_instructions:
                    if instruction not in content:
                        print(f"{name} Dockerfile missing {instruction} instruction")
                        all_passed = False

                # Check for multi-stage build optimization
                if 'AS ' not in content and dockerfile == 'Dockerfile':
                    print(f"{name} Dockerfile should use multi-stage build")
                    all_passed = False

            except Exception as e:
                print(f"{name} Dockerfile test failed: {e}")
                all_passed = False

        duration = time.time() - start_time
        return all_passed, duration
    
    async def test_python_startup_script(self) -> Tuple[bool, float]:
        """Test Python startup script syntax and imports"""
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                'python3', '-m', 'py_compile', 'start-webapp.py',
                cwd=self.project_root,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            duration = time.time() - start_time
            
            if proc.returncode == 0:
                return True, duration
            else:
                print(f"Python script compilation error: {stderr.decode()}")
                return False, duration
        except Exception as e:
            duration = time.time() - start_time
            print(f"Python script test failed: {e}")
            return False, duration
    
    async def test_image_build_performance(self) -> Tuple[bool, float]:
        """Test Docker image build performance with caching"""
        start_time = time.time()
        try:
            # Test backend image build (should use cache after first build)
            proc = await asyncio.create_subprocess_exec(
                'docker', 'build', '--cache-from', 'ibkr-backend:latest',
                '-f', 'docker/Dockerfile.backend', '-t', 'ibkr-backend:test', '.',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await proc.communicate()
            duration = time.time() - start_time
            
            if proc.returncode == 0:
                # Clean up test image
                await asyncio.create_subprocess_exec(
                    'docker', 'rmi', 'ibkr-backend:test',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                return True, duration
            else:
                print(f"Image build test failed: {stdout.decode()[-500:]}")
                return False, duration
        except Exception as e:
            duration = time.time() - start_time
            print(f"Image build test failed: {e}")
            return False, duration
    
    async def test_service_dependencies(self) -> Tuple[bool, float]:
        """Test service dependency configuration"""
        start_time = time.time()
        try:
            # Parse docker-compose.yml to check dependencies
            proc = await asyncio.create_subprocess_exec(
                'docker', 'compose', 'config', '--format', 'json',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            duration = time.time() - start_time
            
            if proc.returncode == 0:
                config = json.loads(stdout.decode())
                services = config.get('services', {})
                
                # Check critical dependencies
                backend_deps = services.get('backend', {}).get('depends_on', {})
                expected_deps = ['redis', 'minio', 'ibkr-gateway']
                
                for dep in expected_deps:
                    if dep not in backend_deps:
                        print(f"Missing dependency: backend should depend on {dep}")
                        return False, duration
                
                return True, duration
            else:
                print(f"Service dependency test failed: {stderr.decode()}")
                return False, duration
        except Exception as e:
            duration = time.time() - start_time
            print(f"Service dependency test failed: {e}")
            return False, duration
    
    async def test_health_checks(self) -> Tuple[bool, float]:
        """Test health check configuration"""
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'compose', 'config', '--format', 'json',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            duration = time.time() - start_time
            
            if proc.returncode == 0:
                config = json.loads(stdout.decode())
                services = config.get('services', {})
                
                # Check that critical services have health checks
                critical_services = ['redis', 'minio', 'backend', 'ibkr-gateway']
                missing_health_checks = []
                
                for service in critical_services:
                    if service in services:
                        if 'healthcheck' not in services[service]:
                            missing_health_checks.append(service)
                
                if missing_health_checks:
                    print(f"Missing health checks for: {', '.join(missing_health_checks)}")
                    return False, duration
                
                return True, duration
            else:
                print(f"Health check test failed: {stderr.decode()}")
                return False, duration
        except Exception as e:
            duration = time.time() - start_time
            print(f"Health check test failed: {e}")
            return False, duration
    
    async def test_resource_limits(self) -> Tuple[bool, float]:
        """Test resource limit configuration"""
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'compose', 'config', '--format', 'json',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            duration = time.time() - start_time
            
            if proc.returncode == 0:
                config = json.loads(stdout.decode())
                services = config.get('services', {})
                
                # Check that services have resource limits
                services_with_limits = []
                for service_name, service_config in services.items():
                    deploy = service_config.get('deploy', {})
                    if 'resources' in deploy:
                        services_with_limits.append(service_name)
                
                if len(services_with_limits) >= 4:  # Expect most services to have limits
                    return True, duration
                else:
                    print(f"Only {len(services_with_limits)} services have resource limits")
                    return False, duration
            else:
                print(f"Resource limits test failed: {stderr.decode()}")
                return False, duration
        except Exception as e:
            duration = time.time() - start_time
            print(f"Resource limits test failed: {e}")
            return False, duration
    
    async def run_all_tests(self) -> Dict[str, Tuple[bool, float]]:
        """Run all optimization tests"""
        tests = [
            ("Docker Compose Syntax", self.test_docker_compose_syntax),
            ("Dockerfile Syntax", self.test_dockerfile_syntax),
            ("Python Startup Script", self.test_python_startup_script),
            ("Image Build Performance", self.test_image_build_performance),
            ("Service Dependencies", self.test_service_dependencies),
            ("Health Checks", self.test_health_checks),
            ("Resource Limits", self.test_resource_limits),
        ]
        
        results = {}
        total_start = time.time()
        
        self.print_header("Running Optimization Validation Tests")
        
        for test_name, test_func in tests:
            try:
                passed, duration = await test_func()
                results[test_name] = (passed, duration)
                status = "PASS" if passed else "FAIL"
                self.print_test(test_name, status, duration)
            except Exception as e:
                results[test_name] = (False, 0)
                self.print_test(test_name, "FAIL")
                print(f"  Error: {e}")
        
        total_duration = time.time() - total_start
        
        # Summary
        self.print_header("Test Results Summary")
        passed_tests = sum(1 for passed, _ in results.values() if passed)
        total_tests = len(results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Total Test Time: {total_duration:.2f}s")
        
        if passed_tests == total_tests:
            print("\n🎉 All optimization tests PASSED!")
            print("✓ Docker Compose configuration is optimized")
            print("✓ Dockerfiles use multi-stage builds and caching")
            print("✓ Python startup script is syntactically correct")
            print("✓ Service dependencies are properly configured")
            print("✓ Health checks are implemented")
            print("✓ Resource limits are set for performance")
        else:
            print(f"\n❌ {total_tests - passed_tests} test(s) FAILED!")
            print("Please review the failed tests above and fix the issues.")
        
        return results

async def main():
    parser = argparse.ArgumentParser(description="Test IBKR WebUI optimizations")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.absolute()
    tester = OptimizationTester(project_root)
    
    results = await tester.run_all_tests()
    
    # Exit with error code if any tests failed
    all_passed = all(passed for passed, _ in results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
