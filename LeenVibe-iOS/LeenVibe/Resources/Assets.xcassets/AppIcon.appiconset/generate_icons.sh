#!/bin/bash

# LeanVibe App Icon Generator Script
# This script generates all required iOS app icon sizes from a source image

echo "🎨 LeanVibe App Icon Generator"
echo "=============================="

# Check if source image exists
if [ ! -f "source-icon.png" ]; then
    echo "❌ Error: source-icon.png not found!"
    echo "Please save your LB logo image as 'source-icon.png' in this directory first."
    echo "Image should be 1024x1024 pixels or larger."
    exit 1
fi

echo "📱 Generating iPhone icon sizes..."

# iPhone sizes
sips -z 40 40 source-icon.png --out icon_20@2x.png
sips -z 60 60 source-icon.png --out icon_20@3x.png
sips -z 58 58 source-icon.png --out icon_29@2x.png
sips -z 87 87 source-icon.png --out icon_29@3x.png
sips -z 80 80 source-icon.png --out icon_40@2x.png
sips -z 120 120 source-icon.png --out icon_40@3x.png
sips -z 120 120 source-icon.png --out icon_60@2x.png
sips -z 180 180 source-icon.png --out icon_60@3x.png

echo "📱 Generating iPad icon sizes..."

# iPad sizes
sips -z 20 20 source-icon.png --out icon_20_ipad@1x.png
sips -z 40 40 source-icon.png --out icon_20_ipad@2x.png
sips -z 29 29 source-icon.png --out icon_29_ipad@1x.png
sips -z 58 58 source-icon.png --out icon_29_ipad@2x.png
sips -z 40 40 source-icon.png --out icon_40_ipad@1x.png
sips -z 80 80 source-icon.png --out icon_40_ipad@2x.png
sips -z 76 76 source-icon.png --out icon_76@1x.png
sips -z 152 152 source-icon.png --out icon_76@2x.png
sips -z 167 167 source-icon.png --out icon_83.5@2x.png

echo "🏪 Generating App Store icon size..."

# App Store
sips -z 1024 1024 source-icon.png --out icon_1024.png

echo ""
echo "✅ All app icon sizes generated successfully!"
echo ""
echo "📋 Generated files:"
ls -la icon_*.png
echo ""
echo "🚀 Next steps:"
echo "1. Build the app: xcodebuild -project ../../../LeanVibe.xcodeproj -scheme LeanVibe build"
echo "2. Deploy to device to see your new icon!"
echo ""
echo "🎯 Your new LB logo is now ready for LeanVibe!"