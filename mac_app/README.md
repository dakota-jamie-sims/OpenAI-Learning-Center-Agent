# Dakota Content Generator - Mac App

A native Mac application for generating institutional investment content with AI.

## Features

- 🎯 Simple, native Mac interface
- 📝 Topic-based article generation
- 📊 Optional spreadsheet data analysis
- 📁 Choose where to save outputs
- 🔐 Embedded API keys (no setup required)
- ⚡ Progress tracking
- 🎨 Professional 4-file output package

## For Users

### Installation

1. **Download** `Dakota-Content-Generator.dmg`
2. **Open** the DMG file
3. **Drag** Dakota Content Generator to your Applications folder
4. **Launch** from Applications (you may need to right-click → Open the first time)

### Usage

1. **Enter topic** - What you want to write about
2. **Select word count** - Short (800), Standard (1,750), or Long (2,500)
3. **Optional: Add data** - Drag and drop a CSV or Excel file for data analysis
4. **Choose save location** - Where to save the generated files
5. **Click Generate** - Wait 2-3 minutes for completion
6. **Access files** - Folder opens automatically when done

### Output Files

Each generation creates a folder with:
- `article.md` - The main article
- `metadata.md` - SEO information and metrics
- `social-media.md` - Social media posts
- `summary.md` - Executive summary

## For Developers

### Building the App

#### Prerequisites
- macOS 10.14 or later
- Python 3.8 or later
- API keys (OpenAI, Vector Store, Serper)

#### Quick Build

```bash
cd mac_app
./install_and_build.sh
```

This will:
1. Ask for your API keys
2. Install dependencies
3. Build the .app bundle
4. Create a DMG installer

#### Manual Build

```bash
# Install dependencies
pip install -r requirements.txt

# Build with your API keys
python3 build_mac_app.py \
    --openai-key "sk-..." \
    --vector-store-id "vs_..." \
    --serper-key "..." \
    --dmg
```

### Project Structure

```
mac_app/
├── dakota_mac_app.py      # Main GUI application
├── build_mac_app.py       # Build script
├── install_and_build.sh   # Easy build script
├── requirements.txt       # Dependencies
└── dist/                  # Built app (after building)
    ├── Dakota Content Generator.app
    └── Dakota-Content-Generator.dmg
```

### How It Works

1. **GUI Layer** - Native Mac interface using tkinter
2. **API Keys** - Embedded during build process
3. **Script Wrapper** - Calls existing Python scripts via subprocess
4. **File Management** - Copies outputs to user's chosen location
5. **Progress Tracking** - Parses script output for phase updates

### Customization

To customize the app:

1. **Change name**: Edit `--name` parameter in build script
2. **Add icon**: Place `dakota_icon.icns` in mac_app folder
3. **Modify UI**: Edit `dakota_mac_app.py`
4. **Update scripts**: The app uses the parent project's scripts

### Troubleshooting

**"App can't be opened because it is from an unidentified developer"**
- Right-click the app and select "Open"
- Or go to System Preferences → Security & Privacy → Open Anyway

**"Generation failed" error**
- Check internet connection
- Verify API keys are valid
- Check console output: `/Applications/Utilities/Console.app`

**App won't build**
- Ensure all Python dependencies are installed
- Check that API keys don't contain special characters
- Try building in a fresh virtual environment

### Distribution

To distribute to your team:

1. **Build** the app with embedded API keys
2. **Sign** (optional): `codesign --deep -s "Developer ID" dist/*.app`
3. **Share** the DMG file via email/Slack/shared drive
4. **Users** install by dragging to Applications

## Security Notes

- API keys are embedded in the app binary
- Keys are only accessible to users who have the app
- For additional security, consider:
  - Code signing with Apple Developer ID
  - Notarization for Gatekeeper approval
  - Encrypted key storage with keychain access

## Support

For issues or questions:
1. Check the troubleshooting section
2. View logs in Console.app
3. Contact your IT administrator