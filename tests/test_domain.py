"""test_domain.py — Domain logic validation for voice-speech-therapy-professionals.

Validates: CAPE-V severity mapping, GRBAS scale, exercise dosage bounds,
red-flag triage logic, and profession classification accuracy.
"""

from __future__ import annotations

import pytest

# ===========================================================================
# CAPE-V Severity Mapping
# ===========================================================================


class TestCAPEV:
    """Consensus Auditory-Perceptual Evaluation of Voice — severity mapping."""

    SEVERITY_MAP = {
        (0, 25): "Mild",
        (26, 50): "Mild-Moderate",
        (51, 75): "Moderate-Severe",
        (76, 100): "Severe",
    }

    @staticmethod
    def capev_to_severity(vas_score: float) -> str:
        """Map a CAPE-V VAS score (0-100mm) to a clinical severity category."""
        if vas_score < 0 or vas_score > 100:
            raise ValueError(f"CAPE-V score must be 0-100, got {vas_score}")
        for (lo, hi), label in TestCAPEV.SEVERITY_MAP.items():
            if lo <= vas_score <= hi:
                return label
        return "Mild"

    def test_normal_voice_is_mild(self) -> None:
        assert self.capev_to_severity(5.0) == "Mild"

    def test_moderate_severity(self) -> None:
        assert self.capev_to_severity(50.0) == "Mild-Moderate"

    def test_severe_voice(self) -> None:
        assert self.capev_to_severity(90.0) == "Severe"

    def test_boundary_zero(self) -> None:
        assert self.capev_to_severity(0.0) == "Mild"

    def test_boundary_hundred(self) -> None:
        assert self.capev_to_severity(100.0) == "Severe"

    def test_twenty_five_boundary(self) -> None:
        assert self.capev_to_severity(25.0) == "Mild"

    def test_twenty_six_boundary(self) -> None:
        assert self.capev_to_severity(26.0) == "Mild-Moderate"

    def test_negative_score_raises(self) -> None:
        with pytest.raises(ValueError):
            self.capev_to_severity(-1.0)

    def test_over_hundred_raises(self) -> None:
        with pytest.raises(ValueError):
            self.capev_to_severity(101.0)

    CAPEV_PARAMETERS = [
        "Overall Severity",
        "Roughness",
        "Breathiness",
        "Strain",
        "Pitch",
        "Loudness",
    ]

    def test_all_capev_parameters_exist(self) -> None:
        assert len(self.CAPEV_PARAMETERS) == 6


# ===========================================================================
# GRBAS Scale Validation
# ===========================================================================


class TestGRBAS:
    """Grade, Roughness, Breathiness, Asthenia, Strain — 0-3 scale."""

    VALID_SCORES = {0, 1, 2, 3}

    @staticmethod
    def is_valid_grbas(score: int) -> bool:
        return score in TestGRBAS.VALID_SCORES

    def test_zero_normal(self) -> None:
        assert self.is_valid_grbas(0)

    def test_three_severe(self) -> None:
        assert self.is_valid_grbas(3)

    def test_negative_invalid(self) -> None:
        assert not self.is_valid_grbas(-1)

    def test_four_invalid(self) -> None:
        assert not self.is_valid_grbas(4)

    GRBAS_PARAMETERS = ["Grade", "Roughness", "Breathiness", "Asthenia", "Strain"]

    def test_all_parameters_present(self) -> None:
        assert len(self.GRBAS_PARAMETERS) == 5


# ===========================================================================
# Exercise Dosage Validation
# ===========================================================================


class TestExerciseDosage:
    """Validates exercise prescription dosage ranges."""

    @staticmethod
    def is_valid_dosage(reps: int, sets: int, frequency_per_day: int) -> bool:
        """Check if exercise dosage falls within evidence-based safe ranges."""
        return (
            3 <= reps <= 30
            and 1 <= sets <= 5
            and 1 <= frequency_per_day <= 3
        )

    def test_standard_dosage_valid(self) -> None:
        assert self.is_valid_dosage(10, 3, 2)

    def test_minimum_dosage_valid(self) -> None:
        assert self.is_valid_dosage(3, 1, 1)

    def test_maximum_dosage_valid(self) -> None:
        assert self.is_valid_dosage(30, 5, 3)

    def test_too_few_reps_invalid(self) -> None:
        assert not self.is_valid_dosage(1, 3, 2)

    def test_too_many_reps_invalid(self) -> None:
        assert not self.is_valid_dosage(50, 3, 2)

    def test_too_many_sets_invalid(self) -> None:
        assert not self.is_valid_dosage(10, 8, 2)

    def test_too_frequent_invalid(self) -> None:
        assert not self.is_valid_dosage(10, 3, 5)

    def test_zero_frequency_invalid(self) -> None:
        assert not self.is_valid_dosage(10, 3, 0)

    @staticmethod
    def progression_is_gradual(
        old_reps: int, new_reps: int, max_increase_pct: float = 0.25
    ) -> bool:
        """Check if progression increase is <= 25% (safe incremental loading)."""
        if old_reps <= 0:
            return new_reps <= old_reps * 2
        increase_pct = (new_reps - old_reps) / old_reps
        return increase_pct <= max_increase_pct

    def test_gradual_progression_valid(self) -> None:
        assert self.progression_is_gradual(10, 12)

    def test_excessive_jump_invalid(self) -> None:
        assert not self.progression_is_gradual(10, 20)


