 
import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

options = VarParsing ('analysis')

# Adding a custom command line option for Pt
options.inputFiles = "root://cmseos.fnal.gov//store/user/cmsdas/2026/short_exercises/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root"  #### for cmslpc
#options.inputFiles = "root://xrootd-cms.infn.it//store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root"  #### for cern
options.register('minPt',
                 20.0, # default value
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.float,
                 "Minimum Muon Pt threshold")

options.parseArguments()

process = cms.Process("Test")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(options.inputFiles)
)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(options.maxEvents)
)

process.analyzeBasicPat = cms.EDAnalyzer("MyZPeakAnalyzer",
    muonSrc = cms.untracked.InputTag("slimmedMuons"),
    elecSrc = cms.untracked.InputTag("slimmedElectrons"),
    # New parameter added here
    minMuonPt = cms.double(options.minPt)
)

process.TFileService = cms.Service("TFileService",
    fileName = cms.string('myZPeak.root')
)

process.p = cms.Path(process.analyzeBasicPat)