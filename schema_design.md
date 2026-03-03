# Part 2 – Metadata Schema Design

## Proposed YAML Metadata File

The following YAML file is designed to accompany the **nominal** weight file (`multifold.h5`).
It fills every gap identified in Part 1's gap analysis - provenance, phase space, observable
definitions, weight semantics, iteration details, file linkage, and reproducibility information.

> **Note:** Placeholder values (e.g. `"X.X.X"`) indicate information that must be filled in by
> the original analysts; the *structure* is what this design exercise is about.

```yaml
# ═══════════════════════════════════════════════════════════════
# OmniFold Unfolding Result - Metadata
# Accompanies: multifold.h5 (nominal weight file)
# ═══════════════════════════════════════════════════════════════

schema_version: "1.0"


# ─── Dataset & Provenance ─────────────────────────────────────
# Fills Gap (a): experiment/dataset provenance

dataset:
  experiment: "ATLAS"
  data_taking_period: "Run 2 (2015–2018)"
  integrated_luminosity:
    value: 139.0
    unit: "fb⁻¹"
  process: "Z+jets → ℓ⁺ℓ⁻ + jets"
  sqrt_s:
    value: 13
    unit: "TeV"
  references:
    paper: "arXiv:XXXX.XXXXX"
    hepdata: "https://www.hepdata.net/record/insXXXXXXX"
    zenodo: "https://zenodo.org/records/11507450"


# ─── Monte Carlo Generator ────────────────────────────────────
# Fills Gap (a): which MC generator, version, settings

mc_generator:
  name: "MadGraph5_aMC@NLO"
  version: "X.X.X"
  process_card: "p p > z j, z > l+ l-"
  pdf_set: "NNPDF3.1 NNLO"
  shower: "Pythia 8"
  shower_version: "8.XXX"
  detector_simulation: "Geant4 (ATLAS full simulation)"


# ─── Event Selection / Phase Space ────────────────────────────
# Fills Gap (b): phase space and selection cuts

event_selection:
  level: "detector"               # "detector", "particle", or "parton"
  description: >
    Dilepton Z+jets selection with a high-pT Z boson requirement.
    Events must contain at least one anti-kT R=0.4 track-jet.
  cuts:
    - variable: "pT_ll"
      operator: ">"
      value: 200
      unit: "GeV"
      description: "Transverse momentum of the Z boson"

    - variable: "pT_l1"
      operator: ">"
      value: 27
      unit: "GeV"
      description: "Leading lepton pT (trigger threshold)"

    - variable: "abs(eta_l1)"
      operator: "<"
      value: 2.4
      description: "Leading lepton pseudorapidity acceptance"

    - variable: "abs(eta_l2)"
      operator: "<"
      value: 2.4
      description: "Sub-leading lepton pseudorapidity acceptance"

    - variable: "n_trackjets"
      operator: ">="
      value: 1
      description: "At least one track-jet required"


# ─── Observable Definitions ───────────────────────────────────
# Fills Gap (c): units, definitions, and valid ranges

observables:
  - name: "pT_ll"
    description: "Transverse momentum of the dilepton (Z boson) system"
    unit: "GeV"
    dtype: "float32"
    valid_range: [200, null]

  - name: "pT_l1"
    description: "Transverse momentum of the leading lepton"
    unit: "GeV"
    dtype: "float32"

  - name: "pT_l2"
    description: "Transverse momentum of the sub-leading lepton"
    unit: "GeV"
    dtype: "float32"

  - name: "eta_l1"
    description: "Pseudorapidity of the leading lepton"
    unit: null
    dtype: "float32"
    valid_range: [-2.4, 2.4]

  - name: "eta_l2"
    description: "Pseudorapidity of the sub-leading lepton"
    unit: null
    dtype: "float32"
    valid_range: [-2.4, 2.4]

  - name: "phi_l1"
    description: "Azimuthal angle of the leading lepton"
    unit: "rad"
    dtype: "float32"
    valid_range: [-3.14159, 3.14159]

  - name: "phi_l2"
    description: "Azimuthal angle of the sub-leading lepton"
    unit: "rad"
    dtype: "float32"
    valid_range: [-3.14159, 3.14159]

  - name: "y_ll"
    description: "Rapidity of the dilepton (Z boson) system"
    unit: null
    dtype: "float32"

  - name: "pT_trackj1"
    description: "Transverse momentum of the leading track-jet"
    unit: "GeV"
    dtype: "float32"

  - name: "y_trackj1"
    description: "Rapidity of the leading track-jet"
    unit: null
    dtype: "float32"

  - name: "phi_trackj1"
    description: "Azimuthal angle of the leading track-jet"
    unit: "rad"
    dtype: "float32"

  - name: "m_trackj1"
    description: "Invariant mass of the leading track-jet"
    unit: "GeV"
    dtype: "float32"

  - name: "tau1_trackj1"
    description: "1-subjettiness (τ₁) of the leading track-jet"
    unit: null
    dtype: "float32"
    algorithm:
      name: "N-subjettiness"
      reference: "arXiv:1011.2268"

  - name: "tau2_trackj1"
    description: "2-subjettiness (τ₂) of the leading track-jet"
    unit: null
    dtype: "float32"

  - name: "tau3_trackj1"
    description: "3-subjettiness (τ₃) of the leading track-jet"
    unit: null
    dtype: "float32"

  - name: "pT_trackj2"
    description: "Transverse momentum of the sub-leading track-jet"
    unit: "GeV"
    dtype: "float32"

  - name: "y_trackj2"
    description: "Rapidity of the sub-leading track-jet"
    unit: null
    dtype: "float32"

  - name: "phi_trackj2"
    description: "Azimuthal angle of the sub-leading track-jet"
    unit: "rad"
    dtype: "float32"

  - name: "m_trackj2"
    description: "Invariant mass of the sub-leading track-jet"
    unit: "GeV"
    dtype: "float32"

  - name: "tau1_trackj2"
    description: "1-subjettiness (τ₁) of the sub-leading track-jet"
    unit: null
    dtype: "float32"

  - name: "tau2_trackj2"
    description: "2-subjettiness (τ₂) of the sub-leading track-jet"
    unit: null
    dtype: "float32"

  - name: "tau3_trackj2"
    description: "3-subjettiness (τ₃) of the sub-leading track-jet"
    unit: null
    dtype: "float32"

  - name: "Ntracks_trackj1"
    description: "Number of charged-particle tracks in the leading track-jet"
    unit: null
    dtype: "int32"

  - name: "Ntracks_trackj2"
    description: "Number of charged-particle tracks in the sub-leading track-jet"
    unit: null
    dtype: "int32"


# ─── Jet Definition ───────────────────────────────────────────
# Fills Gap (c): jet algorithm details

jet_definition:
  algorithm: "anti-kT"
  radius: 0.4
  input: "inner-detector tracks"
  track_selection:
    pT_min:
      value: 500
      unit: "MeV"
    abs_eta_max: 2.5


# ─── Unfolding Method ─────────────────────────────────────────
# Fills Gaps (e) and (g): iteration details, model/training provenance

unfolding:
  method: "OmniFold"
  package: "omnifold"
  package_version: "X.X"
  reference: "arXiv:1911.09107"
  iterations: 4
  convergence_criterion: "Fixed number of iterations"
  weights_nominal_from_iteration: "last"

  network:
    architecture: "Dense neural network"
    hidden_layers: [100, 100, 100]
    activation: "relu"
    optimizer: "Adam"
    learning_rate: 0.001
    batch_size: 512
    epochs_per_iteration: 100
    input_features:
      - "pT_ll"
      - "pT_l1"
      - "pT_l2"
      - "eta_l1"
      - "eta_l2"
      - "phi_l1"
      - "phi_l2"
      - "y_ll"
      # ... (full list of NN input features)

  statistical_uncertainty:
    method: "NN ensemble + bootstrap"
    nn_ensemble_members: 100
    mc_bootstrap_replicas: 25
    data_bootstrap_replicas: 25


# ─── Weight Definitions ──────────────────────────────────────
# Fills Gap (d): normalization convention and per-column semantics
# Categories mirror the classify_columns() function from Part 1

weights:
  normalization: "relative"
  convention: >
    Weights are relative: to produce a histogram, compute
    sum(weight_mc * weights_nominal) per bin. weight_mc carries
    the generator-level cross-section normalisation;
    weights_nominal provides the per-event OmniFold correction.

  columns:
    nominal_weight:
      - name: "weights_nominal"
        description: "Primary OmniFold unfolded weight (final iteration)"

    mc_weight:
      - name: "weight_mc"
        description: "Original Monte Carlo generator-level event weight"

    nn_ensemble:
      pattern: "weights_ensemble_{i}"
      count: 100
      description: >
        Independent NN ensemble members for statistical uncertainty
        estimation. Each member is trained with a different random
        initialisation.

    bootstrap_mc:
      pattern: "weights_bootstrap_mc_{i}"
      count: 25
      description: >
        MC bootstrap replicas - Poisson-resampled MC events used as
        a cross-check for statistical uncertainty.

    bootstrap_data:
      pattern: "weights_bootstrap_data_{i}"
      count: 25
      description: >
        Data bootstrap replicas - Poisson-resampled data events for
        statistical uncertainty estimation.

    systematics:
      - name: "weights_dd"
        description: "Data-driven background reweighting"
      - name: "weights_pileup"
        description: "Pileup reweighting systematic"
      - name: "weights_muEffReco"
        description: "Muon reconstruction efficiency systematic"
      - name: "weights_muEffIso"
        description: "Muon isolation efficiency systematic"
      - name: "weights_muEffTrack"
        description: "Muon tracking efficiency systematic"
      - name: "weights_muEffTrig"
        description: "Muon trigger efficiency systematic"
      - name: "weights_muCalID"
        description: "Muon inner-detector calibration systematic"
      - name: "weights_muCalMS"
        description: "Muon muon-spectrometer calibration systematic"
      - name: "weights_muCalResBias"
        description: "Muon calibration resolution bias systematic"
      - name: "weights_muCalScale"
        description: "Muon calibration scale systematic"
      - name: "weights_trackEffMain"
        description: "Main tracking efficiency systematic"
      - name: "weights_trackEffJet"
        description: "In-jet tracking efficiency systematic"
      - name: "weights_trackFake"
        description: "Fake track rate systematic"
      - name: "weights_trackPtScale"
        description: "Track pT scale systematic"
      - name: "weights_theoryPSjet"
        description: "Parton shower jet modelling systematic"
      - name: "weights_theoryPSsoft"
        description: "Parton shower soft emission systematic"
      - name: "weights_theoryMPI"
        description: "Multi-parton interaction modelling systematic"
      - name: "weights_theoryPSscale"
        description: "Parton shower scale systematic"
      - name: "weights_theoryAlphaS"
        description: "Strong coupling constant (αS) variation"
      - name: "weights_theoryQCD"
        description: "QCD scale variation systematic"
      - name: "weights_theoryPDF"
        description: "PDF uncertainty systematic"
      - name: "weights_topBackground"
        description: "Top-quark background modelling systematic"
      - name: "weights_lumi"
        description: "Integrated luminosity uncertainty"

    metadata:
      - name: "target_dd"
        description: "Binary flag: 1 if the event is a data-driven target"


# ─── Related Files ────────────────────────────────────────────
# Fills Gap (f): explicit link between nominal and systematic files

related_files:
  - filename: "multifold.h5"
    role: "nominal"
    description: "Nominal OmniFold result using MadGraph5 MC"
    mc_generator: "MadGraph5_aMC@NLO"
    events: 418014
    columns: 200

  - filename: "multifold_sherpa.h5"
    role: "systematic_variation"
    variation_type: "alternative_generator"
    description: "Systematic: Sherpa generator replacing MadGraph5"
    mc_generator: "Sherpa"
    events: 326430
    columns: 51

  - filename: "multifold_nonDY.h5"
    role: "systematic_variation"
    variation_type: "alternative_composition"
    description: "Systematic: modified non-Drell-Yan background fraction"
    mc_generator: "MadGraph5_aMC@NLO"
    events: 433397
    columns: 26


# ─── Reproducibility ─────────────────────────────────────────
# Fills Gap (g): full software stack for reproduction

reproducibility:
  software_environment:
    python_version: "3.X"
    omnifold_version: "X.X"
    tensorflow_version: "2.X"
    container: "docker://atlas/omnifold:vX.X"
  random_seed: 42
  training_data: "Available at zenodo.org/records/XXXXXXX"
```

