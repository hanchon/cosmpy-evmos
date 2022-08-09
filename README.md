# Cosmpy Evmos

Example on how to use the cosmpy lib to interact with the Evmos Network

## Requirements:

```sh
pip install comspy
pip install evmoswallet
```

## Modify the cosmpy lib to support evmos

- cosmpy/aerial/client/init.py

Remove the lines:

```python
if not response.account.Is(BaseAccount.DESCRIPTOR):
	raise RuntimeError("Unexpected account type returned from query")
```

- comspy/aerial/tx.py

Add a new parameter to the seal function in order to delegate to the wallet the pubkey generation, then use the wallet to create the pubkey. The seal function should look like this:

```python
    def seal(
        self,
        signing_cfgs: Union[SigningCfg, List[SigningCfg]],
        fee: str,
        gas_limit: int,
        memo: Optional[str] = None,
        wallet = None
    ) -> "Transaction":
        self._state = TxState.Sealed

        input_signing_cfgs: List[SigningCfg] = (
            signing_cfgs if _is_iterable(signing_cfgs) else [signing_cfgs]  # type: ignore
        )

        signer_infos = []
        if hasattr(wallet, 'evmos'):
            signer_infos.append(
                SignerInfo(
                    public_key=_wrap_in_proto_any([wallet.create_proto_pub_key()])[0],
                    mode_info=ModeInfo(
                        single=ModeInfo.Single(mode=SignMode.SIGN_MODE_DIRECT)
                    ),
                    sequence=input_signing_cfgs[0].sequence_num,
                )
            )
        else:
            for signing_cfg in input_signing_cfgs:
                assert signing_cfg.mode == SigningMode.Direct
                signer_infos.append(
                    SignerInfo(
                        public_key=_create_proto_public_key(signing_cfg.public_key),
                        mode_info=ModeInfo(
                            single=ModeInfo.Single(mode=SignMode.SIGN_MODE_DIRECT)
                        ),
                        sequence=signing_cfg.sequence_num,
                    )
                )

        auth_info = AuthInfo(
            signer_infos=signer_infos,
            fee=Fee(amount=parse_coins(fee), gas_limit=gas_limit),
        )

        self._fee = fee

        self._tx_body = TxBody()
        self._tx_body.memo = memo or ""
        self._tx_body.messages.extend(
            _wrap_in_proto_any(self._msgs)
        )  # pylint: disable=E1101

        self._tx = Tx(body=self._tx_body, auth_info=auth_info)
        return self
```

- cosmpy/aerial/client/utils.py

Edit the `prepare_and_broadcast_basic_transaction` to send the new parameter to the `seal` function, the function should look like this:

```python

def prepare_and_broadcast_basic_transaction(
    client: "LedgerClient",  # type: ignore # noqa: F821
    tx: "Transaction",  # type: ignore # noqa: F821
    sender: "Wallet",  # type: ignore # noqa: F821
    account: Optional["Account"] = None,  # type: ignore # noqa: F821
    gas_limit: Optional[int] = None,
    memo: Optional[str] = None,
) -> SubmittedTx:
    # query the account information for the sender
    if account is None:
        account = client.query_account(sender.address())

    if gas_limit is not None:
        # simply build the fee from the provided gas limit
        fee = client.estimate_fee_from_gas(gas_limit)
    else:

        # we need to build up a representative transaction so that we can accurately simulate it
        tx.seal(
            SigningCfg.direct(sender.public_key(), account.sequence),
            fee="",
            gas_limit=0,
            memo=memo,
            wallet=sender
        )
        tx.sign(sender.signer(), client.network_config.chain_id, account.number)
        tx.complete()

        # simulate the gas and fee for the transaction
        gas_limit, fee = client.estimate_gas_and_fee_for_tx(tx)

    # finally, build the final transaction that will be executed with the correct gas and fee values
    tx.seal(
        SigningCfg.direct(sender.public_key(), account.sequence),
        fee=fee,
        gas_limit=gas_limit,
        memo=memo,
        wallet=sender
    )
    tx.sign(sender.signer(), client.network_config.chain_id, account.number)
    tx.complete()

    return client.broadcast_tx(tx)
```

## Run the example:

```python
python main.py
```

## Known issues

- Gas estimations are not working correctly, `gas_limit` should be set manually
