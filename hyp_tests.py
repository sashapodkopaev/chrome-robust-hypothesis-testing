import numpy as np
import pandas as pd
from tools import get_alpha_quantile_student, \
    compute_mean_hist_data, compute_quantile_hist_data


def jackknife_t_test(treatment_mv_all_buckets, treatment_mv_all_expect_given,
                     control_mv_all_buckets, control_mv_all_expect_given,
                     ci_level):
    """
    Jackknife t-test for data in cookie buckets

    Parameters
    ----------
      treatment_mv_all_buckets: float
        aggregated metric over all buckets 
          for treatment group

      treatment_mv_all_expect_given: array_like
        aggregated metric over all buckets expect one 
          for treatment group

      control_mv_all_buckets: float
        aggregated metric over all buckets 
          for control group

      control_mv_all_expect_given:
        aggregated metric over all buckets expect one 
          for control group

      ci_level: float in (0,1)
        nominal coverage of the CI 

    Returns
    ----------
      ci_center:
        center of the confidence interval

      ci_size:
        size/radius of the confidence interval 
    """

    # compute number of buckets
    number_of_buckets = len(treatment_mv_all_expect_given.ravel())

    # obtain correct quantile of the Student t-distribution corresponding
    # to (N-1) degrees of freedom
    qq = get_alpha_quantile_student(ci_level, number_of_buckets-1)

    # check that treatment and control have the same number of buckets
    assert number_of_buckets == len(control_mv_all_expect_given.ravel())

    # compute percent change for total change of metric value (mv)
    overall_percent_change = 100 * \
        (treatment_mv_all_buckets / control_mv_all_buckets - 1)

    # compute percent change for all buckets except given
    percent_change_for_all_but_given = 100 * \
        (treatment_mv_all_expect_given / control_mv_all_expect_given - 1)

    # compute ps_{-j} according to the definition
    ps_j = number_of_buckets * overall_percent_change - \
        (number_of_buckets - 1) * percent_change_for_all_but_given

    # compute center and radius of the CI
    ci_center = ps_j.mean()
    std_ps = ps_j.std(ddof=1)

    ci_size = qq * std_ps / np.sqrt(number_of_buckets)

    return ci_center, ci_size


def jackknife_cookie_bucket_mean(treatment_group, control_group,
                                 number_of_buckets, ci_level):
    """"
    Perform jackknife cookie bucket test (for not binned data)

    Parameters
    ----------
      treatment_group: pd.Dataframe
        dataframe corresponding to treatment group that contains two columns:
          - Client ID
          - Metric Value

      control_group: pd.Dataframe
        dataframe corresponding to control group that contains two columns:
          - Client ID
          - Metric Value

      number_of_buckets: int
        number of buckets to be used for performing the test

      ci_level: (0,1)
        nominal coverage of the CI 

    Returns
    ----------
      ci_center:
        center of the confidence interval

      ci_size:
        size/radius of the confidence interval 

    """

    # temporarily add bucket id
    treatment_group['Bucket ID'] = (
        treatment_group['Client ID'] % number_of_buckets).astype('int')
    control_group['Bucket ID'] = (
        control_group['Client ID'] % number_of_buckets).astype('int')

    # list of all bucket ids
    bucket_ids = np.arange(number_of_buckets).tolist()

    # for stacking the results for both treatment and control groups
    treatment_group_mv = list()
    control_group_mv = list()

    for cur_bucket in bucket_ids:
        # leave one bucket out and compute the mean
        treatment_group_mv += [treatment_group.loc[treatment_group['Bucket ID']
                                                   != cur_bucket]['Metric Value'].mean()]
        control_group_mv += [control_group.loc[control_group['Bucket ID']
                                               != cur_bucket]['Metric Value'].mean()]

    # removing temporary column
    treatment_group = treatment_group.drop(axis=1, columns=['Bucket ID'])
    control_group = control_group.drop(axis=1, columns=['Bucket ID'])

    # convert to array for further purposes
    treatment_group_mv = np.stack(treatment_group_mv)
    control_group_mv = np.stack(control_group_mv)

    # compute mean metric value in both groups
    treatment_all = treatment_group['Metric Value'].mean()
    control_all = control_group['Metric Value'].mean()

    ci_center, ci_size = jackknife_t_test(treatment_all, treatment_group_mv,
                                          control_all, control_group_mv,
                                          ci_level)

    return ci_center, ci_size


