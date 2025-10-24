#!/usr/bin/env python3
"""
Interactive CLI for Bitcoin Node Client
Requires: pip install python-bitcoinrpc click

This CLI connects to Bitcoin Core running in Docker.
Configuration is loaded from bitcoin.conf in the current directory.
"""

import click
import json
from pathlib import Path
from bitcoin_node_client import BitcoinNode, print_json


def parse_bitcoin_conf(conf_path=None):
    """
    Parse bitcoin.conf file and return configuration dict

    Reads RPC credentials from bitcoin.conf to connect to the Docker container.
    """
    if conf_path is None:
        # Look for bitcoin.conf in current directory
        conf_path = Path('./bitcoin.conf')

    if not Path(conf_path).exists():
        return {}

    config = {}
    with open(conf_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

    return config


# Load configuration from bitcoin.conf
bitcoin_conf = parse_bitcoin_conf()

# Configuration: 1. bitcoin.conf, 2. Defaults for Docker setup
DEFAULT_HOST = 'localhost'  # Always localhost when connecting to Docker
DEFAULT_PORT = int(bitcoin_conf.get('rpcport', '8332'))
DEFAULT_USER = bitcoin_conf.get('rpcuser', 'bitcoin')
DEFAULT_PASSWORD = bitcoin_conf.get('rpcpassword', 'bitcoinpassword')
DEFAULT_TIMEOUT = 300  # 5 minutes default timeout


@click.group()
@click.option('--host', default=DEFAULT_HOST, help='Bitcoin node hostname (default: localhost for Docker)')
@click.option('--port', default=DEFAULT_PORT, help='Bitcoin node RPC port')
@click.option('--user', default=DEFAULT_USER, help='RPC username')
@click.option('--password', default=DEFAULT_PASSWORD, help='RPC password')
@click.option('--timeout', default=DEFAULT_TIMEOUT, help='Connection timeout in seconds')
@click.option('--conf', type=click.Path(exists=True), help='Path to bitcoin.conf file')
@click.pass_context
def cli(ctx, host, port, user, password, timeout, conf):
    """Bitcoin Node CLI - Interact with Bitcoin Core running in Docker

    Configuration is automatically loaded from bitcoin.conf in the current directory.
    Command line options override bitcoin.conf values.

    Quick start:
      Run: python bitcoin_cli.py status
    """
    # If custom conf path provided, reload configuration
    if conf:
        custom_conf = parse_bitcoin_conf(conf)
        if 'rpcuser' in custom_conf:
            user = custom_conf['rpcuser']
        if 'rpcpassword' in custom_conf:
            password = custom_conf['rpcpassword']
        if 'rpcport' in custom_conf:
            port = int(custom_conf['rpcport'])

    ctx.ensure_object(dict)
    ctx.obj['node'] = BitcoinNode(host=host, port=port, user=user, password=password, timeout=timeout)
    ctx.obj['conf_path'] = conf
    ctx.obj['connection_info'] = {
        'host': host,
        'port': port,
        'user': user,
        'timeout': timeout
    }


@cli.command()
@click.pass_context
def info(ctx):
    """Get blockchain information"""
    node = ctx.obj['node']
    blockchain_info = node.get_blockchain_info()
    
    if blockchain_info:
        click.echo(click.style("\n📊 Blockchain Information:", fg='cyan', bold=True))
        click.echo(f"  Chain: {blockchain_info.get('chain')}")
        click.echo(f"  Blocks: {blockchain_info.get('blocks'):,}")
        click.echo(f"  Headers: {blockchain_info.get('headers'):,}")
        click.echo(f"  Sync progress: {blockchain_info.get('verificationprogress', 0) * 100:.2f}%")
        click.echo(f"  Blockchain size: {blockchain_info.get('size_on_disk', 0) / 1024**3:.2f} GB")
        click.echo(f"  Best block hash: {blockchain_info.get('bestblockhash')}")
    else:
        click.echo(click.style("❌ Failed to get blockchain info", fg='red'))


@cli.command()
@click.pass_context
def network(ctx):
    """Get network information"""
    node = ctx.obj['node']
    network_info = node.get_network_info()
    
    if network_info:
        click.echo(click.style("\n🌐 Network Information:", fg='cyan', bold=True))
        click.echo(f"  Version: {network_info.get('version')}")
        click.echo(f"  Subversion: {network_info.get('subversion')}")
        click.echo(f"  Protocol version: {network_info.get('protocolversion')}")
        click.echo(f"  Connections: {network_info.get('connections')}")
        click.echo(f"  Network active: {network_info.get('networkactive')}")
    else:
        click.echo(click.style("❌ Failed to get network info", fg='red'))


@cli.command()
@click.pass_context
def mempool(ctx):
    """Get mempool information"""
    node = ctx.obj['node']
    mempool_info = node.get_mempool_info()
    
    if mempool_info:
        click.echo(click.style("\n💾 Mempool Information:", fg='cyan', bold=True))
        click.echo(f"  Transactions: {mempool_info.get('size'):,}")
        click.echo(f"  Size: {mempool_info.get('bytes') / 1024:.2f} KB")
        click.echo(f"  Usage: {mempool_info.get('usage') / 1024:.2f} KB")
        click.echo(f"  Max mempool: {mempool_info.get('maxmempool', 0) / 1024**2:.2f} MB")
    else:
        click.echo(click.style("❌ Failed to get mempool info", fg='red'))


@cli.command()
@click.pass_context
def peers(ctx):
    """Get connected peers information"""
    node = ctx.obj['node']
    peers_info = node.get_peer_info()
    
    if peers_info:
        click.echo(click.style(f"\n👥 Connected Peers: {len(peers_info)}", fg='cyan', bold=True))
        for i, peer in enumerate(peers_info, 1):
            click.echo(f"\n  Peer {i}:")
            click.echo(f"    Address: {peer.get('addr')}")
            click.echo(f"    Version: {peer.get('subver')}")
            click.echo(f"    Connection: {peer.get('connection_type')}")
            click.echo(f"    Connected since: {peer.get('conntime')}")
    else:
        click.echo(click.style("❌ Failed to get peers info", fg='red'))


@cli.command()
@click.option('--conf-target', default=6, help='Target number of blocks for fee estimation')
@click.pass_context
def fee(ctx, conf_target):
    """Estimate transaction fee"""
    node = ctx.obj['node']
    fee_estimate = node.estimate_smart_fee(conf_target)
    
    if fee_estimate:
        click.echo(click.style(f"\n💰 Fee Estimate ({conf_target} blocks):", fg='cyan', bold=True))
        if 'feerate' in fee_estimate:
            click.echo(f"  Fee rate: {fee_estimate.get('feerate')} BTC/kB")
            click.echo(f"  Fee rate: {fee_estimate.get('feerate') * 100000:.2f} sat/vB")
        if 'errors' in fee_estimate:
            click.echo(click.style(f"  Errors: {fee_estimate.get('errors')}", fg='yellow'))
    else:
        click.echo(click.style("❌ Failed to estimate fee", fg='red'))


@cli.command()
@click.argument('height', type=int)
@click.pass_context
def block(ctx, height):
    """Get block information by height"""
    node = ctx.obj['node']
    
    click.echo(f"Getting block at height {height:,}...")
    block_hash = node.get_block_hash(height)
    
    if not block_hash:
        click.echo(click.style("❌ Failed to get block hash", fg='red'))
        return
    
    block_info = node.get_block(block_hash, verbosity=1)
    
    if block_info:
        click.echo(click.style(f"\n🔗 Block #{height:,}:", fg='cyan', bold=True))
        click.echo(f"  Hash: {block_info.get('hash')}")
        click.echo(f"  Height: {block_info.get('height'):,}")
        click.echo(f"  Timestamp: {block_info.get('time')}")
        click.echo(f"  Transactions: {block_info.get('nTx'):,}")
        click.echo(f"  Size: {block_info.get('size'):,} bytes")
        click.echo(f"  Weight: {block_info.get('weight'):,}")
        click.echo(f"  Difficulty: {block_info.get('difficulty'):,.2f}")
    else:
        click.echo(click.style("❌ Failed to get block info", fg='red'))


@cli.command()
@click.pass_context
def latest(ctx):
    """Get latest block information"""
    node = ctx.obj['node']
    
    best_hash = node.get_best_block_hash()
    if not best_hash:
        click.echo(click.style("❌ Failed to get best block hash", fg='red'))
        return
    
    block_info = node.get_block(best_hash, verbosity=1)
    
    if block_info:
        click.echo(click.style("\n🔗 Latest Block:", fg='cyan', bold=True))
        click.echo(f"  Hash: {block_info.get('hash')}")
        click.echo(f"  Height: {block_info.get('height'):,}")
        click.echo(f"  Timestamp: {block_info.get('time')}")
        click.echo(f"  Transactions: {block_info.get('nTx'):,}")
        click.echo(f"  Size: {block_info.get('size'):,} bytes")
        click.echo(f"  Weight: {block_info.get('weight'):,}")
    else:
        click.echo(click.style("❌ Failed to get block info", fg='red'))


@cli.command()
@click.argument('txid')
@click.pass_context
def tx(ctx, txid):
    """Get transaction information by TXID"""
    node = ctx.obj['node']
    
    click.echo(f"Getting transaction {txid}...")
    tx_info = node.get_transaction(txid)
    
    if tx_info:
        click.echo(click.style("\n📝 Transaction Information:", fg='cyan', bold=True))
        click.echo(f"  TXID: {tx_info.get('txid')}")
        click.echo(f"  Hash: {tx_info.get('hash')}")
        click.echo(f"  Size: {tx_info.get('size')} bytes")
        click.echo(f"  Virtual size: {tx_info.get('vsize')} vB")
        click.echo(f"  Weight: {tx_info.get('weight')}")
        click.echo(f"  Confirmations: {tx_info.get('confirmations', 0):,}")
        
        if 'vin' in tx_info:
            click.echo(f"\n  Inputs ({len(tx_info['vin'])}):")
            for i, vin in enumerate(tx_info['vin'][:5], 1):
                if 'txid' in vin:
                    click.echo(f"    {i}. {vin.get('txid')}:{vin.get('vout')}")
        
        if 'vout' in tx_info:
            click.echo(f"\n  Outputs ({len(tx_info['vout'])}):")
            for vout in tx_info['vout'][:5]:
                value = vout.get('value', 0)
                addresses = vout.get('scriptPubKey', {}).get('addresses', [])
                click.echo(f"    {value} BTC -> {addresses}")
    else:
        click.echo(click.style("❌ Failed to get transaction info", fg='red'))


@cli.command()
@click.argument('address')
@click.pass_context
def balance(ctx, address):
    """Get balance for a Bitcoin address"""
    node = ctx.obj['node']
    
    click.echo(f"Checking balance for {address}...")
    click.echo(click.style("⚠️  This may take a while...", fg='yellow'))
    
    balance_info = node.get_address_balance(address)
    
    if balance_info:
        click.echo(click.style(f"\n💰 Address Balance:", fg='cyan', bold=True))
        click.echo(f"  Address: {balance_info['address']}")
        click.echo(f"  Balance: {balance_info['balance']} BTC")
        click.echo(f"  Balance: {balance_info['balance'] * 100000000:,.0f} satoshis")
        click.echo(f"  UTXOs: {balance_info['utxo_count']}")
        
        if balance_info['utxo_count'] > 0 and click.confirm('\nShow UTXO details?'):
            click.echo(click.style("\n  UTXO Details:", fg='cyan'))
            for i, utxo in enumerate(balance_info['utxos'], 1):
                click.echo(f"\n  UTXO {i}:")
                click.echo(f"    Amount: {utxo.get('amount')} BTC")
                click.echo(f"    TxID: {utxo.get('txid')}")
                click.echo(f"    Vout: {utxo.get('vout')}")
                click.echo(f"    Height: {utxo.get('height'):,}")
    else:
        click.echo(click.style("❌ Failed to get balance", fg='red'))


@cli.command()
@click.argument('addresses_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file for results (JSON format)')
@click.pass_context
def batch_balance(ctx, addresses_file, output):
    """Check balances for multiple addresses from a file"""
    node = ctx.obj['node']
    
    # Read addresses from file
    with open(addresses_file, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]
    
    click.echo(f"Found {len(addresses)} addresses to check")
    click.echo(click.style("⚠️  This may take a long time...", fg='yellow'))
    
    if not click.confirm('Continue?'):
        return
    
    results = []
    total_balance = 0
    
    with click.progressbar(addresses, label='Checking balances') as addr_list:
        for address in addr_list:
            balance_info = node.get_address_balance(address)
            if balance_info:
                results.append(balance_info)
                total_balance += balance_info['balance']
    
    # Display summary
    click.echo(click.style("\n📊 Summary:", fg='cyan', bold=True))
    click.echo(f"  Addresses checked: {len(addresses)}")
    click.echo(f"  Successful: {len(results)}")
    click.echo(f"  Failed: {len(addresses) - len(results)}")
    click.echo(f"  Total balance: {total_balance} BTC")
    click.echo(f"  Total balance: {total_balance * 100000000:,.0f} satoshis")
    
    # Save to file if requested
    if output:
        output_data = {
            "total_balance": total_balance,
            "addresses_checked": len(addresses),
            "successful": len(results),
            "addresses": results
        }
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2)
        click.echo(click.style(f"\n✓ Results saved to {output}", fg='green'))


