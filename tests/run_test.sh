#!/usr/bin/env bash
#
# Generic environment-validation test wrapper.
#
# Loads the requested environment module, then invokes the selected
# notebook-derived validation test.
#
# Loads the community environment module, then invokes the Python test script,
# propagating its exit code unchanged. Contains no test logic and no
# Cylc-specific behaviour; runnable manually now, and later from Cylc.
#
# Usage:
#   ./run_test.sh --test <test_name> [--module <module>] [--retention] [--log-level <level>]
#
#   --test: specifies the test to run from data_science_cop tests/notebook_derived_tests (required). e.g. "climatezones_data_exploration".
#   --module: specifies the environment module to load (default: scitools/community/ml).
#   --retention: activates the Python script's artefact-retention mode (off by default).
#   --log-level: sets the log level for the Python script (default: INFO).

set -eu

MODULE="scitools/community/ml"
RETENTION=0
LOG_LEVEL="INFO"
TEST=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --test)
            TEST="$2"
            shift 2
            ;;
        --module)
            MODULE="$2"
            shift 2
            ;;
        --retention)
            RETENTION=1
            shift
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$TESTS_DIR"

if [[ -z "$TEST" ]]; then
    echo "No test specified. Use --test <test_name>" >&2
    exit 1
fi

TEST_SCRIPT="notebook_derived_tests/test_${TEST}.py"

if [[ ! -f "$TEST_SCRIPT" ]]; then
    echo "Test script not found: $TEST_SCRIPT" >&2
    exit 1
fi

module load "$MODULE" || exit 1

ENVIRONMENT_HASH="UNAVAILABLE"
ENVIRONMENT_INVENTORY=""

# Generate a reproducible inventory of packages present in the loaded
# environment by listing the conda-meta records. This inventory is
# subsequently hashed to provide a lightweight environment fingerprint
# for provenance and future run comparisons.
#
# Inventory generation occurs within a pipeline and pipefail is
# intentionally not enabled. Inventory-generation failures therefore
# leave ENVIRONMENT_INVENTORY empty (handled below) rather than
# terminating the wrapper.
ENVIRONMENT_INVENTORY=$(
    find "$SSS_ENV_DIR/conda-meta" \
        -maxdepth 1 \
        -type f \
        -name '*.json' \
        -printf '%f\n' |
    sort
)
if [[ -n "$ENVIRONMENT_INVENTORY" ]]
then
    ENVIRONMENT_HASH=$(
        printf "%s" "$ENVIRONMENT_INVENTORY" |
        sha256sum |
        awk '{print $1}'
    )
else
    echo "Warning: Environment inventory could not be generated." >&2
fi

echo "Module: $MODULE"
echo "Environment: ${SSS_ENV_NAME:-UNKNOWN}"
echo "Log Level: $LOG_LEVEL"
if [[ "$RETENTION" -eq 1 ]]; then
    echo "Retention: ON"
else
    echo "Retention: OFF"
fi
echo "Environment Hash: $ENVIRONMENT_HASH"
echo

PYTHON_OUTPUT_FILE="$(mktemp)"
ARGS=(
    --test "$TEST"
    --module "$MODULE"
    --log-level "$LOG_LEVEL"
)
if [[ "$RETENTION" -eq 1 ]]; then
    ARGS+=(--retention)
    rm -f latest_artefact_dir.txt
fi
set +e
python "$TEST_SCRIPT" "${ARGS[@]}" > "$PYTHON_OUTPUT_FILE" 2>&1
PYTHON_EXIT_CODE=$?
set -e

cat "$PYTHON_OUTPUT_FILE"
PYTHON_OUTPUT_HASH=$(
    sha256sum "$PYTHON_OUTPUT_FILE" |
    awk '{print $1}'
)
echo "Python Output Hash: $PYTHON_OUTPUT_HASH"

if [[ "$RETENTION" -eq 1 ]]; then
    ARTEFACT_DIR=""

    if [[ -f latest_artefact_dir.txt ]]; then
        ARTEFACT_DIR="$(<latest_artefact_dir.txt)"
    fi

    if [[ ! -d "$ARTEFACT_DIR" ]]; then
        echo "Warning: Retention requested but artefacts could not be retained; skipping retention steps." >&2
    else

        printf "%s\n" "$ENVIRONMENT_INVENTORY" \
            > "$ARTEFACT_DIR/environment_inventory.txt"

        printf "%s\n" "$ENVIRONMENT_HASH" \
            > "$ARTEFACT_DIR/environment_hash.txt"

        mv "$PYTHON_OUTPUT_FILE" \
            "$ARTEFACT_DIR/python_output.txt"

        printf "%s\n" "$PYTHON_OUTPUT_HASH" \
            > "$ARTEFACT_DIR/python_output_hash.txt"

        for artefact in \
            "$ARTEFACT_DIR"/*.png \
            "$ARTEFACT_DIR"/metadata.json
        do
            [[ -f "$artefact" ]] || continue

            ARTEFACT_HASH=$(
                sha256sum "$artefact" |
                awk '{print $1}'
            )

            printf "%s\n" "$ARTEFACT_HASH" \
                > "${artefact%.*}_hash.txt"
        done

        MASTER_HASH=$(
            find "$ARTEFACT_DIR" \
                -maxdepth 1 \
                -name '*_hash.txt' \
                ! -name 'environment_hash.txt' |
            sort |
            xargs cat |
            sha256sum |
            awk '{print $1}'
        )

        printf "%s\n" "$MASTER_HASH" \
            > "$ARTEFACT_DIR/master_hash.txt"

        echo "Master Hash: $MASTER_HASH"
    fi
    rm -f latest_artefact_dir.txt
fi

rm -f "$PYTHON_OUTPUT_FILE"
exit "$PYTHON_EXIT_CODE"
