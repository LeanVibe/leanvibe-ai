# SwiftLint Integration for DynaStory

## Overview

SwiftLint is integrated into the DynaStory project to ensure consistent code quality, child safety compliance, and adherence to Swift best practices.

## Installation

### Homebrew (Recommended)
```bash
brew install swiftlint
```

### Verify Installation
```bash
swiftlint version  # Should show 0.59.1 or later
```

## Configuration

The project uses a custom `.swiftlint.yml` configuration that includes:

### Child Safety Rules
- **No Inappropriate Words**: Prevents inappropriate language in code
- **Child Appropriate Language**: Ensures all content is suitable for children
- **No Network Calls**: Enforces COPPA compliance by preventing network requests
- **Proper Error Handling**: Requires safe error handling for child-facing features

### Build Quality Rules
- **Duplicate Import Prevention**: Prevents import conflicts
- **Deployment Target Validation**: Ensures iOS 17.0+ compatibility
- **Unused Declaration Detection**: Catches dead code

### Code Style Rules
- Line length limits (120 warning, 150 error)
- Function body length limits
- Cyclomatic complexity limits
- Proper indentation and spacing

## Usage

### Command Line

#### Basic Linting
```bash
# Run on entire project
swiftlint lint

# Run with specific config
swiftlint lint --config .swiftlint.yml

# Run in quiet mode (errors/warnings only)
swiftlint lint --quiet
```

#### Auto-fix Issues
```bash
# Fix auto-correctable issues
swiftlint --fix

# Fix with specific config
swiftlint --fix --config .swiftlint.yml
```

#### Target Specific Files
```bash
# Lint specific files
swiftlint lint Sources/DynaStory/UI/

# Lint staged files only
git diff --cached --name-only --diff-filter=d | grep "\.swift$" | xargs swiftlint lint
```

### Xcode Integration

1. **Add Run Script Build Phase:**
   - In Xcode, select your target
   - Go to "Build Phases"
   - Click "+" and add "New Run Script Phase"
   - Add this script content:

```bash
if which swiftlint >/dev/null; then
    swiftlint lint --config .swiftlint.yml --reporter xcode
else
    echo "warning: SwiftLint not installed, download from https://github.com/realm/SwiftLint"
fi
```

2. **Use Provided Script:**
```bash
# The project includes a ready-to-use script
# Add this path to your Run Script Build Phase:
${SRCROOT}/scripts/swiftlint-xcode.sh
```

### Git Integration

#### Pre-commit Hook (Recommended)
```bash
# Install pre-commit hook
ln -s ../../scripts/pre-commit-swiftlint.sh .git/hooks/pre-commit

# Make executable (if needed)
chmod +x .git/hooks/pre-commit
```

This prevents commits with SwiftLint errors and warns about issues.

#### Manual Pre-commit Check
```bash
# Run before committing
./scripts/pre-commit-swiftlint.sh
```

## Common Commands

### Development Workflow
```bash
# Check code quality
swiftlint lint --quiet

# Fix auto-correctable issues
swiftlint --fix

# Check specific file
swiftlint lint Sources/DynaStory/UI/SettingsView.swift

# Generate detailed report
swiftlint lint --reporter html > swiftlint-report.html
```

### Continuous Integration
```bash
# CI-friendly command (fails on any violation)
swiftlint lint --strict

# Count violations
swiftlint lint | grep -E "warning|error" | wc -l
```

## Configuration Customization

### Disable Rules for Specific Files
Add to `.swiftlint.yml`:
```yaml
excluded:
  - Tests  # Skip test files
  - Generated  # Skip generated code
```

### Custom Rules
The project includes custom rules for child safety:
```yaml
custom_rules:
  no_inappropriate_words:
    regex: '(?i)(stupid|dumb|hate)'
    message: "Avoid words inappropriate for children"
```

### Override Rules in Code
```swift
// swiftlint:disable rule_name
let problematicCode = "This violates a rule"
// swiftlint:enable rule_name

// Disable for entire file
// swiftlint:disable file_length
```

## Reporting and Analysis

### Generate Reports
```bash
# HTML report
swiftlint lint --reporter html > reports/swiftlint.html

# JSON report for CI
swiftlint lint --reporter json > reports/swiftlint.json

# JUnit XML for CI integration
swiftlint lint --reporter junit > reports/swiftlint.xml
```

### Monitor Progress
```bash
# Count violations by type
swiftlint lint | grep "warning" | wc -l
swiftlint lint | grep "error" | wc -l

# Show most common violations
swiftlint lint | grep -oE "\([a-z_]+\)" | sort | uniq -c | sort -nr
```

## Troubleshooting

### Common Issues

1. **SwiftLint Not Found**
   ```bash
   # Fix with Homebrew
   brew install swiftlint
   
   # Or check PATH
   echo $PATH | grep -o '/opt/homebrew/bin'
   ```

2. **Configuration Warnings**
   ```bash
   # Validate config file
   swiftlint lint --config .swiftlint.yml --quiet | head -5
   ```

3. **Performance Issues**
   ```bash
   # Run on specific directories only
   swiftlint lint Sources/DynaStory/UI/
   
   # Exclude problematic paths
   # Add to .swiftlint.yml excluded: section
   ```

### Child Safety Rule Violations

- **Inappropriate Words**: Replace with child-friendly alternatives
- **Network Calls**: Remove URL/URLSession usage (violates COPPA)
- **Unsafe Error Handling**: Replace `try!` with proper error handling

## Best Practices

1. **Run Before Committing**: Always run SwiftLint before commits
2. **Fix Auto-correctable Issues**: Use `--fix` for formatting problems
3. **Address Warnings Promptly**: Don't let violations accumulate
4. **Follow Child Safety Rules**: These are critical for the app's purpose
5. **Use Xcode Integration**: See violations directly in the editor

## CI/CD Integration

For automated builds, add to your CI script:
```bash
# Install SwiftLint
brew install swiftlint

# Run validation
swiftlint lint --config .swiftlint.yml --reporter json

# Fail build on errors
swiftlint lint --strict
```

## Support

- **SwiftLint Documentation**: https://github.com/realm/SwiftLint
- **Rule Reference**: https://realm.github.io/SwiftLint/rule-directory.html
- **Project Configuration**: See `.swiftlint.yml` for current rules