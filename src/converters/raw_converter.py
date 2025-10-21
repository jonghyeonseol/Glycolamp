"""
RAW to mzML Converter

Wrapper for ThermoRawFileParser to convert Thermo Fisher .raw files to open mzML format.
Implements ORIGINAL and ENDURING ALCOA++ principles.
"""

import subprocess
from pathlib import Path
from typing import Optional
import platform


class RawConverter:
    """
    Converts Thermo Fisher .raw files to mzML format

    Uses ThermoRawFileParser (cross-platform, open-source)
    https://github.com/compomics/ThermoRawFileParser
    """

    def __init__(self, thermo_parser_path: Optional[str] = None):
        """
        Initialize RAW converter

        Parameters
        ----------
        thermo_parser_path : str, optional
            Path to ThermoRawFileParser.exe
            If None, assumes it's in PATH or will provide instructions
        """
        self.thermo_parser_path = thermo_parser_path
        self.is_windows = platform.system() == "Windows"

    def convert_to_mzml(
        self,
        raw_file_path: str,
        output_dir: str = "Results/data/02_mzml_files",
        peak_picking: bool = True,
        gzip: bool = True,
        metadata_format: str = "json"
    ) -> str:
        """
        Convert .raw file to .mzML

        Parameters
        ----------
        raw_file_path : str
            Path to input .raw file
        output_dir : str
            Output directory for mzML file
        peak_picking : bool
            Enable peak picking (default: True)
            If False, uses profile mode (larger files)
        gzip : bool
            Compress output with gzip (default: True)
        metadata_format : str
            Metadata format: 'json', 'txt', or 'none'

        Returns
        -------
        str
            Path to generated mzML file

        Raises
        ------
        FileNotFoundError
            If input .raw file doesn't exist
        RuntimeError
            If ThermoRawFileParser is not installed or conversion fails
        """
        raw_file_path = Path(raw_file_path)
        if not raw_file_path.exists():
            raise FileNotFoundError(f"RAW file not found: {raw_file_path}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if ThermoRawFileParser is available
        if not self._is_thermo_parser_available():
            raise RuntimeError(
                "ThermoRawFileParser not found. Please install it:\n"
                "  - Download from: https://github.com/compomics/ThermoRawFileParser/releases\n"
                "  - Or use conda: conda install -c bioconda thermorawfileparser\n"
                "  - Or use Docker: docker pull quay.io/biocontainers/thermorawfileparser"
            )

        # Build command
        cmd = self._build_command(
            raw_file_path=str(raw_file_path),
            output_dir=str(output_dir),
            peak_picking=peak_picking,
            gzip=gzip,
            metadata_format=metadata_format
        )

        # Execute conversion
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Determine output file name
            output_name = raw_file_path.stem
            if gzip:
                output_file = output_dir / f"{output_name}.mzML.gz"
            else:
                output_file = output_dir / f"{output_name}.mzML"

            if not output_file.exists():
                raise RuntimeError(f"Expected output file not found: {output_file}")

            return str(output_file)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ThermoRawFileParser failed:\n"
                f"  Command: {' '.join(cmd)}\n"
                f"  Error: {e.stderr}"
            )

    def _is_thermo_parser_available(self) -> bool:
        """Check if ThermoRawFileParser is installed"""
        try:
            if self.thermo_parser_path:
                return Path(self.thermo_parser_path).exists()

            # Try to find in PATH
            result = subprocess.run(
                ["ThermoRawFileParser", "--help"] if self.is_windows else ["mono", "ThermoRawFileParser.exe", "--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _build_command(
        self,
        raw_file_path: str,
        output_dir: str,
        peak_picking: bool,
        gzip: bool,
        metadata_format: str
    ) -> list:
        """Build ThermoRawFileParser command"""

        if self.thermo_parser_path:
            base_cmd = [self.thermo_parser_path] if self.is_windows else ["mono", self.thermo_parser_path]
        else:
            base_cmd = ["ThermoRawFileParser"] if self.is_windows else ["mono", "ThermoRawFileParser.exe"]

        cmd = base_cmd + [
            f"-i={raw_file_path}",
            f"-o={output_dir}",
            "-f=1",  # mzML format
        ]

        # Metadata format
        metadata_map = {"json": "0", "txt": "1", "none": "2"}
        cmd.append(f"-m={metadata_map.get(metadata_format, '0')}")

        # Peak picking
        if not peak_picking:
            cmd.append("-p")  # -p flag DISABLES peak picking (profile mode)

        # Gzip compression
        if gzip:
            cmd.append("-g")

        return cmd

    def batch_convert(
        self,
        raw_file_paths: list,
        output_dir: str = "Results/data/02_mzml_files",
        **kwargs
    ) -> list:
        """
        Convert multiple .raw files

        Parameters
        ----------
        raw_file_paths : list
            List of .raw file paths
        output_dir : str
            Output directory
        **kwargs
            Additional arguments passed to convert_to_mzml()

        Returns
        -------
        list
            List of output mzML file paths
        """
        mzml_files = []

        for raw_file in raw_file_paths:
            try:
                mzml_file = self.convert_to_mzml(
                    raw_file_path=raw_file,
                    output_dir=output_dir,
                    **kwargs
                )
                mzml_files.append(mzml_file)

            except Exception as e:
                print(f"Warning: Failed to convert {raw_file}: {e}")
                continue

        return mzml_files
