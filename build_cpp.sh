# from repo root, using the root .venv (recommended)
source .venv/bin/activate

uv pip uninstall predme || true
uv pip install -e .  # will rebuild and install the compiled module

# verify in the active env
uv run --active python -c "import orderbook_ext, sys; print('ok:', orderbook_ext.__file__); print(sys.executable)"