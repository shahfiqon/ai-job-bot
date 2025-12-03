"""Service for generating resume PDFs from JSON using jsonresume-theme-caffine."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from app.config import settings


class ResumeService:
    """Service for generating PDF resumes from JSON using Node.js theme."""

    def __init__(
        self,
        theme_path: str | None = None,
        storage_dir: str | None = None,
    ):
        """
        Initialize ResumeService.

        Args:
            theme_path: Path to jsonresume-theme-caffine project
            storage_dir: Directory to store generated PDFs
        """
        self.theme_path = Path(theme_path or settings.JSONRESUME_THEME_PATH)
        self.storage_dir = Path(storage_dir or settings.RESUME_PDF_STORAGE_DIR)
        self.cli_script = self.theme_path / "cli.js"

    def get_pdf_path(self, user_id: int, job_id: int) -> Path:
        """
        Construct deterministic PDF path for a user and job.

        Args:
            user_id: User ID
            job_id: Job ID

        Returns:
            Path to the PDF file
        """
        filename = f"user_{user_id}_job_{job_id}.pdf"
        return self.storage_dir / filename

    def ensure_pdf_generated(
        self,
        resume_json: str | Dict[str, Any],
        user_id: int,
        job_id: int,
    ) -> Path:
        """
        Check if PDF exists, generate if missing.

        Args:
            resume_json: Resume JSON as string or dict
            user_id: User ID
            job_id: Job ID

        Returns:
            Path to the generated PDF

        Raises:
            FileNotFoundError: If theme CLI script not found
            subprocess.CalledProcessError: If PDF generation fails
            ValueError: If resume_json is invalid
        """
        pdf_path = self.get_pdf_path(user_id, job_id)

        # Check if PDF already exists
        if pdf_path.exists():
            logger.info(f"PDF already exists at {pdf_path}, skipping generation")
            return pdf_path

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Parse resume JSON if it's a string
        if isinstance(resume_json, str):
            try:
                resume_dict = json.loads(resume_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}") from e
        else:
            resume_dict = resume_json

        # Generate PDF
        return self.generate_pdf_from_resume(resume_dict, pdf_path)

    def generate_pdf_from_resume(
        self,
        resume_dict: Dict[str, Any],
        output_path: Path,
    ) -> Path:
        """
        Generate PDF from resume JSON using Node.js CLI.

        Args:
            resume_dict: Resume data as dictionary
            output_path: Path where PDF should be saved

        Returns:
            Path to the generated PDF

        Raises:
            FileNotFoundError: If theme CLI script not found
            subprocess.CalledProcessError: If PDF generation fails
        """
        # Validate CLI script exists
        if not self.cli_script.exists():
            raise FileNotFoundError(
                f"Resume theme CLI script not found at {self.cli_script}. "
                f"Please ensure jsonresume-theme-caffine is installed at {self.theme_path}"
            )

        # Create temporary resume file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            dir=self.storage_dir,
            delete=False,
        ) as tmp_resume:
            json.dump(resume_dict, tmp_resume, indent=2)
            tmp_resume_path = tmp_resume.name

        try:
            logger.info(f"Generating PDF from {tmp_resume_path} to {output_path}")

            # Call Node.js CLI script to generate PDF
            result = subprocess.run(
                [
                    "node",
                    str(self.cli_script),
                    "-i",
                    tmp_resume_path,
                    "-o",
                    str(output_path),
                    "--tmp-dir",
                    str(self.storage_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if not output_path.exists():
                raise FileNotFoundError(
                    f"PDF generation completed but file not found at {output_path}. "
                    f"CLI output: {result.stdout}"
                )

            logger.info(f"Successfully generated PDF at {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to generate PDF: {e.stderr or e.stdout}"
            logger.error(error_msg)
            raise subprocess.CalledProcessError(
                e.returncode, e.cmd, e.stdout, e.stderr
            ) from e
        finally:
            # Clean up temporary resume file
            Path(tmp_resume_path).unlink(missing_ok=True)


