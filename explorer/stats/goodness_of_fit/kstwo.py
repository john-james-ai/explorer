#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ================================================================================================ #
# Project    : Enter Project Name in Workspace Settings                                            #
# Version    : 0.1.19                                                                              #
# Python     : 3.10.10                                                                             #
# Filename   : /explorer/stats/goodness_of_fit/kstwo.py                                            #
# ------------------------------------------------------------------------------------------------ #
# Author     : John James                                                                          #
# Email      : john.james.ai.studio@gmail.com                                                      #
# URL        : Enter URL in Workspace Settings                                                     #
# ------------------------------------------------------------------------------------------------ #
# Created    : Tuesday June 6th 2023 01:45:05 am                                                   #
# Modified   : Wednesday June 7th 2023 05:06:40 am                                                 #
# ------------------------------------------------------------------------------------------------ #
# License    : MIT License                                                                         #
# Copyright  : (c) 2023 John James                                                                 #
# ================================================================================================ #
from dataclasses import dataclass
from typing import Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from explorer.stats.profile import StatTestProfileTwo
from explorer.stats.base import StatTestResult, StatisticalTest, StatTestProfile
from explorer.visual.config import Canvas


# ------------------------------------------------------------------------------------------------ #
#                                     TEST RESULT                                                  #
# ------------------------------------------------------------------------------------------------ #
@dataclass
class KSTwoTestResult(StatTestResult):
    reference_distribution: str = None
    sample1: Union[pd.DataFrame, np.ndarray, pd.Series] = None
    sample2: Union[pd.DataFrame, np.ndarray, pd.Series] = None

    def plot(self, ax: plt.Axes = None) -> plt.Axes:  # pragma: no cover
        """Plots the critical values and shades the area on the KS distribution

        Args:
            ax (plt.Axes): A matplotlib Axes object. Optional
        """
        canvas = Canvas()
        ax = ax or canvas.ax

        # Get the callable for the statistic.
        n = len(self.sample1)

        x = np.linspace(stats.kstwo.ppf(0.01, n), stats.ksone.ppf(0.999, n), 100)
        y = stats.kstwo.pdf(x, n)
        ax = sns.lineplot(
            x=x, y=y, markers=False, dashes=False, sort=True, ax=ax, color=canvas.colors.dark_blue
        )
        line = ax.lines[0]
        xdata = line.get_xydata()[:, 0]
        ydata = line.get_xydata()[:, 1]
        # Get index of first value greater than the statistic.
        try:
            idx = np.where(xdata > self.value)[0][0]
            fill_x = xdata[idx:]
            fill_y2 = ydata[idx:]
            ax.fill_between(x=fill_x, y1=0, y2=fill_y2, color=canvas.colors.orange)
        except IndexError:
            pass
        ax.set_title(
            f"Goodness of Fit\nDistributions of {self.sample1.name.capitalize()} of {self.sample2.name.capitalize()}\n{self.result}",
            fontsize=canvas.fontsize_title,
        )

        ax.set_xlabel("Value")
        ax.set_ylabel("Probability Density")
        return ax

    def plothist(self, ax: plt.Axes = None) -> plt.Axes:  # pragma: no cover)
        """Plots the data against the theoretical probability distribution function.

        Args:
            ax (plt.Axes): A matplotlib Axes object. Optional
        """
        canvas = Canvas()
        ax = ax or canvas.ax

        ax = sns.histplot(
            x=self.sample1,
            color=canvas.colors.dark_blue,
            multiple="layer",
            label=self.sample1.name,
            ax=ax,
        )
        ax = sns.histplot(
            x=self.sample2,
            color=canvas.colors.orange,
            multiple="layer",
            label=self.sample2.name,
            ax=ax,
        )

        title = f"Goodness of Fit\nDistributions of {self.sample1.name.capitalize()} of {self.sample2.name.capitalize()}"
        ax.set_title(title, fontsize=canvas.fontsize_title)
        ax.legend()

        return ax


# ------------------------------------------------------------------------------------------------ #
#                                          TEST                                                    #
# ------------------------------------------------------------------------------------------------ #
class KSTwoTest(StatisticalTest):
    __id = "ks2"

    def __init__(self, alpha: float = 0.05) -> None:
        super().__init__()
        self._alpha = alpha
        self._sample1 = None
        self._sample2 = None
        self._profile = StatTestProfileTwo.create(self.__id)
        self._result = None

    @property
    def profile(self) -> StatTestProfile:
        """Returns the statistical test profile."""
        return self._profile

    @property
    def result(self) -> StatTestResult:
        """Returns a Statistical Test Result object."""
        return self._result

    def __call__(self, sample1: pd.Series, sample2: pd.Series) -> None:
        """Performs the statistical test and creates a result object.

        Args:
            sample1 (pd.Series): Pandas series containing first sample
            sample2 (pd.Series): Pandas series containing second sample

        """
        self._sample1 = sample1
        self._sample2 = sample2

        # Conduct the two-sided ks test
        result = stats.ks_2samp(
            sample1.values, sample2.values, alternative="two-sided", method="auto"
        )

        if result.pvalue > self._alpha:
            gtlt = ">"
            inference = f"The pvalue {round(result.pvalue,2)} is greater than level of significance {self._alpha}; therefore, the null hypothesis is not rejected. The distributions are not significantly different."
        else:
            gtlt = "<"
            inference = f"The pvalue {round(result.pvalue,2)} is less than level of significance {self._alpha}; therefore, the null hypothesis is rejected. The distributions are significantly different."

        # Create the result object.
        self._result = KSTwoTestResult(
            test=self._profile.name,
            H0=self._profile.H0,
            statistic=self._profile.statistic,
            hypothesis=self._profile.hypothesis,
            value=result.statistic,
            pvalue=result.pvalue,
            result=f"(KS={round(result.statistic,2)}, p{gtlt}{self._alpha}",
            sample1=sample1,
            sample2=sample2,
            inference=inference,
            alpha=self._alpha,
        )