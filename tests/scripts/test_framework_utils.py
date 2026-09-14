"""Test Framework Utilities

Provides workflow-agnostic utility functions used by notebook-derived
environment-validation tests.

These utilities implement functionality shared across validation tests,
including validation reporting, provenance capture, artefact retention,
logging configuration and workflow execution.

This module is not intended to be executed directly. Validation tests are
expected to be executed via:

    run_test.sh --test <test_name>

and should invoke these utilities through:

    test_framework_utils.execute_workflow(run_workflow)

where run_workflow is the notebook-derived workflow implementation for that
validation test.

The utilities in this module are intentionally independent of any specific
notebook-derived workflow and are intended to be reused across all validation
tests.

* Author: Jacob Way
* Affiliation: UK Met Office
* History: 1.0
* Last update: 2026-08-28
* (c) British Crown Copyright 2026, Met Office. Please see LICENSE.md for
  license details.
"""

import subprocess
import sys
import traceback
import datetime
import logging
import pathlib
import os
import json

import matplotlib
import matplotlib.pyplot

RESULT_LEVEL = 60
DATA_SCIENCE_COP_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------
# Testing framework helpers
# ---------------------------------------------------------------------

# Framework configuration

def get_test_name():
    """Retrieve the test name supplied by the wrapper."""
    try:
        test_name_index = sys.argv.index("--test")
        return sys.argv[test_name_index + 1]
    except Exception:
        return "UNKNOWN_TEST_NAME"

def initialise_retention_mode():
    """Initialise the framework's optional run-retention functionality."""
    retention = "--retention" in sys.argv
    return retention, []

def configure_logging():
    """Configure framework logging and support the custom RESULT level."""
    logging.addLevelName(RESULT_LEVEL, "RESULT")
    try:
        log_level_index = sys.argv.index("--log-level")
        supplied_level = sys.argv[log_level_index + 1].upper()

        if supplied_level == "RESULT":
            logging_level = RESULT_LEVEL
        else:
            logging_level = getattr(logging, supplied_level)

        logging.basicConfig(
            level=logging_level,
            format="%(message)s",
        )

    except Exception:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
        )
        if "--log-level" in sys.argv:
            logging.warning("Invalid log level supplied. Falling back to INFO.")

    return logging.getLogger(__name__)

# Provenance

def get_git_version():
    """Capture the executed repository revision as part of run provenance."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"

def get_file_git_status(file_path):
    """Determine whether a repository file was modified at execution time."""
    try:
        unstaged_changes = subprocess.run(
            ["git", "diff", "--quiet", "--", str(file_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode

        staged_changes = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", str(file_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode

        if unstaged_changes == 0 and staged_changes == 0:
            return "CLEAN"

        if unstaged_changes == 1 or staged_changes == 1:
            return "DIRTY"

        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"

def get_git_file_statuses():
    """Collect repository cleanliness information for key framework files."""
    try:
        return {
            "test_script": get_file_git_status(DATA_SCIENCE_COP_ROOT/"tests"/"scripts"/f"test_{TEST_NAME}.py"),
            "test_framework_utils": get_file_git_status(DATA_SCIENCE_COP_ROOT/"tests"/"scripts"/"test_framework_utils.py"),
            "run_test_wrapper": get_file_git_status(DATA_SCIENCE_COP_ROOT/"tests"/"scripts"/"run_test.sh"),
            }
    except Exception:
        return {
            "test_script": "UNKNOWN",
            "test_framework_utils": "UNKNOWN",
            "run_test_wrapper": "UNKNOWN",
        }

# Retention

def create_artefact_directory():
    """Create a unique retention location for this test run."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        artefact_dir = (DATA_SCIENCE_COP_ROOT/"tests"/"test_run_logs"/TEST_NAME/timestamp)
        artefact_dir.mkdir(parents=True, exist_ok=False)
        (DATA_SCIENCE_COP_ROOT/"tests"/"scripts"/"latest_artefact_dir.txt").write_text(str(artefact_dir.resolve()))

        return artefact_dir
    except Exception:
        LOGGER.warning("Run artefacts could not be retained.")
        return None

