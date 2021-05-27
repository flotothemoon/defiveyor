import enum
from typing import Optional


class Asset(enum.Enum):
    Bitcoin = "BTC"
    Ethereum = "ETH"
    DAI = "DAI"
    USD_Coin = "USDC"
    USD_Token = "USDT"

    @property
    def is_stable(self) -> bool:
        return self in {Asset.DAI, Asset.USD_Token, Asset.USD_Coin}

    @staticmethod
    def map(asset_symbol: str) -> Optional["Asset"]:
        for asset in Asset:
            # TODO @Robustness: use stricter mechanism for mapping (wrapped) symbols to assets
            if asset.value in asset_symbol:
                return asset

        return None


class Protocol(enum.Enum):
    UniSwapV2 = "uniswap-v2"
    UniSwapV3 = "uniswap-v3"
    SushiSwap = "sushiswap"
    Bancor = "bancor"
    OneInch = "1inch"
    Yearn = "yearn"
    Compound = "compound"
    dYdX = "dYdX"
    Aave = "aave"


class Network(enum.Enum):
    Ethereum = "ethereum"


class RiskProfile(enum.Enum):
    Low = "low"
    Medium = "medium"
    High = "high"
