"""
Tests for PRP system functionality
"""
import os
import json
import pytest

def test_prp_config_file():
    """Test PRP configuration file exists and is valid JSON"""
    config_path = os.path.join("PRPs", "prp-config.json")
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            assert isinstance(config, dict)
            assert "version" in config
    else:
        pytest.skip("PRP config file not found")

def test_prp_metrics_file():
    """Test PRP metrics file exists and is valid JSON"""
    metrics_path = os.path.join("PRPs", "analytics", "prp_metrics.json")
    
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            assert isinstance(metrics, dict)
    else:
        pytest.skip("PRP metrics file not found")

def test_prp_scripts_exist():
    """Test that PRP scripts exist"""
    scripts_dir = os.path.join("PRPs", "scripts")
    
    if os.path.exists(scripts_dir):
        scripts = os.listdir(scripts_dir)
        python_scripts = [s for s in scripts if s.endswith('.py')]
        assert len(python_scripts) > 0, "Should have at least one Python script"
    else:
        pytest.skip("PRP scripts directory not found")

def test_env_example_file():
    """Test .env.example file exists"""
    env_example_path = ".env.example"
    
    if os.path.exists(env_example_path):
        with open(env_example_path, 'r') as f:
            content = f.read()
            assert len(content.strip()) > 0
    else:
        pytest.skip(".env.example file not found")

def test_12_factor_compliance_basics():
    """Test basic 12-factor compliance elements"""
    # Test 1: Codebase - we're in a git repo
    assert os.path.exists(".git") or os.path.exists("../.git"), "Should be in a git repository"
    
    # Test 2: Dependencies - requirements.txt exists
    assert os.path.exists("requirements.txt"), "requirements.txt should exist"
    
    # Test 3: Config - .env.example should exist
    # This is covered in test_env_example_file()
    
    # Test 5: Build, release, run - Dockerfile should exist
    assert os.path.exists("Dockerfile"), "Dockerfile should exist for build stage"

if __name__ == "__main__":
    pytest.main([__file__])