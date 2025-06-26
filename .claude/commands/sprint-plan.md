# Sprint Planning with GitHub Projects

Analyze backlog and create optimized sprint plan.

## Instructions

Plan sprint for: $ARGUMENTS (e.g., "2-week sprint starting Monday")

1. **Backlog Analysis**
   ```bash
   # Fetch all open issues
   gh issue list --state open --json number,title,labels,assignees,milestone \
     > backlog.json
   ```

2. **Velocity Calculation**
   - Analyze last 3 sprints completion rate
   - Calculate team capacity
   - Factor in holidays/meetings

3. **Intelligent Issue Selection**
   - Prioritize by business value
   - Consider dependencies
   - Balance by team member expertise
   - Ensure mix of features/bugs/tech-debt

4. **Sprint Creation**
   ```bash
   # Create sprint milestone
   gh api repos/:owner/:repo/milestones \
     --method POST \
     --field title="Sprint $SPRINT_NUM" \
     --field due_on="$END_DATE"
   ```

5. **Task Assignment Optimization**
   ```bash
   # Assign issues to sprint
   for issue in $SELECTED_ISSUES; do
     gh issue edit $issue \
       --milestone "Sprint $SPRINT_NUM" \
       --project "DynaStory Development"
   done
   ```

6. **Sprint Documentation**
   - Generate sprint goals
   - Create burndown chart template
   - Set up daily standup notes
   - Configure sprint review agenda