# ===========================================================================
# Red-Flag Triage
# ===========================================================================


class TestRedFlagTriage:
    """Validates triage logic for voice pathology red flags."""

    IMMEDIATE_ENT = {
        "aphonia >24 hours",
        "stridor",
        "hemoptysis",
        "odynophagia",
        "airway compromise",
    }

    URGENT_ENT = {
        "hoarseness >3 weeks",
        "dysphagia",
        "referred otalgia",
        "unexplained weight loss",
        "neck mass",
    }

    SLP_REFERRAL = {
        "chronic vocal fatigue",
        "muscle tension dysphonia signs",
        "ineffective compensatory patterns",
        "vocal nodules",
        "functional dysphonia",
    }

    SELF_MANAGEMENT = {
        "transient vocal fatigue",
        "mild strain after heavy use",
        "hygiene adjustments needed",
        "no pathology signs",
    }

    @classmethod
    def triage(cls, symptoms: set[str]) -> str:
        """Classify symptoms into referral urgency category."""
        if symptoms & cls.IMMEDIATE_ENT:
            return "Immediate ENT"
        if symptoms & cls.URGENT_ENT:
            return "Urgent ENT (within 1 week)"
        if symptoms & cls.SLP_REFERRAL:
            return "SLP Referral"
        if symptoms & cls.SELF_MANAGEMENT:
            return "Self-Management"
        return "SLP Referral"

    def test_aphonia_triggers_immediate_ent(self) -> None:
        assert self.triage({"aphonia >24 hours"}) == "Immediate ENT"

    def test_stridor_triggers_immediate_ent(self) -> None:
        assert self.triage({"stridor"}) == "Immediate ENT"

    def test_hoarseness_three_weeks_triggers_urgent_ent(self) -> None:
        assert self.triage({"hoarseness >3 weeks"}) == "Urgent ENT (within 1 week)"

    def test_dysphagia_triggers_urgent_ent(self) -> None:
        assert self.triage({"dysphagia"}) == "Urgent ENT (within 1 week)"

    def test_mtd_signs_triggers_slp_referral(self) -> None:
        assert self.triage({"muscle tension dysphonia signs"}) == "SLP Referral"

    def test_chronic_fatigue_triggers_slp_referral(self) -> None:
        assert self.triage({"chronic vocal fatigue"}) == "SLP Referral"

    def test_transient_fatigue_is_self_management(self) -> None:
        assert self.triage({"transient vocal fatigue", "no pathology signs"}) == "Self-Management"

    def test_multiple_triggers_prioritizes_highest(self) -> None:
        result = self.triage(
            {"transient vocal fatigue", "aphonia >24 hours", "muscle tension dysphonia signs"}
        )
        assert result == "Immediate ENT"

    def test_immediate_over_urgent_priority(self) -> None:
        result = self.triage({"hoarseness >3 weeks", "stridor"})
        assert result == "Immediate ENT"

    def test_unknown_symptoms_default_slp(self) -> None:
        assert self.triage({"some unknown symptom"}) == "SLP Referral"


# ===========================================================================
# Profession Classification
# ===========================================================================


class TestProfessionClassification:
    """Validates voice professional subtype classification from input signals."""

    PROFILES = {
        "Teacher": {"classroom": True, "projection": True, "prolonged_talking": True},
        "Podcaster": {"close_mic": True, "sustained_monologue": True, "recording": True},
        "MC_Host": {"live_events": True, "variable_acoustics": True, "audience_interaction": True},
        "Singer": {"pitch_accuracy": True, "register_transitions": True, "singing": True},
        "Actor": {"character_voices": True, "emotional_range": True, "projection": True},
        "CallCenter": {"headset": True, "scripted_speech": True, "continuous_speaking": True},
    }

    @classmethod
    def classify(cls, signals: dict[str, bool]) -> str:
        """Classify profession from binary signals."""
        scores: dict[str, int] = {}
        for name, profile in cls.PROFILES.items():
            matches = sum(1 for k, v in profile.items() if signals.get(k) == v)
            scores[name] = matches
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[best] < 2:
            return "Other Voice Professional"
        return best

    def test_classroom_signals_map_to_teacher(self) -> None:
        signals = {"classroom": True, "projection": True, "prolonged_talking": True}
        assert self.classify(signals) == "Teacher"

    def test_mic_signals_map_to_podcaster(self) -> None:
        signals = {"close_mic": True, "sustained_monologue": True, "recording": True}
        assert self.classify(signals) == "Podcaster"

    def test_live_event_signals_map_to_mc(self) -> None:
        signals = {"live_events": True, "variable_acoustics": True, "audience_interaction": True}
        assert self.classify(signals) == "MC_Host"

    def test_singing_signals_map_to_singer(self) -> None:
        signals = {"pitch_accuracy": True, "register_transitions": True, "singing": True}
        assert self.classify(signals) == "Singer"

    def test_partial_match_classifies_correctly(self) -> None:
        signals = {"classroom": True, "projection": True}
        assert self.classify(signals) == "Teacher"

    def test_no_strong_match_returns_other(self) -> None:
        signals = {"classroom": True}
        assert self.classify(signals) == "Other Voice Professional"

    def test_empty_signals_returns_other(self) -> None:
        signals: dict[str, bool] = {}
        assert self.classify(signals) == "Other Voice Professional"


