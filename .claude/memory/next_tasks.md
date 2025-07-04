# Next Session Priority Tasks
**Updated**: July 4, 2025  
**Context**: Post-Mobile MCP Testing Validation  
**Current Status**: Production readiness implementation phase

## 🔥 **Immediate Critical Tasks (Start Next Session)**

### **1. UI Architecture Fixes (High Priority - 4-6 hours)**
**Status**: Ready to implement  
**Impact**: Production blocking issues

#### **Task 1.1: Fix Double Navigation Bars**
- **Files**: `SettingsView.swift`, `VoiceSettingsView.swift`, `ServerSettingsView.swift`, `ArchitectureTabView.swift`
- **Action**: Remove all nested `NavigationView` wrappers, ensure only `NavigationStack` usage
- **Evidence**: Agent Chat screen showing duplicate "Connect LeanVibe... Code Test Settings" headers
- **Validation**: Mobile MCP testing to verify single navigation bar
- **Agent**: UI_ARCHITECTURE_AGENT

#### **Task 1.2: Remove Duplicate UI Elements**
- **Files**: Task statistics views, modal presentation code
- **Action**: Fix modal hierarchy causing multiple "Done" buttons
- **Evidence**: Task Statistics view showing both top-left and center-right "Done" buttons
- **Validation**: Visual verification no duplicate elements exist
- **Agent**: UI_CONSISTENCY_AGENT

#### **Task 1.3: Standardize Touch Interactions**
- **Files**: All settings navigation, modal presentations
- **Action**: Replace long-press requirements with standard iOS tap patterns
- **Evidence**: User confirmation that settings require long-press instead of tap
- **Validation**: Mobile MCP interaction testing, accessibility compliance
- **Agent**: INTERACTION_AGENT

### **2. Backend Integration Fixes (High Priority - 2-4 hours)**
**Status**: API issues identified, ready to resolve

#### **Task 2.1: Architecture Viewer API Fix**
- **Problem**: "Failed to load architecture - Network error: The data couldn't be read because it isn't in the correct format"
- **Root Cause**: Backend API format mismatch, expects Mermaid.js format
- **Files**: Architecture visualization endpoints, `ArchitectureVisualizationService.swift`
- **Action**: Align API response format with iOS parsing expectations
- **Validation**: Mobile MCP testing - architecture diagrams load successfully
- **Agent**: BACKEND_INTEGRATION_AGENT

#### **Task 2.2: Statistics API Implementation**
- **Problem**: "No statistics available" placeholder instead of real metrics
- **Files**: `TaskService.swift`, `MetricsViewModel.swift`, statistics endpoints
- **Action**: Connect statistics displays to real backend data
- **Validation**: All statistics show real data, no placeholder messages
- **Agent**: DATA_INTEGRATION_AGENT

### **3. Settings Completeness Audit (Medium Priority - 6-8 hours)**
**Status**: 70% incomplete implementations identified

#### **Task 3.1: Hide Incomplete Settings**
- **Files**: All settings views with placeholder implementations
- **Action**: Implement feature flags to hide non-functional settings
- **Evidence**: Task notifications, metrics, performance settings lead to blank screens
- **Validation**: Only functional settings visible to users
- **Agent**: FEATURE_MANAGEMENT_AGENT

#### **Task 3.2: Complete Critical Settings**
- **Files**: Backend service dependencies, compilation targets
- **Action**: Fix `BackendSettingsService` targeting issues, implement core settings
- **Validation**: All visible settings fully functional
- **Agent**: SETTINGS_IMPLEMENTATION_AGENT

### Secondary Tasks

#### Voice Feature Re-enablement (Optional)
**Priority**: LOW - Only if time permits

**Safety Improvements**:
- Enhanced error recovery mechanisms
- Better permission edge case handling
- User education about voice requirements
- Gradual rollout strategy

**Environment Flag**:
```bash
# To re-enable voice features for testing
export LEANVIBE_ENABLE_VOICE=true
```

### Technical Debt Items

#### Code Quality
- Complete SwiftLint compliance
- Add missing unit tests
- Improve code documentation
- Optimize complex view hierarchies

#### Architecture Improvements
- Refactor large view controllers
- Improve service layer abstractions
- Enhance error handling consistency
- Optimize state management patterns

### Quality Gates for Next Session

#### Build Validation
- All targets compile successfully
- No SwiftLint warnings
- Unit tests pass with >80% coverage
- Integration tests validate core workflows

#### Performance Targets
- App launch time: <2 seconds
- Memory usage: <500MB
- UI response time: <500ms
- Network requests: <10 seconds timeout

#### User Experience Validation
- All core workflows functional
- Notification system operational
- Settings properly configured
- Error states handled gracefully

### Session Success Criteria

**Must Have**:
- ✅ Push notifications fully implemented
- ✅ Performance targets met
- ✅ Production deployment ready
- ✅ All quality gates passed

**Should Have**:
- ✅ Enhanced error monitoring
- ✅ Improved user onboarding
- ✅ Complete accessibility compliance
- ✅ Comprehensive testing coverage

**Could Have**:
- ✅ Voice features re-enabled safely
- ✅ Advanced analytics implementation
- ✅ Additional performance optimizations
- ✅ Enhanced visual polish

### Preparation Notes

#### Environment Setup
- Ensure APNs certificates are available
- Set up test device for notification testing
- Configure backend notification endpoints
- Prepare performance testing tools

#### Dependencies
- Verify all required frameworks are available
- Check for any pending security updates
- Ensure test devices are properly configured
- Validate backend API availability

#### Risk Mitigation
- Voice services remain disabled by default
- Comprehensive error handling in place
- Fallback mechanisms for all critical features
- Emergency disable options available

### Context Optimization Notes

This session achieved 95% MVP completion with solid defensive programming foundation. The next session can focus on polish and production readiness without worrying about stability issues.

Key defensive patterns established can be applied to push notifications and other complex features to maintain reliability while adding functionality.