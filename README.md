# Bitcoin Full Node - Complete Setup

Complete setup for a private Bitcoin full node with:
- ✅ Bitcoin Core full node (v27.0)
- ✅ Dedicated Tor proxy for complete privacy and anonymity
- ✅ Mempool Dashboard with real-time statistics
- ✅ BTC RPC Explorer for blockchain exploration
- ✅ Python RPC client library and interactive CLI

## 📋 Requirements

- Docker and Docker Compose installed
- **At least 600 GB free disk space** (for full blockchain)
- **8 GB RAM** minimum (16 GB recommended)
- Stable internet connection
- Python 3.8+ (for Python CLI and automation scripts)

## 🚀 Quick Start

### 1. Start the containers

```bash
docker-compose up -d
```

### 2. Setup Python environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Check sync status

```bash
# Using Python CLI (easier)
python3 bitcoin_cli.py status

# Or using docker bitcoin-cli
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getblockchaininfo
```

### 4. Monitor logs

```bash
# All services
docker-compose logs -f

# Bitcoin Core only
docker-compose logs -f bitcoin-core

# Mempool only
docker-compose logs -f mempool-api
```

## 🌐 Access Services

Once containers are running, access:

| Service | URL | Description |
|---------|-----|-------------|
| **Mempool Dashboard** | http://localhost:8080 | Web interface for mempool and blockchain visualization |
| **BTC RPC Explorer** | http://localhost:3002 | Complete block explorer |
| **Bitcoin RPC** | http://localhost:8332 | RPC API for programmatic interactions |

## ⚙️ Configuration

### bitcoin.conf

The [bitcoin.conf](bitcoin.conf) file contains node configuration:
- RPC enabled with credentials: `bitcoin:bitcoinpassword`
- Transaction index enabled (`txindex=1`)
- ZMQ enabled for Mempool
- No pruning (full blockchain)
- **Tor enabled** for anonymous connections via onion network

**⚠️ IMPORTANT:** Change RPC credentials in production!

### 🧅 Tor Configuration (Best Practices)

The setup uses a **dedicated Tor proxy** for maximum privacy:

#### Architecture:
- **Separate Tor container** (`tor-proxy`) provides SOCKS proxy on port 9050
- **Bitcoin Core** connects to Tor via `proxy=tor:9050`
- **Automatic v3 hidden service** created by Bitcoin Core via Tor Control Socket
- **Onion-only connections** (`onlynet=onion`) for maximum anonymity

#### How it works:
1. Bitcoin Core uses Tor proxy for all P2P connections
2. Automatically creates a v3 hidden service for incoming connections
3. All peers are `.onion` addresses
4. Your real IP is never exposed

#### Verify Tor configuration:

```bash
# View network info (including onion address)
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getnetworkinfo

# Check connected peers (all should be .onion)
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getpeerinfo | grep addr

# Debug Tor logs
docker-compose logs bitcoin-core | grep -i tor
```

#### Disable Tor (use clearnet)

To use normal clearnet connections, edit [bitcoin.conf](bitcoin.conf):
```conf
# Comment out Tor settings
# proxy=tor:9050
# listenonion=1
# onlynet=onion
# debug=tor
```

Restart:
```bash
docker-compose restart bitcoin-core
```

**⚠️ Note**: Without Tor your IP will be visible on the Bitcoin network.

### Change Credentials

1. Edit `bitcoin.conf`:
```conf
rpcuser=your_username
rpcpassword=your_secure_password
```

2. Update same credentials in `docker-compose.yml`:
   - Service `mempool-api` → `CORE_RPC_USERNAME` and `CORE_RPC_PASSWORD`
   - Service `btc-rpc-explorer` → `BTCEXP_BITCOIND_USER` and `BTCEXP_BITCOIND_PASS`

3. Restart containers:
```bash
docker-compose down
docker-compose up -d
```

## 🐍 Python Integration

Python RPC client library and interactive CLI for interacting with the Bitcoin node running in Docker.

**Note**: All examples below assume you have activated the virtual environment (see Quick Start step 2).
```bash
source venv/bin/activate
```

### Interactive CLI

The `bitcoin_cli.py` provides a user-friendly command-line interface with multiple commands:

