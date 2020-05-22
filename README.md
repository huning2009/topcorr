# TopCorr

A small Python library for constructing filtered correlation networks

## Getting Started

The package requires networkx and numpy. Scikit-learn is used in some of the examples to generate correlation matrices.

An example for creating a PMFG
```
import topcorr
import networkx as nx
import numpy as np
from sklearn.datasets import make_spd_matrix

p = 50
n = 200
C = make_spd_matrix(p)
X = np.random.multivariate_normal(np.zeros(p), C, n)
corr = np.corrcoef(X.T)

pmfg_G = topcorr.pmfg(corr)
```

The other methods work in much the same way (bar thresholding) - put in a correlation matrix and
it will return a networkx graph 

## Testing

If you're interested in running the tests they can be found in the /tests/ folder and are to
be run with nose2. 

For the TMFG the authors have provided an R implementation, so we test against that. This requires
that you install rpy2 and the NetworkToolbox package. The other tests will also require the installation
of sklearn. 

## Authors

* **Tristan Millington**

## License

This project is licensed under the GNU GPL - see the [LICENSE.md](LICENSE.md) file for details

## Implemented
* MST
* PMFG
* TMFG

## References
* [Tumminello, M., Aste, T., Di Matteo, T., & Mantegna, R. N. (2005). A tool for filtering information in complex systems. Proceedings of the National Academy of Sciences of the United States of America, 102(30), 10421-10426.](http://www.pnas.org/content/102/30/10421)
* [Mantegna, R. N. (1999). Hierarchical structure in financial markets. The European Physical Journal B-Condensed Matter and Complex Systems, 11(1), 193-197.](https://epjb.epj.org/articles/epjb/abs/1999/17/b9199/b9199.html)
* [Guido Previde Massara, T. Di Matteo, Tomaso Aste, Network Filtering for Big Data: Triangulated Maximally Filtered Graph, Journal of Complex Networks, Volume 5, Issue 2, June 2017, Pages 161–178](https://doi.org/10.1093/comnet/cnw015)
