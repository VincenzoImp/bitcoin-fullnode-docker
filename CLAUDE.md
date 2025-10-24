# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Bitcoin Full Node running in Docker with Tor privacy, featuring Bitcoin Core v27.0, Mempool dashboard, BTC RPC Explorer, and Python RPC client libraries.

## Common Commands

### Docker Operations

```bash
# Start all services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f bitcoin-core
docker-compose logs -f mempool-api
docker-compose logs -f tor

# Check status
docker-compose ps
```

### Bitcoin CLI

All bitcoin-cli commands must be executed inside the docker container with RPC credentials:

```bash
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword <command>

# Examples:
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getblockchaininfo
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getnetworkinfo
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getpeerinfo
```

### Python Development

```bash
# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Run basic client
python3 bitcoin_node_client.py

# Interactive CLI
python3 bitcoin_cli.py status
python3 bitcoin_cli.py info
python3 bitcoin_cli.py balance <address>
python3 bitcoin_cli.py batch-balance addresses.txt -o results.json

# View CLI configuration
python3 bitcoin_cli.py config

# Deactivate when done
deactivate
```

## Architecture

### Docker Service Stack

Six containers on shared `bitcoin-network` bridge:

1. **tor** → SOCKS proxy on 9050 for Bitcoin Core
2. **bitcoin-core** → Full node (depends on tor)
   - RPC: 8332
   - P2P: 8333
   - ZMQ: 28332-28334
   - Volume: `./bitcoin-data/` (~600GB)
3. **mempool-api** → Backend (depends on bitcoin-core)
4. **mempool-web** → Frontend on 8080 (depends on mempool-api)
5. **mempool-db** → MariaDB (volume: `./mempool-db/`)
6. **btc-rpc-explorer** → Block explorer on 3002 (depends on bitcoin-core)

### Tor Privacy Model

Bitcoin Core configured for **onion-only** P2P connections:
- Proxy: `proxy=tor:9050` (SOCKS5 through tor container)
- Network: `onlynet=onion` (no clearnet connections)
- Auto-creates v3 hidden service via Tor control socket
- All peers are `.onion` addresses
- Real IP never exposed to Bitcoin network

**Trade-off**: Sync is 2-3x slower than clearnet but provides complete privacy.

Verify Tor operation:
```bash
# Should show networks: [{"name":"onion",...}]
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getnetworkinfo

# All peers should have .onion addresses
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getpeerinfo | grep addr
```

### Configuration Files

**bitcoin.conf** - Bitcoin Core configuration (inside Docker container):
- Configures Bitcoin Core daemon itself
- RPC settings: `rpcuser`, `rpcpassword`, `rpcport`
- Network settings: Tor proxy, onion-only
- Node settings: `txindex`, `dbcache`, `prune`

**.env** - Python client configuration (on host machine):
- Used by Python scripts running on host to connect to Docker container
- Settings: `BITCOIN_RPC_HOST=localhost`, `BITCOIN_RPC_PORT=8332`, credentials
- Automatically loaded by `python-dotenv` library
- Copy from `.env.example`: `cp .env.example .env`

**Why both exist:**
- `bitcoin.conf` → configures Bitcoin Core (runs inside container)
- `.env` → configures Python clients (run on host, connect to localhost:8332)
- The exposed port 8332 in docker-compose.yml bridges them

### Credential Management

When changing RPC credentials, update in **three locations**:

1. `bitcoin.conf` (Bitcoin Core config):
   ```conf
   rpcuser=bitcoin
   rpcpassword=bitcoinpassword
   ```

2. `.env` (Python client config):
   ```bash
   BITCOIN_RPC_USER=bitcoin
   BITCOIN_RPC_PASSWORD=bitcoinpassword
   ```

3. `docker-compose.yml` - two services:
   - `mempool-api`: `CORE_RPC_USERNAME`, `CORE_RPC_PASSWORD`
   - `btc-rpc-explorer`: `BTCEXP_BITCOIND_USER`, `BTCEXP_BITCOIND_PASS`

After changing credentials: `docker-compose down && docker-compose up -d`

### Python Client Architecture

**bitcoin_node_client.py** - Core RPC wrapper:
- Class: `BitcoinNode`
- Wraps `python-bitcoinrpc` AuthServiceProxy
- Connects to Docker container via localhost:8332
- Auto-loads config from `.env` file using `python-dotenv`
- Configuration priority: 1) Constructor args, 2) .env variables, 3) Defaults
- Methods: `get_blockchain_info()`, `get_block()`, `get_transaction()`, `get_address_balance()`, etc.
- `get_address_balance()` uses `scantxoutset` RPC (slow, scans entire UTXO set)

