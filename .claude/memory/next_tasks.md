# Priority Task Queue - Next Session

## Immediate High Priority (Next Session)

### 1. Error Handling System Restoration 🔥
**Estimated Effort**: 4-6 hours
**Files**: `DashboardTabView.swift`, `SettingsView.swift`, `TaskDetailView.swift`, `KanbanBoardView.swift`

**Tasks**:
- [ ] Investigate iOS 18.0+ availability attribute module resolution
- [ ] Fix GlobalErrorManager import/scope issues  
- [ ] Restore `.withGlobalErrorHandling()` extension functionality
- [ ] Test error display and retry mechanisms
- [ ] Validate error handling across all affected views

**Context**: Currently commented out with TODO markers, core app functionality depends on this

### 2. RetryManager Integration Fix 🔥  
**Estimated Effort**: 2-3 hours
**Files**: `TaskService.swift`, `ProjectManager.swift`, `RetryManager.swift`

**Tasks**:
- [ ] Resolve BackoffStrategy availability conflicts
- [ ] Restore async retry logic in TaskService operations
- [ ] Verify RetryManager.shared accessibility across modules
- [ ] Test exponential backoff and retry conditions
- [ ] Re-enable retry functionality for network operations

**Context**: Network resilience currently disabled, affects user experience

## High Priority (Same Week)

### 3. Test Coverage Expansion 📊
**Estimated Effort**: 8-12 hours  
**Files**: All test files in `LeanVibeTests/`

**Tasks**:
- [ ] Replace placeholder PushNotificationTests with real tests
- [ ] Add comprehensive unit tests for error handling system
- [ ] Create integration tests for RetryManager functionality  
- [ ] Add UI tests for critical user workflows
- [ ] Achieve 80%+ code coverage target per CLAUDE.md requirements

### 4. Build System Optimization ⚡
**Estimated Effort**: 3-4 hours

**Tasks**:
- [ ] Address iOS 17.0+ deprecation warnings (8 instances)
- [ ] Optimize compilation time (currently ~240s)
- [ ] Review SwiftLint configuration for quality gates
- [ ] Validate on physical iOS devices (not just simulator)

## Medium Priority (Next 2 Weeks)

### 5. Architecture Review & Documentation 📋
**Estimated Effort**: 6-8 hours

**Tasks**:
- [ ] Create architecture decision records (ADRs) for error handling
- [ ] Document availability attribute patterns and best practices
- [ ] Review and update CLAUDE.md build/test commands
- [ ] Create troubleshooting guide for future compilation issues

### 6. Performance Validation 🚀
**Estimated Effort**: 4-6 hours

**Tasks**:
- [ ] Validate <2s story generation target (per CLAUDE.md)
- [ ] Test <500MB memory usage requirement
- [ ] Benchmark build times across different hardware
- [ ] Profile app launch time (<1s target)

## Future Enhancements (Backlog)

### 7. Error Handling UX Polish
- [ ] Design error message improvements
- [ ] Add user-friendly retry interfaces  
- [ ] Implement progressive error disclosure
- [ ] Create error analytics and reporting

### 8. Test Infrastructure Modernization
- [ ] Implement Swift Testing framework migration
- [ ] Add snapshot testing for UI components
- [ ] Create performance regression test suite
- [ ] Add automated accessibility testing

## Success Criteria for Next Session

### Must Achieve ✅
- [ ] GlobalErrorManager fully restored and functional
- [ ] RetryManager integration working end-to-end
- [ ] All TODO markers from this session resolved
- [ ] Build remains stable with 0 errors
- [ ] Test suite maintains 100% pass rate

### Should Achieve 🎯  
- [ ] At least 3 new meaningful test cases added
- [ ] Deprecation warnings reduced by 50%
- [ ] Architecture documentation updated
- [ ] Performance baseline established

### Could Achieve 🌟
- [ ] Full test coverage for error handling system
- [ ] Build time optimization implemented
- [ ] Device testing validation completed

## Knowledge Continuity Notes

### Context to Preserve
- All current TODO markers represent working -> non-working state transitions
- Availability attributes are core issue, not SwiftUI patterns
- Test infrastructure is fragile, validate early and often
- Build system is working well, don't over-optimize

### Patterns to Continue
- Systematic error resolution (dependency order)
- Minimal viable fixes with restoration roadmap
- Comprehensive TODO documentation
- Regular build/test validation cycles

### Risks to Monitor
- Technical debt accumulation if fixes aren't restored
- Module resolution instability with iOS updates
- Test coverage regression if placeholder tests multiply
- Performance degradation from workarounds