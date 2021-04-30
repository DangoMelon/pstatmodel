import numpy as np
import pandas as pd
import statsmodels.api as sm


def stepwise_selection(
    X,
    y,
    initial_list=[],
    threshold_in=0.01,
    threshold_out=0.05,
    verbose=True,
    max_vars=12,
    min_vars=4,
):
    """Perform a forward-backward feature selection
    based on p-value from statsmodels.api.OLS
    Arguments:
        X - pandas.DataFrame with candidate features
        y - list-like with the target
        initial_list - list of features to start with (column names of X)
        threshold_in - include a feature if its p-value < threshold_in
        threshold_out - exclude a feature if its p-value > threshold_out
        verbose - whether to print the sequence of inclusions and exclusions
    Returns: list of selected features
    Always set threshold_in < threshold_out to avoid infinite looping.
    See https://en.wikipedia.org/wiki/Stepwise_regression for the details
    """
    included = list(initial_list)
    lower = False
    #     over = False
    if np.isnan(y).any():
        return [], np.nan, np.nan
    if verbose:
        print(f"Initial threshold_in value: {threshold_in}")
    while True:
        changed = False
        # forward step
        excluded = list(set(X.columns) - set(included))
        new_pval = pd.Series(index=excluded, dtype=float)
        for new_column in excluded:
            model = sm.OLS(
                y, sm.add_constant(pd.DataFrame(X[included + [new_column]]))
            ).fit()
            new_pval[new_column] = model.pvalues[new_column]
        best_pval = new_pval.min()
        if best_pval < threshold_in:
            best_feature = new_pval.index[new_pval.argmin()]
            included.append(best_feature)
            changed = True
            if verbose:
                print("Add  {:30} with p-value {:.6}".format(best_feature, best_pval))
        # backward step
        model = sm.OLS(y, sm.add_constant(pd.DataFrame(X[included]))).fit()
        # use all coefs except intercept
        pvalues = model.pvalues.iloc[1:]
        worst_pval = pvalues.max()  # null if pvalues is empty
        #         print(f"{best_pval=} // {worst_pval=}")
        if worst_pval > threshold_out:
            changed = True
            worst_feature = pvalues.index[pvalues.argmax()]
            included.remove(worst_feature)
            if verbose:
                print("Drop {:30} with p-value {:.6}".format(worst_feature, worst_pval))

        if len(included) > max_vars and threshold_in != 0.01 and not lower:
            threshold_in = np.round(max([0.01, threshold_in - 0.01]), decimals=2)
            if verbose:
                print(f"Upped threshold_in value to {threshold_in}")
            included = []
            changed = True

        if len(included) >= min_vars and lower:
            if model.rsquared ** (0.5) > 0.9:
                changed = False
                if verbose:
                    print("Breaking condition met: R value over 0.9")

        if not changed:
            #             break
            if len(included) < min_vars and threshold_in != 0.1:
                threshold_in = np.round(min([0.1, threshold_in + 0.01]), decimals=2)
                if verbose:
                    print(f"Dropped threshold_in value to {threshold_in}")
                included = []
                lower = True
            else:
                break  # pragma: no cover
    return included, model, threshold_in


# def constraint_stepwise_selection(*args, vars_limit, threshold_in, **kwargs):
#     variables, model = stepwise_selection(*args, **kwargs)
#     list_thresh = [0.04, 0.03]
#     if len(variables) - 1 > vars_limit:
#         for thresh in list_thresh:
#             variables, model = stepwise_selection(*args, threshold_in=thresh ** kwargs)
#             if len(variables) - 1 <= vars_limit:
#                 break
#     return variables, model
