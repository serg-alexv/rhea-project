# rhea-cli

Unified CLI for the Rhea agent coordination OS. Controls three planes from one command:

1. **GitHub org** -- repos, licenses, profiles, topics
2. **Fly.io** -- deploy, secrets, logs, status
3. **Tribunal API** -- agents, history, radio, office, tribunal

## Install

### Homebrew (recommended)

```bash
brew tap timelabs/tap
brew install rhea
```

### pip

```bash
pip install rhea-cli
```

### From source

```bash
git clone https://github.com/timelabs/rhea-cli.git
cd rhea-cli
pip install -e .
```

## Usage

```bash
# GitHub org management
rhea org status
rhea org license --fix
rhea org profile
rhea org create my-repo --public --desc "My repo"

# Fly.io operations
rhea fly status
rhea fly deploy
rhea fly logs -n 100
rhea fly secrets

# Tribunal API
rhea api health
rhea api tribunal "The Earth is round"
rhea api tribunal "Water boils at 100C" --ice
rhea api agents
rhea api radio
rhea api history
rhea api governor

# Live dashboard
rhea monitor --interval 3

# Target cloud instead of localhost
rhea --cloud api health

# Repo checks
rhea check

# Emergency controls
rhea emergency stop
rhea emergency pause
rhea emergency resume
```

## Configuration

- `RHEA_API` env var: override local API base URL (default: `http://localhost:8400`)
- `--cloud` flag: target `rhea-tribunal.fly.dev` instead of localhost

## License

MIT -- Copyright (c) 2026 timelabs npo