def save_retained_figures(retained_figures, artefact_dir, retention):
    """Persist retained figures so workflow outputs can be inspected after execution."""
    if not retention:
        return
    try:
        for filename, fig in retained_figures:
            fig.savefig(artefact_dir / filename)
    except Exception:
        LOGGER.warning("Retained figures could not be retained.")

    try:

        for _, fig in retained_figures:
            matplotlib.pyplot.close(fig)
    except Exception:
        pass

def save_metadata(artefact_dir, git_statuses, git_version):
    """Retain provenance information required to identify the executed test context."""
    try:

        metadata = {
            "git_version": git_version,
            "arguments": sys.argv,
            "git_statuses": git_statuses,
            "loaded_environment": os.environ.get("SSS_ENV_NAME", "UNKNOWN"),
        }

        with open(artefact_dir / "metadata.json", "w") as metadata_file:
            json.dump(metadata, metadata_file, indent=2)
    except Exception:
        LOGGER.warning("Metadata could not be retained.")

def handle_figure_retention(fig, filename):
    """Retain or close a figure according to the selected retention mode."""
    if retention:
        retained_figures.append((filename, fig))
    else:
        matplotlib.pyplot.close(fig)

# Finalisation

def finalise_run(retention, retained_figures):
    """Perform final reporting and retention activities before test exit."""
    git_statuses = get_git_file_statuses()
    git_version = get_git_version()
    LOGGER.info("")
    LOGGER.info(f"Git Version: {git_version}")
    LOGGER.info(f"Python Script Status: {git_statuses['test_script']}")
    LOGGER.info(f"Bash Wrapper Status: {git_statuses['run_test_wrapper']}")
    LOGGER.info(f"Test Framework Utils Status: {git_statuses['test_framework_utils']}")
    LOGGER.info("")
    artefact_dir = None
    if retention:
        artefact_dir = create_artefact_directory()
        save_metadata(artefact_dir, git_statuses, git_version)
        save_retained_figures(retained_figures, artefact_dir, retention)

# Result handling

def classify_exception(exc):
    """Provide an initial indication of whether a failure may be environment related."""
    if isinstance(exc, (ModuleNotFoundError, ImportError)):
        return "LIKELY ENVIRONMENT FAILURE"
    if isinstance(exc, (PermissionError, MemoryError)):
        return "UNCLEAR WHETHER ENVIRONMENT FAILURE"
    return "LIKELY NON-ENVIRONMENT FAILURE"

def log_result(message):
    """Emit the authoritative validation outcome for the current run."""
    LOGGER.log(RESULT_LEVEL, message)

def handle_exception(exc, retention, retained_figures):
    category = classify_exception(exc)
    log_result("RESULT:")
    log_result("NOT SUCCESSFULLY VALIDATED")
    LOGGER.error("")
    LOGGER.error("Failure Category:")
    LOGGER.error(category)
    LOGGER.error("")
    LOGGER.error("Exception:")
    LOGGER.error(f"{type(exc).__name__}: {exc}")
    LOGGER.error(traceback.format_exc())
    finalise_run(retention, retained_figures)
    return 1

def handle_success(retention, retained_figures):
    log_result("RESULT:")
    log_result("VALIDATED")
    finalise_run(retention, retained_figures)
    return 0

# Workflow execution

def execute_workflow(run_notebook_derived_workflow):
    LOGGER.info(TEST_NAME)
    LOGGER.info("")
    try:
        run_notebook_derived_workflow()
    except Exception as exc:
        return handle_exception(exc, retention, retained_figures)

    return handle_success(retention, retained_figures)

TEST_NAME = get_test_name()
LOGGER = configure_logging()

retention, retained_figures = initialise_retention_mode()
