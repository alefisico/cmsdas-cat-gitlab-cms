import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

options = VarParsing ('analysis')

process = cms.Process("Test")

process.source = cms.Source("PoolSource",
  fileNames = cms.untracked.vstring (options.inputFiles)
)

process.MessageLogger = cms.Service("MessageLogger")
process.maxEvents = cms.untracked.PSet(
  input = cms.untracked.int32(10000)
)

process.analyzeBasicPat = cms.EDAnalyzer("MyZPeakAnalyzer",
  muonSrc = cms.untracked.InputTag("slimmedMuons"),
  elecSrc = cms.untracked.InputTag("slimmedElectrons"),
)

process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string('myZPeak.root')
                                   )

process.p = cms.Path(process.analyzeBasicPat)
