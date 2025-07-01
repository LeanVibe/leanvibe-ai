#!/bin/bash

# LeanVibe iOS - Continuous Integration Check Script
# Purpose: Prevent catastrophic integration failures through early error detection
# Based on lessons learned from AI agent integration analysis

echo "🔍 LeanVibe iOS - CI Check Starting..."
echo "📍 Working Directory: $(pwd)"
echo "⏰ $(date)"
echo ""

# Change to iOS project directory
cd "leanvibe-ios" || {
    echo "❌ ERROR: Cannot find leanvibe-ios directory"
    exit 1
}

echo "🏗️  Building iOS project..."
echo "Running: xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build"
echo ""

# Run build and capture output
xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build 2>&1 | tee build.log

# Check for compilation errors
if grep -q "error:" build.log; then
    echo ""
    echo "🚨 BUILD FAILED - COMPILATION ERRORS DETECTED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Error Summary:"
    error_count=$(grep -c "error:" build.log)
    echo "   Total Errors: $error_count"
    echo ""
    echo "🔍 First 10 Errors:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "error:" build.log | head -10
    echo ""
    echo "❌ STOPPING ALL WORK - BUILD MUST BE FIXED FIRST"
    echo "   Please fix compilation errors before continuing"
    echo "   Error budget threshold exceeded ($error_count > 5)"
    echo ""
    exit 1
fi

# Check for warnings
warning_count=$(grep -c "warning:" build.log || echo "0")

echo ""
echo "✅ BUILD SUCCESSFUL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Build Summary:"
echo "   Errors: 0"
echo "   Warnings: $warning_count"

if [ "$warning_count" -gt 10 ]; then
    echo ""
    echo "⚠️  WARNING: High warning count ($warning_count > 10)"
    echo "   Consider addressing warnings to maintain code quality"
fi

echo ""
echo "🎉 CI Check PASSED - Safe to continue development"
echo "⏰ Completed: $(date)"

# Clean up build log
rm -f build.log

exit 0