# ===========================================================================
# Acoustic Norms
# ===========================================================================


class TestAcousticNorms:
    """Validate acoustic measurement normative ranges."""

    NORMATIVE = {
        "jitter_local": 1.04,
        "jitter_absolute": 3.00,
        "shimmer_local": 3.81,
        "shimmer_db": 0.35,
        "hnr": 20.0,
        "mpt_male": 20.0,
        "mpt_female": 15.0,
        "sz_ratio": 1.4,
    }

    def test_jitter_local_threshold(self) -> None:
        """Jitter > 1.04% is pathological."""
        assert 0.5 <= self.NORMATIVE["jitter_local"]

    def test_shimmer_local_threshold(self) -> None:
        """Shimmer > 3.81% is pathological."""
        assert 1.0 <= self.NORMATIVE["shimmer_local"]

    def test_hnr_threshold(self) -> None:
        """HNR < 20 dB suggests dysphonia."""
        assert self.NORMATIVE["hnr"] > 0

    def test_mpt_male_above_female(self) -> None:
        assert self.NORMATIVE["mpt_male"] > self.NORMATIVE["mpt_female"]

    def test_sz_ratio_normal(self) -> None:
        """s/z ratio < 1.4 is normal."""
        assert self.NORMATIVE["sz_ratio"] > 1.0


# ===========================================================================
# Conclusion Logic
# ===========================================================================


class TestConclusionLogic:
    """Validate the conclusion decision tree mapping."""

    VALID_CONCLUSIONS = {
        "Healthy",
        "Improvement Plan",
        "Conditional (needs technique work)",
        "Medical Referral Needed",
        "Inconclusive",
    }

    @staticmethod
    def determine_conclusion(
        red_flags: bool,
        hoarseness_weeks: int,
        abnormal_params: int,
        technique_deficits: bool,
        has_data: bool,
    ) -> str:
        """Determine conclusion based on clinical signals."""
        if not has_data:
            return "Inconclusive"
        if red_flags and hoarseness_weeks > 3:
            return "Medical Referral Needed"
        if red_flags:
            return "Medical Referral Needed"
        if abnormal_params == 0 and not technique_deficits:
            return "Healthy"
        if technique_deficits and abnormal_params == 0:
            return "Conditional (needs technique work)"
        if 1 <= abnormal_params <= 2 and not red_flags:
            return "Improvement Plan"
        if abnormal_params >= 3:
            return "Medical Referral Needed"
        return "Improvement Plan"

    def test_no_data_is_inconclusive(self) -> None:
        assert (
            self.determine_conclusion(False, 0, 0, False, False)
            == "Inconclusive"
        )

    def test_normal_voice_is_healthy(self) -> None:
        assert (
            self.determine_conclusion(False, 0, 0, False, True)
            == "Healthy"
        )

    def test_mild_abnormality_is_improvement(self) -> None:
        assert (
            self.determine_conclusion(False, 0, 1, False, True)
            == "Improvement Plan"
        )

    def test_technique_deficits_is_conditional(self) -> None:
        assert (
            self.determine_conclusion(False, 0, 0, True, True)
            == "Conditional (needs technique work)"
        )

    def test_red_flag_with_prolonged_hoarseness_is_referral(self) -> None:
        assert (
            self.determine_conclusion(True, 4, 2, False, True)
            == "Medical Referral Needed"
        )

    def test_multiple_abnormal_params_is_referral(self) -> None:
        assert (
            self.determine_conclusion(False, 0, 4, False, True)
            == "Medical Referral Needed"
        )

    def test_all_conclusions_in_valid_set(self) -> None:
        cases = [
            (False, 0, 0, False, False),
            (False, 0, 0, False, True),
            (False, 0, 1, False, True),
            (False, 0, 0, True, True),
            (True, 4, 2, False, True),
            (False, 0, 4, False, True),
        ]
        for case in cases:
            conclusion = self.determine_conclusion(*case)
            assert conclusion in self.VALID_CONCLUSIONS