#### Configuration

```bash
# View current configuration
python3 bitcoin_cli.py config

# Use custom bitcoin.conf path
python3 bitcoin_cli.py --conf /path/to/bitcoin.conf status

# Override with command-line options
python3 bitcoin_cli.py --user myuser --password mypass --timeout 600 info
```

**Configuration priority**: Command-line options → bitcoin.conf → Hardcoded defaults

#### Node Information

```bash
# Complete node status (blockchain, network, mempool, latest block)
python3 bitcoin_cli.py status

# Blockchain information
python3 bitcoin_cli.py info

# Network information
python3 bitcoin_cli.py network

# Connected peers
python3 bitcoin_cli.py peers

# Mempool information
python3 bitcoin_cli.py mempool
```

#### Blocks and Transactions

```bash
# Latest block
python3 bitcoin_cli.py latest

# Block by height
python3 bitcoin_cli.py block 800000

# Transaction details
python3 bitcoin_cli.py tx <txid>
```

#### Fee Estimation

```bash
# Fee for 6 blocks confirmation (default)
python3 bitcoin_cli.py fee

# Fee for 2 blocks confirmation
python3 bitcoin_cli.py fee --conf-target 2
```

#### Address Balances

```bash
# Single address balance (WARNING: slow operation, use high timeout)
python3 bitcoin_cli.py --timeout 600 balance bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

# Batch check multiple addresses from file
python3 bitcoin_cli.py --timeout 900 batch-balance addresses.txt

# Save results to JSON
python3 bitcoin_cli.py --timeout 900 batch-balance addresses.txt -o results.json
```

**Note**: Balance checks use `scantxoutset` which scans the entire UTXO set and can take 5-10 minutes per address.

**addresses.txt format** (one address per line):
```
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy
```

**JSON output format** (when using `-o` with batch-balance):
```json
{
  "total_balance": 1.23456789,
  "addresses_checked": 3,
  "successful": 3,
  "addresses": [
    {
      "address": "bc1q...",
      "balance": 0.5,
      "utxos": [...],
      "utxo_count": 2
    }
  ]
}
```

#### Help

```bash
# List all commands
python3 bitcoin_cli.py --help

# Help for specific command
python3 bitcoin_cli.py balance --help
```

### Python Library Usage

Use `bitcoin_node_client.py` as a library in your own scripts:

```python
from bitcoin_node_client import BitcoinNode

# Connect to node (defaults: localhost:8332, bitcoin:bitcoinpassword)
node = BitcoinNode()

# Or specify custom credentials
node = BitcoinNode(
    host="localhost",
    port=8332,
    user="bitcoin",
    password="bitcoinpassword",
    timeout=300
)

# Get blockchain info
info = node.get_blockchain_info()
print(f"Blocks: {info['blocks']}")
print(f"Sync: {info['verificationprogress'] * 100:.2f}%")

# Get latest block
best_hash = node.get_best_block_hash()
block = node.get_block(best_hash)
print(f"Latest block height: {block['height']}")

# Get mempool info
mempool = node.get_mempool_info()
print(f"Mempool transactions: {mempool['size']}")

# Get network info (check Tor status)
network = node.get_network_info()
print(f"Connections: {network['connections']}")
```

### Run Demo Script

```bash
# Run the example (with venv activated)
python3 bitcoin_node_client.py
```

## 📊 Initial Sync

**Bitcoin blockchain synchronization can take several days.**

Estimated times:
- **1-3 days** with fast SSD and good connection
- **5-7 days** with average hardware
- **2+ weeks** with slow hardware

### Monitor progress

```bash
# Via Python CLI (easiest - with venv activated)
python3 bitcoin_cli.py status
python3 bitcoin_cli.py info

# Via docker bitcoin-cli
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getblockchaininfo | grep verificationprogress

# Via Python one-liner (with venv activated)
python3 -c "from bitcoin_node_client import BitcoinNode; node = BitcoinNode(); info = node.get_blockchain_info(); print(f'Progress: {info[\"verificationprogress\"] * 100:.2f}%')"
```

## 🔧 Useful Commands

### Container management

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps

