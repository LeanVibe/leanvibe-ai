#!/bin/bash

# Simplified LeenVibe iOS Install Script
# This script builds and installs the app on your connected iOS device

set -e  # Exit on any error

echo "🚀 Building and Installing LeenVibe on your iOS device..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="LeenVibe"
SCHEME="LeenVibe"
CONFIGURATION="Debug"
PROJECT_PATH="LeenVibe.xcodeproj"

echo -e "${BLUE}📱 Project: ${PROJECT_NAME}${NC}"

# Clean previous builds (optional - comment out if you want faster builds)
# echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
# xcodebuild clean -project "$PROJECT_PATH" -scheme "$SCHEME" -configuration "$CONFIGURATION"

# Build and install directly to connected device
echo -e "${YELLOW}🔨 Building and installing for connected iOS device...${NC}"

# This will build and install on the first available connected device
xcodebuild \
    -project "$PROJECT_PATH" \
    -scheme "$SCHEME" \
    -configuration "$CONFIGURATION" \
    -destination "generic/platform=iOS" \
    -allowProvisioningUpdates \
    -allowProvisioningDeviceRegistration \
    CODE_SIGN_IDENTITY="iPhone Developer" \
    DEVELOPMENT_TEAM="GLKDB2BTQG" \
    build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    
    # Find the built app
    APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "${PROJECT_NAME}.app" -path "*/Build/Products/${CONFIGURATION}-iphoneos/*" | head -1)
    
    if [ -n "$APP_PATH" ]; then
        echo -e "${BLUE}📦 App built at: ${APP_PATH}${NC}"
        
        # Try to install using iOS Deploy or devicectl
        echo -e "${YELLOW}📲 Installing on device...${NC}"
        
        # Method 1: Try with devicectl (iOS 17+)
        if command -v devicectl >/dev/null 2>&1; then
            echo -e "${BLUE}Using devicectl for installation...${NC}"
            
            # Get connected device list
            DEVICE_OUTPUT=$(xcrun devicectl list devices 2>/dev/null | grep -E "iPhone|iPad" | head -1 || true)
            
            if [ -n "$DEVICE_OUTPUT" ]; then
                # Extract device ID (first column)
                DEVICE_ID=$(echo "$DEVICE_OUTPUT" | awk '{print $1}')
                echo -e "${BLUE}Installing on device: ${DEVICE_ID}${NC}"
                
                xcrun devicectl device install app --device "${DEVICE_ID}" "${APP_PATH}"
                
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}🎉 Successfully installed ${PROJECT_NAME}!${NC}"
                    echo -e "${GREEN}✅ You can now launch the app from your home screen${NC}"
                else
                    echo -e "${YELLOW}⚠️ devicectl install failed, but app was built successfully${NC}"
                    echo -e "${BLUE}📱 Try installing manually through Xcode or use iTunes/Finder${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️ Could not detect device with devicectl${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ devicectl not available${NC}"
        fi
        
        # Method 2: Instructions for manual installation
        echo -e "${BLUE}💡 If automatic installation failed:${NC}"
        echo -e "${BLUE}1. Open Xcode${NC}"
        echo -e "${BLUE}2. Go to Window > Devices and Simulators${NC}"
        echo -e "${BLUE}3. Select your device${NC}"
        echo -e "${BLUE}4. Drag the app from: ${APP_PATH}${NC}"
        echo -e "${BLUE}5. Or run: open ${APP_PATH%/*}${NC}"
        
    else
        echo -e "${RED}❌ Could not find built app!${NC}"
        echo -e "${YELLOW}💡 Check Xcode organizer or build manually${NC}"
    fi
    
else
    echo -e "${RED}❌ Build failed!${NC}"
    echo -e "${YELLOW}💡 Check Xcode for detailed error messages${NC}"
    exit 1
fi

echo -e "${GREEN}🎯 Process completed!${NC}"