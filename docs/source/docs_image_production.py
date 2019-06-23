
import matplotlib.pyplot as plt
from numpy import linspace, sqrt, pi, array
from numpy.random import normal, seed

from inference.mcmc import PcaChain

"""
This is a duplicate of /demos/spectroscopy_demo.py which produces
example figures for the documentation
"""



class SpectroPosterior(object):
    def __init__(self, wavelength, intensity, errors):
        self.x = wavelength
        self.y = intensity
        self.sigma = errors
        # Central wavelengths of the lines are known constants:
        self.c1 = 422.
        self.c2 = 428.

    def __call__(self, theta):
        return self.likelihood(theta) + self.prior(theta)

    def prior(self, theta):
        return 0.

    def likelihood(self, theta):
        return -0.5*sum( ((self.y - self.forward_model(self.x, theta)) / self.sigma)**2 )

    def forward_model(self, x, theta):
        # unpack the model parameters
        A1, w1, A2, w2, b0, b1 = theta
        # evaluate each term of the model
        peak_1 = (A1 / (pi*w1)) / (1 + ((x - self.c1)/w1)**2)
        peak_2 = (A2 / (pi*w2)) / (1 + ((x - self.c2)/w2)**2)
        d = (b1-b0)/(max(x) - min(x))
        background = d*x + (b0 - d*min(x))
        # return the prediction of the data
        return peak_1 + peak_2 + background




def build_plots():
    # Create some simulated data
    seed(9)
    N = 35
    x_data = linspace(410, 440, N)
    P = SpectroPosterior(x_data, None, None)
    theta = [1000, 2, 400, 1.5, 35, 25]
    y_data = P.forward_model(x_data, theta)
    errors = sqrt(y_data + 1) + 5
    y_data += normal(size = N) * errors




    # plot the simulated data we're going to use
    plt.errorbar(x_data, y_data, errors, marker = 'D', ls = 'none', markersize = 4)
    plt.plot(x_data, y_data, alpha = 0.5, c = 'C0', ls = 'dashed')
    plt.title('synthetic spectroscopy data')
    plt.xlabel('wavelength (nm)')
    plt.ylabel('intensity')
    plt.grid()
    plt.tight_layout()
    plt.savefig('spectroscopy_data.png')
    plt.close()


    # create the posterior object
    posterior = SpectroPosterior(x_data, y_data, errors)

    # create the markov chain object
    chain = PcaChain( posterior = posterior, start = [1000, 1, 1000, 1, 30, 30] )

    # generate a sample by advancing the chain
    chain.advance(20000)

    # we can check the status of the chain using the plot_diagnostics method
    chain.plot_diagnostics(show = False, filename = 'plot_diagnostics_example.png')

    # We can automatically set sensible burn and thin values for the sample
    chain.autoselect_burn_and_thin()

    # we can get a quick overview of the posterior using the matrix_plot
    # functionality of chain objects, which plots all possible 1D & 2D
    # marginal distributions of the full parameter set (or a chosen sub-set).
    chain.thin = 1
    chain.matrix_plot(show = False, filename = 'matrix_plot_example.png')

    # We can easily estimate 1D marginal distributions for any parameter
    # using the get_marginal method:
    w1_pdf = chain.get_marginal(1, unimodal = True)
    w2_pdf = chain.get_marginal(3, unimodal = True)

    # get_marginal returns a density estimator object, which can be called
    ax = linspace(0.2, 4., 1000)  # build an axis to evaluate the pdf estimates
    plt.plot(ax, w1_pdf(ax), label = 'peak #1 width marginal', lw = 2)  # plot estimates of each marginal PDF
    plt.plot(ax, w2_pdf(ax), label = 'peak #2 width marginal', lw = 2)
    plt.xlabel('peak width')
    plt.ylabel('probability density')
    plt.legend()
    plt.grid()
    plt.savefig('width_pdfs_example.png')
    plt.close()






    # what if instead we wanted a PDF for the ratio of the two widths?
    # get the sample for each width
    width_1 = chain.get_parameter(1)
    width_2 = chain.get_parameter(3)

    # make a new set of samples for the ratio
    widths_ratio = [i/j for i,j in zip(width_1, width_2)]

    # Use one of the density estimator objects from pdf_tools to get the PDF
    from inference.pdf_tools import UnimodalPdf
    pdf = UnimodalPdf(widths_ratio)

    # plot the PDF
    pdf.plot_summary(label = 'Peak widths ratio', show = False, filename = 'pdf_summary_example.png')






    # You may also want to assess the level of uncertainty in the model predictions.
    # This can be done easily by passing each sample through the forward-model
    # and observing the distribution of model expressions that result.

    # However rather than taking the entire sample, it is better to take a sub-sample
    # which corresponds to some credible interval. For example, the 95% credible interval
    # sub sample can be generated by taking the 95% of samples which have the highest
    # associated probabilities.

    # Markov-chain objects have a method for this called get_interval():
    interval_sample, interval_probs = chain.get_interval(samples = 1500)
    # by default the interval is 95%, but any fraction can be used using a keyword argument.

    # generate an axis on which to evaluate the model
    M = 500
    x_fits = linspace(410, 440, M)

    # now evaluate the model for each sample
    models = []
    for theta in interval_sample:
        curve = posterior.forward_model(x_fits, theta)
        models.append(curve)
    models = array(models)

    # calculate the 95% envelope
    upper_bound = models.max(axis = 0)
    lower_bound = models.min(axis = 0)

    # also want to evaluate the most probable model using the mode:
    mode = posterior.forward_model(x_fits, chain.mode())

    # construct the plot
    # plt.figure(figsize = (10,7.5))
    # plt.plot(x_fits, mode, c = 'C2', lw = 2, label = 'mode')
    # plt.plot(x_fits, lower_bound, ls = 'dashed', c = 'red', lw = 2, label = '95% envelope')
    # plt.plot(x_fits, upper_bound, ls = 'dashed', c = 'red', lw = 2)
    # plt.plot( x_data, y_data, 'D', c = 'blue', markeredgecolor = 'black', markersize = 4, label = 'data')
    # plt.title('Forward model 95% interval')
    # plt.xlabel('wavelength (nm)')
    # plt.ylabel('intensity')
    # plt.legend()
    # plt.grid()
    # plt.show()