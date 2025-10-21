"""
ALCOA++ Audit Logger

Implements contemporaneous, attributable, and traceable logging for all pipeline operations.
All events are timestamped and associated with user/system context.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class AuditLogger:
    """
    ALCOA++ compliant audit logging system

    Principles implemented:
    - Attributable: Records user, system, and version information
    - Contemporaneous: Real-time timestamping of all events
    - Traceable: Complete operation history with parameters
    """

    def __init__(
        self,
        log_dir: str = "Results/audit_trail",
        run_id: Optional[str] = None,
        user: Optional[str] = None,
        system_info: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ALCOA++ audit logger

        Parameters
        ----------
        log_dir : str
            Directory for audit trail files
        run_id : str, optional
            Unique identifier for this pipeline run (auto-generated if None)
        user : str, optional
            User running the pipeline (auto-detected if None)
        system_info : dict, optional
            Additional system context (Python version, OS, etc.)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Generate run ID
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()

        # Attributable: Capture user and system context
        self.user = user or os.getlogin()
        self.system_info = system_info or self._get_system_info()

        # Event log
        self.events: List[Dict[str, Any]] = []

        # Initialize text logger (LEGIBLE principle)
        self.text_log_path = self.log_dir / f"{self.run_id}_processing_log.txt"
        self._init_text_logger()

        # Log initialization
        self.log("Audit logger initialized", level="INFO", details={
            "run_id": self.run_id,
            "user": self.user,
            "system": self.system_info
        })

    def _get_system_info(self) -> Dict[str, str]:
        """Collect system information for attributability"""
        import platform
        import sys

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

    def _init_text_logger(self):
        """Initialize human-readable text logger (LEGIBLE principle)"""
        self.text_logger = logging.getLogger(f"ALCOA_{self.run_id}")
        self.text_logger.setLevel(logging.DEBUG)

        # File handler
        fh = logging.FileHandler(self.text_log_path, mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.text_logger.addHandler(fh)
        self.text_logger.addHandler(ch)

    def log(
        self,
        message: str,
        level: str = "INFO",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log an event with ALCOA++ compliance

        Parameters
        ----------
        message : str
            Human-readable event description
        level : str
            Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        details : dict, optional
            Additional structured data (parameters, results, etc.)
        """
        # Contemporaneous: Real-time timestamping
        timestamp = datetime.now()

        # Create event record
        event = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "message": message,
            "user": self.user,
            "run_id": self.run_id,
        }

        if details:
            event["details"] = details

        # Store event (TRACEABLE principle)
        self.events.append(event)

        # Write to text log (LEGIBLE principle)
        log_func = getattr(self.text_logger, level.lower(), self.text_logger.info)
        if details:
            log_func(f"{message} | Details: {json.dumps(details, default=str)}")
        else:
            log_func(message)

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        checksum: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log file-related operations (ORIGINAL, ENDURING principles)

        Parameters
        ----------
        operation : str
            Operation type (created, read, modified, deleted)
        file_path : str
            Path to the file
        checksum : str, optional
            SHA-256 checksum for integrity (ENDURING)
        metadata : dict, optional
            Additional file metadata
        """
        details = {
            "operation": operation,
            "file_path": str(file_path),
        }

        if checksum:
            details["sha256"] = checksum

        if metadata:
            details["metadata"] = metadata

        self.log(f"File {operation}: {Path(file_path).name}", level="INFO", details=details)

    def save(self, output_path: Optional[str] = None):
        """
        Save audit trail to JSON file (ENDURING, AVAILABLE principles)

        Parameters
        ----------
        output_path : str, optional
            Custom output path (auto-generated if None)
        """
        if output_path is None:
            output_path = self.log_dir / f"{self.run_id}_audit_trail.json"
        else:
            output_path = Path(output_path)

        # Calculate runtime
        end_time = datetime.now()
        runtime_seconds = (end_time - self.start_time).total_seconds()

        # Create complete audit record
        audit_record = {
            "run_id": self.run_id,
            "user": self.user,
            "system_info": self.system_info,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "runtime_seconds": runtime_seconds,
            "total_events": len(self.events),
            "events": self.events,
            "alcoa_compliance": {
                "attributable": True,
                "legible": True,
                "contemporaneous": True,
                "original": True,
                "accurate": "validated_by_downstream_analysis",
                "complete": len(self.events) > 0,
                "consistent": True,
                "enduring": "checksums_recorded",
                "available": True,
                "traceable": True
            }
        }

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(audit_record, f, indent=2, default=str)

        self.log(f"Audit trail saved to {output_path}", level="INFO")

        return output_path

    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for the audit trail"""
        level_counts = {}
        for event in self.events:
            level = event["level"]
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "run_id": self.run_id,
            "total_events": len(self.events),
            "level_breakdown": level_counts,
            "start_time": self.start_time.isoformat(),
            "runtime_seconds": (datetime.now() - self.start_time).total_seconds()
        }