def jackknife_cookie_bucket_quantile(treatment_group, control_group,
                                     number_of_buckets, ci_level, quantile_to_test):
    """"
    Perform jackknife cookie bucket test (for not binned data)

    Parameters
    ----------
      treatment_group: pd.Dataframe
        dataframe corresponding to treatment group that contains two columns:
          - Client ID
          - Metric Value

      control_group: pd.Dataframe
        dataframe corresponding to control group that contains two columns:
          - Client ID
          - Metric Value

      number_of_buckets: int
        number of buckets to be used for performing the test

      ci_level: (0,1)
        nominal coverage of the CI 

      quantile_to_test: (0,1)
        quantile for which Jackknife Cookie Bucket test is to be performed

    Returns
    ----------
      ci_center:
        center of the confidence interval

      ci_size:
        size/radius of the confidence interval 

    """

    # temporarily add bucket id
    treatment_group['Bucket ID'] = (
        treatment_group['Client ID'] % number_of_buckets).astype('int')
    control_group['Bucket ID'] = (
        control_group['Client ID'] % number_of_buckets).astype('int')

    # list of all bucket ids
    bucket_ids = np.arange(number_of_buckets).tolist()

    # for stacking the results for both treatment and control groups
    treatment_group_mv = list()
    control_group_mv = list()

    for cur_bucket in bucket_ids:
        # leave one bucket out and compute the quantile
        treatment_group_mv += [treatment_group.loc[treatment_group['Bucket ID']
                                                   != cur_bucket][
            'Metric Value'].quantile(q=quantile_to_test)]
        control_group_mv += [control_group.loc[control_group['Bucket ID']
                                               != cur_bucket][
            'Metric Value'].quantile(q=quantile_to_test)]

    # removing temporary column
    treatment_group = treatment_group.drop(axis=1, columns=['Bucket ID'])
    control_group = control_group.drop(axis=1, columns=['Bucket ID'])

    # convert to array for further purposes
    treatment_group_mv = np.stack(treatment_group_mv)
    control_group_mv = np.stack(control_group_mv)

    # compute overall quantiles in both groups
    treatment_all = treatment_group['Metric Value'].quantile(
        q=quantile_to_test)
    control_all = control_group['Metric Value'].quantile(q=quantile_to_test)

    ci_center, ci_size = jackknife_t_test(treatment_all, treatment_group_mv,
                                          control_all, control_group_mv,
                                          ci_level)

    return ci_center, ci_size


def jackknife_cookie_bucket_quantile_binned(treatment_binned_data, control_binned_data,
                                            bins_boundaries, number_of_buckets,
                                            ci_level, quantile_to_test):
    """"
    Perform jackknife cookie bucket test (for binned data)

    Parameters
    ----------
      treatment_binned_data: pd.Dataframe
        dataframe corresponding to treatment group that contains two types of columns:
          - Client ID
          - Count of observations in Bin "j" for a given client

      control_binned_data: pd.Dataframe
        dataframe corresponding to control group that contains two types of columns:
          - Client ID
          - Count of observations in Bin "j" for a given client

      bins_boundaries: list of bins boundaries (excluding zero)
        Example: [1,3,5,9,16] corresponds to 5 bins

      number_of_buckets: int
        number of buckets to be used for performing the test

      ci_level: (0,1)
        nominal coverage of the CI 

      quantile_to_test: (0,1)
        quantile for which Jackknife Cookie Bucket test is to be performed

    Returns
    ----------
      ci_center:
        center of the confidence interval

      ci_size:
        size/radius of the confidence interval 

    """

    # pdb.set_trace()

    # list of all bucket ids
    bucket_ids = np.arange(number_of_buckets).tolist()

    # compute buckets corresponding to each client
    treatment_binned_data['Bucket ID'] = (treatment_binned_data['Client ID'] %
                                          number_of_buckets).astype('int')

    control_binned_data['Bucket ID'] = (control_binned_data['Client ID'] %
                                        number_of_buckets).astype('int')

    # compute histogram data / total counts within each bucket
    treatment_bucket_data = treatment_binned_data.groupby('Bucket ID').sum()
    control_bucket_data = control_binned_data.groupby('Bucket ID').sum()

    # drop client ID from bucketed data
    treatment_bucket_data = treatment_bucket_data.drop(
        axis=1, columns=['Client ID'])
    control_bucket_data = control_bucket_data.drop(
        axis=1, columns=['Client ID'])

    # drop temporary columns from the Dataframes
    treatment_binned_data = treatment_binned_data.drop(
        axis=1, columns=['Bucket ID'])
    control_binned_data = control_binned_data.drop(
        axis=1, columns=['Bucket ID'])

    # for stacking the results for both treatment and control groups
    treatment_group_mv = list()
    control_group_mv = list()

    # number of histogram bins
    num_of_bins = len(bins_boundaries)

    # obtain bins given boundaries
    bins_tuples = [(0, bins_boundaries[0])] + [(bins_boundaries[i-1],
                                                bins_boundaries[i])
                                               for i in range(1, num_of_bins)]

    for cur_bucket in bucket_ids:
        # leave one bucket out and compute the total counts for the left buckets
        cur_hist_treatment = treatment_bucket_data[treatment_bucket_data.index
                                                   != cur_bucket].sum().values
        cur_hist_control = control_bucket_data[control_bucket_data.index
                                               != cur_bucket].sum().values
        # compute approximate quantiles based on binned data
        treatment_group_mv += [compute_quantile_hist_data(
            cur_hist_treatment, bins_tuples, quantile=quantile_to_test)]
        control_group_mv += [compute_quantile_hist_data(
            cur_hist_control, bins_tuples, quantile=quantile_to_test)]

    # convert to array for further purposes
    treatment_group_mv = np.stack(treatment_group_mv)
    control_group_mv = np.stack(control_group_mv)

    # compute approximate quantiles for all buckets and both groups
    treatment_all = compute_quantile_hist_data(
        treatment_bucket_data.sum().values, bins_tuples, quantile=quantile_to_test)

    control_all = compute_quantile_hist_data(
        control_bucket_data.sum().values, bins_tuples, quantile=quantile_to_test)

    ci_center, ci_size = jackknife_t_test(treatment_all, treatment_group_mv,
                                          control_all, control_group_mv,
                                          ci_level)

    return ci_center, ci_size


