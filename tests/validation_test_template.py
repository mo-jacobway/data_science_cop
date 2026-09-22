"""
Notebook-Derived Validation Test Template

This file provides a template for creating new notebook-derived
environment-validation tests within the environment-validation framework.

Before use, this template should be copied and renamed according to the
standard naming convention:

    test_<origin_notebook_name>.py

For example:

    test_climatezones_data_exploration.py

A new test should be created by replacing the workflow-specific
placeholders with content derived from the notebook being represented.

Authors of new tests remain responsible for ensuring that workflow
implementations, references, documentation and data statements are complete,
accurate and up to date.

Template markers
----------------

The template uses two placeholder conventions:

    ##...##

        Content that should be replaced with workflow-specific information,
        code or documentation.

    ###...###

        Guidance or instructions for the author of the new test. These
        sections should be removed once the test implementation is complete.
"""




"""##origin notebook name (e.g. ClimateZones Data Exploration)## - Environment Validation Test

This script's workflow content originated from the ##origin notebook name (e.g. ClimateZones Data Exploration)##
tutorial notebook and was reduced to provide a representative environment-
validation workflow.

The workflow content below remains substantially derived from that reduced
workflow and is executed within the environment-validation framework.

Test framework functionality including validation reporting, exception handling,
provenance capture and artefact retention is provided separately by
test_framework_utils.py.

* Author: ##origin notebook author(s)##; Environment-validation test wrapper and workflow reduction: ##author of this test script##;
* Affiliation: UK Met Office
* History: 1.0
* Last update: ##last update date (YYYY-MM-DD)##
* (c) British Crown Copyright 2017-2026, Met Office. Please see LICENSE.md for license details.

Running this test
-----------------
This script forms part of an environment-validation framework and contains
the workflow-specific implementation of the ##origin notebook name (e.g. ClimateZones Data Exploration)##
validation test.

It is intended to be executed via:

    run_test.sh --test ##test name (e.g. climatezones_data_exploration)## [--module <module>] [--retention] [--log-level <level>]

which loads the environment under test and invokes this workflow through
the framework.

Data statement
--------------
This script is an environment-validation implementation based on the original
##origin notebook name (e.g. ClimateZones Data Exploration)## tutorial workflow.

###between the asterisks holds true for all climatezones derived tests, use the statement and reference of other workflows where different data is used and should be referenced.###
**The underlying data referenced by the workflow is the Koppen-Geiger Climate
Classification dataset created by GloH2O.

References
----------
- Climate Zones Dataset:
  https://www.gloh2o.org/koppen/#:~:text=The%20K%C3%B6ppen%2DGeiger%20climate%20classification%20maps%20are%20high%2Dresolution,Climate%20Sensitivity%20(ECS)%2C%20and%20historical%20warming%20trend
**
  """

import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
import test_framework_utils as test_framework

# ##notebook derived imports##


# ---------------------------------------------------------------------
# Notebook workflow helpers
# ---------------------------------------------------------------------

# ##any and all helper functions to support and improve code readability of the notebook derived workflow in the below function##

# ---------------------------------------------------------------------
# Notebook derived workflow
# ---------------------------------------------------------------------

def run_notebook_derived_workflow():
    pass # ###replace with the full notebook derived workflow###
if __name__ == "__main__":
    sys.exit(test_framework.execute_workflow(run_notebook_derived_workflow))