**bitcoin_cli.py** - Interactive Click CLI:
- Auto-loads config from `.env` file (recommended) with `bitcoin.conf` as fallback
- Configuration priority (highest to lowest):
  1. Command-line flags (`--user`, `--password`, `--port`, `--host`, `--timeout`)
  2. Environment variables (`.env` file)
  3. Custom conf path (`--conf /path/to/bitcoin.conf`)
  4. Local `bitcoin.conf` in current directory
  5. Hardcoded defaults

Commands implemented: `status`, `info`, `network`, `mempool`, `peers`, `fee`, `block`, `latest`, `tx`, `balance`, `batch-balance`, `config`

**Setup:**
```bash
python3 -m venv venv                    # Create virtual environment
source venv/bin/activate                # Activate venv
pip install -r requirements.txt         # Install python-bitcoinrpc, click
python3 bitcoin_cli.py config           # Verify configuration
python3 bitcoin_cli.py status           # Test connection
```

### Bitcoin Core Configuration

Key settings in `bitcoin.conf`:

- `txindex=1` - Full transaction index (required for block explorer, speeds up address lookups)
- `dbcache=2048` - 2GB cache for faster initial sync
- `prune=0` - No pruning, keeps full ~600GB blockchain
- `maxmempool=300` - 300MB mempool limit
- ZMQ endpoints for Mempool dashboard integration

## Development Workflow

### Monitoring Sync Progress

Initial blockchain sync takes 1-7 days (longer with Tor). Check progress:

```bash
# Via Python CLI (easiest, with venv activated)
python3 bitcoin_cli.py status

# Via docker logs
docker-compose logs -f bitcoin-core

# Via bitcoin-cli (verificationprogress: 0.0 to 1.0)
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getblockchaininfo | grep verificationprogress
```

### Testing Configuration Changes

1. Stop containers: `docker-compose down`
2. Edit config files (`bitcoin.conf`, `docker-compose.yml`, `.env.example`)
3. If changing RPC credentials, update all 3 locations (see Credential Management)
4. Start: `docker-compose up -d`
5. Verify: `docker-compose logs -f` and `python3 bitcoin_cli.py config`

### Working with Python Clients

**First-time setup:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify configuration
python3 bitcoin_cli.py config
```

**Test connection to Docker container:**
```bash
# Quick status check
python3 bitcoin_cli.py status

# Check if node is syncing
python3 bitcoin_cli.py info
```

**Using as a library:**
```python
# With venv activated
from bitcoin_node_client import BitcoinNode

# Uses defaults: localhost:8332, bitcoin:bitcoinpassword
node = BitcoinNode()

# Or override with specific values
node = BitcoinNode(host="localhost", port=8332, user="bitcoin", password="bitcoinpassword", timeout=300)

# Make RPC calls
info = node.get_blockchain_info()
print(f"Blocks: {info['blocks']}, Sync: {info['verificationprogress']*100:.2f}%")
```

**Override config for testing:**
```bash
python3 bitcoin_cli.py --host localhost --port 8332 --user bitcoin --password test --timeout 600 info
```

## Troubleshooting

### Tor Connection Issues

If Bitcoin Core cannot find peers:

```bash
# Check Tor container is running
docker-compose ps tor
docker-compose logs tor

# Check Bitcoin logs for Tor messages
docker-compose logs bitcoin-core | grep -i tor

# Restart Tor and Bitcoin together
docker-compose restart tor bitcoin-core
```

To temporarily disable Tor and use clearnet, comment out in `bitcoin.conf`:
```conf
# proxy=tor:9050
# listenonion=1
# onlynet=onion
# debug=tor
```

**Warning**: Without Tor, your real IP will be visible on the Bitcoin network.

### Python RPC Timeouts

Increase timeout for slow operations (balance checks, blockchain queries during sync):

```bash
# Via command line (with venv activated)
python3 bitcoin_cli.py --timeout 600 balance <address>
```

Default timeout is 300 seconds (5 minutes). Balance checks using `scantxoutset` can take several minutes per address even with `txindex=1` enabled.

### Mempool Dashboard Not Showing Data

- Requires Bitcoin Core to be **fully synced** (verificationprogress = 1.0)
- Check ZMQ connection: `docker-compose logs mempool-api`
- Verify ZMQ ports in `bitcoin.conf` match `docker-compose.yml`

## Security Notes

- Default credentials (`bitcoin:bitcoinpassword`) are **insecure** - change for production
- Setup designed for **local/private use only**
- Do not expose ports 8332, 8080, or 3002 to public internet
- RPC uses HTTP (unencrypted) - consider reverse proxy with TLS for remote access
- Tor provides network-level privacy but does not encrypt RPC communication
