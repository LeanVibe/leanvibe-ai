# Implement Task with GitHub Tracking

Implement feature with automatic GitHub issue creation and progress tracking.

## Instructions

Implement task: $ARGUMENTS

1. **GitHub Issue Creation**
   ```bash
   # Create issue if not exists
   gh issue create --title "$ARGUMENTS" \
     --body "## Task Overview\n$ARGUMENTS\n\n## Acceptance Criteria\n- [ ] Implementation complete\n- [ ] Tests passing\n- [ ] Documentation updated\n- [ ] Code review ready" \
     --label "in-progress,ai-task" \
     --project "DynaStory Development"
   ```
   
   Store issue number for reference: ISSUE_NUMBER

2. **Task Decomposition with Sub-Issues**
   - Break down into subtasks (max 4 hours each)
   - Create linked issues for each subtask:
   ```bash
   gh issue create --title "Subtask: [Component]" \
     --body "Parent: #ISSUE_NUMBER" \
     --label "subtask"
   ```

3. **Implementation Planning**
   - Create implementation checklist in issue
   - Update issue with technical approach:
   ```bash
   gh issue comment ISSUE_NUMBER \
     --body "## Technical Approach\n..."
   ```

4. **Progress Tracking**
   - Update issue status every 2 hours
   - Log key decisions and blockers
   - Request human input when confidence < 70%

5. **Automated Testing & Validation**
   - Run tests after each component
   - Update issue with test results
   - Create draft PR linked to issue

6. **Human Gate Integration**
   ```bash
   # Mark ready for review
   gh issue edit ISSUE_NUMBER \
     --add-label "needs-human-review" \
     --remove-label "in-progress"
   ```