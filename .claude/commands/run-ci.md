# Continuous Integration Execution

Activate virtual environments, run CI checks, and iteratively fix errors.

## Instructions

1. **Environment Activation**
   - Activate the appropriate virtual environment
   - Verify all dependencies are installed
   - Check environment variables are set correctly
   - Ensure database connections are available

2. **Pre-commit Checks**
   - Run code formatting tools
   - Execute linting and style checks
   - Perform static analysis
   - Check for security vulnerabilities

3. **Test Execution**
   - Run unit tests with coverage reporting
   - Execute integration tests
   - Run end-to-end tests if applicable
   - Perform performance tests if configured

4. **Build Process**
   - Execute the build process
   - Verify all assets are generated correctly
   - Check for build warnings or errors
   - Validate build artifacts

5. **Iterative Error Resolution**
   - Analyze any failing checks or tests
   - Fix issues one by one, prioritizing by severity
   - Re-run checks after each fix
   - Continue until all checks pass

6. **Final Validation**
   - Run the complete CI pipeline one final time
   - Verify all checks pass consistently
   - Document any issues encountered and resolved
   - Confirm the codebase is ready for deployment