# Remove everything (WARNING: deletes data!)
docker-compose down -v
```

### Bitcoin CLI

```bash
# Alias for convenience
alias bitcoin-cli="docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword"

# Command examples
bitcoin-cli getblockchaininfo
bitcoin-cli getnetworkinfo
bitcoin-cli getpeerinfo
bitcoin-cli getmempoolinfo
bitcoin-cli getblockcount
bitcoin-cli help
```

## 💾 Data Management

Data is stored in the following directories:

- `./bitcoin-data/` - Bitcoin blockchain (~600 GB) and Tor hidden service keys
- `./mempool-db/` - Mempool database

### Backup

```bash
# Stop containers
docker-compose down

# Backup blockchain
tar -czf bitcoin-backup.tar.gz bitcoin-data/

# Restart
docker-compose up -d
```

### Disk space cleanup

If you need space, enable pruning in `bitcoin.conf`:

```conf
# Keep only last ~5 GB
prune=5000
```

**⚠️ Note:** With pruning enabled you won't have the full blockchain.

## 🔒 Security

**This setup is for LOCAL/PRIVATE use:**

- ✅ Do not expose ports publicly
- ✅ Use firewall to limit access to local network
- ✅ Change default RPC credentials
- ✅ Consider using HTTPS with reverse proxy for web access

## 📝 Notes

- Bitcoin node connects automatically to mainnet **via Tor**
- First sync requires significant time and bandwidth (slower with Tor)
- During sync the system will use many resources (CPU, RAM, disk I/O)
- Mempool Dashboard will show data only after node is fully synced
- BTC RPC Explorer works during sync but with partial data
- **Tor sync can be 2-3x slower** than clearnet but provides complete privacy

## 🐛 Troubleshooting

### Node not syncing

```bash
# Check logs
docker-compose logs bitcoin-core

# Verify connected peers (should be .onion addresses)
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getpeerinfo

# Verify Tor is active
docker exec bitcoin-node bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoinpassword getnetworkinfo
```

### Tor not finding peers

If node cannot connect to Tor peers:

```bash
# Verify Tor proxy is active
docker-compose ps tor
docker-compose logs tor

# Check Bitcoin logs for Tor messages
docker-compose logs bitcoin-core | grep -i tor

# Restart both services
docker-compose restart tor bitcoin-core
```

If persists:
1. Check that `proxy=tor:9050` is configured correctly
2. Temporarily remove `onlynet=onion` to use clearnet too
3. Wait a few minutes - Tor can be slow to find initial peers

### Mempool not showing data

- Wait for Bitcoin Core to be fully synced
- Verify ZMQ is configured correctly
- Check mempool-api logs: `docker-compose logs mempool-api`

### Python connection error

```bash
# Ensure venv is activated
source venv/bin/activate

# Check configuration
python3 bitcoin_cli.py config

# Test basic connection
python3 bitcoin_cli.py info

# If it fails, verify Docker container is running
docker ps | grep bitcoin-node

# Check RPC port is exposed
docker port bitcoin-node 8332

# Test direct RPC connection
curl -u bitcoin:bitcoinpassword --data-binary '{"jsonrpc":"1.0","id":"test","method":"getblockchaininfo","params":[]}' -H 'content-type:text/plain;' http://localhost:8332/
```

### Python timeout errors

If balance checks or other slow operations timeout:

```bash
# Increase timeout (default is 300 seconds, with venv activated)
python3 bitcoin_cli.py --timeout 600 balance <address>

# For batch operations
python3 bitcoin_cli.py --timeout 900 batch-balance addresses.txt
```

**Note**: `scantxoutset` operations can take 5-10 minutes even with a fast SSD.

## 📚 Resources

- [Bitcoin Core Documentation](https://bitcoin.org/en/bitcoin-core/)
- [Bitcoin over Tor](https://github.com/bitcoin/bitcoin/blob/master/doc/tor.md)
- [Mempool GitHub](https://github.com/mempool/mempool)
- [BTC RPC Explorer](https://github.com/janoside/btc-rpc-explorer)
- [Bitcoin RPC API](https://developer.bitcoin.org/reference/rpc/)
- [Tor Project](https://www.torproject.org/)

## 📄 License

This setup is provided as-is for educational and development purposes.
