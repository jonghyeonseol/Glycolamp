# Data Preparation Guide

This guide covers how to prepare mass spectrometry data for analysis with Glycolamp.

## Converting .raw Files to .mzML Format

Glycolamp requires mass spectrometry data in `.mzML` format. If you have Thermo `.raw` files, you need to convert them first.

### macOS (Apple Silicon/Intel)

#### Recommended: ThermoRawFileParser with Mono

This method works natively on Apple Silicon Macs (M1/M2/M3) and Intel Macs.

**Step 1: Install Mono**

```bash
brew install mono
```

**Step 2: Download ThermoRawFileParser**

```bash
cd ~/Downloads
curl -L -o ThermoRawFileParser.zip https://github.com/compomics/ThermoRawFileParser/releases/download/v1.4.3/ThermoRawFileParser1.4.3.zip
unzip ThermoRawFileParser.zip -d ThermoRawFileParser_bin
```

**Step 3: Convert Your Files**

```bash
# Set Mono environment variable
export MONO_GAC_PREFIX="/opt/homebrew"

# Convert single file
mono ~/Downloads/ThermoRawFileParser_bin/ThermoRawFileParser.exe \
  -i /path/to/your/data.raw \
  -o /path/to/output/directory \
  -f 1  # 1 = mzML format

# Convert multiple files in a directory
for file in /path/to/raw/files/*.raw; do
  mono ~/Downloads/ThermoRawFileParser_bin/ThermoRawFileParser.exe \
    -i "$file" \
    -o /path/to/output/directory \
    -f 1
done
```

**Output Format Options:**
- `-f 0`: MGF format
- `-f 1`: mzML format (recommended for Glycolamp)
- `-f 2`: Indexed mzML format
- `-f 3`: Parquet format

**Example Output:**

```
2025-10-22 10:31:32 INFO Started parsing data.raw
2025-10-22 10:31:41 INFO Processing 62701 MS scans
10% 20% 30% 40% 50% 60% 70% 80% 90% 100%
2025-10-22 10:34:05 INFO Finished parsing data.raw
2025-10-22 10:34:05 INFO Processing completed 0 errors, 0 warnings
```

### Windows

#### ProteoWizard MSConvert

**Step 1: Download and Install**
- Visit: http://proteowizard.sourceforge.net/download.html
- Download the installer for Windows
- Run the installer

**Step 2: Convert Files**

**Using GUI:**
1. Open MSConvert
2. Add `.raw` files
3. Select output format: `mzML`
4. Click "Start"

**Using Command Line:**
```cmd
msconvert data.raw --mzML --filter "peakPicking true 1-"
```

### Linux

#### Docker with ProteoWizard

```bash
docker pull chambm/pwiz-skyline-i-agree-to-the-vendor-licenses

docker run -v /path/to/data:/data \
  chambm/pwiz-skyline-i-agree-to-the-vendor-licenses \
  wine msconvert /data/file.raw \
  --mzML \
  --filter "peakPicking true 1-" \
  -o /data
```

**Note**: Docker approach does NOT work on Apple Silicon Macs due to platform incompatibility.

---

## Troubleshooting

### Apple Silicon (M1/M2/M3) Docker Issues

**Problem**: Docker images crash with errors like:
```
wine: dlls/ntdll/unix/virtual.c:260: anon_mmap_fixed: Assertion failed
```

**Solution**: Use ThermoRawFileParser with Mono instead (see macOS section above).

**Why**: ProteoWizard Docker images are built for x86_64 architecture and rely on Wine, which doesn't work well under emulation on ARM-based Macs.

### Mono Not Found

**Problem**: `mono: command not found`

**Solution**:
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Mono
brew install mono
```

### MONO_GAC_PREFIX Error

**Problem**: Mono runtime errors about assemblies

**Solution**: Set the environment variable before running:
```bash
export MONO_GAC_PREFIX="/opt/homebrew"
```

Or add to your `~/.zshrc` or `~/.bashrc`:
```bash
echo 'export MONO_GAC_PREFIX="/opt/homebrew"' >> ~/.zshrc
source ~/.zshrc
```

---

## File Size Expectations

Typical file size changes after conversion:

| Format | Example Size | Notes |
|--------|-------------|-------|
| `.raw` (Thermo) | 1.1 GB | Binary, proprietary |
| `.mzML` (converted) | 500-600 MB | XML-based, ~50% of .raw |
| `.mzML.gz` (compressed) | 100-150 MB | Gzipped mzML |

---

## Verifying Conversion Success

After conversion, verify the output:

```bash
# Check file size (should be 40-60% of original .raw file)
ls -lh output_directory/*.mzML

# Quick validation with Python
python3 << EOF
from pyteomics import mzml
reader = mzml.read('path/to/file.mzML')
first_scan = next(reader)
print(f"First scan ID: {first_scan['id']}")
print(f"MS level: {first_scan['ms level']}")
print("✅ Conversion successful!")
EOF
```

---

## Next Steps

After converting your data to `.mzML` format:

1. **Prepare your protein database** (FASTA format)
2. **Configure search parameters** (see [PIPELINE_QUICKSTART.md](PIPELINE_QUICKSTART.md))
3. **Run the pipeline** (see [README.md](../README.md#basic-usage))

---

## Additional Resources

- **ThermoRawFileParser GitHub**: https://github.com/compomics/ThermoRawFileParser
- **ProteoWizard Documentation**: http://proteowizard.sourceforge.io/
- **mzML Format Specification**: http://www.psidev.info/mzml
- **Pyteomics Documentation**: https://pyteomics.readthedocs.io/

---

## Platform Compatibility Matrix

| Tool | Windows | macOS (Intel) | macOS (Apple Silicon) | Linux |
|------|---------|---------------|----------------------|-------|
| MSConvert (native) | ✅ | ❌ | ❌ | ✅ |
| MSConvert (Docker) | ✅ | ✅ | ❌ | ✅ |
| ThermoRawFileParser (Mono) | ✅ | ✅ | ✅ | ✅ |
| ThermoRawFileParser (Docker) | ✅ | ✅ | ❌ | ✅ |

**✅ = Supported** | **❌ = Not Supported**
