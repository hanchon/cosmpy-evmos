from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.wallet import Wallet as WalletInterface
from cosmpy.crypto.address import Address
from cosmpy.crypto.interface import Signer
from cosmpy.crypto.keypairs import PublicKey
from evmoswallet import Wallet
from evmoswallet.eth.ethereum import sha3_256

from src.ethpubkey import PubKey

evmos = NetworkConfig(
    chain_id='evmos_9001-2',
    url='grpc+https://grpc.bd.evmos.org:9090',
    fee_minimum_gas_price=20000000000,
    fee_denomination='aevmos',
    staking_denomination='aevmos',
    faucet_url='',
)

seed = 'report spend crisp crisp world shock morning hour ' \
       'spoon problem one hole program piano donkey width ' \
       'today view canoe clap brick bundle rose book'


class CosmpyWallet(WalletInterface):

    def __init__(self, seed: str):
        self.wallet = Wallet(seed=seed)
        self.evmos = True

    def address(self) -> Address:
        return Address(self.wallet.evmos_address, 'evmos')

    def public_key(self) -> PublicKey:
        return PublicKey(self.wallet.public_key)

    def signer(self) -> Signer:

        class MySigner(Signer):

            def __init__(self, wallet: Wallet):
                self.wallet = wallet

            def sign(self,
                     message: bytes,
                     deterministic: bool = False,
                     canonicalise: bool = True) -> bytes:
                return self.wallet.sign(sha3_256(message).digest())

            def sign_digest(self,
                            digest: bytes,
                            deterministic=False,
                            canonicalise: bool = True) -> bytes:
                return self.wallet.sign(digest)

        return MySigner(self.wallet)

    def create_proto_pub_key(self):
        pub_key = PubKey()
        pub_key.key = self.wallet.public_key
        return pub_key


if __name__ == '__main__':
    ledger_client = LedgerClient(evmos)
    wallet = CosmpyWallet(seed)
    balances = ledger_client.query_bank_all_balances(wallet.address())
    print(balances)
    tx = ledger_client.send_tokens(wallet.address(),
                                   10,
                                   'aevmows',
                                   wallet,
                                   gas_limit=150000)
    print(tx)

    raise SystemExit(0)
