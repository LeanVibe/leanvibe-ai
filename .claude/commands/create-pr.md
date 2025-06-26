# Create Pull Request with Comprehensive Automation

Create PR with automated quality gates and human checkpoints.

## Instructions

1. **Pre-PR Validation Suite**
   ```bash
   # Run comprehensive checks
   npm run lint:fix
   npm run format
   npm run test:coverage
   npm run security:audit
   npm run performance:benchmark
   ```

2. **Intelligent Branch Creation**
   ```bash
   # Create branch with issue linkage
   ISSUE_NUM=$(gh issue list --search "$ARGUMENTS" --json number -q '.[0].number')
   git checkout -b "feature/$ISSUE_NUM-$BRIEF_DESCRIPTION"
   ```

3. **Commit Strategy with Conventional Commits**
   ```bash
   # Stage changes intelligently
   git add -p  # Interactive staging
   
   # Generate commit message
   git commit -m "feat(#$ISSUE_NUM): implement $FEATURE
   
   - Added $COMPONENT with $BENEFIT
   - Implemented $TESTS for coverage
   - Updated documentation
   
   Breaking Changes: none
   Performance Impact: +15% improvement
   Security: no new vulnerabilities"
   ```

4. **PR Template Population**
   ```bash
   gh pr create \
     --title "feat: $TITLE (#$ISSUE_NUM)" \
     --body-file .github/pull_request_template.md \
     --base main \
     --label "ready-for-review" \
     --project "DynaStory Development" \
     --milestone "Current Sprint"
   ```

5. **Automated PR Enhancements**
   - Add screenshots/recordings for UI changes
   - Generate API documentation diffs
   - Create performance comparison reports
   - Link related issues automatically

6. **Human Review Preparation**
   ```bash
   # Add review checklist
   gh pr comment $PR_NUM --body "## Review Checklist
   - [ ] Code follows style guide
   - [ ] Tests cover new functionality
   - [ ] No security vulnerabilities
   - [ ] Performance targets met
   - [ ] Documentation updated
   
   @team-lead Ready for review"
   ```