---

## Justification

### Why this structure?

The schema is organised into **seven top-level sections**, each mapping directly to one or more
gaps identified in Part 1's analysis. This is deliberate: the file should be readable as a
checklist that, once complete, guarantees every gap is addressed.

| Schema Section          | Gap(s) Addressed |
|-------------------------|------------------|
| `dataset`               | (a) Experiment & provenance |
| `mc_generator`          | (a) Generator identity |
| `event_selection`       | (b) Phase space & cuts |
| `observables` + `jet_definition` | (c) Observable units & definitions |
| `unfolding`             | (e) Iteration details, (g) Model provenance |
| `weights`               | (d) Normalization convention |
| `related_files`         | (f) Link between nominal & systematics |
| `reproducibility`       | (g) Software stack |

The weight categories (`nominal_weight`, `mc_weight`, `nn_ensemble`, `bootstrap_mc`,
`bootstrap_data`, `systematics`, `metadata`) mirror the `classify_columns()` function developed
in Part 1 exactly. This means a consumer can programmatically validate a weight file against the
schema by running `classify_columns()` on the HDF5 columns and checking that each group matches
the corresponding `weights.columns.*` block in the YAML.

YAML was chosen over JSON or TOML because it supports multi-line strings (for descriptions and
conventions), inline comments (to annotate which gap each block fills), and is already the
dominant format for configuration and metadata in the scientific Python ecosystem (conda, CI/CD
pipelines, HEPData submission files). It is also natively human-readable without tooling, which
matters for a sidecar metadata file that physicists will read directly.

