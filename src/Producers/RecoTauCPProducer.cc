
#include "Artus/Consumer/interface/LambdaNtupleConsumer.h"
#include "Artus/KappaAnalysis/interface/KappaTypes.h"

#include "HiggsAnalysis/KITHiggsToTauTau/interface/HttEnumTypes.h"
#include "HiggsAnalysis/KITHiggsToTauTau/interface/Utility/CPQuantities.h"
#include "HiggsAnalysis/KITHiggsToTauTau/interface/Producers/RecoTauCPProducer.h"


std::string RecoTauCPProducer::GetProducerId() const
{
	return "RecoTauCPProducer";
}

void RecoTauCPProducer::Init(setting_type const& settings)
{
	ProducerBase<HttTypes>::Init(settings);
	
	//adding possible quantities for the lambda ntuples consumers
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoPhiStarCP", [](event_type const& event, product_type const& product)
	{
		return product.m_recoPhiStarCP;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoPhiStarCPrPV", [](event_type const& event, product_type const& product)
	{
		return product.m_recoPhiStarCPrPV;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoPhiStarCPrPVbs", [](event_type const& event, product_type const& product)
	{
		return product.m_recoPhiStarCPrPVbs;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoPhiStar", [](event_type const& event, product_type const& product)
	{
		return product.m_recoPhiStar;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoChargedHadron1HiggsFrameEnergy", [](event_type const& event, product_type const& product)
	{
		return product.m_recoChargedHadronEnergies.first;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoChargedHadron2HiggsFrameEnergy", [](event_type const& event, product_type const& product)
	{
		return product.m_recoChargedHadronEnergies.second;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoImpactParameter1", [](event_type const& event, product_type const& product)
	{
		return product.m_recoIP1;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoImpactParameter2", [](event_type const& event, product_type const& product)
	{
		return product.m_recoIP2;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoTrackRefError1", [](event_type const& event, product_type const& product)
	{
		return product.m_recoTrackRefError1;
	});
	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("recoTrackRefError2", [](event_type const& event, product_type const& product)
	{
		return product.m_recoTrackRefError2;
	});
}

void RecoTauCPProducer::Produce(event_type const& event, product_type& product, setting_type const& settings) const
{
	assert(event.m_vertexSummary);
	assert(product.m_flavourOrderedLeptons.size() >= 2);
	
	KTrack trackP = product.m_chargeOrderedLeptons[0]->track;
	KTrack trackM = product.m_chargeOrderedLeptons[1]->track;
	RMFLV momentumP = ((product.m_chargeOrderedLeptons[0]->flavour() == KLeptonFlavour::TAU) ? static_cast<KTau*>(product.m_chargeOrderedLeptons[0])->chargedHadronCandidates.at(0).p4 : product.m_chargeOrderedLeptons[0]->p4);
	RMFLV momentumM = ((product.m_chargeOrderedLeptons[1]->flavour() == KLeptonFlavour::TAU) ? static_cast<KTau*>(product.m_chargeOrderedLeptons[1])->chargedHadronCandidates.at(0).p4 : product.m_chargeOrderedLeptons[1]->p4);
	
	CPQuantities cpq;
	product.m_recoPhiStarCP = cpq.CalculatePhiStarCP(event.m_vertexSummary->pv, trackP, trackM, momentumP, momentumM);
	//product.m_recoPhiStarCPrPV = cpq.CalculatePhiStarCP(event.m_refitVertexSummary->pv, trackP, trackM, momentumP, momentumM);
	//product.m_recoPhiStarCPrPVbs = cpq.CalculatePhiStarCP(event.m_refitVertexBSSummary->pv, trackP, trackM, momentumP, momentumM);
	
	product.m_recoPhiStar = cpq.GetRecoPhiStar();
	product.m_recoIP1 = cpq.GetRecoIP1();
	product.m_recoIP2 = cpq.GetRecoIP2();
	product.m_recoChargedHadronEnergies.first = cpq.CalculateChargedHadronEnergy(product.m_diTauSystem, momentumP);
	product.m_recoChargedHadronEnergies.second = cpq.CalculateChargedHadronEnergy(product.m_diTauSystem, momentumM);
	product.m_recoTrackRefError1 = cpq.CalculateTrackReferenceError(trackP);
	product.m_recoTrackRefError2 = cpq.CalculateTrackReferenceError(trackM);
}
