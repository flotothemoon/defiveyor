import enum


class Asset(enum.Enum):
    Bitcoin = "BTC",
    Ethereum = "ETH",
    DAI = "DAI",
    USD_Coin = "USDC",
    USD_Token = "USDT"


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
