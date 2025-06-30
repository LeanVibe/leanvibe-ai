#!/bin/bash

# LeanVibe iOS Build and Install Script
# This script builds the app and installs it on connected iOS devices

set -e  # Exit on any error

echo "🚀 Starting LeanVibe iOS Build and Install Process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="LeanVibe"
SCHEME="LeanVibe"
CONFIGURATION="Debug"
PROJECT_PATH="LeanVibe.xcodeproj"

echo -e "${BLUE}📱 Project: ${PROJECT_NAME}${NC}"
echo -e "${BLUE}🏗️  Scheme: ${SCHEME}${NC}"
echo -e "${BLUE}⚙️  Configuration: ${CONFIGURATION}${NC}"

# Check if project exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}❌ Error: Project file not found at $PROJECT_PATH${NC}"
    exit 1
fi

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
xcodebuild clean -project "$PROJECT_PATH" -scheme "$SCHEME" -configuration "$CONFIGURATION"

# Check for connected devices using xcodebuild (more reliable)
echo -e "${YELLOW}📱 Checking for connected iOS devices...${NC}"
DEVICES=$(xcodebuild -showdestinations -project "$PROJECT_PATH" -scheme "$SCHEME" 2>/dev/null | grep "platform:iOS" | grep -v "Simulator" | grep -E "iPhone|iPad" || true)

if [ -z "$DEVICES" ]; then
    echo -e "${RED}❌ No connected iOS devices found!${NC}"
    echo -e "${YELLOW}💡 Please connect your iOS device via USB and trust this computer${NC}"
    
    # Try alternative method with xcrun simctl
    echo -e "${YELLOW}🔍 Trying alternative device detection...${NC}"
    xcrun devicectl list devices 2>/dev/null || true
    
    exit 1
fi

echo -e "${GREEN}✅ Connected devices found:${NC}"
echo "$DEVICES"

# Get the first connected device ID and name
DEVICE_LINE=$(echo "$DEVICES" | head -1)
DEVICE_ID=$(echo "$DEVICE_LINE" | grep -o "id:[^,]*" | cut -d: -f2)
DEVICE_NAME=$(echo "$DEVICE_LINE" | grep -o "name:[^}]*" | cut -d: -f2 | sed 's/^ *//' | sed 's/ *$//')

echo -e "${BLUE}🎯 Target device: ${DEVICE_NAME} (${DEVICE_ID})${NC}"

# Build for device
echo -e "${YELLOW}🔨 Building for iOS device...${NC}"
xcodebuild \
    -project "$PROJECT_PATH" \
    -scheme "$SCHEME" \
    -configuration "$CONFIGURATION" \
    -destination "id=${DEVICE_ID}" \
    -allowProvisioningUpdates \
    build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

# Install on device
echo -e "${YELLOW}📲 Installing app on device...${NC}"

# Find the built app
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "${PROJECT_NAME}.app" -path "*/Build/Products/${CONFIGURATION}-iphoneos/*" | head -1)

if [ -z "$APP_PATH" ]; then
    echo -e "${RED}❌ Could not find built app!${NC}"
    exit 1
fi

echo -e "${BLUE}📦 App path: ${APP_PATH}${NC}"

# Install using xcrun devicectl
echo -e "${YELLOW}📱 Installing ${PROJECT_NAME} on ${DEVICE_NAME}...${NC}"

xcrun devicectl device install app --device "${DEVICE_ID}" "${APP_PATH}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Successfully installed ${PROJECT_NAME} on ${DEVICE_NAME}!${NC}"
    echo -e "${GREEN}✅ You can now launch the app from your home screen${NC}"
    
    # Optional: Launch the app
    read -p "Would you like to launch the app now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🚀 Launching ${PROJECT_NAME}...${NC}"
        # Get bundle identifier from Info.plist
        BUNDLE_ID=$(defaults read "${APP_PATH}/Info.plist" CFBundleIdentifier 2>/dev/null || echo "ai.leanvibe.LeanVibe")
        xcrun devicectl device process launch --device "${DEVICE_ID}" "${BUNDLE_ID}"
        echo -e "${GREEN}✅ App launched!${NC}"
    fi
else
    echo -e "${RED}❌ Installation failed!${NC}"
    echo -e "${YELLOW}💡 Make sure your device is unlocked and you've trusted this computer${NC}"
    exit 1
fi

echo -e "${GREEN}🎯 Build and install process completed successfully!${NC}"
echo -e "${BLUE}📱 ${PROJECT_NAME} is now installed on ${DEVICE_NAME}${NC}"