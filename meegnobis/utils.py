import numpy as np


def _conv(array, filt):
    """Run convolution by keeping the same onset of events"""
    res = np.convolve(array, filt)
    return res[:len(array)]


def convolve(array, filt):
    """A vectorized version of np.convolve, lifted from the example

    Parameters
    ----------
    array : np.ndarray
        multi dimensional array on which filt will be applied; it is vectorized
        along the last two dimensions, so for Epochs the dimensions should be
        (channel, epoch, time) in order to average across time
    filt : np.ndarray
        filter to be applied on array

    Returns
    -------
    array_convolve : np.ndarray (shape of array)
        the convolved array, computed using mode = 'same'
    """
    if np.__version__ >= '1.12.0':
        convvect = np.vectorize(lambda x, y: np.convolve(x, y)[..., :len(x)],
                                signature='(n),(m)->(k)',
                                doc=__doc__)
        return convvect(array, filt)
    else:
        # we need to vectorize manually
        if array.ndim > 3:
            raise ValueError(
                "This function doesn't work on multidimensional "
                "arrays with more than 3 dimensions under numpy < 1.12.0")
        conv = lambda x: _conv(x, filt)
        if array.ndim == 1:
            return conv(array)
        else:
            array_convolve = []
            for array0 in array:
                if array0.ndim == 1:
                    array_convolve.append(conv(array0))
                else:
                    array_convolve.append(
                        np.apply_along_axis(conv, 1, array0)
                    )
            return np.stack(array_convolve)


def moving_average(epoch, twindow):
    """

    Parameters
    ----------
    epoch : mne.Epochs object
    twindow : float; time window in s for which to compute a moving average

    Returns
    -------
    epoch_avg : mne.Epochs object
        a new Epochs object containing the epochs after having applied the
        moving average in time
    """
    epoch_ = epoch.copy()
    nsamples = np.ceil(float(twindow) * epoch.info['sfreq'])
    if nsamples > len(epoch.times):
        raise ValueError("Cannot compute moving average with time window "
                         "{0} and epoch length "
                         "{1}".format(twindow,
                                      epoch.times[-1] - epoch.times[0]))
    filt = np.ones(int(nsamples))/nsamples
    data = epoch_._data
    # by default we have (epochs, channels, times);
    # we need (channels, epochs, times)
    data = np.transpose(data, [1, 0, 2])
    data = convolve(data, filt)
    data = np.transpose(data, [1, 0, 2])
    epoch_._data = data
    return epoch_


def _npairs(n_items):
    """Return the number of pairs given n_items; corresponds to the length
    of a triu matrix (diagonal included)"""
    if n_items < 2:
        raise ValueError("More than two items required, "
                         "passed {0}".format(n_items))
    n_pairs = int(n_items * (n_items - 1) / 2. + n_items)
    return n_pairs


def _get_unique_targets(targets_train, targets_test):
    unique_targets_train = np.unique(targets_train)
    unique_targets_test = np.unique(targets_test)
    unique_targets = sorted(set(unique_targets_train).
                            intersection(unique_targets_test))
    return unique_targets