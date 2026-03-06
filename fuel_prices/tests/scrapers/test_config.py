"""
Unit tests for ScraperConfig.

Tests:
- Environment variable loading
- Default values
- Validation
- Configuration properties
"""

import pytest
import os
from fuel_prices.scrapers.config import ScraperConfig


class TestScraperConfig:
    """Test suite for ScraperConfig class."""
    
    def test_default_values(self):
        """Test configuration uses defaults when env vars not set."""
        config = ScraperConfig()
        
        assert config.timeout == ScraperConfig.DEFAULT_TIMEOUT
        assert config.max_retries == ScraperConfig.DEFAULT_MAX_RETRIES
        assert config.backoff_factor == ScraperConfig.DEFAULT_BACKOFF_FACTOR
        assert config.rate_limit == ScraperConfig.DEFAULT_RATE_LIMIT
        assert config.user_agent == ScraperConfig.DEFAULT_USER_AGENT
    
    def test_env_var_timeout(self, monkeypatch):
        """Test loading timeout from environment variable."""
        monkeypatch.setenv('FUEL_SCRAPER_TIMEOUT', '60')
        config = ScraperConfig()
        
        assert config.timeout == 60
    
    def test_env_var_max_retries(self, monkeypatch):
        """Test loading max retries from environment variable."""
        monkeypatch.setenv('FUEL_SCRAPER_MAX_RETRIES', '5')
        config = ScraperConfig()
        
        assert config.max_retries == 5
    
    def test_env_var_backoff_factor(self, monkeypatch):
        """Test loading backoff factor from environment variable."""
        monkeypatch.setenv('FUEL_SCRAPER_BACKOFF_FACTOR', '1.0')
        config = ScraperConfig()
        
        assert config.backoff_factor == 1.0
    
    def test_env_var_rate_limit(self, monkeypatch):
        """Test loading rate limit from environment variable."""
        monkeypatch.setenv('FUEL_SCRAPER_RATE_LIMIT', '2.0')
        config = ScraperConfig()
        
        assert config.rate_limit == 2.0
    
    def test_env_var_user_agent(self, monkeypatch):
        """Test loading user agent from environment variable."""
        custom_agent = 'MyCustomBot/1.0'
        monkeypatch.setenv('FUEL_SCRAPER_USER_AGENT', custom_agent)
        config = ScraperConfig()
        
        assert config.user_agent == custom_agent
    
    def test_invalid_timeout_too_low(self, monkeypatch):
        """Test validation fails for timeout below minimum."""
        monkeypatch.setenv('FUEL_SCRAPER_TIMEOUT', '1')
        
        with pytest.raises(ValueError, match='Timeout must be between'):
            ScraperConfig()
    
    def test_invalid_timeout_too_high(self, monkeypatch):
        """Test validation fails for timeout above maximum."""
        monkeypatch.setenv('FUEL_SCRAPER_TIMEOUT', '500')
        
        with pytest.raises(ValueError, match='Timeout must be between'):
            ScraperConfig()
    
    def test_invalid_retries_negative(self, monkeypatch):
        """Test validation fails for negative retries."""
        monkeypatch.setenv('FUEL_SCRAPER_MAX_RETRIES', '-1')
        
        with pytest.raises(ValueError, match='Max retries must be between'):
            ScraperConfig()
    
    def test_invalid_retries_too_high(self, monkeypatch):
        """Test validation fails for excessive retries."""
        monkeypatch.setenv('FUEL_SCRAPER_MAX_RETRIES', '20')
        
        with pytest.raises(ValueError, match='Max retries must be between'):
            ScraperConfig()
    
    def test_invalid_backoff_too_low(self, monkeypatch):
        """Test validation fails for backoff below minimum."""
        monkeypatch.setenv('FUEL_SCRAPER_BACKOFF_FACTOR', '0.05')
        
        with pytest.raises(ValueError, match='Backoff factor must be between'):
            ScraperConfig()
    
    def test_invalid_backoff_too_high(self, monkeypatch):
        """Test validation fails for backoff above maximum."""
        monkeypatch.setenv('FUEL_SCRAPER_BACKOFF_FACTOR', '10.0')
        
        with pytest.raises(ValueError, match='Backoff factor must be between'):
            ScraperConfig()
    
    def test_invalid_rate_limit_too_low(self, monkeypatch):
        """Test validation fails for rate limit below minimum."""
        monkeypatch.setenv('FUEL_SCRAPER_RATE_LIMIT', '0.05')
        
        with pytest.raises(ValueError, match='Rate limit must be between'):
            ScraperConfig()
    
    def test_invalid_rate_limit_too_high(self, monkeypatch):
        """Test validation fails for rate limit above maximum."""
        monkeypatch.setenv('FUEL_SCRAPER_RATE_LIMIT', '20.0')
        
        with pytest.raises(ValueError, match='Rate limit must be between'):
            ScraperConfig()
    
    def test_invalid_user_agent_empty(self, monkeypatch):
        """Test validation fails for empty user agent."""
        monkeypatch.setenv('FUEL_SCRAPER_USER_AGENT', '')
        
        with pytest.raises(ValueError, match='User agent cannot be empty'):
            ScraperConfig()
    
    def test_invalid_user_agent_whitespace(self, monkeypatch):
        """Test validation fails for whitespace-only user agent."""
        monkeypatch.setenv('FUEL_SCRAPER_USER_AGENT', '   ')
        
        with pytest.raises(ValueError, match='User agent cannot be empty'):
            ScraperConfig()
    
    def test_invalid_env_var_format_int(self, monkeypatch):
        """Test invalid integer format falls back to default."""
        monkeypatch.setenv('FUEL_SCRAPER_TIMEOUT', 'invalid')
        config = ScraperConfig()
        
        # Should use default since parsing failed
        assert config.timeout == ScraperConfig.DEFAULT_TIMEOUT
    
    def test_invalid_env_var_format_float(self, monkeypatch):
        """Test invalid float format falls back to default."""
        monkeypatch.setenv('FUEL_SCRAPER_RATE_LIMIT', 'invalid')
        config = ScraperConfig()
        
        # Should use default since parsing failed
        assert config.rate_limit == ScraperConfig.DEFAULT_RATE_LIMIT
    
    def test_config_repr(self):
        """Test string representation of config."""
        config = ScraperConfig()
        repr_str = repr(config)
        
        assert 'ScraperConfig' in repr_str
        assert 'timeout' in repr_str
        assert 'max_retries' in repr_str
        assert 'backoff_factor' in repr_str
        assert 'rate_limit' in repr_str
    
    def test_properties_are_readonly(self):
        """Test that config properties are read-only."""
        config = ScraperConfig()
        
        # Properties should not have setters
        with pytest.raises(AttributeError):
            config.timeout = 100
        
        with pytest.raises(AttributeError):
            config.max_retries = 10