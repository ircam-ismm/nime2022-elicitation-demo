import numpy as np


# number of samples
# g1.groupby(['id', 'day', 'gesture', 'trial']).ngroups
n_obs = 1080
n_tmp = 5
n_total = n_obs + n_tmp

def get_data(gesture=1):
    """Return the data related to a specific gesture (i.e. 1 or 2) read from file.
    """
    df = pd.read_csv('./data.df', index_col=0)
    data_dimensions = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
    g1 = select(df, gesture=gesture)


def get_distance_matrix(gesture=1):
    """The distance matrix contains each trials by participants, sorted per ['id', 'day', 'gesture', 'trial'].
    d[i, j] = dtw(trial[i], trial[j])

    The last five rows are reserved for the templates provided by Michelle.
    """

    distance_mat = np.zeros((n_total, n_total))

    for i in range(n_obs):
        distance_mat[i, :n_obs] = np.load('../pairwise/g'+str(gesture)+'/'+str(i)+'.npy')

    for i in range(n_tmp):
        distance_mat[n_obs + i] = np.load('../pairwise/g'+str(gesture)+'/template_'+str(i)+'_row.npy')

    for i in range(n_tmp):
        distance_mat[:, n_obs + i] = np.load('../pairwise/g'+str(gesture)+'/template_'+str(i)+'_col.npy')

    # the distances are normalised with max value, in order to get values ranging from 0 to 1.
    dm_ = distance_mat / distance_mat.max()

    return dm_


import scipy.optimize as sopt
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

    sigma = list(map(lambda x: sopt.minimize(obj_perplexity_i(x), 0.1, method='Nelder-Mead').x,
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


def get_affinity_matrix(perplexity=100):
    distance_matrix = get_distance_matrix()
    affinity_matrix = compute_affinity(distance_matrix, perplexity)
    return affinity_matrix


import scipy.sparse as ssparse
from openTSNE.affinity import Affinities
from openTSNE import TSNEEmbedding
# from openTSNE.callbacks import ErrorLogger

def embed(affinity_mat, n_iter_0=250, n_iter_1=750):
    n_total = affinity_mat.shape[0]

    # make sparse
    aff_csr = ssparse.csr_matrix(affinity_mat)

    # plug into opentsne
    affinities = Affinities()
    affinities.P = aff_csr


    # templates are placed on (0,0)
    init_position = np.random.random((n_total, 2))
    # init_position[n_obs:] = 0


    embedding_train = TSNEEmbedding(
        init_position,
        affinities,
        negative_gradient_method="fft",
        n_jobs=8,
    )

    # default parameters on the 2-stage process
    embedding_train_1 = embedding_train.optimize(n_iter=250, exaggeration=12, momentum=0.5)
    embedding_train_2 = embedding_train_1.optimize(n_iter=750, momentum=0.8)

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