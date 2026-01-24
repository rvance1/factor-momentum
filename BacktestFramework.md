2. **Backtesting Framework (MVE Context)**

  **Weights:**

  At each time $t$, the optimal weights are:

  $$
  w_t^* = \frac{1}{2\lambda} \Sigma_t^{-1} \mu_t
  $$
  
  We set lambda (the risk adversion) to 10. For expected return (mu) we use our estimated alpha, and the covarience matrix is forcasted by Barra. 
  
  **Alphas:**

  Alphas estimated with:

  $$
  \alpha_t = \mathrm{IC}_t \cdot Z(\mathrm{signal}_t) \cdot \sigma_{\mathrm{residual}, t}
  $$

  The residual risk component is computed ex-ante, and we assume a 0.05 information coefficient.

  **Constraint**
  
  We add a leverage constraint:

  $$
  \sum_{i=1}^{N} |w_i| \le 1
  $$
  
  We rebalance monthly. Transaction costs are not accounted for.