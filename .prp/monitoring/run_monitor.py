#!/usr/bin/env python3
"""
PRP-12Factor Compliance Monitor - Simple Runner
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_compliance_check():
    """Run 12-factor compliance checks"""
    print("[PRP Monitor] Starting 12-Factor compliance scan...")
    print("=" * 60)
    
    checks = {
        "codebase": check_codebase,
        "dependencies": check_dependencies,
        "config": check_config,
        "backing_services": check_backing_services,
        "build_release_run": check_build_release_run,
        "processes": check_processes,
        "port_binding": check_port_binding,
        "concurrency": check_concurrency,
        "disposability": check_disposability,
        "dev_prod_parity": check_dev_prod_parity,
        "logs": check_logs,
        "admin_processes": check_admin_processes
    }
    
    results = {}
    total_score = 0
    
    for factor, check_func in checks.items():
        score, issues = check_func()
        results[factor] = {
            "score": score,
            "issues": issues,
            "status": get_status(score)
        }
        total_score += score
        
        print(f"\n[{factor.upper()}] Score: {score*100:.1f}% - {get_status(score)}")
        if issues:
            for issue in issues[:3]:  # Show top 3 issues
                print(f"  - {issue}")
    
    overall_score = (total_score / len(checks)) * 100
    print(f"\n{'='*60}")
    print(f"OVERALL COMPLIANCE SCORE: {overall_score:.1f}%")
    print(f"STATUS: {get_overall_status(overall_score)}")
    
    # Save results
    save_results(results, overall_score)
    
    return overall_score

def get_status(score):
    if score >= 0.9:
        return "EXCELLENT"
    elif score >= 0.75:
        return "GOOD"
    elif score >= 0.5:
        return "NEEDS IMPROVEMENT"
    else:
        return "CRITICAL"

def get_overall_status(score):
    if score >= 90:
        return "EXCELLENT - Production Ready"
    elif score >= 75:
        return "GOOD - Minor improvements needed"
    elif score >= 50:
        return "FAIR - Significant improvements needed"
    else:
        return "POOR - Major refactoring required"

def check_codebase():
    """Check codebase factor"""
    score = 0.0
    issues = []
    
    # Check for .git
    if Path(".git").exists():
        score += 0.5
    else:
        issues.append("No Git repository found - initialize with 'git init'")
    
    # Check for .gitignore
    if Path(".gitignore").exists():
        score += 0.3
    else:
        issues.append("No .gitignore file - create one to exclude unnecessary files")
    
    # Check for remote
    try:
        result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            score += 0.2
        else:
            issues.append("No remote repository configured")
    except:
        pass
    
    return score, issues

def check_dependencies():
    """Check dependencies factor"""
    score = 0.0
    issues = []
    
    # Check for dependency files
    if Path("requirements.txt").exists():
        score += 0.4
        
        # Check for pinned versions
        with open("requirements.txt", "r") as f:
            deps = f.read()
            if "==" in deps:
                score += 0.3
            else:
                issues.append("Dependencies not pinned to specific versions")
    else:
        issues.append("No requirements.txt found")
    
    # Check for vulnerabilities
    try:
        result = subprocess.run(["pip", "check"], capture_output=True, text=True)
        if result.returncode == 0:
            score += 0.3
        else:
            issues.append("Dependency conflicts detected")
    except:
        pass
    
    return score, issues

def check_config():
    """Check config factor"""
    score = 0.0
    issues = []
    
    # Check for env files
    if Path(".env.example").exists():
        score += 0.4
    else:
        issues.append("No .env.example file for configuration template")
    
    # Check config.py
    if Path("config.py").exists():
        score += 0.3
        with open("config.py", "r") as f:
            content = f.read()
            if "os.environ" in content or "os.getenv" in content:
                score += 0.3
            else:
                issues.append("Configuration not reading from environment variables")
    
    # Check for hardcoded secrets
    python_files = list(Path(".").rglob("*.py"))[:20]
    hardcoded_found = False
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if any(word in content.lower() for word in ["password=", "secret=", "api_key="]):
                    hardcoded_found = True
                    issues.append(f"Potential hardcoded secret in {py_file}")
                    break
        except:
            pass
    
    if not hardcoded_found:
        score = min(1.0, score + 0.2)
    
    return score, issues

def check_backing_services():
    """Check backing services factor"""
    score = 0.7  # Default good score
    issues = []
    
    # Check for service configuration
    config_files = ["config.py", "settings.py", "app.py"]
    service_config_found = False
    
    for config_file in config_files:
        if Path(config_file).exists():
            with open(config_file, "r") as f:
                content = f.read()
                if "DATABASE_URL" in content or "REDIS_URL" in content:
                    service_config_found = True
                    score = 0.9
                    break
    
    if not service_config_found:
        issues.append("No environment-based service configuration found")
    
    return score, issues

def check_build_release_run():
    """Check build, release, run factor"""
    score = 0.0
    issues = []
    
    # Check for Dockerfile
    if Path("Dockerfile").exists():
        score += 0.4
    else:
        issues.append("No Dockerfile found for containerization")
    
    # Check for CI/CD
    ci_files = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"]
    ci_found = False
    for ci_file in ci_files:
        if Path(ci_file).exists():
            ci_found = True
            score += 0.3
            break
    
    if not ci_found:
        issues.append("No CI/CD configuration found")
    
    # Check for build scripts
    if Path("package.json").exists() or Path("setup.py").exists():
        score += 0.3
    
    return score, issues

def check_processes():
    """Check processes factor"""
    score = 0.0
    issues = []
    
    # Check for Procfile
    if Path("Procfile").exists():
        score += 0.5
    else:
        issues.append("No Procfile found for process declaration")
    
    # Check for stateless design
    python_files = list(Path(".").rglob("*.py"))[:10]
    stateful_patterns = ["open(", "file.write", "pickle.dump"]
    stateful_found = False
    
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if any(pattern in content for pattern in stateful_patterns):
                    stateful_found = True
                    issues.append(f"Potential stateful operation in {py_file}")
                    break
        except:
            pass
    
    if not stateful_found:
        score += 0.5
    
    return score, issues

def check_port_binding():
    """Check port binding factor"""
    score = 0.0
    issues = []
    
    # Check for PORT environment variable usage
    app_files = ["app.py", "prp_app.py", "main.py", "server.py"]
    port_config_found = False
    
    for app_file in app_files:
        if Path(app_file).exists():
            with open(app_file, "r") as f:
                content = f.read()
                if "PORT" in content or "port=" in content:
                    if "os.environ" in content or "os.getenv" in content:
                        port_config_found = True
                        score = 0.9
                        break
                    else:
                        issues.append(f"Hardcoded port in {app_file}")
                        score = 0.4
    
    if not port_config_found and score == 0:
        issues.append("No port binding configuration found")
        score = 0.3
    
    return score, issues

def check_concurrency():
    """Check concurrency factor"""
    score = 0.6  # Default medium score
    issues = []
    
    # Check for worker configuration
    if Path("Procfile").exists():
        with open("Procfile", "r") as f:
            content = f.read()
            if "worker" in content:
                score = 0.9
            else:
                issues.append("No worker processes defined in Procfile")
    
    return score, issues

def check_disposability():
    """Check disposability factor"""
    score = 0.7  # Default good score
    issues = []
    
    # Check for signal handling
    python_files = list(Path(".").rglob("*.py"))[:10]
    signal_handling_found = False
    
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "SIGTERM" in content or "signal.signal" in content:
                    signal_handling_found = True
                    score = 0.9
                    break
        except:
            pass
    
    if not signal_handling_found:
        issues.append("No graceful shutdown handling found")
    
    return score, issues

def check_dev_prod_parity():
    """Check dev/prod parity factor"""
    score = 0.0
    issues = []
    
    # Check for Docker
    if Path("Dockerfile").exists() and Path("docker-compose.yml").exists():
        score += 0.5
    else:
        issues.append("Missing Docker configuration for environment parity")
    
    # Check for environment configs
    env_files = [".env.development", ".env.production", ".env.example"]
    env_found = sum(1 for f in env_files if Path(f).exists())
    
    if env_found >= 2:
        score += 0.5
    else:
        issues.append("Missing environment-specific configuration files")
    
    return score, issues

def check_logs():
    """Check logs factor"""
    score = 0.8  # Default good score
    issues = []
    
    # Check for structured logging
    if Path("logging_config.py").exists():
        score = 0.9
    else:
        issues.append("No centralized logging configuration found")
    
    # Check for file-based logging
    python_files = list(Path(".").rglob("*.py"))[:10]
    file_logging_found = False
    
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "FileHandler" in content or "logging.basicConfig(filename=" in content:
                    file_logging_found = True
                    issues.append(f"File-based logging found in {py_file}")
                    score = 0.5
                    break
        except:
            pass
    
    return score, issues

def check_admin_processes():
    """Check admin processes factor"""
    score = 0.7  # Default good score
    issues = []
    
    # Check for migration system
    if Path("alembic.ini").exists() or Path("migrations").exists():
        score = 0.9
    else:
        issues.append("No database migration system found")
    
    # Check for admin scripts
    if Path("scripts").exists():
        score = min(1.0, score + 0.1)
    
    return score, issues

def save_results(results, overall_score):
    """Save scan results"""
    output_dir = Path(".prp/monitoring")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_score": overall_score,
        "status": get_overall_status(overall_score),
        "factors": results
    }
    
    # Save JSON report
    with open(output_dir / "latest-scan.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Save summary report
    with open(output_dir / "summary.txt", "w") as f:
        f.write(f"PRP-12Factor Compliance Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Overall Score: {overall_score:.1f}%\n")
        f.write(f"Status: {get_overall_status(overall_score)}\n\n")
        
        f.write("Factor Scores:\n")
        for factor, data in results.items():
            f.write(f"  {factor}: {data['score']*100:.1f}% - {data['status']}\n")
        
        f.write("\nTop Issues:\n")
        issue_count = 0
        for factor, data in results.items():
            for issue in data['issues'][:2]:
                f.write(f"  - [{factor}] {issue}\n")
                issue_count += 1
                if issue_count >= 10:
                    break
            if issue_count >= 10:
                break
    
    print(f"\n[SAVED] Results saved to .prp/monitoring/")

if __name__ == "__main__":
    run_compliance_check()