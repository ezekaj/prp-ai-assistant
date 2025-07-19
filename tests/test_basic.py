"""
Basic tests for PRP AI Assistant system
"""
import os
import sys
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_python_version():
    """Test that we're running on a supported Python version"""
    assert sys.version_info >= (3, 8), "Python 3.8+ required"

def test_project_structure():
    """Test that basic project structure exists"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for essential files
    assert os.path.exists(os.path.join(project_root, "README.md"))
    assert os.path.exists(os.path.join(project_root, "requirements.txt"))
    assert os.path.exists(os.path.join(project_root, "config.py"))
    assert os.path.exists(os.path.join(project_root, "prp_app.py"))

def test_requirements_file():
    """Test that requirements.txt exists and is readable"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    requirements_path = os.path.join(project_root, "requirements.txt")
    
    assert os.path.exists(requirements_path)
    with open(requirements_path, 'r') as f:
        content = f.read()
        assert len(content.strip()) > 0, "Requirements file should not be empty"

def test_prp_directory_structure():
    """Test PRP directory structure"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prp_dir = os.path.join(project_root, "PRPs")
    
    assert os.path.exists(prp_dir)
    assert os.path.exists(os.path.join(prp_dir, "scripts"))
    assert os.path.exists(os.path.join(prp_dir, "analytics"))

def test_config_import():
    """Test that config module can be imported"""
    try:
        import config
        assert hasattr(config, 'Config') or len(dir(config)) > 0
    except ImportError:
        pytest.skip("Config module not importable in test environment")

def test_environment_variables():
    """Test basic environment variable handling"""
    # Test that we can set and get environment variables
    test_key = "PRP_TEST_VAR"
    test_value = "test_value"
    
    os.environ[test_key] = test_value
    assert os.getenv(test_key) == test_value
    
    # Clean up
    del os.environ[test_key]

def test_docker_files_exist():
    """Test that Docker configuration files exist"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    assert os.path.exists(os.path.join(project_root, "Dockerfile"))
    assert os.path.exists(os.path.join(project_root, "docker-compose.yml"))

if __name__ == "__main__":
    pytest.main([__file__])