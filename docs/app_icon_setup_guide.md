# LeanVibe App Icon Setup Guide

## 🎨 New App Icon Design
Your new "LB" logo design features:
- Sleek cyan/turquoise circuit-style lettering
- Black background
- Modern, tech-focused aesthetic
- Perfect for the LeanVibe development tool brand

## 📱 Required Icon Sizes

iOS requires multiple icon sizes for different contexts:

### iPhone Icons
- 20x20 (2x, 3x) = 40x40, 60x60
- 29x29 (2x, 3x) = 58x58, 87x87  
- 40x40 (2x, 3x) = 80x80, 120x120
- 60x60 (2x, 3x) = 120x120, 180x180

### iPad Icons  
- 20x20 (1x, 2x) = 20x20, 40x40
- 29x29 (1x, 2x) = 29x29, 58x58
- 40x40 (1x, 2x) = 40x40, 80x80
- 76x76 (1x, 2x) = 76x76, 152x152
- 83.5x83.5 (2x) = 167x167

### App Store
- 1024x1024 (1x) = 1024x1024

## 🛠️ Setup Methods

### Method 1: Automatic Icon Generation (Recommended)

I'll help you create a script to generate all sizes from your source image:

```bash
# Save your uploaded image as source-icon.png (1024x1024 minimum)
# Then run this script to generate all required sizes

#!/bin/bash
cd /Users/bogdan/work/leanvibe-ai/LeanVibe-iOS/LeanVibe/Resources/Assets.xcassets/AppIcon.appiconset

# iPhone sizes
sips -z 40 40 source-icon.png --out icon_20@2x.png
sips -z 60 60 source-icon.png --out icon_20@3x.png
sips -z 58 58 source-icon.png --out icon_29@2x.png
sips -z 87 87 source-icon.png --out icon_29@3x.png
sips -z 80 80 source-icon.png --out icon_40@2x.png
sips -z 120 120 source-icon.png --out icon_40@3x.png
sips -z 120 120 source-icon.png --out icon_60@2x.png
sips -z 180 180 source-icon.png --out icon_60@3x.png

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

# App Store
sips -z 1024 1024 source-icon.png --out icon_1024.png

echo "All app icon sizes generated!"
```

### Method 2: Using Xcode Asset Catalog

1. Open Xcode
2. Navigate to `LeanVibe/Resources/Assets.xcassets/AppIcon.appiconset`
3. Drag your 1024x1024 source image into the App Store slot
4. Xcode can automatically generate other sizes

### Method 3: Manual Creation

Create each size manually using your preferred image editor and save them with the exact filenames from Contents.json.

## 🔄 Current Status

The Contents.json file is already configured with all the correct filenames:
- ✅ Contents.json configured
- ❌ PNG files need to be created
- ❌ Source image needs to be placed

## 📋 Next Steps

1. **Save your source image** as a high-resolution PNG (1024x1024 minimum)
2. **Run the generation script** or use Xcode's automatic generation
3. **Build and deploy** the app to see the new icon
4. **Test on device** to ensure all icon sizes display correctly

## 🎯 Quick Setup Command

Once you have your source image ready, run:

```bash
cd /Users/bogdan/work/leanvibe-ai/LeanVibe-iOS/LeanVibe/Resources/Assets.xcassets/AppIcon.appiconset
# Place your source-icon.png here first
# Then run the generation script above
```

## ✅ Verification

After setup, verify:
- [ ] All PNG files exist in AppIcon.appiconset directory
- [ ] Build succeeds without warnings
- [ ] Icon appears correctly on device home screen  
- [ ] Icon appears correctly in Settings > Apps
- [ ] Icon appears correctly in App Store (1024x1024)

Your new "LB" logo will give LeanVibe a professional, modern appearance that reflects its role as a sophisticated development tool!