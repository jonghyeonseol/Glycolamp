"""
ALCOA++ Metadata Generator

Implements COMPLETE, AVAILABLE, and LEGIBLE principles through structured metadata.
Generates comprehensive metadata for all pipeline outputs.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class MetadataGenerator:
    """
    Generates structured metadata for ALCOA++ compliance

    Principles implemented:
    - Complete: Captures all relevant processing parameters
    - Available: Metadata stored alongside data files
    - Legible: JSON format for human and machine readability
    """

    @staticmethod
    def generate_file_metadata(
        file_path: str,
        file_type: str,
        description: str,
        processing_parameters: Optional[Dict[str, Any]] = None,
        source_files: Optional[list] = None,
        checksum: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive metadata for a data file

        Parameters
        ----------
        file_path : str
            Path to the data file
        file_type : str
            Type of file (e.g., 'mzML', 'PSM_results', 'filtered_data')
        description : str
            Human-readable description
        processing_parameters : dict, optional
            Parameters used to generate this file
        source_files : list, optional
            List of input files used
        checksum : str, optional
            SHA-256 checksum for integrity

        Returns
        -------
        dict
            Structured metadata
        """
        file_path = Path(file_path)

        metadata = {
            "file_info": {
                "name": file_path.name,
                "path": str(file_path.resolve()),
                "type": file_type,
                "description": description,
                "size_bytes": file_path.stat().st_size if file_path.exists() else None,
                "created": datetime.now().isoformat(),
            },
            "provenance": {
                "source_files": source_files or [],
                "processing_parameters": processing_parameters or {},
            },
            "integrity": {
                "checksum_algorithm": "SHA-256",
                "checksum": checksum,
            },
            "alcoa_compliance": {
                "complete": True,
                "available": True,
                "legible": True,
            }
        }

        return metadata

    @staticmethod
    def save_metadata(metadata: Dict[str, Any], output_path: str):
        """
        Save metadata to JSON file

        Parameters
        ----------
        metadata : dict
            Metadata dictionary
        output_path : str
            Path for metadata file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)

    @staticmethod
    def generate_run_metadata(
        run_id: str,
        input_files: list,
        config: Dict[str, Any],
        output_files: list,
        runtime_seconds: float,
        user: str
    ) -> Dict[str, Any]:
        """
        Generate metadata for an entire pipeline run

        Parameters
        ----------
        run_id : str
            Unique run identifier
        input_files : list
            List of input file paths
        config : dict
            Configuration parameters
        output_files : list
            List of output file paths
        runtime_seconds : float
            Total runtime
        user : str
            User who ran the pipeline

        Returns
        -------
        dict
            Run metadata
        """
        metadata = {
            "run_info": {
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "user": user,
                "runtime_seconds": runtime_seconds,
            },
            "inputs": {
                "files": input_files,
                "count": len(input_files),
            },
            "outputs": {
                "files": output_files,
                "count": len(output_files),
            },
            "configuration": config,
            "alcoa_compliance": {
                "attributable": True,
                "complete": True,
                "consistent": True,
                "available": True,
            }
        }

        return metadata
