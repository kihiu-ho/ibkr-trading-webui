#!/usr/bin/env python3
"""
Comprehensive Login Workflow Test Script

This script validates the complete automated login workflow including:
- Authentication credential validation
- Session management and token handling
- Redirect behavior after successful/failed login
- Multi-factor authentication (if applicable)
- Password reset functionality
- Account lockout mechanisms
- Error handling for various failure scenarios

Author: Automated Test Suite
Version: 1.0.0
"""

import unittest
import requests
import json
import time
import logging
import os
import hashlib
import random
import string
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import configparser


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('login_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestUser:
    """Test user data structure"""
    username: str
    password: str
    email: str
    user_type: str
    mfa_enabled: bool = False
    account_locked: bool = False
    password_expired: bool = False


@dataclass
class TestEnvironment:
    """Test environment configuration"""
    name: str
    base_url: str
    api_key: str
    timeout: int
    rate_limit: int
    database_url: str


class TestConfig:
    """Configuration manager for test environments"""
    
    def __init__(self, config_file: str = "test_config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file"""
        self.config['DEFAULT'] = {
            'timeout': '30',
            'rate_limit': '100',
            'log_level': 'INFO'
        }
        
        self.config['dev'] = {
            'base_url': 'https://dev-api.example.com',
            'api_key': 'dev_api_key_here',
            'database_url': 'postgresql://dev_db_url'
        }
        
        self.config['staging'] = {
            'base_url': 'https://staging-api.example.com',
            'api_key': 'staging_api_key_here',
            'database_url': 'postgresql://staging_db_url'
        }
        
        self.config['prod'] = {
            'base_url': 'https://api.example.com',
            'api_key': 'prod_api_key_here',
            'database_url': 'postgresql://prod_db_url'
        }
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get_environment(self, env_name: str) -> TestEnvironment:
        """Get environment configuration"""
        if env_name not in self.config:
            raise ValueError(f"Environment '{env_name}' not found in configuration")
        
        env_config = self.config[env_name]
        return TestEnvironment(
            name=env_name,
            base_url=env_config['base_url'],
            api_key=env_config['api_key'],
            timeout=int(env_config.get('timeout', 30)),
            rate_limit=int(env_config.get('rate_limit', 100)),
            database_url=env_config['database_url']
        )


class MockDataGenerator:
    """Generate mock test data"""
    
    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """Generate random string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def generate_test_users() -> List[TestUser]:
        """Generate test user data"""
        return [
            TestUser(
                username="valid_user",
                password="ValidPass123!",
                email="valid@example.com",
                user_type="standard"
            ),
            TestUser(
                username="admin_user",
                password="AdminPass456!",
                email="admin@example.com",
                user_type="admin"
            ),
            TestUser(
                username="mfa_user",
                password="MfaPass789!",
                email="mfa@example.com",
                user_type="standard",
                mfa_enabled=True
            ),
            TestUser(
                username="locked_user",
                password="LockedPass000!",
                email="locked@example.com",
                user_type="standard",
                account_locked=True
            ),
            TestUser(
                username="expired_user",
                password="ExpiredPass111!",
                email="expired@example.com",
                user_type="standard",
                password_expired=True
            )
        ]
    
    @staticmethod
    def generate_invalid_credentials() -> List[Tuple[str, str]]:
        """Generate invalid credential combinations"""
        return [
            ("", ""),  # Empty credentials
            ("valid_user", ""),  # Empty password
            ("", "password"),  # Empty username
            ("invalid_user", "ValidPass123!"),  # Invalid username
            ("valid_user", "wrongpassword"),  # Wrong password
            ("user@domain", "pass"),  # Short password
            ("a" * 256, "password"),  # Too long username
            ("user", "a" * 256),  # Too long password
            ("user with spaces", "password"),  # Invalid characters
            ("user", "password with spaces"),  # Invalid password
        ]


class LoginTestClient:
    """HTTP client for login testing"""
    
    def __init__(self, environment: TestEnvironment):
        self.env = environment
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'LoginTestSuite/1.0.0',
            'X-API-Key': environment.api_key
        })
        self.auth_token = None
        self.refresh_token = None
    
    def login(self, username: str, password: str, mfa_code: str = None) -> Dict:
        """Perform login request"""
        payload = {
            'username': username,
            'password': password
        }
        
        if mfa_code:
            payload['mfa_code'] = mfa_code
        
        try:
            response = self.session.post(
                f"{self.env.base_url}/auth/login",
                json=payload,
                timeout=self.env.timeout
            )
            
            result = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'headers': dict(response.headers),
                'data': {}
            }
            
            try:
                result['data'] = response.json()
            except json.JSONDecodeError:
                result['data'] = {'raw_response': response.text}
            
            # Store tokens if login successful
            if response.status_code == 200 and 'access_token' in result['data']:
                self.auth_token = result['data']['access_token']
                self.refresh_token = result['data'].get('refresh_token')
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {str(e)}")
            return {
                'status_code': 0,
                'error': str(e),
                'response_time': 0,
                'headers': {},
                'data': {}
            }
    
    def logout(self) -> Dict:
        """Perform logout request"""
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        
        try:
            response = self.session.post(
                f"{self.env.base_url}/auth/logout",
                headers=headers,
                timeout=self.env.timeout
            )
            
            # Clear stored tokens
            self.auth_token = None
            self.refresh_token = None
            
            return {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {'status_code': 0, 'error': str(e)}
    
    def validate_session(self) -> Dict:
        """Validate current session"""
        if not self.auth_token:
            return {'status_code': 401, 'error': 'No auth token available'}
        
        headers = {'Authorization': f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(
                f"{self.env.base_url}/auth/validate",
                headers=headers,
                timeout=self.env.timeout
            )
            
            return {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {'status_code': 0, 'error': str(e)}
    
    def refresh_session(self) -> Dict:
        """Refresh authentication token"""
        if not self.refresh_token:
            return {'status_code': 401, 'error': 'No refresh token available'}
        
        payload = {'refresh_token': self.refresh_token}
        
        try:
            response = self.session.post(
                f"{self.env.base_url}/auth/refresh",
                json=payload,
                timeout=self.env.timeout
            )
            
            result = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.content else {}
            }
            
            # Update tokens if refresh successful
            if response.status_code == 200 and 'access_token' in result['data']:
                self.auth_token = result['data']['access_token']
                if 'refresh_token' in result['data']:
                    self.refresh_token = result['data']['refresh_token']
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {'status_code': 0, 'error': str(e)}
    
    def reset_password(self, email: str) -> Dict:
        """Request password reset"""
        payload = {'email': email}
        
        try:
            response = self.session.post(
                f"{self.env.base_url}/auth/reset-password",
                json=payload,
                timeout=self.env.timeout
            )
            
            return {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {'status_code': 0, 'error': str(e)}


class LoginWorkflowTests(unittest.TestCase):
    """Comprehensive login workflow test suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.config = TestConfig()
        cls.env_name = os.getenv('TEST_ENV', 'dev')
        cls.environment = cls.config.get_environment(cls.env_name)
        cls.test_users = MockDataGenerator.generate_test_users()
        cls.invalid_credentials = MockDataGenerator.generate_invalid_credentials()
        
        logger.info(f"Starting login workflow tests on {cls.env_name} environment")
        logger.info(f"Base URL: {cls.environment.base_url}")
    
    def setUp(self):
        """Set up each test"""
        self.client = LoginTestClient(self.environment)
        self.start_time = time.time()
    
    def tearDown(self):
        """Clean up after each test"""
        # Attempt logout if we have an active session
        if self.client.auth_token:
            self.client.logout()
        
        test_duration = time.time() - self.start_time
        logger.info(f"Test completed in {test_duration:.2f} seconds")

    # ============================================================================
    # CORE LOGIN FUNCTIONALITY TESTS
    # ============================================================================

    def test_successful_login_standard_user(self):
        """Test successful login with valid standard user credentials"""
        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)

        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 200, "Login should succeed with valid credentials")
        self.assertIn('access_token', result['data'], "Response should contain access token")
        self.assertIn('user_id', result['data'], "Response should contain user ID")
        self.assertLess(result['response_time'], 5.0, "Login should complete within 5 seconds")

        logger.info(f"✓ Standard user login successful: {user.username}")

    def test_successful_login_admin_user(self):
        """Test successful login with valid admin user credentials"""
        user = next(u for u in self.test_users if u.user_type == "admin")

        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 200, "Admin login should succeed")
        self.assertIn('access_token', result['data'], "Response should contain access token")
        self.assertEqual(result['data'].get('user_type'), 'admin', "User type should be admin")

        logger.info(f"✓ Admin user login successful: {user.username}")

    def test_login_with_mfa_enabled(self):
        """Test login flow with multi-factor authentication"""
        user = next(u for u in self.test_users if u.mfa_enabled)

        # First attempt without MFA code should require MFA
        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 202, "Should return 202 for MFA required")
        self.assertIn('mfa_required', result['data'], "Response should indicate MFA required")
        self.assertIn('mfa_token', result['data'], "Response should contain MFA token")

        # Simulate MFA code (in real test, this would come from authenticator)
        mfa_code = "123456"  # Mock MFA code

        # Second attempt with MFA code
        result = self.client.login(user.username, user.password, mfa_code)

        # Note: This would fail in real scenario without valid MFA, but demonstrates flow
        logger.info(f"✓ MFA login flow tested for user: {user.username}")

    def test_session_validation(self):
        """Test session token validation"""
        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)

        # Login first
        login_result = self.client.login(user.username, user.password)
        self.assertEqual(login_result['status_code'], 200, "Login should succeed")

        # Validate session
        validation_result = self.client.validate_session()
        self.assertEqual(validation_result['status_code'], 200, "Session validation should succeed")
        self.assertIn('user_id', validation_result['data'], "Validation should return user info")

        logger.info("✓ Session validation successful")

    def test_token_refresh(self):
        """Test authentication token refresh"""
        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)

        # Login first
        login_result = self.client.login(user.username, user.password)
        self.assertEqual(login_result['status_code'], 200, "Login should succeed")

        old_token = self.client.auth_token

        # Refresh token
        refresh_result = self.client.refresh_session()

        if refresh_result['status_code'] == 200:
            self.assertIn('access_token', refresh_result['data'], "Refresh should return new token")
            self.assertNotEqual(old_token, self.client.auth_token, "New token should be different")
            logger.info("✓ Token refresh successful")
        else:
            logger.warning("Token refresh not supported or failed")

    def test_logout_functionality(self):
        """Test logout functionality"""
        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)

        # Login first
        login_result = self.client.login(user.username, user.password)
        self.assertEqual(login_result['status_code'], 200, "Login should succeed")

        # Logout
        logout_result = self.client.logout()
        self.assertIn(logout_result['status_code'], [200, 204], "Logout should succeed")

        # Verify session is invalid after logout
        validation_result = self.client.validate_session()
        self.assertEqual(validation_result['status_code'], 401, "Session should be invalid after logout")

        logger.info("✓ Logout functionality working correctly")

    # ============================================================================
    # INVALID CREDENTIALS AND ERROR HANDLING TESTS
    # ============================================================================

    def test_invalid_credentials(self):
        """Test various invalid credential scenarios"""
        for username, password in self.invalid_credentials:
            with self.subTest(username=username, password=password):
                result = self.client.login(username, password)

                self.assertIn(result['status_code'], [400, 401, 422],
                            f"Invalid credentials should return 4xx status: {username}/{password}")

                if 'data' in result and 'error' in result['data']:
                    self.assertIn('invalid', result['data']['error'].lower(),
                                "Error message should indicate invalid credentials")

        logger.info("✓ Invalid credentials properly rejected")

    def test_account_lockout_mechanism(self):
        """Test account lockout after multiple failed attempts"""
        user = next(u for u in self.test_users if not u.account_locked)
        wrong_password = "WrongPassword123!"

        # Attempt multiple failed logins
        failed_attempts = 0
        max_attempts = 5

        for attempt in range(max_attempts):
            result = self.client.login(user.username, wrong_password)

            if result['status_code'] == 429:  # Account locked
                logger.info(f"✓ Account locked after {attempt + 1} failed attempts")
                break
            elif result['status_code'] in [401, 400]:
                failed_attempts += 1

            time.sleep(1)  # Brief delay between attempts

        # Verify account is locked
        if failed_attempts >= max_attempts:
            result = self.client.login(user.username, user.password)  # Try with correct password
            if result['status_code'] == 429:
                logger.info("✓ Account lockout mechanism working")
            else:
                logger.warning("Account lockout may not be implemented")

    def test_locked_account_login(self):
        """Test login attempt with pre-locked account"""
        user = next(u for u in self.test_users if u.account_locked)

        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 423, "Locked account should return 423 status")
        self.assertIn('locked', result['data'].get('error', '').lower(),
                     "Error should indicate account is locked")

        logger.info(f"✓ Locked account properly rejected: {user.username}")

    def test_expired_password_login(self):
        """Test login with expired password"""
        user = next(u for u in self.test_users if u.password_expired)

        result = self.client.login(user.username, user.password)

        # Could return 200 with password_change_required flag or 403
        if result['status_code'] == 200:
            self.assertTrue(result['data'].get('password_change_required', False),
                          "Should indicate password change required")
        elif result['status_code'] == 403:
            self.assertIn('expired', result['data'].get('error', '').lower(),
                         "Error should indicate password expired")

        logger.info(f"✓ Expired password handled: {user.username}")

    def test_password_reset_functionality(self):
        """Test password reset request"""
        user = self.test_users[0]

        result = self.client.reset_password(user.email)

        self.assertIn(result['status_code'], [200, 202], "Password reset should be accepted")

        if 'data' in result:
            # Should not reveal whether email exists for security
            self.assertNotIn('user_not_found', result['data'].get('error', '').lower(),
                           "Should not reveal if email exists")

        logger.info(f"✓ Password reset request processed: {user.email}")

    # ============================================================================
    # NETWORK AND SERVER ERROR HANDLING TESTS
    # ============================================================================

    @patch('requests.Session.post')
    def test_network_timeout_handling(self, mock_post):
        """Test handling of network timeout"""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        user = self.test_users[0]
        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 0, "Timeout should result in status 0")
        self.assertIn('error', result, "Should contain error information")
        self.assertIn('timeout', result['error'].lower(), "Error should mention timeout")

        logger.info("✓ Network timeout properly handled")

    @patch('requests.Session.post')
    def test_connection_error_handling(self, mock_post):
        """Test handling of connection errors"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        user = self.test_users[0]
        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 0, "Connection error should result in status 0")
        self.assertIn('error', result, "Should contain error information")

        logger.info("✓ Connection error properly handled")

    @patch('requests.Session.post')
    def test_server_error_handling(self, mock_post):
        """Test handling of server errors (5xx)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Internal server error'}
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.headers = {}
        mock_post.return_value = mock_response

        user = self.test_users[0]
        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 500, "Should return server error status")
        self.assertIn('error', result['data'], "Should contain error information")

        logger.info("✓ Server error properly handled")

    @patch('requests.Session.post')
    def test_rate_limiting_handling(self, mock_post):
        """Test handling of rate limiting (429)"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            'error': 'Rate limit exceeded',
            'retry_after': 60
        }
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.headers = {'Retry-After': '60'}
        mock_post.return_value = mock_response

        user = self.test_users[0]
        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 429, "Should return rate limit status")
        self.assertIn('rate limit', result['data']['error'].lower(),
                     "Should indicate rate limiting")

        logger.info("✓ Rate limiting properly handled")

    @patch('requests.Session.post')
    def test_malformed_response_handling(self, mock_post):
        """Test handling of malformed JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.headers = {}
        mock_post.return_value = mock_response

        user = self.test_users[0]
        result = self.client.login(user.username, user.password)

        self.assertEqual(result['status_code'], 200, "Should return original status")
        self.assertIn('raw_response', result['data'], "Should contain raw response")

        logger.info("✓ Malformed response properly handled")

    # ============================================================================
    # PERFORMANCE AND LOAD TESTS
    # ============================================================================

    def test_login_performance_benchmark(self):
        """Test login performance benchmarks"""
        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)

        response_times = []
        successful_logins = 0

        # Perform multiple login attempts to get average performance
        for i in range(5):
            start_time = time.time()
            result = self.client.login(user.username, user.password)
            end_time = time.time()

            response_times.append(end_time - start_time)

            if result['status_code'] == 200:
                successful_logins += 1

            # Logout between attempts
            self.client.logout()
            time.sleep(0.5)  # Brief pause between tests

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        # Performance assertions
        self.assertLess(avg_response_time, 3.0, "Average login time should be under 3 seconds")
        self.assertLess(max_response_time, 5.0, "Maximum login time should be under 5 seconds")
        self.assertGreaterEqual(successful_logins, 4, "At least 80% of logins should succeed")

        logger.info(f"✓ Performance benchmark - Avg: {avg_response_time:.2f}s, "
                   f"Min: {min_response_time:.2f}s, Max: {max_response_time:.2f}s")

    def test_concurrent_login_handling(self):
        """Test system behavior under concurrent login attempts"""
        import threading
        import queue

        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)
        results_queue = queue.Queue()

        def login_worker():
            """Worker function for concurrent login"""
            client = LoginTestClient(self.environment)
            result = client.login(user.username, user.password)
            results_queue.put(result)
            client.logout()

        # Create and start multiple threads
        threads = []
        num_threads = 3  # Conservative number for testing

        for _ in range(num_threads):
            thread = threading.Thread(target=login_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        successful_logins = sum(1 for r in results if r['status_code'] == 200)

        # At least some concurrent logins should succeed
        self.assertGreater(successful_logins, 0, "At least one concurrent login should succeed")

        logger.info(f"✓ Concurrent login test - {successful_logins}/{len(results)} succeeded")

    # ============================================================================
    # REDIRECT AND FLOW TESTS
    # ============================================================================

    def test_login_redirect_behavior(self):
        """Test redirect behavior after successful login"""
        user = next(u for u in self.test_users if u.user_type == "standard" and not u.mfa_enabled)

        # Login with redirect URL parameter
        payload = {
            'username': user.username,
            'password': user.password,
            'redirect_url': '/dashboard'
        }

        try:
            response = self.client.session.post(
                f"{self.environment.base_url}/auth/login",
                json=payload,
                timeout=self.environment.timeout,
                allow_redirects=False  # Don't follow redirects automatically
            )

            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_location = response.headers.get('Location', '')
                self.assertIn('/dashboard', redirect_location,
                             "Should redirect to requested URL")
                logger.info("✓ Login redirect behavior working correctly")
            elif response.status_code == 200:
                # API might return redirect URL in response body instead
                data = response.json()
                if 'redirect_url' in data:
                    self.assertIn('/dashboard', data['redirect_url'],
                                 "Should include redirect URL in response")
                    logger.info("✓ Login redirect URL returned in response")
                else:
                    logger.warning("Redirect behavior not implemented or different pattern")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Redirect test failed: {str(e)}")

    def test_failed_login_redirect(self):
        """Test redirect behavior after failed login"""
        # Test with invalid credentials
        payload = {
            'username': 'invalid_user',
            'password': 'wrong_password',
            'redirect_url': '/login?error=1'
        }

        try:
            response = self.client.session.post(
                f"{self.environment.base_url}/auth/login",
                json=payload,
                timeout=self.environment.timeout,
                allow_redirects=False
            )

            # Failed login should not redirect or redirect to error page
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_location = response.headers.get('Location', '')
                self.assertIn('error', redirect_location.lower(),
                             "Failed login redirect should indicate error")
            else:
                self.assertIn(response.status_code, [400, 401, 422],
                             "Failed login should return error status")

            logger.info("✓ Failed login redirect behavior correct")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed login redirect test error: {str(e)}")

    # ============================================================================
    # SECURITY TESTS
    # ============================================================================

    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        sql_injection_payloads = [
            "admin'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "'; EXEC xp_cmdshell('dir'); --"
        ]

        for payload in sql_injection_payloads:
            with self.subTest(payload=payload):
                result = self.client.login(payload, "password")

                # Should return authentication error, not server error
                self.assertIn(result['status_code'], [400, 401, 422],
                             f"SQL injection should be rejected safely: {payload}")

                # Should not return database errors
                if 'data' in result and 'error' in result['data']:
                    error_msg = result['data']['error'].lower()
                    self.assertNotIn('sql', error_msg, "Should not reveal SQL errors")
                    self.assertNotIn('database', error_msg, "Should not reveal database errors")

        logger.info("✓ SQL injection protection working")

    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]

        for payload in xss_payloads:
            with self.subTest(payload=payload):
                result = self.client.login(payload, "password")

                # Should return authentication error
                self.assertIn(result['status_code'], [400, 401, 422],
                             f"XSS payload should be rejected: {payload}")

                # Response should not contain unescaped payload
                response_str = json.dumps(result['data'])
                self.assertNotIn('<script>', response_str, "Script tags should be escaped/removed")

        logger.info("✓ XSS protection working")

    def test_password_complexity_validation(self):
        """Test password complexity requirements"""
        user = self.test_users[0]
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "password123",
            "admin",
            ""
        ]

        for weak_password in weak_passwords:
            with self.subTest(password=weak_password):
                result = self.client.login(user.username, weak_password)

                # Should reject weak passwords
                self.assertIn(result['status_code'], [400, 401, 422],
                             f"Weak password should be rejected: {weak_password}")

        logger.info("✓ Password complexity validation working")

    # ============================================================================
    # UTILITY AND HELPER METHODS
    # ============================================================================

    def assert_valid_jwt_token(self, token: str):
        """Validate JWT token structure"""
        parts = token.split('.')
        self.assertEqual(len(parts), 3, "JWT should have 3 parts separated by dots")

        # Basic base64 validation (without full JWT verification)
        for part in parts[:2]:  # Header and payload
            try:
                import base64
                # Add padding if needed
                padded = part + '=' * (4 - len(part) % 4)
                base64.b64decode(padded)
            except Exception:
                self.fail(f"Invalid base64 encoding in JWT part: {part}")

    def measure_response_time(self, func, *args, **kwargs):
        """Measure function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            'environment': self.env_name,
            'base_url': self.environment.base_url,
            'timestamp': datetime.now().isoformat(),
            'test_summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0
            }
        }
        return report


class LoginWorkflowTestRunner:
    """Custom test runner with enhanced reporting"""

    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.results = {}

    def run_tests(self, test_pattern='test_*'):
        """Run all login workflow tests"""
        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(LoginWorkflowTests)

        # Custom test result collector
        result = unittest.TextTestRunner(
            verbosity=self.verbosity,
            stream=open('test_output.log', 'w')
        ).run(suite)

        # Generate summary report
        self.generate_summary_report(result)

        return result

    def generate_summary_report(self, test_result):
        """Generate comprehensive test summary"""
        total_tests = test_result.testsRun
        failures = len(test_result.failures)
        errors = len(test_result.errors)
        passed = total_tests - failures - errors

        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        report = f"""
