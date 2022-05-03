import numpy as np

from joblib import Parallel, delayed


from tslearn import metrics

def compute_similarity_matrix(data, normalise=True):
    # Inspired from code by @GillesVandewiele:
    # https://github.com/rtavenar/tslearn/pull/128#discussion_r314978479
    matrix = np.zeros((len(data), len(data)))
    indices = np.triu_indices(len(data), k=1, m=len(data))
    matrix[indices] = Parallel(n_jobs=8, prefer="processes", verbose=1)(
                               delayed(metrics.dtw)(data[i], data[j],)
                               for i, j in zip(*indices))
    sm = matrix + matrix.T
    if normalise:
        sm = sm / sm.max()
    return sm

def tsne_embed(sm, perplexity=10):
    af = compute_affinity(sm, perplexity=perplexity)
    emb = embed(af)
    return emb


import scipy.optimize as scopt
def compute_affinity(distance_mat, perplexity=100):
    """From the distance matrix, the affinity matrix is computed. This converting distances to probabilities
    of being close with a normal distribution. The sigma of each distribution is optimised to provide for a
    given perplexity value of the distribution.
    """
    n_total = distance_mat.shape[0]
    
    def all_but_(i):
        res = np.ones(n_total)
        res[i] = 0
        return res.astype(bool)

    # def p_of_j_given_i(j,i, sigma=1):
    #     if i == j: return 0
    #     all_j = np.exp(-dm_[i,:]**2 / (2*sigma**2))
    #     j = all_j[j]
    #     b = all_j[all_but_(i)].sum()
    #     res = j/b
    #     return res

    def p_of_all_j_given_i(i, sigma=1):
        """The probability of j given i, for all j.
        """
        a = np.exp(-distance_mat[i,:]**2 / (2*sigma**2))
        b = a[all_but_(i)].sum()
        a[i] = 0
        return a/b

    def entropy(i, sigma=1):
        """The entropy of the distribution for point i.
        """
        a = p_of_all_j_given_i(i, sigma)
        a = a[all_but_(i)]
        res = - (a * np.log2(a)).sum()
        return res

    def obj_perplexity_i(i):
        def obj_perplexity_sigma(sigma):
            return np.abs(2**entropy(i, sigma) - perplexity)
        return obj_perplexity_sigma

    sigma = list(map(lambda x: scopt.minimize(obj_perplexity_i(x), 0.1, method='Nelder-Mead').x,
                     range(n_total)))
    sigma = np.array(sigma)

    affinity_mat = np.zeros((n_total, n_total))
    for i in range(n_total):
        affinity_mat[i] = p_of_all_j_given_i(i, sigma[i])

    # make affinity matrix symmetric
    affinity_mat = affinity_mat + affinity_mat.T
    # normalise
    affinity_mat = affinity_mat / affinity_mat.sum()

    return affinity_mat


import scipy.sparse as scspa
from openTSNE.affinity import Affinities
from openTSNE import TSNEEmbedding
# from openTSNE.callbacks import ErrorLogger

def embed(affinity_mat, n_iter_0=250, n_iter_1=750):
    n_total = affinity_mat.shape[0]

    # make sparse
    aff_csr = scspa.csr_matrix(affinity_mat)

    # plug into opentsne
    affinities = Affinities()
    affinities.P = aff_csr

    init_position = np.random.random((n_total, 2))

    embedding_train = TSNEEmbedding(
        init_position,
        affinities,
        negative_gradient_method="fft",
        n_jobs=8,
    )

    # default parameters on the 2-stage process
    embedding_train_1 = embedding_train.optimize(n_iter=250, exaggeration=12, momentum=0.5, verbose=3)
    embedding_train_2 = embedding_train_1.optimize(n_iter=750, momentum=0.8, verbose=3)

    return embedding_train_2



import sklearn
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

def K_NN_classifier(data, labels, K=1):

    split = sklearn.model_selection.ShuffleSplit(n_splits=1, test_size=0.25)
    id_train, id_test = next(split.split(data))

    nnc_train = data[id_train]
    nnc_test  = data[id_test]

    neigh = KNeighborsClassifier(n_neighbors=K)
    neigh.fit(nnc_train, labels[id_train])

    y_pred = neigh.predict(nnc_test)
    y_true = labels[id_test]

    return accuracy_score(y_true, y_pred)