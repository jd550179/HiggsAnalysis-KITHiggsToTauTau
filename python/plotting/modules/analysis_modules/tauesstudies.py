# -*- coding: utf-8 -*-

import logging
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)

import array
import copy
import hashlib
import math

import sys
import ROOT

import Artus.HarryPlotter.analysisbase as analysisbase
import Artus.HarryPlotter.utility.roottools as roottools

class TauEsStudies(analysisbase.AnalysisBase):
	"""TauEsStudies for comparing histograms"""

	def __init__(self):
		super(TauEsStudies, self).__init__()

	def modify_argument_parser(self, parser, args):
		super(TauEsStudies, self).modify_argument_parser(parser, args)
		
		self.tauesstudies_options = parser.add_argument_group("TauEsStudies options")
		self.tauesstudies_options.add_argument(
				"--data-nicks", nargs="+",
				help="Nick names (whitespace separated) of data"
		)
		self.tauesstudies_options.add_argument(
				"--ztt-nicks", nargs="+",
				help="Nick names (whitespace separated) of ztt with shifts"
		)
		self.tauesstudies_options.add_argument(
				"--es-shifts", nargs="+",
				help="ES shifts (whitespace separated)"
		)
		self.tauesstudies_options.add_argument(
				"--res-hist-nick", nargs="+",
				help="Nick name of resulting histogram"
		)
		self.tauesstudies_options.add_argument(
				"--roofit-flag", default=False, action="store_true",
	                    help="Use roofit likelihood scan instead of chi2 test"
	    )

	def prepare_args(self, parser, plotData):
		super(TauEsStudies, self).prepare_args(parser, plotData)
		self.prepare_list_args(plotData, ["data_nicks", "ztt_nicks","es_shifts","res_hist_nick"])

		for index, (data_nicks, ztt_nicks, es_shifts, res_hist_nick) in enumerate(zip(
				*[plotData.plotdict[k] for k in ["data_nicks", "ztt_nicks","es_shifts","res_hist_nick"]]
		)):
			plotData.plotdict["data_nicks"][index] = data_nicks.split()
			plotData.plotdict["ztt_nicks"][index] = ztt_nicks.split()
			plotData.plotdict["es_shifts"][index] = es_shifts.split()

			if not plotData.plotdict["res_hist_nick"][index] in plotData.plotdict["nicks"]:
				plotData.plotdict["nicks"].insert(
					plotData.plotdict["nicks"].index(plotData.plotdict["ztt_nicks"][index][0]),
					plotData.plotdict["res_hist_nick"][index]
				)

	def run(self, plotData=None):
		super(TauEsStudies, self).run(plotData)

		if plotData.plotdict["roofit_flag"]:
			print "Start Roofit Likelihood Scan ..."

			es_shifts=[]

			# negative log likelihood list
			nll_list = []

			# always set this to stop ROOT doing odd things
			ROOT.PyConfig.IgnoreCommandLineOptions = True
			ROOT.gROOT.SetBatch(ROOT.kTRUE)

			# Have to define the "x-axis" variable
			mass = ROOT.RooRealVar('mass', 'mass', 0, 2)

			for index, (data_nick, ztt_nick, es_shift) in enumerate(zip(
					*[plotData.plotdict[k] for k in ["data_nicks", "ztt_nicks","es_shifts"]]
			)):
				es_shifts.append(float(es_shift[0]))

				# Convert the data minus bkg TH1 into a RooDataHist
				data_nobkg_th1 = plotData.plotdict["root_objects"][data_nick[0]]
				data_nobkg_rdh = ROOT.RooDataHist(data_nobkg_th1.GetName(), data_nobkg_th1.GetName(), ROOT.RooArgList(mass), ROOT.RooFit.Import(data_nobkg_th1, False))

				# Convert the ztt TH1 into RooDataHist
				ztt_th1 = plotData.plotdict["root_objects"][ztt_nick[0]]
				ztt_rdh = ROOT.RooDataHist(ztt_th1.GetName(), ztt_th1.GetName(), ROOT.RooArgList(mass), ROOT.RooFit.Import(ztt_th1, False))

				# Create PDF
				ztt_pdf = ROOT.RooHistPdf(ztt_th1.GetName()+'_pdf', ztt_th1.GetName(), ROOT.RooArgSet(mass), ztt_rdh)
				ztt_norm = ROOT.RooRealVar(ztt_th1.GetName()+'_norm', ztt_th1.GetName(), ztt_th1.Integral(), ztt_th1.Integral()/2., ztt_th1.Integral()*2.)

				# Create RooArgLists for the resulting PDF
				ztt_pdf_list = ROOT.RooArgList()
				ztt_norm_list = ROOT.RooArgList()
				ztt_pdf_list.add(ztt_pdf)
				ztt_norm_list.add(ztt_norm)

				# Create resulting ztt PDF
				res_pdf = ROOT.RooAddPdf('pdf', 'pdf', ztt_pdf_list, ztt_norm_list)

				# Do the fit
				res = res_pdf.fitTo(data_nobkg_rdh, ROOT.RooFit.Extended(), ROOT.RooFit.Save(), ROOT.RooFit.Minimizer('Minuit2', 'migrad'))
				nll_list.append(res.minNll())

			for nll in nll_list:
				print nll

			for res_hist_nick in zip(
					*[plotData.plotdict["res_hist_nick"]]
			):
				#Graph
				RooFitGraph = ROOT.TGraphErrors(
						len(es_shifts),
						array.array("d", es_shifts), array.array("d", nll_list)
				)
				plotData.plotdict.setdefault("root_objects", {})[res_hist_nick[0]] = RooFitGraph

				plotData.plotdict["root_objects"][res_hist_nick[0]].SetName(res_hist_nick[0])
				plotData.plotdict["root_objects"][res_hist_nick[0]].SetTitle("")

				#Fit function
				fitf = ROOT.TF1("f1","[0] + [1]*(x-[2])*(x-[2])",min(es_shifts),max(es_shifts))
				#fitf.SetParLimits(0,0,1000000)
				#fitf.SetParLimits(1,0,1000000)
				fitf.SetParLimits(2,min(es_shifts),max(es_shifts))
				RooFitGraph.Fit("f1","R")

				#get minimum
				print "Minimum of fitfunction at: ", fitf.GetMinimumX(min(es_shifts),max(es_shifts))

		else:
			print "Start Chi2 fit ..."

			es_shifts=[]
			chi2res=[]

			for index, (data_nick, ztt_nick, es_shift) in enumerate(zip(
					*[plotData.plotdict[k] for k in ["data_nicks", "ztt_nicks","es_shifts"]]
			)):
				#print "chi2test between ", data_nick, " and ", ztt_nick
				es_shifts.append(float(es_shift[0]))
				chi2res.extend([plotData.plotdict["root_objects"][ztt_nick[0]].Chi2Test(plotData.plotdict["root_objects"][data_nick[0]], "CHI2")])

				if index == 0:
					chi2min = chi2res[0]
					min_shift = es_shifts[0]
				if chi2min > chi2res[index]:
					chi2min = chi2res[index]
					min_shift = es_shifts[index]

			for x_value, y_value in zip(es_shifts, chi2res):
				print "Shift: ", x_value, " Chi2Val: ", y_value

			print "Minimum found at: ", min_shift

			for res_hist_nick in zip(
					*[plotData.plotdict["res_hist_nick"]]
			):

				#Graph
				Chi2Graph = ROOT.TGraphErrors(
						len(es_shifts),
						array.array("d", es_shifts), array.array("d", chi2res)
				)
				plotData.plotdict.setdefault("root_objects", {})[res_hist_nick[0]] = Chi2Graph

				plotData.plotdict["root_objects"][res_hist_nick[0]].SetName(res_hist_nick[0])
				plotData.plotdict["root_objects"][res_hist_nick[0]].SetTitle("")

				#Fit function
				fit2chi = ROOT.TF1("f1","[0] + [1]*(x-[2])*(x-[2])",min(es_shifts),max(es_shifts))
				fit2chi.SetParLimits(0,0,1000000)
				fit2chi.SetParLimits(1,0,1000000)
				fit2chi.SetParLimits(2,min(es_shifts),max(es_shifts))
				Chi2Graph.Fit("f1","R")

				#get minimum
				print "Minimum of fitfunction at: ", fit2chi.GetMinimumX(min(es_shifts),max(es_shifts))