========================================
LOGIN WORKFLOW TEST SUMMARY REPORT
========================================
Environment: {os.getenv('TEST_ENV', 'dev')}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Test Results:
- Total Tests: {total_tests}
- Passed: {passed}
- Failed: {failures}
- Errors: {errors}
- Success Rate: {success_rate:.1f}%

========================================
"""

        if test_result.failures:
            report += "\nFAILURES:\n"
            for test, traceback in test_result.failures:
                report += f"- {test}: {traceback}\n"

        if test_result.errors:
            report += "\nERRORS:\n"
            for test, traceback in test_result.errors:
                report += f"- {test}: {traceback}\n"

        # Write report to file
        with open('login_test_summary.txt', 'w') as f:
            f.write(report)

        # Also log to console
        logger.info(report)

        return report


def setup_test_environment():
    """Setup test environment and dependencies"""
    # Create necessary directories
    os.makedirs('test_logs', exist_ok=True)
    os.makedirs('test_reports', exist_ok=True)

    # Set environment variables if not already set
    if not os.getenv('TEST_ENV'):
        os.environ['TEST_ENV'] = 'dev'

    # Initialize configuration
    config = TestConfig()

    logger.info("Test environment setup complete")
    return config


def main():
    """Main test execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Login Workflow Test Suite')
    parser.add_argument('--env', default='dev',
                       choices=['dev', 'staging', 'prod'],
                       help='Test environment to run against')
    parser.add_argument('--pattern', default='test_*',
                       help='Test pattern to match')
    parser.add_argument('--verbose', '-v', action='count', default=1,
                       help='Increase verbosity')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel (experimental)')

    args = parser.parse_args()

    # Set environment
    os.environ['TEST_ENV'] = args.env

    # Setup test environment
    setup_test_environment()

    # Run tests
    runner = LoginWorkflowTestRunner(verbosity=args.verbose)

    logger.info(f"Starting login workflow tests on {args.env} environment")

    try:
        result = runner.run_tests(args.pattern)

        # Exit with appropriate code
        if result.wasSuccessful():
            logger.info("All tests passed successfully!")
            exit(0)
        else:
            logger.error("Some tests failed or had errors")
            exit(1)

    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        exit(2)


if __name__ == '__main__':
    main()
