import re
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class AnalysisIssue:
    severity: str  # critical, warning, info
    category: str
    message: str
    line: int = 0
    suggestion: str = ""


class CodeAnalyzer:
    SECURITY_PATTERNS = [
        (r'\beval\s*\(', "Use of eval() is dangerous and can lead to code injection", "critical"),
        (r'\bexec\s*\(', "Use of exec() is dangerous and can lead to code injection", "critical"),
        (r'innerHTML\s*=', "Direct innerHTML assignment can lead to XSS attacks", "critical"),
        (r'document\.write\s*\(', "document.write can lead to XSS vulnerabilities", "critical"),
        (r'(?i)SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*[\+\%]', "Possible SQL injection via string concatenation", "critical"),
        (r'(?i)password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected", "critical"),
        (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*["\'][^"\']+["\']', "Hardcoded secret/API key detected", "critical"),
        (r'subprocess\.call\s*\(.*shell\s*=\s*True', "subprocess with shell=True is a security risk", "warning"),
        (r'os\.system\s*\(', "os.system is vulnerable to shell injection", "warning"),
        (r'pickle\.loads?\s*\(', "Pickle deserialization can execute arbitrary code", "warning"),
        (r'yaml\.load\s*\((?!.*Loader)', "yaml.load without SafeLoader is unsafe", "warning"),
        (r'(?i)http://', "Insecure HTTP URL detected; use HTTPS", "info"),
    ]

    QUALITY_PATTERNS = [
        (r'console\.log\s*\(', "Remove console.log statements before production", "warning", "debugging"),
        (r'print\s*\(', "Consider using a proper logger instead of print()", "info", "debugging"),
        (r'#\s*TODO', "Unresolved TODO comment", "info", "maintenance"),
        (r'#\s*FIXME', "Unresolved FIXME comment", "warning", "maintenance"),
        (r'#\s*HACK', "Hack workaround detected", "warning", "maintenance"),
        (r'except\s*:', "Bare except clause catches all exceptions", "warning", "error_handling"),
        (r'except\s+Exception\s*:', "Catching broad Exception class", "info", "error_handling"),
        (r'pass\s*$', "Empty pass statement may indicate incomplete implementation", "info", "completeness"),
        (r'\.\.\.', "Ellipsis may indicate stub implementation", "info", "completeness"),
        (r'import\s+\*', "Wildcard imports reduce code clarity", "warning", "imports"),
    ]

    NAMING_PATTERNS = [
        (r'\b[a-z]\b(?!\s*=\s*["\'])', "Single-letter variable name reduces readability"),
        (r'def\s+[A-Z]', "Function names should use snake_case, not PascalCase"),
        (r'class\s+[a-z]', "Class names should use PascalCase, not snake_case"),
    ]

    def analyze(self, code: str, language: str = "auto") -> Dict[str, Any]:
        if language == "auto":
            language = self._detect_language(code)

        lines = code.split('\n')
        total_lines = len(lines)
        non_empty = [l for l in lines if l.strip()]
        code_lines = [l for l in non_empty if not l.strip().startswith(('#', '//', '/*', '*', '"""', "'''"))]

        issues: List[AnalysisIssue] = []

        security_issues = self._scan_security(code, lines)
        quality_issues = self._scan_quality(code, lines)
        naming_issues = self._scan_naming(code, lines)
        complexity = self._analyze_complexity(code, lines, language)

        issues.extend(security_issues)
        issues.extend(quality_issues)
        issues.extend(naming_issues)

        critical = sum(1 for i in issues if i.severity == "critical")
        warnings = sum(1 for i in issues if i.severity == "warning")
        infos = sum(1 for i in issues if i.severity == "info")

        if critical == 0 and warnings <= 2:
            score = min(98, 95 - warnings)
        elif critical == 0:
            score = max(60, 85 - warnings * 5)
        else:
            score = max(10, 70 - critical * 15 - warnings * 5)

        comment_lines = sum(1 for l in non_empty if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''")))
        comment_ratio = round(comment_lines / max(len(non_empty), 1) * 100, 1)

        function_count = len(re.findall(r'(?:def |function |const \w+ = (?:async )?\(|=>\s*\{)', code))
        class_count = len(re.findall(r'(?:class )', code))
        import_count = len(re.findall(r'(?:^import |^from .+ import )', code, re.MULTILINE))

        return {
            "language": language,
            "metrics": {
                "total_lines": total_lines,
                "code_lines": len(code_lines),
                "blank_lines": total_lines - len(non_empty),
                "comment_lines": comment_lines,
                "comment_ratio": comment_ratio,
                "functions": function_count,
                "classes": class_count,
                "imports": import_count,
                "complexity": complexity,
            },
            "score": score,
            "grade": self._score_to_grade(score),
            "issues": {
                "critical": critical,
                "warnings": warnings,
                "info": infos,
                "total": len(issues),
                "details": [asdict(i) for i in issues[:30]],
            },
            "summary": self._generate_summary(score, critical, warnings, complexity, language),
            "recommendations": self._generate_recommendations(issues, complexity, comment_ratio),
        }

    def _detect_language(self, code: str) -> str:
        if re.search(r'def \w+\s*\(', code) and ('import ' in code or ':' in code):
            return "python"
        if re.search(r'function\s+\w+|const\s+\w+\s*=|=>\s*\{|require\(', code):
            return "javascript"
        if re.search(r'public\s+class|private\s+\w+|System\.out', code):
            return "java"
        if re.search(r'func\s+\w+|package\s+main|fmt\.', code):
            return "go"
        if re.search(r'fn\s+\w+|let\s+mut\s+|impl\s+', code):
            return "rust"
        if re.search(r'<\w+>|</\w+>|className=', code):
            return "html/jsx"
        return "unknown"

    def _scan_security(self, code: str, lines: List[str]) -> List[AnalysisIssue]:
        issues = []
        for pattern, message, severity in self.SECURITY_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(AnalysisIssue(
                        severity=severity,
                        category="security",
                        message=message,
                        line=i,
                        suggestion=f"Review line {i} for security concerns",
                    ))
        return issues

    def _scan_quality(self, code: str, lines: List[str]) -> List[AnalysisIssue]:
        issues = []
        for pattern, message, severity, category in self.QUALITY_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(AnalysisIssue(
                        severity=severity,
                        category=category,
                        message=message,
                        line=i,
                    ))
        return issues

    def _scan_naming(self, code: str, lines: List[str]) -> List[AnalysisIssue]:
        issues = []
        for pattern, message in self.NAMING_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(AnalysisIssue(
                        severity="info",
                        category="naming",
                        message=message,
                        line=i,
                    ))
                    break
        return issues

    def _analyze_complexity(self, code: str, lines: List[str], language: str) -> Dict[str, Any]:
        max_depth = 0
        current_depth = 0
        depth_counts = {}

        indent_chars = 4
        for line in lines:
            stripped = line.lstrip()
            if not stripped:
                continue
            indent = len(line) - len(stripped)
            depth = indent // indent_chars
            current_depth = depth
            max_depth = max(max_depth, depth)
            depth_counts[depth] = depth_counts.get(depth, 0) + 1

        branches = len(re.findall(r'\b(?:if|elif|else|for|while|switch|case|catch|except|try)\b', code))
        returns = len(re.findall(r'\breturn\b', code))

        cyclomatic = branches + 1

        if cyclomatic <= 5:
            rating = "low"
        elif cyclomatic <= 15:
            rating = "moderate"
        elif cyclomatic <= 30:
            rating = "high"
        else:
            rating = "very high"

        return {
            "cyclomatic": cyclomatic,
            "max_nesting_depth": max_depth,
            "branches": branches,
            "returns": returns,
            "rating": rating,
        }

    def _score_to_grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _generate_summary(self, score: int, critical: int, warnings: int,
                          complexity: Dict, language: str) -> str:
        parts = []
        if score >= 90:
            parts.append(f"Excellent {language} code quality with a score of {score}/100.")
        elif score >= 75:
            parts.append(f"Good {language} code quality with a score of {score}/100.")
        elif score >= 60:
            parts.append(f"Moderate {language} code quality with a score of {score}/100. Some improvements recommended.")
        else:
            parts.append(f"Code quality needs improvement (score: {score}/100). Significant issues found.")

        if critical > 0:
            parts.append(f"{critical} critical issue(s) require immediate attention.")
        if warnings > 0:
            parts.append(f"{warnings} warning(s) should be addressed.")
        if complexity["rating"] in ("high", "very high"):
            parts.append(f"Code complexity is {complexity['rating']} (cyclomatic: {complexity['cyclomatic']}).")

        return " ".join(parts)

    def _generate_recommendations(self, issues: List[AnalysisIssue],
                                   complexity: Dict, comment_ratio: float) -> List[str]:
        recs = []
        categories = set(i.category for i in issues)

        if "security" in categories:
            recs.append("Address all security vulnerabilities before deployment")
        if "debugging" in categories:
            recs.append("Remove debugging statements (console.log, print) before production")
        if "maintenance" in categories:
            recs.append("Resolve TODO/FIXME comments to reduce technical debt")
        if "error_handling" in categories:
            recs.append("Use specific exception types instead of bare except clauses")
        if complexity["max_nesting_depth"] > 4:
            recs.append("Reduce nesting depth by extracting helper functions")
        if complexity["rating"] in ("high", "very high"):
            recs.append("Break down complex functions into smaller, focused units")
        if comment_ratio < 5:
            recs.append("Add documentation comments to improve code maintainability")
        if comment_ratio > 40:
            recs.append("Excessive comments may indicate unclear code; prefer self-documenting names")

        if not recs:
            recs.append("Code looks solid. Consider adding more test coverage.")

        return recs