### What was included and why

**Everything a reuser needs to produce a correct histogram** is included: the normalization
convention tells them *how* to apply the weights; the phase-space cuts tell them *where* the
weights are valid; the observable definitions tell them *what* each column means; and the
related-files block tells them *which* file is the nominal result versus a systematic variation.

**Structured cuts** (variable + operator + value + unit) were chosen over a free-text description
because they are machine-parseable. A future validation tool could read these cuts and
automatically check that a user's sample falls within the declared phase space before applying
the weights - preventing the silent misuse that was flagged as a risk in Part 1.

**Per-observable entries** with unit, dtype, and valid_range were included even though they make
the file long. The alternative - a compact table - would sacrifice machine-readability. The
verbosity is acceptable because the file is written once by the analysts and consumed many times
by users and tools.

**The `unfolding` block** captures the full training recipe (architecture, hyperparameters, input
features, number of iterations). This is essential for reproducibility and for understanding
whether the weights are transferable to a slightly different phase space or observable set.

### What was deliberately left out

**Raw data and full model checkpoints** are not referenced inline. The schema points to a Zenodo
DOI for the training data and a Docker container tag for the software environment, but does not
attempt to embed binary artefacts. Metadata files should remain small, portable, and
version-controllable in Git; multi-gigabyte model weights belong in dedicated artefact stores.

