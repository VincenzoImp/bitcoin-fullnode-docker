#!/usr/bin/env python3
"""
Python client for interacting with Bitcoin node via RPC
Requires: pip install python-bitcoinrpc

This client connects to Bitcoin Core running in a Docker container.
Defaults are configured for the Docker setup (localhost:8332).
"""

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json


class BitcoinNode:
    """
    Bitcoin node RPC client

    Connects to Bitcoin Core running in Docker container via exposed RPC port.
    By default uses localhost:8332 which maps to the Docker container's RPC port.
    """

    def __init__(self, host="localhost", port=8332, user="bitcoin", password="bitcoinpassword", timeout=120):
        """
        Initialize Bitcoin node connection

        Args:
            host: Bitcoin node hostname (default: 'localhost' for Docker)
            port: Bitcoin node RPC port (default: 8332)
            user: RPC username (default: 'bitcoin')
            password: RPC password (default: 'bitcoinpassword')
            timeout: Connection timeout in seconds (default: 120)

        For Docker setup:
            - host is always 'localhost' (Docker exposes port 8332 to host)
            - Credentials must match bitcoin.conf inside the container
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout

        self.rpc_url = f"http://{self.user}:{self.password}@{self.host}:{self.port}"
        self.connection = AuthServiceProxy(self.rpc_url, timeout=self.timeout)

    def get_blockchain_info(self):
        """Get blockchain information"""
        try:
            return self.connection.getblockchaininfo()
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_block_count(self):
        """Get current block count"""
        try:
            return self.connection.getblockcount()
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_block_hash(self, height):
        """Get block hash at specific height"""
        try:
            return self.connection.getblockhash(height)
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_block(self, block_hash, verbosity=2):
        """
        Get block information
        verbosity: 0=hex, 1=json, 2=json with transaction details
        """
        try:
            return self.connection.getblock(block_hash, verbosity)
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_transaction(self, txid):
        """Get transaction information"""
        try:
            return self.connection.getrawtransaction(txid, True)
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_mempool_info(self):
        """Get mempool information"""
        try:
            return self.connection.getmempoolinfo()
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_network_info(self):
        """Get network information"""
        try:
            return self.connection.getnetworkinfo()
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_peer_info(self):
        """Get connected peers information"""
        try:
            return self.connection.getpeerinfo()
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_best_block_hash(self):
        """Get hash of the best (tip) block"""
        try:
            return self.connection.getbestblockhash()
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def estimate_smart_fee(self, conf_target=6):
        """Estimate fee for confirmation in conf_target blocks"""
        try:
            return self.connection.estimatesmartfee(conf_target)
        except JSONRPCException as e:
            print(f"RPC Error: {e}")
            return None

    def get_address_balance(self, address):
        """
        Get balance for a specific address
        Note: Uses scantxoutset which works on standard nodes but can be slow
        For faster results, enable txindex in bitcoin.conf
        """
        try:
            # Using scantxoutset - works on standard nodes but can be slow
            result = self.connection.scantxoutset("start", [f"addr({address})"])
            if result:
                return {
                    "address": address,
                    "balance": result.get("total_amount", 0),
                    "utxos": result.get("unspents", []),
                    "utxo_count": len(result.get("unspents", []))
                }
            return None
        except JSONRPCException as e:
            print(f"RPC Error for address {address}: {e}")
            return None


def print_json(data):
    """Print formatted JSON"""
    print(json.dumps(data, indent=2, default=str))


def main():
    """Example usage"""
    print("=== Bitcoin Node Client ===\n")

    # Initialize with custom timeout (default is 120 seconds)
    # Increase timeout if your node is slow or under heavy load
    node = BitcoinNode(timeout=300)  # 5 minutes timeout

    print("📊 Blockchain Information:")
    blockchain_info = node.get_blockchain_info()
    if blockchain_info:
        print(f"  Chain: {blockchain_info.get('chain')}")
        print(f"  Blocks: {blockchain_info.get('blocks')}")
        print(f"  Headers: {blockchain_info.get('headers')}")
        print(f"  Sync progress: {blockchain_info.get('verificationprogress', 0) * 100:.2f}%")
        print(f"  Blockchain size: {blockchain_info.get('size_on_disk', 0) / 1024**3:.2f} GB")

    print("\n🌐 Network Information:")
    network_info = node.get_network_info()
    if network_info:
        print(f"  Version: {network_info.get('version')}")
        print(f"  Subversion: {network_info.get('subversion')}")
        print(f"  Connections: {network_info.get('connections')}")

    print("\n💾 Mempool Information:")
    mempool_info = node.get_mempool_info()
    if mempool_info:
        print(f"  Transactions: {mempool_info.get('size')}")
        print(f"  Size: {mempool_info.get('bytes') / 1024:.2f} KB")
        print(f"  Usage: {mempool_info.get('usage') / 1024:.2f} KB")

    print("\n👥 Connected Peers:")
    peers = node.get_peer_info()
    if peers:
        print(f"  Peer count: {len(peers)}")
        for i, peer in enumerate(peers[:5], 1):
            print(f"  {i}. {peer.get('addr')} - {peer.get('subver')}")

    print("\n💰 Fee Estimate (6 blocks):")
    fee_estimate = node.estimate_smart_fee(6)
    if fee_estimate:
        print_json(fee_estimate)

    print("\n🔗 Latest Block:")
    best_hash = node.get_best_block_hash()
    if best_hash:
        block = node.get_block(best_hash, verbosity=1)
        if block:
            print(f"  Hash: {block.get('hash')}")
            print(f"  Height: {block.get('height')}")
            print(f"  Timestamp: {block.get('time')}")
            print(f"  Transactions: {block.get('nTx')}")
            print(f"  Size: {block.get('size')} bytes")


if __name__ == "__main__":
    main()
