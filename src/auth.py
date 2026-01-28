"""
Authentication module for Stock Market AI Agent Web UI.

Provides simple username/password authentication with secure password hashing.
"""

import os
import hashlib
import hmac
import streamlit as st
from typing import Optional, Tuple


class Authenticator:
    """Simple authentication handler for Streamlit apps."""
    
    def __init__(self):
        """Initialize authenticator with credentials from environment."""
        # Get credentials from environment variables
        self.username = os.getenv('AUTH_USERNAME', 'admin')
        self.password_hash = self._get_password_hash()
        
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = None
    
    def _get_password_hash(self) -> str:
        """Get password hash from environment or use default."""
        # Check if password hash is provided
        password_hash = os.getenv('AUTH_PASSWORD_HASH')
        if password_hash:
            return password_hash
        
        # Otherwise, hash the plain password from environment
        plain_password = os.getenv('AUTH_PASSWORD', 'changeme')
        return self._hash_password(plain_password)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        password_hash = self._hash_password(password)
        return hmac.compare_digest(password_hash, self.password_hash)
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Attempt to log in with provided credentials.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if username == self.username and self._verify_password(password):
            st.session_state.authenticated = True
            st.session_state.username = username
            return True, "Login successful!"
        else:
            return False, "Invalid username or password"
    
    def logout(self):
        """Log out the current user."""
        st.session_state.authenticated = False
        st.session_state.username = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('authenticated', False)
    
    def get_username(self) -> Optional[str]:
        """Get the current authenticated username."""
        return st.session_state.get('username')
    
    def require_authentication(self) -> bool:
        """
        Show login form if not authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        if self.is_authenticated():
            return True
        
        # Show login form
        st.markdown('<h1 style="text-align: center;">🔐 Stock Market AI Agent</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center;">Please log in to continue</h3>', unsafe_allow_html=True)
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("---")
            
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if username and password:
                        success, message = self.login(username, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter both username and password")
            
            st.markdown("---")
        
        return False


def show_logout_button():
    """Show logout button in sidebar."""
    auth = Authenticator()
    
    if auth.is_authenticated():
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 Logged in as: **{auth.get_username()}**")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            auth.logout()
            st.rerun()


def generate_password_hash(password: str) -> str:
    """
    Generate password hash for use in AUTH_PASSWORD_HASH environment variable.
    
    Args:
        password: Plain text password
        
    Returns:
        SHA-256 hash of the password
    """
    return hashlib.sha256(password.encode()).hexdigest()


# Example usage for generating password hash
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
        hash_value = generate_password_hash(password)
        print(f"Password hash for '{password}':")
        print(hash_value)
        print("\nAdd this to your .env file:")
        print(f"AUTH_PASSWORD_HASH={hash_value}")
    else:
        print("Usage: python src/auth.py <password>")
        print("Example: python src/auth.py mySecurePassword123")
