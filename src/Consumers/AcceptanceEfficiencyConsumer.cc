#include "HiggsAnalysis/KITHiggsToTauTau/interface/Consumers/AcceptanceEfficiencyConsumer.h"

std::string AcceptanceEfficiencyConsumer::GetConsumerId() const
{
	return "AcceptanceEfficiencyConsumer";
}

void AcceptanceEfficiencyConsumer::Init(setting_type const& settings)
{
	acc_eff_hist = new TH2D("acc_eff_hist", "acc_eff_hist", 50,0.,200.,50,0.,200);
	number_of_passed_hist = new TH2D("number_of_passed_hist", "number_of_passed_hist", 50,0.,200.,50,0.,200);
	number_of_entries_hist = new TH2D("number_of_entries_hist", "number_of_entries_hist", 50,0.,200.,50,0.,200);

	LambdaNtupleConsumer<HttTypes>::AddFloatQuantity("accEfficiency",[](event_type const& event, product_type const& product)
	{
		return event.m_genEventInfo->weight;
	});

	LambdaNtupleConsumer<HttTypes>::Init(settings);
}

void AcceptanceEfficiencyConsumer::ProcessFilteredEvent(event_type const& event, product_type const& product, setting_type const& settings)
{
	assert(event.m_genTaus->size() == 2);
	KGenTau leadingTau = event.m_genTaus->at(0);
	KGenTau trailingTau = event.m_genTaus->at(1);

	double PtTau1 = leadingTau.p4.Pt();
	double PtTau2 = trailingTau.p4.Pt();
	double weight = event.m_genEventInfo->weight;

	leadingTauDC = (leadingTau.decayMode != 1 && leadingTau.decayMode != 2) ? 3 : leadingTau.decayMode;
	trailingTauDC = (trailingTau.decayMode != 1 && trailingTau.decayMode != 2) ? 3 : trailingTau.decayMode;

	if(leadingTauDC > trailingTauDC)
	{
		PtTau1 = trailingTau.p4.Pt();
		PtTau2 = leadingTau.p4.Pt();
	}

	for(unsigned int i = 0; i<nAttempts; ++i)
	{
		if ((double(i)/double(nAttempts) < weight) && (weight <=1)) number_of_passed_hist->Fill(PtTau1, PtTau2);
		number_of_entries_hist->Fill(PtTau1, PtTau2);
	}
	LambdaNtupleConsumer<HttTypes>::ProcessFilteredEvent(event, product, settings);
}

void AcceptanceEfficiencyConsumer::Finish(setting_type const& settings)
{
	LambdaNtupleConsumer::Finish(settings);
	RootFileHelper::SafeCd(settings.GetRootOutFile(), settings.GetRootFileFolder());
	acc_eff_hist->Divide(number_of_passed_hist,number_of_entries_hist,1.,1.,"B");
	number_of_passed_hist->Write();
	number_of_entries_hist->Write();
	acc_eff_hist->Write();
}
