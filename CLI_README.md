# Bitcoin Node CLI

An interactive CLI for managing your Bitcoin node via RPC.

## Installation

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install python-bitcoinrpc click
```

## Configuration

### Option 1: Using bitcoin.conf (Recommended)

Place your `bitcoin.conf` file in the same directory as the CLI scripts. The CLI will automatically read the configuration from it.

Your `bitcoin.conf` should contain:

```ini
# RPC Settings
server=1
rpcuser=bitcoin
rpcpassword=bitcoinpassword
rpcport=8332
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0

# Transaction Index (required for balance checks)
txindex=1
```

The CLI will automatically load `rpcuser`, `rpcpassword`, and `rpcport` from this file.

### Option 2: Command Line Options

You can override bitcoin.conf values or use the CLI without bitcoin.conf:

```bash
python bitcoin_cli.py \
  --host localhost \
  --port 8332 \
  --user bitcoin \
  --password bitcoinpassword \
  --timeout 300 \
  status
```

### Option 3: Custom bitcoin.conf Path

Specify a custom path to bitcoin.conf:

```bash
python bitcoin_cli.py --conf /path/to/bitcoin.conf status
```

### View Current Configuration

```bash
python bitcoin_cli.py config
```

## Available Commands

### 1. Configuration

#### View current configuration
```bash
python bitcoin_cli.py config
```

### 2. Node Information

#### Complete node status
```bash
python bitcoin_cli.py status
```

#### Blockchain information
```bash
python bitcoin_cli.py info
```

#### Network information
```bash
python bitcoin_cli.py network
```

#### Mempool information
```bash
python bitcoin_cli.py mempool
```

#### Connected peers
```bash
python bitcoin_cli.py peers
```

### 3. Blocks and Transactions

#### Latest block
```bash
python bitcoin_cli.py latest
```

#### Block by height
```bash
python bitcoin_cli.py block 800000
```

#### Transaction details
```bash
python bitcoin_cli.py tx <txid>
```

### 4. Fee Estimation

```bash
# Fee for 6 blocks confirmation (default)
python bitcoin_cli.py fee

# Fee for 2 blocks confirmation
python bitcoin_cli.py fee --conf-target 2
```

### 5. Address Balances

#### Single address balance
```bash
python bitcoin_cli.py balance bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
```

#### Multiple addresses from file
```bash
# Create addresses.txt with one address per line
python bitcoin_cli.py batch-balance addresses.txt

# Save results to JSON file
python bitcoin_cli.py batch-balance addresses.txt -o results.json
```

## Usage Examples

### Example 1: Using bitcoin.conf configuration
```bash
# Just run commands - configuration loaded from bitcoin.conf
python bitcoin_cli.py status
python bitcoin_cli.py info
```

### Example 2: Using custom bitcoin.conf location
```bash
python bitcoin_cli.py --conf /path/to/bitcoin.conf status
```

### Example 3: Override bitcoin.conf with command line options
```bash
python bitcoin_cli.py \
  --host 192.168.1.100 \
  --port 8332 \
  --user myuser \
  --password mypassword \
  info
```

### Example 3: Check sync status
```bash
python bitcoin_cli.py status
```

### Example 4: Monitor latest block
```bash
python bitcoin_cli.py latest
```

### Example 5: Check address balance
```bash
python bitcoin_cli.py balance 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
```

### Example 6: Batch check addresses
```bash
# Create addresses.txt
echo "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh" > addresses.txt
echo "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" >> addresses.txt

# Run batch check
python bitcoin_cli.py batch-balance addresses.txt -o balances.json
```

### Example 7: Get specific block information
```bash
python bitcoin_cli.py block 700000
```

### Example 8: Fee estimation for urgent transactions
```bash
python bitcoin_cli.py fee --conf-target 1
```

## addresses.txt Format

The file should contain one Bitcoin address per line:

```
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy
```

## JSON Output Format

The `batch-balance` command with `-o` generates a JSON file with this structure:

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

## Help

To see all available commands:
```bash
python bitcoin_cli.py --help
```

To see help for a specific command:
```bash
python bitcoin_cli.py balance --help
```

## Notes

- The CLI automatically loads configuration from `bitcoin.conf` if found
- Command line options override `bitcoin.conf` values
- Your config already has `txindex=1` which speeds up balance checks
- The `balance` command uses `scantxoutset` which can be slow
- The `batch-balance` command shows a progress bar during execution
- All timeouts are configurable via `--timeout` option

## Troubleshooting

### Configuration Not Loading
If the CLI can't find your bitcoin.conf:
1. Ensure `bitcoin.conf` is in the same directory as the CLI scripts
2. Check with: `python bitcoin_cli.py config`
3. Or specify custom path: `--conf /path/to/bitcoin.conf`
4. Or use command line options: `--user bitcoin --password yourpass`

### Connection Timeout
If you're getting timeout errors:
1. Use command line: `--timeout 600`
2. Ensure your Bitcoin node is running and synced
3. Check RPC settings in bitcoin.conf

### Balance Check Slow
The `scantxoutset` command is slow by design:
1. Enable `txindex=1` in `bitcoin.conf` (already in your config ✓)
2. Restart your Bitcoin node after changing config
3. Be patient - scanning can take several minutes per address

### RPC Connection Refused
1. Ensure `server=1` is in bitcoin.conf
2. Check `rpcallowip` and `rpcbind` settings
3. Verify Bitcoin Core is running: `bitcoin-cli getblockchaininfo`
