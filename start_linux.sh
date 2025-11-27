SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")

# Change the current working directory to the script's directory
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "Current directory is now: $(pwd)"
python mpvs.py

