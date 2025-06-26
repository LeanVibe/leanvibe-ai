# Autonomous Debug Assistant

Debug issues with minimal human intervention.

## Instructions

Debug issue: $ARGUMENTS

1. **Issue Reproduction**
   - Parse error message/stack trace
   - Set up reproduction environment
   - Confirm issue exists
   - Document reproduction steps

2. **Root Cause Analysis**
   ```bash
   # Create debug branch
   git checkout -b "debug/$ISSUE_NUM"
   
   # Add diagnostic logging
   # Run with various inputs
   # Analyze execution flow
   ```

3. **Solution Exploration**
   - Generate 3 potential fixes
   - Evaluate each for side effects
   - Choose optimal solution
   - Document decision rationale

4. **Fix Implementation**
   - Apply fix incrementally
   - Add regression tests
   - Verify no new issues introduced
   - Performance impact assessment

5. **Automated Verification**
   ```bash
   # Run comprehensive test suite
   npm run test:all
   
   # Check specific regression
   npm run test -- --grep "$ISSUE_DESCRIPTION"
   ```

6. **Human Checkpoint**
   ```bash
   # Only escalate if confidence < 80%
   if [ $CONFIDENCE -lt 80 ]; then
     gh issue comment $ISSUE_NUM \
       --body "🤖 Need human input: $REASON"
   fi
   ```