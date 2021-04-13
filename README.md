# Defiveyor
[Cryptoveyor](https://www.cryptoveyor.com) but for DeFi rates. 

## Format 

```
GET /assets
 => array of
 - protocol: string ("uniswapv2")
 - symbol: string ("BTC")
 - symbol_wrapped: string ("WBTC")
 - apy_average_30days: float (0.07)
```

```
GET /pairs
 => array of
 - protocol: string ("uniswapv2")
 - symbol0: string ("BTC")
 - symbol0_wrapped: string ("WBTC")
 - symbol1: string ("ETH")
 - symbol1_wrapped: string ("WETH")
 - apy_average_30days: float (0.07)
```

## Assets
- BTC
- ETH 
- DAI 
- USDC 
- USDT 

## Platforms
 
- [UniSwap](https://uniswap.org)
- [SushiSwap](https://sushi.com/)
- [Curve](https://curve.fi/)
- [Bancor](https://app.bancor.network) 
- [1Inch](https://1inch.exchange)
- [Yearn](https://yearn.finance) 
  
- [Compound](https://compound.finance) 
- [dYdX](https://trade.dydx.exchange/) 
- [Aave](https://aave.com/)
  
### Not yet supported
- [Idle](https://idle.finance) 
- [mStable](https://app.mstable.org)

## Sources
 - [Zapper API](https://docs.zapper.fi/zapper-api/api-getting-started)
 - [Defirate API?](https://defirate.com/lend/)
 - [Aave API](https://aave-api-v2.aave.com/)
 - [Compound API](https://compound.finance/docs/api#MarketHistoryService)
 - [dYdX API](https://docs.dydx.exchange/#get-orderbook)