**Per-event identifiers** (Gap h) are acknowledged but not added to the schema. They would need
to be added as a new column in the HDF5 file itself, not in the YAML. The schema could include a
field like `event_id_column: "event_id"` once such a column exists, but designing the identifier
scheme (run/event number? sequential index? hash?) is a data-format decision, not a metadata
decision.

**Detailed systematic uncertainty correlations** (e.g., "weights_pileup is 100% correlated
across bins") were omitted. This information is important for a full statistical analysis but
belongs in a dedicated correlation model (e.g., a pyhf workspace), not in a sidecar YAML that
describes the *contents* of a weight file.

### How a new user would interact with this file

A physicist who did not run the original analysis would use this file in three stages:

1. **Discovery.** They find `multifold.h5` on Zenodo or HEPData. The accompanying YAML tells
   them immediately what experiment, process, and phase space the weights correspond to - without
   needing to read the paper first. The `related_files` block tells them which other files exist
   and what role each plays.

2. **Validation.** Before applying the weights to their own MC sample, they check the
   `event_selection.cuts` block to verify that their sample's phase space matches. They check
   `mc_generator` to confirm compatibility. They read `weights.convention` to understand the
   correct formula for producing a histogram.

3. **Reproduction / extension.** If they want to retrain OmniFold with a different observable set
   or more iterations, the `unfolding` block gives them the full recipe. The
   `reproducibility.container` tag lets them recreate the exact software environment. The
   `unfolding.network.input_features` list tells them which observables were used as NN inputs,
   so they know what is safe to change.

This three-stage workflow - *discover, validate, reproduce* - guided every structural decision in
the schema. Each section exists because it answers a question a new user would ask at one of
these stages.
