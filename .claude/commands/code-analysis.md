# Advanced Code Analysis with GitHub Integration

Analyze code and create actionable GitHub issues for improvements.

## Instructions

1. **Comprehensive Analysis Phase**
   - Architecture patterns and anti-patterns
   - Performance bottlenecks with benchmarks
   - Security vulnerabilities with CVSS scores
   - Technical debt with interest calculations
   - Test coverage gaps with risk assessment

2. **Issue Generation for Findings**
   ```bash
   # For each high-priority finding
   gh issue create --title "[Type]: Finding Description" \
     --body "## Finding\n$DESCRIPTION\n\n## Impact\n$IMPACT\n\n## Suggested Fix\n$FIX" \
     --label "tech-debt,$SEVERITY" \
     --milestone "Technical Debt Sprint"
   ```

3. **Dependency Graph Generation**
   ```mermaid
   graph TD
     A[Module A] -->|depends on| B[Module B]
     B --> C[Module C]
   ```
   Save as `docs/dependency-graph.md` and link in issue

4. **Performance Profiling Results**
   - Generate flame graphs
   - Create performance regression tests
   - Document in `docs/performance-baseline.md`

5. **Security Audit Trail**
   ```bash
   # Create security issue for each vulnerability
   gh issue create --title "Security: $VULNERABILITY" \
     --body "CVSS: $SCORE\nCWE: $CWE_ID" \
     --label "security,priority-$LEVEL" \
     --assignee "@security-team"
   ```

6. **Executive Summary Generation**
   - Create dashboard-ready metrics
   - Generate trend analysis
   - Propose remediation roadmap