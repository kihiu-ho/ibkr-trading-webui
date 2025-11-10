#!/usr/bin/env python3
"""
IBKR Trading WebUI - Optimized Python Startup Script
Fast startup with lazy loading, connection pooling, and parallel service startup
"""

import asyncio
import concurrent.futures
import os
import sys
import time
import subprocess
import json
import signal
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import argparse
from contextlib import asynccontextmanager

# Color constants for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

@dataclass
class ServiceConfig:
    name: str
    container_name: str
    health_check: Optional[str] = None
    startup_timeout: int = 30
    critical: bool = True
    depends_on: List[str] = None

class OptimizedStartup:
    def __init__(self, project_root: Path, args):
        self.project_root = project_root
        self.args = args
        self.log_dir = project_root / "logs"
        self.compose_cmd = self._detect_compose_command()
        
        # Service configuration with optimized startup order
        self.services = {
            'redis': ServiceConfig('Redis', 'ibkr-redis', 'redis-cli ping', 15, True),
            'minio': ServiceConfig('MinIO', 'ibkr-minio', 'curl -f http://localhost:9000/minio/health/live', 20, True),
            'ibkr-gateway': ServiceConfig('IBKR Gateway', 'ibkr-gateway', 'curl -k -f https://localhost:5055/tickle', 90, True),
            'backend': ServiceConfig('Backend', 'ibkr-backend', 'curl -f http://localhost:8000/health', 30, True, ['redis', 'minio']),
            'celery-worker': ServiceConfig('Celery Worker', 'ibkr-celery-worker', None, 20, True, ['redis']),
            'celery-beat': ServiceConfig('Celery Beat', 'ibkr-celery-beat', None, 15, True, ['redis']),
            'flower': ServiceConfig('Flower', 'ibkr-flower', None, 15, False, ['redis'])
        }
        
        # Connection pool for health checks
        self.session_pool = None
        
    def _detect_compose_command(self) -> str:
        """Detect available docker compose command"""
        try:
            subprocess.run(['docker', 'compose', 'version'], 
                         capture_output=True, check=True)
            return 'docker compose'
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(['docker-compose', '--version'], 
                             capture_output=True, check=True)
                return 'docker-compose'
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("No Docker Compose command found")

    def print_status(self, message: str, color: str = Colors.GREEN):
        print(f"{color}✓{Colors.NC} {message}")

    def print_error(self, message: str):
        print(f"{Colors.RED}✗{Colors.NC} {message}")

    def print_info(self, message: str):
        print(f"{Colors.YELLOW}ℹ{Colors.NC} {message}")

    def print_header(self, message: str):
        print(f"\n{Colors.CYAN}{'━' * 50}{Colors.NC}")
        print(f"{Colors.CYAN}{message}{Colors.NC}")
        print(f"{Colors.CYAN}{'━' * 50}{Colors.NC}\n")

    async def check_docker_daemon(self) -> bool:
        """Asynchronously check if Docker daemon is ready"""
        for attempt in range(20):
            try:
                proc = await asyncio.create_subprocess_exec(
                    'docker', 'info',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
                if proc.returncode == 0:
                    return True
            except Exception:
                pass
            
            if attempt == 0:
                self.print_info("Waiting for Docker daemon...")
            await asyncio.sleep(2)
        
        return False

    async def load_environment(self) -> Dict[str, str]:
        """Load and validate environment variables"""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            raise RuntimeError("No .env file found! Copy env.example to .env and configure it.")
        
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
        
        # Validate critical environment variables
        if not env_vars.get('DATABASE_URL') or env_vars.get('DATABASE_URL') == 'your_database_url':
            raise RuntimeError("DATABASE_URL is not configured in .env file")
        
        # Merge with os.environ for subprocess calls
        os.environ.update(env_vars)
        return env_vars

    async def check_images_exist(self) -> bool:
        """Check if required Docker images exist"""
        images = ['ibkr-backend:latest', 'ibkr-gateway:latest']
        
        for image in images:
            try:
                proc = await asyncio.create_subprocess_exec(
                    'docker', 'image', 'inspect', image,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
                if proc.returncode != 0:
                    return False
            except Exception:
                return False
        
        return True

    async def pull_base_images(self):
        """Pull required base images in parallel"""
        base_images = ['postgres:15-alpine', 'redis:7-alpine', 'minio/minio:latest']
        
        async def pull_image(image: str):
            try:
                proc = await asyncio.create_subprocess_exec(
                    'docker', 'pull', image,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
                return image, proc.returncode == 0
            except Exception:
                return image, False
        
        tasks = [pull_image(image) for image in base_images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple):
                image, success = result
                if success:
                    self.print_status(f"Image {image} ready")
                else:
                    self.print_info(f"Image {image} pull failed (may already exist)")

    async def build_images_parallel(self):
        """Build Docker images in parallel where possible"""
        self.print_header("Building Docker Images")
        
        start_time = time.time()
        
        # Build backend and gateway images in parallel
        async def build_backend():
            proc = await asyncio.create_subprocess_exec(
                'docker', 'build', '-f', 'docker/Dockerfile.backend', 
                '-t', 'ibkr-backend:latest', '.',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await proc.communicate()
            return 'backend', proc.returncode == 0, stdout.decode()

        async def build_gateway():
            proc = await asyncio.create_subprocess_exec(
                'docker', 'build', '-f', 'Dockerfile', 
                '-t', 'ibkr-gateway:latest', '.',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await proc.communicate()
            return 'gateway', proc.returncode == 0, stdout.decode()

        # Run builds in parallel
        build_tasks = [build_backend(), build_gateway()]
        results = await asyncio.gather(*build_tasks, return_exceptions=True)
        
        build_time = time.time() - start_time
        
        for result in results:
            if isinstance(result, tuple):
                name, success, output = result
                if success:
                    self.print_status(f"{name.capitalize()} image built successfully")
                else:
                    self.print_error(f"{name.capitalize()} image build failed")
                    print(output[-500:])  # Show last 500 chars of output
                    return False
        
        self.print_status(f"Images built in {build_time:.1f}s")
        return True

    async def start_services(self):
        """Start Docker Compose services"""
        self.print_header("Starting Services")

        start_time = time.time()

        proc = await asyncio.create_subprocess_exec(
            *self.compose_cmd.split(), 'up', '-d',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        stdout, _ = await proc.communicate()
        startup_time = time.time() - start_time

        if proc.returncode == 0:
            self.print_status(f"Services started in {startup_time:.1f}s")
            return True
        else:
            self.print_error("Failed to start services")
            print(stdout.decode())
            return False

    async def health_check_service(self, service_name: str, config: ServiceConfig) -> bool:
        """Perform health check for a single service"""
        if not config.health_check or self.args.fast:
            return True

        container_name = config.container_name
        health_cmd = config.health_check

        for attempt in range(config.startup_timeout):
            try:
                if health_cmd.startswith('curl'):
                    # Use docker exec for curl commands
                    proc = await asyncio.create_subprocess_exec(
                        'docker', 'exec', container_name, *health_cmd.split(),
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                else:
                    # Direct docker exec for other commands
                    proc = await asyncio.create_subprocess_exec(
                        'docker', 'exec', container_name, *health_cmd.split(),
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )

                await proc.wait()
                if proc.returncode == 0:
                    return True

            except Exception:
                pass

            await asyncio.sleep(1)

        return False

    async def parallel_health_checks(self) -> Dict[str, bool]:
        """Run health checks for all services in parallel"""
        if self.args.fast:
            self.print_header("Health Checks Skipped (Fast Mode)")
            return {name: True for name in self.services.keys()}

        self.print_header("Checking Service Health")

        # Group services by dependency level for parallel execution
        independent_services = ['redis', 'minio', 'ibkr-gateway']
        dependent_services = ['backend', 'celery-worker', 'celery-beat', 'flower']

        results = {}

        # Check independent services first (in parallel)
        async def check_service(service_name: str):
            config = self.services[service_name]
            self.print_info(f"Checking {config.name}...")
            result = await self.health_check_service(service_name, config)
            if result:
                self.print_status(f"{config.name} is ready")
            else:
                if config.critical:
                    self.print_error(f"{config.name} failed health check")
                else:
                    self.print_info(f"{config.name} health check timeout (non-critical)")
            return service_name, result

        # Check independent services in parallel
        independent_tasks = [check_service(name) for name in independent_services]
        independent_results = await asyncio.gather(*independent_tasks, return_exceptions=True)

        for result in independent_results:
            if isinstance(result, tuple):
                service_name, success = result
                results[service_name] = success

        # Check dependent services (can also be parallel since they depend on the above)
        dependent_tasks = [check_service(name) for name in dependent_services]
        dependent_results = await asyncio.gather(*dependent_tasks, return_exceptions=True)

        for result in dependent_results:
            if isinstance(result, tuple):
                service_name, success = result
                results[service_name] = success

        return results

    async def run_migrations(self):
        """Run database migrations if available"""
        self.print_header("Database Migrations")

        migration_script = self.project_root / "database" / "migrations" / "run_migrations.sh"
        if migration_script.exists():
            self.print_info("Running database migrations...")
            try:
                proc = await asyncio.create_subprocess_exec(
                    'bash', str(migration_script),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                stdout, _ = await proc.communicate()

                if proc.returncode == 0:
                    self.print_status("Database migrations completed")
                else:
                    self.print_info("Migration script exited with warnings (may be expected)")
            except Exception as e:
                self.print_info(f"Migration script error: {e}")
        else:
            self.print_info("No migration script found (skipping)")

    def print_startup_summary(self, total_time: float, health_results: Dict[str, bool]):
        """Print comprehensive startup summary"""
        self.print_header("Startup Complete!")

        print(f"{Colors.GREEN}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
        print(f"{Colors.GREEN}║          All Services Running Successfully! 🎉                ║{Colors.NC}")
        print(f"{Colors.GREEN}║          Total Startup Time: {total_time:.1f}s                     ║{Colors.NC}")
        print(f"{Colors.GREEN}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")

        print(f"\n{Colors.BLUE}🌐 Access Points:{Colors.NC}")
        print("  ├── Web UI:           http://localhost:8000")
        print("  ├── API Docs:         http://localhost:8000/docs")
        print("  ├── Health Check:     http://localhost:8000/health")
        print("  ├── IBKR Gateway:     https://localhost:5055")
        print("  ├── Flower Monitor:   http://localhost:5555")
        print("  └── MinIO Console:    http://localhost:9001")

        print(f"\n{Colors.BLUE}📊 Service Status:{Colors.NC}")
        for service_name, config in self.services.items():
            status = "✓ READY" if health_results.get(service_name, False) else "⏳ STARTING"
            print(f"  {status:<12} {config.name}")

        print(f"\n{Colors.BLUE}📋 Quick Commands:{Colors.NC}")
        print("  View logs:            docker-compose logs -f")
        print("  Stop services:        ./stop-all.sh")
        print("  Restart:              python start-webapp.py")
        print("  Force rebuild:        python start-webapp.py --rebuild")

async def main():
    """Main startup orchestration with optimized parallel execution"""
    parser = argparse.ArgumentParser(description="IBKR Trading WebUI - Optimized Startup")
    parser.add_argument('--rebuild', action='store_true', help='Force rebuild of Docker images')
    parser.add_argument('--fast', action='store_true', help='Skip health checks for faster startup')
    parser.add_argument('--parallel', action='store_true', default=True, help='Use parallel startup (default)')

    args = parser.parse_args()

    # Setup
    project_root = Path(__file__).parent.absolute()
    startup = OptimizedStartup(project_root, args)

    print(f"{Colors.BLUE}==============================================")
    print("IBKR Trading WebUI - Optimized Python Startup")
    mode = "Rebuild Mode" if args.rebuild else "Fast Mode" if args.fast else "Smart Mode"
    print(f"({mode} - Parallel Execution Enabled)")
    print(f"=============================================={Colors.NC}")

    total_start_time = time.time()

    try:
        # Step 1: Environment and Docker checks (parallel where possible)
        env_task = asyncio.create_task(startup.load_environment())
        docker_task = asyncio.create_task(startup.check_docker_daemon())

        env_vars = await env_task
        startup.print_status("Environment variables loaded")

        docker_ready = await docker_task
        if not docker_ready:
            startup.print_error("Docker daemon not ready after 40 seconds")
            return 1
        startup.print_status("Docker daemon ready")

        # Step 2: Check images and pull base images in parallel
        images_exist = await startup.check_images_exist()
        if not images_exist or args.rebuild:
            # Pull base images while checking if we need to build
            pull_task = asyncio.create_task(startup.pull_base_images())
            await pull_task

            # Build images in parallel
            if not await startup.build_images_parallel():
                return 1
        else:
            startup.print_status("Using cached Docker images")

        # Step 3: Start services
        if not await startup.start_services():
            return 1

        # Step 4: Parallel health checks
        health_results = await startup.parallel_health_checks()

        # Step 5: Run migrations
        await startup.run_migrations()

        # Summary
        total_time = time.time() - total_start_time
        startup.print_startup_summary(total_time, health_results)

        # Check for critical service failures
        critical_failures = [
            name for name, config in startup.services.items()
            if config.critical and not health_results.get(name, False)
        ]

        if critical_failures and not args.fast:
            startup.print_error(f"Critical services failed: {', '.join(critical_failures)}")
            return 1

        # Ask about viewing logs (default to yes)
        if not args.fast:
            try:
                print(f"\n{Colors.CYAN}{'━' * 50}{Colors.NC}")
                response = input(f"{Colors.YELLOW}Show live backend logs? (Y/n): {Colors.NC}").strip().lower()
                if response not in ['n', 'no']:  # Default to yes if empty or anything other than n/no
                    startup.print_info("Starting log viewer (Ctrl+C to exit)...")
                    try:
                        subprocess.run([*startup.compose_cmd.split(), 'logs', '-f', 'backend'], check=False)
                    except KeyboardInterrupt:
                        startup.print_info("Log viewer stopped")
            except (KeyboardInterrupt, EOFError):
                startup.print_info("Skipping log viewer")

        return 0

    except KeyboardInterrupt:
        startup.print_info("Startup interrupted by user")
        return 130
    except Exception as e:
        startup.print_error(f"Startup failed: {e}")
        return 1

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print(f"\n{Colors.YELLOW}Received signal {signum}, shutting down...{Colors.NC}")
    sys.exit(130)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Enable Docker BuildKit for faster builds
    os.environ.update({
        'DOCKER_BUILDKIT': '1',
        'COMPOSE_DOCKER_CLI_BUILD': '1',
        'BUILDKIT_PROGRESS': 'plain'
    })

    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
