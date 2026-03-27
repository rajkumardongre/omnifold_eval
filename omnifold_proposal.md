# Publication of OmniFold Weights

**GSoC 2026 Proposal**

Rajkumar Dongre
March, 2026

---

## Contents

1. [The Project](#1-the-project)
    1. [Motivation & Background](#11-motivation--background)
    2. [How OmniFold Works - and Why Publishing Its Output Is Hard](#12-how-omnifold-works-and-why-publishing-its-output-is-hard)
    3. [Gap Analysis - What Is Missing Today](#13-gap-analysis---what-is-missing-today)
    4. [Project Objectives](#14-project-objectives)
    5. [Expected Deliverables](#15-expected-deliverables)
2. [Implementation](#2-implementation)
    1. [Data & Metadata Schema (`omnifold-schema`)](#21-data--metadata-schema)
        1. [Publication Structure - Two Files](#211-publication-structure---two-files)
        2. [`dataset` - Dataset Provenance](#212-dataset---dataset-provenance)
        3. [`mc_generator` - Monte Carlo Generator Information](#213-mc_generator---monte-carlo-generator-information)
        4. [`event_selection` - Phase Space & Selection Cuts](#214-event_selection---phase-space--selection-cuts)
        5. [`observables` - Observable Definitions](#215-observables---observable-definitions)
        6. [`unfolding` - Unfolding Configuration & Model Provenance](#216-unfolding---unfolding-configuration--model-provenance)
        7. [`column_convention` - Column Naming Convention](#217-column_convention---column-naming-convention)
        8. [`weights` - Weight Semantics & Uncertainty Catalog](#218-weights---weight-semantics--uncertainty-catalog)
        9. [`related_files` - Inter-file Linkage](#219-related_files---inter-file-linkage)
        10. [`reproducibility` - Software Environment](#2110-reproducibility---software-environment)
        11. [Complete Schema Example (v1.0)](#2111-complete-schema-example-v10)
    2. [Container Format - Unified Single-Matrix Design](#22-container-format--storage-layer---unified-single-matrix-design)
    3. [HEPData Integration Layer](#23-hepdata-integration-layer)
    4. [Validation Framework](#24-validation-framework)
    5. [Architecture Overview](#25-architecture-overview)
    6. [Python API - `omnifold-pub`](#26-python-api--omnifold-pub)
    7. [Example: End-to-End Consumer Workflow](#27-example-end-to-end-consumer-workflow)
3. [Timeline](#3-timeline)
    1. [Pre-GSoC Period](#31-pre-gsoc-period)
    2. [GSoC Period](#32-gsoc-period)
    3. [Post-GSoC Period](#33-post-gsoc-period)
4. [Risk Mitigation](#4-risk-mitigation)
5. [Acknowledgements](#5-acknowledgements)
6. [References](#6-references)
7. [Contact](#7-contact)

---

## 1. The Project

**Title:** Publication of OmniFold Weights - Standardizing the publication, preservation, and reuse of ML-based unfolding results

### 1.1. Motivation & Background

Modern particle physics measurements at the LHC are undergoing a paradigm shift. Traditional measurements unfold detector effects into fixed, binned histograms. Machine-learning-based methods like **OmniFold** [1] produce something fundamentally different: **per-event weights** that, when applied to a Monte Carlo simulation, yield the unfolded particle-level distribution for *any* observable - including observables not yet conceived at the time of the analysis.

This is a breakthrough capability. As stated by Arratia et al. [2]:

> *"Unbinned measurements can enable, improve, or at least simplify comparisons between experiments and with theoretical predictions. Furthermore, many-dimensional measurements can be used to define observables after the measurement instead of before."*

However, this power comes with a critical challenge: **there is currently no community standard for publishing unbinned data**. As part of the evaluation task for this project, I was provided with the public Z+jets OmniFold weight files (Zenodo [3]), which I use as the reference dataset throughout this proposal. These files contain per-event weights and observables in HDF5 format, but they lack essential metadata for reuse - experiment identity, phase space definitions, observable units, weight normalization conventions, iteration details, and model provenance are all absent.

Without standardization, the promise of OmniFold - that measurements remain useful for reinterpretation years after publication - cannot be realized. A physicist downloading weights from HEPData or Zenodo today would not know:

- What phase space cuts to apply
- How to normalize the weights for cross-section computation
- Which systematic variations are included and what they mean
- How to propagate uncertainties correctly

This project aims to solve these problems by defining **how OmniFold results should be published**, building **tools to produce and consume standardized outputs**, and demonstrating **integration with HEPData**.

### 1.2. How OmniFold Works and Why Publishing Its Output Is Hard

OmniFold [1] is a classifier-based unbinned unfolding method. It iteratively reweights a Monte Carlo simulation to match data using neural network classifiers that learn the likelihood ratio between data and simulation:

1. **Step 1 (Detector-level):** Train a classifier to distinguish data from (weighted) simulation at detector level. The classifier output yields reweighting factors ω(m) that make the simulation match data.
2. **Step 2 (Particle-level):** Pull these weights back to particle level and train a second classifier to convert the per-instance weights into a smooth weighting function ν(t) of the particle-level features.
3. **Iterate:** Repeat Steps 1–2 for several iterations. The procedure converges to the maximum likelihood estimate of the true particle-level distribution.

**Why this is hard to publish:**


| Challenge                    | Description                                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **No fixed binning**         | The result is not a histogram - it is a weighted event sample. HEPData is designed for tables and histograms.                      |
| **Large file sizes**         | A nominal weight file can be ~500 MB; the full dataset with systematics can exceed 2 GB. HEPData has file size limits.             |
| **Multiple weight types**    | Nominal, bootstrap (MC/data), NN ensemble, and systematic weights all serve different purposes and must be clearly documented.     |
| **Normalization ambiguity**  | Weights may be absolute (cross-section × luminosity) or relative. Without metadata, users cannot produce correct physical results. |
| **No self-describing files** | Current HDF5 files contain no metadata about the experiment, generator, event selection, or observable definitions.                |


### 1.3. Gap Analysis - What Is Missing Today

From my evaluation-task exploration of the public OmniFold Z+jets weight files [3], I identified the following critical gaps:


| Gap                                    | Description                                                                                                                                                                              |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **No dataset provenance**              | Which experiment, data-taking period, luminosity, MC generator, and physics process are not recorded.                                                                                    |
| **No phase space / selection cuts**    | What event selection was applied (pT thresholds, η cuts, jet requirements) is unknown. A user applying weights in the wrong phase space will get silently wrong results.                 |
| **No observable definitions**          | Units (GeV?), jet algorithm and radius, track selection criteria, and substructure variable definitions are absent.                                                                      |
| **No weight normalization convention** | Are weights absolute or relative? Mean `weights_nominal ≈ 0.0043` suggests normalization, but to what?                                                                                   |
| **No iteration metadata**              | How many OmniFold iterations were run, what convergence criterion was used, and which iteration produced `weights_nominal` are unknown.                                                  |
| **No inter-file linkage**              | Three standalone files (`multifold.h5`, `multifold_sherpa.h5`, `multifold_nonDY.h5`) with no field indicating they belong to the same analysis or that Sherpa is a systematic variation. |
| **No model provenance**                | NN architecture, hyperparameters, training features, and model checkpoints are not referenced.                                                                                           |
| **No event identifiers**               | No event ID or run/event number to match rows across files or back to original data.                                                                                                     |


The detailed classification shows 24 physics observables, 1 nominal weight, 1 MC weight, 100 NN ensemble members, 25 MC bootstrap replicas, 25 data bootstrap replicas, 23 systematic weight variations, and 1 metadata flag across 200 columns in the nominal file - all of which need clear documentation in a standardized schema.

### 1.4. Project Objectives

1. **Define a formal data & metadata specification** (YAML/JSON schema) for OmniFold results, capturing dataset provenance, observable definitions, weight semantics, phase space, and normalization.
2. **Standardize a container format** for per-event weights (HDF5 or Parquet) with clear naming conventions, indexing, and support for nominal, systematic, bootstrap, and ensemble weights.
3. **Build a Python package (`omnifold-pub`)** that:
  - Produces OmniFold outputs in the standardized format
  - Loads published weights (local or from HEPData/Zenodo)
  - Applies weights to compute arbitrary observables with uncertainty propagation
  - Generates publication-quality plots
4. **Implement validation procedures** - closure tests, normalization checks, and stability diagnostics.
5. **Demonstrate HEPData integration** - mapping OmniFold results to HEPData records with submission templates.
6. **Provide reference examples** - complete unfolding → publication → reinterpretation workflows using public datasets.

### 1.5. Expected Deliverables


| #   | Deliverable                         | Description                                                                                                          |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 1   | **`omnifold-schema` specification** | YAML schema (versioned) defining required and optional fields for OmniFold publications, with a validation CLI tool. |
| 2   | **`omnifold-pub` Python package**   | Installable via pip. Core API for publishing, loading, and analyzing OmniFold weight files.                          |
| 3   | **Container format specification**  | HDF5 layout with standardized group/dataset naming, attributes, and optional Parquet export.                         |
| 4   | **Validation suite**                | Automated tests for normalization, closure, and weight stability.                                                    |
| 5   | **HEPData integration templates**   | Submission YAML and tooling for mapping OmniFold outputs to HEPData records.                                         |
| 6   | **Documentation & examples**        | Jupyter notebooks demonstrating the full workflow: produce → publish → consume → reinterpret.                        |


---

## 2. Implementation

### 2.1. Data & Metadata Schema

#### 2.1.1. Publication Structure - Two Files

Arratia et al. [2, Section 6.1] propose that an unbinned measurement should be published as **two files**:

1. **A submission file** - a YAML file in the same format used by HEPData, describing the measurement metadata and pointing to the data file(s).
2. **A data file** - for each measurement, containing the per-event observables and weights.

We adopt this two-file structure directly. The submission YAML carries all metadata that the data file cannot express on its own - provenance, phase-space definitions, observable semantics, weight normalization, and uncertainty catalogs. The data file carries the numerical payload (the unified N × C matrix described in Section 2.2). The YAML is also embedded as an HDF5 attribute inside the data file so that the data file is self-describing even without the sidecar, but the standalone YAML remains the authoritative, human-readable specification.

The YAML schema is divided into **nine sections**, each addressing a specific gap identified in the exploration (Section 1.3). The sections, their purpose, and the gap they close are summarized below, then explained individually.


| YAML section        | Purpose                                     | Gap it addresses                               |
| ------------------- | ------------------------------------------- | ---------------------------------------------- |
| `dataset`           | What this measurement is                    | No experiment or dataset provenance            |
| `mc_generator`      | How the simulation was produced             | Generator identity only implied by filename    |
| `event_selection`   | What phase space the result covers          | No selection cuts documented                   |
| `observables`       | What each column means                      | No units, no definitions                       |
| `unfolding`         | How OmniFold was configured                 | No iteration or model provenance               |
| `column_convention` | How to parse column names                   | No way to distinguish observables from weights |
| `weights`           | What each weight means and how to normalize | Normalization ambiguity                        |
| `related_files`     | How the files connect to each other         | No inter-file linkage                          |
| `reproducibility`   | How to reproduce the result                 | No software environment captured               |


#### 2.1.2. `dataset` - Dataset Provenance

This section answers the most basic question: *what is this measurement?* Our gap analysis found that the existing weight files contain zero information about which experiment, data-taking period, luminosity, or physics process produced them.

```yaml
dataset:
  name: "Z+jets OmniFold unfolding"
  experiment: "ATLAS"
  sqrt_s_TeV: 13.0
  luminosity_fb: 139.0
  data_period: "Run 2 (2015–2018)"
  process: "pp → Z(→ℓℓ) + jets"
  arxiv_id: null
  inspire_id: null
  hepdata_id: null
  zenodo_doi: "10.5281/zenodo.11507450"
```

**Reasoning:** Every field here is something a physicist would need before deciding whether these weights are relevant to their work. The `arxiv_id`, `inspire_id`, and `hepdata_id` fields are nullable because they may not exist at the time of first publication, but they create a permanent link between the weight file and its associated paper once published. The `zenodo_doi` links to the archival data deposit.

#### 2.1.3. `mc_generator` - Monte Carlo Generator Information

This section records which MC generator produced the particle-level events - the "canvas" on which OmniFold weights are defined. The gap analysis found that the generator identity (MG5 vs. Sherpa) was implied only by the filename, not stored anywhere in the file.

```yaml
mc_generator:
  nominal:
    name: "MadGraph5_aMC@NLO"
    version: "2.9.3"
    pdf_set: "NNPDF31_nnlo_as_0118"
    tune: null
    process_card: null
  alternatives:
    - name: "Sherpa"
      version: "2.2.11"
      role: "generator_systematic"
      file: "multifold_sherpa.h5"
```

**Reasoning:** The nominal generator defines the fixed canvas of N events. Alternative generators are listed with their `role` (e.g. `generator_systematic`) and the filename of their separate data file, establishing the inter-file relationship that is currently absent. The `pdf_set` and `tune` fields are critical for theorists comparing predictions - a different PDF set changes the expected distributions, so this must be explicit.

#### 2.1.4. `event_selection` - Phase Space & Selection Cuts

This section defines the fiducial volume - the region of phase space where the weights are valid. The gap analysis identified this as perhaps the most dangerous omission: a user applying these weights in a different phase space will get silently wrong results.

```yaml
event_selection:
  level: "particle"
  description: "Z boson decaying to two same-flavour leptons"
  cuts:
    - variable: "pT_ll"
      operator: ">"
      value: 200.0
      unit: "GeV"
    - variable: "abs(eta_l1)"
      operator: "<"
      value: 2.4
    - variable: "abs(eta_l2)"
      operator: "<"
      value: 2.4
  jet_definition:
    algorithm: "anti-kT"
    radius: 0.4
    input: "charged tracks"
    min_pT_GeV: 25.0
    max_abs_eta: 2.5
```

**Reasoning:** Cuts are structured as machine-readable `{variable, operator, value, unit}` triples rather than free text. This enables the Python API to programmatically generate a boolean phase-space mask and warn users if their data falls outside the valid region. The `level` field distinguishes particle-level from detector-level observables  a critical distinction for unfolding. The `jet_definition` sub-section documents the jet algorithm, radius, and track selection, which the gap analysis showed are absent from the current files and differ between ATLAS and CMS.

#### 2.1.5. `observables` - Observable Definitions

This section describes each observable column in the data file: its physics meaning, unit, data type, and valid range. The gap analysis found that units are missing (GeV is assumed but not stated), substructure variables like τ₁/τ₂/τ₃ have no description, and the jet algorithm used to define `trackj1/trackj2` is undocumented.

```yaml
observables:
  - name: "pT_ll"
    description: "Transverse momentum of the dilepton system"
    unit: "GeV"
    dtype: "float32"
    range: [200.0, 1500.0]
  - name: "eta_l1"
    description: "Pseudorapidity of the leading lepton"
    unit: null
    dtype: "float32"
    range: [-2.4, 2.4]
  # ... (one entry per observable column)
```

**Reasoning:** Each observable is a structured entry with mandatory `name`, `description`, `unit`, `dtype`, and `range` fields. The `unit` is nullable for dimensionless quantities (pseudorapidity, azimuthal angle). The `range` field documents the physical boundaries, which the validation framework can check against the actual data to flag anomalies. There is one entry per observable column - for the Z+jets analysis, this means 24 entries.

#### 2.1.6. `unfolding` - Unfolding Configuration & Model Provenance

This section captures how OmniFold was configured: the number of iterations, convergence criterion, neural network architecture, training hyperparameters, and which features were used in each step. The gap analysis found that none of this information exists in the current files.

```yaml
unfolding:
  method: "OmniFold"
  package_version: "0.1.0"
  iterations: 5
  convergence_criterion: "fixed iteration count"
  nn_architecture:
    framework: "TensorFlow"
    layers: [50, 50, 50]
    activation: "relu"
    output_activation: "sigmoid"
  training:
    epochs: 20
    batch_size: 10000
    optimizer: "Adam"
    learning_rate: 0.001
    validation_fraction: 0.2
  features_used:
    step1_detector: ["pT_ll", "pT_l1", "pT_l2", "eta_l1", "..."]
    step2_particle: ["pT_ll", "pT_l1", "pT_l2", "eta_l1", "..."]
```

**Reasoning:** This is primarily for reproducibility and trust. A physicist evaluating whether to use these weights needs to know whether 5 iterations was sufficient, what architecture was used, and which features drove the classifier. The `features_used` sub-section is split by OmniFold step (detector-level reweighting vs. particle-level reweighting) because the two steps may use different feature sets. We do not require publishing the trained model checkpoint itself - that is optional and goes into the Zenodo archive - but the architecture and hyperparameters are mandatory.

#### 2.1.7. `column_convention` - Column Naming Convention

This section documents the `__` (double-underscore) prefix scheme used to classify columns in the data file. It is the bridge between the metadata schema and the container format (Section 2.2.2).

```yaml
column_convention:
  description: >
    All columns in the unified N × C matrix follow a prefix-based
    naming convention using double-underscore (__) as the namespace
    separator. See Section 2.2.2 for the full specification.
  prefixes:
    observable: "(no prefix) — bare physics names"
    weight: "weight__ — nominal and MC weights"
    statistical: "stat__ — bootstrap and ensemble replicas"
    systematic: "syst__ — two-point systematic variations"
```

**Reasoning:** By encoding the convention in the schema itself, a consumer tool can validate that every column in the HDF5 `@columns` attribute conforms to the expected prefixes. If a column name does not match any known prefix, the validator flags it as an error. This makes the format self-policing.

#### 2.1.8. `weights` - Weight Semantics & Uncertainty Catalog

This is the largest and most critical section. It documents what each weight column means, how to normalize them for cross-section computation, and catalogs every uncertainty source. The gap analysis identified normalization ambiguity as the most dangerous gap - the mean `weights_nominal ≈ 0.0043` suggests the weights are normalized, but to what?

The schema uses two generic lists - `columns` for named weight columns and `uncertainties` for all variation sources - rather than hardcoded keys for specific methods. This keeps the format analysis-agnostic: an experiment that uses only bootstrap replicas, or only systematic shifts, or an entirely different reweighting method, fills in the same structure without needing to match predefined field names.

```yaml
weights:
  normalization: "absolute | relative | arbitrary"
  normalization_description: "<formula for computing cross section from weights>"

  columns:
    - name: "<column_name>"
      role: "nominal | prior | auxiliary"
      description: "<what this weight represents>"

  uncertainties:
    - name: "<human-readable label>"
      type: "replica | two-point"
      columns_pattern: "<prefix__{i}>"   # for replica-type
      column: "<column_name>"            # for two-point
      count: <N>                         # for replica-type
      description: "<what changes in the training>"
```

**Field-by-field specification:**


| Field                             | Required       | Description                                                                                                                                     |
| --------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `normalization`                   | yes            | One of `absolute`, `relative`, or `arbitrary`. Determines whether Σwᵢ yields a cross section, a probability, or has no physical interpretation. |
| `normalization_description`       | yes            | Free-text formula for computing a differential cross section from the weights.                                                                  |
| `columns[].name`                  | yes            | Exact column name in the data file (must follow the `weight__` prefix convention).                                                              |
| `columns[].role`                  | yes            | Semantic role: `nominal` (unfolded weight), `prior` (MC generator weight), or `auxiliary` (any other per-event weight).                         |
| `columns[].description`           | yes            | Human-readable explanation of the weight.                                                                                                       |
| `uncertainties[].name`            | yes            | Short identifier for the uncertainty source.                                                                                                    |
| `uncertainties[].type`            | yes            | `replica` - consumer computes std dev across replicas. `two-point` - consumer takes difference with nominal.                                    |
| `uncertainties[].columns_pattern` | if `replica`   | Pattern with `{i}` placeholder that expands to the column names of all replicas.                                                                |
| `uncertainties[].column`          | if `two-point` | Exact column name of the varied weight.                                                                                                         |
| `uncertainties[].count`           | if `replica`   | Number of replicas.                                                                                                                             |
| `uncertainties[].description`     | yes            | What changes in the classifier training for this variation.                                                                                     |


**Z+jets example using the generalized schema:**

```yaml
weights:
  normalization: "absolute"
  normalization_description: >
    w_i = weight__mc_i × weight__nominal_i gives the contribution
    to the differential cross section in pb per event.
    Sum of (weight__mc × weight__nominal) equals the fiducial
    cross section in pb.

  columns:
    - name: "weight__nominal"
      role: "nominal"
      description: "Per-event unfolded weight from final OmniFold iteration"
    - name: "weight__mc"
      role: "prior"
      description: "MC generator-level weight (cross-section × filter efficiency / N_gen)"

  uncertainties:
    - name: "bootstrap_mc"
      type: "replica"
      columns_pattern: "stat__bootstrap_mc__{i}"
      count: 25
      description: "MC bootstrap replicas — MC side Poisson-resampled"
    - name: "bootstrap_data"
      type: "replica"
      columns_pattern: "stat__bootstrap_data__{i}"
      count: 25
      description: "Data bootstrap replicas — data side Poisson-resampled"
    - name: "nn_ensemble"
      type: "replica"
      columns_pattern: "stat__ensemble__{i}"
      count: 100
      description: "NN re-initialization ensemble — different random seeds"
    - name: "pileup"
      type: "two-point"
      column: "syst__pileup"
      description: "Pileup reweighting uncertainty"
    - name: "muon_eff_stat"
      type: "two-point"
      column: "syst__muEffStat"
      description: "Muon efficiency statistical uncertainty"
    # ... (one entry per uncertainty source)
```

**Reasoning:**

1. **Uniform list, not hardcoded keys.** The generalized `uncertainties` list lets any analysis enumerate its sources - a CMS measurement might have 50 two-point systematics and no ensemble replicas, while a future Bayesian unfolding might publish posterior samples as a single replica set. Both fit the same schema without modification.
2. **Two types cover all known cases.** The paper [2, Section 6.2] identifies exactly two uncertainty evaluation methods: replica-type (std dev across replicas) and two-point (difference with nominal). By making `type` a mandatory field on every uncertainty entry, a consumer tool can automatically compute uncertainty bands without analysis-specific logic.
3. `columns` **replaces hardcoded** `nominal` **/** `mc_weight`**.** Different analyses may have different weight columns - some may have a single combined weight, others may split into prior and correction. The `role` field (`nominal`, `prior`, `auxiliary`) gives semantic meaning without prescribing a fixed set of column names.
4. **Normalization is mandatory.** The `normalization` field must be declared explicitly. This directly addresses the most dangerous gap - silent normalization errors that lead to incorrect cross-section computations.

**Complete `weights` section for the Z+jets nominal file (`multifold.h5`):**

```yaml
weights:
  normalization: "absolute"
  normalization_description: >
    w_i = weight__mc_i × weight__nominal_i gives the contribution
    to the differential cross section in pb per event.
    Sum of (weight__mc × weight__nominal) over all 418,014 events
    equals the fiducial cross section in pb.

  columns:
    - name: "weight__nominal"
      role: "nominal"
      description: "Per-event unfolded weight from final OmniFold iteration"
    - name: "weight__mc"
      role: "prior"
      description: "MC generator-level weight (cross-section × filter efficiency / N_gen)"

  uncertainties:
    # ── replica-type (compute std dev across replicas) ──────────────
    - name: "bootstrap_mc"
      type: "replica"
      columns_pattern: "stat__bootstrap_mc__{i}"
      count: 25
      description: "MC side Poisson-resampled; data side unchanged"
    - name: "bootstrap_data"
      type: "replica"
      columns_pattern: "stat__bootstrap_data__{i}"
      count: 25
      description: "Data side Poisson-resampled; MC side unchanged"
    - name: "nn_ensemble"
      type: "replica"
      columns_pattern: "stat__ensemble__{i}"
      count: 100
      description: "Different NN random seed; both MC and data unchanged"

    # ── two-point (take difference with nominal) ───────────────────
    - name: "dd"
      type: "two-point"
      column: "syst__dd"
      description: "Data-driven background estimation"
    - name: "pileup"
      type: "two-point"
      column: "syst__pileup"
      description: "Pileup reweighting uncertainty"
    - name: "muon_eff_reco"
      type: "two-point"
      column: "syst__muEffReco"
      description: "Muon reconstruction efficiency"
    - name: "muon_eff_iso"
      type: "two-point"
      column: "syst__muEffIso"
      description: "Muon isolation efficiency"
    - name: "muon_eff_track"
      type: "two-point"
      column: "syst__muEffTrack"
      description: "Muon inner-track efficiency"
    - name: "muon_eff_trig"
      type: "two-point"
      column: "syst__muEffTrig"
      description: "Muon trigger efficiency"
    - name: "muon_cal_id"
      type: "two-point"
      column: "syst__muCalID"
      description: "Muon ID momentum calibration"
    - name: "muon_cal_ms"
      type: "two-point"
      column: "syst__muCalMS"
      description: "Muon MS momentum calibration"
    - name: "muon_cal_res_bias"
      type: "two-point"
      column: "syst__muCalResBias"
      description: "Muon calibration residual bias"
    - name: "muon_cal_scale"
      type: "two-point"
      column: "syst__muCalScale"
      description: "Muon momentum scale"
    - name: "track_eff_main"
      type: "two-point"
      column: "syst__trackEffMain"
      description: "Main track reconstruction efficiency"
    - name: "track_eff_jet"
      type: "two-point"
      column: "syst__trackEffJet"
      description: "Track efficiency inside jets"
    - name: "track_fake"
      type: "two-point"
      column: "syst__trackFake"
      description: "Fake track rate"
    - name: "track_pt_scale"
      type: "two-point"
      column: "syst__trackPtScale"
      description: "Track pT scale uncertainty"
    - name: "theory_ps_jet"
      type: "two-point"
      column: "syst__theoryPSjet"
      description: "Parton-shower jet modelling"
    - name: "theory_ps_soft"
      type: "two-point"
      column: "syst__theoryPSsoft"
      description: "Parton-shower soft radiation"
    - name: "theory_mpi"
      type: "two-point"
      column: "syst__theoryMPI"
      description: "Multi-parton interaction modelling"
    - name: "theory_ps_scale"
      type: "two-point"
      column: "syst__theoryPSscale"
      description: "Parton-shower scale variation"
    - name: "theory_alpha_s"
      type: "two-point"
      column: "syst__theoryAlphaS"
      description: "Strong coupling constant variation"
    - name: "theory_qcd"
      type: "two-point"
      column: "syst__theoryQCD"
      description: "QCD scale variation"
    - name: "theory_pdf"
      type: "two-point"
      column: "syst__theoryPDF"
      description: "PDF set variation"
    - name: "top_background"
      type: "two-point"
      column: "syst__topBackground"
      description: "Top-quark background normalisation"
    - name: "luminosity"
      type: "two-point"
      column: "syst__lumi"
      description: "Integrated luminosity uncertainty"
```

This lists all **3 replica sources** (150 total replica columns) and all **23 two-point systematics** found in the nominal `multifold.h5` file - totalling 175 uncertainty columns. Together with the 24 observables and the 1 metadata column (`target_dd`), this accounts for the full 200-column structure of the file.

#### 2.1.9. `related_files` - Inter-file Linkage

This section explicitly connects the files that belong to the same analysis. The gap analysis found that the three existing files (`multifold.h5`, `multifold_sherpa.h5`, `multifold_nonDY.h5`) are standalone with no field indicating they belong together or that Sherpa is a systematic variation of the nominal.

```yaml
related_files:
  - file: "multifold.h5"
    role: "nominal"
    description: "Nominal MadGraph5 unfolding — 418,014 particle-level events with all uncertainties"
    schema: "https://zenodo.org/records/11507450/files/multifold_schema.yaml"
    data_link: "https://zenodo.org/records/11507450/files/multifold.h5"
  - file: "multifold_sherpa.h5"
    role: "systematic:generator"
    description: "Sherpa generator systematic — 326,430 events, different MC canvas"
    schema: "https://zenodo.org/records/11507450/files/multifold_sherpa_schema.yaml"
    data_link: "https://zenodo.org/records/11507450/files/multifold_sherpa.h5"
  - file: "multifold_nonDY.h5"
    role: "systematic:composition"
    description: "Non-Drell-Yan background composition systematic — 433,397 events, different MC canvas"
    schema: "https://zenodo.org/records/11507450/files/multifold_nonDY_schema.yaml"
    data_link: "https://zenodo.org/records/11507450/files/multifold_nonDY.h5"
```

**Reasoning:** Each entry has five fields: `file` (the local filename), `role` (what this file represents), `description` (a human-readable summary), `schema` (a direct URL to the YAML metadata for this data file), and `data_link` (a permanent URL to download the data file itself). The `schema` field is a URL rather than a local path so that a consumer can fetch the metadata directly without needing prior access to the archive. This is critical because each data file has a different internal structure - the nominal file has 200 columns (24 observables + 2 weights + 150 replicas + 23 systematics + 1 metadata), the Sherpa file has 51 columns (24 observables + 2 weights + 25 bootstrap MC replicas), and the nonDY file has only 26 columns (24 observables + 2 weights). A single schema cannot accurately describe all three. By pointing each entry to its own remotely accessible YAML, a consumer can programmatically discover any related file's column layout, weight semantics, and available uncertainties without downloading the data first. The `role` uses a colon-separated convention (`systematic:generator`, `systematic:composition`) to indicate both the category and the specific variation.

#### 2.1.10. `reproducibility` - Software Environment

This section captures the minimum information needed to reproduce or re-run the unfolding.

```yaml
reproducibility:
  software_environment:
    python_version: "3.9"
    omnifold_version: "0.1.0"
    tensorflow_version: "2.11"
  random_seed: 42
  container_image: null
```

**Reasoning:** The gap analysis noted that bit-for-bit reproducibility requires the same software versions and random seeds. The `container_image` field is nullable but provides a path to a Docker/Singularity image if one exists. Even without a container, recording the package versions gives a future user a fighting chance at reproducing the result.

#### 2.1.11. Complete Schema Example (v1.0)

Combining all sections above, the full metadata YAML for the Z+jets OmniFold analysis:

```yaml
schema_version: "1.0"

dataset:
  name: "Z+jets OmniFold unfolding"
  experiment: "ATLAS"
  sqrt_s_TeV: 13.0
  luminosity_fb: 139.0
  data_period: "Run 2 (2015–2018)"
  process: "pp → Z(→ℓℓ) + jets"
  arxiv_id: null
  inspire_id: null
  hepdata_id: null
  zenodo_doi: "10.5281/zenodo.11507450"

mc_generator:
  nominal:
    name: "MadGraph5_aMC@NLO"
    version: "2.9.3"
    pdf_set: "NNPDF31_nnlo_as_0118"
    tune: null
    process_card: null
  alternatives:
    - name: "Sherpa"
      version: "2.2.11"
      role: "generator_systematic"
      file: "multifold_sherpa.h5"

event_selection:
  level: "particle"
  description: "Z boson decaying to two same-flavour leptons"
  cuts:
    - variable: "pT_ll"
      operator: ">"
      value: 200.0
      unit: "GeV"
    - variable: "abs(eta_l1)"
      operator: "<"
      value: 2.4
    - variable: "abs(eta_l2)"
      operator: "<"
      value: 2.4
  jet_definition:
    algorithm: "anti-kT"
    radius: 0.4
    input: "charged tracks"
    min_pT_GeV: 25.0
    max_abs_eta: 2.5

observables:
  - name: "pT_ll"
    description: "Transverse momentum of the dilepton system"
    unit: "GeV"
    dtype: "float32"
    range: [200.0, 1500.0]
  - name: "eta_l1"
    description: "Pseudorapidity of the leading lepton"
    unit: null
    dtype: "float32"
    range: [-2.4, 2.4]
  # ... (one entry per each of the 24 observable columns)

unfolding:
  method: "OmniFold"
  package_version: "0.1.0"
  iterations: 5
  convergence_criterion: "fixed iteration count"
  nn_architecture:
    framework: "TensorFlow"
    layers: [50, 50, 50]
    activation: "relu"
    output_activation: "sigmoid"
  training:
    epochs: 20
    batch_size: 10000
    optimizer: "Adam"
    learning_rate: 0.001
    validation_fraction: 0.2
  features_used:
    step1_detector: ["pT_ll", "pT_l1", "pT_l2", "eta_l1", "..."]
    step2_particle: ["pT_ll", "pT_l1", "pT_l2", "eta_l1", "..."]

column_convention:
  description: >
    All columns in the unified N × C matrix follow a prefix-based
    naming convention using double-underscore (__) as the namespace
    separator. See Section 2.2.2 for the full specification.
  prefixes:
    observable: "(no prefix) — bare physics names"
    weight: "weight__ — nominal and MC weights"
    statistical: "stat__ — bootstrap and ensemble replicas"
    systematic: "syst__ — two-point systematic variations"

weights:
  normalization: "absolute"
  normalization_description: >
    w_i = weight__mc_i × weight__nominal_i gives the contribution
    to the differential cross section in pb per event.
    Sum of (weight__mc × weight__nominal) equals the fiducial
    cross section in pb.

  columns:
    - name: "weight__nominal"
      role: "nominal"
      description: "Per-event unfolded weight from final OmniFold iteration"
    - name: "weight__mc"
      role: "prior"
      description: "MC generator-level weight (cross-section × filter efficiency / N_gen)"

  uncertainties:
    - name: "bootstrap_mc"
      type: "replica"
      columns_pattern: "stat__bootstrap_mc__{i}"
      count: 25
      description: "MC bootstrap replicas — MC side Poisson-resampled"
    - name: "bootstrap_data"
      type: "replica"
      columns_pattern: "stat__bootstrap_data__{i}"
      count: 25
      description: "Data bootstrap replicas — data side Poisson-resampled"
    - name: "nn_ensemble"
      type: "replica"
      columns_pattern: "stat__ensemble__{i}"
      count: 100
      description: "NN re-initialization ensemble — different random seeds"
    - name: "pileup"
      type: "two-point"
      column: "syst__pileup"
      description: "Pileup reweighting uncertainty"
    - name: "muon_eff_stat"
      type: "two-point"
      column: "syst__muEffStat"
      description: "Muon efficiency statistical uncertainty"
    # ... (one entry per uncertainty source)

related_files:
  - file: "multifold.h5"
    role: "nominal"
    description: "Nominal MadGraph5 unfolding — 418,014 particle-level events with all uncertainties"
    schema: "https://zenodo.org/records/11507450/files/multifold_schema.yaml"
    data_link: "https://zenodo.org/records/11507450/files/multifold.h5"
  - file: "multifold_sherpa.h5"
    role: "systematic:generator"
    description: "Sherpa generator systematic — 326,430 events, different MC canvas"
    schema: "https://zenodo.org/records/11507450/files/multifold_sherpa_schema.yaml"
    data_link: "https://zenodo.org/records/11507450/files/multifold_sherpa.h5"
  - file: "multifold_nonDY.h5"
    role: "systematic:composition"
    description: "Non-Drell-Yan background composition systematic — 433,397 events, different MC canvas"
    schema: "https://zenodo.org/records/11507450/files/multifold_nonDY_schema.yaml"
    data_link: "https://zenodo.org/records/11507450/files/multifold_nonDY.h5"

reproducibility:
  software_environment:
    python_version: "3.9"
    omnifold_version: "0.1.0"
    tensorflow_version: "2.11"
  random_seed: 42
  container_image: null
```

### 2.2. Container Format & Storage Layer - Unified Single-Matrix Design

We adopt the data layout proposed by Arratia et al. [2, Section 6.1] as the starting point, then extend it based on a critical observation about how OmniFold works: **all variations operate on the same fixed canvas of particle-level MC events**.

#### 2.2.1. The Fixed-Canvas Principle

The N particle-level MC events (e.g. 418,014 events generated by MadGraph5) are a permanent reference sample. Their observable values - the k columns of pT, eta, phi, mass, substructure variables - never change. What changes across variations is only the classifier's training:


| Variation type                 | What changes in training                                                         | What stays the same            |
| ------------------------------ | -------------------------------------------------------------------------------- | ------------------------------ |
| Bootstrap MC                   | MC events are Poisson-resampled (different training weights on MC side)          | Real data stays the same       |
| Bootstrap Data                 | Real data events are Poisson-resampled (different training weights on data side) | MC stays the same              |
| NN Ensemble                    | NN random seed changes (different model initialization)                          | Both MC and data stay the same |
| Systematics (pileup, muEff, …) | A physics assumption in the MC simulation is shifted (different MC distribution) | Real data stays the same       |


After each retrained classifier is applied to the same N particle-level events, it produces a new likelihood ratio for each event. That likelihood ratio *is* the weight. So every variation always yields exactly N numbers - one weight per event. The output shape is always N × (number of replicas or variations):

```
418,014 events × 25  bootstrap_mc replicas
418,014 events × 25  bootstrap_data replicas
418,014 events × 100 ensemble members
418,014 events × 23  systematic variations
```

This means bootstrap MC, bootstrap data, NN ensemble, and systematic weights all live on the same canvas of N events and all have the same first dimension. There is no structural reason to store them in separate objects. They are simply additional columns alongside the observables and nominal weights.

The only exception is systematics that use **entirely different MC generators** producing different events (e.g. Sherpa with 326,430 events, nonDY with 433,397 events). These cannot share the canvas and require separate files.

#### 2.2.2. Unified N × C Matrix with Column Naming Convention

Based on the fixed-canvas principle, the entire result for a single MC sample is stored as **one flat N × C matrix**, where every column is either an observable, a weight, or an uncertainty variation. The column's role is encoded in its name through a prefix-based naming convention:

**Naming convention:**


| Prefix     | Role                        | How to identify                                   | Examples                                                                  |
| ---------- | --------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------- |
| *(none)*   | **Observable**              | Name contains no double-underscore `__` separator | `pT_ll`, `eta_l1`, `tau1_trackj1`, `Ntracks_trackj1`                      |
| `weight__` | **Nominal / MC weight**     | Starts with `weight__`                            | `weight__nominal`, `weight__mc`                                           |
| `stat__`   | **Statistical uncertainty** | Starts with `stat__`                              | `stat__bootstrap_mc__0`, `stat__bootstrap_data__24`, `stat__ensemble__99` |
| `syst__`   | **Systematic uncertainty**  | Starts with `syst__`                              | `syst__pileup`, `syst__muEffStat`, `syst__lumi`                           |


A simple split on `__` gives you the full taxonomy of any column:


| Column name             | Split on `__`                   | Interpretation                                                                            |
| ----------------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |
| `pT_ll`                 | `["pT_ll"]`                     | Length 1 → **observable**                                                                 |
| `weight__nominal`       | `["weight", "nominal"]`         | Starts with `weight` → **nominal weight**                                                 |
| `weight__mc`            | `["weight", "mc"]`              | Starts with `weight` → **MC generator weight**                                            |
| `stat__bootstrap_mc__7` | `["stat", "bootstrap_mc", "7"]` | Starts with `stat` → **statistical uncertainty**, subtype `bootstrap_mc`, replica index 7 |
| `stat__ensemble__42`    | `["stat", "ensemble", "42"]`    | Starts with `stat` → **statistical uncertainty**, subtype `ensemble`, member index 42     |
| `syst__pileup`          | `["syst", "pileup"]`            | Starts with `syst` → **systematic uncertainty**, source `pileup`                          |


**Why double underscores?** Single underscores already appear inside physics names (`pT_ll`, `eta_l1`, `bootstrap_mc`). Using `__` as the namespace separator eliminates all ambiguity - no observable name in HEP uses double underscores, so the split is always clean.

#### 2.2.3. Alignment with the Paper's (k + 2 + 2M) × N Format

Arratia et al. [2, Section 6.1] note that for classifier-based methods where systematic variations use the same particle-level events but different detector-level events or different weights, *"it could be possible to use the same feature list with a different set of unfolded weights for each uncertainty. In this case, only (k + 2 + 2M) × N numbers are required (or even fewer if the local uncertainty is w²)."*

Our unified single-matrix design directly implements this recommendation. OmniFold is a classifier-based method, and as described in Section 2.2.1, all variations - bootstrap, ensemble, and two-point systematics produce new weights on the same fixed canvas of N particle-level events. The observables never change, so they are stored once, and each variation adds only a single weight column. The total column count C becomes:

```
C = k + 2 + R_stat + M_syst
```

where:

- k = number of observables (24)
- 2 = nominal weight + MC weight
- R_stat = total statistical replicas (25 bootstrap_mc + 25 bootstrap_data + 100 ensemble = 150)
- M_syst = number of two-point systematic variations (23)

The paper's general format includes per-event w² uncertainty rows alongside each weight. We take advantage of the "even fewer" clause: for replica-type uncertainties, the uncertainty is computed as the standard deviation across replicas, not from individual w² values; for two-point systematics, the uncertainty is the difference between nominal and varied bin contents. Storing w² = w × w would be redundant — the consumer can square the weight on the fly if needed. This keeps the matrix compact at (k + 2 + R_stat + M_syst) × N rather than (k + 2 + 2M) × N.

#### 2.2.4. Concrete Example - Z+jets OmniFold Result

For the public Z+jets analysis:


| Category             | Columns | Column names                                           |
| -------------------- | ------- | ------------------------------------------------------ |
| Observables          | 24      | `pT_ll`, `eta_l1`, `eta_l2`, `phi_l1`, …               |
| Weights              | 2       | `weight__nominal`, `weight__mc`                        |
| Stat: bootstrap MC   | 25      | `stat__bootstrap_mc__0` … `stat__bootstrap_mc__24`     |
| Stat: bootstrap data | 25      | `stat__bootstrap_data__0` … `stat__bootstrap_data__24` |
| Stat: NN ensemble    | 100     | `stat__ensemble__0` … `stat__ensemble__99`             |
| Systematic           | 23      | `syst__pileup`, `syst__muEffStat`, `syst__lumi`, …     |
| **Total C**          | **199** |                                                        |


The result is a single matrix of shape **418,014 × 199**.


| Dimension         | Value   |
| ----------------- | ------- |
| Rows (N)          | 418,014 |
| Columns (C)       | 199     |
| Total numbers     | ~83M    |
| Storage (float64) | ~635 MB |


This is stored as a single HDF5 dataset with a `@columns` attribute listing all 199 column names. The naming convention makes the file self-describing: any consumer can classify every column by inspecting its prefix, without needing external documentation.

#### 2.2.5. Handling Systematics with Different Event Samples

The unified matrix works only when all variations share the same N particle-level events. Systematics that use entirely different MC generators produce different events with different N and different observable values. These break the fixed-canvas assumption and **must be stored as separate HDF5 files, each with its own YAML schema** (as declared in the `related_files` section, Section 2.1.9):

```
omnifold_zjets/
├── multifold.h5                       (418,014 × 199 — nominal, all uncertainties)
├── multifold_schema.yaml              (schema for multifold.h5)
├── multifold_sherpa.h5                (326,430 × 26  — Sherpa generator systematic)
├── multifold_sherpa_schema.yaml       (schema for multifold_sherpa.h5)
├── multifold_nonDY.h5                 (433,397 × 26  — non-DY composition systematic)
└── multifold_nonDY_schema.yaml        (schema for multifold_nonDY.h5)
```

Each alternative file is a self-contained unit: it has its own N', its own column list, and its own schema describing its specific structure. The alternative files contain only k + 2 columns (24 observables + `weight__nominal` + `weight__mc`) because they have no bootstrap or systematic sub-variations - they *are* the systematic variation.

This separate-file design follows three software engineering principles:

- **Single Responsibility** - each file represents exactly one MC canvas. No file mixes event populations with incompatible N.
- **Open/Closed** - adding a new generator systematic (e.g. Herwig) means publishing a new file + schema pair. Existing files are never modified.
- **Self-describing** - a consumer can download any single file and its schema and have a complete, usable artifact without needing the nominal file.

The nominal schema's `related_files` section acts as the manifest that links all files together, providing each file's `role`, `description`, `schema` URL, and `data_link` URL.

#### 2.2.6. Design Reasoning - Why a Single Matrix?

The decision to store everything in one flat matrix rather than separate datasets is driven by three considerations:

1. **Structural honesty.** Bootstrap MC, bootstrap data, NN ensemble, and systematic weights all have identical shape (N × 1) and identical semantics (a per-event reweighting factor produced by a retrained classifier on the same canvas). Splitting them into separate HDF5 datasets or files creates an artificial distinction that does not reflect the underlying physics or the algorithm. The only meaningful distinction is *how they were produced* (what changed in the training), and that is captured by the column name prefix, not by the storage structure.
2. **Simpler I/O and tooling.** A single DataFrame-like matrix can be loaded with `pd.read_hdf()`, `h5py`, or Parquet readers in one call. Users do not need to know which HDF5 group to look in or how to join multiple datasets. Column filtering by prefix (`df.filter(like="stat__")`) gives all statistical replicas in one operation.
3. **Alignment with the paper's intent.** The (k + 2 + 2M) × N format from [2] already places observables and weight variations side by side in a single matrix. We extend M to include statistical replicas because they have the same shape and the same canvas. The paper's w² uncertainty rows are dropped because replica-type uncertainties derive their uncertainty from the *spread* across replicas, not from per-event w² values.

#### 2.2.7. Storage Strategy

Following [2, Section 6.3], unbinned data can be O(GB) and is too large for HEPData directly. The publication is therefore split across two repositories:


| Content                                                | Storage                          | Reason                                       |
| ------------------------------------------------------ | -------------------------------- | -------------------------------------------- |
| Submission YAML + metadata + default binned histograms | **HEPData**                      | Small, searchable, integrates with Rivet     |
| Full per-event weight files in the unified N×C format  | **Zenodo** (linked from HEPData) | Large files, DOI, long-term archival         |
| Trained model checkpoints (optional, ONNX format)      | **Zenodo** or CERN Open Data     | Enables reinterpretation / transfer learning |


The HDF5 format is chosen as the primary format because it supports partial I/O (reading only specific columns or row ranges), chunked compression, and embedded metadata attributes. An optional Parquet export is provided for interoperability with columnar analysis frameworks (awkward-array, coffea).

### 2.3. HEPData Integration Layer

The integration maps OmniFold outputs to HEPData records by:

1. Generating a **submission YAML** in the standard HEPData format, listing each observable as a separate table with default binned histograms (bin edges, contents, and full uncertainty breakdown).
2. Embedding the **metadata YAML** as an additional resource in the submission, making it machine-queryable through the HEPData API.
3. Including a **Zenodo DOI link** pointing to the full per-event weight files, so users can seamlessly transition from browsing binned histograms on HEPData to downloading the unbinned data for reinterpretation.
4. Optionally referencing **ONNX model files** on Zenodo for users who want to apply the learned reweighting function to new MC samples rather than using the stored weights.

### 2.4. Validation Framework

The validation module implements three categories of checks:

1. **Schema validation** : Ensures the metadata YAML conforms to the specification (required fields present, types correct, observable count matches the k dimension of the data matrix).
2. **Normalization checks** : Verifies that weight sums are physically sensible: total cross-section within tolerance of the expected value, fraction of negative weights below threshold, and mean of bootstrap replicas consistent with the nominal within statistical fluctuations.
3. **Closure tests** : For producers, verifies the unfolding pipeline by applying the procedure to MC where the truth is known, then comparing the unfolded distribution to truth across all observables. Pass/fail criteria are defined in terms of the triangular discriminator metric used in [1, Table I].

### 2.5. Architecture Overview

The package is organized into four layers, each with a clear responsibility:

```
┌──────────────────────────────────────────────────────────────────┐
│                         User-Facing API                          │
│   omnifold_pub.load()  ·  omnifold_pub.publish()  ·  .plot()     │
├──────────────────────────────────────────────────────────────────┤
│                      Analysis Engine                             │
│   WeightedDataset  ·  Observable  ·  UncertaintyPropagator       │
├──────────────────────────────────────────────────────────────────┤
│                    Storage & I/O Layer                            │
│   HDF5Reader/Writer  ·  ParquetExporter  ·  HEPDataSubmitter    │
├──────────────────────────────────────────────────────────────────┤
│                   Schema & Validation Layer                       │
│   MetadataSchema  ·  SchemaValidator  ·  ClosureTest             │
└──────────────────────────────────────────────────────────────────┘
```

**Design principles:**

- **Schema-first:** Every published file must pass validation against the metadata schema before it is considered complete. The schema is the single source of truth.
- **Separation of concerns:** I/O, analysis, and presentation are decoupled. A user can load data without plotting; a publisher can validate without running analysis.
- **Backward compatibility:** The package can ingest existing "bare" HDF5 files (like the current Zenodo files) and augment them with metadata interactively.
- **Lightweight dependencies:** Core functionality requires only `numpy`, `h5py`, and `pyyaml`. Plotting requires `matplotlib`. Parquet export requires `pyarrow`.

### 2.6. Python API : `omnifold-pub`

The package provides four main components. The API is designed so that a physicist unfamiliar with the original analysis can load, analyze, and reinterpret published weights in a few lines.

#### 3.6.1. `OmniFoldResult` : Core Container

This is the primary user-facing class. It loads the unified N × C matrix from a standardized HDF5 file (or fetches from HEPData/Zenodo), parses the embedded metadata, and uses the `__` naming convention to automatically classify every column into observables, weights, statistical replicas, and systematic variations. It exposes these as structured attributes: `observables` (columns with no `__` prefix), `weights` (columns starting with `weight__`), and `uncertainties` (a `WeightCollection` grouping all `stat__` and `syst__` columns). It provides methods for computing weighted histograms with proper uncertainty propagation, producing per-bin uncertainty breakdowns, validating the file against the schema, and exporting back to HDF5/Parquet.

#### 3.6.2. `WeightCollection` : Weight Management

Encapsulates all uncertainty columns extracted from the unified matrix by parsing the `__` prefix convention. It groups columns into `stat_bootstrap_mc`, `stat_bootstrap_data`, `stat_ensemble`, and `syst` sub-collections automatically. Key operations include: computing the combined analysis weight (`weight__mc × weight__nominal`), propagating statistical uncertainty as the standard deviation across all `stat__` replicas when histogrammed, computing per-systematic bin-by-bin differences (nominal − varied) for each `syst__` column, and returning the total uncertainty as a quadrature sum of all sources.

#### 3.6.3. `Metadata` : Schema-Driven Metadata

Parses and validates the YAML metadata embedded in the HDF5 file (or a sidecar YAML file). It exposes typed attributes for dataset provenance, event selection cuts, observable definitions, unfolding configuration, and weight semantics. It also validates that the `@columns` attribute in the HDF5 file is consistent with the naming convention (every column either has no `__` prefix or starts with `weight__`, `stat__`, or `syst__`). It can generate a boolean phase-space mask from the declared cuts, which users apply before computing observables — preventing the "silent wrong phase space" error identified in the gap analysis.

#### 3.6.4. `OmniFoldPublisher` : Producing Standardized Output

Used by analyzers (not consumers) to convert raw OmniFold output into the unified N × C format. It accepts a populated `Metadata` object, DataFrames of observables, and weight arrays, then assembles them into a single matrix with standardized column names following the `__` convention, runs schema and normalization validation, and writes the result as a standards-compliant HDF5 file. It also generates a HEPData submission directory (submission YAML, binned histogram tables, metadata YAML, and a link to the Zenodo archive).

### 2.7. Example: End-to-End Consumer Workflow

The following shows how a physicist who did not run the original analysis would consume the published result — load the unified N × C matrix, compute a new observable, and produce a plot with full uncertainties. This is the core user story.

```python
import omnifold_pub as ofp
import numpy as np

# Load the unified 418,014 × 199 matrix
result = ofp.load("omnifold_result.h5")

# Columns are auto-classified by the __ naming convention
print(result.n_events)                     # 418,014
print(result.observable_names)             # ['pT_ll', 'eta_l1', ..., 'Ntracks_trackj2']  (24)
print(result.stat_columns)                 # ['stat__bootstrap_mc__0', ..., 'stat__ensemble__99']  (150)
print(result.syst_columns)                 # ['syst__pileup', ..., 'syst__lumi']  (23)

# Compute a DERIVED observable not in the original analysis: τ21 = τ2/τ1
tau1 = result.observables["tau1_trackj1"]
tau2 = result.observables["tau2_trackj1"]
tau21 = np.where(tau1 > 0, tau2 / tau1, 0.0)

# Produce a histogram with full stat+syst uncertainty propagation
hist = result.histogram_from_array(tau21, bins=30, range=(0, 1.5))
ofp.plot(hist, xlabel=r"$\tau_{21}$", save="tau21_reinterpretation.pdf")
```

---

## 3. Timeline

The project duration is 175 hours (medium difficulty), with mentors available June–October 2026.

I will be **available for the entire GSoC 2026 timeline** (community bonding through final evaluation) and intend to treat this project as my **primary commitment** during the coding period — **full time**, with no conflicting employment or coursework that would block regular mentor syncs, milestones, or deliverables.

### 3.1. Pre-GSoC Period

**Before June 2026:**

- Deep-dive into the [OmniFold codebase](https://github.com/hep-lbdl/OmniFold) and the [omnifold PyPI package](https://pypi.org/project/omnifold/).
- Study the HEPData submission format, Rivet integration, and existing HDF5/Parquet conventions in HEP.
- Set up the development environment, CI/CD pipeline, and project repository structure.
- Discuss schema design choices with mentors and iterate on the metadata specification.
- Familiarize myself with the public Z+jets weight files and reproduce the weighted histograms from the evaluation task.

### 3.2. GSoC Period

#### Community Bonding (Weeks 1–3: June)


| Week | Focus                                                                                                   | Deliverable                                                              |
| ---- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1    | Finalize the metadata schema (v1.0) with mentor feedback. Review existing proposals from [2].           | `schema/omnifold-schema-v1.0.yaml` + JSON Schema for validation          |
| 2    | Design the HDF5 container format. Prototype the `HDF5Reader`/`HDF5Writer` with the public Z+jets files. | Working I/O module that can read existing files and write the new format |
| 3    | Define the `Metadata` class and schema validator. Write unit tests for schema validation.               | `omnifold_pub.schema` module with full test coverage                     |


#### Coding Phase 1 (Weeks 4–9: July – mid-August)


| Week | Focus                                                                                                                                             | Deliverable                                       |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 4    | Implement `OmniFoldResult` and `WeightCollection` classes. Support loading from the new HDF5 format.                                              | Core data model with load/save                    |
| 5    | Implement the `histogram()` method with proper √(Σw²) uncertainty. Port and integrate the `weighted_histogram` function from the evaluation task. | Working histogram computation with tests          |
| 6    | Implement uncertainty propagation: bootstrap (std across replicas), ensemble (std across members), and systematic (nominal − varied).             | `UncertaintyBand` class with breakdown by source  |
| 7    | Implement the `OmniFoldPublisher` class. Convert raw OmniFold output into the standardized format.                                                | Publisher that produces valid HDF5 + sidecar YAML |
| 8    | Implement the plotting module: publication-quality histograms, ratio plots, uncertainty band visualization.                                       | `omnifold_pub.plot` module                        |
| 9    | **Midterm evaluation.** Write the normalization validator and schema validation CLI. Buffer for catching up.                                      | `omnifold_pub validate result.h5` CLI command     |


#### Coding Phase 2 (Weeks 10–15: mid-August – September)


| Week | Focus                                                                                                                                                    | Deliverable                              |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 10   | Implement HEPData submission generator: map observables to HEPData tables, produce submission YAML with binned histograms.                               | `to_hepdata_submission()` method         |
| 11   | Implement `from_hepdata()` loader: fetch metadata from HEPData, follow Zenodo links for full weight files. Optional Parquet export.                      | Remote loading support                   |
| 12   | Implement closure test framework and stability diagnostics.                                                                                              | `omnifold_pub.validation` module         |
| 13   | Build the reference example notebook: end-to-end workflow using public Z+jets data (download → load → histogram → derived observable → comparison plot). | `examples/z_jets_reinterpretation.ipynb` |
| 14   | Build a second example: publishing a new result from scratch, including HEPData submission generation.                                                   | `examples/publishing_workflow.ipynb`     |
| 15   | Documentation: API reference (auto-generated from docstrings), user guide, and contributor guide. Final polish.                                          | Complete documentation on ReadTheDocs    |


#### Final Evaluation (Week 16: early October)

- Final code review and cleanup.
- Submit the package to PyPI as `omnifold-pub`.
- Final mentor evaluation.

### 3.3. Post-GSoC Period

- Continue maintaining the package, fixing bugs, and responding to community feedback.
- Work with ATLAS/CMS collaborators to apply the schema to a real analysis.
- Explore extensions: support for density-based methods (cINN), ONNX model embedding, and multi-analysis combinations.

---

## 4. Risk Mitigation


| Risk                                           | Likelihood | Mitigation                                                                                                                                   |
| ---------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Schema design disagreements**                | Medium     | Iterate with mentors during community bonding. Keep the schema extensible with optional fields and `additional_info` sections.               |
| **HEPData API changes or limitations**         | Low        | Abstract the HEPData interaction behind an interface. Fall back to manual submission if the API is unavailable.                              |
| **Large file handling performance**            | Medium     | Use HDF5 chunked I/O and lazy loading (only read columns when accessed). Benchmark with the full 2.7 GB `target.h5` file early.              |
| **Scope creep (model publishing, retraining)** | High       | Model/training details are documented in metadata but checkpoints are optional. Full retraining support is explicitly out of scope for GSoC. |
| **Backward compatibility with existing files** | Low        | The `from_hdf5()` loader auto-detects whether the file uses the old flat DataFrame format or the new structured format, and handles both.    |


---

## 5. Acknowledgements

I would like to thank **Tanvi Wamorkar** and **Benjamin Nachman** for proposing this project and for providing the evaluation task that directly shaped the design decisions in this proposal. I am also grateful to the authors of the "Presenting Unbinned Differential Cross Section Results" paper [2] for laying the conceptual groundwork for unbinned data publication, and to the OmniFold team for making their code and data publicly available.

---

## 6. References

1. A. Andreassen, P.T. Komiske, E.M. Metodiev, B. Nachman, J. Thaler. *OmniFold: A Method to Simultaneously Unfold All Observables*. Phys. Rev. Lett. 124 (2020) 182001. [arXiv:1911.09107](https://arxiv.org/abs/1911.09107)
2. M. Arratia et al. *Presenting Unbinned Differential Cross Section Results*. [arXiv:2109.13243](https://arxiv.org/abs/2109.13243)
3. OmniFold Z+jets public dataset. Zenodo. [DOI: 10.5281/zenodo.11507450](https://zenodo.org/records/11507450)
4. E. Maguire, L. Heinrich, G. Watt. *HEPData: a repository for high energy physics data*. J. Phys. Conf. Ser. 898 (2017) 102006.
5. OmniFold GitHub Repository. [https://github.com/hep-lbdl/OmniFold](https://github.com/hep-lbdl/OmniFold)
6. OmniFold PyPI Package. [https://pypi.org/project/omnifold/](https://pypi.org/project/omnifold/)
7. A. Buckley et al. *Rivet user manual*. Comput. Phys. Commun. 184 (2013) 2803–2819.
8. B. Nachman, J. Thaler. *A Neural Resampler for Monte Carlo Reweighting with Preserved Uncertainties*. [arXiv:2007.11586](https://arxiv.org/abs/2007.11586)

---

## 7. Contact

- **Email** - [rajkumardongre17@gmail.com](mailto:rajkumardongre17@gmail.com)
- **GitHub** - [rajkumardongre](https://github.com/rajkumardongre)
- **Timezone** - IST (UTC +5:30)

