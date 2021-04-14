import enum
from typing import Optional


class Asset(enum.Enum):
    Bitcoin = "BTC"
    Ethereum = "ETH"
    DAI = "DAI"
    USD_Coin = "USDC"
    USD_Token = "USDT"

    @staticmethod
    def map(asset_symbol: str) -> Optional["Asset"]:
        for asset in Asset:
            # TODO @Robustness: use stricter mechanism for mapping (wrapped) symbols to assets
            if asset.value in asset_symbol:
                return asset

        return None


class Protocol(enum.Enum):
    UniSwap = "uniswap-v2"
    SushiSwap = "sushiswap"
    Curve = "curve"
    Bancor = "bancor"
    OneInch = "1inch"
    Yearn = "yearn"
    Compound = "compound"
    dYdX = "dYdX"
    Aave = "aave"


class Network(enum.Enum):
    Ethereum = "ethereum"