@cli.command()
@click.pass_context
def status(ctx):
    """Show complete node status"""
    node = ctx.obj['node']
    
    click.echo(click.style("\n" + "="*60, fg='cyan'))
    click.echo(click.style("Bitcoin Node Status", fg='cyan', bold=True))
    click.echo(click.style("="*60 + "\n", fg='cyan'))
    
    # Blockchain info
    blockchain_info = node.get_blockchain_info()
    if blockchain_info:
        click.echo(click.style("📊 Blockchain:", fg='yellow', bold=True))
        click.echo(f"  Chain: {blockchain_info.get('chain')}")
        click.echo(f"  Blocks: {blockchain_info.get('blocks'):,}")
        click.echo(f"  Sync: {blockchain_info.get('verificationprogress', 0) * 100:.2f}%")
        click.echo(f"  Size: {blockchain_info.get('size_on_disk', 0) / 1024**3:.2f} GB\n")
    
    # Network info
    network_info = node.get_network_info()
    if network_info:
        click.echo(click.style("🌐 Network:", fg='yellow', bold=True))
        click.echo(f"  Version: {network_info.get('subversion')}")
        click.echo(f"  Connections: {network_info.get('connections')}\n")
    
    # Mempool info
    mempool_info = node.get_mempool_info()
    if mempool_info:
        click.echo(click.style("💾 Mempool:", fg='yellow', bold=True))
        click.echo(f"  Transactions: {mempool_info.get('size'):,}")
        click.echo(f"  Size: {mempool_info.get('bytes') / 1024:.2f} KB\n")
    
    # Latest block
    best_hash = node.get_best_block_hash()
    if best_hash:
        block_info = node.get_block(best_hash, verbosity=1)
        if block_info:
            click.echo(click.style("🔗 Latest Block:", fg='yellow', bold=True))
            click.echo(f"  Height: {block_info.get('height'):,}")
            click.echo(f"  Hash: {block_info.get('hash')}")
            click.echo(f"  Transactions: {block_info.get('nTx'):,}")


