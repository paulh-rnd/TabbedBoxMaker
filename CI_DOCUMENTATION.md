# Continuous Integration Documentation

This project uses GitHub Actions for automated testing and quality assurance. All tests run automatically on every commit and pull request.

## Workflows

### 1. CI - Test and Validate BoxMaker (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches  
- Manual dispatch

**Jobs:**

#### `test` (Python 3.12 - Latest)
- ✅ Checkout code and setup Python 3.12
- ✅ Run comprehensive test suite (`python test_boxmaker.py`)
- ✅ Run CLI examples (`python cli_examples.py`)
- ✅ Test basic CLI functionality
- 📦 Archive test results

#### `test-inkscape-version` (Python 3.11 - Inkscape Compatible)
- ✅ Checkout code and setup Python 3.11 (common Inkscape version)
- ✅ Run comprehensive test suite
- ✅ Run CLI examples

#### `cross-platform` (Matrix: Ubuntu, Windows, macOS)
- ✅ Cross-platform testing with Python 3.12
- ✅ Run basic test suite on all platforms
- ✅ CLI functionality verification
- ✅ File generation verification

#### `performance-test`
- ✅ Large box generation (800×600×400mm)
- ✅ Complex divider layouts (8×6 grid)
- ✅ Rapid generation stress test
- ✅ File size and validity checks

### 2. Release Validation (`.github/workflows/release.yml`)

**Triggers:**
- Release published/created
- Tags starting with `v*`

**Jobs:**

#### `validate-release` (Python 3.12)
- ✅ Run comprehensive test suite (`python test_boxmaker.py`)
- ✅ Generate CLI examples (`python cli_examples.py`)
- ✅ Generate additional showcase examples (precision, workshop, storage boxes)
- ✅ Validate all generated SVG files
- � Archive release artifacts

## Local Testing

Before pushing code, run the test scripts directly:

```bash
# Run the full test suite
python test_boxmaker.py

# Run CLI examples
python cli_examples.py

# Or use the pre-commit script for comprehensive testing
python pre_commit_test.py
```

This script runs the same core tests as CI and validates:
- ✅ Python syntax
- ✅ Module imports  
- ✅ Core test suite
- ✅ CLI examples
- ✅ Error handling
- ✅ SVG validation

## Test Coverage

### Core Functionality
- ✅ Basic box generation (multiple sizes)
- ✅ Divider support (various configurations)
- ✅ Material thickness handling
- ✅ CNC vs Laser cutting modes
- ✅ Layout styles (separated, nested, compact)
- ✅ Inside vs outside dimensions
- ✅ Tab size validation
- ✅ Error conditions

### CLI Interface
- ✅ All command-line parameters
- ✅ File output generation
- ✅ Error message formatting
- ✅ Cross-platform compatibility

### Edge Cases
- ✅ Minimum dimensions (40mm)
- ✅ Maximum reasonable dimensions (1000mm+)
- ✅ Thin tabs (weak but allowed)
- ✅ Large tabs (for big boxes)
- ✅ Complex divider grids
- ✅ Unusual aspect ratios

### Quality Assurance
- ✅ SVG structure validation
- ✅ File size checks
- ✅ Drawing element verification
- ✅ Syntax validation
- ✅ Import dependency checks

## Artifacts

CI runs generate artifacts that are stored for analysis:

### Test Results (`test-results`)
- Generated SVG files from test suite
- CLI example outputs  
- Basic CLI test files
- Retention: 30 days

### Release Validation (`release-validation-artifacts`)
- Showcase examples (precision, workshop, storage boxes)
- All test and example outputs
- Comprehensive file validation results
- Retention: 90 days

## Failure Handling

If CI fails:

1. **Check the logs** - Each step shows detailed output
2. **Run locally** - Use `python pre_commit_test.py` to reproduce
3. **Fix issues** - Address syntax, test, or validation errors
4. **Re-run** - Push again or re-run the workflow

Common failure causes:
- ❌ Python syntax errors
- ❌ Import dependency issues
- ❌ Test assertions failing
- ❌ Invalid SVG generation
- ❌ CLI parameter errors
- ❌ Cross-platform compatibility

## Adding New Tests

To add new test cases:

1. **Add to test suite** - Update `test_boxmaker.py`
2. **Add to pre-commit** - Update `pre_commit_test.py` if needed
3. **Document edge cases** - Add comments explaining test purpose
4. **Verify CI passes** - Check all platforms and Python versions

The CI system ensures code quality and catches regressions early, maintaining the reliability of the TabbedBox2 generator across all supported platforms and use cases.
