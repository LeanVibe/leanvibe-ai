# Next Session Priority Tasks - July 3, 2025

## 🎯 Immediate Action Items (Session Continuation)

### 1. CRITICAL: Complete iOS Hard-coded Metrics Integration
**Priority**: HIGHEST  
**Estimated Time**: 30-45 minutes  
**Status**: Backend ready, iOS integration 50% complete  

**Files to Modify:**
- `ProjectManager.swift:128,228,236` - Replace random/hardcoded health scores with API calls
- `Project.swift:143` - Remove hardcoded default health score (0.85)

**Implementation Steps:**
1. Update `fetchProjectsFromBackend()` to call `/api/projects/{id}/metrics`
2. Parse returned metrics and update Project models
3. Remove hardcoded random values in `loadSampleProjects()`
4. Test end-to-end iOS ↔ Backend integration

**Acceptance Criteria:**
- ✅ iOS app shows dynamic health scores from backend (92%, 87%)
- ✅ No more hardcoded 90%, 85% values anywhere in codebase
- ✅ Projects refresh with real-time calculated metrics

### 2. HIGH: Fix Color Contrast Accessibility Issues
**Priority**: HIGH  
**Estimated Time**: 15-20 minutes  
**Status**: Issues identified, fix pending  

**Files to Fix:**
- `ProjectDetailView.swift:84,88,140,217,242` - Replace light gray backgrounds

**Implementation Steps:**
1. Replace `Color(red: 0.95, green: 0.95, blue: 0.97)` with accessible alternatives
2. Ensure WCAG AA compliance (4.5:1 contrast ratio)
3. Test with iOS Accessibility Inspector
4. Validate color combinations across light/dark modes

**Acceptance Criteria:**
- ✅ All project cards meet WCAG AA standards
- ✅ Text remains readable in all conditions
- ✅ No user reports of poor visibility

### 3. MEDIUM: Implement Functional Quick Actions
**Priority**: MEDIUM  
**Estimated Time**: 20-30 minutes  
**Status**: Empty implementations identified  

**Files to Fix:**
- `ProjectDashboardView.swift:228-248` - Implement navigation for empty quick actions

**Implementation Steps:**
1. Replace empty "Agent Chat" action with NavigationCoordinator tab switch
2. Replace empty "Monitor" action with monitor tab navigation
3. Replace empty "Settings" action with settings tab navigation
4. Test all navigation flows work correctly

**Acceptance Criteria:**
- ✅ "Agent Chat" button navigates to Agent tab
- ✅ "Monitor" button navigates to Monitor tab  
- ✅ "Settings" button navigates to Settings tab
- ✅ All actions provide user feedback

## 🔧 Technical Preparation Notes

### Backend Status
- ✅ All project APIs implemented and tested
- ✅ Dynamic health score calculation working (92%, 87%)
- ✅ Sample data includes realistic task and project information
- ✅ Pydantic models with proper enum inheritance

### iOS Integration Points
- **WebSocketService**: Already available as `.shared` singleton
- **NavigationCoordinator**: Already handles tab switching logic
- **Project Models**: Already compatible with backend schema
- **Error Handling**: Consider network failure scenarios

### Testing Strategy
1. **Unit Testing**: Backend ProjectService already validated
2. **Integration Testing**: iOS ↔ Backend API calls need verification
3. **UI Testing**: Color contrast and navigation functionality
4. **Accessibility Testing**: WCAG compliance validation

## 📊 Expected Session Outcomes

### Completion Metrics
- **Hard-coded Metrics Fix**: 50% → 100% complete
- **Color Contrast Issues**: 0% → 100% complete  
- **Quick Actions Functionality**: 0% → 100% complete
- **Overall Projects Section**: 60% → 95% complete

### Quality Gates
- ✅ All iOS builds succeed
- ✅ Backend APIs return dynamic data
- ✅ Accessibility standards met
- ✅ Navigation flows work correctly
- ✅ No hardcoded values remain

### User Experience Impact
- **Before**: Fake metrics, poor contrast, broken actions
- **After**: Real-time data, accessible design, functional navigation
- **Benefit**: Professional, production-ready Projects section

## 🚀 Workflow Recommendations

### Start Session Protocol
1. **Wake Command**: Use `/wake` to restore context from memory
2. **Backend Verification**: Ensure backend server running on port 8002
3. **iOS Build Check**: Verify current build state before changes
4. **Todo List Review**: Check current task status

### Implementation Order
1. **Backend-First Validation**: Test new APIs work correctly
2. **iOS Integration**: One file at a time with build verification
3. **UI Polish**: Color contrast and accessibility improvements
4. **Navigation Enhancement**: Quick actions implementation
5. **End-to-end Testing**: Full user journey validation

### Quality Assurance
1. **Each Change**: Build validation before proceeding
2. **Each File**: Individual testing of modified components
3. **Each Feature**: User experience verification
4. **Session End**: Comprehensive integration testing

## 🧠 Context Optimization

### Memory Usage Strategy
- **Focused Approach**: Target specific files and line numbers
- **Batch Operations**: Group related changes in single edits
- **Progressive Building**: Each change builds on previous success

### Session Continuity
- **Progress Tracking**: Update todos as tasks complete
- **Decision Documentation**: Record rationale for choices
- **Issue Resolution**: Mark problems solved with evidence

### Knowledge Preservation
- **Implementation Notes**: Document any unexpected findings
- **Pattern Recognition**: Record successful approaches for future use
- **Quality Standards**: Maintain build success and test coverage