def jackknife_cookie_bucket_mean_binned(treatment_binned_data, control_binned_data,
                                        bins_boundaries, number_of_buckets,
                                        ci_level):
    """"
    Perform jackknife cookie bucket test (for binned data)

    Parameters
    ----------
      treatment_binned_data: pd.Dataframe
        dataframe corresponding to treatment group that contains two types of columns:
          - Client ID
          - Count of observations in Bin "j" for a given client

      control_binned_data: pd.Dataframe
        dataframe corresponding to control group that contains two types of columns:
          - Client ID
          - Count of observations in Bin "j" for a given client

      bins_boundaries: list of bins boundaries (excluding zero)
        Example: [1,3,5,9,16] corresponds to 5 bins

      number_of_buckets: int
        number of buckets to be used for performing the test

      ci_level: (0,1)
        nominal coverage of the CI 

    Returns
    ----------
      ci_center:
        center of the confidence interval

      ci_size:
        size/radius of the confidence interval 

    """

    # pdb.set_trace()

    # list of all bucket ids
    bucket_ids = np.arange(number_of_buckets).tolist()

    # compute buckets corresponding to each client
    treatment_binned_data['Bucket ID'] = (treatment_binned_data['Client ID'] %
                                          number_of_buckets).astype('int')

    control_binned_data['Bucket ID'] = (control_binned_data['Client ID'] %
                                        number_of_buckets).astype('int')

    # compute histogram data / total counts within each bucket
    treatment_bucket_data = treatment_binned_data.groupby('Bucket ID').sum()
    control_bucket_data = control_binned_data.groupby('Bucket ID').sum()

    # drop client ID from bucketed data
    treatment_bucket_data = treatment_bucket_data.drop(
        axis=1, columns=['Client ID'])
    control_bucket_data = control_bucket_data.drop(
        axis=1, columns=['Client ID'])

    # drop temporary columns from the Dataframes
    treatment_binned_data = treatment_binned_data.drop(
        axis=1, columns=['Bucket ID'])
    control_binned_data = control_binned_data.drop(
        axis=1, columns=['Bucket ID'])

    # for stacking the results for both treatment and control groups
    treatment_group_mv = list()
    control_group_mv = list()

    # number of histogram bins
    num_of_bins = len(bins_boundaries)

    # obtain bins given boundaries
    bins_tuples = [(0, bins_boundaries[0])] + [(bins_boundaries[i-1],
                                                bins_boundaries[i])
                                               for i in range(1, num_of_bins)]

    for cur_bucket in bucket_ids:
        # leave one bucket out and compute the total counts for the left buckets
        cur_hist_treatment = treatment_bucket_data[treatment_bucket_data.index
                                                   != cur_bucket].sum().values
        cur_hist_control = control_bucket_data[control_bucket_data.index
                                               != cur_bucket].sum().values
        # compute approximate means based on binned data
        treatment_group_mv += [compute_mean_hist_data(
            cur_hist_treatment, bins_tuples)]
        control_group_mv += [compute_mean_hist_data(
            cur_hist_control, bins_tuples)]

    # convert to array for further purposes
    treatment_group_mv = np.stack(treatment_group_mv)
    control_group_mv = np.stack(control_group_mv)

    # compute approximate means for all buckets and both groups
    treatment_all = compute_mean_hist_data(
        treatment_bucket_data.sum().values, bins_tuples)

    control_all = compute_mean_hist_data(
        control_bucket_data.sum().values, bins_tuples)

    ci_center, ci_size = jackknife_t_test(treatment_all, treatment_group_mv,
                                          control_all, control_group_mv,
                                          ci_level)

    return ci_center, ci_size