@cli.command()
@click.option('--conf-path', type=click.Path(exists=True), help='Path to bitcoin.conf')
def config(conf_path):
    """Show current configuration and connection info"""
    if conf_path:
        conf = parse_bitcoin_conf(conf_path)
    else:
        conf = bitcoin_conf

    click.echo(click.style("\n⚙️  Bitcoin RPC Configuration:", fg='cyan', bold=True))
    click.echo(click.style("\nConnection Settings:", fg='yellow'))
    click.echo(f"  Host: {DEFAULT_HOST} (connecting to Docker container)")
    click.echo(f"  Port: {DEFAULT_PORT}")
    click.echo(f"  User: {DEFAULT_USER}")
    click.echo(f"  Password: {'*' * len(DEFAULT_PASSWORD)}")
    click.echo(f"  Timeout: {DEFAULT_TIMEOUT}s")

    # Show configuration source
    click.echo(click.style("\nConfiguration Source:", fg='yellow'))

    # Check bitcoin.conf
    conf_file = Path('./bitcoin.conf')
    conf_exists = conf_file.exists()
    conf_status = "✓ Found" if conf_exists else "✗ Not found"
    click.echo(f"  bitcoin.conf: {conf_status}")
    if conf_exists:
        click.echo(f"    Location: {conf_file.absolute()}")

    click.echo(click.style("\nConfiguration Priority:", fg='yellow'))
    click.echo("  1. Command-line arguments (--host, --user, etc.)")
    click.echo("  2. bitcoin.conf file")
    click.echo("  3. Hardcoded defaults (localhost:8332, bitcoin:bitcoinpassword)")

    if conf:
        click.echo(click.style("\nSettings loaded from bitcoin.conf:", fg='yellow'))
        for key in ['rpcuser', 'rpcpassword', 'rpcport', 'rpcallowip', 'txindex', 'mainnet']:
            if key in conf:
                value = conf[key] if key != 'rpcpassword' else '*' * len(conf[key])
                click.echo(f"  {key} = {value}")

    click.echo(click.style("\n💡 Note:", fg='green'))
    click.echo("  Python clients connect to localhost:8332 to reach Bitcoin Core in Docker.")
    click.echo("  RPC credentials must match those in bitcoin.conf inside the container.")


if __name__ == '__main__':
    cli(obj={})
