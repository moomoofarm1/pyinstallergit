# Assets Directory

This directory contains assets used for building the ALF executable.

## Files

- `alf_icon.ico` - Application icon for Windows executable (to be added)
- `version_info.txt` - Windows version information (generated during build)

## Icon Creation

To create the application icon:

1. Create or find a suitable icon image (PNG/SVG)
2. Convert to ICO format using online tools or:
   ```bash
   # Using ImageMagick
   magick icon.png -resize 256x256 alf_icon.ico
   ```
3. Place the `alf_icon.ico` file in this directory

## Build Process

The icon and version information are automatically included during the PyInstaller build process.